# App Factory — Service Roadmap V1

> Stand: 2026-09-13  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| AUTO_WORKSHOP Certificate | **CURRENT** (production_active NO) / **UNCHANGED** |
| BICYCLE Certificate | **CURRENT** (`cert-service-bicycle-workshop-v1`, production_active **NO**) / **UNCHANGED** |
| MOTORCYCLE Certificate | **CURRENT** (`cert-service-motorcycle-workshop-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** / **UNCHANGED** |
| ELECTRICIAN Certificate | **CURRENT** (`cert-service-electrician-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** |
| APPLIANCE_SERVICE Certificate | **CURRENT** (`cert-service-appliance-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** · **CONFIG_ONLY** |
| HVAC / Sanitary peer audit | **DONE** · both **CONFIG_ONLY** · winner **HVAC** (`hvac_service`) · Sanitary deferred · **not registered** |
| App Factory mapping | `service_first` + commercial `catalog_specialization_options()` — HVAC packaging only after reference proof; **no** HVAC/Sanitary forks invent now |
| Remaining | Wait for `SERVICE_HVAC_SERVICE_REFERENCE_VERTICAL_PROOF_V1` |

```text
STOP APPLIANCE SERVICE CERTIFICATION WORK.
PRIOR DONE: SERVICE_NEXT_FIELD_PEER_HVAC_SANITARY_REUSE_GAP_AUDIT_V1
  → HVAC CONFIG_ONLY winner · Sanitary AUDITED deferred · registered NO
PRIOR DONE: SERVICE_APPLIANCE_SERVICE_VERSIONED_VERTICAL_CERTIFICATION_V1 (`cert-service-appliance-v1` CURRENT)
NEXT: SERVICE_HVAC_SERVICE_REFERENCE_VERTICAL_PROOF_V1 (BusinessForge)
NOT: HVAC/Sanitary App Factory forks · Sanitary parallel · GPS · production_active · new asset enums
STATUS: Electrician + Appliance Certificates CURRENT · production_active NO
DO NOT: invent HVAC packaging before reference proof · reopen Electrician/Appliance certification
```

Identity vs cert: customer/app label may say Reifenservice; technical certification stays AUTO (`cert-service-auto-workshop-v1`).  
Electrician / FIELD: Certificate **`cert-service-electrician-v1` CURRENT** · production_active **NO**.  
Appliance FIELD peer: Certificate **`cert-service-appliance-v1` CURRENT** · **CONFIG_ONLY** · production_active **NO**.  
HVAC: **AUDITED** only — proposed `hvac_service` / `field_service_hvac@v1` / `HVAC_SERVICE` — not packaged.  
Authority: BusinessForge `SERVICE_NEXT_FIELD_PEER_HVAC_SANITARY_REUSE_GAP_AUDIT_V1`.  
LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. Appointment demos unchanged. No APK/batch change in this slice.
