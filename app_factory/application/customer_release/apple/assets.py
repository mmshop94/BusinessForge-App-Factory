"""iOS asset catalog + store screenshot manifest. No device farm."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_factory.application.customer_release.assets import (
    CUSTOMER_PROVIDED,
    GENERATED,
    MISSING,
    OPTIONAL,
    REQUIRED,
    AssetEntry,
    _entry,
    _is_demo_asset,
)
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile

IOS_ASSETS_READY = "IOS_ASSETS_READY"
IOS_ASSETS_INCOMPLETE = "IOS_ASSETS_INCOMPLETE"
IOS_STORE_METADATA_READY = "IOS_STORE_METADATA_READY"
IOS_SCREENSHOTS_READY = "IOS_SCREENSHOTS_READY"
IOS_STORE_ASSETS_INCOMPLETE = "IOS_STORE_ASSETS_INCOMPLETE"


def evaluate_ios_assets(
    profile: CustomerAppReleaseProfile,
    asset_root: Path,
) -> dict[str, Any]:
    entries = [
        _entry("app_icon", profile.branding.app_icon, REQUIRED, profile.branding.icon_origin, asset_root),
        _entry(
            "launch_assets",
            profile.branding.splash,
            OPTIONAL,
            CUSTOMER_PROVIDED,
            asset_root,
        ),
    ]
    if profile.store.screenshots:
        for index, shot in enumerate(profile.store.screenshots):
            entries.append(
                _entry(f"screenshot_{index + 1}", shot, OPTIONAL, CUSTOMER_PROVIDED, asset_root)
            )
    else:
        entries.append(AssetEntry("screenshot", "", OPTIONAL, CUSTOMER_PROVIDED, MISSING))

    icon_ok = all(
        item.name != "app_icon" or (item.status != MISSING and not _is_demo_asset(item))
        for item in entries
    )
    shots_present = [
        item for item in entries if item.name.startswith("screenshot") and item.status != MISSING
    ]
    screenshots_status = IOS_SCREENSHOTS_READY if len(shots_present) >= 2 else IOS_STORE_ASSETS_INCOMPLETE
    metadata_ok = bool(profile.store.short_description.strip()) and bool(
        profile.legal.privacy_url.strip()
    )
    catalog_ready = icon_ok
    return {
        "layout": "store-assets/ios/",
        "status": IOS_ASSETS_READY if catalog_ready else IOS_ASSETS_INCOMPLETE,
        "ios_store_metadata": IOS_STORE_METADATA_READY if metadata_ok else IOS_STORE_ASSETS_INCOMPLETE,
        "ios_screenshots": screenshots_status,
        "entries": [item.to_dict() for item in entries],
        "app_icon": next((item.status for item in entries if item.name == "app_icon"), MISSING),
        "launch_assets": GENERATED if icon_ok else MISSING,
        "screenshots": screenshots_status,
        "metadata": IOS_STORE_METADATA_READY if metadata_ok else IOS_STORE_ASSETS_INCOMPLETE,
    }
