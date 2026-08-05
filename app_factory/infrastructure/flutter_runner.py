from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from app_factory.domain.errors import BuildExecutionError


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class FlutterRunner:
    """Execute Flutter CLI commands in the workspace."""

    def __init__(self, flutter_executable: str = "flutter") -> None:
        self._flutter = flutter_executable

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        dart_defines: dict[str, str] | None = None,
        check: bool = True,
    ) -> CommandResult:
        command = [self._flutter, *args]
        if dart_defines:
            for key, value in sorted(dart_defines.items()):
                command.extend(["--dart-define", f"{key}={value}"])
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
        result = CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and not result.ok:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise BuildExecutionError(
                f"Command failed ({' '.join(command)}): {detail}"
            )
        return result

    def version_info(self) -> tuple[str | None, str | None]:
        try:
            flutter = self.run(["--version"], cwd=Path.cwd(), check=False)
            flutter_bin = Path(self._flutter).resolve().parent
            dart_exe = flutter_bin / ("dart.exe" if flutter_bin.joinpath("dart.exe").exists() else "dart")
            dart = subprocess.run(
                [str(dart_exe), "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return None, None
        flutter_line = flutter.stdout.splitlines()[0] if flutter.stdout else None
        dart_line = (dart.stdout or dart.stderr).strip() if dart.stdout or dart.stderr else None
        return flutter_line, dart_line

    @staticmethod
    def git_commit(path: Path) -> str | None:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        return completed.stdout.strip()
