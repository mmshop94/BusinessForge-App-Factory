"""Internal test-track delivery — no production writes, idempotent per edit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_factory.application.customer_release.play import (
    STATUS_PACKAGE_ID_MISMATCH,
    STATUS_READY,
    GooglePlayPublisherConnection,
)
from app_factory.application.customer_release.play.approval import (
    TEST_RELEASE_AVAILABLE,
    TEST_UPLOAD_IN_PROGRESS,
    ApprovalRegistry,
)
from app_factory.application.customer_release.play.provider import (
    PRODUCTION_SUBMISSION_BLOCKED,
    TRACK_INTERNAL,
    PublisherProvider,
    assert_test_track,
)
from app_factory.domain.errors import PlayConnectionError, PlayDeliveryError, ProductionSubmissionBlocked

ANDROID_PRODUCTION_READY = "NOT_IMPLEMENTED"
PLAY_INTERNAL_RELEASE_VERIFIED = "PLAY_INTERNAL_RELEASE_VERIFIED"
PLAY_RELEASE_READBACK_MISMATCH = "PLAY_RELEASE_READBACK_MISMATCH"
INSTALLATION_PROOF_NOT_RUN = "INSTALLATION_PROOF_NOT_RUN"


def deliver_internal_test_track(
    *,
    provider: PublisherProvider,
    connection: GooglePlayPublisherConnection,
    expected_package: str,
    version_code: int,
    aab_sha256: str,
    snapshot_id: str,
    release_id: str,
    tenant_id: str,
    customer_app_id: str,
    approvals: ApprovalRegistry,
    track: str = TRACK_INTERNAL,
    aab_path: str | Path | None = None,
    upload_certificate_sha256: str = "",
    version_name: str = "",
) -> dict[str, Any]:
    """verify → edit → upload → track → validate → commit → read-back. Never production."""
    connection.assert_bound(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        package_name=expected_package,
    )
    try:
        normalized = assert_test_track(track)
    except ProductionSubmissionBlocked:
        return _blocked_production()

    if normalized != TRACK_INTERNAL:
        # CLOSED is modelled but Internal is the proven first track.
        if normalized != "closed":
            raise PlayConnectionError(f"UNSUPPORTED_TRACK:{track}")

    verification = provider.verify_connection(connection, expected_package=expected_package)
    if verification.get("status") != STATUS_READY:
        if verification.get("status") == STATUS_PACKAGE_ID_MISMATCH:
            raise PlayConnectionError("PACKAGE_ID_MISMATCH")
        raise PlayConnectionError(str(verification.get("last_error_code") or verification.get("status")))

    approvals.require_approved(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        package_name=expected_package,
        release_id=release_id,
        snapshot_id=snapshot_id,
    )

    edit_id = provider.create_edit(expected_package)
    uploaded = provider.upload_bundle(
        expected_package,
        edit_id,
        aab_sha256=aab_sha256,
        version_code=version_code,
        aab_path=aab_path,
        upload_certificate_sha256=upload_certificate_sha256,
    )
    if int(uploaded["version_code"]) != int(version_code):
        raise PlayConnectionError("WRONG_VERSION_CODE")
    provider.configure_track(
        expected_package,
        edit_id,
        track=TRACK_INTERNAL,
        version_code=version_code,
    )
    validation = provider.validate_edit(expected_package, edit_id)
    committed = provider.commit_edit(expected_package, edit_id)
    read_back = provider.read_track(expected_package, TRACK_INTERNAL)
    readback_result = _compare_readback(
        read_back,
        expected_package=expected_package,
        version_code=version_code,
    )
    if readback_result == PLAY_RELEASE_READBACK_MISMATCH:
        raise PlayDeliveryError(PLAY_RELEASE_READBACK_MISMATCH)

    approvals.consume_for_upload(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        package_name=expected_package,
        release_id=release_id,
        snapshot_id=snapshot_id,
    )

    google_play = {
        "connection_reference": connection.principal_reference,
        "package_name": expected_package,
        "target_track": TRACK_INTERNAL,
        "edit_reference": edit_id,
        "version_code": version_code,
        "version_name": version_name,
        "bundle_sha256": aab_sha256,
        "upload_certificate_sha256": upload_certificate_sha256,
        "upload_status": "UPLOADED",
        "validation_status": validation.get("status"),
        "commit_status": committed.get("status"),
        "release_status": read_back.get("status"),
        "google_bundle_version_code": int(
            read_back.get("bundle_version_code") or read_back.get("version_code") or version_code
        ),
        "readback_result": PLAY_INTERNAL_RELEASE_VERIFIED,
        "verified_at": verification.get("last_verified_at"),
        "snapshot_id": snapshot_id,
        "release_id": release_id,
        "approval": TEST_RELEASE_AVAILABLE,
        "android_production_ready": ANDROID_PRODUCTION_READY,
        "publisher_owner_type": connection.owner_type,
        "customer_owned_publishing_proven": False,
        "installation_proof": INSTALLATION_PROOF_NOT_RUN,
        "tester_opt_in_url": read_back.get("tester_opt_in_url")
        or verification.get("tester_opt_in_url")
        or "",
    }
    if not google_play["tester_opt_in_url"]:
        google_play.pop("tester_opt_in_url")
    _assert_public(google_play)
    return {
        "status": TEST_RELEASE_AVAILABLE,
        "android_test_released": True,
        "android_production_ready": ANDROID_PRODUCTION_READY,
        "google_play": google_play,
        "progress": TEST_UPLOAD_IN_PROGRESS,
        "verification": {
            "status": verification.get("status"),
            "excess_permissions_recorded_not_used": verification.get(
                "excess_permissions_recorded_not_used"
            )
            or [],
            "EXTRA_PERMISSION_PRESENT": bool(
                verification.get("EXTRA_PERMISSION_PRESENT")
                or verification.get("excess_permissions_recorded_not_used")
            ),
            "production_permission_used": False,
            "access_result": verification.get("access_result") or verification.get("status"),
            "permission_result": verification.get("permission_result")
            or verification.get("permission_status"),
            "principal_reference": connection.principal_reference,
            "provider_response_id": verification.get("provider_response_id"),
        },
    }


def _compare_readback(
    read_back: dict[str, Any],
    *,
    expected_package: str,
    version_code: int,
) -> str:
    got_package = str(read_back.get("package_name") or "")
    got_track = str(read_back.get("track") or "")
    got_version = int(read_back.get("version_code") or 0)
    if (
        got_package != expected_package
        or got_track != TRACK_INTERNAL
        or got_version != int(version_code)
        or not read_back.get("status")
    ):
        return PLAY_RELEASE_READBACK_MISMATCH
    return PLAY_INTERNAL_RELEASE_VERIFIED


def _blocked_production() -> dict[str, Any]:
    return {
        "status": PRODUCTION_SUBMISSION_BLOCKED,
        "android_production_ready": ANDROID_PRODUCTION_READY,
        "google_play": None,
        "api_write_executed": False,
    }


def _assert_public(payload: dict[str, Any]) -> None:
    blob = str(payload).lower()
    for marker in ("-----begin", "private_key", "client_secret", "refresh_token", "password="):
        if marker in blob:
            raise PlayConnectionError("Delivery manifest leaked a credential")
