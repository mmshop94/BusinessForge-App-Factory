"""Discover Official Sales Demo tenants from the demo plane (read-only).

Canonical slug list mirrors BusinessForge ``official_demo.py`` +
``appointment_official_sales_demos.py``. Technical ``test-appointment-*``
tenants are explicitly excluded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

# Must stay aligned with businessforge/application/provisioning/official_demo.py
OFFICIAL_SALES_DEMO_SLUGS: tuple[str, ...] = (
    "demo-restaurant",
    "demo-village-store",
    "demo-hairdresser",
    "demo-barber",
    "demo-nail-studio",
    "demo-cosmetics",
    "demo-massage",
    "demo-tattoo",
    "demo-lash-brow",
    "demo-foot-care",
    "demo-pet-grooming",
)

# Fallback branding when bootstrap omits colors (core demos).
_FALLBACK_BRANDING: dict[str, tuple[str, str, str]] = {
    "demo-restaurant": ("warm", "#C0392B", "#FDEBD0"),
    "demo-village-store": ("warm", "#8B4A2F", "#F2E3D5"),
}

DEFAULT_THEME = "modern"
DEFAULT_PRIMARY = "#2563EB"
DEFAULT_SECONDARY = "#EFF6FF"


@dataclass(frozen=True)
class OfficialSalesDemoRecord:
    slug: str
    business_name: str
    display_name: str
    public_app_id: str
    runtime_package: str
    package_version: str
    primary_color: str
    secondary_color: str
    theme: str
    booking_enabled: bool
    hero_media_id: str | None
    logo_media_id: str | None
    design_template_id: str | None
    bootstrap_ok: bool
    login_ok: bool


def _owner_email(slug: str) -> str:
    return f"owner@{slug}.bforge.local"


def _resolve_colors(
    slug: str,
    branding: dict[str, Any],
    experience: dict[str, Any],
) -> tuple[str, str, str]:
    fallback = _FALLBACK_BRANDING.get(slug, (DEFAULT_THEME, DEFAULT_PRIMARY, DEFAULT_SECONDARY))
    theme = DEFAULT_THEME
    primary = (
        branding.get("primary_color")
        or experience.get("accent_color")
        or fallback[1]
    )
    secondary = branding.get("secondary_color") or fallback[2]
    if not primary:
        primary = fallback[1]
    if not secondary:
        secondary = fallback[2]
    return theme, str(primary), str(secondary)


def _features_for_package(package: str) -> dict[str, bool]:
    if package == "restaurant":
        return {
            "restaurant_menu": True,
            "ordering": True,
            "scheduling": True,
            "notifications": True,
            "payments": True,
        }
    if package == "village_store":
        return {
            "village_store": True,
            "ordering": True,
            "news": True,
            "notifications": True,
            "payments": True,
        }
    if package.startswith("appointment_"):
        return {
            "appointments": True,
            "notifications": True,
            "documents": True,
        }
    return {"catalog": True, "ordering": True, "notifications": True}


def discover_official_sales_demos(
    *,
    api_base_url: str,
    owner_password: str,
    slugs: tuple[str, ...] = OFFICIAL_SALES_DEMO_SLUGS,
    timeout: float = 45.0,
) -> list[OfficialSalesDemoRecord]:
    """Login + bootstrap each official sales demo (read-only)."""
    api_v1 = api_base_url.rstrip("/")
    if not api_v1.endswith("/api/v1"):
        api_v1 = f"{api_v1.rstrip('/')}/api/v1"
    origin = api_v1[: -len("/api/v1")]

    records: list[OfficialSalesDemoRecord] = []
    with httpx.Client(timeout=timeout) as client:
        health = client.get(f"{origin}/health")
        health.raise_for_status()
        version = health.json().get("version", "")
        if version and _version_tuple(version) < _version_tuple("0.8.67"):
            raise RuntimeError(f"Demo API {version} is below required 0.8.67")

        for slug in slugs:
            email = _owner_email(slug)
            login = client.post(
                f"{api_v1}/auth/operator/login",
                json={"email": email, "password": owner_password},
            )
            login_ok = login.status_code == 200
            public_app_id = ""
            if login_ok:
                tenant = login.json().get("tenant") or {}
                public_app_id = str(tenant.get("public_app_id") or "")

            bootstrap_ok = False
            payload: dict[str, Any] = {}
            if public_app_id:
                boot = client.get(f"{api_v1}/public/apps/{public_app_id}/bootstrap")
                bootstrap_ok = boot.status_code == 200
                if bootstrap_ok:
                    payload = boot.json()

            branding = payload.get("branding") or {}
            experience = payload.get("app_experience") or {}
            theme, primary, secondary = _resolve_colors(slug, branding, experience)
            display = (
                branding.get("display_name")
                or payload.get("business_name")
                or slug.replace("demo-", "").replace("-", " ").title()
            )
            runtime_package = str(payload.get("runtime_package") or experience.get("package_id") or "")
            if slug == "demo-restaurant":
                runtime_package = runtime_package or "restaurant"
            if slug == "demo-village-store":
                runtime_package = runtime_package or "village_store"

            records.append(
                OfficialSalesDemoRecord(
                    slug=slug,
                    business_name=display,
                    display_name=display,
                    public_app_id=public_app_id,
                    runtime_package=runtime_package,
                    package_version="v1",
                    primary_color=primary,
                    secondary_color=secondary,
                    theme=theme,
                    booking_enabled=bool(payload.get("booking_enabled")),
                    hero_media_id=experience.get("hero_media_id") or experience.get("cover_media_id"),
                    logo_media_id=branding.get("logo_media_id") or branding.get("icon_media_id"),
                    design_template_id=experience.get("design_template_id"),
                    bootstrap_ok=bootstrap_ok,
                    login_ok=login_ok,
                )
            )
    return records


def features_for_record(record: OfficialSalesDemoRecord) -> dict[str, bool]:
    return _features_for_package(record.runtime_package)


def _version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in value.strip().split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts)
