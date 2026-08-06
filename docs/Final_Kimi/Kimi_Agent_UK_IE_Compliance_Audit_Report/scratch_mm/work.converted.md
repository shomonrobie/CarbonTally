# CarbonTally — Migration Manifest (RC1 Package)

This manifest is the implementation roadmap the Product Owner approves before migration packages are generated and executed **one at a time, in order, each gated by the verification suite (007)**. Platform: **Supabase / PostgreSQL 16**, schema `public`, UK primary launch with Ireland beta enabled structurally. The package comprises seven files (001–006 migrations, 007 read-only verification) plus release notes (008). **Standing precondition — Gate 1 ("action zero"):** before any execution, the RC1 migration files must be inspected against the real Supabase migration history, because the schema dump showed no indexes, foreign keys, CHECKs or RLS policies and is known to be silent on them. Every RC1 file is verify-first and idempotent, so Gate 1 may convert some "added" counts below into "verified pre-existing" — that reconciliation is expected and is not a defect. One RC2 amendment is incorporated: the rename batch in migration 001 also covers `manual_extraction_items.defra_factor_used` → `emission_factor_used` (approved RC2-003, Architecture Freeze).

## 1. Execution Order and Dependencies

| Order | File | Purpose | Depends on | Transactional? | Rollback posture |
|---|---|---|---|---|---|
| 1 | 001_rc1_schema.sql | Renames (R1–R3 + RC2-003), 16 new columns, type widening, NOT NULL relaxation | Gate 1 inspection | Yes — single BEGIN/COMMIT | Inline commented reverse DDL per change; C7 reversal lossy if any value > int4 max |
| 2 | 002_rc1_constraints.sql | CHECKs, UNIQUEs, FKs, NOT NULL tightenings | **001's renames and new columns must be in place** (constraints reference final names: `emission_factors.country`, `emissions_logs.emission_factor_id`, `dpq.emission_factor_used`, `facilities.eircode`) | Yes — single BEGIN/COMMIT | Named constraints: DROP CONSTRAINT/INDEX per item; K7 backfill irreversible (pre-migration snapshot of the six tables is the only un-backfill path) |
| 3 | 003_rc1_indexes.sql | 18 indexes + 2 extensions | 001/002 final names (indexes reference `emission_factor_id`, K4-aligned partial predicates) | **No — non-transactional** (CREATE INDEX CONCURRENTLY cannot run inside a transaction); run outside the transaction batch, statement-by-statement, never wrapped by a transaction-forcing runner | DROP INDEX CONCURRENTLY per index; a failed build leaves an INVALID index — drop and re-run; file is idempotent and re-runnable |
| 4 | 004_rc1_rls.sql | RLS enablement + ~160 policies + 2 helper functions | 001 (final table/column names, `organizations.is_active` from C2) | Yes | Additive; full-file rollback template drops only policies it created; never drop pre-existing policies; prefer fixing forward |
| 5 | 005_rc1_functions.sql | `set_updated_at()`, `anonymise_user()` | **003's pgcrypto** (sha256 for the erasure email hash); 001 final names | Yes | DROP FUNCTION per item; erasure itself is irreversible by design — Gate 5 staging rehearsal is the mitigation |
| 6 | 006_rc1_triggers.sql | `trg_set_updated_at_*` on ≤76 mutable tables | **005's `set_updated_at()`**; 001 final names | Yes | Commented DO block drops every owned trigger by name pattern |
| 7 | 007_rc1_verification.sql | Read-only verification suite (10 check areas) | 001–006 applied | n/a (SELECTs and NOTICE-only DO blocks) | Nothing to roll back; run last after each package and **re-runnable at any time** |

**Batching note:** files 001 and 002 form one logical schema-and-constraint batch but are executed as **two separately reviewed steps** (002 cannot precede 001; 001 must verify clean before 002 starts). File 003 deliberately sits outside the transaction batch.

## 2. Migration 001 — Schema

**Tables affected (9 modified, 1 renamed, 0 added):** `defra_conversion_factors` → `emission_factors` (rename); modified: `facilities`, `organizations`, `consultant_billing`, `emission_factors`, `emissions_logs`, `customer_documents`, `file_attachments`, `suppliers`, `organization_metadata`, plus `manual_extraction_items` (RC2-003 rename target).

**Columns added — 16, by table:**

| Table | Columns added |
|---|---|
| facilities | `eircode` (C1), `meter_mpan_mprn` (C9) |
| organizations | `is_active` (C2; NOT NULL DEFAULT true, backfilled true), `archived_at` (C2) |
| consultant_billing | `currency` (C3; DEFAULT 'GBP', backfilled) |
| emission_factors | `unit`, `scope`, `factor_source`, `factor_set`, `country` (C4 provenance set; backfilled DEFRA-DESNZ / GB / DEFRA-`<year>`) |
| emissions_logs | `unit`, `scope` (C5; derived backfill via factor join) |
| customer_documents | `file_checksum` (C6; SHA-256 hex, deliberately not unique) |
| suppliers | `sort_code` (C8) |
| organization_metadata | `total_floor_area_sqm`, `occupied_floor_area_sqm` (C10) |

**Columns renamed (4 renames + 1 retirement):**

| Old | New | Note |
|---|---|---|
| defra_conversion_factors (table) | emission_factors | R1 — jurisdiction-neutral v1.1 enabler |
| emissions_logs.defra_factor_id | emission_factor_id | R2 |
| document_processing_queue.defra_factor_used | emission_factor_used | R2 |
| manual_extraction_items.defra_factor_used | emission_factor_used | **RC2 amendment (RC2-003)** — added to this batch |
| organizations.default_defra_version | default_factor_year | R3 |
| emission_factors.region | region_deprecated | C4 retirement — non-destructive; values folded into `country` first; drop only after consumer audit |

**Type changes (1):** `file_attachments.file_size` int4 → int8 (C7 — aligns with the int8 peer columns `document_processing_queue.file_size_bytes` / `processing_queue.file_size_bytes`; removes the 2 GB ceiling).

**NOT NULL relaxation (1):** `facilities.postcode` NOT NULL dropped (C1 — Ireland has no postcodes; the pairwise presence CHECK lands in 002).

## 3. Migration 002 — Constraints

All CHECKs and FKs on populated tables are added **NOT VALID then VALIDATE CONSTRAINT**, preceded by value-mapping UPDATEs, so existing rows are never scanned under a write-blocking lock. No format/regex CHECKs anywhere (K9 rejected — API layer owns format validation). Staging data audit (NULL counts, duplicate sweeps, value mapping) runs before this file.

| Group | Count | Target tables / names |
|---|---|---|
| Presence CHECK (C1 companion) | 1 | `facilities_postcode_or_eircode_check` — postcode OR eircode present |
| Country IN ('GB','IE') (K1) | 5 | `organizations`, `facilities`, `suppliers`, `consultant_profiles`, `emission_factors` (`<t>_country_in_list`; legacy UK/IE variants mapped first) |
| Currency IN ('GBP','EUR') (K2) | 8 | `organizations.currency`, `suppliers.payment_currency`, `document_processing_queue.billing_currency`, `customer_subscriptions.currency`, `manual_extraction_batches.currency`, `consultant_profiles.revenue_currency`, `consultant_billing.currency`, `system_settings.default_currency` |
| Non-negative ≥ 0 (K3a/b/d) | 27 | Emission quantities/factors ×3 (`emissions_logs.raw_quantity`, `emissions_logs.calculated_kg_co2e`, `emission_factors.co2e_multiplier`); supplier per-scope ×6 + `supplier_categories.default_emission_factor`; usage/money counters ×13 (`usage_tracking` ×5, `customer_subscriptions` ×4, `consultant_billing` ×4); file sizes ×4 (`file_attachments.file_size`, `document_processing_queue.file_size_bytes`, `processing_queue.file_size_bytes`, `report_generation_queue.final_report_size_bytes`) — `<t>_<c>_nonneg` |
| Percentage/confidence 0–100 (K3c) | 7 | `organization_metadata.renewable_energy_percentage`, `organization_metadata.carbon_offset_percentage`, `report_generation_queue.progress_percentage`, `customer_documents.confidence_score`, `emissions_logs.confidence_score`, `document_processing_queue.ai_confidence_score`, `document_processing_queue.ai_mapping_confidence` — `<t>_<c>_range` |
| Status/role IN-lists (K4) | 5 | `processing_queue_queue_status_in_list`, `document_processing_queue_status_in_list`, `customer_documents_status_in_list`, `organization_members_role_in_list`, `customer_subscriptions_status_in_list` (CHECKs over PG enums by design) |
| **CHECK total** | **53** | |
| UNIQUEs added (K5, as unique indexes) | 7 | `organization_members_org_user_uniq`, `consultant_clients_consultant_org_uniq`, `usage_tracking_org_month_uniq`, `report_versions_report_version_uniq`, `suppliers_org_vat_number_uniq` (partial), `suppliers_org_company_number_uniq` (partial), `emission_factors_year_activity_country_uniq` (natural key: reporting_year, activity_type, country) |
| UNIQUE dropped (K6) | 1 | `password_reset_tokens(user_id)` — closes reset-DoS; `token` UNIQUE retained |
| Foreign keys added (F1) | 11 | `emissions_logs_emission_factor_id_fkey`, `emissions_logs_asset_id_fkey`, `emissions_logs_unit_fkey` (→ units.code), `customer_documents_supplier_id_fkey`, `customer_documents_document_type_id_fkey`, `customer_documents_org_member_id_fkey`, `dpq_ai_mapped_facility_id_fkey`, `dpq_ai_mapped_asset_id_fkey`, `dpq_ai_mapped_supplier_id_fkey` (AI-mapping hints, ON DELETE SET NULL), `dpq_emission_factor_used_fkey`, `messages_conversation_id_fkey` — all NOT VALID + VALIDATE; NO ACTION elsewhere; `report_versions.report_id` intentionally omitted (no `reports` parent in dump) |
| NOT NULL tightenings | 13 | `organizations.is_active` (C2, in 001); K7 — `organization_id` on 6 hot tenant tables (`conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications`); K8 — `customer_documents.status`, `document_processing_queue.status`/`qc_required`/`customer_approved`, `processing_queue.queue_status`/`sla_breached` (with defaults) |

**Backfill-then-constrain note:** every tightening populates existing rows first (K7 derives org from parent rows where possible; the guarded SET NOT NULL raises and fails safe on any residual NULL). K7's backfill is irreversible — a pre-migration snapshot of the six tables is mandatory (Gate 6 rehearsal).

## 4. Migration 003 — Indexes

**Non-transactional file** (CONCURRENTLY): no BEGIN/COMMIT, applied statement-by-statement outside a transaction; each statement independent and idempotent.

| Family | Count | Index names |
|---|---|---|
| I1 — tenant RLS-path composites | 4 | `customer_documents_org_created_idx`, `emissions_logs_org_start_date_idx`, `suppliers_org_idx`, `facilities_org_idx` |
| I2 — queue-claim partials | 3 | `dpq_claim_idx`, `processing_queue_claim_idx`, `report_generation_queue_claim_idx` (partial predicates must match worker claim queries exactly) |
| I3 — messaging/notifications | 3 | `messages_conversation_created_idx`, `conversation_participants_conv_user_idx`, `notifications_unread_recipient_idx` |
| I4 — client_access GIN | 1 | `consultant_firm_members_client_access_gin` |
| I5 — trigram (pg_trgm) | 3 | `suppliers_name_trgm_idx`, `suppliers_vat_number_trgm_idx`, `organizations_name_trgm_idx` |
| FK-supporting (F1 companions) | 4 | `emissions_logs_emission_factor_id_idx`, `emissions_logs_asset_id_idx`, `customer_documents_supplier_id_idx`, `dpq_customer_document_id_idx` |
| **Total** | **18** | (K5's 7 unique-backed indexes were built in 002 and also serve lookups; the rejected I6 blanket programme is absent) |

**Extensions (2, created IF NOT EXISTS at the top of 003):** `pg_trgm` (pre-requisite for I5) and `pgcrypto` (required by `anonymise_user()` in 005 for the sha256 erasure email hash).

## 5. Migration 004 — RLS

Verify-first and additive only: never drops/alters/weakens an existing policy; ENABLE ROW LEVEL SECURITY where absent; CREATE POLICY only where no policy of the same name exists on the same table. One pattern throughout: `auth.uid()` membership via `organization_members`, evaluated by SECURITY DEFINER helpers (row_security off inside, search_path pinned). No FORCE ROW LEVEL SECURITY. No UK/IE policy differences.

**Helper functions (2, created here because policies depend on them):** `public.is_org_member(uuid)` — active-membership predicate; `public.is_org_active(uuid)` — tenant-live predicate (C2 suspend switch; write policies require `organizations.is_active = true`). EXECUTE revoked from PUBLIC, granted to `authenticated` + `service_role`.

| Table group | Tables | Policies per table | Naming pattern | Policies |
|---|---|---|---|---|
| Org-scoped tenant tables | 36 (every `organization_id`-bearing table per the dump, e.g. `customer_documents`, `emissions_logs`, `suppliers`, `facilities`, `organization_members`, both queues, messaging, billing, usage) | 4 (SELECT / INSERT / UPDATE / DELETE; writes also require `is_org_active`) | `<table>_tenant_select` / `_insert` / `_update` / `_delete` | 144 |
| organizations (tenant root) | 1 | 2 (member select, member update; no INSERT — org creation is service-role only) | `organizations_member_select` / `_update` | 2 |
| users | 1 | 2 (self select/update) | `users_self_select` / `_update` | 2 |
| notifications | 1 | 2 (recipient select/update) | `notifications_recipient_select` / `_update` | 2 |
| Reference tables (read-only to authenticated; writes service-role) | 10 (`activity_categories`, `document_type_categories`, `document_types`, `email_templates`, `emission_factors`, `glossary`, `notification_templates`, `roles`, `supplier_categories`, `units`) | 1 (SELECT … USING (true)) | `<table>_authenticated_read` | 10 |
| **Total** | | | | **~160** (create-if-absent; pre-existing policies stand and are validated by the Gate 4 penetration matrix) |

RLS is enabled on every table above (36 tenant + organizations + users + notifications + 10 reference); the dangerous "RLS enabled, zero policies" state is surfaced by 007 §6.

## 6. Migration 005 — Functions

| Function | Purpose | Security posture |
|---|---|---|
| `public.set_updated_at()` | Generic BEFORE UPDATE trigger function stamping `updated_at = now()`; companion to 006 | SECURITY INVOKER by design (runs with the updating role's rights) |
| `public.anonymise_user(uuid, uuid, text)` | GDPR/UK-GDPR anonymise-in-place erasure — the only approved function-level compliance artefact; **launch-gated** on the Gate 5 staging rehearsal with residual-PII scan. Derives the marker email from a SHA-256 hash of the user ID — `deleted-<sha256(user_id)>@anonymised.invalid` (005: `'deleted-' || encode(sha256(p_user_id::text::bytea), 'hex') || '@anonymised.invalid'`); sets `first_name` = 'Deleted' and `last_name` = 'User' (mirroring 005 exactly), nulls `password_hash`, deactivates the account, scrubs profile PII across `consultant_profiles`, `staff_profiles`, `beta_users`, `user_feedback`; preserves the UUID and all FK/audit aggregates (hard delete structurally impossible — ~40 referencing FK columns). Idempotent; transactional; irreversible by design | SECURITY DEFINER, pinned `search_path = public`; actor guard (data subject self-service, active staff, or service context); EXECUTE revoked from PUBLIC, granted to `service_role` + `authenticated` (guarded self-service) |

Explicitly absent: audit hash-chain functions (rejected), retention/pg_cron wrappers and soft-delete functions (deferred).

## 7. Migration 006 — Triggers

One `trg_set_updated_at_<table>` BEFORE UPDATE trigger per mutable table carrying an `updated_at` column — **up to 76 tables** (reference/config ×11, tenant core ×8, tenant business ×39, staff/QC/operations ×18; candidates missing `updated_at` are skipped with NOTICE, so the actual count is confirmed by 007 §7). Each trigger is dropped by its deterministic name and recreated (idempotent; touches nothing else).

**Deliberately excluded — 6 append-only log tables:** `activity_logs`, `document_activity_log`, `email_logs`, `processing_logs`, `user_activity_log`, `review_audit_trail` (the approved v1.0.1 item drops `updated_at` from exactly these; installing maintenance triggers now would bless UPDATEs on immutable rows).

## 8. Migration 007 — Verification

Read-only (SELECTs and NOTICE-only DO blocks); safe against production; run after 001–006, before the Gate 4 penetration matrix and application smoke tests; **re-runnable at any time**. The 10 check areas:

| § | Check area | Pass criterion |
|---|---|---|
| 1 | Renames (R1–R3 + region retirement) | Old names absent; 7 expected new objects present |
| 2 | New columns (C1–C10) | 16 rows with expected nullability; `file_size` = bigint; `postcode` nullable |
| 3 | Foreign keys (F1) | 11 FKs validated; zero NOT VALID constraints schema-wide; all orphan counts 0; K7 NULL-org counts 0; K6 user_id uniqueness gone, token unique retained |
| 4 | Indexes | All 18 from 003 present + 7 K5 unique-backed |
| 5 | CHECK constraints (C1, K1–K4) | All validated; country/currency/status violation, negative and out-of-range counts zero |
| 6 | RLS (004) | No RLS-enabled-no-policy table; no org-bearing table without RLS |
| 7 | Triggers (006) + functions (005) | Trigger coverage complete; append-only exclusions empty; 4 functions present with correct grants |
| 8 | Ireland-beta readiness | Eircode path, IE factor insert, GB/IE vocabularies accepted |
| 9 | Data preservation | Row counts before/after unchanged |
| 10 | One-line summary | NOTICE per gate; any FAIL row blocks sign-off |

## 9. Cross-Migration Dependency Notes

- **Rename-then-constrain ordering:** 002's constraints, 003's indexes, 004's policies and 005's functions all reference the final names produced by 001 (`emission_factors`, `emission_factor_id`, `emission_factor_used`, `default_factor_year`, `eircode`, `is_active`); no later file may run before 001 verifies clean. The RC2-003 rename (`manual_extraction_items.defra_factor_used`) ships inside 001 so all downstream objects see only final names.
- **pgcrypto before first `anonymise_user` execution:** the extension is created in 003; 005's function creation and any Gate 5 rehearsal invocation must follow 003.
- **K4 vocabulary reconciliation before VALIDATE:** the five status/role IN-lists are scoped from the application enumerations as currently understood; the staging audit must reconcile each list against the application's centralised status constants (adjust the list, not the data) before 002 is validated in production. The same audit gates the K3c 0–100 scale assumption.
- **Seed data is a SEPARATE future package** (Phase B: DEFRA/DESNZ current-year factors + minimal SEAI/EPA Irish core + reference data + seed-user cleanup). It depends on 001–003 only (final names, factor provenance columns, GB/IE vocabularies, factor natural-key uniqueness) — not on 004–006 — and is not part of this manifest's execution batch.
- **I2 partial-index predicates must match worker claim queries exactly** (checked in Gate 7, not enforceable by the migration).

## 10. Approval Sign-off

Approval of this manifest authorises generation and gated, one-at-a-time execution of migration packages 001–007 exactly as ordered above, subject to Gate 1 inspection as the standing precondition.

☐ Approved — Product Owner, date

---

*Counts verified against migration files 001–007 and release notes 008: 16 columns added; 1 table renamed; 4 column renames + 1 retirement (incl. RC2-003); 1 type widening; 1 NOT NULL relaxation; 53 CHECKs; 7 UNIQUEs added + 1 dropped; 11 FKs; 13 NOT NULL tightenings; 18 indexes (+7 unique-backed from 002); 2 extensions; ~160 RLS policies across 36 tenant tables + organizations + users + notifications + 10 reference tables; 4 functions (2 RLS helpers in 004, 2 in 005); up to 76 triggers with 6 append-only exclusions; 10 verification areas.*
