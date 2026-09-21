"""Customer app release intake + Android signing foundation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app_factory.application.customer_release.change_class import (
    APP_RELEASE_REQUIRED_CHANGE,
    IOS_STORE_RELEASE_REQUIRED_CHANGE,
    LIVE_CONTENT_CHANGE,
    classify_intake_delta,
)
from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.pipeline import prepare_customer_release
from app_factory.application.customer_release.profile import profile_from_dict
from app_factory.application.customer_release.signing import (
    MappingSecretResolver,
    SHARED_OWNER_KEYSTORE_FORBIDDEN,
    assert_customer_production_signing,
)
from app_factory.application.customer_release.snapshot import freeze_snapshot, load_snapshot
from app_factory.application.image_assets import generate_default_icon
from app_factory.application.official_sales_demo_discovery import OFFICIAL_SALES_DEMO_SLUGS
from app_factory.domain.errors import (
    IdentityCollisionError,
    PackageMutationError,
    SigningGuardError,
    SnapshotImmutabilityError,
)
from tests.test_official_sales_generate_path import SLUG_RUNTIME_PACKAGE, _journey

SECRET_VALUE = "fixture-unlock-aa11-not-for-logs"
PUBLIC_APP_PREFIX = "app_01JABCDEFGHJKMNPQRSTVWX"


def _png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(generate_default_icon(primary_color="#8B4A2F", size=512))


def _write_assets(root: Path) -> None:
    _png(root / "branding" / "icon.png")
    _png(root / "branding" / "logo.png")
    _png(root / "branding" / "splash.png")
    _png(root / "store-assets" / "android" / "feature-graphic.png")
    _png(root / "store-assets" / "android" / "screenshots" / "phone-1.png")
    _png(root / "store-assets" / "android" / "screenshots" / "phone-2.png")


def _signing() -> dict:
    return {
        "android": {
            "provider": "CUSTOMER_UPLOAD_KEY",
            "alias_reference": "fixture://android-alias",
            "material_reference": "fixture://android-material",
            "store_unlock_reference": "fixture://android-store-unlock",
            "key_unlock_reference": "fixture://android-key-unlock",
            "play_app_signing_enabled": True,
            "status": "CONFIGURED",
        },
        "ios": {"provider": "ABSENT", "status": "NOT_SUBSCRIBED"},
    }


def _resolver() -> MappingSecretResolver:
    return MappingSecretResolver(
        {
            "fixture://android-alias": "upload",
            "fixture://android-material": "/tmp/not-a-real-keystore",
            "fixture://android-store-unlock": SECRET_VALUE,
            "fixture://android-key-unlock": SECRET_VALUE,
        }
    )


def _intake(
    root: Path,
    *,
    app_id: str = "dorfladen-hutthurm",
    display_name: str = "Dorfladen Hutthurm",
    package_name: str = "de.hutthurm.dorfladen",
    bundle_identifier: str | None = None,
    vertical: str = "village_store",
    platforms: str = "ANDROID_ONLY",
    version_code: int = 1,
    release_id: str = "rel-1",
    published: bool = False,
    public_app_id: str = "app_01JABCDEFGHJKMNPQRSTVWXYZ0",
    icon: str = "branding/icon.png",
    privacy_url: str = "https://dorfladen-hutthurm.de/datenschutz",
    imprint_url: str = "https://dorfladen-hutthurm.de/impressum",
    short_description: str = "Dorfladen Hutthurm — regionale Lebensmittel und Vorbestellung.",
    full_description: str = (
        "Die App des Dorfladens Hutthurm zeigt das aktuelle Sortiment, "
        "Vorbestellung und Öffnungszeiten des Betriebs. Kein Demo-Text."
    ),
    has_content: bool = True,
    icon_origin: str = "customer_provided",
    include_screenshots: bool = True,
) -> dict:
    store = {
        "short_description": short_description,
        "full_description": full_description,
        "category": "SHOPPING",
        "locale": "de-DE",
        "feature_graphic": "store-assets/android/feature-graphic.png" if include_screenshots else "",
        "screenshots": (
            [
                "store-assets/android/screenshots/phone-1.png",
                "store-assets/android/screenshots/phone-2.png",
            ]
            if include_screenshots
            else []
        ),
    }
    return {
        "schema_version": 1,
        "tenant_id": "tenant-hutthurm",
        "app_id": app_id,
        "vertical": vertical,
        "journey": _journey(vertical),
        "release_id": release_id,
        "release_version": "1.0.0",
        "version_code": version_code,
        "display_name": display_name,
        "package_name": package_name,
        "bundle_identifier": bundle_identifier or package_name,
        "platforms": {"selection": platforms},
        "branding": {
            "logo": "branding/logo.png",
            "app_icon": icon,
            "splash": "branding/splash.png",
            "primary_color": "#8B4A2F",
            "secondary_color": "#F2E3D5",
            "theme": "warm",
            "icon_origin": icon_origin,
        },
        "legal": {
            "privacy_url": privacy_url,
            "imprint_url": imprint_url,
            "support_url": "https://dorfladen-hutthurm.de/kontakt",
            "support_email": "laden@dorfladen-hutthurm.de",
        },
        "store": store,
        "capabilities": {"village_store": True, "ordering": True} if vertical in {"village_store", "butcher"} else {"appointments": True} if vertical.startswith("appointment_") else {"service_requests": True} if vertical.startswith(("service_", "field_service_")) else {"restaurant_menu": True},
        "content": {"has_customer_offerings": has_content, "offering_kind": "catalog"},
        "signing": _signing(),
        "public_app_id": public_app_id,
        "api_base_url": "https://api.bforge.de/api/v1",
        "channel": "production",
        "published": published,
        "asset_root": str(root),
        "customer_app_ref": "main",
    }


def _gate_status(result: dict, name: str) -> str:
    for gate in result["readiness"]["gates"]:
        if gate["name"] == name:
            return gate["status"]
    raise AssertionError(name)


def test_android_only_customer_release_ready(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path),
        tmp_path / "out",
        resolver=_resolver(),
        skip_build=True,
        apply_workspace=False,
    )
    dumped = json.dumps(result)
    assert SECRET_VALUE not in dumped
    assert result["store_release"] == "STORE_RELEASE_READY"
    assert _gate_status(result, "ANDROID_CONFIG_READY") == "READY"
    assert _gate_status(result, "ANDROID_SIGNING_READY") == "READY"
    assert _gate_status(result, "IOS_CONFIG_READY") == "NOT_SUBSCRIBED"
    assert _gate_status(result, "IOS_SIGNING_READY") == "NOT_SUBSCRIBED"
    assert result["signing"]["android"]["provider"] == "CUSTOMER_UPLOAD_KEY"


def test_ios_only_not_blocked_by_android(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, platforms="IOS_ONLY", package_name="de.hutthurm.dorfladen"),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert _gate_status(result, "ANDROID_CONFIG_READY") == "NOT_SUBSCRIBED"
    assert _gate_status(result, "ANDROID_SIGNING_READY") == "NOT_SUBSCRIBED"
    assert _gate_status(result, "ANDROID_ASSETS_READY") == "NOT_SUBSCRIBED"
    assert _gate_status(result, "IOS_CONFIG_READY") == "READY"
    assert _gate_status(result, "IOS_SIGNING_READY") == "BLOCKED"
    assert "FAILED" not in json.dumps(result["readiness"]["gates"])
    assert result["apple"]["app_store_production_ready"] == "NOT_IMPLEMENTED"


def test_android_and_ios_modelled(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, platforms="ANDROID_AND_IOS"),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert _gate_status(result, "ANDROID_SIGNING_READY") == "READY"
    assert _gate_status(result, "IOS_CONFIG_READY") == "READY"
    assert _gate_status(result, "IOS_SIGNING_READY") == "BLOCKED"
    assert "FAILED" not in json.dumps(result["readiness"]["gates"])
    assert result["store_release"] == "STORE_RELEASE_NOT_READY"


def test_missing_production_icon_blocks(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, icon="branding/missing-icon.png"),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert result["store_release"] == "STORE_RELEASE_NOT_READY"
    assert _gate_status(result, "BRANDING_READY") == "BLOCKED"


def test_missing_privacy_url_blocks(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, privacy_url=""),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert _gate_status(result, "LEGAL_READY") == "BLOCKED"


def test_missing_legal_identity_blocks(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, imprint_url="https://bforge.de/impressum"),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert _gate_status(result, "LEGAL_READY") == "BLOCKED"


def test_demo_placeholder_blocks(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(
            tmp_path,
            display_name="BusinessForge Demo Restaurant",
            short_description="Official Sales Demo — internal demo plane build",
            full_description="Official BusinessForge sales demo app for evaluation.",
            icon_origin="monogram_fallback",
            has_content=False,
        ),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert result["store_release"] == "STORE_RELEASE_NOT_READY"
    assert _gate_status(result, "CONTENT_READY") == "BLOCKED"
    assert _gate_status(result, "UNIQUENESS_READY") == "BLOCKED"


def test_package_collision_blocks(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    registry = CustomerAppIdentityRegistry(tmp_path / "identity.json")
    prepare_customer_release(
        _intake(tmp_path, app_id="app-a"),
        tmp_path / "out-a",
        registry=registry,
        resolver=_resolver(),
        apply_workspace=False,
    )
    with pytest.raises(IdentityCollisionError):
        prepare_customer_release(
            _intake(tmp_path, app_id="app-b", public_app_id="app_01JABCDEFGHJKMNPQRSTVWXYZ1"),
            tmp_path / "out-b",
            registry=registry,
            resolver=_resolver(),
            apply_workspace=False,
        )


def test_published_package_mutation_blocks(tmp_path: Path) -> None:
    registry = CustomerAppIdentityRegistry()
    registry.validate_and_register(
        customer_app_id="dorfladen-hutthurm",
        package_name_android="de.hutthurm.dorfladen",
        bundle_identifier="de.hutthurm.dorfladen",
        published=True,
        version_code=1,
        production=True,
    )
    with pytest.raises(PackageMutationError):
        registry.validate_and_register(
            customer_app_id="dorfladen-hutthurm",
            package_name_android="de.hutthurm.dorfladen2",
            bundle_identifier="de.hutthurm.dorfladen",
            published=True,
            version_code=2,
            production=True,
        )


def test_shared_owner_keystore_forbidden_for_customer_production() -> None:
    profile = profile_from_dict(
        _intake(Path("."), privacy_url="https://kunde.example-betrieb.de/datenschutz")
    )
    # rebuild signing as owner
    from app_factory.application.customer_release.profile import AndroidSigningIntake

    owner = AndroidSigningIntake(
        provider="SHARED_OWNER_KEYSTORE",
        alias_reference="env://BF_ANDROID_KEY_ALIAS",
        material_reference="env://BF_ANDROID_KEYSTORE_PATH",
        store_unlock_reference="env://BF_ANDROID_STORE_PASSWORD",
        key_unlock_reference="env://BF_ANDROID_KEY_PASSWORD",
        status="OWNER",
    )
    with pytest.raises(SigningGuardError) as exc:
        assert_customer_production_signing(owner, resolver=_resolver())
    assert SHARED_OWNER_KEYSTORE_FORBIDDEN in str(exc.value)


def test_customer_signing_reference_pass() -> None:
    from app_factory.application.customer_release.profile import AndroidSigningIntake

    intake = AndroidSigningIntake(
        provider="PLAY_APP_SIGNING",
        alias_reference="fixture://android-alias",
        material_reference="fixture://android-material",
        store_unlock_reference="fixture://android-store-unlock",
        key_unlock_reference="fixture://android-key-unlock",
        play_app_signing_enabled=True,
        status="CONFIGURED",
    )
    assert_customer_production_signing(intake, resolver=_resolver())


def test_snapshot_immutable(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path))
    first = freeze_snapshot(profile, tmp_path / "snaps", generated_at="2026-09-20T00:00:00+00:00")
    path = tmp_path / "snaps" / f"{first['snapshot_id']}.json"
    original = path.read_text(encoding="utf-8")
    mutated = json.loads(original)
    mutated["profile"]["display_name"] = "Hacked"
    path.write_text(json.dumps(mutated), encoding="utf-8")
    with pytest.raises(SnapshotImmutabilityError):
        load_snapshot(path)
    path.write_text(original, encoding="utf-8")
    again = freeze_snapshot(profile, tmp_path / "snaps")
    assert again["snapshot_id"] == first["snapshot_id"]


def test_second_release_new_version(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    registry = CustomerAppIdentityRegistry(tmp_path / "identity.json")
    first = prepare_customer_release(
        _intake(tmp_path, release_id="rel-1", version_code=1),
        tmp_path / "r1",
        registry=registry,
        resolver=_resolver(),
        apply_workspace=False,
    )
    second = prepare_customer_release(
        _intake(tmp_path, release_id="rel-2", version_code=2, display_name="Dorfladen Hutthurm Plus"),
        tmp_path / "r2",
        registry=registry,
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert first["package_name"] == second["package_name"]
    assert second["version_code"] == 2
    assert second["release_snapshot_id"] != first["release_snapshot_id"]
    assert Path(first["snapshot_path"]).is_file()


def test_live_content_does_not_require_store_release() -> None:
    previous = {"display_name": "Dorfladen", "products": [{"sku": "a", "price": 1}]}
    current = {"display_name": "Dorfladen", "products": [{"sku": "a", "price": 2}]}
    assert classify_intake_delta(previous, current) == LIVE_CONTENT_CHANGE
    renamed = {"display_name": "Neuer Name", "products": previous["products"]}
    assert classify_intake_delta(previous, renamed) == APP_RELEASE_REQUIRED_CHANGE
    ios_id = {"display_name": "Dorfladen", "bundle_identifier": "de.kunde.app"}
    assert (
        classify_intake_delta({"display_name": "Dorfladen", "bundle_identifier": "de.alt.app"}, ios_id)
        == IOS_STORE_RELEASE_REQUIRED_CHANGE
    )


def test_customer_apply_writes_identity_without_owner_keystore(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    app = tmp_path / "customer-app"
    app.mkdir()
    (app / "pubspec.yaml").write_text("name: businessforge_mobile\nversion: 0.5.9+1\n", encoding="utf-8")
    gradle = app / "android" / "app"
    gradle.mkdir(parents=True)
    (gradle / "build.gradle.kts").write_text(
        'applicationId = "com.businessforge.businessforge_mobile"\n    buildTypes {\n    }\n',
        encoding="utf-8",
    )
    manifest_dir = gradle / "src" / "main"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "AndroidManifest.xml").write_text(
        '<manifest><application android:label="placeholder"></application></manifest>',
        encoding="utf-8",
    )
    result = prepare_customer_release(
        _intake(tmp_path),
        tmp_path / "out",
        customer_app_path=app,
        resolver=_resolver(),
        apply_workspace=True,
        skip_build=True,
    )
    workspace = tmp_path / "out" / "workspace"
    gradle_text = (workspace / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'applicationId = "de.hutthurm.dorfladen"' in gradle_text
    assert "BF_CUSTOMER_ANDROID_KEYSTORE_PATH" in gradle_text
    assert "BF_ANDROID_KEYSTORE_PATH" not in gradle_text
    config = json.loads((workspace / "build_config" / "app_factory_config.json").read_text(encoding="utf-8"))
    assert config["display_name"] == "Dorfladen Hutthurm"
    assert config["public_app_id"] == "app_01JABCDEFGHJKMNPQRSTVWXYZ0"
    assert config["tenant_package"] == "village_store"
    assert config["customer_store_release"] is True
    assert config["android_application_id"] == "de.hutthurm.dorfladen"
    assert SECRET_VALUE not in json.dumps(result)
    assert SECRET_VALUE not in gradle_text
    assert SECRET_VALUE not in json.dumps(config)


def test_35_official_verticals_android_only_generate_and_profile(tmp_path: Path) -> None:
    assert len(OFFICIAL_SALES_DEMO_SLUGS) == 35
    _write_assets(tmp_path)
    registry = CustomerAppIdentityRegistry(tmp_path / "identity.json")
    for index, slug in enumerate(OFFICIAL_SALES_DEMO_SLUGS):
        package = SLUG_RUNTIME_PACKAGE[slug]
        public_app_id = f"{PUBLIC_APP_PREFIX}{index:03d}"
        result = prepare_customer_release(
            _intake(
                tmp_path,
                app_id=f"kunde-{slug.replace('demo-', '')}",
                display_name=f"Betrieb {slug.replace('demo-', '').replace('-', ' ').title()}",
                package_name=f"de.kunde.n{index:02d}.app",
                vertical=package,
                public_app_id=public_app_id,
                release_id=f"rel-{index}",
            ),
            tmp_path / f"out-{index}",
            registry=registry,
            resolver=_resolver(),
            apply_workspace=False,
        )
        assert _gate_status(result, "ANDROID_CONFIG_READY") == "READY"
        assert _gate_status(result, "IOS_CONFIG_READY") == "NOT_SUBSCRIBED"
        assert result["readiness"]["uniqueness"]["ready"] is True
    assert len(SLUG_RUNTIME_PACKAGE) == 35
