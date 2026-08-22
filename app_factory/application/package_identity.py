"""Android application identity — deterministic, collision-safe, not slug-based."""

from __future__ import annotations

import re

ANDROID_APPLICATION_ID_PATTERN = re.compile(r"^de\.bforge\.app\.u[0-9a-z]{26}$")
PUBLIC_APP_ID_PATTERN = re.compile(r"^app_([0-9A-Z]{26})$")


def android_application_id_from_public_app_id(public_app_id: str) -> str:
    match = PUBLIC_APP_ID_PATTERN.match(public_app_id.strip())
    if not match:
        raise ValueError(f"Invalid public_app_id: {public_app_id}")
    return f"de.bforge.app.u{match.group(1).lower()}"


def validate_android_application_id(value: str) -> str:
    normalized = value.strip()
    if not ANDROID_APPLICATION_ID_PATTERN.match(normalized):
        raise ValueError(f"Invalid Android application ID: {normalized}")
    return normalized
