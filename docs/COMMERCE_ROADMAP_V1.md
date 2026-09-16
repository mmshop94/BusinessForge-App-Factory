# App Factory — Commerce Roadmap (pointer)

> Stand: 2026-09-16 · Docs-only · App Factory product surface unchanged (11/11)

| Item | Status |
|---|---|
| Village Store certificate | **`cert-commerce-village-store-v1` CURRENT** · production_active **NO** |
| Butcher certificate | **`cert-commerce-butcher-v1` CURRENT** · production_active **NO** · not in official sales demos |
| Farm Shop … Beverage Store | **CURRENT** (CONFIG_ONLY on `village_store@v1`) · production_active **NO** |
| Winery | **`cert-commerce-winery-v1` CURRENT** · CONFIG_ONLY · production_active **NO** · no `winery@v1` |
| Age Restriction | **PRESENT** (pickup + local delivery handoff; no digital ID/KYC) |
| App Factory reuse (age) | **READY** (shared store age fields; no `delivery_age@v1`) |
| App Factory reuse (winery) | **READY** (`BusinessType.WINERY` → `village_store@v1`) |
| Delivery / shipping fulfillment | Address core, rate engine, and manual shipment lifecycle **PRESENT** · local delivery **PARTIAL** |
| Local Delivery Age Verification | **PRESENT** (operator visual ID at handoff + server hard gate) |
| Shipping Age Verification Domain | **PRESENT** (port) · DHL Ident-Check adapter **PRESENT** (sandbox software) |
| External Carrier Age Adapter | **DHL_IDENT_CHECK_PRESENT** · DPD/GLS/UPS **NOT_IMPLEMENTED** |
| App Factory fulfillment reuse | **READY** (shared Commerce capability; no `shipping@v1` / `delivery@v1`) |
| App Factory carrier age reuse | **READY** (no `dhl@v1` / `ident-check@v1`) |
| Online payment (tenant Connect) | Software core **PRESENT** · account connection **PRESENT** · webhook + full refund **PRESENT** (Fake domain) |
| Stripe Connect live adapter | **PARTIAL** (Accounts v2 merchant+full; real testmode READY deferred / hosted onboarding) |
| App Factory online payment reuse | **READY** (shared Commerce capability; no `stripe@v1` / `payment@v1`; no per-tenant secrets in generated apps) |
| Production shipping checkout | **FUNCTIONALLY_READY_VIA_FAKE** · real Stripe **NOT_YET_PROVEN** |
| Age-restricted shipping | Software core **PRESENT** · production **NOT_READY** · **NOT_CERTIFIED** |
| Application fee / PayPal | **NOT_USED** / **NOT_REQUIRED** |
| Next shared core | **DHL_PRODUCTION_TENANT_CARRIER_ONBOARDING** (secure secrets + real entitlement) |

Online payment is configuration of the existing Commerce path, not a new factory
product family. Official sales demos remain 11/11 unchanged. No app generation
in this docs freeze. Account routing and Stripe secrets stay server-side.

Authority: BusinessForge  
`COMMERCE_ONLINE_PAYMENT_DOMAIN_BOUNDARY_V1.md` ·  
`COMMERCE_STRIPE_CONNECT_LIVE_ADAPTER_CLOSURE_V1.md`
