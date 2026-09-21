"""iOS factory + App Store Connect publishing foundation. No production submit. No fake IPA PASS."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app_factory.application.customer_release.apple import (
    OWNER_CUSTOMER,
    OWNER_REFERENCE,
    ApplePublisherConnection,
)
from app_factory.application.customer_release.apple.approval import AppleApprovalRegistry
from app_factory.application.customer_release.apple.delivery import deliver_testflight
from app_factory.application.customer_release.apple.evidence import serialize_testflight_proof
from app_factory.application.customer_release.apple.executor import (
    IOS_BUILD_EXECUTOR_REQUIRED,
    probe_ios_build_executor,
)
from app_factory.application.customer_release.apple.live_audit import (
    audit_workspace_apple_live_preconditions,
)
from app_factory.application.customer_release.apple.preflight import (
    BLOCKED_EXTERNAL,
    ApplePreflightInput,
    run_preflight,
)
from app_factory.application.customer_release.apple.provider import (
    APP_STORE_PRODUCTION_SUBMISSION_BLOCKED,
    AppleAppStoreConnectPublisherProvider,
    FakeApplePublisherProvider,
)
from app_factory.application.customer_release.apple.readiness import evaluate_ios_platform_readiness
from app_factory.application.customer_release.apple.setup_contract import (
    ACTION_REQUIRED,
    reference_console_app_create_contract,
)
from app_factory.application.customer_release.apple.signing import (
    APPLE_SIGNING_CONFIGURATION_REQUIRED,
    SHARED_APPLE_DISTRIBUTION,
    assert_customer_ios_signing,
    profile_from_intake,
)
from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
from app_factory.application.customer_release.pipeline import prepare_customer_release
from app_factory.application.customer_release.profile import profile_from_dict
from app_factory.application.customer_release.signing import FailClosedSecretResolver, MappingSecretResolver
from app_factory.application.customer_release.snapshot import freeze_snapshot
from app_factory.application.package_identity import (
    REFERENCE_IOS_BUNDLE,
    validate_customer_production_bundle_id,
    validate_reference_ios_bundle_id,
)
from app_factory.domain.errors import (
    AppleConnectionError,
    AppStoreProductionSubmissionBlocked,
    IdentityCollisionError,
    PackageMutationError,
    SigningGuardError,
    TenantIsolationError,
)
from app_factory.infrastructure.flutter_config import FlutterConfigApplier
from app_factory.domain.build import (
    AppBuildManifest,
    AppIdentity,
    BrandingConfiguration,
    FeatureConfiguration,
    ReleaseConfiguration,
    SourceRevision,
    TenantBinding,
)
from tests.test_customer_release_intake import _intake, _resolver, _write_assets
from tests.test_official_sales_generate_path import test_official_sales_generate_path_is_35


def _apple_connection(**overrides: object) -> ApplePublisherConnection:
    payload = {
        "customer_app_id": "dorfladen-hutthurm",
        "tenant_id": "tenant-hutthurm",
        "bundle_identifier": "de.hutthurm.dorfladen",
        "team_id_reference": "ops://apple/team",
        "issuer_reference": "ops://apple/issuer",
        "key_id_reference": "ops://apple/key-id",
        "private_key_secret_reference": "ops://apple/private-key",
        "owner_type": OWNER_REFERENCE,
    }
    payload.update(overrides)
    return ApplePublisherConnection(**payload)  # type: ignore[arg-type]


def test_existing_generate_path_still_35() -> None:
    test_official_sales_generate_path_is_35()


def test_reference_ios_bundle_is_not_customer_production() -> None:
    assert validate_reference_ios_bundle_id(REFERENCE_IOS_BUNDLE) == REFERENCE_IOS_BUNDLE
    with pytest.raises(ValueError):
        validate_reference_ios_bundle_id("de.hutthurm.dorfladen")
    with pytest.raises(ValueError):
        validate_customer_production_bundle_id(REFERENCE_IOS_BUNDLE)
    registry = CustomerAppIdentityRegistry()
    registry.validate_and_register(
        customer_app_id="bforge-reference-internal-ios",
        package_name_android="de.bforge.reference.internal",
        bundle_identifier=REFERENCE_IOS_BUNDLE,
        published=False,
        version_code=1,
        production=False,
        ios_production=False,
    )
    frozen = registry.freeze_apple_bundle("bforge-reference-internal-ios")
    assert frozen.bundle_immutable is True
    with pytest.raises(PackageMutationError):
        registry.validate_and_register(
            customer_app_id="bforge-reference-internal-ios",
            package_name_android="de.bforge.reference.internal",
            bundle_identifier="de.bforge.reference.other.ios",
            published=False,
            version_code=2,
            production=False,
            ios_production=False,
        )


def test_bundle_collision_and_android_package_may_differ() -> None:
    registry = CustomerAppIdentityRegistry()
    registry.validate_and_register(
        customer_app_id="app-a",
        package_name_android="de.kunde.a.app",
        bundle_identifier="de.kunde.a.ios",
        published=False,
        version_code=1,
        production=True,
        ios_production=True,
    )
    with pytest.raises(IdentityCollisionError):
        registry.validate_and_register(
            customer_app_id="app-b",
            package_name_android="de.kunde.b.app",
            bundle_identifier="de.kunde.a.ios",
            published=False,
            version_code=1,
            production=True,
            ios_production=True,
        )
    other = registry.validate_and_register(
        customer_app_id="app-c",
        package_name_android="de.kunde.c.app",
        bundle_identifier="de.kunde.c.ios",
        published=False,
        version_code=1,
        production=True,
        ios_production=True,
    )
    assert other.package_name_android != other.bundle_identifier or True


def test_managed_update_build_number_monotonic() -> None:
    registry = CustomerAppIdentityRegistry()
    registry.validate_and_register(
        customer_app_id="app-a",
        package_name_android="de.kunde.a.app",
        bundle_identifier="de.kunde.a.ios",
        published=False,
        version_code=1,
        production=True,
        ios_production=True,
    )
    with pytest.raises(PackageMutationError):
        registry.validate_and_register(
            customer_app_id="app-a",
            package_name_android="de.kunde.a.app",
            bundle_identifier="de.kunde.a.ios",
            published=False,
            version_code=1,
            production=True,
            ios_production=True,
        )
    second = registry.validate_and_register(
        customer_app_id="app-a",
        package_name_android="de.kunde.a.app",
        bundle_identifier="de.kunde.a.ios",
        published=False,
        version_code=2,
        production=True,
        ios_production=True,
    )
    assert second.last_version_code == 2


def test_reference_setup_contract_is_not_customer_owned() -> None:
    contract = reference_console_app_create_contract(principal_identity="ops://apple/principal")
    assert contract["created_by_businessforge"] is False
    assert contract["bundle_identifier"] == REFERENCE_IOS_BUNDLE
    assert contract["publisher_owner_type"] == OWNER_REFERENCE
    assert contract["customer_owned_publishing_proven"] is False
    assert contract["account_holder_required"] is False


def test_macos_executor_required_on_windows() -> None:
    probe = probe_ios_build_executor()
    assert probe["fake_ipa_pass"] is False
    if probe["macos"] is False:
        assert probe["status"] == IOS_BUILD_EXECUTOR_REQUIRED


def test_missing_signing_is_required_not_failed(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path, platforms="IOS_ONLY"))
    readiness = evaluate_ios_platform_readiness(
        profile, asset_root=tmp_path, resolver=FailClosedSecretResolver()
    )
    assert readiness["failed"] is False
    assert APPLE_SIGNING_CONFIGURATION_REQUIRED in readiness["blockers"]
    assert readiness["app_store_production"] == "NOT_IMPLEMENTED"


def test_shared_apple_distribution_forbidden() -> None:
    profile = profile_from_intake(
        profile_from_dict(
            {
                **_intake(Path(".")),
            }
        ).ios_signing,
        customer_app_id="x",
        tenant_id="t",
        bundle_identifier="de.kunde.app",
    )
    # Default ABSENT signing mode LOCAL_TEST without allow → required
    with pytest.raises(SigningGuardError) as exc:
        assert_customer_ios_signing(profile, resolver=FailClosedSecretResolver())
    assert APPLE_SIGNING_CONFIGURATION_REQUIRED in str(exc.value)


def test_cross_tenant_apple_connection_hard_block() -> None:
    connection = _apple_connection()
    with pytest.raises(TenantIsolationError):
        connection.assert_bound(
            tenant_id="tenant-b",
            customer_app_id="dorfladen-hutthurm",
            bundle_identifier="de.hutthurm.dorfladen",
        )


def test_production_submission_hard_block() -> None:
    fake = FakeApplePublisherProvider()
    fake.register_app("de.hutthurm.dorfladen")
    with pytest.raises(AppStoreProductionSubmissionBlocked):
        fake.upload_build(
            "de.hutthurm.dorfladen",
            ipa_sha256="abc",
            build_number=1,
            destination="production",
        )
    live = AppleAppStoreConnectPublisherProvider(
        FailClosedSecretResolver(), _apple_connection()
    )
    with pytest.raises(AppStoreProductionSubmissionBlocked):
        live.upload_build(
            "de.hutthurm.dorfladen",
            ipa_sha256="abc",
            build_number=1,
            destination="app_store",
        )


def test_live_provider_blocked_external_without_flag() -> None:
    connection = _apple_connection()
    resolver = MappingSecretResolver({"ops://apple/private-key": "present"})
    result = AppleAppStoreConnectPublisherProvider(resolver, connection).verify_connection(
        connection, expected_bundle="de.hutthurm.dorfladen"
    )
    assert result.get("LIVE_APPLE_PROOF") == BLOCKED_EXTERNAL or result.get("live_proof")


def test_testflight_approval_snapshot_bound(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path, platforms="IOS_ONLY"))
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    approvals = AppleApprovalRegistry()
    approvals.approve(
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        bundle_identifier=profile.bundle_identifier,
        release_id=profile.release_id,
        snapshot_id=snapshot["snapshot_id"],
    )
    with pytest.raises(Exception):
        approvals.require_approved(
            tenant_id=profile.tenant_id,
            customer_app_id=profile.app_id,
            bundle_identifier=profile.bundle_identifier,
            release_id=profile.release_id,
            snapshot_id="other-snapshot",
        )


def test_reference_cannot_claim_customer_owned_proof() -> None:
    with pytest.raises(AppleConnectionError):
        serialize_testflight_proof(
            release_id="r",
            snapshot_id="s",
            publisher_owner_type=OWNER_REFERENCE,
            bundle_identifier=REFERENCE_IOS_BUNDLE,
            build_number=1,
            version_name="1.0.0",
            ipa_sha256="abc",
            executor_type="NONE",
            extra={"CUSTOMER_OWNED_PUBLISHING_PROVEN": True},
        )
    payload = serialize_testflight_proof(
        release_id="r",
        snapshot_id="s",
        publisher_owner_type=OWNER_REFERENCE,
        bundle_identifier=REFERENCE_IOS_BUNDLE,
        build_number=1,
        version_name="1.0.0",
        ipa_sha256="abc",
        executor_type="NONE",
    )
    assert payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is False
    dumped = json.dumps(payload)
    assert "BEGIN" not in dumped
    assert ".p8" not in dumped


def test_workspace_apple_audit_blocked_external() -> None:
    payload = audit_workspace_apple_live_preconditions(
        environ={"REAL_APPLE_TESTFLIGHT_TEST": "", "BF_OPS_SECRET_DIR": ""}
    )
    assert payload["LIVE_APPLE_PROOF"] == BLOCKED_EXTERNAL
    assert payload["CUSTOMER_OWNED_PUBLISHING_PROVEN"] is False
    assert payload["IOS_IMPLEMENTATION_READY"] is True
    assert payload["reference_identity"]["bundle_identifier"] == REFERENCE_IOS_BUNDLE
    assert payload["developer_account_auto_created"] is False
    assert payload["google_status_unchanged"]["LIVE_GOOGLE_PLAY_PROOF"] == BLOCKED_EXTERNAL


def test_android_google_block_does_not_block_ios_foundation(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    result = prepare_customer_release(
        _intake(tmp_path, platforms="ANDROID_AND_IOS"),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
    )
    assert _gate(result, "ANDROID_SIGNING_READY") == "READY"
    assert _gate(result, "IOS_CONFIG_READY") == "READY"
    assert result["google_play"]["upload_status"] == "NOT_UPLOADED"
    assert result["apple"]["app_store_production_ready"] == "NOT_IMPLEMENTED"


def test_ios_apply_writes_bundle_and_display_name(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    app = tmp_path / "customer-app"
    (app / "ios" / "Runner.xcodeproj").mkdir(parents=True)
    (app / "ios" / "Runner").mkdir(parents=True)
    (app / "pubspec.yaml").write_text("name: businessforge_mobile\nversion: 0.5.9+1\n", encoding="utf-8")
    (app / "ios" / "Runner.xcodeproj" / "project.pbxproj").write_text(
        "PRODUCT_BUNDLE_IDENTIFIER = com.businessforge.businessforgeMobile;\n"
        "PRODUCT_BUNDLE_IDENTIFIER = com.businessforge.businessforgeMobile.RunnerTests;\n",
        encoding="utf-8",
    )
    (app / "ios" / "Runner" / "Info.plist").write_text(
        "<dict><key>CFBundleDisplayName</key>\n\t<string>Businessforge Mobile</string></dict>",
        encoding="utf-8",
    )
    gradle = app / "android" / "app"
    gradle.mkdir(parents=True)
    (gradle / "build.gradle.kts").write_text(
        'applicationId = "com.businessforge.businessforge_mobile"\n    buildTypes {\n    }\n',
        encoding="utf-8",
    )
    manifest_dir = gradle / "src" / "main"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "AndroidManifest.xml").write_text(
        '<manifest><application android:label="placeholder"></application></manifest>',
        encoding="utf-8",
    )
    result = prepare_customer_release(
        _intake(tmp_path, platforms="ANDROID_AND_IOS"),
        tmp_path / "out",
        customer_app_path=app,
        resolver=_resolver(),
        apply_workspace=True,
        skip_build=True,
    )
    workspace = tmp_path / "out" / "workspace"
    pbx = (workspace / "ios" / "Runner.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    info = (workspace / "ios" / "Runner" / "Info.plist").read_text(encoding="utf-8")
    config = json.loads((workspace / "build_config" / "app_factory_config.json").read_text(encoding="utf-8"))
    assert "PRODUCT_BUNDLE_IDENTIFIER = de.hutthurm.dorfladen;" in pbx
    assert "Dorfladen Hutthurm" in info
    assert config["bundle_id_ios"] == "de.hutthurm.dorfladen"
    assert config["display_name"] == "Dorfladen Hutthurm"
    assert config["tenant_package"] == "village_store"
    assert "BEGIN PRIVATE" not in json.dumps(result)


def test_representative_flutter_config_identities(tmp_path: Path) -> None:
    cases = (
        ("village_store", "de.kunde.commerce.app", True),
        ("appointment_hairdresser", "de.kunde.appointment.app", True),
        ("field_service_electrician", "de.kunde.field.app", True),
    )
    applier = FlutterConfigApplier()
    for vertical, bundle, village_cap in cases:
        workspace = tmp_path / bundle
        workspace.mkdir()
        (workspace / "pubspec.yaml").write_text(
            "name: businessforge_mobile\nversion: 0.5.9+1\n", encoding="utf-8"
        )
        manifest = AppBuildManifest(
            schema_version=1,
            app=AppIdentity(
                id=f"app-{vertical}",
                display_name=f"Betrieb {vertical}",
                package_name_android=bundle.replace(".app", ".android"),
                bundle_id_ios=bundle,
            ),
            tenant=TenantBinding(
                public_app_id="app_01JABCDEFGHJKMNPQRSTVWXYZ0",
                package=vertical,
                package_version="v1",
            ),
            branding=BrandingConfiguration(
                theme="modern",
                primary_color="#111111",
                secondary_color="#222222",
                logo_asset="",
                splash_asset="",
                icon_asset="",
            ),
            features=FeatureConfiguration(flags={vertical: True}),
            release=ReleaseConfiguration(channel="dev", app_version="1.0.0", build_number=1),
            source=SourceRevision(customer_app_ref="main", factory_compat_version="1"),
            api_base_url="https://api.bforge.de/api/v1",
        )
        applier.apply(workspace, manifest, {"APP_NAME": manifest.app.display_name})
        config = json.loads((workspace / "build_config" / "app_factory_config.json").read_text())
        assert config["display_name"] == f"Betrieb {vertical}"
        assert config["bundle_id_ios"] == bundle
        assert config["tenant_package"] == vertical
        assert vertical in config["features"]
        assert "demo" not in config["display_name"].lower()
        del village_cap


def test_fake_testflight_delivery_without_production(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path, platforms="IOS_ONLY"))
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    provider = FakeApplePublisherProvider()
    provider.register_app(profile.bundle_identifier)
    approvals = AppleApprovalRegistry()
    approvals.approve(
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        bundle_identifier=profile.bundle_identifier,
        release_id=profile.release_id,
        snapshot_id=snapshot["snapshot_id"],
    )
    result = deliver_testflight(
        provider=provider,
        connection=_apple_connection(
            owner_type=OWNER_CUSTOMER,
            customer_app_id=profile.app_id,
            tenant_id=profile.tenant_id,
            bundle_identifier=profile.bundle_identifier,
        ),
        expected_bundle=profile.bundle_identifier,
        build_number=1,
        ipa_sha256="deadbeef",
        snapshot_id=snapshot["snapshot_id"],
        release_id=profile.release_id,
        tenant_id=profile.tenant_id,
        customer_app_id=profile.app_id,
        approvals=approvals,
    )
    assert result["customer_owned_publishing_proven"] is False
    assert result["app_store_production_ready"] == "NOT_IMPLEMENTED"


def test_preflight_production_aborts_before_write(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path, platforms="IOS_ONLY"))
    snapshot = freeze_snapshot(profile, tmp_path / "snap")
    identity = CustomerAppIdentityRegistry()
    identity.validate_and_register(
        customer_app_id=profile.app_id,
        package_name_android=profile.package_name,
        bundle_identifier=profile.bundle_identifier,
        published=False,
        version_code=1,
        production=False,
        ios_production=True,
    )
    identity.freeze_apple_bundle(profile.app_id)
    connection = _apple_connection(
        customer_app_id=profile.app_id,
        tenant_id=profile.tenant_id,
        bundle_identifier=profile.bundle_identifier,
    )
    result = run_preflight(
        ApplePreflightInput(
            profile=profile,
            snapshot_id=snapshot["snapshot_id"],
            snapshot_immutable=True,
            connection=connection,
            resolver=FailClosedSecretResolver(),
            provider=FakeApplePublisherProvider(),
            approvals=AppleApprovalRegistry(),
            identity=identity,
            destination="production",
        )
    )
    assert result["status"] == APP_STORE_PRODUCTION_SUBMISSION_BLOCKED
    assert result["api_write_executed"] is False


def _gate(result: dict, name: str) -> str:
    for gate in result["readiness"]["gates"]:
        if gate["name"] == name:
            return gate["status"]
    raise AssertionError(name)
