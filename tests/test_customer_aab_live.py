"""Optional live Flutter AAB. Off by default. Enable with BF_LIVE_CUSTOMER_AAB=1."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app_factory.application.customer_release.aab import customer_signing_env, fingerprint_or_hash
from app_factory.application.customer_release.pipeline import prepare_customer_release
from app_factory.application.customer_release.upload_key import create_ephemeral_upload_keystore
from app_factory.infrastructure.flutter_runner import FlutterRunner
from app_factory.infrastructure.paths import repo_root
from tests.test_customer_release_intake import SECRET_VALUE, _intake, _resolver, _write_assets

FLUTTER_BAT = Path(r"d:\projekte\tools\flutter\bin\flutter.bat")
CUSTOMER_APP = repo_root().parent / "BusinessForge FlutterApp"


@pytest.mark.skipif(
    os.environ.get("BF_LIVE_CUSTOMER_AAB") != "1",
    reason="Set BF_LIVE_CUSTOMER_AAB=1 for the controlled live AAB proof",
)
def test_live_customer_release_aab(tmp_path: Path) -> None:
    if not FLUTTER_BAT.is_file() or not CUSTOMER_APP.is_dir():
        pytest.skip("Flutter SDK or customer app checkout missing")
    sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not sdk:
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
        if local.is_dir():
            os.environ["ANDROID_SDK_ROOT"] = str(local)
        else:
            pytest.skip("Android SDK not configured")

    _write_assets(tmp_path)
    keystore = tmp_path / "upload.p12"
    cert = create_ephemeral_upload_keystore(keystore, alias="upload", store_unlock="test-unlock-aa11")
    environ = customer_signing_env(
        keystore_path=keystore,
        alias="upload",
        store_unlock="test-unlock-aa11",
        key_unlock="test-unlock-aa11",
    )
    recorded = fingerprint_or_hash(keystore, "upload", "test-unlock-aa11")
    assert recorded
    result = prepare_customer_release(
        _intake(tmp_path),
        tmp_path / "out",
        customer_app_path=CUSTOMER_APP,
        resolver=_resolver(),
        apply_workspace=True,
        skip_build=False,
        flutter_runner=FlutterRunner(str(FLUTTER_BAT)),
        signing_environ=environ,
        upload_cert_sha256=cert,
    )
    dumped = json.dumps(result)
    assert SECRET_VALUE not in dumped
    assert "test-unlock-aa11" not in dumped
    assert result["build"]["executed"] is True
    assert result["build"]["package_name"] == "de.hutthurm.dorfladen"
    assert result["build"]["version_code"] == 1
    assert result["build"]["signing"] == "CUSTOMER_UPLOAD_KEY"
    assert Path(result["build"]["aab_path"]).is_file()
