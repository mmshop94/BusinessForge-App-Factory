"""Florist App Factory consume — village_store@v1 + BusinessType FLORIST.

Florist is not a factory package. The shared village_store screens are reused.
"""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_florist_consumes_village_store_shared_commerce_screens() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines["FEATURE_VILLAGE_STORE"] == "true"
    assert defines["FEATURE_PAYMENTS"] == "true"
    assert "FEATURE_FLORIST" not in defines
    florist_package_defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(florist_package_defines, "florist")
    assert florist_package_defines == {}
    assert "village_store" in BuildPlanner.FLUTTER_FEATURE_FLAGS
    assert "florist" not in BuildPlanner.FLUTTER_FEATURE_FLAGS
