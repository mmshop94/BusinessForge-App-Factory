"""Platform selectivity — missing Apple must not fail an Android-only customer."""

from __future__ import annotations

from enum import Enum


class PlatformSelection(str, Enum):
    ANDROID_ONLY = "ANDROID_ONLY"
    IOS_ONLY = "IOS_ONLY"
    ANDROID_AND_IOS = "ANDROID_AND_IOS"


class PlatformBooking(str, Enum):
    SUBSCRIBED = "SUBSCRIBED"
    NOT_SUBSCRIBED = "NOT_SUBSCRIBED"


def platform_status(selection: PlatformSelection, platform: str) -> PlatformBooking:
    key = platform.strip().lower()
    if key == "android":
        if selection in {PlatformSelection.ANDROID_ONLY, PlatformSelection.ANDROID_AND_IOS}:
            return PlatformBooking.SUBSCRIBED
        return PlatformBooking.NOT_SUBSCRIBED
    if key == "ios":
        if selection in {PlatformSelection.IOS_ONLY, PlatformSelection.ANDROID_AND_IOS}:
            return PlatformBooking.SUBSCRIBED
        return PlatformBooking.NOT_SUBSCRIBED
    raise ValueError(f"Unknown platform: {platform}")


def android_enabled(selection: PlatformSelection) -> bool:
    return platform_status(selection, "android") is PlatformBooking.SUBSCRIBED


def ios_enabled(selection: PlatformSelection) -> bool:
    return platform_status(selection, "ios") is PlatformBooking.SUBSCRIBED
