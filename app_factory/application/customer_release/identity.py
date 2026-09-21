"""Per-customer Android application ID registry — collisions and published immutability."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_factory.application.package_identity import (
    is_reference_android_package,
    is_reserved_android_package,
    validate_android_package_format,
    validate_customer_production_application_id,
    validate_reference_application_id,
)
from app_factory.domain.errors import IdentityCollisionError, PackageMutationError


@dataclass(frozen=True)
class CustomerAppIdentityRecord:
    customer_app_id: str
    package_name_android: str
    bundle_identifier: str
    published: bool
    last_version_code: int
    package_immutable: bool = False


class CustomerAppIdentityRegistry:
    """Tracks customer app identities. File-backed for operator workspaces; in-memory for tests."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._by_app: dict[str, CustomerAppIdentityRecord] = {}
        if path and path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            for item in payload.get("records") or []:
                record = _record_from_dict(item)
                self._by_app[record.customer_app_id] = record

    def get(self, customer_app_id: str) -> CustomerAppIdentityRecord | None:
        return self._by_app.get(customer_app_id)

    def validate_and_register(
        self,
        *,
        customer_app_id: str,
        package_name_android: str,
        bundle_identifier: str,
        published: bool,
        version_code: int,
        production: bool,
    ) -> CustomerAppIdentityRecord:
        package = validate_android_package_format(package_name_android)
        if production:
            package = validate_customer_production_application_id(package)
        elif is_reference_android_package(package):
            package = validate_reference_application_id(package)
        elif is_reserved_android_package(package) and not package.startswith("de.bforge.app.u"):
            raise IdentityCollisionError(
                f"Reserved Android namespace is not allowed: {package}"
            )

        existing_app = self._by_app.get(customer_app_id)
        if existing_app is not None:
            frozen = existing_app.published or existing_app.package_immutable
            if frozen and existing_app.package_name_android != package:
                raise PackageMutationError(
                    "Published customer app must not change package_name_android"
                )
            if frozen and existing_app.bundle_identifier != bundle_identifier:
                raise PackageMutationError(
                    "Published customer app must not change bundle_identifier"
                )
            if version_code <= existing_app.last_version_code:
                raise PackageMutationError(
                    "version_code must increase strictly for a managed update"
                )

        for other in self._by_app.values():
            if other.customer_app_id == customer_app_id:
                continue
            if other.package_name_android == package:
                raise IdentityCollisionError(
                    f"Android package collides with {other.customer_app_id}: {package}"
                )

        immutable = bool(existing_app and existing_app.package_immutable) or published
        record = CustomerAppIdentityRecord(
            customer_app_id=customer_app_id,
            package_name_android=package,
            bundle_identifier=bundle_identifier,
            published=published or bool(existing_app and existing_app.published),
            last_version_code=version_code,
            package_immutable=immutable,
        )
        self._by_app[customer_app_id] = record
        self._persist()
        return record

    def freeze_play_package(self, customer_app_id: str) -> CustomerAppIdentityRecord:
        """After first successful Play package binding the applicationId is immutable."""
        existing = self._by_app.get(customer_app_id)
        if existing is None:
            raise PackageMutationError("PACKAGE_NOT_REGISTERED")
        record = CustomerAppIdentityRecord(
            customer_app_id=existing.customer_app_id,
            package_name_android=existing.package_name_android,
            bundle_identifier=existing.bundle_identifier,
            published=existing.published,
            last_version_code=existing.last_version_code,
            package_immutable=True,
        )
        self._by_app[customer_app_id] = record
        self._persist()
        return record

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "records": [
                {
                    "customer_app_id": record.customer_app_id,
                    "package_name_android": record.package_name_android,
                    "bundle_identifier": record.bundle_identifier,
                    "published": record.published,
                    "last_version_code": record.last_version_code,
                    "package_immutable": record.package_immutable,
                }
                for record in self._by_app.values()
            ]
        }
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _record_from_dict(item: dict[str, Any]) -> CustomerAppIdentityRecord:
    return CustomerAppIdentityRecord(
        customer_app_id=str(item["customer_app_id"]),
        package_name_android=str(item["package_name_android"]),
        bundle_identifier=str(item["bundle_identifier"]),
        published=bool(item.get("published")),
        last_version_code=int(item.get("last_version_code") or 0),
        package_immutable=bool(item.get("package_immutable") or item.get("published")),
    )
