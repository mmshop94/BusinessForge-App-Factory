"""Canonical CustomerAppReleaseProfile — references only, never secret values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app_factory.application.customer_release.platforms import PlatformSelection
from app_factory.application.package_identity import validate_android_package_format
from app_factory.domain.errors import CustomerReleaseError
from app_factory.application.manifest_validator import ManifestValidator


DEMO_NAME_MARKERS = (
    "demo ",
    " demo",
    "businessforge demo",
    "sales demo",
    "placeholder",
    "test app",
)
GENERIC_LEGAL_HOSTS = (
    "bforge.de",
    "businessforge.example",
    "example.com",
    "localhost",
)
PLACEHOLDER_STORE_MARKERS = (
    "businessforge demo",
    "official sales demo",
    "lorem ipsum",
    "todo:",
    "tbd",
    "coming soon",
    "replace this",
)


@dataclass(frozen=True)
class BrandingIntake:
    logo: str
    app_icon: str
    splash: str
    primary_color: str
    secondary_color: str
    theme: str = "modern"
    icon_origin: str = "customer_provided"


@dataclass(frozen=True)
class LegalIntake:
    privacy_url: str
    imprint_url: str
    support_url: str
    support_email: str
    terms_url: str = ""


@dataclass(frozen=True)
class StoreIntake:
    short_description: str
    full_description: str
    category: str
    locale: str = "de-DE"
    screenshots: tuple[str, ...] = ()
    feature_graphic: str = ""


@dataclass(frozen=True)
class ContentIntake:
    """Whether the live tenant already has real business content (not baked into the APK)."""

    has_customer_offerings: bool
    offering_kind: str = "catalog"


@dataclass(frozen=True)
class AndroidSigningIntake:
    provider: str
    alias_reference: str = ""
    material_reference: str = ""
    store_unlock_reference: str = ""
    key_unlock_reference: str = ""
    play_app_signing_enabled: bool = False
    status: str = "MISSING"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "alias_reference": self.alias_reference,
            "material_reference": self.material_reference,
            "store_unlock_reference": self.store_unlock_reference,
            "key_unlock_reference": self.key_unlock_reference,
            "play_app_signing_enabled": self.play_app_signing_enabled,
            "status": self.status,
        }


@dataclass(frozen=True)
class IosSigningIntake:
    provider: str = "ABSENT"
    status: str = "NOT_SUBSCRIBED"
    team_reference: str = ""
    profile_reference: str = ""
    team_id_reference: str = ""
    distribution_certificate_reference: str = ""
    key_material_reference: str = ""
    provisioning_profile_reference: str = ""
    signing_mode: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "team_reference": self.team_reference,
            "profile_reference": self.profile_reference,
            "team_id_reference": self.team_id_reference or self.team_reference,
            "distribution_certificate_reference": self.distribution_certificate_reference,
            "key_material_reference": self.key_material_reference,
            "provisioning_profile_reference": self.provisioning_profile_reference
            or self.profile_reference,
            "signing_mode": self.signing_mode,
        }


@dataclass(frozen=True)
class CustomerAppReleaseProfile:
    tenant_id: str
    app_id: str
    vertical: str
    release_id: str
    release_version: str
    version_code: int
    display_name: str
    package_name: str
    bundle_identifier: str
    platforms: PlatformSelection
    branding: BrandingIntake
    legal: LegalIntake
    store: StoreIntake
    capabilities: dict[str, bool]
    android_signing: AndroidSigningIntake
    content: ContentIntake
    public_app_id: str
    api_base_url: str
    package_version: str = "v1"
    customer_app_ref: str = "main"
    factory_compat_version: str = "1"
    channel: str = "production"
    published: bool = False
    release_snapshot_id: str = ""
    schema_version: int = 1
    ios_signing: IosSigningIntake = field(default_factory=IosSigningIntake)
    backend_origin: str = ""
    journey: str = ""
    asset_root: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "app_id": self.app_id,
            "vertical": self.vertical,
            "release_id": self.release_id,
            "release_version": self.release_version,
            "version_code": self.version_code,
            "release_snapshot_id": self.release_snapshot_id,
            "display_name": self.display_name,
            "package_name": self.package_name,
            "bundle_identifier": self.bundle_identifier,
            "platforms": {
                "selection": self.platforms.value,
                "android_enabled": self.platforms
                in {PlatformSelection.ANDROID_ONLY, PlatformSelection.ANDROID_AND_IOS},
                "ios_enabled": self.platforms
                in {PlatformSelection.IOS_ONLY, PlatformSelection.ANDROID_AND_IOS},
            },
            "branding": {
                "logo": self.branding.logo,
                "app_icon": self.branding.app_icon,
                "splash": self.branding.splash,
                "primary_color": self.branding.primary_color,
                "secondary_color": self.branding.secondary_color,
                "theme": self.branding.theme,
                "icon_origin": self.branding.icon_origin,
            },
            "legal": {
                "privacy_url": self.legal.privacy_url,
                "imprint_url": self.legal.imprint_url,
                "terms_url": self.legal.terms_url,
                "support_url": self.legal.support_url,
                "support_email": self.legal.support_email,
            },
            "store": {
                "short_description": self.store.short_description,
                "full_description": self.store.full_description,
                "category": self.store.category,
                "locale": self.store.locale,
                "screenshots": list(self.store.screenshots),
                "feature_graphic": self.store.feature_graphic,
            },
            "capabilities": dict(self.capabilities),
            "content": {
                "has_customer_offerings": self.content.has_customer_offerings,
                "offering_kind": self.content.offering_kind,
            },
            "signing": {
                "android": self.android_signing.to_public_dict(),
                "ios": self.ios_signing.to_public_dict(),
            },
            "public_app_id": self.public_app_id,
            "api_base_url": self.api_base_url,
            "backend_origin": self.backend_origin,
            "package_version": self.package_version,
            "customer_app_ref": self.customer_app_ref,
            "factory_compat_version": self.factory_compat_version,
            "channel": self.channel,
            "published": self.published,
            "journey": self.journey,
            "asset_root": self.asset_root,
        }

    def with_snapshot_id(self, snapshot_id: str) -> "CustomerAppReleaseProfile":
        return CustomerAppReleaseProfile(
            **{**self.__dict__, "release_snapshot_id": snapshot_id}
        )


def profile_from_dict(data: dict[str, Any]) -> CustomerAppReleaseProfile:
    ManifestValidator._assert_no_secrets(data)
    try:
        platforms_raw = data.get("platforms") or {}
        if isinstance(platforms_raw, str):
            selection = PlatformSelection(platforms_raw)
        else:
            selection = PlatformSelection(str(platforms_raw.get("selection") or "ANDROID_ONLY"))
        branding = data["branding"]
        legal = data["legal"]
        store = data["store"]
        signing = data.get("signing") or {}
        android_signing = signing.get("android") or {}
        ios_signing = signing.get("ios") or {}
        content = data.get("content") or {}
        package_name = validate_android_package_format(str(data["package_name"]))
        return CustomerAppReleaseProfile(
            tenant_id=str(data["tenant_id"]),
            app_id=str(data["app_id"]),
            vertical=str(data["vertical"]),
            release_id=str(data["release_id"]),
            release_version=str(data["release_version"]),
            version_code=int(data["version_code"]),
            display_name=str(data["display_name"]),
            package_name=package_name,
            bundle_identifier=str(data.get("bundle_identifier") or package_name),
            platforms=selection,
            branding=BrandingIntake(
                logo=str(branding["logo"]),
                app_icon=str(branding["app_icon"]),
                splash=str(branding.get("splash") or branding["app_icon"]),
                primary_color=str(branding["primary_color"]),
                secondary_color=str(branding["secondary_color"]),
                theme=str(branding.get("theme") or "modern"),
                icon_origin=str(branding.get("icon_origin") or "customer_provided"),
            ),
            legal=LegalIntake(
                privacy_url=str(legal.get("privacy_url") or ""),
                imprint_url=str(legal.get("imprint_url") or ""),
                support_url=str(legal.get("support_url") or ""),
                support_email=str(legal.get("support_email") or ""),
                terms_url=str(legal.get("terms_url") or ""),
            ),
            store=StoreIntake(
                short_description=str(store.get("short_description") or ""),
                full_description=str(store.get("full_description") or ""),
                category=str(store.get("category") or ""),
                locale=str(store.get("locale") or "de-DE"),
                screenshots=tuple(str(item) for item in (store.get("screenshots") or ())),
                feature_graphic=str(store.get("feature_graphic") or ""),
            ),
            capabilities=dict(data.get("capabilities") or {}),
            android_signing=AndroidSigningIntake(
                provider=str(android_signing.get("provider") or "MISSING"),
                alias_reference=str(android_signing.get("alias_reference") or ""),
                material_reference=str(android_signing.get("material_reference") or ""),
                store_unlock_reference=str(android_signing.get("store_unlock_reference") or ""),
                key_unlock_reference=str(android_signing.get("key_unlock_reference") or ""),
                play_app_signing_enabled=bool(
                    android_signing.get("play_app_signing_enabled") or False
                ),
                status=str(android_signing.get("status") or "MISSING"),
            ),
            ios_signing=IosSigningIntake(
                provider=str(ios_signing.get("provider") or "ABSENT"),
                status=str(ios_signing.get("status") or "NOT_SUBSCRIBED"),
                team_reference=str(ios_signing.get("team_reference") or ""),
                profile_reference=str(ios_signing.get("profile_reference") or ""),
                team_id_reference=str(ios_signing.get("team_id_reference") or ""),
                distribution_certificate_reference=str(
                    ios_signing.get("distribution_certificate_reference") or ""
                ),
                key_material_reference=str(ios_signing.get("key_material_reference") or ""),
                provisioning_profile_reference=str(
                    ios_signing.get("provisioning_profile_reference") or ""
                ),
                signing_mode=str(ios_signing.get("signing_mode") or ""),
            ),
            content=ContentIntake(
                has_customer_offerings=bool(content.get("has_customer_offerings")),
                offering_kind=str(content.get("offering_kind") or "catalog"),
            ),
            public_app_id=str(data["public_app_id"]),
            api_base_url=str(data["api_base_url"]),
            package_version=str(data.get("package_version") or "v1"),
            customer_app_ref=str(data.get("customer_app_ref") or "main"),
            factory_compat_version=str(data.get("factory_compat_version") or "1"),
            channel=str(data.get("channel") or "production"),
            published=bool(data.get("published") or False),
            release_snapshot_id=str(data.get("release_snapshot_id") or ""),
            schema_version=int(data.get("schema_version") or 1),
            backend_origin=str(data.get("backend_origin") or ""),
            journey=str(data.get("journey") or ""),
            asset_root=str(data.get("asset_root") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CustomerReleaseError(f"Invalid customer release profile: {exc}") from exc


def looks_like_demo_name(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    return any(marker in lowered for marker in DEMO_NAME_MARKERS)


def looks_like_placeholder_store_text(value: str) -> bool:
    lowered = value.strip().lower()
    if len(lowered) < 20:
        return True
    return any(marker in lowered for marker in PLACEHOLDER_STORE_MARKERS)


def looks_like_generic_legal_url(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered.startswith("https://"):
        return True
    return any(host in lowered for host in GENERIC_LEGAL_HOSTS)
