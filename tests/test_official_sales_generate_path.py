"""Config proof: 35 official sales demos have an AppFactory generate path.

Does not run 35 native builds. Maps slug → runtime package → compat → Flutter journey.
"""

from __future__ import annotations

import json

from app_factory.application.official_sales_demo_discovery import (
    OFFICIAL_SALES_DEMO_SLUGS,
    OfficialSalesDemoRecord,
    features_for_record,
)
from app_factory.infrastructure.paths import compat_path

# Fallback runtime packages from official_sales_demo_discovery (no live API).
SLUG_RUNTIME_PACKAGE: dict[str, str] = {
    "demo-restaurant": "restaurant",
    "demo-village-store": "village_store",
    "demo-bakery": "village_store",
    "demo-florist": "village_store",
    "demo-butcher": "butcher",
    "demo-farm-shop": "village_store",
    "demo-beverage-store": "village_store",
    "demo-delicatessen": "village_store",
    "demo-winery": "village_store",
    "demo-cheese-shop": "village_store",
    "demo-fish-shop": "village_store",
    "demo-garden-center": "village_store",
    "demo-pet-supply": "village_store",
    "demo-hairdresser": "appointment_hairdresser",
    "demo-barber": "appointment_barber",
    "demo-nail-studio": "appointment_nail_studio",
    "demo-cosmetics": "appointment_cosmetics",
    "demo-massage": "appointment_massage",
    "demo-tattoo": "appointment_tattoo",
    "demo-piercing": "appointment_piercing",
    "demo-lash-brow": "appointment_cosmetics",
    "demo-foot-care": "appointment_foot_care",
    "demo-pet-grooming": "appointment_pet_grooming",
    "demo-bicycle-workshop": "service_bicycle_workshop",
    "demo-device-shop": "service_device_shop",
    "demo-motorcycle-workshop": "service_motorcycle_workshop",
    "demo-electrician": "field_service_electrician",
    "demo-appliance-service": "field_service_appliance",
    "demo-hvac-service": "field_service_hvac",
    "demo-sanitary-service": "field_service_sanitary",
    "demo-auto-workshop": "service_auto_workshop",
    "demo-vehicle-detailing": "service_vehicle_detailing",
    "demo-cleaning-service": "field_service_cleaning",
    "demo-landscaping-service": "field_service_landscaping",
    "demo-caretaker": "field_service_caretaker",
}


def _journey(package: str) -> str:
    if package == "restaurant":
        return "restaurant"
    if package in {"village_store", "butcher"}:
        return "commerce"
    if package.startswith("appointment_"):
        return "appointment"
    if package.startswith("service_"):
        return "shop"
    if package.startswith("field_service_"):
        return "field"
    return "unknown"


def test_official_sales_generate_path_is_35() -> None:
    assert len(OFFICIAL_SALES_DEMO_SLUGS) == 35
    assert "demo-workshop" not in OFFICIAL_SALES_DEMO_SLUGS
    assert set(SLUG_RUNTIME_PACKAGE) == set(OFFICIAL_SALES_DEMO_SLUGS)

    packages = json.loads(compat_path().read_text(encoding="utf-8"))["packages"]
    missing: list[str] = []
    journeys: dict[str, str] = {}
    for slug, package in SLUG_RUNTIME_PACKAGE.items():
        if package not in packages:
            missing.append(f"{slug}:{package}")
        journeys[slug] = _journey(package)
        record = OfficialSalesDemoRecord(
            slug=slug,
            business_name=slug,
            display_name=slug,
            public_app_id="app_1DZR48F5F7MCFXS2ZM89V6EADV",
            runtime_package=package,
            package_version="v1",
            primary_color="#2563EB",
            secondary_color="#EFF6FF",
            theme="modern",
            booking_enabled=True,
            hero_media_id=None,
            logo_media_id=None,
            design_template_id=None,
            bootstrap_ok=True,
            login_ok=True,
        )
        flags = features_for_record(record)
        if journeys[slug] == "appointment":
            assert flags.get("appointments") is True
        elif journeys[slug] == "commerce":
            assert flags.get("village_store") is True
        elif journeys[slug] == "restaurant":
            assert flags.get("restaurant_menu") is True
        elif journeys[slug] in {"shop", "field"}:
            assert flags.get("service_requests") is True

    assert missing == []
    assert set(journeys.values()) == {"restaurant", "commerce", "appointment", "shop", "field"}
    assert sum(1 for value in journeys.values() if value == "appointment") == 10
    assert sum(1 for value in journeys.values() if value == "commerce") == 12
    assert sum(1 for value in journeys.values() if value == "shop") == 5
    assert sum(1 for value in journeys.values() if value == "field") == 7
    assert sum(1 for value in journeys.values() if value == "restaurant") == 1
