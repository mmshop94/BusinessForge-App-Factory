# Security — BusinessForge App Factory

> **Stand:** 2026-08-14 (Wave 1 store-ready foundation)

---

## Threat model (Slice 1)

| Asset | Risk | Mitigation |
|-------|------|------------|
| Android signing keys | Forge malicious APKs | **Never stored in this repo** — env `BF_ANDROID_*` / vault only; reports reject secret markers |
| Play Store service accounts | Unauthorized uploads | Out of scope; Store remains MANUAL_OPERATION |
| Tenant secrets | Client or manifest leak | Manifest validator rejects secret-like keys/values; export has no credentials |
| Build reports / Build Result | Information disclosure | Public fields only — no keystore paths, passwords, or local secret paths |

---

## Repository rules

### Must NOT be committed

- `*.jks`, `*.keystore`, `*.p12`, `*.pem`
- `.env` files with credentials
- Play Store or App Store API keys
- Tenant private keys or JWT signing material
- Generated `output/` artifacts with PII (operational hygiene)

### `.gitignore` enforcement

The repository `.gitignore` blocks common secret and artifact patterns. Pre-commit hooks may be added in Slice 2.

---

## Manifest security

Manifests may contain:

- ✅ Public `public_app_id` (bootstrap identifier)
- ✅ Package name, display name, colors
- ✅ Public API URLs

Manifests must NOT contain:

- ❌ Keystore passwords
- ❌ OAuth client secrets
- ❌ Private API keys
- ❌ Firebase service account JSON
- ❌ APNs keys

The `ManifestValidator` scans for forbidden key names and PEM/AWS-like values.

---

## Build runner security

Recommended production setup:

```text
Isolated CI runner (no internet except Flutter pub + backend API)
        │
        Secrets injected at runtime (GitHub Actions / Vault)
        │
        Ephemeral workspace — destroyed after build
        │
        Artifact uploaded to secure storage
```

Local development:

- Use `--dry-run` when Flutter toolchain unavailable
- Do not place keystores in the factory or customer app directories
- Clear `output/` and `.workspaces/` after debugging

---

## Customer App client security

The white-label APK embeds only:

- Public app identifier
- Public API base URL
- Package/feature flags

Tenant authorization happens **server-side** after bootstrap. See Customer App [MULTI_TENANT.md](../../BusinessForge%20FlutterApp/docs/architecture/MULTI_TENANT.md).

---

## Incident response

If a signing key is suspected compromised:

1. Revoke key in Play Console / App Store Connect
2. Rotate via vault — not via git history
3. Rebuild affected tenant apps with new key (Slice 3+)
4. Audit build reports for unexpected `manifest_hash` values

---

## Future work

- Vault/KMS integration for signing (Slice 3)
- Manifest signature verification (Slice 2)
- SBOM generation per build (Slice 4)
- OIDC-scoped CI per tenant (Slice 4)
