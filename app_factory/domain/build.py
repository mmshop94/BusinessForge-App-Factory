from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app_factory.domain.enums import AndroidArtifactFormat, BuildStatus


@dataclass(frozen=True)
class AppIdentity:
    """Public app identity used by stores and package managers."""

    id: str
    display_name: str
    package_name_android: str
    bundle_id_ios: Optional[str] = None


@dataclass(frozen=True)
class TenantBinding:
    """Non-secret tenant association embedded in the client."""

    public_app_id: str
    package: str
    package_version: str


@dataclass(frozen=True)
class BrandingConfiguration:
    """Build-time branding inputs referenced by the manifest."""

    theme: str
    primary_color: str
    secondary_color: str
    logo_asset: str
    splash_asset: Optional[str] = None
    icon_asset: Optional[str] = None


@dataclass(frozen=True)
class FeatureConfiguration:
    """Feature flags applied at build time."""

    flags: dict[str, bool] = field(default_factory=dict)

    def is_enabled(self, name: str) -> bool:
        return self.flags.get(name, False)


@dataclass(frozen=True)
class ReleaseConfiguration:
    """Versioning and release channel metadata."""

    channel: str
    app_version: str
    build_number: int


@dataclass(frozen=True)
class SourceRevision:
    """Pinned customer-app source used for reproducible builds."""

    customer_app_ref: str
    customer_app_repo: Optional[str] = None
    factory_compat_version: str = "1"


@dataclass(frozen=True)
class AppBuildManifest:
    """Validated tenant build manifest — no secrets allowed."""

    schema_version: int
    app: AppIdentity
    tenant: TenantBinding
    branding: BrandingConfiguration
    features: FeatureConfiguration
    release: ReleaseConfiguration
    source: SourceRevision
    api_base_url: str
    backend_origin: Optional[str] = None
    manifest_path: Optional[str] = None

    @property
    def flutter_version_name(self) -> str:
        return self.release.app_version

    @property
    def flutter_build_number(self) -> str:
        return str(self.release.build_number)

    @property
    def resolved_backend_origin(self) -> str:
        if self.backend_origin:
            return self.backend_origin.rstrip("/")
        # Derive from api_base_url: strip trailing /api/v1
        base = self.api_base_url.rstrip("/")
        for suffix in ("/api/v1", "/api"):
            if base.endswith(suffix):
                return base[: -len(suffix)]
        return base


@dataclass(frozen=True)
class BuildArtifact:
    """Single output file produced by a build."""

    kind: str
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class BuildRequest:
    """Input to the build orchestrator."""

    manifest: AppBuildManifest
    manifest_hash: str
    customer_app_path: str
    output_dir: str
    artifact_format: AndroidArtifactFormat = AndroidArtifactFormat.APK
    run_tests: bool = True
    run_analyze: bool = True
    dry_run: bool = False


@dataclass
class BuildResult:
    """Outcome of a build including reproducibility metadata."""

    status: BuildStatus
    request: BuildRequest
    started_at: datetime
    finished_at: Optional[datetime] = None
    customer_app_commit: Optional[str] = None
    flutter_version: Optional[str] = None
    dart_version: Optional[str] = None
    artifacts: list[BuildArtifact] = field(default_factory=list)
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    steps: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def mark_finished(self, status: BuildStatus, error: Optional[str] = None) -> None:
        self.status = status
        self.finished_at = datetime.now(timezone.utc)
        if error:
            self.error_message = error
