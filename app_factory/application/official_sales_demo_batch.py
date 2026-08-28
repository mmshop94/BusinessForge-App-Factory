"""Batch build all Official Sales Demo Android apps."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app_factory.application.build_orchestrator import BuildOrchestrator
from app_factory.application.manifest_validator import ManifestLoader, ManifestValidator
from app_factory.application.official_sales_demo_discovery import (
    OFFICIAL_SALES_DEMO_SLUGS,
    discover_official_sales_demos,
)
from app_factory.application.official_sales_demo_manifests import materialize_demo_manifest_dir
from app_factory.domain.build import BuildRequest
from app_factory.domain.enums import AndroidArtifactFormat
from app_factory.domain.errors import AppFactoryError
from app_factory.infrastructure.flutter_runner import FlutterRunner
from app_factory.infrastructure.paths import compat_path, repo_root, schema_path


@dataclass
class DemoBuildEntry:
    slug: str
    manifest_path: Path
    metadata_path: Path
    apk_path: Path | None = None
    aab_path: Path | None = None
    apk_sha256: str | None = None
    aab_sha256: str | None = None
    status: str = "pending"
    errors: list[str] = field(default_factory=list)


@dataclass
class BatchBuildResult:
    output_root: Path
    api_base_url: str
    demos_found: int
    entries: list[DemoBuildEntry] = field(default_factory=list)
    matrix_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_root": str(self.output_root),
            "api_base_url": self.api_base_url,
            "demos_found": self.demos_found,
            "entries": [
                {
                    "slug": entry.slug,
                    "status": entry.status,
                    "manifest": str(entry.manifest_path),
                    "apk": str(entry.apk_path) if entry.apk_path else None,
                    "aab": str(entry.aab_path) if entry.aab_path else None,
                    "apk_sha256": entry.apk_sha256,
                    "aab_sha256": entry.aab_sha256,
                    "errors": entry.errors,
                }
                for entry in self.entries
            ],
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refresh_official_sales_demo_matrix(output_root: Path) -> Path:
    """Reconcile manifest.json and per-app metadata with artifacts already on disk."""
    matrix_path = output_root / "manifest.json"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"Matrix not found: {matrix_path}")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for slug, app in matrix.get("apps", {}).items():
        demo_dir = output_root / slug
        meta_path = demo_dir / "metadata" / "app.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else dict(app)
        apk_files = sorted((demo_dir / "apk").glob("*.apk")) if (demo_dir / "apk").is_dir() else []
        aab_files = sorted((demo_dir / "aab").glob("*.aab")) if (demo_dir / "aab").is_dir() else []
        if apk_files:
            meta["apk_path"] = str(apk_files[0])
            meta["apk_sha256"] = _sha256_file(apk_files[0])
        if aab_files:
            meta["aab_path"] = str(aab_files[0])
            meta["aab_sha256"] = _sha256_file(aab_files[0])
        if apk_files and aab_files:
            meta["build_status"] = "success"
        elif apk_files or aab_files:
            meta["build_status"] = "partial"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        matrix["apps"][slug] = meta
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    return matrix_path


def _load_demo_password(env_demo_path: Path) -> str:
    if not env_demo_path.is_file():
        raise FileNotFoundError(f"Demo env not found: {env_demo_path}")
    for line in env_demo_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("BF_DEMO_OWNER_PASSWORD="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("BF_DEMO_OWNER_PASSWORD missing in .env.demo")


def _store_metadata(entry: DemoBuildEntry, **updates: Any) -> None:
    payload = json.loads(entry.metadata_path.read_text(encoding="utf-8"))
    payload.update(updates)
    entry.metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_single_build(
    manifest_path: Path,
    *,
    customer_app: Path,
    artifact_format: AndroidArtifactFormat,
    skip_tests: bool,
    skip_analyze: bool,
    flutter_path: str,
) -> tuple[str, Path | None, str | None]:
    validator = ManifestValidator(schema_path(), compat_path())
    loader = ManifestLoader()
    raw = loader.load(manifest_path)
    domain = validator.validate_file(manifest_path)
    manifest_hash = ManifestValidator.manifest_hash(raw)
    request = BuildRequest(
        manifest=domain,
        manifest_hash=manifest_hash,
        customer_app_path=str(customer_app),
        output_dir=str(manifest_path.parent.parent / "_factory_output"),
        artifact_format=artifact_format,
        run_tests=not skip_tests,
        run_analyze=not skip_analyze,
        dry_run=False,
    )
    result = BuildOrchestrator(flutter_runner=FlutterRunner(flutter_path)).build_android(request)
    if result.status.value != "succeeded":
        raise AppFactoryError(f"Build failed: {result.status.value}")
    artifact_obj = result.artifacts[-1] if result.artifacts else None
    artifact = Path(artifact_obj.path) if artifact_obj else None
    digest = artifact_obj.sha256 if artifact_obj else None
    return result.status.value, artifact, digest


def build_official_sales_demo_apps(
    *,
    output_root: Path,
    api_base_url: str = "http://192.168.178.95:8090/api/v1",
    customer_app: Path,
    env_demo_path: Path | None = None,
    slugs: tuple[str, ...] = OFFICIAL_SALES_DEMO_SLUGS,
    skip_tests: bool = True,
    skip_analyze: bool = True,
    build_apk: bool = True,
    build_aab: bool = True,
    flutter_path: str = "flutter",
    manifest_only: bool = False,
) -> BatchBuildResult:
    password_path = env_demo_path or (repo_root().parent / "BusinessForge" / ".env.demo")
    owner_password = _load_demo_password(password_path)
    records = discover_official_sales_demos(
        api_base_url=api_base_url,
        owner_password=owner_password,
        slugs=slugs,
    )
    if slugs == OFFICIAL_SALES_DEMO_SLUGS and len(records) != len(OFFICIAL_SALES_DEMO_SLUGS):
        raise RuntimeError(
            f"Expected {len(OFFICIAL_SALES_DEMO_SLUGS)} official demos, discovered {len(records)}"
        )
    for record in records:
        if not record.login_ok or not record.bootstrap_ok or not record.public_app_id:
            raise RuntimeError(f"Demo plane validation failed for {record.slug}")

    output_root.mkdir(parents=True, exist_ok=True)
    matrix_path = output_root / "manifest.json"
    existing_matrix: dict[str, Any] = {}
    if matrix_path.is_file() and slugs != OFFICIAL_SALES_DEMO_SLUGS:
        existing_matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix: dict[str, Any] = {
        "schema": "official-sales-demo-app-matrix-v1",
        "api_base_url": api_base_url,
        "customer_app": str(customer_app),
        "apps": dict(existing_matrix.get("apps", {})),
    }
    result = BatchBuildResult(
        output_root=output_root,
        api_base_url=api_base_url,
        demos_found=len(records),
    )

    for record in records:
        demo_dir = output_root / record.slug
        manifest_path = materialize_demo_manifest_dir(
            record,
            demo_dir,
            api_base_url=api_base_url,
        )
        entry = DemoBuildEntry(
            slug=record.slug,
            manifest_path=manifest_path,
            metadata_path=demo_dir / "metadata" / "app.json",
        )
        result.entries.append(entry)
        matrix["apps"][record.slug] = json.loads(entry.metadata_path.read_text(encoding="utf-8"))

        if manifest_only:
            entry.status = "manifest_ready"
            _store_metadata(entry, build_status="manifest_ready")
            continue

        try:
            if build_apk:
                _, artifact, digest = _run_single_build(
                    manifest_path,
                    customer_app=customer_app,
                    artifact_format=AndroidArtifactFormat.APK,
                    skip_tests=skip_tests,
                    skip_analyze=skip_analyze,
                    flutter_path=flutter_path,
                )
                if artifact and artifact.is_file():
                    apk_dir = demo_dir / "apk"
                    apk_dir.mkdir(parents=True, exist_ok=True)
                    target = apk_dir / f"{record.slug}-release.apk"
                    shutil.copy2(artifact, target)
                    entry.apk_path = target
                    entry.apk_sha256 = digest

            if build_aab:
                _, artifact, digest = _run_single_build(
                    manifest_path,
                    customer_app=customer_app,
                    artifact_format=AndroidArtifactFormat.AAB,
                    skip_tests=skip_tests,
                    skip_analyze=skip_analyze,
                    flutter_path=flutter_path,
                )
                if artifact and artifact.is_file():
                    aab_dir = demo_dir / "aab"
                    aab_dir.mkdir(parents=True, exist_ok=True)
                    target = aab_dir / f"{record.slug}-release.aab"
                    shutil.copy2(artifact, target)
                    entry.aab_path = target
                    entry.aab_sha256 = digest

            if build_apk and not entry.apk_path:
                raise AppFactoryError("APK build did not produce an artifact")
            if build_aab and not entry.aab_path:
                raise AppFactoryError("AAB build did not produce an artifact")
            entry.status = "success"
            _store_metadata(
                entry,
                build_status="success",
                apk_path=str(entry.apk_path) if entry.apk_path else None,
                aab_path=str(entry.aab_path) if entry.aab_path else None,
                apk_sha256=entry.apk_sha256,
                aab_sha256=entry.aab_sha256,
            )
            matrix["apps"][record.slug] = json.loads(entry.metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            partial = entry.apk_path is not None or entry.aab_path is not None
            entry.status = "partial" if partial else "failed"
            entry.errors.append(str(exc)[:500])
            _store_metadata(
                entry,
                build_status=entry.status,
                error=entry.errors[-1],
                apk_path=str(entry.apk_path) if entry.apk_path else None,
                aab_path=str(entry.aab_path) if entry.aab_path else None,
                apk_sha256=entry.apk_sha256,
                aab_sha256=entry.aab_sha256,
            )
            matrix["apps"][record.slug] = json.loads(entry.metadata_path.read_text(encoding="utf-8"))

    matrix_path = output_root / "manifest.json"
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    if manifest_only:
        refresh_official_sales_demo_matrix(output_root)
    result.matrix_path = matrix_path
    return result
