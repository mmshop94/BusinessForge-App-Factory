# BusinessForge App Factory

White-label build and release infrastructure for the [BusinessForge Customer App](../BusinessForge%20FlutterApp).

This repository **does not** contain Flutter product code. It orchestrates tenant-specific Android builds from:

1. a pinned **Customer App** revision (Git tag/commit),
2. a versioned **Tenant App Manifest** (YAML/JSON),
3. referenced **Branding assets**.

## Quick start

```powershell
cd "d:\projekte\BusinessForge App_Generator"
pip install -e ".[dev]"

# Validate example manifest
app-factory validate manifests/examples/dorfladen-hutthurm.yaml

# Deterministic build plan
app-factory plan manifests/examples/dorfladen-hutthurm.yaml `
  --customer-app "d:\projekte\BusinessForge FlutterApp"

# Dry-run build (no Flutter execution)
app-factory build-android manifests/examples/dorfladen-hutthurm.yaml --dry-run

# Full Android build (requires Flutter SDK + Android toolchain)
app-factory build-android manifests/examples/dorfladen-hutthurm.yaml `
  --customer-app "d:\projekte\BusinessForge FlutterApp" `
  --format apk
```

## CLI commands

| Command | Purpose |
|---------|---------|
| `validate <manifest>` | Schema + business-rule + asset validation |
| `plan <manifest>` | Deterministic build plan JSON |
| `build-android <manifest>` | Execute Slice 1 Android pipeline |
| `inspect-build <report>` | Pretty-print build report |

## Repository layout

```text
app_factory/          Python package (domain / application / infrastructure / cli)
schemas/              JSON Schema + compatibility matrix
manifests/examples/   Sample tenant manifests and branding assets
templates/            Generated config templates
tests/                Unit tests (mocked Flutter)
docs/                 Architecture and integration docs
output/               Build artifacts and reports (gitignored)
```

## Related repositories

| Repository | Role |
|------------|------|
| `BusinessForge FlutterApp` | Customer App — single generic Flutter codebase |
| `BusinessForge` | Backend platform — tenant/app configuration source of truth |
| `BusinessForge Dashboard` | Admin UI for tenants and packages |
| **BusinessForge App Factory** (this repo) | Build orchestration |

## Versioning

| Artifact | Example | Meaning |
|----------|---------|---------|
| Customer App | `v0.5.9` | Product features and client behavior |
| App Factory | `v0.1.0` | Generator and pipeline capabilities |
| Tenant App | `1.0.0+1` | Published white-label build for one tenant |

These versions are **independent** and must not be coupled.

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [APP_MANIFEST_V1.md](docs/APP_MANIFEST_V1.md)
- [CUSTOMER_APP_INTEGRATION.md](docs/CUSTOMER_APP_INTEGRATION.md)
- [SECURITY.md](docs/SECURITY.md)
- [ROADMAP.md](docs/ROADMAP.md)

## Slice 1 scope

Included: manifest validation, branding application, Android ID/label, Flutter build orchestration, reproducible build reports.

Not included: Play Store upload, iOS, signing key storage, screenshot generation, tenant forks.
