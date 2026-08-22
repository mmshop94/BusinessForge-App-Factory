"""Materialize a backend factory export into a local manifest + assets directory."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from app_factory.application.image_assets import validate_icon_bytes
from app_factory.application.package_identity import validate_android_application_id
from app_factory.application.manifest_validator import ManifestValidator
from app_factory.domain.errors import ManifestValidationError


def materialize_export(payload: dict[str, Any], output_dir: Path) -> Path:
    ManifestValidator._assert_no_secrets(payload)
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        raise ManifestValidationError("Export must contain manifest object")
    validate_android_application_id(str(manifest["app"]["package_name_android"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = payload.get("assets") or {}
    if not isinstance(assets, dict):
        raise ManifestValidationError("assets must be an object")
    for relative, spec in assets.items():
        if ".." in relative or relative.startswith("/") or "\\" in relative:
            raise ManifestValidationError(f"Illegal asset path: {relative}")
        if not isinstance(spec, dict) or "content_base64" not in spec:
            raise ManifestValidationError(f"Asset {relative} missing content")
        data = base64.b64decode(str(spec["content_base64"]))
        if Path(relative).name.startswith("icon."):
            validate_icon_bytes(data, label=relative)
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path
