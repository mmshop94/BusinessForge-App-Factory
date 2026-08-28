# Android Release Pipeline — White-Label Store Foundation

> **Stand:** 2026-08-14  
> **Repository:** BusinessForge App Factory  
> **Google Play Publication:** **MANUAL_OPERATION** — keine Play-API-Automatisierung

Die Factory bleibt die einzige Generator-Architektur. Super Admin stößt **keine** Remote-Code-Execution und **keine** Shell aus HTTP-Input an.

---

## Operator flow

```text
App Delivery Job (Backend)
        ↓  Super Admin: Generation vorbereiten
Validated Build Manifest + optional base64 assets
        ↓  operator command (statisch)
app-factory materialize-export export.json --output-dir ./work
app-factory build-android ./work/manifest.json
        ↓
Public Build Result JSON (no secrets / no local secret paths)
        ↓  Super Admin: Build-Result import
Delivery Job status: review_required | failed
        ↓  MANUAL
Google Play Console submission
```

---

## Package identity

- Authority: Backend + Factory, derived from `public_app_id`
- Format: `de.bforge.app.u{ulid26_lower}`
- Deterministic, unique, collision-checked
- **Immutable** after `submitted` / `store_review` / `published`
- Slug-based IDs such as `de.bforge.customer.slug` are **rejected**

---

## Native icon

Tenant branding icon → Delivery export → Factory → Android mipmaps (mdpi–xxxhdpi) + Play 512.

Validation: PNG/JPEG, square, min 512×512, max 2 MB.

Production channel: missing/invalid customer icon is **`TENANT_INPUT_REQUIRED`**, not a missing platform feature. BusinessForge default icon is **development/preview only**.

---

## Native splash

Static splash from primary branding color + optional raster logo (PNG/JPEG/WebP). SVG is skipped for raster splash. No animation.

---

## Signing foundation

Environment / private storage only — never Git, DB plaintext, logs, or build reports:

| Variable | Purpose |
|----------|---------|
| `BF_ANDROID_KEYSTORE_PATH` | Keystore file reference |
| `BF_ANDROID_KEY_ALIAS` | Key alias |
| `BF_ANDROID_STORE_PASSWORD` | Store password |
| `BF_ANDROID_KEY_PASSWORD` | Key password |

If unset: status **`SIGNING_CONFIGURATION_REQUIRED`** / **`OPERATIONAL_BLOCKER: ANDROID_SIGNING_MATERIAL`**. The signing **pipeline is SOFTWARE_READY**; signed production APKs wait for operator keystore. Missing keystore is not a platform feature gap.

CLI: `app-factory signing-status`

---

## AppBuildReadiness

Result `READY` or `BLOCKED` plus `requirements[]`. Super Admin sees why a build cannot start (tenant, public_app_id, vertical, template, name, package identity, branding, icon, splash source, API env, signing).

Signing/API env are reported even when not blocking export preparation.

---

## Build Manifest (schema_version 1)

Includes `delivery_job_id`, tenant/public app, vertical, template, display name, package identity, branding, asset references, API base, `build_target`, `generated_at`. **No secrets.** Incompatible schema versions are rejected by the Factory.

---

## Build Result

Public fields only: `delivery_job_id`, `build_id`, `status` (`success` | `failed` | `validation_failed`), artifact type, version/versionCode, package identity, `created_at`, validation results, error category.

Secret-like keys/paths are rejected. Results map onto the delivery job; they cannot be assigned to a foreign job/tenant.

---

## Store lifecycle (documentable, not automated)

`configuration_pending` → `ready_for_generation` → `generation_queued` → `generating` → `review_required` → `ready_for_submission` → `submitted` → `store_review` → `published` | `rejected` | `failed`

Documentable: `submitted_at`, `store`, `store_listing_reference`, `store_review_status`, `rejection_reason`, `published_at`. No Play credentials stored.

## Official Sales Demo artefacts

Official Sales Demo APK/AAB are **not** Play uploads. Channels:

| Channel | Root | API |
|---------|------|-----|
| LAN | `BusinessForge-Demo-Apps/lan/` | `http://192.168.178.95:8090/api/v1` |
| Public | `BusinessForge-Demo-Apps/public/` | `https://demo-api.bforge.de/api/v1` |

`--public-api` is fail-closed. See [OFFICIAL_SALES_DEMO_APP_FACTORY.md](OFFICIAL_SALES_DEMO_APP_FACTORY.md).

