"""App Store Connect provider: Fake (tests) + live fail-closed. No production submit."""

from __future__ import annotations

import os
from typing import Any, Protocol

from app_factory.application.customer_release.apple import (
    STATUS_APP_RECORD_REQUIRED,
    STATUS_AUTH_FAILED,
    STATUS_BUNDLE_ID_MISMATCH,
    STATUS_CREDENTIAL_MISSING,
    STATUS_NOT_CONFIGURED,
    STATUS_READY,
    ApplePublisherConnection,
    classify_apple_permissions,
    stamp_now,
)
from app_factory.application.customer_release.signing import SecretReferenceResolver
from app_factory.domain.errors import (
    AppleConnectionError,
    AppStoreProductionSubmissionBlocked,
    TenantIsolationError,
)

APP_STORE_PRODUCTION_SUBMISSION_BLOCKED = "APP_STORE_PRODUCTION_SUBMISSION_BLOCKED"
LIVE_TESTFLIGHT_ENV = "REAL_APPLE_TESTFLIGHT_TEST"
BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"


def live_apple_testflight_enabled() -> bool:
    return os.environ.get(LIVE_TESTFLIGHT_ENV) == "1"


class ApplePublisherProvider(Protocol):
    def verify_connection(
        self,
        connection: ApplePublisherConnection,
        *,
        expected_bundle: str,
    ) -> dict[str, Any]: ...

    def lookup_app(self, bundle_identifier: str) -> dict[str, Any]: ...

    def upload_build(
        self,
        bundle_identifier: str,
        *,
        ipa_sha256: str,
        build_number: int,
        destination: str = "testflight",
    ) -> dict[str, Any]: ...


class FakeApplePublisherProvider:
    def __init__(self) -> None:
        self.apps: set[str] = set()
        self.credentials_present = True
        self.permissions: dict[str, list[str]] = {}
        self.auth_fail = False

    def register_app(self, bundle_identifier: str, permissions: list[str] | None = None) -> None:
        self.apps.add(bundle_identifier)
        self.permissions[bundle_identifier] = permissions or [
            "APP_MANAGER",
            "CLOUD_MANAGED_APP_DISTRIBUTION",
        ]

    def verify_connection(
        self,
        connection: ApplePublisherConnection,
        *,
        expected_bundle: str,
    ) -> dict[str, Any]:
        connection.assert_bound(
            tenant_id=connection.tenant_id,
            customer_app_id=connection.customer_app_id,
            bundle_identifier=connection.bundle_identifier,
        )
        if expected_bundle != connection.bundle_identifier:
            raise TenantIsolationError("APPLE_BUNDLE_ID_MISMATCH")
        if not connection.private_key_secret_reference:
            return _result(connection, STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        if not self.credentials_present:
            return _result(connection, STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        if self.auth_fail:
            return _result(connection, STATUS_AUTH_FAILED, "AUTH_FAILED")
        if expected_bundle not in self.apps:
            return _result(connection, STATUS_APP_RECORD_REQUIRED, "APP_STORE_APP_RECORD_REQUIRED")
        classified = classify_apple_permissions(self.permissions.get(expected_bundle) or ())
        if not classified["ready_for_testflight"]:
            return _result(
                connection,
                "PERMISSION_INCOMPLETE",
                "PERMISSION_INCOMPLETE",
                extra=classified,
            )
        payload = _result(connection, STATUS_READY, "", extra=classified)
        payload["play_app"] = None
        payload["app_record"] = "APP_STORE_APP_BOUND"
        payload["customer_owned_publishing_proven"] = False
        return payload

    def lookup_app(self, bundle_identifier: str) -> dict[str, Any]:
        if bundle_identifier not in self.apps:
            return {"status": STATUS_APP_RECORD_REQUIRED, "bundle_identifier": bundle_identifier}
        return {
            "status": "APP_STORE_APP_BOUND",
            "bundle_identifier": bundle_identifier,
        }

    def upload_build(
        self,
        bundle_identifier: str,
        *,
        ipa_sha256: str,
        build_number: int,
        destination: str = "testflight",
    ) -> dict[str, Any]:
        if destination.strip().lower() in {"production", "app_store", "appstore", "review"}:
            raise AppStoreProductionSubmissionBlocked(APP_STORE_PRODUCTION_SUBMISSION_BLOCKED)
        if bundle_identifier not in self.apps:
            raise AppleConnectionError("APP_STORE_APP_RECORD_REQUIRED")
        return {
            "status": "TESTFLIGHT_UPLOAD_IN_PROGRESS",
            "bundle_identifier": bundle_identifier,
            "ipa_sha256": ipa_sha256,
            "build_number": build_number,
            "destination": "testflight",
        }


class AppleAppStoreConnectPublisherProvider:
    """Live adapter. Without credentials or the live flag: BLOCKED_EXTERNAL."""

    def __init__(
        self,
        resolver: SecretReferenceResolver,
        connection: ApplePublisherConnection,
    ) -> None:
        self._resolver = resolver
        self._connection = connection

    def verify_connection(
        self,
        connection: ApplePublisherConnection,
        *,
        expected_bundle: str,
    ) -> dict[str, Any]:
        if expected_bundle != connection.bundle_identifier:
            return _result(connection, STATUS_BUNDLE_ID_MISMATCH, "APPLE_BUNDLE_ID_MISMATCH")
        if not connection.private_key_secret_reference:
            return _result(connection, STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        present = self._resolver.has(
            connection.private_key_secret_reference,
            tenant_id=connection.tenant_id,
            customer_app_id=connection.customer_app_id,
        )
        if not present:
            return _result(connection, STATUS_CREDENTIAL_MISSING, "CREDENTIAL_MISSING")
        if not live_apple_testflight_enabled():
            payload = _result(connection, STATUS_NOT_CONFIGURED, "LIVE_APPLE_PROOF_BLOCKED_EXTERNAL")
            payload["live_proof"] = "LIVE_APPLE_PROOF_BLOCKED_EXTERNAL"
            payload["LIVE_APPLE_PROOF"] = BLOCKED_EXTERNAL
            return payload
        payload = _result(connection, STATUS_NOT_CONFIGURED, "LIVE_APPLE_PROOF_BLOCKED_EXTERNAL")
        payload["live_proof"] = "LIVE_APPLE_PROOF_BLOCKED_EXTERNAL"
        payload["LIVE_APPLE_PROOF"] = BLOCKED_EXTERNAL
        payload["notes"] = [
            "Live App Store Connect JWT auth is not wired in this workspace.",
        ]
        return payload

    def lookup_app(self, bundle_identifier: str) -> dict[str, Any]:
        del bundle_identifier
        return {"status": STATUS_APP_RECORD_REQUIRED, "LIVE_APPLE_PROOF": BLOCKED_EXTERNAL}

    def upload_build(
        self,
        bundle_identifier: str,
        *,
        ipa_sha256: str,
        build_number: int,
        destination: str = "testflight",
    ) -> dict[str, Any]:
        del bundle_identifier, ipa_sha256, build_number
        if destination.strip().lower() in {"production", "app_store", "appstore", "review"}:
            raise AppStoreProductionSubmissionBlocked(APP_STORE_PRODUCTION_SUBMISSION_BLOCKED)
        raise AppleConnectionError("LIVE_APPLE_PROOF_BLOCKED_EXTERNAL")


def _result(
    connection: ApplePublisherConnection,
    status: str,
    error: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "status": status,
        "last_error_code": error,
        "last_verified_at": stamp_now() if status == STATUS_READY else "",
        "principal_reference": connection.issuer_reference,
        "publisher_owner_type": connection.owner_type,
        "bundle_identifier": connection.bundle_identifier,
        "customer_owned_publishing_proven": False,
        "role_status": status,
        "EXTRA_PERMISSION_PRESENT": bool((extra or {}).get("EXTRA_PERMISSION_PRESENT")),
    }
    if extra:
        payload.update(extra)
    return payload
