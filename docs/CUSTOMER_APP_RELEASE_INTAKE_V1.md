# Customer App Release Intake + Android Signing Foundation V1

> Stand: 2026-09-20 · **SOFTWARE FOUNDATION** · no Play upload · no iOS IPA · no secrets in git  
> Companion (historical audit, unchanged): BusinessForge `WHITE_LABEL_APP_STORE_DELIVERY_READINESS_V1.md`

```text
tenant current state
        ↓
immutable release snapshot
        ↓
AppFactory apply (shared Flutter workspace)
        ↓
customer Android release candidate (AAB path reserved)
```

Official generate path **35/35 is retained**. This layer sits **on top** of `AppBuildManifest` v1. Demo artefacts still use `de.bforge.app.u{ulid}`. Production customer apps must not.

## CustomerAppReleaseProfile

Canonical object (no secret values):

| Group | Fields |
|-------|--------|
| Identity | `tenant_id`, `app_id`, `public_app_id`, `vertical`, `journey` |
| Release | `release_id`, `release_version`, `version_code`, `release_snapshot_id` |
| Stores | `display_name`, `package_name`, `bundle_identifier` |
| Platforms | `ANDROID_ONLY` / `IOS_ONLY` / `ANDROID_AND_IOS` |
| Branding | logo, app icon, splash, colours, `icon_origin=customer_provided` |
| Legal | privacy / imprint / support URL + email (customer-owned HTTPS) |
| Store | short/full description, category, locale, screenshot + feature-graphic paths |
| Capabilities | feature flags (journeys) — not catalog rows |
| Signing | **references only** (`ops://`, `env://`, `fixture://`) |
| Content | `has_customer_offerings` — live tenant data, not baked into the APK |

CLI: `app-factory prepare-customer-release intake.json --output-dir ./work`

## Release snapshot

`freeze_snapshot` writes `snapshots/snap_{hash16}.json` with `snapshot_hash`. Tampering fails closed. A later tenant edit does **not** rewrite an existing snapshot. New binary → new `release_id` / new snapshot.

## Platform selectivity

Unbooked platform status is **`NOT_SUBSCRIBED`**, never `FAILED` / `BLOCKED`.

An Android-only customer is not blocked by missing Apple setup. iOS identity/signing/setup-contract are modelled; live archive/TestFlight stay `BLOCKED_EXTERNAL` without macOS + Apple credentials. iOS-only customers cannot become `STORE_RELEASE_READY` until signing + executor + TestFlight are wired.

## Readiness gates

`CONTENT_READY` · `BRANDING_READY` · `LEGAL_READY` · `UNIQUENESS_READY` · `ANDROID_CONFIG_READY` · `ANDROID_SIGNING_READY` · `ANDROID_ASSETS_READY` (+ iOS counterparts `NOT_SUBSCRIBED` or `BLOCKED`).

Overall: `STORE_RELEASE_READY` only for **booked** platforms that are all `READY`.

Android blockers: valid name, unique non-reserved `applicationId`, production customer icon, HTTPS privacy + imprint (not `bforge.de` generics), support contact, real tenant content, no demo/placeholder store copy, per-customer signing refs, asset manifest complete.

Legal URLs are **never invented**.

## Uniqueness foundation

Deterministic signals (no similarity percentage): tenant identity, branding, real content, legal identity, vertical/journey, capabilities, store metadata, store assets.

Blocks: demo name, demo/monogram logo, placeholder store text, missing offerings, generic BF legal identity.

`similarity` is reserved (`status: RESERVED`) for a later cross-app engine.

## Android identity

| Channel | applicationId |
|---------|----------------|
| Official demo / generate | `de.bforge.app.u{ulid}` from `public_app_id` |
| Customer production | customer reverse-DNS, **not** reserved (`de.bforge.app.*`, `com.businessforge.*`, `com.example.*`, …) |

Published records: package ID is **immutable**. Collisions with another `CustomerAppReleaseProfile` fail closed. Shared Flutter `namespace` stays `com.businessforge.businessforge_mobile`; store identity is Gradle `applicationId`.

## Android signing

| Provider | Production customer |
|----------|---------------------|
| `LOCAL_TEST_SIGNING` | forbidden |
| `SHARED_OWNER_KEYSTORE` / `BF_ANDROID_KEYSTORE_*` | **forbidden** (`SHARED_OWNER_KEYSTORE_FORBIDDEN`) |
| `CUSTOMER_UPLOAD_KEY` | required refs + secret resolver `has()` |
| `PLAY_APP_SIGNING` | same upload-key refs; Play holds the app signing key |

Secret resolver: production default is **fail-closed**. Tests may use `fixture://`. Values never enter snapshots, release manifests, factory JSON, or logs.

Gradle for customer production reads **`BF_CUSTOMER_ANDROID_*` only**, never the shared Owner env vars.

Owner-Keystore remains **ACCEPTABLE for official demos only**.

## Store asset manifest

Layout: `store-assets/android/{icon,screenshots,feature-graphic,metadata}/`

Entries: `REQUIRED` / `OPTIONAL` / `GENERATED` / `CUSTOMER_PROVIDED` / `MISSING`.

`ANDROID_ASSETS_READY` needs customer icon + feature graphic + ≥2 phone screenshots, none demo-named. No screenshot device farm in this slice.

## Workflow

`validate → snapshot → apply → assets → signing-check → build → verify → release-manifest`

`--skip-build` (default) prepares the candidate without Gradle. Production signing missing → fail-closed (`STORE_RELEASE_NOT_READY`). Play Developer API upload is **out of scope**.

## Live content vs app release

| `LIVE_CONTENT_CHANGE` | products, prices, hours, staff, appointments, catalog, orders |
| `APP_RELEASE_REQUIRED_CHANGE` | icon, display name, package/bundle, native capabilities, API identity, splash |

Catalog changes must not force a new `versionCode`. Icon/name/package changes must.

Managed update: same `app_id` + package ID, strictly monotonic `version_code`, new snapshot. Prior snapshot stays on disk.

## Secret boundaries

Forbidden: git, generated customer zip, tenant API, Dashboard, log lines, release manifest values.

## Not in this slice

Play/App Store upload, iOS IPA, Apple signing automation, screenshot farm, account invite, per-customer Flutter forks, pricing changes.
