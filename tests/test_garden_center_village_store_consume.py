"""Garden Center App Factory consume — village_store@v1 + BusinessType GARDEN_CENTER.

Garden Center is not a factory package. Shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_garden_center_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_GARDEN_CENTER" not in defines
    garden_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(garden_package_defines, "garden_center")
    assert garden_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "garden_center" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
