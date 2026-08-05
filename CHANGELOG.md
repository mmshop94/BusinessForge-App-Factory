# Changelog

All notable changes to BusinessForge App Factory are documented here.

## [0.1.0] - 2026-08-05

### Added

- Initial repository structure (`app_factory/`, `schemas/`, `manifests/`, `templates/`, `tests/`, `docs/`)
- Domain model: `AppBuildManifest`, `BuildRequest`, `BuildResult`, and related types
- JSON Schema `app-build-manifest-v1.json` with strict validation
- Customer app compatibility matrix `customer-app-compat-v1.json`
- Manifest validator with secret detection and asset checks
- Deterministic build planner with `--dart-define` mapping
- Slice 1 Android build orchestrator with isolated workspace
- Flutter config applier (pubspec version, Android applicationId, label, build_config)
- CLI: `validate`, `plan`, `build-android`, `inspect-build`
- Example manifest: `manifests/examples/dorfladen-hutthurm.yaml`
- Documentation: ARCHITECTURE, APP_MANIFEST_V1, CUSTOMER_APP_INTEGRATION, SECURITY, ROADMAP
- 14 unit tests covering validation, planning, workspace isolation, and mocked builds

### Open decisions

- Customer App must adopt documented `--dart-define` keys (`PUBLIC_APP_ID`, feature flags) — see CUSTOMER_APP_INTEGRATION.md
- Icon/splash generation from SVG is deferred; assets are copied, not rasterized in Slice 1
- iOS Bundle ID is stored in manifest but not applied until Slice 2
- Manifest sourcing from BusinessForge Backend API is planned for Slice 2

### Security

- Signing keys and store credentials are explicitly out of scope for this repository
