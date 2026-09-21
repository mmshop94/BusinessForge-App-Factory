"""macOS / Xcode build executor contract. Windows must not pretend to archive an IPA."""

from __future__ import annotations

import platform
import shutil
import sys
from typing import Any

IOS_BUILD_EXECUTOR_REQUIRED = "IOS_BUILD_EXECUTOR_REQUIRED"
LOCAL_MACOS = "LOCAL_MACOS"
CI_MACOS = "CI_MACOS"
EXTERNAL_MACOS = "EXTERNAL_MACOS"
NOT_AVAILABLE = "NOT_AVAILABLE"

SUPPORTED_XCODE_MAJOR = (15, 16)


def probe_ios_build_executor(*, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Machine-readable executor probe. Never reports IOS_BUILD_FAILED for a missing Mac."""
    del environ
    is_macos = sys.platform == "darwin" or platform.system() == "Darwin"
    xcodebuild = shutil.which("xcodebuild") if is_macos else None
    flutter = shutil.which("flutter")
    pod = shutil.which("pod") if is_macos else None
    if not is_macos:
        return {
            "status": IOS_BUILD_EXECUTOR_REQUIRED,
            "provider": None,
            "macos": False,
            "xcode": NOT_AVAILABLE,
            "flutter_sdk": "VERIFIED" if flutter else "ACTION_REQUIRED",
            "cocoapods": NOT_AVAILABLE,
            "keychain": NOT_AVAILABLE,
            "export_tooling": NOT_AVAILABLE,
            "fake_ipa_pass": False,
            "notes": [
                "This workspace is not macOS. Store IPAs cannot be produced here.",
                "Reuse an existing macOS runner later; do not invent paid CI in this slice.",
            ],
        }
    xcode_ok = bool(xcodebuild)
    return {
        "status": "LOCAL_MACOS_AVAILABLE" if xcode_ok else IOS_BUILD_EXECUTOR_REQUIRED,
        "provider": LOCAL_MACOS if xcode_ok else None,
        "macos": True,
        "xcode": "VERIFIED" if xcode_ok else "ACTION_REQUIRED",
        "flutter_sdk": "VERIFIED" if flutter else "ACTION_REQUIRED",
        "cocoapods": "VERIFIED" if pod else "ACTION_REQUIRED",
        "keychain": "ACTION_REQUIRED",
        "export_tooling": "VERIFIED" if xcode_ok else "ACTION_REQUIRED",
        "fake_ipa_pass": False,
        "notes": [],
    }
