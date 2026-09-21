"""Machine-readable store readiness gates. Unbooked platforms are NOT_SUBSCRIBED, never FAILED."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app_factory.application.customer_release.apple.assets import (
    IOS_ASSETS_READY as IOS_ASSETS_CATALOG_READY,
    evaluate_ios_assets,
)
from app_factory.application.customer_release.apple.signing import (
    APPLE_SIGNING_CONFIGURATION_REQUIRED,
    assert_customer_ios_signing,
    profile_from_intake,
)
from app_factory.application.customer_release.assets import (
    ANDROID_ASSETS_READY,
    evaluate_android_assets,
)
from app_factory.application.customer_release.platforms import (
    android_enabled,
    ios_enabled,
    platform_status,
)
from app_factory.application.customer_release.profile import (
    CustomerAppReleaseProfile,
    looks_like_demo_name,
    looks_like_generic_legal_url,
)
from app_factory.application.customer_release.signing import (
    assert_customer_production_signing,
    FailClosedSecretResolver,
    SecretReferenceResolver,
)
from app_factory.application.customer_release.uniqueness import evaluate_uniqueness
from app_factory.domain.errors import SigningGuardError

NOT_SUBSCRIBED = "NOT_SUBSCRIBED"
READY = "READY"
BLOCKED = "BLOCKED"

STORE_RELEASE_NOT_READY = "STORE_RELEASE_NOT_READY"
STORE_RELEASE_READY = "STORE_RELEASE_READY"

GATE_NAMES = (
    "CONTENT_READY",
    "BRANDING_READY",
    "LEGAL_READY",
    "UNIQUENESS_READY",
    "ANDROID_CONFIG_READY",
    "ANDROID_SIGNING_READY",
    "ANDROID_ASSETS_READY",
    "IOS_CONFIG_READY",
    "IOS_SIGNING_READY",
    "IOS_ASSETS_READY",
)


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "blockers": list(self.blockers)}


def evaluate_readiness(
    profile: CustomerAppReleaseProfile,
    *,
    asset_root: Path,
    resolver: SecretReferenceResolver | None = None,
    allow_local_test_signing: bool = False,
) -> dict[str, Any]:
    uniqueness = evaluate_uniqueness(profile)
    assets = evaluate_android_assets(profile, asset_root)
    ios_assets = evaluate_ios_assets(profile, asset_root)
    secret_resolver = resolver or FailClosedSecretResolver()

    content = _content_gate(profile)
    branding = _branding_gate(profile, asset_root)
    legal = _legal_gate(profile)
    uniqueness_gate = GateResult(
        "UNIQUENESS_READY",
        READY if uniqueness.ready else BLOCKED,
        uniqueness.blockers,
    )

    android_booked = android_enabled(profile.platforms)
    ios_booked = ios_enabled(profile.platforms)

    if android_booked:
        android_config = _android_config_gate(profile)
        android_signing = _android_signing_gate(
            profile,
            secret_resolver,
            allow_local_test_signing=allow_local_test_signing,
        )
        android_assets = GateResult(
            "ANDROID_ASSETS_READY",
            READY if assets["status"] == ANDROID_ASSETS_READY else BLOCKED,
            () if assets["status"] == ANDROID_ASSETS_READY else ("ANDROID_ASSETS_INCOMPLETE",),
        )
    else:
        android_config = GateResult("ANDROID_CONFIG_READY", NOT_SUBSCRIBED, ())
        android_signing = GateResult("ANDROID_SIGNING_READY", NOT_SUBSCRIBED, ())
        android_assets = GateResult("ANDROID_ASSETS_READY", NOT_SUBSCRIBED, ())

    if ios_booked:
        ios_config = _ios_config_gate(profile)
        ios_signing = _ios_signing_gate(
            profile,
            secret_resolver,
            allow_local_test_signing=allow_local_test_signing,
        )
        ios_assets_gate = GateResult(
            "IOS_ASSETS_READY",
            READY if ios_assets["status"] == IOS_ASSETS_CATALOG_READY else BLOCKED,
            () if ios_assets["status"] == IOS_ASSETS_CATALOG_READY else ("IOS_ASSETS_INCOMPLETE",),
        )
    else:
        ios_config = GateResult("IOS_CONFIG_READY", NOT_SUBSCRIBED, ())
        ios_signing = GateResult("IOS_SIGNING_READY", NOT_SUBSCRIBED, ())
        ios_assets_gate = GateResult("IOS_ASSETS_READY", NOT_SUBSCRIBED, ())

    gates = (
        content,
        branding,
        legal,
        uniqueness_gate,
        android_config,
        android_signing,
        android_assets,
        ios_config,
        ios_signing,
        ios_assets_gate,
    )
    blocking = [
        gate
        for gate in gates
        if gate.status == BLOCKED
    ]
    overall = STORE_RELEASE_READY if not blocking else STORE_RELEASE_NOT_READY
    return {
        "overall": overall,
        "platforms": {
            "selection": profile.platforms.value,
            "android": platform_status(profile.platforms, "android").value,
            "ios": platform_status(profile.platforms, "ios").value,
        },
        "gates": [gate.to_dict() for gate in gates],
        "uniqueness": uniqueness.to_dict(),
        "android_assets": assets,
        "ios_assets": ios_assets if ios_booked else {"status": NOT_SUBSCRIBED},
        "blockers": [item for gate in blocking for item in gate.blockers] or [
            gate.name for gate in blocking
        ],
    }


def _content_gate(profile: CustomerAppReleaseProfile) -> GateResult:
    blockers: list[str] = []
    if looks_like_demo_name(profile.display_name):
        blockers.append("DEMO_NAME")
    if not profile.display_name.strip() or len(profile.display_name.strip()) < 3:
        blockers.append("APP_NAME_INVALID")
    if not profile.content.has_customer_offerings:
        blockers.append("MISSING_CUSTOMER_CONTENT")
    return GateResult("CONTENT_READY", READY if not blockers else BLOCKED, tuple(blockers))


def _branding_gate(profile: CustomerAppReleaseProfile, asset_root: Path) -> GateResult:
    blockers: list[str] = []
    icon = asset_root / profile.branding.app_icon if profile.branding.app_icon else None
    if icon is None or not icon.is_file():
        blockers.append("PRODUCTION_ICON_MISSING")
    if profile.branding.icon_origin != "customer_provided":
        blockers.append("PRODUCTION_ICON_NOT_CUSTOMER")
    if not profile.branding.primary_color.startswith("#"):
        blockers.append("BRANDING_COLOR_INVALID")
    return GateResult("BRANDING_READY", READY if not blockers else BLOCKED, tuple(blockers))


def _legal_gate(profile: CustomerAppReleaseProfile) -> GateResult:
    blockers: list[str] = []
    if looks_like_generic_legal_url(profile.legal.privacy_url):
        blockers.append("PRIVACY_URL_MISSING")
    if looks_like_generic_legal_url(profile.legal.imprint_url):
        blockers.append("LEGAL_IDENTITY_MISSING")
    if "@" not in profile.legal.support_email:
        blockers.append("SUPPORT_CONTACT_MISSING")
    if not _https_url(profile.legal.support_url):
        blockers.append("SUPPORT_URL_MISSING")
    return GateResult("LEGAL_READY", READY if not blockers else BLOCKED, tuple(blockers))


def _android_config_gate(profile: CustomerAppReleaseProfile) -> GateResult:
    blockers: list[str] = []
    from app_factory.application.package_identity import (
        is_reserved_android_package,
        GENERIC_ANDROID_PACKAGE_PATTERN,
    )

    if not GENERIC_ANDROID_PACKAGE_PATTERN.match(profile.package_name):
        blockers.append("PACKAGE_NAME_INVALID")
    if profile.channel == "production" and is_reserved_android_package(profile.package_name):
        blockers.append("PACKAGE_RESERVED_NAMESPACE")
    if not profile.release_version or profile.version_code < 1:
        blockers.append("VERSION_INVALID")
    return GateResult("ANDROID_CONFIG_READY", READY if not blockers else BLOCKED, tuple(blockers))


def _android_signing_gate(
    profile: CustomerAppReleaseProfile,
    resolver: SecretReferenceResolver,
    *,
    allow_local_test_signing: bool,
) -> GateResult:
    try:
        assert_customer_production_signing(
            profile.android_signing,
            resolver=resolver,
            allow_local_test=allow_local_test_signing and profile.channel != "production",
            tenant_id=profile.tenant_id,
            customer_app_id=profile.app_id,
        )
    except SigningGuardError as exc:
        return GateResult("ANDROID_SIGNING_READY", BLOCKED, (str(exc),))
    return GateResult("ANDROID_SIGNING_READY", READY, ())


def _ios_config_gate(profile: CustomerAppReleaseProfile) -> GateResult:
    blockers: list[str] = []
    from app_factory.application.package_identity import (
        GENERIC_ANDROID_PACKAGE_PATTERN,
        is_reserved_android_package,
    )

    if not GENERIC_ANDROID_PACKAGE_PATTERN.match(profile.bundle_identifier):
        blockers.append("BUNDLE_IDENTIFIER_INVALID")
    if profile.channel == "production" and is_reserved_android_package(profile.bundle_identifier):
        blockers.append("BUNDLE_RESERVED_NAMESPACE")
    if not profile.release_version or profile.version_code < 1:
        blockers.append("VERSION_INVALID")
    return GateResult("IOS_CONFIG_READY", READY if not blockers else BLOCKED, tuple(blockers))


def _ios_signing_gate(
    profile: CustomerAppReleaseProfile,
    resolver: SecretReferenceResolver,
    *,
    allow_local_test_signing: bool,
) -> GateResult:
    signing = profile_from_intake(
        profile.ios_signing,
        customer_app_id=profile.app_id,
        tenant_id=profile.tenant_id,
        bundle_identifier=profile.bundle_identifier,
    )
    try:
        assert_customer_ios_signing(
            signing,
            resolver=resolver,
            allow_local_test=allow_local_test_signing and profile.channel != "production",
        )
    except SigningGuardError:
        return GateResult(
            "IOS_SIGNING_READY",
            BLOCKED,
            (APPLE_SIGNING_CONFIGURATION_REQUIRED,),
        )
    return GateResult("IOS_SIGNING_READY", READY, ())


ANDROID_PRODUCTION_READY = "NOT_IMPLEMENTED"


def compose_android_delivery(
    *,
    intake_readiness: dict[str, Any],
    play_verification: dict[str, Any] | None = None,
    aab_ready: bool = False,
    upload_approved: bool = False,
    test_released: bool = False,
) -> dict[str, Any]:
    """Android delivery gates. ANDROID_PRODUCTION_READY is never READY in this slice."""
    play = play_verification or {}
    play_status = str(play.get("status") or "NOT_CONFIGURED")
    play_ready = play_status == "READY"
    play_bound = play.get("play_app") in {"PLAY_APP_BOUND", "READY"} or play_ready
    perm_ready = play.get("permission_status") == "READY" or play_ready
    signing_ready = _named_ready(intake_readiness, "ANDROID_SIGNING_READY")
    build_ready = signing_ready and _named_ready(intake_readiness, "ANDROID_CONFIG_READY")
    test_upload_ready = play_ready and aab_ready and upload_approved
    return {
        "ANDROID_SIGNING_READY": "READY" if signing_ready else "BLOCKED",
        "PLAY_CONNECTION_READY": play_status if play_status != "READY" else "READY",
        "PLAY_APP_BOUND": "PLAY_APP_BOUND" if play_bound else play.get("play_app") or "NOT_CONFIGURED",
        "PLAY_TEST_PERMISSION_READY": "READY" if perm_ready else play.get("permission_status") or "NOT_CONFIGURED",
        "ANDROID_AAB_READY": "READY" if aab_ready else "BLOCKED",
        "PLAY_TEST_UPLOAD_READY": "READY" if test_upload_ready else "BLOCKED",
        "PLAY_TEST_RELEASE_READY": "READY" if test_released else "BLOCKED",
        "ANDROID_BUILD_READY": "READY" if build_ready else "BLOCKED",
        "ANDROID_TEST_DELIVERY_READY": "READY" if test_upload_ready else "BLOCKED",
        "ANDROID_TEST_RELEASED": bool(test_released),
        "ANDROID_PRODUCTION_READY": ANDROID_PRODUCTION_READY,
    }


def _named_ready(readiness: dict[str, Any], name: str) -> bool:
    for gate in readiness.get("gates") or []:
        if gate.get("name") == name:
            return gate.get("status") == "READY"
    return False


def _https_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)
