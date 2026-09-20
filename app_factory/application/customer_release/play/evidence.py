"""Non-sensitive Google Play internal live-proof serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.play import OWNER_REFERENCE, stamp_now
from app_factory.application.customer_release.play.setup_contract import owner_type_claims
from app_factory.domain.errors import PlayConnectionError

EVIDENCE_KIND = "GOOGLE_PLAY_INTERNAL_LIVE_PROOF_V1"
EVIDENCE_FILENAME = "GOOGLE_PLAY_INTERNAL_LIVE_PROOF_V1.json"

_SECRET_MARKERS = (
    "-----begin",
    "private_key",
    "client_secret",
    "refresh_token",
    "password=",
    "password",
    '"type": "service_account"',
    "service_account",
    "token",
    "-----BEGIN",
)


def serialize_internal_live_proof(
    *,
    release_id: str,
    snapshot_id: str,
    publisher_owner_type: str,
    package_name: str,
    version_code: int,
    version_name: str,
    aab_sha256: str,
    upload_certificate_sha256: str,
    target_track: str,
    google_edit_reference: str,
    google_bundle_version_code: int,
    commit_result: str,
    readback_result: str,
    verification_timestamp: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claims = owner_type_claims(
        publisher_owner_type,
        live_internal_proven=readback_result == "PLAY_INTERNAL_RELEASE_VERIFIED",
    )
    payload: dict[str, Any] = {
        "kind": EVIDENCE_KIND,
        "release_id": release_id,
        "snapshot_id": snapshot_id,
        "publisher_owner_type": publisher_owner_type,
        "package_name": package_name,
        "version_code": int(version_code),
        "version_name": version_name,
        "aab_sha256": aab_sha256,
        "upload_certificate_sha256": upload_certificate_sha256,
        "target_track": target_track,
        "google_edit_reference": google_edit_reference,
        "google_bundle_version_code": int(google_bundle_version_code),
        "commit_result": commit_result,
        "readback_result": readback_result,
        "verification_timestamp": verification_timestamp or stamp_now(),
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": claims["REFERENCE_PUBLISHER_LIVE_PROOF"],
        "android_production_ready": "NOT_IMPLEMENTED",
        "installation_proof": extra.get("installation_proof", "INSTALLATION_PROOF_NOT_RUN")
        if extra
        else "INSTALLATION_PROOF_NOT_RUN",
    }
    if extra:
        if extra.get("CUSTOMER_OWNED_PUBLISHING_PROVEN") is True:
            raise PlayConnectionError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
        for key, value in extra.items():
            if key in payload:
                continue
            payload[key] = value
    _assert_public(payload)
    if payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is True:
        raise PlayConnectionError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
    if publisher_owner_type == OWNER_REFERENCE and payload.get("CUSTOMER_OWNED_PUBLISHING_PROVEN"):
        raise PlayConnectionError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
    return payload


def write_internal_live_proof(path: Path, payload: dict[str, Any]) -> Path:
    _assert_public(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _assert_public(payload: dict[str, Any]) -> None:
    blob = json.dumps(payload).lower()
    for marker in _SECRET_MARKERS:
        if marker.lower() in blob and marker.lower() not in {
            # Public evidence field names may contain "token" as substring of "timestamp".
            "token",
        }:
            if marker.lower() == "token" and "timestamp" in blob and "refresh_token" not in blob:
                continue
            raise PlayConnectionError("Live evidence leaked a credential")
    # Explicit forbidden keys.
    for key in payload:
        lowered = str(key).lower()
        if lowered in {"credentials", "private_key", "password", "refresh_token", "client_secret"}:
            raise PlayConnectionError("Live evidence leaked a credential")
