# App Factory — Commerce Roadmap (pointer)

> Stand: 2026-09-16 · Docs-only · App Factory product surface unchanged (11/11)

| Item | Status |
|---|---|
| Village Store certificate | **`cert-commerce-village-store-v1` CURRENT** · production_active **NO** |
| Butcher certificate | **`cert-commerce-butcher-v1` CURRENT** · production_active **NO** · not in official sales demos |
| Farm Shop … Beverage Store | **CURRENT** (CONFIG_ONLY on `village_store@v1`) · production_active **NO** |
| Winery | **`cert-commerce-winery-v1` CURRENT** · CONFIG_ONLY · production_active **NO** · no `winery@v1` |
| Age Restriction | **PRESENT** (operator pickup verification; no digital ID/KYC) |
| App Factory reuse (age) | **READY** (shared store age fields) |
| App Factory reuse (winery) | **READY** (`BusinessType.WINERY` → `village_store@v1`) |
| Delivery / shipping fulfillment | Address core, rate engine, and manual shipment lifecycle **PRESENT** · local delivery **PARTIAL** |
| App Factory fulfillment reuse | **READY** (shared Commerce capability; no `shipping@v1` / `delivery@v1`) |
| Online payment (tenant Connect) | Software core **PRESENT** · account connection **PRESENT** · webhook + full refund **PRESENT** |
| App Factory online payment reuse | **READY** (shared Commerce capability; no `stripe@v1` / `payment@v1`) |
| Production shipping checkout | **READY** (via online card + READY account) |
| Age-restricted shipping | **NOT_CERTIFIED** |
| Application fee / PayPal | **NOT_USED** / **NOT_REQUIRED** |
| Next shared core | **DELIVERY_AGE_VERIFICATION** |

Online payment is configuration of the existing Commerce path, not a new factory
product family. Official sales demos remain 11/11 unchanged. No app generation
in this docs freeze.

Authority: BusinessForge
`COMMERCE_ONLINE_PAYMENT_DOMAIN_BOUNDARY_V1.md`
