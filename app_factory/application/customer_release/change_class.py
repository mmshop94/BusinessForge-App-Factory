"""LIVE_CONTENT_CHANGE vs APP_RELEASE_REQUIRED_CHANGE."""

from __future__ import annotations

from typing import Any, Mapping

LIVE_CONTENT_CHANGE = "LIVE_CONTENT_CHANGE"
APP_RELEASE_REQUIRED_CHANGE = "APP_RELEASE_REQUIRED_CHANGE"
IOS_STORE_RELEASE_REQUIRED_CHANGE = "IOS_STORE_RELEASE_REQUIRED_CHANGE"

RELEASE_REQUIRED_KEYS = frozenset(
    {
        "display_name",
        "package_name",
        "bundle_identifier",
        "app_icon",
        "splash",
        "logo",
        "primary_color",
        "capabilities",
        "android_enabled",
        "ios_enabled",
        "platforms",
        "api_base_url",
        "public_app_id",
        "vertical",
    }
)

LIVE_CONTENT_KEYS = frozenset(
    {
        "products",
        "prices",
        "opening_hours",
        "appointments",
        "staff",
        "catalog",
        "availability",
        "orders",
        "bookings",
        "menu",
        "inventory",
        "offerings",
    }
)


def classify_intake_delta(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> str:
    """A live catalog/hours change must not force a new store binary."""
    changed = _changed_keys(previous, current)
    if not changed:
        return LIVE_CONTENT_CHANGE
    if changed & RELEASE_REQUIRED_KEYS:
        if changed & {"bundle_identifier", "ios_enabled"}:
            return IOS_STORE_RELEASE_REQUIRED_CHANGE
        return APP_RELEASE_REQUIRED_CHANGE
    if changed <= LIVE_CONTENT_KEYS:
        return LIVE_CONTENT_CHANGE
    if changed & LIVE_CONTENT_KEYS and not (changed & RELEASE_REQUIRED_KEYS):
        return LIVE_CONTENT_CHANGE
    return APP_RELEASE_REQUIRED_CHANGE


def _changed_keys(previous: Mapping[str, Any], current: Mapping[str, Any]) -> set[str]:
    keys = set(previous) | set(current)
    changed: set[str] = set()
    for key in keys:
        if previous.get(key) != current.get(key):
            changed.add(key)
    return changed
