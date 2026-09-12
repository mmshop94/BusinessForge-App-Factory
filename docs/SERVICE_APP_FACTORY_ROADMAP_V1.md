# App Factory — Service Roadmap V1

> Stand: 2026-09-12  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| AUTO_WORKSHOP Certificate | **CURRENT** (production_active NO) / **UNCHANGED** |
| BICYCLE Certificate | **CURRENT** (`cert-service-bicycle-workshop-v1`, production_active **NO**) / **UNCHANGED** |
| MOTORCYCLE Certificate | **CURRENT** (`cert-service-motorcycle-workshop-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** / **UNCHANGED** |
| BICYCLE | **CONFIG_ONLY** · Functional/Asset/Resource **PROVEN**; Visual/Cross-UI **PROVEN**; Load/Soak/Chaos **INHERITED** |
| MOTORCYCLE | **CONFIG_ONLY** · Functional **PROVEN** · Visual/Cross-UI **PROVEN** (`bf-e2e-visual-service-motorcycle-20260911-153956`) · Domain Ext **NO** · Material Div **NO** · asset **VEHICLE** · package **IMPLEMENTED** · runtime **ACCEPTED_DOCUMENTED_DEMO_FINGERPRINT** (`overlays/motorcycle-v1`) — **not reopened** |
| TIRE / Reifenservice | **CATALOG_ONLY_SPECIALIZATION** · `auto_tire` **READY** · **non-certification boundary** · no tire package/cert · customer identity may be Reifenservice; certification identity remains AUTO_WORKSHOP |
| ELECTRICIAN / FIELD | Gap audit **DONE** · FIELD core **SEALED** · Reference FIELD proof **PROVEN** (E01–E24) · FIELD Load25 **PROVEN** · FIELD Load50 **PROVEN** · FIELD Soak60 **PROVEN** · FIELD Chaos **PROVEN** · FIELD Class Evidence Bundle **`service-field-evidence-v1` CURRENT / READY** · FIELD Class Evidence Complete **YES** · Engine **REUSED** · Separate engine **NO** · Appointment→site **PROVEN** · Certificate Ready **NO** · certificate **NO** |
| App Factory mapping | `service_first` + commercial `catalog_specialization_options()` — tire is **not** a COMMERCIAL_VERTICAL/package; FIELD/electrician product packaging waits for Visual |
| Remaining | wait for `SERVICE_ELECTRICIAN_FULL_VISUAL_CROSSUI_V1` |

```text
NEXT APP FACTORY SERVICE ACTION: WAIT_FOR_SERVICE_ELECTRICIAN_FULL_VISUAL_CROSSUI_V1
SCOPE WAIT: Electrician Full Visual + Cross-UI (vertical-specific; not class bundle)
PRIOR DONE: WAIT_FOR_SERVICE_FIELD_EVIDENCE_BUNDLE_V1 (`service-field-evidence-v1` CURRENT / READY)
THEN (upstream): Certificate
NOT: electrician-specific App Factory forks · GPS · certificate · tire storage
STATUS: READY / WAITING (NOT executed)
DO NOT: implement tire storage · treat auto_tire as a cert vertical · mint electrician cert · electrician packaging fork
```

Identity vs cert: customer/app label may say Reifenservice; technical certification stays AUTO (`cert-service-auto-workshop-v1`).  
Electrician / FIELD: Bundle **CURRENT / READY** · Class Evidence Complete **YES** · Certificate Ready **NO** — wait for Visual/Cross-UI before packaging.  
Authority: BusinessForge / E2E `SERVICE_FIELD_EVIDENCE_BUNDLE_V1`.  
LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. Appointment demos unchanged. No APK/batch change in this slice.
