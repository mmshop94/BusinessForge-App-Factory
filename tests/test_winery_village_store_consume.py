"""Winery App Factory consume — village_store@v1 + BusinessType WINERY.

Winery is not a factory package. Shared village_store screens are reused,
including Age Restriction projection on the Commerce path.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_winery_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_WINERY" not in defines
    winery_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(winery_package_defines, "winery")
    assert winery_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "winery" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
