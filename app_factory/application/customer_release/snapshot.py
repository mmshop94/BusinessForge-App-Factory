"""Immutable customer release snapshots — tenant edits never mutate a frozen release."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.profile import (
    CustomerAppReleaseProfile,
    profile_from_dict,
)
from app_factory.application.manifest_validator import ManifestValidator
from app_factory.domain.errors import SnapshotImmutabilityError

SNAPSHOT_SCHEMA_VERSION = 1


def freeze_snapshot(
    profile: CustomerAppReleaseProfile,
    output_dir: Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    ManifestValidator._assert_no_secrets(profile.to_dict())
    stamped = generated_at or datetime.now(timezone.utc).isoformat()
    body = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "release_id": profile.release_id,
        "app_id": profile.app_id,
        "tenant_id": profile.tenant_id,
        "generated_at": stamped,
        "profile": profile.to_dict(),
        "source": {
            "customer_app_ref": profile.customer_app_ref,
            "factory_compat_version": profile.factory_compat_version,
        },
    }
    snapshot_id = _snapshot_id(body)
    body["snapshot_id"] = snapshot_id
    path = snapshot_path(output_dir, snapshot_id)
    if path.is_file():
        return load_snapshot(path)
    body["snapshot_hash"] = _hash_body({**body, "snapshot_hash": None})
    output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


def load_snapshot(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.get("snapshot_hash")
    check = _hash_body({**payload, "snapshot_hash": None})
    if expected != check:
        raise SnapshotImmutabilityError("Snapshot hash mismatch — file was mutated")
    ManifestValidator._assert_no_secrets(payload)
    return payload


def profile_from_snapshot(payload: dict[str, Any]) -> CustomerAppReleaseProfile:
    profile = profile_from_dict(payload["profile"])
    return profile.with_snapshot_id(str(payload["snapshot_id"]))


def snapshot_path(output_dir: Path, snapshot_id: str) -> Path:
    return output_dir / f"{snapshot_id}.json"


def _snapshot_id(body: dict[str, Any]) -> str:
    basis = {
        "release_id": body["release_id"],
        "app_id": body["app_id"],
        "profile": body["profile"],
        "source": body["source"],
    }
    digest = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"snap_{digest[:16]}"


def _hash_body(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
