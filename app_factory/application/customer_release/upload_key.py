"""Upload-key public record — certificate fingerprint only, never private key material."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_factory.application.customer_release.signing import (
    SHARED_OWNER_KEYSTORE_FORBIDDEN,
    looks_like_shared_owner_reference,
)
from app_factory.domain.errors import SigningGuardError

PLAY_APP_SIGNING_ENROLLED = "ENROLLED"
PLAY_APP_SIGNING_UNKNOWN = "UNKNOWN"
PLAY_APP_SIGNING_NOT_ENROLLED = "NOT_ENROLLED"


@dataclass(frozen=True)
class UploadKeyRecord:
    customer_app_id: str
    upload_key_reference: str
    certificate_sha256: str
    status: str
    play_app_signing_status: str

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "customer_app_id": self.customer_app_id,
            "upload_key_reference": self.upload_key_reference,
            "certificate_sha256": self.certificate_sha256,
            "status": self.status,
            "play_app_signing_status": self.play_app_signing_status,
            "role": "UPLOAD_KEY",
            "app_signing_key": "PLAY_APP_SIGNING",
        }
        blob = str(payload).lower()
        for marker in ("-----begin", "private", ".jks", "password"):
            if marker in blob:
                raise SigningGuardError("Upload key public record leaked private material")
        return payload


def assert_not_owner_upload_key(reference: str) -> None:
    if looks_like_shared_owner_reference(reference):
        raise SigningGuardError(SHARED_OWNER_KEYSTORE_FORBIDDEN)


def certificate_sha256_from_keystore(
    keystore_path: Path,
    *,
    alias: str,
    store_unlock: str,
) -> str:
    """Public fingerprint only. store_unlock is used in-process and never returned."""
    assert_not_owner_upload_key(str(keystore_path))
    completed = subprocess.run(
        [
            "keytool",
            "-list",
            "-v",
            "-keystore",
            str(keystore_path),
            "-alias",
            alias,
            "-storepass",
            store_unlock,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    text = f"{completed.stdout}\n{completed.stderr}"
    match = re.search(r"SHA256:\s*([0-9A-F:]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).replace(":", "").lower()
    digest = hashlib.sha256(keystore_path.read_bytes()).hexdigest()
    return f"keystore-bytes-{digest[:16]}"


def create_ephemeral_upload_keystore(
    path: Path,
    *,
    alias: str,
    store_unlock: str,
    dname: str = "CN=CustomerUpload,O=BusinessForgeTest,C=DE",
) -> str:
    """Test-only keystore. Never commit the file. Returns certificate SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    completed = subprocess.run(
        [
            "keytool",
            "-genkeypair",
            "-keystore",
            str(path),
            "-alias",
            alias,
            "-storepass",
            store_unlock,
            "-keypass",
            store_unlock,
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "3650",
            "-dname",
            dname,
            "-storetype",
            "PKCS12",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not path.is_file():
        raise SigningGuardError(
            "UPLOAD_KEYSTORE_CREATE_FAILED"
        )
    return certificate_sha256_from_keystore(path, alias=alias, store_unlock=store_unlock)
