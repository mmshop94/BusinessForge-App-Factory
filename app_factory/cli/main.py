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


if __name__ == "__main__":
    cli()
