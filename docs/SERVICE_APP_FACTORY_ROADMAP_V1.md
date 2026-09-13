# App Factory — Service Roadmap V1

> Stand: 2026-09-13  
> Official sales batch remains **11/11** without Service.

## Status

| Item | Status |
|---|---|
| ELECTRICIAN Certificate | **CURRENT** (`cert-service-electrician-v1`, production_active **NO**) |
| APPLIANCE_SERVICE Certificate | **CURRENT** (`cert-service-appliance-v1`, production_active **NO**) · **CONFIG_ONLY** |
| HVAC Certificate | **CURRENT** (`cert-service-hvac-v1`, production_active **NO**) · **CONFIG_ONLY** |
| Sanitary | **AUDITED** · **UNREGISTERED** · deferred |
| DEVICE_SHOP | **REGISTERED** · Architecture **B** · **SHOP_SERVICE** · **MINOR_EXTENSION** · D01–D24 **PROVEN** · Visual **PROVEN** · Cross-UI **PROVEN** · Certificate Ready **YES** · issued **NO** |
| App Factory mapping | `service_first` may list `service_device_shop` under existing rules — **no** DEVICE_SHOP-specific forks; packaging wait for certificate |

```text
PRIOR DONE: SERVICE_DEVICE_SHOP_FULL_VISUAL_CROSSUI_V1
  → bf-e2e-visual-service-device-shop-20260913-065614 PASS
NEXT WAIT: SERVICE_DEVICE_SHOP_VERSIONED_VERTICAL_CERTIFICATION_V1
STOP HVAC CERTIFICATION WORK.
NOT: DEVICE_SHOP packaging forks · Sanitary parallel · third Service class · GPS · production_active · certificate invent
```

LIVE=0 · Deploy=0 · Push=0 · Production mutation=0 · Production Active=NO. No APK/batch change in this slice.
