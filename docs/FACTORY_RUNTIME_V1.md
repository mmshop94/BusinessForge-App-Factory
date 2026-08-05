# Factory Runtime v1 — Qualification Record

> **Status:** ✅ Qualified  
> **Contract:** [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md) — **Approved**  
> **Build date:** 2026-08-05  
> **Report:** [../output/dorfladen-hutthurm-20260805T183453Z-build-report.json](../output/dorfladen-hutthurm-20260805T183453Z-build-report.json)

---

## Summary

| Field | Value |
|-------|-------|
| **Result** | `succeeded` |
| **Manifest** | `manifests/examples/dorfladen-hutthurm.yaml` |
| **Manifest hash** | `48087308182c04089642d94892ca1e97bdfa7932ece6d892ba534d6800facb2b` |
| **Customer App ref** | `v0.5.10` (contract adoption) |
| **Customer App commit** | `7bf318780d96d5c4d5381c2dc4823a7d2a1d784c` |
| **Tenant build version** | `1.0.0+1` |
| **Flutter SDK** | 3.44.8 (stable) |
| **Dart SDK** | 3.12.2 |
| **Java (Gradle)** | 17 (Microsoft OpenJDK 17.0.20) |
| **Duration** | 116.9 s |

---

## Artifact

| Property | Value |
|----------|-------|
| **File** | `output/dorfladen-hutthurm-app-release.apk` |
| **Size** | 52,251,934 bytes (~49.8 MiB) |
| **SHA-256** | `25ed216a0bc2091f264f240935091c377d9d0d346ab1f5e1df894df7870d1345` |
| **Application ID** | `de.bforge.dorfladenhutthurm` |
| **Application label** | `Dorfladen Hutthurm` |
| **versionName** | `1.0.0` |
| **versionCode** | `1` |

Verified via `aapt dump badging` (no emulator attached).

---

## Pipeline (executed)

```text
validate manifest          ✅
prepare workspace          ✅
apply manifest + branding  ✅
flutter pub get            ✅
flutter analyze            ✅  (--no-fatal-infos --no-fatal-warnings)
flutter test               ✅  (with full dart-define set)
flutter build apk          ✅
collect artifact + report  ✅
cleanup workspace          ✅
source integrity check     ✅
```

---

## Dart defines (applied)

```json
{
  "API_BASE_URL": "https://api.businessforge.example/api/v1",
  "APP_NAME": "Dorfladen Hutthurm",
  "BACKEND_ORIGIN": "https://api.businessforge.example",
  "PUBLIC_APP_ID": "app_01JABCDEFGHJKMNPQRSTVWXYZ0",
  "PACKAGE_ID": "village_store",
  "PACKAGE_VERSION": "v1",
  "PRIMARY_COLOR": "#8B4A2F",
  "SECONDARY_COLOR": "#F2E3D5",
  "FEATURE_VILLAGE_STORE": "true",
  "FEATURE_ORDERING": "true",
  "FEATURE_NEWS": "true",
  "FEATURE_NOTIFICATIONS": "true",
  "FEATURE_PAYMENTS": "true",
  "FEATURE_LOYALTY": "false"
}
```

---

## Regression

| Check | Result |
|-------|--------|
| Customer App source files (snapshot) unchanged by Factory | ✅ |
| Workspace removed after build | ✅ |
| No manual edits during Factory run | ✅ |
| Factory unit tests (14) | ✅ |
| Flutter unit/widget tests (97 + 6 skipped live) | ✅ |

---

## Runtime prerequisites (documented)

| Requirement | Notes |
|-------------|-------|
| **JAVA_HOME** | JVM 17+ required for Android Gradle Plugin |
| **Flutter** | 3.44.x stable, Dart ^3.12.2 |
| **Windows** | Factory workspace sets `kotlin.incremental=false` in isolated copy (cross-drive Kotlin cache) |
| **Android SDK** | As configured in Customer App `local.properties` |

---

## APK validation (static)

| Contract field | Expected | Verified |
|----------------|----------|----------|
| App name | Dorfladen Hutthurm | ✅ `application-label` |
| Application ID | de.bforge.dorfladenhutthurm | ✅ `package` |
| Version | 1.0.0+1 | ✅ versionName/versionCode |
| PUBLIC_APP_ID | embedded via dart-define | ✅ compile-time (AppConfiguration) |
| API URL | https://api.businessforge.example/api/v1 | ✅ dart-define |
| Theme colours | #8B4A2F / #F2E3D5 | ✅ dart-define → TenantTheme |
| village_store routing | FEATURE_VILLAGE_STORE | ✅ dart-define |

Device install was not performed — no emulator/device connected. Static APK inspection confirms manifest-level contract application.

---

## Approvals

| Gate | Status |
|------|--------|
| **Contract v1 Approved** | ✅ |
| **Factory Runtime v1 Approved** | ✅ |
| **Build Contract Qualified** | ✅ |

---

*Qualified build command:*

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.20.8-hotspot"
app-factory build-android manifests/examples/dorfladen-hutthurm.yaml `
  --customer-app "d:\projekte\BusinessForge FlutterApp" `
  --flutter-path "D:\projekte\tools\flutter\bin\flutter.bat" `
  --format apk
```
