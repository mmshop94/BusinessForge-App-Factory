from __future__ import annotations


class AppFactoryError(Exception):
    """Base error for app factory operations."""


class ManifestValidationError(AppFactoryError):
    """Manifest failed schema or business-rule validation."""


class ManifestSecretError(ManifestValidationError):
    """Manifest contains forbidden secret-like fields or values."""


class CompatibilityError(AppFactoryError):
    """Customer app revision is incompatible with this factory version."""


class AssetNotFoundError(AppFactoryError):
    """Referenced branding asset is missing."""


class BuildExecutionError(AppFactoryError):
    """Flutter build pipeline failed."""


class WorkspaceError(AppFactoryError):
    """Temporary workspace could not be prepared or cleaned up."""


class CustomerReleaseError(AppFactoryError):
    """Customer app release intake or snapshot failed."""


class SigningGuardError(CustomerReleaseError):
    """Production customer signing is missing or uses a forbidden shared keystore."""


class IdentityCollisionError(CustomerReleaseError):
    """Android application ID collides with another customer app."""


class PackageMutationError(CustomerReleaseError):
    """Published customer app attempted to change an immutable package ID."""


class SnapshotImmutabilityError(CustomerReleaseError):
    """An existing release snapshot was mutated or rebuilt in place."""
