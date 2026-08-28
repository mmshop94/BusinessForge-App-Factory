# Official Sales Demo App Factory — Batch Builds V1

> **Stand:** 2026-08-28  
> **Authority:** BusinessForge App Factory (`app-factory`)  
> **Customer App:** `BusinessForge FlutterApp` @ `main` (isolated worktree recommended)  
> **Demo plane (LAN):** `http://192.168.178.95:8090/api/v1` · API ≥ `0.8.67`  
> **Public API (LIVE):** `https://demo-api.bforge.de/api/v1`

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
| Output | `D:\projekte\BusinessForge-Demo-Apps\` (outside repos, gitignored) |

## Official Sales Demos (11)

Includes `demo-restaurant`, `demo-village-store`, and nine appointment sales demos (`demo-hairdresser` … `demo-pet-grooming`).

**Excluded:** `test-appointment-*` technical fixtures · `demo-workshop` (not provisioned).

## Batch entry point

```powershell
cd D:\projekte\BusinessForge App_Generator
pip install -e ".[dev]"

# Manifests + assets only (read-only demo plane discovery)
app-factory build-official-sales-demos --manifest-only

# Full batch (APK + AAB per demo) — LAN until public TLS exists
app-factory build-official-sales-demos --skip-tests --skip-analyze

# After demo-api.bforge.de HTTPS is live (do not discard LAN APKs)
app-factory build-official-sales-demos --public-api --skip-tests --skip-analyze

# Single demo
app-factory build-official-sales-demos --slug demo-hairdresser --skip-tests --skip-analyze
```

Wrapper script: `scripts/build_official_sales_demo_apps.py`

## Output layout

```text
BusinessForge-Demo-Apps/
├── manifest.json
├── demo-restaurant/
│   ├── manifest.yaml
│   ├── branding/
│   ├── metadata/
│   │   ├── app.json
│   │   └── play_store.json
│   ├── apk/
│   └── aab/
└── …
```

## Build types

| Type | Purpose |
|------|---------|
| **LOCAL/INTERNAL DEMO BUILD** | LAN HTTP demo API · cleartext allowed · debug or env signing |
| **PLAY-READY CONFIGURATION** | Unique `applicationId`, release APK/AAB, store metadata scaffold |
| **ACTUAL PUBLIC STORE RELEASE** | Requires HTTPS demo/public API, privacy policy URL, release keystore, store creatives |

**Release gap:** Public HTTPS `demo-api.bforge.de` is **LIVE**. Rebuild 11 apps with `--public-api` so APK/AAB no longer contain `192.168.178.95:8090`. LAN APKs remain valid proof.

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
4. Verify `BusinessForge-Demo-Apps/manifest.json` and per-app `metadata/app.json`.

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
```

See also: [ANDROID_RELEASE_PIPELINE.md](ANDROID_RELEASE_PIPELINE.md) · [APP_MANIFEST_V1.md](APP_MANIFEST_V1.md)
