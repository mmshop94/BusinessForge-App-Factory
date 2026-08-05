# Architecture — BusinessForge App Factory

> **Repository:** [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory)  
> **Stand:** 2026-08-05  
> **Slice:** 1 — Foundation  
> **Status:** ✅ Runtime v1 qualified ([FACTORY_RUNTIME_V1.md](FACTORY_RUNTIME_V1.md))

---

## Purpose

BusinessForge App Factory transforms a **single generic Flutter Customer App** into **tenant-specific white-label Android builds** without creating permanent per-tenant repositories.

```text
Tenant App Manifest + Branding Assets + Customer App @ ref
                    ↓
            BusinessForge App Factory
                    ↓
        Signed-ready APK/AAB + Build Report
```

---

## Repository boundaries

| Repository | Responsibility | Must NOT contain |
|------------|----------------|------------------|
| [BusinessForge-FlutterApp](https://github.com/mmshop94/BusinessForge-FlutterApp) | Product runtime, features, UI, runtime branding API | Generator logic, signing keys, tenant manifests |
| [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory) (this repo) | Validate manifests, apply build config, orchestrate Flutter builds | Flutter feature code, business logic |
| [BusinessForge](https://github.com/mmshop94/BusinessForge) | Authoritative tenant/package/branding configuration | Client build artifacts |
| [BusinessForge-Dashboard](https://github.com/mmshop94/BusinessForge-Dashboard) | Admin UI for operators | Build pipeline execution |

This separation follows the decision documented in the Customer App's [WHITE_LABEL.md](https://github.com/mmshop94/BusinessForge-FlutterApp/blob/main/docs/architecture/WHITE_LABEL.md), renamed from "AppForge" to **App Factory** for clarity.

The **binding build contract** between Factory and Customer App is [CUSTOMER_APP_BUILD_CONTRACT_V1.md](CUSTOMER_APP_BUILD_CONTRACT_V1.md) — **Approved** and qualified against Customer App `v0.5.10`.

---

## Layered design

```text
app_factory/
├── domain/           Pure types, enums, errors — no I/O
├── application/      Validation, planning, orchestration
├── infrastructure/   Filesystem, Flutter CLI, hashing, reports
└── cli/              Operator-facing commands
```

### Domain

Immutable dataclasses represent the build contract:

- `AppBuildManifest` — validated tenant configuration
- `BuildRequest` / `BuildResult` — execution input/output
- `BuildArtifact` — output file with SHA-256

### Application

| Service | Role |
|---------|------|
| `ManifestValidator` | JSON Schema + business rules + secret scan |
| `BuildPlanner` | Deterministic step list and dart-defines |
| `BuildOrchestrator` | End-to-end Android pipeline |

### Infrastructure

| Adapter | Role |
|---------|------|
| `WorkspaceManager` | Isolated copy of Customer App — never mutates source |
| `FlutterConfigApplier` | Patches pubspec, Gradle, AndroidManifest, assets |
| `FlutterRunner` | Subprocess wrapper for `flutter` CLI |
| `BuildReportWriter` | Machine-readable reproducibility metadata |

---

## Build pipeline (Slice 1)

```text
1. Load + validate manifest
2. Resolve Customer App path + compatibility
3. Snapshot source files (integrity check)
4. Copy Customer App → temp workspace
5. Apply manifest (config, branding, IDs, version)
6. flutter pub get
7. flutter analyze          (optional, default on)
8. flutter test             (optional, default on)
9. flutter build apk|appbundle --release
10. Collect artifacts + SHA-256
11. Write build report
12. Cleanup workspace
13. Assert source unchanged
```

---

## Reproducibility

Each build report records:

| Field | Purpose |
|-------|---------|
| `manifest_hash` | SHA-256 of canonical manifest JSON |
| `customer_app_commit` | Git HEAD of Customer App checkout |
| `flutter_version` / `dart_version` | Toolchain fingerprint |
| `artifacts[].sha256` | Output integrity |
| `started_at` / `finished_at` | Audit trail |

Same manifest + same Customer App commit + same toolchain → same **configurative** build. Binary APK hashes may differ due to timestamps unless fully hermetic builds are configured (future).

---

## Data flow with platform

```text
BusinessForge Backend
        │
        ├── Tenant, Package, Branding (runtime)
        └── App Configuration (future API export)
                │
                ▼
        Tenant App Manifest (YAML, versioned)
                │
                ▼
        App Factory ──► White-Label APK/AAB
```

Slice 1 uses **file-based manifests**. Backend-driven manifest export is planned for Slice 2.

---

## Open architecture decisions

| Decision | Current choice | Alternatives considered |
|----------|----------------|-------------------------|
| Manifest format | YAML + JSON Schema | Protobuf, DB-only |
| Config injection | `--dart-define` + patched native files | Flutter flavors, code generation |
| Workspace strategy | `shutil.copytree` to `.workspaces/` | Git worktree, Docker bind-mount |
| Factory language | Python 3.9+ | Go, shell-only |
| Customer App naming | `BusinessForge FlutterApp` → future rename to `BusinessForge-Customer-App` | — |

---

## Non-goals (Slice 1)

- Play Store / App Store upload
- Signing key management in-repo
- iOS builds
- Per-tenant Git forks
- Screenshot or store metadata generation

See [ROADMAP.md](ROADMAP.md) for planned slices.
