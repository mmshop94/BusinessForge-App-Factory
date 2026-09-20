"""Per-customer Android signing references — fail-closed in production, no secret values."""

from __future__ import annotations

import os
from typing import Mapping, Protocol

from app_factory.application.customer_release.profile import AndroidSigningIntake
from app_factory.application.signing import (
    KEYSTORE_PATH_ENV,
    SHARED_OWNER_KEYSTORE_FORBIDDEN,
    SIGNING_CONFIGURATION_REQUIRED,
)
from app_factory.domain.errors import SigningGuardError

LOCAL_TEST_SIGNING = "LOCAL_TEST_SIGNING"
CUSTOMER_UPLOAD_KEY = "CUSTOMER_UPLOAD_KEY"
PLAY_APP_SIGNING = "PLAY_APP_SIGNING"
SHARED_OWNER_KEYSTORE = "SHARED_OWNER_KEYSTORE"

SHARED_OWNER_REF_MARKERS = (
    "env://BF_ANDROID_KEYSTORE_PATH",
    "ops://owner/",
    "shared-owner",
    "owner-keystore",
    "BF_ANDROID_KEYSTORE_PATH",
)

REFERENCE_PREFIXES = ("ops://", "env://", "fixture://")


class SecretReferenceResolver(Protocol):
    """Resolves signing material references. Implementations must never log values."""

    def has(self, reference: str) -> bool: ...


class FailClosedSecretResolver:
    """Production default — references are unknown until an ops store is wired."""

    def has(self, reference: str) -> bool:
        del reference
        return False


class MappingSecretResolver:
    """Local tests / fixtures only. Keys are references; values must never be serialized."""

    def __init__(self, mapping: Mapping[str, str]) -> None:
        self._mapping = dict(mapping)

    def has(self, reference: str) -> bool:
        return bool(reference) and reference in self._mapping

    def resolve_value(self, reference: str) -> str:
        return self._mapping[reference]


def looks_like_reference(value: str) -> bool:
    return bool(value) and value.startswith(REFERENCE_PREFIXES)


def looks_like_shared_owner_reference(value: str) -> bool:
    lowered = value.strip()
    return any(marker in lowered for marker in SHARED_OWNER_REF_MARKERS)


def assert_customer_production_signing(
    intake: AndroidSigningIntake,
    *,
    resolver: SecretReferenceResolver,
    environ: Mapping[str, str] | None = None,
    allow_local_test: bool = False,
) -> None:
    """Fail-closed: production customer releases must not use the shared Owner keystore."""
    env = environ if environ is not None else dict(os.environ)
    provider = intake.provider.strip()

    if provider == SHARED_OWNER_KEYSTORE:
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)

    if provider == LOCAL_TEST_SIGNING:
        if not allow_local_test:
            raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
        return

    if provider not in {CUSTOMER_UPLOAD_KEY, PLAY_APP_SIGNING}:
        raise SigningGuardError(SIGNING_CONFIGURATION_REQUIRED)

    required_refs = (
        intake.alias_reference,
        intake.material_reference,
        intake.store_unlock_reference,
        intake.key_unlock_reference or intake.store_unlock_reference,
    )
    if not all(looks_like_reference(item) for item in required_refs):
        raise SigningGuardError(SIGNING_CONFIGURATION_REQUIRED)
    if any(looks_like_shared_owner_reference(item) for item in required_refs):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    if not all(resolver.has(item) for item in required_refs if item):
        raise SigningGuardError(SIGNING_CONFIGURATION_REQUIRED)

    owner_path = env.get(KEYSTORE_PATH_ENV, "").strip()
    if owner_path and not intake.material_reference:
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)
    if looks_like_shared_owner_reference(intake.material_reference):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)


def public_signing_status(intake: AndroidSigningIntake) -> dict[str, object]:
    payload = intake.to_public_dict()
    blob = str(payload).lower()
    for marker in ("password", "-----begin", ".jks", ".keystore"):
        if marker in blob:
            raise SigningGuardError("Signing public status leaked a secret-like value")
    return payload
