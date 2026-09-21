# White-Label Google Play Live Publisher Proof V1

> Stand: 2026-09-21 · **no production submission** · no secrets in git  
> Prior: [ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md](ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md)  
> Identity: `de.bforge.reference.internal` · owner `BUSINESSFORGE_REFERENCE`

```text
SETUP_CONTRACT_COMPLETE
REFERENCE_IDENTITY_RESERVED
LIVE_GOOGLE_PLAY_PROOF = BLOCKED_EXTERNAL
CUSTOMER_OWNED_PUBLISHING_PROVEN = FALSE
ANDROID_PRODUCTION_READY = NOT_IMPLEMENTED
```

This slice does **not** create a Google Play developer account and does **not**
upload an AAB. This workspace has no wired publisher credential, no
`BF_OPS_SECRET_DIR`, and `google.auth` is not installed. Live Google remains
externally blocked.

## Owner-type split

```text
BUSINESSFORGE_REFERENCE  !=  CUSTOMER_OWNED
```

A reference proof, if it ever lands, is platform API verification only. It
must never be marked `CUSTOMER_OWNED_PUBLISHING_PROVEN`.

## Canonical reference identity

| Field | Value |
|-------|--------|
| Package | `de.bforge.reference.internal` |
| App id | `bforge-reference-internal` |
| Tenant | `tenant-bforge-reference` |
| Recyclable as customer app | **false** |
| Forbidden customer package | `de.hutthurm.dorfladen` |

After the first successful Play bind the package is `PACKAGE_IMMUTABLE`.

## Workspace preconditions (this operator host)

Statuses are only `VERIFIED` / `ACTION_REQUIRED` / `BLOCKED_EXTERNAL` /
`NOT_APPLICABLE`. Nothing below is invented as `VERIFIED` on the Google side.

| Prerequisite | Status |
|--------------|--------|
| `PLAY_DEVELOPER_ACCOUNT` | `BLOCKED_EXTERNAL` |
| `PLAY_APP_CREATED` | `BLOCKED_EXTERNAL` |
| `PLAY_APP_SIGNING_TERMS_ACCEPTED` | `BLOCKED_EXTERNAL` |
| `PACKAGE_BOUND` | `BLOCKED_EXTERNAL` |
| `BF_PRINCIPAL_GRANTED` | `BLOCKED_EXTERNAL` |
| `VIEW_APP_INFORMATION_GRANTED` | `BLOCKED_EXTERNAL` |
| `TEST_RELEASE_PERMISSION_GRANTED` | `BLOCKED_EXTERNAL` |
| `PUBLISHER_CREDENTIAL_AVAILABLE` | `ACTION_REQUIRED` |
| `INTERNAL_TESTER_CONFIGURATION` | `NOT_APPLICABLE` |

Workspace wiring:

| Item | Status |
|------|--------|
| `REAL_GOOGLE_PLAY_INTERNAL_TEST` | `ACTION_REQUIRED` (unset) |
| `BF_OPS_SECRET_DIR` | `ACTION_REQUIRED` (unset) |
| `google.auth` extra `play` | `ACTION_REQUIRED` |
| `httpx` | present |

## Play Console app binding

BusinessForge does not simulate a Create-App API. The publisher must create
the Console app, then:

```text
package visible
publisher connection authenticates
target app belongs to expected publisher
→ PLAY_APP_BOUND
```

Authority: [ANDROID_GOOGLE_PLAY_LIVE_PUBLISHER_PROOF_V1.json](ANDROID_GOOGLE_PLAY_LIVE_PUBLISHER_PROOF_V1.json).

## App-scoped principal (when later wired)

Required: `VIEW_APP_INFORMATION`, `MANAGE_TEST_RELEASES`.  
Optional: `MANAGE_TESTERS` only if an install proof is wanted.  
Forbidden / never used: `PRODUCTION_RELEASE`, `PLAY_ADMIN`, `FINANCIAL_DATA`,
`ACCOUNT_WIDE_ADMIN`. Excess grants are `EXTRA_PERMISSION_PRESENT` and unused.

## Upload key vs Play App Signing

```text
UPLOAD KEY  !=  PLAY APP SIGNING KEY
```

Shared BusinessForge owner key and debug signing stay forbidden. No private
keys in evidence.

## Production hard-block

Any `track=production` attempt returns `PRODUCTION_SUBMISSION_BLOCKED` before
a Google write. That path is proven in tests; it is not a live production
submission.

## Operator commands

```text
app-factory google-play setup-contract --reference
app-factory google-play live-proof-audit
app-factory google-play preflight … --owner-type BUSINESSFORGE_REFERENCE --track internal
```

Live Google additionally needs `REAL_GOOGLE_PLAY_INTERNAL_TEST=1`, extra
`play` (`google-auth`), `BF_OPS_SECRET_DIR/{tenant}/{app}/`, and a real
reference publisher. None of those are wired here.

## Out of scope

Production track, customer-owned publishing proof, Play app auto-create,
pilot customer, iOS, store listing automation, device install proof.
