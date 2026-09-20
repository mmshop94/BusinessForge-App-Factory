"""Deterministic uniqueness foundation — extendable, no similarity score."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app_factory.application.customer_release.profile import (
    CustomerAppReleaseProfile,
    looks_like_demo_name,
    looks_like_generic_legal_url,
    looks_like_placeholder_store_text,
)


@dataclass(frozen=True)
class UniquenessVerdict:
    ready: bool
    signals: dict[str, bool]
    blockers: tuple[str, ...]
    similarity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "signals": dict(self.signals),
            "blockers": list(self.blockers),
            "similarity": dict(self.similarity),
        }


def evaluate_uniqueness(profile: CustomerAppReleaseProfile) -> UniquenessVerdict:
    """Require real customer signals. Similarity analysis is reserved for a later slice."""
    blockers: list[str] = []
    tenant_identity = bool(profile.tenant_id.strip()) and bool(profile.public_app_id.strip())
    if not tenant_identity:
        blockers.append("UNIQUENESS_TENANT_IDENTITY")
    if looks_like_demo_name(profile.display_name) or looks_like_demo_name(profile.app_id):
        blockers.append("UNIQUENESS_DEMO_NAME")
        tenant_identity = False

    branding = (
        profile.branding.icon_origin == "customer_provided"
        and bool(profile.branding.app_icon)
        and profile.branding.app_icon.lower() not in {"monogram", "monogram_fallback", "default"}
    )
    if not branding:
        blockers.append("UNIQUENESS_DEMO_LOGO")

    real_content = bool(profile.content.has_customer_offerings)
    if not real_content:
        blockers.append("UNIQUENESS_MISSING_CONTENT")

    legal = not (
        looks_like_generic_legal_url(profile.legal.privacy_url)
        or looks_like_generic_legal_url(profile.legal.imprint_url)
    )
    if not legal:
        blockers.append("UNIQUENESS_GENERIC_LEGAL")

    vertical = bool(profile.vertical.strip()) and bool(profile.journey.strip() or profile.vertical)
    capabilities = any(bool(value) for value in profile.capabilities.values())
    store_metadata = not looks_like_placeholder_store_text(
        profile.store.short_description
    ) and not looks_like_placeholder_store_text(profile.store.full_description)
    if not store_metadata:
        blockers.append("UNIQUENESS_PLACEHOLDER_STORE_TEXT")

    store_assets = bool(profile.store.screenshots) and bool(profile.store.feature_graphic)
    if not store_assets:
        blockers.append("UNIQUENESS_STORE_ASSETS")

    signals = {
        "tenant_identity": tenant_identity and "UNIQUENESS_DEMO_NAME" not in blockers,
        "branding": branding,
        "real_content": real_content,
        "legal_identity": legal,
        "vertical_journey": vertical,
        "capabilities": capabilities,
        "store_metadata": store_metadata,
        "store_assets": store_assets,
    }
    ready = all(signals.values()) and not blockers
    return UniquenessVerdict(
        ready=ready,
        signals=signals,
        blockers=tuple(dict.fromkeys(blockers)),
        similarity={"status": "RESERVED", "engine": None},
    )
