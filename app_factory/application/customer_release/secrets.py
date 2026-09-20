"""Tenant-scoped secret resolver — production fail-closed, no owner-keystore fallback."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from app_factory.application.customer_release.signing import MappingSecretResolver
from app_factory.domain.errors import SigningGuardError, TenantIsolationError

OWNER_FALLBACK_MARKERS = (
    "BF_ANDROID_KEYSTORE_PATH",
    "ops://owner/",
    "shared-owner",
    "owner-keystore",
)


class ScopedSecretResolver:
    """Secrets are keyed by (tenant_id, customer_app_id, reference). Cross-tenant = HARD BLOCK."""

    def __init__(self) -> None:
        self._vault: dict[tuple[str, str], dict[str, str]] = {}

    def put(self, tenant_id: str, customer_app_id: str, reference: str, value: str) -> None:
        if any(marker in reference for marker in OWNER_FALLBACK_MARKERS):
            raise SigningGuardError("SHARED_OWNER_KEYSTORE_FORBIDDEN")
        bucket = self._vault.setdefault((tenant_id, customer_app_id), {})
        bucket[reference] = value

    def has(self, reference: str, *, tenant_id: str = "", customer_app_id: str = "") -> bool:
        if not tenant_id or not customer_app_id:
            return False
        return reference in self._vault.get((tenant_id, customer_app_id), {})

    def resolve_value(
        self,
        reference: str,
        *,
        tenant_id: str,
        customer_app_id: str,
    ) -> str:
        if any(marker in reference for marker in OWNER_FALLBACK_MARKERS):
            raise SigningGuardError("SHARED_OWNER_KEYSTORE_FORBIDDEN")
        bucket = self._vault.get((tenant_id, customer_app_id))
        if bucket is None or reference not in bucket:
            raise TenantIsolationError(
                f"Secret reference not bound to tenant={tenant_id} app={customer_app_id}"
            )
        return bucket[reference]


class OpsDirSecretResolver:
    """Existing ops layout: {root}/{tenant_id}/{customer_app_id}/{file}. Missing dir = fail-closed."""

    def __init__(self, root: Path | None) -> None:
        self._root = root

    def has(self, reference: str, *, tenant_id: str = "", customer_app_id: str = "") -> bool:
        path = self._resolve_path(reference, tenant_id=tenant_id, customer_app_id=customer_app_id)
        return path is not None and path.is_file()

    def resolve_value(
        self,
        reference: str,
        *,
        tenant_id: str,
        customer_app_id: str,
    ) -> str:
        if any(marker in reference for marker in OWNER_FALLBACK_MARKERS):
            raise SigningGuardError("SHARED_OWNER_KEYSTORE_FORBIDDEN")
        path = self._resolve_path(reference, tenant_id=tenant_id, customer_app_id=customer_app_id)
        if path is None or not path.is_file():
            raise SigningGuardError("SIGNING_CONFIGURATION_REQUIRED")
        return path.read_text(encoding="utf-8").strip()

    def _resolve_path(
        self,
        reference: str,
        *,
        tenant_id: str,
        customer_app_id: str,
    ) -> Path | None:
        if self._root is None or not tenant_id or not customer_app_id:
            return None
        if not reference.startswith("ops://"):
            return None
        name = reference[len("ops://") :].replace("\\", "/").split("/")[-1]
        if not name or ".." in name:
            return None
        candidate = self._root / tenant_id / customer_app_id / name
        try:
            candidate.resolve().relative_to(self._root.resolve())
        except ValueError:
            return None
        return candidate


def ops_secret_root_from_env(environ: Mapping[str, str] | None = None) -> Path | None:
    env = environ if environ is not None else dict(os.environ)
    raw = env.get("BF_OPS_SECRET_DIR", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


def production_secret_resolver(
    *,
    environ: Mapping[str, str] | None = None,
    mapping: Mapping[str, str] | None = None,
) -> MappingSecretResolver | ScopedSecretResolver | OpsDirSecretResolver:
    """Fixture mapping is test-only. Production without ops dir stays fail-closed at call sites."""
    if mapping is not None:
        return MappingSecretResolver(mapping)
    root = ops_secret_root_from_env(environ)
    if root is not None:
        return OpsDirSecretResolver(root)
    return ScopedSecretResolver()
