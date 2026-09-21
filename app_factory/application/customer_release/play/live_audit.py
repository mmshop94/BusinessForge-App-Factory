"""Workspace audit for Google Play live publisher proof. No secrets. Nothing invented."""

from __future__ import annotations

import importlib.util
import os
from typing import Any, Mapping

from app_factory.application.customer_release.play import OWNER_REFERENCE, stamp_now
from app_factory.application.customer_release.play.evidence import _assert_public
from app_factory.application.customer_release.play.setup_contract import (
    ACTION_REQUIRED,
    BF_PRINCIPAL_GRANTED,
    BLOCKED_EXTERNAL,
    INTERNAL_TESTER_CONFIGURATION,
    NOT_APPLICABLE,
    PACKAGE_BOUND,
    PLAY_APP_CREATED,
    PLAY_APP_SIGNING_TERMS_ACCEPTED,
    PLAY_DEVELOPER_ACCOUNT,
    PUBLISHER_CREDENTIAL_AVAILABLE,
    TEST_RELEASE_PERMISSION_GRANTED,
    VIEW_APP_INFORMATION_GRANTED,
    REFERENCE_APP_ID,
    REFERENCE_TENANT_ID,
    evaluate_setup_states,
    reference_console_app_create_contract,
)
from app_factory.application.customer_release.secrets import ops_secret_root_from_env
from app_factory.application.package_identity import REFERENCE_INTERNAL_PACKAGE

LIVE_TEST_ENV = "REAL_GOOGLE_PLAY_INTERNAL_TEST"
GOOGLE_AUTH_EXTRA = "play"

_GOOGLE_SIDE = (
    PLAY_DEVELOPER_ACCOUNT,
    PLAY_APP_CREATED,
    PLAY_APP_SIGNING_TERMS_ACCEPTED,
    PACKAGE_BOUND,
    BF_PRINCIPAL_GRANTED,
    VIEW_APP_INFORMATION_GRANTED,
    TEST_RELEASE_PERMISSION_GRANTED,
)


def _module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def audit_workspace_play_live_preconditions(
    *,
    environ: Mapping[str, str] | None = None,
    source_baseline: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Honest per-prerequisite statuses for this operator workspace.

    Does not create a Play developer account. Does not authenticate. Does not
    log credential values. Google-side items stay BLOCKED_EXTERNAL until an
    operator wires a real reference publisher.
    """
    env = dict(os.environ if environ is None else environ)
    live_flag = env.get(LIVE_TEST_ENV, "").strip() == "1"
    ops_root = ops_secret_root_from_env(env)
    google_auth = _module_present("google.auth")
    httpx_present = _module_present("httpx")

    workspace: dict[str, str] = {
        LIVE_TEST_ENV: "VERIFIED" if live_flag else ACTION_REQUIRED,
        "BF_OPS_SECRET_DIR": "VERIFIED" if ops_root is not None else ACTION_REQUIRED,
        "GOOGLE_AUTH_LIBRARY": "VERIFIED" if google_auth else ACTION_REQUIRED,
        "HTTPX": "VERIFIED" if httpx_present else ACTION_REQUIRED,
    }

    prerequisites: dict[str, str] = {
        PLAY_DEVELOPER_ACCOUNT: BLOCKED_EXTERNAL,
        PLAY_APP_CREATED: BLOCKED_EXTERNAL,
        PLAY_APP_SIGNING_TERMS_ACCEPTED: BLOCKED_EXTERNAL,
        PACKAGE_BOUND: BLOCKED_EXTERNAL,
        BF_PRINCIPAL_GRANTED: BLOCKED_EXTERNAL,
        VIEW_APP_INFORMATION_GRANTED: BLOCKED_EXTERNAL,
        TEST_RELEASE_PERMISSION_GRANTED: BLOCKED_EXTERNAL,
        PUBLISHER_CREDENTIAL_AVAILABLE: ACTION_REQUIRED,
        INTERNAL_TESTER_CONFIGURATION: NOT_APPLICABLE,
    }

    setup = evaluate_setup_states(prerequisites)
    contract = reference_console_app_create_contract(
        principal_identity="ops://play/principal"
    )
    _assert_public(contract)

    payload: dict[str, Any] = {
        "kind": "GOOGLE_PLAY_LIVE_PUBLISHER_PROOF_AUDIT_V1",
        "audited_at": stamp_now(),
        "LIVE_GOOGLE_PLAY_PROOF": BLOCKED_EXTERNAL,
        "PLAY_APP_BOUND": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": False,
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "ANDROID_PRODUCTION_READY": "NOT_IMPLEMENTED",
        "PRODUCTION_SUBMISSION": "PRODUCTION_SUBMISSION_BLOCKED",
        "AAB_BUILT": "NOT_RUN",
        "INTERNAL_TRACK_UPLOAD": "NOT_RUN",
        "INSTALLATION_PROOF": "INSTALLATION_PROOF_NOT_RUN",
        "publisher_owner_type": OWNER_REFERENCE,
        "reference_identity": {
            "package_name": REFERENCE_INTERNAL_PACKAGE,
            "customer_app_id": REFERENCE_APP_ID,
            "tenant_id": REFERENCE_TENANT_ID,
            "recyclable_as_customer_app": False,
            "customer_package_forbidden": "de.hutthurm.dorfladen",
        },
        "workspace_wiring": workspace,
        "prerequisites": prerequisites,
        "setup": setup,
        "reference_setup_contract": {
            "created_by_businessforge": contract["created_by_businessforge"],
            "external_publisher_action_required": contract[
                "external_publisher_action_required"
            ],
            "package_name": contract["package_name"],
            "publisher_owner_type": contract["publisher_owner_type"],
            "customer_owned_publishing_proven": False,
            "required_permissions": contract["required_permissions"],
            "optional_permissions": contract["optional_permissions"],
            "forbidden_permissions": contract["forbidden_permissions"],
        },
        "required_permissions": ["VIEW_APP_INFORMATION", "MANAGE_TEST_RELEASES"],
        "optional_permissions": ["MANAGE_TESTERS"],
        "forbidden_permissions": [
            "PLAY_ADMIN",
            "ACCOUNT_WIDE_ADMIN",
            "PRODUCTION_RELEASE",
            "FINANCIAL_DATA",
        ],
        "live_test_gate": LIVE_TEST_ENV,
        "google_auth_extra": GOOGLE_AUTH_EXTRA,
        "ops_secret_dir_configured": ops_root is not None,
        "google_auth_present": google_auth,
        "httpx_present": httpx_present,
        "live_flag_set": live_flag,
        "developer_account_auto_created": False,
        "play_app_auto_created": False,
        "source_baseline": dict(source_baseline or {}),
        "notes": [
            "No Play developer account was created by this audit.",
            "No credential values or private keys are included.",
            "BUSINESSFORGE_REFERENCE must never be read as CUSTOMER_OWNED_PUBLISHING_PROVEN.",
            "Production track writes remain PRODUCTION_SUBMISSION_BLOCKED before any Google write.",
        ],
    }
    _assert_public(payload)
    if payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is True:
        raise RuntimeError("REFERENCE_CANNOT_CLAIM_CUSTOMER_OWNED_PROOF")
    if any(prerequisites[key] == "VERIFIED" for key in _GOOGLE_SIDE):
        raise RuntimeError("GOOGLE_SIDE_MUST_NOT_BE_INVENTED")
    return payload
