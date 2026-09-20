"""Customer Play onboarding gate + structured instruction data for a future dashboard."""

from __future__ import annotations

from typing import Any

from app_factory.application.customer_release.play.setup_contract import (
    ACTION_REQUIRED,
    BF_PRINCIPAL_GRANTED,
    FAILED,
    NOT_STARTED,
    PACKAGE_BOUND,
    PLAY_APP_CREATED,
    PLAY_APP_SIGNING_TERMS_ACCEPTED,
    PLAY_DEVELOPER_ACCOUNT,
    PLAY_EXTERNAL_SETUP_READY,
    PUBLISHER_CREDENTIAL_AVAILABLE,
    TEST_RELEASE_PERMISSION_GRANTED,
    VERIFIED,
    VIEW_APP_INFORMATION_GRANTED,
    evaluate_setup_states,
)

ACCOUNT_CREATED = "ACCOUNT_CREATED"
APP_CREATED = "APP_CREATED"
BF_INVITED = "BF_INVITED"
APP_SCOPED_PERMISSIONS_GRANTED = "APP_SCOPED_PERMISSIONS_GRANTED"
CREDENTIAL_CONNECTED = "CREDENTIAL_CONNECTED"
CONNECTION_VERIFIED = "CONNECTION_VERIFIED"
PACKAGE_BOUND_GATE = "PACKAGE_BOUND"
TEST_DELIVERY_READY = "TEST_DELIVERY_READY"

ONBOARDING_STAGES = (
    ACCOUNT_CREATED,
    APP_CREATED,
    BF_INVITED,
    APP_SCOPED_PERMISSIONS_GRANTED,
    CREDENTIAL_CONNECTED,
    CONNECTION_VERIFIED,
    PACKAGE_BOUND_GATE,
    TEST_DELIVERY_READY,
)

_INSTRUCTIONS: tuple[dict[str, Any], ...] = (
    {
        "step_id": "play_developer_account",
        "title": "Play-Entwicklerkonto anlegen",
        "description": "Legen Sie ein Google-Play-Console-Entwicklerkonto Ihrer Firma an. BusinessForge erstellt dieses Konto nicht.",
        "required_value": PLAY_DEVELOPER_ACCOUNT,
        "verification_method": "publisher_declares_account_then_ops_reference",
        "blocking": True,
        "prerequisite": PLAY_DEVELOPER_ACCOUNT,
    },
    {
        "step_id": "play_app_created",
        "title": "App in der Play Console anlegen",
        "description": "Einmaliger manueller Schritt: App-Name, Sprache, App/Game, Kostenlos, Support-E-Mail und Package-Name laut Setup-Contract. Keine automatische API-Erzeugung.",
        "required_value": PLAY_APP_CREATED,
        "verification_method": "package_visible_via_publisher_api",
        "blocking": True,
        "prerequisite": PLAY_APP_CREATED,
    },
    {
        "step_id": "play_app_signing_terms",
        "title": "Play App Signing akzeptieren",
        "description": "Google Play App Signing für diese App akzeptieren. BusinessForge signiert nur mit dem Upload-Schlüssel.",
        "required_value": PLAY_APP_SIGNING_TERMS_ACCEPTED,
        "verification_method": "publisher_console_enrollment",
        "blocking": True,
        "prerequisite": PLAY_APP_SIGNING_TERMS_ACCEPTED,
    },
    {
        "step_id": "bf_principal_granted",
        "title": "BusinessForge auf diese App einladen",
        "description": "Laden Sie das BusinessForge-Principal nur für diese eine App ein — nicht als Konto-Admin.",
        "required_value": BF_PRINCIPAL_GRANTED,
        "verification_method": "app_scoped_authentication",
        "blocking": True,
        "prerequisite": BF_PRINCIPAL_GRANTED,
        "missing_summary": "Es fehlt: BusinessForge Zugriff auf diese App",
    },
    {
        "step_id": "view_app_information",
        "title": "Berechtigung: App-Informationen ansehen",
        "description": "App-bezogene Berechtigung zum Ansehen der App-Informationen erteilen.",
        "required_value": VIEW_APP_INFORMATION_GRANTED,
        "verification_method": "permission_probe",
        "blocking": True,
        "prerequisite": VIEW_APP_INFORMATION_GRANTED,
    },
    {
        "step_id": "test_release_permission",
        "title": "Berechtigung: Test-Releases",
        "description": "App-bezogene Berechtigung zum Veröffentlichen auf Teststrecken erteilen. Produktion bleibt gesperrt.",
        "required_value": TEST_RELEASE_PERMISSION_GRANTED,
        "verification_method": "test_track_permission_probe",
        "blocking": True,
        "prerequisite": TEST_RELEASE_PERMISSION_GRANTED,
        "missing_summary": "Es fehlt: Berechtigung für Test-Releases",
    },
    {
        "step_id": "publisher_credential",
        "title": "App-scoped Zugangsdaten verbinden",
        "description": "Ops-Secret-Referenz hinterlegen. Niemals Passwörter, JSON-Keys oder Tokens per E-Mail senden.",
        "required_value": PUBLISHER_CREDENTIAL_AVAILABLE,
        "verification_method": "secret_resolver_has",
        "blocking": True,
        "prerequisite": PUBLISHER_CREDENTIAL_AVAILABLE,
    },
    {
        "step_id": "package_bound",
        "title": "Package an die App binden",
        "description": "Nach dem ersten erfolgreichen Binding ist der Package-Name unveränderlich (PACKAGE_IMMUTABLE).",
        "required_value": PACKAGE_BOUND,
        "verification_method": "identity_registry_play_bound",
        "blocking": True,
        "prerequisite": PACKAGE_BOUND,
    },
)


def instruction_steps(states: dict[str, str]) -> list[dict[str, Any]]:
    evaluated = evaluate_setup_states(states)
    prereq = evaluated["prerequisites"]
    steps: list[dict[str, Any]] = []
    for item in _INSTRUCTIONS:
        status = prereq[str(item["prerequisite"])]
        steps.append(
            {
                "step_id": item["step_id"],
                "title": item["title"],
                "description": item["description"],
                "required_value": item["required_value"],
                "verification_method": item["verification_method"],
                "status": status,
                "blocking": item["blocking"],
            }
        )
    return steps


def onboarding_summary(states: dict[str, str]) -> str:
    """Operator-facing sentence. Never 'Google funktioniert nicht'."""
    evaluated = evaluate_setup_states(states)
    if evaluated["play_external_setup_ready"]:
        return "Google Play ist bereit"
    prereq = evaluated["prerequisites"]
    if prereq[BF_PRINCIPAL_GRANTED] not in {VERIFIED}:
        return "Es fehlt: BusinessForge Zugriff auf diese App"
    if prereq[TEST_RELEASE_PERMISSION_GRANTED] not in {VERIFIED}:
        return "Es fehlt: Berechtigung für Test-Releases"
    if prereq[PLAY_APP_CREATED] not in {VERIFIED}:
        return "Es fehlt: Play-Console-App für dieses Package"
    if prereq[PUBLISHER_CREDENTIAL_AVAILABLE] not in {VERIFIED}:
        return "Es fehlt: verbundene Publisher-Zugangsdaten"
    if prereq[PACKAGE_BOUND] not in {VERIFIED}:
        return "Es fehlt: Package-Bindung"
    if prereq[PLAY_DEVELOPER_ACCOUNT] not in {VERIFIED}:
        return "Es fehlt: Play-Entwicklerkonto"
    if prereq[PLAY_APP_SIGNING_TERMS_ACCEPTED] not in {VERIFIED}:
        return "Es fehlt: Play App Signing"
    if prereq[VIEW_APP_INFORMATION_GRANTED] not in {VERIFIED}:
        return "Es fehlt: Berechtigung App-Informationen ansehen"
    return "Es fehlen noch Play-Einrichtungsschritte"


def evaluate_customer_play_onboarding(
    states: dict[str, str],
    *,
    connection_verified: bool = False,
    test_delivery_ready: bool = False,
) -> dict[str, Any]:
    evaluated = evaluate_setup_states(states)
    prereq = evaluated["prerequisites"]
    stages = {
        ACCOUNT_CREATED: prereq[PLAY_DEVELOPER_ACCOUNT],
        APP_CREATED: prereq[PLAY_APP_CREATED],
        BF_INVITED: prereq[BF_PRINCIPAL_GRANTED],
        APP_SCOPED_PERMISSIONS_GRANTED: (
            VERIFIED
            if prereq[VIEW_APP_INFORMATION_GRANTED] == VERIFIED
            and prereq[TEST_RELEASE_PERMISSION_GRANTED] == VERIFIED
            else ACTION_REQUIRED
        ),
        CREDENTIAL_CONNECTED: prereq[PUBLISHER_CREDENTIAL_AVAILABLE],
        CONNECTION_VERIFIED: VERIFIED if connection_verified else _gate_state(prereq[BF_PRINCIPAL_GRANTED]),
        PACKAGE_BOUND_GATE: prereq[PACKAGE_BOUND],
        TEST_DELIVERY_READY: (
            VERIFIED
            if test_delivery_ready and evaluated["play_external_setup_ready"]
            else _gate_state(prereq[TEST_RELEASE_PERMISSION_GRANTED])
        ),
    }
    return {
        "kind": "CUSTOMER_PLAY_ONBOARDING",
        "stages": stages,
        "setup": evaluated,
        "summary": onboarding_summary(states),
        "google_play_ready": evaluated["play_external_setup_ready"] and connection_verified,
        "status": PLAY_EXTERNAL_SETUP_READY if evaluated["play_external_setup_ready"] else "ONBOARDING_INCOMPLETE",
        "instructions": instruction_steps(states),
        "failed": any(state == FAILED for state in prereq.values()),
        "not_started": all(state == NOT_STARTED for state in prereq.values()),
    }


def _gate_state(prereq_state: str) -> str:
    if prereq_state == VERIFIED:
        return ACTION_REQUIRED
    return prereq_state
