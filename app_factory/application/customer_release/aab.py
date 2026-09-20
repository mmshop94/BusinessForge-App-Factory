"""Customer release AAB build + public inspection. Secrets stay in process env only."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Mapping

from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.customer_release.signing import (
    SHARED_OWNER_KEYSTORE_FORBIDDEN,
    looks_like_shared_owner_reference,
)
from app_factory.application.customer_release.upload_key import (
    certificate_sha256_from_keystore,
)
from app_factory.application.package_identity import is_reserved_android_package
from app_factory.application.signing import (
    CUSTOMER_KEY_ALIAS_ENV,
    CUSTOMER_KEY_PASSWORD_ENV,
    CUSTOMER_KEYSTORE_PATH_ENV,
    CUSTOMER_STORE_PASSWORD_ENV,
    KEYSTORE_PATH_ENV,
)
from app_factory.domain.errors import BuildExecutionError, CustomerReleaseError, SigningGuardError
from app_factory.infrastructure.flutter_runner import FlutterRunner
from app_factory.infrastructure.hashing import sha256_file

DEBUG_CERT_MARKERS = ("android debug", "cn=android debug", "debug.keystore")


def customer_signing_env(
    *,
    keystore_path: Path,
    alias: str,
    store_unlock: str,
    key_unlock: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Process env for Gradle. Never write these values to disk."""
    if looks_like_shared_owner_reference(str(keystore_path)):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    merged = dict(environ if environ is not None else os.environ)
    if merged.get(KEYSTORE_PATH_ENV) and Path(merged[KEYSTORE_PATH_ENV]) == keystore_path:
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    merged[CUSTOMER_KEYSTORE_PATH_ENV] = str(keystore_path)
    merged[CUSTOMER_KEY_ALIAS_ENV] = alias
    merged[CUSTOMER_STORE_PASSWORD_ENV] = store_unlock
    merged[CUSTOMER_KEY_PASSWORD_ENV] = key_unlock
    return merged


def inspect_customer_aab(
    aab_path: Path,
    *,
    profile: CustomerAppReleaseProfile,
    snapshot_id: str,
    factory_config: dict[str, Any],
    upload_cert_sha256: str,
    debug_signed: bool = False,
) -> dict[str, Any]:
    if not aab_path.is_file():
        raise CustomerReleaseError("AAB_MISSING")
    if debug_signed:
        raise SigningGuardError("DEBUG_SIGNING_BLOCKED")
    sha = sha256_file(aab_path)
    package = str(factory_config.get("android_application_id") or profile.package_name)
    if package != profile.package_name:
        raise CustomerReleaseError("AAB_PACKAGE_MISMATCH")
    if is_reserved_android_package(package):
        raise CustomerReleaseError("DEMO_PACKAGE_ID")
    if str(factory_config.get("public_app_id") or "") != profile.public_app_id:
        raise CustomerReleaseError("DEMO_TENANT_IDENTITY")
    display = str(factory_config.get("display_name") or "")
    if "demo" in display.lower():
        raise CustomerReleaseError("DEMO_TENANT_IDENTITY")
    if str(factory_config.get("release_snapshot_id") or "") != snapshot_id:
        raise CustomerReleaseError("SNAPSHOT_MISMATCH")
    if looks_like_shared_owner_reference(upload_cert_sha256):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    payload = {
        "aab_path": str(aab_path),
        "aab_sha256": sha,
        "size_bytes": aab_path.stat().st_size,
        "package_name": package,
        "version_code": profile.version_code,
        "version_name": profile.release_version,
        "display_name": display or profile.display_name,
        "release_build": True,
        "signing": "CUSTOMER_UPLOAD_KEY",
        "upload_certificate_sha256": upload_cert_sha256,
        "debug_signing": False,
        "shared_owner_signing": False,
        "snapshot_id": snapshot_id,
        "zip": zipfile.is_zipfile(aab_path),
    }
    return payload


def write_placeholder_aab(path: Path, *, package_name: str, version_code: int) -> str:
    """Deterministic zip used when Flutter is mocked. Not a Play-valid bundle."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "BundleConfig.pb",
            f"placeholder:{package_name}:{version_code}".encode("utf-8"),
        )
        archive.writestr("META-INF/BNDLTOOL.SF", b"placeholder-signature-file")
    return sha256_file(path)


def build_customer_aab(
    workspace: Path,
    output_dir: Path,
    *,
    profile: CustomerAppReleaseProfile,
    snapshot_id: str,
    flutter_runner: FlutterRunner,
    dart_defines: dict[str, str],
    signing_environ: Mapping[str, str],
    upload_cert_sha256: str,
) -> dict[str, Any]:
    if KEYSTORE_PATH_ENV in signing_environ and not signing_environ.get(CUSTOMER_KEYSTORE_PATH_ENV):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    previous = dict(os.environ)
    try:
        os.environ.update({k: str(v) for k, v in signing_environ.items()})
        flutter_runner.run(["pub", "get"], cwd=workspace)
        flutter_runner.run(
            ["build", "appbundle", "--release"],
            cwd=workspace,
            dart_defines=dart_defines,
        )
    finally:
        os.environ.clear()
        os.environ.update(previous)

    matches = sorted(workspace.glob("build/app/outputs/bundle/release/*.aab"))
    if not matches:
        raise BuildExecutionError("AAB not produced")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{profile.app_id}-{profile.version_code}.aab"
    shutil.copy2(matches[-1], target)
    config_path = workspace / "build_config" / "app_factory_config.json"
    factory_config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    return inspect_customer_aab(
        target,
        profile=profile,
        snapshot_id=snapshot_id,
        factory_config=factory_config,
        upload_cert_sha256=upload_cert_sha256,
    )


def fingerprint_or_hash(keystore_path: Path, alias: str, store_unlock: str) -> str:
    try:
        return certificate_sha256_from_keystore(
            keystore_path, alias=alias, store_unlock=store_unlock
        )
    except OSError:
        return hashlib.sha256(keystore_path.read_bytes()).hexdigest()
