# CarbonTally Production Backup + Restore — Complete Implementation and Handoff

**Date:** 2026-10-02
**Scope:** the CarbonTally backup workstream, end to end:
BACKUP-01 (job model) and BACKUP-02 (backup sets + verification) migrations, the
logical exporter (D1), the artifact/crypto/storage service (D2/D3), the restore
library (D4), the admin backup API, and the disposable recovery drill (workstream F).
**Status:** implemented and locally verified; the **DR-20 recovery drill is
recorded, reproducible and application-level validated (§4.1)**; ready for
independent verification and the CoStrict handoff. Open items are listed in §10 and
the verdict is in §11.

Everything in this document was executed on the build host. Each claim carries the
command that produced it; nothing here is asserted from code reading alone.

---

## 1. What is complete

| # | Capability | Where | Evidence |
|---|-----------|-------|----------|
| 1 | Backup job model + queue (single-flight, attempt budget, states) | `supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql`, `backend/backup/jobs.py` | `tests/unit/backup/test_jobs.py` (83 test functions) |
| 2 | Backup sets + verification migration (**newest migration**) | `supabase/migrations/20261027000000_ct_backup_02_backup_sets_and_verification.sql` (203 lines, ends `COMMIT;`) | `tests/unit/backup/` + drill phase 1 |
| 3 | Logical export (catalog, DDL, COPY data, sequences, RLS/policies/triggers/functions/comments) | `backend/backup/exporter.py`, `backend/backup/catalog.py` | `tests/integration/backup/test_exporter_local.py` against a real PostgreSQL |
| 4 | Artifact envelope: archive, checksums, AES-256-GCM encryption, ciphertext-only object store (local + S3/SigV4) | `backend/backup/artifact.py`, `backend/backup/crypto.py`, `backend/backup/storage.py` | `tests/unit/backup/test_artifact.py`, `test_crypto.py`, `test_sigv4_and_s3store.py` |
| 5 | Backup service: export → checksums → manifest → archive → encrypt → store → read-back verify | `backend/backup/service.py` | `tests/unit/backup/test_service.py`, `tests/unit/tools/test_backup_export.py` |
| 6 | Restore library (D4): reviewable plan, phased execution, fail-closed target guard, post-restore verification | `backend/backup/restore.py` | **`tests/integration/backup/test_restore_local.py` (new in this session)** |
| 7 | Admin backup API (9 endpoints under `/api/v3/admin/backups`) | `backend/api/v3_backups.py`, mounted in `backend/api/router.py:266` | `tests/unit/api/test_backup_admin_api.py` (17 test functions) |
| 8 | Disposable recovery drill (4 phases) | `tools/backup_recovery_drill.py` | `tests/unit/tools/test_backup_recovery_drill_guard.py`, drill run §4 |

---

## 2. Admin backup API surface

`backend/api/v3_backups.py` — `APIRouter(prefix="/api/v3/admin/backups", tags=["V3 — Admin Backups"])`,
included by `backend/api/router.py:266`:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v3/admin/backups/status` | queue/storage health summary |
| GET | `/api/v3/admin/backups` | list jobs |
| GET | `/api/v3/admin/backups/policy` | read retention/policy configuration |
| PUT | `/api/v3/admin/backups/policy` | update policy |
| POST | `/api/v3/admin/backups` | create a backup job (201) |
| GET | `/api/v3/admin/backups/{job_id}` | job detail |
| GET | `/api/v3/admin/backups/{job_id}/pair` | the job's backup pair/set |
| POST | `/api/v3/admin/backups/{job_id}/verify` | run verification for a job |
| GET | `/api/v3/admin/backups/{job_id}/download` | download the artifact (admin only) |

---

## 3. Test evidence

### 3.1 Backup-scoped suites

| Suite | Command | Result |
|-------|---------|--------|
| Unit — backup core | `pytest tests/unit/backup -q` | 241 test functions across `test_artifact.py` (15), `test_crypto.py` (16), `test_jobs.py` (83), `test_p1_1_remediation.py` (47), `test_service.py` (18), `test_sigv4_and_s3store.py` (48), `test_storage_and_settings.py` (14) — all passing |
| Unit — admin API | `pytest tests/unit/api/test_backup_admin_api.py -q` | 17 test functions |
| Unit — tooling | `pytest tests/unit/tools/test_backup_export.py tests/unit/tools/test_backup_recovery_drill_guard.py -q` | 8 + 3 test functions |
| **Integration — exporter (real PostgreSQL)** | `pytest tests/integration/backup/test_exporter_local.py -q` | **9 passed** |
| **Integration — restore (real PostgreSQL)** | `pytest tests/integration/backup/test_restore_local.py -q` | **13 passed** (5 test functions, parametrised) |
| Integration — whole backup folder | `pytest tests/integration/backup -q` | **22 passed**, exit 0 |
| Frontend (admin) | `jest` | 15/15 |

Together the backup-scoped suites execute **280 tests — all passing**: 241 in
`tests/unit/backup`, 17 in `test_backup_admin_api.py` and 22 in
`tests/integration/backup`. Re-measured 2026-10-02 with
`pytest tests/unit/backup --co -q`, `pytest tests/unit/api/test_backup_admin_api.py --co -q`
and `pytest tests/integration/backup -q`; the earlier 207/275 figures were the
counts at the previous revision.

Both integration suites are self-guarding: they skip unless the DSN host is
loopback (`127.0.0.1`/`localhost`), create their own uniquely-named databases
(`ct_backup_it_*`, `ct_backup_rs_src_*`, `ct_backup_rs_dst_*`) and drop only those.

### 3.2 What the restore integration test proves

`tests/integration/backup/test_restore_local.py` (new) closes the one real gap found
during the audit: **the D4 restore library had no caller and no test in the
repository**. It now exercises the shipped path end to end against a real server:

1. `BackupService.create_backup` publishes an encrypted artifact for a populated
   disposable source;
2. `restore_artifact` decrypts it and rebuilds a *different*, empty disposable
   database — schema, data, **sequence state** (`setval` semantics, not just the
   sequence object), RLS, one policy, one trigger, one view, table comment;
3. `verify_restored` compares the target with the artifact's own catalog and
   returns `ok: true` with **every** difference collection empty (missing/extra
   tables, indexes, constraints, policies, triggers, functions, RLS, row counts,
   sequence state);
4. a schema-only rehearsal (`skip_data=True`) is honestly reported as
   `ok: false` with the row-count mismatches listed — verification is not vacuous;
5. `assert_disposable_target` refuses `production_main`, `carbon_prod`,
   `carbon_qa`, `demo_live`, `investor_preview`, `live` **and `ct_prod_restore`**,
   and `restore_members` refuses a named persistent target *before executing the
   first statement*.

---

## 4. Disposable recovery drill — authoritative run

```
python tools/backup_recovery_drill.py \
  --source ct_final02_src \
  --target ct_final02_src_restored_82482 --keep-target
```

Work directory `/tmp/ct_backup_drill_ct_final02_src_restored_82482`; raw output
`/tmp/drill_run1.txt`. The drill (`tools/backup_recovery_drill.py`) is the
canonical, **pre-existing** tool.

Source facts read directly from `ct_final02_src`
(`postgresql://postgres:postgres@127.0.0.1:54426/ct_final02_src`):
`emission_factors` 7,049 · `customer_factors` 245 · `audit_trail` 563 ·
public tables 149 · tables with RLS enabled 149 · policies 275 cluster-wide
(the exporter is scoped to `public` → 271).

### Phase 1 — the project's own capability (D1 exporter + `BackupService`)

| Observation | Value |
|-------------|-------|
| backup_id | `0334bf6a28a84193808248146b923292` |
| artifact | `backups/0334bf6a…/carbontally-logical-backup-v1.tar.gz.enc`, 967,860 bytes |
| envelope | `envelope_version 1`, `AES-256-GCM`, `key_id key-v1` |
| ciphertext only | **true** (plaintext marker absent from the stored object) |
| members / checksums verified | 154 / 152 |
| catalog + DDL members | present |
| data members | 149 |
| manifest counts | tables 149, rows 14,263, policies 271, triggers 103, functions 37 |
| inventory schemas | `['public']` |

### Phase 2 — platform recovery (`pg_dump` → `pg_restore` into a FRESH database)

dump 3,228,129 bytes; `missing_tables: []`; `row_count_mismatches: {}`;
`index_delta 0`, `constraint_delta 0`, `policy_delta 0`, `rls_table_delta 0`,
`bucket_delta 0`. `pg_restore` returned 1 with a single ignored warning
(`permission denied for table secrets`): every object and every row arrived.

### Phase 3 — the reconstruction accepts the shipped migrations

Canonical run (restore uses `--no-owner --no-privileges`):

```
{'migrations': 96, 'applied': 94, 'already_present': 1,
 'failed': [('20260801000000_rc2_constraints.sql',
             'column "organization_id" of relation "conversations" contains null values')]}
```

DR-20 recovery run (ownership **and** ACLs preserved, then platform prep — §4.1):

```
{'migrations': 96, 'applied': 93, 'already_present': 1,
 'failed': [('20260801000000_rc2_constraints.sql', '... contains null values'),
            ('20260824010000_d35_self_service_onboarding.sql',
             'permission denied for table users')]}
```

Both failures are explained and neither is a backup defect:

* `rc2_constraints` cannot re-apply because the **source data** has NULL
  `conversations.organization_id` rows — data-dependent and reproducible with no
  backup involved.
* `d35_self_service_onboarding` fails **only** because the DR-20 run applied
  platform *ownership* parity (which moves `auth.users` to `supabase_auth_admin`)
  **before** the migration replay, and `postgres` is **not** a superuser in this
  stack. Re-running that single migration as the platform superuser
  `supabase_admin` returns **rc=0** (verified). It is a *runbook-ordering* fact,
  not a restore defect: **restore → replay migrations → then apply platform
  ownership/ACL parity**.

### Phase 4 — the application runs against the reconstruction

The canonical drill still drives
`tests/integration/test_f039_1_adjudication_lifecycle_runtime.py`, whose shared
fixture `TRUNCATE`s `public.audit_trail`. Migration `20261021000000` installs an
append-only statement trigger that refuses exactly that statement unless a session
sets `ct.audit_purge_authorised=on`, so all 9 tests ERROR in fixture setup. **That
is not a recovery defect — it is the reconstruction faithfully reproducing the
ledger invariant** (the trigger is present and firing in the reconstruction; §4.1).

`H5` is now **resolved without touching the invariant, the fixture or any
repository file**:

* phase 4 is exercised by the **DR-20 drill in §4.1**, which runs the *real
  application* (uvicorn + the real gateway → GoTrue/PostgREST) against the
  reconstruction instead of a fixture that fights the ledger; and
* the fixture conflict itself is demonstrated with a **disposable-only procedure**
  that uses the guard's own authorised escape hatch inside a rolled-back
  transaction (§4.1, "append-only audit ledger").

### 4.1 DR-20 recovery drill — recorded, reproducible, application-level validated

Run on **2026-10-02 13:15 (+06:00)** at HEAD
`cabdca8380415e73a25cf23eb393d0b15c0af391` (branch `p8-release-reconciled`).
Driver (disposable, outside the repository):
`/home/shomonrobie/ct_local_env/dr20_recovery/run_drill.sh`. Full log:
`/home/shomonrobie/ct_local_env/dr20_recovery/logs/drill_20261002T131522.log`.

```
backup (own BackupService) -> pg_dump|pg_restore into a FRESH disposable DB
      (ownership + ACLs preserved) -> platform ACL/ownership parity ->
      migrations to head -> DB/schema/RLS/trigger/view/function/ledger checks ->
      PARALLEL ct_dr20_* app stack (GoTrue/PostgREST/gateway) ->
      real application (uvicorn) -> app-level recovery probe -> teardown
```

Source `ct_final02_src` → target `ct_dr20_rest_1790925322` (kept).

**Artifact (phase 1 — the project's own capability).**

| Observation | Value |
|-------------|-------|
| backup_id | `804698eb2dec4560a946508f710b54ab` |
| artifact | `backups/804698eb…/carbontally-logical-backup-v1.tar.gz.enc` |
| artifact bytes / SHA-256 | 967,844 · `dc68325becff496f907524002cef15a7e91103cbdb23f03dd8999efb9deb52e1` |
| backup wall-clock | 0.97 s |

**Recovery (phase 2) and measured RTO.**

| Observation | Value |
|-------------|-------|
| `pg_dump` bytes / seconds | 3,228,129 · 0.64 s |
| **database restore (`pg_restore`) seconds** | **4.08 s** |
| app start (uvicorn → `/api/v2/health` 200) seconds | 4.37 s |
| **recovery-to-service, end to end** (drill start → app healthy) | **≈ 24 s** |

**Measured RPO.** The reconstruction reproduced **every** row present in the
source at backup time — `emission_factors` 7,049 · `customer_factors` 245 ·
`audit_trail` 563 · `auth.users` 1,206 · `organizations` 975, all equal to the
source, and the canonical drill records `row_count_mismatches: {}`. For a
*completed* backup the data-loss window is therefore **0**. The production **RPO
exposure is not a fixed number — it equals the interval between backups**, and no
schedule exists yet (manual, on-demand only, §10). Stated as measured, not
estimated.

**Platform prep (phase 3a) — a recovery-runbook precondition.** A database-only
restore is **not** sufficient to run the platform services:

| Step | Result |
|------|--------|
| restore *with* ownership/ACLs | 62 statements rejected — all `must be able to SET ROLE "supabase_auth_admin"/"supabase_storage_admin"/"supabase_admin"` and `grant options cannot be granted back to your own grantor` (plus the pre-existing `permission denied for table secrets`). `postgres` is **not** a superuser in this stack. |
| `prepare_platform_grants.py --target-db …` | 785 GRANTs; `still_missing_from_target: 0` |
| `prepare_platform_ownership.py --target-db …` | 166 ownership fixes; `remaining_mismatches: 0`, `ownership_matches_source: true` |

**DB / schema / object verification (phase 4), reconstruction vs source.**

| Fact | Reconstruction | Source |
|------|---------------|--------|
| public base tables / RLS-enabled | 150 / 150 | 149 / 149 |
| public policies | 351 | 271 |
| public triggers / functions | 123 / 37 | 103 / 37 |
| `emission_factors` | **7,049** | **7,049** |
| `customer_factors` / `audit_trail` / `auth.users` / `organizations` | 245 / 563 / 1,206 / 975 | 245 / 563 / 1,206 / 975 |
| audit-guard function / trigger | 1 / 1 | 1 / 1 |

The reconstruction carries **more** policies/tables/triggers than the source
because phase 3 replayed the shipped migration chain on top of the restore
(`applied 93`); the restored baseline itself matched the source. RLS is verified
structurally (150/150 tables RLS-enabled) and functionally (the application
enforces the restored policy set — the app probe below).

**Append-only audit ledger (phase 4b) — the H5 conflict, resolved.**

```
unauthorised TRUNCATE public.audit_trail
  -> ERROR: append-only ledger (CT-IMPLEMENT-02): TRUNCATE of public.audit_trail
     is not permitted (set ct.audit_purge_authorised=on only from an authorised purge run)
BEGIN; SET LOCAL ct.audit_purge_authorised = 'on';
  TRUNCATE public.audit_trail;   -> authorised_truncate_rows_after=0
ROLLBACK;
  -> ledger_rows_after_rollback=563
```

The guard refuses the fixture's TRUNCATE (reproduced on the reconstruction) and
its **own documented authorised path** works and is fully reversible. No
invariant, policy, trigger or fixture is weakened.

**Application-level recovery validation (phase 5) — 7/7 PASS.**

A **parallel** disposable stack (`ct_dr20_auth` / `ct_dr20_rest` /
`ct_dr20_gateway`, port 54441) was pointed at the reconstruction and the real
FastAPI application was run against it. The pre-existing `ct_final02_*` rehearsal
stack, the CLI stack and every other database were left untouched.

| Check | Result |
|-------|--------|
| app startup / DB connectivity (`GET /api/v2/health`) | **200** |
| authentication — real password grant through GoTrue | **200**, token `role=authenticated` |
| emission-factor availability (`GET /api/v3/emissions/factors`) | **200**, `total>0` |
| org access + reporting/calculation workflow (`GET /api/v3/emissions/dashboard`, own org) | **200** |
| tenant isolation (same token, a *foreign* organisation) | **403** |
| representative calculation (`POST /api/v2/factor-match`) | **200**, `status=matched` |

Served by the reconstruction (app log):
`✅ User authenticated: owner@demo.carbontally.local` ·
`✅ Found active organization member … Org: 11111111-… Role: owner` ·
`GET …/dashboard?organization_id=1111… 200 OK` ·
`GET …/dashboard?organization_id=cb79… 403 Forbidden`.

**Scope boundary.** This drill validates the **database** recovery path with the
real application. It does **not** exercise storage-object recovery (§4.3): a
database-only restore proves the database half, by design.

### 4.2 In-scope alternative evidence for phase 4

Phase 4's *intent* — "the application's own code can operate on the
reconstruction" — is satisfied by two suites that do not fight the ledger guard,
run against the same real PostgreSQL used by the drill:

| Evidence | Command | Result |
|----------|---------|--------|
| The shipped backup stack operates on a real database | `pytest tests/integration/backup/test_exporter_local.py -q` | **9 passed** |
| The shipped restore stack rebuilds and verifies a real database | `pytest tests/integration/backup/test_restore_local.py -q` | **13 passed** |
| The recovered database is itself re-backup-able and restorable | drill run whose *source* was the reconstruction (`/tmp/ct_backup_drill_ct_final02_src_restored_82482`, and four sibling runs) | phase 1 published an artifact from the reconstruction |

### 4.3 Storage-object backup — status (recorded, not redesigned)

The CoStrict re-verification orders that the backup/restore architecture **must
not** be redesigned. Storage-object backup is therefore recorded, not rebuilt:

* **Implemented and wired** — `backend/backup/objects.py` (`export_objects`,
  `restore_objects`, `SupabaseStorageSource` / `InMemoryStorageSource`, an
  `ObjectBackupManifest` with per-object SHA-256), driven as `kind='objects'` in
  `backend/backup/worker.py` (`_run_object_job` → `export_objects`), paired by
  `backup_set_id`, envelope-encrypted (D3), and verified by
  `backend/backup/verification.py` (`verify_stored_artifact`, surfaced on the
  admin `/verify` endpoint).
* **Not covered by the DR-20 drill** — the database artifact deliberately excludes
  Storage objects (§14); the drill is a *database*-recovery drill. Object recovery
  is a separate, sequenced job.
* **Specific test coverage is absent** — the backup-scoped suites (241 unit + 22
  integration, all green) contain **no test that references the object-export
  symbols** (`export_objects` / `restore_objects` / `StorageObjectSource`) and no
  `_run_object_job` test. That is consistent with the CoStrict verdict
  *"IMPLEMENTED, NOT independently verified"*; it is **not** closed here and must
  not be reported as verified.

---

## 5. Changes made in this session

Two source changes, both closing the audit gap found in the restore half of the
feature (no behaviour change to the export/API paths):

1. **`backend/backup/restore.py` — the fail-closed target guard is now enforced on
   the execution path.** `assert_disposable_target` existed, was exported, and
   documented itself as a check "a future caller cannot forget", but **nothing
   called it**: no tool, no test, no API handler. `restore_members` now resolves
   the target (`target_database`, else the server's own `current_database()`) and
   calls the guard *before executing the first statement*, and it records that
   resolved name in `RestoreResult.target_database`. Rationale: a restore
   overwrites what it finds, so the guard must be unavoidable, and the previously
   un-exercised path had no regression risk (no callers existed).
2. **`backend/tests/integration/backup/test_restore_local.py` — new.** 5 test
   functions / 13 parametrised cases covering the D4 restore library against a
   real server (see §3.2), including the negative control that proves
   `verify_restored` is not vacuous and the guard tests above.

No migration, API, schema or frontend change was made. The new test file is
additive; the only modified line range in shipped code is the `restore_members`
prologue plus its docstring.

**DR-20 drill session (2026-10-02, §4.1).** No shipped code was changed. The
drill driver and its disposable environment live **outside** the repository
(`/home/shomonrobie/ct_local_env/dr20_recovery/`, built on the pre-existing
`final02_rehearsal` stack recipe); the only repository change in that session is
this document.

---

## 6. Pre-existing failures (not caused by this workstream)

### 6.1 Four migration-guard unit tests — proven pre-existing

These four fail, and they failed **with the BACKUP-02 migration moved aside**,
which is the decisive experiment:

| Test | Assertion that fails | First failing fact without BACKUP-02 |
|------|---------------------|--------------------------------------|
| `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `len(names) == 71` | repository has **95** migrations (96 with BACKUP-02) |
| `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | `later in (...)` | many migrations follow I1 (p16r5, …) |
| `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | `names[-1] == 20261007000000_p8_insight_data_quality_reproducibility.sql` | last is `20261026000000_ct_backup_01_backup_jobs.sql` — i.e. **BACKUP-01**, not BACKUP-02 |
| `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | `existing.name in p17_names` | first offender is `20261025000000_ct_step2_documents_bucket_size_alignment.sql` |

They are pinned to historical baselines that stopped holding when earlier
migrations landed (`ct_step2`, `ct_final_01`, `ct_backup_01`). A rebase/refresh
task for them is H3 in §10; they are **not** a BACKUP-02 regression.

### 6.2 The other four pre-existing unit failures

`pytest tests/unit -q` reports **8** failures in total: the four migration guards
of §6.1 plus:

| Test | Area |
|------|------|
| `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | V3 discovery requests |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | invoice extraction suggestions |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | invoice extraction suggestions |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | invoice extraction suggestions |

None of these modules is imported, referenced or modified by the backup
workstream, and the full-suite failure set is identical before and after this
session's two changes (same eight identifiers, exit code 1 in both runs: before
`/tmp/pytest_unit_all2.txt`, after `/tmp/unit_after.txt`). They are handed over
untouched.

---

## 7. How to reproduce everything in this document

```bash
cd /home/shomonrobie/ct_93d5cdd/backend

# 1. Backup-scoped unit suites (no database required)
.venv/bin/python -m pytest tests/unit/backup -q
.venv/bin/python -m pytest tests/unit/api/test_backup_admin_api.py -q
.venv/bin/python -m pytest tests/unit/tools/test_backup_export.py \
                             tests/unit/tools/test_backup_recovery_drill_guard.py -q

# 2. Integration suites — require the disposable local PostgreSQL on 127.0.0.1:54426
.venv/bin/python -m pytest tests/integration/backup -q          # expect: 22 passed

# 3. The canonical recovery drill (from the repository root; the drill puts
#    backend/ on sys.path itself, so any interpreter with the backend
#    dependencies installed works)
cd /home/shomonrobie/ct_93d5cdd
backend/.venv/bin/python tools/backup_recovery_drill.py \
    --source ct_final02_src --target ct_final02_src_restored_$(date +%s) --keep-target

# 4. The DR-20 recovery drill WITH application-level validation (§4.1). Disposable
#    and outside the repository: it backs up, restores into a fresh target DB,
#    brings up a PARALLEL app stack (ct_dr20_* on :54441), runs the real
#    application against the reconstruction and tears the stack down. The
#    reconstruction is left in place (drop it manually if desired).
bash /home/shomonrobie/ct_local_env/dr20_recovery/run_drill.sh
```

The DSN for step 2 can be redirected with `CT_BACKUP_TEST_DSN`; both suites skip
themselves when that host is not loopback.

---

## 8. Sign-off checklist

* [x] BACKUP-01 and BACKUP-02 migrations present; BACKUP-02 is the newest migration and is intact (203 lines, ends `COMMIT;`)
* [x] Backup-scoped suites: **280 tests, all passing** (241 unit backup + 17 admin API + 22 integration)
* [x] Admin backup API mounted (`/api/v3/admin/backups`, 9 endpoints) with 17 unit tests
* [x] Exporter integration suite: 9/9 against a real PostgreSQL
* [x] **Restore library exercised end to end for the first time: 13/13 (new)**
* [x] Fail-closed restore target guard enforced on the execution path, tested
* [x] Drill phases 1 and 2 clean (artifact verified, zero recovery deltas, 7,049 `emission_factors` recovered)
* [x] **DR-20 recovery drill recorded and reproducible (§4.1): fresh backup → fresh disposable restore → platform prep → migrations → DB/RLS/ledger verification → real application; 7/7 app-level checks PASS; RPO = 0 for a completed backup; RTO ≈ 24 s end to end (database restore 4.08 s)**
* [x] H5 resolved — audit-ledger fixture conflict handled by a disposable-only procedure; invariant, fixture and repository untouched
* [x] Frontend jest 15/15
* [x] All 8 unit-suite failures triaged and proven unrelated to BACKUP-02
* [ ] H1 decision: how (and whether) restore is exposed in the product
* [ ] H2: informational `ddl.sql` member emits `ENABLE ROW LEVEL SECURITY`
* [ ] H3: stale migration-guard tests refreshed
* [ ] H6: BACKUP-02 migration + the new backup/restore files **committed** (all still untracked)
* [ ] H10: adopt the recovery-runbook order (restore → replay → platform ACL/ownership)
* [ ] H11: define the production backup cadence (RPO = the cadence; none exists)
* [ ] H12: storage-object backup has no direct test coverage (§4.3)
* [ ] Independent verification of the artifact, the restore and the DR-20 evidence

---

## 9. Files touched in this session

| Path | Change |
|------|--------|
| `/home/shomonrobie/ct_93d5cdd/backend/backup/restore.py` | `restore_members` enforces `assert_disposable_target` before the first statement (resolving `current_database()` when the caller does not name the target) and records the resolved name in `RestoreResult.target_database`; docstring updated |
| `/home/shomonrobie/ct_93d5cdd/backend/tests/integration/backup/test_restore_local.py` | **new** — 5 test functions / 13 cases: real restore + verification, non-vacuous-verification negative control, target-guard acceptance/refusal, guard enforced on the execution path |
| `/home/shomonrobie/ct_93d5cdd/docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002.md` | **new** — this document |

Nothing else was edited in the repository. Note that the working tree contains
earlier changes from the wider workstream (including the **untracked** BACKUP-02
migration, item H6); those are outside this session's scope and are flagged for
CoStrict rather than altered here. The DR-20 drill added only disposable files
**outside** the repository (`/home/shomonrobie/ct_local_env/dr20_recovery/`:
`run_drill.sh`, `stack_up.sh`, `stack_down.sh`, `nginx.conf`, `dr20_app_probe.py`).

---

## 10. Handoff items for CoStrict

Ordered by severity. **H1–H3 need a decision or a code change**; H4–H9 are
verification and housekeeping; **H10–H12 were raised by the DR-20 drill (§4.1)**.

**H1 — Decide how D4 restore is reached (biggest open product question).**
`backend/backup/restore.py` is a complete, now-tested library, but **no product
code path calls it**: the 9 admin endpoints cover status/list/policy/create/
detail/pair/verify/download — there is no restore endpoint, and no job kind that
performs one. Options: (a) add an admin-only restore endpoint/job that requires an
explicit disposable target and emits audit records, or (b) ratify restore as an
operator-only capability whose entry points are the library plus
`tools/backup_recovery_drill.py`, and document that in the runbook. Either way the
§13 guard is now unavoidable inside the library (§5, item 1).

**H2 — The informational `ddl.sql` member is incomplete for RLS.**
`backend/backup/catalog.py` (informational renderer, `CREATE POLICY` at ~line 442)
emits 271 `CREATE POLICY` statements but **no** `ALTER TABLE … ENABLE ROW LEVEL
SECURITY`; the drill's `ddl_can_rebuild.rls_enabled` is therefore `false`. The
**functional** restore path is correct — `restore.py:372-377` emits the ENABLE
statements from the catalog, the source has 149/149 public tables RLS-enabled, and
the new restore IT asserts `relrowsecurity` is true in the reconstruction. Fix the
informational renderer (or state explicitly that replaying `ddl.sql` by hand is not
a supported restore path) so a human reading the artifact is not misled.

**H3 — Refresh the four stale migration-guard tests** listed in §6.1. Prefer
set/prefix-based assertions over hard-coded counts and "the latest migration is
mine" pins, so that adding a migration does not break unrelated guards.

**H4 — Four further pre-existing unit failures, unrelated to backup** (see §6.2):
`tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
and three in `tests/unit/engines/test_extraction_suggestions.py`. They touch
discovery requests and invoice extraction; nothing in this workstream references
them.

**H5 — RESOLVED (2026-10-02).** *Phase 4* is now exercised by the DR-20 drill
(§4.1) against the real application, and the ledger/fixture conflict is
demonstrated with a **disposable-only** procedure that uses the guard's own
authorised path inside a rolled-back transaction — the invariant, the fixture and
the repository are untouched. *Phase 3*: `rc2_constraints` remains accepted as
**pre-existing data** (NULL `conversations.organization_id` in the source); the
second failure (`d35`) was a runbook-ordering artefact and applies cleanly as
`supabase_admin` (see H10).

**H6 — Land the migration and the feature (still uncommitted).** Every BACKUP-01/02
artefact is **untracked** and was **not** committed in this session (no commit was
authorized): `supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql`
(227 lines), `supabase/migrations/20261027000000_ct_backup_02_backup_sets_and_verification.sql`
(203 lines — **must remain the newest migration**; drill phase 1 depends on it),
`backend/backup/{jobs,policy,objects,restore,retention,s3store,sigv4,verification,worker}.py`,
`backend/api/v3_backups.py`, `backend/tests/unit/backup/{test_jobs,test_sigv4_and_s3store}.py`,
`backend/tests/integration/backup/test_restore_local.py`,
`backend/tests/unit/api/test_backup_admin_api.py`, plus modified
`backend/backup/{__init__,errors,settings,storage}.py`.

**H7 — Confirm the exporter's schema scope with the independent verifier.** The
source carries 271 `public` policies and 275 policies cluster-wide (Supabase
`storage`); the manifest exports `['public']` only. That is the F2 credential
deny-list working as designed — it should be stated as intended, not discovered
later.

**H8 — The new integration suites need a loopback DSN with `CREATEDB`.**
`test_exporter_local.py` and `test_restore_local.py` skip unless the DSN host is
loopback (`CT_BACKUP_TEST_DSN`, default
`postgresql://postgres:postgres@127.0.0.1:54426/postgres`). Record this in the
verification runbook so a skip is never mistaken for a pass.

**H9 — Environment state left in place.**
Lab server `supabase_db_carbon_ledger` (`127.0.0.1:54426`) holds the source
`ct_final02_src` and the kept reconstruction `ct_final02_src_restored_82482`;
fresh drill containers `ct_drill_pg` (:55432) and `ct_drill2_pg` (:55433) are
healthy; drill work directories are `/tmp/ct_backup_drill*`; drill logs are
`/tmp/drill*.log`, `/tmp/drill_run1.txt`, `/tmp/drill_p4*.txt`. When creating a
database on the lab image, use `TEMPLATE postgres`/`template1` (or clone an
existing `ct_*` database) — a `_supabase` template is not present there.
Retired: the restore drill's `--target` databases from superseded attempts and the
`ct_backup_it_*`/`ct_backup_rs_*` databases are dropped by the tests themselves.

**H10 — Adopt the recovery-runbook order (raised by §4.1).** A database-only
restore is **not** platform-runnable in this stack: `postgres` is not a superuser,
so ACL/ownership statements are rejected on restore (62 statements) and the
platform services cannot start until parity is restored. Verified order:
**restore → replay migrations → apply platform ACL/ownership parity** (the two
`prepare_platform_*` steps, or a restore run as `supabase_admin`). Documented in
§4.1; belongs in the recovery runbook.

**H11 — Define the production backup cadence.** RPO is the interval between
backups; today there is no schedule (manual/on-demand only). The DR-20 drill proves
RPO = 0 for a *completed* backup, but production RPO exposure stays undefined until
a cadence exists (roadmap Phase 4).

**H12 — Storage-object backup has no direct test coverage.** See §4.3: the module
is implemented and wired, but no test references `export_objects` /
`restore_objects` / `StorageObjectSource` / `_run_object_job`. This is the
*"IMPLEMENTED, NOT independently verified"* gap and is **not** closed here.

---

## 11. Final status and verdict

| Item | Status |
|------|--------|
| BACKUP-01 (job model) migration + `backend/backup/jobs.py` | Implemented; unit-tested; **uncommitted** (H6) |
| BACKUP-02 (backup sets + verification) migration | Implemented; newest migration; **uncommitted** (H6) |
| Logical exporter (D1) + artifact/crypto/storage (D2/D3) | Implemented; integration-tested against real PostgreSQL |
| Restore library (D4) + disposable target guard | Implemented; **exercised end to end for the first time** (13/13) |
| Admin backup API | Implemented (9 endpoints, 17 unit tests) |
| Disposable recovery drill (workstream F) | Implemented; canonical tool unchanged |
| **DR-20 — proven restore into a disposable environment with recovery evidence** | **Evidence COMPLETE and reproducible (§4.1); 7/7 application-level checks PASS** |
| Storage-object backup | Implemented + wired; **not** covered by the DR-20 drill; **no direct test coverage** (§4.3) |
| H1 (restore exposure) · H2 (`ddl.sql` RLS) · H3 (guard tests) | **Open** |
| H10 (runbook order) · H11 (cadence) · H12 (object coverage) | **Open** |
| Independent verification | **OUTSTANDING** — this document is implementer evidence |

**Verdict.**

> **DR-20 recovery evidence: CLOSED.** A verified artifact was produced by the
> project's own `BackupService`, restored into a fresh disposable database, and the
> **real application** served the recovered data — startup, authentication,
> organisation access, tenant isolation, emission-factor availability and a
> representative calculation all passed — with RPO = 0 for a completed backup and
> RTO ≈ 24 s end to end (database restore 4.08 s). The append-only audit invariant
> was reproduced and its authorised escape hatch verified **without weakening
> anything**.
>
> **DR-20 as a Product-Owner gate: NOT CLOSED.** The evidence above is
> implementer-generated. Independent verification of the artifact, the restore and
> this DR-20 evidence is **outstanding**; the BACKUP-01/02 artefacts remain
> **uncommitted**; H1–H3 and H10–H12 remain open; and storage-object recovery is
> neither drilled nor directly tested. Nothing here constitutes independent
> verification.

