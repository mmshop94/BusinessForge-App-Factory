from __future__ import annotations

import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path

from app_factory.domain.errors import WorkspaceError

_IGNORE_PATTERNS = (
    ".git",
    ".dart_tool",
    "build",
    ".idea",
    ".vscode",
    "android/.gradle",
    "android/local.properties",
    "android/build",
    "android/app/build",
    "ios/Pods",
    "node_modules",
)


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for pattern in _IGNORE_PATTERNS:
        ignored.update(fnmatch.filter(names, pattern))
    return ignored


def _robocopy(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    excluded = [".git", ".dart_tool", "build", ".idea", ".vscode", "node_modules"]
    cmd = [
        "robocopy",
        str(source),
        str(destination),
        "/E",
        "/XJ",
        "/R:1",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/nc",
        "/ns",
        "/np",
    ]
    for name in excluded:
        cmd.extend(["/XD", name])
    cmd.extend(["/XF", "local.properties"])
    completed = subprocess.run(cmd, check=False)
    if completed.returncode >= 8:
        raise WorkspaceError(f"robocopy failed with exit code {completed.returncode}")


class WorkspaceManager:
    """Creates isolated temporary copies of the customer app."""

    def __init__(self, workspace_path: Path) -> None:
        self._workspace_path = workspace_path

    @property
    def path(self) -> Path:
        return self._workspace_path

    def prepare(self, customer_app_path: Path) -> Path:
        if not customer_app_path.is_dir():
            raise WorkspaceError(f"Customer app path does not exist: {customer_app_path}")
        if self._workspace_path.exists():
            self.cleanup()
        self._workspace_path.parent.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            _robocopy(customer_app_path, self._workspace_path)
        else:
            shutil.copytree(
                customer_app_path,
                self._workspace_path,
                ignore=_copy_ignore,
                dirs_exist_ok=False,
            )
        marker = self._workspace_path / "build_config" / ".app_factory_workspace"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("generated-by=businessforge-app-factory\n", encoding="utf-8")
        return self._workspace_path

    def cleanup(self) -> None:
        if self._workspace_path.exists():
            shutil.rmtree(self._workspace_path, ignore_errors=True)

    @staticmethod
    def assert_source_unmodified(source_path: Path, before_snapshot: dict[str, str]) -> None:
        """Ensure the original customer app working copy was not mutated."""
        for rel, digest in before_snapshot.items():
            current = source_path / rel
            if not current.is_file():
                raise WorkspaceError(f"Source file missing after build: {rel}")
            from app_factory.infrastructure.hashing import sha256_file

            if sha256_file(current) != digest:
                raise WorkspaceError(f"Source file modified after build: {rel}")

    @staticmethod
    def snapshot_files(source_path: Path, relative_paths: list[str]) -> dict[str, str]:
        from app_factory.infrastructure.hashing import sha256_file

        snapshot: dict[str, str] = {}
        for rel in relative_paths:
            path = source_path / rel
            if path.is_file():
                snapshot[rel] = sha256_file(path)
        return snapshot
