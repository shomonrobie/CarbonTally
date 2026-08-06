# CarbonTally — Architecture Freeze (RC2) Approval Document

*Final implementation specification for approval before any further migration work. United Kingdom (primary launch) · Ireland (beta) · Supabase / PostgreSQL 16 · multi-tenant RLS. Compiled from the Production Readiness Review, Production Hardening Plan, Structural Change Review, Management Approval Report and the RC1 migration package. No SQL, migrations or application code are included; every approved change is justified with business reason, technical reason, migration impact and long-term maintenance implications.*

## Section 1 — Final Approved Database Structure

This register freezes, as RC2, every structural change approved for the CarbonTally v1.0 launch (UK primary, Ireland beta) on Supabase/PostgreSQL 16. It is compiled from the Structural Change Review (28 APPROVE items: R1–R3, C1–C10, I1–I5, K1–K8, F1–F2), expanded into concrete physical change units, and includes the structural-adjacent approved items shipped in the RC1 package (RLS hardening, the erasure procedure, `updated_at` triggers, extensions). Identifiers RC2-001 … RC2-041 are unique, sequential and in logical implementation order: renames first, then columns, constraints, foreign keys, indexes, and finally RLS/functions/triggers/extensions. The five-year maintainability lens applies throughout: every name, key and constraint below is one the platform can still defend in year five without a redesign migration.

### 1.1 Renames

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-001 | Rename (table) | `defra_conversion_factors` → `emission_factors`; jurisdiction-neutral name is the cheapest of the three v1.1-Ireland enablers and the one whose cost grows fastest with time | Low technical, moderate completeness (every query/ORM/seed reference must move in one coordinated deploy) | Yes | No (atomic rename; no dual-name period) | P1 |
| RC2-002 | Rename (column) | `emissions_logs.defra_factor_id` → `emission_factor_id`; the factor-read path must not freeze a jurisdiction-specific lie into the hottest consumer table | Low; wider search-and-replace across reporting, exports and pipeline | Yes | No | P1 |
| RC2-003 | Rename (column) | `document_processing_queue.defra_factor_used` → `emission_factor_used` and `manual_extraction_items.defra_factor_used` → `emission_factor_used`; companion to RC2-002 — splitting buys nothing; both columns share the same factor-reference semantics and leaving the manual-extraction column behind would strand one `defra_*` name on the manual path the R2 rename was designed to clean up | Low | Yes | No | P1 |
| RC2-004 | Rename (column) | `organizations.default_defra_version` → `default_factor_year`; aligns with the already-neutral `system_settings.default_emission_factor_year`; read by Irish beta tenants on day one | Trivial; few readers (onboarding defaults, report generation) | Yes | No | P1 |
| RC2-005 | Rename (retirement) | `emission_factors.region` → `region_deprecated` (non-destructive); values folded into the new `country` column so the factor table carries one jurisdiction column, not two | Low; non-destructive reversal is a single rename back | Yes | Partial (old data preserved under a new name; readers must switch to `country`) | P1 |

The renames are deliberately grouped in one release: they are atomic, mutually dependent, and breaking only for pre-launch code (no external consumers exist). Migration-file inspection must confirm no view, function or RLS policy references any old name — the schema dump is silent on all three.

### 1.2 Columns

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-006 | Column | Add nullable `facilities.eircode` (varchar); Ireland has no postcodes — without it an Irish beta user physically cannot create the facility whose emissions the product measures | Low; additive | No | Yes | P1 |
| RC2-007 | Column relaxation | Drop `facilities.postcode` NOT NULL; paired with RC2-006 and closed by the presence CHECK (RC2-018) | Widens state space; the presence CHECK closes the only harmful new state (both NULL) | No | Partial (readers assuming non-NULL `postcode` must tolerate NULL — small audit) | P1 |
| RC2-008 | Column | Add `organizations.is_active` (boolean, NOT NULL, default true, backfilled true); a reversible, evidence-preserving tenant off-switch — the alternative is deleting audit evidence | New flag must be enforced everywhere to mean anything; default-true backfill makes rollout safe | No | Yes | P1 |
| RC2-009 | Column | Add `organizations.archived_at` (timestamptz, nullable); lifecycle timestamp companion to RC2-008 | Low; additive | No | Yes | P1 |
| RC2-010 | Column | Add `consultant_billing.currency` (varchar; defaulted and backfilled 'GBP', then constrained by RC2-020); the only billing table without a currency in a two-currency launch | Backfill assumption (GBP) must be validated against existing rows — near-zero pre-launch | No | Yes (existing rows default to GBP, matching UK-primary reality) | P1 |
| RC2-011 | Columns | Add five `emission_factors` provenance columns: `unit`, `scope`, `factor_source`, `factor_set`, `country` (backfilled 'GB', 'DEFRA-DESNZ'); makes every factor self-describing and carries jurisdiction as a column — the structural hook that makes v1.1 Ireland a data load, not a migration | Low; five nullable adds plus a one-statement backfill; unit strings are free text by design (a units lookup is over-modelling at two jurisdictions) | No | Yes | P1 |
| RC2-012 | Columns | Add `emissions_logs.unit` (FK to `units.code` via RC2-030) and `emissions_logs.scope`; SECR kWh totals and scope rollups become computable without the factor join — a UK-primary reporting fix | Derived backfill via the factor join could mislabel history; staging data audit gates it | No | Yes (readers ignoring the columns behave as today) | P1 |
| RC2-013 | Column | Add nullable `customer_documents.file_checksum` (SHA-256 hex); deterministic duplicate detection on the entity that drives AI extraction spend; no UNIQUE in v1.0 | None structural; application must hash at upload | No | Yes | P2 |
| RC2-014 | Type widening | `file_attachments.file_size` int4 → int8, matching the pipeline peers; eliminates ~2.1 GB overflow at the customer's highest-value moment | Table rewrite — trivial at seed-scale rows now, Large if deferred a year; the reason it ships now | No | Yes (widening is value-compatible) | P1 |
| RC2-015 | Column | Add nullable `suppliers.sort_code` (varchar, normalised digits-only); completes UK domestic banking capture to pair with the existing `iban` (IE) | One more banking-PII column for the PII register; masking is API-layer | No | Yes | P1 |
| RC2-016 | Column | Add nullable `facilities.meter_mpan_mprn` (varchar); enables future bill-to-facility matching for both markets (MPAN GB; MPRN GB-gas and IE-gas) | Free-format identifier invites inconsistent entry — mitigated by API normalisation, not a CHECK (K9 layering rule) | No | Yes | P2 |
| RC2-017 | Columns | Add nullable `organization_metadata.total_floor_area_sqm` / `.occupied_floor_area_sqm` alongside the existing sqft columns; prevents Irish beta users entering m² into sqft-labelled columns and silently corrupting intensity ratios by ~10.8× | Two parallel unit-labelled columns invite drift — bounded by the API write rule (populate per org country default) | No | Yes | P2 |

All twelve column items are additive or value-compatible; none rewrites data except RC2-014 (a deliberate, pre-emptive widening while the table is young). The C4 provenance set (RC2-011) and C5 pair (RC2-012) are the audit-correctness core of the release: unauditable numbers are the worst defect class in a carbon product.

### 1.3 Constraints

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-018 | Constraint (presence) | CHECK on `facilities` requiring at least one of `postcode`/`eircode`; guarantees every facility row carries a locatable identifier for either market | Country-conditional XOR was rejected (`facilities.country` is nullable; the API owns the per-country rule) | No | Partial (one new rejection case — both NULL — that no legitimate UK row can hit) | P1 |
| RC2-019 | Constraint (IN-list) | `country IN ('GB','IE')` on five columns: `organizations`, `facilities`, `suppliers`, `consultant_profiles`, `emission_factors.country`; every jurisdiction rule keys off a machine-readable value | Existing non-conforming values ('UK', seed `.de`/`.fr` rows) block the constraint — staging audit and value mapping first | Yes (rejects previously allowed writes) | Partial (intentional; no legitimate v1.0 value excluded) | P1 |
| RC2-020 | Constraint (IN-list) | `currency IN ('GBP','EUR')` on eight columns (the seven existing currency columns plus `system_settings.default_currency`, now including RC2-010's new column); a third code anywhere silently breaks money maths | Value-mapping risk only ('£'-style variants mapped to 'GBP') | Yes | Partial (intentional) | P1 |
| RC2-021 | Constraint (range) | CHECK (value >= 0) on 27 emission-quantity, factor, money/usage-counter and file-size columns; one negative `calculated_kg_co2e` silently corrupts every SECR total it enters | Legitimate negative adjustment lines are replaced by the signed-row correction pattern — accepted and documented | Yes (rejects negatives) | Partial (intentional; none legitimate) | P1 |
| RC2-022 | Constraint (range) | CHECK 0–100 on seven confidence/percentage columns; bounds the AI-extraction scoring surface | Assumes 0–100 storage; if the staging audit finds 0–1, bounds are revisited before VALIDATE | Yes | Partial (conditional on the storage-scale audit) | P1 |
| RC2-023 | Constraint (IN-list) | Status/role value lists on five columns (`processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status`); closes silent stuck-state and unrecognised-subscription failure modes; CHECKs chosen over PG enums deliberately (enums are migration-hostile) | Every new legitimate state requires a migration — accepted as the cost of a closed set on five columns only; vocabulary must be reconciled against app constants before VALIDATE | Yes | Partial (intentional) | P1 |
| RC2-024 | Constraint (uniqueness) | Four composite UNIQUEs: `organization_members(organization_id, user_id)`, `consultant_clients(consultant_id, organization_id)`, `usage_tracking(organization_id, usage_month)`, `report_versions(report_id, version_number)`; duplicate memberships corrupt RLS semantics, duplicate months split billing, duplicate versions make `is_current` ambiguous | Pre-existing duplicates block the constraints — staging dedupe sweep gates | Yes (rejects duplicates) | Partial (intentional) | P1 |
| RC2-025 | Constraint (uniqueness, partial) | Partial UNIQUEs on `suppliers(organization_id, vat_number)` and `(organization_id, company_number)` WHERE NOT NULL; duplicate supplier identifiers are amplified by `ai_mapped_supplier_id` into emissions data; a name-unique is explicitly excluded (trigram soft control instead) | Partials avoid penalising NULL-heavy legitimate rows; dedupe sweep gates | Yes | Partial (intentional) | P1 |
| RC2-026 | Constraint (uniqueness) | UNIQUE on `emission_factors(reporting_year, activity_type, country)` — the natural key made possible by RC2-011; duplicate factors double-count the product's core number | Depends on RC2-001/RC2-011 landing first; per-country keying verified by the IE fixture test | Yes | Partial (intentional) | P1 |
| RC2-027 | Constraint (relaxation) | Drop UNIQUE on `password_reset_tokens.user_id`; retain UNIQUE on `token`; closes the unauthenticated reset-DoS where cycling requests invalidate a victim's genuine token | Multiple live tokens per user — bounded by `expires_at` and the used-flag lifecycle; latest-valid-wins is application work | No (relaxes a constraint — safe direction) | Yes | P1 |
| RC2-028 | Constraint (NOT NULL) | Backfill from parent rows, verify zero NULLs, then NOT NULL `organization_id` on six hot tenant tables (`conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications`); a NULL-`organization_id` row falls outside every tenant-equality RLS policy — a tenancy hole reachable by one forgotten insert | Backfill correctness on orphaned rows; un-backfilling is impossible, so the pre-migration snapshot is mandatory | Yes (rejects NULL-org writes) | Partial (intentional) | P1 |
| RC2-029 | Constraint (NOT NULL + DEFAULT) | Backfill then NOT NULL with sensible DEFAULTs on the named hot subset only: `customer_documents.status`, `document_processing_queue.status`/`qc_required`/`customer_approved`, `processing_queue.queue_status`/`sla_breached` (plus RC2-008's `is_active`); a NULL on a hot-path flag is an ambiguous third state workers misread | Backfill semantics per column (NULL → false vs true) must be chosen deliberately; the broad ~80-column sweep stays deferred to v1.1 | Yes (explicit-NULL inserts now fail; defaults preserve normal inserts) | Partial | P1 |

The frozen constraint philosophy stands: the database enforces exactly four validation shapes — IN-lists, ranges, presence, uniqueness. All CHECKs are added non-validating then validated to avoid table locks, and the staging data audit (NULL counts, duplicate sweeps, value mapping) precedes every entry above.

### 1.4 Foreign Keys

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-030 | Foreign keys (verify-first) | Full FK inventory from the migration files, then add the missing FKs implied by the dump — 11 in the RC1 set (factor, asset and `units.code` references; document/supplier/member references; four AI-mapping hints; `messages.conversation_id`), all NOT VALID + VALIDATE with ON DELETE NO ACTION or SET NULL; unenforced references permit orphaned emissions rows landing silently in reported figures | Discovery risk: findings may force data cleanup before constraints validate — that discovery is the point, and pre-launch is the cheapest time for it | Yes (rejects orphan writes) | Partial (intentional) | P1 |
| RC2-031 | Foreign keys (delete behaviour) | Where inspection proves a dangerous CASCADE from `organizations`/`users` into financial or audit tables, convert to RESTRICT (or NO ACTION with an explicit application delete path); retain CASCADE only for truly owned session-scoped rows | Conditional: no speculative rewrites of behaviour that may already be correct; RESTRICT converts silent cascades into explicit failures — that friction is the control working | Yes (stricter deletes) | Partial (intended; no read-path change) | P2 |

Both FK items are verify-first: the dump shows no FK definitions at all, so the migration-file inspection ("action zero") is a precondition, and each addition collapses to a no-op where enforcement already exists.

### 1.5 Indexes

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-032 | Index family | Four tenant composites: `customer_documents(organization_id, created_at DESC)`, `emissions_logs(organization_id, start_date)`, `suppliers(organization_id)`, `facilities(organization_id)`; every customer screen and every RLS policy joins on `organization_id` | Write amplification on the hot path — four indexes is the disciplined minimum (the ~60-index blanket stays rejected) | No | Yes | P1 |
| RC2-033 | Index family | Three queue-claim partials (`document_processing_queue`, `processing_queue`, `report_generation_queue`) restricted to unclaimed/active statuses; worker claim polling is the hottest read pattern in the system and must not seq-scan completed history | Partial indexes must match the claim predicate exactly or are silently unused — Gate 7 query-plan check is the mitigation | No | Yes | P1 |
| RC2-034 | Index family | Three messaging/notifications indexes: `messages(conversation_id, created_at)`, `conversation_participants(conversation_id, user_id)`, unread-notifications partial; thread rendering, participant resolution and badge counts are per-page-load queries in committed v1.0 screens | Minimal write cost on moderate-volume tables | No | Yes | P2 |
| RC2-035 | Index | GIN on `consultant_firm_members.client_access` (uuid array, ADR-locked); a security predicate forced into an array cannot B-tree — without GIN every consultant RLS check seq-scans | GIN write amplification on updates — acceptable on a low-churn membership table | No | Yes | P1 |
| RC2-036 | Index family | `pg_trgm` trigram indexes on `suppliers.name`, `suppliers.vat_number`, `organizations.name`; fuzzy matching is the soft duplicate control complementing RC2-025 and backs autocomplete UX | Extension enablement and modest index size; may land in the v1.0.x window — it serves UX, not correctness | No | Yes | P3 |
| RC2-037 | Index family | Four FK-supporting B-trees backing the RC2-030 reference paths whose parent-side deletes and joins would otherwise seq-scan | Low; CONCURRENT builds | No | Yes | P2 |

All index builds are CONCURRENT, each in its own transaction — the index migration file is deliberately non-transactional and must never be wrapped by a transaction-forcing runner. The dump shows no indexes at all; if the migration files already contain some, each family collapses from "build" to "verify against this list".

### 1.6 Structural-adjacent approved items (RLS, functions, triggers, extensions)

| Change ID | Category | Reason | Risk | Breaking? | Backward compatible? | Priority |
|---|---|---|---|---|---|---|
| RC2-038 | Extensions | Enable `pg_trgm` (prerequisite for RC2-036) and `pgcrypto` (required by `anonymise_user()` for the erasure email hash), both `IF NOT EXISTS` | Low; platform-managed extensions on Supabase | No | Yes | P1 |
| RC2-039 | RLS hardening | Enable RLS across the tenant surface (~160 policies: 36 tenant tables × 4 CRUD + `organizations`/`users`/`notifications` specials + 10 reference-table reads) backed by helper functions `is_org_member(uuid)` and `is_org_active(uuid)`; write policies require `organizations.is_active = true`; organisation creation stays service-role only | The largest application risk in the release: any code path connecting as `authenticated` without a logged-in user now reads/writes zero rows; workers and cron must use the service role | Yes | No (deliberately changes access behaviour where previously absent) | P1 |
| RC2-040 | Function + triggers | `set_updated_at()` plus one BEFORE UPDATE trigger per mutable table carrying `updated_at` (up to 76; six append-only audit log tables deliberately excluded); keeps modification timestamps honest without application discipline | Low; per-row trigger overhead on hot tables accepted; skips with NOTICE where no `updated_at` exists | No | Yes | P2 |
| RC2-041 | Function (erasure) | `anonymise_user(uuid, uuid, text)` — GDPR anonymise-in-place erasure: hashes email to a `deleted-<sha256>@anonymised.invalid` mailbox, nulls credentials, deactivates the account and scrubs profile PII across consultant/staff/beta/feedback tables while preserving `users.id` and all FK references | Irreversible by design; invocation is guarded (self, active staff, or service context) and rehearsed end-to-end on staging (Gate 5) before production use | No (a procedure, not a schema change to read paths) | Yes (idempotent; no read-path change) | P1 |

### 1.7 Explicitly excluded from this freeze

The following review items are **not** in RC2 and remain out of scope for the launch schema. **DEFER — C11** (typed invoice columns on `customer_documents`): contradicts the frozen jsonb ADR's evidence-first promotion criterion and creates a two-sources-of-truth sync burden before production traffic exists; revisit in v1.1 against query logs. **DEFER — C12** (`emissions_logs.facility_id`): denormalisation drift risk; the genuine defect (nullable `asset_id`) is a write-path rule, not a column. **DEFER — C13** (`customer_documents.deleted_at` soft-delete): every document read path must change to make it safe; scheduled for the v1.0.x hardening window while the table is young. **DEFER — T2** (audit-archive table): premature at projected volumes; retention DELETEs plus scheduled jobs bound growth without new structure. **REJECT — C14** (per-user 2FA/lockout columns): conflicts with the frozen Supabase Auth ownership ADR — no parallel credential state in the application schema. **REJECT — C15** (`external_id`/integration columns): speculative identity with no sync contract (YAGNI); columns ship with the first integration contract, not before. **REJECT — T1** (`emission_factor_sets` table): over-modelling at two jurisdictions; RC2-011's columns carry the same semantics at a tenth of the cost. **REJECT — T3** (county lookup table): zero consumers in v1.0/v1.1; county normalisation arrives free with the v1.1 address-verification loop. **REJECT — I6** (blanket index-every-FK programme, ~60 indexes): ~3× over-scoped permanent write amplification; real query paths are served by RC2-032…RC2-037 plus the UNIQUE-backed indexes of RC2-024…RC2-026. **REJECT — K9** (country-conditional regex CHECKs): the layering rule is frozen — formats (VAT, postcode, Eircode routing keys, phone, email, company numbers) live in the API validation pack; the database enforces only IN-lists, ranges, presence and uniqueness.

---


## Section 2 — Column Review

*Every table and every column in the schema dump (`database.txt`) has been reviewed. Coverage: **100 tables**, grouped into 14 schema areas below. Verdict vocabulary: KEEP / RENAME / REMOVE / MERGE / SPLIT / NORMALIZE. Tables that are entirely KEEP are presented as a single compact row; any table containing a non-KEEP verdict is enumerated column by column. Verdicts are consistent with the frozen Structural Change Review (renames R1–R3, columns C1–C10 approved; C11 typed invoice columns, T3 county lookup and the jsonb ADRs remain rejected/deferred and are not resurrected here). Approved new columns (C1–C10) are shown as KEEP rows marked "(approved add)". Timing is stated on every non-KEEP verdict.*

### 2.1 Organisations & membership (6 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `organizations` | `id`, `name`, `company_number`, `created_at`, `updated_at`, `logo_url`, `industry`, `sector`, `company_size`, `vat_number`, `registration_number`, `country`, `timezone`, `currency`, `financial_year_end`, `reporting_standard`, `secr_enabled`, `esrs_enabled`, `issb_enabled`, `preferred_units`, `website`, `primary_contact_email`, `primary_contact_name`, `billing_contact_email`, `billing_contact_name`, `subscription_status`, `trial_start_date`, `trial_end_date`, `subscription_tier`, `subscription_id`, `billing_address`, `tax_rate`, `metadata`, `address_line1`, `address_line2`, `city`, `county`, `postcode`, `eircode`, `language`, `locale`, `vat_registered`, `registration_region`, `sic_code`, `naics_code`, `nace_code`, `business_structure`, `is_public`, `is_listed`, `isin`, `cik`, `sedol`, `lei`, `reporting_frequency`, `accounting_standard`, `sustainability_standard`, `carbon_tax_region`, `data_protection_officer`, `privacy_policy_url`, `terms_url` | KEEP | Core tenant record; GB/IE identifiers already dual-carried (`postcode`/`eircode`, `sic_code`/`nace_code`). |
| `organizations` | `default_defra_version` | RENAME | Approved **R3**: → `default_factor_year`. Jurisdiction-specific `defra` prefix on the one org setting an Irish beta tenant reads on day one; platform-level `system_settings.default_emission_factor_year` already uses neutral naming, so the old name is also internally inconsistent. RC2. |
| `organizations` | `registered_address` | MERGE | Free-text duplicate of the structured `address_line1`/`address_line2`/`city`/`county`/`postcode`/`eircode` block on the same row — two sources of truth for one fact. Fold into the structured columns; retire in v1.0.x. |
| `organizations` | `vat_region` | MERGE | Duplicates `tax_region` semantics (a fourth region column alongside `tax_region`, `registration_region`, `carbon_tax_region`). Fold into `tax_region`; retire in v1.0.x. |
| `organizations` | `tax_region` | KEEP | Canonical tax-jurisdiction column (merge target). |
| `organizations` | `is_active`, `archived_at` | KEEP (approved add C2) | Tenant lifecycle / evidence-preserving suspend path. |
| `organization_members` | — all columns | KEEP | Minimal membership join; `role` gains its K4 value-list CHECK (constraint, not a column change). |
| `organization_metadata` | `id`, `organization_id`, `total_employees`, `full_time_employees`, `part_time_employees`, `contract_employees`, `average_employees`, `annual_revenue`, `ebitda`, `total_assets`, `total_facilities`, `renewable_energy_percentage`, `carbon_offset_percentage`, `energy_intensity`, `reporting_standard`, `fiscal_year_start`, `fiscal_year_end`, `primary_contact_*`, `sustainability_officer_*`, `industry_sector`, `naics_code`, `sic_code`, `custom_metrics`, `created_at`, `updated_at`, `updated_by` | KEEP | One-to-one extension table correctly keeps the wide/org-profile payload off the hot `organizations` row. |
| `organization_metadata` | `total_floor_area_sqft`, `occupied_floor_area_sqft` | KEEP | Retained during transition; m² twins arrive via C10; sqft deprecation is v1.1 data/app work, not a column removal now. |
| `organization_metadata` | `total_floor_area_sqm`, `occupied_floor_area_sqm` | KEEP (approved add C10) | Prevents Irish beta users entering m² into sqft-labelled columns (~10.8× intensity error). |
| `roles` | — all columns | KEEP | Reference table; `permissions` jsonb per frozen ADR. |
| `pending_invites` | (table) `id`, `organization_id`, `email`, `role`, `created_at`, `updated_at` | MERGE | Duplicate of `user_invitations` (which is a strict superset: `token`, `status`, `expires_at`, `invited_by`, `role_id`). Merge target `user_invitations`; port `role` text into `role_id` resolution at the app layer. Timing: v1.0.x — pre-launch both tables are seed-scale, but two invite write paths must not reach production. |
| `user_invitations` | — all columns | KEEP | Canonical invitation table (merge target for `pending_invites`). |

### 2.2 Users, auth & beta (6 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `users` | — all columns | KEEP | Mirrors Supabase Auth; `password_hash` stays nullable and is never written (frozen C14 decision — platform owns credentials/2FA; no per-user auth columns are added). |
| `password_reset_tokens` | — all columns | KEEP | Column set correct; **K6** drops the UNIQUE on `user_id` (reset-DoS fix) — a constraint change, not a column verdict. |
| `beta_users` | — all columns | KEEP | Beta-gate table; whole-table retirement scheduled post-GA (v1.1 data purge) — no column change now. |
| `beta_access_codes` | — all columns | KEEP | As above; `magic_token`/`token_created_at` support the beta magic-link flow. |
| `waitlist` | — all columns | KEEP | Marketing capture; purged at GA (table-level decision, per I6 rationale). |
| `user_presence` | — all columns | KEEP | Ephemeral presence state; correctly minimal. |

### 2.3 Facilities & assets (2 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `facilities` | `id`, `organization_id`, `name`, `created_at`, `is_active`, `metadata`, `latitude`, `longitude`, `type`, `address_line1`, `address_line2`, `city`, `county`, `country`, `region`, `updated_at` | KEEP | `county` stays free text (frozen T3 rejection — no county lookup). `region` is a display-level free-text field here (distinct from the factor-table `region` retired under R1/C4). |
| `facilities` | `postcode` | KEEP | NOT NULL relaxed to nullable under **C1** (constraint change); Ireland has no postcodes. |
| `facilities` | `eircode` | KEEP (approved add C1) | Unblocks the Irish beta write path; presence CHECK guarantees postcode-or-eircode. |
| `facilities` | `meter_mpan_mprn` | KEEP (approved add C9) | Bill-to-site matching identifier; serves GB (MPAN/MPRN) and IE (MPRN). |
| `assets` | — all columns | KEEP | Correct child of `facilities`; `capacity`/`capacity_unit` pair is self-describing. |

### 2.4 Emissions, factors & activity reference (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `defra_conversion_factors` | (table) | RENAME | Approved **R1**: → `emission_factors`. The name hard-codes one national factor authority (UK DEFRA/DESNZ) into the platform's factor store; a rename on a live factor-referenced table is exactly what the "no major redesign in v1.1" rule exists to pre-empt, and pre-launch is the only cheap moment. RC2. |
| `defra_conversion_factors` | `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `created_at`, `updated_at` | KEEP | `co2e_multiplier` gains its K3 ≥ 0 CHECK and K5 uniqueness on `(reporting_year, activity_type, country)` — constraint work, no column change. (The doubled `updated_at` line in the dump is a dump artefact, per the structural review.) |
| `defra_conversion_factors` | `region` | RENAME (retire) | → `region_deprecated`. Half-does what C4's `country` does properly; values are mapped into `country` during the C4 backfill and the column is then retired, keeping a single jurisdiction column (single-source-of-truth stance, structural review §R1/§C4). RC2 rename; physical drop in v1.0.x once the backfill is verified. |
| `defra_conversion_factors` | `unit`, `scope`, `factor_source`, `factor_set`, `country` | KEEP (approved add C4) | Provenance + jurisdiction enabler: v1.1 Ireland becomes a data load (`country='IE'` SEAI/EPA rows), not a migration. |
| `emissions_logs` | `id`, `organization_id`, `asset_id`, `start_date`, `end_date`, `raw_quantity`, `calculated_kg_co2e`, `created_by_user_id`, `created_at`, `metadata`, `file_id`, `updated_at`, `customer_document_id`, `organization_member_id`, `supplier_id`, `product_category_id`, `data_source`, `confidence_score`, `verified_by`, `verified_at`, `updated_by` | KEEP | Core ledger; C12 (`facility_id`) stays DEFERRED to v1.1 — no denormalised copy in v1.0. |
| `emissions_logs` | `defra_factor_id` | RENAME | Approved **R2**: → `emission_factor_id`. Renaming the factor table (R1) while leaving its referencing columns named `defra_*` would freeze a permanent lie into the hottest factor-consuming table; renaming after a year of tenant data is materially harder. RC2. |
| `emissions_logs` | `unit`, `scope` | KEEP (approved add C5) | Self-describing quantities; SECR kWh totals and scope rollups without the factor join; `unit` FK'd to `units.code`. |
| `activity_categories` | — all columns | KEEP | Reference mapping across GHG Protocol / ESRS E1 / ISSB — deliberately multi-standard. |
| `units` | — all columns | KEEP | Reference table; now also the FK target for `emissions_logs.unit` (C5). |

### 2.5 Documents & uploads (11 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `customer_documents` | — all columns | KEEP | Primary pipeline entity. `extracted_data`/`mapped_data` jsonb stay (frozen ADR; C11 typed invoice columns remain DEFERRED). `file_checksum` (approved add **C6**) lands for duplicate detection. C13 `deleted_at` stays DEFERRED to v1.0.x. Polymorphic-style `file_id` naming noted in §5 register; no change. |
| `customer_verifications` | — all columns | KEEP | Full verification state machine (`submitted_*`/`verified_*`/`rejected_*`/`revision_*`/escalation) is coherent and in use. |
| `customer_review_log` | — all columns | KEEP | Review event log; `file_id` naming noted in §5. |
| `document_activity_log` | — all columns | KEEP | Per-document audit feed. |
| `document_types` | — all columns | KEEP | Reference + per-type requirements flags; consistent with `document_type_categories`. |
| `document_type_categories` | `id`, `code`, `name`, `description`, `category_group`, `default_priority`, `requires_facility`, `requires_asset`, `requires_supplier`, `requires_date_range`, `default_scope`, `is_active`, `is_system`, `created_at`, `updated_at` | KEEP | |
| `document_type_categories` | `default_defra_activity_type` | KEEP | Carries a `defra_` prefix but is **not** in the approved R1–R3 set; a further rename does not clear the "materially improve" bar pre-launch (churn breaks seed/app references). Recorded as a v1.1 rename candidate in the §5 violations register. |
| `organization_files` | — all columns | KEEP | General file store with review lifecycle timestamps; distinct responsibility from `customer_documents`. |
| `file_attachments` | — all columns | KEEP | `file_size` widened int4→int8 under approved **C7** (type change, not a column verdict change). |
| `upload_batches` | — all columns | KEEP | Batch orchestration; `created_by_user_id`/`created_by` pair is legacy overlap but both are read by live code — consolidation logged as v1.1 tidy-up, not a v1.0 verdict. |
| `draft_entries` | — all columns | KEEP | Autosave drafts; jsonb `data` per ADR. |
| `export_history` | — all columns | KEEP | Export audit trail with expiry; `filters` jsonb per ADR. |

### 2.6 Processing queues & review workflow (14 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `document_processing_queue` | `id`, `organization_id`, `customer_document_id`, `processing_type`, `status`, `file_name`, `file_url`, `file_size_bytes`, `file_type`, `page_count`, `ai_*` (12 columns), `manual_*` (8 columns), `qc_*` (5 columns), `customer_*` (5 columns), `calculated_emissions_kg_co2e`, `emission_calculation_method`, `batch_id`, `batch_sequence`, `processing_cost`, `billing_currency`, `created_at`, `created_by`, `updated_at`, `updated_by`, `completed_at`, `metadata` | KEEP | Single processing-queue direction is a frozen ADR; the wide stage-prefixed column groups (`ai_`, `manual_`, `qc_`, `customer_`) are the deliberate alternative to split stage tables. |
| `document_processing_queue` | `defra_factor_used` | RENAME | Approved **R2**: → `emission_factor_used`. Companion to R1; the pipeline's audit record of which factor was applied must not carry a jurisdiction-specific name into the IE era. RC2. |
| `manual_extraction_items` | `batch_id`, `document_processing_queue_id`, `file_name`, `file_url`, `page_count`, `document_type`, `status`, `extracted_data`, `mapped_data`, `mapped_facility_id`, `mapped_asset_id`, `mapped_supplier_id`, `calculated_emissions_kg_co2e`, `extracted_by`, `extracted_at`, `qc_by`, `qc_at`, `qc_notes`, `quality_score`, `customer_reviewed_by`, `customer_reviewed_at`, `customer_approved`, `customer_rejection_reason`, `customer_notes`, `created_at`, `updated_at` | KEEP | |
| `manual_extraction_items` | `defra_factor_used` | RENAME | **R2 companion**: → `emission_factor_used`. Same factor-reference semantics as `document_processing_queue.defra_factor_used`; leaving it behind would strand one `defra_*` name on the manual path the R2 rename was designed to clean up. RC2, rides the R2 migration. |
| `processing_queue` | — all columns | KEEP | Staff-facing queue; `queue_status` gains K4 value list (constraint). |
| `processing_assignments` | — all columns | KEEP | |
| `processing_steps` | — all columns | KEEP | |
| `processing_time_log` | — all columns | KEEP | |
| `processing_logs` | — all columns | KEEP | Step-level telemetry; `duration_ms` naming consistent with other `*_ms` columns. |
| `processing_audit_trail` | — all columns | KEEP | |
| `manual_review_queue` | — all columns | KEEP | SLA/escalation column set is the committed ops surface. |
| `manual_extraction_batches` | — all columns | KEEP | `currency` present (K2 set); consistent QC/SLA shape with peers. |
| `review_assignment_history` | — all columns | KEEP | |
| `review_audit_trail` | — all columns | KEEP | |
| `verification_logs` | — all columns | KEEP | |
| `reassignment_history` | — all columns | KEEP | |

### 2.7 Suppliers & categories (3 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `suppliers` | `id`, `organization_id`, `name`, `supplier_category_id`, `website`, `registration_number`, `annual_emissions_scope1/2/3`, `reporting_year`, `emission_factor_scope1/2/3`, `emission_factor_unit`, `is_active`, `created_at`, `created_by`, `updated_at`, `updated_by`, `metadata`, `address_line1`, `address_line2`, `city`, `county`, `postcode`, `country`, `eircode`, `tax_region`, `tax_rate`, `vat_number`, `company_number`, `registration_region`, `supplier_rating`, `is_certified`, `certification_type`, `certification_expiry`, `contract_start`, `contract_end`, `payment_terms`, `payment_currency`, `bank_name`, `bank_account`, `iban`, `swift_code`, `risk_score`, `compliance_status` | KEEP | Scoped emissions/factor sets are the canonical shape (K3 ranges apply). |
| `suppliers` | `type` / `supplier_type` | MERGE | Duplicate pair for one concept. Keep `supplier_type` (unambiguous beside `product_categories.category_type`), fold `type` values in, retire `type`. Timing: v1.0.x. |
| `suppliers` | `contact_name` / `contact_email` / `contact_phone` vs `primary_contact` / `primary_email` / `primary_phone` | MERGE | Two parallel contact triples on one row. Keep the `contact_*` triple (clearer, matches `organizations.primary_contact_*` convention inversely — `primary_` here is the legacy add), fold `primary_*` values across, retire. Timing: v1.0.x. |
| `suppliers` | `annual_emissions`, `emission_factor` | MERGE | Unscoped legacy duplicates of the per-scope columns (`annual_emissions_scope1/2/3`, `emission_factor_scope1/2/3`); an aggregate and a single-factor value kept in parallel invite drift. Fold into the scoped set (aggregate computed at read time). Timing: v1.0.x. |
| `suppliers` | `address` | MERGE | Free-text duplicate of the structured address block on the same row (same defect as `organizations.registered_address`). Fold into structured columns; retire in v1.0.x. |
| `suppliers` | `sort_code` | KEEP (approved add C8) | Completes UK domestic banking capture alongside existing `iban` (IE). |
| `supplier_categories` | — all columns | KEEP | `default_emission_factor`/`_unit` pair self-describing; K3 range applies. |
| `product_categories` | — all columns | KEEP | Per-org category mapping with multi-standard labels; consistent with `activity_categories`. |

### 2.8 Billing & subscriptions (3 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `customer_subscriptions` | — all columns | KEEP | Limits/usage/Stripe triple is complete; `currency` in the K2 set. |
| `consultant_billing` | — all columns | KEEP | Gains `currency` (approved add **C3**) — the only billing table previously undenominated. |
| `usage_tracking` | — all columns | KEEP | Counters covered by K3/K5 (non-negative; UNIQUE on `(organization_id, usage_month)`). |

### 2.9 Messaging & notifications (13 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `conversations` | — all columns | KEEP | `read_by`/`unread_count`/`participant_count` are denormalised read-model caches maintained by triggers — accepted, not re-normalised pre-launch. |
| `conversation_participants` | — all columns | KEEP | |
| `messages` | — all columns | KEEP | `is_read`/`read_at` alongside `read_by`/`read_count`/`last_read_at` serves 1:1 and group read-state respectively; consolidation is v1.1 evidence-gated, not a v1.0 verdict. |
| `message_activity_log` | — all columns | KEEP | |
| `conversation_activity_log` | — all columns | KEEP | |
| `typing_status` | — all columns | KEEP | Ephemeral UI state. |
| `customer_communication` | — all columns | KEEP | Staff→customer comms log; singular name noted in §5 (accept-with-reason). |
| `notifications` | — all columns | KEEP | Polymorphic `recipient_type`/`recipient_id` is the committed design. |
| `notification_templates` | — all columns | KEEP | |
| `notification_delivery` | (table) `id`, `notification_id`, `channel`, `status`, `sent_at`, `delivered_at`, `opened_at`, `error_message`, `metadata`, `created_at`, `updated_at` | MERGE | Near-duplicate of `notification_delivery_log` (same channel/status/timestamp payload; the `_log` twin adds `user_id`). One delivery-write path must survive. Merge target `notification_delivery_log` (superset); retire this table. Timing: v1.0.x, per prior triage deferral. |
| `notification_delivery_log` | — all columns | KEEP | Canonical delivery log (merge target). |
| `email_templates` | — all columns | KEEP | Overlaps `notification_templates` only superficially (channel-specific rendering); no merge. |
| `email_logs` | — all columns | KEEP | |

### 2.10 Consultant portal (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `consultant_profiles` | — all columns | KEEP | White-label branding + partner programme columns committed for launch; `eircode`/`postcode` dual-carried per K1. |
| `consultant_clients` | — all columns | KEEP | K5 UNIQUE on `(consultant_id, organization_id)` applies (constraint). |
| `consultant_firm_members` | — all columns | KEEP | `client_access` uuid array is ADR-locked (I4 GIN index approved); no junction-table normalisation. |
| `consultant_tasks` | — all columns | KEEP | `task_title`/`task_description` prefixed names acceptable (disambiguate against `internal_tasks`); noted in §5. |

### 2.11 Staff, admin & QC (20 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `staff_roles` | — all columns | KEEP | |
| `staff_profiles` | — all columns | KEEP | |
| `staff_workload` | — all columns | KEEP | Live workload snapshot; overlaps `staff_daily_performance` conceptually — consolidation noted as **v1.1 NORMALIZE candidate** (snapshot vs daily-rollup split is defensible today; no v1.0 action). |
| `staff_performance` | — all columns | KEEP | Period rollup; complements `staff_daily_performance`. |
| `staff_daily_performance` | — all columns | KEEP | |
| `team_performance` | — all columns | KEEP | |
| `staff_activity_log` | — all columns | KEEP | |
| `login_history` | — all columns | KEEP | |
| `internal_tasks` | — all columns | KEEP | |
| `task_assignments` | — all columns | KEEP | |
| `qc_checks` | — all columns | KEEP | |
| `qc_checklists` | — all columns | KEEP | `checklist_items` jsonb per ADR. |
| `qc_errors` | — all columns | KEEP | |
| `approval_requests` | — all columns | KEEP | |
| `approval_decisions` | — all columns | KEEP | |
| `sla_compliance` | — all columns | KEEP | |
| `sla_definitions` | — all columns | KEEP | |
| `business_hours` | — all columns | KEEP | |
| `queue_settings` | — all columns | KEEP | Key-value store; deliberately separate from `system_settings` (worker ops vs platform config). |
| `verification_activity_log` | — all columns | KEEP | |

### 2.12 Audit & activity logs (5 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `audit_logs` | `id`, `user_id`, `staff_id`, `organization_member_id`, `organization_id`, `resource_type`, `resource_id`, `description`, `ip_address`, `user_agent`, `old_data`, `new_data`, `changes`, `metadata`, `created_at` | KEEP | |
| `audit_logs` | `action_type` / `action` | MERGE | Two columns carrying the same event verb (both effectively required by the dump) — every writer must currently dual-write. Keep `action_type` (aligns with `audit_trail.action_type` and the `*_activity_log.action_type` family), fold `action` values in, retire. Timing: v1.0.x. |
| `audit_trail` | — all columns | KEEP | Trigger-maintained row-version trail; distinct responsibility from `audit_logs` (business events). Naming overlap with `audit_logs` noted in §5 (accept-with-reason). |
| `activity_logs` | — all columns | KEEP | User-facing activity; `metadata` + `details` jsonb both retained (different producers). |
| `activity_feed` | — all columns | KEEP | Read-model feed; `event_data` jsonb per ADR. |
| `user_activity_log` | — all columns | KEEP | Per-user security activity; distinct from org-scoped `activity_logs`. |

### 2.13 Reports & AI content (5 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `report_templates` | — all columns | KEEP | `template_structure`/`ai_prompts` jsonb per ADR. |
| `report_generation_queue` | — all columns | KEEP | AI cost telemetry (`ai_model_used`, `ai_tokens_used`, `ai_cost`) is the committed FinOps surface. |
| `report_versions` | — all columns | KEEP | K5 UNIQUE `(report_id, version_number)` applies. |
| `report_comments` | — all columns | KEEP | |
| `ai_content_history` | — all columns | KEEP | |

### 2.14 Reference, settings & misc (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `glossary` | — all columns | KEEP | Seed/reference content. |
| `system_settings` | `id`, `setting_key`, `setting_value`, `setting_type`, `description`, `is_editable`, `updated_by`, `updated_at`, `created_at`, and all typed `default_*` / `sla_*` / `max_*` / `api_*` / `webhook_*` / `session_*` / `two_factor_*` / `password_*` / `login_*` / `*_retention_*` / `backup_*` columns | KEEP | Hybrid key-value + typed-column settings row; global `two_factor_*` flags stay as marketing/config only until platform MFA ships (frozen C14). |
| `system_settings` | `default_vat_rate` | MERGE | Exact duplicate of `default_tax_rate` on the same row (UK calls it VAT, IE calls it VAT too — one concept, one column). Keep `default_tax_rate` (jurisdiction-neutral), fold value across, retire. Timing: v1.0 — trivial, pre-launch, and removes a which-one-wins ambiguity before billing code hardens against it. |
| `dashboard_metrics` | — all columns | KEEP | Cache table with `expires_at`; correct shape. |
| `user_feedback` | — all columns | KEEP | |

**Coverage statement:** 100 tables in the dump; 100 appear above across 14 areas. **Verdict counts:** KEEP 91 tables (incl. compact rows; all ~1,150 columns not otherwise listed below); **RENAME 6** (R1 table rename; `region`→`region_deprecated` retire; R2 ×2 approved + 1 R2 companion on `manual_extraction_items`; R3 ×1); **MERGE 10** (`pending_invites`→`user_invitations`; `notification_delivery`→`notification_delivery_log`; `system_settings.default_vat_rate`→`default_tax_rate`; `organizations.registered_address` and `vat_region`; `suppliers` `type`, `primary_contact/_email/_phone`, `annual_emissions`+`emission_factor`, `address`; `audit_logs.action`→`action_type`); **REMOVE 0 columns** (no provably dead column exists pre-launch; table-level retirements — `waitlist`, `beta_users`, `beta_access_codes` post-GA — are data/lifecycle decisions, not RC2 column verdicts); **SPLIT 0**; **NORMALIZE 0 in v1.0** — two explicit v1.1 candidates noted (`staff_workload`/`staff_daily_performance` consolidation; remaining ~20 free-text status columns per K4's deferred tail). Typed invoice columns (C11), county lookup (T3) and the jsonb promotion freeze are not resurrected.


## Section 3 — UK Launch Validation

This register specifies validation for every field class the UK primary launch touches. It is written against the frozen validation-layering decision of the Production Hardening Plan (§4 item 1, §6 D1) and the approved constraint set of the Structural Change Review (K1–K8, C1): **the database enforces exactly four validation shapes — IN-lists, ranges, presence, uniqueness. All format, regex and checksum validation lives in the API layer. Regex-heavy CHECKs are rejected (K9) and are not reinstated anywhere in this document.** Where a "Database constraint" cell reads "none — API layer", that is a deliberate frozen outcome, not an omission.

### 3.1 UK validation register

| # | Field | Column(s) | Validation method | Regex | Length | Database constraint | API validation (authoritative) | Frontend validation (UX) |
|---|-------|-----------|-------------------|-------|--------|---------------------|--------------------------------|--------------------------|
| 1 | Phone (org/consultant/supplier contacts) | `consultant_profiles.phone`, `.support_phone`; `suppliers.contact_phone`, `.primary_phone`; `organization_metadata.primary_contact_phone` | libphonenumber parse, normalise to E.164 at write | `^\+[1-9]\d{6,14}$` (stored form; GB national input `^0\d{10}$` converted to `+44…`) | ≤ 16 stored | none — API layer | libphonenumber GB validation (mobile/landline acceptance rules); store E.164 only; reject non-GB/+44 at UK onboarding unless country overridden | Live mask + inline "enter a valid UK number" hint; auto-prefix `+44` on `07…`/`01…` input |
| 2 | Email | `users.email`, `suppliers.contact_email`, `.primary_email`, `organizations.primary_contact_email`, `.billing_contact_email`, `organization_metadata.primary_contact_email`, `.sustainability_officer_email`, `consultant_profiles.support_email`, `email_logs.email` | RFC 5322 practical subset via validator library | `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` | ≤ 254 | Uniqueness: `users.email` UNIQUE (existing); presence only on sign-up path — no format CHECK | validator-library syntax check; MX/domain existence check on sign-up; normalise to lowercase domain; erasure runbook hashes `users.email` (P5) | Immediate syntax feedback; common-domain typo nudge ("did you mean gmail.com?") |
| 3 | Postcode (GB) | `facilities.postcode`, `organizations.postcode`, `suppliers.postcode`, `consultant_profiles.postcode` | GIR-valid shape + outward-area check, normalised at write | `^(GIR ?0AA|[A-PR-UWYZ](\d{1,2}|[A-HK-Y]\d{1,2}|\d[A-HJKPSTUW]|[A-HK-Y]\d[ABEHMNPRV-Y]) ?\d[ABD-HJLNP-UW-Z]{2})$` | ≤ 8 stored | Presence (C1): `facilities` presence CHECK — `postcode` OR `eircode` present; no format CHECK | Canonical-case + single-space normalisation; GIR 0AA special case; outward-area allowlist (living Royal Mail registry — app config, never a frozen CHECK); `facilities` per-country rule: GB row must carry postcode | Case auto-format as typed; inline validity tick; PAF-style lookup affordance |
| 4 | VAT number (GB) | `organizations.vat_number`, `suppliers.vat_number`, `consultant_profiles.vat_number` | Format + HMRC MOD97 checksum | `^(GB)?(\d{9}|\d{12}|GD\d{3}|HA\d{3})$` (9 standard, 12 branch-trader, GD government dept, HA health authority) | ≤ 12 digits + 2 prefix | Uniqueness (K5): partial UNIQUE `suppliers(organization_id, vat_number)` WHERE NOT NULL; no format CHECK | MOD97 checksum authoritative (HMRC algorithm); strip spaces/GB prefix at normalisation; GD/HA ranges exempted from MOD97; optional VIES cross-check deferred | Prefix/digit-count feedback as typed; checksum failure surfaces as "check this VAT number" warning, not hard block on draft |
| 5 | Company number (Companies House) | `organizations.company_number`, `suppliers.company_number`, `consultant_profiles.company_number` | 8-char shape with nation prefixes | `^([A-Z]{2})?\d{6}$` — 8 digits England/Wales; `SC\d{6}` Scotland; `NI\d{6}` Northern Ireland; also `OC|SO|NC` LLP variants per CH rules | = 8 | Uniqueness: `organizations.company_number` UNIQUE (existing) + K5 partial `suppliers(organization_id, company_number)` WHERE NOT NULL; no format CHECK | CH prefix/length rules country-conditional; optional Companies House API existence lookup (app integration, C11/D12 — no DB artefacts) | Length counter + prefix auto-uppercase; "verified by Companies House" badge when lookup passes |
| 6 | Currency | `organizations.currency`, `suppliers.payment_currency`, `document_processing_queue.billing_currency`, `customer_subscriptions.currency`, `manual_extraction_batches.currency`, `consultant_profiles.revenue_currency`, `consultant_billing.currency` (C3), `system_settings.default_currency` | IN-list (frozen set) | n/a — ISO 4217 codes, list-bound | = 3 | **IN-list (K2): CHECK IN ('GBP','EUR') on all seven columns + `default_currency`** | UK defaulting rule: 'GBP' when `country='GB'`; EUR only via country selection, never free entry | Currency selector limited to GBP/EUR; GBP preselected for UK onboarding |
| 7 | Country | `organizations.country`, `facilities.country`, `suppliers.country`, `consultant_profiles.country` | IN-list (frozen set) | n/a — ISO 3166-1 alpha-2, list-bound | = 2 | **IN-list (K1): CHECK IN ('GB','IE') on all four columns** | Drives every jurisdiction rule (currency, factor `country` selection, validation pack selection, reporting defaults); UK onboarding writes 'GB' | Country picker constrained to GB/IE; GB preselected and visually primary |
| 8 | URLs (file/logo/export/report links) | `customer_documents.file_url`, `file_attachments.file_url`, `manual_review_queue.file_url`, `export_history.file_url`, `organizations.logo_url`, `consultant_profiles.logo_url`, `report_generation_queue.final_report_url`, `organization_files.file_url` | URL parse + scheme allowlist | `^https://[^\s]+$` (HTTPS only; internal storage URLs validated against the storage origin allowlist) | ≤ 2048 | none — API layer | Scheme allowlist `https:`; host allowlist for storage-generated URLs; SSRF guard on any user-supplied fetchable URL | Read-only display in v1.0 (system-generated); no user URL entry for these fields |
| 9 | Website | `organizations.website`, `suppliers.website`, `consultant_profiles.website` | URL parse + scheme allowlist | `^https?://[^\s]+\.[A-Za-z]{2,}(/[^\s]*)?$` | ≤ 2048 | none — API layer | Scheme restricted to http/https; IDN normalised to punycode at write; no fetch/verification in v1.0 | Auto-prefix `https://` when scheme omitted; malformed-URL inline error |
| 10 | Coordinates | `facilities.latitude`, `facilities.longitude` | Range validation | n/a | numeric | **Range:** API-enforced bounds −90 ≤ lat ≤ 90, −180 ≤ lng ≤ 180 (B-class range CHECK in the v1.0.2 window alongside the remaining B CHECKs); UK plausibility window (49.9–60.9 N, −8.7–1.8 E) is an API warning rule, not a hard bound | Bounds check; UK-window soft warning ("outside the UK — confirm"); precision capped at 6 dp | Map-picker capture preferred over manual entry; out-of-UK prompt |
| 11 | IBAN | `suppliers.iban` | Format + ISO 13616 MOD-97 checksum | `^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$` (per-country BBAN length map applied by the validator, e.g. GB = 22, IE = 22) | ≤ 34 | none — API layer | MOD-97 checksum authoritative; country-length table; spaces stripped, uppercase normalised at write; last-4 masking in responses (B, v1.0.2) | Group-of-4 display formatting; checksum failure inline error |
| 12 | Sort code | `suppliers.sort_code` (C8) | Format + modulus check | `^\d{6}$` stored normalised (display `^\d{2}-\d{2}-\d{2}$`) | = 6 digits | none — API layer | Digits-only normalisation at write; industry modulus check (10/11/double-alternate) per the Vocalink weight table — app-maintained data, never a CHECK; last-4 masking in API responses | `##-##-##` input mask; inline modulus failure hint |
| 13 | Account number | `suppliers.bank_account` | Length/charset rule | `^\d{8}$` (GB domestic standard; 7-digit inputs left-padded with 0 per convention) | = 8 digits | none — API layer | 8-digit normalisation; paired with `sort_code` for modulus validation where the weight table requires the pair; masked in responses | 8-digit numeric input; pairing prompt when sort code present |
| 14 | File types (extensions) | `customer_documents.file_type`, `file_attachments.file_type`, `organization_files.file_type`, `manual_review_queue.file_type`, `document_processing_queue.file_type` | Extension allowlist | `^(pdf|csv|xlsx?|docx?|png|jpe?g)$` (lowercase, normalised at write) | ≤ 10 | none — API layer (extension allowlist is product config; pipeline acceptance rules change with extraction capability and must not require migrations) | Allowlist enforced at upload; extension/MIME cross-check (item 15); size ceiling against the int8-widened columns (C7) | Uploader restricts picker to allowed types; reject with "supported: PDF, CSV, Excel, Word, PNG, JPEG" before upload starts |
| 15 | MIME types | `file_attachments.mime_type` (and upload-time content sniffing for `customer_documents`) | MIME allowlist + magic-byte verification | `^(application/pdf|text/csv|application/vnd\.(ms-excel|openxmlformats-officedocument\.[a-z.]+)|image/(png|jpeg))$` | ≤ 127 | none — API layer | Server-side magic-byte sniffing is authoritative — client-declared MIME never trusted; mismatch with extension rejected; MIME recorded from sniff, not the request header | Client-side pre-check from file header where readable; clear per-file rejection reason |
| 16 | Units | `units.code` (FK target), `emissions_logs.unit` (C5, FK to `units.code`), `emission_factors.unit` (C4), `assets.capacity_unit`, `supplier_categories.default_emission_factor_unit`, `system_settings.carbon_tax_unit` | Referential membership of the `units` reference table | n/a — code list | ≤ 20 | **Presence/reference:** FK `emissions_logs.unit` → `units.code` (C5/F1); `units.code` UNIQUE (existing); no per-value format CHECK | Unit selection constrained to active `units` rows; kWh the UK default for energy entry; conversion applied via `units.conversion_factor` | Unit dropdowns populated from `units`; kWh preselected on UK energy forms |
| 17 | Measurement / activity types | `emission_factors.activity_type`, `defra_conversion_factors` (→ `emission_factors`, R1) `activity_type`; `activity_categories.ghg_protocol_scope` | Controlled vocabulary per factor set | n/a — set-defined list | ≤ 100 | Uniqueness (K5): UNIQUE `(reporting_year, activity_type, country)` on `emission_factors`; value vocabulary owned by the factor set (data), not a CHECK | Activity type must resolve to a factor row for the org's country and reporting year; unresolvable entries route to manual review | Type-ahead picker over factor activity types; no free entry |
| 18 | Emission units (quantities and factors) | `emissions_logs.raw_quantity`, `.calculated_kg_co2e`; `emission_factors.co2e_multiplier`; `suppliers.annual_emissions_scope1/2/3`, `.emission_factor_scope1/2/3`; `supplier_categories.default_emission_factor` | Numeric range | n/a | numeric | **Range (K3): CHECK ≥ 0 on all seven column groups** — one negative `calculated_kg_co2e` silently corrupts every SECR total | Sign convention: corrections are positive quantities with a sign/adjustment flag, never negative rows; unit/`co2e_multiplier` dimensional consistency check at calculation time | Numeric-only entry; negative input blocked with explanation of the adjustment pattern |
| 19 | Names (org, facility, supplier, contact, consultant) | `organizations.name`, `facilities.name`, `suppliers.name`, `.contact_name`, `.primary_contact`, `organization_metadata.primary_contact_name`, `.sustainability_officer_name`, `consultant_profiles.company_name` | Presence + length + character sanity | `^[^<>{}]{1,200}$` (markup-brace exclusion; no restrictive alpha-only rule — O'Brien, Dún Laoghaire, hyphens and diacritics are legitimate) | ≤ 200 | Presence: existing NOT NULL on `organizations.name`, `facilities.name`, `suppliers.name`; uniqueness explicitly **not** imposed on supplier names (frozen D14 — legitimate same-name suppliers; `pg_trgm` "did you mean?" is the soft control) | Trim/collapse whitespace; NFC unicode normalisation; trigram duplicate nudge against `suppliers.name` (I5) | Length counter; duplicate-suggestion prompt on supplier entry |
| 20 | Dates / financial years | `emissions_logs.start_date`, `.end_date`; `customer_documents.billing_period_start`, `.billing_period_end`; `organizations.financial_year_end`; `organization_metadata.fiscal_year_start`, `.fiscal_year_end`; `emission_factors.reporting_year` (int4); `organizations.default_factor_year` (R3); `suppliers.contract_start`, `.contract_end` | Date parse + pair ordering + year range | ISO `YYYY-MM-DD` on the wire; `reporting_year` `^(19|20)\d{2}$` | n/a | **Range/pairing:** date-pair CHECKs (start ≤ end) on `emissions_logs` and `customer_documents` billing periods (B-class, v1.0.2 window); `reporting_year` plausibility range 2000–2100 (B-class range) | UK financial-year convention surfaced in reporting (int4 `reporting_year` cannot name a UK FY — HP-C16 reporting-period columns are v1.1); billing period overlap detection per supplier/facility; `financial_year_end` captured as day-month | Date pickers, never free text; end-before-start inline error; FY helper text "e.g. 31 March" |
| 21 | Percentages | `organization_metadata.renewable_energy_percentage`, `.carbon_offset_percentage`; `report_generation_queue.progress_percentage`; `staff_workload.capacity_percentage` | Range 0–100 after scale convention fixed | n/a | numeric / int4 | **Range:** 0–100 CHECKs once the 0–100 scale convention is standardised (B-class, v1.0.2 window — the scale standardisation precedes the CHECK) | Single 0–100 convention platform-wide; reject fractional-scale (0–1) writes at the boundary | Slider/percentage input with 0 and 100 hard stops |
| 22 | Confidence scores | `customer_documents.confidence_score` (float8), `emissions_logs.confidence_score`, `document_processing_queue.ai_confidence_score`, `.ai_mapping_confidence`, `draft_entries.confidence_score` | Range after type/scale standardisation | n/a | float8 / numeric | **Range:** bounded CHECK (0–1 or 0–100 per the standardisation decision) — `confidence_score` type/scale standardisation is B-class (v1.0.2); no CHECK before the scale is fixed | Scale standardised across the pipeline before the CHECK lands; values outside scale rejected at the worker write path; low-confidence threshold routes to manual review | Percentage-style display ("87% confident"); amber/red rendering below review threshold |
| 23 | Quantities (usage counters, money, record counts) | `usage_tracking.*_used`, `export_history.record_count`, `organization_metadata.total_employees`/headcount columns, `file_attachments.file_size` (C7 int8), `document_processing_queue.file_size_bytes` | Numeric range | n/a | numeric / int4 / int8 | **Range (K3 companions): ≥ 0 CHECKs on usage counters and money counters; `used ≤ limit` on `usage_tracking`; size CHECKs on the widened int8 file-size columns** | Integer coercion for counters; currency-denominated amounts must carry one of the seven K2-constrained currency columns | Numeric-only entry; thousand separators for display |

### 3.2 The layering principle — frozen decision

The layering is restated here as frozen architecture, not guidance. **The database protects integrity and nothing else**: the four shapes it enforces are IN-lists (K1 country, K2 currency, K4 status/role lists), ranges (K3 emission values, factors and counters; the B-class percentage/date-pair/confidence ranges once their scale conventions land), presence (C1 postcode-or-eircode; existing NOT NULLs; K7/K8) and uniqueness (K5, K6). **The API layer is the sole format authority**: MOD97 for GB VAT, ISO 13616 MOD-97 for IBAN, the Vocalink modulus rules for sort codes, GIR-shape postcodes, libphonenumber E.164, RFC-practical email, Companies House prefix rules — all library-backed, all country-conditional, all normalising at write so the database stores and constrains the *normalised* value. **The frontend validates for user experience only** — masks, pickers, immediate feedback — and its verdicts are never trusted server-side. Regex-heavy CHECK constraints, including any country-conditional regex matrix and any frozen Eircode routing-key allowlist, remain rejected (K9/D1): formats rot, registries change, and a migration must never be the price of admitting a legitimate address.

### 3.3 UK-default behaviours

The UK primary launch fixes the defaults in one direction: `organizations.country` defaults to **GB**, every currency column and `system_settings.default_currency` defaults to **GBP**, and `organizations.timezone` / `system_settings.default_timezone` default to **Europe/London**. `units` kWh is the default energy entry unit, `default_factor_year`/`system_settings.default_emission_factor_year` point at the current DEFRA-DESNZ reporting year, date presentation is `DD/MM/YYYY`, and the financial-year helper surfaces the UK convention (commonly 31 March or 5 April aligned). Non-GB values are reachable only by an explicit country selection at onboarding — never by free entry into an IN-listed or format-validated field.

## Section 4 — Ireland Beta Readiness

Ireland is a beta market in RC2: Irish users may register and operate, with localisation limited to beta necessities, and full Ireland support guaranteed in v1.1 **with no database redesign**. This register enumerates every Ireland-specific item, its layer, and whether it ships in RC2 or v1.1. The same frozen layering applies: no Irish format rule enters the database; the Eircode routing-key registry in particular must never be frozen into a CHECK (D1/K9).

### 4.1 Ireland beta register

| # | Item | Requirement | Layer | Beta status | Notes |
|---|------|-------------|-------|-------------|-------|
| 1 | Eircode capture & storage | `facilities.eircode` nullable column; `facilities.postcode` NOT NULL relaxed; presence CHECK (postcode OR eircode) | Database | **in RC2** (C1 — approved) | The non-negotiable Irish write-path fix: without it an Irish beta user cannot insert the facility whose emissions the product measures. `organizations`, `suppliers`, `consultant_profiles` already carry nullable `eircode`. DB stores the plain normalised value; no format rule in the constraint. |
| 2 | Eircode format validation | Shape regex `^[AC-FHKNPRTV-Y]\d{2} ?[AC-FHKNPRTV-Y0-9]{4}$` — note the charset deliberately excludes **I and O** (and G, J, Q, S, U, W, Z in the routing key) to avoid visual ambiguity; normalise to uppercase, single space (`D02 X285`) | API | **in RC2** (shape check); routing-key allowlist verification **v1.1** | Beta validates shape only; the routing-key allowlist is a living third-party registry and lives in app config, never a CHECK (frozen D1). |
| 3 | Facilities presence rule | Every facility carries at least one locatable identifier: postcode (GB) or Eircode (IE); both-NULL rejected | Database | **in RC2** (C1 CHECK) | Simple "at least one" form chosen over country-conditional XOR because `facilities.country` is nullable and the per-country rule belongs to the API. Acceptance: IE facility with Eircode and NULL postcode inserts; both-NULL rejected. |
| 4 | EUR currency | EUR admitted across the billing surface | Database + API | **in RC2** (K2) | K2's IN-list ('GBP','EUR') already contains EUR on all seven currency columns — no v1.1 change. API applies the EUR default when `country='IE'` (app rule, P4/v1.0.1 window). |
| 5 | CRO company numbers | Irish company number validation: 6-digit core with prefixes — `^\d{6}$` standard; `^C\d{6}$` (legacy); R/LP/FC/SO-style prefixes per CRO conventions, e.g. `^(C\|R\|LP\|FC\|SO)?\d{6}$` applied country-conditionally | API | **in RC2** (beta depth: shape + prefix) | Single `company_number` column serves both jurisdictions (frozen D13 — a parallel `cro_number` column is rejected); K5's partial UNIQUE applies. Full CRO registry lookup is v1.1 app work. |
| 6 | IE VAT numbers | Irish VAT format `^IE\d{7}[A-Z]{1,2}$` (plus legacy `^IE\d[A-Z]\d{5}[A-Z]$`); checksum per Revenue algorithm; VIES cross-check | API | **in RC2** (format only); checksum + VIES **v1.1** | Beta necessity is acceptance, not verification: an IE-formatted VAT number must not be rejected by UK-only rules. Selected by the country-conditional validation pack when `country='IE'`. |
| 7 | Irish address format | Ireland has no general postcode system: Eircode is optional-but-recommended, not mandatory; address capture must not force a "postcode" field on IE forms | API + Frontend | **in RC2** | IE forms render address lines, town/city, county (free text) and an optional Eircode field; the C1 presence CHECK guarantees a locatable identifier only at `facilities`, where the emissions product genuinely needs one. |
| 8 | 26 ROI counties | Dropdown list of the 26 Republic of Ireland counties for IE address forms | API / Frontend | **in RC2** (list in app config) | A county **database lookup table was explicitly rejected (T3/D9)**: nothing computes from `county`, it is display data, and the table imports Dublin city/county and Derry/Londonderry edge-case debt for zero consumers. `county` stays free text in the DB; the list lives in frontend/API config; normalisation arrives with the v1.1 address-verification loop (HP-C8). |
| 9 | +353 phone | libphonenumber IE region; E.164 storage; `^\+353\d{7,9}$` stored form (national `0…` input converted) | API | **in RC2** | Same pipeline as UK phones; region selected by the row's `country`; +353 accepted alongside +44 wherever phones are captured. |
| 10 | Europe/Dublin timezone | IE orgs default to Europe/Dublin; platform timezone IN-list admits both zones | API + config | **in RC2** (default); IN-list **v1.0.2** (B-class) | One-hour offset from Europe/London matters for SLA boundaries and report cut-offs; the timezone IN-list CHECK is a B-window item, not a launch gate. |
| 11 | SEAI/EPA emission factors — beta core | Minimal current-year Irish core set: grid electricity (Scope 2), natural gas, common liquid/gaseous fuels, loaded with `country='IE'`, `factor_source` 'SEAI'/'EPA' | Seed Data | **in RC2** (hardening plan A item 15) | The correctness gate: a DEFRA-factored Dublin site reports silently wrong Scope 2, and a wrong number is worse than a missing feature. Ships as a data load riding the provenance-columns phase — rows, not structure. Fallback if the load slips: UK-only launch with IE sign-ups gated (item 13). |
| 12 | SEAI/EPA full catalogue | Historical catalogue, CO2/CH4/N2O species breakdowns, full activity-type breadth | Seed Data | **v1.1** (HP-C15) | Breadth, not correctness. The C4 jurisdiction/provenance column design (`country`, `unit`, `scope`, `factor_source`, `factor_set`) is already approved, so v1.1 activation is a pure data load against the existing schema — **no schema change**. |
| 13 | Irish financial-year / localisation defaults | IE onboarding defaults: currency EUR, timezone Europe/Dublin, country 'IE', EUR tax/VAT defaults (23% standard rate vs UK 20%, surfaced via `default_vat_rate` per tenant), date format DD/MM/YYYY (shared), FY helper without UK conventions | API + Frontend | **in RC2** | Selected wholesale by the country picker; int4 `reporting_year` cannot name an Irish FY — reporting-period columns are v1.1 (HP-C16) and are acceptable in beta because no IE statutory reporting flow is committed in RC2. |
| 14 | IE sign-up gating fallback | If the SEAI/EPA core load (item 11) slips the launch window, IE sign-ups are gated at onboarding: UK-only registration, IE held on a waitlist with clear messaging | API + Frontend | Contingency only — **RC2** decision point | A product decision executed in the registration flow, never in the schema. The schema work (K1/K2, C1, C4) is required under either outcome, so the fallback costs the programme nothing but honesty. What is never acceptable: shipping Irish customers DEFRA factors and calling it Scope 2. |
| 15 | Irish regression fixtures | IE organisation + IE facility fixture carrying Eircode, EUR currency and an IE emission factor, exercised through onboarding, upload, mapping and reporting | Seed Data / testing | **in RC2**, then permanent (Gate 3) | The guard whose absence let the facilities blocker survive to audit; runs in every release candidate. |
| 16 | Irish floor-area units | Metric m² entry for IE orgs via `organization_metadata.total_floor_area_sqm` / `.occupied_floor_area_sqm` | Database (approved columns) + API | **in RC2** (C10, B-window) | Prevents IE beta users entering m² into sqft-labelled columns and corrupting intensity ratios by ~10.8×; form renders the unit-appropriate field by country. |
| 17 | MPRN meter identifiers | `facilities.meter_mpan_mprn` captures Irish gas MPRN as well as GB MPAN/MPRN | Database (approved column) | **in RC2** (C9, B-window) | Single free-format identifier column; bill-to-facility matching logic is v1.1 app work. |

### 4.2 The v1.1 full-Ireland guarantee

Full Ireland support in v1.1 requires **no database redesign**, and that guarantee rests on enablers already approved in RC2. The renamed `emission_factors` table (R1) carries the approved provenance columns — `unit`, `scope`, `factor_source`, `factor_set` and the jurisdiction column `country` constrained to the ('GB','IE') IN-list (C4/K1) — with the referencing columns renamed `emissions_logs.emission_factor_id` and `document_processing_queue.emission_factor_used` (R2), so Irish factor rows select by a `country` predicate on a table whose name and keys already speak jurisdiction-neutrally. The `facilities.eircode` column plus the postcode-or-eircode presence CHECK (C1) means the Irish write-path is structurally complete today. And the currency IN-list (K2) already contains EUR across all seven currency columns. v1.1 Ireland activation is therefore a **data and API release**: load the full SEAI/EPA catalogue with `country='IE'`, deepen API validation (routing-key verification, CRO registry lookup, IE VAT checksum/VIES, the address-verification loop), and activate localisation depth — against a schema that already names, keys and constrains Ireland correctly, with zero migration-led redesign.

## Section 5 — Naming Standard

### 5(a) The standard — ten rules

1. **snake_case everywhere, lower-case only.** Tables, columns, constraints. No exceptions in the schema; this codifies existing practice (`organization_members`, `calculated_emissions_kg_co2e`).
2. **Plural nouns for entity tables** (`organizations`, `suppliers`, `facilities`, `emissions_logs`). Singular/mass-noun names are permitted only for genuine singleton or state resources (`user_presence`, `typing_status`, `glossary`, `waitlist`) and for `_settings` stores.
3. **Suffix conventions are semantic, not decorative.** `_log`/`_logs` = append-only event history (`audit_logs`, `email_logs`); `_trail` = row-version history (`audit_trail`, `processing_audit_trail`); `_queue` = claimable work (`processing_queue`, `document_processing_queue`); `_queue` never doubles as a log; `_templates`, `_definitions`, `_categories`, `_settings` for reference/config; `_history` for immutable transition records (`reassignment_history`, `login_history`).
4. **Jurisdiction-neutral names for anything cross-border.** No national authority, registry or scheme in an identifier unless the column is definitionally jurisdiction-bound. Hence `emission_factors` (not `defra_conversion_factors`), `emission_factor_id`, `default_factor_year`, `country` carrying `('GB','IE')` per K1. Jurisdiction-bound identifiers are named for what they are: `eircode`, `postcode`, `sort_code`, `iban`, `company_number`.
5. **Foreign keys are `<referenced_singular>_id`** (`organization_id`, `customer_document_id`, `emission_factor_id`). Actor columns use role-prefixed forms (`assigned_to`/`assigned_by`, `verified_by`, `created_by`/`updated_by`). Polymorphic references must be named by the pair, e.g. `recipient_type` + `recipient_id` (`notifications`).
6. **Timestamps are `<event>_at` (`timestamptz`); dates are `<event>_date` (`date`); durations carry their unit** (`duration_ms`, `review_time_seconds`, `sla_default_hours`). Booleans are `is_*`/`has_*`/`can_*` or a `<verb>ed`/`required` predicate (`is_active`, `has_attachments`, `can_manage_clients`, `qc_required`, `email_verified`).
7. **Measurements carry their unit in the name** (`calculated_emissions_kg_co2e`, `total_floor_area_sqft`/`_sqm`, `file_size_bytes`, `max_upload_size_mb`) or reference `units.code` (`emissions_logs.unit`, C5). Bare numeric measures of money are only acceptable where a sibling `currency` column denominates them (`processing_cost` + `billing_currency`).
8. **No non-standard abbreviations.** Domain-standard acronyms are permitted and preferred over invention: `co2e`, `qc`, `sla`, `vat`, `ebitda`, `isin`, `lei`, `sedol`, `cik`, `mpan`/`mprn`, `ai` (as a stage prefix), `avg`. Banned class: ad-hoc truncations (`org`, `doc`, `addr`, `qty`) — none exist in the schema and none may be introduced.
9. **Stage/namespace prefixes group wide-table columns by lifecycle stage**, underscore-terminated and used consistently within the table: `ai_*`, `manual_*`, `qc_*`, `customer_*` on `document_processing_queue`; `default_*` on `system_settings`; `stripe_*` for third-party identifiers. A prefix, once chosen for a stage, is used by every column of that stage in every table (hence the `defra_*` retirements — a jurisdiction is not a stage).
10. **jsonb payload columns have fixed names**: `metadata` (opaque extension bag), `details`/`event_data` (log payloads), `extracted_data`/`mapped_data` (pipeline payloads), `old_data`/`new_data`/`changes` (audit diffs). New jsonb columns must reuse these names rather than coin synonyms.

### 5(b) Violations register

| Object | Violation | Verdict |
|--------|-----------|---------|
| `defra_conversion_factors` (table) | Rule 4 — jurisdiction-specific authority in a cross-border entity name | **Fix in RC2 (R1, approved)** → `emission_factors` |
| `emissions_logs.defra_factor_id` | Rules 4, 5 — jurisdiction prefix on an FK | **Fix in RC2 (R2, approved)** → `emission_factor_id` |
| `document_processing_queue.defra_factor_used` | Rules 4, 9 — jurisdiction prefix masquerading as stage prefix | **Fix in RC2 (R2, approved)** → `emission_factor_used` |
| `manual_extraction_items.defra_factor_used` | Same as above; R2 companion | **Fix in RC2** → `emission_factor_used` (same migration; stranding it would leave one `defra_*` reference behind) |
| `organizations.default_defra_version` | Rule 4 + internal inconsistency with `system_settings.default_emission_factor_year` | **Fix in RC2 (R3, approved)** → `default_factor_year` |
| `defra_conversion_factors.region` | Ambiguous jurisdiction-ish name superseded by C4 `country` | **Fix in RC2** → `region_deprecated` (retire; drop in v1.0.x after backfill verification) |
| `document_type_categories.default_defra_activity_type` | Rule 4 residue | **Fix in v1.1** → `default_activity_type`. Does not clear the "materially improve" bar pre-launch: it is a seed-lookup label, not a live FK path, and renaming churn breaks app/seed references for cosmetic gain. Scheduled with the v1.1 IE factor load so all factor-surface naming lands once. |
| `audit_trail` vs `audit_logs` | Near-synonymous pluralisation for different responsibilities | **Accept-with-reason** — both names are load-bearing in app code; the `_trail`/`_logs` distinction is documented in Rule 3 and is now the sanctioned convention. |
| `customer_communication` | Rule 2 — singular name on an entity table | **Accept-with-reason** — reads as a mass noun ("communication record"); rename churn not justified. Revisit only if a sibling comms table appears. |
| `customer_review_log.file_id`, `document_activity_log.file_id`, `draft_entries.file_id`, `emissions_logs.file_id` | Rule 5 — polymorphic FK named `file_id` rather than `<entity>_id` | **Accept-with-reason (v1.0); review v1.1** — the polymorphism is the real design question, not the name; renaming four hot columns pre-launch fails the materially-improve bar. |
| `consultant_tasks.task_title`/`task_description`, `internal_tasks.task_title`/`task_description` | Redundant `task_` prefix inside a `*_tasks` table | **Accept-with-reason** — disambiguates against joined task tables in reporting queries; harmless. |
| `organizations` (~65 columns) mixes `text` and `varchar` for like fields | Type inconsistency, not a naming violation | **Accept-with-reason** — types are out of scope for the naming standard; normalisation is a v1.1 type-hygiene pass, not a rename. |
| `upload_batches.created_by_user_id` vs `created_by` | Rule 5 — two actor columns, one concept | **Fix in v1.1** — merge into `created_by`; logged with the §2 tidy-up note. Not RC2: both are read by live code and the merge is behavioural, not cosmetic. |
| `messages` read-state trio (`is_read`/`read_at` vs `read_by`/`read_count`/`last_read_at`) | Rule 6-adjacent redundancy | **Accept-with-reason** — 1:1 vs group semantics; consolidation is evidence-gated for v1.1. |
| `waitlist`, `glossary`, `user_presence`, `typing_status` | Rule 2 — singular names | **Accept-with-reason** — sanctioned singleton/state exceptions under Rule 2. |
| `staff_workload.date`, `staff_daily_performance.date`, `team_performance.date` | `date` is a type name used as a column name | **Accept-with-reason** — unambiguous in context and widely referenced; renaming to `metric_date` is v1.1-optional, not required. |

### 5(c) Five-year future-proofing confirmation

This standard is durable for at least five years because its load-bearing names are jurisdiction-, vendor- and standard-neutral at exactly the points where the business will change. The factor surface — the schema's most jurisdiction-sensitive asset — is named `emission_factors` / `emission_factor_id` / `emission_factor_used` / `default_factor_year` with jurisdiction carried as *data* (`country IN ('GB','IE')`, `factor_source`, `factor_set`), so admitting SEAI/EPA in v1.1, or any further national factor authority thereafter, is a row load and an IN-list extension, never a rename. The same pattern holds for money (ISO `currency` codes constrained by K2, neutral `tax_rate`/`tax_region` rather than `vat_*` on forward-looking surfaces), for addresses (`postcode`/`eircode` duality generalises to any future `postal_code` abstraction without renaming history), and for reporting (`ghg_protocol_*`, `esrs_e1_category`, `issb_category` are additive label columns on reference tables, so a new disclosure standard is a new column on a small reference table, not a refactor). Rule 4's ban on embedding authorities in identifiers, Rule 7's unit-in-name discipline, and Rule 9's stage prefixes together mean that the schema's names describe *what things are* rather than *who issued them or which market launched first* — which is precisely the property a UK-primary-then-Ireland, then-wider-Europe product needs its database to have.

*Verification: §2 covers all 100 tables in the dump (stated and counted in §2); every non-KEEP verdict carries a Why and a timing; all verdicts are consistent with the frozen R1–R3 / C1–C10 approvals and the C11/T2/T3/ADR deferrals and rejections; no SQL appears in this document.*

## Section 6 — Performance Review

*Scope: Supabase/PostgreSQL 16, multi-tenant with row-level security. The index posture below restates the frozen Structural Change Review verdicts — five targeted index families (I1–I5, roughly 18 indexes once the UNIQUE-backed indexes of the constraint set are counted), the I6 blanket "index every FK" programme REJECTED, the blanket-jsonb GIN programme REJECTED, and partitioning REJECTED with a documented revisit trigger. Nothing in this section resurrects a rejected item. All builds are CONCURRENT, each in its own transaction, per the P3 phase of the hardening plan; every family carries the migration-file verification caveat (the schema dump showed no indexes, so each family may collapse from "build" to "verify"). All volume figures are stated assumptions, not measurements.*

### 6.1 Approved index register

The register admits only indexes serving actual v1.0 query paths: RLS tenant joins, queue claiming, dedup lookups, unread counts and search. Anything else failed the real-value bar and was rejected (I6) or deferred evidence-gated to v1.1.

| Index family | Target table / columns | Type | Query it serves | Why it earns its place |
|---|---|---|---|---|
| I1a | `customer_documents(organization_id, created_at DESC)` | Composite B-tree | Document list screen (tenant-scoped, most recent first) | Every document screen and every RLS policy joins on `organization_id`; the DESC ordering matches the dominant list query on the primary pipeline entity. Without it, the launch's busiest screen seq-scans a growing table. |
| I1b | `emissions_logs(organization_id, start_date)` | Composite B-tree | Emissions aggregations and period rollups (SECR/UK reporting flow) | The core reporting read path: tenant-scoped aggregation over a date range. Index-serves the product's headline numbers and the RLS join simultaneously. |
| I1c | `suppliers(organization_id)` | B-tree | Supplier pickers, supplier-scoped lists | Tenant picker queried on every upload and mapping screen. |
| I1d | `facilities(organization_id)` | B-tree | Facility pickers, site lists | Same tenant-picker shape as I1c; small table now, but the index is the discipline that keeps the join constant as facilities accrete. |
| I2a | `document_processing_queue(status, created_at)` WHERE status in the unclaimed/active set | Partial composite B-tree | Worker claim polling (claim oldest unclaimed item) | The single hottest read pattern in the system: workers poll continuously, and an unindexed claim query seq-scans the whole history of completed work on every poll. The partial keeps the index small and hot — completed rows never enter it. |
| I2b | `processing_queue(queue_status, …)` WHERE unclaimed/active | Partial composite B-tree | Ops-queue claim polling | Same claim shape on the ops/manual processing queue; decouples worker throughput from table age. |
| I2c | `report_generation_queue` status path | Partial B-tree | Report-generation worker polling | Lower volume than I2a/I2b but identical access shape; same justification at smaller scale. |
| I3a | `messages(conversation_id, created_at)` | Composite B-tree | Support-chat thread rendering | Per-page-load query on a committed v1.0 screen; timeline ordering is the natural index shape. |
| I3b | `conversation_participants(conversation_id, user_id)` | Composite B-tree | Participant resolution on every thread view and message insert | Stops the participant join seq-scanning; also the lookup path for unread-state derivation. |
| I3c | `notifications(recipient_id)` WHERE unread (`is_read = false`) | Partial B-tree | Notification badge / unread count | A badge count on every page load must not scan the full notification history; the partial indexes only what the badge can ever count. |
| I4 | `consultant_firm_members.client_access` | GIN (uuid array) | Consultant RLS evaluation (is this client org in the consultant's access array?) | The sole justified GIN in v1.0. The array is ADR-locked (junction-table replacement rejected), so the security predicate cannot B-tree; without the GIN every consultant RLS check seq-scans membership rows. Low-churn table, so GIN write amplification is acceptable. |
| I5a | `suppliers.name` | Trigram (`pg_trgm`) | Supplier autocomplete, "did you mean?" duplicate prompt | The soft control complementing the hard identifier uniqueness of the constraint set — prevents the "City Electrical 2" workaround pattern without outlawing legitimate same-name suppliers. |
| I5b | `suppliers.vat_number` | Trigram (`pg_trgm`) | Fuzzy identifier matching at supplier entry | Near-duplicate VAT detection at entry time. |
| I5c | `organizations.name` | Trigram (`pg_trgm`) | Org autocomplete (consultant/staff screens) | Same autocomplete justification; may land in the v1.0.x window rather than launch day, as it serves UX, not correctness. |

Register count: 16 targeted indexes in I1–I5, plus the UNIQUE-backed indexes below — the "~18 targeted indexes" headline once shared paths are collapsed. Deferred without prejudice (evidence-gated, v1.1, against query logs or committed screens): a targeted GIN on `customer_documents.extracted_data`, full-text search on `messages.content`, staff/ops composites, and non-entry-point FK indexes. The blanket jsonb GIN programme and the I6 blanket FK programme remain rejected, not deferred.

### 6.2 Index-bearing unique constraints

The uniqueness set (constraint item K5 of the structural review) is enforced by UNIQUE constraints whose backing indexes double as query-path indexes. They are counted here, not in §6.1, per the review's own accounting.

| Unique constraint | Table / columns | Lookup path it also serves |
|---|---|---|
| Membership uniqueness | `organization_members(organization_id, user_id)` | RLS membership evaluation — the most frequent security lookup in the system |
| Consultant-client link | `consultant_clients(consultant_id, organization_id)` | Consultant portal client lists |
| Billing month | `usage_tracking(organization_id, usage_month)` | Limit-check on every metered action (uploads, extractions) |
| Report version | `report_versions(report_id, version_number)` | Version resolution and `is_current` disambiguation |
| Supplier VAT (partial, WHERE NOT NULL) | `suppliers(organization_id, vat_number)` | Supplier dedup lookup at document mapping |
| Supplier company number (partial, WHERE NOT NULL) | `suppliers(organization_id, company_number)` | As above, on the second identifier |
| Factor uniqueness | `emission_factors(reporting_year, activity_type, country)` | Factor resolution in the calculation path |
| Reset token (retained per K6) | `password_reset_tokens(token)` | Token validation on the reset flow |

A name-unique on `suppliers` remains explicitly excluded (legitimate same-name suppliers exist; the trigram "did you mean?" of I5 is the soft control).

### 6.3 Expected bottlenecks at launch

Five pressure points are expected to dominate at launch volume (~50 customers; pipeline tables at low six figures; busiest log tables at low seven figures after year one — stated assumptions from the hardening plan's volume realism). None requires structural change now; each has a named mitigation already in the plan.

| Bottleneck | Where it bites | Why | Posture |
|---|---|---|---|
| RLS per-row policy evaluation | `emissions_logs`, `customer_documents`, the queue tables, `messages`, `notifications` | PostgreSQL evaluates the tenant predicate per row on every query; on large tables the predicate cost and the membership join dominate query time | I1 composites and the membership UNIQUE-backed index make the predicate index-served; K7's NOT NULL `organization_id` makes policies total functions. Watch p95 on the document list and emissions aggregation (Gate 7 load smoke). |
| Queue polling contention | `document_processing_queue`, `processing_queue` | Workers poll on a fixed cadence; concurrent claimers contend for the head of the queue, and the partial indexes only help if the claim predicate matches them exactly | I2 partials plus the skip-locked claim pattern (§6.6); Gate 7 verifies the plans use the partials — a predicate mismatch is silently unused, not an error. |
| jsonb metadata filtering without GIN | `customer_documents.extracted_data`/`mapped_data`, `emissions_logs.metadata`, `activity_logs.metadata`, audit `old_data`/`new_data` | Any filter on a jsonb key seq-scans; this is **deliberate** — the blanket GIN programme is rejected because GIN rewrites entries on every jsonb update, write-amplifying the hottest tables for zero observed key-filter queries | A targeted GIN on `extracted_data` is reconsidered only when query logs show a committed screen or worker filtering on jsonb keys (the HP-C23 evidence gate), and even then the preferred remedy is promoting the hot key to a typed column (C11, v1.1), not indexing the jsonb. |
| Trigram search cost | `suppliers.name`/`.vat_number`, `organizations.name` | Trigram similarity scans are costlier than B-tree lookups and degrade on large tables; autocomplete keystrokes multiply the query rate | Acceptable at launch volume on small master-data tables; if supplier counts grow an order of magnitude, tenant-scope the search first (the org equality prunes the trigram scan). |
| Wide-row audit tables | `audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, `review_audit_trail` and peers (9+ tables) | Rows carry multiple jsonb payloads (`old_data`, `new_data`, `changes`, `metadata`); table scans and vacuum traverse large TOAST-heavy rows, and retention DELETEs get slower as tables grow | Append-only posture (UPDATE/DELETE revoked per the audit-hardening B item) plus the retention schedule (§7); no index on the jsonb payloads — reads are time-ordered, served by the primary key and `created_at`. |

### 6.4 Large tables watchlist

Hot and growing tables identified from the schema dump, with the metric watched and the threshold that forces action. Thresholds are stated assumptions, tuned at the first quarterly review against real growth.

| Table | Why it grows | Monitoring metric | Intervention threshold |
|---|---|---|---|
| `emissions_logs` | One row per emission entry per tenant per period; grows with documents processed and manual entries | Row count per org; aggregation p95 on `(organization_id, start_date)` | >10–20M rows or aggregation p95 doubling quarter-on-quarter → partitioning revisit (§6.5) |
| `document_processing_queue` | One row per document through the AI/manual pipeline; accumulates completed history | Claim-poll latency; dead-tuple ratio between vacuums | Claim p95 > 200ms at the partial index, or vacuum pressure → retention tightening on completed rows; partitioning revisit |
| `processing_queue` | Ops/manual processing history | As above | As above |
| `processing_logs` | Step-level logging per document — highest write rate in the pipeline | Row count growth per week | 90-day retention job (already scheduled v1.0.1) missing its window or table > 10M rows |
| `messages` / `notifications` | Support chat and event notifications per user | Unread-partial size; thread-render p95 | Thread render p95 breach, or notification history degrading the badge partial → retention/archival review |
| `audit_logs` + `audit_trail` + the 9+ audit/activity family | Append-only history of every sensitive action; widest rows in the schema | Family row counts; vacuum duration; retention-job duration | Retention window cannot be met by the pg_cron jobs, or vacuum pressure → audit-archive table (T2, deferred to v1.1) activates |
| `file_attachments` | Chat/document attachments; metadata rows here, bytes in storage | Row count; storage bucket size | Storage growth per Section 7; table itself is not the pressure point |
| `login_history` / `email_logs` / `notification_delivery_log` | Per-event logging | Row counts | 12-month retention jobs (scheduled) failing to hold the line |

### 6.5 Partition candidates — frozen decision

**Decision: NO partitioning in v1.0 or v1.1 as currently scoped.** Monthly RANGE partitioning was evaluated and REJECTED (hardening plan D4; confirmed by the structural review): low-seven-figure row counts after year one are trivially served by B-trees plus retention DELETEs, and partitioning multiplies operational surface — per-partition indexes, partition-aware migration tooling, pruning edge cases — for zero measured benefit. Cheap-to-do is not worth-doing.

Future candidates, named now so the trigger is unambiguous:

1. The audit/activity log family (`audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, peers) — append-only, time-ordered, the natural RANGE shape.
2. `emissions_logs` — the largest tenant data table; partitioning key would be period date.
3. `document_processing_queue` / `processing_logs` — only if completed-row retention cannot hold the partial-index posture.

**Revisit trigger (frozen):** any watchlist table exceeding ~10–20M rows, **or** sustained vacuum pressure (autovacuum unable to keep dead tuples bounded at the tuned settings), **or** retention DELETEs that can no longer run inside their maintenance window. The trigger is re-tested at each quarterly review against measured counts, not projected ones.

### 6.6 Query optimisation guidance — principles for the application team

- **Tenant-scope every query first.** Always filter on `organization_id` equality before anything else; it makes the RLS predicate and the I1 composites work together and prunes every other access path. Never rely on RLS alone for scoping in application SQL — belt and braces are cheap at read time.
- **No `SELECT *` on hot tables.** Name the columns. The pipeline and audit tables are wide and jsonb-heavy; projecting `extracted_data`, `metadata` or `old_data`/`new_data` when the screen needs three fields toasts and detoasts megabytes per page.
- **Paginate `messages`, `notifications` and document lists with keyset (cursor) pagination**, not `OFFSET`. Deep offsets re-scan and re-sort everything skipped; the I1/I3 composites are ordered exactly for keyset use.
- **Claim queue work with the skip-locked pattern**: select the head of the unclaimed set ordered FIFO, `FOR UPDATE SKIP LOCKED`, bounded batch. Never claim with an ad-hoc status filter — the I2 partials match one predicate exactly, and a mismatched predicate silently seq-scans (Gate 7 checks the plans; CI keeps checking).
- **Never filter on jsonb keys in application queries.** If a screen needs to filter by something inside `extracted_data` or `metadata`, that is the signal to raise the typed-column promotion discussion (v1.1 evidence gate), not to ship the jsonb filter.
- **Count unread via the partial's shape** (`recipient_id` + unread flag), and prefer existence checks over `COUNT(*)` where the UI only needs a badge-or-none.
- **EXPLAIN gate in CI**: every new or changed query against a watchlist table lands with an `EXPLAIN` (analyse, buffers) captured in the pull request on a seeded database; any seq scan on `emissions_logs`, `customer_documents`, the queue tables, `messages` or `notifications` fails the gate unless explicitly waived with a reason recorded.
- **Batch writes; avoid row-at-a-time upserts on the pipeline path.** Each row write touches I1/I2/K5 indexes; batching amortises index maintenance and keeps write amplification predictable.

## Section 7 — Future Scalability

*Assumptions, stated explicitly and deliberately rough: an average organisation uploads ~50 documents/month (~600/year), producing ~600 pipeline rows and ~2,000–5,000 step-log rows/year; accumulates ~1,000–2,000 `emissions_logs` rows/year; generates ~500 messages and ~1,000 notifications/year; and every sensitive action appends to one or more audit tables at roughly 10–50 audit rows per user-day. A consultant org aggregates its client base (×10–×50 tenants' activity through one membership surface). These are planning assumptions, not measurements; the quarterly review replaces them with observed values.*

### 7.1 Scale ladder

| Scale (orgs) | What degrades or breaks | Why | Now (inexpensive) | Defer — trigger and target version |
|---|---|---|---|---|
| **100** (~launch ×2) | Nothing structural. `emissions_logs` ~10⁵–10⁶ rows; queues ~10⁵; audit family ~10⁶. All within B-tree comfort. | I1–I5 plus retention jobs are sized for this | Monitoring baselines captured at launch (row counts, p95 per watchlist table, vacuum stats) so every later threshold is judged against evidence, not vibes | — |
| **1,000** | RLS policy evaluation becomes the dominant per-query cost on `emissions_logs` and queue tables; queue polling contention rises with worker count; index bloat appears on churn-heavy partials (queue tables) and on the membership/GIN surface; storage at ~0.6M documents/year (~low-TB in buckets, stated assumption) | Per-row predicate cost scales with rows scanned; more workers × same poll cadence multiplies claim traffic; every write maintains ~5–8 indexes on the pipeline path (write amplification) | Retention jobs verified to hold completed queue rows and `processing_logs` inside their windows (v1.0.x schedule); pg_cron retention already B-class | Connection pooling (PgBouncer/Supabase pooler sizing) reviewed at ~500 concurrent tenants; targeted index consolidation if bloat measured — v1.1/v1.2, triggered by bloat ratio, not calendar |
| **10,000** | `emissions_logs` ~10⁷–10⁸ rows — partitioning revisit trigger likely fires; audit family (9+ tables) at 10⁸ aggregate — retention DELETEs strain maintenance windows and the audit-archive question (T2, DEFERRED to v1.1) becomes live; backup/restore windows lengthen beyond comfortable RTO; queue throughput needs worker autoscaling; tenant data skew (one consultant org with thousands of client tenants) makes per-tenant statistics and any per-tenant operation lumpy; anonymisation/erasure jobs against ~40 FK references stretch toward the one-month DSAR clock | Rows and TOAST volume outgrow single-table vacuum/retention economics; PITR base-backup size scales linearly; erasure touches every tenant table per request | Archival posture on the biggest log table: retention windows and the erasure runbook's FK graph kept current (already plan artefacts); nothing else inexpensive is left | Partitioning of the audit family and `emissions_logs` — trigger: >10–20M rows/table or vacuum pressure (frozen) — v1.2/v2.0. Audit-archive table (T2) — trigger: retention/vacuum pressure — v1.1+. Read replicas / reporting offload — trigger: reporting p95 contention — v2.0. Erasure-job parallelisation and a rehearsed bulk-erasure variant — trigger: rehearsal time approaching one week — v1.1 |
| **100,000** | Single-primary PostgreSQL assumption itself: connection counts exceed Supabase plan ceilings even pooled; storage at tens of TB; backup windows require continuous-archiving economics review; per-tenant RLS evaluation and index maintenance are fine per query but aggregate write amplification on the pipeline path is the ceiling; consultant-skew orgs may individually exceed the 10–20M row trigger on their own | At this scale the constraint is platform economics and operational windows, not any single index | Nothing — nothing here is inexpensive | Sharding/tenant-grouping strategy, storage tiering, possibly a second cluster per region — trigger: ~25,000 orgs or platform-limit telemetry — v2.0+ planning horizon |

### 7.2 Stress points in prose

**RLS policy evaluation at scale.** The policy model is sound and frozen; the cost is per-row predicate evaluation plus the membership/`client_access` lookup on every query. At 100–1,000 orgs the I1 composites and the membership UNIQUE-backed index keep this index-served. The risk at 10,000+ is not correctness but the aggregate: policies that join `organization_members` on every query of a 10⁸-row table demand that the membership lookup never leaves cache. Recommendation NOW: capture the Gate 7 query plans as the launch baseline so any planner regression (e.g. after statistics drift) is detected against evidence. DEFER: policy simplification or cached-claims patterns — trigger: measured p95 regression attributable to the predicate — v1.2.

**Index bloat and write amplification.** Every pipeline write maintains the I1/I2 composites and partials plus the K5 UNIQUE-backed indexes; the queue partials churn as rows transition status (a row leaves the partial on completion — the partial self-heals by design). GIN write amplification exists only on the low-churn `client_access` column, which is why it was the sole GIN admitted. NOW: include index bloat ratio in the launch monitoring baseline. DEFER: reindex scheduling and any index consolidation — trigger: measured bloat or write-latency regression — v1.1/v1.2.

**Queue throughput.** The claim pattern is constant-time by construction (I2 partials + skip-locked); throughput scales with workers until claim contention on the queue head becomes visible. DEFER: worker autoscaling and poll-cadence jitter — trigger: sustained claim latency or backlog age breaching the SLA definitions already in `sla_definitions` — v1.1.

**Audit-log growth (9+ tables).** The per-domain taxonomy is ADR-frozen and consolidation is rejected. Growth is unbounded by design (append-only evidence); the bound is retention. NOW (inexpensive): land the v1.0.x retention schedule and confirm the audit privilege-hardening (no UPDATE/DELETE) so the retention DELETEs are the only writer of history. DEFER: the audit-archive table (T2) — **kept as DEFERRED to v1.1 with its trigger** (measured log growth or vacuum pressure, the same revisit trigger as partitioning); unified read-only view (HP-C7) — v1.1.

**Storage growth (documents).** Metadata lives in the database; bytes live in Supabase Storage. At ~0.6M documents/year per 1,000 orgs (assumption), bucket size — not table size — is the cost driver, and `file_attachments`/`customer_documents` rows stay modest. NOW: `retention_until` on the document class (already B-class) so lifecycle policy exists before the data does. DEFER: storage tiering/lifecycle rules — trigger: storage cost trajectory at the first annual review — v1.1+.

**Connection pooling / Supabase limits.** Supabase plan ceilings on connections and compute bind before the schema does. NOW: nothing beyond using the platform pooler correctly (workers and API on pooled connections; no long-lived idle transactions — an app-team rule, free). DEFER: plan-tier and pooler sizing review — trigger: ~500 concurrent tenants or pooler saturation telemetry — v1.1/v1.2.

**Tenant data skew.** One consultant org aggregating thousands of client tenants concentrates membership checks, `client_access` array evaluations and list queries. The I4 GIN is exactly the mitigation for the security predicate; list-level skew is absorbed by the tenant composites. NOW: nothing. DEFER: per-tenant statistics review and possible pagination hard-limits on consultant portal surfaces — trigger: measured skew (top-tenant row share > 10× median) with latency impact — v1.1/v1.2.

**Backup/restore windows.** PITR base backups grow linearly with data; restore rehearsal time is the honest metric. NOW: residency verification already gates launch (P5); add a timed restore rehearsal to the first quarterly review — inexpensive and evidence-producing. DEFER: restore-window objectives and any archival-tier backup strategy — trigger: rehearsal time exceeding the recovery objective — v1.1+.

**Anonymisation/erasure duration at scale.** The anonymise-in-place runbook touches ~40 FK references per user; per-request duration grows with tenant history, and the statutory clock does not. NOW: the procedure is launch-gated and rehearsal-timed (P5) — already the plan. DEFER: parallelised/batched erasure variant and a per-tenant data-retention sweep that shrinks what erasure must touch — trigger: staging rehearsal time trending toward one week per request — v1.1.

### 7.3 Recommendation summary

**Inexpensive now-items (approved):** monitoring baselines at launch (row counts, p95 per watchlist table, index bloat ratio, vacuum stats); retention schedule and pg_cron jobs per the v1.0.x window (archival posture on the biggest log tables is retention, not new structure — the audit-archive table itself stays DEFERRED to v1.1 with its growth/vacuum trigger); Gate 7 query plans captured as the regression baseline; one timed restore rehearsal per quarter; pooler discipline as an app-team rule.

**Everything else is deferred with a named trigger and target version** — partitioning (>10–20M rows/table or vacuum pressure; v1.2/v2.0), audit-archive table (T2; measured growth or vacuum pressure; v1.1+), targeted GIN on `extracted_data` (query-log evidence of jsonb key filtering; v1.1, with typed-column promotion preferred), read replicas (reporting contention; v2.0), connection/plan scaling (pooler saturation; v1.1/v1.2), erasure parallelisation (rehearsal time → one week; v1.1), storage tiering (annual cost review; v1.1+), and sharding/second-cluster planning (~25,000 orgs or platform-limit telemetry; v2.0+). No rejected item — blanket GIN, the I6 index programme, partitioning now — is resurrected anywhere in this ladder; each appears only as a triggered revisit, exactly as the structural review froze it.

## Section 8 — Security Review

This section records the security posture of the RC2 freeze as approved, not as audited. Every posture below is either already shipped in the RC1 migration package (files 001–006, verified by 007) or scheduled against a named release window in the Production Hardening Plan (§3/§4/§7). Nothing here re-opens a triaged decision: rejected mechanisms stay rejected, deferred mechanisms stay deferred, and each entry names the control that actually ships instead.

### 8.1 Row-Level Security — approved posture

RLS is the tenant-isolation boundary and its RC1 posture is frozen as-is for RC2. Approximately 160 policies cover the 36 tenant tables (four CRUD policies each), plus owner/scoped policies on `organizations`, `users` and `notifications`, and read policies on the ten reference tables. Two SECURITY DEFINER-style helpers, `is_org_member(uuid)` and `is_org_active(uuid)`, carry the predicates so policy bodies stay uniform and auditable.

| Posture element | Approved behaviour |
|---|---|
| Tenant isolation | Every tenant-table policy filters on `organization_id` via `is_org_member()`; consultant access adds the `consultant_clients` grant union and the `consultant_firm_members.client_access` array predicate (GIN-backed) |
| Suspend predicate | Write policies require `organizations.is_active = true`; suspending an organisation blocks member writes while reads continue — the churn lever that never deletes audit evidence |
| Organisation creation | Deliberately service-role only — no INSERT policy for `authenticated` on `organizations` |
| Verification gate | 007 §6a (no RLS-enabled table without a policy) and §6b (no org-bearing table without RLS) must both return empty; the Gate 4 penetration matrix must show zero cross-tenant rows for customer, consultant, staff and service roles |

**Rule: RLS is never weakened.** A policy found too tight is fixed by correcting the predicate or the data, never by disabling RLS, adding `FORCE ROW LEVEL SECURITY` exceptions, or widening to `USING (true)`. One cross-tenant sighting is a reportable ICO/DPC incident; the enabled-but-no-policy gate exists precisely because a silently unprotected table fails invisibly at demo scale and publicly in production.

### 8.2 Permissions — service-role versus authenticated paths

Two database roles carry the whole permission model, and the boundary between them is an enforcement rule, not a convention.

| Role | May do | May never |
|---|---|---|
| `authenticated` | Read/write own-tenant rows under RLS; execute `is_org_member`/`is_org_active`; execute `anonymise_user` only under the guarded self-service path | Touch another tenant's rows; create organisations; bypass the suspend predicate |
| `service_role` | Bypass RLS for server-side, worker, migration and erasure paths; execute all four RC1 functions; insert into audit/append-only tables | Appear in any client bundle, browser, mobile app or user-facing configuration |

Workers connecting as `service_role` **must filter `organization_id` in code** — the role bypasses the boundary, so the discipline moves to the application, and the Gate 4 matrix includes a service-role row to prove the filter exists. PUBLIC is revoked on all four RC1 functions. Privilege hardening (revoking UPDATE/DELETE on the append-only audit tables; dropping `updated_at` from them so no `trg_set_updated_at_*` trigger touches them) is a B-window item landing v1.0.1 — approved, scheduled, and not launch-gating.

### 8.3 JWT — platform ownership

JSON Web Tokens are owned end-to-end by Supabase Auth. The database performs no app-level JWT handling: no token minting, no signing-key storage, no custom claim manipulation in the application schema. Session and membership claims reach policies through Supabase's request context (`auth.uid()`), which is what `is_org_member()` reads. The corollaries are equally fixed: `users.password_hash` is dead-columned and never written (Supabase Auth is the IdP — the A-class ownership decision); per-user 2FA/lockout columns are REJECTED as parallel auth state (structural review C14), with TOTP and lockout belonging to the platform's `auth.mfa_*` responsibility; and the global `two_factor_required` flag is marketed honestly as a configuration intent, not an enforced control, until the platform feature ships.

### 8.4 Service Role — permitted usage register

The service role is the most powerful credential in the system and its permitted call sites are enumerated, not implied:

| Permitted use | Constraint |
|---|---|
| Organisation creation | Sole INSERT path into `organizations` (§8.1) |
| Queue workers (`document_processing_queue`, `processing_queue`, `report_generation_queue`, notification delivery) | Must filter `organization_id` in code; claim predicates must match the I2 partial indexes exactly |
| Erasure actor | `anonymise_user(uuid, uuid, text)` invoked only via the approved runbook; actor guard admits self, active staff, or service context |
| Migrations and data loads | Never run as a user-facing session |

The service key is never exposed client-side — not in the web bundle, the mobile app, environment-derived client configuration, or error telemetry. Suspected exposure is treated as a credential compromise: rotate, then investigate.

### 8.5 Audit — append-only, honestly told

The existing per-domain audit/activity log family (`audit_logs`, `audit_trail`, `activity_logs`, `processing_audit_trail`, `review_audit_trail`, `user_activity_log`, `staff_activity_log`, `login_history` and peers) is kept: the per-domain taxonomy is a frozen ADR and consolidation is rejected (D6). The six append-only log tables deliberately carry no `set_updated_at` trigger (007 §7c must remain empty).

**Hash-chain tamper-evidence remains REJECTED (D5), and RC2 does not resurrect it.** The reason is evidentiary, not effort: the chain's verifier is the same principal as its writer (the service role / DBA can rewrite rows and re-hash the chain), so the construction proves nothing to an external auditor — security theatre. The honest storey ships instead: revoke UPDATE/DELETE on the audit tables (B-window privilege hardening, v1.0.1), no `updated_at` on append-only tables, and point-in-time-recovery backups. Genuine cryptographic tamper-evidence requires external anchoring and is a v2.x conversation.

### 8.6 GDPR — erasure and DSAR posture

The approved erasure model is **anonymise-in-place**, shipped in RC1 as `anonymise_user()` and **launch-gated** (Hardening Plan §3 item 22): hard delete is structurally impossible against ~40 referencing foreign keys, so erasure hashes `users.email` to `deleted-<sha256>@anonymised.invalid`, sets the name to "Deleted User", nulls credentials, deactivates the account, and scrubs profile PII across the consultant/staff/beta/feedback tables while preserving `users.id` and every FK — and leaving audit rows untouched. The procedure is irreversible by design, idempotent on re-run, and callable only under the actor guard (§8.4). Gate 5 requires a timed staging rehearsal against a production-like FK graph with a clean residual-PII scan before launch; the one-month statutory clock means the rehearsal, not the first live DSAR, is where the procedure earns trust.

DSAR posture is dual-regulator: ICO (UK) as primary supervisory authority, DPC (Ireland) for the beta cohort. v1.0 obligations beyond erasure are the PII inventory (§8.10), DSAR export expiry, waitlist/beta PII purge at GA, and the residency verification (Supabase region UK-London or eu-west-1 with backups co-located — one free configuration check on which every enterprise questionnaire's residency claim depends). Erasure self-serve UI and consent/PECR capture fields stay deferred (HP-C24); v1.0 onboarding rests on contract/legitimate interest.

### 8.7 Data retention

Retention principle: **keep financial evidence for the statutory period, age out operational exhaust on schedule, and never let a retention job touch an audit-bearing row before its time.** The Companies Act 2006 baseline is ~6 years for financial records, which anchors the document/billing classes; Ireland's equivalent obligations are of the same order and the single schedule serves both markets. Operational logs age out far sooner: `processing_logs` 90 days; login/email logs 12 months; activity logs 12–24 months; audit tables 24 months. `retention_until` rides the document class so customer evidence carries its own expiry.

The retention pg_cron jobs are a **B-window item (v1.0.1, first weeks post-launch)** — the Hardening Plan's deliberate inversion of the audit's rating: on empty tables nothing ages out for months, so a cron job cannot be a day-one gate, while the erasure procedure (which can be demanded on day one) was promoted to A. Jobs run in small batches with dry-run counts first; rollback is dropping the job. Monthly RANGE partitioning as an alternative retention mechanism stays rejected (D4): low-seven-figure row counts after year one are trivially served by B-trees plus retention deletes, with a documented revisit trigger above 10–20M rows per table.

### 8.8 Soft delete — DEFERRED, and staying deferred

**Decision: soft delete (`customer_documents.deleted_at`) remains DEFERRED per the structural review (C13) and the Hardening Plan B-window; RC2 does not ship it and this document does not resurrect it.** The reasoning stands as written: the change is Small structurally but Medium application-wide — every document read path must gain filter discipline, and partial adoption leaks deleted rows into reported totals. At pre-revenue volumes nothing is unrecoverable via backups, so the undo path does not gate launch. What v1.0 does instead: tenant lifecycle is handled by `organizations.is_active` / `organizations.archived_at` (suspend preserves all rows; archive is deliberate and communicated), document lifecycle by the `customer_documents.status` vocabulary (`rejected`/`failed` terminal states), and disaster recovery by PITR backups. The C13 target window is early in the v1.0.x hardening cycle, while the table is young — the earliest safe moment, not a silent cancellation. RC2's verification obligation is negative and cheap: confirm no `deleted_at` column exists on `customer_documents`.

### 8.9 PII — register and classification

The PII register below is the v1.0 inventory the compliance pack maintains; classification drives masking, retention and erasure scoping.

| Class | Definition | Tables/columns (principal, not exhaustive) |
|---|---|---|
| **Identity** | Names a natural person | `users.email`, `first_name`, `last_name`; `staff_profiles.email`; `consultant_profiles` name/contact columns; `beta_users`, `waitlist` emails |
| **Credentials/secrets** | Grants access if disclosed | `consultant_profiles.api_key` (hashed, RC2 fix), `password_reset_tokens.token`, `user_invitations.token` (hashed); `users.password_hash` (dead-columned); `auth.magic_token` |
| **Financial-personal** | Payment/banking data | `suppliers.bank_name`, `bank_account`, `iban`, `swift_code`, `sort_code` (RC1); `consultant_billing` |
| **Behavioural** | Reveals activity patterns | `login_history` (incl. `ip_address`), `user_activity_log`, `staff_activity_log`, `activity_logs` |
| **Customer business data** | Tenant-confidential, not personal | `customer_documents` + `extracted_data`, `emissions_logs`, `organization_metadata`, `organizations.registered_address` |
| **Operational exhaust** | Short-retention telemetry | `processing_logs`, `email_logs`, `typing_status`/`user_presence` (interim purge until the Realtime migration, HP-C21) |

Erasure scope follows the Identity and Credentials classes (`anonymise_user` coverage); retention classes follow §8.7; the Financial-personal class carries the §8.11 masking/encryption posture. `ip_address` standardisation on `inet` is deferred (HP-C4) and rides the v1.1 retention work.

### 8.10 Secrets — plaintext fixes approved, envelope encryption deferred

| Item | Status | Detail |
|---|---|---|
| `consultant_profiles.api_key` plaintext | **Fix approved (A)** | SHA-256 hash + lookup prefix + rotation columns; rollback is roll-forward — re-issue keys, never reverse |
| `password_reset_tokens.token` plaintext | **Fix approved (A)** | Hashed; UNIQUE stays on `token`, dropped on `user_id` (closes the reset-DoS); latest-valid-wins in the app |
| `user_invitations.token` plaintext | **Fix approved (A)** | Hashed; `pending_invites` (the weaker parallel table — no token, expiry or status) is write-blocked, `user_invitations` canonical |
| Bank details at rest | **Masking approved (B-window, v1.0.2)** | API responses mask to last-4; storage untouched in v1.0 |
| Vault/KMS envelope encryption for bank columns | **Deferred (HP-C30, v1.1)** | Needs a vault-versus-KMS provider decision that must not be rushed inside a launch sprint |

Rationale for the A rating on hashing: plaintext credentials defeat RLS — any escaped backup, verbose log or service-role context yields live keys, and the first such escape converts a marketing promise into a reportable incident.

### 8.11 Uploads

Duplicate detection is **approved and shipped**: `customer_documents.file_checksum` (SHA-256) gives deterministic duplicate detection on the primary pipeline entity; hard UNIQUE enforcement stays deferred (HP-C2) until the duplicate-resolution UX exists in v1.1, because rejecting legitimate re-uploads before then punishes customers for the pipeline's own re-processing. File-type and MIME validation is an **API-layer responsibility by design** (the layering rule: integrity in the database, formats in the application — D1/K9 stay rejected); the database's upload-side obligations are structural only: `file_attachments.file_size` widened to int8 (the 2 GB int4 overflow was reachable by invoice bundles and would have failed the upload at the customer's highest-value moment) with non-negative size CHECKs, and queue rows landing with non-NULL `organization_id` and a valid status. Size limits are enforced at the API/storage layer against per-plan policy, not by the schema.

### 8.12 Storage buckets — posture statement

Supabase Storage follows the same tenancy discipline as the tables. Posture: **all customer-document buckets are private** (no public buckets for tenant content); **object paths are tenant-prefixed** (`<organization_id>/…`) so path layout mirrors the RLS boundary and a path alone can never guess another tenant's object; and **RLS on `storage.objects`** enforces the same membership predicate as the tables, with service-role-only writes from the ingestion workers. Bucket policies are verified in the same Gate 4 exercise as table policies — storage is not a side-door around the matrix.

### 8.13 Signed URLs

All client access to stored documents is via **short-expiry signed URLs** — minutes, not hours — generated server-side after an authorisation check against the requesting user's membership and role. Consultant access is **scoped to the `consultant_clients` grant set**: a consultant receives signed URLs only for tenants appearing in their grants (mirroring the §8.1 policy union), never for the firm-wide `client_access` superset without a corresponding grant. URLs are single-purpose (one object, one operation), never logged in full, and regeneration is cheap so expiry is kept aggressive. Staff-side document access rides the same mechanism — no persistent public or long-lived URLs exist anywhere in the product.


## Section 9 — Migration Impact

Every RC2 register entry is classified below for migration risk on the launch database (seed-scale to early tenant data, PostgreSQL 16 on Supabase). The classification considers data/table rewrite cost, lock duration, NOT NULL on populated tables, renames breaking application code, RLS enablement changing access behaviour, and irreversibility. Scale: **SAFE** (additive, transparent, trivially reversible) — **LOW RISK** (small, bounded, reversible) — **MEDIUM RISK** (backfills, rewrites at seed scale, breaking-but-coordinated renames, constraint validation against live values) — **HIGH RISK** (irreversible or tenancy-breaking without a rehearsed gate) — **CRITICAL** (changes access behaviour for every request; launch-stopping if wrong).

| RC2 ID | Change (short) | Classification | Why |
|---|---|---|---|
| RC2-001 | Rename `defra_conversion_factors` → `emission_factors` | HIGH RISK | Metadata-only (no table rewrite), but instantly breaks every query, ORM model, view and seed referencing the old name; a missed reference surfaces only at runtime. Mitigated by one coordinated deploy and migration-file inspection for view/function/policy references. |
| RC2-002 | Rename `emissions_logs.defra_factor_id` | MEDIUM RISK | Metadata-only rename on the hottest consumer table; breaking for reporting/exports/pipeline code but the reference surface is enumerable and pre-launch. |
| RC2-003 | Rename `defra_factor_used` → `emission_factor_used` on `document_processing_queue` and `manual_extraction_items` | MEDIUM RISK | As RC2-002, narrower surface (pipeline, manual-extraction path and audit display); the second table rides the same migration and adds no new lock or deploy step. |
| RC2-004 | Rename `organizations.default_defra_version` | LOW RISK | Few readers (onboarding defaults, report generation); mechanical rename riding the same release. |
| RC2-005 | Retire `region` → `region_deprecated` | LOW RISK | Non-destructive rename; values preserved and mapped into `country`; reversal is a single rename back. |
| RC2-006 | Add `facilities.eircode` | SAFE | Nullable additive column; no rewrite, no lock beyond the brief catalogue update. |
| RC2-007 | Drop `postcode` NOT NULL | LOW RISK | Instant catalogue change; widens accepted states, with the only harmful new state closed by RC2-018. |
| RC2-008 | Add `organizations.is_active` | LOW RISK | NOT NULL with DEFAULT true plus trivial backfill on a small table; lock is brief at org-table size. |
| RC2-009 | Add `organizations.archived_at` | SAFE | Nullable additive column. |
| RC2-010 | Add `consultant_billing.currency` | LOW RISK | Add, default, backfill 'GBP' on a small billing table; assumption validated pre-launch. |
| RC2-011 | Add five `emission_factors` provenance columns | LOW RISK | Nullable adds plus a one-statement backfill on a small factor table; `country` feeds RC2-019/RC2-026 later. |
| RC2-012 | Add `emissions_logs.unit`/`scope` | MEDIUM RISK | Derived backfill via the factor join can mislabel history if wrong; seed-scale volumes keep the cost low, but the staging data audit is a hard gate. |
| RC2-013 | Add `customer_documents.file_checksum` | SAFE | Nullable additive; existing rows stay NULL with no consequence. |
| RC2-014 | Widen `file_attachments.file_size` to int8 | MEDIUM RISK | Full table rewrite — trivial at pre-launch row counts, which is precisely why it ships now; a year later this same change is Large. Rollback is lossy above int4 max. |
| RC2-015 | Add `suppliers.sort_code` | SAFE | Nullable additive. |
| RC2-016 | Add `facilities.meter_mpan_mprn` | SAFE | Nullable additive. |
| RC2-017 | Add two `organization_metadata` sqm columns | SAFE | Nullable additive. |
| RC2-018 | Presence CHECK (postcode/eircode) | LOW RISK | Added NOT VALID then VALIDATE; no table lock for the add; only rejects rows no legitimate tenant has. |
| RC2-019 | Country IN-lists ×5 | MEDIUM RISK | Requires value audit and mapping ('UK'→'GB', non-market seed rows) before VALIDATE; post-constraint, previously legal writes fail — intentional, but application constants must match first. |
| RC2-020 | Currency IN-lists ×8 | MEDIUM RISK | As RC2-019, on money columns; '£'-style variants mapped before validation; a missed writer becomes a database error. |
| RC2-021 | Non-negative range CHECKs ×27 | LOW RISK | NOT VALID + VALIDATE protects existing rows; staging sweep for negatives precedes validation; correction-pattern redesign is application work already agreed. |
| RC2-022 | 0–100 range CHECKs ×7 | MEDIUM RISK | Conditional on the confidence-scale audit: if any column stores 0–1, the bounds must be reworked before VALIDATE — hence NOT VALID posture until proven. |
| RC2-023 | Status/role IN-lists ×5 | MEDIUM RISK | Vocabulary reconciliation against the application's centralised status constants is a documented pre-VALIDATE gate; an out-of-list app state becomes a database error at runtime. |
| RC2-024 | Four composite UNIQUEs | MEDIUM RISK | Pre-existing duplicates block creation; staging dedupe sweep gates; each unique-backed index also builds (non-concurrently if naively run — schedule in the constraint window). |
| RC2-025 | Supplier identifier partial UNIQUEs ×2 | MEDIUM RISK | As RC2-024; partials limit blast radius to rows with identifiers present. |
| RC2-026 | Factor natural-key UNIQUE | MEDIUM RISK | Depends on RC2-001/RC2-011 ordering and a clean (year, activity, country) sweep; duplicate factors would double-count, so the dedupe evidence is itself valuable. |
| RC2-027 | Drop UNIQUE on `password_reset_tokens.user_id` | SAFE | Relaxes a constraint — the safe direction; application adopts latest-valid-wins in the same release. |
| RC2-028 | NOT NULL `organization_id` on six tables | HIGH RISK | Backfill from parents is irreversible (un-backfilling is impossible — the pre-migration snapshot is the only path back), and NOT NULL on populated tables turns previously legal inserts into failures; verify-zero-NULLs step and insert-path code inspection are mandatory gates. |
| RC2-029 | NOT NULL + DEFAULT on hot status/flag columns | MEDIUM RISK | Backfill semantics per column (NULL → false vs true) must be deliberate; defaults preserve normal inserts but explicit-NULL writes now fail; scoped list keeps it bounded. |
| RC2-030 | FK inventory + 11 missing FKs | MEDIUM RISK | Each FK added NOT VALID then VALIDATE (no long table locks); discovery of orphans may force data cleanup before validation — that discovery is the point, but it can move the schedule. |
| RC2-031 | ON DELETE corrections to RESTRICT | MEDIUM RISK | Conditional on RC2-030's inspection — no speculative rewrites; each swap converts silent cascades into explicit delete failures the application must handle (the control working, but a behaviour change). |
| RC2-032 | Tenant composite indexes ×4 | LOW RISK | CONCURRENT builds, no table lock; transient build load only; a failed build leaves an INVALID index to drop and rebuild. |
| RC2-033 | Queue-claim partial indexes ×3 | LOW RISK | CONCURRENT builds; the real risk is silent non-use if the claim predicate drifts from the partial predicate — a Gate 7 EXPLAIN check, not a data risk. |
| RC2-034 | Messaging/notifications indexes ×3 | LOW RISK | CONCURRENT builds on moderate-volume tables. |
| RC2-035 | `client_access` GIN index | LOW RISK | CONCURRENT build; modest write amplification thereafter on a low-churn table. |
| RC2-036 | Trigram indexes ×3 | LOW RISK | CONCURRENT builds; requires RC2-038's `pg_trgm`; may slide to the v1.0.x window without correctness impact. |
| RC2-037 | FK-supporting indexes ×4 | LOW RISK | CONCURRENT builds serving the RC2-030 paths. |
| RC2-038 | Enable `pg_trgm` + `pgcrypto` | SAFE | `IF NOT EXISTS`, platform-managed extensions; no data impact. |
| RC2-039 | RLS enablement + ~160 policies + helpers | CRITICAL | Changes access behaviour on every tenant request: any `authenticated`-role path without a logged-in user (background jobs, cron, anonymous flows) now reads/writes zero rows or fails; a wrong policy is either a cross-tenant leak (launch-stopping) or a total outage for that table. |
| RC2-040 | `set_updated_at()` + up to 76 triggers | LOW RISK | Additive trigger layer with per-table NOTICE-skip; small per-row write overhead; fully removable via the name-pattern drop block. |
| RC2-041 | `anonymise_user()` erasure procedure | HIGH RISK | The function itself is additive, but its effect is irreversible by design — erased PII has no rollback; only the actor guard, the service-role execution posture and the Gate 5 staging rehearsal (including idempotence and unauthorised-actor tests) make it shippable. |

### 9.1 CRITICAL and HIGH items and their mitigations

Four entries sit at HIGH RISK or CRITICAL, and each carries a named mitigation already embedded in the release plan. **RC2-039 (RLS hardening, CRITICAL)** ships in a verify-first posture: create-if-absent policies that never drop pre-existing ones, no FORCE ROW LEVEL SECURITY anywhere, a permissions gate confirming service-role execution for workers and cron, and the Gate 4 penetration matrix (one cross-tenant row from any role is a launch-stopping failure) run before sign-off. **RC2-001 (factor-table rename, HIGH)** is mitigated by a single coordinated deploy of all rename items (RC2-001…RC2-005) with a migration-file inspection gate confirming no view, function or RLS policy references the old names — the dump is silent on all three, so inspection is the evidence, not assumption. **RC2-028 (NOT NULL `organization_id`, HIGH)** follows backfill-then-constrain strictly: backfill from parent rows, verify zero NULLs, retain the pre-migration snapshot of all six tables as the only un-backfill path, and rehearse the restore (Gate 6) before production execution; NOT VALID + VALIDATE is used wherever a constraint form permits, so existing rows are never locked behind an unproven rule. **RC2-041 (`anonymise_user`, HIGH)** is gated by the end-to-end staging rehearsal on a production-like FK graph — verifying the hash mailbox, PII scrub, FK preservation, idempotence and the unauthorised-actor raise — with invocation restricted to the approved runbook. Across the whole register the same four disciplines recur and are treated as standing gates for RC2: backfill-then-constrain (never constrain-then-hope), NOT VALID + VALIDATE (no long table locks against unproven data), verify-first FK/RLS posture (inspection before remediation, additive-only policies), and the migration-file inspection gate as "action zero" (the dump's silence on indexes, FKs, CHECKs and policies is a caveat on every count in this document, never a licence to assume absence).

## Section 10 — Final Approval Checklist

Every row must carry its named evidence before the RC2 freeze is approved. There is no partial credit: one open row is a NO-GO.

| ☐ | # | Item | Acceptance criterion |
|---|---|---|---|
| ☐ | 1 | Naming conventions | All identifiers consistent and jurisdiction-neutral post-RC1 — `emission_factors`, `emission_factor_id`, `default_factor_year` in use; no `defra_*` remnant outside the documented rename trail (RC1 §Breaking Changes 1–3) |
| ☐ | 2 | Validation layering | Database carries exactly four rule shapes — IN-lists, ranges, presence, uniqueness (53 CHECKs, 002); all format validation (VAT/MOD97, CH/CRO, postcode, Eircode shape, phone, email) confirmed at the API layer, D1/K9 not resurrected (§8.11) |
| ☐ | 3 | Tables | Table inventory matches the approved register: zero tables added, one renamed; no T1/T3 (rejected) or T2 (deferred) artefact present |
| ☐ | 4 | Relationships | All 11 F1 foreign keys validated; FK/ON DELETE inventory complete with RESTRICT/NO ACTION on financial/audit tables; staging destructive-delete rehearsal matches the inventory (Plan §7 row 10) |
| ☐ | 5 | Constraints | 53 CHECKs and 7 UNIQUEs present and validated; `password_reset_tokens(user_id)` UNIQUE dropped, `token` UNIQUE retained; violation smoke script rejects out-of-list and negative writes (007 §5) |
| ☐ | 6 | RLS | ~160 policies live; 007 §6a/§6b empty (no enabled-no-policy table, no org-bearing table without RLS); Gate 4 penetration matrix shows zero cross-tenant rows for all four roles; suspend predicate demonstrated (§8.1) |
| ☐ | 7 | Performance | 18 targeted indexes + 7 unique-backed in place; Gate 7 load smoke green — claim-query partial indexes used, p95 within target at year-one volumes; no blanket-index creep (D2/D19) |
| ☐ | 8 | GDPR | `anonymise_user` rehearsed on staging (Gate 5): timed, residual-PII scan clean, idempotent, actor guard enforced; PII register (§8.9) current; DSAR export expiry and waitlist/beta purge scheduled |
| ☐ | 9 | UK launch readiness | `country` IN ('GB','IE'), currency IN ('GBP','EUR') enforced; GB fixtures pass end-to-end; residency evidence (UK-London or eu-west-1, backups co-located) archived (Plan §7 rows 3, 4, 24) |
| ☐ | 10 | Ireland beta readiness | IE fixture green: Eircode-only facility insert succeeds, both-NULL rejected; EUR default applied; minimal SEAI/EPA core factor set loaded and the Dublin fixture's Scope 2 resolves to the IE factor (Gate 3; §11 Phase B) |
| ☐ | 11 | Seed data | Staging seed holds only GB/IE rows; out-of-market `.de`/`.fr`/`.fi`/`.ai` seed users removed; IE org + facility fixtures present; no PII-flavoured marketing seed survives to GA (Plan §7 row 11; §11 Phase B) |
| ☐ | 12 | API ready | Application enums/constants exactly match the five K4 status/role vocabularies; normalised value writes only ('GB'/'GBP'); `file_checksum` populated on ingest; signed-URL generation scoped per §8.13 |
| ☐ | 13 | UI ready | Eircode-only facility forms ship; suspend/read-only state communicated; duplicate-upload prompt wired to `file_checksum`; trigram "did you mean?" UX on supplier/org name fields |
| ☐ | 14 | Mobile ready | No service-role key in any mobile bundle (§8.2/§8.4); all document access via short-expiry signed URLs; RLS-authenticated paths only |
| ☐ | 15 | No ADR conflicts | Per-domain audit taxonomy, additive-only posture, array columns and queue design untouched; C14/D6/D7/D8/D17 rejections intact — no platform-ownership or consolidation drift (§8.5, §8.3) |
| ☐ | 16 | No DEFER/REJECT leakage | No `deleted_at` on `customer_documents` (C13 stays deferred, §8.8); no hash-chain artefacts (D5, §8.5); no regex CHECKs, no enums, no partitioning, no `country_code`, no 2FA/lockout columns, no `api_keys`/`webhook_events` tables |
| ☐ | 17 | Migration-file inspection gate passed | Gate 1 "action zero" signed note on file reconciling the schema dump against the Supabase migration files; findings re-scored against reality (Plan §7 row 1) |
| ☐ | 18 | Verification SQL green | `007_rc1_verification.sql` §3, §5, §6, §7 all pass on a production-like restore; zero unvalidated constraints, zero orphans, zero policy gaps |
| ☐ | 19 | Rollback strategy accepted | Per-file rollback/roll-forward paths (RC1 §Rollback) reviewed; Gate 6 rehearsals done — snapshot restore for the org backfill, re-issuance for credential hashing; erasure irreversibility acknowledged |
| ☐ | 20 | **Approve RC2 freeze** | Rows 1–19 all evidenced and initialled; the freeze is approved for the §11 implementation order to consume |

## Section 11 — Implementation Order

The client's 13-phase roadmap, A–M, consumed against the RC2-approved schema. Phase A takes the RC1 migration package **as-is** — files 001–006 plus verification 007 — with no re-scoping: Gate 1's reconciliation note is the only permitted amendment, and it re-points findings at evidence rather than changing the package. Phase B includes the **DEFRA/DESNZ current-year factors, the minimal SEAI/EPA core set for the Ireland beta (grid electricity, natural gas, common liquid/gaseous fuels, current reporting year), the reference data, and seed-user cleanup** — the out-of-market `.de`/`.fr`/`.fi`/`.ai` seed users are removed and only GB/IE fixtures survive. One addition to the rename migration: the R2 rename batch also covers `manual_extraction_items.defra_factor_used` → `emission_factor_used` (discovered during the RC2 column review and registered under RC2-003), which should be added to the rename migration alongside the `document_processing_queue` rename.

| Phase | Objective | Depends on | Database touchpoints | Exit criteria |
|---|---|---|---|---|
| **A — Database migration** | Deploy the RC1 hardening package to production: renames, 16 columns, 53 CHECKs, 7 UNIQUEs, 11 FKs, 13 NOT NULLs, 18+7 indexes, ~160 RLS policies, 4 functions, `set_updated_at` triggers. | Gate 1 note; Gate 2 staging data audit; Gate 6 rollback rehearsals | Migration files 001–006 applied in order; `007_rc1_verification.sql` | 007 §3/§5/§6/§7 green on production; zero breaking-change regressions in smoke suite; RLS penetration matrix clean |
| **B — Seed data** | Load factor and reference data for both markets; clean the seed set. Includes: DEFRA/DESNZ current-year factors (backfilled `factor_source`/`factor_set`), the minimal SEAI/EPA IE core set, units/document-types/glossary reference data, and removal of the `.de`/`.fr`/`.fi`/`.ai` seed users with IE org + facility fixtures added. | A | `emission_factors` (data only — structure already shipped), `units`, `document_types`, `roles`, seed block of `users`/`organizations`/`facilities` | Dublin fixture's Scope 2 resolves to the IE factor, not DEFRA; factor natural-key UNIQUE rejects a scripted duplicate; staging seed holds only GB/IE rows; Gate 3 Irish end-to-end fixture passes |
| **C — Storage buckets** | Stand up private, tenant-prefixed buckets with RLS on `storage.objects` per §8.12/§8.13. | A | `storage.objects` policies; `file_attachments`, `organization_files` path conventions | Cross-tenant signed-URL attempt fails; bucket policies verified in the Gate 4 exercise; no public bucket exists for tenant content |
| **D — Mock PDFs** | Generate representative GB/IE invoice/statement PDF fixtures to exercise the pipeline before live OCR. | A, B | `customer_documents` (fixture rows), `upload_batches`, `document_types` | Fixture set covers both jurisdictions (GB sort-code/postcode, IE Eircode/EUR cases) and exercises every `customer_documents.status` transition once on staging |
| **E — OCR** | Wire the OCR stage into the document processing queue for text extraction from uploads. | C, D | `document_processing_queue` (status transitions), `processing_logs`, `customer_documents.file_checksum` populated on ingest | Claim query uses `dpq_claim_idx` (predicate matches exactly); end-to-end fixture document moves `uploaded → processing → ai_extracted`-ready with non-NULL org; >2 GB synthetic path handled |
| **F — AI Extraction** | Land AI field extraction into `extracted_data` with confidence scoring and supplier auto-mapping hints. | E | `customer_documents.extracted_data`, `document_processing_queue` AI statuses, `ai_content_history`, 4 AI-mapping hint FKs, `suppliers` partial UNIQUEs | Extracted fixture values land in jsonb within the K3c confidence range; duplicate supplier identifiers rejected by the K5 partials; wrong-tenant mapping impossible under RLS |
| **G — Realtime Messaging** | Launch customer↔staff↔consultant messaging on the conversations model. | A | `conversations`, `messages`, `conversation_participants`, `message_activity_log`; presence tables (`typing_status`, `user_presence`) under interim UNIQUE+purge | Cross-tenant message read returns zero rows (Gate 4 class); `messages(conversation_id, created_at)` index used; unread badge path uses the unread-notifications partial index |
| **H — Notifications** | Deliver in-app and email notifications from queue and pipeline events. | G | `notifications`, `notification_templates`, `notification_delivery`, `email_templates`, `email_logs` | Every delivery row tenant-scoped and RLS-clean; dedup decision (keep one delivery table) executed per the B-window note; email log retention scheduled |
| **I — Customer Portal** | Ship the customer-facing portal: facilities, suppliers, documents, emissions dashboards. | B, E, F | `organizations`, `facilities` (Eircode path), `suppliers`, `customer_documents`, `emissions_logs` (+ `unit`/`scope`), `organization_members` | GB and IE onboarding complete end-to-end; SECR kWh totals computable without the factor join; suspend state renders read-only; portal runs entirely on `authenticated` + signed URLs |
| **J — Consultant Portal** | Ship the consultant workspace with grant-scoped multi-client access. | I | `consultant_profiles` (hashed `api_key`), `consultant_clients`, `consultant_firm_members.client_access` (GIN), `consultant_tasks`, `consultant_billing` (now `currency`-denominated) | Consultant sees exactly the granted-tenant union and nothing else (Gate 4 consultant row); `client_access` predicate resolves via GIN in EXPLAIN; no plaintext API key recoverable from a dump |
| **K — Internal Staff Portal** | Ship staff operations: manual review, QC, workload and SLA surfaces. | F, H | `processing_queue`, `manual_review_queue`, `qc_checks`/`qc_errors`/`qc_checklists`, `staff_profiles`, `staff_workload`, `sla_compliance`, `staff_activity_log` | Staff role row of Gate 4 clean; queue-claim partial indexes used by staff claim queries; erasure actor guard admits active staff per runbook; audit inserts succeed via service role |
| **L — Reports** | Generate versioned customer reports and exports from verified emissions data. | I, J | `report_templates`, `report_versions` (UNIQUE per version), `report_generation_queue`, `report_comments`, `export_history`, `emission_factors` provenance columns | Every generated figure traceable to a factor row stating unit, scope and source; regenerated report of the same version number rejected by UNIQUE; report claim query uses its partial index; GB and IE fixture reports reconcile to fixture expectations |
| **M — Public Launch** | GA cut-over: marketing purge, compliance pack closure, go-live checklist sign-off. | A–L; Section 10 rows 1–19 | `waitlist`/`beta_users` purge at GA; `system_settings` residency/backup evidence; retention pg_cron jobs armed (B-window v1.0.1) | Section 10 fully initialled (row 20); erasure rehearsal evidence archived; residency evidence in the compliance pack; out-of-market seed remnants confirmed absent in production; retention jobs scheduled with dry-run counts |

**Sequencing notes.** Phases C–F form the pipeline spine and must not be reordered; G–H are separable but H consumes G's tables. The B-window hardening items (audit privilege revocation, bank masking, retention jobs, soft-delete evaluation per C13) land in the v1.0.x releases after M, not inside any phase above — the roadmap consumes the RC2 freeze, it does not amend it. Where a phase exposes a schema need not in the approved register, the change returns through structural review; it is never improvised inside a phase.
