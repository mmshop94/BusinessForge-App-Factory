from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app_factory.domain.build import BuildArtifact, BuildResult, BuildStatus
from app_factory.infrastructure.hashing import sha256_file


class BuildReportWriter:
    """Persist machine-readable build reports."""

    def write(self, result: BuildResult, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        app_id = result.request.manifest.app.id
        timestamp = result.started_at.strftime("%Y%m%dT%H%M%SZ")
        report_path = output_dir / f"{app_id}-{timestamp}-build-report.json"
        payload = {
            "status": result.status.value,
            "contract_version": "1",
            "started_at": result.started_at.isoformat(),
            "finished_at": result.finished_at.isoformat() if result.finished_at else None,
            "duration_seconds": result.duration_seconds,
            "manifest": {
                "schema_version": result.request.manifest.schema_version,
                "app_id": result.request.manifest.app.id,
                "app_version": result.request.manifest.release.app_version,
                "build_number": result.request.manifest.release.build_number,
                "customer_app_ref": result.request.manifest.source.customer_app_ref,
                "public_app_id": result.request.manifest.tenant.public_app_id,
                "package_id": result.request.manifest.tenant.package,
            },
            "manifest_hash": result.request.manifest_hash,
            "manifest_path": result.request.manifest.manifest_path,
            "customer_app_commit": result.customer_app_commit,
            "flutter_version": result.flutter_version,
            "dart_version": result.dart_version,
            "dart_defines": _extract_dart_defines(result.steps),
            "error_message": result.error_message,
            "artifacts": [
                {
                    "kind": artifact.kind,
                    "path": artifact.path,
                    "sha256": artifact.sha256,
                    "size_bytes": artifact.size_bytes,
                }
                for artifact in result.artifacts
            ],
            "steps": result.steps,
        }
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result.report_path = str(report_path)
        return report_path

    @staticmethod
    def load(report_path: Path) -> dict:
        return json.loads(report_path.read_text(encoding="utf-8"))


def collect_android_artifact(
    workspace: Path,
    output_dir: Path,
    app_id: str,
    artifact_kind: str,
    glob_pattern: str,
) -> BuildArtifact | None:
    matches = sorted(workspace.glob(glob_pattern))
    if not matches:
        return None
    source = matches[-1]
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{app_id}-{source.name}"
    shutil.copy2(source, target)
    return BuildArtifact(
        kind=artifact_kind,
        path=str(target),
        sha256=sha256_file(target),
        size_bytes=target.stat().st_size,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_dart_defines(steps: list) -> dict[str, str]:
    for step in steps:
        if step.get("name") == "apply_manifest" and "dart_defines" in step:
            defines = step["dart_defines"]
            if isinstance(defines, dict):
                return defines
    return {}
