"""Tests — backend store selection SoT mapping."""

from __future__ import annotations

import pytest

from app_factory.application.customer_release.backend_selection import (
    from_backend_store_selection,
    selection_implies_publication,
)
from app_factory.application.customer_release.platforms import PlatformSelection


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        ("NONE", None),
        ("GOOGLE_PLAY", PlatformSelection.ANDROID_ONLY),
        ("APPLE_APP_STORE", PlatformSelection.IOS_ONLY),
        ("BOTH", PlatformSelection.ANDROID_AND_IOS),
    ],
)
def test_backend_mapping(backend: str, expected: PlatformSelection | None) -> None:
    assert from_backend_store_selection(backend) is expected


def test_selection_not_publication() -> None:
    assert selection_implies_publication() is False
