# CarbonTally — Development Database Backup Report

- **Date:** 2026-09-01
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607`
- **Purpose:** Complete, verified logical backup of the CURRENT CarbonTally development database before any migration-history/application work.
- **Status:** **BACKUP COMPLETE AND VERIFIED. NO MIGRATIONS APPLIED. NO DATABASE MODIFICATION.**

---

## 1. Database identity

| Item | Value (verified) |
|---|---|
| Host | `127.0.0.1` |
| Port | **54426** (Postgres), 54425 (Supabase API/Kong) |
| Database | `postgres` |
| User | `postgres` (superuser; credentials used in-process only, never printed) |
| PostgreSQL version | **17.6** on x86_64-pc-linux-gnu |
| Supabase/local stack | project_id `carbon_ledger` (`supabase/config.toml`); linked project ref `pvwiojoyaqywtydzcpbg` ("CarbonTally", eu-west-2) |
| Supabase schemas present | `_realtime`, `auth`, `extensions`, `graphql`, `graphql_public`, `public`, `realtime`, `storage`, `supabase_functions`, `vault` |
| Extensions | `pg_stat_statements` 1.11, `pg_trgm` 1.6, `pgcrypto` 1.3, `plpgsql` 1.0, `supabase_vault` 0.3.1, `uuid-ossp` 1.1 |
| Connection note | `.env` still lists stale ports (`SUPABASE_URL=…:54325`, `DATABASE_URL=…:54326`); the running stack uses 54425/54426 per current `supabase/config.toml` — connection verified live on 54426 |

This is the current development database actively used for CarbonTally development (investor-demo data present; no `supabase_migrations` history — it was restored from a schema dump, which is why a full backup is essential).

## 2. Database size

- `pg_database_size('postgres')` = **37,416,083 bytes** ≈ **35.7 MiB** (0.03 GiB).

## 3. Table / object inventory (read-only)

- **115** tables in `public`, **181** RLS policies, **115/115** tables RLS-enabled, **0** forced (FORCE RLS not enabled — consistent with the deferred DB-0003 decision).
- **84** triggers, **226** indexes (public), **14** public functions.
- Largest tables by size: `emission_factors` (3.54 MiB), `organizations` (1.05 MiB), `consultant_clients` (0.70 MiB), `users` (0.60 MiB), `manual_extraction_items` (0.36 MiB), `organization_members` (0.35 MiB), `organization_files` (0.34 MiB), `suppliers` (0.32 MiB), `audit_trail` (0.31 MiB).

### 4. Emission-factor inventory — CRITICAL DATA

| Item | Value |
|---|---|
| Table | `public.emission_factors` |
| **Exact row count** | **7,049** (7,049 distinct ids) |
| reporting_year | **2025** for all 7,049 rows |
| factor_set | `DEFRA-2025` = **7,029**; `SEAI-2025` = **20** |
| factor_source | `DEFRA-DESNZ` = 7,029; `SEAI` = 20 |
| scope | Scope 3 = 4,090; Scope 1 = 2,549; Scope 2 = 354; Outside of Scopes = 56 |
| country | GB = 7,029; IE = 20 |
| **Deterministic checksum** | `md5(string_agg(id::text, ',' order by id::text))` = **`93668772ba460b0d03c7d9f9029f16c9`** |

This matches the documented DEFRA/SEAI baseline (7,029 + 20 = 7,049). The 7,000+ emission factors are preserved and verified (see §10).

### 5. Major data inventories (exact row counts)

| Table | Count | Table | Count |
|---|---|---|---|
| `emission_factors` | **7,049** | `organizations` | 975 |
| `users` | 1,329 | `auth.users` | 1,192 |
| `organization_members` | 1,125 | `organization_metadata` | 51 |
| `consultant_profiles` | 55 | `consultant_firm_members` | 54 |
| `consultant_clients` | 917 | `emissions_logs` | 100 |
| `calculation_snapshots` | 100 | `customer_factors` | 245 |
| `audit_trail` | 440 | `organization_files` | 254 |
| `upload_batches` | 52 | `manual_extraction_batches` | 56 |
| `manual_extraction_items` | 255 | `manual_review_queue` | 2 |
| `facilities` | 157 | `assets` | 310 |
| `suppliers` | 156 | `vehicles` | 3 |
| `issues` | 60 | `messages` | 52 |
| `conversations` | 33 | `conversation_participants` | 61 |
| `processing_entities` | 11 | `staff_profiles` | 21 |
| `staff_roles` | 6 | `report_versions` | 16 |
| `report_generation_queue` | 13 | `document_processing_queue` | 31 |
| `billing_plans` | 6 | `billing_commercial_config` | 7 |
| `queue_settings` | 1 | `system_settings` | 1 |
| `user_invitations` | 8 | `customer_documents` | 0 |
| `audit_logs` / `activity_logs` / `activity_feed` / `document_activity_log` | 0 / 0 / 0 / 0 (tables + policies exist, rows empty) | — | — |

### Full public table inventory (exact row counts, all 115 tables)

```
activity_categories 0 | activity_feed 0 | activity_logs 0 | ai_content_history 0
approval_decisions 0 | approval_requests 0 | assets 310 | audit_logs 0
audit_trail 440 | beta_access_codes 0 | beta_users 0 | billing_commercial_config 7
billing_credit_ledger 0 | billing_idempotency_keys 0 | billing_orders 0
billing_payment_records 0 | billing_plans 6 | billing_storage_usage 0 | business_hours 0
calculation_snapshots 100 | consultant_billing 0 | consultant_clients 917
consultant_custom_domains 0 | consultant_firm_members 54 | consultant_profiles 55
consultant_senders 0 | consultant_tasks 0 | conversation_activity_log 0
conversation_participants 61 | conversations 33 | customer_communication 0
customer_documents 0 | customer_factors 245 | customer_review_log 0
customer_subscriptions 0 | customer_verifications 0 | dashboard_metrics 0
data_discovery_requests 0 | document_activity_log 0 | document_processing_queue 31
document_type_categories 0 | document_types 0 | domain_events 0 | draft_entries 0
email_logs 0 | email_templates 0 | emission_factors 7049 | emissions_logs 100
export_history 0 | facilities 157 | factor_aliases 0 | file_attachments 0 | glossary 0
import_batches 0 | issues 60 | login_history 0 | manual_extraction_batches 56
manual_extraction_items 255 | manual_review_queue 2 | message_activity_log 0
messages 52 | notification_delivery 0 | notification_templates 0 | notifications 0
organization_files 254 | organization_members 1125 | organization_metadata 51
organizations 975 | password_reset_tokens 0 | pending_invites 0
processing_assignments 0 | processing_audit_trail 0 | processing_entities 11
processing_logs 0 | processing_queue 0 | processing_steps 0 | processing_time_log 0
product_categories 0 | qc_checklists 0 | qc_checks 0 | qc_errors 0 | queue_settings 1
reassignment_history 0 | report_comments 0 | report_generation_queue 13
report_templates 0 | report_versions 16 | review_assignment_history 0
review_audit_trail 0 | roles 0 | sla_compliance 0 | sla_definitions 0
staff_activity_log 0 | staff_daily_performance 0 | staff_performance 0
staff_profiles 21 | staff_roles 6 | staff_workload 0 | supplier_categories 0
suppliers 156 | system_settings 1 | team_performance 0 | typing_status 0 | units 0
upload_batches 52 | usage_tracking 0 | user_activity_log 0 | user_feedback 0
user_invitations 8 | user_presence 0 | vehicles 3 | verification_activity_log 0
verification_logs 0 | waitlist 0
```

## 6. Backup method

Standard PostgreSQL logical backup via `pg_dump` (client 18.6 against server 17.6), **two formats**:

1. **Custom archive** (`pg_dump -Fc`) — gzip-compressed, restorable with `pg_restore`, supports listing/selective restore. TOC entries: **1,930**; archive created `2026-09-01 12:51:34 +06`; dump version 1.16-0.
2. **Plain SQL** (`pg_dump` default) — portable, human-readable; contains all `CREATE TABLE`/`CREATE POLICY`/`COPY`/constraint/index statements.

Both capture: schema, table data, sequences, functions, triggers, indexes, constraints, RLS policies, grants, comments, and the Supabase platform schemas (`auth`, `storage`, `realtime`, `vault`, `graphql`, `supabase_functions`). `pg_dump` is read-only — the source database was not modified.

## 7. Backup file location

Outside the CarbonTally application source tree (not under the repo), so it cannot be accidentally committed:

- **`/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump`** (custom format)
- **`/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.sql`** (plain SQL)

## 8. Backup size

| File | Size (bytes) | Size (MiB) |
|---|---|---|
| `.dump` (custom, gzip) | 2,819,811 | 2.69 |
| `.sql` (plain) | 11,469,572 | 10.94 |

Plausible relative to the 35.7 MiB live database (custom format compresses well).

## 9. Backup integrity verification

1. **Files exist and are non-empty** — verified (`ls -la`).
2. **Archive is listable** — `pg_restore --list` succeeded: 1,930 TOC entries including all 10 schemas, the 6 extensions, `auth.*` functions, and all `public` tables.
3. **SQL backup contains the expected objects** — 1 × `COPY public.emission_factors (id, reporting_year, activity_type, co2e_multiplier, created_at, updated_at, unit, scope, factor_source, factor_set, country, region_deprecated, import_batch_id)`; **185** `CREATE POLICY` statements; 2 × `ALTER TABLE ONLY public.emission_factors`.
4. **SHA-256 checksums** (rollback reference):
   - `.dump`: `8c7a1874d540215fecfba076c1a83de35c62877b4a6752ce35b5b0b12eefeb4f`
   - `.sql`: `aa21854fee1d07a67859a65cdc211635690b1d7bb92d26ca0a466c50226ec600`


## 10. Restore verification (performed — strongest available)

A **safe restore verification** was performed into a separate temporary database `carbontally_bkverify_20260901T125134` (created, restored, verified, then **dropped**). The source development database was never the restore target.

- `pg_restore --no-owner --no-privileges` exit code 1 with **only 2 cosmetic errors**, both in Supabase *platform* schemas, not application data:
  1. `permission denied to set parameter "log_min_messages"` — `realtime.list_changes` function SET clause (needs superuser; cosmetic).
  2. `permission denied for table secrets` — `vault` schema (Supabase vault privilege model; cosmetic).
- **Application data verified identical to source:**

| Check | Source | Restored | Match |
|---|---|---|---|
| `emission_factors` count | 7,049 | **7,049** | ✅ |
| `emission_factors` md5 (ordered ids) | `93668772ba460b0d03c7d9f9029f16c9` | **`93668772ba460b0d03c7d9f9029f16c9`** | ✅ |
| `organizations` | 975 | 975 | ✅ |
| `users` | 1,329 | 1,329 | ✅ |
| `consultant_clients` | 917 | 917 | ✅ |
| `consultant_profiles` | 55 | 55 | ✅ |
| `consultant_firm_members` | 54 | 54 | ✅ |
| `emissions_logs` | 100 | 100 | ✅ |
| `calculation_snapshots` | 100 | 100 | ✅ |
| `customer_factors` | 245 | 245 | ✅ |
| `audit_trail` | 440 | 440 | ✅ |
| `organization_files` | 254 | 254 | ✅ |
| `manual_extraction_items` | 255 | 255 | ✅ |
| `assets` | 310 | 310 | ✅ |
| `facilities` | 157 | 157 | ✅ |
| `suppliers` | 156 | 156 | ✅ |
| `processing_entities` | 11 | 11 | ✅ |
| `auth.users` | 1,192 | 1,192 | ✅ |
| RLS: public tables RLS-enabled / policies | 115 / 181 | 115 / 181 | ✅ |

## 11. Emission-factor integrity (before ↔ after)

- Live source: `count(*)` = **7,049**; checksum `md5(ordered ids)` = `93668772ba460b0d03c7d9f9029f16c9`.
- Restored copy (from the backup): `count(*)` = **7,049**; checksum = `93668772ba460b0d03c7d9f9029f16c9` (**identical**).
- Distribution preserved: DEFRA-2025 7,029 / SEAI-2025 20; all reporting_year 2025; scope and country distributions verified in §4.
- No emission-factor records were modified.

## 12. Rollback / recovery instructions (restore point)

Use the custom archive with `pg_restore` (most reliable, supports all objects):

```
PGPASSWORD=<in-process> pg_restore --no-owner --no-privileges \
  --host 127.0.0.1 --port 54426 --username postgres --dbname postgres \
  /home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.dump
```

Expected: the two cosmetic platform-schema errors noted in §10 (realtime/vault) are harmless; all application data, schema, RLS policies, functions, triggers, and indexes restore. The plain SQL backup (`…_20260901T125134.sql`) is the portable fallback (`psql -h 127.0.0.1 -p 54426 -U postgres -d postgres -f <file>`).

**Restore point record:**

- Backup files: `/home/shomonrobie/carbontally_db_backups/carbontally_dev_20260901T125134.{dump,sql}`
- Created: **2026-09-01 12:51:34 +06**
- Database: `postgres` @ `127.0.0.1:54426`, project `carbon_ledger`, PostgreSQL 17.6
- Database size: 37,416,083 bytes (35.7 MiB)
- Public tables: 115 · RLS policies: 181 · Triggers: 84 · Indexes: 226 · Extensions: 6
- Emission factors: **7,049** (checksum `93668772ba460b0d03c7d9f9029f16c9`)
- Backup verification: **PASSED** (custom archive listable; SQL contains all objects; full temp-restore verified critical data identical; SHA-256 recorded)
- Note: `.dump` SHA-256 `8c7a1874d540215fecfba076c1a83de35c62877b4a6752ce35b5b0b12eefeb4f`; `.sql` SHA-256 `aa21854fee1d07a67859a65cdc211635690b1d7bb92d26ca0a466c50226ec600`

## 13. Limitations

- Restore verification was performed on the same Postgres server (temp database) — extensions are pre-available there, so extension-install behaviour on a different host wasn't exercised.
- Two Supabase-platform-schema statements (realtime `list_changes` SET clause; vault `secrets` permission) do not restore under a non-superuser role; they do not affect `public` application data. On a full Supabase stack restore these are handled by the platform role model.
- The plain SQL backup is large (11.5 MiB) but was verified for key object presence only, not re-run end-to-end (the custom archive is the primary, end-to-end-verified artifact).
- The backup is a logical backup taken at a point in time; any writes to the live DB after 12:51:34 +06 are not included.

## 14. Final status

```
MIGRATIONS APPLIED: NO

DATABASE MODIFIED: NO
```

No migration, baseline, `schema_migrations` creation, reset, RLS change, schema change, or data change was performed. The only new artifacts are the two backup files (outside the source tree) and this report.

## 15. Safety check

- Source database data unchanged; emission factors unchanged (7,049, checksum identical before/after); schema/RLS unchanged.
- Application code, frontend, backend, admin, migration files, and `supabase/config.toml` unchanged.
- No migrations applied; no `db reset`; no commits; no pushes.
- No secrets exposed (credentials used in-process only; not printed, not written to any file).

