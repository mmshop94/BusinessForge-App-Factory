"""TestFlight delivery foundation. Production / App Review is a hard block."""

from __future__ import annotations

from typing import Any

from app_factory.application.customer_release.apple import ApplePublisherConnection
from app_factory.application.customer_release.apple.approval import AppleApprovalRegistry
from app_factory.application.customer_release.apple.provider import (
    APP_STORE_PRODUCTION_SUBMISSION_BLOCKED,
    ApplePublisherProvider,
)
from app_factory.domain.errors import AppStoreProductionSubmissionBlocked

TESTFLIGHT_UPLOAD_READY = "TESTFLIGHT_UPLOAD_READY"
TESTFLIGHT_UPLOAD_IN_PROGRESS = "TESTFLIGHT_UPLOAD_IN_PROGRESS"
APPLE_BUILD_PROCESSING = "APPLE_BUILD_PROCESSING"
TESTFLIGHT_BUILD_AVAILABLE = "TESTFLIGHT_BUILD_AVAILABLE"
TESTFLIGHT_RELEASE_READY = "TESTFLIGHT_RELEASE_READY"


def deliver_testflight(
    *,
    provider: ApplePublisherProvider,
    connection: ApplePublisherConnection,
    expected_bundle: str,
    build_number: int,
    ipa_sha256: str,
    snapshot_id: str,
    release_id: str,
    tenant_id: str,
    customer_app_id: str,
    approvals: AppleApprovalRegistry,
    destination: str = "testflight",
) -> dict[str, Any]:
    if destination.strip().lower() in {"production", "app_store", "appstore", "review"}:
        raise AppStoreProductionSubmissionBlocked(APP_STORE_PRODUCTION_SUBMISSION_BLOCKED)
    connection.assert_bound(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        bundle_identifier=expected_bundle,
    )
    approvals.require_approved(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        bundle_identifier=expected_bundle,
        release_id=release_id,
        snapshot_id=snapshot_id,
    )
    verify = provider.verify_connection(connection, expected_bundle=expected_bundle)
    uploaded = provider.upload_build(
        expected_bundle,
        ipa_sha256=ipa_sha256,
        build_number=build_number,
        destination="testflight",
    )
    return {
        "status": TESTFLIGHT_UPLOAD_IN_PROGRESS,
        "readback_result": uploaded.get("status"),
        "bundle_identifier": expected_bundle,
        "build_number": build_number,
        "ipa_sha256": ipa_sha256,
        "snapshot_id": snapshot_id,
        "release_id": release_id,
        "publisher_owner_type": connection.owner_type,
        "customer_owned_publishing_proven": False,
        "app_store_production_ready": "NOT_IMPLEMENTED",
        "verification": {
            "status": verify.get("status"),
            "principal_reference": verify.get("principal_reference"),
        },
    }
