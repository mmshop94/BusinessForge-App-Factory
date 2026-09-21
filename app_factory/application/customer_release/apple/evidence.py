"""Public Apple TestFlight evidence. No private keys or .p8/.p12 material."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.apple import stamp_now
from app_factory.application.customer_release.apple.setup_contract import owner_type_claims
from app_factory.application.customer_release.play import OWNER_REFERENCE
from app_factory.domain.errors import AppleConnectionError

_SECRET_MARKERS = (
    "-----begin",
    "private_key",
    "-----BEGIN",
    ".p8",
    ".p12",
    "client_secret",
    "refresh_token",
)


def serialize_testflight_proof(
    *,
    release_id: str,
    snapshot_id: str,
    publisher_owner_type: str,
    bundle_identifier: str,
    build_number: int,
    version_name: str,
    ipa_sha256: str,
    executor_type: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claims = owner_type_claims(
        publisher_owner_type,
        live_testflight_proven=False,
    )
    payload: dict[str, Any] = {
        "kind": "APPLE_TESTFLIGHT_PROOF_V1",
        "release_id": release_id,
        "snapshot_id": snapshot_id,
        "publisher_owner_type": publisher_owner_type,
        "bundle_identifier": bundle_identifier,
        "build_number": int(build_number),
        "version_name": version_name,
        "ipa_sha256": ipa_sha256,
        "executor_type": executor_type,
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": claims["REFERENCE_PUBLISHER_LIVE_PROOF"],
        "app_store_production_ready": "NOT_IMPLEMENTED",
        "verified_at": stamp_now(),
    }
    if extra:
        if extra.get("CUSTOMER_OWNED_PUBLISHING_PROVEN") is True:
            raise AppleConnectionError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
        for key, value in extra.items():
            if key not in payload:
                payload[key] = value
    _assert_public(payload)
    if publisher_owner_type == OWNER_REFERENCE and payload.get("CUSTOMER_OWNED_PUBLISHING_PROVEN"):
        raise AppleConnectionError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
    return payload


def write_public_evidence(path: Path, payload: dict[str, Any]) -> Path:
    _assert_public(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _assert_public(payload: dict[str, Any]) -> None:
    blob = json.dumps(payload).lower()
    for marker in _SECRET_MARKERS:
        if marker.lower() in blob:
            if marker.lower() == "token" and "timestamp" in blob:
                continue
            raise AppleConnectionError("Live evidence leaked a credential")
    for key in payload:
        if str(key).lower() in {"private_key", "password", "p8", "p12"}:
            raise AppleConnectionError("Live evidence leaked a credential")
