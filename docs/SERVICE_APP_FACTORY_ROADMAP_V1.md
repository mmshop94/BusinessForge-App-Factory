# App Factory — Service Roadmap V1

> Stand: 2026-09-13  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| ELECTRICIAN Certificate | **CURRENT** (`cert-service-electrician-v1`, production_active **NO**) |
| APPLIANCE_SERVICE Certificate | **CURRENT** (`cert-service-appliance-v1`, production_active **NO**) · **CONFIG_ONLY** |
| HVAC reference proof | **PROVEN** (H01–H24) · package `field_service_hvac@v1` / `HVAC_SERVICE` / `test-service-hvac` · Visual **NOT_PROVEN** · Certificate Ready **NO** |
| Sanitary | **AUDITED** · **UNREGISTERED** · deferred |
| App Factory mapping | `service_first` may list `field_service_hvac` under existing rules — **no** HVAC-specific forks; packaging wait for Visual/cert |
| Remaining | Wait for `SERVICE_HVAC_SERVICE_FULL_VISUAL_CROSSUI_V1` |

```text
PRIOR DONE: SERVICE_HVAC_SERVICE_REFERENCE_VERTICAL_PROOF_V1
NEXT: SERVICE_HVAC_SERVICE_FULL_VISUAL_CROSSUI_V1 (BusinessForge/E2E)
NOT: HVAC packaging forks · Sanitary parallel · GPS · production_active · certificate invent
```

LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. No APK/batch change in this slice.
