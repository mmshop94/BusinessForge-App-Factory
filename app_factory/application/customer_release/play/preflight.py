"""Google Play live preflight — LIVE_INTERNAL_UPLOAD_READY or concrete blockers. No secrets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.play import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    STATUS_READY,
    VALID_OWNER_TYPES,
    GooglePlayPublisherConnection,
)
from app_factory.application.customer_release.play.approval import ApprovalRegistry
from app_factory.application.customer_release.play.provider import (
    PRODUCTION_SUBMISSION_BLOCKED,
    TRACK_INTERNAL,
    TRACK_PRODUCTION,
    PublisherProvider,
    assert_test_track,
)
from app_factory.application.customer_release.play.setup_contract import evaluate_setup_states
from app_factory.application.customer_release.play.testers import (
    TESTER_GROUP_NOT_CONFIGURED,
    InternalTesterGroupReference,
)
from app_factory.application.customer_release.play.versioning import resolve_play_version_code
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.customer_release.signing import (
    SecretReferenceResolver,
    looks_like_shared_owner_reference,
)
from app_factory.domain.errors import ProductionSubmissionBlocked
from app_factory.application.package_identity import validate_android_package_format

LIVE_INTERNAL_UPLOAD_READY = "LIVE_INTERNAL_UPLOAD_READY"
BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"
BLOCKED = "BLOCKED"


@dataclass
class PlayPreflightInput:
    profile: CustomerAppReleaseProfile
    snapshot_id: str
    snapshot_immutable: bool
    connection: GooglePlayPublisherConnection
    resolver: SecretReferenceResolver
    provider: PublisherProvider
    approvals: ApprovalRegistry
    identity: CustomerAppIdentityRegistry
    upload_key_reference: str
    aab_path: Path | None = None
    aab_sha256: str = ""
    upload_certificate_sha256: str = ""
    google_known_version: int | None = None
    track: str = TRACK_INTERNAL
    tester: InternalTesterGroupReference | None = None
    setup_states: dict[str, str] = field(default_factory=dict)


def run_preflight(inp: PlayPreflightInput) -> dict[str, Any]:
    blockers: list[str] = []
    notes: list[str] = []

    if inp.track.strip().lower() == TRACK_PRODUCTION:
        return {
            "status": PRODUCTION_SUBMISSION_BLOCKED,
            "live_internal_upload_ready": False,
            "blockers": [PRODUCTION_SUBMISSION_BLOCKED],
            "api_write_executed": False,
            "android_production_ready": "NOT_IMPLEMENTED",
        }

    try:
        assert_test_track(inp.track)
    except ProductionSubmissionBlocked:
        return {
            "status": PRODUCTION_SUBMISSION_BLOCKED,
            "live_internal_upload_ready": False,
            "blockers": [PRODUCTION_SUBMISSION_BLOCKED],
            "api_write_executed": False,
            "android_production_ready": "NOT_IMPLEMENTED",
        }

    if not inp.snapshot_immutable or not inp.snapshot_id:
        blockers.append("SNAPSHOT_CHANGED")
    if inp.profile.release_snapshot_id and inp.profile.release_snapshot_id != inp.snapshot_id:
        blockers.append("SNAPSHOT_CHANGED")

    android_on = inp.profile.platforms.value in {"ANDROID_ONLY", "ANDROID_AND_IOS"}
    if not android_on:
        blockers.append("ANDROID_NOT_SUBSCRIBED")

    try:
        package = validate_android_package_format(inp.profile.package_name)
    except Exception:
        package = inp.profile.package_name
        blockers.append("PACKAGE_INVALID")

    record = inp.identity.get(inp.profile.app_id)
    package_frozen = bool(record and (record.package_immutable or record.published))
    if record and record.package_name_android != package:
        blockers.append("PACKAGE_ID_MISMATCH")
    if not package_frozen:
        blockers.append("PACKAGE_NOT_FROZEN")

    if inp.connection.owner_type not in VALID_OWNER_TYPES:
        blockers.append("PUBLISHER_OWNER_TYPE_MISSING")
    if inp.connection.owner_type not in {OWNER_CUSTOMER, OWNER_REFERENCE}:
        blockers.append("PUBLISHER_OWNER_TYPE_MISSING")

    try:
        inp.connection.assert_bound(
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
            package_name=package,
        )
    except Exception:
        blockers.append("CONNECTION_TENANT_MISMATCH")

    if not inp.connection.credential_secret_reference:
        blockers.append("PUBLISHER_CREDENTIAL_MISSING")
    else:
        present = inp.resolver.has(
            inp.connection.credential_secret_reference,
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
        )
        if not present:
            blockers.append("PUBLISHER_CREDENTIAL_MISSING")

    if not inp.upload_key_reference:
        blockers.append("UPLOAD_KEY_MISSING")
    elif looks_like_shared_owner_reference(inp.upload_key_reference):
        blockers.append("SHARED_OWNER_KEYSTORE_FORBIDDEN")
    else:
        if not inp.resolver.has(
            inp.upload_key_reference,
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
        ):
            blockers.append("UPLOAD_KEY_MISSING")

    if inp.aab_path is None or not Path(inp.aab_path).is_file():
        if not inp.aab_sha256:
            blockers.append("AAB_MISSING")
    if inp.upload_certificate_sha256:
        notes.append("AAB_SIGNING_FINGERPRINT_PRESENT")
    elif inp.aab_sha256:
        blockers.append("WRONG_SIGNING_CERTIFICATE")

    version = resolve_play_version_code(
        built=inp.profile.version_code,
        google_known=inp.google_known_version,
    )
    if inp.google_known_version and int(inp.google_known_version) == int(inp.profile.version_code):
        if version <= int(inp.google_known_version):
            blockers.append("DUPLICATE_VERSION_CODE")

    try:
        inp.approvals.require_approved(
            tenant_id=inp.profile.tenant_id,
            customer_app_id=inp.profile.app_id,
            package_name=package,
            release_id=inp.profile.release_id,
            snapshot_id=inp.snapshot_id,
        )
    except Exception as exc:
        blockers.append(str(exc) or "RELEASE_APPROVAL_STALE")

    setup = evaluate_setup_states(inp.setup_states) if inp.setup_states else None

    verification = inp.provider.verify_connection(
        inp.connection, expected_package=package
    )
    verify_status = str(verification.get("status") or "")
    live_proof = str(verification.get("live_proof") or "")
    if live_proof == "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL" or verify_status in {
        "NOT_CONFIGURED",
    }:
        # External account not wired — not a silent PASS and not a product FAIL.
        return {
            "status": BLOCKED_EXTERNAL,
            "live_internal_upload_ready": False,
            "live_google_play_proof": "BLOCKED_EXTERNAL",
            "blockers": blockers + ["LIVE_PLAY_PROOF_BLOCKED_EXTERNAL"],
            "verification": _public_verification(verification),
            "version_code": version,
            "package_name": package,
            "publisher_owner_type": inp.connection.owner_type,
            "customer_owned_publishing_proven": False,
            "setup": setup,
            "tester": (inp.tester.to_public_dict() if inp.tester else {"status": TESTER_GROUP_NOT_CONFIGURED}),
            "android_production_ready": "NOT_IMPLEMENTED",
            "notes": notes,
        }

    if verify_status != STATUS_READY:
        blockers.append(str(verification.get("last_error_code") or verify_status))

    extra = verification.get("excess_permissions_recorded_not_used") or []
    extra_present = bool(verification.get("EXTRA_PERMISSION_PRESENT") or extra)

    if blockers:
        return {
            "status": BLOCKED,
            "live_internal_upload_ready": False,
            "blockers": blockers,
            "verification": _public_verification(verification),
            "version_code": version,
            "package_name": package,
            "publisher_owner_type": inp.connection.owner_type,
            "customer_owned_publishing_proven": False,
            "extra_permission_present": extra_present,
            "setup": setup,
            "tester": (inp.tester.to_public_dict() if inp.tester else {"status": TESTER_GROUP_NOT_CONFIGURED}),
            "android_production_ready": "NOT_IMPLEMENTED",
            "notes": notes,
        }

    return {
        "status": LIVE_INTERNAL_UPLOAD_READY,
        "live_internal_upload_ready": True,
        "blockers": [],
        "verification": _public_verification(verification),
        "version_code": version,
        "package_name": package,
        "publisher_owner_type": inp.connection.owner_type,
        "customer_owned_publishing_proven": False,
        "extra_permission_present": extra_present,
        "setup": setup,
        "tester": (inp.tester.to_public_dict() if inp.tester else {"status": TESTER_GROUP_NOT_CONFIGURED}),
        "android_production_ready": "NOT_IMPLEMENTED",
        "notes": notes,
        "production_permission_used": False,
    }


def _public_verification(verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": verification.get("status"),
        "play_app": verification.get("play_app"),
        "last_error_code": verification.get("last_error_code"),
        "last_verified_at": verification.get("last_verified_at"),
        "permission_status": verification.get("permission_status"),
        "live_proof": verification.get("live_proof"),
        "access_result": verification.get("access_result") or verification.get("status"),
        "permission_result": verification.get("permission_status"),
        "principal_reference": verification.get("principal_reference"),
        "provider_response_id": verification.get("provider_response_id"),
        "EXTRA_PERMISSION_PRESENT": bool(
            verification.get("EXTRA_PERMISSION_PRESENT")
            or verification.get("excess_permissions_recorded_not_used")
        ),
        "production_permission_used": False,
    }
