# CT-PO — Schema ↔ Code Mismatch Register (CT-SCHEMA-01)

**Task ID:** `CT-SCHEMA-01-20260927-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION`
**Type:** READ-ONLY register. No source, migration, database or production change.
**Authority:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`).
**Canonical reference schema:** `CT-SCHEMA-01-TARGET-A` (disposable rebuild, 89/89 migrations applied; see
`CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md`).
**Date:** 2026-09-27.

## 0. Severity scale and classification key

| Severity | Meaning |
|---|---|
| **S1** | BLOCKING — prevents a canonical rebuild or a documented operational path from succeeding |
| **S2** | HIGH — a durable code/service path cannot function against the schema, or a deployment is materially behind |
| **S3** | MEDIUM — process/automation defect, unreachable comparison target, or latent risk |
| **S4** | LOW — documentation-level inconsistency with no runtime effect |
| INFO | Recorded for completeness; no action required |

| Class | Meaning |
|---|---|
| `ENVIRONMENT_DEPENDENCY` | The chain needs something the platform provides (or an operator does) |
| `RUNNER` | The result depends on **how** the chain is executed (role, `search_path`, harness) |
| `ORDERING` / `MISSING_DEPENDENCY` | A step cannot run in the assumed order |
| `CODE_EXPECTS_MISSING_OBJECT` | Code references an object no migration creates |
| `SCHEMA_OBJECT_NO_CONSUMER` | Object exists with no code reference |
| `DEPLOYMENT_DRIFT` | A durable database is behind the canonical schema |
| `TEST_HARNESS` | Test/integration scaffolding can pollute non-throwaway databases |
| `UNKNOWN` | Could not be resolved read-only in this task |

## 1. S1 — Blocking

### SCM-001 — Migration 27 requires the platform storage layer, which no migration creates

| Field | Value |
|---|---|
| Class | `ENVIRONMENT_DEPENDENCY` |
| Severity | **S1** |
| Migration | `20260823000000_d32_private_documents_storage.sql` (sequence 27 of 89) |
| Required object(s) | `storage.buckets`, `storage.objects`, `storage.foldername()` |
| Canonical object exists? | In the **final** rebuild: yes (platform-provisioned). On a bare Supabase Postgres baseline: **no** |
| Evidence | `ERROR: relation "storage.buckets" does not exist` (line 83) — reproduced on two fresh clusters under two roles; per-file log `027_20260823000000_d32_private_documents_storage.sql.log` |
| Code consumer | None (platform object); CarbonTally reaches the bucket through storage-api, not SQL |
| Interpretation | Not a migration defect — the migration's own header documents the platform mechanism. It **is** a defect in any procedure claiming "apply 89 from zero" without the platform layer |
| Recommended action | Encode "platform storage provisioning (storage-api migrations) before application migrations" in the canonical rebuild runbook/automation |

### SCM-002 — Migration 27's validation is `search_path`-dependent; the documented apply role fails it

| Field | Value |
|---|---|
| Class | `RUNNER` |
| Severity | **S1** |
| Migration | `20260823000000_d32_private_documents_storage.sql` (the `DO $d32_policies$ …` block, ~line 192) |
| Mechanism | The block substring-matches approved policy predicates from `pg_policies.qual`. PostgreSQL deparses `auth.uid()` **unqualified** when `auth` is visible in the session `search_path` |
| Evidence | As `supabase_admin` (`search_path = "$user", public, auth, extensions`) → `ERROR: D32 policy drift: d32_documents_select_org_member is missing the approved org-scope fragment "auth.uid()"`; as `postgres` (`search_path = "$user", public, extensions`) → passes; the deparsed policy text is otherwise byte-identical in both sessions and equal to the flagship's |
| Contradiction | `e2e/environment/scripts/apply_migrations.sh` prescribes `supabase_admin` for exactly this migration, on an ownership rationale that the current migration revision (`P8-D17-MIGRATION-REVISION-001`, which removed the ownership-sensitive DDL) has made stale |
| Interpretation | Chain-integrity defect: chain success depends on the runner role, and the repository's documented role is the failing one. Invisible to code review and to any environment where the migration was applied by a different tool |
| Recommended action | Make the validation `search_path`-independent (e.g. `SET LOCAL search_path` inside the block, or compare function references instead of deparsed text), **or** correct the harness role and the stale rationale. Requires an implementation task |

## 2. S2 — High

### SCM-003 — Operator D32 provisioning cannot precede migration 1

| Field | Value |
|---|---|
| Class | `ORDERING` / `MISSING_DEPENDENCY` |
| Severity | **S2** |
| Evidence | Creating the four approved `storage.objects` policies before any application migration → `ERROR: relation "organization_members" does not exist`; succeeds after migration 1 (`00000000000000_init_schema.sql:277` creates `public.organization_members`) |
| Impact | A "provision platform first, then migrate" automation fails; correct order is platform → migrations ≥ 1 → operator policies → migrations 27–89 |
| Recommended action | Document/automate the interleaved order; make the operator step idempotent and re-runnable |

### SCM-004 — `defra_conversion_factors`: referenced by durable code, created by no migration, absent everywhere

| Field | Value |
|---|---|
| Class | `CODE_EXPECTS_MISSING_OBJECT` |
| Severity | **S2** |
| Code consumers | `backend/utils/emissions.py:58,72,89`; `backend/routes/reports.py:280,1265`; `backend/routes/organizations/data.py:391`; `backend/routes/organizations/dashboard.py:124`; `backend/routes/emissions.py:199` |
| Migrations creating it | **none** (no occurrence in any of the 89 files) |
| Present in canonical rebuild / flagship / demo_local | **No / No / No** |
| Interpretation | Legacy DEFRA conversion-factor table from the pre-V3 factor model (superseded by `emission_factors` + `factor_aliases`). The table exists in **no** environment, so the referencing paths cannot succeed |
| Recommended action | Determine whether those routes are still registered (U4). If live → add the table by migration or repoint to `emission_factors`; if dead → remove the code. **Engineering/PO decision — not silently fixable** |

### SCM-005 — `report_history`: referenced by durable code, created by no migration

| Field | Value |
|---|---|
| Class | `CODE_EXPECTS_MISSING_OBJECT` |
| Severity | **S2** |
| Code consumers | `backend/routes/reports.py:1852,1929,1969` |
| Migrations creating it | **none** |
| Present in canonical / flagship / demo_local | No / No / No |
| Interpretation | Superseded by `report_versions` (+ `report_version_artifacts`, `report_generation_queue`, `report_comments`) |
| Recommended action | As SCM-004 |

### SCM-006 — `report_schedules`: referenced by durable code, created by no migration

| Field | Value |
|---|---|
| Class | `CODE_EXPECTS_MISSING_OBJECT` |
| Severity | **S2** |
| Code consumers | `backend/routes/reports.py:1372,1435,1498,1510` |
| Migrations creating it | **none** |
| Present in canonical / flagship / demo_local | No / No / No |
| Recommended action | As SCM-004 |

### SCM-007 — `notification_delivery_log`: referenced by durable code, created by no migration

| Field | Value |
|---|---|
| Class | `CODE_EXPECTS_MISSING_OBJECT` |
| Severity | **S2** |
| Code consumers | `backend/routes/admin/audit_logs.py:404` |
| Migrations creating it | **none** |
| Present in canonical / flagship / demo_local | No / No / No |
| Note | `notification_delivery` and `notifications` **do** exist in canonical — the mismatch is the `_log` variant |
| Recommended action | As SCM-004 |

### SCM-008 — Durable databases are 4–29 canonical tables behind the migration chain

| Field | Value |
|---|---|
| Class | `DEPLOYMENT_DRIFT` |
| Severity | **S2** |
| Evidence | flagship `postgres` 116 tables / 29 missing / ledger 46 rows (max `20260903010000`); `carbontally_demo_local` 141 / 4 missing; `carbontally_qa_phase8` 133 / 12 missing; `carbontally_test` 117 / 28 missing; disposable `ct_p17k_20260926` 145 / 0 missing |
| Impact | Code compiled against canonical objects (`evidence_line_items`, `disclosure_*`, accounting columns, `report_version_artifacts`, `manual_processing_grants`, `activity_clarifications`, …) fails against every durable database until the chain is applied — the same underlying condition the CT-FEATURE-02 FIEW register recorded |
| Recommended action | Apply the chain to a declared durable environment (verification document §16 step 3); retire the FIEW "absent / clone-only" caveats only from that environment |

## 3. S3 — Medium

### SCM-009 — Integration tests create scratch objects in `public` on whichever database they target

| Field | Value |
|---|---|
| Class | `TEST_HARNESS` |
| Severity | **S3** |
| Evidence | `backend/tests/integration/backup/test_exporter_local.py` executes `CREATE TABLE public.widgets`, `public.notes`, `public.secure_things`, `public.unlogged_demo`, `public.unlogged_only`, `public.identity_demo`, `public.events_a/b/c`, `CREATE VIEW public.widget_names` |
| Impact | These names are absent from the canonical schema (correctly — they are fixtures). If such a suite were ever pointed at a durable database, it would silently add tables to it. Consistent with the standing F-046-1 harness-target invariant |
| Recommended action | Keep the F-046-1 guard; optionally move fixtures into a dedicated schema |

### SCM-010 — No applied-migration ledger exists for psql-built durable databases

| Field | Value |
|---|---|
| Class | `PROCESS` |
| Severity | **S3** |
| Evidence | `supabase_migrations.schema_migrations` exists only in the flagship (46 rows, CLI-managed); `carbontally_demo_local`, `carbontally_qa_phase8`, `carbontally_test` and the canonical rebuild have **no** ledger table |
| Impact | "Which migrations are applied?" cannot be answered from the database in most environments, so drift must be inferred from object presence (as §13 of the verification document had to do) |
| Recommended action | Standardise on Supabase CLI application (or create the ledger table) for every durable environment |

### SCM-011 — `ct_local_93d5cdd` could not be compared

| Field | Value |
|---|---|
| Class | `UNKNOWN` |
| Severity | **S3** |
| Evidence | The database is not present in the shared Supabase cluster (`supabase_db_carbon_ledger`, which hosts `postgres`, `carbontally_demo_local`, `carbontally_qa_phase8`, `carbontally_test` and ~60 `ct_*` clones); the host PostgreSQL 18 cluster on `127.0.0.1:5432` rejected the only read-only credential available to this task |
| Impact | One comparison row missing from the comparison matrix; the prior finding "`ct_local_93d5cdd` = 25 orgs, 0 factors, no P17 objects" is therefore **not re-verified** by this task |
| Recommended action | Provide a read-only credential and repeat the comparison |

## 4. S4 / INFO — recorded, no action

| ID | Object / observation | Class | Severity | Why recorded |
|---|---|---|---|---|
| SCM-012 | `conversation_participants_conv_user_idx` (declared by `00000000000000_init_schema.sql` and `20260802000000_rc2_indexes.sql`) is absent after the rebuild | `SUPERSEDED_OBJECT` | S4 | Absence is **intentional**: explicitly dropped by `20260828000000_v3m8_messaging_unique_participants.sql`. Recorded so that "declared but absent" is not misread as failure |
| SCM-013 | `cc_insert_own_firm` policy (declared by `20260803000000_rc2_rls.sql`, re-created by `20260822000000_p9_rls_recursion_fix.sql`) is absent after the rebuild | `SUPERSEDED_OBJECT` | S4 | Absence is **intentional**: explicitly dropped by `20260906090000_p6_1c_consultant_engagement.sql` (legacy name superseded by the engagement model) |
| SCM-014 | `conversation_activity_log` exists in canonical with **0** code references at grep level | `SCHEMA_OBJECT_NO_CONSUMER` | S4/INFO | Only canonical table with no code hit; may be legacy or referenced dynamically. Not evidence that the table should be removed |
| SCM-015 | Reference to `'documents'` in code is a **storage bucket**, not a table (`storage.from_('documents')`, `"bucket": "documents"`) | `FALSE_POSITIVE` | INFO | Prevents a future reader from registering `documents` as a missing table |
| SCM-016 | Application schema declares **0 enums**; only enum in the cluster is `storage.buckettype` | `FACT` | INFO | Governed vocabularies are enforced by CHECK constraints/text — relevant to any code assuming PG enum types |
| SCM-017 | `gen_random_uuid()` / `uuid_generate_v4()` usage (7 / 135 occurrences) resolves from extensions (`pgcrypto`, `uuid-ossp`) provisioned at baseline | `FACT` | INFO | Confirms the extension dependency is satisfied by the platform layer, not the chain |

## 5. Summary counts

| Severity | Count | IDs |
|---|---|---|
| S1 | **2** | SCM-001, SCM-002 |
| S2 | **6** | SCM-003 … SCM-008 |
| S3 | **3** | SCM-009, SCM-010, SCM-011 |
| S4 / INFO | **6** | SCM-012 … SCM-017 |
| **Total registered** | **17** | |

Of the S1/S2 items: **SCM-001, SCM-002, SCM-003 are properties of the platform/runner environment** (they
do not indicate a wrong schema), while **SCM-004 … SCM-008 are genuine code↔schema/deployment mismatches**
that predate this task and are neither caused nor cured by the from-zero rebuild.

<!--CTEOF-->


