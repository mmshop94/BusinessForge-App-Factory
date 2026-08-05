# Customer App Build Contract v1

> **Contract version:** 1  
> **Status:** ✅ **Approved** — qualified 2026-08-05 ([FACTORY_RUNTIME_V1.md](FACTORY_RUNTIME_V1.md))  
> **Factory repo:** [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory)  
> **Customer App repo:** [BusinessForge-FlutterApp](https://github.com/mmshop94/BusinessForge-FlutterApp)  
> **Manifest schema:** [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md)  
> **Stand:** 2026-08-05

---

## 1. Purpose

This document defines the **stable integration contract** between:

- **BusinessForge App Factory** — build orchestration, manifest application, artifact production
- **BusinessForge Customer App** — single generic Flutter codebase (runtime product)

```text
App Factory
    │
    ├── Which Customer App revision?
    ├── Which configuration files may be touched?
    ├── Which assets are injected?
    ├── Which build commands are run?
    ├── Which placeholders / defines are set?
    └── Which artifacts must be produced?
            │
            ▼
    Reproducible White-Label Build
```

**Goal:** Both repositories evolve independently. The Factory must not break when the Customer App adds features — as long as this contract is honoured. The Customer App must not embed factory or signing logic.

**Non-goals (Contract v1):** Play Store upload, iOS builds, automatic publishing, tenant Git forks.

---

## 2. Contract parties and version axes

Three independent version numbers exist. They must **not** be coupled.

| Axis | Example | Owner | Meaning |
|------|---------|-------|---------|
| **Customer App** | `v0.5.9` | Flutter repo | Product features, UI, API client behaviour |
| **Build Contract** | `v1` | This document + compat matrix | Allowed patch points, defines, artifacts |
| **App Factory** | `v0.1.0` | Factory repo | Generator, validator, pipeline implementation |
| **Tenant App Build** | `1.0.0+12` | Manifest `release.*` | One published white-label build for one tenant |

### Compatibility rule

A build is valid only when:

```text
manifest.schema_version == 1
AND manifest.source.factory_compat_version == "1"
AND customer_app_ref is listed in customer-app-compat-v1.json for tenant.package
AND factory_version supports the contract version
```

Reference: [schemas/customer-app-compat-v1.json](../schemas/customer-app-compat-v1.json)

---

## 3. Build input

Every Factory build consumes exactly four input groups.

### 3.1 Customer App revision

| Field | Source | Required |
|-------|--------|----------|
| Git ref | `manifest.source.customer_app_ref` | yes — tag, branch, or commit SHA |
| Resolved commit | Factory records at build time | output in build report |
| Checkout path | CLI `--customer-app` or `manifest.source.customer_app_repo` | yes |

The Factory copies the Customer App into an **isolated workspace**. The source working copy must remain **unchanged** after the build.

**Pinning policy:**

- **Production tenant builds:** immutable Git tag (e.g. `v0.5.9`)
- **Pilot / dev builds:** branch or commit allowed, must be listed in compat matrix

### 3.2 Tenant App Manifest

YAML or JSON conforming to [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md).

| Section | Purpose |
|---------|---------|
| `app` | Identity — name, Android Application ID, iOS Bundle ID (stored) |
| `tenant` | Public app ID, business package slug, package version |
| `branding` | Theme profile, colours, asset paths |
| `features` | Boolean feature flags |
| `release` | Semver, build number, channel |
| `source` | Customer App ref + factory compat version |
| `api_base_url` | Backend API entry point |

**Manifest hash** (SHA-256 of canonical JSON) is recorded in every build report.

**Secrets are forbidden** in manifests — see [SECURITY.md](SECURITY.md).

### 3.3 Branding assets

Paths are **relative to the manifest directory**.

| Asset | Manifest key | Required | Formats (v1) |
|-------|--------------|----------|--------------|
| Logo | `branding.logo_asset` | yes | SVG, PNG |
| Splash | `branding.splash_asset` | no | PNG |
| App icon source | `branding.icon_asset` | no | PNG (SVG → rasterization in Factory Slice 2) |

Factory copies assets into the workspace at:

```text
{workspace}/assets/branding/
```

The Customer App **must** declare this path in `pubspec.yaml` once contract adoption is complete (Slice 2 Customer App task).

### 3.4 Target platform and build profile

| Input | Values (Contract v1) | Default |
|-------|----------------------|---------|
| **Target platform** | `android` | `android` |
| **Artifact format** | `apk`, `aab` | `apk` |
| **Build profile** | `release` | `release` |
| **Run analyze** | `true`, `false` | `true` |
| **Run tests** | `true`, `false` | `true` |
| **Dry run** | `true`, `false` | `false` |

iOS (`ipa`) is reserved for Contract v2 — fields may be present in manifest but are not applied in v1.

---

## 4. Build output

Every successful Factory build produces:

### 4.1 Primary artifacts

| Artifact | Path pattern | When |
|----------|--------------|------|
| **APK** | `output/{app_id}-app-release.apk` | `--format apk` |
| **AAB** | `output/{app_id}-app-release.aab` | `--format aab` |

Both are release builds. Debug artifacts are out of scope for tenant builds.

### 4.2 Build report (mandatory)

JSON file: `output/{app_id}-{timestamp}-build-report.json`

| Field | Purpose |
|-------|---------|
| `status` | `planned`, `succeeded`, `failed` |
| `manifest_hash` | Reproducibility |
| `customer_app_commit` | Exact source revision |
| `flutter_version`, `dart_version` | Toolchain fingerprint |
| `artifacts[].sha256` | Integrity verification |
| `artifacts[].size_bytes` | Storage / transfer |
| `started_at`, `finished_at`, `duration_seconds` | Audit |
| `steps[]` | Pipeline trace |
| `error_message` | Present on failure |

CLI: `app-factory inspect-build <report>`

### 4.3 Logs

Stdout/stderr of each pipeline step are captured in `steps[]` (summary). Full Flutter logs remain in CI runner output — not committed to the repository.

### 4.4 Version embedded in artifact

```text
pubspec version = {release.app_version}+{release.build_number}
```

Example: manifest `1.0.0` + build `12` → `1.0.0+12` in APK/AAB metadata.

---

## 5. Toolchain requirements

The Factory runner must satisfy:

| Tool | Minimum (Contract v1) | Notes |
|------|----------------------|-------|
| **Flutter SDK** | `3.24.x` stable channel | Record exact version in build report |
| **Dart SDK** | `^3.12.2` (matches Customer App `pubspec.yaml`) | Bundled with Flutter |
| **Android SDK** | API level per Customer App `compileSdk` | Factory does not pin independently |
| **Java** | 17 | Matches `android/app/build.gradle.kts` |
| **Python** | 3.9+ | Factory CLI only |

**Customer App baseline:** tag `v0.5.9` — Dart `^3.12.2`, no explicit Flutter pin in repo (Factory records resolved Flutter at build time).

**Policy:** Production builds use a **pinned Flutter version** in CI (to be added in Factory Slice 2 GitHub Actions template). Local builds record whatever `flutter --version` returns.

---

## 6. Configuration surface — allowed mutations

The Factory may modify **only** the following locations in the **isolated workspace**. Everything else is read-only.

### 6.1 Flutter / Dart configuration

| Location | Mutation | Manifest source |
|----------|----------|-----------------|
| `pubspec.yaml` → `version` | `{app_version}+{build_number}` | `release.*` |
| `--dart-define` at build/test | see §7 | manifest fields |

### 6.2 Android native (Contract v1)

| File | Field | Manifest source |
|------|-------|-----------------|
| `android/app/build.gradle.kts` | `applicationId` | `app.package_name_android` |
| `android/app/src/main/AndroidManifest.xml` | `android:label` | `app.display_name` |

**Explicitly not mutated in v1:**

| File | Reason |
|------|--------|
| `android/app/build.gradle.kts` → `namespace` | Kotlin path stability |
| `MainActivity.kt` package path | Requires refactor — Contract v2 candidate |
| `ic_launcher` mipmaps | Icon rasterization pipeline — Slice 2 |
| `launch_background.xml` | Splash injection — Slice 2 |
| `google-services.json` | Per-tenant Firebase — Slice 3 |

### 6.3 iOS native (Contract v1)

**No mutations.** `app.bundle_id_ios` is stored in manifest and build report for forward compatibility.

Contract v2 will add: `Info.plist` display name, bundle identifier, asset catalog icons.

### 6.4 Generated files (Factory-owned)

Written to `{workspace}/build_config/` — **never committed** in Customer App repo:

| File | Purpose |
|------|---------|
| `app_factory_config.json` | Normalized manifest subset |
| `dart_defines.json` | Exact defines used |
| `.app_factory_workspace` | Ephemeral workspace marker |

Contract v2 target: Customer App reads `app_factory_config.json` via `AppConfiguration.load()` — see §8.

### 6.5 Branding assets (injected)

| Workspace path | Source |
|----------------|--------|
| `assets/branding/logo.*` | `branding.logo_asset` |
| `assets/branding/splash.*` | `branding.splash_asset` (optional) |
| `assets/branding/icon.*` | `branding.icon_asset` (optional) |

---

## 7. Compile-time placeholders (`--dart-define`)

The Factory passes defines to `flutter test` and `flutter build`. Keys are **stable API** — Customer App must read them via a single entry point (§8).

### 7.1 Required defines (Contract v1 target)

| Define | Type | Manifest source | Customer App status |
|--------|------|-----------------|---------------------|
| `API_BASE_URL` | string (URI) | `api_base_url` | ✅ implemented |
| `BACKEND_ORIGIN` | string (URI) | `backend_origin` or derived | ✅ implemented |
| `PUBLIC_APP_ID` | string | `tenant.public_app_id` | ⏳ adoption required |

### 7.2 Package defines (Contract v1 target)

| Define | Type | Manifest source | Customer App status |
|--------|------|-----------------|---------------------|
| `APP_PACKAGE` | string | `tenant.package` | ⏳ adoption required |
| `APP_PACKAGE_VERSION` | string | `tenant.package_version` | ⏳ adoption required |

### 7.3 Branding seed defines (optional build-time defaults)

| Define | Type | Manifest source | Customer App status |
|--------|------|-----------------|---------------------|
| `BRAND_THEME` | string | `branding.theme` | ⏳ optional |
| `BRAND_PRIMARY_COLOR` | string (hex) | `branding.primary_color` | ⏳ optional |
| `BRAND_SECONDARY_COLOR` | string (hex) | `branding.secondary_color` | ⏳ optional |

Runtime branding via `GET /branding` remains **authoritative after first launch**. Build-time values seed splash / cold start only.

### 7.4 Feature flags

For each `features.{name}: bool` in manifest:

```text
--dart-define=FEATURE_{NAME_UPPER}={true|false}
```

Example: `ordering: true` → `FEATURE_ORDERING=true`

Customer App gates compile-time routes/modules on these defines. **No runtime secret flags.**

### 7.5 Dev-only defines (Factory must NOT set in tenant builds)

| Define | Purpose |
|--------|---------|
| `DEV_TENANT_ID` | Local dev login — **absent** in production builds |
| `DEV_CUSTOMER_ID` | Live tests only |
| `RUN_LIVE_*_TEST` | Test harness only |

---

## 8. Customer App configuration entry point

### 8.1 Current state (Slice 1)

```dart
AppConfig.fromEnvironment()
```

Location: `lib/config/app_config.dart` — reads `API_BASE_URL`, `BACKEND_ORIGIN`, `DEV_TENANT_ID`.

### 8.2 Target state (Contract v1 adoption — Customer App Slice 2)

Single entry point for all build-time configuration:

```dart
/// Unified build-time + optional file-based configuration.
abstract final class AppConfiguration {
  static AppConfiguration load() {
    // 1. Try build_config/app_factory_config.json (asset/bundled)
    // 2. Fall back to String.fromEnvironment(...) for each field
    // 3. Never read secret values
  }
}
```

**Rules:**

- All Factory defines are consumed **only** through `AppConfiguration.load()`
- No scattered `String.fromEnvironment` in feature modules
- `PUBLIC_APP_ID` replaces `DEV_TENANT_ID` for release/bootstrap flows
- Widgets and business logic **never** parse manifest or JSON directly

### 8.3 Configuration precedence

```text
1. build_config/app_factory_config.json   (Factory-generated, bundled asset)
2. --dart-define                          (compile-time override)
3. Sensible dev defaults                  (local flutter run only)
```

---

## 9. Forbidden mutations

The Factory **must never**:

| Forbidden action | Reason |
|------------------|--------|
| Edit Dart files under `lib/` | Business logic belongs to Customer App |
| Edit widgets, routes, repositories | Same |
| Search-and-replace across source tree | Fragile, unmaintainable |
| Inject tenant secrets or signing keys | Security boundary |
| Commit workspace changes back to Customer App repo | Isolation |
| Create permanent per-tenant Git repositories | Architecture principle |
| Modify `lib/` test files to make build pass | Quality gate integrity |

If a tenant-specific behaviour is needed, it must be expressed via **manifest feature flags** or **package capability** — implemented once in the Customer App.

---

## 10. Build pipeline and commands

### 10.1 Pipeline (Contract v1)

```text
validate manifest
    ↓
resolve customer app @ ref
    ↓
snapshot source integrity hashes
    ↓
copy → isolated workspace
    ↓
apply configuration (§6) + assets (§3.3)
    ↓
flutter pub get
    ↓
flutter analyze                    [skippable via profile]
    ↓
flutter test --dart-define=...     [skippable via profile]
    ↓
flutter build apk|appbundle --release --dart-define=...
    ↓
collect artifact + SHA-256
    ↓
write build report
    ↓
cleanup workspace
    ↓
assert source checkout unchanged
```

### 10.2 Exact commands

```bash
flutter pub get

flutter analyze

flutter test \
  --dart-define=API_BASE_URL=... \
  --dart-define=PUBLIC_APP_ID=... \
  # ... all defines from §7

flutter build apk --release \
  --dart-define=API_BASE_URL=... \
  # ... same define set

# or

flutter build appbundle --release \
  --dart-define=...
```

Defines must be **identical** between `flutter test` and `flutter build` for the same build request.

### 10.3 Factory CLI mapping

| CLI command | Contract operation |
|-------------|-------------------|
| `app-factory validate <manifest>` | Input validation only |
| `app-factory plan <manifest>` | Deterministic plan, no side effects |
| `app-factory build-android <manifest>` | Full pipeline §10.1 |
| `app-factory inspect-build <report>` | Output inspection |

---

## 11. Configuration mapping reference

Quick reference: manifest field → mutation target.

| Manifest field | Output |
|----------------|--------|
| `app.display_name` | Android `android:label` |
| `app.package_name_android` | Gradle `applicationId` |
| `app.bundle_id_ios` | Report only (v1) |
| `release.app_version` + `release.build_number` | `pubspec.yaml` version |
| `api_base_url` | `API_BASE_URL` define |
| `backend_origin` | `BACKEND_ORIGIN` define |
| `tenant.public_app_id` | `PUBLIC_APP_ID` define |
| `tenant.package` | `APP_PACKAGE` define |
| `tenant.package_version` | `APP_PACKAGE_VERSION` define |
| `branding.theme` | `BRAND_THEME` define |
| `branding.primary_color` | `BRAND_PRIMARY_COLOR` define |
| `branding.secondary_color` | `BRAND_SECONDARY_COLOR` define |
| `branding.logo_asset` | `assets/branding/` |
| `features.*` | `FEATURE_*` defines |

---

## 12. Change management

### 12.1 Customer App changes that do NOT require Factory updates

- New screens, widgets, API clients
- Runtime branding improvements
- Bug fixes without moving contract patch points
- New package modules gated by existing `FEATURE_*` pattern

### 12.2 Customer App changes that REQUIRE contract / Factory update

| Change | Action |
|--------|--------|
| Move `applicationId` out of `build.gradle.kts` | Bump contract, update Factory applier |
| Rename `app_config.dart` or config API | Update define documentation + Factory |
| Change minimal Dart SDK | Update §5 toolchain table + compat matrix |
| Add new build-time config field | Add to manifest schema + §7 defines |
| Restructure Android manifest path | Bump contract version |

### 12.3 Contract version bump procedure

```text
1. Document changes in CUSTOMER_APP_BUILD_CONTRACT_V2.md
2. Add factory_compat_version "2" to manifest schema
3. Update customer-app-compat-v2.json
4. Factory supports v1 and v2 during transition window
5. Customer App tags a release declaring v2 support
```

---

## 13. Acceptance criteria

A build satisfies Contract v1 when all checks pass:

- [ ] Manifest validates against schema v1 with no secrets
- [ ] Customer App ref approved in compat matrix for tenant package
- [ ] Source Customer App checkout byte-identical to pre-build snapshot
- [ ] Only §6 paths modified in workspace
- [ ] `flutter analyze` exits 0 (unless profile skips)
- [ ] `flutter test` exits 0 with full define set (unless profile skips)
- [ ] APK or AAB produced with correct `applicationId` and label
- [ ] Build report contains manifest hash, commit SHA, artifact SHA-256
- [ ] No `DEV_TENANT_ID` define present in release build plan

---

## 14. Long-term platform flow

This contract is the static boundary between dynamic platform provisioning and deterministic client builds.

```text
BusinessForge Backend
        │
        ├── Tenant, Package, Branding (runtime)
        └── App Configuration (export)
                │
                ▼
        Provisioning / Dashboard
                │
                ▼
        Tenant App Manifest (versioned)
                │
                ▼
BusinessForge App Factory          ← this contract
        │
        ├── validate
        ├── workspace
        ├── apply config + assets
        └── flutter build
                │
                ▼
BusinessForge Customer App (template @ pinned ref)
                │
                ▼
        APK / AAB + Build Report
                │
                ▼
        Play Store (Contract v3+ — out of scope here)
```

**Operational benefit:** A new customer requires **no Flutter developer** — only a manifest, branding assets, and an approved Customer App tag.

---

## 15. Open decisions

| Topic | Status | Target |
|-------|--------|--------|
| `AppConfiguration.load()` implementation | Planned | Customer App Slice 2 |
| Android launcher icon mipmaps | Deferred | Factory Slice 2 |
| Splash screen native injection | Deferred | Factory Slice 2 |
| iOS patch points | Deferred | Contract v2 |
| Pinned Flutter in CI | Deferred | Factory Slice 2 |
| `build_config` as bundled Flutter asset | Planned | Customer App Slice 2 |
| Rename repo to `BusinessForge-Customer-App` | Optional | Cosmetic |

---

## 16. Related documents

| Document | Relationship |
|----------|--------------|
| [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md) | Manifest input schema |
| [CUSTOMER_APP_INTEGRATION.md](CUSTOMER_APP_INTEGRATION.md) | Slice 1 implementation notes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Factory internal design |
| [SECURITY.md](SECURITY.md) | Secrets and signing boundary |
| [ROADMAP.md](ROADMAP.md) | Slice planning |
| Customer App [WHITE_LABEL.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/architecture/WHITE_LABEL.md) | Product-side white-label vision |

---

*Contract v1 is the gate for Factory Slice 2 implementation. No Slice 2 code until Customer App adoption tasks in §7–§8 are scheduled and compat matrix is updated.*
