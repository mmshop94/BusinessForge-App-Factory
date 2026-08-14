# Customer App Integration — Implementation Notes

> **Canonical contract:** [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md)  
> **Customer App:** [BusinessForge-FlutterApp](https://github.com/mmshop94/BusinessForge-FlutterApp)  
> **Factory version:** 0.1.0  
> **Compat version:** 1

This document describes **Slice 1 implementation details**. For the binding build contract (inputs, outputs, allowed mutations, defines, toolchain), see **CUSTOMER_APP_BUILD_CONTRACT_V1.md**.

---

## Principle

The App Factory **must not** perform arbitrary search-and-replace across Dart source code. Integration happens through:

1. **`--dart-define` compile-time constants**
2. **Documented native file patch points**
3. **Generated `build_config/` files** (informational + future codegen)
4. **Copied branding assets** under `assets/branding/`

---

## Dart defines (build time)

The factory passes these `--dart-define` values to `flutter build` and `flutter test`:

| Define | Source | Status in Customer App |
|--------|--------|------------------------|
| `API_BASE_URL` | `manifest.api_base_url` | ✅ Implemented ([app_config.dart](../../BusinessForge%20FlutterApp/lib/config/app_config.dart)) |
| `BACKEND_ORIGIN` | manifest or derived | ✅ Implemented |
| `PUBLIC_APP_ID` | `manifest.tenant.public_app_id` | ⏳ **Required adoption** — replace dev `DEV_TENANT_ID` for production bootstrap |
| `APP_PACKAGE` | `manifest.tenant.package` | ⏳ Planned — package-aware navigation |
| `APP_PACKAGE_VERSION` | `manifest.tenant.package_version` | ⏳ Planned |
| `BRAND_THEME` | `manifest.branding.theme` | ⏳ Optional build-time default before runtime `/branding` |
| `BRAND_PRIMARY_COLOR` | manifest | ⏳ Optional build-time seed |
| `BRAND_SECONDARY_COLOR` | manifest | ⏳ Optional build-time seed |
| `FEATURE_<NAME>` | `manifest.features` | ⏳ Planned — compile-time feature gates |

### Required Customer App change (next slice)

Extend `AppConfig.fromEnvironment()`:

```dart
const publicAppId = String.fromEnvironment('PUBLIC_APP_ID');
// Use publicAppId for tenant bootstrap API instead of DEV_TENANT_ID in release builds.
```

**No secret tenant keys** in the client — only the public `app_id`. Mandant resolution remains server-side.

Legal documents are **not** a factory concern: the Customer App loads published tenant texts at runtime via bootstrap / `GET /public/apps/{public_app_id}/legal`. Do not inject imprint, privacy, or terms into generated Dart or native files.

---

## Native patch points

The factory modifies **only** these files in the isolated workspace:

| File | Change |
|------|--------|
| `pubspec.yaml` | `version: {app_version}+{build_number}` |
| `android/app/build.gradle.kts` | `applicationId` |
| `android/app/src/main/AndroidManifest.xml` | `android:label` |
| `assets/branding/*` | Copied from manifest asset paths |

### Not modified in Slice 1

- Kotlin `MainActivity` package path / directory structure
- iOS `Info.plist` / bundle identifier
- Firebase configuration files
- ProGuard rules

**Open decision:** Android `namespace` and Kotlin package path still use `com.businessforge.businessforge_mobile`. Changing Application ID without relocating `MainActivity` is valid for Android — document for store review.

---

## Generated files

Written to `{workspace}/build_config/`:

| File | Purpose |
|------|---------|
| `app_factory_config.json` | Full manifest subset for tooling/debug |
| `dart_defines.json` | Exact defines used for the build |
| `.app_factory_workspace` | Marker that directory is ephemeral |

These files are **gitignored** in the Customer App and must never be committed from production builds.

---

## Stable asset paths (future)

When the Customer App adopts build-time branding, it should read from:

```text
assets/branding/logo.*
assets/branding/icon.*
assets/branding/splash.*
```

Runtime branding via `GET /branding` remains authoritative after first launch — build-time branding covers splash/icon/store listing only.

---

## Compatibility matrix

See [schemas/customer-app-compat-v1.json](../schemas/customer-app-compat-v1.json).

| Package | Min Customer App | Supported refs (Slice 1) |
|---------|------------------|--------------------------|
| `village_store` | 0.5.0 | `v0.5.9`, `main`, `feat/village-store-pilot` |
| `restaurant` | 0.5.0 | `v0.5.9`, `main` |

The factory rejects builds when `source.customer_app_ref` is not listed for the tenant package.

---

## Quality gates

When executing a full build (not `--dry-run`), the factory runs:

```text
flutter pub get
flutter analyze
flutter test --dart-define=...
flutter build apk|appbundle --release --dart-define=...
```

Customer App tests must pass **without modification** in the isolated workspace.

---

## Verification checklist

- [ ] `app-factory validate` passes for tenant manifest
- [ ] `app-factory plan` shows expected dart-defines and steps
- [ ] Source Customer App working copy unchanged after build
- [ ] Build report contains commit hash and artifact SHA-256
- [ ] Generated APK shows correct label and applicationId

---

## References

- **Build contract (canonical):** [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md)
- Customer App white-label architecture: [WHITE_LABEL.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/architecture/WHITE_LABEL.md)
- Runtime branding: [BRANDING.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/architecture/BRANDING.md)
- Multi-tenant model: [MULTI_TENANT.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/architecture/MULTI_TENANT.md)
