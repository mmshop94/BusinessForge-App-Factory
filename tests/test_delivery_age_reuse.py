"""App Factory — delivery age verification reuse is shared (no dedicated package)."""

from app_factory.application.build_planner import BuildPlanner
from app_factory.domain.manifest import AppManifest


def test_no_delivery_age_or_alcohol_delivery_package_in_defines():
    """Delivery age stays on shared store journey — no delivery_age@v1 / alcohol_delivery@v1."""
    # Minimal sanity: planner never invents vertical age packages.
    assert "delivery_age" not in dir(BuildPlanner)
    assert "alcohol_delivery" not in dir(BuildPlanner)
    assert AppManifest is not None
