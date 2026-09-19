"""Pet Supply App Factory consume — village_store@v1 + BusinessType PET_SUPPLY.

Pet Supply is not a factory package. Shared village_store screens are reused.
Distinct from appointment pet_grooming.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_pet_supply_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_PET_SUPPLY" not in defines
    pet_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(pet_package_defines, "pet_supply")
    assert pet_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "pet_supply" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
