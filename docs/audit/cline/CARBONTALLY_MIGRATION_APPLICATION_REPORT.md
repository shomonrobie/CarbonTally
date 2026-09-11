# CarbonTally — Migration Application Report

- **Date:** 2026-09-01
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607`
- **Task:** Apply the three pending approved remediation migrations to the baselined development database via the normal Supabase workflow (Option A: temporary config enable → apply → verify → restore config).
- **Status:** **ALL THREE MIGRATIONS APPLIED_AND_VERIFIED. CONFIGURATION RESTORED. NO DATA LOSS.**

---

## 1. Backup confirmation

- **`/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump`** — exists, **2,819,811 bytes**, listable (`pg_restore --list` OK, 1,930 TOC entries). Not overwritten. Rollback point (restore only on explicit instruction).

## 2. Baseline confirmation

- Baseline: **`20260831010000_v3m11_operational_indexes.sql`** — confirmed established and unchanged.
- Pre-apply state (read-only) matched expectations: 38 migration-history rows (through v3m11), 115 tables, 181 policies, `emission_factors` **7,049** (md5 `93668772ba460b0d03c7d9f9029f16c9`), organizations 975, users 1,329, consultant_clients 917, assets 310, audit_trail 440.

## 3. Configuration change (temporary, fully restored)

- `supabase/config.toml` `[db.migrations]`:
  - Before: `enabled = false` (pre-existing project config).
  - Temporarily set to `enabled = true` (only this setting) for the apply run.
  - **After: restored to `enabled = false`** (verified). No other configuration value was changed.

## 4. Migration application results

Applied in chronological order via the normal workflow (`supabase db push --local`):

1. `20260831020000_audit_activity_immutability.sql` — **applied**
2. `20260831030000_tenant_org_id_not_null.sql` — **applied**
3. `20260831040000_consultant_revocation_roles.sql` — **applied**

- The CLI confirmed the push list contained **only these three** migrations.
- No historical migration was replayed; no unrelated migration applied.
- Post-apply history: `supabase_migrations.schema_migrations` = **41 rows**, last four = `20260831010000`, `20260831020000`, `20260831030000`, `20260831040000` (baseline intact, three appended).

## 5. Live database verification

### DB-0001 (audit/activity immutability)
- `audit_logs`: only INSERT + SELECT policies remain (UPDATE/DELETE dropped) ✓
- `activity_logs`: only INSERT + SELECT ✓
- `document_activity_log`: only INSERT + SELECT ✓
- `activity_feed`: INSERT + SELECT + `activity_feed_own_update` (UPDATE, `user_id = auth.uid()`) + `activity_feed_own_delete` (DELETE, row-owner) ✓ — legitimate row-owner mutation preserved
- V3 `audit_trail`: **0 policies** (deny-by-default, untouched) ✓

### DB-0002 (tenant NOT NULL)
- `assets.organization_id` `is_nullable` = **NO** (constraint active) ✓
- NULL rows = **0** ✓
- Assets preserved: **310** ✓

### SEC-0003 (consultant revocation)
- `public.is_consultant_firm_revoker(uuid)` **exists** (role-based: owner/admin/manager) ✓
- `cc_delete_own_firm` DELETE qual = `is_consultant_firm_revoker(consultant_id)` ✓
- `consultant_clients_tenant_delete` DELETE qual = `is_org_admin_or_owner(organization_id)` ✓
- Lifecycle/provenance columns present: `status`, `ended_at`, `ended_by`, `suspended_at`, `lifecycle_updated_at` ✓
- `consultant_clients` rows preserved: **917** ✓
- Allowed: Consultant Owner/Admin/Manager · Denied: Consultant Member/Viewer (backend `ensure_consultant_revocation_authority` + RLS predicate). No client data deleted/anonymized; no account-deletion triggered.

## 6. Data-integrity before/after comparison

| Item | Before | After | Status |
|---|---|---|---|
| `emission_factors` | 7,049 | **7,049** | ✅ |
| `emission_factors` md5 (ordered ids) | `93668772ba460b0d03c7d9f9029f16c9` | **`93668772ba460b0d03c7d9f9029f16c9`** | ✅ |
| `organizations` / `users` | 975 / 1,329 | 975 / 1,329 | ✅ |
| `consultant_clients` | 917 | 917 | ✅ |
| `assets` | 310 | 310 | ✅ |
| `audit_trail` | 440 | 440 | ✅ |
| `emissions_logs` / `calculation_snapshots` / `customer_factors` | 100 / 100 / 245 | 100 / 100 / 245 | ✅ |
| `organization_files` / `manual_extraction_items` / `facilities` / `suppliers` | 254 / 255 / 157 / 156 | 254 / 255 / 157 / 156 | ✅ |
| tables | 115 | 115 | ✅ |
| policies | 181 | **175** | ✅ expected (WS1: −8 tenant UPDATE/DELETE, +2 row-owner; WS6 recreated 2 DELETE predicates) |

## 7. Regression tests

Run after application (backend `tests/unit/api/` targeted suites for the affected workstreams):

- `test_audit_immutability_migration.py` (DB-0001) · `test_tenant_org_not_null_migration.py` (DB-0002) · `test_consultant_revocation.py` + `test_consultant_revocation_migration.py` (SEC-0003) · `test_d19_lifecycle.py` · `test_v3_consultants.py` · `test_operations_auth.py` · `test_scope_aware_authorization.py` · `test_admin_endpoints.py` · `test_legacy_upload_idor.py` · `test_auth_status_semantics.py` · `test_review_sla_surfaces.py`

**Result: 82/82 passed** (0 failures). No tests were modified.

## 8. Final configuration state

- `supabase/config.toml` `[db.migrations] enabled = false` — **restored to its previous value** (verified by `sed -n '53,58p'`).
- No other configuration change was made.

## 9. Final status table

| Migration | Status |
|---|---|
| `20260831020000_audit_activity_immutability` | **APPLIED_AND_VERIFIED** |
| `20260831030000_tenant_org_id_not_null` | **APPLIED_AND_VERIFIED** |
| `20260831040000_consultant_revocation_roles` | **APPLIED_AND_VERIFIED** |

## 10. Warnings and remaining risks

- **Application note:** the first `db push --local` invocation stalled waiting on the interactive confirmation prompt (the CLI asks `[Y/n]` before applying). The run was re-attempted with the CLI `--yes` flag; the push confirmed and applied exactly the three listed migrations. No partial application occurred (history stayed at 38 until the successful run).
- **Config is re-disabled** (`[db.migrations] enabled = false`). Future migration application requires the same temporary-enable (Option A) or an equivalent approved mechanism. Do NOT run `db push`/`db reset` merely to test the disabled config.
- The live DB is now under proper migration management: baseline `20260831010000` + the three remediation migrations, with `schema_migrations` = 41 rows. A fresh `db reset` build would NOT reproduce the ~142 live-restore `*_tenant_*` policies or the external factor/demo data (documented limitation; the verified backup remains authoritative).
- Rollback point (restore only on explicit instruction): `/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump`.

---

## Final safety check

- Migration baseline remains correct (`20260831010000`); all three remediation migrations recorded as applied (41 rows).
- **No historical migration replayed; no unrelated migration applied.**
- Schema/RLS correct (verified §5); `assets.organization_id` NOT NULL; consultant revocation authorization correct.
- `emission_factors` = **7,049**, checksum **`93668772ba460b0d03c7d9f9029f16c9`** unchanged; major table counts preserved.
- Configuration restored to previous state (`[db.migrations] enabled = false`).
- Application code, frontend, backend, admin, migration files unchanged; no secrets exposed; no commits; no pushes.
- Verified backup remains intact.

