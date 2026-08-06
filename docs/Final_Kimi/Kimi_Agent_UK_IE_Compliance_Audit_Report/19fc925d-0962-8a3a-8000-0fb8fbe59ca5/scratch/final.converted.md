# CarbonTally v1.0 — Production Hardening Plan

*Implementation decision document — prepared 4 August 2026; UK & Ireland launch scope; ADRs treated as frozen; no SQL, no migrations, no schema redesign.*

## 1. Executive Summary

This document is CarbonTally's official Production Hardening Plan. It triages the junior audit team's Production Readiness Report into the four client categories — **A** (must implement before launch), **B** (strongly recommended for v1.0), **C** (defer to v1.1), **D** (reject) — and converts the result into an executable checklist, a phased migration order, a testing strategy and a go/no-go verdict, superseding the audit's severity ratings wherever the two disagree.

The headline triage result is a recalibration, not a rubber stamp. The audit declared 26 "v1.0 launch blockers", fourteen of them Critical. The architect's register confirms 25 launch-gated A items once verification gates and deduplication are accounted for (§3) — roughly eleven to thirteen true defect classes — while deferring 29 recommendations to v1.1 and beyond (§5) and rejecting 20 outright with reasoning (§6). Roughly half of what the audit asked for will not be built before launch, and the launched half surrenders no defect touching customer money, credentials, tenant isolation or a reported carbon number.

Five launch-gating themes are restated here as decisions. First, the **Irish facility write-path**: `facilities.eircode` is added, `facilities.postcode` relaxed, and a presence CHECK guarantees one or the other — without this, an Irish customer cannot register the site whose emissions the product measures. Second, **jurisdiction IN-lists**: `country` constrained to ('GB','IE') and the six `currency` columns plus `system_settings.default_currency` to ('GBP','EUR'), because every jurisdiction rule, aggregation and Stripe reconciliation keys off them. Third, **factor provenance plus the minimal SEAI/EPA core load**: provenance columns and a uniqueness rule on `defra_conversion_factors`, then the current-year Irish grid, gas and common-fuels set — a DEFRA-factored Dublin site reports silently wrong Scope 2, and wrong numbers are worse than a missing feature. Fourth, **security-of-secrets and tenancy verification**: hashing of `consultant_profiles.api_key`, `password_reset_tokens.token` and `user_invitations.token`, the reset-token UNIQUE correction, the `users.password_hash` ownership decision, and evidence — not assumption — that the RLS matrix and nullable-`organization_id` remediation hold. Fifth, **the erasure procedure before the first DSAR**: an anonymise-in-place runbook tested on staging, because hard delete is structurally impossible against ~40 foreign keys and the statutory clock starts on day one.

Equally deliberate is what this plan does **not** do. Country-conditional regex CHECKs are rejected: presentation formats belong at the API layer, and the Eircode routing-key allowlist is a living registry that must not be frozen into a constraint (§6, D1). Monthly RANGE partitioning is rejected: low-seven-figure row counts after year one are trivially served by B-trees plus retention deletes (§6, D4). The audit hash-chain is rejected as security theatre whose verifier is its own writer; privilege revocation and PITR tell the honest storey (§6, D5). And the blanket "index every FK" programme is rejected at roughly 3× over-scope in favour of 15–18 targeted indexes (§6, D2/D19).

The effort shape is favourable: most A items are Small, Low-risk, additive changes — nullable columns, IN-list CHECKs, a data load, one configuration check — batched into five migration batches (six deployable migrations) plus two verification gates — Gate 1 (migration-file inspection) and Gate 4 (RLS matrix) (§8–§9). The verdict is a **conditional GO**: launch proceeds once every row of the §7 checklist is evidenced, with no partial credit (full reasoning in §10).



*Sections 2–6 triage the Production Readiness Report against the two challenge briefs. Categories: **A** = must implement before launch · **B** = strongly recommended for v1.0 · **C** = defer to v1.1 · **D** = reject. Phases per the client roadmap: P1 critical fixes · P2 data integrity · P3 performance · P4 validation · P5 compliance.*

## 2. Overall Assessment of the Production Readiness Report

The audit report is technically thorough and directionally correct on the four structural blockers that genuinely gate a UK/IE launch: the `facilities` Eircode blocker (§5.1, findings B1/D5), the unconstrained `country` and `currency` columns every jurisdiction rule keys off (§4, findings A5/A6; §7.1), the UK-only emission factor model (§5.4, finding E1; §6.1), and the unit-less `emissions_logs.raw_quantity` (§6.1, finding A13). Its architectural restraint is also sound: §13 correctly refuses queue consolidation, log consolidation and UUID-to-bigint churn on ADR grounds. Where the report fails is calibration, and the failures are systematic.

First, severity inflation. Section 12.1 declares 26 "v1.0 launch blockers," fourteen 🔴 Critical — a list containing URL-format CHECKs, 1–5 rating CHECKs, `numeric(12,2)` money precision and timezone IN-lists alongside the Ireland blocker and the RLS matrix. A register that cannot distinguish "an Irish customer cannot insert a facility" from "a feedback rating is unconstrained" trains its audience to disbelieve the word *blocker*, and a disbelieved blocker list is worse than none. My register contains roughly eleven to thirteen true A items, presented in §3 as 25 rows once verification gates and deduplication are accounted for.

Second, the report over-locates validation in the database. Section 7.1 states that "format regexes belong in the database," and §12.1 item 4 prescribes country-conditional regex CHECKs for VAT, CH/CRO company numbers, postcodes and Eircodes. This is rejected under the client's layering rule: the database guarantees integrity — uniqueness, ranges, presence, simple IN-lists — while presentation formats live at the API layer with libphonenumber and validator libraries. The Eircode routing-key allowlist proves why: a living registry owned by a third party, frozen into a CHECK, guarantees a future migration to admit a legitimate address. The database keeps exactly four validation shapes.

Third, the index programme is over-scoped roughly 3×. Finding D3-A1 ("index every FK across ~90 tables") implies a 60-plus-index programme spraying write-amplifying indexes onto static reference tables (`units`, `glossary`, `roles`), marketing tables being purged at launch, and FKs that are never query entry points. The correct baseline is 15–18 targeted indexes (§4, item 4). Fourth, the report reaches for infrastructure a ~50-customer pre-revenue SaaS does not need: monthly RANGE partitioning rated 🔴 (§12.2 item 16), a hash-chain whose verifier is the same principal as its writer (§9.4, finding B7), and per-user 2FA/lockout columns duplicating Supabase Auth's platform responsibility (§9.3, finding B4).

Two considerations reframe the scoring. The evidence caveat — buried at §2 and §14 — records that the schema dump showed no indexes, RLS policies, foreign keys or CHECK definitions. This plan elevates that caveat to **action zero**: inspect the Supabase migration files before any remediation is scored or scheduled. If migrations contain the index layer and policy matrix, the Performance (25) and Security (30) scores rate an evidence pack, not a database, and several §8/§9 findings collapse to verification. The structural findings stand regardless. And volume realism should discipline every infrastructure call: ~50 launch customers at a few hundred documents a month puts the pipeline tables at low six figures and the busiest log tables at low seven after year one. B-trees plus retention deletes handle that comfortably; nothing here justifies partitioning, hash-chains or GIN blankets in v1.x.

| Audit claim (report ref.) | Architect's verdict |
|---|---|
| 26 v1.0 launch blockers, 14 🔴 (§12.1) | ~11–13 true A items; remainder re-triaged B/C/D (§3, §4) |
| 60+ index programme; "index every FK" (D3-A1; §12.1 item 10) | 15–18 targeted indexes on observed v1.0 query paths (deferred §5, rejected §6) |
| Format regex CHECK matrix (§7.1–7.2; §12.1 item 4) | Rejected; app-layer validators + MOD97 checksum; DB keeps four rule shapes (§4, item 1) |
| Monthly RANGE partitioning 🔴 (§8.3 A5; §12.2 item 16) | **D** — revisit trigger documented: >10–20M rows per table or vacuum pressure |
| Hash-chain tamper-evidence (§9.4 B7) | **D** — security theatre; privilege revocation + dropped `updated_at` + PITR is the honest storey |
| Retention jobs 🔴 v1.0 (§12.1 item 16) | **B** — nothing ages out on empty tables for months; erasure procedure promoted to A (§3) |
| Typed invoice columns Critical (§6.1; §12.1 item 8) | **C** — `file_checksum` + ADR-protected jsonb covers v1.0 duplicate detection (§4, item 2) |
| Trigram/full-text search 🔴 (§10.3.1; D3-C1) | **B** — supplier/org name only; message FTS deferred with its uncommitted screen (§4, item 5) |

The pattern is consistent: the audit's diagnosis is almost always right and its prescription wrong in degree — correct defect, inflated severity, oversized remedy. Every downgrade is argued in §4 with its blast radius stated, so the client can see triage being exercised rather than corners cut. The net effect is material: the sprint shrinks from a 26-item programme of record to five migration batches (six deployable migrations) plus two verification gates, without surrendering any defect touching customer money, credentials, tenant isolation or a reported carbon number. Sections 5 and 6 carry the deferred and rejected registers; nothing is silently dropped.

## 3. Recommendations Accepted (Category A — Launch Blockers)

Consolidated from both challenge briefs, deduplicated and sequenced by phase. Verification gates are listed as launch blockers deliberately: a multi-tenant financial product cannot go live on unverified isolation, whatever the migration files contain.

| # | Item | Affected `table.column` | Why it is a blocker | Phase |
|---|---|---|---|---|
| 1 | Verify the full RLS policy matrix; enforce service-role discipline (no service key client-side; workers filter `organization_id` in code) | `organization_id` passim; `consultant_firm_members.client_access` | One cross-tenant sighting is a reportable ICO/DPC incident; unverifiable in the dump (§9.1 B1; §12.1 item 11; perf/sec Table 2). | P1 |
| 2 | Resolve nullable `organization_id` on hot tenant tables — backfill, then NOT NULL | `conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications` (`.organization_id`) | A NULL-org row falls outside every tenant-equality policy: invisible-to-all or visible-through-exception. Cheap pre-launch, painful after (§9.1 B1). | P1 |
| 3 | Hash long-lived credentials (SHA-256 + lookup prefix, rotation columns) | `consultant_profiles.api_key`, `password_reset_tokens.token`, `user_invitations.token` | Plaintext credentials defeat RLS: any backup, log or service-role context yields live keys (§9.2 B2; §12.1 item 13). | P1 |
| 4 | Drop UNIQUE on `password_reset_tokens.user_id`; keep UNIQUE on `token`; latest-valid-wins | `password_reset_tokens.user_id`, `.token` | Unauthenticated reset-DoS: cycling requests continuously invalidates a victim's genuine token. Constraint correction, not redesign (§9.3 B3; §12.1 item 15). | P1 |
| 5 | Decide `users.password_hash` ownership explicitly; if Supabase Auth is IdP, dead-column it and never write | `users.password_hash` | A dormant credential column will eventually be written, creating two drifting credential stores; free to decide now, embarrassing to retrofit (§9.3 B5; §12.1 item 26). | P1 |
| 6 | Verify every FK and ON DELETE action; RESTRICT on financial/audit tables where dangerous CASCADEs found | passim (e.g. `emissions_logs.asset_id`, `report_versions.report_id`) | The product cannot launch without *knowing* its delete behaviour; verification is the blocker, remediation only where inspection proves danger (§12.1 item 12; perf/sec Table 4). | P1 → P2 |
| 7 | Seed cleanup: remove out-of-market `.de`/`.fr`/`.fi`/`.ai` users; add IE org + IE facility fixtures (Eircode, EUR, IE factor) | seed block; `facilities.eircode`, `.country` | Never ship out-of-market PII-flavoured seeds; the missing Irish fixture is the regression guard that let B1 survive (§5.5 G1/G5; §12.1 item 18). | P1 |
| 8 | Add tenant lifecycle columns | `organizations.is_active`, `organizations.archived_at` | Without a suspend path, the only lever for a churned customer is deleting audit evidence (§3.3, §6.1; §12.1 item 7). | P1 |
| 9 | Relax NOT NULL on `customer_documents.asset_id` | `customer_documents.asset_id` | Supplier invoices have no asset; the constraint forces fake assets into the emissions hierarchy — manufactured corruption on the core entity (perf/sec Table 4). | P1 |
| 10 | Fix the facilities blocker: add nullable `eircode`, relax `postcode` NOT NULL, add presence CHECK (postcode OR eircode present) | `facilities.eircode`, `facilities.postcode` | The single launch blocker: Ireland has no postcodes, so an Irish customer cannot register the site whose emissions the product measures (§5.1 B1/D5; §12.1 item 1; validation Tables 1–2). | P1 |
| 11 | Constrain `country` to the launch markets | `organizations.country`, `facilities.country`, `suppliers.country`, `consultant_profiles.country` | CHECK IN ('GB','IE'); machine-readable country is the key every jurisdiction rule reads (§7.1 A5; §12.1 item 2). | P1 |
| 12 | Constrain currency to the launch currencies | six `currency` columns + `system_settings.default_currency` | CHECK IN ('GBP','EUR'); every aggregation, Stripe reconciliation and spend-based calculation keys off it (§7.2; §12.1 item 3). | P1 |
| 13 | Add the missing billing currency | `consultant_billing.currency` | The only billing table with undenominated prices in a two-currency launch (§6.1; §12.1 item 9). | P2 |
| 14 | Add factor provenance columns; backfill 'DEFRA-DESNZ'; UNIQUE `(reporting_year, activity_type)` | `defra_conversion_factors.unit`, `.scope`, `.factor_source`/`.factor_set`, `.country` | `co2e_multiplier` never states kg CO2e per *what*; duplicate rows silently double-count the product's core number (§5.4 E1, C10; §12.1 item 5). | P2 |
| 15 | Load the minimal current-year SEAI/EPA core factor set (grid electricity, gas, common fuels) | `defra_conversion_factors.factor_set`, `.country` (data load) | The architect's upgrade (§4, item 10): a DEFRA-factored Dublin site yields silently wrong Scope 2; wrong numbers are worse than a missing feature. | P2 |
| 16 | Add unit and scope to emission entries | `emissions_logs.unit` (FK to `units.code`), `emissions_logs.scope` | Unit-less quantities make SECR kWh totals an inference through the factor join — unauditable numbers (§6.1 A13; §12.1 item 6). | P2 |
| 17 | Range CHECKs on all emission values ≥ 0 | `emissions_logs.raw_quantity`, `.calculated_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*`, `supplier_categories.default_emission_factor` | One negative `calculated_kg_co2e` silently corrupts every SECR total (§7.2; validation Table 1). | P2 |
| 18 | Widen `file_size` to int8; add size CHECKs | `file_attachments.file_size` (and peers) | int4 overflows at 2 GB — reachable by invoice bundles — failing the upload at the customer's highest-value moment; near-free pre-launch, a table rewrite after (§8.4 A6; §12.1 item 23). | P2 |
| 19 | Add the content-hash column for duplicate-upload detection | `customer_documents.file_checksum` (SHA-256) | Deterministic duplicate detection on the primary pipeline entity; near-free on an empty table. Unique enforcement defers to v1.1 (§10.3.4; validation Table 2). | P2 |
| 20 | Add the uniqueness set: memberships, consultant links, billing months, report versions, supplier identifier partials | `organization_members(organization_id, user_id)`; `consultant_clients(consultant_id, organization_id)`; `usage_tracking(organization_id, usage_month)`; `report_versions(report_id, version_number)`; `suppliers(organization_id, vat_number)`/`(organization_id, company_number)` partial WHERE NOT NULL | Duplicates corrupt RLS semantics, split billing allowances, make `is_current` ambiguous, and are amplified by `ai_mapped_supplier_id` into emissions data (§3.3, §8.1 A9; perf/sec Tables 1, 4). | P2 |
| 21 | Block writes to `pending_invites`; `user_invitations` is canonical | `pending_invites.*` | The weaker table — no token, expiry or status — is a live security downgrade still writable (§3.2, §3.5; validation Table 6). | P2 |
| 22 | Anonymise-in-place erasure procedure (hash `users.email`, "Deleted User", keep UUID), tested on staging | `users.email` and ~40 referencing FK columns | Hard delete is structurally impossible; a DSAR can arrive on day one with a one-month clock, and an untested erasure script is how companies end up in front of the ICO (§9.4 D2; §12.1 item 17). Launch-gated. | P5 |
| 23 | Residency verification: Supabase region UK-London or eu-west-1; backup location matches | `system_settings.backup_storage_location` (configuration check) | One free check on which every enterprise questionnaire's residency claim depends (§9.4 D6; perf/sec Table 3). | P5 |
| 24 | Targeted NOT NULL + DEFAULT on hot booleans/timestamps — backfill, then constrain | `organizations.is_active`-style flags and processing timestamps on the hot pipeline tables (`processing_queue`, `document_processing_queue`, `customer_documents`, `emissions_logs`) | A NULL on a hot-path flag or processing timestamp is an ambiguous state workers and suspend logic silently misread; the broad ~80-column sweep stays C10, the hot subset gates launch (§8.4 A7/A11; §4 item 8; §5 C10). | P2 |
| 25 | CHECK value lists on queue/billing/role status columns | `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status` | Status typos on queue and billing columns become silent states workers and limit-checks miss; the D8 alternative to enums, scoped per §4 item 8 — the remaining ~20 free-text statuses stay C3 (§10.3.3; §12.1 item 21). | P2 |

The register divides into six classes, and the cost of omission differs sharply by class. Without the **tenancy class** (items 1–2), one forgotten `organization_id` on an insert path places a row outside every policy — no attacker required, only time. Without the **secrets class** (items 3–5), the first escaped backup or verbose log hands over live credentials, and the reset-token UNIQUE lets any unauthenticated caller deny a victim recovery indefinitely. Without the **integrity class** (items 6, 9, 20–21, 24–25), duplicates, fake assets, ambiguous NULL flags and unconstrained statuses enter via the AI mapping and queue paths and land in `emissions_logs` as part of a customer's reported figures. Without the **numbers class** (items 10–17), the product ships silently wrong Scope 2 values to Irish launch customers and unit-less quantities to everyone — the defect class where nothing fails loudly and the report is simply wrong. Without the **upload-integrity class** (items 18–19), the first 2 GB bundle fails publicly and duplicate invoices are undetectable. Without the **compliance class** (items 7, 22–23), the first DSAR triggers an untested destructive script against a live tenant. Every class fails invisibly at demo scale and publicly in production; that asymmetry, not effort, is what makes them launch gates.

## 4. Recommendations Modified (Accepted with Changes)

The defects in this register are real; the prescriptions needed correction in scope, layer or timing. Each is accepted in principle and modified in execution.

| # | Original audit recommendation | Modification | Reasoning |
|---|---|---|---|
| 1 | Country-conditional format regex CHECKs in the database for VAT, postcode, Eircode, phone, email and CH/CRO numbers (§7.1–7.2; §12.1 items 4, 24) | All format validation moves to the API layer: libphonenumber (store E.164), validator libraries plus HMRC MOD97 checksum, GIR-valid postcode and Eircode shape checks with normalisation at write. DB keeps only IN-lists, ranges, presence, uniqueness. | The client's layering rule places presentation formats in the application. DB regexes reject valid edge cases and rot as registries change — the Eircode routing-key allowlist is third-party-owned. The DB guarantees uniqueness of the *normalised* value, not its shape. |
| 2 | Six typed invoice columns on `customer_documents`, rated Critical (§6.1; §12.1 item 8) | Deferred to **C** (v1.1). v1.0 duplicate detection comes from `customer_documents.file_checksum` (§3 item 19); the ADR-protected `extracted_data` jsonb already carries the output. Promote hot keys in v1.1 against query logs. | The audit's own §8.2 argues for promoting jsonb keys only after query logs prove the need, then §6.1 contradicts it. Typed columns in v1.0 buy sync complexity, not capability. |
| 3 | Add a parallel ISO `country_code` column (finding D3; §6.4) | **Rejected.** Constrain the existing `country` columns instead (§3 item 11). | Diagnosis right, prescription wrong: the fix for a single-source-of-truth problem cannot be a second source of truth kept in sync with the first. |
| 4 | Index baseline: FK indexes on ~30 tenant keys plus blanket coverage, ~60 implied (§8.1 A1/A2; §12.1 item 10) | Scoped to 15–18 targeted indexes: tenant composites on `customer_documents(organization_id, created_at DESC)`, `emissions_logs(organization_id, start_date)`, `suppliers`/`facilities(organization_id)`; the UNIQUE-backed membership/billing/version paths; the queue-claim partial on `document_processing_queue(status, created_at)`; `messages(conversation_id, created_at)`; the unread-notifications partial; `conversation_participants(conversation_id, user_id)`; the `client_access` GIN. Deferred set §5; rejected set §6. | Index what v1.0 screens and workers actually query. Static lookup tables are optimally seq-scanned; marketing tables are being purged; every unnecessary index is write cost on the pipeline's hot path. |
| 5 | Trigram/full-text search programme rated 🔴 (§10.3.1; D3-C1) | Downgraded to **B**, scoped to `suppliers.name`/`vat_number` and `organizations.name` (autocomplete + "did you mean?" prompts). Message FTS and file-name trigram deferred to C with their uncommitted screens. | An autocomplete box is not a go/no-go gate at launch volumes; hard duplicate prevention rests on UNIQUE + normalised identifiers (§3 item 20). A search blocker must block a screen, not an aspiration. |
| 6 | `emissions_logs.facility_id` rated Critical (§6.1 A13; §12.1 item 6) | Downgraded to **B**: nullable column plus dual-write in v1.0 if trivial; do not gate launch on the backfill. The real control is an API write rule against nullable `asset_id`. | Site rollups are derivable via `asset_id → assets.facility_id`; the direct column is denormalisation with a backfill cost. Unattributable emissions are the genuine risk, and that is a write-path rule, not a schema gate. |
| 7 | Soft-delete on `customer_documents` bundled into a Critical item (§12.1 item 8) | Kept at **B**, not A: `deleted_at` plus RLS/query filters early in v1.0. | Right thing while the table is young, but every document read path changes (app impact medium), and nothing at launch volume is unrecoverable via backups. |
| 8 | CHECK value lists on free-text `status` across ~25 tables (§10.3.3; §12.1 item 21) | Scoped to queue/billing/role columns first — `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status` (A, P2). The remaining ~20 are C. | Status typos on queue and billing columns become silent states workers and limit-checks miss. All 25 pre-launch is a normalisation project, not a hardening item. |
| 9 | Square-metre floor area: §6.2 says v1.0, §12.2 item 14 says v1.1 — contradictory | Resolved: the two labelled nullable columns `organization_metadata.total_floor_area_sqm`/`.occupied_floor_area_sqm` are **B**; conversion tooling and sqft deprecation are **C**. | Irish customers will mislabel m² as sqft into SECR intensity ratios; two labelled columns prevent that without any conversion machinery in v1.0. |
| 10 | SEAI/EPA Irish factor load rated 🔴 Critical yet deferred to v1.1 (§5.4 E1; §12.2 item 2) | Upgraded to **A** with minimal-core scope: grid electricity, natural gas, common liquid/gaseous fuels, current reporting year (§3 item 15). Full catalogue stays C. Alternative: a UK-only launch gate on IE signups — a product decision. | A finding cannot be Critical while the data making it Critical is deferred. Irish grid intensity differs materially from the UK's; the join succeeds while the report is wrong. With `.ie` companies in the launch cohort, UK-factors-first ships silently wrong Scope 2 to paying customers — a credibility blocker, and only days of work once provenance columns exist. |
| 11 | Per-user 2FA columns (`totp_secret`, `two_factor_enabled`, `backup_codes`) and lockout columns (§9.3 B4; §12.1 item 26; §12.2 item 6) | Replaced by the `users.password_hash` ownership decision (§3 item 5) plus honest marketing of the global flags. If Supabase Auth is IdP, MFA/lockout are platform responsibilities; per-user columns are **C**, shipped only with the feature. | Parallel auth state in `users` contradicts the ADR direction and duplicates controls Supabase Auth provides. The v1.0 obligation is to stop advertising `two_factor_required` as enforced in enterprise questionnaires until it is. |
| 12 | Retention schedule + pg_cron jobs rated 🔴 v1.0; erasure procedure sharing the rating (§8.3 D1, §9.4 D1/D2; §12.1 items 16–17) | Priorities inverted: retention jobs **B** (schedule designed in P1, jobs land in the first weeks post-launch); the anonymise-in-place erasure procedure promoted to **A**, launch-gated at P5 (§3 item 22). | On empty tables nothing ages out for months, so a cron job cannot be a day-one blocker. An erasure request can arrive on day one against a `users` table pinned by ~40 FKs with a one-month statutory clock — the tested procedure is the urgent artefact, not the job. |

The twelve modifications share one discipline: match the remedy to the layer, the scale and the moment. Items 1–3 enforce the layering rule — integrity in the database, formats in the application, never two columns answering the same question. Items 4–8 apply volume realism: at low-six-figure pipeline tables, targeted B-trees, a scoped trigram pair and phased status CHECKs deliver every real benefit of the audit's larger programmes without their write amplification or migration risk. Items 9–12 correct sequencing errors — internal contradictions (sqm, SEAI/EPA), a platform-responsibility confusion (2FA/lockout) and an inverted compliance urgency (retention versus erasure). None weakens a control; each moves effort from ceremony to the defect that can actually hurt a customer. Where disagreement survives these adjustments — partitioning, hash-chains, county lookups, `country_code` — the rejections are recorded with reasoning in §6, and the deferred remainder is scheduled in §5.


## 5. Recommendations Deferred (Category C — v1.1 and Beyond)

Category C is not a dustbin: each item is a sound recommendation whose cost, scope or dependencies make it wrong for a launch sprint. The discipline applied is the one the audit states in §8.2 then abandons — promote structures when query logs, committed screens or scoped integrations prove the need. Placement notes to avoid double-booking v1.0 items: `confidence_score` type/scale standardisation, the `timezone` IN-list, the date-pair CHECKs and the percentage-scale 0–100 CHECKs are all **B** (validation brief, Table 1), in the v1.0 register; the country-conditional app-layer validations (VAT, CRO/CH number, postcode, Eircode, phone, email) are likewise **B** at the API layer — only their database-regex incarnations are rejected (Section 6).

### 5.1 Deferred register — validation and data integrity (v1.1)

| # | Item | Why good but not v1.0 | Trigger or version |
|---|---|---|---|
| C1 | Typed invoice columns on `customer_documents` (`document_number`, `document_date`, `currency`, `net_amount`, `vat_amount`, `gross_amount`) promoted from `extracted_data` jsonb (audit §12.1 item 8) | ADR-protected jsonb already carries pipeline output; typed columns duplicate it and force sync logic | v1.1, once query logs prove the hot keys — the audit's own §8.2 criterion |
| C2 | UNIQUE enforcement on `file_checksum` (audit §10.3.4) | Column ships in v1.0; hard uniqueness before duplicate-handling UX exists would reject legitimate re-uploads | v1.1, with duplicate-resolution UX |
| C3 | CHECK value lists on the remaining ~20 free-text `status` columns (audit §12.1 item 21) | Right mechanism, but all-25-at-once is a normalisation project; queue/billing/role lands in v1.0 | v1.1, phased by screen usage |
| C4 | Standardise `ip_address` on `inet` across ~8–10 log tables (audit §12.2 item 17) | Hygiene value for retention/PII jobs; nothing reads these columns in v1.0 query paths | v1.1, with the retention work |
| C5 | Identity/contact consolidation: `staff_profiles.email` deduped against `users.email`; `suppliers.contact_*` canonical over `primary_*`; `organization_metadata.primary_contact_*` demoted for `organizations.*` (audit §12.2 item 9) | Drift is real but low-stakes; writes stop by convention in v1.0 | v1.1, with contacts review (C14) |
| C6 | Canonical state: `conversation_participants.last_read_at` for read state (derive `messages.read_by`, `conversations.unread_count`); `customer_verifications` for approval (audit §12.2 item 8) | App-heavy derivation across four read mechanisms and five approval surfaces; blocks nothing | v1.1 enforcement; v1.0 documentation |
| C7 | Unified read-only audit/activity view over the 9+ log tables (audit §12.2 item 1) | Right idea (consolidation is rejected in Section 6) but no auditor or support volume at launch | v1.1 |
| C8 | County normalisation via the address-verification loop; `county` stays free text (audit §12.2 item 11) | Nothing computes from `county` in v1.0; normalisation arrives free with the verification loop | v1.1, rides C12 |
| C9 | Constrain dormant region columns (`tax_region`, `vat_region`, `registration_region`, `carbon_tax_region`) (audit §7.2) | CHECKs on columns serving dormant features are ceremony | At feature activation (v1.1+) |
| C10 | Counter-drift recompute jobs (`usage_tracking.*_used`, `conversations.unread_count`) and NOT NULL DEFAULT sweep on ~80 remaining booleans/timestamps (audit §8.4 findings A7/A11/C7) | v1.0 CHECKs (≥0, `used ≤ limit`) bound damage but do not fix drift — that is worker logic | v1.1 sweep |
| C11 | Floor-area conversion tooling and sqft dormancy; `sic_code` 5-digit UI hint (audit §12.2 item 14, finding A4) | Labelled sqm columns land in v1.0 (B); SIC is informational, nothing computes from it | v1.1 |
| C30 | Bank-details encryption at rest beyond masking — vault/KMS envelope encryption for the `suppliers` bank columns | Last-4 API masking (B) covers the display risk; envelope encryption needs a vault-versus-KMS provider decision that must not be rushed inside a launch sprint | v1.1, pending provider decision |

**Interpretation.** Each item converts a convention agreed for v1.0 into enforced structure once the application stops moving. The hazard the audit underweights is sequencing: C1's typed columns before query logs freeze the wrong hot keys; C3's twenty CHECKs pre-launch turn a hardening sprint into a redesign; C2's checksum uniqueness before the duplicate UX exists punishes customers for the pipeline's own re-processing. Deferral here is justified by dependency and evidence, never by effort: none of these items is low-value; each is correctly timed rather than refused.

### 5.2 Deferred register — features requiring schema (v1.1)

| # | Item | Why good but not v1.0 | Trigger or version |
|---|---|---|---|
| C12 | `address_validation_status`/`formatted_address` plus the PAF/Loqate/Eircode-finder verification loop; `post_town`/`dependent_locality` fidelity (audit §12.2 item 3, finding D1-D4) | Explicitly C-class: status/cache columns are inert without the verification feature behind them | v1.1, with the feature |
| C13 | Platform `invoices` table with sequential numbers and stored UK/IE VAT evidence (audit §12.2 item 5, finding D3-E2) | Stripe-hosted invoices plus Stripe Tax cover UK 20%/IE 23% at v1.0 scale; a local table now creates a second source of truth | v1.1; precondition: VAT evidence stored locally, not delegated to Stripe |
| C14 | `contacts` table and `support_tickets` table (audit §6.3; §12.3 items 2, 7) | Inline contact columns serve single-contact onboarding; `user_feedback` suffices as tickets-v1. Tables encode workflow commitments — freezing shapes before the workflow is real | v1.1 planning; build with portal work / ticket volume |
| C15 | SEAI/EPA full historical catalogue, CO2/CH4/N2O breakdowns, FK rename `defra_factor_id` → `emission_factor_id` (audit §12.2 item 2) | The minimal current-year core load is upgraded to A; the full catalogue and gas-species splits are breadth, not correctness | v1.1 |
| C16 | Reporting-period columns replacing int4 `reporting_year`; `regulatory_framework`; `organizations.legal_entity_type` and SECR qualification metadata (audit §12.2 item 18) | An integer year cannot name a UK financial year; SECR is not a day-one flow; no v1.0 process consumes entity type | v1.1, before the first SECR season |
| C17 | `users.phone` / `users.timezone`; `organizations.phone` / `.mobile` (audit §6.2) | Per-user phone matters only when 2FA ships; Stripe needs no org phone — columns ship *with* the features | v1.1, with 2FA and invoicing |
| C18 | MPAN/MPRN bill-to-facility matching logic; `site_manager_name`/`phone` (audit §6.2) | The `facilities.meter_mpan_mprn` column is B (cheap now); the matching itself is application work | v1.1 app work |
| C19 | Org-level holiday dates (audit §12.2 item 13, modified; finding D1-A14) | Per-org holiday lists fix SLA-boundary maths with less machinery than four-jurisdiction modelling (rejected in Section 6) | v1.1, with business-calendar work |
| C20 | Per-user notification preferences — channel opt-in/out (audit §12.2 item 7, finding D2-F5) | Preferences without per-channel delivery logic are inert columns | v1.1 |
| C21 | Realtime Presence migration for `typing_status`/`user_presence` (audit §8.4 finding A8) | Keystroke/heartbeat upserts are a mismatch the platform absorbs free; interim UNIQUE + purge (B) contains the risk | v1.1 |
| C22 | `consultant_clients` identity fields (`client_company_number`, VAT, country), `trading_name`, `credit_limit`, `purchase_order_required`; `waitlist.country`; Xero/QBO columns (`external_id`, `integration_source`, `last_synced_at`, `suppliers.account_reference`) (audit §11.1.1) | None launch-blocking — they earn their keep only once invoicing and sync exist; `external_id` has no semantics pre-contract | v1.1 batch for identity fields; Xero/QBO columns when the integration is scoped (may slip to v2.0) |
| C23 | Evidence-gated indexes: GIN on `customer_documents.extracted_data`; FTS on `messages.content`; staff/ops composites (`staff_daily_performance(staff_id, date)`, `sla_compliance(queue_id)`); non-entry-point FK indexes; extra `pg_trgm` (audit §8.1/§8.2, §12.2 item 15) | Once C1 promotes hot keys, invoice lookup moves to a B-tree; no message-search screen is committed; back-office dashboards are trivial at launch scale | v1.1, against observed query logs or committed screens |
| C24 | Erasure self-serve UI, PII-inventory enforcement jobs, consent/PECR capture fields (audit §12.2 item 20) | The *tested anonymise-in-place procedure* is A — a DSAR can arrive on day one; self-serve layers onto it. v1.0 onboarding is covered by contract/legitimate interest | v1.1 |

**Interpretation.** Every row fails the same honest test: name the screen, worker or contract that consumes it on launch day — C13/C14 on workflow, C22 on semantics, C23 on UI, C17 on feature dependency. Two items carry preconditions rather than dates (C13's local VAT evidence; C22's scoped sync contract), because building early is corrosive: speculative columns acquire improvised meanings the real feature must unpick. The SEAI/EPA split (C15) marks the boundary with the v1.0 section: provenance columns, the UNIQUE and the minimal Irish core load are A-class; only historical depth waits.

### 5.3 Deferred register — Future (v2.0+)

| # | Item | Why good but not v1.0/v1.1 | Trigger or version |
|---|---|---|---|
| C25 | Queue rationalisation — merge `processing_queue`, `manual_review_queue`, `document_processing_queue` (audit §12.3 item 1) | The multi-phase pipeline is an approved ADR; the v1.x remedy is the data-flow contract and cross-FKs, not a redesign | v2.0+, only if ADRs are revisited |
| C26 | `api_keys` (scopes, expiry, revocation) and `webhook_events` tables (audit §12.3 item 4, finding D3-E3) | `system_settings.api_rate_limit` advertising rate limits is no commitment to build an API product; there is no integration customer | v2.0, first integration customer exists |
| C27 | Entra ID SSO columns (`users.sso_provider`, `users.sso_subject`) (audit §12.3 item 5, finding D3-E5) | Correctly deferred by the audit; trivial to add when the first enterprise procurement demands it | v2.0, first enterprise SSO requirement |
| C28 | Supplier-portal identity model (`suppliers.portal_user_id`, `users.user_type`) (audit §12.3 item 3, finding D3-E4) | Suppliers are pure data rows; half-built portal columns are the structural drift the ADRs guard against | v2.0, with the contacts question (C14) |
| C29 | EU activation of dormant ESRS/CSRD/NACE fields (`organizations.esrs_enabled`, `organizations.nace_code`, `activity_categories.esrs_e1_category`) (audit §12.3 item 6, finding D1-B10) | EU scope is Future by definition — but Ireland has transposed CSRD and uses NACE Rev.2, so large Irish customers may activate early | v2.0+ generally; **v1.1 watch item** for enterprise IE signings |

**Interpretation.** The v2.0+ shelf is short on purpose: items whose precondition is an architectural decision (C25), a customer who does not yet exist (C26, C28), or a market the launch does not serve (C29). Each carries a named trigger so planning reviews test the trigger rather than re-litigating the idea. The Ireland CSRD watch item is the one piece of EU scaffolding with a pulse: `esrs_enabled` and `nace_code` are dormant-but-early-activation candidates, reviewed at each v1.1 planning cycle — and, per Section 6, never deleted.

## 6. Recommendations Rejected (Category D — With Reasoning)

This section is where the plan earns its keep. The audit was thorough but not always discriminating; each rejection is argued on its merits and names the cheaper control that ships — several rejected items diagnosed a real defect and prescribed the wrong remedy.

| # | Rejected recommendation (audit source) | Category of rejection | Reasoning | What to do instead |
|---|---|---|---|---|
| D1 | Regex-heavy CHECK constraints for VAT, postcode, Eircode, E.164 phone, email, CH/CRO company numbers (audit §7.1 "format regexes belong in the database"; §12.1 item 4; findings D1-A1–A3, D1-B3–B6) | ADR conflict (layering rule); over-engineering | Formats are app-layer concerns: DB regexes reject valid edge cases, cannot express per-country rules, and rot. The Eircode routing-key allowlist is a living registry — the worst thing to freeze into a CHECK | App-layer validation (B): validator libraries, MOD97, libphonenumber, normalisation. DB keeps IN-lists, ranges, presence, uniqueness |
| D2 | Blanket "index every FK" programme — ~60 indexes (audit §8.1 finding D3-A1 as written; §12.1 item 10) | Over-engineering | ~3× over-scoped: write-amplifying indexes on static reference tables, marketing tables purged at launch, and never-queried FKs. The principle is A; the blanket is not | 15–18 targeted indexes (tenant composites, queue partials, unread-notification partial, membership uniques), one CONCURRENT batch |
| D3 | Blanket GIN on all jsonb (`audit_logs.old_data`/`new_data`, `activity_logs.metadata`, queue payloads) (audit §8.2, generalised) | Over-engineering | GIN rewrites entries on every jsonb update — write amplification on the hottest tables for zero observed key-filter queries | Sole exception: `consultant_firm_members.client_access` array GIN — a security predicate the ADR-locked array forces into RLS (rest evidence-gated, C23) |
| D4 | Monthly RANGE partitioning of 9+ log tables (audit §12.2 item 16, finding D3-A5 — rated 🔴) | Premature optimisation | Low seven figures after year one — trivially served by a `created_at` index plus retention DELETEs; partitioning multiplies operational surface for zero benefit. Cheap-to-do ≠ worth-doing | Retention + pg_cron (B); documented revisit trigger: >10–20M rows/table or vacuum pressure |
| D5 | Audit hash-chain / cryptographic tamper-evidence on `audit_trail` (audit §12.2 item 19, finding D3-B7, hash-chain clause) | Low value (security theatre) | Verifier = writer = same principal (the DBA/service role could rewrite the chain): no evidentiary value to an external auditor. Real tamper-evidence needs external anchoring — v2.x | Revoke UPDATE/DELETE, drop `updated_at` from append-only logs, PITR backups — the honest storey (B) |
| D6 | Consolidation of the 9+ audit/activity log tables (audit §3.2, §13) | ADR conflict | Per-domain log design is a frozen ADR; merging rewrites every call site for a benefit a view delivers read-only | Freeze taxonomy; unified read-only view in v1.1 (C7) |
| D7 | Replace `uuid[]` arrays (`client_access`, `read_by`) with junction tables (audit §13) | ADR conflict | Table structure is ADR-fixed; arrays are functionally fine at v1.0 scale; the churn buys nothing measurable | GIN on the security-bearing array; app membership hygiene; `last_read_at` canonical (C6) |
| D8 | Convert free-text statuses to PG enums (audit §13; §10.3.3 context) | ADR conflict | PG enums are migration-hostile: every new value is a type alteration | CHECK value lists: queue/billing/role in v1.0 (A); the rest in v1.1 (C3) |
| D9 | County lookup table — 26 ROI + 6 NI + UK ceremonial (audit §12.2 item 11, finding D1-B7) | Low value; maintenance burden | Nothing in v1.0 computes from `county` — display data in both markets; neither Royal Mail nor Eircode routing requires it. Imports Dublin city/county and Derry/Londonderry edge-case debt for zero consumers | Free text; normalise via address verification (C8); CHECK-in list if facets ever needed |
| D10 | UK nation field plus four-jurisdiction bank-holiday modelling on `business_hours` (audit §12.2 items 12–13, findings D1-A10, D1-A14) | Low value; over-engineering | No v1.x consumer: CH prefix validation is app-layer; nation is derivable from postcode outward area. Four-jurisdiction modelling is disproportionate to a few SLA-boundary days yearly | Org-level holiday dates in v1.1 (C19); `facilities.region` documented/dormant |
| D11 | New parallel `country_code` ISO column (audit §6.4 finding D-3) | Over-engineering (second source of truth) | Diagnosis right, prescription wrong: free-text `country` collecting "UK"/"England" is not cured by a second column kept in sync with the first | Constrain existing `country` to CHECK IN ('GB','IE') — A |
| D12 | SIC 2007 lookup table / Companies House API schema artefacts (audit §4.1 finding A4 context) | Low value (gold-plating) | Nothing computes from `sic_code` in v1.0; a lookup is a maintenance artefact in search of a requirement; CH integration is app-layer | Free entry with 5-digit UI hint (C11); app-layer integration if a consumer emerges |
| D13 | Separate `cro_number` column alongside `company_number` (audit §5.2 finding D1-B4 context) | Over-engineering (duplication) | One `company_number` column with country-conditional app validation serves both jurisdictions; a second duplicates identity and splits the existing UNIQUE | One column + UNIQUE; 6-digit CRO at API when `country='IE'` (B) |
| D14 | UNIQUE on `suppliers(organization_id, name)` (audit §10.3.2, findings F4/A4) | Low value (incorrect integrity rule) | Same-name suppliers legitimately exist (two "City Electrical" branches); a name-unique forces "City Electrical 2" workarounds that pollute the master data | Partials on `vat_number`/`company_number` (A) + `pg_trgm` "did you mean?" UX (B) |
| D15 | `external_id` / `integration_source` / `last_synced_at` columns "now" (audit §11.1.1, finding D3-E1) | Premature (YAGNI) | Speculative identity columns across five tables with no sync contract invite semantic drift; `external_id` means nothing before an integration exists | Add when the Xero/QBO integration is scoped (C22) |
| D16 | `api_keys` / `webhook_events` tables in v1.x (audit §11.3.1, finding D3-E3) | Premature | Rate-limit settings are no commitment to build an API product; no integration customer exists to consume keys or webhooks | v2.0 with the first integration customer (C26); hash `consultant_profiles.api_key` now (A) |
| D17 | Deleting dormant EU/US fields (`organizations.cik`, `naics_code`, `isin`, `sedol`, `issb_*`, `esrs_*`) as scope hygiene (audit §7.4/§13, deletion option) | ADR conflict (additive-only posture); irreversible | Dropping compliance columns from a live schema is irreversible scope vandalism; `nace_code`/`esrs_enabled` may activate for CSRD-scope Irish customers. Dormant ≠ deleted | Keep dormant, marked out-of-scope; activate per C29's watch item |
| D18 | Per-user 2FA columns (`users.totp_secret`, `two_factor_enabled`, `backup_codes`) and lockout columns (`failed_login_attempts`, `locked_until`) (audit §12.2 item 6, §12.1 item 26, finding D3-B4) | ADR conflict (platform ownership) | With Supabase Auth as IdP (ADR-consistent; null `password_hash` seeds), TOTP/lockout belong to the platform (`auth.mfa_*`); parallel auth state creates two drifting credential/lockout truths | Decide `users.password_hash` ownership (A); market `two_factor_required` honestly until the platform feature ships |
| D19 | Indexes on static reference, marketing and presence tables (`units`, `glossary`, `roles`, `waitlist`, `beta_users`, `beta_access_codes`, `dashboard_metrics`, `typing_status`, `user_presence`) (audit §8.1 finding D3-A1's blanket) | Low value; premature | Dozens-of-rows tables: the planner never chooses the index — dead weight. Marketing tables are purged at GA; presence tables move to Realtime (C21) | Purge `waitlist`/`beta_*` PII at GA (B); interim UNIQUE + purge on presence tables (B) |
| D20 | DB sync triggers keeping `suppliers.address` / `organizations.registered_address` / `billing_address` blobs aligned with structured columns (audit §6.4 finding D-2 option; §12.1 item 25) | Over-engineering | Triggers add hidden write-path complexity and failure modes to a procedural problem. Two writers with a trigger is still two writers | Write-path convention (B): structured columns canonical; blobs are app-generated display caches |

**Interpretation.** Read together, the twenty rejections expose one instinct in the audit: on finding a defect, reach for the strongest available mechanism — a constraint, an index, a table, a cryptographic construction — regardless of whether a weaker control closes the actual risk. Hence regex CHECKs where a library call suffices (D1), sixty indexes where eighteen serve every committed screen (D2), partitioning where a cron delete suffices (D4), a hash chain whose verifier is its own writer (D5) — and correct diagnoses with wrong cures: a second `country` column for a single-source-of-truth defect (D11), a name-unique outlawing legitimate same-name suppliers (D14).

The through-line is an audit that is thorough but indiscriminate: twenty-six "launch blockers" mixing genuine gates with hygiene, strong mechanisms unaccompanied by the volume, threat-model or consumer analysis that would justify them. Restraint here is not leniency — every rejection pairs with a control that ships — it is calibration. Each rejected mechanism is work built, tested, migrated and maintained before launch, for risk reduction that is zero (D19), illusory (D5), or a line of application code (D1). Protecting the launch date *is* protecting the launch: absorbing the audit wholesale turns a hardening sprint into a redesign programme, and the UK and Irish firms the schema serves would feel the delay long before they felt the difference.


## 7. Final Production Hardening Checklist

This is the single authoritative launch gate: every row is Category A, drawn from the §3 register and ordered for execution. The ✔ column is initialled only when the named evidence exists; "code merged" is not evidence.

| ✔ | # | Item | Verification evidence required |
|---|---|---|---|
| ☐ | 1 | Inspect the Supabase migration files (action zero): reconcile the dump — which showed no indexes, FKs, CHECKs or RLS policies — against reality | Signed note restating which findings are real and which collapse to verification |
| ☐ | 2 | Fix the facilities blocker: nullable `facilities.eircode`, relaxed `facilities.postcode`, presence CHECK (postcode OR eircode) | Staging insert of an IE facility with Eircode and NULL postcode succeeds; insert with both NULL is rejected |
| ☐ | 3 | Constrain `organizations.country`, `facilities.country`, `suppliers.country`, `consultant_profiles.country` to IN ('GB','IE') | Constraint definitions present; out-of-list write rejected on staging |
| ☐ | 4 | Constrain the six `currency` columns and `system_settings.default_currency` to IN ('GBP','EUR') | As above; existing values audited to the list first |
| ☐ | 5 | Verify the full RLS policy matrix; enforce service-role discipline (no service key client-side; workers filter `organization_id` in code) | Executed penetration matrix (§9): zero cross-tenant rows for customer, consultant, staff and service roles; sign-off on service-key handling |
| ☐ | 6 | Backfill then NOT NULL `organization_id` on `conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications` | Zero-NULL counts; constraints present; pre-backfill snapshot retained |
| ☐ | 7 | Hash `consultant_profiles.api_key`, `password_reset_tokens.token`, `user_invitations.token` (SHA-256 + lookup prefix; rotation columns on the API key) | No plaintext credential recoverable from a staging dump; auth-flow regression passes |
| ☐ | 8 | Drop UNIQUE on `password_reset_tokens.user_id`; keep UNIQUE on `password_reset_tokens.token`; latest-valid-wins in app | Repeated resets for one user no longer error; only the latest token validates |
| ☐ | 9 | Decide `users.password_hash` ownership; if Supabase Auth is IdP, dead-column it and never write | Recorded decision; column confirmed unwritten by code inspection |
| ☐ | 10 | Verify every FK and ON DELETE action; RESTRICT on financial/audit tables where dangerous CASCADEs are found | FK/ON DELETE inventory; staging destructive-delete rehearsal matches it |
| ☐ | 11 | Seed cleanup: remove `.de`/`.fr`/`.fi`/`.ai` users; add IE org + IE facility fixtures (Eircode, EUR, IE factor) | Staging seed holds only GB/IE rows; the Irish end-to-end fixture passes |
| ☐ | 12 | Add `organizations.is_active` and `organizations.archived_at` | Suspend demonstrated on staging without deleting child rows |
| ☐ | 13 | Relax NOT NULL on `customer_documents.asset_id` | Supplier-invoice upload with no asset completes on staging |
| ☐ | 14 | Add `consultant_billing.currency` with default and backfill | All billing tables denominated; reconciliation report clean |
| ☐ | 15 | Add provenance columns to `defra_conversion_factors` (`unit`, `scope`, `factor_source`/`factor_set`, `country`); backfill 'DEFRA-DESNZ'; UNIQUE `(reporting_year, activity_type)` | Duplicate-insert rejected; every factor row states unit, scope, source |
| ☐ | 16 | Load the minimal current-year SEAI/EPA core set (grid electricity, gas, common fuels) | Dublin fixture's Scope 2 resolves to the Irish factor, not DEFRA |
| ☐ | 17 | Add `emissions_logs.unit` (FK to `units.code`) and `emissions_logs.scope` | kWh totals computable without the factor join; SECR fixture totals audit-clean |
| ☐ | 18 | Range CHECKs ≥ 0 on `emissions_logs.raw_quantity`, `.calculated_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*`, `supplier_categories.default_emission_factor` | Negative write rejected on each column |
| ☐ | 19 | Widen `file_attachments.file_size` (and peers) to int8 with size CHECKs | >2 GB synthetic upload path handled; constraints present |
| ☐ | 20 | Add `customer_documents.file_checksum` (SHA-256) for duplicate-upload detection | Identical re-upload detected deterministically |
| ☐ | 21 | Add the uniqueness set: `organization_members(organization_id, user_id)`, `consultant_clients(consultant_id, organization_id)`, `usage_tracking(organization_id, usage_month)`, `report_versions(report_id, version_number)`, `suppliers(organization_id, vat_number)`/`(organization_id, company_number)` partial WHERE NOT NULL | Dedupe sweep clean; each constraint rejects a scripted duplicate |
| ☐ | 22 | Block writes to `pending_invites`; `user_invitations` is canonical | Write to `pending_invites` fails; invite regression passes |
| ☐ | 23 | Anonymise-in-place erasure procedure (hash `users.email`, "Deleted User", keep UUID), tested on staging | Timed staging rehearsal against a production-like FK graph; residual-PII scan clean |
| ☐ | 24 | Residency verification: Supabase region UK-London or eu-west-1; `system_settings.backup_storage_location` matches | Configuration evidence archived in the compliance pack |
| ☐ | 25 | Targeted NOT NULL + DEFAULT on hot booleans/timestamps: `organizations.is_active`-style flags and processing timestamps on `processing_queue`, `document_processing_queue`, `customer_documents`, `emissions_logs`; backfill before constrain | Zero-NULL counts on the named columns; defaults verified on staging insert paths |
| ☐ | 26 | CHECK value lists on `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status` | Value-mapping audit clean; out-of-list write rejected on each column |

**B items scheduled for the v1.0.x hardening window** (recommended, none launch-gating):

| Item | Target release |
|---|---|
| Retention schedule + first pg_cron jobs (`processing_logs` 90d; login/email 12m; activity logs 12–24m; audit 24m); `retention_until` on the document class | v1.0.1 — first weeks post-launch |
| `customer_documents` soft-delete (`deleted_at` + RLS/query filters) | v1.0.1 |
| `pg_trgm` on `suppliers.name`/`.vat_number` and `organizations.name` + "did you mean?" UX | v1.0.1–v1.0.2 |
| App-layer validation pack (VAT + MOD97, CH/CRO numbers, GIR postcode, Eircode shape, libphonenumber/E.164) + EUR default when `country='IE'` | v1.0.1 |
| Audit privilege hardening (revoke UPDATE/DELETE on audit tables; drop `updated_at` from append-only logs) | v1.0.1 |
| `suppliers.sort_code` column ships with the P1 security migration; last-4 bank masking in API responses lands here | v1.0.2 |
| Labelled `organization_metadata.total_floor_area_sqm`/`.occupied_floor_area_sqm`; `facilities.meter_mpan_mprn`; `emissions_logs.facility_id` dual-write | v1.0.2 |
| Remaining B-class CHECKs (timezone IN-list, date pairs, percentage 0–100 after scale convention, counts ≥ 0) | v1.0.2 |
| PII inventory, DSAR export expiry, waitlist/beta purge at GA, support-log indexes | v1.0.1–v1.0.2 |
| `notification_delivery`/`notification_delivery_log` dedup — keep one delivery table, drop/merge the other (mirrors the `pending_invites` consolidation) | v1.0.1–v1.0.2 |
| `notifications.recipient_type` IN-list CHECK | v1.0.2 |
| `customer_documents.organization_member_id` NOT NULL relaxation | v1.0.1 |
| `default_vat_rate`/`default_tax_rate` dedup — keep one canonical column, deprecate the other | v1.0.2 |
| `confidence_score` type/scale standardisation | v1.0.2 |

The checklist is the gate. There is no partial credit: twenty-five of twenty-six rows evidenced is a NO-GO, and the twenty-sixth row is precisely the one that fails publicly in the first month. The "verify" rows (1, 5, 10, 24) gate on evidence because a multi-tenant financial product cannot go live on unverified isolation, whatever the migration files turn out to contain.

## 8. Recommended Migration Order

Five phases, as the client framed them. Most A-class change is additive and Small; the phasing sequences verification before constraint, and constraint before data load — it is not managing heavy migration risk on a live-but-pre-revenue database.

### P1 — Critical production fixes

| Attribute | Detail |
|---|---|
| Objectives | Close the launch-blocking security, tenancy and Irish write-path defects (checklist rows 2–13): credential/token hashing, reset-token UNIQUE correction, `users.password_hash` decision, RLS verification, nullable-`organization_id` backfill + NOT NULL, tenant lifecycle columns, `asset_id` nullability, facilities Eircode fix, country/currency IN-lists, seed cleanup |
| Database impact | Medium (tenancy backfill + constraints); otherwise Small/additive |
| Application impact | Small: key/token issuance flows; insert paths must always set `organization_id`; suspend UI hook; upload paths |
| Migration risk | Low (security batch); Medium (tenancy batch — policy changes can lock out users if untested with non-privileged roles) |
| Estimated effort | Two migrations plus verification: (1) **P1 security migration** — hashing columns, reset-token UNIQUE drop, `suppliers.sort_code`, one deploy; (2) **P1 tenancy migration** — lifecycle columns, nullability, org backfill staged backfill → verify → constrain, one deploy |
| Testing requirements | RLS penetration matrix; auth-flow regression (reset, invite, API key); Irish fixture end-to-end; lockout test under non-privileged roles |
| Rollback strategy | Security migration rolls forward — hashing is one-way; re-issue keys/tokens rather than reverse. Tenancy migration: snapshot before backfill; dropping a NOT NULL is easy, un-backfilling is not |

### P2 — Data integrity improvements

| Attribute | Detail |
|---|---|
| Objectives | Land the integrity register — checklist rows 14–22 and 25–26 (Category A): uniqueness set, emission range CHECKs, `file_size` int8 widening, `file_checksum`, factor provenance + UNIQUE, `pending_invites` write-block, targeted NOT NULL DEFAULTs on hot booleans/timestamps, CHECK value lists on the five queue/billing/role status columns; FK/ON DELETE remediation where P1 inspection proved danger. B-class companions in the same phase: money/count range CHECKs, soft-delete, audit privilege hardening |
| Database impact | Medium (constraints across many tables, one type widening) |
| Application impact | Small: invalid-state errors, duplicate 409s, ingest sets new columns; Medium for soft-delete (every document read path filters) |
| Migration risk | Low–Medium pre-revenue: dedupe before UNIQUEs, backfill before NOT NULLs, value-mapping before status CHECKs |
| Estimated effort | One **P2 integrity migration** after a staging data audit; CHECKs added NOT VALID-style then validated to avoid table locks; SEAI/EPA data load rides this phase as a data deploy |
| Testing requirements | Staging data audit (§9 gate 2) signed off first; constraint-rejection script per rule; soft-delete regression across every document read path |
| Rollback strategy | Easy — drop constraint / re-grant privilege; the soft-delete column drops safely only before the app depends on it |

### P3 — Performance improvements

| Attribute | Detail |
|---|---|
| Objectives | Build the targeted index baseline (~11 A-set plus ~7 B-set): tenant composites on `customer_documents(organization_id, created_at DESC)` and `emissions_logs(organization_id, start_date)`, `suppliers`/`facilities(organization_id)`, the `document_processing_queue(status, created_at)` queue-claim partial, `messages(conversation_id, created_at)`, the unread-notifications partial, support-log indexes, the `consultant_firm_members.client_access` GIN; plus `pg_trgm` indexes and interim presence-table UNIQUEs |
| Database impact | Medium (build I/O only; no schema shape change) |
| Application impact | None |
| Migration risk | Low — every index built CONCURRENTLY, each in its own transaction |
| Estimated effort | One **P3 index migration**: the full A+B set built CONCURRENTLY, one release; may land at any point in the programme |
| Testing requirements | Load smoke (§9 gate 7); before/after query plans on the document list, emissions aggregation and worker claim path |
| Rollback strategy | Trivial — drop each index CONCURRENTLY |

### P4 — Validation improvements

| Attribute | Detail |
|---|---|
| Objectives | Land the application-layer validation pack replacing the rejected regex CHECKs: VAT + MOD97, CH/CRO company-number rules, GIR-valid postcode, Eircode shape + routing-key allowlist, libphonenumber/E.164; normalisation at write; EUR default when `country='IE'`; write-path conventions (structured address columns canonical, blobs as display caches; API rule against nullable `asset_id`); trigram "did you mean?" UX |
| Database impact | None — this is the phase that keeps formats out of the database per the layering rule |
| Application impact | Medium: validator library integration on all write surfaces, onboarding defaults, supplier/org creation UX |
| Migration risk | Low; the principal risk is over-rejecting legitimate edge cases, mitigated by shadow-mode logging before enforcement |
| Estimated effort | One application sprint parallel to P2–P3; the trigram UX depends on the P3 indexes |
| Testing requirements | Validator unit suites per jurisdiction (GB/IE positive and negative cases); shadow-mode review; normalisation idempotence |
| Rollback strategy | Feature-flag enforcement per validator; revert to shadow mode without a database change |

### P5 — Compliance improvements

| Attribute | Detail |
|---|---|
| Objectives | Ship the compliance pack (checklist rows 23–24 plus B items): anonymise-in-place erasure procedure (launch-gated), residency verification, retention schedule + first pg_cron jobs, `retention_until` on the document class, PII inventory, DSAR export expiry, waitlist/beta purge at GA |
| Database impact | Small: one `retention_until` column, job schedule; the erasure artefact is a procedure, not schema |
| Application impact | Small: ingest sets `retention_until`; erasure is a manual runbook in v1.0 |
| Migration risk | Low for jobs (small batches, dry-run counts first); Medium for the erasure procedure — a destructive script rehearsed on staging against a production-like FK graph |
| Estimated effort | Documentation-led **P5 compliance pack**: two small migrations plus the runbook; design begins in P1 |
| Testing requirements | Erasure rehearsal with residual-PII scan (§9 gate 5); retention dry-runs; residency evidence archived |
| Rollback strategy | Jobs: drop the job. Erasure: not reversible by design — the staging rehearsal evidence *is* the mitigation |

**Sequencing rationale.** P1→P5 is not strictly linear. The P3 index batch is independent and can land whenever a release window allows — it blocks nothing and nothing blocks it. P5 design work (the retention schedule and the erasure runbook's FK-graph mapping) starts in P1 so documentation matures alongside the schema it describes. And although the erasure procedure lives administratively in P5, it is launch-gated with the P1 items: a DSAR can arrive on day one, and the one artefact this plan refuses to schedule after launch is the tested answer to that request.

## 9. Testing Strategy

The testing philosophy follows the triage: launch-gating defects are the ones that fail silently, so the programme exists to make silent failures loud before customers do. Seven pre-launch gates apply.

**Gate 1 — migration-file inspection (action zero).** Before any remediation is scored, reconcile the schema dump against the actual Supabase migration files: the dump showed no indexes, FKs, CHECKs or RLS policies, so if migrations contain them, several findings collapse to verification and the plan re-points at evidence.

**Gate 2 — staging data audit before constraints.** The P2 migration runs only after a staging audit: NULL backfills counted before NOT NULLs, duplicate sweeps clean before UNIQUEs, existing values mapped before status CHECKs. On a pre-revenue database the sweeps should be near-empty; the audit proves that rather than assumes it.

**Gate 3 — Irish end-to-end regression fixtures.** An IE organisation with an IE facility carrying an Eircode, EUR currency and an IE emission factor, exercised through onboarding, upload, mapping and reporting — the guard whose absence let the facilities blocker survive to audit, now running in every release candidate permanently.

**Gate 4 — RLS penetration matrix.** Scripted cross-tenant access attempts per role — customer, consultant, staff, service — against every tenant table class. One cross-tenant row from any role is a launch-stopping failure, not a bug ticket.

**Gate 5 — erasure runbook rehearsal.** The anonymise-in-place procedure executed on staging against a production-like FK graph, timed, with a residual-PII scan. The one-month statutory clock means the rehearsal, not the first live DSAR, is where the procedure earns trust.

**Gate 6 — rollback rehearsal for the two non-trivial rollbacks.** The nullable-org backfill (snapshot restore — un-backfilling is impossible) and the token-hashing roll-forward (re-issuance — hashing is one-way), each rehearsed once on staging before P1 ships.

**Gate 7 — load smoke on the indexed query paths.** Document list, emissions aggregation, worker claim path and notification badge at projected year-one volumes, with query-plan evidence the P3 indexes are used.

| Test | Phase | Pass criterion |
|---|---|---|
| Migration-file reconciliation | Pre-P1 | Signed note; findings re-scored against reality |
| Staging data audit | Pre-P2 | Zero unhandled NULLs/duplicates/unmapped values |
| Irish end-to-end fixture | P1, then every release | IE org/facility registers, uploads, reports with IE factor |
| RLS penetration matrix | P1 | Zero cross-tenant rows across all four roles |
| Erasure rehearsal | P5 (launch-gated) | Completes in time; residual-PII scan clean |
| Rollback rehearsals | Pre-P1 deploy | Snapshot restore and re-issuance demonstrated |
| Load smoke | P3 | New indexes used; p95 within target at year-one volume |

## 10. Go/No-Go Assessment

**Verdict: Conditional GO.** CarbonTally launches in the UK and Ireland once — and only once — every row of the §7 checklist carries its named evidence. The triage shrunk the audit's 26-item programme into five migration batches (six deployable migrations) and two verification gates; what remains is small, additive and mostly low-risk, and nothing in the B, C or D registers stands between the product and revenue. But the A register is not negotiable, and the reasoning is concrete rather than doctrinal.

Launch without the **write-path and jurisdiction class** (rows 2–4) and Irish customers cannot register the sites whose emissions the product measures — the loudest possible failure in a launch market, discovered in the first onboarding call. Launch without the **numbers class** (rows 14–18) and the product ships silently wrong Scope 2 to Irish customers and unit-less quantities to everyone: nothing errors, the join succeeds, the arithmetic succeeds, and the filed report is wrong. Launch without the **upload-integrity class** (rows 19–20) and the first 2 GB bundle fails publicly while duplicate invoices go undetected on the primary pipeline entity. Launch without the **integrity class** (rows 13, 21–22, 25–26) and fake assets, duplicates, ambiguous NULL flags and unconstrained statuses enter silently through the pipeline and land in a customer's reported figures. Launch without the **tenancy and secrets class** (rows 5–9) and tenant isolation is unprovable — one forgotten `organization_id` or one escaped backup converts a marketing promise into a reportable ICO/DPC incident. Launch without the **foundations class** (rows 1, 10–12) — migration-file inspection, FK/ON DELETE verification, seed cleanup, tenant lifecycle columns — and the launch flies blind on its own delete behaviour, runs on out-of-market seeds, and has no suspend lever short of deleting audit evidence. Launch without the **compliance class** (rows 23–24) and the first DSAR triggers an untested destructive script against a live tenant under a one-month statutory clock. Every class fails invisibly at demo scale and publicly in production; that asymmetry is the entire case for the gate.

| Gate | Status today | Evidence required to clear |
|---|---|---|
| Irish write-path + jurisdiction IN-lists | Defects confirmed; fixes specified | Rows 2–4 evidenced on staging |
| Factor provenance + SEAI/EPA core load | Provenance columns and Irish data absent | Rows 15–16 evidenced; Dublin fixture resolves to IE factor |
| Tenancy isolation + secrets | Unverifiable from the dump; plaintext credentials present | Rows 1, 5–9 evidenced; penetration matrix clean |
| Uniqueness/integrity set | Unconstrained duplicates possible | Rows 13, 17–22, 25–26 evidenced post data audit |
| Erasure + residency | Procedure unwritten; region unchecked | Rows 23–24 evidenced; rehearsal timed, scan clean |

One descope is acceptable. If the SEAI/EPA load slips beyond the launch window, the fallback is a **UK-only launch with IE signups gated at onboarding** — a product decision, executed at the registration flow, not in the schema. What is never acceptable is the third option: shipping Irish customers DEFRA factors and calling it Scope 2; a wrong answer is not a placeholder. The schema work is required under either outcome, so the fallback costs the programme nothing but honesty.

**The verdict: GO — conditional on every row of §7 being evidenced; the checklist is the launch.**
