# Roadmap — BusinessForge App Factory

> **Stand:** 2026-08-05

---

## Slice 1 — Foundation ✅ (this release)

**Goal:** Prove manifest → branded Android build without store upload.

- [x] Repository structure and domain model
- [x] Manifest schema v1 + validator
- [x] Deterministic build planner
- [x] Isolated workspace + Flutter orchestration
- [x] CLI (`validate`, `plan`, `build-android`, `inspect-build`)
- [x] Build report with SHA-256 and commit hash
- [x] Unit tests
- [x] Documentation

**Exit criteria:** One example tenant manifest produces a planned or real APK on a machine with Flutter SDK.

---

## Contract v1 — Build integration gate ⏳ (next milestone)

**Goal:** Stabilize the Factory ↔ Customer App boundary before Slice 2 implementation.

- [x] Document [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md)
- [ ] Customer App: `AppConfiguration.load()` entry point (replaces scattered `fromEnvironment`)
- [ ] Customer App: adopt `PUBLIC_APP_ID`, `APP_PACKAGE`, `FEATURE_*` defines
- [ ] Customer App: declare `assets/branding/` in pubspec
- [ ] Update compat matrix with contract-adopted Customer App tag
- [ ] Review and sign-off from both repo maintainers

**Exit criteria:** Contract v1 accepted; Factory Slice 2 work may begin.

---

## Slice 2 — Reproducible builds + platform hooks

**Goal:** End-to-end white-label APK/AAB from manifest; backend manifest export optional.

- [ ] First production tenant build against contract-adopted Customer App tag
- [ ] Icon rasterization pipeline (SVG → mipmap)
- [ ] Splash screen native injection
- [ ] `GET /internal/app-factory/manifests/{tenant_id}` API (optional)
- [ ] Dashboard action: "Generate build manifest" (optional)
- [ ] GitHub Actions workflow with pinned Flutter

**Not in Slice 2:** Play Store upload, iOS, signing key storage.

---

## Slice 3 — Signing and store upload

**Goal:** Production release to Google Play internal track.

- [ ] Keystore reference via CI secrets (not files)
- [ ] `jarsigner` / Play App Signing integration
- [ ] Play Store upload (internal testing track)
- [ ] Rollback and version conflict handling
- [ ] Batch rebuild orchestration on Customer App tag

**Explicitly deferred from Slice 1–2.**

---

## Slice 4 — Operations at scale

- [ ] Remote build farm / queue
- [ ] Tenant rollout channels (pilot → production)
- [ ] Screenshot generation for store listings
- [ ] Store metadata (title, description) from backend
- [ ] SBOM and supply-chain attestations
- [ ] Optional `BusinessForge-App-Configs` repository for manifest-only storage

---

## Slice 5 — Apple ecosystem

- [ ] IPA build on macOS runner
- [ ] Provisioning profiles via App Store Connect API
- [ ] TestFlight upload

---

## Customer App dependencies

| Factory slice | Customer App requirement |
|---------------|-------------------------|
| Contract v1 gate | [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md) adoption |
| Slice 1 | Stable Android Gradle/Manifest structure |
| Slice 2 | `AppConfiguration.load()`, `PUBLIC_APP_ID`, feature flags, branding assets |
| Slice 3 | Push notification Firebase per-tenant config surface |
| Slice 4 | Package capability API alignment |

---

## Naming migration

| Local folder (legacy) | GitHub repository | Status |
|-----------------------|-------------------|--------|
| `BusinessForge App_Generator` | [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory) | ✅ published |
| `BusinessForge FlutterApp` | [BusinessForge-FlutterApp](https://github.com/mmshop94/BusinessForge-FlutterApp) | ✅ published |

Optional future rename: `BusinessForge-FlutterApp` → `BusinessForge-Customer-App` (cosmetic; requires CI path updates).
