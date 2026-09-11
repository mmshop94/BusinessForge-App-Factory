# App Factory — Service Roadmap V1

> Stand: 2026-09-11  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| AUTO_WORKSHOP Certificate | **CURRENT** (production_active NO) / **UNCHANGED** |
| BICYCLE Certificate | **CURRENT** (`cert-service-bicycle-workshop-v1`, production_active **NO**) / **UNCHANGED** |
| MOTORCYCLE Certificate | **CURRENT** (`cert-service-motorcycle-workshop-v1`, production_active **NO**) · **PRODUCTION_APPROVED_WITH_FINDINGS** / **UNCHANGED** |
| BICYCLE | **CONFIG_ONLY** · Functional/Asset/Resource **PROVEN**; Visual/Cross-UI **PROVEN**; Load/Soak/Chaos **INHERITED** |
| MOTORCYCLE | **CONFIG_ONLY** · Functional **PROVEN** · Visual/Cross-UI **PROVEN** (`bf-e2e-visual-service-motorcycle-20260911-153956`) · Domain Ext **NO** · Material Div **NO** · asset **VEHICLE** · package **IMPLEMENTED** · runtime **ACCEPTED_DOCUMENTED_DEMO_FINGERPRINT** (`overlays/motorcycle-v1`) — **not reopened** |
| TIRE / Reifenservice | **CATALOG_ONLY_SPECIALIZATION** of AUTO · **non-certification boundary** · no tire package/cert · independent tenant/app/branding allowed without cert boundary |
| App Factory mapping | `service_first` covers bicycle + motorcycle package; tire-branded apps = product packaging on AUTO path, not a cert boundary |
| Remaining | AUTO tire catalog specialization (next) |

```text
NEXT APP FACTORY SERVICE ACTION: WAIT_FOR_SERVICE_AUTO_TIRE_CATALOG_SPECIALIZATION_V1
ALTERNATE: WAIT_FOR_SERVICE_AUTO_TIRE_CAPABILITY_PROFILE_V1
STATUS: READY / WAITING (NOT executed)
```

Authority: BusinessForge / E2E `SERVICE_TIRE_SERVICE_VERTICAL_VS_AUTO_CAPABILITY_AUDIT_V1`.  
LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. Appointment demos unchanged. No APK/batch change in this slice.
