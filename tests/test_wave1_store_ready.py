from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
import yaml

from app_factory.application.build_result import public_build_result
from app_factory.application.export_materializer import materialize_export
from app_factory.application.image_assets import (
    generate_android_icons,
    generate_default_icon,
    generate_splash,
    validate_icon_bytes,
)
from app_factory.application.manifest_validator import ManifestValidator
from app_factory.application.package_identity import android_application_id_from_public_app_id
from app_factory.application.signing import SIGNING_CONFIGURATION_REQUIRED, signing_status
from app_factory.domain.errors import ManifestSecretError, ManifestValidationError
from app_factory.infrastructure.flutter_config import FlutterConfigApplier
from app_factory.infrastructure.paths import compat_path, schema_path


def _square_png(size: int = 512) -> bytes:
    return generate_default_icon(primary_color="#2563EB", size=size)


def test_icon_validation_rejects_tiny_and_nonsquare() -> None:
    tiny = generate_default_icon(primary_color="#111111", size=64)
    with pytest.raises(ManifestValidationError):
        validate_icon_bytes(tiny)
    from PIL import Image
    import io

    image = Image.new("RGB", (512, 256), (0, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    with pytest.raises(ManifestValidationError):
        validate_icon_bytes(buffer.getvalue())


def test_icon_generation_writes_mipmaps(tmp_path: Path) -> None:
    written = generate_android_icons(_square_png(), tmp_path)
    assert any("mipmap-xxxhdpi" in item and "ic_launcher.png" in item for item in written)
    assert (tmp_path / "mipmap-mdpi" / "ic_launcher.png").is_file()
    assert (tmp_path / "play" / "ic_launcher-512.png").is_file()


def test_splash_generation(tmp_path: Path) -> None:
    written = generate_splash(background_color="#8B4A2F", logo_bytes=_square_png(512), output_res=tmp_path)
    assert (tmp_path / "drawable" / "splash_brand.png").is_file()
    assert (tmp_path / "drawable" / "launch_background.xml").is_file()
    assert any("splash_brand.png" in item for item in written)


def test_package_identity_from_public_app_id() -> None:
    app_id = "app_01JABCDEFGHJKMNPQRSTVWXYZ0"
    assert android_application_id_from_public_app_id(app_id) == "de.bforge.app.u01jabcdefghjkmnpqrstvwxyz0"


def test_package_identity_rejected_if_not_canonical() -> None:
    validator = ManifestValidator(schema_path(), compat_path())
    data = yaml.safe_load(Path("manifests/examples/dorfladen-hutthurm.yaml").read_text(encoding="utf-8"))
    data["app"]["package_name_android"] = "de.bforge.customer.slug"
    with pytest.raises(ManifestValidationError):
        validator.validate_raw(data)


def test_no_secrets_in_manifest_and_result() -> None:
    validator = ManifestValidator(schema_path(), compat_path())
    data = yaml.safe_load(Path("manifests/examples/dorfladen-hutthurm.yaml").read_text(encoding="utf-8"))
    data["keystore_password"] = "nope"
    with pytest.raises(ManifestSecretError):
        validator.validate_raw(data)
    with pytest.raises(ValueError):
        public_build_result(
            delivery_job_id="job",
            build_id="b1",
            status="success",
            artifact_type="apk",
            app_version="1.0.0",
            version_code=1,
            package_identity="de.bforge.app.u01jabcdefghjkmnpqrstvwxyz0",
            public_app_id="app_01JABCDEFGHJKMNPQRSTVWXYZ0",
            validation_results=[{"keystore": "/secret/path"}],
        )


def test_signing_status_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BF_ANDROID_KEYSTORE_PATH", raising=False)
    monkeypatch.delenv("BF_ANDROID_KEY_ALIAS", raising=False)
    monkeypatch.delenv("BF_ANDROID_STORE_PASSWORD", raising=False)
    status = signing_status(environ={})
    assert status.configured is False
    assert status.code == SIGNING_CONFIGURATION_REQUIRED


def test_production_requires_icon(tmp_path: Path) -> None:
    data = yaml.safe_load(Path("manifests/examples/dorfladen-hutthurm.yaml").read_text(encoding="utf-8"))
    data["release"]["channel"] = "production"
    data["branding"].pop("icon_asset", None)
    data["branding"].pop("splash_asset", None)
    manifest_dir = tmp_path / "tenant"
    manifest_dir.mkdir()
    (manifest_dir / "branding").mkdir()
    (manifest_dir / "branding" / "logo.svg").write_text("<svg/>", encoding="utf-8")
    data["branding"]["logo_asset"] = "branding/logo.svg"
    manifest_path = manifest_dir / "manifest.yaml"
    manifest_path.write_text(yaml.dump(data), encoding="utf-8")
    validator = ManifestValidator(schema_path(), compat_path())
    manifest = validator.validate_file(manifest_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "pubspec.yaml").write_text("name: x\nversion: 1.0.0+1\n", encoding="utf-8")
    with pytest.raises(Exception):
        FlutterConfigApplier().apply(workspace, manifest, {}, branding_assets_root=manifest_dir)


def test_materialize_export_writes_manifest(tmp_path: Path) -> None:
    icon = _square_png()
    payload = {
        "manifest": yaml.safe_load(Path("manifests/examples/dorfladen-hutthurm.yaml").read_text()),
        "assets": {
            "branding/icon.png": {"content_base64": base64.b64encode(icon).decode("ascii")},
        },
    }
    payload["manifest"]["branding"]["logo_asset"] = "branding/logo.svg"
    path = materialize_export(payload, tmp_path / "export")
    assert path.is_file()
    assert (tmp_path / "export" / "branding" / "icon.png").is_file()


def test_public_build_result_mapping() -> None:
    payload = public_build_result(
        delivery_job_id="11111111-1111-4111-8111-111111111111",
        build_id="build-1",
        status="succeeded",
        artifact_type="apk",
        app_version="1.0.0",
        version_code=1,
        package_identity="de.bforge.app.u01jabcdefghjkmnpqrstvwxyz0",
        public_app_id="app_01JABCDEFGHJKMNPQRSTVWXYZ0",
    )
    assert payload["status"] == "success"
    assert payload["schema_version"] == 1
    dumped = json.dumps(payload)
    assert "password" not in dumped
    assert "keystore" not in dumped
