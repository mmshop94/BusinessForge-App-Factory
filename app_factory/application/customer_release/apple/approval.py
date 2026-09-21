"""TestFlight upload approval is bound to one release_id + snapshot_id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app_factory.application.customer_release.apple import stamp_now
from app_factory.domain.errors import ApprovalError, TenantIsolationError

PENDING = "PENDING"
APPROVED = "APPROVED"
CONSUMED = "CONSUMED"
TESTFLIGHT_UPLOAD_APPROVED = "TESTFLIGHT_UPLOAD_APPROVED"


@dataclass
class TestFlightUploadApproval:
    tenant_id: str
    customer_app_id: str
    bundle_identifier: str
    release_id: str
    snapshot_id: str
    status: str = PENDING
    approved_at: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "customer_app_id": self.customer_app_id,
            "bundle_identifier": self.bundle_identifier,
            "release_id": self.release_id,
            "snapshot_id": self.snapshot_id,
            "status": self.status,
            "approved_at": self.approved_at,
            "kind": "TESTFLIGHT_UPLOAD",
            "production_approval": False,
        }


class AppleApprovalRegistry:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], TestFlightUploadApproval] = {}

    def approve(
        self,
        *,
        tenant_id: str,
        customer_app_id: str,
        bundle_identifier: str,
        release_id: str,
        snapshot_id: str,
    ) -> TestFlightUploadApproval:
        item = TestFlightUploadApproval(
            tenant_id=tenant_id,
            customer_app_id=customer_app_id,
            bundle_identifier=bundle_identifier,
            release_id=release_id,
            snapshot_id=snapshot_id,
            status=APPROVED,
            approved_at=stamp_now(),
        )
        self._items[(customer_app_id, release_id)] = item
        return item

    def require_approved(
        self,
        *,
        tenant_id: str,
        customer_app_id: str,
        bundle_identifier: str,
        release_id: str,
        snapshot_id: str,
    ) -> TestFlightUploadApproval:
        item = self._items.get((customer_app_id, release_id))
        if item is None or item.status not in {APPROVED, CONSUMED}:
            raise ApprovalError("TESTFLIGHT_UPLOAD_NOT_APPROVED")
        if item.status == CONSUMED:
            raise ApprovalError("TESTFLIGHT_UPLOAD_ALREADY_CONSUMED")
        if item.tenant_id != tenant_id or item.bundle_identifier != bundle_identifier:
            raise TenantIsolationError("Approval bound to a different tenant or bundle")
        if item.snapshot_id != snapshot_id:
            raise ApprovalError("SNAPSHOT_CHANGED_AFTER_APPROVAL")
        return item
