from __future__ import annotations

import json

from app_factory.application.demo_api_origins import (
    LAN_DEMO_API_BASE_URL,
    PUBLIC_DEMO_API_BASE_URL,
    DemoApiOriginError,
    assert_official_sales_demo_api_origin,
)
from app_factory.application.official_sales_demo_discovery import OFFICIAL_SALES_DEMO_SLUGS
from app_factory.application.package_identity import android_application_id_from_public_app_id


def test_official_sales_demo_slug_count() -> None:
    assert len(OFFICIAL_SALES_DEMO_SLUGS) == 11
    assert "demo-restaurant" in OFFICIAL_SALES_DEMO_SLUGS
    assert "demo-pet-grooming" in OFFICIAL_SALES_DEMO_SLUGS
    assert not any(slug.startswith("test-appointment-") for slug in OFFICIAL_SALES_DEMO_SLUGS)


def test_android_id_from_public_app_id() -> None:
    public_app_id = "app_1DZR48F5F7MCFXS2ZM89V6EADV"
    android_id = android_application_id_from_public_app_id(public_app_id)
    assert android_id == "de.bforge.app.u1dzr48f5f7mcfxs2zm89v6eadv"


def test_build_manifest_dict_structure() -> None:
    from app_factory.application.official_sales_demo_discovery import OfficialSalesDemoRecord
    from app_factory.application.official_sales_demo_manifests import build_manifest_dict

    record = OfficialSalesDemoRecord(
        slug="demo-hairdresser",
        business_name="Salon Haarzeit",
        display_name="Salon Haarzeit",
        public_app_id="app_1DZR48F5F7MCFXS2ZM89V6EADV",
        runtime_package="appointment_hairdresser",
        package_version="v1",
        primary_color="#8B6914",
        secondary_color="#F5E6C8",
        theme="modern",
        booking_enabled=True,
        hero_media_id="adb940c6-aa74-40dc-a4c0-01dc39ba13f4",
        logo_media_id=None,
        design_template_id="service_first",
        bootstrap_ok=True,
        login_ok=True,
    )
    manifest = build_manifest_dict(record, api_base_url="http://192.168.178.95:8090/api/v1")
    assert manifest["tenant"]["public_app_id"] == record.public_app_id
    assert manifest["features"]["appointments"] is True
    assert manifest["api_base_url"].endswith("/api/v1")


def test_official_sales_demo_api_origin_guard() -> None:
    assert assert_official_sales_demo_api_origin(LAN_DEMO_API_BASE_URL) == LAN_DEMO_API_BASE_URL
    assert (
        assert_official_sales_demo_api_origin(PUBLIC_DEMO_API_BASE_URL) == PUBLIC_DEMO_API_BASE_URL
    )
    try:
        assert_official_sales_demo_api_origin("https://api.bforge.de/api/v1")
    except DemoApiOriginError:
        return
    raise AssertionError("production API origin must be rejected")


def test_public_demo_api_origin_is_fail_closed() -> None:
    from app_factory.application.demo_api_origins import assert_public_demo_api_origin

    assert assert_public_demo_api_origin(PUBLIC_DEMO_API_BASE_URL) == PUBLIC_DEMO_API_BASE_URL
    for forbidden in (
        LAN_DEMO_API_BASE_URL,
        "https://api.bforge.de/api/v1",
        "http://demo-api.bforge.de/api/v1",
        "https://127.0.0.1/api/v1",
        "https://localhost/api/v1",
    ):
        try:
            assert_public_demo_api_origin(forbidden)
        except DemoApiOriginError:
            continue
        raise AssertionError(f"must reject {forbidden}")


def test_production_host_not_confused_with_demo_api() -> None:
    from app_factory.application.demo_api_origins import production_api_host_present

    assert production_api_host_present(b"https://demo-api.bforge.de/api/v1") is False
    assert production_api_host_present(b"https://api.bforge.de/api/v1") is True


def test_preserve_legacy_lan_layout(tmp_path) -> None:
    from app_factory.application.demo_apps_layout import preserve_legacy_lan_builds

    root = tmp_path / "BusinessForge-Demo-Apps"
    demo = root / "demo-restaurant"
    demo.mkdir(parents=True)
    (demo / "apk").mkdir()
    (demo / "apk" / "demo-restaurant-release.apk").write_bytes(b"apk")
    matrix = {
        "api_base_url": "http://192.168.178.95:8090/api/v1",
        "apps": {
            "demo-restaurant": {
                "apk_path": str(demo / "apk" / "demo-restaurant-release.apk"),
            }
        },
    }
    (root / "manifest.json").write_text(json.dumps(matrix), encoding="utf-8")
    lan = preserve_legacy_lan_builds(root)
    moved = lan / "demo-restaurant" / "apk" / "demo-restaurant-release.apk"
    assert moved.is_file()
    assert not demo.exists()
    rewritten = json.loads((lan / "manifest.json").read_text(encoding="utf-8"))
    assert str(lan) in rewritten["apps"]["demo-restaurant"]["apk_path"]
    assert (root / "public").is_dir()


def test_inspect_artifact_distinguishes_demo_api(tmp_path) -> None:
    import zipfile

    from app_factory.application.demo_api_origins import inspect_android_artifact_origins

    apk = tmp_path / "app.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr(
            "lib/arm64-v8a/libapp.so",
            b"API_BASE_URL=https://demo-api.bforge.de/api/v1",
        )
    report = inspect_android_artifact_origins(apk)
    assert report["public_demo_origin_present"] is True
    assert report["production_origin_present"] is False
    assert report["lan_origin_present"] is False


def test_artifact_scan_ignores_flutter_loopback_default(tmp_path) -> None:
    import zipfile

    from app_factory.application.demo_api_origins import (
        PUBLIC_DEMO_API_BASE_URL,
        assert_public_artifact_origins,
        lan_origin_present,
    )

    assert lan_origin_present(b"http://127.0.0.1:8000/api/v1 localhost") is False
    assert lan_origin_present(b"http://192.168.178.95:8090/api/v1") is True

    apk = tmp_path / "app.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr(
            "lib/arm64-v8a/libapp.so",
            b"http://127.0.0.1:8000/api/v1 https://demo-api.bforge.de/api/v1",
        )
        archive.writestr(
            "assets/flutter_assets/build_config/app_factory_config.json",
            '{"api_base_url": "https://demo-api.bforge.de/api/v1"}',
        )
    report = assert_public_artifact_origins(apk)
    assert report["lan_origin_present"] is False
    assert report["factory_config_api_base_url"] == PUBLIC_DEMO_API_BASE_URL
    assert report["snapshot_loopback_present"] is True


def test_artifact_scan_reads_aab_base_paths(tmp_path) -> None:
    import zipfile

    from app_factory.application.demo_api_origins import (
        PUBLIC_DEMO_API_BASE_URL,
        assert_public_artifact_origins,
    )

    aab = tmp_path / "app.aab"
    with zipfile.ZipFile(aab, "w") as archive:
        archive.writestr(
            "base/lib/arm64-v8a/libapp.so",
            b"https://demo-api.bforge.de/api/v1",
        )
        archive.writestr(
            "base/assets/flutter_assets/build_config/app_factory_config.json",
            '{"api_base_url": "https://demo-api.bforge.de/api/v1"}',
        )
    report = assert_public_artifact_origins(aab)
    assert report["factory_config_api_base_url"] == PUBLIC_DEMO_API_BASE_URL
    assert report["public_demo_origin_present"] is True
