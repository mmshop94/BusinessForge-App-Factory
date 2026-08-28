"""LAN vs public output channels for Official Sales Demo app artefacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from app_factory.infrastructure.paths import repo_root

CHANNEL_LAN = "lan"
CHANNEL_PUBLIC = "public"
LEGACY_DEMO_PREFIX = "demo-"


def demo_apps_root() -> Path:
    return repo_root().parent / "BusinessForge-Demo-Apps"


def channel_output_root(channel: str, *, base: Path | None = None) -> Path:
    root = base or demo_apps_root()
    if channel not in {CHANNEL_LAN, CHANNEL_PUBLIC}:
        raise ValueError(f"Unknown demo apps channel: {channel}")
    return root / channel


def _rewrite_paths(value: object, old: str, new: str) -> object:
    if isinstance(value, dict):
        return {key: _rewrite_paths(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_paths(item, old, new) for item in value]
    if isinstance(value, str):
        return value.replace(old, new)
    return value


def preserve_legacy_lan_builds(base: Path | None = None) -> Path:
    """Move legacy top-level demo-* trees into lan/ without deleting files.

    Existing LAN artefacts stay intact; public builds write to public/.
    """
    root = base or demo_apps_root()
    lan = root / CHANNEL_LAN
    if not root.is_dir():
        lan.mkdir(parents=True, exist_ok=True)
        (root / CHANNEL_PUBLIC).mkdir(parents=True, exist_ok=True)
        return lan

    legacy_dirs = sorted(
        path for path in root.iterdir() if path.is_dir() and path.name.startswith(LEGACY_DEMO_PREFIX)
    )
    if not legacy_dirs:
        lan.mkdir(parents=True, exist_ok=True)
        (root / CHANNEL_PUBLIC).mkdir(parents=True, exist_ok=True)
        return lan

    lan.mkdir(parents=True, exist_ok=True)
    (root / CHANNEL_PUBLIC).mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for src in legacy_dirs:
        dest = lan / src.name
        if dest.exists():
            raise RuntimeError(f"Refusing to overwrite preserved LAN dir: {dest}")
        shutil.move(str(src), str(dest))
        moved.append(src.name)

    extra_names = ("manifest.json", "batch-build.log", "_factory_output")
    for name in extra_names:
        src = root / name
        if not src.exists():
            continue
        dest = lan / name
        if dest.exists():
            raise RuntimeError(f"Refusing to overwrite preserved LAN path: {dest}")
        shutil.move(str(src), str(dest))

    matrix = lan / "manifest.json"
    if matrix.is_file():
        payload = json.loads(matrix.read_text(encoding="utf-8"))
        matrix.write_text(
            json.dumps(_rewrite_paths(payload, str(root), str(lan)), indent=2) + "\n",
            encoding="utf-8",
        )

    readme = lan / "README.txt"
    if not readme.is_file():
        readme.write_text(
            "LAN Official Sales Demo builds (http://192.168.178.95:8090).\n"
            "Do not delete. Public HTTPS builds live in ../public/.\n",
            encoding="utf-8",
        )
    public_readme = root / CHANNEL_PUBLIC / "README.txt"
    if not public_readme.is_file():
        public_readme.write_text(
            "Public Official Sales Demo builds (https://demo-api.bforge.de).\n"
            "LAN artefacts are preserved in ../lan/.\n",
            encoding="utf-8",
        )
    _ = moved
    return lan
