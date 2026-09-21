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


class TenantIsolationError(CustomerReleaseError):
    """Tenant/app/package binding mismatch — hard block."""


class PlayDeliveryError(CustomerReleaseError):
    """Google Play test-track delivery failed without a production fallback."""


class ProductionSubmissionBlocked(PlayDeliveryError):
    """Production track writes are forbidden in this slice."""


class ApprovalError(CustomerReleaseError):
    """Test-upload approval is missing, consumed, or bound to another snapshot."""


class PlayConnectionError(PlayDeliveryError):
    """Publisher connection is not READY for the bound customer app."""


class AppleDeliveryError(CustomerReleaseError):
    """App Store Connect / TestFlight delivery failed without a production fallback."""


class AppStoreProductionSubmissionBlocked(AppleDeliveryError):
    """App Store production / App Review writes are forbidden in this slice."""


class AppleConnectionError(AppleDeliveryError):
    """App Store Connect connection is not READY for the bound customer app."""
