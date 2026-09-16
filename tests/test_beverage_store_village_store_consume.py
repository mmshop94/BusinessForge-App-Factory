"""Beverage Store App Factory consume — village_store@v1 + BusinessType BEVERAGE_STORE.

Beverage Store is not a factory package. Shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_beverage_store_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_BEVERAGE_STORE" not in defines
    beverage_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(beverage_package_defines, "beverage_store")
    assert beverage_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "beverage_store" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
