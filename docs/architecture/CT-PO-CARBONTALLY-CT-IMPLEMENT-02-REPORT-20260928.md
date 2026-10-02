# CT-IMPLEMENT-02 — DB-layer remediation + PD-1/PD-2 schema (implementation report)

**Date:** 2026-09-28
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Base commit:** `af08f45`
**Status:** DATABASE LAYER **IMPLEMENTED · TESTED · VERIFIED** (from-zero rebuild);
APPLICATION LAYER **PARTIALLY IMPLEMENTED · UNIT-TESTED · NOT INDEPENDENTLY VERIFIED**

> **INDEPENDENT VERIFICATION NOT PERFORMED.** Every result below is from the
> implementing agent's own harness on disposable infrastructure. `TESTED` and
> `VERIFIED` here mean "the named evidence file reproduces the stated result",
> not "independently accepted" (AGENTS.md §73).

---

## 1. Task and scope

Finish the CT-IMPLEMENT-02 DB-layer remediation (make `ct02_db_suite.sql` green),
then rebuild the canonical schema **from zero** with the three new migrations and
pin the resulting fingerprints. Scope of this change-set:

| Layer | In scope | Out of scope (remaining) |
|---|---|---|
| Schema | 3 additive migrations (audit hardening, report sharing, scheduled reporting) | any modification to the 89-migration baseline (forbidden — proved unchanged) |
| Harness | `ct02_db_suite.sql`, `ct02_verify_db.py`, `canonical_schema_verify.py`, `canonical_schema_rebuild.sh` | independent QA harness (`qa_harness/`) |
| App | pure domain + runner for canonical scheduled reporting (PD-2) | route/data-layer rewrite for PD-1/PD-2, R-6 audit-site classification, R-1/R-3/R-5/R-8/R-9 |

No business policy was invented. PD-1 and PD-2 were implemented as ratified;
where a decision was needed it is recorded as PO-decision-gated (see §8).

---

## 2. Database changes (migrations)

| Migration | Adds | Modifies |
|---|---|---|
| `supabase/migrations/20261021000000_ct02_audit_ledger_hardening.sql` | `ct02_audit_truncate_guard()`, `ct02_append_only_guard()` + 5 guards | nothing |
| `supabase/migrations/20261022000000_ct02_report_sharing.sql` | `report_shares`, `report_share_access_events` (+ policies/functions) | nothing |
| `supabase/migrations/20261023000000_ct02_scheduled_reporting.sql` | `report_schedule_definitions`, `report_schedule_runs`, `ct02_report_schedule_validate()`, `ct02_report_schedule_run_guard()` | nothing |

**PD-2 forbids recreating the retired `report_schedules` / `report_history`
tables.** They remain absent and are asserted absent (§4). The canonical names
are `report_schedule_definitions` / `report_schedule_runs`.

### 2.1 Verified headline-count deltas (89 → 92 migrations)

| Count | Baseline (CT-SCHEMA-02) | Extended (CT-IMPLEMENT-02) | Delta |
|---|---|---|---|
| public tables | 145 | 149 | +4 |
| public tables with RLS | 145 | 149 | +4 |
| public tables **without** RLS | 0 | 0 | — |
| policies | 227 | 235 | +8 |
| policies granting anon/public | 0 | 0 | — |
| foreign keys | 172 | 182 | +10 |
| indexes | 551 | 569 | +18 |
| public functions | 31 | 37 | +6 |
| triggers | 88 | 100 | +12 |
| columns (all schemas) | 4592 | 4652 | +60 |

Every count is additionally asserted **not below** the frozen baseline, so the
extended chain can only ever add schema objects.

---

## 3. Fingerprints recorded from the verified rebuild

Never guessed — read from the successful run, then re-pinned and re-verified
(§4.2).

| Value | Fingerprint |
|---|---|
| Baseline migration set (89 files, CT-SCHEMA-01/02) | `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` (unchanged) |
| Extended migration set (92 files) | `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` |
| Extended canonical inventory | `5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407` |
| Canonical inventory (CT-SCHEMA-01 baseline) | `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f` (unchanged) |

The **baseline** fingerprint is recomputed inside the verifier from exactly the
89 non-CT-IMPLEMENT-02 files and compared to the recorded value, so appending
migrations can never mask a modification to an earlier migration — even if the
extended fingerprint were re-pinned.


---

## 4. Runtime verification (disposable infrastructure only)

### 4.1 From-zero canonical rebuild — VERIFIED

```
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
  --prefix ct_impl02b --port 55481 --profile ct-implement-02 \
  --evidence /tmp/ct_impl02b_evidence
```

Target: brand-new disposable container/volume `ct_impl02b_pg` /
`ct_impl02b_pgdata`, Supabase Postgres 17.6.1.159 + storage-api v1.69.0 (no
existing data, no authoritative environment touched).

Result (`/tmp/ct_impl02b_evidence/verify.txt`, tail of
`/tmp/ct_impl02b_rebuild.log`):

```
[01:04:30] REBUILD VERIFIED — canonical schema reproduced (see /tmp/ct_impl02b_evidence)
=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===
```

All 92 migrations applied; PHASE A/B/C (platform layer, migrations 1–26, D32
operator step + idempotency re-run) and PHASE D (migrations 27–92) completed with
zero failures.

### 4.2 Pinned values re-verified against the live rebuilt target

Re-running the verifier against the same target reproduced the recorded values
(`/tmp/ct_impl02_evidence/verify_rerun.txt`, exit 0):

```
PASS  baseline_migration_set_unchanged — … still reproduce 40b168b393fb2ca7…
PASS  migration_set_only_authorised_revision — files differing from CT-SCHEMA-01 HEAD:
      ['20260823000000_d32_private_documents_storage.sql',
       '20261021000000_ct02_audit_ledger_hardening.sql',
       '20261022000000_ct02_report_sharing.sql',
       '20261023000000_ct02_scheduled_reporting.sql']
PASS  inventory_fingerprint_matches_canonical — actual=5291cd91… expected=5291cd91…
PASS  count_public_tables — observed=149 expected=149
PASS  count_policies — observed=235 expected=235
PASS  legacy_absent_report_history / legacy_absent_report_schedules /
      legacy_absent_notification_delivery_log / legacy_absent_defra_conversion_factors
=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===
```

### 4.3 CT-IMPLEMENT-02 database suite — PASS (68 assertions, 0 FAIL)

Run against the **from-zero rebuilt** database (stronger than the earlier
migrated-in-place run):

```
. /tmp/ct_impl02.env
E2E_DB_USER=postgres python3 e2e/environment/scripts/ct02_verify_db.py \
  --host 127.0.0.1 --port 55480 --db postgres --password "$CT02_PW" \
  --json /tmp/ct_impl02_evidence/ct02_db_suite.json
```

Evidence `/tmp/ct_impl02_evidence/ct02_db_suite.txt`:

```
assertions_passed=68
assertions_failed=0
suite_completed=True
transaction_aborted_early=False
VERDICT: PASS — every CT-IMPLEMENT-02 database assertion holds.
rc=0
```

This supersedes the earlier migrated-in-place run (`/tmp/ct02_suite_run6.txt`,
68/0). The suite covers, among others: tenant isolation (a consultant of another
client sees 0 rows), anon denials on `emissions_logs` / `report_shares` /
`report_schedule_definitions`, PD-1/PD-2 table and policy presence, append-only
refusals, and the emissions provenance chain resolving both forward and backward.

### 4.4 Negative control (the guard has teeth)

Dropping `ct02_audit_trail_no_truncate` and retrying the TRUNCATE still refuses —
the guard is not satisfied merely by existing (`/tmp/ct02_negctl.txt`).

### 4.5 Application unit tests

```
cd backend
python3 -m pytest tests/unit/domain/test_report_schedule.py \
                 tests/unit/services/test_report_schedule_runner.py -q
# 38 passed
```

---

## 5. Harness defects found and corrected (not normalised away)

The first from-zero run of the extended chain produced **81 PASS / 2 FAIL**. Both
failures were defects in the *verifier*, not in the schema; each was fixed by
evidence, and the fix is confirmed by the green re-run (§4.1–4.2):

1. **`migration_set_only_authorised_revision` ignored untracked files.** The check
   used `git diff --name-only HEAD`, which cannot see a new migration until it is
   committed, so it reported "only D32 differs" and failed against the allowed
   set. Fixed to include `git ls-files --others --exclude-standard`
   (AGENTS.md §70 — nothing was committed to make the check pass).
2. **`ct02_guards_attached_audit_trail` expectation was a guess (2 guards).**
   Replaced with the trigger→function map transcribed from
   `20261021000000_ct02_audit_ledger_hardening.sql`. The truth: `audit_trail`
   carries **one** CT-IMPLEMENT-02 guard (`ct02_audit_trail_no_truncate` →
   `ct02_audit_truncate_guard`); `audit_logs` and `activity_logs` carry two each
   (truncate + append-only row guard). `audit_trail` deliberately has no new row
   guard because its row immutability is the pre-existing ledger trigger
   (migration `20260912000000`).

Also corrected in the same unit: `check_counts` now distinguishes an exact
expectation from a monotonic floor, and the extended-chain inventory is *recorded*
on a first run and *enforced* thereafter (the `record_only` branch). Recording a
value is never reported as a PASS of the property it will later enforce.

Earlier-session harness fixes (carried forward, same files): `ct02_expect_ok_as`
no longer fabricates a PASS via `ct02_assert_actor`; the `audit_logs` probe uses
the real columns `(action_type, action)`; the `activity_logs` row-guard tests
insert a row before asserting UPDATE/DELETE/TRUNCATE refusal.

---

### 5.1 Post-commit finding F-6 (state-aware provenance) — corrected

Committing the three migrations legitimately changed what "HEAD" means, and two
provenance assertions that had been written for the *pre-commit* state began to
fail (92 pass / 2 fail) — this was caught by a deliberate post-commit re-run, not
by assuming the earlier result still held:

* `migration_set_provenance_ct_schema_01` asserted that `git HEAD` itself
  reproduces the CT-SCHEMA-01 fingerprint. Once the CT-IMPLEMENT-02 migrations are
  committed, HEAD has legitimately moved on, so the assertion was false — **not**
  a schema defect.
* `migration_set_only_authorised_revision` compared against `git diff HEAD` only,
  so committed-but-in-HEAD files dropped out of the comparison while the allowed
  set still listed them.

Both were rewritten to be **state-aware and strictly stronger**, and re-verified
green against both live rebuilt targets (`exit=0`):

* `migration_set_provenance_baseline_from_head` — HEAD's migration set **minus**
  the CT-IMPLEMENT-02 additions must reproduce one of the two recorded baseline
  anchors: CT-SCHEMA-01 `d73e1e2b…` or CT-SCHEMA-02 `40b168b3…`. The observed
  value here is `d73e1e2b…` (i.e. HEAD is still exactly CT-SCHEMA-01 plus the
  three CT-IMPLEMENT-02 files, because the authorised D32 revision is still
  uncommitted). Any *third* value means the baseline was altered and fails.
* `migration_set_only_authorised_revision` — working-tree vs HEAD is now read from
  `git status --porcelain`, which reports tracked modifications **and** untracked
  additions, so the check is correct both before and after commit. Observed:
  `['20260823000000_d32_private_documents_storage.sql']`, with the three
  CT-IMPLEMENT-02 files reported as already in HEAD.

Coverage preserved: a rogue migration still fails — committed, it joins the
baseline subset and changes that fingerprint; uncommitted, it is not in the
allowed set.

Post-commit verification against both targets:

```
=== target ct_impl02b (from-zero VERIFIED rebuild) ===
=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===
=== target ct_impl02 (first from-zero rebuild) ===
=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===
```

---

## 6. Application-layer change (new, additive — PD-2 domain + runner)

### 6.1 `backend/domain/report_schedule.py` (new)

Pure, dependency-free canonical scheduled-reporting model. Every constant mirrors
a database constraint, so the model and the schema cannot drift silently:

| Module constant | Mirrors |
|---|---|
| `FREQUENCIES = (weekly, monthly, quarterly, annual)` | `report_schedule_definitions_frequency_check` |
| `RUN_STATUSES`, `TERMINAL_RUN_STATUSES` | `report_schedule_runs_status_check` |
| `SCHEDULE_RESULTS = (succeeded, failed, skipped)` | `report_schedule_definitions_result_check` |
| `DEFAULT_RETRY_POLICY = {max_attempts: 3, backoff_minutes: [5,30,120]}` | `retry_policy` column default |
| `MAX_ATTEMPTS_BOUNDS = (1, 10)` | `…_retry_policy_check` / `…_attempt_check` |
| `DEFAULT_TIMEZONE = "Europe/London"`, `DEFAULT_RUN_TIME = 07:00` | column defaults |

It also provides `validate_frequency`, `validate_timezone`,
`resolve_retry_policy`, `attempt_number`, `can_retry`, `backoff_delta`,
`next_occurrence` (timezone-correct period arithmetic including DST), `is_due`
(reads the persisted due time only), and the `ScheduleDefinition` /
`ProducedReport` value objects.

### 6.2 `backend/services/report_schedule_runner.py` (new)

The orchestration module that
`20261023000000_ct02_scheduled_reporting.sql` names explicitly ("orchestration is
the application's job — see backend/services/report_schedule_runner.py") and that
did not exist. `ReportScheduleRunner.run_due()`:

* reads due schedules from the **persisted** `next_run_at` (restart-safe);
* claims each due slot via `open_run` → the UNIQUE
  `(schedule_id, scheduled_for)` refusal means a repeated tick is a recorded no-op
  (no duplicate report) — verified by test;
* records `succeeded` **with** the canonical `report_id`/`report_version_id`, or
  `skipped` with a reason, or `failed` with an error code and message; a producer
  that returns "success" without a report id is recorded as `no_report_produced`
  (never a fake success);
* applies `retry_policy` backoff on failure and **pauses** the schedule
  (`is_active = false` + `paused_at`) when `max_attempts` is exhausted;
* appends an audit entry per outcome with `correlation_id = schedule id`, exactly
  as the migration's table comment requires, and never lets an audit failure break
  a run.

The store, producer and audit sink are injected (`ScheduleStore`,
`ReportProducer`, `AuditSink` protocols), so the service holds no database client
and cannot itself bypass RLS or the report workflow.

### 6.3 Tests (new)

* `backend/tests/unit/domain/test_report_schedule.py` — 27 tests: vocabulary ==
  schema CHECKs; `daily` rejected with a message naming the retired surface;
  malformed retry policies rejected; attempt/backoff/`can_retry` semantics; period
  arithmetic including an explicit DST case and an explicit anchor case; `is_due`
  reads persisted state only; value-object defaults are per-instance.
* `backend/tests/unit/services/test_report_schedule_runner.py` — 11 tests against
  an in-memory store that reproduces the UNIQUE-slot refusal and single-transition
  run states: success path, idempotent repeat tick, described skip, failure with
  backoff, retries-exhausted pause, no-report failure, unusable stored
  configuration, audit-failure resilience, nothing-due no-op, due-selection
  arguments, naive-tick rejection.

One defect was found by these tests during development and fixed before the run:
`ScheduleDefinition.from_row` originally referenced the module-level default
`retry_policy` object, so instances shared mutable state; it now resolves (copies
and validates) the policy per instance, and a test asserts non-sharing.

---

## 7. Findings (recorded, not normalised away)

| # | Severity | Finding | Status |
|---|---|---|---|
| F-1 | High | `POST /api/reports/schedule` (+ list/delete) and the `/reports/{id}/share` family in `backend/routes/reports.py` read/write the **retired** `report_schedules` table, which the canonical schema does not contain. The create path was **live-broken** against any canonical database. | NOT FIXED here (scope). Canonical tables now exist; the route/data-layer rewrite is the next unit. |
| F-2 | Medium | `GET /api/reports/schedule/frequencies` advertises `daily`, which the canonical frequency CHECK rejects — the legacy advertisement contradicts the ratified model. | Recorded in code (`LEGACY_UNSUPPORTED_FREQUENCIES`) + tested; the endpoint is left unchanged because F-1 makes the surface non-functional anyway. |
| F-3 | Medium | The PD-2 migration references `backend/services/report_schedule_runner.py` as the orchestration point, but no such module existed — the schema was complete with **nothing able to execute a schedule**. | FIXED: module implemented and unit-tested (§6.2). Not yet wired to a worker/route. |
| F-4 | Medium | `report_versions` has RLS enabled with **zero** policies; clients see nothing and the server-side org-filtered read is authoritative. | Documented posture from `20260921000000`; asserted in the suite. Unchanged. |
| F-5 | Informational | Email-addressed share lookup matches the authenticated email exactly (case/whitespace sensitive). | Recorded; behaviour asserted, not changed. |

---

## 8. PO-decision-gated work (not implemented, not invented)

* **R-6 — audit call-site classification.** The strict-failure mechanism exists,
  but classifying the ~35 canonical audit call sites into *fail-closed* vs
  *log-and-continue* is a product/operations decision (AGENTS.md §62). No
  classification was invented.
* **R-7 — retention enforcement.** Destructive enforcement needs a data-class
  inventory and a reversibility review first.
* **R-10 — audit coverage gaps** (auth events, security-setting changes, read
  auditing). Each needs either an existing-policy implementation or a new
  privacy/product decision.



---

## 9. Remaining work (explicitly not claimed as complete)

1. **PD-1 application layer:** data layer + route rewrite for share / revoke /
   access-history against `report_shares` and `report_share_access_events`
   (replacing the retired-table path, F-1).
2. **PD-2 wiring:** a data layer implementing `ScheduleStore`, a `ReportProducer`
   bound to the canonical report engine, a route rewrite for schedule
   create/list/pause/delete, and a worker/trigger that calls `run_due()`.
3. **R-6** classification + mechanism once the PO decision is ratified.
4. **R-1** remaining factor read sites (~37; **status 2026-09-28: reduced to 19
   occurrences in 3 backend files by CT-IMPLEMENT-04 — see its §5**); **R-3** provenance suite;
   **R-5** documentation truth (including `API_ENDPOINTS.md`); **R-8** feature
   catalogue regeneration; **R-9** seeded tenant-isolation negative suite.
5. **R-11 live migration:** EXTERNAL BLOCKER — no production target and no
   verified recovery point.
6. Independent QA of every result in this report.

---

## 10. Files changed

**New — schema**
* `supabase/migrations/20261021000000_ct02_audit_ledger_hardening.sql`
* `supabase/migrations/20261022000000_ct02_report_sharing.sql`
* `supabase/migrations/20261023000000_ct02_scheduled_reporting.sql`

**New — verification harness**
* `e2e/environment/scripts/canonical_schema_rebuild.sh`
* `e2e/environment/scripts/canonical_schema_verify.py`
* `e2e/environment/scripts/ct02_db_suite.sql`
* `e2e/environment/scripts/ct02_verify_db.py`

**New — application**
* `backend/domain/report_schedule.py`
* `backend/services/report_schedule_runner.py`
* `backend/tests/unit/domain/test_report_schedule.py`
* `backend/tests/unit/services/test_report_schedule_runner.py`

**New — report**
* `docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md`

**Unchanged in this change-set:** the 89-migration baseline (proved unchanged by
fingerprint), all routes, all other services, RLS on existing tables.

---

## 11. Security verification

* Tenant isolation is enforced in the schema: every new table has RLS enabled,
  `anon` is revoked on all three, and the new tables expose **no** anon/public
  policy (`count_policies_granting_anon_or_public = 0`).
* `report_schedule_runs` grants `authenticated` **SELECT only** — clients cannot
  manufacture execution history; the runner writes it with the owner role.
* Audit integrity: `TRUNCATE` on `audit_trail` / `audit_logs` / `activity_logs` is
  refused, and `UPDATE`/`DELETE` on the retained legacy audit surfaces is refused
  (proved at runtime, with a negative control proving the guards have teeth).
* The runner cannot bypass RLS: it holds no client and writes through the injected
  store; every outcome is audited.
* No secrets, tokens or signed URLs were introduced by this change-set; the
  disposable target's password lives only in `/tmp/ct_impl02*.env` (never
  committed) — and the harness used is the disposable-only path required by
  F-046-1.

---

## 12. Git state

* Branch `p8-release-reconciled`, base `af08f45`.
* Committed as coherent units (schema + harness, application, report); **not
  pushed**.
* The pre-existing modification to
  `supabase/migrations/20260823000000_d32_private_documents_storage.sql` (the
  CT-SCHEMA-02 authorised revision) is **not** part of this change-set.
* The environment-layer files from the CT-SCHEMA-02 unit remain **uncommitted**
  (`apply_migrations.sh`, `bootstrap.sh`, `reset.sh`, `.gitignore`,
  `e2e/environment/README.md`, `supabase/config.toml`, plus the D32 operator
  scripts). `canonical_schema_rebuild.sh` **requires** them at runtime
  (`apply_migrations.sh` and `d32_storage_operator.sql`), so the committed
  harness is only runnable once that unit is committed too. Stated explicitly
  rather than silently absorbed into this change-set.

---

## 13. Reproduce

```bash
# 1. from-zero rebuild + verification (disposable target)
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
  --prefix ct_impl02c --port 55482 --profile ct-implement-02 \
  --evidence /tmp/ct_impl02c_evidence

# 2. database suite (68 assertions)
. /tmp/ct_impl02c.env
E2E_DB_USER=postgres python3 e2e/environment/scripts/ct02_verify_db.py \
  --host 127.0.0.1 --port 55482 --db postgres --password "$CT02_PW"

# 3. application unit tests
cd backend && python3 -m pytest tests/unit/domain/test_report_schedule.py \
  tests/unit/services/test_report_schedule_runner.py -q
```

**INDEPENDENT VERIFICATION NOT PERFORMED.**
