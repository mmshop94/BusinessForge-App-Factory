# App Build Manifest v1

> **Schema:** [schemas/app-build-manifest-v1.json](../schemas/app-build-manifest-v1.json)  
> **Example:** [manifests/examples/dorfladen-hutthurm.yaml](../manifests/examples/dorfladen-hutthurm.yaml)

---

## Overview

A Tenant App Manifest describes **everything the factory needs** to produce one white-label build. It is versioned independently from the Customer App and the Factory.

**Rules:**

- `schema_version` is **required** (currently `1`)
- **No secrets** — signing keys, passwords, API tokens are forbidden
- Assets are **relative paths** from the manifest directory
- iOS `bundle_id_ios` is optional in Slice 1 (stored but not applied)

---

## Full example

```yaml
schema_version: 1

app:
  id: dorfladen-hutthurm
  display_name: Dorfladen Hutthurm
  package_name_android: de.bforge.dorfladenhutthurm
  bundle_id_ios: de.bforge.dorfladenhutthurm

tenant:
  public_app_id: app_01JABCDEFGHJKMNPQRSTVWXYZ0
  package: village_store
  package_version: v1

branding:
  theme: warm
  primary_color: "#8B4A2F"
  secondary_color: "#F2E3D5"
  logo_asset: branding/logo.svg
  splash_asset: branding/splash.png
  icon_asset: branding/icon.png

features:
  news: true
  ordering: true
  loyalty: false

release:
  channel: pilot
  app_version: 1.0.0
  build_number: 1

source:
  customer_app_ref: v0.5.9
  customer_app_repo: ../BusinessForge FlutterApp
  factory_compat_version: "1"

api_base_url: https://api.businessforge.example/api/v1
backend_origin: https://api.businessforge.example
```

---

## Field reference

### `app`

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Stable slug (`a-z0-9-`, 3–64 chars) |
| `display_name` | yes | Launcher / store display name |
| `package_name_android` | yes | Reverse-DNS Android Application ID |
| `bundle_id_ios` | no | iOS bundle identifier (future) |

### `tenant`

| Field | Required | Description |
|-------|----------|-------------|
| `public_app_id` | yes | Public bootstrap ID (`app_` + 26-char ULID) |
| `package` | yes | BusinessForge package slug (e.g. `village_store`) |
| `package_version` | yes | Package capability version (`v1`, `v2`, …) |

### `branding`

| Field | Required | Description |
|-------|----------|-------------|
| `theme` | yes | `warm`, `modern`, `classic`, `minimal` |
| `primary_color` | yes | Hex color `#RRGGBB` |
| `secondary_color` | yes | Hex color `#RRGGBB` |
| `logo_asset` | yes | Relative path to logo |
| `splash_asset` | no | Splash image |
| `icon_asset` | no | App icon source |

### `features`

Open map of boolean feature flags. Keys are passed to Flutter as `FEATURE_<KEY>=true|false`.

### `release`

| Field | Required | Description |
|-------|----------|-------------|
| `channel` | yes | `dev`, `pilot`, `production` |
| `app_version` | yes | Semver `MAJOR.MINOR.PATCH` |
| `build_number` | yes | Integer ≥ 1 |

Combined as `app_version+build_number` in `pubspec.yaml`.

### `source`

| Field | Required | Description |
|-------|----------|-------------|
| `customer_app_ref` | yes | Git tag, branch, or commit |
| `customer_app_repo` | no | Relative path hint for CLI resolution |
| `factory_compat_version` | no | Factory schema compatibility (default `"1"`) |

### Network

| Field | Required | Description |
|-------|----------|-------------|
| `api_base_url` | yes | Full API base including `/api/v1` |
| `backend_origin` | no | Origin for `/health`; derived from `api_base_url` if omitted |

---

## Validation

```powershell
app-factory validate manifests/examples/dorfladen-hutthurm.yaml
```

Validation stages:

1. JSON Schema structural validation
2. Secret key/value scan
3. Android Application ID pattern
4. Branding asset existence
5. Package/ref compatibility ([customer-app-compat-v1.json](../schemas/customer-app-compat-v1.json))

---

## Forbidden content

The validator rejects manifest keys matching:

- `password`, `secret`, `api_key`, `private_key`, `keystore`, `token`, `credential`

And values resembling PEM private keys or AWS access key IDs.

---

## Versioning policy

| Change type | Action |
|-------------|--------|
| Add optional field | Same schema version with relaxed schema |
| Remove/rename required field | Increment `schema_version` |
| Change semantics | New schema + factory compat bump |

Tenant manifests should be stored in a dedicated config repo or backend export in production — not mixed into the Customer App repository.
