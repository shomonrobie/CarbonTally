# CarbonTally — Migration History Reconciliation

- **Date:** 2026-09-01
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607`
- **Task:** Read-only reconciliation of (1) current live development DB, (2) local migration files, (3) historical development work, (4) `v3_schema.sql`/schema snapshots.
- **Status:** **INVESTIGATION COMPLETE — NO DATABASE/SCHEMA/MIGRATION/CONFIG CHANGE.**

---

## 1. Executive summary

The current CarbonTally development database (local Supabase stack, Postgres `127.0.0.1:54426`, PG 17.6, db `postgres`, project `carbon_ledger`) **contains the complete schema end-state of the historical migration chain**:

- **115 public tables in the live DB = exactly the 115 tables defined across all 41 migration files** (0 missing, 0 extra).
- Every sampled migration end-state object exists in the live DB (RC2 `emission_factors`, V3M1 `processing_entities`, V3M3 `customer_factors`, V3M5 `issues`, V3M7 `vehicles`, V3M8 messaging uniqueness, V3M9 `document_processing_queue`, V3M10 membership-unique index, V3M11 operational indexes, D22 `processing_assignments`, D27 lifecycle columns, D32 storage policies, D37 billing tables, P9 `is_org_consultant`).
- The live DB is a **policy superset**: it carries ~142 additional `*_tenant_*` RLS policies that came from the **Aug-20 live-schema restore** (`local_backups/carbon_tally_live_public_schema.sql`, 70 `tenant_update/delete` occurrences) and are **not** defined in the migration chain.
- **Emission-factor provenance established:** the 7,049 factors (DEFRA-2025 7,029 + SEAI-2025 20, all reporting_year 2025) were imported via **generated idempotent SQL insert scripts** (`output/sql/emission_factors.sql` DEFRA, `output/seai_2025/sql` SEAI), **not** via migrations (`emission_factors.import_batch_id` is NULL for all 7,049 rows) and **not** via the investor-demo seed (no `emission_factors` reference in `tools/seed_investor_demo/`).
- **Missing `supabase_migrations.schema_migrations` explanation:** the current DB was assembled by **restore + seed + direct migration application** (not by a single `supabase db reset`/`db push` replay), so the Supabase CLI never created the history table. The project config also has `[db.migrations] enabled = false` and was modified locally after its only commit (`2d23fb8`).

**Baseline determination: SAFE TO BASELINE at `20260831010000_v3m11_operational_indexes.sql`**, with documented caveats (policy superset; recommend a final column-level diff before recording the baseline). The three remediation migrations (`2026083102/03/04`) can safely follow that baseline — all their preconditions were verified present on the live DB.

## 2. Current database state

| Item | Value |
|---|---|
| Host / port / db / user | `127.0.0.1:54426` / `postgres` / `postgres` (API on 54425) |
| PostgreSQL | 17.6 |
| Stack / project | local Supabase `carbon_ledger` (linked ref `pvwiojoyaqywtydzcpbg`) |
| Size | 37,416,083 bytes (~35.7 MiB) |
| Public tables | 115 (all RLS-enabled; 0 forced) |
| Public RLS policies | 181 |
| Triggers / indexes / public functions | 84 / 226 / 14 |
| Extensions | pgcrypto, uuid-ossp, pg_trgm, pg_stat_statements, supabase_vault, plpgsql |
| `supabase_migrations` schema | **absent** |
| Key data | emission_factors 7,049 · organizations 975 · users 1,329 (auth.users 1,192) · consultant_clients 917 · audit_trail 440 · assets 310 · organization_files 254 · manual_extraction_items 255 · emissions_logs 100 · calculation_snapshots 100 · customer_factors 245 · facilities 157 · suppliers 156 |
| Verified backup (rollback point) | `/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump` (intact, restore-verified) |

## 3. Migration inventory (`supabase/migrations/` — 41 files)

The chain, in order:

| Group | Files | Purpose |
|---|---|---|
| Baseline | `00000000000000_init_schema.sql` | RC2/V3 baseline schema (~104 tables incl. `emission_factors`) |
| RC2 repair (8) | `20260800000000`–`20260806000000` (`rc2_schema/constraints/indexes/rls/functions/triggers/verification`) | conformance, constraints, indexes, RLS, functions, updated_at triggers, verification suite |
| V2.1 Phase 0 (8) | `20260807000000`–`20260807070000` | import_batches, emission_factors.import_batch_id, calculation_snapshots, emissions_logs snapshot, domain_events, factor_aliases, dpq workflow columns, new-table RLS |
| V3 modules (5) | `20260810000000`–`20260810050000` (`v3m1`–`v3m6`) | processing_entities, entity relationships, customer_factors, issues, entity RLS |
| D-series (10) | `20260821000000`–`20260824030000` (`d20/d15`,`d21`,`d22`,`p9`,`d27/d19`,`d32`,`d33`,`d35`,`d37-0`,`d37`) | active-consultant grant, white-label, work assignment, RLS recursion fix, customer lifecycle, storage policies, evidence traceability, onboarding, billing security + commercial billing |
| V3M7–M11 (6) | `20260825000000_v3m7_vehicles`, `20260828000000`–`20260828020000_v3m8_*`, `20260829000000_v3m9`, `20260831000000_v3m10`, `20260831010000_v3m11` | vehicles, messaging uniqueness, system_admin role, PE manager role, durable processing, membership uniqueness, operational indexes |
| **Remediation (3, not yet applied)** | `20260831020000_audit_activity_immutability`, `20260831030000_tenant_org_id_not_null`, `20260831040000_consultant_revocation_roles` | WS1/DB-0001, WS5/DB-0002, WS6/SEC-0003 |

Other migration locations: `database/rc1/` (`001–007_rc1_*`), `database/rc2/` (`000` + `001–007_rc2_*` + release notes), `database/v3/verification_v3m1_v3m2.sql`. The `supabase/migrations/` chain is the canonical chronological set.

## 4. Historical migration analysis

- Migrations were the development mechanism: Git history shows the chain committed across releases — `2d23fb8` (RC2 final baseline incl. `supabase/config.toml`), `dbe72aa` (V2.1+V3 foundation), `9458067` (D20–D37), `6148c86` (V3 Phase 1), `17665d0` (V3 phases A–C).
- Development docs confirm migration-driven schema evolution: `CarbonTally_V3_Backend_Post_Migration_Runtime_Verification_v1.0.md`, `docs/Final_Kimi/CarbonTally RC1 — Independent Database Audit.md`, `CARBONTALLY_V3_D20_D37_RELEASE_STAGING_REPORT.md` (10 migrations in the D20–D37 release), `CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT.md` (the intended local `supabase start`/`db reset` workflow and the chain as build source).
- **Conclusion: the migrations were applied to a database during development** — the chain is not hypothetical, and the absence of `schema_migrations` does NOT imply the migrations were never applied.

## 5. Git / history evidence

- `git log -- supabase/migrations/`: `2d23fb8`, `97e0f69`, `dbe72aa`, `9458067`, `077c866`, `6148c86`, `17665d0`.
- `git log -- supabase/config.toml`: only `2d23fb8` — the current config (ports 54425/54426, `[db.migrations] enabled = false`) is an **uncommitted local change** from that baseline.
- `v3_schema.sql` is **untracked** (not in Git). `CarbonTally_DB_Schema_V3M2.sql` (root) is tracked and is an older 102-table dump.
- Restore artifacts in `local_backups/` (untracked): `carbon_tally_live_public_schema.sql` (232 KB, Aug 20 13:30), `carbon_tally_live_public_data.sql` (1.86 MB, Aug 20 13:37), `local_before_live_data_restore.sql` (364 KB, Aug 20 13:49), `seed_demo_data.sql` (37 KB), plus `supabase/seed.sql` (14 KB pg_dump fragment).


## 6. Emission-factor provenance (CRITICAL)

- Current dataset: **7,049 rows** — `factor_set` DEFRA-2025 = **7,029**, SEAI-2025 = **20**; `factor_source` DEFRA-DESNZ 7,029 / SEAI 20; all `reporting_year = 2025`; scope 3/1/2/Outside = 4,090/2,549/354/56; country GB 7,029 / IE 20.
- **Import mechanism (established, not assumed):**
  - `output/sql/emission_factors.sql` — "DEFRA 2025 emission factors import (idempotent)": `INSERT … WHERE NOT EXISTS` keyed on `(reporting_year, activity_type)` → applied directly to the DB (not a migration file).
  - `output/seai_2025/{json,reports,sql}` — SEAI 2025 import artifacts.
  - `emission_factors.import_batch_id` is **NULL for all 7,049 rows** → the factors were **not** imported through the `import_batches` workflow that the Phase-0 migrations introduced; the SQL-script path was used.
  - `tools/seed_investor_demo/` contains **no** `emission_factors` references → the investor-demo seed does not supply factors.
- **Not represented by migration history:** the migration chain defines the `emission_factors` table schema (RC2 baseline) and the `import_batch_id` column (M2) but **no factor rows**. The factor dataset is external reference data applied via generated SQL.
- Integrity: count 7,049 and `md5(ordered ids)` = `93668772ba460b0d03c7d9f9029f16c9` — identical in the live DB and in the verified backup restore.

## 7. v3_schema.sql analysis

- **Schema-only snapshot:** 0 `COPY` statements (no data, no factor rows).
- **104 tables** vs 115 in the live DB — it is **11 tables behind** the current schema. The missing tables are exactly those added by post-Aug-15 migrations: `vehicles` (V3M7), `consultant_custom_domains`/`consultant_senders` (D21), `data_discovery_requests` (D35), and the 7 `billing_*` tables (D37). 0 tables present in it but absent from the DB.
- Contains RLS (179 `CREATE POLICY`), functions, triggers, constraints, comments, owner statements.
- **Not tracked by Git**; generated ~Aug 15 (before D37/V3M7–M11).
- **Conclusion: v3_schema.sql is an older, schema-only partial snapshot — it is NOT equivalent to the current DB or to the full migration chain.**

## 8. Current DB vs historical migration comparison

| Dimension | Result |
|---|---|
| Tables (migration chain vs live DB) | **115 = 115 — 0 missing, 0 extra** |
| Policies (chain ⊆ live DB) | All 43 non-remediation chain policies present; live DB carries ~142 extra `*_tenant_*` policies (from the Aug-20 live-schema restore) |
| D32 storage policies | Present in live DB (`storage.objects`) |
| V3M10 unique index / V3M11 indexes | Present |
| V3M7–V3M11 + D37 objects in Aug-20 dump vs live DB | `vehicles`, `billing_plans`, `conversation_participants` unique index, V3M11 indexes: **0 in the Aug-20 dump, present in the live DB** → these migrations were applied to this DB **after** the Aug-20 restore |
| Key columns/functions | `consultant_clients.ended_at/ended_by/lifecycle_updated_at`, `is_org_consultant`, `is_org_admin_or_owner`, `is_consultant_firm_manager` present |
| Remediation preconditions | Tenant UPDATE/DELETE policies present on the 4 audit/activity tables; `assets` 0/310 NULL; `cc_delete_own_firm`/`consultant_clients_tenant_delete` present; `is_consultant_firm_revoker` absent |


## 9. Explanation of the missing migration history

The `supabase_migrations.schema_migrations` table is absent because the current DB was **not built by a single Supabase CLI migration replay**. Evidence-supported reconstruction:

1. A **live schema + data dump** was captured (`local_backups/carbon_tally_live_public_schema.sql` + `carbon_tally_live_public_data.sql`, Aug 20) — a production/live snapshot containing the migration-chain schema of that era **plus** live-schema RLS extras.
2. The current local DB was **restored from that live dump** (`local_before_live_data_restore.sql` documents the pre-restore state; `supabase/seed.sql` and `seed_demo_data.sql` contributed further data), then the **investor-demo seed** populated orgs/users/consultants/clients, then the **factor import scripts** added the 7,049 factors, then **later migrations (V3M7–M11, D37) were applied directly** on top (proven by V3M7/V3M8/V3M11/D37 objects being absent from the Aug-20 dump but present now).
3. Because the CLI's `db reset`/`db push` replay was never the mechanism, `schema_migrations` was never created. Additionally, the current `supabase/config.toml` has **`[db.migrations] enabled = false`** (an uncommitted local change since the only commit `2d23fb8`), so the CLI would skip migrations anyway.

This is therefore the documented development workflow: **restore/seed/import + direct migration application** — not a migration-chain replay, and not "migrations never used".

## 10. Baseline determination

**SAFE TO BASELINE**

The current database demonstrably contains the intended historical schema state of the migration chain:
- Exact table-set equality (115 = 115, 0 missing / 0 extra).
- Chain-defined policies are a subset of the live DB's policies (0 missing other than the 2 not-yet-applied WS1 policies).
- Migration end-state objects (indexes, tables, columns, functions) verified present — including V3M7–M11 objects that were applied to this very DB after the Aug-20 restore.
- The live DB is a **superset** (extra tenant RLS + external data), which cannot cause the chain's state to be missing.

Caveats (do not weaken the verdict but must be handled before recording the baseline):
- Column-level equivalence was sampled, not exhaustively diffed — run a full column/constraint diff of all 115 tables against the chain immediately before recording the baseline.
- The ~142 extra tenant policies and the 7,049 factors/demo data are **not reproducible from the chain alone** — a fresh `db reset` build will differ (documented limitation, not a blocker for baselining the current DB).

## 11. Exact baseline point

**`20260831010000_v3m11_operational_indexes.sql`** — the last historical migration file before the three remediation files. The live DB contains V3M11's objects (4 operational indexes), and the chain order puts V3M10/V3M11 immediately before the remediation files. Recording the baseline as "all migrations through `20260831010000` applied" makes the three remediation files the next-pending migrations.

## 12. Can the three remediation migrations safely follow the baseline?

**YES — verified against the live DB (read-only):**

| Migration | Precondition on live DB | Verdict |
|---|---|---|
| `20260831020000` (WS1) | The 8 target `*_tenant_update/delete` policies exist on `audit_logs`, `activity_logs`, `activity_feed`, `document_activity_log`; `audit_trail` has 0 policies (untouched); `activity_feed_own_*` do not yet exist (created) | SAFE |
| `20260831030000` (WS5) | `assets.organization_id` currently nullable; **0/310 NULL rows** | SAFE |
| `20260831040000` (WS6) | `cc_delete_own_firm` + `consultant_clients_tenant_delete` exist (recreated); `is_org_admin_or_owner`/`is_consultant_firm_manager` exist; `is_consultant_firm_revoker` absent (created) | SAFE |


## 13. Risks and uncertainties

1. **Policy superset:** the live DB has ~142 `*_tenant_*` policies not defined in the chain (from the live-schema restore). Baselinig the chain at V3M11 does not remove them, but a fresh `db reset` build would not reproduce them — the chain is not a complete description of the live DB's policy surface. Any future schema-baseline work should treat the chain + the tenant-policy family as the de-facto schema.
2. **Factor + demo data are external to the chain:** 7,049 factors (SQL imports) and the investor-demo dataset (seed tool) are not reproducible from migrations. They must be preserved via the verified backup, not assumed reproducible.
3. **Column-level equivalence sampled, not exhaustive:** the table-set match (115/115) and sampled columns/functions/indexes are strong, but a full column/constraint/function diff of all 115 tables against the chain's cumulative result should be run immediately before recording the baseline.
4. **`[db.migrations] enabled = false`:** the config currently disables the CLI migration workflow; applying the three remediation migrations via `db push` will require an approved decision about the config and the baseline mechanism.
5. **v3_schema.sql is not the current schema:** it is 11 tables behind and schema-only; it must not be used as a baseline source or as a proxy for the migration chain.

## 14. Recommended safe procedure for the next step (NOT implemented)

1. Confirm the verified backup remains intact (SHA-256 on record).
2. Run a full read-only column/constraint/function diff of all 115 live tables vs the cumulative migration-chain schema (up to `20260831010000`). Expected: 0 material differences; any difference → STOP and report.
3. Obtain approval for the baseline mechanism: create `supabase_migrations.schema_migrations` and record the chain through `20260831010000` as applied (a one-time, explicitly approved bootstrap) — or an operator-approved alternative.
4. Only then run the standard workflow to apply exactly the three remediation migrations, with the data-safety checks repeated immediately before apply.
5. Post-apply verification per the migration report checklist (RLS state, NOT NULL, revoker function, regression tests).

---

## Final summary table

| Question | Result |
|---|---|
| Historical migrations previously used? | **YES** — chain committed across Git history (RC2 → V3M1–M11, D-series) and development docs confirm migration-driven schema work |
| Current DB contains historical schema state? | **YES** — 115/115 tables match the chain (0 missing/0 extra); all chain policies present (superset with ~142 live tenant extras) |
| Current DB contains 7,049 factors? | **YES** — exact count 7,049, checksum-verified |
| Factor provenance established? | **YES** — generated idempotent SQL imports (DEFRA `output/sql/emission_factors.sql` + SEAI `output/seai_2025/sql`); `import_batch_id` all NULL; not migrations, not demo seed |
| v3_schema.sql represents current schema? | **NO** — schema-only, 104/115 tables (11 behind), 0 data; untracked ~Aug-15 snapshot |
| Migration history missing? | **YES** — `supabase_migrations.schema_migrations` absent |
| Reason migration history is missing? | DB built by restore (Aug-20 live schema+data dump) + demo seed + factor imports + direct application of later migrations (V3M7–M11, D37) — not a single CLI `db reset`/`db push` replay; CLI migrations also disabled in current config |
| Safe to baseline? | **SAFE TO BASELINE** (caveats: superset policies; run a full column diff before recording) |
| Baseline point | **`20260831010000_v3m11_operational_indexes.sql`** (last historical migration; V3M11 objects verified present) |
| Three remediation migrations can follow? | **YES** — all preconditions verified present on the live DB (tenant policies to drop, assets 0 NULL, DELETE policies + helper functions, revoker absent) |

---

## Final safety check

- Database unchanged; **7,049 emission factors unchanged** (count + md5 re-verified); no migration applied; no migration history created; no schema/RLS/data changed.
- No config, migration-file, or application-file changes.
- Verified backup `/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump` intact (not modified/overwritten/deleted).
- No commits; no pushes; no secrets exposed (DB credentials used in-process only).
- Only artifact created: this report.

