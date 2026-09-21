"""Per-customer Android + iOS identity registry — collisions and published immutability."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from pathlib import Path

from app_factory.application.package_identity import (
    is_reference_android_package,
    is_reference_ios_bundle,
    is_reserved_android_package,
    validate_android_package_format,
    validate_customer_production_application_id,
    validate_customer_production_bundle_id,
    validate_ios_bundle_format,
    validate_reference_application_id,
    validate_reference_ios_bundle_id,
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
    bundle_immutable: bool = False


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
        ios_production: bool = False,
    ) -> CustomerAppIdentityRecord:
        package = validate_android_package_format(package_name_android)
        if production:
            package = validate_customer_production_application_id(package)
        elif is_reference_android_package(package) and not is_reference_ios_bundle(package):
            package = validate_reference_application_id(package)
        elif is_reserved_android_package(package) and not package.startswith("de.bforge.app.u"):
            if not is_reference_ios_bundle(package):
                raise IdentityCollisionError(
                    f"Reserved Android namespace is not allowed: {package}"
                )

        bundle = validate_ios_bundle_format(bundle_identifier)
        if ios_production:
            bundle = validate_customer_production_bundle_id(bundle)
        elif is_reference_ios_bundle(bundle):
            bundle = validate_reference_ios_bundle_id(bundle)
        elif is_reference_android_package(bundle):
            bundle = validate_ios_bundle_format(bundle)
        elif is_reserved_android_package(bundle) and not bundle.startswith("de.bforge.app.u"):
            raise IdentityCollisionError(
                f"Reserved iOS namespace is not allowed: {bundle}"
            )

        existing_app = self._by_app.get(customer_app_id)
        if existing_app is not None:
            package_frozen = (
                existing_app.published or existing_app.package_immutable
            )
            bundle_frozen = existing_app.published or existing_app.bundle_immutable
            if package_frozen and existing_app.package_name_android != package:
                raise PackageMutationError(
                    "Published customer app must not change package_name_android"
                )
            if bundle_frozen and existing_app.bundle_identifier != bundle:
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
            if other.bundle_identifier == bundle:
                raise IdentityCollisionError(
                    f"iOS bundle collides with {other.customer_app_id}: {bundle}"
                )

        immutable_pkg = bool(existing_app and existing_app.package_immutable) or published
        immutable_bundle = bool(existing_app and existing_app.bundle_immutable) or published
        record = CustomerAppIdentityRecord(
            customer_app_id=customer_app_id,
            package_name_android=package,
            bundle_identifier=bundle,
            published=published or bool(existing_app and existing_app.published),
            last_version_code=version_code,
            package_immutable=immutable_pkg,
            bundle_immutable=immutable_bundle,
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
            bundle_immutable=existing.bundle_immutable,
        )
        self._by_app[customer_app_id] = record
        self._persist()
        return record

    def freeze_apple_bundle(self, customer_app_id: str) -> CustomerAppIdentityRecord:
        """After first successful App Store Connect bind the bundle ID is immutable."""
        existing = self._by_app.get(customer_app_id)
        if existing is None:
            raise PackageMutationError("BUNDLE_NOT_REGISTERED")
        record = CustomerAppIdentityRecord(
            customer_app_id=existing.customer_app_id,
            package_name_android=existing.package_name_android,
            bundle_identifier=existing.bundle_identifier,
            published=existing.published,
            last_version_code=existing.last_version_code,
            package_immutable=existing.package_immutable,
            bundle_immutable=True,
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
                    "bundle_immutable": record.bundle_immutable,
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
        bundle_immutable=bool(item.get("bundle_immutable") or item.get("published")),
    )
