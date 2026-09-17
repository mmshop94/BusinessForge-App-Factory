# Official Sales Demo App Factory — Batch Builds V1

> **Stand:** 2026-08-30  
> **Authority:** BusinessForge App Factory (`app-factory`)  
> **Customer App:** `BusinessForge FlutterApp` @ `main` (isolated worktree recommended)  
> **Demo plane (LAN):** `http://192.168.178.95:8090/api/v1` (LAN artefacts preserved under `lan/`)  
> **Public API (LIVE):** `https://demo-api.bforge.de/api/v1` · Demo API `0.8.79`  
> **Latest public rebuild:** Push Device Registration V3-02 — **11/11** APK+AAB; API `https://demo-api.bforge.de/api/v1`; Production origin absent; LAN origin absent in public artefacts. FCM `google-services.json` remains Factory Slice 3 (`PROVIDER_CONFIGURATION_REQUIRED` for delivery; harness registration READY).

## Goal

Build **11 independent Android apps** (one per Official Sales Demo `demo-*`) from the **same** Flutter Customer App via factory configuration — no source forks, no copied Flutter projects.

## Authorities

| Concern | Authority |
|---------|-----------|
| App Factory | `app-factory` CLI · `BuildOrchestrator` |
| White-label config | Per-tenant `manifest.yaml` under output root |
| Android package ID | `de.bforge.app.u{public_app_ulid}` from `public_app_id` |
| App name / icons / splash | Manifest + demo bootstrap + public hero media |
| API target | Manifest `api_base_url` — LAN default or `--public-api` → `https://demo-api.bforge.de/api/v1` |
| Signing | Env vars only (`BF_ANDROID_*`) — never in Git |
| Output | `D:\projekte\BusinessForge-Demo-Apps\public\` (`--public-api`) or `...\lan\` (LAN). Legacy top-level `demo-*` trees are moved into `lan/` without overwrite. |

## Official Sales Demos (11)

Includes `demo-restaurant`, `demo-village-store`, and nine appointment sales demos (`demo-hairdresser` … `demo-pet-grooming`).

**Excluded:** `test-appointment-*` technical fixtures · `demo-workshop` (not provisioned).

**Service Engine (2026-09-09):** Official batch remains **11/11** (restaurant, village store, nine appointment demos). There is **no** certified Service APK. `service_first` exists as Flutter design template; factory cannot build a Service sales app until a Service demo/test tenant is separately authorized. Certification authority: BusinessForge [SERVICE_ENGINE_CERTIFICATION_BASELINE_V1.md](../../BusinessForge/docs/architecture/SERVICE_ENGINE_CERTIFICATION_BASELINE_V1.md). Reference vertical `AUTO_WORKSHOP` — **not** in this 11/11 set. Legacy Workshop excluded.

## Batch entry point

```powershell
cd D:\projekte\BusinessForge App_Generator
pip install -e ".[dev]"

# Manifests + assets only (read-only demo plane discovery)
app-factory build-official-sales-demos --manifest-only

# LAN batch (writes to BusinessForge-Demo-Apps/lan/)
app-factory build-official-sales-demos --skip-tests --skip-analyze

# Public HTTPS batch (writes to BusinessForge-Demo-Apps/public/)
# --public-api sets API_BASE_URL=https://demo-api.bforge.de/api/v1 (fail-closed)
app-factory build-official-sales-demos --public-api --skip-tests --skip-analyze

# Single demo
app-factory build-official-sales-demos --slug demo-hairdresser --skip-tests --skip-analyze
```

Wrapper script: `scripts/build_official_sales_demo_apps.py`

## Output layout

```text
BusinessForge-Demo-Apps/
├── lan/                          # preserved LAN HTTP artefacts
│   ├── README.txt
│   ├── manifest.json
│   └── demo-*/
└── public/                       # HTTPS demo-api.bforge.de artefacts
    ├── README.txt
    ├── manifest.json
    └── demo-restaurant/
        ├── manifest.yaml
        ├── branding/
        ├── metadata/
        │   ├── app.json
        │   └── play_store.json
        ├── apk/
        └── aab/
```

Do not delete or overwrite `lan/`. Public rebuilds must not land in the same folder as LAN APKs.

## Build types

| Type | Purpose |
|------|---------|
| **LOCAL/INTERNAL DEMO BUILD** | LAN HTTP demo API · cleartext allowed · debug or env signing |
| **PLAY-READY CONFIGURATION** | Unique `applicationId`, release APK/AAB, store metadata scaffold |
| **ACTUAL PUBLIC STORE RELEASE** | Requires HTTPS demo/public API, privacy policy URL, release keystore, store creatives |

**Public HTTPS:** `demo-api.bforge.de` is **LIVE**. `--public-api` fail-closes on `http://`, LAN IPs, `:8090`, `localhost`, `127.0.0.1`, and Production `api.bforge.de` (token-aware so `demo-api.bforge.de` is not a production hit). After each APK/AAB copy the factory scans Dart snapshot / Flutter assets and `app_factory_config.json`. Artefact scan treats `192.168.*` / `:8090` as fail; leftover Flutter dev defaults (`http://127.0.0.1:8000`) in the Dart snapshot are not LAN API origins. LAN APKs in `lan/` remain valid LAN proof.

### AAB on Windows

Flutter may exit with `failed to strip debug symbols from native libraries` when Android NDK/cmdline-tools are incomplete. If `build/app/outputs/bundle/release/*.aab` is still produced, the factory treats the build as succeeded and copies the bundle. For clean toolchain output, install Android SDK Command-line Tools, accept licenses (`flutter doctor --android-licenses`), and install NDK.

## Signing

```powershell
app-factory signing-status
```

Production Play upload requires `BF_ANDROID_KEYSTORE_PATH`, `BF_ANDROID_KEY_ALIAS`, `BF_ANDROID_STORE_PASSWORD`, `BF_ANDROID_KEY_PASSWORD` in the environment. Never commit keystore material.

## Rebuild

1. Ensure demo plane reachable and `.env.demo` contains `BF_DEMO_OWNER_PASSWORD` (BusinessForge repo, gitignored).
2. Use clean Customer App checkout: `git worktree add ../BusinessForge-FlutterApp-main main`
3. Run batch command above.
4. Verify `BusinessForge-Demo-Apps/public/manifest.json` (or `lan/`) and per-app `metadata/app.json`.

## Do not commit

- `BusinessForge-Demo-Apps/`
- `output/` APK/AAB/workspace artifacts
- `.env.demo` / keystore files
- Demo owner passwords in manifests or docs

## Architecture guards

```text
SECOND APP FACTORY: NO
SECOND BRANDING ENGINE: NO
11 COPIED FLUTTER PROJECTS: NO
HARDCODED DEMO PASSWORDS: NO
SAME APP CODE AS REAL WHITE LABEL: YES
DEMO-SPECIFIC DOMAIN CODE: NONE
```

Demos are factory configuration (branding, package id, `public_app_id`, API origin). Customer App checkout: `BusinessForge-FlutterApp-main`.

Commerce age restriction is a **shared** store capability (operator pickup + local-delivery handoff verification). No `winery@v1` / `delivery_age@v1` / alcohol app package is required for App Factory reuse — see [COMMERCE_ROADMAP_V1.md](COMMERCE_ROADMAP_V1.md).

Commerce delivery / shipping fulfillment is also a **shared** Commerce capability.
`APP_FACTORY_FULFILLMENT_REUSE: READY`; no `shipping@v1` or `delivery@v1`
package is required. This documentation freeze does not add an official demo or
generate an app, so the official sales-demo batch remains **11/11**.

Commerce online payment (tenant Connect card) is likewise a **shared** Commerce
capability. `APP_FACTORY_ONLINE_PAYMENT_REUSE: READY`; no `stripe@v1` or
`payment@v1` package is required. Demos remain **11/11**; no app generation.

Variable-measure / scale barcodes are a **shared** Commerce backend capability
(configurable schemes + PLU + MEASURED cart path). 
`APP_FACTORY_VARIABLE_MEASURE_REUSE: READY`; no `scale@v1` or
`variable-barcode@v1` package. No Flutter customer change required for this
slice. Direct scale hardware remains out of scope.

Commerce accounting export (sales journal + Generic CSV + DATEV-oriented
EXTF adapter) is a **shared** Backend/Dashboard capability.
`APP_FACTORY_ACCOUNTING_REUSE: READY`; no `accounting@v1` or `datev@v1`
customer-app package. DATEV official certification is not claimed.

Commerce food ingredient / allergen labeling is a **shared** Backend + Customer
App product-detail capability (published food information only).
`APP_FACTORY_FOOD_INFORMATION_REUSE: READY`; no `food@v1` or `allergen@v1`
package. Full LMIV / distance-selling food compliance is **NOT_CERTIFIED**.
Demos remain **11/11**; no app generation in this freeze.

Commerce meat origin / provenance is a **shared** Backend + Customer App
product-detail capability (published provenance declaration only).
`APP_FACTORY_PROVENANCE_REUSE: READY`; no `meat-origin@v1` or `provenance@v1`
package. Full meat labelling legal compliance is **NOT_CERTIFIED**.
Demos remain **11/11**; no app generation in this freeze.

Commerce food batch / MHD / use-by / traceability is a **shared** Backend +
Customer App capability (published date/lot declaration only when lot known).
`APP_FACTORY_TRACEABILITY_REUSE: READY`; no `expiry@v1`, `batch@v1`, or
`traceability@v1` package. Cold-chain remains out of scope.
Demos remain **11/11**; no app generation in this freeze.

Commerce food recall / withdrawal management is a **shared** Backend + Customer
App capability (operator workflow + customer-safe order notices).
`APP_FACTORY_RECALL_REUSE: READY`; no `recall@v1` or `food-safety@v1` package.
Authority API / RASFF / lebensmittelwarnung.de remain out of scope.
Demos remain **11/11**; no app generation in this freeze.

Commerce lot-level inventory / FEFO is a **shared** Backend capability
(lot balances + FEFO allocation on LOT_TRACKED products).
`APP_FACTORY_LOT_INVENTORY_REUSE: READY`; no `inventory-lot@v1` or `fefo@v1`
package. Multi-lot line split / auto reallocation remain out of scope.
Demos remain **11/11**; no app generation in this freeze.

Commerce nutrition declaration is a **shared** Backend + Customer App
capability (published Annex XV presentation; checkout gate server-side).
`APP_FACTORY_NUTRITION_REUSE: READY`; no `nutrition@v1` package.
Vitamins/minerals remain PARTIAL_OPTIONAL; wine sector override remains
PARTIAL_SECTOR_OVERRIDE. Full LMIV nutrition compliance not certified.
Demos remain **11/11**; no app generation in this freeze.

Commerce POS / operator counter checkout is a **shared** Backend capability
(cash tender, commercial receipt, fiscalization port).
`APP_FACTORY_POS_REUSE: READY`; no `pos@v1` package.
Certified TSE remains NOT_IMPLEMENTED; DSFinV-K and integrated payment
terminal remain OUT_OF_SCOPE_V1; Flutter POS operator NOT_REQUIRED.
German POS production fiscal readiness is NOT_READY — never claim
KassenSichV / TSE / GoBD compliance from App Factory demos.
Demos remain **11/11**; no app generation in this freeze.

See also: [ANDROID_RELEASE_PIPELINE.md](ANDROID_RELEASE_PIPELINE.md) · [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md)
