"""Publisher provider protocol + Fake (tests) + Live Google adapter (fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app_factory.application.customer_release.play import (
    REQUIRED_TEST_PERMISSIONS,
    STATUS_ACCESS_DENIED,
    STATUS_APP_NOT_FOUND,
    STATUS_AUTH_FAILED,
    STATUS_CREDENTIAL_MISSING,
    STATUS_NOT_CONFIGURED,
    STATUS_PACKAGE_ID_MISMATCH,
    STATUS_PERMISSION_INCOMPLETE,
    STATUS_PLAY_APP_SETUP_REQUIRED,
    STATUS_PLAY_POLICY_REQUIREMENT_PENDING,
    STATUS_READY,
    STATUS_REVOKED,
    GooglePlayPublisherConnection,
    classify_permissions,
    stamp_now,
)
from app_factory.application.customer_release.signing import SecretReferenceResolver
from app_factory.domain.errors import (
    PlayConnectionError,
    PlayDeliveryError,
    ProductionSubmissionBlocked,
    TenantIsolationError,
)

PRODUCTION_SUBMISSION_BLOCKED = "PRODUCTION_SUBMISSION_BLOCKED"
TRACK_INTERNAL = "internal"
TRACK_CLOSED = "closed"
TRACK_PRODUCTION = "production"


@dataclass
class PlayAppRecord:
    package_name: str
    exists: bool = True
    policy_pending: bool = False
    permissions: list[str] = field(default_factory=list)


class PublisherProvider(Protocol):
    def verify_connection(
        self,
        connection: GooglePlayPublisherConnection,
        *,
        expected_package: str,
    ) -> dict[str, Any]: ...

    def create_edit(self, package_name: str) -> str: ...

    def upload_bundle(
        self,
        package_name: str,
        edit_id: str,
        *,
        aab_sha256: str,
        version_code: int,
    ) -> dict[str, Any]: ...

    def configure_track(
        self,
        package_name: str,
        edit_id: str,
        *,
        track: str,
        version_code: int,
    ) -> dict[str, Any]: ...

    def validate_edit(self, package_name: str, edit_id: str) -> dict[str, Any]: ...

    def commit_edit(self, package_name: str, edit_id: str) -> dict[str, Any]: ...

    def read_track(self, package_name: str, track: str) -> dict[str, Any]: ...


class FakePlayPublisherProvider:
    """In-memory Play Android Publisher API. Production writes never execute."""

    def __init__(self) -> None:
        self.apps: dict[str, PlayAppRecord] = {}
        self.auth_ok = True
        self.revoked = False
        self.credentials_present = True
        self.timeout = False
        self.validate_fail = False
        self.commit_fail = False
        self.reject_aab = False
        self.edits: dict[str, dict[str, Any]] = {}
        self.committed: dict[str, dict[str, Any]] = {}
        self._edit_seq = 0
        self.writes: list[str] = []

    def register_app(self, package_name: str, *, permissions: list[str] | None = None) -> None:
        self.apps[package_name] = PlayAppRecord(
            package_name=package_name,
            exists=True,
            permissions=list(permissions or sorted(REQUIRED_TEST_PERMISSIONS)),
        )

    def verify_connection(
        self,
        connection: GooglePlayPublisherConnection,
        *,
        expected_package: str,
    ) -> dict[str, Any]:
        connection.assert_bound(
            tenant_id=connection.tenant_id,
            customer_app_id=connection.customer_app_id,
            package_name=connection.package_name,
        )
        if connection.package_name != expected_package:
            return _result(STATUS_PACKAGE_ID_MISMATCH, "PACKAGE_ID_MISMATCH")
        if self.revoked:
            return _result(STATUS_REVOKED, "REVOKED")
        if not self.credentials_present or not connection.credential_secret_reference:
            return _result(STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        if not self.auth_ok:
            return _result(STATUS_AUTH_FAILED, "AUTH_FAILED")
        app = self.apps.get(connection.package_name)
        if app is None or not app.exists:
            return _result(
                STATUS_PLAY_APP_SETUP_REQUIRED,
                "PLAY_APP_SETUP_REQUIRED",
                missing=["play_console_app_record"],
            )
        if app.policy_pending:
            return _result(STATUS_PLAY_POLICY_REQUIREMENT_PENDING, "PLAY_POLICY_REQUIREMENT_PENDING")
        classified = classify_permissions(app.permissions)
        excess = classified["excess_forbidden"]
        if not classified["ready_for_internal_track"]:
            return _result(
                STATUS_PERMISSION_INCOMPLETE,
                "PERMISSION_INCOMPLETE",
                permissions=classified,
            )
        if connection.scope != "APP_SCOPED":
            return _result(STATUS_ACCESS_DENIED, "ACCOUNT_WIDE_ADMIN")
        return {
            "status": STATUS_READY,
            "play_app": "PLAY_APP_BOUND",
            "permission_status": STATUS_READY,
            "permissions": classified,
            "excess_permissions_recorded_not_used": excess,
            "last_verified_at": stamp_now(),
            "last_error_code": "",
        }

    def create_edit(self, package_name: str) -> str:
        self._guard_app(package_name)
        self._edit_seq += 1
        edit_id = f"edit-{self._edit_seq}"
        self.edits[edit_id] = {
            "id": edit_id,
            "package_name": package_name,
            "bundle_version_code": None,
            "bundle_sha256": None,
            "track": None,
            "committed": False,
        }
        return edit_id

    def upload_bundle(
        self,
        package_name: str,
        edit_id: str,
        *,
        aab_sha256: str,
        version_code: int,
    ) -> dict[str, Any]:
        if self.timeout:
            raise PlayDeliveryError("API_TIMEOUT")
        edit = self._edit(package_name, edit_id)
        if self.reject_aab:
            raise PlayDeliveryError("AAB_REJECTED")
        committed = self.committed.get(package_name) or {}
        if committed.get("version_code") == version_code:
            raise PlayDeliveryError("DUPLICATE_VERSION_CODE")
        edit["bundle_version_code"] = version_code
        edit["bundle_sha256"] = aab_sha256
        return {"version_code": version_code, "sha256": aab_sha256}

    def configure_track(
        self,
        package_name: str,
        edit_id: str,
        *,
        track: str,
        version_code: int,
    ) -> dict[str, Any]:
        normalized = track.strip().lower()
        if normalized == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        if normalized not in {TRACK_INTERNAL, TRACK_CLOSED}:
            raise PlayDeliveryError(f"UNSUPPORTED_TRACK:{track}")
        if normalized == TRACK_CLOSED:
            # Prepared but Internal is the proven default.
            pass
        edit = self._edit(package_name, edit_id)
        if edit["bundle_version_code"] != version_code:
            raise PlayDeliveryError("WRONG_VERSION_CODE")
        edit["track"] = TRACK_INTERNAL if normalized == TRACK_INTERNAL else TRACK_CLOSED
        self.writes.append(f"track:{edit['track']}")
        return {"track": edit["track"], "version_code": version_code}

    def validate_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        edit = self._edit(package_name, edit_id)
        if self.validate_fail:
            raise PlayDeliveryError("EDIT_VALIDATION_FAILURE")
        if not edit["bundle_version_code"] or not edit["track"]:
            raise PlayDeliveryError("EDIT_VALIDATION_FAILURE")
        edit["validated"] = True
        return {"status": "VALID"}

    def commit_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        edit = self._edit(package_name, edit_id)
        if self.commit_fail:
            raise PlayDeliveryError("EDIT_COMMIT_FAILURE")
        if edit.get("committed"):
            return self.committed[package_name]
        if not edit.get("validated"):
            raise PlayDeliveryError("EDIT_COMMIT_FAILURE")
        payload = {
            "package_name": package_name,
            "edit_id": edit_id,
            "track": edit["track"],
            "version_code": edit["bundle_version_code"],
            "bundle_sha256": edit["bundle_sha256"],
            "status": "COMPLETED",
        }
        edit["committed"] = True
        self.committed[package_name] = payload
        return payload

    def read_track(self, package_name: str, track: str) -> dict[str, Any]:
        if track.strip().lower() == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        payload = self.committed.get(package_name)
        if not payload:
            raise PlayDeliveryError("RELEASE_NOT_FOUND")
        if payload["track"] != track.strip().lower():
            raise PlayDeliveryError("TRACK_MISMATCH")
        return dict(payload)

    def _guard_app(self, package_name: str) -> None:
        app = self.apps.get(package_name)
        if app is None or not app.exists:
            raise PlayConnectionError(STATUS_APP_NOT_FOUND)

    def _edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        edit = self.edits.get(edit_id)
        if edit is None or edit["package_name"] != package_name:
            raise PlayDeliveryError("EDIT_NOT_FOUND")
        if edit.get("committed"):
            return edit
        return edit


class GooglePlayPublisherProvider:
    """Live Android Publisher API adapter. Missing creds/library → fail-closed, no invented PASS."""

    def __init__(
        self,
        resolver: SecretReferenceResolver,
        connection: GooglePlayPublisherConnection,
    ) -> None:
        self._resolver = resolver
        self._connection = connection

    def verify_connection(
        self,
        connection: GooglePlayPublisherConnection,
        *,
        expected_package: str,
    ) -> dict[str, Any]:
        connection.assert_bound(
            tenant_id=connection.tenant_id,
            customer_app_id=connection.customer_app_id,
            package_name=connection.package_name,
        )
        if connection.package_name != expected_package:
            return _result(STATUS_PACKAGE_ID_MISMATCH, "PACKAGE_ID_MISMATCH")
        if not connection.credential_secret_reference:
            return _result(STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        present = self._resolver.has(
            connection.credential_secret_reference,
            tenant_id=connection.tenant_id,
            customer_app_id=connection.customer_app_id,
        )
        if not present:
            return _result(STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        try:
            import google.auth  # noqa: F401
        except ImportError:
            return {
                "status": STATUS_NOT_CONFIGURED,
                "play_app": STATUS_NOT_CONFIGURED,
                "live_proof": "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL",
                "last_error_code": "GOOGLE_AUTH_LIBRARY_MISSING",
                "external_requirements": [
                    "customer_play_developer_account",
                    "app_scoped_service_account_or_oauth",
                    "play_console_app_with_matching_application_id",
                    "internal_test_track_capability",
                    "google-auth optional extra",
                ],
            }
        return {
            "status": STATUS_NOT_CONFIGURED,
            "play_app": STATUS_NOT_CONFIGURED,
            "live_proof": "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL",
            "last_error_code": "LIVE_PLAY_ACCOUNT_NOT_WIRED",
            "external_requirements": [
                "authorized_customer_play_app",
                "app_scoped_credential_in_ops_secret_dir",
            ],
        }

    def create_edit(self, package_name: str) -> str:
        del package_name
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def upload_bundle(self, package_name: str, edit_id: str, **kwargs: Any) -> dict[str, Any]:
        del package_name, edit_id, kwargs
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def configure_track(self, package_name: str, edit_id: str, **kwargs: Any) -> dict[str, Any]:
        if str(kwargs.get("track") or "").lower() == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        del package_name, edit_id
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def validate_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        del package_name, edit_id
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def commit_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        del package_name, edit_id
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def read_track(self, package_name: str, track: str) -> dict[str, Any]:
        if track.strip().lower() == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        del package_name
        raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")


def _result(
    status: str,
    error: str,
    *,
    permissions: dict[str, Any] | None = None,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "play_app": status if status == STATUS_PLAY_APP_SETUP_REQUIRED else status,
        "permission_status": status,
        "last_error_code": error,
        "last_verified_at": stamp_now(),
    }
    if permissions is not None:
        payload["permissions"] = permissions
    if missing is not None:
        payload["missing_preconditions"] = missing
    return payload


def assert_test_track(track: str) -> str:
    normalized = track.strip().lower()
    if normalized == TRACK_PRODUCTION:
        raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
    if normalized not in {TRACK_INTERNAL, TRACK_CLOSED}:
        raise PlayDeliveryError(f"UNSUPPORTED_TRACK:{track}")
    return normalized
