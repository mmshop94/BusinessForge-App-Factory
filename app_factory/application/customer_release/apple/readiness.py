"""iOS platform readiness states. Unbooked iOS is NOT_SUBSCRIBED, never FAILED."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_factory.application.customer_release.apple.assets import evaluate_ios_assets
from app_factory.application.customer_release.apple.executor import (
    IOS_BUILD_EXECUTOR_REQUIRED,
    probe_ios_build_executor,
)
from app_factory.application.customer_release.apple.signing import (
    APPLE_SIGNING_CONFIGURATION_REQUIRED,
    assert_customer_ios_signing,
    profile_from_intake,
)
from app_factory.application.customer_release.apple.store import (
    evaluate_apple_privacy_intake,
    evaluate_ios_store_metadata,
)
from app_factory.application.customer_release.platforms import ios_enabled
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.customer_release.signing import SecretReferenceResolver
from app_factory.application.package_identity import (
    is_reserved_android_package,
    validate_ios_bundle_format,
)
from app_factory.domain.errors import SigningGuardError

IOS_NOT_SUBSCRIBED = "IOS_NOT_SUBSCRIBED"
IOS_CONFIG_REQUIRED = "IOS_CONFIG_REQUIRED"
IOS_IDENTITY_READY = "IOS_IDENTITY_READY"
IOS_ASSETS_READY = "IOS_ASSETS_READY"
IOS_SIGNING_REQUIRED = "IOS_SIGNING_REQUIRED"
IOS_BUILD_READY = "IOS_BUILD_READY"
IOS_ARCHIVE_READY = "IOS_ARCHIVE_READY"
IOS_IPA_READY = "IOS_IPA_READY"
APP_STORE_CONNECTION_REQUIRED = "APP_STORE_CONNECTION_REQUIRED"
APP_STORE_APP_RECORD_REQUIRED = "APP_STORE_APP_RECORD_REQUIRED"
TESTFLIGHT_DELIVERY_READY = "TESTFLIGHT_DELIVERY_READY"
TESTFLIGHT_RELEASED = "TESTFLIGHT_RELEASED"
NOT_SUBSCRIBED = "NOT_SUBSCRIBED"


def evaluate_ios_platform_readiness(
    profile: CustomerAppReleaseProfile,
    *,
    asset_root: Path,
    resolver: SecretReferenceResolver | None = None,
    allow_local_test_signing: bool = False,
) -> dict[str, Any]:
    if not ios_enabled(profile.platforms):
        return {
            "booked": False,
            "state": IOS_NOT_SUBSCRIBED,
            "states": {"ios": NOT_SUBSCRIBED},
            "failed": False,
            "executor": {"status": NOT_SUBSCRIBED},
            "app_store_production": "NOT_IMPLEMENTED",
        }

    states: dict[str, str] = {}
    blockers: list[str] = []
    identity_ready = True
    try:
        bundle = validate_ios_bundle_format(profile.bundle_identifier)
    except ValueError:
        bundle = profile.bundle_identifier
        identity_ready = False
        blockers.append(IOS_CONFIG_REQUIRED)
    if profile.channel == "production" and is_reserved_android_package(profile.bundle_identifier):
        identity_ready = False
        blockers.append("IOS_RESERVED_NAMESPACE")
    if not profile.release_version or profile.version_code < 1:
        identity_ready = False
        blockers.append("VERSION_INVALID")
    states["identity"] = IOS_IDENTITY_READY if identity_ready else IOS_CONFIG_REQUIRED

    assets = evaluate_ios_assets(profile, asset_root)
    states["assets"] = assets["status"]
    if assets["status"] != "IOS_ASSETS_READY":
        blockers.append("IOS_ASSETS_INCOMPLETE")

    signing_profile = profile_from_intake(
        profile.ios_signing,
        customer_app_id=profile.app_id,
        tenant_id=profile.tenant_id,
        bundle_identifier=bundle,
    )
    try:
        assert_customer_ios_signing(
            signing_profile,
            resolver=resolver,
            allow_local_test=allow_local_test_signing and profile.channel != "production",
        )
        states["signing"] = "IOS_SIGNING_READY"
    except SigningGuardError:
        states["signing"] = IOS_SIGNING_REQUIRED
        blockers.append(APPLE_SIGNING_CONFIGURATION_REQUIRED)

    executor = probe_ios_build_executor()
    states["executor"] = executor["status"]
    if executor["status"] == IOS_BUILD_EXECUTOR_REQUIRED:
        blockers.append(IOS_BUILD_EXECUTOR_REQUIRED)

    states["archive"] = IOS_BUILD_EXECUTOR_REQUIRED
    states["ipa"] = IOS_BUILD_EXECUTOR_REQUIRED
    states["app_store_connection"] = APP_STORE_CONNECTION_REQUIRED
    states["app_record"] = APP_STORE_APP_RECORD_REQUIRED
    states["testflight"] = "IMPLEMENTATION_READY"
    metadata = evaluate_ios_store_metadata(profile)
    privacy = evaluate_apple_privacy_intake(profile)

    overall = IOS_IDENTITY_READY if identity_ready else IOS_CONFIG_REQUIRED
    if identity_ready and assets["status"] == "IOS_ASSETS_READY":
        overall = IOS_ASSETS_READY
    if states["signing"] == IOS_SIGNING_REQUIRED:
        overall = IOS_SIGNING_REQUIRED
    if executor["status"] == IOS_BUILD_EXECUTOR_REQUIRED:
        overall = IOS_BUILD_EXECUTOR_REQUIRED

    return {
        "booked": True,
        "state": overall,
        "states": states,
        "blockers": blockers,
        "failed": False,
        "bundle_identifier": bundle,
        "display_name": profile.display_name,
        "version": profile.release_version,
        "build_number": profile.version_code,
        "executor": executor,
        "assets": assets,
        "metadata": metadata,
        "privacy": privacy,
        "app_store_production": "NOT_IMPLEMENTED",
        "live_apple_proof": "BLOCKED_EXTERNAL",
        "customer_owned_publishing_proven": False,
    }
