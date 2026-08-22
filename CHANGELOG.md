# Changelog

All notable changes to BusinessForge App Factory are documented here.

## [Unreleased]

### Added

- Wave 1 store-ready pipeline: native Android icons/splash, package identity `de.bforge.app.u{ulid}`, signing foundation (env only), build result JSON
- CLI: `signing-status`, `materialize-export`
- Docs: [ANDROID_RELEASE_PIPELINE.md](docs/ANDROID_RELEASE_PIPELINE.md)
- Tests: `tests/test_wave1_store_ready.py`
- Dorfladen #1 pilot manifest: `manifests/dorfladen-1-pilot.yaml` + production export JSON
- Qualified APK build against `api.bforge.de` (`output/dorfladen-hutthurm-app-release.apk`)

### Changed

- Privacy inventory (Backend): IONOS Domain/DNS/Mail + first-party Demo-Leads; Formspree removed; Plausible remains PLANNED. See [PRIVACY_INVENTORY_REPORT.md](../BusinessForge/docs/privacy/PRIVACY_INVENTORY_REPORT.md).
- DSAR/Privacy Foundation (Backend 2026-08-14): Customer self-service export, tenant/platform DSAR tools, controlled erasure. See [DATA_SUBJECT_RIGHTS.md](../BusinessForge/docs/privacy/DATA_SUBJECT_RIGHTS.md). Customer App needs rebuild for `/account/privacy`.
- Commercial Self-Service Foundation (Backend 2026-08-14): App Delivery Jobs are Backend/Super-Admin queues. Factory remains manual CLI — payment does not publish to stores. See [APP_DELIVERY_LIFECYCLE.md](../BusinessForge/docs/commercial/APP_DELIVERY_LIFECYCLE.md).
- Commercial Feature Audit (2026-08-14): White-label classified FUNCTIONAL — native icon/splash + signing gaps (GAP-001/002). See [FEATURE_READINESS_MATRIX.md](../BusinessForge/docs/commercial/FEATURE_READINESS_MATRIX.md).
- Standard requalification (2026-08-14): White-Label **SOFTWARE_READY**; missing Owner-Keystore is `OPERATIONAL_BLOCKER: ANDROID_SIGNING_MATERIAL`; missing customer icon is `TENANT_INPUT_REQUIRED`. See [STANDARD_EDITION_READINESS.md](../BusinessForge/docs/commercial/STANDARD_EDITION_READINESS.md), [ANDROID_RELEASE_PIPELINE.md](docs/ANDROID_RELEASE_PIPELINE.md).
- Transactional Mail (Backend 2026-08-14): generic SMTP adapter, fail-closed production. IONOS Mail Basic is not an approved transactional provider. See [TRANSACTIONAL_MAIL.md](../BusinessForge/docs/operations/TRANSACTIONAL_MAIL.md).

### Notes

- Rechtstexte sind Runtime-Daten der Customer App (Bootstrap / Public Legal API). Die Factory backt keine Tenant- oder Platform-Rechtstexte in die APK.
- Legal Activation: [LEGAL_COMPLIANCE_V1.md](../BusinessForge/docs/architecture/LEGAL_COMPLIANCE_V1.md), [LEGAL_READINESS_REPORT.md](../BusinessForge/docs/pilot/LEGAL_READINESS_REPORT.md).
- Datenschutz-Inventur (IST, Backend): [PRIVACY_INVENTORY_REPORT.md](../BusinessForge/docs/privacy/PRIVACY_INVENTORY_REPORT.md) — keine Policy/AVV-Texte.
- Production security hardening (2026-08-14): Flutter JWT in secure storage; Factory APK must be rebuilt after Customer App pull.


## [0.1.1] - 2026-08-05

### Added

- **Contract qualification** — full Android pipeline against Customer App `v0.5.10` ([FACTORY_RUNTIME_V1.md](docs/FACTORY_RUNTIME_V1.md))
- [COMPATIBILITY_MATRIX.md](docs/COMPATIBILITY_MATRIX.md) — qualified toolchain and define matrix
- Kotlin incremental disabled in workspace only (`kotlin.incremental=false`) for cross-drive Windows builds
- Flutter/Dart version capture in build reports via `dart.exe` adjacent to Flutter SDK

### Changed

- [CUSTOMER_APP_BUILD_CONTRACT_V1.md](docs/CUSTOMER_APP_BUILD_CONTRACT_V1.md) — **Approved** (qualified 2026-08-05)
- `flutter analyze` uses `--no-fatal-infos --no-fatal-warnings` in pipeline
- Removed `flutter clean` from pipeline (Windows symlink/Developer Mode issue)

### Fixed

- `BuildOrchestrator` — restore `mark_finished(SUCCEEDED)` on successful builds

## [0.1.0] - 2026-08-05

### Added

- GitHub repository [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory) on branch `main`
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
