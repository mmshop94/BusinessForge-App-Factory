"""Customer Android release workflow: validate → snapshot → apply → assets → signing-check → build → verify."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.gates import (
    STORE_RELEASE_READY,
    evaluate_readiness,
)
from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.platforms import android_enabled, ios_enabled
from app_factory.application.customer_release.profile import (
    CustomerAppReleaseProfile,
    profile_from_dict,
)
from app_factory.application.customer_release.signing import (
    FailClosedSecretResolver,
    SecretReferenceResolver,
    assert_customer_production_signing,
    public_signing_status,
)
from app_factory.application.customer_release.snapshot import freeze_snapshot, profile_from_snapshot
from app_factory.application.signing import gradle_customer_release_signing_snippet
from app_factory.domain.build import (
    AppBuildManifest,
    AppIdentity,
    BrandingConfiguration,
    FeatureConfiguration,
    ReleaseConfiguration,
    SourceRevision,
    TenantBinding,
)
from app_factory.domain.errors import CustomerReleaseError, SigningGuardError
from app_factory.infrastructure.flutter_config import FlutterConfigApplier

SECRET_VALUE_MARKERS = ("-----begin", ".jks", "password=")


def prepare_customer_release(
    intake: dict[str, Any],
    output_dir: Path,
    *,
    customer_app_path: Path | None = None,
    registry: CustomerAppIdentityRegistry | None = None,
    resolver: SecretReferenceResolver | None = None,
    skip_build: bool = True,
    apply_workspace: bool = True,
    allow_local_test_signing: bool = False,
    flutter_runner: Any = None,
    signing_environ: dict[str, str] | None = None,
    upload_cert_sha256: str = "",
) -> dict[str, Any]:
    """Prepare a customer Android release candidate. Never writes secret values."""
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = profile_from_dict(intake)
    steps: list[dict[str, Any]] = []

    identity_registry = registry or CustomerAppIdentityRegistry(output_dir / "identity-registry.json")
    identity_registry.validate_and_register(
        customer_app_id=profile.app_id,
        package_name_android=profile.package_name,
        bundle_identifier=profile.bundle_identifier,
        published=profile.published,
        version_code=profile.version_code,
        production=profile.channel == "production" and android_enabled(profile.platforms),
        ios_production=profile.channel == "production" and ios_enabled(profile.platforms),
    )
    steps.append({"name": "validate", "status": "succeeded"})

    snapshots_dir = output_dir / "snapshots"
    snapshot = freeze_snapshot(profile, snapshots_dir)
    frozen = profile_from_snapshot(snapshot)
    steps.append(
        {
            "name": "snapshot",
            "status": "succeeded",
            "snapshot_id": snapshot["snapshot_id"],
        }
    )

    asset_root = Path(frozen.asset_root) if frozen.asset_root else output_dir
    secret_resolver = resolver or FailClosedSecretResolver()
    readiness = evaluate_readiness(
        frozen,
        asset_root=asset_root,
        resolver=secret_resolver,
        allow_local_test_signing=allow_local_test_signing,
    )

    applied: list[str] = []
    workspace: Path | None = None
    native_booked = android_enabled(frozen.platforms) or ios_enabled(frozen.platforms)
    if apply_workspace and native_booked and customer_app_path is not None:
        workspace = output_dir / "workspace"
        if workspace.exists():
            shutil.rmtree(workspace)
        shutil.copytree(
            customer_app_path,
            workspace,
            ignore=shutil.ignore_patterns(".git", "build", ".dart_tool"),
        )
        manifest = _to_build_manifest(frozen)
        dart_defines = {
            "PUBLIC_APP_ID": frozen.public_app_id,
            "API_BASE_URL": frozen.api_base_url,
            "APP_NAME": frozen.display_name,
            "PACKAGE_ID": frozen.vertical,
            "PACKAGE_VERSION": frozen.package_version,
        }
        applied = FlutterConfigApplier().apply(
            workspace,
            manifest,
            dart_defines,
            branding_assets_root=asset_root,
            customer_production=frozen.channel == "production",
        )
        _write_extended_factory_config(workspace, frozen, snapshot["snapshot_id"])
        _patch_customer_signing_gradle(workspace)
        steps.append({"name": "apply", "status": "succeeded", "changed_files": applied})
    else:
        steps.append({"name": "apply", "status": "skipped"})

    steps.append(
        {
            "name": "assets",
            "status": "succeeded",
            "android_assets": readiness["android_assets"]["status"],
        }
    )

    signing_ok = True
    signing_error = None
    if android_enabled(frozen.platforms) and frozen.channel == "production":
        try:
            assert_customer_production_signing(
                frozen.android_signing,
                resolver=secret_resolver,
                allow_local_test=False,
                tenant_id=frozen.tenant_id,
                customer_app_id=frozen.app_id,
            )
            steps.append({"name": "signing-check", "status": "succeeded"})
        except SigningGuardError as exc:
            signing_ok = False
            signing_error = str(exc)
            steps.append({"name": "signing-check", "status": "failed", "error": str(exc)})
            if not skip_build:
                raise
    else:
        steps.append({"name": "signing-check", "status": "skipped"})

    build_meta: dict[str, Any] = {
        "executed": False,
        "artifact_format": "aab",
        "aab_path": None,
        "aab_sha256": None,
        "reason": "SKIPPED",
        "signing": None,
    }
    if skip_build or not signing_ok:
        steps.append({"name": "build", "status": "skipped"})
    else:
        from app_factory.application.customer_release.aab import build_customer_aab
        from app_factory.infrastructure.flutter_runner import FlutterRunner

        if workspace is None:
            raise CustomerReleaseError("Customer workspace missing for AAB build")
        runner = flutter_runner or FlutterRunner()
        inspect = build_customer_aab(
            workspace,
            output_dir / "artifacts",
            profile=frozen,
            snapshot_id=snapshot["snapshot_id"],
            flutter_runner=runner,
            dart_defines={
                "PUBLIC_APP_ID": frozen.public_app_id,
                "API_BASE_URL": frozen.api_base_url,
                "APP_NAME": frozen.display_name,
                "PACKAGE_ID": frozen.vertical,
                "PACKAGE_VERSION": frozen.package_version,
            },
            signing_environ=signing_environ or {},
            upload_cert_sha256=upload_cert_sha256,
        )
        build_meta = {
            "executed": True,
            "artifact_format": "aab",
            "aab_path": inspect["aab_path"],
            "aab_sha256": inspect["aab_sha256"],
            "signing": inspect["signing"],
            "upload_certificate_sha256": inspect["upload_certificate_sha256"],
            "package_name": inspect["package_name"],
            "version_code": inspect["version_code"],
            "version_name": inspect["version_name"],
            "reason": None,
        }
        steps.append({"name": "build", "status": "succeeded", "inspect": {
            key: inspect[key]
            for key in (
                "package_name",
                "version_code",
                "signing",
                "aab_sha256",
                "debug_signing",
                "shared_owner_signing",
            )
        }})

    steps.append({"name": "verify", "status": "succeeded" if signing_ok else "blocked"})

    release_manifest = {
        "schema_version": 1,
        "kind": "customer-app-release-manifest",
        "release_id": frozen.release_id,
        "release_snapshot_id": snapshot["snapshot_id"],
        "app_id": frozen.app_id,
        "tenant_id": frozen.tenant_id,
        "vertical": frozen.vertical,
        "display_name": frozen.display_name,
        "package_name": frozen.package_name,
        "bundle_identifier": frozen.bundle_identifier,
        "release_version": frozen.release_version,
        "version_code": frozen.version_code,
        "platforms": frozen.to_dict()["platforms"],
        "readiness": readiness,
        "signing": {
            "android": public_signing_status(frozen.android_signing),
            "ios": frozen.ios_signing.to_public_dict(),
        },
        "build": build_meta,
        "google_play": {
            "connection_reference": None,
            "package_name": frozen.package_name,
            "target_track": None,
            "edit_reference": None,
            "version_code": frozen.version_code,
            "bundle_sha256": build_meta.get("aab_sha256"),
            "upload_status": "NOT_UPLOADED",
            "validation_status": None,
            "commit_status": None,
            "release_status": None,
            "verified_at": None,
        },
        "apple": {
            "connection_reference": None,
            "bundle_identifier": frozen.bundle_identifier,
            "upload_status": "NOT_UPLOADED",
            "destination": "testflight",
            "app_store_production_ready": "NOT_IMPLEMENTED",
        },
        "android_production_ready": "NOT_IMPLEMENTED",
        "generated_config": "workspace/build_config/app_factory_config.json" if workspace else None,
        "snapshot_path": str(snapshots_dir / f"{snapshot['snapshot_id']}.json"),
        "source_handoff": False,
        "steps": steps,
        "store_release": readiness["overall"] if signing_ok else STORE_RELEASE_READY.replace(
            "READY", "NOT_READY"
        ),
    }
    if not signing_ok:
        release_manifest["store_release"] = "STORE_RELEASE_NOT_READY"
        release_manifest["signing_error"] = signing_error
    _assert_no_secret_values(release_manifest)
    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    steps.append({"name": "release-manifest", "status": "succeeded", "path": str(manifest_path)})
    release_manifest["steps"] = steps
    manifest_path.write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return release_manifest


def _to_build_manifest(profile: CustomerAppReleaseProfile) -> AppBuildManifest:
    return AppBuildManifest(
        schema_version=1,
        app=AppIdentity(
            id=profile.app_id,
            display_name=profile.display_name,
            package_name_android=profile.package_name,
            bundle_id_ios=profile.bundle_identifier,
        ),
        tenant=TenantBinding(
            public_app_id=profile.public_app_id,
            package=profile.vertical,
            package_version=profile.package_version,
        ),
        branding=BrandingConfiguration(
            theme=profile.branding.theme,
            primary_color=profile.branding.primary_color,
            secondary_color=profile.branding.secondary_color,
            logo_asset=profile.branding.logo,
            splash_asset=profile.branding.splash,
            icon_asset=profile.branding.app_icon,
        ),
        features=FeatureConfiguration(flags=dict(profile.capabilities)),
        release=ReleaseConfiguration(
            channel=profile.channel if profile.channel in {"dev", "pilot", "production"} else "production",
            app_version=profile.release_version,
            build_number=profile.version_code,
        ),
        source=SourceRevision(
            customer_app_ref=profile.customer_app_ref,
            factory_compat_version=profile.factory_compat_version,
        ),
        api_base_url=profile.api_base_url,
        backend_origin=profile.backend_origin or None,
    )


def _write_extended_factory_config(
    workspace: Path,
    profile: CustomerAppReleaseProfile,
    snapshot_id: str,
) -> None:
    config_path = workspace / "build_config" / "app_factory_config.json"
    data: dict[str, Any] = {}
    if config_path.is_file():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    data.update(
        {
            "customer_store_release": True,
            "release_snapshot_id": snapshot_id,
            "release_id": profile.release_id,
            "android_application_id": profile.package_name,
            "bundle_id_ios": profile.bundle_identifier,
            "ios_production_ready": False,
            "legal_privacy_url": profile.legal.privacy_url,
            "legal_imprint_url": profile.legal.imprint_url,
            "support_url": profile.legal.support_url,
            "journey": profile.journey,
            "android_production_ready": False,
            "ios_production_ready": False,
            "bundle_id_ios": profile.bundle_identifier,
        }
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _patch_customer_signing_gradle(workspace: Path) -> None:
    gradle = workspace / "android" / "app" / "build.gradle.kts"
    if not gradle.is_file():
        return
    content = gradle.read_text(encoding="utf-8")
    if "BF_CUSTOMER_ANDROID_KEYSTORE_PATH" not in content:
        snippet = gradle_customer_release_signing_snippet().strip()
        if "buildTypes {" in content:
            content = content.replace("buildTypes {", snippet + "\n    buildTypes {", 1)
    if "signingConfigs.getByName(\"debug\")" in content:
        content = content.replace(
            'signingConfig = signingConfigs.getByName("debug")',
            'signingConfig = signingConfigs.getByName("release")',
            1,
        )
    gradle.write_text(content, encoding="utf-8")


def _assert_no_secret_values(payload: dict[str, Any]) -> None:
    blob = json.dumps(payload)
    lowered = blob.lower()
    for marker in SECRET_VALUE_MARKERS:
        if marker in lowered:
            raise CustomerReleaseError(f"Release manifest must not contain {marker}")
    hashed = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    del hashed
