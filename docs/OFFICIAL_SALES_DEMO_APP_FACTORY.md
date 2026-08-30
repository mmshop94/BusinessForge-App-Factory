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

See also: [ANDROID_RELEASE_PIPELINE.md](ANDROID_RELEASE_PIPELINE.md) · [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md)
