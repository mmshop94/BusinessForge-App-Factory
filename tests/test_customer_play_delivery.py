"""Play connection + internal test-track delivery proofs. No production writes. No secrets in output."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app_factory.application.customer_release.aab import (
    inspect_customer_aab,
    write_placeholder_aab,
)
from app_factory.application.customer_release.gates import compose_android_delivery
from app_factory.application.customer_release.pipeline import prepare_customer_release
from app_factory.application.customer_release.play import (
    STATUS_AUTH_FAILED,
    STATUS_CREDENTIAL_MISSING,
    STATUS_PERMISSION_INCOMPLETE,
    STATUS_PLAY_APP_SETUP_REQUIRED,
    STATUS_READY,
    STATUS_REVOKED,
    GooglePlayPublisherConnection,
)
from app_factory.application.customer_release.play.approval import ApprovalError, ApprovalRegistry
from app_factory.application.customer_release.play.delivery import deliver_internal_test_track
from app_factory.application.customer_release.play.provider import (
    PRODUCTION_SUBMISSION_BLOCKED,
    FakePlayPublisherProvider,
    GooglePlayPublisherProvider,
)
from app_factory.application.customer_release.profile import profile_from_dict
from app_factory.application.customer_release.secrets import ScopedSecretResolver
from app_factory.application.customer_release.signing import (
    SHARED_OWNER_KEYSTORE_FORBIDDEN,
    FailClosedSecretResolver,
    assert_customer_production_signing,
)
from app_factory.application.customer_release.upload_key import UploadKeyRecord, assert_not_owner_upload_key
from app_factory.domain.errors import (
    ProductionSubmissionBlocked,
    SigningGuardError,
    TenantIsolationError,
)
from app_factory.infrastructure.flutter_runner import CommandResult
from tests.test_customer_release_intake import (
    SECRET_VALUE,
    _intake,
    _resolver,
    _write_assets,
)
from tests.test_official_sales_generate_path import test_official_sales_generate_path_is_35


def _connection(**overrides: object) -> GooglePlayPublisherConnection:
    payload = {
        "customer_app_id": "dorfladen-hutthurm",
        "tenant_id": "tenant-hutthurm",
        "package_name": "de.hutthurm.dorfladen",
        "developer_account_reference": "ops://play/dev-account",
        "principal_reference": "ops://play/principal",
        "credential_secret_reference": "ops://play/publisher-credential",
        "scope": "APP_SCOPED",
        "permissions": ("VIEW_APP_INFORMATION", "MANAGE_TEST_RELEASES"),
    }
    payload.update(overrides)
    return GooglePlayPublisherConnection(**payload)  # type: ignore[arg-type]


def test_existing_generate_path_still_35() -> None:
    test_official_sales_generate_path_is_35()


def test_no_credentials_blocks() -> None:
    provider = FakePlayPublisherProvider()
    provider.credentials_present = False
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_CREDENTIAL_MISSING


def test_invalid_credentials_auth_failed() -> None:
    provider = FakePlayPublisherProvider()
    provider.auth_ok = False
    provider.register_app("de.hutthurm.dorfladen")
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_AUTH_FAILED


def test_package_inaccessible_setup_required() -> None:
    provider = FakePlayPublisherProvider()
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_PLAY_APP_SETUP_REQUIRED


def test_package_mismatch_hard_block() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    result = provider.verify_connection(_connection(), expected_package="de.other.app")
    assert result["status"] == "PACKAGE_ID_MISMATCH"


def test_insufficient_permission_blocks() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen", permissions=["VIEW_APP_INFORMATION"])
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_PERMISSION_INCOMPLETE


def test_valid_app_scoped_test_permission_pass() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_READY
    assert result["permissions"]["production_permission_required"] is False
    assert result["permissions"]["production_permission_used"] is False


def test_excess_production_permission_recorded_not_used() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app(
        "de.hutthurm.dorfladen",
        permissions=[
            "VIEW_APP_INFORMATION",
            "MANAGE_TEST_RELEASES",
            "PRODUCTION_RELEASE",
        ],
    )
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_READY
    assert "PRODUCTION_RELEASE" in result["excess_permissions_recorded_not_used"]
    assert result["permissions"]["production_permission_used"] is False


def test_revoked_credentials() -> None:
    provider = FakePlayPublisherProvider()
    provider.revoked = True
    result = provider.verify_connection(_connection(), expected_package="de.hutthurm.dorfladen")
    assert result["status"] == STATUS_REVOKED


def test_scoped_secret_cross_tenant_hard_block() -> None:
    vault = ScopedSecretResolver()
    vault.put("tenant-a", "app-a", "ops://android/upload-key", "secret-a")
    vault.put("tenant-b", "app-b", "ops://android/upload-key", "secret-b")
    assert vault.has("ops://android/upload-key", tenant_id="tenant-a", customer_app_id="app-a")
    assert not vault.has("ops://android/upload-key", tenant_id="tenant-a", customer_app_id="app-b")
    with pytest.raises(TenantIsolationError):
        vault.resolve_value("ops://android/upload-key", tenant_id="tenant-a", customer_app_id="app-b")


def test_owner_keystore_still_blocked() -> None:
    with pytest.raises(SigningGuardError) as exc:
        assert_not_owner_upload_key("env://BF_ANDROID_KEYSTORE_PATH")
    assert SHARED_OWNER_KEYSTORE_FORBIDDEN in str(exc.value)


def test_fail_closed_secret_resolver() -> None:
    resolver = FailClosedSecretResolver()
    assert resolver.has("ops://anything", tenant_id="t", customer_app_id="a") is False


def test_ephemeral_upload_key_fingerprint(tmp_path: Path) -> None:
    from app_factory.application.customer_release.upload_key import create_ephemeral_upload_keystore

    path = tmp_path / "customer-upload.p12"
    digest = create_ephemeral_upload_keystore(path, alias="upload", store_unlock="test-unlock-aa11")
    assert len(digest) >= 16
    assert "BEGIN" not in digest
    record = UploadKeyRecord(
        customer_app_id="dorfladen-hutthurm",
        upload_key_reference="ops://android/upload-key",
        certificate_sha256=digest,
        status="CREATED",
        play_app_signing_status="ENROLLED",
    )
    dumped = json.dumps(record.to_public_dict())
    assert "test-unlock-aa11" not in dumped
    assert path.is_file()
    record = UploadKeyRecord(
        customer_app_id="dorfladen-hutthurm",
        upload_key_reference="ops://android/upload-key",
        certificate_sha256="abc123def456",
        status="IMPORTED",
        play_app_signing_status="ENROLLED",
    )
    dumped = json.dumps(record.to_public_dict())
    assert "private" not in dumped.lower()
    assert "BEGIN" not in dumped
    assert record.to_public_dict()["role"] == "UPLOAD_KEY"
    assert record.to_public_dict()["app_signing_key"] == "PLAY_APP_SIGNING"


def test_inspect_aab_rejects_demo_and_debug(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    profile = profile_from_dict(_intake(tmp_path))
    aab = tmp_path / "app.aab"
    write_placeholder_aab(aab, package_name=profile.package_name, version_code=1)
    config = {
        "android_application_id": profile.package_name,
        "public_app_id": profile.public_app_id,
        "display_name": profile.display_name,
        "release_snapshot_id": "snap_1",
    }
    inspect = inspect_customer_aab(
        aab,
        profile=profile,
        snapshot_id="snap_1",
        factory_config=config,
        upload_cert_sha256="deadbeef",
    )
    assert inspect["signing"] == "CUSTOMER_UPLOAD_KEY"
    assert inspect["debug_signing"] is False
    with pytest.raises(SigningGuardError):
        inspect_customer_aab(
            aab,
            profile=profile,
            snapshot_id="snap_1",
            factory_config=config,
            upload_cert_sha256="deadbeef",
            debug_signed=True,
        )


def test_approval_bound_to_snapshot(tmp_path: Path) -> None:
    registry = ApprovalRegistry()
    registry.approve(
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        package_name="de.hutthurm.dorfladen",
        release_id="rel-1",
        snapshot_id="snap-a",
    )
    with pytest.raises(ApprovalError):
        registry.require_approved(
            tenant_id="tenant-hutthurm",
            customer_app_id="dorfladen-hutthurm",
            package_name="de.hutthurm.dorfladen",
            release_id="rel-1",
            snapshot_id="snap-b",
        )
    with pytest.raises(ApprovalError):
        registry.require_approved(
            tenant_id="tenant-hutthurm",
            customer_app_id="dorfladen-hutthurm",
            package_name="de.hutthurm.dorfladen",
            release_id="rel-2",
            snapshot_id="snap-a",
        )


def test_cross_tenant_publisher_and_approval_blocked() -> None:
    connection = _connection()
    with pytest.raises(TenantIsolationError):
        connection.assert_bound(
            tenant_id="tenant-b",
            customer_app_id="app-b",
            package_name="de.hutthurm.dorfladen",
        )
    registry = ApprovalRegistry()
    registry.approve(
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        package_name="de.hutthurm.dorfladen",
        release_id="rel-1",
        snapshot_id="snap-a",
    )
    with pytest.raises(TenantIsolationError):
        registry.require_approved(
            tenant_id="tenant-b",
            customer_app_id="dorfladen-hutthurm",
            package_name="de.hutthurm.dorfladen",
            release_id="rel-1",
            snapshot_id="snap-a",
        )


def test_internal_track_delivery_mock_pass(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    prepared = prepare_customer_release(
        _intake(tmp_path),
        tmp_path / "out",
        resolver=_resolver(),
        apply_workspace=False,
        skip_build=True,
    )
    aab = tmp_path / "app.aab"
    sha = write_placeholder_aab(aab, package_name="de.hutthurm.dorfladen", version_code=1)
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    approvals = ApprovalRegistry()
    approvals.approve(
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        package_name="de.hutthurm.dorfladen",
        release_id=prepared["release_id"],
        snapshot_id=prepared["release_snapshot_id"],
    )
    result = deliver_internal_test_track(
        provider=provider,
        connection=_connection(),
        expected_package="de.hutthurm.dorfladen",
        version_code=1,
        aab_sha256=sha,
        snapshot_id=prepared["release_snapshot_id"],
        release_id=prepared["release_id"],
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        approvals=approvals,
        track="internal",
    )
    dumped = json.dumps(result)
    assert SECRET_VALUE not in dumped
    assert "BEGIN" not in dumped
    assert result["google_play"]["target_track"] == "internal"
    assert result["google_play"]["upload_status"] == "UPLOADED"
    assert result["google_play"]["commit_status"] == "COMPLETED"
    assert result["google_play"]["release_status"] == "COMPLETED"
    assert result["android_production_ready"] == "NOT_IMPLEMENTED"
    delivery = compose_android_delivery(
        intake_readiness=prepared["readiness"],
        play_verification={"status": "READY", "play_app": "READY", "permission_status": "READY"},
        aab_ready=True,
        upload_approved=True,
        test_released=True,
    )
    assert delivery["ANDROID_TEST_RELEASED"] is True
    assert delivery["ANDROID_PRODUCTION_READY"] == "NOT_IMPLEMENTED"
    assert delivery["PLAY_TEST_RELEASE_READY"] == "READY"


def test_production_track_hard_block_no_write() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    approvals = ApprovalRegistry()
    approvals.approve(
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        package_name="de.hutthurm.dorfladen",
        release_id="rel-1",
        snapshot_id="snap-a",
    )
    result = deliver_internal_test_track(
        provider=provider,
        connection=_connection(),
        expected_package="de.hutthurm.dorfladen",
        version_code=1,
        aab_sha256="abc",
        snapshot_id="snap-a",
        release_id="rel-1",
        tenant_id="tenant-hutthurm",
        customer_app_id="dorfladen-hutthurm",
        approvals=approvals,
        track="production",
    )
    assert result["status"] == PRODUCTION_SUBMISSION_BLOCKED
    assert result["api_write_executed"] is False
    assert provider.writes == []
    with pytest.raises(ProductionSubmissionBlocked):
        provider.configure_track("de.hutthurm.dorfladen", "edit-1", track="production", version_code=1)


def test_wrong_version_duplicate_timeout_validate_commit_aab_rejected() -> None:
    provider = FakePlayPublisherProvider()
    provider.register_app("de.hutthurm.dorfladen")
    edit = provider.create_edit("de.hutthurm.dorfladen")
    provider.upload_bundle("de.hutthurm.dorfladen", edit, aab_sha256="sha", version_code=1)
    with pytest.raises(Exception):
        provider.configure_track("de.hutthurm.dorfladen", edit, track="internal", version_code=99)

    provider.validate_fail = True
    provider.configure_track("de.hutthurm.dorfladen", edit, track="internal", version_code=1)
    with pytest.raises(Exception):
        provider.validate_edit("de.hutthurm.dorfladen", edit)

    provider.validate_fail = False
    provider.commit_fail = True
    provider.validate_edit("de.hutthurm.dorfladen", edit)
    with pytest.raises(Exception):
        provider.commit_edit("de.hutthurm.dorfladen", edit)

    provider.commit_fail = False
    provider.reject_aab = True
    edit2 = provider.create_edit("de.hutthurm.dorfladen")
    with pytest.raises(Exception):
        provider.upload_bundle("de.hutthurm.dorfladen", edit2, aab_sha256="sha", version_code=2)

    provider.reject_aab = False
    provider.timeout = True
    with pytest.raises(Exception):
        provider.upload_bundle("de.hutthurm.dorfladen", edit2, aab_sha256="sha", version_code=2)


def test_live_google_provider_is_fail_closed_without_account() -> None:
    connection = _connection()
    result = GooglePlayPublisherProvider(FailClosedSecretResolver(), connection).verify_connection(
        connection, expected_package="de.hutthurm.dorfladen"
    )
    assert result["status"] in {STATUS_CREDENTIAL_MISSING, "NOT_CONFIGURED"}
    assert result.get("live_proof") in {None, "LIVE_PLAY_PROOF_BLOCKED_EXTERNAL"} or result[
        "status"
    ] == STATUS_CREDENTIAL_MISSING


def test_mocked_flutter_aab_build_pipeline(tmp_path: Path) -> None:
    _write_assets(tmp_path)
    app = tmp_path / "customer-app"
    app.mkdir()
    (app / "pubspec.yaml").write_text("name: businessforge_mobile\nversion: 0.5.9+1\n", encoding="utf-8")
    gradle = app / "android" / "app"
    gradle.mkdir(parents=True)
    (gradle / "build.gradle.kts").write_text(
        'applicationId = "com.businessforge.businessforge_mobile"\n'
        "    buildTypes {\n"
        '        release { signingConfig = signingConfigs.getByName("debug") }\n'
        "    }\n",
        encoding="utf-8",
    )
    manifest_dir = gradle / "src" / "main"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "AndroidManifest.xml").write_text(
        '<manifest><application android:label="placeholder"></application></manifest>',
        encoding="utf-8",
    )

    def run(args, cwd, dart_defines=None, check=True):
        del dart_defines, check
        if "appbundle" in args:
            out = Path(cwd) / "build" / "app" / "outputs" / "bundle" / "release"
            out.mkdir(parents=True, exist_ok=True)
            write_placeholder_aab(
                out / "app-release.aab",
                package_name="de.hutthurm.dorfladen",
                version_code=1,
            )
        return CommandResult(command=list(args), returncode=0, stdout="ok", stderr="")

    runner = MagicMock()
    runner.run.side_effect = run
    result = prepare_customer_release(
        _intake(tmp_path),
        tmp_path / "out",
        customer_app_path=app,
        resolver=_resolver(),
        apply_workspace=True,
        skip_build=False,
        flutter_runner=runner,
        signing_environ={
            "BF_CUSTOMER_ANDROID_KEYSTORE_PATH": str(tmp_path / "upload.p12"),
            "BF_CUSTOMER_ANDROID_KEY_ALIAS": "upload",
        },
        upload_cert_sha256="abc123",
    )
    dumped = json.dumps(result)
    assert SECRET_VALUE not in dumped
    assert result["build"]["executed"] is True
    assert result["build"]["signing"] == "CUSTOMER_UPLOAD_KEY"
    assert result["build"]["package_name"] == "de.hutthurm.dorfladen"
    assert result["build"]["version_code"] == 1
    gradle_text = (tmp_path / "out" / "workspace" / "android" / "app" / "build.gradle.kts").read_text(
        encoding="utf-8"
    )
    assert "BF_CUSTOMER_ANDROID_KEYSTORE_PATH" in gradle_text
    assert "BF_ANDROID_KEYSTORE_PATH" not in gradle_text
    assert 'signingConfigs.getByName("release")' in gradle_text
    assert result["android_production_ready"] == "NOT_IMPLEMENTED"
    assert result["google_play"]["upload_status"] == "NOT_UPLOADED"
