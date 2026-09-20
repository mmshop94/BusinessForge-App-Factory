"""Publisher provider protocol + Fake (tests) + Live Google adapter (fail-closed)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
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
    STATUS_PLAY_ACCOUNT_REQUIREMENT_PENDING,
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
LIVE_INTERNAL_TEST_ENV = "REAL_GOOGLE_PLAY_INTERNAL_TEST"


def live_google_play_internal_test_enabled() -> bool:
    return os.environ.get(LIVE_INTERNAL_TEST_ENV) == "1"


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
        aab_path: str | Path | None = None,
        upload_certificate_sha256: str = "",
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
        self.credentials_malformed = False
        self.timeout = False
        self.validate_fail = False
        self.commit_fail = False
        self.reject_aab = False
        self.edit_create_fail = False
        self.readback_mismatch = False
        self.account_requirement_pending = False
        self.expected_upload_cert_sha256 = ""
        self.known_version_codes: dict[str, int] = {}
        self.tester_opt_in_url = ""
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
        if self.credentials_malformed:
            return _result(STATUS_AUTH_FAILED, "CREDENTIAL_MALFORMED")
        if not self.auth_ok:
            return _result(STATUS_AUTH_FAILED, "AUTH_FAILED")
        if self.account_requirement_pending:
            return _result(
                STATUS_PLAY_ACCOUNT_REQUIREMENT_PENDING,
                "PLAY_ACCOUNT_REQUIREMENT_PENDING",
            )
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
        extra_present = bool(excess) or bool(classified.get("production_permission_present"))
        return {
            "status": STATUS_READY,
            "play_app": "PLAY_APP_BOUND",
            "permission_status": STATUS_READY,
            "permissions": classified,
            "excess_permissions_recorded_not_used": excess,
            "EXTRA_PERMISSION_PRESENT": extra_present,
            "last_verified_at": stamp_now(),
            "last_error_code": "",
            "access_result": "READY",
            "permission_result": "READY",
            "principal_reference": connection.principal_reference,
            "package_name": connection.package_name,
            "publisher_connection_id": connection.principal_reference,
            "provider_response_id": f"fake:{connection.package_name}",
            "tester_opt_in_url": self.tester_opt_in_url,
            "production_permission_used": False,
        }

    def create_edit(self, package_name: str) -> str:
        if self.edit_create_fail:
            raise PlayDeliveryError("EDIT_CREATE_FAILURE")
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
        aab_path: str | Path | None = None,
        upload_certificate_sha256: str = "",
    ) -> dict[str, Any]:
        del aab_path
        if self.timeout:
            raise PlayDeliveryError("API_TIMEOUT")
        edit = self._edit(package_name, edit_id)
        if self.reject_aab:
            raise PlayDeliveryError("AAB_REJECTED")
        if (
            self.expected_upload_cert_sha256
            and upload_certificate_sha256
            and upload_certificate_sha256 != self.expected_upload_cert_sha256
        ):
            raise PlayDeliveryError("WRONG_SIGNING_CERTIFICATE")
        committed = self.committed.get(package_name) or {}
        known = int(self.known_version_codes.get(package_name) or committed.get("version_code") or 0)
        if known and int(version_code) == known:
            raise PlayDeliveryError("DUPLICATE_VERSION_CODE")
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
        result = dict(payload)
        if self.readback_mismatch:
            result["version_code"] = int(result["version_code"]) + 99
            result["status"] = "MISMATCH"
        if self.tester_opt_in_url:
            result["tester_opt_in_url"] = self.tester_opt_in_url
        return result

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
        if not live_google_play_internal_test_enabled():
            return {
                "status": STATUS_NOT_CONFIGURED,
                "play_app": STATUS_NOT_CONFIGURED,
                "live_proof": "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL",
                "last_error_code": "LIVE_PLAY_ACCOUNT_NOT_WIRED",
                "external_requirements": [
                    "authorized_customer_or_reference_play_app",
                    "app_scoped_credential_in_ops_secret_dir",
                    "REAL_GOOGLE_PLAY_INTERNAL_TEST=1",
                ],
            }
        return self._live_verify(connection, expected_package=expected_package)

    def create_edit(self, package_name: str) -> str:
        self._require_live_writes()
        payload = self._live_json(
            "POST",
            f"/androidpublisher/v3/applications/{package_name}/edits",
            json_body={},
        )
        edit_id = str(payload.get("id") or "")
        if not edit_id:
            raise PlayDeliveryError("EDIT_CREATE_FAILURE")
        return edit_id

    def upload_bundle(self, package_name: str, edit_id: str, **kwargs: Any) -> dict[str, Any]:
        self._require_live_writes()
        aab_path = kwargs.get("aab_path")
        version_code = int(kwargs.get("version_code") or 0)
        if not aab_path:
            raise PlayDeliveryError("AAB_MISSING")
        path = Path(str(aab_path))
        if not path.is_file():
            raise PlayDeliveryError("AAB_MISSING")
        payload = self._live_upload_bundle(package_name, edit_id, path)
        returned = int(payload.get("versionCode") or payload.get("version_code") or 0)
        if version_code and returned and returned != version_code:
            raise PlayConnectionError("WRONG_VERSION_CODE")
        return {"version_code": returned or version_code, "sha256": kwargs.get("aab_sha256")}

    def configure_track(self, package_name: str, edit_id: str, **kwargs: Any) -> dict[str, Any]:
        if str(kwargs.get("track") or "").lower() == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        self._require_live_writes()
        track = str(kwargs.get("track") or TRACK_INTERNAL).strip().lower()
        if track != TRACK_INTERNAL:
            raise PlayDeliveryError(f"UNSUPPORTED_TRACK:{track}")
        version_code = int(kwargs.get("version_code") or 0)
        payload = self._live_json(
            "PUT",
            f"/androidpublisher/v3/applications/{package_name}/edits/{edit_id}/tracks/{TRACK_INTERNAL}",
            json_body={
                "track": TRACK_INTERNAL,
                "releases": [{"status": "completed", "versionCodes": [str(version_code)]}],
            },
        )
        return {"track": TRACK_INTERNAL, "version_code": version_code, "provider_response_id": payload.get("track")}

    def validate_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        self._require_live_writes()
        payload = self._live_json(
            "GET",
            f"/androidpublisher/v3/applications/{package_name}/edits/{edit_id}",
        )
        if not payload.get("id"):
            raise PlayDeliveryError("EDIT_VALIDATION_FAILURE")
        return {"status": "VALID", "provider_response_id": payload.get("id")}

    def commit_edit(self, package_name: str, edit_id: str) -> dict[str, Any]:
        self._require_live_writes()
        payload = self._live_json(
            "POST",
            f"/androidpublisher/v3/applications/{package_name}/edits/{edit_id}:commit",
            json_body={},
        )
        return {"status": "COMPLETED", "edit_id": payload.get("id") or edit_id, "package_name": package_name}

    def read_track(self, package_name: str, track: str) -> dict[str, Any]:
        if track.strip().lower() == TRACK_PRODUCTION:
            raise ProductionSubmissionBlocked(PRODUCTION_SUBMISSION_BLOCKED)
        self._require_live_writes()
        # Read-back uses a fresh edit so we do not depend on the committed edit id.
        edit_id = self.create_edit(package_name)
        payload = self._live_json(
            "GET",
            f"/androidpublisher/v3/applications/{package_name}/edits/{edit_id}/tracks/{track.strip().lower()}",
        )
        releases = payload.get("releases") or []
        version_codes: list[int] = []
        status = ""
        for rel in releases:
            status = str(rel.get("status") or status)
            for code in rel.get("versionCodes") or []:
                version_codes.append(int(code))
        return {
            "package_name": package_name,
            "track": track.strip().lower(),
            "version_code": max(version_codes) if version_codes else 0,
            "bundle_version_code": max(version_codes) if version_codes else 0,
            "status": status or "UNKNOWN",
            "edit_id": edit_id,
        }

    def _live_verify(
        self,
        connection: GooglePlayPublisherConnection,
        *,
        expected_package: str,
    ) -> dict[str, Any]:
        try:
            token = self._live_token(connection)
        except PlayConnectionError as exc:
            code = str(exc)
            if "CREDENTIAL_MALFORMED" in code:
                return _result(STATUS_AUTH_FAILED, "CREDENTIAL_MALFORMED")
            if "CREDENTIAL_MISSING" in code:
                return _result(STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
            if "REVOKED" in code:
                return _result(STATUS_REVOKED, "REVOKED")
            return _result(STATUS_AUTH_FAILED, "AUTH_FAILED")
        try:
            import httpx
        except ImportError:
            return {
                "status": STATUS_NOT_CONFIGURED,
                "play_app": STATUS_NOT_CONFIGURED,
                "live_proof": "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL",
                "last_error_code": "HTTPX_MISSING",
            }
        url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{expected_package}/edits"
        try:
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                json={},
                timeout=30.0,
            )
        except Exception:
            return _result(STATUS_AUTH_FAILED, "AUTH_FAILED")
        if response.status_code in {401, 403}:
            body = (response.text or "").lower()
            if "not found" in body or response.status_code == 404:
                return _result(STATUS_PLAY_APP_SETUP_REQUIRED, "PLAY_APP_SETUP_REQUIRED")
            return _result(STATUS_ACCESS_DENIED, "ACCESS_DENIED")
        if response.status_code == 404:
            return _result(STATUS_PLAY_APP_SETUP_REQUIRED, "PLAY_APP_SETUP_REQUIRED")
        if response.status_code >= 400:
            return _result(STATUS_AUTH_FAILED, "AUTH_FAILED")
        edit_id = ""
        try:
            edit_id = str(response.json().get("id") or "")
        except Exception:
            edit_id = ""
        return {
            "status": STATUS_READY,
            "play_app": "PLAY_APP_BOUND",
            "permission_status": STATUS_READY,
            "last_verified_at": stamp_now(),
            "last_error_code": "",
            "access_result": "READY",
            "permission_result": "READY",
            "principal_reference": connection.principal_reference,
            "package_name": expected_package,
            "publisher_connection_id": connection.principal_reference,
            "provider_response_id": edit_id,
            "EXTRA_PERMISSION_PRESENT": False,
            "production_permission_used": False,
            "live_proof": "LIVE_AUTH_AND_PACKAGE_ACCESS",
        }

    def _require_live_writes(self) -> None:
        if not live_google_play_internal_test_enabled():
            raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL")

    def _live_token(self, connection: GooglePlayPublisherConnection | None = None) -> str:
        conn = connection or self._connection
        resolve = getattr(self._resolver, "resolve_value", None)
        if resolve is None:
            raise PlayConnectionError("CREDENTIAL_MISSING")
        raw = resolve(
            conn.credential_secret_reference,
            tenant_id=conn.tenant_id,
            customer_app_id=conn.customer_app_id,
        )
        try:
            info = json.loads(raw)
        except Exception as exc:
            raise PlayConnectionError("CREDENTIAL_MALFORMED") from exc
        if not isinstance(info, dict) or not info.get("private_key"):
            raise PlayConnectionError("CREDENTIAL_MALFORMED")
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
        except ImportError as exc:
            raise PlayConnectionError("GOOGLE_AUTH_LIBRARY_MISSING") from exc
        try:
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/androidpublisher"],
            )
            creds.refresh(Request())
        except Exception as exc:
            message = str(exc).lower()
            if "revoked" in message:
                raise PlayConnectionError("REVOKED") from exc
            raise PlayConnectionError("AUTH_FAILED") from exc
        token = getattr(creds, "token", "") or ""
        if not token:
            raise PlayConnectionError("AUTH_FAILED")
        return str(token)

    def _live_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:
            raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL") from exc
        token = self._live_token()
        url = f"https://androidpublisher.googleapis.com{path}"
        response = httpx.request(
            method,
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            json=json_body,
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise PlayDeliveryError(f"GOOGLE_API_{response.status_code}")
        if not response.content:
            return {}
        payload = response.json()
        if not isinstance(payload, dict):
            raise PlayDeliveryError("EDIT_VALIDATION_FAILURE")
        return payload

    def _live_upload_bundle(self, package_name: str, edit_id: str, path: Path) -> dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:
            raise PlayConnectionError("LIVE_PLAY_PROOF_BLOCKED_EXTERNAL") from exc
        token = self._live_token()
        url = (
            "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/"
            f"applications/{package_name}/edits/{edit_id}/bundles?uploadType=media"
        )
        data = path.read_bytes()
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream",
            },
            content=data,
            timeout=120.0,
        )
        if response.status_code >= 400:
            raise PlayDeliveryError("AAB_REJECTED")
        payload = response.json()
        if not isinstance(payload, dict):
            raise PlayDeliveryError("AAB_REJECTED")
        return payload


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
