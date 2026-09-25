"""Map canonical BusinessForge store selection SoT → AppFactory PlatformSelection.

Backend SoT (tenant.store_platform_selection):
  NONE | GOOGLE_PLAY | APPLE_APP_STORE | BOTH

AppFactory PlatformSelection (release snapshot):
  ANDROID_ONLY | IOS_ONLY | ANDROID_AND_IOS

NONE means no store release snapshot is requested (hosted customer surface remains).
File snapshots remain freeze artifacts — not the customer subscription SoT.
"""

from __future__ import annotations

from app_factory.application.customer_release.platforms import PlatformSelection

BACKEND_NONE = "NONE"
BACKEND_GOOGLE = "GOOGLE_PLAY"
BACKEND_APPLE = "APPLE_APP_STORE"
BACKEND_BOTH = "BOTH"


def from_backend_store_selection(selection: str) -> PlatformSelection | None:
    """Return AppFactory platform selection, or None when store delivery not requested."""
    key = (selection or "").strip().upper()
    if key in {"", BACKEND_NONE}:
        return None
    if key == BACKEND_GOOGLE:
        return PlatformSelection.ANDROID_ONLY
    if key == BACKEND_APPLE:
        return PlatformSelection.IOS_ONLY
    if key == BACKEND_BOTH:
        return PlatformSelection.ANDROID_AND_IOS
    raise ValueError(f"Unknown backend store_platform_selection: {selection!r}")


def selection_implies_publication() -> bool:
    """Hard rule: selection never equals live publication."""
    return False
