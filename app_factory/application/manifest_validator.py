from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

from app_factory.domain.build import (
    AppBuildManifest,
    AppIdentity,
    BrandingConfiguration,
    FeatureConfiguration,
    ReleaseConfiguration,
    SourceRevision,
    TenantBinding,
)
from app_factory.domain.errors import (
    AssetNotFoundError,
    CompatibilityError,
    ManifestSecretError,
    ManifestValidationError,
)

SECRET_KEY_PATTERN = re.compile(
    r"(password|secret|api[_-]?key|private[_-]?key|keystore|token|credential)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(BEGIN (RSA |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}|-----BEGIN)",
    re.IGNORECASE,
)
ANDROID_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


class ManifestLoader:
    """Load YAML/JSON manifests into domain objects."""

    def load(self, manifest_path: Path) -> dict[str, Any]:
        text = manifest_path.read_text(encoding="utf-8")
        if manifest_path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        elif manifest_path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            raise ManifestValidationError(
                f"Unsupported manifest format: {manifest_path.suffix}"
            )
        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest root must be an object")
        return data

    def to_domain(self, data: dict[str, Any], manifest_path: Path | None = None) -> AppBuildManifest:
        return AppBuildManifest(
            schema_version=int(data["schema_version"]),
            app=AppIdentity(
                id=data["app"]["id"],
                display_name=data["app"]["display_name"],
                package_name_android=data["app"]["package_name_android"],
                bundle_id_ios=data["app"].get("bundle_id_ios"),
            ),
            tenant=TenantBinding(
                public_app_id=data["tenant"]["public_app_id"],
                package=data["tenant"]["package"],
                package_version=data["tenant"]["package_version"],
            ),
            branding=BrandingConfiguration(
                theme=data["branding"]["theme"],
                primary_color=data["branding"]["primary_color"],
                secondary_color=data["branding"]["secondary_color"],
                logo_asset=data["branding"]["logo_asset"],
                splash_asset=data["branding"].get("splash_asset"),
                icon_asset=data["branding"].get("icon_asset"),
            ),
            features=FeatureConfiguration(flags=dict(data.get("features") or {})),
            release=ReleaseConfiguration(
                channel=data["release"]["channel"],
                app_version=data["release"]["app_version"],
                build_number=int(data["release"]["build_number"]),
            ),
            source=SourceRevision(
                customer_app_ref=data["source"]["customer_app_ref"],
                customer_app_repo=data["source"].get("customer_app_repo"),
                factory_compat_version=str(data["source"].get("factory_compat_version", "1")),
            ),
            api_base_url=data["api_base_url"],
            backend_origin=data.get("backend_origin"),
            manifest_path=str(manifest_path) if manifest_path else None,
            delivery_job_id=data.get("delivery_job_id"),
            design_template_id=data.get("design_template_id"),
        )


class ManifestValidator:
    """Schema + business-rule validation for tenant manifests."""

    def __init__(
        self,
        schema_path: Path,
        compat_path: Path | None = None,
        *,
        supported_packages: Iterable[str] | None = None,
    ) -> None:
        self._schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self._compat: dict[str, Any] = {}
        if compat_path and compat_path.exists():
            self._compat = json.loads(compat_path.read_text(encoding="utf-8"))
        self._supported_packages = set(supported_packages or [])
        if self._compat.get("packages"):
            self._supported_packages |= set(self._compat["packages"].keys())

    def validate_raw(self, data: dict[str, Any]) -> None:
        self._assert_no_secrets(data)
        try:
            jsonschema.validate(instance=data, schema=self._schema)
        except jsonschema.ValidationError as exc:
            raise ManifestValidationError(str(exc.message)) from exc
        self._validate_business_rules(data)

    def validate_file(self, manifest_path: Path) -> AppBuildManifest:
        loader = ManifestLoader()
        data = loader.load(manifest_path)
        self.validate_raw(data)
        manifest = loader.to_domain(data, manifest_path)
        self.validate_assets(manifest_path.parent, manifest)
        self.validate_compatibility(manifest)
        return manifest

    def validate_assets(self, manifest_dir: Path, manifest: AppBuildManifest) -> None:
        assets = [manifest.branding.logo_asset]
        if manifest.branding.splash_asset:
            assets.append(manifest.branding.splash_asset)
        if manifest.branding.icon_asset:
            assets.append(manifest.branding.icon_asset)
        for rel in assets:
            if not (manifest_dir / rel).is_file():
                raise AssetNotFoundError(f"Branding asset not found: {rel}")

    def validate_compatibility(self, manifest: AppBuildManifest) -> None:
        packages = self._compat.get("packages", {})
        pkg = manifest.tenant.package
        if self._supported_packages and pkg not in self._supported_packages:
            raise CompatibilityError(f"Unknown package: {pkg}")
        pkg_info = packages.get(pkg)
        if not pkg_info:
            return
        supported_refs = set(pkg_info.get("supported_customer_app_refs", []))
        if supported_refs and manifest.source.customer_app_ref not in supported_refs:
            raise CompatibilityError(
                f"Customer app ref '{manifest.source.customer_app_ref}' "
                f"is not supported for package '{pkg}'"
            )
        supported_schema = self._compat.get("supported_schema_versions", [1])
        if manifest.schema_version not in supported_schema:
            raise CompatibilityError(
                f"Schema version {manifest.schema_version} is not supported"
            )

    @staticmethod
    def manifest_hash(data: dict[str, Any]) -> str:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _validate_business_rules(self, data: dict[str, Any]) -> None:
        android_id = data["app"]["package_name_android"]
        if not ANDROID_ID_PATTERN.match(android_id):
            raise ManifestValidationError(f"Invalid Android application ID: {android_id}")
        from app_factory.application.package_identity import ANDROID_APPLICATION_ID_PATTERN

        if not ANDROID_APPLICATION_ID_PATTERN.match(android_id):
            raise ManifestValidationError(
                "Android application ID must be de.bforge.app.{public_app_ulid}"
            )

    @classmethod
    def _assert_no_secrets(cls, data: Any, path: str = "$") -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                key_path = f"{path}.{key}"
                if SECRET_KEY_PATTERN.search(str(key)):
                    raise ManifestSecretError(f"Forbidden secret-like key: {key_path}")
                cls._assert_no_secrets(value, key_path)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                cls._assert_no_secrets(item, f"{path}[{index}]")
        elif isinstance(data, str) and SECRET_VALUE_PATTERN.search(data):
            raise ManifestSecretError(f"Forbidden secret-like value at {path}")
