### First Live Google Play Internal Track Proof + Customer Onboarding Gate V1

* Canonical Play external setup contract, `CUSTOMER_OWNED` vs `BUSINESSFORGE_REFERENCE` owner types, `google-play preflight` / setup-contract / onboarding CLI, package immutability after bind, tester group references, live evidence without secrets. Live Google remains `BLOCKED_EXTERNAL` until `REAL_GOOGLE_PLAY_INTERNAL_TEST=1` and a wired app-scoped credential exist. Production still `NOT_IMPLEMENTED`.
* Docs: [ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md](docs/ANDROID_GOOGLE_PLAY_ONBOARDING_GATE_V1.md). Tests: `tests/test_play_onboarding_gate.py` (live test skipped by default).

### Android Customer Play Connection + Test-Track Delivery V1

* App-scoped Play publisher connection, INTERNAL test-track provider (fake proven, live fail-closed), per-customer upload-key fingerprint, production track hard-block. No production submission.
* Docs: [ANDROID_CUSTOMER_PLAY_TEST_TRACK_DELIVERY_V1.md](docs/ANDROID_CUSTOMER_PLAY_TEST_TRACK_DELIVERY_V1.md).

### Customer App Release Intake + Android Signing Foundation V1

* `prepare-customer-release`: immutable snapshot, ANDROID_ONLY / IOS_ONLY / ANDROID_AND_IOS gates, per-customer signing references, shared Owner-Keystore forbidden for production customers. 35/35 generate path retained. No Play upload.
* Docs: [CUSTOMER_APP_RELEASE_INTAKE_V1.md](docs/CUSTOMER_APP_RELEASE_INTAKE_V1.md). Tests: `tests/test_customer_release_intake.py`.

### White-Label App + Store Delivery Readiness V1

* Config proof: 35 official slugs map to a compatible package and Flutter journey (`tests/test_official_sales_generate_path.py`). No 35 native builds. No Play/App Store upload.

### Official Demo Visual + Presentation Readiness V2

* `butcher` added to `customer-app-compat-v1.json` (same floor as `village_store`). Official generate path 35/35. Store-grade still 0/35. No APK rebuild. No push.

### Service Caretaker Package + Versioned Vertical Certification V1

* `demo-caretaker` added to `OFFICIAL_SALES_DEMO_SLUGS` (35). Package `field_service_caretaker` in `customer-app-compat-v1.json`.
* `APP_FACTORY_CARETAKER: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Landscaping Service Package + Versioned Vertical Certification V1

* `demo-landscaping-service` added to `OFFICIAL_SALES_DEMO_SLUGS` (34). Package `field_service_landscaping` in `customer-app-compat-v1.json`.
* `APP_FACTORY_LANDSCAPING_SERVICE: READY`. Proof tenant `test-service-*` excluded. Distinct from `demo-garden-center`. No app generation. No push.

### Service Cleaning Service Package + Versioned Vertical Certification V1

* `demo-cleaning-service` added to `OFFICIAL_SALES_DEMO_SLUGS` (33). Package `field_service_cleaning` in `customer-app-compat-v1.json`.
* `APP_FACTORY_CLEANING_SERVICE: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Vehicle Detailing Package + Versioned Vertical Certification V1

* `demo-vehicle-detailing` added to `OFFICIAL_SALES_DEMO_SLUGS` (32). Package `service_vehicle_detailing` in `customer-app-compat-v1.json`.
* `APP_FACTORY_VEHICLE_DETAILING: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Commerce Pet Supply Versioned Certification + Official Sales Demo V1

* `demo-pet-supply` added to `OFFICIAL_SALES_DEMO_SLUGS` (31). Runtime consume `village_store` (no `pet_supply` factory package). Distinct from `demo-pet-grooming`.
* `APP_FACTORY_PET_SUPPLY: READY`. Proof tenant `test-commerce-*` excluded. No app generation. No push.

### Commerce Garden Center Versioned Certification + Official Sales Demo V1

* `demo-garden-center` added to `OFFICIAL_SALES_DEMO_SLUGS` (30). Runtime consume `village_store` (no `garden_center` factory package).
* `APP_FACTORY_GARDEN_CENTER: READY`. Proof tenant `test-commerce-*` excluded. No app generation. No push.

### Commerce Fish Shop Versioned Certification + Official Sales Demo V1

* `demo-fish-shop` added to `OFFICIAL_SALES_DEMO_SLUGS` (29). Runtime consume `village_store` (no `fish_shop` factory package).
* `APP_FACTORY_FISH_SHOP: READY`. Proof tenant `test-commerce-*` excluded. No app generation. No push.

### Commerce Cheese Shop Versioned Certification + Official Sales Demo V1

* `demo-cheese-shop` added to `OFFICIAL_SALES_DEMO_SLUGS` (28). Runtime consume `village_store` (no `cheese_shop` factory package).
* `APP_FACTORY_CHEESE_SHOP: READY`. Proof tenant `test-commerce-*` excluded. No app generation. No push.

### Sanitary Service Package + Versioned Vertical Certification V1

* `demo-sanitary-service` added to `OFFICIAL_SALES_DEMO_SLUGS` (27). Package `field_service_sanitary` in `customer-app-compat-v1.json`.
* `APP_FACTORY_SANITARY_SERVICE: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Auto Workshop Official Sales Demo V1

* `demo-auto-workshop` added to `OFFICIAL_SALES_DEMO_SLUGS` (26). `demo-workshop` excluded. Package `service_auto_workshop` in `customer-app-compat-v1.json`.
* `APP_FACTORY_AUTO_WORKSHOP: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service HVAC Service Field Official Sales Demo V1

* `demo-hvac-service` added to `OFFICIAL_SALES_DEMO_SLUGS` (25). Package `field_service_hvac` in `customer-app-compat-v1.json`.
* `APP_FACTORY_HVAC_SERVICE: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Appliance Service Field Official Sales Demo V1

* `demo-appliance-service` added to `OFFICIAL_SALES_DEMO_SLUGS` (24). Package `field_service_appliance` in `customer-app-compat-v1.json`.
* `APP_FACTORY_APPLIANCE_SERVICE: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Electrician Field Official Sales Demo V1

* `demo-electrician` added to `OFFICIAL_SALES_DEMO_SLUGS` (23). Package `field_service_electrician` in `customer-app-compat-v1.json`.
* `APP_FACTORY_ELECTRICIAN: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Motorcycle Workshop Official Sales Demo V1

* `demo-motorcycle-workshop` added to `OFFICIAL_SALES_DEMO_SLUGS` (22). Package `service_motorcycle_workshop` in `customer-app-compat-v1.json`.
* `APP_FACTORY_MOTORCYCLE_WORKSHOP: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Device Shop Official Sales Demo V1

* `demo-device-shop` added to `OFFICIAL_SALES_DEMO_SLUGS` (21). Package `service_device_shop` in `customer-app-compat-v1.json`.
* `APP_FACTORY_DEVICE_SHOP: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Service Bicycle Workshop Official Sales Demo V1

* `demo-bicycle-workshop` added to `OFFICIAL_SALES_DEMO_SLUGS` (20). Package `service_bicycle_workshop` in `customer-app-compat-v1.json`.
* `APP_FACTORY_BICYCLE_WORKSHOP: READY`. Proof tenant `test-service-*` excluded. No app generation. No push.

### Commerce Stripe Connect Hosted Onboarding Domain Boundary V1

* Docs: shared Stripe Connect Account + Hosted Onboarding + Connected Account payment readiness; no vertical Connect package.
* `APP_FACTORY_STRIPE_CONNECT_REUSE: READY`. Human onboarding / production account proofs NOT_EXECUTED; testmode account proof NOT_CONFIGURED; Real Online Payment Provider remains DEFERRED. Flutter NOT_REQUIRED. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Integrated Payment Terminal Domain Boundary V1

* Docs: shared backend integrated payment terminal (Stripe Terminal Connect Direct Charge + Simulated S700 software path); no `stripe-terminal@v1` package.
* `APP_FACTORY_PAYMENT_TERMINAL_REUSE: READY`. Physical S700 NOT_EXECUTED; Stripe Terminal Connect testmode live proof NOT_CONFIGURED; Hosted Onboarding Core PRESENT (live account proofs separate); server-driven offline NOT_SUPPORTED_V1; terminal production readiness BLOCKED_BY_CONNECTED_ACCOUNT or NOT_CONFIGURED. Flutter NOT_REQUIRED. 11/11 sales demos unchanged. No app generation. No push.

### Commerce German Fiscalization / Certified TSE + DSFinV-K Domain Boundary V1

* Docs: shared backend German fiscalization (Fiskaly SIGN DE V2 adapter + DSFinV-K software core); no `tse@v1` / `fiskaly@v1` packages.
* `APP_FACTORY_FISCALIZATION_REUSE: READY`. Fiskaly testsystem / production credentials NOT_CONFIGURED; DE POS production fiscal readiness NOT_CONFIGURED; §146a(4) electronic submission OUT_OF_SCOPE_V1; DSFinV-K FA import NOT_EXECUTED. Flutter NOT_REQUIRED. 11/11 sales demos unchanged. No app generation. No push.

### Commerce POS / Operator Checkout Domain Boundary V1

* Docs: shared backend POS / operator counter checkout software core; no `pos@v1` package.
* `APP_FACTORY_POS_REUSE: READY`. Certified TSE NOT_IMPLEMENTED; DSFinV-K / payment terminal OUT_OF_SCOPE_V1; Flutter POS operator NOT_REQUIRED. DE production fiscal readiness NOT_READY. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Nutrition Declaration Domain Boundary V1

* Docs: shared backend nutrition declaration (manual / lab / recipe-calc) + checkout gate; no `nutrition@v1` package.
* `APP_FACTORY_NUTRITION_REUSE: READY`. Vitamins PARTIAL_OPTIONAL; wine PARTIAL_SECTOR_OVERRIDE. Full LMIV not certified. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Lot-Level Inventory / FEFO Domain Boundary V1

* Docs: shared backend lot balances + FEFO on LOT_TRACKED products; no `inventory-lot@v1` / `fefo@v1` packages.
* `APP_FACTORY_LOT_INVENTORY_REUSE: READY`. Multi-lot split / auto reallocation out of scope. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Food Recall Management Domain Boundary V1

* Docs: shared withdrawal/recall workflow + customer-safe order notices; no `recall@v1` / `food-safety@v1` packages.
* `APP_FACTORY_RECALL_REUSE: READY`. Authority APIs out of scope. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Food MHD / Use-By / Batch Traceability Domain Boundary V1

* Docs: shared food lot/date/traceability on customer product detail when lot known; no `expiry@v1` / `batch@v1` / `traceability@v1` packages.
* `APP_FACTORY_TRACEABILITY_REUSE: READY`. Recall/cold-chain not claimed. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Meat Origin / Provenance Domain Boundary V1

* Docs: shared published meat provenance on customer product detail; no `meat-origin@v1` / `provenance@v1` packages.
* `APP_FACTORY_PROVENANCE_REUSE: READY`. Full meat labelling not certified. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Food Ingredient / Allergen Labeling Domain Boundary V1

* Docs: shared published food information (ingredients/allergens) on customer product detail; no `food@v1` / `allergen@v1` packages.
* `APP_FACTORY_FOOD_INFORMATION_REUSE: READY`. Full LMIV not certified. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Stripe Connect Live Adapter Closure V1

* Docs: Stripe Connect adapter PARTIAL; shipping **FUNCTIONALLY_READY_VIA_FAKE**; real Stripe NOT_YET_PROVEN.
* `APP_FACTORY_ONLINE_PAYMENT_REUSE: READY` (no per-tenant secrets in generated apps). No push.

### Commerce Stripe Connect Live Adapter Closure V1

* Docs: Stripe Connect adapter PARTIAL; shipping **FUNCTIONALLY_READY_VIA_FAKE**; real Stripe NOT_YET_PROVEN.
* `APP_FACTORY_ONLINE_PAYMENT_REUSE: READY` (no per-tenant secrets in generated apps). No push.

### Commerce Online Payment Domain Boundary V1

* Docs: shared Commerce online-payment capability; `APP_FACTORY_ONLINE_PAYMENT_REUSE: READY`.
* No `stripe@v1` / `payment@v1` packages; 11/11 sales demos unchanged. No app generation. No push.

### Commerce Delivery / Shipping Fulfillment Domain Boundary V1

* Docs: shared Commerce fulfillment capability; `APP_FACTORY_FULFILLMENT_REUSE: READY`.
* No `shipping@v1` / `delivery@v1` packages; 11/11 sales demos unchanged. No app generation. No push.

### Commerce Winery Product Certification V1

* Docs: `cert-commerce-winery-v1` CURRENT · production_active NO · `WINERY` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Winery Vertical Proof V1

* Consume proof: `WINERY` → `village_store@v1` + `FEATURE_VILLAGE_STORE`; no `FEATURE_WINERY` / `winery@v1`.
* App Factory reuse **READY**. 11/11 sales demos unchanged. No app generation. No push.

### Commerce Winery Certification Gap + Reuse Audit V1

* Docs: Winery CONFIG_ONLY on village_store@v1; App Factory reuse **READY** after BusinessType registration. 11/11 demos unchanged. No push.

### Commerce Age Restriction / ID Validation Domain Boundary V1

* Docs: shared age-restriction core **PRESENT**; App Factory reuse **READY** (shared store fields; no winery@v1).
* 11/11 sales demos unchanged. No app generation. No push.

### Commerce Beverage Store Product Certification V1

* Docs: `cert-commerce-beverage-store-v1` CURRENT · production_active NO · `BEVERAGE_STORE` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Beverage Store Vertical Proof V1

* App Factory reuse **READY**: `BEVERAGE_STORE` → `village_store@v1` consume; no beverage package. No push.

### Commerce Beverage Store Certification Gap + Reuse Audit V1

* Docs: beverage CONFIG_ONLY on village_store@v1; App Factory reuse **PARTIAL** until BusinessType exists. 11/11 demos unchanged. No push.

### Commerce Deposit / Reusable Packaging Domain Boundary V1

* Docs: deposit software core PRESENT on shared village_store Commerce path; `APP_FACTORY_DEPOSIT_REUSE: READY`.
* No deposit package. No beverage app generation. 11/11 sales demos unchanged. No push.

### Commerce Delicatessen Product Certification V1

* Docs: `cert-commerce-delicatessen-v1` CURRENT · production_active NO · `DELICATESSEN` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Delicatessen Vertical Proof V1

* Consume proof: `village_store@v1` + `FEATURE_VILLAGE_STORE`; `DELICATESSEN` is BusinessType, not a factory package.
* `APP_FACTORY_REUSE: READY`. Official sales demos 11/11 unchanged. No app generation. No push.

### Commerce Delicatessen Certification Gap + Reuse Audit V1

* Docs: `DELICATESSEN_CONFIG_ONLY_CONFIRMED` · delicatessen **AUDITED** · **NOT_READY**; 11/11 unchanged.
* App Factory can consume `village_store@v1` (READY). No `delicatessen@v1`. No app generation. No push.

### Commerce Florist Product Certification V1

* Docs: `cert-commerce-florist-v1` CURRENT · production_active NO · `FLORIST` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Florist Vertical Proof V1

* Consume proof: `village_store@v1` + `FEATURE_VILLAGE_STORE`; `FLORIST` is BusinessType, not a factory package.
* `APP_FACTORY_REUSE: READY`. Official sales demos 11/11 unchanged. No app generation. No push.

### Commerce Florist Certification Gap + Reuse Audit V1

* Docs: `FLORIST_CONFIG_ONLY_CONFIRMED` · florist **AUDITED** · **NOT_READY**; 11/11 unchanged.
* App Factory can consume `village_store@v1` (READY). No `florist@v1`. No app generation. No push.

### Commerce Bakery Product Certification V1

* Docs: `cert-commerce-bakery-v1` CURRENT · production_active NO · `BAKERY` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Bakery Vertical Proof V1

* Consume proof: `village_store@v1` + `FEATURE_VILLAGE_STORE`; `BAKERY` is BusinessType, not a factory package.
* `APP_FACTORY_REUSE: READY`. Official sales demos 11/11 unchanged. No app generation. No push.

### Commerce Bakery Certification Gap + Reuse Audit V1

* Docs: `BAKERY_CONFIG_ONLY_CONFIRMED` · bakery **AUDITED** · **NOT_READY**; 11/11 unchanged.
* App Factory can consume `village_store@v1` (READY). No `bakery@v1`. No app generation. No push.

### Commerce Farm Shop Product Certification V1

* Docs: `cert-commerce-farm-shop-v1` CURRENT · production_active NO · `FARM_SHOP` via `village_store@v1`; 11/11 sales demos unchanged.
* `APP_FACTORY_REUSE: READY`. No app generation. No push.

### Commerce Farm Shop Vertical Proof V1

* Consume proof: `village_store@v1` + `FEATURE_VILLAGE_STORE`; `FARM_SHOP` is BusinessType, not a factory package.
* `APP_FACTORY_REUSE: READY`. Official sales demos 11/11 unchanged. No app generation. No push.

### Commerce Farm Shop Certification Gap + Reuse Audit V1

* Docs: `FARM_SHOP_CONFIG_ONLY_CONFIRMED` · farm_shop **AUDITED** · **NOT_READY**; 11/11 unchanged.
* App Factory can consume `village_store@v1` (PARTIAL). No `farm_shop@v1`. No app generation. No push.

### Commerce Butcher Product Certification V1

* Docs: `cert-commerce-butcher-v1` CURRENT · production_active NO · butcher@v1 still not in official sales demos; 11/11 unchanged.
* No app generation. No push.

### Commerce Butcher Measured Vertical Proof V1

* Docs: butcher measured proof **PASS / READY**; certificate still NOT_ISSUED; 11/11 unchanged.
* No push.

### Commerce Catch-Weight / Unit-Pricing Domain Boundary V1

* Docs: Commerce further-cert **CONTINUE**; catch-weight **PARTIAL**; butcher cert still NOT_ISSUED; 11/11 unchanged.
* No push.

### Commerce Physical Retail Capability Gap Audit V1

* Docs: Commerce further-cert **PAUSE_FOR_CORE_GAPS**; wait for catch-weight / unit-pricing domain boundary; 11/11 unchanged.
* No push.

### Commerce Butcher Certification Gap + Reuse Audit V1

* Docs: Butcher CONFIG_ONLY_CONFIRMED; wait for Reference Contract + Functional; 11/11 unchanged.
* No push.

### Commerce Village Store Certificate V1

* Docs: Village Store certificate CURRENT · production_active NO; wait for Butcher gap audit; 11/11 unchanged.
* No push.

### Commerce Engine Evidence Bundle V1 + Village Store Certification Readiness V1

* Docs: wait for Village Store Certificate V1; 11/11 unchanged.
* No push.

### Commerce Village Store Communication Proof V1

* Docs: wait for Engine Evidence Bundle + Village Store Certification Readiness; 11/11 unchanged.
* No push.

### Commerce Village Store CHAOS Proof V1

* Docs: wait for Village Store Communication; 11/11 unchanged.
* No push.

### Commerce Village Store SOAK60 Proof V1

* Docs: wait for Village Store Chaos; 11/11 unchanged.
* No push.

### Commerce Village Store LOAD25 + LOAD50 Proof V1

* Docs: wait for Village Store Soak60; 11/11 unchanged.
* No push.

### Commerce Village Store Full Visual + Cross-UI Proof V1

* Docs: wait for Village Store Load25 + Load50; 11/11 unchanged.
* No push.

### Commerce Village Store Cross-Layer Proof V1

* Docs: wait for Village Store Full Visual + Cross-UI; 11/11 unchanged.
* No push.

### Commerce Village Store Reference Contract + Functional Proof V1

* Docs: wait for Village Store Cross-Layer proof; 11/11 unchanged.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Commerce Engine Certification Baseline + Village Store Gap Audit V1

* Docs: wait for Village Store reference functional proof; 11/11 unchanged; no packaging forks.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Global Vertical Certification Coverage + Remaining Roadmap Audit V1

* Docs: wait for Commerce village_store certification baseline; Service enablement DEFERRED; 11/11 unchanged.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service First Real Pilot Production Enablement V1

* Docs: AUTO enablement path DEFINED; wait for real owner input then controlled provisioning.
* No packaging forks; 11/11 unchanged; production_active NO.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service Production Readiness + Activation Gap Audit V1

* Docs: wait for `SERVICE FIRST REAL PILOT PRODUCTION ENABLEMENT V1`; no packaging forks; 11/11 unchanged.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service SHOP Evidence Bundle V1

* Docs: `service-shop-evidence-v1` CURRENT/READY; wait for production readiness audit; no packaging forks; 11/11 unchanged.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service SHOP + FIELD Coverage Consolidation V1

* Docs: expansion SATURATED · wait for `SERVICE_SHOP_EVIDENCE_BUNDLE_V1`; no packaging forks; 11/11 sales batch unchanged.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service DEVICE_SHOP Versioned Vertical Certification V1

* Mirror `cert-service-device-shop-v1` CURRENT · production_active NO.
* Packaging wait under existing `service_first` rules — no DEVICE_SHOP forks.
* STOP DEVICE SHOP CERTIFICATION WORK. Next consolidation wait. No push.


### Service DEVICE_SHOP Demo Bootstrap + Visual Reproof V1

* Visual/Cross-UI **PROVEN** · Certificate Ready **YES** · run f-e2e-visual-service-device-shop-20260913-065614.
* Roadmap wait for SERVICE_DEVICE_SHOP_VERSIONED_VERTICAL_CERTIFICATION_V1. No packaging forks. No push.


### Service DEVICE_SHOP Vertical Contract + Reference Proof V1

* DEVICE_SHOP REGISTERED / D01-D24 PROVEN / Certificate Ready NO / Visual NOT_PROVEN.
* Packaging wait for Visual under existing service_first rules; no DEVICE_SHOP forks.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service DEVICE_SHOP Class + Device Repair Gap Audit V1

* Audit only: DEVICE_SHOP = Architecture **B** / **SHOP_SERVICE** / **MINOR_EXTENSION** / **not** a third class / **not registered**.
* No App Factory packaging / Handy forks / wait for optional vertical contract/proof.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service HVAC Service Versioned Vertical Certification V1

* HVAC certificate **CURRENT** · packaging under existing `field_service_*` rules · **no** HVAC forks.
* **STOP HVAC CERTIFICATION WORK.** Sanitary remains unregistered.
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

### Service HVAC Service Full Visual + Cross-UI Proof V1

* HVAC Visual/Cross-UI **PROVEN** · Certificate Ready **YES** · issued **NO**.
* Packaging still waits for versioned vertical certification (compose only).
* Roadmap: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md). No push.

All notable changes to BusinessForge App Factory are documented here.

## [Unreleased]

### Added

- Docs: HVAC Service reference vertical **PROVEN** (H01â€“H24) Â· package `field_service_hvac@v1` / `HVAC_SERVICE` / `test-service-hvac` Â· Certificate Ready **NO** Â· Visual **NOT_PROVEN** Â· wait for `SERVICE_HVAC_SERVICE_FULL_VISUAL_CROSSUI_V1`; no HVAC App Factory forks; Sanitary remains AUDITED/UNREGISTERED; not GPS; 11/11 sales batch unchanged.
- Docs: Next FIELD Peer HVAC vs Sanitary Reuse + Gap Audit V1 â€” both **CONFIG_ONLY** Â· winner **HVAC** (`hvac_service` / `field_service_hvac@v1` / `HVAC_SERVICE` â€” **not registered**) Â· Sanitary **AUDITED** deferred Â· FIELD bundle REUSABLE_WITH_CONDITIONS Â· wait for `SERVICE_HVAC_SERVICE_REFERENCE_VERTICAL_PROOF_V1`; no HVAC/Sanitary App Factory forks yet; not GPS; 11/11 sales batch unchanged. (historical wait; reference proof now PROVEN)
- Docs: Appliance Certificate **CURRENT** (`cert-service-appliance-v1`, production_active **NO**, PRODUCTION_APPROVED_WITH_FINDINGS, **CONFIG_ONLY**) after certification V1 Â· **STOP** Appliance certification wait Â· packaging may proceed under existing App Factory rules without inventing appliance forks Â· next prefer FIELD CONFIG_ONLY audit before NEW_SERVICE_CLASS; not GPS; 11/11 sales batch unchanged. (historical wait; HVAC vs Sanitary audit now DONE)
- Docs: Appliance Full Visual + Cross-UI **PROVEN** (`bf-e2e-visual-service-appliance-20260912-061103`) Â· Certificate Ready **YES** Â· issued **NO** Â· wait for `SERVICE_APPLIANCE_SERVICE_VERSIONED_VERTICAL_CERTIFICATION_V1`; no App Factory packaging yet; not GPS; 11/11 sales batch unchanged. (historical wait; certificate now CURRENT)
- Docs: Appliance Service reference vertical **PROVEN** (A01â€“A24) Â· package `field_service_appliance@v1` / `APPLIANCE_SERVICE` / `test-service-appliance` Â· Certificate Ready **NO** Â· Visual **NOT_PROVEN** Â· wait for `SERVICE_APPLIANCE_SERVICE_FULL_VISUAL_CROSSUI_V1` (`WAIT_FOR_SERVICE_APPLIANCE_SERVICE_FULL_VISUAL_CROSSUI_V1`); no App Factory packaging yet; not GPS; 11/11 sales batch unchanged. (historical wait; Visual now PROVEN)
- Docs: Next FIELD Vertical Reuse + Gap Audit V1 â€” candidate on-site appliance/machine service = **CONFIG_ONLY** FIELD peer (proposed `appliance_service` / `field_service_appliance@v1` / `APPLIANCE_SERVICE` â€” **not registered**); FIELD bundle REUSABLE_WITH_CONDITIONS; Load/Soak/Chaos repeat **NO**; next wait `SERVICE_APPLIANCE_SERVICE_REFERENCE_VERTICAL_PROOF_V1`; no App Factory packaging yet; not GPS; 11/11 sales batch unchanged. (historical wait; reference proof now PROVEN)
- Docs: Electrician Certificate **CURRENT** (`cert-service-electrician-v1`, production_active **NO**, PRODUCTION_APPROVED_WITH_FINDINGS) Â· **STOP** Electrician certification wait Â· packaging may proceed under existing App Factory rules without inventing electrician forks Â· next architectural decision A/B (another FIELD vertical reuse **or** next Service class gap); not GPS; 11/11 sales batch unchanged.
- Docs: Electrician Full Visual + Cross-UI **PROVEN** (`bf-e2e-visual-service-electrician-20260912-042927`) Â· Certificate Ready **YES** Â· issued **NO** Â· wait for `SERVICE_ELECTRICIAN_VERSIONED_VERTICAL_CERTIFICATION_V1` (`WAIT_FOR_SERVICE_ELECTRICIAN_VERSIONED_VERTICAL_CERTIFICATION_V1`); no electrician packaging fork yet; not GPS; 11/11 sales batch unchanged. (historical wait; certificate now CURRENT)
- Docs: FIELD Evidence Bundle **CURRENT / READY** (`service-field-evidence-v1`) Â· Certificate Ready **NO** Â· wait for `SERVICE_ELECTRICIAN_FULL_VISUAL_CROSSUI_V1`; electrician remains reference config only; no electrician packaging fork; not certificate; not GPS; 11/11 sales batch unchanged. (historical wait; Visual now PROVEN)

- Docs: FIELD Chaos **PROVEN** (`bf-e2e-chaos-service-field-20260912-033705`) Â· FIELD Class Evidence Complete **YES** Â· Certificate Ready **NO** Â· wait for `SERVICE_FIELD_EVIDENCE_BUNDLE_V1`; electrician remains reference config only; not certificate; not GPS; 11/11 sales batch unchanged.
- Docs: FIELD Soak60 **PROVEN** (`bf-e2e-soak60-service-field-20260911-191701`) Â· wait for `SERVICE_FIELD_CHAOS_PROOF_V1` (`WAIT_FOR_SERVICE_FIELD_CHAOS_PROOF_V1`); electrician remains reference config only; not certificate; not GPS; 11/11 sales batch unchanged.
- Docs: FIELD Load50 **PROVEN** (`bf-e2e-load50-service-field-20260911-185443`) Â· wait for `SERVICE_FIELD_SOAK60_PROOF_V1` (DONE â€” now wait Chaos); electrician remains reference config only; not certificate; not GPS; 11/11 sales batch unchanged.
- Docs: FIELD Load25 **PROVEN** (`bf-e2e-load25-service-field-20260911-183324`) Â· wait for `SERVICE_FIELD_LOAD50_PROOF_V1` (DONE â€” now wait Chaos via Soak60); electrician remains reference config only; not certificate; not GPS; 11/11 sales batch unchanged.
- Docs: Electrician reference FIELD proof **PROVEN** (E01â€“E24 Â· 23 PROVEN + E20 N/A) Â· Certificate Ready **NO** Â· wait for `SERVICE_FIELD_LOAD25_PROOF_V1` (DONE â€” now wait Load50); not GPS; not certificate; 11/11 sales batch unchanged.
- Docs: FIELD Core Domain **SEALED** â€” Engine/ServiceJob REUSED Â· Appointmentâ†’site PROVEN Â· Electrician domain fork NO Â· wait for `SERVICE_ELECTRICIAN_REFERENCE_FIELD_PROOF_V1` (`WAIT_FOR_SERVICE_ELECTRICIAN_REFERENCE_FIELD_PROOF_V1`); not GPS; not certificate; 11/11 sales batch unchanged. (historical wait; reference proof now PROVEN)
- Docs: Electrician FIELD Service Class gap audit **DONE** â€” **NEW_SERVICE_CLASS** Â· Engine REUSED Â· FIELD class REQUIRED Â· Separate engine NO Â· package/profile already exist Â· certificate NO Â· wait for `SERVICE_FIELD_CORE_DOMAIN_V1` (DONE â€” FIELD Load25 PROVEN); 11/11 sales batch unchanged.
- Docs: AUTO tire catalog specialization **DONE** (`auto_tire` READY) â€” customer identity may be Reifenservice; certification identity remains AUTO_WORKSHOP; commercial via `catalog_specialization_options()` (not COMMERCIAL_VERTICAL/package); wait for `SERVICE_ELECTRICIAN_FIELD_SERVICE_CLASS_GAP_AUDIT_V1` (DONE â€” now wait FIELD core); do not implement tire storage; 11/11 sales batch unchanged.
- Docs: Tire vs AUTO capability audit **DONE** â€” core Reifenservice = **CATALOG_ONLY_SPECIALIZATION** of AUTO Â· non-certification boundary Â· no tire package/profile/certificate Â· Einlagerung MATERIAL_DOMAIN out of core Â· wait for `SERVICE_AUTO_TIRE_CATALOG_SPECIALIZATION_V1`; independent tenant/app/branding allowed without cert boundary; 11/11 sales batch unchanged. (historical wait; specialization now DONE)
- Docs: MOTORCYCLE Certificate CURRENT (`cert-service-motorcycle-workshop-v1`, production_active NO, PRODUCTION_APPROVED_WITH_FINDINGS) â€” wait for Tire Service vs AUTO capability audit; runtime file-bound overlay ACCEPTED; 11/11 sales batch unchanged. (historical wait; tire audit now DONE)
- Docs: MOTORCYCLE Full Visual + Cross-UI **PROVEN** (`bf-e2e-visual-service-motorcycle-20260911-153956`) â€” wait for `SERVICE_MOTORCYCLE_VERSIONED_VERTICAL_CERTIFICATION_V1`; Certificate Ready YES Â· issued NO; 11/11 sales batch unchanged. (historical wait; certificate now CURRENT)
- Docs: MOTORCYCLE reference vertical **PROVEN** â€” wait for `SERVICE_MOTORCYCLE_FULL_VISUAL_CROSS_UI_PROOF_V1`; Certificate Ready NO; 11/11 sales batch unchanged. (historical wait; visual now proven)
- Docs: MOTORCYCLE CONFIG_ONLY reuse/gap **PROVEN** â€” wait for `SERVICE_MOTORCYCLE_REFERENCE_VERTICAL_PROOF_V1`; Certificate Ready NO; 11/11 sales batch unchanged. (historical wait; reference vertical now proven)
- Docs: BICYCLE Certificate CURRENT (`cert-service-bicycle-workshop-v1`, production_active NO) â€” wait for Motorcycle reuse/gap; 11/11 sales batch unchanged. (historical wait; motorcycle reuse/gap now proven)
- Docs: BICYCLE Full Visual + Cross-UI **PROVEN** (`bf-e2e-visual-service-bicycle-20260911-132941`) â€” wait for versioned vertical certification; 11/11 sales batch unchanged. (historical wait; certificate now CURRENT)
- Docs: BICYCLE Functional/Asset/Resource **PROVEN** â€” wait for Full Visual + Cross-UI; 11/11 sales batch unchanged. (historical wait; visual now proven)
- Docs: BICYCLE CONFIG_ONLY reuse/gap proven â€” wait for Bicycle reference vertical proof; 11/11 sales batch unchanged. (historical wait; reference vertical now proven)
- Docs: AUTO_WORKSHOP Certificate CURRENT (`cert-service-auto-workshop-v1`, production_active NO) â€” wait for Bicycle reuse/gap; 11/11 sales batch unchanged. (historical wait; reuse now proven)
- Docs: Service Engine Evidence Bundle **CURRENT** â€” wait for AUTO_WORKSHOP versioned vertical certification; 11/11 sales batch unchanged. (historical wait; certificate now CURRENT)
- Docs: Service Chaos **PROVEN** (`bf-e2e-chaos-service-auto-20260910-053422`) â€” wait for Evidence Bundle; 11/11 sales batch unchanged. (historical wait; bundle now CURRENT)
- Docs: Service Chaos NOT_PROVEN (C05) â€” wait for Chaos re-proof after demo inventory fix; 11/11 sales batch unchanged. (historical; superseded)
- Docs: Service Soak60 PROVEN â€” wait for Chaos or demo authorization; 11/11 sales batch unchanged.
- Docs: Service Load50 PROVEN â€” wait for Soak60/Chaos or demo authorization; 11/11 sales batch unchanged.
- Docs: Service Load25 PROVEN â€” wait for Load50/Soak/Chaos or demo authorization; 11/11 sales batch unchanged.
- Docs: Full Visual UI reproof PASS â€” wait for Load/Soak/Chaos or demo authorization; 11/11 sales batch unchanged.
- Docs: Flutter public visual actor gap CLOSED â€” wait for Full Visual UI reproof (`WAIT_FOR_SERVICE_FULL_VISUAL_UI_REPROOF`); 11/11 sales batch unchanged.
- Docs: Service Full Visual V1 attempted â€” Dashboard visual proven after demo static sync; App Factory now waits for Flutter visual actor gap closure.
- Docs: Cross-Layer PROVEN â€” App Factory waits for Full Visual (`WAIT_FOR_SERVICE_FULL_VISUAL_UI_PROOF`); 11/11 sales batch unchanged.
- Docs: Service Reference Test Tenant READY â€” App Factory waits for Cross-Layer (`WAIT_FOR_SERVICE_CROSS_LAYER_PROOF`); 11/11 sales batch unchanged.
- Docs: [SERVICE_APP_FACTORY_ROADMAP_V1.md](docs/SERVICE_APP_FACTORY_ROADMAP_V1.md) â€” Service demos wait for reference tenant; 11/11 batch unchanged.
- Docs: Service Engine certification baseline â€” official 11/11 sales batch still excludes Service (`demo-workshop` not provisioned). `service_first` template is not a Service certificate. Authority: BusinessForge `SERVICE_ENGINE_CERTIFICATION_BASELINE_V1.md`.

### Fixed

- `--debug` now runs `flutter build apk --debug`. Omitting `--release` alone still produced a release APK.

### Added

- E2E test-build profile: `--e2e-test --e2e-environment demo --e2e-run-id â€¦ --debug`. Fail-closed against production `api.bforge.de`. No manifest schema change. Docs: [E2E_TEST_BUILD_V1.md](docs/E2E_TEST_BUILD_V1.md).

### Changed

- Official public Sales Demo Apps **11/11** APK+AAB rebuild for Push Device Registration (V3-02 / Flutter). API origin `https://demo-api.bforge.de/api/v1`. API version remains `0.8.79`. FCM/`google-services.json` remains Slice 3 (`PROVIDER_CONFIGURATION_REQUIRED` for delivery). LAN artefacts preserved. Production origin absent.
- Official public Sales Demo Apps **11/11** APK+AAB rebuild for Marketing Consent Customer Surface (V3-01 / Flutter). API origin `https://demo-api.bforge.de/api/v1`. API version remains `0.8.79`. LAN artefacts preserved. Production origin absent.
- Restaurant Inventory V1 Reachability (`0.8.77`) â€” Factory-Runtime unverÃ¤ndert. Kein Demo-App-Rebuild (Flutter unverÃ¤ndert). Demo-API-Deploy + `--bootstrap-only` Bridge erwartet.
- Docs: Reachability V2 â€” R07 READY; nÃ¤chster Gap R05 Availability.
- Docs: Real Friseur Pilot wartet auf Owner-Input; Production-App nur `https://api.bforge.de/api/v1`; Signing weiterhin `SIGNING_CONFIGURATION_REQUIRED`. Public Demo-Apps vom 2026-08-28 decken Loyalty/Delivery aus aktuellem Flutter `main` noch nicht ab.

### Added

- Official Sales Demo public API origin: `https://demo-api.bforge.de/api/v1`
- CLI flag `--public-api` sets `API_BASE_URL=https://demo-api.bforge.de/api/v1` (fail-closed HTTPS)
- Output channels: `BusinessForge-Demo-Apps/lan/` vs `.../public/`; legacy top-level `demo-*` trees are moved into `lan/` without overwrite
- Public artefact origin scan (Dart snapshot / Flutter assets + `app_factory_config.json`): require `demo-api.bforge.de`, block LAN `192.168.*` / `:8090` and Production `api.bforge.de` (token-aware). Flutter snapshot loopback defaults are not treated as LAN API origins.
- Guard: official sales demo builds refuse Production `api.bforge.de`
- Docs: public demo hosts and lan/public layout in [OFFICIAL_SALES_DEMO_APP_FACTORY.md](docs/OFFICIAL_SALES_DEMO_APP_FACTORY.md)

### Changed

- No APK/AAB rebuild for Appointment Intake V1: Flutter `main` already contained the intake step; public artefacts remain on `https://demo-api.bforge.de/api/v1` against demo plane `0.8.68`
- `--public-api` default output is `BusinessForge-Demo-Apps/public/`; LAN default remains `.../lan/`
- Existing LAN APKs are preserved under `lan/` and are not overwritten by public rebuilds
- Public store metadata `api_release_gap` is cleared when the API origin is `https://demo-api.bforge.de`

## [0.1.2] â€” 2026-08-28

### Added

- Official Sales Demo batch builds: `app-factory build-official-sales-demos`
- Demo plane discovery + manifest materialization from live bootstrap/hero media
- Output root: `BusinessForge-Demo-Apps/` (outside repo)
- Docs: [OFFICIAL_SALES_DEMO_APP_FACTORY.md](docs/OFFICIAL_SALES_DEMO_APP_FACTORY.md)
- Wave 1 store-ready pipeline: native Android icons/splash, package identity `de.bforge.app.u{ulid}`, signing foundation (env only), build result JSON
- CLI: `signing-status`, `materialize-export`
- Docs: [ANDROID_RELEASE_PIPELINE.md](docs/ANDROID_RELEASE_PIPELINE.md)
- Tests: `tests/test_wave1_store_ready.py`
- Dorfladen #1 pilot manifest: `manifests/dorfladen-1-pilot.yaml` + production export JSON
- Qualified APK build against `api.bforge.de` (`output/dorfladen-hutthurm-app-release.apk`)

### Changed

- Play Store 512px icon written to `assets/branding/` (not `res/play/` â€” fixes aapt merge)
- Flutter `--dart-define` uses `key=value` form (spaces in app names)
- Windows: tolerate Flutter pub-get symlink warning when deps resolve
- Appointment packages added to `customer-app-compat-v1.json`
- Demo HTTP builds: `usesCleartextTraffic` patched when `api_base_url` is `http://`
- Windows: tolerate Flutter appbundle exit 1 when AAB exists but native symbol stripping fails (missing NDK/cmdline-tools)
- Android manifest `android:label` XML-escapes display names containing `&`
- Privacy inventory (Backend): IONOS Domain/DNS/Mail + first-party Demo-Leads; Formspree removed; Plausible remains PLANNED. See [PRIVACY_INVENTORY_REPORT.md](../BusinessForge/docs/privacy/PRIVACY_INVENTORY_REPORT.md).
- DSAR/Privacy Foundation (Backend 2026-08-14): Customer self-service export, tenant/platform DSAR tools, controlled erasure. See [DATA_SUBJECT_RIGHTS.md](../BusinessForge/docs/privacy/DATA_SUBJECT_RIGHTS.md). Customer App needs rebuild for `/account/privacy`.
- Commercial Self-Service Foundation (Backend 2026-08-14): App Delivery Jobs are Backend/Super-Admin queues. Factory remains manual CLI â€” payment does not publish to stores. See [APP_DELIVERY_LIFECYCLE.md](../BusinessForge/docs/commercial/APP_DELIVERY_LIFECYCLE.md).
- Commercial Feature Audit (2026-08-14): White-label classified FUNCTIONAL â€” native icon/splash + signing gaps (GAP-001/002). See [FEATURE_READINESS_MATRIX.md](../BusinessForge/docs/commercial/FEATURE_READINESS_MATRIX.md).
- Standard requalification (2026-08-14): White-Label **SOFTWARE_READY**; missing Owner-Keystore is `OPERATIONAL_BLOCKER: ANDROID_SIGNING_MATERIAL`; missing customer icon is `TENANT_INPUT_REQUIRED`. See [STANDARD_EDITION_READINESS.md](../BusinessForge/docs/commercial/STANDARD_EDITION_READINESS.md), [ANDROID_RELEASE_PIPELINE.md](docs/ANDROID_RELEASE_PIPELINE.md).
- Transactional Mail (Backend 2026-08-14): generic SMTP adapter, fail-closed production. IONOS Mail Basic is not an approved transactional provider. See [TRANSACTIONAL_MAIL.md](../BusinessForge/docs/operations/TRANSACTIONAL_MAIL.md).

### Notes

- Rechtstexte sind Runtime-Daten der Customer App (Bootstrap / Public Legal API). Die Factory backt keine Tenant- oder Platform-Rechtstexte in die APK.
- Legal Activation: [LEGAL_COMPLIANCE_V1.md](../BusinessForge/docs/architecture/LEGAL_COMPLIANCE_V1.md), [LEGAL_READINESS_REPORT.md](../BusinessForge/docs/pilot/LEGAL_READINESS_REPORT.md).
- Datenschutz-Inventur (IST, Backend): [PRIVACY_INVENTORY_REPORT.md](../BusinessForge/docs/privacy/PRIVACY_INVENTORY_REPORT.md) â€” keine Policy/AVV-Texte.
- Production security hardening (2026-08-14): Flutter JWT in secure storage; Factory APK must be rebuilt after Customer App pull.

## [0.1.1] - 2026-08-05

### Added

- **Contract qualification** â€” full Android pipeline against Customer App `v0.5.10` ([FACTORY_RUNTIME_V1.md](docs/FACTORY_RUNTIME_V1.md))
- [COMPATIBILITY_MATRIX.md](docs/COMPATIBILITY_MATRIX.md) â€” qualified toolchain and define matrix
- Kotlin incremental disabled in workspace only (`kotlin.incremental=false`) for cross-drive Windows builds
- Flutter/Dart version capture in build reports via `dart.exe` adjacent to Flutter SDK

### Changed

- [CUSTOMER_APP_BUILD_CONTRACT_V1.md](docs/CUSTOMER_APP_BUILD_CONTRACT_V1.md) â€” **Approved** (qualified 2026-08-05)
- `flutter analyze` uses `--no-fatal-infos --no-fatal-warnings` in pipeline
- Removed `flutter clean` from pipeline (Windows symlink/Developer Mode issue)

### Fixed

- `BuildOrchestrator` â€” restore `mark_finished(SUCCEEDED)` on successful builds

## [0.1.0] - 2026-08-05

### Added

- GitHub repository [BusinessForge-App-Factory](https://github.com/mmshop94/BusinessForge-App-Factory) on branch `main`
- Initial repository structure (`app_factory/`, `schemas/`, `manifests/`, `templates/`, `tests/`, `docs/`)
- Domain model: `AppBuildManifest`, `BuildRequest`, `BuildResult`, and related types
- JSON Schema `app-build-manifest-v1.json` with strict validation
- Customer app compatibility matrix `customer-app-compat-v1.json`
- Manifest validator with secret detection and asset checks
- Deterministic build planner with `--dart-define` mapping
- Slice 1 Android build orchestrator with isolated workspace
- Flutter config applier (pubspec version, Android applicationId, label, build_config)
- CLI: `validate`, `plan`, `build-android`, `inspect-build`
- Example manifest: `manifests/examples/dorfladen-hutthurm.yaml`
- Documentation: ARCHITECTURE, APP_MANIFEST_V1, CUSTOMER_APP_INTEGRATION, SECURITY, ROADMAP
- 14 unit tests covering validation, planning, workspace isolation, and mocked builds

### Open decisions

- Customer App must adopt documented `--dart-define` keys (`PUBLIC_APP_ID`, feature flags) â€” see CUSTOMER_APP_INTEGRATION.md
- Icon/splash generation from SVG is deferred; assets are copied, not rasterized in Slice 1
- iOS Bundle ID is stored in manifest but not applied until Slice 2
- Manifest sourcing from BusinessForge Backend API is planned for Slice 2

### Security

- Signing keys and store credentials are explicitly out of scope for this repository
