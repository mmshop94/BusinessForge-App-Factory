from __future__ import annotations

from enum import Enum


class BuildStatus(str, Enum):
    """Lifecycle state of a build execution."""

    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AndroidArtifactFormat(str, Enum):
    APK = "apk"
    AAB = "aab"
