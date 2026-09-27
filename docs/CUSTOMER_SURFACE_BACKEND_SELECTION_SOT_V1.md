# Customer Surface Backend Selection SoT V1

Canonical SoT: BusinessForge tenant `store_platform_selection`.
AppFactory maps via `backend_selection.from_backend_store_selection`.
File snapshots = freeze only. selection ≠ publication.

## Store account connection (separate authority)

Customer-facing `StoreConnectionState` is owned by **hq_ops**
(`STORE_ACCOUNT_ONBOARDING_AND_VERIFICATION_V1`). AppFactory does **not**
own or mirror those enums for the Dashboard / customer-surface UI.

See [STORE_ACCOUNT_CONNECTION_AUTHORITY_BOUNDARY_V1.md](STORE_ACCOUNT_CONNECTION_AUTHORITY_BOUNDARY_V1.md).
