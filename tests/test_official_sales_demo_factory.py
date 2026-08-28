from __future__ import annotations

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
