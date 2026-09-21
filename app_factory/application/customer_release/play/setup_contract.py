"""Google Play external setup contract — per-prerequisite states, no blanket 'connected' flag."""

from __future__ import annotations

from typing import Any

from app_factory.application.customer_release.play import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    VALID_OWNER_TYPES,
    GooglePlayPublisherConnection,
)
from app_factory.application.customer_release.profile import CustomerAppReleaseProfile
from app_factory.application.package_identity import (
    REFERENCE_INTERNAL_PACKAGE,
    is_reference_android_package,
    validate_reference_application_id,
)
from app_factory.domain.errors import PlayConnectionError

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

PLAY_DEVELOPER_ACCOUNT = "PLAY_DEVELOPER_ACCOUNT"
PLAY_APP_CREATED = "PLAY_APP_CREATED"
PLAY_APP_SIGNING_TERMS_ACCEPTED = "PLAY_APP_SIGNING_TERMS_ACCEPTED"
PACKAGE_BOUND = "PACKAGE_BOUND"
BF_PRINCIPAL_GRANTED = "BF_PRINCIPAL_GRANTED"
VIEW_APP_INFORMATION_GRANTED = "VIEW_APP_INFORMATION_GRANTED"
TEST_RELEASE_PERMISSION_GRANTED = "TEST_RELEASE_PERMISSION_GRANTED"
PUBLISHER_CREDENTIAL_AVAILABLE = "PUBLISHER_CREDENTIAL_AVAILABLE"
INTERNAL_TESTER_CONFIGURATION = "INTERNAL_TESTER_CONFIGURATION"

SETUP_PREREQUISITES = (
    PLAY_DEVELOPER_ACCOUNT,
    PLAY_APP_CREATED,
    PLAY_APP_SIGNING_TERMS_ACCEPTED,
    PACKAGE_BOUND,
    BF_PRINCIPAL_GRANTED,
    VIEW_APP_INFORMATION_GRANTED,
    TEST_RELEASE_PERMISSION_GRANTED,
    PUBLISHER_CREDENTIAL_AVAILABLE,
    INTERNAL_TESTER_CONFIGURATION,
)

OPTIONAL_PREREQUISITES = frozenset({INTERNAL_TESTER_CONFIGURATION})

REFERENCE_APP_ID = "bforge-reference-internal"
REFERENCE_TENANT_ID = "tenant-bforge-reference"
REFERENCE_DISPLAY_NAME = "BusinessForge Reference Internal"

PLAY_EXTERNAL_SETUP_READY = "PLAY_EXTERNAL_SETUP_READY"


def _state(value: str | None) -> str:
    token = (value or NOT_STARTED).strip().upper()
    if token not in VALID_STATES:
        raise PlayConnectionError(f"INVALID_SETUP_STATE:{token}")
    return token


def play_external_setup_ready(states: dict[str, str]) -> bool:
    """All required prerequisites VERIFIED or NOT_APPLICABLE. Fail-closed on anything else."""
    for key in SETUP_PREREQUISITES:
        raw = states.get(key)
        if not raw and key in OPTIONAL_PREREQUISITES:
            continue
        state = _state(raw)
        if state not in {VERIFIED, NOT_APPLICABLE}:
            return False
    return True


def evaluate_setup_states(states: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, str] = {}
    for key in SETUP_PREREQUISITES:
        raw = states.get(key)
        if not raw and key in OPTIONAL_PREREQUISITES:
            normalized[key] = NOT_APPLICABLE
        else:
            normalized[key] = _state(raw)
    ready = play_external_setup_ready(normalized)
    missing = [
        key
        for key, state in normalized.items()
        if state not in {VERIFIED, NOT_APPLICABLE}
    ]
    failed = [key for key, state in normalized.items() if state == FAILED]
    return {
        "prerequisites": normalized,
        "play_external_setup_ready": ready,
        "status": PLAY_EXTERNAL_SETUP_READY if ready else "PLAY_EXTERNAL_SETUP_INCOMPLETE",
        "missing": missing,
        "failed": failed,
        "blanket_google_connected": False,
    }


def console_app_create_contract(
    profile: CustomerAppReleaseProfile,
    *,
    principal_identity: str,
    owner_type: str = OWNER_CUSTOMER,
) -> dict[str, Any]:
    """Data the publisher needs for the one-time Play Console app-create step.

    BusinessForge does not create the Play app via API. This contract is not a claim
    that the app already exists.
    """
    if owner_type not in VALID_OWNER_TYPES:
        raise PlayConnectionError("INVALID_PUBLISHER_OWNER_TYPE")
    if owner_type == OWNER_REFERENCE and not is_reference_android_package(profile.package_name):
        raise PlayConnectionError("REFERENCE_PACKAGE_REQUIRED")
    locale = profile.store.locale or "de-DE"
    language = locale.split("-")[0] if locale else "de"
    return {
        "kind": "PLAY_CONSOLE_APP_CREATE_CONTRACT",
        "created_by_businessforge": False,
        "external_publisher_action_required": True,
        "publisher_owner_type": owner_type,
        "customer_owned_publishing_proven": False,
        "app_name": profile.display_name,
        "default_language": language,
        "app_or_game": "App",
        "free_or_paid": "Free",
        "support_email": profile.legal.support_email,
        "package_name": profile.package_name,
        "play_app_signing_requirement": "REQUIRED",
        "businessforge_principal_identity": principal_identity,
        "required_permissions": [
            "VIEW_APP_INFORMATION",
            "MANAGE_TEST_RELEASES",
        ],
        "optional_permissions": [
            "MANAGE_TESTERS",
            "MANAGE_STORE_LISTING",
        ],
        "forbidden_permissions": [
            "PLAY_ADMIN",
            "ACCOUNT_WIDE_ADMIN",
            "PRODUCTION_RELEASE",
        ],
        "notes": [
            "Create the Play Console app record in the publisher account.",
            "BusinessForge cannot invent this API step.",
            "After first successful package binding, PACKAGE_IMMUTABLE = TRUE.",
        ],
    }


def reference_console_app_create_contract(
    *,
    principal_identity: str,
    package_name: str = REFERENCE_INTERNAL_PACKAGE,
) -> dict[str, Any]:
    """One-time Play Console contract for the BusinessForge reference identity.

    Does not create a Play developer account or Play app. Package is reserved
    for BUSINESSFORGE_REFERENCE and must never be recycled as a customer app.
    """
    package = validate_reference_application_id(package_name)
    return {
        "kind": "PLAY_CONSOLE_APP_CREATE_CONTRACT",
        "created_by_businessforge": False,
        "external_publisher_action_required": True,
        "publisher_owner_type": OWNER_REFERENCE,
        "customer_owned_publishing_proven": False,
        "allowed_for_customer_production": False,
        "recyclable_as_customer_app": False,
        "app_name": REFERENCE_DISPLAY_NAME,
        "default_language": "de",
        "app_or_game": "App",
        "free_or_paid": "Free",
        "support_email": "",
        "support_email_status": ACTION_REQUIRED,
        "package_name": package,
        "customer_app_id": REFERENCE_APP_ID,
        "tenant_id": REFERENCE_TENANT_ID,
        "environment": OWNER_REFERENCE,
        "play_app_signing_requirement": "REQUIRED",
        "businessforge_principal_identity": principal_identity,
        "required_permissions": [
            "VIEW_APP_INFORMATION",
            "MANAGE_TEST_RELEASES",
        ],
        "optional_permissions": [
            "MANAGE_TESTERS",
        ],
        "forbidden_permissions": [
            "PLAY_ADMIN",
            "ACCOUNT_WIDE_ADMIN",
            "PRODUCTION_RELEASE",
            "FINANCIAL_DATA",
        ],
        "notes": [
            "Create the Play Console app record in a BusinessForge-owned reference publisher account.",
            "BusinessForge cannot invent this API step and does not auto-create developer accounts.",
            "Do not use de.hutthurm.dorfladen or any future customer package.",
            "After first successful package binding, PACKAGE_IMMUTABLE = TRUE.",
            "This identity is BUSINESSFORGE_REFERENCE only and must never be marked CUSTOMER_OWNED_PUBLISHING_PROVEN.",
        ],
    }


def owner_type_claims(owner_type: str, *, live_internal_proven: bool = False) -> dict[str, Any]:
    if owner_type not in VALID_OWNER_TYPES:
        raise PlayConnectionError("INVALID_PUBLISHER_OWNER_TYPE")
    reference = owner_type == OWNER_REFERENCE
    return {
        "publisher_owner_type": owner_type,
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": bool(live_internal_proven and reference),
        "allowed_for_customer_production": owner_type == OWNER_CUSTOMER,
        "allowed_for_platform_live_proof": reference,
    }


def rotate_publisher_credential(
    connection: GooglePlayPublisherConnection,
    new_credential_secret_reference: str,
) -> GooglePlayPublisherConnection:
    """Replace the secret reference only. Package, app identity, and owner type stay put."""
    if not new_credential_secret_reference.strip():
        raise PlayConnectionError("CREDENTIAL_MISSING")
    return GooglePlayPublisherConnection(
        customer_app_id=connection.customer_app_id,
        tenant_id=connection.tenant_id,
        package_name=connection.package_name,
        developer_account_reference=connection.developer_account_reference,
        principal_reference=connection.principal_reference,
        credential_secret_reference=new_credential_secret_reference.strip(),
        scope=connection.scope,
        permissions=connection.permissions,
        connection_status=connection.connection_status,
        permission_status=connection.permission_status,
        last_verified_at="",
        last_error_code="",
        created_at=connection.created_at,
        updated_at=connection.updated_at,
        owner_type=connection.owner_type,
    )
