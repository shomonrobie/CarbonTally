# DIM 01 — UK/IE Business-Fields & Validation Audit Brief

Scope applied: UK + Republic of Ireland v1.0 only. No schema redesign, no SQL, no ADR conflicts (UUID PKs, jsonb metadata, soft-delete, RLS approach, no-redesign all respected — everything below is *additive* column or CHECK/enum-constraint recommendations only).

---

## A) UK Readiness Findings

| # | Finding (table.column) | Detail & Why it matters | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| A1 | `organizations.company_number` (Unique, varchar) | No format constraint. UK Companies House numbers are 8 chars: `^\d{8}$` or 2-alpha prefix + 6 digits (SC, NI, OC, SO, LP, SL, FC, BR, GE, IP, SP, RS, CE, CS, AC, SA, SZ, R…). Without a CHECK, garbage CH numbers enter a *unique* column and poison duplicate-detection and future CH API lookups. | 🟠 High | Small | Low | v1.0 |
| A2 | `organizations.vat_number` / `suppliers.vat_number` / `consultant_profiles.vat_number` | Free `text/varchar`, no CHECK. UK VAT: `GB` + 9 digits, `GB` + 12 digits (branch traders), `GBGD`/`GBHA` + 3 digits (govt/health). HMRC MOD97/MOD9755 checksum belongs at app layer, but a regex CHECK must exist in DB. | 🟠 High | Small | Low | v1.0 |
| A3 | `organizations.postcode`, `suppliers.postcode`, `consultant_profiles.postcode` | No UK postcode regex (full GIR-valid pattern), no normalisation strategy (uppercase, single space before incode). Blocks Royal Mail PAF / Loqate lookup matching. | 🟠 High | Small | Low | v1.0 |
| A4 | `organizations.sic_code` / `organization_metadata.sic_code` | Present (good) but unconstrained. Must be UK **SIC 2007** (5-digit, e.g. `62012`). No CHECK, no lookup table. SECR submissions and Companies House filings use SIC 2007. | 🟡 Medium | Small | Low | v1.0 |
| A5 | `organizations.country` (text), `facilities.country`, `suppliers.country`, `consultant_profiles.country` | Free text, no ISO 3166-1 alpha-2 constraint, no GB/IE restriction for v1.0. Every downstream rule (VAT format, postcode vs Eircode, currency, timezone) keys off country — an unconstrained country field makes all jurisdiction logic unreliable. | 🔴 Critical | Small | Low | v1.0 |
| A6 | `organizations.currency` (text), `customer_subscriptions.currency`, `manual_extraction_batches.currency`, `suppliers.payment_currency`, `consultant_profiles.revenue_currency`, `document_processing_queue.billing_currency`, `system_settings.default_currency` | All free `text/varchar`, none constrained to ISO 4217. For v1.0 the valid set is exactly {GBP, EUR}. Six different currency columns across the schema with zero validation is an invoicing-bug factory. | 🔴 Critical | Small | Low | v1.0 |
| A7 | `organizations.timezone` (text), `business_hours.timezone`, `system_settings.default_timezone` | Unconstrained. Must be IANA names restricted to `Europe/London` / `Europe/Dublin` for v1.0. SLA deadline calculations (`sla_definitions`, `sla_compliance`, business_hours) silently break if a user enters "GMT" vs "Europe/London" (GMT has no DST). | 🟠 High | Small | Low | v1.0 |
| A8 | `organizations` — no `phone`/`mobile` columns at all | `primary_contact_email/name` and `billing_contact_email/name` exist, but no phone for the org. UK B2B onboarding/credit checks (and Stripe billing) routinely require a contact phone. Only `organization_metadata.primary_contact_phone` exists — buried in the 1:1 metadata table. | 🟡 Medium | Small | Low | v1.0 |
| A9 | `suppliers.bank_account` exists but **no `sort_code`** | UK domestic payments use sort code (6 digits, `^\d{6}$`) + 8-digit account number. `iban`/`swift_code` serve Ireland/international but a UK supplier cannot be paid correctly without sort code. | 🟠 High | Small | Low | v1.0 |
| A10 | `organizations.region`/`county` vs UK nations | `organizations.county` exists but there is no UK **nation** field (England/Scotland/Wales/Northern Ireland) — and nation is the reporting boundary that matters (Scotland/NI have different CH number prefixes (SC/NI) and different bank holidays for SLA). `facilities.region` exists but is free text and duplicated in meaning vs `county`. | 🟡 Medium | Small | Low | v1.1 |
| A11 | `report_generation_queue.reporting_year` (int4 only) | SECR reports on the **financial year** (arbitrary start/end), not calendar year. `organizations.financial_year_end` exists but reports have no `period_start`/`period_end` columns — an int4 year cannot express a UK FY like Apr 2025–Mar 2026. No `regulatory_framework` column either (SECR vs voluntary). | 🟠 High | Medium | Low | v1.1 (v1.0 if SECR is in launch scope) |
| A12 | `defra_conversion_factors` — no `unit`, no `scope`, no `source/jurisdiction` | `co2e_multiplier numeric` with no unit column (kg CO2e per *what*? kWh? litre? tonne-km?) and no source column. DEFRA is UK-only; the table name hard-codes UK but nothing enforces or labels the factor set, year edition, or unit. Ambiguous emission factors = wrong SECR numbers. | 🔴 Critical | Medium | Medium (existing rows need unit backfill) | v1.0 |
| A13 | `emissions_logs` — `raw_quantity` has **no unit column**, no `facility_id`, no `scope` | Unit-less quantities, and emissions can only attach to an `asset_id` (nullable), never directly to a facility — site-level SECR reporting can't be computed reliably. Scope is only inferable via the DEFRA factor join. | 🔴 Critical | Medium | Medium | v1.0–v1.1 |
| A14 | `business_hours` — no jurisdiction column for bank holidays | England & Wales, Scotland, NI, and ROI all have *different* bank holidays. `is_holiday`/`holiday_name` per day-of-week can't model this. SLA breach math will be wrong for one of the nations/ROI at least 4–5 days/year. | 🟡 Medium | Medium | Low | v1.1 |
| A15 | `organizations.language`/`locale` | Present but unconstrained; valid v1.0 set is `en-GB`, `en-IE` (+ optionally `ga-IE` later). | 🟢 Low | Small | Low | v1.1 |

---

## B) Ireland Readiness Findings

| # | Finding | Detail & Why | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| B1 | **`facilities` has no `eircode` column AND `postcode` is NOT NULL** | This is the single worst UK/IE defect in the schema. Ireland has **no postcode system** — Eircode is the only code. An Irish customer's site *cannot be inserted* without entering a fake "postcode". `organizations`, `suppliers`, `consultant_profiles` all have `eircode`; `facilities` was missed. | 🔴 **Critical** | Small | Medium (relaxing NOT NULL on `postcode` + adding column; existing rows unaffected) | **v1.0 blocker** |
| B2 | Cross-table "postcode **OR** eircode" rule absent everywhere | Even where both columns exist (`organizations`, `suppliers`, `consultant_profiles`), there is no CHECK enforcing: if `country = 'IE'` then `eircode` present; if `country = 'GB'` then `postcode` present. Data will be half-filled. | 🟠 High | Small | Low | v1.0 |
| B3 | Eircode format unconstrained | Eircode = 3-char routing key + 4-char unique identifier, charset excludes I/O (e.g. `A65 F4E2`, `D02 X285`, `V94…`). Regex `^[AC-FHKNPRTV-Y\d]{3}\s?[AC-FHKNPRTV-Y\d]{4}$` plus routing-key allowlist at app layer. | 🟠 High | Small | Low | v1.0 |
| B4 | No `cro_number` column anywhere | `organizations.company_number` is a single column for both jurisdictions, but Irish CRO numbers are 6 digits (`^\d{6}$`) — a different format from the 8-char CH number. The column must be validated *conditionally on country* (or split into `company_number` + `cro_number`). `suppliers.company_number` and `consultant_profiles.company_number` have the same problem. | 🟠 High | Small | Low | v1.0 |
| B5 | Irish VAT unconstrained | IE formats: `IE` + 7 digits + 1–2 letters (e.g. `IE6388047V`, `IE9999999XX`), old format `IE` + digit + 6 digits + 2 letters (e.g. `IE8S42396H`). Needs jurisdiction-aware validation paired with A2. | 🟠 High | Small | Low | v1.0 |
| B6 | Irish phone (+353) unsupported conceptually | Phone columns exist (`consultant_profiles.phone`, `suppliers.contact_phone`…) but no E.164 CHECK, and no +353 handling rule. E.164 CHECK `^\+[1-9]\d{6,14}$` covering both +44 and +353 solves both markets at once. | 🟡 Medium | Small | Low | v1.0 |
| B7 | `county` free text — no 26-county constraint | ROI has 26 counties (32-county island incl. the 6 NI counties: Antrim, Armagh, Down, Fermanagh, Derry/Londonderry, Tyrone). Free-text `county` will collect "Co. Dublin", "Dublin", "co dublin"… Needs a lookup/enum with the 26 ROI counties + 6 NI counties + UK ceremonial counties, disambiguated by `country`. Also note Dublin city/county and the three administrative counties (Dún Laoghaire–Rathdown, Fingal, South Dublin). | 🟡 Medium | Small | Low | v1.1 |
| B8 | Irish emission factors unsupported | `defra_conversion_factors` is UK-DEFRA-by-name. Irish customers should use SEAI/EPA factors. No `factor_source`/`jurisdiction` column (see A12). Without it, Irish orgs silently get UK grid factors — materially wrong Scope 2 for IE. | 🔴 Critical | Medium | Medium | v1.0–v1.1 |
| B9 | EUR supported in principle but nothing couples country→currency | `organizations.currency` free text means an IE org can be set to "GBP" or "euro". Needs CHECK (ISO 4217) + app-level default EUR when country=IE. | 🟠 High | Small | Low | v1.0 |
| B10 | Ireland nuance: `nace_code` and `esrs_enabled` are NOT purely "EU-expansion" fields | Irish CRO activity codes are **NACE Rev.2**, and Ireland has **transposed CSRD** — large Irish companies are in scope of ESRS reporting now. Recommend keeping both columns **dormant** for v1.0 SME launch but *not* deleting them and flagging ESRS as a **v1.1 candidate for large IE customers**, unlike (e.g.) `cik` which is genuinely US-only. | 🟡 Medium (disambiguation) | — | — | keep dormant; v1.1 review |
| B11 | Ireland carbon tax | `organizations.carbon_tax_region` / `system_settings.carbon_tax_rate` are free text. Ireland *does* levy carbon tax (€/tCO2); UK uses UK ETS instead. Keep columns dormant for v1.0 but constrain region to GB/IE enum when enabled. | 🟢 Low | Small | Low | v1.1 |

---

## C) Missing Fields — Table by Table

**(Only business-meaningful gaps; every item additive — no redesign.)**

| Table | Missing field(s) | Why (UK/IE) | Severity | Effort | Risk | Version |
|---|---|---|---|---|---|---|
| `users` | `phone`, `mobile` (E.164), `timezone`, `locale`, `country_code` | Notifications/2FA (system_settings has `two_factor_method` — SMS 2FA impossible without a phone), date/time display. | 🟡 Medium | Small | Low | v1.0–v1.1 |
| `organizations` | `phone`, `mobile`, `trading_name`, `legal_entity_type` (enum: Ltd, PLC, LLP, CIC, DAC, CLG, sole trader, partnership), `invoice_number_prefix`, `credit_limit` | UK Ltd vs LLP changes CH prefix and legal identity on reports; Irish DAC/CLG/LTD types differ. `business_structure` exists but is free text — either constrain it or add enum. Credit limit needed for B2B SaaS invoicing. | 🟠 High (legal_entity_type) / 🟡 Medium (rest) | Small | Low | v1.0 / v1.1 |
| `organization_metadata` | `total_floor_area_sqm` / `occupied_floor_area_sqm` (or a `floor_area_unit`) | sqft columns are imperial/US-flavoured; IE uses m² exclusively, UK officially m². SECR intensity ratios need consistent units. Keep sqft columns dormant; add sqm. | 🟡 Medium | Small | Low | v1.0 |
| `facilities` | `eircode` (B1), `site_reference`/`meter_mpan_mprn`, `site_manager_name/phone`, `floor_area_sqm`, `country_code` NOT NULL | UK electricity/gas meters (MPAN/MPRN) and Irish MPRN are the keys that tie utility bills to sites — the AI document pipeline maps bills→facilities today only via fuzzy AI matching (`ai_mapped_facility_id`). Meter numbers make it deterministic. | 🟠 High | Small–Medium | Low | v1.0–v1.1 |
| `suppliers` | `sort_code` (A9), `credit_limit`, `account_reference` (ledger code), `purchase_order_required` bool | UK payment + future Xero/QuickBooks mapping (ledger account codes). PO-required flag drives invoice validation. | 🟠 High / 🟡 Medium | Small | Low | v1.0–v1.1 |
| `customer_documents` | `document_number` (invoice number), `document_date`, `purchase_order`, `currency`, `net_amount`, `vat_amount`, `gross_amount` | Invoice/bill extraction results live only in `extracted_data jsonb`. Without typed columns: no duplicate-invoice detection (`org + supplier + invoice_number`), no currency-consistent totals, no spend-based emissions reconciliation. Duplicate detection is explicitly a brief requirement. | 🔴 Critical | Medium | Low (additive) | v1.0–v1.1 |
| `emissions_logs` | `unit` (FK to `units.code`), `scope`, `facility_id`, `currency` (spend-based), `reporting_period` link | See A12/A13. | 🔴 Critical | Medium | Medium | v1.0–v1.1 |
| `defra_conversion_factors` | `unit`, `scope`, `factor_source` (DEFRA/SEAI/EPA), `ghg_breakdown` (CO2/CH4/N2O) | SECR requires CO2e with disclosed factors; SEAI publishes CO2/CH4/N2O splits. | 🔴 Critical | Medium | Medium | v1.0 |
| `consultant_profiles` | `timezone`, `default_currency`, `cro_number` (or country-aware company_number), `company_number` constraint | White-label consultant invoices to UK/IE clients need correct currency/registration. | 🟡 Medium | Small | Low | v1.0–v1.1 |
| `consultant_billing` | `currency`, `invoice_number_prefix` | Prices exist (`auto_extraction_price`, `manual_extraction_price`) with **no currency at all** — the only billing table missing one. | 🟠 High | Small | Low | v1.0 |
| `consultant_clients` | `client_company_number`, `client_vat_number`, `client_country` | Client records store only name/email/phone; can't validate or report on the underlying business entity. | 🟢 Low | Small | Low | v1.1 |
| `waitlist` / `beta_users` | `country` | Can't segment UK vs IE demand for a two-market launch; also feeds scope hygiene (Section G). | 🟢 Low | Small | Low | v1.1 |
| `system_settings` | Nothing missing, but `default_vat_rate` vs `default_tax_rate` are redundant duplicates with no source of truth | Ambiguity: UK VAT 20%, IE VAT 23% — which column wins? Pick one, keep other dormant. | 🟡 Medium | Small | Low | v1.0 |
| *(table missing)* | `contacts` table (org-level contacts) | Contact data is scattered as inline `primary_contact_*` columns on 3 tables; no multi-contact support (finance vs sustainability vs site manager). Defer if v1.0 scope is single-contact. | 🟡 Medium | Medium | Medium | v1.1–v2.0 |
| *(table missing)* | `support_tickets` | `user_feedback` partially covers it but lacks ticket lifecycle (queue, SLA link, requester org linkage is nullable). Acceptable for v1.0. | 🟢 Low | Medium | Medium | v1.1–v2.0 |
| *(table missing)* | `invoices` (platform billing) | Stripe IDs exist on `customer_subscriptions`/`consultant_billing` but no local invoice records (number, VAT, PDF URL) — UK/EU VAT invoicing requires sequential invoice numbers and stored VAT invoices. | 🟠 High | Medium | Low | v1.1 |

---

## D) Address Architecture Assessment

**Current state per table:**

| Table | line1/line2 | city | county | postcode | eircode | country | lat/long | text blob? |
|---|---|---|---|---|---|---|---|---|
| `organizations` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (free text) | ❌ | ✅ `registered_address` + `billing_address` (text) |
| `facilities` | ✅ | ✅ | ✅ | ✅ **NOT NULL** | ❌ **missing** | ✅ (nullable, free text) | ✅ | ❌ |
| `suppliers` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (free text) | ❌ | ✅ `address` (text) |
| `consultant_profiles` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (free text) | ❌ | ❌ |

**Assessment:**
1. 🔴 **D1. `facilities` postcode NOT NULL + no eircode** — Irish facilities unenterable (see B1). *Critical / Small / Medium risk / v1.0 blocker.*
2. 🟠 **D2. Dual storage (structured + single-text `registered_address`/`billing_address`/`address`)** — guaranteed divergence: two writers, no sync rule. Recommend structured columns as canonical, demote text blobs to dormant (or app-generated display cache). Conflicts with nothing — it's a data-entry convention, not redesign. *High / Small / Low / v1.0.*
3. 🟠 **D3. No `country_code` (ISO 3166-1 alpha-2)** anywhere — every address rule (postcode vs Eircode, county list, phone prefix, currency) needs a machine-readable country. Free-text `country` will collect "UK", "United Kingdom", "GB", "England". *High / Small / Low / v1.0.*
4. 🟡 **D4. Geocoding readiness partial** — `facilities` has `latitude`/`longitude` (good) but `organizations`/`suppliers` don't, and there is **no `geocode_status`/`address_validation_status`** on any table. Without a validation-status column you can't build the "verify address → Royal Mail PAF / Loqate / Eircode finder → mark validated" UX loop. Add `address_validation_status` (enum: unverified/verified/failed) + `formatted_address` (the canonical string returned by the lookup provider). *Medium / Small / Low / v1.1.*
5. 🟡 **D5. Google Maps / PAF / Loqate compatibility** — structured line1/line2/city/county/postcode-or-eircode/country maps cleanly onto both PAF (UK: add `post_town`, `dependent_locality` optionally later) and Eircode (routing key ≠ town). Missing `post_town` is acceptable for v1.0 (city can serve). Keep everything nullable except line1+country. *Low / Small / Low / v1.1.*
6. 🟢 **D6. `facilities.region` vs `county` semantic overlap** — document that `region` = UK nation / IE province if kept, else dormant. *Low / Small / Low / v1.1.*

---

## E) Validation Rules Matrix (field → rule → severity)

| Field(s) | Rule | Status in schema | Severity | Effort | Risk | Version |
|---|---|---|---|---|---|---|
| All `email` columns (`users.email`, `pending_invites.email`, `waitlist.email`, `beta_users.email`, `email_logs.email`, contact emails on 6+ tables) | RFC-5322-lite regex + lowercase normalisation (citext for unique emails) | None | 🟠 High | Small | Low | v1.0 |
| All phone columns (`consultant_profiles.phone/support_phone`, `suppliers.contact_phone/primary_phone`, `organization_metadata.primary_contact_phone`, `consultant_clients.client_contact_phone`) | E.164 `^\+[1-9]\d{6,14}$`; v1.0 allow +44/+353 only (app layer) | None | 🟠 High | Small | Low | v1.0 |
| `*.vat_number` (3 tables) | GB: `^GB(\d{9}\|\d{12}\|(GD\|HA)\d{3})$`; IE: `^IE(\d{7}[A-W]{1,2}\|\d[A-W]\d{5}[A-W])$`; checksum at app layer; jurisdiction picked by `country` | None | 🟠 High | Small | Low | v1.0 |
| `*.company_number` (3 tables) | GB: `^([A-Z]{2}\d{6}\|\d{8})$` with CH prefix allowlist; IE: `^\d{6}$` (CRO) | None (org has Unique only) | 🟠 High | Small | Low | v1.0 |
| `*.postcode` (3 tables + facilities) | UK postcode regex (GIR + all outward formats), normalise case/spacing | None | 🟠 High | Small | Low | v1.0 |
| `*.eircode` (3 tables; facilities missing) | `^[AC-FHKNPRTV-Y\d]{3}\s?[AC-FHKNPRTV-Y\d]{4}$` + routing-key allowlist | None | 🟠 High | Small | Low | v1.0 |
| All 6 `currency` columns + `system_settings.default_currency` | ISO 4217, CHECK IN ('GBP','EUR') for v1.0 | None | 🔴 Critical | Small | Low | v1.0 |
| All 4 `country` columns | ISO 3166-1 alpha-2, CHECK IN ('GB','IE') for v1.0 | None | 🔴 Critical | Small | Low | v1.0 |
| `organizations.timezone`, `business_hours.timezone`, `system_settings.default_timezone` | IANA tz names, v1.0 ∈ {Europe/London, Europe/Dublin} | None | 🟠 High | Small | Low | v1.0 |
| `*.tax_region`, `*.vat_region`, `*.registration_region`, `carbon_tax_region` (orgs, suppliers, consultants, system_settings) | Enum GB/IE (these are currently 7+ free-text columns) | None | 🟡 Medium | Small | Low | v1.0–v1.1 |
| Emission values: `emissions_logs.raw_quantity/calculated_kg_co2e`, `customer_documents.calculated_emissions_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*`, `emission_factor*`, `supplier_categories.default_emission_factor` | CHECK ≥ 0 | None | 🟠 High | Small | Low | v1.0 |
| Percentages: `organization_metadata.renewable_energy_percentage/carbon_offset_percentage`, `consultant_profiles.commission_rate`, `staff_performance.qc_pass_rate/accuracy_rate`, `staff_workload.capacity_percentage`, `team_performance.qc_pass_rate/sla_compliance_rate`, `report_generation_queue.progress_percentage`, `tax_rate` columns | CHECK 0–100 (or 0–1 consistently — currently mixed semantics, e.g. `confidence_score` float8/numeric unspecified) | None | 🟠 High | Small | Low | v1.0 |
| `confidence_score` (customer_documents float8, emissions_logs numeric, ai_confidence_score, ai_mapping_confidence) | One scale (0–1), CHECK range, consistent type (float8 vs numeric mixed) | Inconsistent types, no CHECK | 🟡 Medium | Small | Low | v1.0 |
| URLs: `website` (3 tables), `logo_url`, `privacy_policy_url`, `terms_url`, `webhook_url`, `client_portal_url`, `file_url` columns, `screenshot_url` | `^https?://` + length cap; webhooks https-only | None | 🟡 Medium | Small | Low | v1.0 |
| File constraints: `file_attachments.file_size` **int4** (2 GB overflow risk — `organization_files.size_bytes` is int8, inconsistent), `mime_type`/`file_type` free text everywhere | int8 for sizes; mime allowlist (pdf, xlsx, csv, jpg, png); CHECK size > 0 and ≤ `system_settings.max_upload_size_mb` | Partial (organization_files best) | 🟠 High | Small | Low | v1.0 |
| Ratings: `user_feedback.rating`, `ai_content_history.user_rating` | CHECK 1–5 | None | 🟢 Low | Small | Low | v1.0 |
| Counts: `page_count`, `total_files`, `processed_files`, `*_used`, `*_limit`, `employee_count` | CHECK ≥ 0; `used ≤ limit` where paired | None | 🟡 Medium | Small | Low | v1.0 |
| `ip_address` across 8 log tables | Standardise on `inet` (audit_trail/staff_activity_log/login_history use inet; activity_logs/document_activity_log use varchar; others text) | Inconsistent | 🟢 Low | Small | Low | v1.1 |
| `financial_year_end`, `fiscal_year_start/end`, `contract_start/end`, `billing_period_start/end` | CHECK end > start where pair present | None | 🟡 Medium | Small | Low | v1.0 |
| `emissions_logs.start_date/end_date` | CHECK end_date ≥ start_date | None | 🟠 High | Small | Low | v1.0 |

---

## F) Fields to Mark v2.0+ / Dormant (EU/US-centric)

| Field (table) | Verdict | Rationale |
|---|---|---|
| `organizations.cik` | **Dormant — v2.0+ / arguably Never** | US SEC CIK. Zero UK/IE relevance. |
| `organizations.naics_code`, `organization_metadata.naics_code` | **Dormant — v2.0+** | US/Canadian classification. UK uses SIC 2007 (keep); IE uses NACE. |
| `organizations.isin` | **Dormant — v2.0+** | Securities identifier; only matters for listed-company reporting (subset of SECR quoted companies). Not v1.0 SME scope. |
| `organizations.sedol` | **Dormant — v2.0+** | Technically a *London* Stock Exchange identifier (UK-relevant), but only for listed entities — out of v1.0 SME scope. |
| `organizations.lei` | **Keep dormant, v1.1 candidate** | LEI is global and appears in UK regulatory contexts; cheap to keep, no harm. |
| `organizations.nace_code` | **Keep dormant — BUT note B10**: Ireland's CRO uses NACE Rev.2, so this may activate for IE customers in **v1.1**, earlier than other EU fields. | Disambiguation, not removal. |
| `organizations.esrs_enabled`, `activity_categories.esrs_e1_category`, `product_categories.esrs_e1_category` | **Keep dormant.** CSRD/ESRS is EU — but Ireland has transposed CSRD, so large Irish customers are in scope. Flag for **v1.1 review** (not v2.0) if enterprise IE clients sign. | Do not delete. |
| `organizations.issb_enabled`, `activity_categories.issb_category`, `product_categories.issb_category` | **Dormant — v2.0+** | ISSB/IFRS S1-S2 voluntary; UK SRS still pending. |
| `organization_metadata.total_floor_area_sqft`, `occupied_floor_area_sqft` | **Dormant** (imperial/US-flavoured); add sqm columns (Section C) rather than removing. | ADR-safe (additive). |
| `suppliers.swift_code` | Keep (needed for IE/international payments). | Not in scope to flag. |
| `system_settings.default_vat_rate` vs `default_tax_rate` | Keep one, **dormant the other** — duplicate semantics. | v1.0 tidy-up. |

---

## G) Seed Data & Scope Inconsistencies

| # | Finding | Severity | Effort | Risk | Version |
|---|---|---|---|---|---|
| G1 | Seed users include `klaus.schmidt@eurologistics.de`, `marie.dubois@pharmacare.fr`, `anna.makela@nordictech.fi` — **.de/.fr/.fi users in a UK/IE-only launch**. Test-data hygiene + market-scope inconsistency: if these reach production, analytics, per-country logic, and future GDPR data-residency assumptions are polluted. Replace with `.co.uk`/`.ie` fixtures. | 🟡 Medium | Small | Low | v1.0 (pre-launch cleanup) |
| G2 | `peter.chen@datavision.ai` — non-market TLD as well (`.ai`); same treatment. | 🟢 Low | Small | Low | v1.0 |
| G3 | All `password_hash = null` — acceptable if Supabase Auth owns credentials (ADR-consistent), but then `users.password_hash` column itself is dead weight; mark dormant to avoid a future dev writing to it. | 🟢 Low | Small | Low | v1.1 |
| G4 | All seed rows have `updated_at = 2026-08-02` (a single future-dated timestamp) while `created_at` varies — impossible to trust audit columns in fixtures; also `email_verified = true` for all. Fixtures should exercise *false*/null states too, or validation gaps (Section E) will never be caught in testing. | 🟡 Medium | Small | Low | v1.0 |
| G5 | No seed user exercises an Irish-specific path (no Eircode/CRO/IE VAT anywhere in seed data — note `emma.walsh@greenenergy.ie` and `john.obrien@ecobuild.ie` exist but there is no Irish *org/facility* fixture, which is exactly why B1 — facilities can't take an Eircode — slipped through). Add IE org + IE facility fixtures after B1 fix as a regression guard. | 🟠 High | Small | Low | v1.0 |

---

## H) Summary Scoring Inputs (1–100)

| Dimension | Score | One-line justification |
|---|---|---|
| **Data Integrity** | **55** | Core business fields (country, currency, VAT, company number, postcode/Eircode, percentages, emission values, dates) are free text with virtually no CHECK constraints, plus dual structured/text address storage and unit-less emission quantities. |
| **Compliance** | **50** | UK (Companies House/HMRC/SIC 2007/SECR financial-year) and Irish (Eircode, CRO, IE VAT, SEAI factors, IE-transposed CSRD) validations are all absent, and Irish facilities cannot even be inserted (postcode NOT NULL, no eircode). |
| **Developer Experience** | **72** | Consistent UUID PKs, timestamptz, and jsonb metadata patterns are good, but devs face 6 unconstrained currency columns, 3 redundant contact/address patterns, inconsistent `ip_address` types, duplicated audit/log tables, and DEFRA-hard-coded naming for a two-market product. |

**Top-5 pre-launch blockers (all v1.0):** B1 (facilities eircode/postcode), A5+A6 (country & currency constraints), A2+B4+B5 (VAT/CH/CRO validation), A12+B8 (factor unit + source), A13 (emissions unit/scope/facility linkage).
