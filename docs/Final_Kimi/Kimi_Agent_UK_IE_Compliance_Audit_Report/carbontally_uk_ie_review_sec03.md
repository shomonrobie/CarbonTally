# CarbonTally UK/IE Production-Readiness Review

## 6. Missing Fields

The schema's domain coverage is broad, but a UK/Ireland launch exposes concrete column-level absences, all additive and ADR-compliant: critical gaps (6.1), high-value fields (6.2), deferred tables (6.3), addresses (6.4).

### 6.1 Critical Gaps

These gaps block legitimate data entry or make reporting numbers unauditable.

| Finding | Table / column(s) | Gap and consequence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| (finding B-1) | `facilities.eircode` (add); `facilities.postcode` (relax NOT NULL) | Ireland has no postcodes; other address tables carry `eircode`, but `facilities` mandates `postcode` — Irish sites are uninsertable. | 🔴 Critical | Small | Medium | v1.0 blocker |
| (finding A-13) | `emissions_logs.unit`, `.scope`, `.facility_id` | `raw_quantity` is unit-less; scope only inferable via the factor join; emissions attach only to a nullable `asset_id` — site-level SECR totals uncomputable. | 🔴 Critical | Medium | Medium | v1.0–v1.1 |
| (findings A-12, B-8; DIM-02 finding E-1) | `defra_conversion_factors.unit`, `.scope`, `.factor_source` | `co2e_multiplier` never states kg CO2e per *what*; without `factor_source` (DEFRA-DESNZ vs SEAI/EPA), Irish organisations silently get UK grid factors (wrong Scope 2). | 🔴 Critical | Medium | Medium (backfill) | v1.0 |
| (DIM-01 §C; DIM-02 finding C-5) | `customer_documents.document_number`, `.document_date`, `.currency`, `.net_amount`, `.vat_amount`, `.gross_amount` | Extraction results live only in `extracted_data` jsonb: no duplicate-invoice detection, no currency-consistent totals, no spend-based reconciliation. | 🔴 Critical | Medium | Low | v1.0–v1.1 |
| (DIM-01 §C) | `consultant_billing.currency`, `.invoice_number_prefix` | `auto_extraction_price`/`manual_extraction_price` have no currency — the only billing table missing one; GBP/EUR ambiguity guaranteed. | 🟠 High | Small | Low | v1.0 |
| (DIM-02 finding A-1; DIM-03 finding B-6) | `organizations.is_active` / `.archived_at` | Child tables (`suppliers`, `facilities`, `assets`, `organization_members`) have `is_active`; the tenant root does not — churned customers cannot be suspended without deleting audit evidence (cross-reference: Architecture chapter). | 🔴 Critical | Small | Low | v1.0 |

The pattern is consistent: the schema stores *values* generously but withholds the *qualifiers* that give them meaning — unit, scope, currency, provenance, jurisdiction. For a carbon-accounting product that is the most dangerous defect class, because nothing fails loudly: rows insert, pipelines run, reports generate — and the numbers are simply wrong. The `facilities.eircode` gap is the exception, failing immediately in the first Irish onboarding session. All six are Small-to-Medium effort, pre-launch-safe, requiring no redesign; only the `emissions_logs` backfill may phase into v1.1.

### 6.2 High-Value UK/IE Business Fields

Each removes a recurring UK/Irish friction or makes an AI process deterministic.

| Finding | Table / column(s) | Why it matters (UK/IE) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| (finding A-9; DIM-03 finding B-9) | `suppliers.sort_code` | UK payments use sort code + account number; `iban`/`swift_code` serve Ireland — UK suppliers cannot be paid correctly today. | 🟠 High | Small | Low | v1.0 |
| (DIM-01 §C) | `organizations.legal_entity_type` (enum: Ltd, PLC, LLP, CIC, DAC, CLG, sole trader, partnership) | Drives Companies House prefixes and legal identity on SECR reports; Irish DAC/CLG/LTD forms differ; `business_structure` free text — constrain or replace. | 🟠 High | Small | Low | v1.0 |
| (finding A-8) | `organizations.phone`, `.mobile` | Contact emails exist but no organisation phone; UK onboarding, credit checks and Stripe billing require one. | 🟡 Medium | Small | Low | v1.0 |
| (DIM-01 §C) | `facilities.meter_mpan_mprn` (+ `site_manager_name`/`phone`, `floor_area_sqm`) | UK MPAN/MPRN and Irish MPRN tie utility bills to sites; mapping today is fuzzy AI only (`ai_mapped_facility_id`). Meter numbers make it deterministic. | 🟠 High | Small–Medium | Low | v1.0–v1.1 |
| (DIM-02 finding D-3) | `organization_metadata.total_floor_area_sqm`, `.occupied_floor_area_sqm` | Ireland uses m² exclusively, the UK officially so; sqft-only columns invite m² mislabelled as sq ft, corrupting SECR intensity ratios. | 🟡 Medium | Small | Low | v1.0 |
| (DIM-01 §C; DIM-03 finding B-4) | `users.phone`, `users.timezone` | `system_settings.two_factor_method` anticipates SMS 2FA — impossible without a per-user phone; timezone drives SLA display. | 🟡 Medium | Small | Low | v1.0–v1.1 |

Two fields deserve emphasis. `facilities.meter_mpan_mprn` converts bill-to-facility mapping from probabilistic to deterministic: every MPAN is unique to a supply point, so one column eliminates an entire class of misattributed emissions and reduces dependence on AI confidence thresholds. The sqm floor-area columns protect SECR intensity ratios at trivial cost — a dual-unit schema with one labelled and one dormant column is fully ADR-compliant. Both are cheap insurance against errors surfacing at a customer's first assurance review, when correction is most expensive and most visible.

### 6.3 Missing Tables (v1.1+)

Three tables are absent; none justifies a v1.0 rush.

| Missing table | Justification | Deferral rationale | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| `invoices` (platform billing) | Stripe IDs exist on `customer_subscriptions`/`consultant_billing` but no local invoice records (number, VAT amount, PDF URL); UK VAT invoicing requires sequential numbers and stored VAT evidence (DIM-02 finding C-5; DIM-03 finding E-2). | Stripe-hosted invoices/Tax cover the 20%/23% UK/IE split for v1.0; needed once invoice search and consultant billing mature. | 🟠 High | Medium | Low | v1.1 |
| `contacts` | Contact data is scattered as inline `primary_contact_*`/`contact_*` columns across four tables — same person stored three ways, no multi-contact support. | Acceptable while v1.0 onboarding is single-contact; introduce with supplier-portal readiness. | 🟡 Medium | Medium | Medium | v1.1–v2.0 |
| `support_tickets` | `user_feedback` partially covers it (status, severity, `assigned_to`) but lacks ticket lifecycle: queue, SLA linkage, requester organisation. | Adequate as tickets-v1; defer until volume justifies a dedicated model. | 🟢 Low | Medium | Medium | v1.1–v2.0 |

The deferral logic is deliberate and belongs in the roadmap. Columns are cheap and additive, so they go in early; tables encode workflow commitments, so they wait until the workflow is real. Introducing `invoices` now would create a second source of truth competing with Stripe; introducing `contacts` now would freeze a premature model. One precondition is non-negotiable: when `invoices` arrives it must store VAT evidence locally rather than depend on Stripe retention, because UK accounting-record obligations rest with customers, not Stripe.

### 6.4 Address Architecture Assessment

Four address tables are capable but undermined by dual storage and no machine-readable country.

| Table | Structured lines | `postcode` | `eircode` | `country` | Lat/long | Free-text blob |
|---|---|---|---|---|---|---|
| `organizations` | ✅ | ✅ | ✅ | free text | ❌ | ✅ `registered_address` + `billing_address` |
| `facilities` | ✅ | ✅ **NOT NULL** | ❌ missing | nullable free text | ✅ | ❌ |
| `suppliers` | ✅ | ✅ | ✅ | free text | ❌ | ✅ `address` |
| `consultant_profiles` | ✅ | ✅ | ✅ | free text | ❌ | ❌ |

The structural skeleton is genuinely good — `line1/line2/city/county/postcode-or-eircode/country` maps cleanly onto Royal Mail PAF, Loqate and the Eircode finder — so remediations are conventions and small columns, not redesign. Weaknesses concentrate in two places: `facilities`, the most important address in a carbon product (it is where emissions occur) yet the least complete (mandatory postcode, no Eircode); and the free-text blobs holding a second, unverifiable copy of every `organizations`/`suppliers` address. Two writers, no synchronisation rule: divergence is a certainty, not a risk.

| Finding | Issue and recommendation | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| (finding D-1) | `facilities.postcode` NOT NULL + no `eircode` — Irish facilities unenterable; fix per finding B-1 (add `eircode`, conditional `postcode`). | 🔴 Critical | Small | Medium | v1.0 blocker |
| (finding D-2) | Dual storage (structured + text `registered_address`/`billing_address`/`address`), two writers, no sync rule — make structured canonical; demote blobs. | 🟠 High | Small | Low | v1.0 |
| (finding D-3) | No `country_code` (ISO 3166-1 alpha-2) — every address rule (postcode vs Eircode, currency, phone prefix) needs a machine-readable country; free text collects "UK", "England". | 🟠 High | Small | Low | v1.0 |
| (finding D-4) | Geocoding readiness partial — only `facilities` has `latitude`/`longitude`; no `address_validation_status` (unverified/verified/failed) or `formatted_address` anywhere, so the verify-then-mark-validated loop cannot be built. | 🟡 Medium | Small | Low | v1.1 |
| (finding D-5) | PAF/Loqate-compatible — structured set maps onto both providers; `post_town`/`dependent_locality` can follow later. | 🟢 Low | Small | Low | v1.1 |
| (finding D-6) | `facilities.region` overlaps `county` — document `region` as UK nation / IE province if kept, else dormant. | 🟢 Low | Small | Low | v1.1 |

Findings D-2 and D-3 are prerequisites for everything in Section 7: jurisdiction-keyed validation can only key off a constrained, machine-readable country, and only works with one canonical address per entity. Until then, every downstream rule rests on a field users can fill with "England". PAF/Loqate/Eircode-finder readiness is otherwise strong — once `facilities.eircode` exists and the blobs are demoted, both markets support verified addresses with only the v1.1 status/cache columns outstanding. That position should be protected by refusing any new free-text address fields.

## 7. Validation Improvements

Almost every business field is free text with no CHECK constraint. The programme: jurisdiction-keyed rules (7.1), the full matrix (7.2), semantic consistency (7.3), dormancy (7.4).

### 7.1 Jurisdiction-Keyed Validation

All jurisdiction logic keys off `country`, unconstrained free text on `organizations`, `facilities`, `suppliers`, `consultant_profiles` (finding A-5); CHECK IN ('GB','IE') unlocks the paired rules below.

| Rule surface | GB rule | IE rule | Table.column(s) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|---|
| Postal code + conditional presence | UK postcode regex, GIR-valid, normalised (finding A-3); `country='GB'` ⇒ `postcode` present (finding B-2) | Eircode regex — routing key + identifier, excludes I/O (finding B-3); `country='IE'` ⇒ `eircode` present | `organizations.postcode`/`eircode`, `suppliers.*`, `consultant_profiles.*`, `facilities.*` | 🟠 High | Small | Low | v1.0 |
| VAT number | `GB` + 9 or 12 digits, `GBGD`/`GBHA` + 3 (finding A-2) | `IE` + 7 digits + 1–2 letters; legacy `IE` + digit + 6 digits + 2 letters (finding B-5) | `organizations.vat_number`, `suppliers.vat_number`, `consultant_profiles.vat_number` | 🟠 High | Small | Low | v1.0 |
| Company number | 8 digits or 2-alpha prefix + 6 digits, allowlist (finding A-1) | CRO: 6 digits (finding B-4; DIM-03 finding C-9) | `organizations.company_number`, `suppliers.company_number`, `consultant_profiles.company_number` | 🟠 High | Small | Low | v1.0 |
| Currency | GBP (finding A-6) | EUR by default when `country='IE'` (finding B-9) | All six `currency` columns + `system_settings.default_currency` | 🔴 Critical | Small | Low | v1.0 |
| Timezone | `Europe/London` | `Europe/Dublin` (finding A-7) | `organizations.timezone`, `business_hours.timezone`, `system_settings.default_timezone` | 🟠 High | Small | Low | v1.0 |

Sequencing matters. The `country` constraint must land first, because every paired rule — and the conditional postcode/Eircode CHECK (finding B-2) — reads from it; applying format CHECKs to rows whose country says "UK" or "England" would reject legitimate data on rollout. Format regexes belong in the database; checksums (HMRC MOD97/MOD9755, Eircode routing-key allowlist) belong at the application layer. A single `company_number` column serving both jurisdictions (finding B-4) works only with country-conditional validation — left unconstrained and unique, it poisons duplicate detection and future registry lookups.

### 7.2 Field-Level Validation Matrix

Complete matrix (DIM-01 §E); all rules are additive CHECKs or normalisation conventions.

| Field(s) | Rule | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| All `email` columns (`users.email`, `pending_invites.email`, `waitlist.email`, `beta_users.email`, `email_logs.email`, + contact emails) | RFC-5322-lite regex + lowercase normalisation | 🟠 High | Small | Low | v1.0 |
| All phone columns (`consultant_profiles.phone`/`support_phone`, `suppliers.contact_phone`/`primary_phone`, `organization_metadata.primary_contact_phone`, `consultant_clients.client_contact_phone`) | E.164 pattern; +44/+353 in v1.0 (app layer) | 🟠 High | Small | Low | v1.0 |
| `*.vat_number` (3 tables) | GB/IE patterns per 7.1; checksum at app layer | 🟠 High | Small | Low | v1.0 |
| `*.company_number` (3 tables) | GB CH formats + prefix allowlist; IE CRO 6 digits | 🟠 High | Small | Low | v1.0 |
| `*.postcode` (3 tables + `facilities`) | UK postcode regex (GIR-valid); normalise case/spacing | 🟠 High | Small | Low | v1.0 |
| `*.eircode` (3 tables; `facilities` missing) | Eircode regex + routing-key allowlist (app layer) | 🟠 High | Small | Low | v1.0 |
| All 6 `currency` columns + `system_settings.default_currency` | ISO 4217; CHECK IN ('GBP','EUR') | 🔴 Critical | Small | Low | v1.0 |
| All 4 `country` columns | ISO 3166-1 alpha-2; CHECK IN ('GB','IE') | 🔴 Critical | Small | Low | v1.0 |
| `organizations.timezone`, `business_hours.timezone`, `system_settings.default_timezone` | IANA names; ∈ {Europe/London, Europe/Dublin} | 🟠 High | Small | Low | v1.0 |
| `*.tax_region`/`vat_region`/`registration_region`, `carbon_tax_region` (7+ free-text columns) | Enum GB/IE | 🟡 Medium | Small | Low | v1.0–v1.1 |
| Emission values: `emissions_logs.raw_quantity`/`calculated_kg_co2e`, `customer_documents.calculated_emissions_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*`, `emission_factor*`, `supplier_categories.default_emission_factor` | CHECK ≥ 0 | 🟠 High | Small | Low | v1.0 |
| Percentages: `organization_metadata.renewable_energy_percentage`/`carbon_offset_percentage`, `consultant_profiles.commission_rate`, `staff_performance.qc_pass_rate`/`accuracy_rate`, `staff_workload.capacity_percentage`, `team_performance.qc_pass_rate`/`sla_compliance_rate`, `report_generation_queue.progress_percentage`, `tax_rate` columns | CHECK 0–100 (or 0–1 consistently — mixed today) | 🟠 High | Small | Low | v1.0 |
| `confidence_score` family (`customer_documents` float8, `emissions_logs` numeric, `ai_confidence_score`, `ai_mapping_confidence`) | One 0–1 scale, CHECK range, consistent type | 🟡 Medium | Small | Low | v1.0 |
| URLs: `website` (3 tables), `logo_url`, `privacy_policy_url`, `terms_url`, `webhook_url`, `client_portal_url`, `file_url`, `screenshot_url` | `^https?://` + length cap; webhooks https-only | 🟡 Medium | Small | Low | v1.0 |
| File constraints: `file_attachments.file_size` int4 (2 GB overflow vs int8 `organization_files.size_bytes`, DIM-03 finding A-6); `mime_type`/`file_type` free text | int8 sizes; mime allowlist (pdf/xlsx/csv/jpg/png); CHECK 0 < size ≤ `max_upload_size_mb` | 🟠 High | Small | Low | v1.0 |
| Ratings: `user_feedback.rating`, `ai_content_history.user_rating` | CHECK 1–5 | 🟢 Low | Small | Low | v1.0 |
| Counts: `page_count`, `total_files`, `processed_files`, `*_used`, `*_limit`, `employee_count` | CHECK ≥ 0; `used ≤ limit` where paired | 🟡 Medium | Small | Low | v1.0 |
| `ip_address` across 8 log tables | Standardise on `inet` (mixed inet/varchar/text) | 🟢 Low | Small | Low | v1.1 |
| `financial_year_end`, `fiscal_year_start`/`end`, `contract_start`/`end`, `billing_period_start`/`end` | CHECK end > start where paired | 🟡 Medium | Small | Low | v1.0 |
| `emissions_logs.start_date`/`end_date` | CHECK `end_date ≥ start_date` | 🟠 High | Small | Low | v1.0 |

The matrix is deliberately exhaustive because partial validation is worse than none: it creates false confidence while leaving aggregates — SECR totals, intensity ratios, spend reconciliations — hostage to the weakest unconstrained column. The two Critical rows (`currency`, `country`) gate everything beneath them and should ship together. Effort is uniformly Small and risk Low because CHECKs are additive; only `ip_address` and the region enums defer past v1.0. The emission-value and percentage rows carry disproportionate compliance weight: one negative `calculated_kg_co2e` silently corrupts every report.

### 7.3 Semantic Consistency Fixes

Four fields carry ambiguous or duplicated semantics that produce contradictory numbers.

| Finding | Issue and fix | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| (DIM-01 §E; DIM-03 finding C-6) | `confidence_score` mixed scale and type: `customer_documents.confidence_score` float8 vs numeric on `emissions_logs.confidence_score`, `ai_confidence_score`, `ai_mapping_confidence`; no range CHECK. Standardise numeric, one 0–1 scale. | 🟡 Medium | Small | Low | v1.0 |
| (DIM-01 §E; DIM-03 finding B-8) | `ip_address`: `inet` in `audit_trail`, `staff_activity_log`, `login_history`; varchar in `activity_logs`, `document_activity_log`, `user_activity_log`; text elsewhere — standardise on `inet`. | 🟢 Low | Small | Low | v1.1 |
| (DIM-01 §F; DIM-03 finding C-5) | `system_settings.default_vat_rate` vs `default_tax_rate`: redundant duplicates, no source of truth; UK VAT 20% vs IE 23% makes ambiguity costly. Keep one, dormant the other. | 🟡 Medium | Small | Low | v1.0 |
| (DIM-03 finding C-6) | Duplicate contact columns: `suppliers.contact_email` vs `primary_email`, `contact_phone` vs `primary_phone`; `organization_metadata.primary_contact_*` duplicates `organizations.*` — pick one source of truth. | 🟡 Medium | Medium | Medium | v1.1 |

These are not cosmetic. A confidence score whose scale differs between `customer_documents` and `emissions_logs` will be averaged into nonsense by the first dashboard combining them; a duplicated VAT/tax rate guarantees billing and reporting eventually disagree. The duplicated contact columns drift silently until a supplier is invoiced at a stale address. All four fixes are conventions plus CHECKs — cheap now, expensive after data accumulates — and none requires redesign. The v1.1 placement of `ip_address` and the contact columns reflects backfill effort, not importance.

### 7.4 EU/US-Centric Fields to Mark Dormant

Dormancy, not deletion: fields stay, marked out-of-scope for v1.0; nothing is removed.

| Field (table) | Verdict | Rationale | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| `organizations.cik` | Dormant | US SEC identifier; zero UK/IE relevance. | 🟢 Low | — | — | v2.0+ / arguably never |
| `organizations.naics_code`, `organization_metadata.naics_code` | Dormant | US/Canadian classification; UK uses SIC 2007, IE uses NACE. | 🟢 Low | — | — | v2.0+ |
| `organizations.isin` | Dormant | Securities identifier; listed companies only. | 🟢 Low | — | — | v2.0+ |
| `organizations.sedol` | Dormant | London Stock Exchange identifier (UK-relevant), but listed entities only. | 🟢 Low | — | — | v2.0+ |
| `organizations.lei` | Keep dormant | Global identifier appearing in UK regulatory contexts; cheap to retain. | 🟢 Low | — | — | v1.1 candidate |
| `organizations.nace_code` | Keep dormant — may activate for IE | Ireland's CRO uses NACE Rev.2 (finding B-10); may activate for IE earlier than other EU fields. | 🟡 Medium | — | — | v1.1 review |
| `organizations.esrs_enabled`, `activity_categories.esrs_e1_category`, `product_categories.esrs_e1_category` | Keep dormant — may activate for IE | CSRD/ESRS is EU — but Ireland has transposed CSRD; large Irish customers are in scope now (finding B-10). | 🟡 Medium | — | — | v1.1 review if enterprise IE clients sign |
| `organizations.issb_enabled`, `activity_categories.issb_category`, `product_categories.issb_category` | Dormant | ISSB/IFRS S1-S2 voluntary; UK SRS still pending. | 🟢 Low | — | — | v2.0+ |
| `organization_metadata.total_floor_area_sqft`, `organization_metadata.occupied_floor_area_sqft` | Dormant | Imperial-flavoured; sqm columns added per Section 6.2 instead of removal. | 🟢 Low | — | — | Dormant |

The Ireland nuance cuts against the "EU means v2.0" instinct. `nace_code` and the `esrs_*` fields look like EU-expansion scaffolding, but Ireland is a launch market using NACE Rev.2 at the CRO that has already transposed CSRD — a large Irish customer could need both within months of a v1.1 signing. They are dormant-but-may-activate, reviewed at v1.1, and must not be deleted. By contrast `cik`/`naics_code` are genuinely foreign-market artefacts, and `issb_*` awaits UK SRS adoption. Dormancy marking prevents placeholder data accumulating in these columns.
