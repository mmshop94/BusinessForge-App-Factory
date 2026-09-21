"""Apple TestFlight preflight. LIVE_APPLE_PROOF stays BLOCKED_EXTERNAL without credentials."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.apple import (
    STATUS_NOT_CONFIGURED,
    STATUS_READY,
    ApplePublisherConnection,
)
from app_factory.application.customer_release.apple.approval import AppleApprovalRegistry
from app_factory.application.customer_release.apple.executor import (
    IOS_BUILD_EXECUTOR_REQUIRED,
    probe_ios_build_executor,
)
from app_factory.application.customer_release.apple.provider import (
    APP_STORE_PRODUCTION_SUBMISSION_BLOCKED,
    ApplePublisherProvider,
)
from app_factory.application.customer_release.apple.setup_contract import evaluate_setup_states
from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.play import OWNER_CUSTOMER, OWNER_REFERENCE, VALID_OWNER_TYPES
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.customer_release.signing import SecretReferenceResolver
from app_factory.domain.errors import AppStoreProductionSubmissionBlocked

TESTFLIGHT_UPLOAD_READY = "TESTFLIGHT_UPLOAD_READY"
BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
BLOCKED = "BLOCKED"


@dataclass
class ApplePreflightInput:
    profile: CustomerAppReleaseProfile
    snapshot_id: str
    snapshot_immutable: bool
    connection: ApplePublisherConnection
    resolver: SecretReferenceResolver
    provider: ApplePublisherProvider
    approvals: AppleApprovalRegistry
    identity: CustomerAppIdentityRegistry
    ipa_sha256: str = ""
    destination: str = "testflight"
    setup_states: dict[str, str] = field(default_factory=dict)


def run_preflight(inp: ApplePreflightInput) -> dict[str, Any]:
    dest = inp.destination.strip().lower()
    if dest in {"production", "app_store", "appstore", "review"}:
        return {
            "status": APP_STORE_PRODUCTION_SUBMISSION_BLOCKED,
            "testflight_upload_ready": False,
            "api_write_executed": False,
            "app_store_production_ready": "NOT_IMPLEMENTED",
            "blockers": [APP_STORE_PRODUCTION_SUBMISSION_BLOCKED],
        }

    blockers: list[str] = []
    if not inp.snapshot_immutable or not inp.snapshot_id:
        blockers.append("SNAPSHOT_CHANGED")

    bundle = inp.profile.bundle_identifier
    try:
        inp.connection.assert_bound(
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
            bundle_identifier=bundle,
        )
    except Exception:
        blockers.append("CONNECTION_TENANT_MISMATCH")

    if inp.connection.owner_type not in VALID_OWNER_TYPES:
        blockers.append("PUBLISHER_OWNER_TYPE_MISSING")

    record = inp.identity.get(inp.profile.app_id)
    if record and record.bundle_identifier != bundle:
        blockers.append("APPLE_BUNDLE_ID_MISMATCH")
    if record and not record.bundle_immutable:
        blockers.append("BUNDLE_NOT_FROZEN")

    executor = probe_ios_build_executor()
    if executor["status"] == IOS_BUILD_EXECUTOR_REQUIRED:
        blockers.append(IOS_BUILD_EXECUTOR_REQUIRED)

    if not inp.ipa_sha256:
        blockers.append("IPA_MISSING")

    try:
        inp.approvals.require_approved(
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
            bundle_identifier=bundle,
            release_id=inp.profile.release_id,
            snapshot_id=inp.snapshot_id,
        )
    except Exception as exc:
        blockers.append(str(exc) or "RELEASE_APPROVAL_STALE")

    verification = inp.provider.verify_connection(
        inp.connection, expected_bundle=bundle
    )
    live_proof = str(verification.get("live_proof") or verification.get("LIVE_APPLE_PROOF") or "")
    if live_proof in {"LIVE_APPLE_PROOF_BLOCKED_EXTERNAL", BLOCKED_EXTERNAL} or verification.get(
        "status"
    ) == STATUS_NOT_CONFIGURED:
        return {
            "status": BLOCKED_EXTERNAL,
            "testflight_upload_ready": False,
            "live_apple_proof": BLOCKED_EXTERNAL,
            "blockers": blockers + ["LIVE_APPLE_PROOF_BLOCKED_EXTERNAL"],
            "executor": executor,
            "verification": {
                "status": verification.get("status"),
                "principal_reference": verification.get("principal_reference"),
                "permission_result": verification.get("role_status"),
            },
            "publisher_owner_type": inp.connection.owner_type,
            "customer_owned_publishing_proven": False,
            "app_store_production_ready": "NOT_IMPLEMENTED",
            "setup": evaluate_setup_states(inp.setup_states) if inp.setup_states else None,
        }

    if verification.get("status") != STATUS_READY:
        blockers.append(str(verification.get("last_error_code") or verification.get("status")))

    if blockers:
        return {
            "status": BLOCKED,
            "testflight_upload_ready": False,
            "blockers": blockers,
            "executor": executor,
            "publisher_owner_type": inp.connection.owner_type,
            "customer_owned_publishing_proven": False,
            "app_store_production_ready": "NOT_IMPLEMENTED",
        }

    return {
        "status": TESTFLIGHT_UPLOAD_READY,
        "testflight_upload_ready": True,
        "blockers": [],
        "executor": executor,
        "publisher_owner_type": inp.connection.owner_type,
        "customer_owned_publishing_proven": False,
        "app_store_production_ready": "NOT_IMPLEMENTED",
        "reference_publisher": inp.connection.owner_type == OWNER_REFERENCE,
        "allowed_customer_owned": inp.connection.owner_type == OWNER_CUSTOMER,
    }
