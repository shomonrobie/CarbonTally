# CarbonTally v1.0 — Hardening Challenge & Validation Triage (Principal Architect Review)

*Critical review of `carbontally_uk_ie_review.agent.final.md` §§3–7, 10, 12. Categories: **A** = must implement before launch / **B** = strongly recommended for v1.0 / **C** = defer to v1.1 / **D** = reject (reasoning given). Validation-layering rule applied rigorously: DB constraints protect integrity (uniqueness, ranges, NOT NULL, FK, simple IN-lists); presentation formats (VAT, postcode, Eircode, E.164, email) live at the API layer with libphonenumber/validator libraries — **not** in regex CHECK constraints.*

**Overall verdict on the audit report:** technically thorough and directionally correct on the four structural blockers (facilities Eircode, country/currency IN-lists, factor provenance, unit-less emissions), but it systematically over-locates validation in the database (§7.1 says "format regexes belong in the database" — rejected), over-severities several Medium items as v1.0/Critical, and is internally inconsistent on sqm floor area (§6.2 says v1.0, §12.2 item 14 says v1.1) and the Irish factor load (§5.4 "Critical" yet deferred to v1.1). Roughly: accept the spine of §12.1 items 1–3, 5–8; modify item 4 (split app/DB) and item 24 (split app/DB); downgrade items 8 (partial), 19, 21, 22 (partial); reject county lookup, nation field, `country_code` column, SIC/CH lookup tables, and all format-regex CHECKs.

---

## Table 1 — Validation-Layering Matrix (report §7.2, all rows triaged)

| Field(s) | Validate? | Layer: UI/API/DB/Multi | DB rule (if any) | Category | Reasoning |
|---|---|---|---|---|---|
| All `email` columns | Y | Multi: API (validator lib) + UI; DB stores lowercased | None new. Keep existing UNIQUE on `users.email`; lowercase-at-write convention | **B** (API validation + normalisation); **D** for RFC-5322 regex CHECK | Email shape is a presentation format; a DB regex rejects valid edge cases and rots. Lowercase normalisation matters because it feeds uniqueness and login. |
| All phone columns | Y | API only (libphonenumber; store E.164, +44/+353 in v1.0) | Optional max-length cap only | **B** (API); **D** for E.164 regex CHECK | The audit's `^\+[1-9]\d{6,14}$` CHECK (finding B6) duplicates one line of libphonenumber and can't validate per-country rules anyway. No DB regex. |
| `*.vat_number` (3 tables) | Y | Multi: API (GB/IE format + MOD97 checksum, jurisdiction picked by `country`) + uppercase/strip-spaces normalisation | None new. Normalised values feed the supplier-dedupe UNIQUE (Table 6) | **B** (API); **D** for GB/IE regex CHECKs | Format validation is app-layer per client rules. What the DB must guarantee is *uniqueness of the normalised value*, not its shape. |
| `*.company_number` (CH 8-char / CRO 6-digit) | Y | API only (country-conditional: CH formats + prefix allowlist for GB, 6 digits for IE) | Keep existing UNIQUE on `organizations.company_number` | **B** (API); **D** for DB regex; **D** for a separate `cro_number` column | One column + country-conditional app validation is correct; a second column creates a new duplicate. A country-conditional DB regex is exactly the fragile pattern the client rule excludes. |
| `*.postcode` (3 tables + `facilities`) | Y | Multi: API (GIR-valid regex) + normalisation (uppercase, single space) | None new (except the facilities presence rule, row below) | **B** (API); **D** for postcode regex CHECK | Normalisation is the valuable part (PAF/Loqate matching, trigram search) and is app-enforced. DB regex rejected per client rule. |
| `*.eircode` (3 tables; add to `facilities`) | Y | API (shape + routing-key allowlist) | None new | **B** (API); **D** for Eircode regex CHECK | Routing keys are a living allowlist owned by Eircode — the worst possible thing to freeze into a CHECK constraint. |
| `facilities.postcode`/`eircode` presence | Y | Multi: DB + API | **DB: relax `postcode` NOT NULL; add nullable `eircode`; simple presence CHECK `postcode IS NOT NULL OR eircode IS NOT NULL`** | **A** | The launch blocker. The DB rule is a presence check (integrity), not a format check — allowed. Country-conditional refinement (GB⇒postcode, IE⇒eircode) stays at API (**B**), so legitimate partial rows elsewhere aren't hard-blocked. |
| All 6 `currency` columns + `default_currency` | Y | Multi: DB + API default (EUR when `country='IE'`) | **DB: CHECK IN ('GBP','EUR')** | **A** | Simple, stable IN-list; every aggregation, Stripe reconciliation and spend-based calculation keys off it. The audit is right; this is the cheapest Critical fix in the report. |
| All 4 `country` columns | Y | Multi: DB + UI picker | **DB: CHECK IN ('GB','IE')** | **A** | Machine-readable country is the key every jurisdiction rule reads. Constrain the existing column — do **not** add a parallel `country_code` column (Table 2, D). |
| `timezone` (3 columns) | Y | Multi: DB + UI | DB: CHECK IN ('Europe/London','Europe/Dublin') | **B** | Simple IN-list, cheap and stable — but a wrong tz shifts SLA boundaries, it doesn't corrupt money or emissions data. Strongly recommended, not a gate. |
| `*.tax_region`/`vat_region`/`registration_region`, `carbon_tax_region` (7+ columns) | Y (later) | API when the features activate | None now | **C** | These columns serve dormant features (carbon tax v1.1+, IE/GB ETS). CHECKs on unused columns are ceremony; constrain at activation alongside the feature. |
| Emission values ≥ 0 (`emissions_logs.*`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*`, `supplier_categories.default_emission_factor`, etc.) | Y | DB | **DB: CHECK (value >= 0)** | **A** | Cheap range integrity on the numbers the product sells. One negative `calculated_kg_co2e` silently corrupts every SECR total. Correctly Critical in the audit. |
| Percentages (`renewable_energy_percentage`, `commission_rate`, `qc_pass_rate`, `capacity_percentage`, `progress_percentage`, `tax_rate` columns…) | Y | Multi: convention first, then DB | DB: CHECK 0–100 **after** declaring one scale canonical (0–100); fix the mixed 0–1/0–100 semantics first | **B** | The range CHECK is trivial; the hazard is the mixed scale. Landing CHECKs before the scale convention would reject legitimate rows. Sequence: convention (app) → backfill → CHECK. |
| `confidence_score` family (float8 vs numeric; `ai_confidence_score`, `ai_mapping_confidence`) | Y | Multi: DB type/scale standardisation | DB: one numeric type, one 0–1 scale, CHECK 0–1 | **B** | Challenge the audit's framing: these are *not* duplicates (extraction vs mapping confidence are different events) — the defect is type/scale inconsistency. Cheap to fix pre-launch, expensive after. |
| URLs (`website`, `logo_url`, `webhook_url`, `client_portal_url`, …) | Y (webhooks only) | API only | Optional length caps | **B** for https-only on `webhook_url` at API (SSRF guard); **C** for the rest; **D** for URL regex CHECKs | URL shape is presentation. Only the webhook rule is security-relevant and it is one line of app code, not a DB constraint. |
| File types/sizes (`file_attachments.file_size` int4, `mime_type`/`file_type`) | Y | Multi | **DB: widen `file_size` to int8; CHECK size > 0** (and ≤ `max_upload_size_mb` where practical) | **A** (int8 widening + size CHECK — pre-launch it's near-free, post-launch a table rewrite); **B** (mime allowlist at API); **D** (mime CHECK in DB — allowlists churn) | 2 GB overflow hits at the customer's highest-value moment. Mime enforcement is app-layer; a DB allowlist needs a migration every time product adds a format. |
| Ratings (`user_feedback.rating`, `ai_content_history.user_rating`) | Y | DB | CHECK 1–5 | **B** | Harmless, stable range. Not a blocker because nothing downstream aggregates ratings into compliance numbers. |
| Counts (`page_count`, `total_files`, `*_used`, `*_limit`, `employee_count`) | Y | DB | CHECK ≥ 0; `used ≤ limit` where paired | **B** | Worth having because `usage_tracking.*_used` gates billing limits, but counter drift itself is a v1.1 (recompute/trigger) problem — the CHECK alone doesn't fix it. |
| `ip_address` across ~8 log tables | N (not the format) | — | Standardise type on `inet` | **C** | Type consistency has real value for retention jobs and PII handling, but nothing reads these columns in v1.0 query paths. Do it with the v1.1 retention/tamper-evidence work. |
| Date pairs (`financial_year_end`, `fiscal_year_start/end`, `contract_start/end`, `billing_period_start/end`) | Y | DB | CHECK end > start where paired | **B** | Simple integrity, cheap. Per client rule: B. |
| `emissions_logs.start_date`/`end_date` | Y | DB | CHECK end_date ≥ start_date | **B** | Downgraded from the audit's High/v1.0: inverted periods are caught in app review and the CHECK is hygiene, not a gate. (Fiscal-year *alignment* to the org FY is an app-layer rule — v1.1.) |
| `sic_code` (SIC 2007) | Y (loosely) | UI/API (5-digit hint) | None | **C**; **D** for a SIC lookup table | SIC is informational on v1.0 reports; nothing computes from it. A lookup table is maintenance burden for zero consumers. |

---

## Table 2 — Missing/New Fields & Columns Triage (report §6, §12.1 items 1–9)

| Item | Category | Reasoning |
|---|---|---|
| `facilities.eircode` + relax `postcode` NOT NULL + presence CHECK | **A** | The single launch blocker. Minimum fix is exactly three parts: nullable `eircode` column, nullable `postcode`, at-least-one-present CHECK. No lookup tables, no regex, no `region` changes. |
| `emissions_logs.unit` (FK to `units.code`) + `.scope` | **A** | Unit-less quantities make SECR kWh totals an inference through the factor join. FK + IN-list are integrity-level DB rules. Backfill from the factor join can phase into the launch sprint. |
| `emissions_logs.facility_id` | **B** | Challenge to the audit's Critical: site rollups are derivable today via `asset_id → assets.facility_id`; the direct column is a denormalisation convenience with a backfill cost. Add nullable column + dual-write in v1.0 if trivial; don't gate launch on it. Guard against nullable `asset_id` at API instead. |
| `defra_conversion_factors.unit`, `.scope`, `.factor_source`/`factor_set`, `.country` + UNIQUE `(reporting_year, activity_type)` | **A** | Provenance columns + backfill 'DEFRA-DESNZ' are required regardless of when Irish data lands; the UNIQUE stops duplicate factors double-counting emissions. All integrity-level. |
| SEAI/EPA Irish factor **data load** (minimal core set) | **A** (upgraded from the audit's v1.1 — see Challenges #6) | Scope: Irish grid electricity + gas + common liquid fuels, current reporting year only. Full historical catalogue = C. |
| `customer_documents` typed invoice fields (`document_number`, `document_date`, `currency`, `net_amount`, `vat_amount`, `gross_amount`) | **C** | Challenge to the audit's Critical. `extracted_data` jsonb is ADR-protected and already carries these; typed columns duplicate pipeline output and force sync logic. v1.0 duplicate detection is covered by `file_checksum`. Promote hot keys in v1.1 once query logs prove the need (the audit's own §8.2 says exactly this, then contradicts itself in §6.1). |
| `customer_documents.file_checksum` (SHA-256) | **A** (column), C (unique enforcement) | Deterministic duplicate-upload detection; column on an empty table is near-free. |
| `customer_documents.deleted_at` | **A** | Asymmetric soft-delete on the primary pipeline entity breaks retention/erasure symmetry; additive and trivial. |
| `consultant_billing.currency` | **A** | The only billing table with undenominated prices in a two-currency launch. One nullable column + default + backfill. (`invoice_number_prefix`: **C** — no local invoicing until v1.1.) |
| `organizations.is_active` / `.archived_at` | **A** | Tenant root can't be suspended while every child table can. Small, low-risk, and the audit evidence must survive churn. Agree with the audit. |
| `suppliers.sort_code` | **B** | Downgraded from High/Critical-adjacent: CarbonTally stores supplier bank details but does not execute payment runs, so "cannot be paid correctly" overstates. Add the column anyway — cheap, and it stops sort codes being improvised into `iban` fields. Masking last-4 at API = B; encryption at rest = C. |
| `organizations.legal_entity_type` | **C** | Downgraded from the audit's High/v1.0. No v1.0 process consumes entity type (CH prefixes are validated app-side; SECR eligibility uses `is_public`/`is_listed` + size data). Add with the v1.1 reporting-metadata work; constrain `business_structure` at API in the meantime. |
| `organizations.phone`/`.mobile` | **C** | `primary_contact_email` exists; Stripe does not require an org phone. Add when v1.1 invoicing/billing needs it — a nullable column costs nothing then too. |
| `users.phone` (for SMS 2FA), `users.timezone` | **C** | Only meaningful when per-user 2FA ships (report's own §12.2 item 6 puts 2FA in v1.1). Ship the column with the feature, not before. |
| `facilities.meter_mpan_mprn` (MPAN/MPRN) | **B** | Genuinely valuable — converts bill→facility mapping from fuzzy AI to deterministic. Column is cheap; add now to avoid backfill. The *matching logic* is app work = C (v1.1). `site_manager_name/phone`: C. |
| `organization_metadata.total_floor_area_sqm` / `.occupied_floor_area_sqm` | **B** (columns + UI unit label); **C** (conversion tooling); sqft columns stay, dormant later | Resolves the audit's internal contradiction (§6.2 v1.0 vs §12.2 #14 v1.1). Irish customers *will* mislabel m² as sqft; two labelled nullable columns prevent that without any conversion machinery. |
| `address_validation_status` / `formatted_address` | **C** | Geocoding/autocomplete support — explicitly a C-class item per client rules. Schema is already PAF/Loqate-shaped; add with the v1.1 verification loop. |
| `country_code` (new ISO column, finding D3) | **D** | Rejected: the fix for free-text `country` is to constrain `country` to ('GB','IE') (Table 1, A), not to add a second country column that must be kept in sync with the first. The audit correctly diagnosed the disease and prescribed a second infection. |
| UK nation field (England/Scotland/Wales/NI, finding A10) | **D** | No v1.x consumer: CH prefix validation is app-layer; bank-holiday modelling (A14) is v1.1 and better served by org-level holiday date lists than jurisdiction modelling. Derivable from postcode outward area if ever needed. Revisit only alongside A14. |
| County lookup table (26 ROI + 6 NI + ceremonial, finding B7) | **D** | Nothing in v1.0 computes from `county`. The lookup carries real edge-case debt (Dublin city vs county, Dún Laoghaire–Rathdown/Fingal/South Dublin, Derry/Londonderry) for zero consumers. Free text + v1.1 address-verification normalisation is sufficient. |
| SIC 2007 lookup table / CH API integration | **D** | Gold-plating. External lookups, if ever needed, are app-layer integrations — no schema artefacts now. |
| Bank-holiday jurisdiction modelling (A14) | **D** (jurisdiction column); **C** (org-level holiday date support in v1.1) | Four-jurisdiction calendar modelling is disproportionate to a few SLA-boundary days per year; explicit per-org holiday dates solve it with less machinery. |
| `contacts` table | **C** | Inline contact columns are adequate for single-contact v1.0 onboarding; a premature contacts model freezes the wrong shape before the supplier portal exists. |
| `invoices` table (platform billing) | **C** | Stripe-hosted invoices + Stripe Tax cover UK 20%/IE 23% for v1.0. Non-negotiable precondition when built: store VAT evidence locally. |
| `support_tickets` table | **C** | `user_feedback` (status, severity, `assigned_to`) is adequate as tickets-v1 at launch volume. |
| `consultant_clients.client_company_number/vat/country`; `waitlist.country`; `trading_name`, `credit_limit`, `account_reference`, `purchase_order_required` | **C** | All legitimate, none launch-blocking; batch with the v1.1 Xero/QuickBooks and invoicing work. |

---

## Table 3 — UK Coverage Checklist

| Requirement | Schema-ready? | Gap fix | Category |
|---|---|---|---|
| Companies House compatibility (company number column) | ✅ `organizations.company_number` (+ suppliers/consultants), UNIQUE present | App-layer format validation (8-digit / prefix+6) + normalisation; no CH API lookup, no lookup table | **B** (API); **D** (DB regex, CH API, lookup) |
| VAT number | ✅ columns on 3 tables | App-layer GB formats + MOD97 checksum; normalise (uppercase, strip spaces) so the dedupe UNIQUE works | **B** (API); **D** (DB regex) |
| SIC 2007 | ✅ `sic_code` on `organizations` + `organization_metadata` | Free entry with a 5-digit UI/API hint; no lookup table | **C** |
| UK postcode | ✅ columns on all 4 address tables | App-layer GIR-valid regex + normalisation; relax `facilities.postcode` NOT NULL (shared with IE fix) | **B** (API validation); **A** (facilities nullability) |
| County | ✅ free-text column | Keep free text; normalise via v1.1 address verification; reject lookup table | **D** (lookup); C (normalisation) |
| Telephone formatting | ✅ phone columns exist | libphonenumber at API, store E.164 | **B** (API); **D** (DB regex) |
| Currency (GBP) | ✅ 6 columns + default, unconstrained | DB CHECK IN ('GBP','EUR') | **A** |
| Country | ✅ free-text columns | DB CHECK IN ('GB','IE') | **A** |
| UK payments (sort code) | ❌ column missing | Add nullable `suppliers.sort_code`; API last-4 masking | **B** |
| Timezone | ✅ columns exist | DB IN-list {Europe/London, Europe/Dublin} | **B** |
| Nation field / bank-holiday jurisdiction | ❌ (and not needed) | None — rejected; revisit with v1.1 calendar work as org-level holiday dates | **D** |
| SECR readiness | ⚠️ reporting spine strong; numbers unverifiable | Factor unit/scope/source (A), emissions unit/scope (A), single FY source convention (B); int4 `reporting_year` → period columns = v1.1 | Mixed — see Tables 1–2 |

---

## Table 4 — Ireland Coverage Checklist

| Requirement | Schema-ready? | Gap fix | Category |
|---|---|---|---|
| CRO number | ⚠️ served by `company_number` | Country-conditional app validation (6 digits when `country='IE'`); **no** separate `cro_number` column | **B** (API); **D** (new column, DB regex) |
| IE VAT number | ✅ columns exist | App-layer IE formats (current + legacy) + checksum | **B** (API); **D** (DB regex) |
| Eircode (orgs/suppliers/consultants) | ✅ columns exist | App-layer shape + routing-key allowlist | **B** (API); **D** (DB regex) |
| **Eircode on `facilities`** | ❌ **blocker: no column + `postcode` NOT NULL** | Minimum fix: add nullable `eircode`, relax NOT NULL, presence CHECK (postcode OR eircode). Nothing else. | **A** |
| County (26 ROI) | ✅ free-text column | Keep free text; reject 26+6 county lookup | **D** (lookup) |
| Telephone +353 | ✅ columns exist | Same E.164 app rule covers +353 — one rule, two markets | **B** (API) |
| EUR coupling | ⚠️ possible but unenforced | DB currency IN-list (A) + app default EUR when `country='IE'` | **A** (CHECK) / **B** (default) |
| Timezone `Europe/Dublin` | ✅ column exists | Same IN-list as UK | **B** |
| SEAI/EPA emission factors | ❌ no provenance columns, no data | Provenance columns + UNIQUE (A); **minimal core IE factor load before launch (A)**; full catalogue v1.1 (C) | **A** — see Challenges #6 |
| IE org/facility seed fixture (regression guard) | ❌ missing (only IE *users* seeded) | Add IE org + IE facility + EUR + IE-factor fixture proving the write path; remove .de/.fr/.fi/.ai seeds | **A** |
| NACE / ESRS (CSRD transposed in IE) | ✅ dormant columns | Keep dormant; v1.1 watch item if large IE customers sign — no v1.0 action | **C** |
| Carbon tax region (IE levies carbon tax) | ✅ dormant columns | Constrain at feature activation (v1.1+) | **C** |

---

## Table 5 — Address Model Verdict

| Field | v1.0 required? | Future? | Notes |
|---|---|---|---|
| `address_line1` | ✅ Yes (present on all 4 tables) | — | Keep nullable except where onboarding enforces at API. |
| `address_line2` | ✅ Yes (nullable) | — | Present; no action. |
| Town/City | ✅ Yes — single `city` column suffices | `post_town`/`dependent_locality` = v1.1+ (PAF fidelity) | Do not split town/city now; PAF extras are a lookup-provider concern, not v1.0. |
| County | ✅ Keep, free text | Normalisation via address verification (v1.1); **lookup table rejected (D)** | Nothing computes from county in v1.0. |
| Postcode / Eircode | ✅ Yes — both columns on all 4 tables (after the facilities fix) | — | Presence rule at DB on `facilities`; formats at API. |
| Country | ✅ Yes — constrained to ('GB','IE') | — | The existing `country` column, constrained. **No new `country_code` column (D).** |
| Latitude / Longitude | Not required for v1.0 operation (facilities already has them — keep) | Geocoding for other tables = v1.1+ (C) | Do not add lat/long to orgs/suppliers now; arrives free with the geocoding feature. |
| `address_validation_status` / `formatted_address` | ❌ No | v1.1 (C) — with the PAF/Loqate/Eircode verification loop | Explicitly C-class (geocoding/autocomplete) per client rules. |
| Text blobs (`registered_address`, `billing_address`, `suppliers.address`) | Demote now | — | **Convention (B), no schema change:** structured columns are canonical; blobs become app-generated display caches written *from* the structured columns. **D** for DB sync triggers — complexity and failure modes for a problem a write-path convention solves. |
| `facilities.region` | Leave as-is | Document or dormant (C) | Overlaps `county`; no consumer. Not worth a migration. |

---

## Table 6 — Single-Source-of-Truth Dispositions

| Duplicate set | Canonical | Other field disposition | Category |
|---|---|---|---|
| `confidence_score` (customer_documents, float8) vs `ai_confidence_score` / `ai_mapping_confidence` / `emissions_logs.confidence_score` (numeric) | Not true duplicates — different events (extraction vs mapping). Canonical *convention*: one type (numeric), one scale (0–1), CHECK range | Standardise float8 → numeric pre-launch while cheap | **B** |
| `system_settings.default_vat_rate` vs `default_tax_rate` (+ `tax_rate` column sprawl) | `default_vat_rate` (UK/IE terminology is VAT; line-level `tax_rate` columns are a separate, legitimate per-row concept — document the distinction, add 0–100 CHECK) | `default_tax_rate` → dormant (stop writes) | **B** |
| `suppliers.contact_email`/`contact_phone` vs `primary_email`/`primary_phone` | `contact_*` family (coherent name/email/phone set) | `primary_*` → dormant/derived; stop dual writes | **C** (drift is real but low-stakes pre-launch; fix with the contacts review, don't rush a data migration days before launch) |
| `organization_metadata.primary_contact_*` vs `organizations.primary_contact_*` | `organizations.*` (tenant root) | metadata copies → dormant/derived | **C** |
| Structured address columns vs `registered_address`/`billing_address`/`suppliers.address` text blobs | Structured columns | Blobs → app-generated display caches (write-path convention) | **B** |
| `organizations.financial_year_end` vs `organization_metadata.fiscal_year_start`/`fiscal_year_end` | `organization_metadata.fiscal_year_start/end` (a start+end pair fully expresses a UK FY; a lone year-end date cannot) | `financial_year_end` → derived display value | **B** (convention needed before SECR reporting ships; no migration) |
| `staff_profiles.email` vs `users.email` | `users.email` | `staff_profiles.email` → stop writes, dedupe in v1.1 | **C** |
| `pending_invites` vs `user_invitations` | `user_invitations` (full lifecycle: token, expiry, status) | `pending_invites` → block writes immediately, deprecate | **A** — the weaker table is a live security downgrade (no token/expiry); stopping writes is Small/Low |
| `notification_delivery` vs `notification_delivery_log` (identical columns) | Keep one (pick the one the app reads most) | Other → deprecated/aliased | **B** (cheap, but nothing corrupts if it slips a week past launch) |
| Four read-state mechanisms (`messages.read_by`, `read_count`/`last_read_at`, `conversations.read_by`/`unread_count`, `conversation_participants.last_read_at`) | `conversation_participants.last_read_at` | Others → derived (app/trigger), v1.1 | **C** — phantom badges erode trust but don't block launch; needs app changes |
| Approval state across 5 tables | Declare one canonical per surface (document-level: `customer_verifications`) | Others → documented, derived | **C** (documentation now, enforcement v1.1) |

---

## UX-Facing Items (report §10) — Dispositions

| Item | Category | Reasoning |
|---|---|---|
| `pg_trgm` trigram indexes (names, emails, file_name) powering search + duplicate detection | **B** | Downgraded from the audit's 🔴. Cheap and genuinely dual-purpose (search + "did you mean" supplier dedupe), but hard duplicate prevention rests on UNIQUE + normalised VAT/company numbers, not fuzzy search — and at launch volumes search works acceptably on plain b-tree indexes. Ship in the hardening sprint; do not gate go-live on it. |
| Free-text `status` → CHECK value lists for filter facets (~25 tables) | **B** | Agree with the mechanism (CHECK-in lists, not PG enums — ADR-consistent) but scope it: queue status, billing status, `customer_documents.status`, `organization_members.role` first. Attempting all 25 pre-launch is a normalisation project, not a hardening item. |
| Four read-state mechanisms → one canonical | **C** | Table 6. App-heavy; v1.1. |
| Unified activity view over 9+ log tables | **C** | Read-only view is the right call (consolidation correctly rejected as ADR conflict); highest-value v1.1 item but not a launch gate — support staff can union manually at launch volume. |

---

## Irish Emission Factor Set — Firm Recommendation

**The audit is internally incoherent here: it rates E1 🔴 Critical and then defers the actual data to v1.1. I upgrade the minimal data load to A.**

Reasoning: (1) Scope 2 is kWh × grid factor; the Irish grid factor differs materially from the UK's, so a DEFRA-factored Dublin site produces a *silently wrong* headline number — the join succeeds, the arithmetic succeeds, the report is wrong. For a product whose entire proposition is defensible carbon numbers, shipping wrong numbers to a launch-market customer is worse than shipping a missing feature. (2) The seed data already contains two `.ie` companies — Ireland is not a roadmap market, it is in the launch cohort. (3) The remediation is bounded: SEAI/EPA publish the factors; v1.0 needs only the core set (grid electricity, natural gas, common liquid/gaseous fuels) for the current reporting year — a data load, not a modelling exercise, once the provenance columns (factor_set/country/unit/scope, already A) exist.

**Firm call:** provenance columns + UNIQUE = A; minimal current-year SEAI/EPA core factor load = A; full historical SEAI catalogue, CO2/CH4/N2O breakdowns, and FK renaming (`defra_factor_id` → `emission_factor_id`) = C. If the business instead chooses to launch UK-first, then IE signups must be gated at onboarding (a wrong answer is not an acceptable placeholder) — that is a product decision, and the schema work above is required either way.

---

## Strongest Challenges to the Audit Team

1. **"Format regexes belong in the database" (§7.1) — rejected wholesale.** VAT, postcode, Eircode, E.164, email and CH/CRO regex CHECKs all move to the API layer (validator libraries + checksums). The DB keeps exactly four validation shapes: IN-lists (`country`, `currency`, `timezone`), ranges (≥0, 0–100, 1–5, 0–1), presence (postcode-or-eircode on facilities), and uniqueness. The Eircode routing-key allowlist is the clearest proof of why: it is a living registry owned by a third party — freezing it into a CHECK constraint guarantees a future migration to admit a legitimate address.
2. **Typed invoice columns on `customer_documents` downgraded Critical → C.** The audit's own §8.2 argues (correctly) for promoting hot jsonb keys only after query logs prove the need — then §6.1 contradicts it by demanding six typed columns pre-launch. The ADR-protected jsonb already carries extraction output; `file_checksum` (A) delivers v1.0 duplicate detection. Typed columns in v1.0 buy sync complexity, not capability.
3. **`country_code` column rejected (D).** Diagnosis right, prescription wrong: constrain the existing `country` to ('GB','IE') rather than adding a second country column that must be synchronised with the first — the fix for a single-source-of-truth problem cannot be a second source.
4. **County lookup table and UK nation field rejected (D).** Neither has a single v1.0 consumer — no jurisdiction rule, report, or validation keys off county or nation. The county lookup also imports real edge-case debt (Dublin city vs county; the three Dublin administrative counties; Derry/Londonderry). Bank-holiday correctness, when it matters in v1.1, is better served by org-level holiday dates than by four-jurisdiction calendar modelling.
5. **SEAI/EPA data load upgraded v1.1 → A (minimal core set).** The audit cannot coherently call E1 Critical and then defer the data that makes it Critical. With `.ie` companies in the launch cohort, UK-factors-first means silently wrong Scope 2 for paying Irish customers — a credibility blocker, not a roadmap item. Scoped to the current-year core set, the load is days, not weeks.
6. **Sqm floor area: the audit contradicts itself (§6.2 v1.0 vs §12.2 #14 v1.1).** Resolved: add the two labelled nullable sqm columns in v1.0 (**B** — prevents Irish m² being mislabelled as sqft into SECR intensity ratios), defer conversion tooling and sqft deprecation (**C**). No typed-conversion machinery in v1.0.
7. **`emissions_logs.facility_id` downgraded Critical → B.** Site rollups are derivable via `asset_id → assets.facility_id`; the direct column is denormalisation with a backfill cost. The real v1.0 risk is *nullable* `asset_id` leaving emissions unattributed — an API-layer write rule, not a new column gated behind a backfill.
8. **`legal_entity_type`, `organizations.phone`, `users.phone` downgraded High/v1.0 → C.** None has a v1.0 consumer: CH prefixes are validated app-side, Stripe doesn't need an org phone, and SMS 2FA doesn't exist until v1.1 per the audit's own register. Adding columns "because cheap" is how schemas accumulate the dormant-field clutter the audit itself criticises in §7.4.
9. **`suppliers.sort_code` downgraded from the Critical framing (B).** CarbonTally stores supplier bank details but runs no payment runs; "a UK supplier cannot be paid correctly" overstates the blast radius. Add the column (cheap, prevents sort codes polluting `iban`), mask last-4 at API, defer encryption to v1.1.
10. **`pg_trgm` downgraded 🔴 → B, and the free-text-status programme scoped.** Trigram search is valuable and cheap but not a go/no-go gate at launch volumes; hard duplicate prevention comes from UNIQUE + normalised identifiers. The 25-table status normalisation is likewise a phased programme (hot queue/billing columns first), not a single v1.0 item — attempting it whole pre-launch is how hardening sprints become redesign projects.

---

*End of challenge brief. No SQL generated; no schema modified. Categories follow the client's A/B/C/D definitions; every D carries explicit reasoning above.*
