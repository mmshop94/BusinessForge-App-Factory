"""App Store Connect publisher connection — app-scoped references, no credential values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app_factory.application.customer_release.play import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    VALID_OWNER_TYPES,
)
from app_factory.domain.errors import TenantIsolationError

SCOPE_APP = "APP_SCOPED"

REQUIRED_TESTFLIGHT_PERMISSIONS = frozenset(
    {
        "APP_MANAGER",
        "CLOUD_MANAGED_APP_DISTRIBUTION",
    }
)
OPTIONAL_TESTFLIGHT_PERMISSIONS = frozenset(
    {
        "CREATE_APPS",
        "CUSTOMER_SUPPORT",
    }
)
FORBIDDEN_PERMISSIONS = frozenset(
    {
        "ACCOUNT_HOLDER",
        "ADMIN",
        "FINANCE",
        "ACCESS_TO_REPORTS",
        "SALES",
    }
)

STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"
STATUS_CREDENTIAL_MISSING = "CREDENTIAL_MISSING"
STATUS_AUTH_FAILED = "AUTH_FAILED"
STATUS_APP_NOT_FOUND = "APP_NOT_FOUND"
STATUS_ACCESS_DENIED = "ACCESS_DENIED"
STATUS_PERMISSION_INCOMPLETE = "PERMISSION_INCOMPLETE"
STATUS_APP_RECORD_REQUIRED = "APP_STORE_APP_RECORD_REQUIRED"
STATUS_APP_BOUND = "APP_STORE_APP_BOUND"
STATUS_BUNDLE_ID_MISMATCH = "APPLE_BUNDLE_ID_MISMATCH"
STATUS_READY = "READY"
STATUS_REVOKED = "REVOKED"
STATUS_AGREEMENT_PENDING = "AGREEMENTS_PENDING"


@dataclass(frozen=True)
class ApplePublisherConnection:
    customer_app_id: str
    tenant_id: str
    bundle_identifier: str
    team_id_reference: str
    issuer_reference: str
    key_id_reference: str
    private_key_secret_reference: str
    scope: str = SCOPE_APP
    permissions: tuple[str, ...] = ()
    connection_status: str = STATUS_NOT_CONFIGURED
    role_status: str = STATUS_NOT_CONFIGURED
    last_verified_at: str = ""
    last_error_code: str = ""
    created_at: str = ""
    updated_at: str = ""
    owner_type: str = OWNER_CUSTOMER
    sku_reference: str = ""

    def __post_init__(self) -> None:
        if self.owner_type not in VALID_OWNER_TYPES:
            raise TenantIsolationError("INVALID_PUBLISHER_OWNER_TYPE")

    def assert_bound(self, *, tenant_id: str, customer_app_id: str, bundle_identifier: str) -> None:
        if (
            self.tenant_id != tenant_id
            or self.customer_app_id != customer_app_id
            or self.bundle_identifier != bundle_identifier
        ):
            raise TenantIsolationError("Apple connection is bound to a different customer app")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "customer_app_id": self.customer_app_id,
            "tenant_id": self.tenant_id,
            "bundle_identifier": self.bundle_identifier,
            "team_id_reference": self.team_id_reference,
            "issuer_reference": self.issuer_reference,
            "key_id_reference": self.key_id_reference,
            "private_key_secret_reference": self.private_key_secret_reference,
            "sku_reference": self.sku_reference,
            "scope": self.scope,
            "permissions": list(self.permissions),
            "connection_status": self.connection_status,
            "role_status": self.role_status,
            "last_verified_at": self.last_verified_at,
            "last_error_code": self.last_error_code,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "publisher_owner_type": self.owner_type,
            "customer_owned_publishing_proven": False,
            "reference_publisher": self.owner_type == OWNER_REFERENCE,
        }


def classify_apple_permissions(granted: list[str] | tuple[str, ...]) -> dict[str, Any]:
    granted_set = {item.strip().upper() for item in granted if item.strip()}
    required_missing = sorted(REQUIRED_TESTFLIGHT_PERMISSIONS - granted_set)
    optional_present = sorted(OPTIONAL_TESTFLIGHT_PERMISSIONS & granted_set)
    forbidden_present = sorted(FORBIDDEN_PERMISSIONS & granted_set)
    return {
        "required_missing": required_missing,
        "optional_present": optional_present,
        "excess_forbidden": forbidden_present,
        "EXTRA_PERMISSION_PRESENT": bool(forbidden_present),
        "production_permission_used": False,
        "account_holder_required": False,
        "ready_for_testflight": not required_missing,
    }


def stamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()
