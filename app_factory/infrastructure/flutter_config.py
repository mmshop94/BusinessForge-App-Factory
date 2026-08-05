from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from app_factory.domain.build import AppBuildManifest
from app_factory.domain.errors import BuildExecutionError


class FlutterConfigApplier:
    """Apply manifest values to an isolated Flutter workspace."""

    PUBSPEC_VERSION_PATTERN = re.compile(
        r"^(version:\s*)([^\n]+)$",
        re.MULTILINE,
    )

    def apply(
        self,
        workspace: Path,
        manifest: AppBuildManifest,
        dart_defines: dict[str, str],
        branding_assets_root: Path | None = None,
    ) -> list[str]:
        changed: list[str] = []
        changed.extend(self._write_build_config(workspace, manifest, dart_defines))
        changed.extend(self._patch_pubspec(workspace, manifest))
        changed.extend(self._patch_android(workspace, manifest))
        if branding_assets_root:
            changed.extend(self._copy_branding_assets(workspace, manifest, branding_assets_root))
        return changed

    def _write_build_config(
        self,
        workspace: Path,
        manifest: AppBuildManifest,
        dart_defines: dict[str, str],
    ) -> list[str]:
        config_dir = workspace / "build_config"
        config_dir.mkdir(parents=True, exist_ok=True)

        app_factory_config = {
            "schema_version": manifest.schema_version,
            "app_id": manifest.app.id,
            "display_name": manifest.app.display_name,
            "package_name_android": manifest.app.package_name_android,
            "bundle_id_ios": manifest.app.bundle_id_ios,
            "public_app_id": manifest.tenant.public_app_id,
            "tenant_package": manifest.tenant.package,
            "tenant_package_version": manifest.tenant.package_version,
            "branding": {
                "theme": manifest.branding.theme,
                "primary_color": manifest.branding.primary_color,
                "secondary_color": manifest.branding.secondary_color,
            },
            "features": manifest.features.flags,
            "release": {
                "channel": manifest.release.channel,
                "app_version": manifest.release.app_version,
                "build_number": manifest.release.build_number,
            },
            "source": {
                "customer_app_ref": manifest.source.customer_app_ref,
                "factory_compat_version": manifest.source.factory_compat_version,
            },
        }
        config_path = config_dir / "app_factory_config.json"
        config_path.write_text(
            json.dumps(app_factory_config, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        defines_path = config_dir / "dart_defines.json"
        defines_path.write_text(
            json.dumps(dart_defines, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return [str(config_path.relative_to(workspace)), str(defines_path.relative_to(workspace))]

    def _patch_pubspec(self, workspace: Path, manifest: AppBuildManifest) -> list[str]:
        pubspec = workspace / "pubspec.yaml"
        if not pubspec.is_file():
            raise BuildExecutionError("pubspec.yaml not found in customer app workspace")
        content = pubspec.read_text(encoding="utf-8")
        version = f"{manifest.release.app_version}+{manifest.release.build_number}"
        updated, count = self.PUBSPEC_VERSION_PATTERN.subn(rf"\g<1>{version}", content, count=1)
        if count == 0:
            raise BuildExecutionError("Could not patch pubspec.yaml version")
        pubspec.write_text(updated, encoding="utf-8")
        return ["pubspec.yaml"]

    def _patch_android(self, workspace: Path, manifest: AppBuildManifest) -> list[str]:
        changed: list[str] = []
        gradle = workspace / "android" / "app" / "build.gradle.kts"
        if gradle.is_file():
            content = gradle.read_text(encoding="utf-8")
            content = re.sub(
                r'applicationId\s*=\s*"[^"]+"',
                f'applicationId = "{manifest.app.package_name_android}"',
                content,
                count=1,
            )
            gradle.write_text(content, encoding="utf-8")
            changed.append(str(gradle.relative_to(workspace)))

        manifest_xml = workspace / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
        if manifest_xml.is_file():
            content = manifest_xml.read_text(encoding="utf-8")
            content = re.sub(
                r'android:label="[^"]+"',
                f'android:label="{manifest.app.display_name}"',
                content,
                count=1,
            )
            manifest_xml.write_text(content, encoding="utf-8")
            changed.append(str(manifest_xml.relative_to(workspace)))
        return changed

    def _copy_branding_assets(
        self,
        workspace: Path,
        manifest: AppBuildManifest,
        branding_assets_root: Path,
    ) -> list[str]:
        target_dir = workspace / "assets" / "branding"
        target_dir.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for rel in (
            manifest.branding.logo_asset,
            manifest.branding.splash_asset,
            manifest.branding.icon_asset,
        ):
            if not rel:
                continue
            source = branding_assets_root / rel
            if not source.is_file():
                source = branding_assets_root.parent / rel
            if not source.is_file():
                continue
            target = target_dir / Path(rel).name
            shutil.copy2(source, target)
            copied.append(str(target.relative_to(workspace)))
        return copied
