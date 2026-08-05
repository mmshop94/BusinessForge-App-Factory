from __future__ import annotations

from pathlib import Path

from app_factory.application.build_planner import BuildPlanner
from app_factory.domain.build import BuildRequest, BuildResult, BuildStatus
from app_factory.domain.enums import AndroidArtifactFormat
from app_factory.domain.errors import BuildExecutionError, WorkspaceError
from app_factory.infrastructure.build_report import (
    BuildReportWriter,
    collect_android_artifact,
    utc_now,
)
from app_factory.infrastructure.flutter_config import FlutterConfigApplier
from app_factory.infrastructure.flutter_runner import FlutterRunner
from app_factory.infrastructure.workspace import WorkspaceManager


class BuildOrchestrator:
    """Slice 1 Android build pipeline with workspace isolation."""

    SOURCE_SNAPSHOT_FILES = [
        "pubspec.yaml",
        "android/app/build.gradle.kts",
        "android/app/src/main/AndroidManifest.xml",
        "lib/config/app_config.dart",
    ]

    def __init__(
        self,
        flutter_runner: FlutterRunner | None = None,
        config_applier: FlutterConfigApplier | None = None,
        planner: BuildPlanner | None = None,
    ) -> None:
        self._flutter = flutter_runner or FlutterRunner()
        self._config = config_applier or FlutterConfigApplier()
        self._planner = planner or BuildPlanner()
        self._reports = BuildReportWriter()

    def build_android(self, request: BuildRequest) -> BuildResult:
        plan = self._planner.plan_request(request)
        result = BuildResult(
            status=BuildStatus.RUNNING,
            request=request,
            started_at=utc_now(),
        )

        workspace_mgr = WorkspaceManager(plan.workspace_path)
        source_path = plan.customer_app_path
        source_snapshot = WorkspaceManager.snapshot_files(
            source_path, self.SOURCE_SNAPSHOT_FILES
        )
        branding_root = (
            Path(request.manifest.manifest_path).parent
            if request.manifest.manifest_path
            else None
        )

        try:
            if request.dry_run:
                result.steps.append(
                    {"name": "dry_run", "status": "skipped", "plan": plan.to_dict()}
                )
                result.mark_finished(BuildStatus.PLANNED)
                self._reports.write(result, Path(request.output_dir))
                return result

            self._record_step(result, "prepare_workspace", "running")
            workspace = workspace_mgr.prepare(source_path)
            self._record_step(result, "prepare_workspace", "succeeded")

            self._record_step(result, "apply_manifest", "running")
            changed = self._config.apply(
                workspace,
                request.manifest,
                plan.dart_defines,
                branding_assets_root=branding_root,
            )
            self._record_step(
                result,
                "apply_manifest",
                "succeeded",
                extra={"changed_files": changed},
            )

            self._record_step(result, "flutter_pub_get", "running")
            self._flutter.run(["pub", "get"], cwd=workspace)
            self._record_step(result, "flutter_pub_get", "succeeded")

            if request.run_analyze:
                self._record_step(result, "flutter_analyze", "running")
                self._flutter.run(["analyze"], cwd=workspace)
                self._record_step(result, "flutter_analyze", "succeeded")

            if request.run_tests:
                self._record_step(result, "flutter_test", "running")
                self._flutter.run(["test"], cwd=workspace, dart_defines=plan.dart_defines)
                self._record_step(result, "flutter_test", "succeeded")

            build_target = (
                "apk"
                if request.artifact_format == AndroidArtifactFormat.APK
                else "appbundle"
            )
            self._record_step(result, f"flutter_build_{build_target}", "running")
            self._flutter.run(
                ["build", build_target, "--release"],
                cwd=workspace,
                dart_defines=plan.dart_defines,
            )
            self._record_step(result, f"flutter_build_{build_target}", "succeeded")

            self._record_step(result, "collect_artifacts", "running")
            artifact = self._collect_artifact(workspace, request, build_target)
            if artifact:
                result.artifacts.append(artifact)
            self._record_step(result, "collect_artifacts", "succeeded")

            result.customer_app_commit = self._flutter.git_commit(source_path)
            flutter_version, dart_version = self._flutter.version_info()
            result.flutter_version = flutter_version
            result.dart_version = dart_version

            WorkspaceManager.assert_source_unmodified(source_path, source_snapshot)
            result.mark_finished(BuildStatus.SUCCEEDED)
        except (BuildExecutionError, WorkspaceError) as exc:
            result.mark_finished(BuildStatus.FAILED, str(exc))
            self._record_step(result, "failed", "failed", extra={"error": str(exc)})
        finally:
            self._record_step(result, "cleanup_workspace", "running")
            workspace_mgr.cleanup()
            self._record_step(result, "cleanup_workspace", "succeeded")
            self._reports.write(result, Path(request.output_dir))

        return result

    @staticmethod
    def _collect_artifact(workspace: Path, request: BuildRequest, build_target: str):
        if build_target == "apk":
            return collect_android_artifact(
                workspace,
                Path(request.output_dir),
                request.manifest.app.id,
                artifact_kind="apk",
                glob_pattern="build/app/outputs/flutter-apk/*.apk",
            )
        return collect_android_artifact(
            workspace,
            Path(request.output_dir),
            request.manifest.app.id,
            artifact_kind="aab",
            glob_pattern="build/app/outputs/bundle/release/*.aab",
        )

    @staticmethod
    def _record_step(
        result: BuildResult,
        name: str,
        status: str,
        extra: dict | None = None,
    ) -> None:
        step = {"name": name, "status": status}
        if extra:
            step.update(extra)
        result.steps.append(step)
