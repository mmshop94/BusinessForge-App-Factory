"""App Factory — carrier age verification reuse (no dhl@v1 / ident-check@v1)."""

from __future__ import annotations

from app_factory.application.build_planner import BuildPlanner


def test_no_dhl_or_ident_check_app_package() -> None:
    defines: dict[str, str] = {}
    BuildPlanner._apply_package_features(defines, "village_store")
    assert defines.get("FEATURE_VILLAGE_STORE") == "true"
    for pkg in ("dhl", "ident_check", "ident-check"):
        empty: dict[str, str] = {}
        BuildPlanner._apply_package_features(empty, pkg)
        assert empty == {}
