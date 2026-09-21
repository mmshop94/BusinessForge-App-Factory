"""Workspace audit for Apple TestFlight live proof. No secrets. Nothing invented."""

from __future__ import annotations

import os
from typing import Any, Mapping

from app_factory.application.customer_release.apple.evidence import _assert_public
from app_factory.application.customer_release.apple.executor import probe_ios_build_executor
from app_factory.application.customer_release.apple.setup_contract import (
    ACTION_REQUIRED,
    AGREEMENTS_ACCEPTED,
    APP_RECORD_CREATED,
    APP_STORE_CONNECT_API_ACCESS,
    APPLE_DEVELOPER_ACCOUNT,
    BF_USER_OR_API_ACCESS_GRANTED,
    BLOCKED_EXTERNAL,
    BUNDLE_ID_REGISTERED,
    MACOS_BUILD_EXECUTOR_AVAILABLE,
    NOT_APPLICABLE,
    SIGNING_MATERIAL_AVAILABLE,
    evaluate_setup_states,
    reference_console_app_create_contract,
)
from app_factory.application.customer_release.play import OWNER_REFERENCE
from app_factory.application.customer_release.secrets import ops_secret_root_from_env
from app_factory.application.package_identity import REFERENCE_IOS_BUNDLE

LIVE_TEST_ENV = "REAL_APPLE_TESTFLIGHT_TEST"


def audit_workspace_apple_live_preconditions(
    *,
    environ: Mapping[str, str] | None = None,
    source_baseline: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = dict(os.environ if environ is None else environ)
    live_flag = env.get(LIVE_TEST_ENV, "").strip() == "1"
    ops_root = ops_secret_root_from_env(env)
    executor = probe_ios_build_executor(environ=dict(env))
    prerequisites = {
        APPLE_DEVELOPER_ACCOUNT: BLOCKED_EXTERNAL,
        APP_STORE_CONNECT_API_ACCESS: ACTION_REQUIRED,
        AGREEMENTS_ACCEPTED: BLOCKED_EXTERNAL,
        BUNDLE_ID_REGISTERED: BLOCKED_EXTERNAL,
        APP_RECORD_CREATED: BLOCKED_EXTERNAL,
        BF_USER_OR_API_ACCESS_GRANTED: BLOCKED_EXTERNAL,
        SIGNING_MATERIAL_AVAILABLE: ACTION_REQUIRED,
        MACOS_BUILD_EXECUTOR_AVAILABLE: BLOCKED_EXTERNAL
        if executor["status"] != "LOCAL_MACOS_AVAILABLE"
        else ACTION_REQUIRED,
    }
    setup = evaluate_setup_states(prerequisites)
    contract = reference_console_app_create_contract(principal_identity="ops://apple/principal")
    payload: dict[str, Any] = {
        "kind": "APPLE_TESTFLIGHT_LIVE_PROOF_AUDIT_V1",
        "LIVE_APPLE_PROOF": BLOCKED_EXTERNAL,
        "IOS_IMPLEMENTATION_READY": True,
        "APPLE_ONBOARDING_CONTRACT_READY": True,
        "IOS_BUILD_BLOCKED_NO_MACOS_EXECUTOR": executor["status"] != "LOCAL_MACOS_AVAILABLE",
        "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
        "REFERENCE_PUBLISHER_LIVE_PROOF": False,
        "APP_STORE_PRODUCTION": "NOT_IMPLEMENTED",
        "IPA_BUILT": "NOT_RUN",
        "TESTFLIGHT_UPLOAD": "NOT_RUN",
        "publisher_owner_type": OWNER_REFERENCE,
        "reference_identity": {
            "bundle_identifier": REFERENCE_IOS_BUNDLE,
            "recyclable_as_customer_app": False,
        },
        "workspace_wiring": {
            LIVE_TEST_ENV: "VERIFIED" if live_flag else ACTION_REQUIRED,
            "BF_OPS_SECRET_DIR": "VERIFIED" if ops_root is not None else ACTION_REQUIRED,
        },
        "prerequisites": prerequisites,
        "setup": setup,
        "executor": executor,
        "reference_setup_contract": {
            "created_by_businessforge": contract["created_by_businessforge"],
            "bundle_identifier": contract["bundle_identifier"],
            "publisher_owner_type": contract["publisher_owner_type"],
            "customer_owned_publishing_proven": False,
        },
        "google_status_unchanged": {
            "LIVE_GOOGLE_PLAY_PROOF": BLOCKED_EXTERNAL,
            "CUSTOMER_OWNED_PUBLISHING_PROVEN": False,
            "ANDROID_PRODUCTION_READY": "NOT_IMPLEMENTED",
        },
        "developer_account_auto_created": False,
        "app_record_auto_created": False,
        "source_baseline": dict(source_baseline or {}),
        "notes": [
            "No Apple Developer account was created by this audit.",
            "No private keys or provisioning profiles are included.",
            "Production App Store submission remains APP_STORE_PRODUCTION_SUBMISSION_BLOCKED.",
        ],
    }
    _assert_public(payload)
    return payload
