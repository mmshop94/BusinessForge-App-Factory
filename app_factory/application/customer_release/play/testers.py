"""Internal tester group references — no private emails in git, no invented opt-in URLs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app_factory.application.customer_release.signing import SecretReferenceResolver
from app_factory.domain.errors import TenantIsolationError

TESTER_GROUP_NOT_CONFIGURED = "TESTER_GROUP_NOT_CONFIGURED"
TESTER_GROUP_READY = "TESTER_GROUP_READY"
TESTER_ACCESS_VERIFIED = "TESTER_ACCESS_VERIFIED"


@dataclass(frozen=True)
class InternalTesterGroupReference:
    tenant_id: str
    customer_app_id: str
    group_reference: str
    status: str = TESTER_GROUP_NOT_CONFIGURED
    opt_in_url: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "tenant_id": self.tenant_id,
            "customer_app_id": self.customer_app_id,
            "group_reference": self.group_reference,
            "status": self.status,
            "kind": "InternalTesterGroupReference",
        }
        if self.opt_in_url:
            payload["opt_in_url"] = self.opt_in_url
        return payload


def resolve_tester_group(
    resolver: SecretReferenceResolver,
    *,
    tenant_id: str,
    customer_app_id: str,
    group_reference: str,
    provider_opt_in_url: str = "",
    access_verified: bool = False,
) -> InternalTesterGroupReference:
    if not tenant_id or not customer_app_id:
        raise TenantIsolationError("Tester group requires tenant and customer app")
    if not group_reference.strip():
        return InternalTesterGroupReference(
            tenant_id=tenant_id,
            customer_app_id=customer_app_id,
            group_reference="",
            status=TESTER_GROUP_NOT_CONFIGURED,
        )
    present = resolver.has(
        group_reference,
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
    )
    if not present:
        return InternalTesterGroupReference(
            tenant_id=tenant_id,
            customer_app_id=customer_app_id,
            group_reference=group_reference,
            status=TESTER_GROUP_NOT_CONFIGURED,
        )
    status = TESTER_ACCESS_VERIFIED if access_verified else TESTER_GROUP_READY
    # Opt-in URL only when the provider actually returned one. Never synthesize.
    return InternalTesterGroupReference(
        tenant_id=tenant_id,
        customer_app_id=customer_app_id,
        group_reference=group_reference,
        status=status,
        opt_in_url=provider_opt_in_url.strip(),
    )
