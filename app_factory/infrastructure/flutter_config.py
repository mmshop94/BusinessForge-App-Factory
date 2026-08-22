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
        changed.extend(self._patch_pubspec_assets(workspace))
        changed.extend(self._patch_android(workspace, manifest))
        changed.extend(self._patch_gradle_properties(workspace))
        if branding_assets_root:
            changed.extend(self._copy_branding_assets(workspace, manifest, branding_assets_root))
        changed.extend(self._apply_native_branding(workspace, manifest, branding_assets_root))
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
            "api_base_url": manifest.api_base_url,
            "backend_origin": manifest.backend_origin,
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

    def _patch_pubspec_assets(self, workspace: Path) -> list[str]:
        """Register Factory build_config JSON as Flutter asset."""
        pubspec = workspace / "pubspec.yaml"
        if not pubspec.is_file():
            raise BuildExecutionError("pubspec.yaml not found in customer app workspace")
        content = pubspec.read_text(encoding="utf-8")
        asset_entry = "    - build_config/app_factory_config.json"
        if asset_entry.strip() in content:
            return []
        flutter_block = re.search(r"(?m)^flutter:\r?\n", content)
        if not flutter_block:
            content = content.rstrip() + (
                "\nflutter:\n  uses-material-design: true\n  assets:\n"
                f"{asset_entry}\n"
            )
            pubspec.write_text(content, encoding="utf-8")
            return ["pubspec.yaml"]
        insert_at = flutter_block.end()
        if re.search(r"(?m)^  assets:\n", content[insert_at:]):
            content = content.replace(
                "  assets:\n",
                f"  assets:\n{asset_entry}\n",
                1,
            )
        else:
            content = (
                content[:insert_at]
                + "  assets:\n"
                + f"{asset_entry}\n"
                + content[insert_at:]
            )
        pubspec.write_text(content, encoding="utf-8")
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

    def _apply_native_branding(
        self,
        workspace: Path,
        manifest: AppBuildManifest,
        branding_assets_root: Path | None,
    ) -> list[str]:
        from app_factory.application.image_assets import generate_default_icon, validate_icon_file
        from app_factory.application.native_branding import NativeBrandingApplier
        from app_factory.domain.errors import AssetNotFoundError

        icon_path = None
        logo_path = None
        if branding_assets_root:
            if manifest.branding.icon_asset:
                candidate = branding_assets_root / manifest.branding.icon_asset
                if candidate.is_file():
                    icon_path = candidate
            if manifest.branding.logo_asset:
                candidate = branding_assets_root / manifest.branding.logo_asset
                if candidate.is_file():
                    logo_path = candidate
        production = manifest.release.channel == "production"
        if icon_path is None:
            if production:
                raise AssetNotFoundError("Production app delivery requires a customer app icon")
            icon_bytes = generate_default_icon(primary_color=manifest.branding.primary_color)
        else:
            validate_icon_file(icon_path)
            icon_bytes = icon_path.read_bytes()
        logo_bytes = None
        if logo_path and logo_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            logo_bytes = logo_path.read_bytes()
        return NativeBrandingApplier().apply(
            workspace,
            manifest,
            icon_bytes=icon_bytes,
            logo_bytes=logo_bytes,
            allow_default_icon=not production,
        )

    def _patch_gradle_properties(self, workspace: Path) -> list[str]:
        """Windows cross-drive Kotlin cache fix for Factory workspaces."""
        gradle_props = workspace / "android" / "gradle.properties"
        if not gradle_props.is_file():
            return []
        content = gradle_props.read_text(encoding="utf-8")
        marker = "kotlin.incremental=false"
        if marker not in content:
            content = content.rstrip() + f"\n{marker}\n"
            gradle_props.write_text(content, encoding="utf-8")
        return [str(gradle_props.relative_to(workspace))]
