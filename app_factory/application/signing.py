"""Android signing configuration from environment — never persist secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


KEYSTORE_PATH_ENV = "BF_ANDROID_KEYSTORE_PATH"
KEY_ALIAS_ENV = "BF_ANDROID_KEY_ALIAS"
STORE_PASSWORD_ENV = "BF_ANDROID_STORE_PASSWORD"
KEY_PASSWORD_ENV = "BF_ANDROID_KEY_PASSWORD"

SIGNING_CONFIGURATION_REQUIRED = "SIGNING_CONFIGURATION_REQUIRED"


@dataclass(frozen=True)
class SigningStatus:
    configured: bool
    code: str | None
    keystore_present: bool
    key_alias_set: bool

    def to_public_dict(self) -> dict[str, object]:
        return {
            "configured": self.configured,
            "code": self.code,
            "keystore_present": self.keystore_present,
            "key_alias_set": self.key_alias_set,
        }


def signing_status(*, environ: dict[str, str] | None = None) -> SigningStatus:
    env = environ if environ is not None else dict(os.environ)
    path = env.get(KEYSTORE_PATH_ENV, "").strip()
    alias = env.get(KEY_ALIAS_ENV, "").strip()
    keystore_present = bool(path) and Path(path).is_file()
    key_alias_set = bool(alias)
    passwords_set = bool(env.get(STORE_PASSWORD_ENV, "").strip())
    configured = keystore_present and key_alias_set and passwords_set
    return SigningStatus(
        configured=configured,
        code=None if configured else SIGNING_CONFIGURATION_REQUIRED,
        keystore_present=keystore_present,
        key_alias_set=key_alias_set,
    )


def gradle_release_signing_snippet() -> str:
    """Kotlin DSL that reads credentials from env at build time. No secrets in files."""
    return """
    val bfKeystorePath = System.getenv("BF_ANDROID_KEYSTORE_PATH")
    val bfKeyAlias = System.getenv("BF_ANDROID_KEY_ALIAS")
    if (!bfKeystorePath.isNullOrBlank() && !bfKeyAlias.isNullOrBlank()) {
        signingConfigs {
            create("release") {
                storeFile = file(bfKeystorePath)
                storePassword = System.getenv("BF_ANDROID_STORE_PASSWORD") ?: ""
                keyAlias = bfKeyAlias
                keyPassword = System.getenv("BF_ANDROID_KEY_PASSWORD")
                    ?: System.getenv("BF_ANDROID_STORE_PASSWORD")
                    ?: ""
            }
        }
    }
"""
