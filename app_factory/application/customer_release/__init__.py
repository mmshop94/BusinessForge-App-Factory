"""Customer app release intake — snapshots, gates, per-customer Android signing."""

from app_factory.application.customer_release.change_class import (
    APP_RELEASE_REQUIRED_CHANGE,
    LIVE_CONTENT_CHANGE,
    classify_intake_delta,
)
from app_factory.application.customer_release.gates import evaluate_readiness
from app_factory.application.customer_release.pipeline import prepare_customer_release
from app_factory.application.customer_release.platforms import PlatformSelection, platform_status
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.customer_release.snapshot import freeze_snapshot, load_snapshot

__all__ = [
    "APP_RELEASE_REQUIRED_CHANGE",
    "LIVE_CONTENT_CHANGE",
    "CustomerAppReleaseProfile",
    "PlatformSelection",
    "classify_intake_delta",
    "evaluate_readiness",
    "freeze_snapshot",
    "load_snapshot",
    "platform_status",
    "prepare_customer_release",
]
