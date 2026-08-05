# Compatibility Matrix v1

> **Status:** Qualified with Customer App `v0.5.10`  
> **Machine-readable:** [schemas/customer-app-compat-v1.json](../schemas/customer-app-compat-v1.json)  
> **Contract:** [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md)

---

## Version axes

| Component | Version | Tag / ref |
|-----------|---------|-----------|
| **Build Contract** | v1 | Approved 2026-08-05 |
| **App Factory** | v0.1.1 | Runtime qualified |
| **Customer App** | v0.5.10 | Contract adoption |
| **Manifest schema** | 1 | `app-build-manifest-v1.json` |
| **Example tenant build** | 1.0.0+1 | Dorfladen Hutthurm |

---

## Customer App ↔ Factory compatibility

| Package | Min Customer App | Qualified refs | Factory defines |
|---------|------------------|----------------|-----------------|
| `village_store` | 0.5.10 | `v0.5.10`, `main`, `feat/build-contract-v1` | `FEATURE_VILLAGE_STORE`, `PACKAGE_ID=village_store` |
| `restaurant` | 0.5.10 | `v0.5.10`, `main` | `FEATURE_RESTAURANT_MENU`, `PACKAGE_ID=restaurant` |

---

## Toolchain matrix (qualified run)

| Tool | Required | Qualified with |
|------|----------|----------------|
| Flutter | 3.24+ stable | **3.44.8** |
| Dart | ^3.12.2 | **3.12.2** |
| Java | 17+ | **Microsoft OpenJDK 17.0.20** |
| Python (Factory) | 3.9+ | 3.12 |
| Android compileSdk | per Customer App | 36 |

---

## Dart-define contract (v1)

| Define | Required (release) | Customer App reader |
|--------|-------------------|---------------------|
| `PUBLIC_APP_ID` | yes | `AppConfiguration.fromDartDefines()` |
| `API_BASE_URL` | yes | `AppConfiguration` |
| `BACKEND_ORIGIN` | no | `AppConfiguration` |
| `PACKAGE_ID` | yes | `AppConfiguration` |
| `PACKAGE_VERSION` | yes | `AppConfiguration` |
| `APP_NAME` | yes | `AppConfiguration` |
| `PRIMARY_COLOR` | no | `TenantTheme.fromConfiguration()` |
| `SECONDARY_COLOR` | no | `TenantTheme.fromConfiguration()` |
| `FEATURE_*` | package-dependent | `FeatureConfiguration` |

Factory aliases still accepted: `APP_PACKAGE`, `BRAND_PRIMARY_COLOR`, etc.

---

## Qualification evidence

- Build report: `output/dorfladen-hutthurm-20260805T183453Z-build-report.json`
- Runtime doc: [FACTORY_RUNTIME_V1.md](FACTORY_RUNTIME_V1.md)
- Customer App: [BUILD_CONTRACT_REFERENCED.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/BUILD_CONTRACT_REFERENCED.md)

---

## Upgrade policy

1. Bump Customer App minor → update `min_customer_app_version` and `supported_customer_app_refs`
2. Add define or patch point → bump Build Contract to v2
3. Factory-only pipeline fix → Factory patch version (no Customer App change)
