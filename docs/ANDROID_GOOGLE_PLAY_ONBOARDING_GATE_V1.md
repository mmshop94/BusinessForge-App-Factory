# Google Play Onboarding Gate + Internal Live Proof V1

> Stand: 2026-09-20 · **no production submission** · no secrets in git  
> Prior (unchanged): [ANDROID_CUSTOMER_PLAY_TEST_TRACK_DELIVERY_V1.md](ANDROID_CUSTOMER_PLAY_TEST_TRACK_DELIVERY_V1.md)

```text
IMPLEMENTATION_COMPLETE
ONBOARDING_CONTRACT_READY
LIVE_GOOGLE_PLAY_PROOF = BLOCKED_EXTERNAL
```

No Play Console app is created by AppFactory. No customer-owned publisher was wired in this slice. A BusinessForge **reference** publisher may be used later for a platform live-proof only — that is **not** `CUSTOMER_OWNED_PUBLISHING_PROVEN`.

## External setup contract

Each prerequisite has its own state (`NOT_STARTED` / `ACTION_REQUIRED` / `VERIFYING` / `VERIFIED` / `FAILED` / `NOT_APPLICABLE`):

```text
PLAY_DEVELOPER_ACCOUNT
PLAY_APP_CREATED
PLAY_APP_SIGNING_TERMS_ACCEPTED
PACKAGE_BOUND
BF_PRINCIPAL_GRANTED
VIEW_APP_INFORMATION_GRANTED
TEST_RELEASE_PERMISSION_GRANTED
PUBLISHER_CREDENTIAL_AVAILABLE
```

`PLAY_EXTERNAL_SETUP_READY` only when every required item is `VERIFIED` or `NOT_APPLICABLE`. There is no blanket “Google connected” flag.

## One-time Play Console app-create

`console_app_create_contract(profile)` emits the data the publisher needs (app name, default language, App/Game, Free/Paid, support email, package name, Play App Signing, BusinessForge principal, required permissions).

BusinessForge does **not** claim to have created the Play app via API.

After the first successful package bind: `PACKAGE_IMMUTABLE = TRUE` (`CustomerAppIdentityRegistry.freeze_play_package`). No regeneration.

Package form: frozen `applicationId` (`de.<customer>.<app>` or the already frozen id).

## Publisher owner type

```text
CUSTOMER_OWNED              later customer production path
BUSINESSFORGE_REFERENCE     platform / CI / internal live-proof only
```

Architecture is identical. Ownership is an authority/evidence property.

`BUSINESSFORGE_REFERENCE` must never be read as `CUSTOMER_OWNED_PUBLISHING_PROVEN`.

## Preflight

```text
app-factory google-play preflight <intake.json> --tenant-id … --app-id … --package-name …
app-factory google-play setup-contract <intake.json>
app-factory google-play onboarding --states-json states.json
```

Result: `LIVE_INTERNAL_UPLOAD_READY` or concrete blockers. Live Google without `REAL_GOOGLE_PLAY_INTERNAL_TEST=1` and a wired credential is `BLOCKED_EXTERNAL` (not a silent PASS).

`track=production` returns `PRODUCTION_SUBMISSION_BLOCKED` before any Google write.

## App-scoped live verify

Authentication + target package accessible + test-release permitted. Credential file presence alone is not `READY`.

Non-sensitive evidence: publisher connection id / principal reference, package, timestamp, access/permission result, safe provider response ids. `PRODUCTION_RELEASE` if present is `EXTRA_PERMISSION_PRESENT` and is never used.

## Internal delivery + read-back

`create edit → upload AAB → INTERNAL track → validate → commit → read-back`.

Consistent package / track / versionCode / status → `PLAY_INTERNAL_RELEASE_VERIFIED`. Deviation → `PLAY_RELEASE_READBACK_MISMATCH` (not READY).

`versionCode`: reuse the built value until Google already knows it; then next monotonic value.

## Testers

`InternalTesterGroupReference` from ops (`ops://play/internal-tester-group`). States: `TESTER_GROUP_NOT_CONFIGURED` / `TESTER_GROUP_READY` / `TESTER_ACCESS_VERIFIED`. Opt-in URLs only if Google actually returns one. No private emails in git. No invented URLs.

Device installation is outside this factory: `INSTALLATION_PROOF_NOT_RUN`.

## Policy / account vs factory

`PLAY_POLICY_REQUIREMENT_PENDING` and `PLAY_ACCOUNT_REQUIREMENT_PENDING` stay distinct from AppFactory errors. Internal = `SUPPORTED`. Production = `NOT_IMPLEMENTED`.

## Customer onboarding gate

`CUSTOMER_PLAY_ONBOARDING` stages: `ACCOUNT_CREATED` → `APP_CREATED` → `BF_INVITED` → `APP_SCOPED_PERMISSIONS_GRANTED` → `CREDENTIAL_CONNECTED` → `CONNECTION_VERIFIED` → `PACKAGE_BOUND` → `TEST_DELIVERY_READY`.

Summaries are specific, never “Google funktioniert nicht”:

- “Google Play ist bereit”
- “Es fehlt: BusinessForge Zugriff auf diese App”
- “Es fehlt: Berechtigung für Test-Releases”

Instruction rows: `step_id`, `title`, `description`, `required_value`, `verification_method`, `status`, `blocking`.

## Live proof artefact

`GOOGLE_PLAY_INTERNAL_LIVE_PROOF_V1.json` — release/snapshot/owner type/package/version/AAB hashes/track/edit/commit/read-back/timestamp. No credentials, tokens, private keys, passwords, or service-account JSON.

## Live test gate

```text
REAL_GOOGLE_PLAY_INTERNAL_TEST=1
```

Unset (this workspace): skipped, `LIVE_GOOGLE_PLAY_PROOF = BLOCKED_EXTERNAL`. Must not fail the default suite and must not claim PASS.

## Security

- Tenant A cannot use tenant B publisher connection, upload key, package, or tester reference.
- Credential rotation updates only the secret reference; package, customer app identity, and release history stay put.
- Reference publisher ≠ customer-owned proof.
- Production track unreachable.
- Credentials never enter release artefacts.

## Out of scope (unchanged)

Google production release, store listing automation, Data Safety, content rating, public listing, Apple, dashboard UI, billing, pilot onboarding, source handoff.
