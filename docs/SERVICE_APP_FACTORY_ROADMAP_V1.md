# App Factory — Service Roadmap V1

> Stand: 2026-09-12  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| AUTO_WORKSHOP Certificate | **CURRENT** (production_active NO) / **UNCHANGED** |
| BICYCLE Certificate | **CURRENT** (`cert-service-bicycle-workshop-v1`, production_active **NO**) / **UNCHANGED** |
| MOTORCYCLE Certificate | **CURRENT** (`cert-service-motorcycle-workshop-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** / **UNCHANGED** |
| ELECTRICIAN Certificate | **CURRENT** (`cert-service-electrician-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** |
| BICYCLE | **CONFIG_ONLY** · Functional/Asset/Resource **PROVEN**; Visual/Cross-UI **PROVEN**; Load/Soak/Chaos **INHERITED** |
| MOTORCYCLE | **CONFIG_ONLY** · Functional **PROVEN** · Visual/Cross-UI **PROVEN** (`bf-e2e-visual-service-motorcycle-20260911-153956`) · Domain Ext **NO** · Material Div **NO** · asset **VEHICLE** · package **IMPLEMENTED** · runtime **ACCEPTED_DOCUMENTED_DEMO_FINGERPRINT** (`overlays/motorcycle-v1`) — **not reopened** |
| TIRE / Reifenservice | **CATALOG_ONLY_SPECIALIZATION** · `auto_tire` **READY** · **non-certification boundary** · no tire package/cert · customer identity may be Reifenservice; certification identity remains AUTO_WORKSHOP |
| ELECTRICIAN / FIELD | **NEW_SERVICE_CLASS** · FIELD core **SEALED** · Reference FIELD proof **PROVEN** (E01–E24) · FIELD Load/Soak/Chaos **PROVEN** · FIELD Class Evidence Bundle **`service-field-evidence-v1` CURRENT / READY** · Full Visual + Cross-UI **PROVEN** (`bf-e2e-visual-service-electrician-20260912-042927`) · Certificate **CURRENT** · production_active **NO** |
| App Factory mapping | `service_first` + commercial `catalog_specialization_options()` — tire is **not** a COMMERCIAL_VERTICAL/package; electrician packaging may proceed under **existing** App Factory rules (**no** electrician-specific forks) |
| Remaining | Next: `SERVICE_APPLIANCE_SERVICE_REFERENCE_VERTICAL_PROOF_V1` after gap audit (proposed `appliance_service` CONFIG_ONLY — not registered) |

```text
NEXT APP FACTORY SERVICE ACTION: WAIT_FOR_SERVICE_APPLIANCE_SERVICE_REFERENCE_VERTICAL_PROOF_V1
PRIOR DONE: SERVICE_NEXT_FIELD_VERTICAL_REUSE_GAP_AUDIT_V1
  → appliance_service = CONFIG_ONLY FIELD peer (proposed field_service_appliance@v1 / APPLIANCE_SERVICE — NOT registered)
  → FIELD bundle REUSABLE_WITH_CONDITIONS · Load/Soak/Chaos repeat NO · Visual vertical-specific
PRIOR DONE: WAIT_FOR_SERVICE_ELECTRICIAN_VERSIONED_VERTICAL_CERTIFICATION_V1 (`cert-service-electrician-v1` CURRENT · production_active NO)
PRIOR DONE: WAIT_FOR_SERVICE_ELECTRICIAN_FULL_VISUAL_CROSSUI_V1 (`bf-e2e-visual-service-electrician-20260912-042927` PASS)
PRIOR DONE: WAIT_FOR_SERVICE_FIELD_EVIDENCE_BUNDLE_V1 (`service-field-evidence-v1` CURRENT / READY)
STOP: Electrician certification work / Electrician certification wait
NOT: electrician-specific App Factory forks · GPS · production_active · new asset enums · dual SHOP+FIELD for on-site appliance
STATUS: Electrician Certificate CURRENT — packaging may proceed under existing rules
DO NOT: invent electrician packaging forks · implement tire storage · treat auto_tire as a cert vertical · reopen Electrician certification
```

Identity vs cert: customer/app label may say Reifenservice; technical certification stays AUTO (`cert-service-auto-workshop-v1`).  
Electrician / FIELD: Certificate **`cert-service-electrician-v1` CURRENT** · production_active **NO** — **STOP** Electrician certification wait; packaging under existing App Factory rules only.  
Next FIELD peer (audit): proposed **`appliance_service`** · **CONFIG_ONLY** · authority BusinessForge `SERVICE_NEXT_FIELD_VERTICAL_REUSE_GAP_AUDIT_V1` — **not registered** / no App Factory packaging yet.  
Authority: BusinessForge / E2E `SERVICE_ELECTRICIAN_VERSIONED_VERTICAL_CERTIFICATION_V1`.  
LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. Appointment demos unchanged. No APK/batch change in this slice.
