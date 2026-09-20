"""Android application identity — deterministic, collision-safe, not slug-based."""

from __future__ import annotations

import re

ANDROID_APPLICATION_ID_PATTERN = re.compile(r"^de\.bforge\.app\.u[0-9a-z]{26}$")
PUBLIC_APP_ID_PATTERN = re.compile(r"^app_([0-9A-Z]{26})$")
GENERIC_ANDROID_PACKAGE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,}$")

# Demo / shared-core namespaces — forbidden for production customer store apps.
RESERVED_ANDROID_PREFIXES = (
    "de.bforge.app.",
    "de.bforge.customer.",
    "com.businessforge.",
    "com.example.",
    "io.flutter.",
    "org.chromium.",
)


def android_application_id_from_public_app_id(public_app_id: str) -> str:
    match = PUBLIC_APP_ID_PATTERN.match(public_app_id.strip())
    if not match:
        raise ValueError(f"Invalid public_app_id: {public_app_id}")
    return f"de.bforge.app.u{match.group(1).lower()}"


def validate_android_application_id(value: str) -> str:
    """Validate the factory demo/pilot identity (`de.bforge.app.u{ulid}`)."""
    normalized = value.strip()
    if not ANDROID_APPLICATION_ID_PATTERN.match(normalized):
        raise ValueError(f"Invalid Android application ID: {normalized}")
    return normalized


def validate_android_package_format(value: str) -> str:
    normalized = value.strip()
    if not GENERIC_ANDROID_PACKAGE_PATTERN.match(normalized):
        raise ValueError(f"Invalid Android package format: {normalized}")
    if ".." in normalized:
        raise ValueError(f"Invalid Android package format: {normalized}")
    return normalized


def is_reserved_android_package(value: str) -> bool:
    normalized = value.strip().lower()
    return any(normalized.startswith(prefix) for prefix in RESERVED_ANDROID_PREFIXES)


def validate_customer_production_application_id(value: str) -> str:
    """Production customer apps must own a non-reserved reverse-DNS applicationId."""
    normalized = validate_android_package_format(value)
    if is_reserved_android_package(normalized):
        raise ValueError(
            f"Reserved Android namespace is not allowed for customer production: {normalized}"
        )
    return normalized
