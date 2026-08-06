## 4. UK Readiness Assessment

The UK is the schema's home market: Companies House, VAT, SIC and DEFRA concepts all exist as columns. Readiness therefore fails not on missing fields but on **unvalidated fields**: every downstream rule — VAT format, postcode versus Eircode, currency, timezone, factor selection — keys off `country` and `currency`, both free text (findings A5, A6, both 🔴 Critical / Small / Low risk / v1.0). Until those two are constrained, all other UK validation is built on sand. Every fix below is additive and ADR-safe.

### 4.1 Company & Tax Identity

| ID | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A1 | `organizations.company_number` UNIQUE but no format CHECK for 8-character CH numbers; garbage in a unique column poisons duplicate detection and future CH API lookups. | 🟠 High | Small | Low | v1.0 |
| A2 | `*.vat_number` (3 tables) unconstrained; UK formats `GB` + 9/12 digits, `GBGD`/`GBHA` + 3. MOD97 checksum at app layer; regex CHECK in DB. | 🟠 High | Small | Low | v1.0 |
| A4 | `organizations.sic_code` / `organization_metadata.sic_code` present but unconstrained; SECR and Companies House use **SIC 2007** (five digits). | 🟡 Medium | Small | Low | v1.0 |
| C | `organizations` lacks `legal_entity_type` (Ltd, PLC, LLP, CIC); `business_structure` is free text. Entity type drives CH prefix and legal identity on reports. | 🟠 High | Small | Low | v1.0 |

The pattern is consistent and cheap to fix: the schema *knows about* UK identity fields but treats them as opaque strings — a validation layer never written, not a modelling error. Left unfixed, duplicate detection cannot work when `vat_number` and `company_number` accept arbitrary formats, and the AI pipeline writes unvalidated invoice extractions into `suppliers.company_number`/`suppliers.vat_number`, turning extraction errors into permanent master-data errors. Note (dim03 finding C9, 🟡 / v1.1): `organizations.company_number` is UNIQUE across both jurisdictions — workable only if validation is conditional on `country` (§5.2).

### 4.2 Address, Postcode & Geodata

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A3 | `*.postcode` (3 tables): no UK regex, no normalisation (uppercase, spaced incode); blocks Royal Mail PAF / Loqate matching and trigram search. | 🟠 High | Small | Low | v1.0 |
| D2 | Dual storage: structured columns coexist with text `registered_address`/`billing_address`/`suppliers.address` — two writers, no sync rule. Structured canonical; blobs as display cache. | 🟠 High | Small | Low | v1.0 |
| D3 | No ISO 3166-1 `country_code` anywhere; free-text `country` collects "UK", "United Kingdom", "GB", "England" — yet every jurisdiction rule keys off it. | 🟠 High | Small | Low | v1.0 |
| A10 | No UK **nation** field (England/Scotland/Wales/NI); `facilities.region` is free text overlapping `county`. Nation drives CH prefixes and bank holidays. | 🟡 Medium | Small | Low | v1.1 |
| D4 | `facilities` has `latitude`/`longitude` (good) but no `address_validation_status`/`formatted_address` — the verify-then-cache PAF/Loqate loop cannot be built. | 🟡 Medium | Small | Low | v1.1 |

The structured model maps cleanly onto PAF and Eircode lookups (finding D5 rates provider compatibility acceptable for v1.0), so the foundation is sound. What breaks is consistency: storing the same address twice means any invoice or SECR submission reading the blob can disagree with any lookup reading the columns. The fix — structured canonical, blob as display cache — is a data-entry convention, not a redesign. The normalisation gap (A3) compounds: unnormalised postcodes defeat provider matching and future `pg_trgm` similarity search alike — one missing convention, three casualties.

### 4.3 Currency, Timezone & Business Calendar

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A6 | Six currency columns (e.g. `organizations.currency`, `customer_subscriptions.currency`) plus `system_settings.default_currency`: free text, none ISO 4217; v1.0 set {GBP, EUR}. | 🔴 Critical | Small | Low | v1.0 |
| A7 | `organizations.timezone`, `business_hours.timezone`, `system_settings.default_timezone` unconstrained; must be IANA names in {`Europe/London`, `Europe/Dublin`}. | 🟠 High | Small | Low | v1.0 |
| A14 | `business_hours` has no bank-holiday jurisdiction column; England & Wales, Scotland, NI and ROI differ — per-day `is_holiday`/`holiday_name` cannot model this. | 🟡 Medium | Medium | Low | v1.1 |
| C | `system_settings.default_vat_rate` vs `default_tax_rate`: redundant duplicates (UK VAT 20% vs IE 23% — which wins?). | 🟡 Medium | Small | Low | v1.0 |

A6 is Critical not for difficulty — a one-line CHECK — but for blast radius: one "£" or "gbp" row in any of six currency columns breaks aggregation, Stripe reconciliation and spend-based emissions maths. A7 fails more quietly: SLA deadlines in `sla_definitions` and `sla_compliance` depend on `business_hours.timezone`, and a user-entered "GMT" silently drops British Summer Time, shifting every SLA boundary by an hour for half the year. The bank-holiday gap (A14) guarantees wrong SLA breach maths for one UK nation several days a year; ship it with the nation field (A10).

### 4.4 UK Payments & Banking

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A9 | `suppliers.bank_account`, `iban`, `swift_code` exist but there is **no `sort_code`**. UK payments use 6-digit sort code + 8-digit account number; a UK supplier cannot be paid correctly. | 🟠 High | Small | Low | v1.0 |
| B9 (dim03) | Supplier bank details (`bank_account`, `iban`, `swift_code`, `bank_name`) plaintext, unmasked, unaudited — the classic UK/IE payment-diversion fraud target. Add `sort_code` + last-4 masking now; encrypt at rest in v1.1. | 🔴 Critical | Medium | Medium | v1.0 (sort code + masking) / v1.1 (encryption) |
| C | `consultant_billing` prices (`auto_extraction_price`, `manual_extraction_price`) have **no currency column at all** — the only billing table missing one. | 🟠 High | Small | Low | v1.0 |

Payments is where the UK blind spot is most concrete: the model describes an Irish or international account completely yet cannot represent the two fields every UK B2B payment run uses — an IBAN-centric assumption that holds for Ireland but not UK domestic practice. The security dimension (dim03 finding B9) raises the stakes: plaintext storage means the system can neither pay UK suppliers correctly nor protect their payment details. Both fixes are additive and low-risk pre-launch; retrofitting onto live data is the expensive version.

### 4.5 UK Carbon Reporting Readiness (SECR)

SECR requires, for in-scope UK companies and LLPs: total UK energy in kWh, associated tCO2e, at least one intensity ratio, prior-year comparatives, an energy-efficiency narrative, and alignment to the **financial year** of the Directors' Report. The reporting spine is strong — `report_templates`, `report_generation_queue`, `report_versions`, and `organization_metadata` denominators (revenue, employees, floor area) are present (findings D2, D6, D7, D8: adequate, 🟢) — but three defects undermine the numbers it would report.

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A12 | `defra_conversion_factors`: no `unit`, `scope` or `source` — `co2e_multiplier numeric` states kg CO2e per *what*? No factor-year edition; UK-only table name, nothing enforced. | 🔴 Critical | Medium | Medium (unit backfill) | v1.0 |
| A13 | `emissions_logs.raw_quantity` has **no unit column**, no `facility_id`, no `scope`; emissions attach only to a nullable `asset_id` — site-level SECR totals cannot be computed reliably. | 🔴 Critical | Medium | Medium | v1.0–v1.1 |
| A11 | `report_generation_queue.reporting_year` int4 cannot express a UK FY (Apr 2025–Mar 2026); `organizations.financial_year_end` is duplicated by `organization_metadata.fiscal_year_start/end` (D4). No `regulatory_framework` column. | 🟠 High | Medium | Low | v1.1 (v1.0 if SECR in launch scope) |
| D3 | Floor area sqft-only (`organization_metadata.total_floor_area_sqft`); UK official practice is m² and intensity ratios need consistent units. Add sqm columns or `floor_area_unit`. | 🟡 Medium | Small | Low | v1.1 |

The so-what: CarbonTally can produce a beautifully versioned SECR-shaped report containing indefensible numbers. Unit-less factors (A12) and unit-less quantities (A13) mean the kWh total SECR demands is assembled by inference through the factor join — one ambiguous row from silently wrong — and a nullable-`asset_id`-only facility link cannot guarantee site coverage. The FY defect (A11/D4) surfaces first in an accountant's hands: an integer `reporting_year` cannot name the period a Directors' Report covers. Caveat from dim02: the dump shows no indexes or CHECK constraints; if migrations add them, some ratings drop — but missing columns (A12, A13) and the int4 year stand regardless.

## 5. Ireland Readiness Assessment

Ireland is a declared launch market — Irish seed users (`emma.walsh@greenenergy.ie`, `john.obrien@ecobuild.ie`) are in the fixtures — yet readiness is materially worse, and worse in kind. Section 4 described unvalidated columns; this section describes **missing and impossible states**: a facility that cannot be inserted, a factor set that does not exist, formats no column validates. The recommendation throughout: generalise rather than fork — additive columns and conditional CHECKs keyed off `country = 'IE'`.

### 5.1 The Facilities Eircode Blocker

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B1 | `facilities`: **no `eircode` column AND `postcode` NOT NULL**. Ireland has no postcode system; the other address tables have `eircode`, `facilities` was missed. Irish sites cannot be inserted without a fake "postcode". | 🔴 Critical | Small | Medium (relax NOT NULL + add column) | **v1.0 blocker** |
| D5 (dim03) | Same defect confirmed in the governance dimension: make `postcode` conditionally required (postcode XOR eircode) and add `eircode`. | 🔴 Critical | Small | Low | v1.0 |

This is the single worst UK/IE defect in the schema: a mandatory `postcode` on `facilities` demands a value that does not exist in Ireland, which has never had a postcode system. The AI pipeline maps bills to facilities and emissions attach at facility level — the blocker sits on the data path that matters most: an Irish customer can create an organisation but cannot register the site whose energy the product measures. The fix is small and safe, but needs finding G5's regression guard: seed data has Irish *users* yet no Irish *org or facility* fixture — how B1 survived to audit.

### 5.2 Irish Identity & Tax

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B4 | No `cro_number` anywhere; `organizations.company_number` serves both jurisdictions, but CRO numbers are 6 digits vs 8-character CH. Validate conditionally on `country`. | 🟠 High | Small | Low | v1.0 |
| B5 | Irish VAT unconstrained on all three `vat_number` columns (`IE` + 7 digits + 1–2 letters, e.g. `IE6388047V`, plus a legacy format). Pairs with A2 as one rule. | 🟠 High | Small | Low | v1.0 |
| B2 | No "postcode OR eircode" CHECK even where both columns exist: `country = 'IE'` ⇒ `eircode`; `country = 'GB'` ⇒ `postcode`. | 🟠 High | Small | Low | v1.0 |
| B3 | Eircode format unconstrained: 3-char routing key + 4-char identifier, charset excluding I/O (`^[AC-FHKNPRTV-Y\d]{3}\s?[AC-FHKNPRTV-Y\d]{4}$`). | 🟠 High | Small | Low | v1.0 |
| B7 | `county` free text — no 26-county constraint; collects "Co. Dublin", "Dublin", "co dublin". Needs 26 ROI + 6 NI + UK ceremonial counties, disambiguated by `country`. | 🟡 Medium | Small | Low | v1.1 |

The root cause across B2–B5 is §4's single point of failure: the unconstrained `country` column (A5). Every Irish rule is conditional on country, so "Ireland"/"IE"/"Éire" free text makes all four checks unreliable at a stroke. Implementation should be unified: one VAT CHECK branched on `country` (A2 + B5); one company-number CHECK covering CH and CRO (A1 + B4); one postcode/eircode XOR rule across the four address-bearing tables (B2). The county lookup (B7, v1.1) should anticipate the known edge cases — Dublin city versus county, the three administrative counties.

### 5.3 Currency, Timezone & Locale

Ireland inherits the Critical currency finding (A6) and adds a coupling defect (finding B9, 🟠 High / Small / Low / v1.0): nothing ties `country` to `currency`, so an Irish org can be set to "GBP" or "euro". Fix via the shared CHECK ({GBP, EUR}) plus an app-level EUR default for `country = 'IE'`. Timezone (A7): `Europe/Dublin` must sit alongside `Europe/London`, and SLA maths (§4.3) must use Irish civil time for Irish orgs. Locale (A15, 🟢 Low / v1.1) should constrain `organizations.language`/`locale` to `en-GB`/`en-IE`. Phone (B6, 🟡 / v1.0): one E.164 CHECK (`^\+[1-9]\d{6,14}$`) covers +44 and +353 — one constraint serving both markets.

### 5.4 Irish Emission Factors Gap

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| E1 | Only factor table is `defra_conversion_factors` (UK DESNZ); only factor FK is `emissions_logs.defra_factor_id`. Irish practice uses **SEAI/EPA**; the Irish grid factor differs materially — DEFRA on a Dublin site misstates Scope 2. Add `factor_set`/`source_authority` + `country`. | 🔴 Critical | Medium | Medium (column add + backfill) | v1.0 (columns) / v1.1 (SEAI load) |
| E2 | `system_settings.default_emission_factor_set` already anticipates multiple factor sets — settings layer ready, data layer not. E1 is a gap, not a design choice. | 🟡 Medium | — | — | — |
| C10 (dim03) | No provenance column and no unique `(reporting_year, activity_type)` on `defra_conversion_factors` — duplicate rows would silently double-count emissions. | 🟠 High | Small | Low | v1.1 (v1.0 given the IE launch cohort) |

This is the highest-stakes Irish finding because the error is invisible and quantitatively material. Scope 2 is kWh multiplied by a grid factor; Irish grid carbon intensity differs from the UK's enough that a DEFRA-factored Dublin office yields a wrong number with no warning — the join succeeds, the arithmetic succeeds, the report is wrong. That `default_emission_factor_set` exists in settings (E2) proves multi-jurisdiction factors were *intended*; the table never grew the provenance columns to match. The unique `(reporting_year, activity_type)` composite (C10) stops data-load errors becoming systematic over-statement.

### 5.5 Ireland-Specific Nuances

| ID | Finding | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B10 | `organizations.nace_code` and `esrs_enabled` are **not** purely EU-expansion fields: Irish CRO codes are NACE Rev.2 and Ireland has transposed CSRD — large IE companies are in ESRS scope now. Keep dormant; v1.1 review for large IE customers (unlike US-only `organizations.cik`). | 🟡 Medium | — | — | Keep dormant; v1.1 review |
| B11 | `organizations.carbon_tax_region` / `system_settings.carbon_tax_rate` free text. Ireland levies carbon tax (€/tCO2); the UK uses UK ETS. Keep dormant; GB/IE enum when enabled. | 🟢 Low | Small | Low | v1.1 |
| G5 / G1 | No Irish org or facility fixture in seed data (only IE users); out-of-market `.de`/`.fr`/`.fi`/`.ai` users seeded — the gap that let B1 through. Replace with UK/IE fixtures. | 🟠 High (G5) / 🟡 Medium (G1) | Small | Low | v1.0 |

Three nuances separate tolerating Ireland from being ready for it. First, dormant-field disambiguation (B10): scope hygiene would otherwise lump `nace_code` and `esrs_enabled` with `cik` and `naics_code` as clutter — but Ireland's NACE Rev.2 usage and CSRD transposition make these early-activation candidates, not v2.0 ballast. Second, carbon-tax columns (B11): correctly dormant but not deletable — a GB/IE enum on `carbon_tax_region` at activation prevents free-text drift. Third, the fixture gap (G5) is process, not data: every Irish defect — B1 above all — passed testing because no seed row exercised an Irish write path.
