# iOS Factory + App Store Connect Publishing Foundation V1

> Stand: 2026-09-21 · **no App Store production** · no secrets in git  
> Prior Android: [ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md](ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md)

```text
IOS_IMPLEMENTATION_READY
APPLE_ONBOARDING_CONTRACT_READY
LIVE_APPLE_PROOF = BLOCKED_EXTERNAL
IOS_BUILD_BLOCKED_NO_MACOS_EXECUTOR
APP_STORE_PRODUCTION = NOT_IMPLEMENTED
CUSTOMER_OWNED_PUBLISHING_PROVEN = FALSE
```

This workspace is Windows. It cannot produce a store IPA. Missing Mac is
`IOS_BUILD_EXECUTOR_REQUIRED`, never `IOS_BUILD_FAILED`. No fake IPA is PASS.

## Identity

Customer bundle IDs are reverse-DNS, collision-checked, immutable after
`freeze_apple_bundle`. Android package and iOS bundle may differ; both bind
to the same `CustomerAppReleaseProfile`.

Reserved for customers: `de.bforge.app.*`, `de.bforge.reference.*`,
`com.businessforge.*`.

Reference (not customer, not recyclable):

```text
de.bforge.reference.internal.ios
BUSINESSFORGE_REFERENCE
```

## Signing

`AppleSigningProfile` holds secret **references** only (`ops://` / `env://` /
`fixture://`). Modes: `LOCAL_TEST`, `CUSTOMER_DEVELOPMENT`,
`CUSTOMER_DISTRIBUTION`, `APP_STORE_DISTRIBUTION`. Shared BusinessForge
distribution material is forbidden.

## Executor

`LOCAL_MACOS` / `CI_MACOS` / `EXTERNAL_MACOS`. This host: not macOS. No new
paid CI was added (no existing AppFactory macOS runner).

## App Store Connect

`ApplePublisherConnection` is app-scoped. Owner types match Play:
`CUSTOMER_OWNED` vs `BUSINESSFORGE_REFERENCE`. Account Holder stays with the
customer. Fake provider is fully testable. Live provider without
`REAL_APPLE_TESTFLIGHT_TEST=1` and credentials: `BLOCKED_EXTERNAL`.

Production / App Review writes: `APP_STORE_PRODUCTION_SUBMISSION_BLOCKED`
before any Apple write.

## CLI

```text
app-factory ios setup-contract --reference
app-factory ios live-proof-audit
```

Evidence: [IOS_FACTORY_APP_STORE_CONNECT_FOUNDATION_V1.json](IOS_FACTORY_APP_STORE_CONNECT_FOUNDATION_V1.json)
