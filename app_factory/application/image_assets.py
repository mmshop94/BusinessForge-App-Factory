"""Validate source branding images and generate Android native assets."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app_factory.domain.errors import AssetNotFoundError, ManifestValidationError

ALLOWED_FORMATS = frozenset({"PNG", "JPEG"})
MIN_ICON_PX = 512
MAX_BYTES = 2 * 1024 * 1024
ICON_DENSITIES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}
PLAY_ICON_PX = 512
SPLASH_LOGO_MAX_RATIO = 0.42
SPLASH_SIZE = (1080, 1920)


@dataclass(frozen=True)
class ImageValidation:
    width: int
    height: int
    format: str
    size_bytes: int


def validate_icon_bytes(data: bytes, *, label: str = "icon") -> ImageValidation:
    if len(data) > MAX_BYTES:
        raise ManifestValidationError(f"{label} exceeds {MAX_BYTES} bytes")
    if not data:
        raise ManifestValidationError(f"{label} is empty")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            fmt = (image.format or "").upper()
            width, height = image.size
    except Exception as exc:  # noqa: BLE001 — invalid asset must fail closed
        raise ManifestValidationError(f"{label} is not a readable image") from exc
    if fmt not in ALLOWED_FORMATS:
        raise ManifestValidationError(f"{label} format {fmt or 'unknown'} is not supported")
    if width != height:
        raise ManifestValidationError(f"{label} must be square")
    if width < MIN_ICON_PX:
        raise ManifestValidationError(f"{label} must be at least {MIN_ICON_PX}x{MIN_ICON_PX}")
    return ImageValidation(width=width, height=height, format=fmt, size_bytes=len(data))


def validate_icon_file(path: Path) -> ImageValidation:
    if not path.is_file():
        raise AssetNotFoundError(f"Branding asset not found: {path.name}")
    return validate_icon_bytes(path.read_bytes(), label=path.name)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        return (37, 99, 235)
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def generate_default_icon(*, primary_color: str, size: int = 1024) -> bytes:
    """Development/preview fallback only — never a production customer icon."""
    color = _hex_to_rgb(primary_color)
    image = Image.new("RGBA", (size, size), color + (255,))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_android_icons(source: bytes, output_res: Path) -> list[str]:
    validate_icon_bytes(source)
    written: list[str] = []
    with Image.open(io.BytesIO(source)) as image:
        rgba = image.convert("RGBA")
        for density, px in ICON_DENSITIES.items():
            folder = output_res / f"mipmap-{density}"
            folder.mkdir(parents=True, exist_ok=True)
            resized = rgba.resize((px, px), Image.Resampling.LANCZOS)
            for name in ("ic_launcher.png", "ic_launcher_round.png"):
                target = folder / name
                resized.save(target, format="PNG")
                written.append(str(target))
    return written


def write_play_store_icon(source: bytes, destination: Path) -> str:
    """512px store listing icon — must not live under android/res (breaks aapt)."""
    validate_icon_bytes(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(source)) as image:
        rgba = image.convert("RGBA")
        store = rgba.resize((PLAY_ICON_PX, PLAY_ICON_PX), Image.Resampling.LANCZOS)
        store.save(destination, format="PNG")
    return str(destination)


def generate_splash(
    *,
    background_color: str,
    logo_bytes: bytes | None,
    output_res: Path,
) -> list[str]:
    background = Image.new("RGBA", SPLASH_SIZE, _hex_to_rgb(background_color) + (255,))
    if logo_bytes:
        with Image.open(io.BytesIO(logo_bytes)) as logo:
            logo = logo.convert("RGBA")
            max_w = int(SPLASH_SIZE[0] * SPLASH_LOGO_MAX_RATIO)
            max_h = int(SPLASH_SIZE[1] * SPLASH_LOGO_MAX_RATIO)
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            x = (SPLASH_SIZE[0] - logo.width) // 2
            y = (SPLASH_SIZE[1] - logo.height) // 2
            background.alpha_composite(logo, (x, y))
    drawable = output_res / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    splash_path = drawable / "splash_brand.png"
    background.convert("RGB").save(splash_path, format="PNG")
    launch_background = drawable / "launch_background.xml"
    launch_background.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@color/splash_background" />
    <item>
        <bitmap android:gravity="center" android:src="@drawable/splash_brand" />
    </item>
</layer-list>
""",
        encoding="utf-8",
    )
    values = output_res / "values"
    values.mkdir(parents=True, exist_ok=True)
    colors = values / "splash_colors.xml"
    hex_color = background_color if background_color.startswith("#") else f"#{background_color}"
    colors.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="splash_background">{hex_color}</color>
</resources>
""",
        encoding="utf-8",
    )
    return [str(splash_path), str(launch_background), str(colors)]
