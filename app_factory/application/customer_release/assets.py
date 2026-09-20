"""Store asset manifest — classify completeness without a screenshot device farm."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.profile import CustomerAppReleaseProfile

REQUIRED = "REQUIRED"
OPTIONAL = "OPTIONAL"
GENERATED = "GENERATED"
CUSTOMER_PROVIDED = "CUSTOMER_PROVIDED"
MISSING = "MISSING"

ANDROID_ASSETS_READY = "ANDROID_ASSETS_READY"
ANDROID_ASSETS_INCOMPLETE = "ANDROID_ASSETS_INCOMPLETE"

DEMO_ASSET_MARKERS = ("demo", "monogram", "placeholder", "sample-screenshot")


@dataclass(frozen=True)
class AssetEntry:
    name: str
    path: str
    requirement: str
    origin: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
            "requirement": self.requirement,
            "origin": self.origin,
            "status": self.status,
        }


def evaluate_android_assets(
    profile: CustomerAppReleaseProfile,
    asset_root: Path,
) -> dict[str, Any]:
    entries = [
        _entry(
            "icon",
            profile.branding.app_icon,
            REQUIRED,
            profile.branding.icon_origin,
            asset_root,
        ),
        _entry("feature_graphic", profile.store.feature_graphic, REQUIRED, CUSTOMER_PROVIDED, asset_root),
    ]
    if profile.store.screenshots:
        for index, shot in enumerate(profile.store.screenshots):
            entries.append(
                _entry(f"screenshot_phone_{index + 1}", shot, REQUIRED, CUSTOMER_PROVIDED, asset_root)
            )
    else:
        entries.append(
            AssetEntry("screenshot_phone", "", REQUIRED, CUSTOMER_PROVIDED, MISSING)
        )

    ready = all(
        item.requirement != REQUIRED or (item.status != MISSING and not _is_demo_asset(item))
        for item in entries
    ) and sum(1 for item in entries if item.name.startswith("screenshot_phone") and item.status != MISSING) >= 2

    return {
        "layout": "store-assets/android/",
        "status": ANDROID_ASSETS_READY if ready else ANDROID_ASSETS_INCOMPLETE,
        "entries": [item.to_dict() for item in entries],
    }


def _entry(
    name: str,
    relative: str,
    requirement: str,
    origin: str,
    asset_root: Path,
) -> AssetEntry:
    if not relative:
        return AssetEntry(name, "", requirement, origin, MISSING)
    path = asset_root / relative
    if not path.is_file():
        return AssetEntry(name, relative, requirement, origin, MISSING)
    status = CUSTOMER_PROVIDED if origin == "customer_provided" or origin == CUSTOMER_PROVIDED else GENERATED
    if _is_demo_path(relative) or origin in {"monogram", "monogram_fallback", "default"}:
        status = MISSING
        origin = "demo_rejected"
    return AssetEntry(name, relative, requirement, origin, status)


def _is_demo_asset(entry: AssetEntry) -> bool:
    return entry.origin == "demo_rejected" or _is_demo_path(entry.path)


def _is_demo_path(relative: str) -> bool:
    lowered = relative.replace("\\", "/").lower()
    return any(marker in lowered for marker in DEMO_ASSET_MARKERS)
