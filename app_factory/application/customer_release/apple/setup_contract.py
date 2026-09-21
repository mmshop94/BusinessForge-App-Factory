"""Apple external setup contract — per-prerequisite states, no blanket 'connected' flag."""

from __future__ import annotations

from typing import Any

from app_factory.application.customer_release.apple import ApplePublisherConnection
from app_factory.application.customer_release.play import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    VALID_OWNER_TYPES,
)
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.package_identity import (
    REFERENCE_IOS_BUNDLE,
    is_reference_ios_bundle,
    validate_reference_ios_bundle_id,
)
from app_factory.domain.errors import AppleConnectionError

NOT_STARTED = "NOT_STARTED"
ACTION_REQUIRED = "ACTION_REQUIRED"
VERIFYING = "VERIFYING"
VERIFIED = "VERIFIED"
FAILED = "FAILED"
NOT_APPLICABLE = "NOT_APPLICABLE"
BLOCKED_EXTERNAL = "BLOCKED_EXTERNAL"

VALID_STATES = frozenset(
    {
        NOT_STARTED,
        ACTION_REQUIRED,
        VERIFYING,
        VERIFIED,
        FAILED,
        NOT_APPLICABLE,
        BLOCKED_EXTERNAL,
    }
)

APPLE_DEVELOPER_ACCOUNT = "APPLE_DEVELOPER_ACCOUNT"
APP_STORE_CONNECT_API_ACCESS = "APP_STORE_CONNECT_API_ACCESS"
AGREEMENTS_ACCEPTED = "AGREEMENTS_ACCEPTED"
BUNDLE_ID_REGISTERED = "BUNDLE_ID_REGISTERED"
APP_RECORD_CREATED = "APP_RECORD_CREATED"
BF_USER_OR_API_ACCESS_GRANTED = "BF_USER_OR_API_ACCESS_GRANTED"
SIGNING_MATERIAL_AVAILABLE = "SIGNING_MATERIAL_AVAILABLE"
MACOS_BUILD_EXECUTOR_AVAILABLE = "MACOS_BUILD_EXECUTOR_AVAILABLE"

SETUP_PREREQUISITES = (
    APPLE_DEVELOPER_ACCOUNT,
    APP_STORE_CONNECT_API_ACCESS,
    AGREEMENTS_ACCEPTED,
    BUNDLE_ID_REGISTERED,
    APP_RECORD_CREATED,
    BF_USER_OR_API_ACCESS_GRANTED,
    SIGNING_MATERIAL_AVAILABLE,
    MACOS_BUILD_EXECUTOR_AVAILABLE,
)

REFERENCE_APP_ID = "bforge-reference-internal-ios"
REFERENCE_TENANT_ID = "tenant-bforge-reference"
REFERENCE_DISPLAY_NAME = "BusinessForge Reference Internal iOS"

APPLE_EXTERNAL_SETUP_READY = "APPLE_EXTERNAL_SETUP_READY"


def _state(value: str | None) -> str:
    token = (value or NOT_STARTED).strip().upper()
    if token not in VALID_STATES:
        raise AppleConnectionError(f"INVALID_SETUP_STATE:{token}")
    return token


def apple_external_setup_ready(states: dict[str, str]) -> bool:
    for key in SETUP_PREREQUISITES:
        state = _state(states.get(key))
        if state not in {VERIFIED, NOT_APPLICABLE}:
            return False
    return True


def evaluate_setup_states(states: dict[str, str]) -> dict[str, Any]:
    normalized = {key: _state(states.get(key)) for key in SETUP_PREREQUISITES}
    ready = apple_external_setup_ready(normalized)
    missing = [
        key
        for key, state in normalized.items()
        if state not in {VERIFIED, NOT_APPLICABLE}
    ]
    return {
        "prerequisites": normalized,
        "apple_external_setup_ready": ready,
        "status": APPLE_EXTERNAL_SETUP_READY if ready else "APPLE_EXTERNAL_SETUP_INCOMPLETE",
        "missing": missing,
        "blanket_apple_connected": False,
    }


def console_app_create_contract(
    profile: CustomerAppReleaseProfile,
    *,
    principal_identity: str,
    owner_type: str = OWNER_CUSTOMER,
) -> dict[str, Any]:
    if owner_type not in VALID_OWNER_TYPES:
        raise AppleConnectionError("INVALID_PUBLISHER_OWNER_TYPE")
    if owner_type == OWNER_REFERENCE and not is_reference_ios_bundle(profile.bundle_identifier):
        raise AppleConnectionError("REFERENCE_BUNDLE_REQUIRED")
    locale = profile.store.locale or "de-DE"
    return {
        "kind": "APP_STORE_CONNECT_APP_CREATE_CONTRACT",
        "created_by_businessforge": False,
        "external_publisher_action_required": True,
        "publisher_owner_type": owner_type,
        "customer_owned_publishing_proven": False,
        "app_name": profile.display_name,
        "primary_locale": locale,
        "sku_reference": profile.app_id,
        "bundle_identifier": profile.bundle_identifier,
        "support_url": profile.legal.support_url,
        "privacy_url": profile.legal.privacy_url,
        "businessforge_principal_identity": principal_identity,
        "account_holder_required": False,
        "required_roles": ["APP_MANAGER"],
        "forbidden_roles": ["ACCOUNT_HOLDER", "ADMIN", "FINANCE"],
        "notes": [
            "Create the App Store Connect app record in the customer or reference Apple account.",
            "BusinessForge does not invent an unsupported auto-create API.",
            "After first successful bundle binding, BUNDLE_IMMUTABLE = TRUE.",
        ],
    }


def reference_console_app_create_contract(*, principal_identity: str) -> dict[str, Any]:
    bundle = validate_reference_ios_bundle_id(REFERENCE_IOS_BUNDLE)
    return {
        "kind": "APP_STORE_CONNECT_APP_CREATE_CONTRACT",
        "created_by_businessforge": False,
        "external_publisher_action_required": True,
        "publisher_owner_type": OWNER_REFERENCE,
        "customer_owned_publishing_proven": False,
        "allowed_for_customer_production": False,
        "recyclable_as_customer_app": False,
        "app_name": REFERENCE_DISPLAY_NAME,
        "primary_locale": "de-DE",
        "sku_reference": REFERENCE_APP_ID,
        "bundle_identifier": bundle,
        "customer_app_id": REFERENCE_APP_ID,
        "tenant_id": REFERENCE_TENANT_ID,
        "environment": OWNER_REFERENCE,
        "support_url": "",
        "privacy_url": "",
        "businessforge_principal_identity": principal_identity,
        "account_holder_required": False,
        "required_roles": ["APP_MANAGER"],
        "forbidden_roles": ["ACCOUNT_HOLDER", "ADMIN", "FINANCE"],
        "notes": [
            "Create the App Store Connect app in a BusinessForge-owned reference Apple account.",
            "Do not auto-create an Apple Developer account.",
            "Never recycle this bundle as a customer app.",
            "CUSTOMER_OWNED_PUBLISHING_PROVEN stays false.",
        ],
    }


def owner_type_claims(owner_type: str, *, live_testflight_proven: bool = False) -> dict[str, Any]:
    if owner_type not in VALID_OWNER_TYPES:
        raise AppleConnectionError("INVALID_PUBLISHER_OWNER_TYPE")
    reference = owner_type == OWNER_REFERENCE
    return {
        "publisher_owner_type": owner_type,
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": bool(live_testflight_proven and reference),
        "allowed_for_customer_production": owner_type == OWNER_CUSTOMER,
        "allowed_for_platform_live_proof": reference,
    }


def rotate_publisher_credential(
    connection: ApplePublisherConnection,
    new_private_key_secret_reference: str,
) -> ApplePublisherConnection:
    if not new_private_key_secret_reference.strip():
        raise AppleConnectionError("CREDENTIAL_MISSING")
    return ApplePublisherConnection(
        customer_app_id=connection.customer_app_id,
        tenant_id=connection.tenant_id,
        bundle_identifier=connection.bundle_identifier,
        team_id_reference=connection.team_id_reference,
        issuer_reference=connection.issuer_reference,
        key_id_reference=connection.key_id_reference,
        private_key_secret_reference=new_private_key_secret_reference.strip(),
        scope=connection.scope,
        permissions=connection.permissions,
        connection_status=connection.connection_status,
        role_status=connection.role_status,
        last_verified_at="",
        last_error_code="",
        created_at=connection.created_at,
        updated_at=connection.updated_at,
        owner_type=connection.owner_type,
        sku_reference=connection.sku_reference,
    )
