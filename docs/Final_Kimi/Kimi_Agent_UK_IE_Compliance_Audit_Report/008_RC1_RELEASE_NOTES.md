# CarbonTally Database v1.0 RC1 — Release Notes

## Overview

RC1 is the production-hardening migration for the CarbonTally UK launch, with Ireland beta enabled structurally. It renames the DEFRA-specific factor objects to jurisdiction-neutral names, adds the Ireland write-path columns (Eircode, provenance on emission factors, lifecycle flags on organisations), closes tenancy and integrity holes (RLS everywhere, foreign keys, NOT NULL backfills, IN-list and range constraints), and ships the approved query-path indexes and the GDPR anonymise-in-place erasure procedure. Emission factors are now v1.1-ready: `country`, `unit`, `scope`, `factor_source` and `factor_set` columns mean SEAI/EPA Irish factors can be loaded as data in v1.1 with no further schema change. Everything in this release implements an APPROVE item from `CarbonTally_v1.0_Structural_Change_Review.md` or an A-class item from `CarbonTally_v1.0_Production_Hardening_Plan.md`; every DEFER and REJECT item is intentionally absent.

## Migration Summary

All counts derived from migration files 001–006.

| Artefact | Count | Detail |
|---|---|---|
| Tables added | **0** | None approved (T1/T3 rejected, T2 deferred) |
| Tables renamed | **1** | `defra_conversion_factors` → `emission_factors` (R1) |
| Tables modified | **9** structural (001); **27** gain constraints/NOT NULL (002) | |
| Columns added | **16** | `facilities.eircode`, `facilities.meter_mpan_mprn`, `organizations.is_active`, `organizations.archived_at`, `consultant_billing.currency`, `emission_factors.unit`/`scope`/`factor_source`/`factor_set`/`country`, `emissions_logs.unit`/`scope`, `customer_documents.file_checksum`, `suppliers.sort_code`, `organization_metadata.total_floor_area_sqm`/`occupied_floor_area_sqm` |
| Columns renamed | **4** + 1 retirement | `defra_factor_id` → `emission_factor_id`; `document_processing_queue.defra_factor_used` → `emission_factor_used`; `manual_extraction_items.defra_factor_used` → `emission_factor_used` (added to the R2 batch per the RC2 freeze, RC2-003); `default_defra_version` → `default_factor_year`; legacy `emission_factors.region` retired to `region_deprecated` (non-destructive) |
| Columns re-typed / relaxed | 2 | `file_attachments.file_size` int4 → int8 (C7); `facilities.postcode` NOT NULL dropped (C1) |
| CHECK constraints added | **53** | 1 presence (postcode/eircode) + 5 country IN-lists (K1) + 8 currency IN-lists (K2) + 27 non-negative (K3a/b/d) + 7 percentage/confidence 0–100 (K3c) + 5 status/role IN-lists (K4) |
| UNIQUE constraints added | **7** | All as unique indexes (K5): org/user membership, consultant/org client, org/month usage, report/version, suppliers VAT and company number (partial, NULL-excluding), factor (year, activity, country) natural key. *Note: the seventh (factor natural key) is deliberate and is now counted in the K5 header comment.* |
| UNIQUE constraint dropped | **1** | `password_reset_tokens(user_id)` (K6 — closes reset-DoS); `token` UNIQUE retained |
| Foreign keys added | **11** | F1 verify-first set (factor/asset/unit references, document/supplier/member references, 4 AI-mapping hints, messages→conversations), all NOT VALID + VALIDATE, ON DELETE NO ACTION or SET NULL |
| NOT NULL tightenings | **13** | `organizations.is_active` (C2); `organization_id` on 6 hot tenant tables (K7); 6 status/flag columns across `customer_documents`, `document_processing_queue`, `processing_queue` (K8) |
| Indexes added | **18** + **7** unique-backed | I1 tenant composites ×4, I2 queue-claim partials ×3, I3 messaging ×3, I4 client_access GIN ×1, I5 trigram ×3, FK-supporting ×4 (003); the 7 K5 unique indexes (002) also serve lookups |
| Views | **0** | None added by this migration (confirmed by 007 §7e) |
| Functions | **4** | `is_org_member(uuid)`, `is_org_active(uuid)` (004, RLS helpers); `set_updated_at()`, `anonymise_user(uuid, uuid, text)` (005) |
| Triggers | **up to 76** | One `trg_set_updated_at_<table>` BEFORE UPDATE per mutable table with `updated_at`; 6 append-only log tables deliberately excluded; actual count depends on which candidate tables carry `updated_at` (006 skips with NOTICE) |
| RLS policies | **up to 160** | 36 tenant tables × 4 CRUD policies + 2 on `organizations` + 2 each on `users`/`notifications` + 10 reference-table read policies (004, create-if-absent; pre-existing policies stand) |
| Extensions | **2** | `pg_trgm` (pre-requisite for the I5 trigram index family, 003) and `pgcrypto` (required by `anonymise_user()` for the `sha256()` erasure email hash, 005); both created `IF NOT EXISTS` at the top of 003 |
| Enums | **0** | No PostgreSQL enums created. All value vocabularies use CHECK IN-lists by design (K4): PG enums are migration-hostile — extending a list requires `ALTER TYPE` outside a transaction and cannot be rolled back, whereas a CHECK is dropped and re-added in one migration |

## Breaking Changes

Application code must be updated for all of the following before or with this release:

1. **Renamed table** — `defra_conversion_factors` no longer exists; all queries, ORM models, and reporting SQL must use `emission_factors`. Old name fails immediately.
2. **Renamed columns** — `emissions_logs.defra_factor_id` → `emission_factor_id`; `document_processing_queue.defra_factor_used` → `emission_factor_used`; `manual_extraction_items.defra_factor_used` → `emission_factor_used` (the manual-extraction path must use the new name); `organizations.default_defra_version` → `default_factor_year`. Old names fail immediately.
3. **Retired column** — `emission_factors.region` is now `region_deprecated` and must not be read. Read `country` instead.
4. **NOT NULL tightenings** — inserts must now always supply: `organization_id` on conversations, messages, upload_batches, manual_review_queue, file_attachments, customer_verifications (previously nullable — silent tenancy hole); `status` on customer_documents / document_processing_queue; `queue_status`, `sla_breached` on processing_queue; `qc_required`, `customer_approved` on document_processing_queue. Defaults exist ('uploaded', 'pending', false) but code passing explicit NULL will now fail.
5. **IN-list vocabularies** — application enums/constants must exactly match: country ∈ {GB, IE}; currency ∈ {GBP, EUR}; processing_queue.queue_status ∈ {pending, assigned, in_progress, on_hold, completed, cancelled}; document_processing_queue.status ∈ {pending, processing, ai_extracted, manual_review, manual_extraction, qc, customer_review, approved, rejected, completed, failed}; customer_documents.status ∈ {uploaded, pending, processing, processed, manual_review, verified, approved, rejected, failed}; organization_members.role ∈ {owner, admin, member, viewer}; customer_subscriptions.status ∈ {trialing, active, past_due, paused, cancelled, expired}. Any app state outside these lists is now a database error.
6. **Value normalisation** — existing 'UK'/'£'-style values were mapped to 'GB'/'GBP' by the migration; the application must stop writing legacy variants (they will now be rejected) and must display the new codes.
7. **Facilities postcode now nullable + eircode** — forms must accept Eircode-only Irish facilities and must not require postcode; at least one of postcode/eircode is required (DB CHECK). Per-country conditional rules (Eircode required when country='IE') remain an API-layer responsibility. Format validation for Eircode/postcode stays in the API layer by design (K9 rejected).
8. **Range constraints** — emission quantities, factors, money/usage counters and file sizes must be ≥ 0; confidence scores and percentages must be 0–100. Negative correction lines are now impossible by design — corrections are positive rows with a type/flag; the application must implement corrections that way.
9. **RLS enforcement where previously absent** — **the largest application risk.** Every tenant table is now RLS-protected for the `authenticated` role. Any code path connecting as `authenticated` without a logged-in user (anonymous uploads, background jobs, cron) will now read/write zero rows or fail. All server-side, worker and migration paths **must** use the service role (which bypasses RLS) and must continue to filter `organization_id` in code. Organisation creation is intentionally service-role only — no INSERT policy for `authenticated` on `organizations`.
10. **Suspended-tenant write block** — write policies require `organizations.is_active = true`. Setting an organisation inactive blocks all member writes (reads still work). The suspend/offboarding flow must set `is_active = false` / `archived_at` deliberately and communicate the read-only state in the UI.
11. **Optional columns** — `suppliers.sort_code`, `facilities.meter_mpan_mprn`, `customer_documents.file_checksum` are additive-optional; no app change required, but upload pipelines should start populating `file_checksum` for duplicate detection.
12. **`password_reset_tokens`** — multiple outstanding tokens per user are now allowed (UNIQUE on user_id dropped); latest-valid-wins semantics must be implemented in the application.
13. **`anonymise_user` is irreversible** — erasure hashes email to a `deleted-<sha256>@anonymised.invalid` mailbox, sets name to "Deleted User", nulls credentials, deactivates the account, and scrubs profile PII across consultant/staff/beta/feedback tables. There is no rollback; invoke only via the approved runbook with actor guard (self, active staff, or service context).

## Test Plan

SQL-level checks are in `007_rc1_verification.sql` (referenced as §n below). Manual/application tests follow.

### Data integrity
- Run 007 §3 (FK inventory all validated; all orphan counts zero; org NULL counts zero), §5 (all CHECKs validated; country/currency/status violation counts zero; negative and out-of-range counts zero).
- Attempt negative `raw_quantity`, out-of-range `confidence_score`, invalid status and invalid currency inserts — each must raise a CHECK violation (manual SQL smoke).
- Attempt a duplicate (organization_id, vat_number) supplier insert — must fail with the K5 unique violation; same-name different-identifier suppliers must succeed.

### Permissions
- Confirm 004's grants: `authenticated`/`service_role` can execute `is_org_member`/`is_org_active`; only `service_role` + `authenticated` (guarded self-service) can execute `anonymise_user`; PUBLIC revoked on all four functions.
- Verify no FORCE ROW LEVEL SECURITY anywhere (004 creates none); table-owner flows unaffected.

### Workspace / tenant isolation (Gate 4 penetration matrix)
- As user A (org 1), attempt SELECT/INSERT/UPDATE/DELETE against every tenant table class scoping to org 2 — zero cross-tenant rows; every write rejected. One cross-tenant row from any role is a launch-stopping failure.
- 007 §6a must be empty (no RLS-enabled-no-policy table) and §6b empty (no org-bearing table without RLS).

### Consultant access
- Consultant user with `consultant_clients` grant: can read granted client tenant data per policy union; cannot read non-granted tenants. `consultant_firm_members.client_access` array predicates resolve via the new GIN index (check with EXPLAIN).

### Organization switching
- User with memberships in two organisations: sees exactly the union of own tenants' rows; writes carry the correct `organization_id`; switching context never leaks the previous tenant's rows.

### Supplier management
- Create GB supplier (sort_code, postcode facility), IE supplier (no sort code, Eircode facility). Trigram "did you mean?" query: `SELECT name, similarity(name, 'acme') FROM suppliers WHERE name % 'acme' ORDER BY 2 DESC` — confirm `suppliers_name_trgm_idx` in the plan.

### Document uploads
- Upload with `file_checksum` populated; re-upload same content — application duplicate prompt fires. `file_size` > 2 GB value accepted (int8). Queue rows land in `document_processing_queue` with status 'pending' and non-NULL org.

### Search (trigram)
- EXPLAIN autocomplete/fuzzy queries on suppliers.name, suppliers.vat_number, organizations.name — each must use the corresponding `*_trgm_idx` GIN index.

### Performance (Gate 7)
- EXPLAIN ANALYZE the worker claim queries at projected year-one volumes: partial index must be used — `dpq_claim_idx` for `status IN ('pending','processing','manual_review','manual_extraction','qc','customer_review') ORDER BY created_at`; `processing_queue_claim_idx` and `report_generation_queue_claim_idx` likewise. **The partial predicates must match the claim queries exactly** — if the worker uses a different status subset, align predicate or query before sign-off.
- EXPLAIN the RLS join path on customer_documents list and emissions aggregation — must use `customer_documents_org_created_idx` / `emissions_logs_org_start_date_idx`.

### Audit logging
- Posture unchanged: no new audit machinery, no hash chain (rejected). The 6 append-only log tables have no updated_at triggers by design (007 §7c empty). Confirm audit inserts still succeed via service role.

### Soft delete
- **Confirm NOT implemented** — `customer_documents.deleted_at` (C13) is deferred to the v1.0.x window. Verify no `deleted_at` column exists; deletion behaviour is unchanged from pre-RC1.

### Erasure procedure end-to-end (Gate 5)
- On staging with a production-like FK graph: call `anonymise_user(user_id)` as service role; verify email becomes `deleted-<sha256>@anonymised.invalid`, names 'Deleted'/'User', `password_hash` NULL, `is_active` false; consultant/staff/beta/feedback PII scrubbed; all FK references intact (users.id preserved); audit rows untouched. Re-run — must no-op (idempotence NOTICE). Unauthorised actor (non-staff, non-self authenticated) — must raise. Run residual-PII scan per runbook; time the execution.

### Ireland beta (Gate 3 regression fixtures)
- Register an IE organisation (country 'IE', currency 'EUR' set by application default); create a facility with **eircode only** (postcode NULL) — succeeds; both NULL — fails with `facilities_postcode_or_eircode_check`.
- Insert an IE emission factor (country 'IE', factor_source 'SEAI', EUR context) — accepted by all constraints; natural-key uniqueness applies per country.
- Exercise onboarding → upload → AI mapping → reporting for the IE fixture end-to-end.

## Rollback

Each migration file carries inline, commented rollback blocks at the relevant section; prefer fixing forward over rollback for the additive security machinery.

- **001 (schema)** — reverse renames and column drops are commented inline per change. Reverting the C4 region retirement is `RENAME COLUMN region_deprecated TO region`. Rolling back C7 (int8 → int4) is lossy if any value exceeds int4 max — verify first.
- **002 (constraints)** — every constraint is named; rollback is `ALTER TABLE … DROP CONSTRAINT IF EXISTS <name>` per item (names inline). K6 rollback recreates the `password_reset_tokens_user_id_key` unique index. K7 NOT NULL rollback is trivial (`DROP NOT NULL`) but the **backfill is irreversible — the pre-migration snapshot of the six tables is the only un-backfill path** (Gate 6 rehearsal).
- **003 (indexes)** — **non-transactional file** (CREATE INDEX CONCURRENTLY cannot run in a transaction). Rollback is `DROP INDEX CONCURRENTLY IF EXISTS <name>` per index; a failed build leaves an INVALID index — drop it and re-run. Never wrap this file in BEGIN/COMMIT or a transaction-forcing migration runner.
- **004 (RLS)** — additive; full-file rollback template at the foot of the file drops only the policies it created. Disabling RLS re-opens the dangerous state — prefer fixing forward. Never drop pre-existing policies.
- **005 (functions)** — `DROP FUNCTION IF EXISTS public.anonymise_user(uuid, uuid, text);` and `set_updated_at()` (only after 006 triggers are removed). **The erasure performed by `anonymise_user` is irreversible by design** — the Gate 5 staging rehearsal is the mitigation.
- **006 (triggers)** — commented DO block at the foot drops every `trg_set_updated_at_*` trigger by name pattern; touches nothing else.

## Known Limitations

1. **Gate 1 (migration-file inspection) still required.** The schema dump showed no indexes, FKs, CHECKs or RLS policies, but is known to be silent on them. All RC1 files are verify-first/idempotent and collapse to no-ops where the Supabase migration files already enforce an object — but the reconciliation itself ("action zero") has not been performed and may convert some "added" counts above into "verified pre-existing".
2. **K4 vocabulary reconciliation before VALIDATE.** The five status/role IN-lists are scoped from the application enumerations as currently understood; the staging audit must reconcile each list against the application's centralised status constants (adjust the list, not the data) before 002 is validated in production.
3. **Format validation lives in the API layer by design** (K9 rejected): UK company number, VAT, MOD97, postcode, Eircode routing keys, phone and email formats are NOT checked by the database. The DB enforces exactly four shapes: IN-lists, ranges, presence, uniqueness. The API validation pack is a hard launch dependency.
4. **SEAI/EPA Irish factor data load is a data task, not this migration.** The structure is ready (country/source/set columns, GB/IE IN-list, per-country natural key); Irish factor rows ship with the v1.1 data load alongside the emission-factor data audit (unit/scope population).
5. **Worker claim predicates and I2 partial indexes must match exactly** or the indexes are silently unused — verified in Gate 7, not enforceable by the migration.
6. **Confidence-score scale assumption** — K3c assumes 0–100 storage; if the staging audit finds 0–1 storage, the bounds must be revisited before tightening (NOT VALID protects existing rows until then).

---
*Release: CarbonTally Database v1.0 RC1. Migration files 001–006; verification 007; these notes 008. Source of truth: CarbonTally_v1.0_Structural_Change_Review.md (approved changes) and CarbonTally_v1.0_Production_Hardening_Plan.md (test gates, §9).*
