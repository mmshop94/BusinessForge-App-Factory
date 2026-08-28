"""Canonical API origins and fail-closed origin inspection for demo app builds."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

LAN_DEMO_API_BASE_URL = "http://192.168.178.95:8090/api/v1"
PUBLIC_DEMO_API_BASE_URL = "https://demo-api.bforge.de/api/v1"
PRODUCTION_API_HOST = "api.bforge.de"
DEMO_API_HOST = "demo-api.bforge.de"

# Config-time --public-api also blocks localhost / 127.0.0.1 / http://.
# Artefact scan cannot use those: Dart snapshots retain Flutter dev defaults
# such as http://127.0.0.1:8000/api/v1 even when dart-define overrides API_BASE_URL.
_LAN_CONFIG_MARKERS = (
    "192.168.",
    ":8090",
    "localhost",
    "127.0.0.1",
)
_LAN_ARTIFACT_MARKERS = (
    "192.168.178.95",
    "192.168.",
    ":8090",
)


class DemoApiOriginError(ValueError):
    """Raised when an official sales demo would target a forbidden API origin."""


def _normalize(api_base_url: str) -> str:
    return (api_base_url or "").strip()


def assert_official_sales_demo_api_origin(api_base_url: str) -> str:
    """LAN or public demo API is allowed; Production ``api.bforge.de`` is not."""
    value = _normalize(api_base_url)
    lowered = value.lower()
    if DEMO_API_HOST in lowered:
        return value
    if PRODUCTION_API_HOST in lowered:
        raise DemoApiOriginError(
            "Official Sales Demo builds must not use Production api.bforge.de. "
            f"Use {PUBLIC_DEMO_API_BASE_URL} (public) or {LAN_DEMO_API_BASE_URL} (LAN)."
        )
    return value


def assert_public_demo_api_origin(api_base_url: str) -> str:
    """Fail-closed origin for ``--public-api`` builds."""
    value = assert_official_sales_demo_api_origin(api_base_url)
    lowered = value.lower()
    if not lowered.startswith("https://"):
        raise DemoApiOriginError(
            f"Public demo builds require HTTPS. Got {value!r}."
        )
    if any(marker in lowered for marker in _LAN_CONFIG_MARKERS):
        raise DemoApiOriginError(
            f"Public demo builds must not use a LAN origin. Got {value!r}."
        )
    if lowered.rstrip("/") != PUBLIC_DEMO_API_BASE_URL.rstrip("/"):
        raise DemoApiOriginError(
            "Public demo builds require "
            f"{PUBLIC_DEMO_API_BASE_URL}. Got {value!r}."
        )
    return value


def _count_utf8_and_utf16(blob: bytes, needle: str) -> int:
    return blob.count(needle.encode("utf-8")) + blob.count(needle.encode("utf-16-le"))


def production_api_host_present(blob: bytes) -> bool:
    """True when ``api.bforge.de`` appears outside ``demo-api.bforge.de``."""
    prod = _count_utf8_and_utf16(blob, PRODUCTION_API_HOST)
    demo = _count_utf8_and_utf16(blob, DEMO_API_HOST)
    return prod > demo


def lan_origin_present(blob: bytes) -> bool:
    """True when a LAN demo API origin is embedded (not Flutter loopback defaults)."""
    return any(_count_utf8_and_utf16(blob, marker) for marker in _LAN_ARTIFACT_MARKERS)


def snapshot_loopback_present(blob: bytes) -> bool:
    """Informational: Dart snapshots often retain 127.0.0.1:8000 / localhost defaults."""
    return any(
        _count_utf8_and_utf16(blob, marker) for marker in ("localhost", "127.0.0.1")
    )


def public_demo_origin_present(blob: bytes) -> bool:
    return _count_utf8_and_utf16(blob, DEMO_API_HOST) > 0


def _should_scan_member(name: str) -> bool:
    lowered = name.replace("\\", "/").lower()
    if lowered.endswith("libapp.so") or lowered.endswith("kernel_blob.bin"):
        return True
    return "assets/flutter_assets/" in lowered


def _factory_config_api_base_url(archive: zipfile.ZipFile) -> str | None:
    suffix = "assets/flutter_assets/build_config/app_factory_config.json"
    for info in archive.infolist():
        if info.filename.replace("\\", "/").endswith(suffix):
            payload = json.loads(archive.read(info).decode("utf-8"))
            return str(payload.get("api_base_url") or "").strip() or None
    return None


def inspect_android_artifact_origins(path: Path) -> dict[str, bool | str | None]:
    """Scan APK/AAB Dart/asset members for API origins."""
    public = False
    lan = False
    production = False
    loopback = False
    config_api: str | None = None
    with zipfile.ZipFile(path) as archive:
        config_api = _factory_config_api_base_url(archive)
        for info in archive.infolist():
            if info.is_dir() or not _should_scan_member(info.filename):
                continue
            blob = archive.read(info)
            public = public or public_demo_origin_present(blob)
            lan = lan or lan_origin_present(blob)
            production = production or production_api_host_present(blob)
            loopback = loopback or snapshot_loopback_present(blob)
    return {
        "public_demo_origin_present": public,
        "lan_origin_present": lan,
        "production_origin_present": production,
        "snapshot_loopback_present": loopback,
        "factory_config_api_base_url": config_api,
    }


def assert_public_artifact_origins(path: Path) -> dict[str, bool | str | None]:
    report = inspect_android_artifact_origins(path)
    if report["lan_origin_present"]:
        raise DemoApiOriginError(f"LAN origin embedded in {path}")
    if report["production_origin_present"]:
        raise DemoApiOriginError(f"Production api.bforge.de embedded in {path}")
    if not report["public_demo_origin_present"]:
        raise DemoApiOriginError(f"demo-api.bforge.de missing from {path}")
    config_api = report.get("factory_config_api_base_url")
    if config_api:
        assert_public_demo_api_origin(str(config_api))
    return report
