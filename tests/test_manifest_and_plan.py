from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from app_factory.application.build_planner import BuildPlanner
from app_factory.application.manifest_validator import ManifestLoader, ManifestValidator
from app_factory.domain.errors import (
    AssetNotFoundError,
    CompatibilityError,
    ManifestSecretError,
    ManifestValidationError,
)
from app_factory.infrastructure.paths import compat_path, schema_path
from app_factory.infrastructure.workspace import WorkspaceManager


EXAMPLE_MANIFEST = Path("manifests/examples/dorfladen-hutthurm.yaml")


@pytest.fixture
def validator() -> ManifestValidator:
    return ManifestValidator(schema_path(), compat_path())


@pytest.fixture
def valid_manifest_data() -> dict:
    return yaml.safe_load(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))


def test_valid_manifest_passes(validator: ManifestValidator, tmp_path: Path) -> None:
    manifest_dir = tmp_path / "tenant"
    manifest_dir.mkdir()
    branding = manifest_dir / "branding"
    branding.mkdir()
    (branding / "logo.svg").write_text("<svg/>", encoding="utf-8")
    (branding / "splash.png").write_bytes(_minimal_png())
    (branding / "icon.png").write_bytes(_minimal_png())

    data = yaml.safe_load(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))
    data["branding"]["logo_asset"] = "branding/logo.svg"
    data["branding"]["splash_asset"] = "branding/splash.png"
    data["branding"]["icon_asset"] = "branding/icon.png"
    manifest_path = manifest_dir / "manifest.yaml"
    manifest_path.write_text(yaml.dump(data), encoding="utf-8")

    domain = validator.validate_file(manifest_path)
    assert domain.app.id == "dorfladen-hutthurm"
    assert domain.tenant.package == "village_store"


def test_invalid_application_id(validator: ManifestValidator, valid_manifest_data: dict) -> None:
    valid_manifest_data["app"]["package_name_android"] = "Invalid-Package"
    with pytest.raises(ManifestValidationError):
        validator.validate_raw(valid_manifest_data)


def test_missing_assets(validator: ManifestValidator, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.dump(yaml.safe_load(EXAMPLE_MANIFEST.read_text())), encoding="utf-8")
    with pytest.raises(AssetNotFoundError):
        validator.validate_file(manifest_path)


def test_unknown_customer_app_ref(validator: ManifestValidator, valid_manifest_data: dict) -> None:
    valid_manifest_data["source"]["customer_app_ref"] = "nonexistent-tag-999"
    validator.validate_raw(valid_manifest_data)
    manifest = ManifestLoader().to_domain(valid_manifest_data)
    with pytest.raises(CompatibilityError):
        validator.validate_compatibility(manifest)


def test_no_secrets_in_manifest(validator: ManifestValidator, valid_manifest_data: dict) -> None:
    valid_manifest_data["api_key"] = "AKIA0123456789ABCDEF"
    with pytest.raises(ManifestSecretError):
        validator.validate_raw(valid_manifest_data)


def test_secret_key_name_rejected(validator: ManifestValidator, valid_manifest_data: dict) -> None:
    valid_manifest_data["signing"] = {"keystore_password": "test"}
    with pytest.raises(ManifestSecretError):
        validator.validate_raw(valid_manifest_data)


def test_deterministic_build_plan(valid_manifest_data: dict, tmp_path: Path) -> None:
    loader = ManifestLoader()
    manifest = loader.to_domain(valid_manifest_data)
    manifest_hash = ManifestValidator.manifest_hash(valid_manifest_data)
    customer_app = tmp_path / "customer-app"
    customer_app.mkdir()
    output_dir = tmp_path / "output"

    planner = BuildPlanner()
    plan_a = planner.plan(manifest, manifest_hash, customer_app, output_dir)
    plan_b = planner.plan(manifest, manifest_hash, customer_app, output_dir)

    assert plan_a.to_dict() == plan_b.to_dict()
    assert plan_a.dart_defines["PUBLIC_APP_ID"] == manifest.tenant.public_app_id
    assert plan_a.dart_defines["PACKAGE_ID"] == manifest.tenant.package
    assert plan_a.dart_defines["APP_NAME"] == manifest.app.display_name
    assert plan_a.dart_defines["FEATURE_LOYALTY"] == "false"


def test_customer_app_compatibility_check(validator: ManifestValidator) -> None:
    data = yaml.safe_load(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))
    data["tenant"]["package"] = "unknown_package_xyz"
    validator.validate_raw(data)
    manifest = ManifestLoader().to_domain(data)
    with pytest.raises(CompatibilityError):
        validator.validate_compatibility(manifest)


def test_build_workspace_isolation(tmp_path: Path) -> None:
    source = tmp_path / "source-app"
    source.mkdir()
    (source / "pubspec.yaml").write_text("name: demo\nversion: 1.0.0+1\n", encoding="utf-8")
    (source / "lib").mkdir()
    (source / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")

    workspace_mgr = WorkspaceManager(tmp_path / "workspace" / "tenant-a")
    workspace = workspace_mgr.prepare(source)
    (workspace / "pubspec.yaml").write_text("name: mutated\n", encoding="utf-8")

    assert (source / "pubspec.yaml").read_text(encoding="utf-8").startswith("name: demo")
    workspace_mgr.cleanup()
    assert not workspace.exists()


def test_source_copy_does_not_modify_customer_app(tmp_path: Path) -> None:
    source = tmp_path / "customer-app"
    gradle = source / "android" / "app"
    gradle.mkdir(parents=True)
    gradle_file = gradle / "build.gradle.kts"
    gradle_file.write_text('applicationId = "com.example.app"\n', encoding="utf-8")

    snapshot = WorkspaceManager.snapshot_files(source, ["android/app/build.gradle.kts"])
    workspace_mgr = WorkspaceManager(tmp_path / "ws")
    workspace_mgr.prepare(source)
    workspace_mgr.cleanup()
    WorkspaceManager.assert_source_unmodified(source, snapshot)


def test_manifest_hash_stable(valid_manifest_data: dict) -> None:
    hash_a = ManifestValidator.manifest_hash(valid_manifest_data)
    hash_b = ManifestValidator.manifest_hash(json.loads(json.dumps(valid_manifest_data)))
    assert hash_a == hash_b


def _minimal_png() -> bytes:
    # 1x1 transparent PNG
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
