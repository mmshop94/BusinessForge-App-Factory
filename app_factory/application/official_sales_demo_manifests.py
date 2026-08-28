"""Materialize App Factory manifests + branding assets for Official Sales Demos."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import httpx
import yaml
from PIL import Image, ImageDraw, ImageFont

from app_factory.application.image_assets import MIN_ICON_PX, validate_icon_bytes
from app_factory.application.official_sales_demo_discovery import OfficialSalesDemoRecord
from app_factory.application.package_identity import android_application_id_from_public_app_id


def _backend_origin(api_base_url: str) -> str:
    url = api_base_url.rstrip("/")
    if url.endswith("/api/v1"):
        return url[: -len("/api/v1")]
    return url


def _fetch_public_media(api_base_url: str, public_app_id: str, media_id: str) -> bytes | None:
    api_v1 = api_base_url.rstrip("/")
    if not api_v1.endswith("/api/v1"):
        api_v1 = f"{api_v1.rstrip('/')}/api/v1"
    url = f"{api_v1}/public/apps/{public_app_id}/media/{media_id}/content"
    try:
        response = httpx.get(url, timeout=60.0)
        if response.status_code == 200 and response.content:
            return response.content
    except httpx.HTTPError:
        return None
    return None


def _square_icon_png(source: bytes, *, size: int = 1024) -> bytes:
    with Image.open(io.BytesIO(source)) as image:
        image = image.convert("RGBA")
        width, height = image.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        cropped = image.crop((left, top, left + side, top + side))
        if side < MIN_ICON_PX:
            cropped = cropped.resize((size, size), Image.Resampling.LANCZOS)
        elif side != size:
            cropped = cropped.resize((size, size), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG")
        return buffer.getvalue()


def _monogram_icon_png(*, label: str, primary_color: str, size: int = 1024) -> bytes:
    color = primary_color.lstrip("#")
    rgb = (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
    image = Image.new("RGBA", (size, size), rgb + (255,))
    draw = ImageDraw.Draw(image)
    letter = (label.strip()[:1] or "?").upper()
    try:
        font = ImageFont.truetype("arial.ttf", size // 2)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - bbox[1]), letter, fill=(255, 255, 255, 255), font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _write_logo_svg(path: Path, *, title: str, primary_color: str) -> None:
    letter = (title.strip()[:1] or "?").upper()
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="{title}">\n'
        f'  <rect width="128" height="128" rx="24" fill="{primary_color}"/>\n'
        f'  <text x="64" y="82" text-anchor="middle" font-size="56" fill="#ffffff" '
        f'font-family="Arial,sans-serif">{letter}</text>\n'
        f"</svg>\n",
        encoding="utf-8",
    )


def build_manifest_dict(
    record: OfficialSalesDemoRecord,
    *,
    api_base_url: str,
    customer_app_ref: str = "main",
    app_version: str = "1.0.0",
    build_number: int = 1,
    channel: str = "pilot",
) -> dict[str, Any]:
    android_id = android_application_id_from_public_app_id(record.public_app_id)
    return {
        "schema_version": 1,
        "app": {
            "id": record.slug,
            "display_name": record.display_name,
            "package_name_android": android_id,
            "bundle_id_ios": android_id,
        },
        "tenant": {
            "public_app_id": record.public_app_id,
            "package": record.runtime_package,
            "package_version": record.package_version,
        },
        "branding": {
            "theme": record.theme,
            "primary_color": record.primary_color,
            "secondary_color": record.secondary_color,
            "logo_asset": "branding/logo.svg",
            "splash_asset": "branding/splash.png",
            "icon_asset": "branding/icon.png",
        },
        "features": _features_from_record(record),
        "release": {
            "channel": channel,
            "app_version": app_version,
            "build_number": build_number,
        },
        "source": {
            "customer_app_ref": customer_app_ref,
            "customer_app_repo": "../BusinessForge-FlutterApp-main",
            "factory_compat_version": "1",
        },
        "api_base_url": api_base_url,
        "backend_origin": _backend_origin(api_base_url),
        "design_template_id": record.design_template_id,
        "build_target": "android",
    }


def _features_from_record(record: OfficialSalesDemoRecord) -> dict[str, bool]:
    from app_factory.application.official_sales_demo_discovery import features_for_record

    return features_for_record(record)


def materialize_demo_manifest_dir(
    record: OfficialSalesDemoRecord,
    output_dir: Path,
    *,
    api_base_url: str,
    customer_app_ref: str = "main",
) -> Path:
    """Write manifest.yaml + branding assets for one official sales demo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    branding_dir = output_dir / "branding"
    branding_dir.mkdir(parents=True, exist_ok=True)

    icon_source: bytes | None = None
    media_id = record.hero_media_id or record.logo_media_id
    if media_id and record.public_app_id:
        raw = _fetch_public_media(api_base_url, record.public_app_id, str(media_id))
        if raw:
            try:
                icon_source = _square_icon_png(raw)
                validate_icon_bytes(icon_source, label="hero_icon")
            except Exception:
                icon_source = None

    if icon_source is None:
        icon_source = _monogram_icon_png(
            label=record.display_name,
            primary_color=record.primary_color,
        )

    icon_path = branding_dir / "icon.png"
    icon_path.write_bytes(icon_source)
    splash_path = branding_dir / "splash.png"
    splash_path.write_bytes(icon_source)
    _write_logo_svg(branding_dir / "logo.svg", title=record.display_name, primary_color=record.primary_color)

    manifest = build_manifest_dict(
        record,
        api_base_url=api_base_url,
        customer_app_ref=customer_app_ref,
    )
    manifest_path = output_dir / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    metadata = {
        "tenant_slug": record.slug,
        "business_name": record.business_name,
        "vertical": record.runtime_package,
        "public_app_id": record.public_app_id,
        "api_base_url": api_base_url,
        "application_id": manifest["app"]["package_name_android"],
        "app_name": record.display_name,
        "version_name": manifest["release"]["app_version"],
        "version_code": manifest["release"]["build_number"],
        "branding_source": "demo_plane_bootstrap",
        "icon_source": "hero_media" if media_id else "monogram_fallback",
        "hero_media_id": record.hero_media_id,
        "login_ok": record.login_ok,
        "bootstrap_ok": record.bootstrap_ok,
        "build_status": "pending",
    }
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "app.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    store_metadata = {
        "app_name": record.display_name,
        "short_description": f"{record.display_name} — BusinessForge Demo App",
        "full_description": (
            f"Official BusinessForge sales demo app for {record.display_name}. "
            "Connected to the isolated demo data plane for internal evaluation."
        ),
        "application_id": manifest["app"]["package_name_android"],
        "default_language": "de-DE",
        "category_recommendation": _category_for_package(record.runtime_package),
        "privacy_policy_status": "MISSING",
        "privacy_policy_url": None,
        "icon_status": "generated" if media_id else "monogram_fallback",
        "feature_graphic_status": "MISSING",
        "phone_screenshot_status": "MISSING",
        "tablet_screenshot_status": "MISSING",
        "release_notes": "Official Sales Demo — internal demo plane build",
        "api_release_gap": (
            None
            if str(api_base_url).startswith("https://demo-api.bforge.de")
            else "Demo uses LAN HTTP endpoint; public HTTPS demo API required for store release"
        ),
    }
    (metadata_dir / "play_store.json").write_text(
        json.dumps(store_metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _category_for_package(package: str) -> str:
    if package == "restaurant":
        return "FOOD_AND_DRINK"
    if package == "village_store":
        return "SHOPPING"
    if package.startswith("appointment_"):
        return "BEAUTY"
    return "BUSINESS"
