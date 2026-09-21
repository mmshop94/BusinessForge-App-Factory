from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from app_factory import __version__
from app_factory.application.build_orchestrator import BuildOrchestrator
from app_factory.application.build_planner import BuildPlanner
from app_factory.application.export_materializer import materialize_export
from app_factory.application.manifest_validator import ManifestLoader, ManifestValidator
from app_factory.application.signing import signing_status
from app_factory.domain.build import BuildRequest
from app_factory.domain.enums import AndroidArtifactFormat
from app_factory.domain.errors import AppFactoryError
from app_factory.infrastructure.build_report import BuildReportWriter
from app_factory.infrastructure.flutter_runner import FlutterRunner
from app_factory.infrastructure.paths import compat_path, repo_root, schema_path


def _default_customer_app_path(manifest_path: Path, manifest_repo: str | None) -> Path:
    if manifest_repo:
        candidate = (manifest_path.parent / manifest_repo).resolve()
        if candidate.is_dir():
            return candidate
    env_override = Path(
        click.get_current_context().obj.get("customer_app_path", "")
        if click.get_current_context(silent=True)
        and click.get_current_context().obj
        else ""
    )
    if env_override and env_override.is_dir():
        return env_override
    sibling = (repo_root().parent / "BusinessForge FlutterApp").resolve()
    if sibling.is_dir():
        return sibling
    raise click.ClickException(
        "Customer app path not found. Pass --customer-app or set source.customer_app_repo."
    )


@click.group()
@click.version_option(__version__, prog_name="app-factory")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """BusinessForge App Factory — white-label Android builds."""
    ctx.ensure_object(dict)
    ctx.obj["customer_app_path"] = ""


@cli.command("validate")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate_cmd(manifest: Path) -> None:
    """Validate a tenant app manifest."""
    validator = ManifestValidator(schema_path(), compat_path())
    try:
        domain = validator.validate_file(manifest)
    except AppFactoryError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"OK: {domain.app.display_name} ({domain.app.id})")


@cli.command("plan")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--customer-app",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to BusinessForge Customer App checkout",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=lambda: repo_root() / "output",
    show_default=True,
)
@click.option(
    "--format",
    "artifact_format",
    type=click.Choice(["apk", "aab"], case_sensitive=False),
    default="apk",
    show_default=True,
)
def plan_cmd(
    manifest: Path,
    customer_app: Path | None,
    output_dir: Path,
    artifact_format: str,
) -> None:
    """Render a deterministic build plan."""
    validator = ManifestValidator(schema_path(), compat_path())
    loader = ManifestLoader()
    try:
        raw = loader.load(manifest)
        validator.validate_raw(raw)
        domain = loader.to_domain(raw, manifest)
        validator.validate_assets(manifest.parent, domain)
        validator.validate_compatibility(domain)
        manifest_hash = ManifestValidator.manifest_hash(raw)
    except AppFactoryError as exc:
        raise click.ClickException(str(exc)) from exc

    customer_path = customer_app or _default_customer_app_path(
        manifest, domain.source.customer_app_repo
    )
    plan = BuildPlanner().plan(
        domain,
        manifest_hash,
        customer_path,
        output_dir,
        artifact_format=AndroidArtifactFormat(artifact_format.lower()),
    )
    click.echo(json.dumps(plan.to_dict(), indent=2, sort_keys=True))


@cli.command("build-android")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--customer-app",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to BusinessForge Customer App checkout",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=lambda: repo_root() / "output",
    show_default=True,
)
@click.option(
    "--format",
    "artifact_format",
    type=click.Choice(["apk", "aab"], case_sensitive=False),
    default="apk",
    show_default=True,
)
@click.option("--skip-tests", is_flag=True, help="Skip flutter test")
@click.option("--skip-analyze", is_flag=True, help="Skip flutter analyze")
@click.option("--dry-run", is_flag=True, help="Plan only — do not execute Flutter")
@click.option(
    "--debug",
    "debug_build",
    is_flag=True,
    help="Build a debug APK (E2E test apps). Release remains the default.",
)
@click.option(
    "--e2e-test",
    is_flag=True,
    help="Fail-closed E2E test build (E2E_TEST_BUILD=true, demo API only).",
)
@click.option(
    "--e2e-environment",
    default="demo",
    show_default=True,
    help="Required environment when --e2e-test is set.",
)
@click.option(
    "--e2e-run-id",
    default="",
    help="Optional BF_E2E_RUN_ID baked into an E2E test build.",
)
@click.option(
    "--flutter-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to flutter executable (default: flutter on PATH)",
)
def build_android_cmd(
    manifest: Path,
    customer_app: Path | None,
    output_dir: Path,
    artifact_format: str,
    skip_tests: bool,
    skip_analyze: bool,
    dry_run: bool,
    debug_build: bool,
    e2e_test: bool,
    e2e_environment: str,
    e2e_run_id: str,
    flutter_path: Path | None,
) -> None:
    """Build a tenant Android APK/AAB from manifest + customer app."""
    validator = ManifestValidator(schema_path(), compat_path())
    loader = ManifestLoader()
    try:
        raw = loader.load(manifest)
        domain = validator.validate_file(manifest)
        manifest_hash = ManifestValidator.manifest_hash(raw)
    except AppFactoryError as exc:
        raise click.ClickException(str(exc)) from exc

    customer_path = customer_app or _default_customer_app_path(
        manifest, domain.source.customer_app_repo
    )
    request = BuildRequest(
        manifest=domain,
        manifest_hash=manifest_hash,
        customer_app_path=str(customer_path),
        output_dir=str(output_dir),
        artifact_format=AndroidArtifactFormat(artifact_format.lower()),
        run_tests=not skip_tests,
        run_analyze=not skip_analyze,
        dry_run=dry_run,
        debug_build=debug_build,
        e2e_test=e2e_test,
        e2e_environment=e2e_environment,
        e2e_run_id=e2e_run_id,
    )
    result = BuildOrchestrator(
        flutter_runner=FlutterRunner(str(flutter_path) if flutter_path else "flutter")
    ).build_android(request)
    click.echo(json.dumps({"status": result.status.value, "report": result.report_path}, indent=2))
    if result.status.value != "succeeded" and result.status.value != "planned":
        sys.exit(1)


@cli.command("inspect-build")
@click.argument("build_report", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def inspect_build_cmd(build_report: Path) -> None:
    """Pretty-print a build report JSON file."""
    payload = BuildReportWriter.load(build_report)
    click.echo(json.dumps(payload, indent=2, sort_keys=True))


@cli.command("signing-status")
def signing_status_cmd() -> None:
    """Show whether Android signing env is configured (no secrets)."""
    click.echo(json.dumps(signing_status().to_public_dict(), indent=2, sort_keys=True))


@cli.command("prepare-customer-release")
@click.argument("intake", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--customer-app",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option("--skip-build/--build", default=True, show_default=True)
def prepare_customer_release_cmd(
    intake: Path,
    output_dir: Path,
    customer_app: Path | None,
    skip_build: bool,
) -> None:
    """Validate, snapshot, and prepare a customer Android release (no Play upload)."""
    from app_factory.application.customer_release.pipeline import prepare_customer_release
    from app_factory.application.manifest_validator import ManifestLoader

    payload = ManifestLoader().load(intake)
    try:
        result = prepare_customer_release(
            payload,
            output_dir,
            customer_app_path=customer_app,
            skip_build=skip_build,
            apply_workspace=customer_app is not None,
        )
    except AppFactoryError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps({"store_release": result.get("store_release"), "path": str(output_dir / "release-manifest.json")}, indent=2))
    if result.get("store_release") != "STORE_RELEASE_READY":
        raise SystemExit(1)


@cli.command("verify-play-connection")
@click.option("--package-name", required=True)
@click.option("--tenant-id", required=True)
@click.option("--app-id", required=True)
@click.option("--credential-ref", default="")
def verify_play_connection_cmd(
    package_name: str,
    tenant_id: str,
    app_id: str,
    credential_ref: str,
) -> None:
    """Verify app-scoped Play access. Never prints credential values."""
    from app_factory.application.customer_release.play import GooglePlayPublisherConnection
    from app_factory.application.customer_release.play.provider import GooglePlayPublisherProvider
    from app_factory.application.customer_release.signing import FailClosedSecretResolver

    connection = GooglePlayPublisherConnection(
        customer_app_id=app_id,
        tenant_id=tenant_id,
        package_name=package_name,
        developer_account_reference="ops://play/developer-account",
        principal_reference="ops://play/principal",
        credential_secret_reference=credential_ref,
    )
    result = GooglePlayPublisherProvider(FailClosedSecretResolver(), connection).verify_connection(
        connection, expected_package=package_name
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") != "READY":
        raise SystemExit(1)


@cli.group("google-play")
def google_play_group() -> None:
    """Google Play onboarding, preflight, and internal-track proof. No production."""


@google_play_group.command("setup-contract")
@click.argument("intake", required=False, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--principal-identity", default="ops://play/principal")
@click.option("--owner-type", default="CUSTOMER_OWNED", show_default=True)
@click.option(
    "--reference",
    "reference_identity",
    is_flag=True,
    help="Emit the BusinessForge reference Play identity contract. Does not create a Play app.",
)
def google_play_setup_contract_cmd(
    intake: Path | None,
    principal_identity: str,
    owner_type: str,
    reference_identity: bool,
) -> None:
    """Emit the one-time Play Console app-create contract. Does not create the Play app."""
    from app_factory.application.customer_release.play.setup_contract import (
        console_app_create_contract,
        reference_console_app_create_contract,
    )
    from app_factory.application.customer_release.profile import profile_from_dict
    from app_factory.application.manifest_validator import ManifestLoader

    if reference_identity:
        click.echo(
            json.dumps(
                reference_console_app_create_contract(principal_identity=principal_identity),
                indent=2,
                sort_keys=True,
            )
        )
        return
    if intake is None:
        raise click.UsageError("INTAKE is required unless --reference is set")
    profile = profile_from_dict(ManifestLoader().load(intake))
    click.echo(
        json.dumps(
            console_app_create_contract(
                profile,
                principal_identity=principal_identity,
                owner_type=owner_type,
            ),
            indent=2,
            sort_keys=True,
        )
    )


@google_play_group.command("onboarding")
@click.option("--states-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
def google_play_onboarding_cmd(states_json: Path) -> None:
    """Print CUSTOMER_PLAY_ONBOARDING status and instruction steps. No secrets."""
    from app_factory.application.customer_release.play.onboarding import (
        evaluate_customer_play_onboarding,
    )

    states = json.loads(states_json.read_text(encoding="utf-8"))
    click.echo(json.dumps(evaluate_customer_play_onboarding(states), indent=2, ensure_ascii=False))


@google_play_group.command("preflight")
@click.argument("intake", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--snapshot-id", default="")
@click.option("--tenant-id", required=True)
@click.option("--app-id", required=True)
@click.option("--package-name", required=True)
@click.option("--credential-ref", default="")
@click.option("--upload-key-ref", default="")
@click.option("--owner-type", default="CUSTOMER_OWNED", show_default=True)
@click.option("--track", default="internal", show_default=True)
def google_play_preflight_cmd(
    intake: Path,
    snapshot_id: str,
    tenant_id: str,
    app_id: str,
    package_name: str,
    credential_ref: str,
    upload_key_ref: str,
    owner_type: str,
    track: str,
) -> None:
    """Check LIVE_INTERNAL_UPLOAD_READY. Never prints credential values. No production writes."""
    from app_factory.application.customer_release.identity import CustomerAppIdentityRegistry
    from app_factory.application.customer_release.play import GooglePlayPublisherConnection
    from app_factory.application.customer_release.play.approval import ApprovalRegistry
    from app_factory.application.customer_release.play.preflight import PlayPreflightInput, run_preflight
    from app_factory.application.customer_release.play.provider import GooglePlayPublisherProvider
    from app_factory.application.customer_release.profile import profile_from_dict
    from app_factory.application.customer_release.signing import FailClosedSecretResolver
    from app_factory.application.manifest_validator import ManifestLoader

    profile = profile_from_dict(ManifestLoader().load(intake))
    connection = GooglePlayPublisherConnection(
        customer_app_id=app_id,
        tenant_id=tenant_id,
        package_name=package_name,
        developer_account_reference="ops://play/developer-account",
        principal_reference="ops://play/principal",
        credential_secret_reference=credential_ref,
        owner_type=owner_type,
    )
    resolver = FailClosedSecretResolver()
    result = run_preflight(
        PlayPreflightInput(
            profile=profile,
            snapshot_id=snapshot_id or profile.release_snapshot_id,
            snapshot_immutable=bool(snapshot_id or profile.release_snapshot_id),
            connection=connection,
            resolver=resolver,
            provider=GooglePlayPublisherProvider(resolver, connection),
            approvals=ApprovalRegistry(),
            identity=CustomerAppIdentityRegistry(),
            upload_key_reference=upload_key_ref,
            track=track,
        )
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True, default=str))
    if result.get("status") == "PRODUCTION_SUBMISSION_BLOCKED":
        raise SystemExit(2)
    if result.get("live_internal_upload_ready") is not True:
        raise SystemExit(1)


@google_play_group.command("live-proof-audit")
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write public evidence JSON. Never contains credentials.",
)
def google_play_live_proof_audit_cmd(output: Path | None) -> None:
    """Audit this workspace for a real Google Play internal-track proof. No secrets."""
    from app_factory.application.customer_release.play.evidence import write_internal_live_proof
    from app_factory.application.customer_release.play.live_audit import (
        audit_workspace_play_live_preconditions,
    )

    payload = audit_workspace_play_live_preconditions()
    click.echo(json.dumps(payload, indent=2, sort_keys=True))
    if output is not None:
        write_internal_live_proof(output, payload)


@cli.group("ios")
def ios_group() -> None:
    """iOS identity, Apple setup contract, and TestFlight foundation. No App Store production."""


@ios_group.command("setup-contract")
@click.argument("intake", required=False, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--principal-identity", default="ops://apple/principal")
@click.option("--owner-type", default="CUSTOMER_OWNED", show_default=True)
@click.option("--reference", "reference_identity", is_flag=True)
def ios_setup_contract_cmd(
    intake: Path | None,
    principal_identity: str,
    owner_type: str,
    reference_identity: bool,
) -> None:
    """Emit the App Store Connect app-create contract. Does not create the Apple app."""
    from app_factory.application.customer_release.apple.setup_contract import (
        console_app_create_contract,
        reference_console_app_create_contract,
    )
    from app_factory.application.customer_release.profile import profile_from_dict
    from app_factory.application.manifest_validator import ManifestLoader

    if reference_identity:
        click.echo(
            json.dumps(
                reference_console_app_create_contract(principal_identity=principal_identity),
                indent=2,
                sort_keys=True,
            )
        )
        return
    if intake is None:
        raise click.UsageError("INTAKE is required unless --reference is set")
    profile = profile_from_dict(ManifestLoader().load(intake))
    click.echo(
        json.dumps(
            console_app_create_contract(
                profile,
                principal_identity=principal_identity,
                owner_type=owner_type,
            ),
            indent=2,
            sort_keys=True,
        )
    )


@ios_group.command("live-proof-audit")
@click.option("--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
def ios_live_proof_audit_cmd(output: Path | None) -> None:
    """Audit this workspace for a real TestFlight proof. No secrets. No fake IPA."""
    from app_factory.application.customer_release.apple.evidence import write_public_evidence
    from app_factory.application.customer_release.apple.live_audit import (
        audit_workspace_apple_live_preconditions,
    )

    payload = audit_workspace_apple_live_preconditions()
    click.echo(json.dumps(payload, indent=2, sort_keys=True))
    if output is not None:
        write_public_evidence(output, payload)


@cli.command("materialize-export")
@click.argument("export_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
def materialize_export_cmd(export_file: Path, output_dir: Path) -> None:
    """Write a backend factory export to a local manifest directory."""
    payload = json.loads(export_file.read_text(encoding="utf-8"))
    try:
        manifest_path = materialize_export(payload, output_dir)
    except AppFactoryError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps({"manifest": str(manifest_path)}, indent=2))


@cli.command("build-official-sales-demos")
@click.option(
    "--output-root",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Output root. Default: BusinessForge-Demo-Apps/public with --public-api, else .../lan",
)
@click.option(
    "--api-base-url",
    default="http://192.168.178.95:8090/api/v1",
    show_default=True,
    help="Demo API origin. LAN default; --public-api overrides to https://demo-api.bforge.de/api/v1.",
)
@click.option(
    "--public-api",
    is_flag=True,
    help="Use https://demo-api.bforge.de/api/v1 (after Owner DNS/TLS).",
)
@click.option(
    "--customer-app",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Flutter Customer App checkout (default: ../BusinessForge-FlutterApp-main)",
)
@click.option(
    "--env-demo",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to BusinessForge .env.demo for demo owner password",
)
@click.option("--manifest-only", is_flag=True, help="Generate manifests/assets only")
@click.option("--skip-tests", is_flag=True, default=True, show_default=True)
@click.option("--skip-analyze", is_flag=True, default=True, show_default=True)
@click.option("--no-apk", is_flag=True, help="Skip APK builds")
@click.option("--no-aab", is_flag=True, help="Skip AAB builds")
@click.option("--slug", "only_slug", default=None, help="Build a single demo slug")
@click.option(
    "--flutter-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
def build_official_sales_demos_cmd(
    output_root: Path,
    api_base_url: str,
    public_api: bool,
    customer_app: Path | None,
    env_demo: Path | None,
    manifest_only: bool,
    skip_tests: bool,
    skip_analyze: bool,
    no_apk: bool,
    no_aab: bool,
    only_slug: str | None,
    flutter_path: Path | None,
) -> None:
    """Discover Official Sales Demos and batch-build Android APK/AAB packages."""
    from app_factory.application.demo_api_origins import (
        PUBLIC_DEMO_API_BASE_URL,
        assert_public_demo_api_origin,
    )
    from app_factory.application.demo_apps_layout import (
        CHANNEL_LAN,
        CHANNEL_PUBLIC,
        channel_output_root,
        preserve_legacy_lan_builds,
    )
    from app_factory.application.official_sales_demo_batch import build_official_sales_demo_apps
    from app_factory.application.official_sales_demo_discovery import OFFICIAL_SALES_DEMO_SLUGS

    preserve_legacy_lan_builds()
    require_public = False
    if public_api:
        api_base_url = assert_public_demo_api_origin(PUBLIC_DEMO_API_BASE_URL)
        require_public = True

    if output_root is None:
        output_root = channel_output_root(CHANNEL_PUBLIC if public_api else CHANNEL_LAN)

    customer_path = customer_app or (repo_root().parent / "BusinessForge-FlutterApp-main")
    if not customer_path.is_dir():
        raise click.ClickException(f"Customer app not found: {customer_path}")

    slugs = OFFICIAL_SALES_DEMO_SLUGS
    if only_slug:
        if only_slug not in OFFICIAL_SALES_DEMO_SLUGS:
            raise click.ClickException(f"Unknown official sales demo slug: {only_slug}")
        slugs = (only_slug,)

    try:
        result = build_official_sales_demo_apps(
            output_root=output_root,
            api_base_url=api_base_url,
            customer_app=customer_path,
            env_demo_path=env_demo,
            slugs=slugs,
            skip_tests=skip_tests,
            skip_analyze=skip_analyze,
            build_apk=not no_apk,
            build_aab=not no_aab,
            flutter_path=str(flutter_path) if flutter_path else "flutter",
            manifest_only=manifest_only,
            require_public_origins=require_public,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(result.to_dict(), indent=2))
    failed = [entry.slug for entry in result.entries if entry.status == "failed"]
    if failed and not manifest_only:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
