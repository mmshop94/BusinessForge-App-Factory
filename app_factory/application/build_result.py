"""Standardized factory build result — no secret paths, no credentials."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PUBLIC_RESULT_KEYS = (
    "schema_version",
    "delivery_job_id",
    "build_id",
    "status",
    "artifact_type",
    "app_version",
    "version_code",
    "package_identity",
    "public_app_id",
    "created_at",
    "validation_results",
    "error_category",
    "artifact_sha256",
    "artifact_size_bytes",
)

SECRET_PATH_MARKERS = ("keystore", "password", "secret", "credential")


def public_build_result(
    *,
    delivery_job_id: str | None,
    build_id: str,
    status: str,
    artifact_type: str | None,
    app_version: str,
    version_code: int,
    package_identity: str,
    public_app_id: str,
    validation_results: list[dict[str, Any]] | None = None,
    error_category: str | None = None,
    artifact_sha256: str | None = None,
    artifact_size_bytes: int | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    mapped_status = _map_status(status)
    payload = {
        "schema_version": 1,
        "delivery_job_id": delivery_job_id,
        "build_id": build_id,
        "status": mapped_status,
        "artifact_type": artifact_type,
        "app_version": app_version,
        "version_code": version_code,
        "package_identity": package_identity,
        "public_app_id": public_app_id,
        "created_at": (created_at or datetime.now(timezone.utc)).isoformat(),
        "validation_results": validation_results or [],
        "error_category": error_category,
        "artifact_sha256": artifact_sha256,
        "artifact_size_bytes": artifact_size_bytes,
    }
    assert_no_secret_paths(payload)
    return payload


def _map_status(status: str) -> str:
    value = status.strip().lower()
    if value in {"succeeded", "success", "planned"}:
        return "success"
    if value in {"validation_failed", "invalid"}:
        return "validation_failed"
    return "failed"


def assert_no_secret_paths(payload: dict[str, Any]) -> None:
    blob = str(payload).lower()
    for marker in SECRET_PATH_MARKERS:
        if marker in blob:
            raise ValueError(f"Build result must not contain {marker}")


def write_public_result(payload: dict[str, Any], output_dir: Path, build_id: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{build_id}-build-result.json"
    import json

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
