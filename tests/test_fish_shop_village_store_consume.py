"""Fish Shop App Factory consume — village_store@v1 + BusinessType FISH_SHOP.

Fish Shop is not a factory package. Shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_fish_shop_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_FISH_SHOP" not in defines
    fish_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(fish_package_defines, "fish_shop")
    assert fish_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "fish_shop" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
