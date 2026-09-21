"""Play onboarding gate, preflight, owner type, evidence, and fail-closed live parity."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.play import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    STATUS_AUTH_FAILED,
    STATUS_CREDENTIAL_MISSING,
    STATUS_PLAY_ACCOUNT_REQUIREMENT_PENDING,
    STATUS_READY,
    GooglePlayPublisherConnection,
)
from app_factory.application.customer_release.play.approval import ApprovalRegistry
from app_factory.application.customer_release.play.delivery import (
    PLAY_INTERNAL_RELEASE_VERIFIED,
    PLAY_RELEASE_READBACK_MISMATCH,
    deliver_internal_test_track,
)
from app_factory.application.customer_release.play.evidence import serialize_internal_live_proof
from app_factory.application.customer_release.play.onboarding import (
    evaluate_customer_play_onboarding,
    instruction_steps,
    onboarding_summary,
)
from app_factory.application.customer_release.play.preflight import (
    BLOCKED_EXTERNAL,
    LIVE_INTERNAL_UPLOAD_READY,
    PlayPreflightInput,
    run_preflight,
)
from app_factory.application.customer_release.play.provider import (
    PRODUCTION_SUBMISSION_BLOCKED,
    FakePlayPublisherProvider,
    GooglePlayPublisherProvider,
)
from app_factory.application.customer_release.play.setup_contract import (
    ACTION_REQUIRED,
    BF_PRINCIPAL_GRANTED,
    BLOCKED_EXTERNAL as SETUP_BLOCKED_EXTERNAL,
    INTERNAL_TESTER_CONFIGURATION,
    NOT_APPLICABLE,
    PACKAGE_BOUND,
    PLAY_APP_CREATED,
    PLAY_APP_SIGNING_TERMS_ACCEPTED,
    PLAY_DEVELOPER_ACCOUNT,
    PLAY_EXTERNAL_SETUP_READY,
    PUBLISHER_CREDENTIAL_AVAILABLE,
    TEST_RELEASE_PERMISSION_GRANTED,
    VERIFIED,
    VIEW_APP_INFORMATION_GRANTED,
    console_app_create_contract,
    evaluate_setup_states,
    reference_console_app_create_contract,
    rotate_publisher_credential,
)
from app_factory.application.customer_release.play.live_audit import (
    audit_workspace_play_live_preconditions,
)
from app_factory.application.package_identity import (
    REFERENCE_INTERNAL_PACKAGE,
    validate_customer_production_application_id,
    validate_reference_application_id,
)
from app_factory.application.customer_release.play.testers import (
    TESTER_GROUP_NOT_CONFIGURED,
    TESTER_GROUP_READY,
    resolve_tester_group,
)
from app_factory.application.customer_release.play.versioning import resolve_play_version_code
from app_factory.application.customer_release.profile import profile_from_dict
from app_factory.application.customer_release.secrets import ScopedSecretResolver
from app_factory.application.customer_release.signing import FailClosedSecretResolver
from app_factory.application.customer_release.snapshot import freeze_snapshot
from app_factory.domain.errors import PlayConnectionError, PlayDeliveryError, TenantIsolationError
from tests.test_customer_play_delivery import _connection
from tests.test_customer_release_intake import _intake, _write_assets
from tests.test_official_sales_generate_path import test_official_sales_generate_path_is_35


def _verified_states() -> dict[str, str]:
    return {
        PLAY_DEVELOPER_ACCOUNT: VERIFIED,
        PLAY_APP_CREATED: VERIFIED,
        PLAY_APP_SIGNING_TERMS_ACCEPTED: VERIFIED,
        PACKAGE_BOUND: VERIFIED,
        BF_PRINCIPAL_GRANTED: VERIFIED,
        VIEW_APP_INFORMATION_GRANTED: VERIFIED,
        TEST_RELEASE_PERMISSION_GRANTED: VERIFIED,
        PUBLISHER_CREDENTIAL_AVAILABLE: VERIFIED,
    }


def _profile(tmp_path: Path):
    _write_assets(tmp_path)
    return profile_from_dict(_intake(tmp_path))


def _scoped() -> ScopedSecretResolver:
    vault = ScopedSecretResolver()
    vault.put("tenant-hutthurm", "dorfladen-hutthurm", "ops://play/publisher-credential", "present")
    vault.put("tenant-hutthurm", "dorfladen-hutthurm", "ops://android/upload-key", "present")
    vault.put("tenant-hutthurm", "dorfladen-hutthurm", "ops://play/internal-tester-group", "group-ref")
    return vault


def test_existing_generate_path_still_35() -> None:
    test_official_sales_generate_path_is_35()


def test_external_setup_contract_generation(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    contract = console_app_create_contract(
        profile,
        principal_identity="ops://play/principal",
        owner_type=OWNER_CUSTOMER,
    )
    assert contract["created_by_businessforge"] is False
    assert contract["package_name"] == "de.hutthurm.dorfladen"
    assert contract["app_name"] == profile.display_name
    assert contract["support_email"]
    assert contract["play_app_signing_requirement"] == "REQUIRED"
    assert "VIEW_APP_INFORMATION" in contract["required_permissions"]
    assert contract["customer_owned_publishing_proven"] is False
    incomplete = evaluate_setup_states(
        {PLAY_DEVELOPER_ACCOUNT: ACTION_REQUIRED, PLAY_APP_CREATED: ACTION_REQUIRED}
    )
    assert incomplete["play_external_setup_ready"] is False
    assert incomplete["blanket_google_connected"] is False
    ready = evaluate_setup_states(_verified_states())
    assert ready["status"] == PLAY_EXTERNAL_SETUP_READY
    assert ready["play_external_setup_ready"] is True


def test_publisher_owner_type_distinction() -> None:
    customer = _connection(owner_type=OWNER_CUSTOMER)
    reference = _connection(owner_type=OWNER_REFERENCE)
    assert customer.to_public_dict()["publisher_owner_type"] == OWNER_CUSTOMER
    assert reference.to_public_dict()["publisher_owner_type"] == OWNER_REFERENCE
    assert customer.to_public_dict()["customer_owned_publishing_proven"] is False
    assert reference.to_public_dict()["customer_owned_publishing_proven"] is False
    assert reference.to_public_dict()["reference_publisher"] is True
    with pytest.raises(TenantIsolationError):
        _connection(owner_type="SOMETHING_ELSE")


def test_reference_publisher_cannot_claim_customer_owned_proof() -> None:
    payload = serialize_internal_live_proof(
        release_id="rel-1",
        snapshot_id="snap-1",
        publisher_owner_type=OWNER_REFERENCE,
        package_name="de.bforge.reference.internal",
        version_code=1,
        version_name="1.0.0",
        aab_sha256="abc",
        upload_certificate_sha256="def",
        target_track="internal",
        google_edit_reference="edit-1",
        google_bundle_version_code=1,
        commit_result="COMPLETED",
        readback_result=PLAY_INTERNAL_RELEASE_VERIFIED,
    )
    assert payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is False
    assert payload["REFERENCE_PUBLISHER_LIVE_PROOF"] is True
    with pytest.raises(PlayConnectionError):
        serialize_internal_live_proof(
            release_id="rel-1",
            snapshot_id="snap-1",
            publisher_owner_type=OWNER_REFERENCE,
            package_name="de.bforge.reference.internal",
            version_code=1,
            version_name="1.0.0",
            aab_sha256="abc",
            upload_certificate_sha256="def",
            target_track="internal",
            google_edit_reference="edit-1",
            google_bundle_version_code=1,
            commit_result="COMPLETED",
            readback_result=PLAY_INTERNAL_RELEASE_VERIFIED,
            extra={"CUSTOMER_OWNED_PUBLISHING_PROVEN": True},
        )


def test_live_evidence_rejects_secrets() -> None:
    with pytest.raises(PlayConnectionError):
        serialize_internal_live_proof(
            release_id="rel-1",
            snapshot_id="snap-1",
            publisher_owner_type=OWNER_REFERENCE,
            package_name="de.bforge.reference.internal",
            version_code=1,
            version_name="1.0.0",
            aab_sha256="abc",
            upload_certificate_sha256="def",
            target_track="internal",
            google_edit_reference="edit-1",
            google_bundle_version_code=1,
            commit_result="COMPLETED",
            readback_result=PLAY_INTERNAL_RELEASE_VERIFIED,
            extra={"private_key": "-----BEGIN PRIVATE KEY-----"},
        )


def test_package_binding_immutability() -> None:
    registry = CustomerAppIdentityRegistry()
    registry.validate_and_register(
        customer_app_id="dorfladen-hutthurm",
        package_name_android="de.hutthurm.dorfladen",
        bundle_identifier="de.hutthurm.dorfladen",
        published=False,
        version_code=1,
        production=True,
    )
    frozen = registry.freeze_play_package("dorfladen-hutthurm")
    assert frozen.package_immutable is True
    from app_factory.domain.errors import PackageMutationError

    with pytest.raises(PackageMutationError):
        registry.validate_and_register(
            customer_app_id="dorfladen-hutthurm",
            package_name_android="de.hutthurm.dorfladen2",
            bundle_identifier="de.hutthurm.dorfladen",
            published=False,
            version_code=2,
            production=True,
        )


def test_credential_rotation_does_not_mutate_identity() -> None:
    original = _connection(owner_type=OWNER_REFERENCE)
    rotated = rotate_publisher_credential(original, "ops://play/publisher-credential-rotated")
    assert rotated.package_name == original.package_name
    assert rotated.customer_app_id == original.customer_app_id
    assert rotated.tenant_id == original.tenant_id
    assert rotated.owner_type == original.owner_type
    assert rotated.credential_secret_reference == "ops://play/publisher-credential-rotated"
    assert original.credential_secret_reference != rotated.credential_secret_reference


def test_duplicate_version_handling() -> None:
    assert resolve_play_version_code(built=1, google_known=None) == 1
    assert resolve_play_version_code(built=1, google_known=0) == 1
    assert resolve_play_version_code(built=1, google_known=1) == 2
    assert resolve_play_version_code(built=3, google_known=1) == 3
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    provider.known_version_codes["de.hutthurm.dorfladen"] = 1
    edit = provider.create_edit("de.hutthurm.dorfladen")
    with pytest.raises(PlayDeliveryError):
        provider.upload_bundle(
            "de.hutthurm.dorfladen", edit, aab_sha256="sha", version_code=1
        )


def test_readback_mismatch(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    provider.readback_mismatch = True
    approvals = ApprovalRegistry()
    approvals.approve(
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        package_name=profile.package_name,
        release_id=profile.release_id,
        snapshot_id=snapshot["snapshot_id"],
    )
    with pytest.raises(PlayDeliveryError) as exc:
        deliver_internal_test_track(
            provider=provider,
            connection=_connection(),
            expected_package=profile.package_name,
            version_code=1,
            aab_sha256="sha",
            snapshot_id=snapshot["snapshot_id"],
            release_id=profile.release_id,
            tenant_id=profile.tenant_id,
            customer_app_id=profile.app_id,
            approvals=approvals,
        )
    assert PLAY_RELEASE_READBACK_MISMATCH in str(exc.value)


def test_tester_reference_isolation() -> None:
    vault = _scoped()
    ready = resolve_tester_group(
        vault,
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        group_reference="ops://play/internal-tester-group",
    )
    assert ready.status == TESTER_GROUP_READY
    missing = resolve_tester_group(
        vault,
        tenant_id="tenant-b",
        customer_app_id="app-b",
        group_reference="ops://play/internal-tester-group",
    )
    assert missing.status == TESTER_GROUP_NOT_CONFIGURED
    empty = resolve_tester_group(
        vault,
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        group_reference="",
    )
    assert empty.status == TESTER_GROUP_NOT_CONFIGURED
    assert "opt_in_url" not in empty.to_public_dict()


def test_customer_onboarding_gate_messages() -> None:
    ready = evaluate_customer_play_onboarding(
        _verified_states(), connection_verified=True, test_delivery_ready=True
    )
    assert ready["summary"] == "Google Play ist bereit"
    assert ready["google_play_ready"] is True
    steps = instruction_steps(_verified_states())
    assert {item["step_id"] for item in steps}
    assert all("title" in item and "blocking" in item for item in steps)
    missing_bf = dict(_verified_states())
    missing_bf[BF_PRINCIPAL_GRANTED] = ACTION_REQUIRED
    assert onboarding_summary(missing_bf) == "Es fehlt: BusinessForge Zugriff auf diese App"
    missing_test = dict(_verified_states())
    missing_test[TEST_RELEASE_PERMISSION_GRANTED] = ACTION_REQUIRED
    assert onboarding_summary(missing_test) == "Es fehlt: Berechtigung für Test-Releases"
    assert "Google funktioniert nicht" not in json.dumps(ready, ensure_ascii=False)


def _preflight_ready(tmp_path: Path, **overrides: object) -> PlayPreflightInput:
    profile = _profile(tmp_path)
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    profile = profile.with_snapshot_id(snapshot["snapshot_id"])
    identity = CustomerAppIdentityRegistry()
    identity.validate_and_register(
        customer_app_id=profile.app_id,
        package_name_android=profile.package_name,
        bundle_identifier=profile.bundle_identifier,
        published=False,
        version_code=1,
        production=True,
    )
    identity.freeze_play_package(profile.app_id)
    provider = FakePlayPublisherProvider()
    provider.register_app(profile.package_name)
    approvals = ApprovalRegistry()
    approvals.approve(
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        package_name=profile.package_name,
        release_id=profile.release_id,
        snapshot_id=snapshot["snapshot_id"],
    )
    inp = PlayPreflightInput(
        profile=profile,
        snapshot_id=snapshot["snapshot_id"],
        snapshot_immutable=True,
        connection=_connection(owner_type=OWNER_REFERENCE),
        resolver=_scoped(),
        provider=provider,
        approvals=approvals,
        identity=identity,
        upload_key_reference="ops://android/upload-key",
        aab_sha256="deadbeef",
        upload_certificate_sha256="cafebabe",
        setup_states=_verified_states(),
    )
    for key, value in overrides.items():
        setattr(inp, key, value)
    return inp


def test_preflight_ready(tmp_path: Path) -> None:
    result = run_preflight(_preflight_ready(tmp_path))
    assert result["status"] == LIVE_INTERNAL_UPLOAD_READY
    assert result["live_internal_upload_ready"] is True
    assert result["customer_owned_publishing_proven"] is False
    assert result["publisher_owner_type"] == OWNER_REFERENCE
    assert result["android_production_ready"] == "NOT_IMPLEMENTED"


def test_preflight_blocked_missing_credential(tmp_path: Path) -> None:
    result = run_preflight(
        _preflight_ready(tmp_path, connection=_connection(credential_secret_reference=""))
    )
    assert result["live_internal_upload_ready"] is False
    assert "PUBLISHER_CREDENTIAL_MISSING" in result["blockers"] or result["status"] != LIVE_INTERNAL_UPLOAD_READY


def test_preflight_production_hard_block(tmp_path: Path) -> None:
    result = run_preflight(_preflight_ready(tmp_path, track="production"))
    assert result["status"] == PRODUCTION_SUBMISSION_BLOCKED
    assert result["api_write_executed"] is False


def test_preflight_live_provider_blocked_external(tmp_path: Path) -> None:
    connection = _connection(owner_type=OWNER_REFERENCE)
    resolver = _scoped()
    provider = GooglePlayPublisherProvider(resolver, connection)
    result = run_preflight(
        _preflight_ready(tmp_path, provider=provider, connection=connection, resolver=resolver)
    )
    assert result["status"] == BLOCKED_EXTERNAL
    assert result["live_internal_upload_ready"] is False


def test_malformed_and_account_requirement_states() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    provider.credentials_malformed = True
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_AUTH_FAILED
    assert result["last_error_code"] == "CREDENTIAL_MALFORMED"
    provider.credentials_malformed = False
    provider.account_requirement_pending = True
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_PLAY_ACCOUNT_REQUIREMENT_PENDING


def test_real_fake_provider_state_parity() -> None:
    fake = FakePlayPublisherProvider()
    live = GooglePlayPublisherProvider(FailClosedSecretResolver(), _connection())
    fake_missing = fake.verify_connection(
        _connection(credential_secret_reference=""), expected_package="de.hutthurm.dorfladen"
    )
    live_missing = live.verify_connection(
        _connection(credential_secret_reference=""), expected_package="de.hutthurm.dorfladen"
    )
    assert fake_missing["status"] == STATUS_CREDENTIAL_MISSING
    assert live_missing["status"] == STATUS_CREDENTIAL_MISSING
    with pytest.raises(Exception):
        fake.configure_track("de.hutthurm.dorfladen", "e", track="production", version_code=1)
    with pytest.raises(Exception):
        live.configure_track("de.hutthurm.dorfladen", "e", track="production", version_code=1)
    live_result = live.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert live_result.get("status") != STATUS_READY
    assert live_result.get("live_proof") in {None, "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL"} or live_result[
        "status"
    ] == STATUS_CREDENTIAL_MISSING


def test_internal_delivery_readback_verified(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    provider = FakePlayPublisherProvider()
    provider.register_app(profile.package_name)
    approvals = ApprovalRegistry()
    approvals.approve(
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        package_name=profile.package_name,
        release_id=profile.release_id,
        snapshot_id=snapshot["snapshot_id"],
    )
    result = deliver_internal_test_track(
        provider=provider,
        connection=_connection(owner_type=OWNER_REFERENCE),
        expected_package=profile.package_name,
        version_code=1,
        aab_sha256="sha",
        snapshot_id=snapshot["snapshot_id"],
        release_id=profile.release_id,
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        approvals=approvals,
        upload_certificate_sha256="cert",
        version_name="1.0.0",
    )
    assert result["google_play"]["readback_result"] == PLAY_INTERNAL_RELEASE_VERIFIED
    assert result["google_play"]["publisher_owner_type"] == OWNER_REFERENCE
    assert result["google_play"]["customer_owned_publishing_proven"] is False
    dumped = json.dumps(result)
    assert "private_key" not in dumped
    assert "BEGIN" not in dumped


def test_wrong_signing_certificate() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    provider.expected_upload_cert_sha256 = "expected"
    edit = provider.create_edit("de.hutthurm.dorfladen")
    with pytest.raises(PlayDeliveryError):
        provider.upload_bundle(
            "de.hutthurm.dorfladen",
            edit,
            aab_sha256="sha",
            version_code=1,
            upload_certificate_sha256="other",
        )


def test_edit_create_failure() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    provider.edit_create_fail = True
    with pytest.raises(PlayDeliveryError):
        provider.create_edit("de.hutthurm.dorfladen")


def test_reference_package_is_not_customer_production() -> None:
    package = validate_reference_application_id(REFERENCE_INTERNAL_PACKAGE)
    assert package == "de.bforge.reference.internal"
    with pytest.raises(ValueError):
        validate_reference_application_id("de.hutthurm.dorfladen")
    with pytest.raises(ValueError):
        validate_customer_production_application_id(REFERENCE_INTERNAL_PACKAGE)
    registry = CustomerAppIdentityRegistry()
    record = registry.validate_and_register(
        customer_app_id="bforge-reference-internal",
        package_name_android=REFERENCE_INTERNAL_PACKAGE,
        bundle_identifier=REFERENCE_INTERNAL_PACKAGE,
        published=False,
        version_code=1,
        production=False,
    )
    assert record.package_name_android == REFERENCE_INTERNAL_PACKAGE
    with pytest.raises(ValueError):
        registry.validate_and_register(
            customer_app_id="customer-would-recycle",
            package_name_android=REFERENCE_INTERNAL_PACKAGE,
            bundle_identifier=REFERENCE_INTERNAL_PACKAGE,
            published=False,
            version_code=1,
            production=True,
        )
    frozen = registry.freeze_play_package("bforge-reference-internal")
    assert frozen.package_immutable is True


def test_reference_setup_contract_is_not_customer_owned() -> None:
    contract = reference_console_app_create_contract(principal_identity="ops://play/principal")
    assert contract["created_by_businessforge"] is False
    assert contract["package_name"] == REFERENCE_INTERNAL_PACKAGE
    assert contract["publisher_owner_type"] == OWNER_REFERENCE
    assert contract["customer_owned_publishing_proven"] is False
    assert contract["recyclable_as_customer_app"] is False
    assert "PRODUCTION_RELEASE" in contract["forbidden_permissions"]


def test_customer_package_cannot_be_reference_setup_contract(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    with pytest.raises(PlayConnectionError):
        console_app_create_contract(
            profile,
            principal_identity="ops://play/principal",
            owner_type=OWNER_REFERENCE,
        )


def test_blocked_external_is_not_setup_ready() -> None:
    blocked = evaluate_setup_states(
        {
            PLAY_DEVELOPER_ACCOUNT: SETUP_BLOCKED_EXTERNAL,
            PLAY_APP_CREATED: SETUP_BLOCKED_EXTERNAL,
            PLAY_APP_SIGNING_TERMS_ACCEPTED: SETUP_BLOCKED_EXTERNAL,
            PACKAGE_BOUND: SETUP_BLOCKED_EXTERNAL,
            BF_PRINCIPAL_GRANTED: SETUP_BLOCKED_EXTERNAL,
            VIEW_APP_INFORMATION_GRANTED: SETUP_BLOCKED_EXTERNAL,
            TEST_RELEASE_PERMISSION_GRANTED: SETUP_BLOCKED_EXTERNAL,
            PUBLISHER_CREDENTIAL_AVAILABLE: ACTION_REQUIRED,
        }
    )
    assert blocked["play_external_setup_ready"] is False
    assert blocked["prerequisites"][INTERNAL_TESTER_CONFIGURATION] == NOT_APPLICABLE
    ready = evaluate_setup_states(_verified_states())
    assert ready["play_external_setup_ready"] is True
    assert ready["prerequisites"][INTERNAL_TESTER_CONFIGURATION] == NOT_APPLICABLE


def test_workspace_live_proof_audit_is_blocked_external() -> None:
    payload = audit_workspace_play_live_preconditions(
        environ={
            "REAL_GOOGLE_PLAY_INTERNAL_TEST": "",
            "BF_OPS_SECRET_DIR": "",
        }
    )
    assert payload["LIVE_GOOGLE_PLAY_PROOF"] == BLOCKED_EXTERNAL
    assert payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is False
    assert payload["REFERENCE_PUBLISHER_LIVE_PROOF"] is False
    assert payload["PLAY_APP_BOUND"] is False
    assert payload["AAB_BUILT"] == "NOT_RUN"
    assert payload["INTERNAL_TRACK_UPLOAD"] == "NOT_RUN"
    assert payload["ANDROID_PRODUCTION_READY"] == "NOT_IMPLEMENTED"
    assert payload["reference_identity"]["package_name"] == REFERENCE_INTERNAL_PACKAGE
    assert payload["prerequisites"][PLAY_DEVELOPER_ACCOUNT] == SETUP_BLOCKED_EXTERNAL
    assert payload["prerequisites"][PUBLISHER_CREDENTIAL_AVAILABLE] == ACTION_REQUIRED
    assert payload["prerequisites"][INTERNAL_TESTER_CONFIGURATION] == NOT_APPLICABLE
    assert payload["developer_account_auto_created"] is False
    dumped = json.dumps(payload)
    assert "BEGIN PRIVATE" not in dumped
    assert "private_key" not in dumped
    assert "refresh_token" not in dumped


@pytest.mark.skipif(
    os.environ.get("REAL_GOOGLE_PLAY_INTERNAL_TEST") != "1",
    reason="LIVE_GOOGLE_PLAY_PROOF = BLOCKED_EXTERNAL",
)
def test_real_google_play_internal_live() -> None:
    from app_factory.application.package_identity import REFERENCE_INTERNAL_PACKAGE

    connection = _connection(
        owner_type=OWNER_REFERENCE,
        customer_app_id="bforge-reference-internal",
        tenant_id="tenant-bforge-reference",
        package_name=REFERENCE_INTERNAL_PACKAGE,
    )
    result = GooglePlayPublisherProvider(FailClosedSecretResolver(), connection).verify_connection(
        connection, expected_package=REFERENCE_INTERNAL_PACKAGE
    )
    assert result.get("status") == STATUS_READY
    assert result.get("live_proof") != "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL"
    assert result.get("CUSTOMER_OWNED_PUBLISHING_PROVEN") is not True
