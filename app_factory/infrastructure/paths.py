from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def schema_path(name: str = "app-build-manifest-v1.json") -> Path:
    return repo_root() / "schemas" / name


def compat_path() -> Path:
    return repo_root() / "schemas" / "customer-app-compat-v1.json"


def templates_dir() -> Path:
    return repo_root() / "templates"
