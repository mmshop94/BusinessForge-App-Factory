"""Canonical API origins for Official Sales Demo app builds.

LAN builds remain valid for internal proof. Public HTTPS rebuilds must use
``PUBLIC_DEMO_API_BASE_URL`` after ``demo-api.bforge.de`` DNS/TLS exists.

Official sales demos must never target Production ``api.bforge.de``.
"""

from __future__ import annotations

LAN_DEMO_API_BASE_URL = "http://192.168.178.95:8090/api/v1"
PUBLIC_DEMO_API_BASE_URL = "https://demo-api.bforge.de/api/v1"
PRODUCTION_API_HOST = "api.bforge.de"
DEMO_API_HOST = "demo-api.bforge.de"


class DemoApiOriginError(ValueError):
    """Raised when an official sales demo would target Production."""


def assert_official_sales_demo_api_origin(api_base_url: str) -> str:
    """Return a stripped URL or raise if it points at Production API."""
    value = (api_base_url or "").strip()
    lowered = value.lower()
    if DEMO_API_HOST in lowered:
        return value
    if PRODUCTION_API_HOST in lowered:
        raise DemoApiOriginError(
            "Official Sales Demo builds must not use Production api.bforge.de. "
            f"Use {PUBLIC_DEMO_API_BASE_URL} (public) or {LAN_DEMO_API_BASE_URL} (LAN)."
        )
    return value
