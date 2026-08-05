from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app_factory.domain.build import AppBuildManifest, BuildRequest
from app_factory.domain.enums import AndroidArtifactFormat


@dataclass(frozen=True)
class BuildPlanStep:
    name: str
    description: str
    command: str | None = None


@dataclass(frozen=True)
class BuildPlan:
    manifest: AppBuildManifest
    manifest_hash: str
    customer_app_path: Path
    workspace_path: Path
    output_dir: Path
    artifact_format: AndroidArtifactFormat
    steps: list[BuildPlanStep] = field(default_factory=list)
    dart_defines: dict[str, str] = field(default_factory=dict)
    generated_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": {
                "app_id": self.manifest.app.id,
                "display_name": self.manifest.app.display_name,
                "package_name_android": self.manifest.app.package_name_android,
                "public_app_id": self.manifest.tenant.public_app_id,
                "customer_app_ref": self.manifest.source.customer_app_ref,
                "app_version": self.manifest.release.app_version,
                "build_number": self.manifest.release.build_number,
            },
            "manifest_hash": self.manifest_hash,
            "customer_app_path": str(self.customer_app_path),
            "workspace_path": str(self.workspace_path),
            "output_dir": str(self.output_dir),
            "artifact_format": self.artifact_format.value,
            "dart_defines": self.dart_defines,
            "generated_files": self.generated_files,
            "steps": [
                {"name": step.name, "description": step.description, "command": step.command}
                for step in self.steps
            ],
        }


class BuildPlanner:
    """Deterministic build plan from manifest + factory defaults."""

    GENERATED_FILES = [
        "build_config/app_factory_config.json",
        "build_config/dart_defines.json",
        "android/local.properties.generated",
    ]

    def plan(
        self,
        manifest: AppBuildManifest,
        manifest_hash: str,
        customer_app_path: Path,
        output_dir: Path,
        *,
        artifact_format: AndroidArtifactFormat = AndroidArtifactFormat.APK,
        workspace_root: Path | None = None,
    ) -> BuildPlan:
        workspace_path = (workspace_root or output_dir / ".workspaces") / manifest.app.id
        dart_defines = self._dart_defines(manifest)
        steps = self._steps(artifact_format)

        return BuildPlan(
            manifest=manifest,
            manifest_hash=manifest_hash,
            customer_app_path=customer_app_path.resolve(),
            workspace_path=workspace_path.resolve(),
            output_dir=output_dir.resolve(),
            artifact_format=artifact_format,
            dart_defines=dart_defines,
            generated_files=list(self.GENERATED_FILES),
            steps=steps,
        )

    def plan_request(self, request: BuildRequest, workspace_root: Path | None = None) -> BuildPlan:
        return self.plan(
            manifest=request.manifest,
            manifest_hash=request.manifest_hash,
            customer_app_path=Path(request.customer_app_path),
            output_dir=Path(request.output_dir),
            artifact_format=request.artifact_format,
            workspace_root=workspace_root,
        )

    @staticmethod
    def _dart_defines(manifest: AppBuildManifest) -> dict[str, str]:
        defines = {
            "API_BASE_URL": manifest.api_base_url,
            "BACKEND_ORIGIN": manifest.resolved_backend_origin,
            "PUBLIC_APP_ID": manifest.tenant.public_app_id,
            "APP_PACKAGE": manifest.tenant.package,
            "APP_PACKAGE_VERSION": manifest.tenant.package_version,
            "BRAND_THEME": manifest.branding.theme,
            "BRAND_PRIMARY_COLOR": manifest.branding.primary_color,
            "BRAND_SECONDARY_COLOR": manifest.branding.secondary_color,
        }
        for name, enabled in sorted(manifest.features.flags.items()):
            defines[f"FEATURE_{name.upper()}"] = "true" if enabled else "false"
        return defines

    @staticmethod
    def _steps(artifact_format: AndroidArtifactFormat) -> list[BuildPlanStep]:
        build_target = "apk" if artifact_format == AndroidArtifactFormat.APK else "appbundle"
        return [
            BuildPlanStep(
                name="prepare_workspace",
                description="Copy customer app into isolated temporary workspace",
            ),
            BuildPlanStep(
                name="apply_manifest",
                description="Generate Flutter/Android configuration from manifest",
            ),
            BuildPlanStep(
                name="flutter_pub_get",
                description="Resolve Dart dependencies",
                command="flutter pub get",
            ),
            BuildPlanStep(
                name="flutter_analyze",
                description="Static analysis gate",
                command="flutter analyze",
            ),
            BuildPlanStep(
                name="flutter_test",
                description="Unit and widget tests",
                command="flutter test",
            ),
            BuildPlanStep(
                name="flutter_build",
                description=f"Build Android {build_target.upper()}",
                command=f"flutter build {build_target} --release",
            ),
            BuildPlanStep(
                name="collect_artifacts",
                description="Hash and copy build outputs with report",
            ),
            BuildPlanStep(
                name="cleanup_workspace",
                description="Remove temporary workspace",
            ),
        ]
