# Store Account Connection — Authority Boundary V1

> **Stand:** 2026-09-27  
> **Status:** FOUNDATION_READY / LIVE_PENDING · Deploy: NOT_RUN  
> **Product READY:** 35/35 UNCHANGED  
> **hq_ops authority:** `STORE_ACCOUNT_ONBOARDING_AND_VERIFICATION_V1` (migration 113)

## Two owners — do not merge

| Authority | Question | Owner | Repo |
| --- | --- | --- | --- |
| `StorePlatformSelection` | Which stores did the customer order? | Tenant row | hq_ops |
| `StoreDeliveryStatus` | How far is BusinessForge's delivery? | Tenant row | hq_ops |
| `StoreConnectionState` | Does BusinessForge have usable access to the **customer-owned** store account? | `store_account_connections` | **hq_ops** |
| Publisher pipeline | Can AppFactory upload / bind / deliver to a connected account? | Publisher connection + setup contract | **AppFactory (this repo)** |

**hq_ops owns customer-facing connection state.**  
**AppFactory owns the publisher pipeline** (app-scoped credentials, package bind, internal track / TestFlight delivery).

They never write to each other. A `VERIFIED` connection does not imply a published app. A successful INTERNAL upload does not invent a customer connection state.

## Customer-facing state machine (hq_ops SoT only)

```text
NOT_SELECTED | SETUP_REQUIRED | GUIDE_IN_PROGRESS | USER_CONFIRMED_SETUP
VERIFYING | VERIFIED | PARTIAL | NEEDS_ACTION | FAILED | REVOKED
```

Critical invariant: guide completion → `USER_CONFIRMED_SETUP`, **never** `VERIFIED`.  
Only a provider probe answer may reach `VERIFIED` / `PARTIAL` / `REVOKED`.

Customer API (company_admin):

```text
GET  /api/v1/customer-surface/store-connections
POST /api/v1/customer-surface/store-connections/{provider}/guide-progress
POST /api/v1/customer-surface/store-connections/{provider}/verify
PUT  /api/v1/customer-surface/store-connections/{provider}/credentials
```

List response shape: `{ store_platform_selection, verifier_mode?, connections[], visible_providers[], invite_identities }`.

## AppFactory pipeline states (not customer connection states)

These stay **publisher / delivery** vocabulary and must not be shown as customer connection enums:

| AppFactory term | Meaning | Not equal to |
| --- | --- | --- |
| `CONNECTION_VERIFIED` (onboarding stage) | Pipeline gate: principal + permissions usable for upload | hq_ops `VERIFIED` |
| `PLAY_APP_SETUP_REQUIRED` | Play Console app record missing for package bind | hq_ops `SETUP_REQUIRED` |
| `CREDENTIAL_MISSING` / `AUTH_FAILED` | Publisher credential probe result | customer guide progress |
| `CUSTOMER_PLAY_ONBOARDING` stages | Operator/factory checklist | customer `guide_steps` |

### Deprecated / mismatched names (do not invent in clients)

| Term | Status |
| --- | --- |
| `VERIFICATION_PENDING` | **Deprecated** — use hq_ops `VERIFYING` / `USER_CONFIRMED_SETUP` |
| `CREDENTIALS_PENDING` | **Deprecated** — use `credential_configured: false` + missing requirements |
| Flat `/guide-progress` (no provider) | **Deprecated** — path is `…/store-connections/{provider}/guide-progress` |
| `guide_url` as connection field | **Deprecated** — guides are `guide_steps[{id,title_de,body_de}]` |

## Permission matrices (conceptual reuse)

Google Play required (customer invite / hq_ops):

- `VIEW_APP_INFORMATION`
- `MANAGE_TESTING_RELEASES` (hq_ops customer SoT)

AppFactory publisher pipeline historically emits `MANAGE_TEST_RELEASES` for the same Play Console capability. Both names are accepted as aliases in `classify_permissions` — they are **one permission**, not two states.

Apple App Store Connect required roles (aligned):

- `APP_MANAGER`
- `CLOUD_MANAGED_APP_DISTRIBUTION`

See hq_ops `STORE_PROVIDER_PERMISSION_MATRIX_V1.json` and local setup contracts under `play/` / `apple/`.

## LIVE_PENDING (intentionally not in this slice)

- Live Google verification via AppFactory store-access port (hq_ops LIVE → `PROVIDER_UNAVAILABLE` until wired).
- Apple ES256 JWT signing / real access probe (`APPLE_LIVE_PENDING`).
- Real customer provider credential uploads in production.
- Any deploy. **NO DEPLOY.**

## Related local docs

- [CUSTOMER_SURFACE_BACKEND_SELECTION_SOT_V1.md](CUSTOMER_SURFACE_BACKEND_SELECTION_SOT_V1.md) — selection mapping only
- [ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md](ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md) — publisher onboarding gate
- [IOS_FACTORY_APP_STORE_CONNECT_FOUNDATION_V1.md](IOS_FACTORY_APP_STORE_CONNECT_FOUNDATION_V1.md) — Apple publisher foundation
