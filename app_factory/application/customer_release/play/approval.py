"""Test-upload approval is bound to one release_id + snapshot_id. Not reusable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app_factory.application.customer_release.play import stamp_now
from app_factory.domain.errors import ApprovalError, TenantIsolationError

BUILD_READY = "BUILD_READY"
TEST_UPLOAD_APPROVED = "TEST_UPLOAD_APPROVED"
TEST_UPLOAD_IN_PROGRESS = "TEST_UPLOAD_IN_PROGRESS"
TEST_RELEASE_AVAILABLE = "TEST_RELEASE_AVAILABLE"
PENDING = "PENDING"
APPROVED = "APPROVED"
CONSUMED = "CONSUMED"
REVOKED = "REVOKED"


@dataclass
class TestUploadApproval:
    tenant_id: str
    customer_app_id: str
    package_name: str
    release_id: str
    snapshot_id: str
    status: str = PENDING
    approved_at: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "customer_app_id": self.customer_app_id,
            "package_name": self.package_name,
            "release_id": self.release_id,
            "snapshot_id": self.snapshot_id,
            "status": self.status,
            "approved_at": self.approved_at,
            "kind": "TEST_UPLOAD",
            "production_approval": False,
        }


class ApprovalRegistry:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], TestUploadApproval] = {}

    def approve(
        self,
        *,
        tenant_id: str,
        customer_app_id: str,
        package_name: str,
        release_id: str,
        snapshot_id: str,
    ) -> TestUploadApproval:
        key = (customer_app_id, release_id)
        item = TestUploadApproval(
            tenant_id=tenant_id,
            customer_app_id=customer_app_id,
            package_name=package_name,
            release_id=release_id,
            snapshot_id=snapshot_id,
            status=APPROVED,
            approved_at=stamp_now(),
        )
        self._items[key] = item
        return item

    def require_approved(
        self,
        *,
        tenant_id: str,
        customer_app_id: str,
        package_name: str,
        release_id: str,
        snapshot_id: str,
    ) -> TestUploadApproval:
        item = self._items.get((customer_app_id, release_id))
        if item is None or item.status not in {APPROVED, CONSUMED}:
            raise ApprovalError("TEST_UPLOAD_NOT_APPROVED")
        if item.status == CONSUMED:
            # Idempotent retry of the same snapshot after a successful commit is allowed
            # only when the caller is re-reading, not uploading again — upload path
            # must see APPROVED.
            raise ApprovalError("TEST_UPLOAD_ALREADY_CONSUMED")
        if item.tenant_id != tenant_id or item.package_name != package_name:
            raise TenantIsolationError("Approval bound to a different tenant or package")
        if item.snapshot_id != snapshot_id:
            raise ApprovalError("SNAPSHOT_CHANGED_AFTER_APPROVAL")
        return item

    def consume_for_upload(
        self,
        *,
        tenant_id: str,
        customer_app_id: str,
        package_name: str,
        release_id: str,
        snapshot_id: str,
    ) -> TestUploadApproval:
        item = self.require_approved(
            tenant_id=tenant_id,
            customer_app_id=customer_app_id,
            package_name=package_name,
            release_id=release_id,
            snapshot_id=snapshot_id,
        )
        item.status = CONSUMED
        return item
