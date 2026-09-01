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

    FLUTTER_FEATURE_FLAGS = {
        "ordering",
        "news",
        "loyalty",
        "scheduling",
        "notifications",
        "payments",
        "catalog",
        "restaurant_menu",
        "village_store",
        "documents",
    }

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
        extra_dart_defines: dict[str, str] | None = None,
        debug_build: bool = False,
    ) -> BuildPlan:
        workspace_path = (workspace_root or output_dir / ".workspaces") / manifest.app.id
        dart_defines = self._dart_defines(manifest)
        if extra_dart_defines:
            dart_defines.update(extra_dart_defines)
        steps = self._steps(artifact_format, debug_build=debug_build)

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
        extra = dict(request.extra_dart_defines)
        if request.e2e_test:
            from app_factory.application.e2e_build import e2e_dart_defines

            extra.update(
                e2e_dart_defines(
                    environment=request.e2e_environment or "demo",
                    run_id=request.e2e_run_id,
                )
            )
        return self.plan(
            manifest=request.manifest,
            manifest_hash=request.manifest_hash,
            customer_app_path=Path(request.customer_app_path),
            output_dir=Path(request.output_dir),
            artifact_format=request.artifact_format,
            workspace_root=workspace_root,
            extra_dart_defines=extra,
            debug_build=request.debug_build,
        )

    @staticmethod
    def _dart_defines(manifest: AppBuildManifest) -> dict[str, str]:
        defines = {
            "API_BASE_URL": manifest.api_base_url,
            "BACKEND_ORIGIN": manifest.resolved_backend_origin,
            "PUBLIC_APP_ID": manifest.tenant.public_app_id,
            "PACKAGE_ID": manifest.tenant.package,
            "PACKAGE_VERSION": manifest.tenant.package_version,
            "APP_NAME": manifest.app.display_name,
            "PRIMARY_COLOR": manifest.branding.primary_color,
            "SECONDARY_COLOR": manifest.branding.secondary_color,
        }
        for name, enabled in sorted(manifest.features.flags.items()):
            if name not in BuildPlanner.FLUTTER_FEATURE_FLAGS:
                continue
            feature_key = name.upper()
            if feature_key == "VILLAGE_STORE" or name == "village_store":
                defines["FEATURE_VILLAGE_STORE"] = "true" if enabled else "false"
            elif feature_key == "RESTAURANT" or name == "restaurant_menu":
                defines["FEATURE_RESTAURANT_MENU"] = "true" if enabled else "false"
            else:
                defines[f"FEATURE_{feature_key}"] = "true" if enabled else "false"

        BuildPlanner._apply_package_features(defines, manifest.tenant.package)
        return defines

    @staticmethod
    def _apply_package_features(defines: dict[str, str], package_id: str) -> None:
        """Package slug implies compile-time module flags unless explicitly disabled."""
        if package_id == "village_store":
            defines.setdefault("FEATURE_VILLAGE_STORE", "true")
            defines.setdefault("FEATURE_NOTIFICATIONS", "true")
            defines.setdefault("FEATURE_PAYMENTS", "true")
        elif package_id == "restaurant":
            defines.setdefault("FEATURE_RESTAURANT_MENU", "true")
            defines.setdefault("FEATURE_SCHEDULING", "true")
            defines.setdefault("FEATURE_NOTIFICATIONS", "true")
            defines.setdefault("FEATURE_PAYMENTS", "true")
        elif package_id.startswith("appointment_"):
            defines.setdefault("FEATURE_APPOINTMENTS", "true")
            defines.setdefault("FEATURE_NOTIFICATIONS", "true")
            defines.setdefault("FEATURE_DOCUMENTS", "true")

    @staticmethod
    def _steps(
        artifact_format: AndroidArtifactFormat,
        *,
        debug_build: bool = False,
    ) -> list[BuildPlanStep]:
        build_target = "apk" if artifact_format == AndroidArtifactFormat.APK else "appbundle"
        mode = "" if debug_build else " --release"
        if debug_build and artifact_format != AndroidArtifactFormat.APK:
            raise ValueError("E2E debug builds support APK only (not AAB).")
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
                command=f"flutter build {build_target}{mode}",
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
