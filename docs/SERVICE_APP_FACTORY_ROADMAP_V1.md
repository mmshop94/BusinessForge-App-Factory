# App Factory — Service Roadmap V1

> Stand: 2026-09-13  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| ELECTRICIAN Certificate | **CURRENT** (`cert-service-electrician-v1`, production_active **NO**) |
| APPLIANCE_SERVICE Certificate | **CURRENT** (`cert-service-appliance-v1`, production_active **NO**) · **CONFIG_ONLY** |
| HVAC Full Visual + Cross-UI | **PROVEN** · `bf-e2e-visual-service-hvac-20260913-052502` · package `field_service_hvac@v1` / `HVAC_SERVICE` / `test-service-hvac` · Certificate Ready **YES** · issued **NO** |
| Sanitary | **AUDITED** · **UNREGISTERED** · deferred |
| App Factory mapping | `service_first` may list `field_service_hvac` under existing rules — **no** HVAC-specific forks; packaging wait for Visual/cert |
| Remaining | Wait for `SERVICE_HVAC_SERVICE_VERSIONED_VERTICAL_CERTIFICATION_V1` (compose only) |

```text
PRIOR DONE: SERVICE_HVAC_SERVICE_FULL_VISUAL_CROSSUI_V1
NEXT: SERVICE_HVAC_SERVICE_VERSIONED_VERTICAL_CERTIFICATION_V1 (BusinessForge/E2E compose)
NOT: HVAC packaging forks · Sanitary parallel · GPS · production_active · certificate invent
```

LIVE=0 · Deploy=0 · Push=0 · Demo mutation=0 · Production mutation=0 · Production Active=NO. No APK/batch change in this slice.
