# Android Customer Play Connection + Internal Test-Track Delivery V1

> Stand: 2026-09-20 · **no production submission** · no secrets in git  
> Prior intake (unchanged): [CUSTOMER_APP_RELEASE_INTAKE_V1.md](CUSTOMER_APP_RELEASE_INTAKE_V1.md)

```text
frozen snapshot
→ per-customer upload key
→ signed AAB
→ customer-owned Play account (app-scoped)
→ INTERNAL test track
→ read-back
→ ANDROID_PRODUCTION_READY = NOT_IMPLEMENTED
```

## Customer-owned publisher

The customer owns the Play developer account. BusinessForge stores only a
`GooglePlayPublisherConnection` bound to `tenant_id` + `customer_app_id` + `package_name`.

Credential values live in the ops secret resolver (`ops://…` / `BF_OPS_SECRET_DIR/{tenant}/{app}/`).
Snapshots, release manifests, logs, and generated Flutter workspaces must not contain tokens, JSON keys, or passwords.

Scope is **APP_SCOPED**. Account-wide admin is a hard block.

## Least privilege

Required for this slice:

- `VIEW_APP_INFORMATION`
- `MANAGE_TEST_RELEASES`

Optional if used later: `MANAGE_TESTERS`, `MANAGE_STORE_LISTING`.

Forbidden and never invoked: `PLAY_ADMIN`, `ACCOUNT_WIDE_ADMIN`, `FINANCIAL_DATA`, `ORDER_MANAGEMENT`, `PRODUCTION_RELEASE`, `USER_PERMISSION_MANAGEMENT`.

If a principal also has `PRODUCTION_RELEASE`, it is **recorded as excess** and **not used**. Internal test delivery does not require production permission.

## Connection lifecycle

`NOT_CONFIGURED` → credentials present → auth → package bound → test permissions → `READY`

Also: `CREDENTIAL_MISSING`, `AUTH_FAILED`, `APP_NOT_FOUND`, `ACCESS_DENIED`, `PERMISSION_INCOMPLETE`, `PLAY_APP_SETUP_REQUIRED`, `PACKAGE_ID_MISMATCH` (hard block, frozen applicationId is never rewritten), `REVOKED`, `PLAY_POLICY_REQUIREMENT_PENDING`.

Verification talks to the Publisher provider. A customer saying “we invited you” is not sufficient.

## Play app precondition

Creating the Play Console app record is **outside** the API this slice implements. Until the package exists: `PLAY_APP_SETUP_REQUIRED`. When it matches the snapshot package: `PLAY_APP_BOUND`.

## Upload key vs Play App Signing

BusinessForge builds with the **upload key** only (`CUSTOMER_UPLOAD_KEY` / `PLAY_APP_SIGNING` enrollment). The app-signing key stays with Play App Signing. Public model stores `certificate_sha256` only.

Shared Owner-Keystore + production customer build remains `SHARED_OWNER_KEYSTORE_FORBIDDEN`.

Secret rotation: replace the ops file behind the same reference; do not put material in the profile.

## Test-track pipeline

`verify → create edit → upload AAB → configure INTERNAL → validate → commit → read-back`

Idempotent on the same edit. `track=production` returns `PRODUCTION_SUBMISSION_BLOCKED` and **does not write**. No Internal→Production promotion.

`CLOSED` is modelled; Internal is the proven first track.

## Customer approval

`BUILD_READY` ≠ upload. `TEST_UPLOAD_APPROVED` is bound to `release_id` + `snapshot_id`. Release 1 approval cannot upload release 2. Snapshot change after approval is `SNAPSHOT_CHANGED_AFTER_APPROVAL`. No production approval object exists.

## Failure / retry

No silent fallback, no production detour. Failed edits stay auditible; retries reuse an unused approval on the same snapshot. Duplicate committed `versionCode` is `DUPLICATE_VERSION_CODE`.

## Live Google account

Without a wired customer Play app + app-scoped credential in ops:

```text
IMPLEMENTATION_READY
LIVE_PLAY_PROOF_BLOCKED_EXTERNAL
```

External requirements: customer Play developer account, Console app with the frozen `applicationId`, app-scoped principal with test-track rights, credential reference in `BF_OPS_SECRET_DIR`, optional `google-auth` extra for a future live HTTP adapter.

## CLI

```text
app-factory verify-play-connection --package-name … --tenant-id … --app-id …
app-factory prepare-customer-release … --build   # AAB, still no Play upload
```

Provider isolation: `PublisherProvider` → `FakePlayPublisherProvider` (tests) / `GooglePlayPublisherProvider` (live fail-closed).
