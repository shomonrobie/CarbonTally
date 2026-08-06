# CarbonTally v1.0 — Structural Change Review

*Chief Database Architect's review — prepared against the actual schema dump (`database.txt`, ~90 tables), the Production Hardening Plan and the original readiness review. Scope: structural changes only — renames, added columns, added tables, indexes, constraints, foreign keys. ADRs are frozen: the jsonb `metadata`/`extracted_data` pattern, the single processing-queue direction and Supabase Auth ownership are not revisited. No SQL is specified anywhere in this document; proposals are design prose. Data-only loads (e.g. seeding the SEAI/EPA factor set) and application-layer work are noted for context only, never as recommendations.*

## Executive Summary

Thirty-eight candidate structural changes were evaluated against the schema as dumped. The verdicts: **28 APPROVE, 4 DEFER, 6 REJECT**. The approved set is dominated by Small, additive changes — nullable columns, IN-list CHECKs, one type widening, three renames and five targeted index families — consistent with the hardening plan's finding that the launch programme is a hardening sprint, not a redesign.

The new product decision — UK as the default and primary launch market with full UK validation, UK reporting and UK defaults; Ireland as a beta market in which Irish users may register and operate but Ireland-specific localisation is limited to beta necessities — recalibrates rather than enlarges the prior triage. Two consequences follow. First, Ireland remains a *write-path* necessity even in beta: an Irish beta user must be able to register an organisation, add a facility (which requires the `facilities.eircode` fix, since Ireland has no postcodes), upload documents and see a reported number — so the Eircode write-path and the country/currency IN-lists stay approved. Second, Ireland-specific *validation depth* (Eircode routing-key verification, CRO number rules, county normalisation, Irish address-verification loops) is correctly held at the API layer or deferred — none of it is structural, and none of it justifies schema. The rejected regex-CHECK matrix stays rejected under either framing.

The hard requirement — full Ireland support in v1.1 with **no major database redesign** — is met by three specific enablers in the approved set: **R1** (`defra_conversion_factors` renamed to the jurisdiction-neutral `emission_factors`), **R2** (the two referencing FK columns renamed to `emission_factor_id`/`emission_factor_used`), and **C4** (provenance columns including a `country` jurisdiction column constrained to the ('GB','IE') list by K1's mechanism). With those three in place, v1.1 Ireland activation is a *data* exercise — loading SEAI/EPA rows with `country='IE'` — plus API-layer validation work, against a schema that already names, keys and constrains jurisdiction correctly. Note for context (not a recommendation, being a data load): the minimal current-year SEAI/EPA core factor load identified in the hardening plan remains the correct companion to C4 and should ride the same phase; it is excluded from this register because it changes rows, not structure. Where the dump is silent — it shows no indexes, foreign keys, CHECK definitions or RLS policies — this review states so explicitly, and the migration-file inspection (the hardening plan's "action zero") is recorded as the migration-impact caveat on every affected item.

## Summary Register

| ID | Change | Type | Recommendation | Effort |
|----|--------|------|----------------|--------|
| R1 | `defra_conversion_factors` → `emission_factors` | Rename | APPROVE | Small |
| R2 | `emissions_logs.defra_factor_id` → `emission_factor_id`; `document_processing_queue.defra_factor_used` → `emission_factor_used` | Rename | APPROVE | Small |
| R3 | `organizations.default_defra_version` → `default_factor_year` | Rename | APPROVE | Small |
| C1 | `facilities.eircode`; relax `facilities.postcode` NOT NULL; presence CHECK (postcode XOR-or-OR by country) | Column + constraint | APPROVE | Small |
| C2 | `organizations.is_active` + `organizations.archived_at` lifecycle columns | Columns | APPROVE | Small |
| C3 | `consultant_billing.currency` | Column | APPROVE | Small |
| C4 | `emission_factors` provenance columns: `unit`, `scope`, `factor_source`, `factor_set`, `country` | Columns | APPROVE | Small |
| C5 | `emissions_logs.unit` (FK to `units.code`) + `emissions_logs.scope` | Columns | APPROVE | Small |
| C6 | `customer_documents.file_checksum` (SHA-256) | Column | APPROVE | Small |
| C7 | `file_attachments.file_size` int4 → int8 widening | Type change | APPROVE | Small |
| C8 | `suppliers.sort_code` (masked banking) | Column | APPROVE | Small |
| C9 | `facilities.meter_mpan_mprn` | Column | APPROVE | Small |
| C10 | `organization_metadata.total_floor_area_sqm` / `.occupied_floor_area_sqm` | Columns | APPROVE | Small |
| C11 | Typed invoice columns on `customer_documents` | Columns | DEFER | Medium |
| C12 | `emissions_logs.facility_id` direct column | Column | DEFER | Medium |
| C13 | `customer_documents.deleted_at` soft-delete | Column | DEFER | Small |
| C14 | Per-user 2FA/lockout columns on `users` | Columns | REJECT | — |
| C15 | `external_id`/`integration_source`/`last_synced_at` integration columns | Columns | REJECT | — |
| T1 | `emission_factor_sets` / factor-jurisdiction mapping table | Table | REJECT | — |
| T2 | Audit-archive table | Table | DEFER | Medium |
| T3 | County lookup table (26 ROI + 6 NI + UK ceremonial) | Table | REJECT | — |
| I1 | Tenant composites: `customer_documents(organization_id, created_at DESC)`, `emissions_logs(organization_id, start_date)`, `suppliers(organization_id)`, `facilities(organization_id)` | Index family | APPROVE | Medium |
| I2 | Queue-claim partials: `document_processing_queue(status, created_at)`, `processing_queue(queue_status, …)`, `report_generation_queue` | Index family | APPROVE | Medium |
| I3 | Messaging/notifications: `messages(conversation_id, created_at)`, `conversation_participants(conversation_id, user_id)`, unread-notifications partial | Index family | APPROVE | Medium |
| I4 | `consultant_firm_members.client_access` array GIN | Index | APPROVE | Small |
| I5 | `pg_trgm` on `suppliers.name`/`.vat_number`, `organizations.name` | Index family | APPROVE | Small |
| I6 | Blanket "index every FK" programme (~60 indexes) | Index programme | REJECT | — |
| K1 | `country` IN ('GB','IE') on `organizations`, `facilities`, `suppliers`, `consultant_profiles` | Constraint | APPROVE | Small |
| K2 | Currency IN ('GBP','EUR') on six `currency` columns + `system_settings.default_currency` | Constraint | APPROVE | Small |
| K3 | Range CHECKs ≥ 0 on emission quantities, factors and money counters | Constraint | APPROVE | Small |
| K4 | Status/role CHECK value lists on five queue/billing/role columns | Constraint | APPROVE | Small |
| K5 | Uniqueness set: memberships, consultant links, billing months, report versions, supplier identifier partials, factor UNIQUE | Constraint | APPROVE | Medium |
| K6 | Drop UNIQUE on `password_reset_tokens.user_id`; keep UNIQUE on `token` | Constraint | APPROVE | Small |
| K7 | Backfill then NOT NULL `organization_id` on six hot tenant tables | Constraint | APPROVE | Medium |
| K8 | NOT NULL + DEFAULT on hot booleans/processing timestamps | Constraint | APPROVE | Small |
| K9 | Country-conditional regex CHECKs (VAT, postcode, Eircode, phone, email, company numbers) | Constraint | REJECT | — |
| F1 | Verify-first full FK inventory; add missing FKs implied by the dump | Foreign key | APPROVE | Medium |
| F2 | ON DELETE behaviour corrections (RESTRICT on financial/audit tables where CASCADE proven dangerous) | Foreign key | APPROVE | Medium |

**Counts: 38 changes — 28 APPROVE, 4 DEFER, 6 REJECT.**

---

## 1. Column and Table Renames

### R1 — `defra_conversion_factors` → `emission_factors`

1. **Current design.** The table is named `defra_conversion_factors` and holds `id`, `reporting_year` (int4), `activity_type` (varchar), `co2e_multiplier` (numeric), `region` (varchar, nullable), `created_at`, `updated_at` — the schema dump also lists a second, duplicated `updated_at` line, treated here as a dump artefact to be confirmed during migration-file inspection. The name hard-codes one national factor authority (UK DEFRA/DESNZ) into the identity of the platform's factor store.
2. **Proposed design.** Rename the table to `emission_factors`. Row content is unchanged; the provenance columns that make the name honest arrive via C4, and the `country` jurisdiction column carries 'GB' for all existing rows. The existing `region` column half-does what `country` will do properly, so during the C4 backfill its values are mapped into `country` and `region` is then retired, keeping the factor table to a single jurisdiction column in line with this review's single-source-of-truth stance.
3. **Why the change is needed.** Under the UK-primary/IE-beta decision, Irish factors do not need full support in v1.0 — but the *name* of the table is the single structural artefact that cannot absorb a second jurisdiction without either a misleading label or a breaking rename later. A table rename on a live, factor-referenced table is precisely the kind of change the "no major redesign in v1.1" requirement exists to pre-empt. The only cheap moment to do it is pre-launch, while the referencing surface is small and pre-revenue.
4. **Benefits.** Jurisdiction-neutral naming for the v1.1 SEAI/EPA activation; honest naming for beta users who will see Irish factors later; reporting and analytics code written in v1.0 against the permanent name.
5. **Risks.** A rename touches every query, view, ORM model and seed script referencing the old name — a mechanical but wide search-and-replace; a missed reference surfaces only at runtime. Low technical risk, moderate completeness risk, mitigated by a single coordinated deploy.
6. **Migration impact.** Small: one metadata-only rename (no table rewrite). Verify against migration files that no view, function or RLS policy references the old name — the dump shows none, but the dump is silent on policies and functions.
7. **Application impact.** All factor-lookup call sites updated in the same release; no behavioural change.
8. **Backward compatibility.** Breaking for any external consumer of the old name; there are none pre-launch. Not compatible with a staged old/new dual-name period — renames are atomic.
9. **Recommendation: APPROVE.** This is the cheapest of the three v1.1-Ireland enablers and the one whose cost grows fastest with time.

### R2 — `emissions_logs.defra_factor_id` → `emission_factor_id`; `document_processing_queue.defra_factor_used` → `emission_factor_used`

1. **Current design.** `emissions_logs.defra_factor_id` (uuid, nullable) references the factor table; `document_processing_queue.defra_factor_used` (uuid, nullable) records the factor applied during pipeline calculation. Both column names repeat the jurisdiction-specific prefix.
2. **Proposed design.** Rename both columns to jurisdiction-neutral names in the same migration as R1.
3. **Why the change is needed.** The hardening plan deferred the `defra_factor_id` rename to v1.1 (item C15); the UK-primary/IE-beta decision and the no-redesign requirement invert that. Renaming the table (R1) while leaving its referencing columns named `defra_*` would freeze a permanent lie into the two hottest tables that consume factors — and a column rename on `emissions_logs` after a year of tenant data and reporting snapshots is materially harder than today.
4. **Benefits.** Consistent neutral naming across the factor-read path; v1.1 needs no rename migration on a populated `emissions_logs`; seeds, fixtures and reporting code written once against final names.
5. **Risks.** Same mechanical completeness risk as R1, slightly wider because `emissions_logs` is touched by reporting, exports and the pipeline. Coordinated single release required.
6. **Migration impact.** Small — metadata-only renames. Verify no views/functions reference the old column names (dump silent; migration-file inspection is the caveat).
7. **Application impact.** All factor-join and audit-display call sites updated with R1's release.
8. **Backward compatibility.** Breaking only for pre-launch code; no external consumers exist.
9. **Recommendation: APPROVE.** Companion to R1; splitting them buys nothing and strands misleading names on hot tables.

### R3 — `organizations.default_defra_version` → `default_factor_year`

1. **Current design.** `organizations.default_defra_version` (int4, nullable) stores each organisation's default factor reporting year; `system_settings.default_emission_factor_year` (int4) already uses neutral naming at platform level, making the org column's `defra` prefix both jurisdiction-specific and internally inconsistent.
2. **Proposed design.** Rename to `default_factor_year`, matching the platform-level setting's semantics.
3. **Why the change is needed.** This is the one org-level setting an Irish beta tenant will read on day one (which year's factors apply to their reports). Under UK-primary it stays functionally UK-defaulted; under the no-redesign rule its name must not require a v1.1 migration.
4. **Benefits.** Neutral, self-consistent naming; zero functional change.
5. **Risks.** Trivial completeness risk; the column has few readers (onboarding defaults, report generation).
6. **Migration impact.** Small, metadata-only; rides the R1/R2 release.
7. **Application impact.** Onboarding-default and report-generation readers updated in the same release.
8. **Backward compatibility.** Breaking only for pre-launch code.
9. **Recommendation: APPROVE.**

---

## 2. New Columns

### C1 — `facilities.eircode`; relax `facilities.postcode` NOT NULL; presence CHECK

1. **Current design.** `facilities` has `postcode` (varchar, **NOT NULL**), `country` (varchar, nullable), and **no** `eircode` column — while `organizations`, `suppliers` and `consultant_profiles` all already carry nullable `eircode` columns, proving the pattern was intended and `facilities` was missed.
2. **Proposed design.** Add nullable `facilities.eircode` (varchar); relax `facilities.postcode` to nullable; add a presence CHECK requiring at least one of `postcode`/`eircode` to be present (country-conditional XOR — exactly one when `country` is known — was considered; the simpler "at least one" form is preferred because `facilities.country` is itself nullable and the API layer owns the per-country rule). Format validation of the Eircode value stays at the API layer (K9).
3. **Why the change is needed.** Ireland has no postcodes. With `postcode` NOT NULL and no `eircode`, an Irish beta user physically cannot insert the facility row whose emissions the product measures. This is beta-necessary, not beta-optional: registration and site creation are the core beta flow.
4. **Benefits.** Unblocks the Irish onboarding path; aligns `facilities` with the three peer tables; the CHECK guarantees the row always carries a locatable identifier for either market.
5. **Risks.** Relaxing a NOT NULL widens the state space; the presence CHECK closes the only harmful new state (both NULL). Any existing UK code assuming `postcode` always present must tolerate NULL — small audit.
6. **Migration impact.** Small: one nullable add, one constraint drop, one CHECK add. Pre-launch data is GB-only seeds, so no backfill is required; verify seed facilities all carry postcodes.
7. **Application impact.** Facility forms render Eircode when `country='IE'`; API normalises and validates format. The staging acceptance test: IE facility with Eircode and NULL postcode inserts; both-NULL rejected.
8. **Backward compatibility.** Fully additive for reads; writes gain one rejection case (both NULL) that no legitimate UK row can hit.
9. **Recommendation: APPROVE.** The single non-negotiable Ireland write-path change; everything else Irish is negotiable, this is not.

### C2 — `organizations.is_active` + `organizations.archived_at`

1. **Current design.** `organizations` (~65 columns) has no tenant lifecycle state — no `is_active`, no `archived_at` — although `users`, `facilities`, `suppliers`, `consultant_profiles` and `report_templates` all carry `is_active` flags.
2. **Proposed design.** Add `organizations.is_active` (boolean, NOT NULL, default true, backfilled true) and `organizations.archived_at` (timestamptz, nullable).
3. **Why the change is needed.** Without a suspend path, the only lever for a churned, abusive or non-paying tenant is deleting rows — which destroys the audit evidence carbon accounting exists to preserve. Applies equally to UK-primary tenants; jurisdiction-neutral.
4. **Benefits.** A reversible, evidence-preserving off-switch; gives support and billing a state machine hook; RLS policies gain a clean suspend predicate.
5. **Risks.** A new flag read on hot paths must be enforced everywhere to mean anything — partial enforcement is worse than none; default-true backfill makes pre-launch rollout safe.
6. **Migration impact.** Small: two adds plus a trivial backfill on a small table.
7. **Application impact.** Suspend/resume admin hook; login/API middleware checks the flag; Medium effort at the app layer but structurally trivial.
8. **Backward compatibility.** Fully additive; default true preserves current behaviour.
9. **Recommendation: APPROVE.**

### C3 — `consultant_billing.currency`

1. **Current design.** `consultant_billing` carries prices (`auto_extraction_price`, `manual_extraction_price`, numeric, nullable) with **no currency column** — the only billing table in the schema without one (`customer_subscriptions.currency`, `document_processing_queue.billing_currency`, `manual_extraction_batches.currency`, `suppliers.payment_currency`, `consultant_profiles.revenue_currency`, `organizations.currency` all exist).
2. **Proposed design.** Add `consultant_billing.currency` (varchar, nullable at add; defaulted and backfilled 'GBP'; constrained by K2's IN-list).
3. **Why the change is needed.** A two-currency launch (GBP primary, EUR for Irish beta consultants) cannot tolerate an undenominated price on any billing table; Stripe reconciliation keys off currency.
4. **Benefits.** Complete denomination of the billing surface; reconciliation and invoicing correctness for IE consultants.
5. **Risks.** Backfill assumption (GBP) must be validated against existing rows — pre-launch, near-zero risk.
6. **Migration impact.** Small: add, default, backfill, then K2's CHECK.
7. **Application impact.** Consultant-billing UI and Stripe sync read the column; invoice rendering denominates.
8. **Backward compatibility.** Additive; existing rows default to GBP, which matches the UK-primary launch reality.
9. **Recommendation: APPROVE.**

### C4 — `emission_factors` provenance columns: `unit`, `scope`, `factor_source`, `factor_set`, `country`

1. **Current design.** `defra_conversion_factors` (to be `emission_factors`, R1) stores `co2e_multiplier` with no statement of unit (kg CO2e per *what*), scope, source authority, factor set or jurisdiction. `system_settings.default_emission_factor_set` exists as a platform pointer to a set the factor table cannot currently identify.
2. **Proposed design.** Add five columns: `unit` (text; e.g. 'kWh', 'kg', 'litre', 'passenger.km'), `scope` (text; 1/2/3-category label), `factor_source` (text; 'DEFRA-DESNZ' backfill for all existing rows, 'SEAI'/'EPA' for v1.1 Irish rows), `factor_set` (text; named vintage/set identifier aligning with `system_settings.default_emission_factor_set`), and `country` (varchar, constrained to the ('GB','IE') IN-list per K1's mechanism, backfilled 'GB'). The existing nullable `region` column (R1) is folded into `country` during this backfill — its values mapped/migrated — and then retired, so the table does not carry two jurisdiction-ish columns into v1.1, consistent with this review's single-source-of-truth stance.
3. **Why the change is needed.** Two distinct defects: (a) correctness — a multiplier with no unit or scope makes every calculated number an inference, and unauditable numbers in a carbon product are the worst defect class; (b) the v1.1 enabler — `country` is the minimal structural hook that lets Irish factor rows coexist and be selected by jurisdiction *without* a new table (T1 evaluated and rejected below) or any redesign.
4. **Benefits.** Self-describing factors; jurisdiction selection becomes a `WHERE country = …` on the same table; K5's factor UNIQUE gains its natural key; honest audit trail for reported figures in both markets.
5. **Risks.** Five nullable adds plus a backfill — low risk; the only subtlety is choosing unit strings consistently (free text, not a lookup — a units FK is over-modelling at two jurisdictions).
6. **Migration impact.** Small: additive columns plus a one-statement backfill of existing DEFRA rows. Data load of Irish factors rides the same phase but is not structural and is excluded from this register.
7. **Application impact.** Factor selection UI shows unit/source/jurisdiction; calculation logging records `factor_source` against each computed line — Small.
8. **Backward compatibility.** Additive; existing rows remain valid with backfilled values.
9. **Recommendation: APPROVE.** The third and most substantive v1.1-Ireland enabler; combined with R1/R2 it converts "full Ireland in v1.1" from a migration project into a data load.

### C5 — `emissions_logs.unit` + `emissions_logs.scope`

1. **Current design.** `emissions_logs` stores `raw_quantity` (numeric, NOT NULL) with no unit column — the unit is only inferable through `defra_factor_id` → factor table, and no scope column exists despite `activity_categories.ghg_protocol_scope` and suppliers' per-scope columns.
2. **Proposed design.** Add `emissions_logs.unit` (text, FK to `units.code` — the existing `units` reference table) and `emissions_logs.scope` (varchar, nullable with backfill, value list per K4's mechanism once populated).
3. **Why the change is needed.** SECR kWh totals and scope rollups currently require the factor join to interpret every quantity; a quantity whose unit is an inference is unauditable. UK reporting (SECR) is the primary-market reporting obligation, so this is a UK-primary fix as much as anything.
4. **Benefits.** Self-describing emission entries; SECR totals computable without joins; scope rollups become direct aggregations for UK reporting and, later, Irish CSRD-adjacent reporting.
5. **Risks.** Backfill requires deriving unit/scope for existing rows via the factor join — feasible pre-launch because volumes are seed-scale; mis-backfilled rows would mislabel history, so the staging data audit gates it.
6. **Migration impact.** Small-to-Medium: two adds, a derived backfill, one FK. Verify `units.code` values cover the factor units introduced by C4.
7. **Application impact.** Entry and mapping forms capture unit explicitly; workers write scope at calculation time — Small.
8. **Backward compatibility.** Additive after backfill; readers ignoring the columns behave as today.
9. **Recommendation: APPROVE.**

### C6 — `customer_documents.file_checksum`

1. **Current design.** `customer_documents` — the primary pipeline entity — has no content hash; duplicate-upload detection is impossible except by name, and `document_processing_queue.file_size_bytes` (int8) is the only file fingerprint anywhere in the pipeline.
2. **Proposed design.** Add nullable `customer_documents.file_checksum` (text, SHA-256 hex), populated at upload. No UNIQUE in v1.0 (hard uniqueness defers with duplicate-resolution UX).
3. **Why the change is needed.** Deterministic duplicate detection on the entity that drives AI extraction spend; re-uploads currently re-process silently, costing money and doubling draft emissions.
4. **Benefits.** Cheap, deterministic dedup signal; enables "this file was already uploaded" UX; near-free on a young table.
5. **Risks.** None structural; application must hash before/at upload.
6. **Migration impact.** Small: one nullable add; existing rows stay NULL (undetectable duplicates among pre-launch seeds are inconsequential).
7. **Application impact.** Upload path computes SHA-256; dedup prompt UX — Small.
8. **Backward compatibility.** Fully additive.
9. **Recommendation: APPROVE.**

### C7 — `file_attachments.file_size` int4 → int8

1. **Current design.** `file_attachments.file_size` is int4 (2 GB ceiling), while its pipeline peers `document_processing_queue.file_size_bytes` and `processing_queue.file_size_bytes` are already int8 — an inconsistent widening that leaves one table able to overflow.
2. **Proposed design.** Widen `file_attachments.file_size` to int8, matching the peer columns; add a non-negative size CHECK per K3's mechanism.
3. **Why the change is needed.** int4 overflows at ~2.1 GB, reachable by invoice bundles; the failure mode is an upload error at the customer's highest-value moment. Widening is near-free pre-launch and a full table rewrite on a large table later.
4. **Benefits.** Consistent int8 across the pipeline; overflow eliminated; ceiling raised beyond any plausible upload.
5. **Risks.** Type widening rewrites the table — trivial at pre-launch row counts; the only reason to do it *now* rather than defer.
6. **Migration impact.** Small now (table rewrite over seed-scale rows); Large if deferred a year.
7. **Application impact.** None — int8 is returned where int4 was; clients using 32-bit parsing should already handle the peer int8 columns.
8. **Backward compatibility.** Widening is value-compatible; no data change.
9. **Recommendation: APPROVE.**

### C8 — `suppliers.sort_code`

1. **Current design.** `suppliers` holds `bank_name`, `bank_account`, `iban`, `swift_code` (all varchar, nullable) but no `sort_code` — the standard UK domestic account-routing identifier, absent from the banking set of a UK-primary product.
2. **Proposed design.** Add nullable `suppliers.sort_code` (varchar), stored normalised (digits only); masking (last-4 display) is an API concern and not structural.
3. **Why the change is needed.** UK supplier banking is keyed by sort code + account number; without the column, UK supplier payment data is incomplete while the IE path (IBAN) is already covered by the existing `iban` column. Beta-necessity cuts both ways: IE is served, UK is not.
4. **Benefits.** Complete UK domestic banking capture; no IE impact; pairs with the existing `iban` for full GB/IE coverage.
5. **Risks.** Another banking PII column to inventory (joins the PII register with its peers); masking/envelope-encryption questions are app/vault work, not structural.
6. **Migration impact.** Small: one nullable add.
7. **Application impact.** Supplier banking form gains the field; API masks in responses — Small.
8. **Backward compatibility.** Fully additive.
9. **Recommendation: APPROVE.**

### C9 — `facilities.meter_mpan_mprn`

1. **Current design.** `facilities` has no meter identifier, yet the product's core UK flow is matching electricity/gas bills (which carry MPAN for electricity, MPRN for gas — Ireland also uses MPRN) to sites.
2. **Proposed design.** Add nullable `facilities.meter_mpan_mprn` (varchar) as a single free-format identifier column. Bill-to-facility matching logic is application work and explicitly out of scope.
3. **Why the change is needed.** The column is cheap now and serves both markets (MPAN is GB, MPRN is GB-gas and IE-gas); retrofitting it after facilities accumulate means a backfill against paper records.
4. **Benefits.** Enables the future matching feature with no schema change; immediate value as a display/reference field.
5. **Risks.** Free-format identifier invites inconsistent entry — mitigated by API normalisation, not a CHECK (K9 layering rule).
6. **Migration impact.** Small: one nullable add.
7. **Application impact.** Facility form gains the field; matching logic is v1.1 app work.
8. **Backward compatibility.** Fully additive.
9. **Recommendation: APPROVE.**

### C10 — `organization_metadata.total_floor_area_sqm` / `.occupied_floor_area_sqm`

1. **Current design.** `organization_metadata` carries `total_floor_area_sqft` and `occupied_floor_area_sqft` only — square-foot labelled columns for a product whose intensity ratios (kg CO2e/m²) are conventionally reported in square metres, and whose beta market (Ireland) is metric.
2. **Proposed design.** Add two nullable numeric columns `total_floor_area_sqm` and `occupied_floor_area_sqm`, explicitly labelled, alongside the existing sqft columns. Conversion tooling and sqft deprecation are deferred (v1.1).
3. **Why the change is needed.** Irish beta users will otherwise enter m² values into sqft-labelled columns, silently corrupting SECR-style intensity ratios by a factor of ~10.8. Two labelled columns prevent the mislabelling with no conversion machinery.
4. **Benefits.** Correct intensity denominators in both markets; zero migration risk; honest dual-labelling during the transition period.
5. **Risks.** Two parallel unit-labelled columns invite drift — bounded by the API write rule (populate the column matching the org's country default); deprecation path already planned.
6. **Migration impact.** Small: two nullable adds.
7. **Application impact.** Form renders the unit-appropriate field by country; reporting reads m² preferentially — Small.
8. **Backward compatibility.** Fully additive.
9. **Recommendation: APPROVE.**

### C11 — Typed invoice columns on `customer_documents`

1. **Current design.** Extracted invoice fields (`document_number`, dates, amounts, currency) live in the ADR-protected `extracted_data` jsonb on `customer_documents`; no typed columns exist.
2. **Proposed design.** Would promote six keys to typed columns.
3. **Why the change is needed.** The audit rated it Critical for query performance and typed filtering.
4. **Benefits.** Typed filtering and B-tree lookups on hot invoice keys.
5. **Risks.** Duplicates the jsonb payload into maintained-parallel columns with sync logic; contradicts the frozen jsonb ADR's own promotion criterion (promote keys when query logs prove the need); freezes guessed hot keys before any production traffic exists.
6. **Migration impact.** Medium: six adds, a backfill from jsonb, and permanent write-path dual-maintenance.
7. **Application impact.** Extraction pipeline dual-writes; sync-failure modes forever.
8. **Backward compatibility.** Additive, but creates the two-sources-of-truth problem the rejected `country_code` column (§5) exemplifies.
9. **Recommendation: DEFER** to v1.1, against query logs — the hardening plan's C1 stands. v1.0 duplicate detection is served by C6's checksum.

### C12 — `emissions_logs.facility_id`

1. **Current design.** `emissions_logs` attributes to `asset_id` (nullable); facility rollups derive via `assets.facility_id`.
2. **Proposed design.** Would add a denormalised direct `facility_id` column plus backfill and dual-write.
3. **Why the change is needed.** Site-level rollup performance and simpler reporting queries.
4. **Benefits.** One join fewer on site rollups.
5. **Risks.** Denormalisation drift (asset reassignment desynchronises the copy); backfill cost; the genuine defect — unattributable emissions via nullable `asset_id` — is a write-path rule, not a column.
6. **Migration impact.** Medium: add, derive-backfill, dual-write.
7. **Application impact.** Every emissions write path maintains the copy.
8. **Backward compatibility.** Additive.
9. **Recommendation: DEFER** to v1.1 with dual-write if trivial; the API write rule against nullable `asset_id` ships regardless (application layer, out of scope here).

### C13 — `customer_documents.deleted_at` soft-delete

1. **Current design.** No soft-delete on the primary document entity.
2. **Proposed design.** Nullable `deleted_at` timestamp with query/RLS filtering.
3. **Why the change is needed.** Recoverability of customer-deleted documents.
4. **Benefits.** Undo path; support recovery without backup restores.
5. **Risks.** Every document read path changes (filter discipline); partial adoption leaks deleted rows into totals.
6. **Migration impact.** Small structurally; Medium application-wide.
7. **Application impact.** All document reads filter — the reason it is not launch-gating.
8. **Backward compatibility.** Additive.
9. **Recommendation: DEFER** to the v1.0.x hardening window (per the plan's B-window), early while the table is young; not a launch gate at pre-revenue volumes with backups.

### C14 — Per-user 2FA/lockout columns on `users`

1. **Current design.** `users` holds `password_hash` (nullable; seeds show NULL, consistent with Supabase Auth as IdP) and no TOTP/lockout columns; `system_settings` advertises global `two_factor_required`/`login_attempts_*` flags.
2. **Proposed design.** Would add `totp_secret`, `two_factor_enabled`, `backup_codes`, `failed_login_attempts`, `locked_until`.
3. **Why the change is needed.** The audit proposed them for per-user MFA enforcement.
4. **Benefits.** None that the platform does not already provide.
5. **Risks.** Parallel auth state in `users` duplicates Supabase Auth's `auth.mfa_*` platform responsibility — a frozen ADR; two drifting credential/lockout truths; secrets at rest in the application schema.
6. **Migration impact.** — (not adopted).
7. **Application impact.** Would force auth-flow rewrites away from the platform.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT** (ADR conflict — platform ownership). The v1.0 obligations are the `users.password_hash` ownership decision (never write the column) and honest marketing of the global flags until the platform feature ships; both are application/config work.

### C15 — `external_id`/`integration_source`/`last_synced_at` integration columns

1. **Current design.** No integration-identity columns on `suppliers`, `organizations`, `customer_documents` or peers.
2. **Proposed design.** Would add speculative Xero/QBO sync columns across ~five tables.
3. **Why the change is needed.** Anticipated accounting integrations.
4. **Benefits.** None until a sync contract exists.
5. **Risks.** Speculative identity columns acquire improvised meanings the real integration must unpick; `external_id` has no semantics pre-contract (YAGNI).
6. **Migration impact.** — (not adopted).
7. **Application impact.** None.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT** (premature). Revisit when the first integration is scoped — columns ship with the contract, not before it.

---

## 3. New Tables

### T1 — `emission_factor_sets` / factor-jurisdiction mapping table

1. **Current design.** Factors live in one table (`defra_conversion_factors`, → `emission_factors`); `system_settings.default_emission_factor_set` is a free-text varchar with nothing to reference.
2. **Proposed design.** Would add a `factor_sets` parent table (id, jurisdiction, source authority, vintage year) with factors FK'd to it.
3. **Why the change is needed.** Argued as the "clean" normal form for multi-jurisdiction factors.
4. **Benefits.** Referential integrity on the set pointer; a place for set-level metadata.
5. **Risks.** Over-modelling at two jurisdictions: the same semantics are carried by C4's `country` + `factor_set` + `factor_source` columns at one-tenth the cost; a new table forces join changes across the calculation path; at two rows ('GB set', 'IE set') the table is ceremony. The explicit instruction for this review is to prefer the simpler option — the columns win.
6. **Migration impact.** Medium: new table, back-population, FK migration on the factor table, join rewrites.
7. **Application impact.** Factor resolution rewritten to traverse the set.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT.** C4's columns are the minimal sufficient v1.1 enabler; if a third jurisdiction or per-set metadata ever materialises, promotion to a table remains possible later from clean column data.

### T2 — Audit-archive table

1. **Current design.** Nine-plus per-domain audit/activity log tables (`audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, `review_audit_trail`, etc.) hold live history; no archive tier exists.
2. **Proposed design.** A cold-storage archive table/partition family with retention-driven moves.
3. **Why the change is needed.** Anticipated log growth and retention posture.
4. **Benefits.** Bounds hot-table growth; cheaper cold storage.
5. **Risks.** Premature at projected volumes (low seven figures after year one); retention DELETEs plus pg_cron jobs (v1.0.x window) deliver the same bound without new structure; an archive tier is operational surface a 50-customer SaaS does not need.
6. **Migration impact.** Medium when eventually built.
7. **Application impact.** Audit readers gain a second source.
8. **Backward compatibility.** N/A.
9. **Recommendation: DEFER** to v1.1+, triggered by measured log growth or vacuum pressure — the same revisit trigger documented for partitioning.

### T3 — County lookup table

1. **Current design.** `county` is free text on `organizations`, `facilities`, `suppliers`, `consultant_profiles`.
2. **Proposed design.** A lookup of 26 ROI + 6 NI + UK ceremonial counties with FKs.
3. **Why the change is needed.** Normalisation instinct from the audit.
4. **Benefits.** Clean faceting, if anything ever faceted on county.
5. **Risks.** Nothing in v1.0 or v1.1 computes from `county` — it is display data in both markets; neither Royal Mail nor Eircode routing requires it; imports Dublin city/county and Derry/Londonderry edge-case debt for zero consumers; a maintenance artefact in search of a requirement.
6. **Migration impact.** — (not adopted).
7. **Application impact.** Would force dropdown UX on four forms.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT** (low value, maintenance burden). County normalisation arrives free with the v1.1 address-verification loop; `county` stays free text.

---

## 4. Indexes

*The dump shows no indexes at all. Per the hardening plan's "action zero", the Supabase migration files must be inspected first: if an index layer already exists, each family below collapses from "build" to "verify against this list". All builds are CONCURRENT, each in its own transaction. Attributes 3–9 are shared across each family where identical and are stated once.*

### I1 — Tenant composite family: `customer_documents(organization_id, created_at DESC)`, `emissions_logs(organization_id, start_date)`, `suppliers(organization_id)`, `facilities(organization_id)`

1. **Current design.** No indexes visible in the dump on the four hot tenant tables' RLS-join paths.
2. **Proposed design.** Four B-tree indexes keyed on the tenant column, with the ordering column matching the dominant list/rollup query on the two pipeline tables.
3. **Why the change is needed.** Every customer screen and every RLS policy joins on `organization_id`; without these, document lists, emissions aggregations and supplier/facility pickers seq-scan growing tables, and RLS join evaluation degrades with them.
4. **Benefits.** Predictable p95 on the launch screens; efficient RLS-join evaluation; the emissions aggregation the UK reporting flow depends on becomes index-served.
5. **Risks.** Write amplification on the pipeline's hot path — four indexes is the disciplined minimum, not the blanket programme (I6); risk accepted.
6. **Migration impact.** Medium effort, Low risk: CONCURRENT builds; caveat — verify the migration files do not already contain them.
7. **Application impact.** None.
8. **Backward compatibility.** Fully compatible; indexes are transparent.
9. **Recommendation: APPROVE.**

### I2 — Queue-claim partial family: `document_processing_queue(status, created_at)`, `processing_queue(queue_status, …)`, `report_generation_queue` status path

1. **Current design.** No indexes visible on the worker-facing status columns (`document_processing_queue.status`, `processing_queue.queue_status`, both varchar nullable).
2. **Proposed design.** Partial B-trees on the claim predicate (status plus FIFO ordering), restricted to unclaimed/active statuses so the index stays small and hot.
3. **Why the change is needed.** Workers poll these queues continuously; an unindexed claim query is the single hottest read pattern in the system and seq-scans the whole history of completed work on every poll.
4. **Benefits.** Constant-time claim polling regardless of completed-row accumulation; worker throughput decoupled from table age.
5. **Risks.** Partial indexes must match the claim predicate exactly or are silently unused — a query-plan check (the plan's Gate 7) is the mitigation.
6. **Migration impact.** Medium/Low: CONCURRENT builds; migration-file verification caveat applies.
7. **Application impact.** None (the claim query already exists; the index serves it).
8. **Backward compatibility.** Fully compatible.
9. **Recommendation: APPROVE.**

### I3 — Messaging/notifications family: `messages(conversation_id, created_at)`, `conversation_participants(conversation_id, user_id)`, unread-notifications partial

1. **Current design.** No indexes visible on `messages.conversation_id` (nullable), `conversation_participants`, or `notifications` (`is_read`/`recipient_id` drive the badge count).
2. **Proposed design.** Three indexes: the conversation-timeline composite, the participant-lookup composite, and a partial on unread notifications by recipient.
3. **Why the change is needed.** The support-chat thread view, participant resolution and notification badge are per-page-load queries in the committed v1.0 screens.
4. **Benefits.** Thread rendering and badge counts index-served; participant joins stop seq-scanning.
5. **Risks.** Minimal write cost on moderate-volume tables.
6. **Migration impact.** Medium/Low: CONCURRENT builds; verification caveat applies.
7. **Application impact.** None.
8. **Backward compatibility.** Fully compatible.
9. **Recommendation: APPROVE.**

### I4 — `consultant_firm_members.client_access` array GIN

1. **Current design.** `consultant_firm_members.client_access` is a uuid array (ADR-locked; junction-table replacement is rejected on ADR grounds) carrying client-access grants evaluated in RLS.
2. **Proposed design.** A GIN index on the array column.
3. **Why the change is needed.** A security predicate forced into an array by the ADR cannot B-tree; without GIN, every consultant RLS check seq-scans membership rows.
4. **Benefits.** The sole justified GIN in v1.0 (blanket-jsonb GIN stays rejected); consultant portal queries index-served.
5. **Risks.** GIN write amplification on updates — acceptable on a low-churn membership table.
6. **Migration impact.** Small; verification caveat applies.
7. **Application impact.** None.
8. **Backward compatibility.** Fully compatible.
9. **Recommendation: APPROVE.**

### I5 — `pg_trgm` family: `suppliers.name`/`.vat_number`, `organizations.name`

1. **Current design.** No trigram indexes; supplier/org pickers would do exact-prefix or seq-scan substring matching.
2. **Proposed design.** Trigram indexes on the three columns, backing autocomplete and "did you mean?" duplicate prompts.
3. **Why the change is needed.** Fuzzy supplier matching is the soft control complementing K5's hard identifier uniqueness — it prevents the "City Electrical 2" workaround pattern without outlawing legitimate same-name suppliers.
4. **Benefits.** Autocomplete UX; duplicate-nudging at entry; scoped to three columns, not the audit's programme.
5. **Risks.** Extension enablement and modest index size; nothing at launch volume.
6. **Migration impact.** Small; may land in the v1.0.x window rather than launch day — it serves UX, not correctness.
7. **Application impact.** Autocomplete/"did you mean?" UX consumes the indexes (application work).
8. **Backward compatibility.** Fully compatible.
9. **Recommendation: APPROVE** (v1.0.x window acceptable).

### I6 — Blanket "index every FK" programme (~60 indexes)

1. **Current design.** The dump's silence tempts the conclusion that every FK needs an index.
2. **Proposed design.** The audit's blanket: index all FK columns across ~90 tables.
3. **Why the change is needed.** FK-write performance and join coverage, in the abstract.
4. **Benefits.** Complete join coverage in theory.
5. **Risks.** ~3× over-scoped: write-amplifying indexes on dozens-of-rows static reference tables (`units`, `glossary`, `roles`, `document_types`) the planner will never choose, on marketing tables being purged at GA (`waitlist`, `beta_users`, `beta_access_codes`), and on FKs that are never query entry points; every unnecessary index is permanent write cost on the pipeline's hot path.
6. **Migration impact.** Large, for negative net value.
7. **Application impact.** Slower writes everywhere.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT.** The principle (index real query paths) is honoured by I1–I5 plus the UNIQUE-backed indexes of K5; the blanket is not. Non-entry-point FK indexes are revisited evidence-gated in v1.1 against query logs.

---

## 5. Constraints

*The dump shows no CHECK constraints or NOT NULL beyond the markers noted; the staging data audit (NULL counts, duplicate sweeps, value mapping) precedes every constraint below, and all CHECKs are added in the non-validating-then-validate style to avoid table locks. The frozen decision stands: the database enforces exactly four validation shapes — IN-lists, ranges, presence, uniqueness. Formats live at the API layer (K9).*

### K1 — `country` IN ('GB','IE') on `organizations`, `facilities`, `suppliers`, `consultant_profiles`

1. **Current design.** All four `country` columns are unconstrained free text (varchar/text, nullable) — the seeds already show the failure mode, with `.de`/`.fr`/`.fi`/`.ai` users present (seed cleanup is data work, noted for context only).
2. **Proposed design.** CHECK IN ('GB','IE') on the four columns, after auditing existing values to the list. No new `country_code` column — constraining the existing single source of truth is the fix; a parallel ISO column would be a second source of truth kept in sync with the first (rejected diagnosis-right-prescription-wrong in the hardening plan, and rejected again here).
3. **Why the change is needed.** Every jurisdiction rule — currency defaults, validation selection, factor `country` selection (C4), reporting defaults — keys off this value; under UK-primary/IE-beta the launch market set is exactly two codes, and the list must be machine-readable, not convention.
4. **Benefits.** Jurisdiction logic reads a guaranteed value; adding IE depth in v1.1 needs no schema change (the list already contains 'IE'); out-of-market rows become impossible at the database.
5. **Risks.** Existing non-conforming values block the constraint — the staging audit handles; "UK"/"England" variants need mapping to 'GB' first.
6. **Migration impact.** Small: audit, map, constrain four columns. Verification caveat: dump shows no existing CHECKs.
7. **Application impact.** Onboarding country pickers constrain to GB/IE (aligned with the product decision); error surfaces for rejected writes.
8. **Backward compatibility.** Rejects writes previously allowed — intentional; no legitimate v1.0 value is excluded.
9. **Recommendation: APPROVE.**

### K2 — Currency IN ('GBP','EUR') on the six currency columns + `system_settings.default_currency`

1. **Current design.** Unconstrained currency columns on `organizations.currency`, `suppliers.payment_currency`, `document_processing_queue.billing_currency`, `customer_subscriptions.currency`, `manual_extraction_batches.currency`, `consultant_profiles.revenue_currency`, plus `system_settings.default_currency`; C3 adds the missing seventh on `consultant_billing`.
2. **Proposed design.** CHECK IN ('GBP','EUR') on all seven, after value audit; EUR default applied at the application layer when `country='IE'` (application work, noted for context).
3. **Why the change is needed.** Every aggregation, Stripe reconciliation and spend-based calculation keys off currency; a third code in any of seven columns silently breaks money maths in a two-currency launch.
4. **Benefits.** Denominated, reconcilable money across the whole billing surface; GBP-primary/EUR-beta exactly matches the market decision.
5. **Risks.** Value-mapping risk only; low.
6. **Migration impact.** Small.
7. **Application impact.** Currency selectors constrain; defaulting logic at onboarding.
8. **Backward compatibility.** Intentionally rejects out-of-list writes; no legitimate v1.0 value excluded.
9. **Recommendation: APPROVE.**

### K3 — Range CHECKs ≥ 0 on emission quantities, factors and counters

1. **Current design.** `emissions_logs.raw_quantity` and `.calculated_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_scope1/2/3` and `.emission_factor_scope1/2/3`, `supplier_categories.default_emission_factor` are all unconstrained numerics.
2. **Proposed design.** CHECK (value >= 0) on each; companion non-negative CHECKs on money/usage counters (`usage_tracking.*`, subscription price/usage ints) in the same batch.
3. **Why the change is needed.** One negative `calculated_kg_co2e` silently corrupts every SECR total it enters; nothing fails loudly — the report is simply wrong.
4. **Benefits.** The core number is range-protected at the database; pipeline bugs surface as write errors instead of wrong reports.
5. **Risks.** A legitimate correction workflow might want negative adjustment lines — the adjustment pattern is a positive quantity with a sign/flag, confirmed at design; risk accepted and documented.
6. **Migration impact.** Small: value audit then CHECKs.
7. **Application impact.** Write paths surface validation errors; extraction pipeline guards negatives.
8. **Backward compatibility.** Rejects previously-allowed negatives — intended; none legitimate.
9. **Recommendation: APPROVE.**

### K4 — Status/role CHECK value lists on five queue/billing/role columns

1. **Current design.** Free-text status columns: `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status` (all varchar/text, nullable).
2. **Proposed design.** CHECK value lists on these five, scoped from the application enumerations; the remaining ~20 free-text statuses defer to v1.1.
3. **Why the change is needed.** Status typos on queue and billing columns become silent states workers and limit-checks miss — a stuck document no queue ever claims, a subscription no limit logic recognises.
4. **Benefits.** Closed state sets on the columns whose wrongness is invisible; CHECKs chosen over PG enums deliberately (enums are migration-hostile; the frozen D8 decision).
5. **Risks.** Every new legitimate state requires a migration — accepted as the cost of a closed set on five columns only.
6. **Migration impact.** Small: value-mapping audit first.
7. **Application impact.** Centralised status constants verified against the lists.
8. **Backward compatibility.** Rejects out-of-list writes — intended.
9. **Recommendation: APPROVE.**

### K5 — Uniqueness set

1. **Current design.** No UNIQUE on: `organization_members(organization_id, user_id)`; `consultant_clients(consultant_id, organization_id)`; `usage_tracking(organization_id, usage_month)`; `report_versions(report_id, version_number)`; supplier identifiers (`suppliers.vat_number`, `.company_number` unconstrained); the factor table (duplicate `(reporting_year, activity_type)` rows possible — silently double-counted factors).
2. **Proposed design.** UNIQUE constraints on the four composites; partial UNIQUEs on `suppliers(organization_id, vat_number)` and `(organization_id, company_number)` WHERE NOT NULL; and — after C4 — UNIQUE on `emission_factors(reporting_year, activity_type, country)`. A name-unique on suppliers is explicitly **not** included (legitimate same-name suppliers exist; the trigram "did you mean?" of I5 is the soft control).
3. **Why the change is needed.** Duplicate memberships corrupt RLS semantics; duplicate usage months split billing allowances; duplicate report versions make `is_current` ambiguous; duplicate factors double-count the product's core number; duplicate supplier identifiers are amplified by `ai_mapped_supplier_id` into emissions data.
4. **Benefits.** One row per real-world fact across the five highest-blast-radius relationships.
5. **Risks.** Pre-existing duplicates block the constraints — the staging dedupe sweep gates; partials avoid penalising NULL-heavy legitimate rows.
6. **Migration impact.** Medium: dedupe audit, then six constraints; each UNIQUE-backed index also serves its lookup path (counted here, not in §4).
7. **Application impact.** Duplicate submissions surface 409s with resolution UX.
8. **Backward compatibility.** Rejects duplicates previously allowed — intended.
9. **Recommendation: APPROVE.**

### K6 — Drop UNIQUE on `password_reset_tokens.user_id`; keep UNIQUE on `token`

1. **Current design.** `password_reset_tokens.user_id` is Nullable **Unique**; `token` is Unique.
2. **Proposed design.** Drop the `user_id` uniqueness; retain `token` uniqueness; latest-valid-wins semantics in the application.
3. **Why the change is needed.** One-reset-per-user uniqueness creates an unauthenticated reset-DoS: cycling reset requests continuously invalidates a victim's genuine token, and repeat legitimate requests error.
4. **Benefits.** DoS closed; multiple outstanding tokens with latest-wins is the standard posture.
5. **Risks.** Multiple live tokens per user — bounded by `expires_at` and the used-flag lifecycle.
6. **Migration impact.** Small: one constraint drop. (Token *hashing* rides the same migration but is data/security work, not structure.)
7. **Application impact.** Reset flow issues freely, validates latest.
8. **Backward compatibility.** Relaxes a constraint — safe direction.
9. **Recommendation: APPROVE.**

### K7 — Backfill then NOT NULL `organization_id` on six hot tenant tables

1. **Current design.** `organization_id` is nullable on `conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications` (confirmed in the dump), while the pipeline tables (`customer_documents`, `processing_queue`, `document_processing_queue`, `emissions_logs`, `suppliers`, `facilities`) already carry it NOT NULL.
2. **Proposed design.** Backfill from parent rows (e.g. `messages` via `conversation_id`), verify zero NULLs, then NOT NULL on all six.
3. **Why the change is needed.** A NULL-`organization_id` row falls outside every tenant-equality RLS policy: invisible-to-all or visible-through-exception — a tenancy hole reachable by one forgotten insert, no attacker required.
4. **Benefits.** Uniform tenant keying across the hot surface; RLS policies become total functions.
5. **Risks.** Backfill correctness on orphaned rows (parent missing) — staging audit enumerates; un-backfilling is impossible, so the pre-migration snapshot is mandatory.
6. **Migration impact.** Medium: backfill → verify → constrain, snapshot retained. Cheap pre-launch, painful after.
7. **Application impact.** Insert paths must always set `organization_id` — code inspection evidence.
8. **Backward compatibility.** Rejects NULL-org writes previously allowed — intended.
9. **Recommendation: APPROVE.**

### K8 — NOT NULL + DEFAULT on hot booleans/processing timestamps

1. **Current design.** Hot-path flags and processing timestamps are broadly nullable — e.g. `customer_documents.status`, `document_processing_queue.status`/`qc_required`/`customer_approved`, `processing_queue.queue_status`/`sla_breached`, `emissions_logs` processing timestamps, and the new `organizations.is_active` (C2).
2. **Proposed design.** Backfill, then NOT NULL with sensible DEFAULTs on the named hot subset only; the broad ~80-column sweep stays deferred to v1.1.
3. **Why the change is needed.** A NULL on a hot-path flag or processing timestamp is an ambiguous third state workers and suspend logic silently misread.
4. **Benefits.** Two-state booleans on the paths that branch on them; defaults make inserts self-consistent.
5. **Risks.** Backfill semantics per column (NULL → false vs true) must be chosen deliberately; staging audit enumerates.
6. **Migration impact.** Small: backfill then constrain, scoped list.
7. **Application impact.** None beyond honest tri-state removal.
8. **Backward compatibility.** DEFAULTs preserve insert behaviour; NULL writes rejected — intended.
9. **Recommendation: APPROVE.**

### K9 — Country-conditional regex CHECKs (VAT, postcode, Eircode, phone, email, CH/CRO numbers)

1. **Current design.** Format validation currently lives nowhere in the database (correctly).
2. **Proposed design.** The audit's matrix of format regex CHECKs, including a frozen Eircode routing-key allowlist.
3. **Why the change is needed.** Asserted as defence-in-depth.
4. **Benefits.** None net of the API-layer pack.
5. **Risks.** Frozen decision, confirmed under the layering rule: the database protects integrity; the API owns format. DB regexes reject valid edge cases, cannot express per-country rules well, and rot as registries change — the Eircode routing-key list is a living third-party registry whose freezing into a CHECK guarantees a future migration to admit a legitimate Irish address. Beta-level IE validation (Eircode shape) is precisely the API-layer pack.
6. **Migration impact.** — (not adopted).
7. **Application impact.** The API validation pack (MOD97 VAT, GIR postcode, Eircode shape + routing-key list, libphonenumber) ships in the application — noted for context, not a structural recommendation.
8. **Backward compatibility.** N/A.
9. **Recommendation: REJECT** (frozen decision; layering rule). The four database validation shapes — IN-lists, ranges, presence, uniqueness — are all delivered by K1–K8.

---

## 6. Foreign Keys

*The dump shows no foreign key definitions at all. A verify-first posture is mandatory: the Supabase migration files must be inspected before any FK work is scored or scheduled (the hardening plan's Gate 1). The two items below are therefore (a) the inventory itself and (b) conditional remediation.*

### F1 — Verify-first full FK inventory; add missing FKs implied by the dump

1. **Current design.** The schema implies dozens of relationships the dump cannot confirm as enforced — e.g. `emissions_logs.defra_factor_id` → the factor table, `emissions_logs.asset_id` → `assets`, `customer_documents.supplier_id`/`.document_type_id`/`.organization_member_id`, `document_processing_queue.ai_mapped_facility_id`/`.ai_mapped_asset_id`/`.ai_mapped_supplier_id`, `messages.conversation_id`, `report_versions.report_id`, and `emissions_logs.unit` → `units.code` once C5 lands.
2. **Proposed design.** Produce the complete FK inventory from the migration files; where a relationship the dump implies is genuinely unenforced, add the FK (non-validating add then validate) — prioritising the AI-mapping columns and the factor reference, whose orphan rows poison emissions data.
3. **Why the change is needed.** Unenforced references permit orphaned emissions rows — a `supplier_id` pointing nowhere, an AI-mapped asset that no longer exists — landing silently in reported figures. The product cannot launch without *knowing* which of these are real.
4. **Benefits.** Referential integrity on the paths that feed reported numbers; the inventory itself is launch evidence.
5. **Risks.** Discovery risk: findings may force data cleanup before constraints validate; that discovery is the point, and pre-launch is the cheapest time for it.
6. **Migration impact.** Medium: inspection (Gate 1), then per-FK adds with validation; orphan cleanup where found. The entire item is caveat-conditioned on what the migration files contain.
7. **Application impact.** Write paths must satisfy the FKs (order-of-insert discipline); error surfaces for rejected orphans.
8. **Backward compatibility.** Rejects orphan writes previously possible — intended.
9. **Recommendation: APPROVE** (as a verification gate with conditional remediation — verification is the launch blocker, remediation only where inspection proves absence).

### F2 — ON DELETE behaviour corrections

1. **Current design.** Unknown — no ON DELETE actions are visible in the dump. The dangerous shapes to hunt: CASCADE from `organizations` or `users` into financial/audit tables (`customer_subscriptions`, `consultant_billing`, `audit_trail`, `emissions_logs`), and CASCADE into `report_versions` from `report_id`.
2. **Proposed design.** Where inspection proves a dangerous CASCADE, convert to RESTRICT (or NO ACTION with an explicit application delete path) on financial and audit tables; retain CASCADE only where child rows are truly owned and valueless without the parent (e.g. session-scoped rows).
3. **Why the change is needed.** Delete behaviour is currently unverifiable; one unconsidered CASCADE from a tenant delete could erase the audit evidence the product exists to preserve, and hard delete is already structurally near-impossible against ~40 references (hence the anonymise-in-place erasure runbook — application/compliance work, noted for context).
4. **Benefits.** Deletes become deliberate; financial and audit history cannot vanish as a side effect; the erasure runbook's FK graph is confirmed rather than assumed.
5. **Risks.** RESTRICT converts silent cascades into explicit failures — application delete flows must handle the rejection; that friction is the control working.
6. **Migration impact.** Medium, conditional: only where inspection proves danger; each correction is a small constraint swap after dependent-row review.
7. **Application impact.** Admin/erasure delete paths gain explicit ordering; support runbooks updated.
8. **Backward compatibility.** Stricter delete behaviour — intended; no read-path change.
9. **Recommendation: APPROVE** (conditional on F1's inspection; no speculative rewrites of behaviour that may already be correct).

---

*End of review. Register totals restated for verification: 3 renames (§1) + 15 column items (§2) + 3 table items (§3) + 6 index items (§4) + 9 constraint items (§5) + 2 foreign-key items (§6) = 38 changes; 28 APPROVE, 4 DEFER (C11, C12, C13, T2), 6 REJECT (C14, C15, T1, T3, I6, K9). Section subsection counts match the Summary Register row-for-row.*
