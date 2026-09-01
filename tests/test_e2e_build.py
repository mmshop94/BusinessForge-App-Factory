from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app_factory.application.build_orchestrator import BuildOrchestrator
from app_factory.application.build_planner import BuildPlanner
from app_factory.application.e2e_build import (
    E2eTestBuildError,
    assert_e2e_test_build_safe,
    e2e_dart_defines,
)
from app_factory.application.manifest_validator import ManifestValidator
from app_factory.domain.build import BuildRequest
from app_factory.domain.enums import BuildStatus
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
    data = yaml.safe_load(Path("manifests/examples/dorfladen-hutthurm.yaml").read_text(encoding="utf-8"))
    data["branding"]["logo_asset"] = "branding/logo.svg"
    data["branding"].pop("splash_asset", None)
    data["branding"].pop("icon_asset", None)
    manifest_path = manifest_dir / "manifest.yaml"
    manifest_path.write_text(yaml.dump(data), encoding="utf-8")
    return manifest_path


def test_e2e_defines_are_absent_from_normal_plan(mini_customer_app, tenant_manifest, tmp_path):
    validator = ManifestValidator(schema_path(), compat_path())
    raw = yaml.safe_load(tenant_manifest.read_text(encoding="utf-8"))
    manifest = validator.validate_file(tenant_manifest)
    request = BuildRequest(
        manifest=manifest,
        manifest_hash=ManifestValidator.manifest_hash(raw),
        customer_app_path=str(mini_customer_app),
        output_dir=str(tmp_path / "output"),
    )
    plan = BuildPlanner().plan_request(request)
    assert "E2E_TEST_BUILD" not in plan.dart_defines
    assert "BF_E2E_RUN_ID" not in plan.dart_defines
    assert plan.dart_defines["PUBLIC_APP_ID"] == manifest.tenant.public_app_id


def test_e2e_test_plan_adds_defines(mini_customer_app, tenant_manifest, tmp_path):
    validator = ManifestValidator(schema_path(), compat_path())
    raw = yaml.safe_load(tenant_manifest.read_text(encoding="utf-8"))
    manifest = validator.validate_file(tenant_manifest)
    request = BuildRequest(
        manifest=manifest,
        manifest_hash=ManifestValidator.manifest_hash(raw),
        customer_app_path=str(mini_customer_app),
        output_dir=str(tmp_path / "output"),
        e2e_test=True,
        e2e_environment="demo",
        e2e_run_id="bf-e2e-app-20260901-001",
        debug_build=True,
    )
    plan = BuildPlanner().plan_request(request)
    assert plan.dart_defines["E2E_TEST_BUILD"] == "true"
    assert plan.dart_defines["BF_E2E_ENVIRONMENT"] == "demo"
    assert plan.dart_defines["BF_E2E_RUN_ID"] == "bf-e2e-app-20260901-001"
    assert "--release" not in (plan.steps[-3].command or "")
    assert "--debug" in (plan.steps[-3].command or "")


def test_e2e_production_origin_aborts():
    try:
        assert_e2e_test_build_safe(
            api_base_url="https://api.bforge.de/api/v1",
            environment="demo",
            public_app_id="app_1DZR48F5F7MCFXS2ZM89V6EADV",
        )
    except E2eTestBuildError:
        return
    raise AssertionError("production origin must abort")


def test_e2e_unknown_environment_aborts():
    try:
        assert_e2e_test_build_safe(
            api_base_url="https://demo-api.bforge.de/api/v1",
            environment="staging",
            public_app_id="app_1DZR48F5F7MCFXS2ZM89V6EADV",
        )
    except E2eTestBuildError:
        return
    raise AssertionError("unknown environment must abort")


def test_e2e_demo_origin_allowed():
    assert_e2e_test_build_safe(
        api_base_url="https://demo-api.bforge.de/api/v1",
        environment="demo",
        public_app_id="app_1DZR48F5F7MCFXS2ZM89V6EADV",
    )
    defines = e2e_dart_defines(environment="demo", run_id="bf-e2e-app-1", actor_id="C01")
    assert defines["E2E_TEST_BUILD"] == "true"
    assert defines["BF_E2E_ACTOR_ID"] == "C01"


def test_orchestrator_e2e_production_fails_before_flutter(
    mini_customer_app, tenant_manifest, tmp_path
):
    validator = ManifestValidator(schema_path(), compat_path())
    raw = yaml.safe_load(tenant_manifest.read_text(encoding="utf-8"))
    manifest = validator.validate_file(tenant_manifest)
    poisoned = type(manifest)(
        **{
            **manifest.__dict__,
            "api_base_url": "https://api.bforge.de/api/v1",
            "backend_origin": "https://api.bforge.de",
        }
    )
    request = BuildRequest(
        manifest=poisoned,
        manifest_hash=ManifestValidator.manifest_hash(raw),
        customer_app_path=str(mini_customer_app),
        output_dir=str(tmp_path / "output"),
        e2e_test=True,
        e2e_environment="demo",
        dry_run=True,
    )
    result = BuildOrchestrator().build_android(request)
    assert result.status == BuildStatus.FAILED
    assert "production" in (result.error_message or "").lower()
