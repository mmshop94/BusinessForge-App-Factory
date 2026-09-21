"""Per-customer Apple signing profile — references only, no .p12/.p8/passwords."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app_factory.application.customer_release.profile import IosSigningIntake
from app_factory.application.customer_release.signing import (
    FailClosedSecretResolver,
    SecretReferenceResolver,
    looks_like_reference,
)
from app_factory.domain.errors import SigningGuardError

LOCAL_TEST = "LOCAL_TEST"
CUSTOMER_DEVELOPMENT = "CUSTOMER_DEVELOPMENT"
CUSTOMER_DISTRIBUTION = "CUSTOMER_DISTRIBUTION"
APP_STORE_DISTRIBUTION = "APP_STORE_DISTRIBUTION"
VALID_SIGNING_MODES = frozenset(
    {LOCAL_TEST, CUSTOMER_DEVELOPMENT, CUSTOMER_DISTRIBUTION, APP_STORE_DISTRIBUTION}
)

SHARED_APPLE_DISTRIBUTION = "SHARED_APPLE_DISTRIBUTION_FORBIDDEN"
APPLE_SIGNING_CONFIGURATION_REQUIRED = "IOS_SIGNING_REQUIRED"

SHARED_OWNER_MARKERS = (
    "ops://owner/",
    "shared-apple",
    "shared-owner",
    "BF_APPLE_DISTRIBUTION",
)


@dataclass(frozen=True)
class AppleSigningProfile:
    customer_app_id: str
    tenant_id: str
    bundle_identifier: str
    team_id_reference: str
    distribution_certificate_reference: str
    key_material_reference: str
    provisioning_profile_reference: str
    signing_mode: str
    status: str
    provider: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "customer_app_id": self.customer_app_id,
            "tenant_id": self.tenant_id,
            "bundle_identifier": self.bundle_identifier,
            "team_id_reference": self.team_id_reference,
            "distribution_certificate_reference": self.distribution_certificate_reference,
            "key_material_reference": self.key_material_reference,
            "provisioning_profile_reference": self.provisioning_profile_reference,
            "signing_mode": self.signing_mode,
            "status": self.status,
            "provider": self.provider,
        }


def profile_from_intake(
    intake: IosSigningIntake,
    *,
    customer_app_id: str,
    tenant_id: str,
    bundle_identifier: str,
) -> AppleSigningProfile:
    mode = (intake.signing_mode or "").strip() or (
        APP_STORE_DISTRIBUTION
        if intake.status not in {"ABSENT", "NOT_SUBSCRIBED", ""}
        else LOCAL_TEST
    )
    return AppleSigningProfile(
        customer_app_id=customer_app_id,
        tenant_id=tenant_id,
        bundle_identifier=bundle_identifier,
        team_id_reference=intake.team_id_reference or intake.team_reference,
        distribution_certificate_reference=intake.distribution_certificate_reference,
        key_material_reference=intake.key_material_reference,
        provisioning_profile_reference=intake.provisioning_profile_reference
        or intake.profile_reference,
        signing_mode=mode,
        status=intake.status,
        provider=intake.provider,
    )


def assert_customer_ios_signing(
    profile: AppleSigningProfile,
    *,
    resolver: SecretReferenceResolver | None = None,
    allow_local_test: bool = False,
) -> None:
    secret = resolver or FailClosedSecretResolver()
    if profile.signing_mode not in VALID_SIGNING_MODES:
        raise SigningGuardError(APPLE_SIGNING_CONFIGURATION_REQUIRED)
    if profile.signing_mode == LOCAL_TEST:
        if not allow_local_test:
            raise SigningGuardError(APPLE_SIGNING_CONFIGURATION_REQUIRED)
        return
    refs = (
        profile.team_id_reference,
        profile.distribution_certificate_reference,
        profile.key_material_reference,
        profile.provisioning_profile_reference,
    )
    if not all(looks_like_reference(item) for item in refs):
        raise SigningGuardError(APPLE_SIGNING_CONFIGURATION_REQUIRED)
    blob = " ".join(refs).lower()
    if any(marker.lower() in blob for marker in SHARED_OWNER_MARKERS):
        raise SigningGuardError(SHARED_APPLE_DISTRIBUTION)
    for item in refs:
        if not secret.has(
            item, tenant_id=profile.tenant_id, customer_app_id=profile.customer_app_id
        ):
            raise SigningGuardError(APPLE_SIGNING_CONFIGURATION_REQUIRED)
