"""Bakery App Factory consume — village_store@v1 + BusinessType BAKERY.

Bakery is not a factory package. The shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_bakery_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_BAKERY" not in defines
    bakery_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(bakery_package_defines, "bakery")
    assert bakery_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "bakery" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
