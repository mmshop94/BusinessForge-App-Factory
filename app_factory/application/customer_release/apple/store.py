"""iOS store metadata + Apple privacy intake. No invented questionnaire answers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app_factory.application.customer_release.profile import (
    CustomerAppReleaseProfile,
    looks_like_generic_legal_url,
)

APPLE_PRIVACY_INTAKE_REQUIRED = "APPLE_PRIVACY_INTAKE_REQUIRED"
IOS_STORE_METADATA_READY = "IOS_STORE_METADATA_READY"
IOS_STORE_ASSETS_INCOMPLETE = "IOS_STORE_ASSETS_INCOMPLETE"


def evaluate_ios_store_metadata(profile: CustomerAppReleaseProfile) -> dict[str, Any]:
    blockers: list[str] = []
    if len(profile.display_name.strip()) < 3:
        blockers.append("APP_NAME_INVALID")
    if len((profile.store.short_description or "").strip()) < 20:
        blockers.append("SUBTITLE_OR_SHORT_DESCRIPTION_MISSING")
    if len((profile.store.full_description or "").strip()) < 40:
        blockers.append("DESCRIPTION_MISSING")
    if not _https(profile.legal.support_url):
        blockers.append("SUPPORT_URL_MISSING")
    if looks_like_generic_legal_url(profile.legal.privacy_url):
        blockers.append("PRIVACY_URL_MISSING")
    return {
        "status": IOS_STORE_METADATA_READY if not blockers else IOS_STORE_ASSETS_INCOMPLETE,
        "app_name": profile.display_name,
        "subtitle": profile.store.short_description[:30],
        "description": profile.store.full_description,
        "keywords": "",
        "support_url": profile.legal.support_url,
        "privacy_url": profile.legal.privacy_url,
        "marketing_url": "",
        "category": profile.store.category,
        "locale": profile.store.locale,
        "blockers": blockers,
    }


def evaluate_apple_privacy_intake(profile: CustomerAppReleaseProfile) -> dict[str, Any]:
    """Reference BusinessForge legal URLs. Do not invent App Privacy answers."""
    known = {
        "privacy_url": profile.legal.privacy_url,
        "support_url": profile.legal.support_url,
        "support_email": profile.legal.support_email,
        "legal_identity_url": profile.legal.imprint_url,
    }
    missing_known = [key for key, value in known.items() if not str(value).strip()]
    return {
        "status": APPLE_PRIVACY_INTAKE_REQUIRED,
        "known_from_businessforge": {key: bool(value) for key, value in known.items()},
        "missing_known_fields": missing_known,
        "questionnaire_answers_generated": False,
        "notes": [
            "App Privacy questionnaire answers are not inferred from BusinessForge data.",
        ],
    }


def _https(value: str) -> bool:
    parsed = urlparse((value or "").strip())
    return parsed.scheme == "https" and bool(parsed.netloc)
