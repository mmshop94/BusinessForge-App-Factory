"""Google Play publisher connection — app-scoped references, no credential values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app_factory.domain.errors import TenantIsolationError

SCOPE_APP = "APP_SCOPED"

REQUIRED_TEST_PERMISSIONS = frozenset(
    {
        "VIEW_APP_INFORMATION",
        "MANAGE_TEST_RELEASES",
    }
)
OPTIONAL_TEST_PERMISSIONS = frozenset(
    {
        "MANAGE_TESTERS",
        "MANAGE_STORE_LISTING",
    }
)
FORBIDDEN_PERMISSIONS = frozenset(
    {
        "PLAY_ADMIN",
        "ACCOUNT_WIDE_ADMIN",
        "FINANCIAL_DATA",
        "ORDER_MANAGEMENT",
        "PRODUCTION_RELEASE",
        "USER_PERMISSION_MANAGEMENT",
    }
)

STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"
STATUS_CREDENTIAL_MISSING = "CREDENTIAL_MISSING"
STATUS_AUTH_FAILED = "AUTH_FAILED"
STATUS_APP_NOT_FOUND = "APP_NOT_FOUND"
STATUS_ACCESS_DENIED = "ACCESS_DENIED"
STATUS_PERMISSION_INCOMPLETE = "PERMISSION_INCOMPLETE"
STATUS_PLAY_APP_SETUP_REQUIRED = "PLAY_APP_SETUP_REQUIRED"
STATUS_PLAY_APP_BOUND = "PLAY_APP_BOUND"
STATUS_PACKAGE_ID_MISMATCH = "PACKAGE_ID_MISMATCH"
STATUS_READY = "READY"
STATUS_REVOKED = "REVOKED"
STATUS_PLAY_POLICY_REQUIREMENT_PENDING = "PLAY_POLICY_REQUIREMENT_PENDING"


@dataclass(frozen=True)
class GooglePlayPublisherConnection:
    customer_app_id: str
    tenant_id: str
    package_name: str
    developer_account_reference: str
    principal_reference: str
    credential_secret_reference: str
    scope: str = SCOPE_APP
    permissions: tuple[str, ...] = ()
    connection_status: str = STATUS_NOT_CONFIGURED
    permission_status: str = STATUS_NOT_CONFIGURED
    last_verified_at: str = ""
    last_error_code: str = ""
    created_at: str = ""
    updated_at: str = ""

    def assert_bound(self, *, tenant_id: str, customer_app_id: str, package_name: str) -> None:
        if (
            self.tenant_id != tenant_id
            or self.customer_app_id != customer_app_id
            or self.package_name != package_name
        ):
            raise TenantIsolationError("Publisher connection is bound to a different customer app")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "customer_app_id": self.customer_app_id,
            "tenant_id": self.tenant_id,
            "package_name": self.package_name,
            "developer_account_reference": self.developer_account_reference,
            "principal_reference": self.principal_reference,
            "credential_secret_reference": self.credential_secret_reference,
            "scope": self.scope,
            "permissions": list(self.permissions),
            "connection_status": self.connection_status,
            "permission_status": self.permission_status,
            "last_verified_at": self.last_verified_at,
            "last_error_code": self.last_error_code,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def classify_permissions(granted: list[str] | tuple[str, ...]) -> dict[str, Any]:
    granted_set = {item.strip().upper() for item in granted if item.strip()}
    required_missing = sorted(REQUIRED_TEST_PERMISSIONS - granted_set)
    optional_present = sorted(OPTIONAL_TEST_PERMISSIONS & granted_set)
    forbidden_present = sorted(FORBIDDEN_PERMISSIONS & granted_set)
    usable = sorted(granted_set - FORBIDDEN_PERMISSIONS)
    ready = not required_missing
    return {
        "required_missing": required_missing,
        "optional_present": optional_present,
        "excess_forbidden": forbidden_present,
        "usable": usable,
        "production_permission_required": False,
        "production_permission_present": "PRODUCTION_RELEASE" in granted_set,
        "production_permission_used": False,
        "ready_for_internal_track": ready,
    }


def stamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()
