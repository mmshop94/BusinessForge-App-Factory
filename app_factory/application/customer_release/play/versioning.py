"""Monotonic Play versionCode — reuse local build until Google already knows it."""

from __future__ import annotations


def resolve_play_version_code(*, built: int, google_known: int | None) -> int:
    """Reuse `built` when Google has not seen it. Otherwise next monotonic value.

    No random jumps. versionCode 1 is reused only when Google does not know it yet.
    """
    local = int(built)
    if local < 1:
        local = 1
    known = int(google_known or 0)
    if known <= 0:
        return local
    if local > known:
        return local
    return known + 1
