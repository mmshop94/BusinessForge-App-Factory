"""Cheese Shop App Factory consume — village_store@v1 + BusinessType CHEESE_SHOP.

Cheese Shop is not a factory package. Shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_cheese_shop_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_CHEESE_SHOP" not in defines
    cheese_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(cheese_package_defines, "cheese_shop")
    assert cheese_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "cheese_shop" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
