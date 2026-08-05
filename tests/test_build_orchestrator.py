from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from app_factory.application.build_orchestrator import BuildOrchestrator
from app_factory.application.manifest_validator import ManifestLoader, ManifestValidator
from app_factory.domain.build import BuildRequest
from app_factory.domain.enums import AndroidArtifactFormat, BuildStatus
from app_factory.infrastructure.flutter_config import FlutterConfigApplier
from app_factory.infrastructure.flutter_runner import CommandResult, FlutterRunner
from app_factory.infrastructure.paths import compat_path, schema_path


@pytest.fixture
def mini_customer_app(tmp_path: Path) -> Path:
    app = tmp_path / "customer-app"
    app.mkdir()
    (app / "pubspec.yaml").write_text(
        "name: businessforge_mobile\nversion: 0.5.9+1\n",
        encoding="utf-8",
    )
    android = app / "android" / "app"
    android.mkdir(parents=True)
    (android / "build.gradle.kts").write_text(
        'applicationId = "com.businessforge.businessforge_mobile"\n',
        encoding="utf-8",
    )
    manifest_xml_dir = android / "src" / "main"
    manifest_xml_dir.mkdir(parents=True)
    (manifest_xml_dir / "AndroidManifest.xml").write_text(
        '<manifest android:label="businessforge_mobile"></manifest>',
        encoding="utf-8",
    )
    config = app / "lib" / "config"
    config.mkdir(parents=True)
    (config / "app_config.dart").write_text("// config\n", encoding="utf-8")
    return app


@pytest.fixture
def tenant_manifest(tmp_path: Path) -> Path:
    manifest_dir = tmp_path / "tenant"
    manifest_dir.mkdir()
    branding = manifest_dir / "branding"
    branding.mkdir()
    (branding / "logo.svg").write_text("<svg/>", encoding="utf-8")

    data = yaml.safe_load(
        Path("manifests/examples/dorfladen-hutthurm.yaml").read_text(encoding="utf-8")
    )
    data["branding"]["logo_asset"] = "branding/logo.svg"
    data["branding"].pop("splash_asset", None)
    data["branding"].pop("icon_asset", None)
    manifest_path = manifest_dir / "manifest.yaml"
    manifest_path.write_text(yaml.dump(data), encoding="utf-8")
    return manifest_path


def test_config_applier_patches_workspace(
    mini_customer_app: Path, tenant_manifest: Path, tmp_path: Path
) -> None:
    validator = ManifestValidator(schema_path(), compat_path())
    manifest = validator.validate_file(tenant_manifest)
    workspace = tmp_path / "workspace"
    import shutil

    shutil.copytree(mini_customer_app, workspace)

    applier = FlutterConfigApplier()
    changed = applier.apply(
        workspace,
        manifest,
        {"API_BASE_URL": manifest.api_base_url, "PUBLIC_APP_ID": manifest.tenant.public_app_id},
        branding_assets_root=tenant_manifest.parent,
    )
    assert "pubspec.yaml" in changed
    assert "1.0.0+1" in (workspace / "pubspec.yaml").read_text(encoding="utf-8")
    gradle = (workspace / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert "de.bforge.dorfladenhutthurm" in gradle


def test_build_orchestrator_dry_run(
    mini_customer_app: Path, tenant_manifest: Path, tmp_path: Path
) -> None:
    validator = ManifestValidator(schema_path(), compat_path())
    raw = yaml.safe_load(tenant_manifest.read_text(encoding="utf-8"))
    manifest = validator.validate_file(tenant_manifest)
    request = BuildRequest(
        manifest=manifest,
        manifest_hash=ManifestValidator.manifest_hash(raw),
        customer_app_path=str(mini_customer_app),
        output_dir=str(tmp_path / "output"),
        artifact_format=AndroidArtifactFormat.APK,
        dry_run=True,
    )
    result = BuildOrchestrator(flutter_runner=MagicMock()).build_android(request)
    assert result.status == BuildStatus.PLANNED
    assert result.report_path is not None


def test_build_orchestrator_mocked_flutter_success(
    mini_customer_app: Path, tenant_manifest: Path, tmp_path: Path
) -> None:
    validator = ManifestValidator(schema_path(), compat_path())
    raw = yaml.safe_load(tenant_manifest.read_text(encoding="utf-8"))
    manifest = validator.validate_file(tenant_manifest)

    flutter = MagicMock(spec=FlutterRunner)
    flutter.run.return_value = CommandResult(
        command=["flutter", "test"],
        returncode=0,
        stdout="ok",
        stderr="",
    )
    flutter.git_commit.return_value = "abc123"
    flutter.version_info.return_value = ("Flutter 3.24.0", "Dart 3.5.0")

    request = BuildRequest(
        manifest=manifest,
        manifest_hash=ManifestValidator.manifest_hash(raw),
        customer_app_path=str(mini_customer_app),
        output_dir=str(tmp_path / "output"),
        artifact_format=AndroidArtifactFormat.APK,
        run_tests=True,
        run_analyze=True,
    )

    orchestrator = BuildOrchestrator(flutter_runner=flutter)
    result = orchestrator.build_android(request)

    assert result.status == BuildStatus.SUCCEEDED
    assert (mini_customer_app / "pubspec.yaml").read_text(encoding="utf-8").startswith(
        "name: businessforge_mobile"
    )
    assert flutter.run.call_count >= 4
