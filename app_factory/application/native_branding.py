"""Apply native Android branding (icons, splash, signing hooks) to a workspace."""

from __future__ import annotations

import re
from pathlib import Path

from app_factory.application.image_assets import (
    generate_android_icons,
    generate_splash,
    write_play_store_icon,
)
from app_factory.application.signing import gradle_release_signing_snippet, signing_status
from app_factory.domain.build import AppBuildManifest


class NativeBrandingApplier:
    def apply(
        self,
        workspace: Path,
        manifest: AppBuildManifest,
        *,
        icon_bytes: bytes,
        logo_bytes: bytes | None,
        allow_default_icon: bool,
    ) -> list[str]:
        del allow_default_icon
        res = workspace / "android" / "app" / "src" / "main" / "res"
        res.mkdir(parents=True, exist_ok=True)
        changed = generate_android_icons(icon_bytes, res)
        branding_assets = workspace / "assets" / "branding"
        branding_assets.mkdir(parents=True, exist_ok=True)
        changed.append(
            write_play_store_icon(icon_bytes, branding_assets / "play_store_icon_512.png")
        )
        splash_color = manifest.branding.primary_color or "#2563EB"
        changed.extend(
            generate_splash(
                background_color=splash_color,
                logo_bytes=logo_bytes,
                output_res=res,
            )
        )
        changed.extend(self._patch_signing(workspace))
        return [str(Path(item).relative_to(workspace)) if Path(item).is_absolute() else item for item in changed]

    def _patch_signing(self, workspace: Path) -> list[str]:
        gradle = workspace / "android" / "app" / "build.gradle.kts"
        if not gradle.is_file():
            return []
        content = gradle.read_text(encoding="utf-8")
        if "BF_ANDROID_KEYSTORE_PATH" in content:
            return []
        snippet = gradle_release_signing_snippet().strip()
        # Insert signingConfigs before buildTypes when env is used at build time.
        if "buildTypes {" in content:
            content = content.replace(
                "buildTypes {",
                snippet + "\n    buildTypes {",
                1,
            )
        if signing_status().configured:
            content = re.sub(
                r"signingConfig\s*=\s*signingConfigs\.getByName\(\"debug\"\)",
                'signingConfig = signingConfigs.getByName("release")',
                content,
                count=1,
            )
        gradle.write_text(content, encoding="utf-8")
        return [str(gradle.relative_to(workspace))]
