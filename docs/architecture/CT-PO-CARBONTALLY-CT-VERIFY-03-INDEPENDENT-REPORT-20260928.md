# CT-VERIFY-03 — Independent Verification of CT-IMPLEMENT-02 and CT-IMPLEMENT-03

**Task ID:** CT-VERIFY-03-20260928-INDEPENDENT-REPORT-SCHEDULE-SHARE-AND-CANONICAL-CHAIN-VERIFICATION
**Date:** 2026-09-28
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Role:** Independent verification agent (NOT the implementer)
**Mode:** read-only against the repository; disposable infrastructure only

---

## 1. Task ID

`CT-VERIFY-03-20260928-INDEPENDENT-REPORT-SCHEDULE-SHARE-AND-CANONICAL-CHAIN-VERIFICATION`

## 2. Verification scope

Independently determine whether CT-IMPLEMENT-02 and CT-IMPLEMENT-03 actually
established criteria **A–J** of the task brief: a reproducible canonical
92-migration rebuild; a functioning canonical report-schedule application path;
a functioning report-sharing/revocation/history path; removal of active runtime
dependence on the retired `report_schedules` table; correct canonical frequency
enforcement; correct runner behaviour; correct report/version linkage; correct
audit correlation; correct legacy-route delegation; and correct behaviour
against a fresh disposable PostgreSQL database.

Independence discipline applied:

* the implementer's disposable databases (`ct_impl02*`, `ct_impl03_e2e`) were
  **not** re-used as the verification target;
* a **brand-new** disposable target (`ct_verify03`) was created and the canonical
  rebuild was re-run from zero;
* schema fingerprints and inventory were **recomputed by the verifier's own
  script**, not read from the implementer's evidence;
* the implementer's unit/E2E results were **re-executed**, not trusted;
* **no application code, migration, configuration, production system or Git
  history was modified.**

## 3. Starting SHA

| Property | Value |
|---|---|
| Branch | `p8-release-reconciled` |
| **Starting HEAD (full)** | `b313fc2242b1deca0370ac48749549f5bb435a11` |
| **Ending HEAD (full)** | `b313fc2242b1deca0370ac48749549f5bb435a11` (unchanged — no commit was made) |

## 4. Repository state

The worktree was **already dirty before this verification began**; nothing was
changed by the verifier. Recorded exactly as found:

* **Tracked modifications (pre-existing, not part of CT-IMPLEMENT-02/03):**
  `.gitignore`, `e2e/environment/README.md`,
  `e2e/environment/scripts/{apply_migrations.sh,bootstrap.sh,reset.sh}`,
  `e2e/environment/supabase/config.toml`, and
  `supabase/migrations/20260823000000_d32_private_documents_storage.sql`
  (111 insertions / 10 deletions — the authorised CT-SCHEMA-02 D32 revision,
  **uncommitted**).
* **Tracked deletions:** the 53 legacy files under
  `e2e/environment/supabase/migrations/` (that path is now a **symlink** to
  `../../../supabase/migrations`; the 53-file copy was removed and the directory
  replaced by the symlink — untracked).
* **Untracked (relevant):** `e2e/environment/scripts/d32_storage_operator.sql`,
  `e2e/environment/scripts/verify_d32_policy_semantics.sql`,
  `e2e/environment/scripts/d32_search_path_regression.sh`, the symlink above,
  and a large body of audit/architecture documents plus assorted stray files
  (`8`, `=`, `.costrict/`, `.p18_audit_tmp/`).

Both implementation reports acknowledge this state explicitly (CT-IMPLEMENT-02
§12; CT-IMPLEMENT-03 §22) and state that the environment-layer files are the
**pre-existing CT-SCHEMA-02 unit**, not part of their change-sets — which this
verification confirms from the commit file lists (§5).

## 5. Implementation commits examined

Every commit was inspected with `git show --name-status`.

**CT-IMPLEMENT-02 (base `af08f45`):**

| SHA | Subject | Files |
|---|---|---|
| `8652e34` | canonical audit hardening, report sharing and scheduled reporting **schema** | +7 (4 harness scripts, 3 migrations) |
| `30387ba` | (PD-2) canonical scheduled-reporting domain model and execution runner | +4 (2 app modules, 2 unit suites) |
| `bf11445` | implementation report | +1 (report) |
| `21310af` | make migration-set provenance state-aware (F-6) | 2 (report + verifier) |

**CT-IMPLEMENT-03 (starting SHA `21310af`):**

| SHA | Subject | Files |
|---|---|---|
| `a74359e` | canonical schedule/share data layer, services and producer | +6, ~1 |
| `a599b24` | canonical schedule/share routes, legacy delegation, runner worker | 4 modified + 1 new worker |
| `429df43` | unit + disposable-DB E2E coverage | +5 test files |
| `eff1c56` | implementation report | +1 (report) |
| `a121ecc` | record the ending SHA in the report | report only |
| `6bb8458` | drop an unused import; precise ending-SHA note | 1 code (import) + report |
| `b313fc2` | scope the runner E2E assertions to the schedule under test (N-3) | 1 test + report |

**Unrelated-change check:** every commit's file list is scoped to the task's own
artefacts (schema, harness, app layer, tests, report). No production
configuration, deployment descriptor (Render/Vercel), `supabase/config.toml`, or
unrelated module was absorbed. **No commit other than the CT-IMPLEMENT-02/03
units appears in the range `af08f45..b313fc2`.**

**Push/deploy boundary:** `git log origin/p8-release-reconciled..HEAD` and
`git log github/p8-release-reconciled..HEAD` both list the 11 CT-IMPLEMENT-02/03
commits (plus older unpushed units) — i.e. **nothing was pushed**. No deployment
artefact changed.

## 6. Fresh verification DB identity (F-046-1 compliance)

A **new** disposable target was created by the canonical rebuild harness:

| Property | Value |
|---|---|
| Containers | `ct_verify03_pg`, `ct_verify03_storage` (both newly created) |
| Volume | `ct_verify03_pgdata` (new) |
| Postgres image | `public.ecr.aws/supabase/postgres:17.6.1.159` (PostgreSQL 17.6) |
| Storage image | `public.ecr.aws/supabase/storage-api:v1.69.0` |
| Host/port | `127.0.0.1:55491` |
| Database | `postgres` (rebuild) → `ct_verify03_e2e` (E2E clone) |
| Evidence dir | `/tmp/ct_verify03_evidence` |
| Freshness proof | `PHASE A … fresh target public tables: 0` |

The E2E clone is named `ct_verify03_e2e` — it starts with `ct_` and contains no
protected marker, satisfying the F-046-1 discipline. The implementer's databases
(`ct_impl02_pg:55480`, `ct_impl02b_pg:55481`) were **not** used.

Command:

```bash
bash e2e/environment/scripts/canonical_schema_rebuild.sh \
  --prefix ct_verify03 --port 55491 --profile ct-implement-02 \
  --evidence /tmp/ct_verify03_evidence
```

## 7. 92-migration result — **VERIFIED**

```
PHASE B — migrations 1-26  → ALL_APPLIED applied=26 selected=26
PHASE C — D32 operator step → idempotent (4 policies, 1 bucket, unchanged on re-run)
PHASE D — migrations 27-92 → ALL_APPLIED applied=66 selected=66
ledger_rows_excluding_header=92  applied=92  failed=0  distinct_files=92
=== RESULT: ALL CHECKS PASSED (94 pass, 0 fail) ===
REBUILD VERIFIED   EXIT=0
```

* Expected count **92** — observed **92**.
* Deterministic ordering: filenames sort by 14-digit version prefix; versions
  unique; first `00000000000000_init_schema.sql`, last
  `20261023000000_ct02_scheduled_reporting.sql`.
* No migration skipped; no migration silently ignored (`failed=0`,
  `distinct_files=92`).
* **D32 platform prerequisites** satisfied before use: `storage.buckets`,
  `storage.objects`, `storage.foldername(text)`, `auth.uid()`, RLS on
  `storage.objects`, and `public.organization_members` present before PHASE C
  (`PHASE B complete … public.organization_members present`).
* **D32 operator ordering** correct: PHASE C (bucket + four provider-context
  policies) runs **after** migrations 1–26 and **before** migration 27, which is
  the migration that validates it.
* Final schema reproducible: the run's own inventory fingerprint matched the
  pinned value (see §9–§10), and the verifier recomputed it independently.

## 8. Migration fingerprint — **VERIFIED (recomputed independently)**

Recomputed by an independent script (own implementation of the documented
recipe: `sha256` of the `sha256sum` listing of sorted `*.sql`):

| Set | Files | Independently computed fingerprint | Recorded | Match |
|---|---|---|---|---|
| Extended canonical set | 92 | `36d5d85b93e6a6d0caba68037445fc43df4a87203b5931513bf07494e2437944` | `36d5d85b…` | ✅ |
| Baseline set (extended minus the 3 CT-IMPLEMENT-02 migrations) | 89 | `40b168b393fb2ca70ea40093bd4e9eecebf5c4604c752eea6a6f5a902c003c30` | `40b168b3…` | ✅ |
| CT-SCHEMA-01 historical anchor | — | recorded `d73e1e2b…` (historical, pre-D32-revision) | — | n/a |

The 89-file baseline fingerprint is **unchanged**, proving the CT-IMPLEMENT-02
migrations only *appended* and did not alter an earlier migration.

## 9. Schema inventory — **VERIFIED (recomputed independently)**

Counts recomputed by the verifier directly against the fresh target:

| Metric | Independently observed | CT-IMPLEMENT-02 claim | Match |
|---|---|---|---|
| public tables | 149 | 149 | ✅ |
| public tables with RLS | 149 | 149 | ✅ |
| public tables **without** RLS | 0 | 0 | ✅ |
| policies | 235 | 235 | ✅ |
| policies granting anon/public | 0 | 0 | ✅ |
| foreign keys | 182 | 182 | ✅ |
| indexes | 569 | 569 | ✅ |
| public functions | 37 | 37 | ✅ |
| triggers | 100 | 100 | ✅ |
| columns (all schemas) | 4,652 | 4,652 | ✅ |

Legacy absence and canonical presence (independently queried):

* `public.report_schedules` → **NULL (absent)**
* `public.report_history` → **NULL (absent)**
* `public.defra_conversion_factors` → **NULL (absent)**
* `public.notification_delivery_log` → **NULL (absent)**
* `report_schedule_definitions`, `report_schedule_runs`, `report_shares`,
  `report_share_access_events` → **present**

### 9.1 Verifier-integrity finding (self, recorded and corrected)

On the first pass the verifier's **own** index query
(`pg_indexes` excluding system schemas) returned **445**, not 569. Investigation
showed the recorded metric is defined as `count(*) from pg_indexes` **including**
`pg_catalog`/`information_schema`. Re-running with the correct definition
reproduced **569** exactly. This was a **definition mismatch in the verifier, not
a defect in the implementation**; both the original value and the correction are
recorded (per the verifier-integrity obligation).

## 10. Schema fingerprint — **VERIFIED (recomputed independently)**

The 12 documented inventory classes were re-executed by an independent script
with the pinned session `search_path` (`"$user", public, auth, extensions`) and
concatenated exactly as documented:

```
A_schemas    rows=  12   B_tables   rows= 379   C_columns rows=4652
D_constraints rows= 798  E_indexes  rows= 569   F_enums   rows=   1
G_functions  rows= 150   H_triggers rows= 100   I_views   rows=   3
K_sequences  rows=   1   L_rls      rows= 233   M_policies rows= 235
inventory_fingerprint = 5291cd9197bb7f0f84a99dec22c1b365633f4cd206cac5b787668cb4ee9c1407
```

Matches the pinned extended inventory fingerprint `5291cd91…` **byte-for-byte**.
(The extended fingerprint was originally *recorded* on the first run and has
been *enforced* on every later run — a shared-recipe determinism proof across two
independent environments, not a comparison of the implementation against
itself.)

## 11. D32 result

The D32 operator step ran, was **idempotent** (4 `storage.objects` policies → 4;
1 `documents` bucket, unchanged on re-run), and the behavioural semantics proof
passed: `D32_SEMANTICS_RESULT pass=11 fail=0`. The four approved
provider-context policies are the only `storage.objects` policies
(`d32_no_extra_storage_policies`).

## 12. search_path result — **VERIFIED**

The historical F-02 condition was reproduced independently with the untracked
`d32_search_path_regression.sh` against the fresh target: **13 passed, 0 failed**.

| Check | Result |
|---|---|
| Ambient `search_path` — `supabase_admin` | `"$user", public, auth, extensions` (includes `auth`) |
| Ambient `search_path` — `postgres` | `"$user", public, extensions` (no `auth`) |
| **R1** pre-revision validator as `supabase_admin` | **REJECTED** (`missing the approved org-scope fragment "auth.uid()"`) — the F-02 risk reproduced |
| **R2** pre-revision validator as `postgres` | passes — **role-dependent** |
| **R3–R5** revised validator under `supabase_admin`, forced `auth, public`, forced `pg_catalog` | **all pass** — search_path-independent |
| **R6a/R6b** look-alike `myauth.uid()` | accepted by the pre-revision validator; **REJECTED** by the revised validator (`does not call the approved session-identity function auth.uid()`) |
| **R7** missing org-scope fragment | **REJECTED** — drift still caught |
| **R8** target restored | 4 policies, 1 private bucket |
| **R9** final re-run of the revised migration | passes |

The `auth.uid()` predicate no longer resolves as an unqualified `uid()`, the
validation is not dependent on a developer-local `search_path`, and it remains
**fail-closed**. Validation was not weakened.

## 13. `report_schedules` dependency result — **NO ACTIVE RUNTIME DEPENDENCY**

Repository-wide enumeration (`grep -rIn report_schedules`, excluding VCS/caches)
and a targeted access-pattern scan
(`from_('report_schedules')`, `FROM/INTO/UPDATE/DELETE public.report_schedules`)
was performed across backend routes, services, data, workers, SQL, migrations,
frontend, tests and docs. Classification:

| Class | Locations |
|---|---|
| ACTIVE_RUNTIME | **none** |
| TEST_ONLY | `backend/tests/integration/test_ct03_report_schedule_share_canonical.py:294`; `backend/tests/unit/routes/test_ct03_legacy_canonical_delegation.py` (retired-table *access* regexes) |
| DOCUMENTATION_ONLY | `backend/data/report_schedules.py:5` (module-name/docstring); `backend/routes/reports.py:1196-1199` (comments); `backend/api/v3_reports.py:370-374` (comments); `API_ENDPOINTS.md:774` (still lists the legacy handler name — R-5 scope) |
| DEAD_LEGACY | none remaining |
| DDL guard (documentation-only) | `supabase/migrations/20261023000000_ct02_scheduled_reporting.sql:85` (`to_regclass('public.report_schedules')` fail-closed guard) |
| Verifier | `e2e/environment/scripts/canonical_schema_verify.py:154` (forbidden-legacy list) |

**`backend/routes/reports.py` contains no retired-table access and no
`report_history` mention at all** (only an import of the canonical
`services.report_schedules` module, comments, and the handler symbol
`get_report_schedules`). No module, route, worker or SQL path queries the retired
table. **Answer to the critical question: NO.**

## 14. Schedule E2E result — **VERIFIED**

Canonical E2E executed three times against the fresh clone `ct_verify03_e2e`:
**10 passed / 0 failed each run, EXIT=0**. Independently reproduced with real
HTTP + real PostgreSQL:

| Criterion | Evidence (real rows) |
|---|---|
| create | `report_schedule_definitions` row (201) |
| retrieve | list + detail (200) |
| update | pause/resume state changes |
| pause | `is_active=false`, `paused_at` set, `next_run_at` preserved |
| resume | `paused_at` cleared; due time recomputed when past |
| due selection | persisted `next_run_at <= now`, `is_active`, oldest-first |
| execution | `run_due()` executed the schedule (past `next_run_at` set directly in the table) |
| successful result | `report_schedule_runs.status='succeeded'`, `attempt=1`, `finished_at` set |
| failed result | unit-tested (fault injection not available) — **not** E2E |
| retry behaviour | unit-tested |
| retry exhaustion/pause | unit-tested |
| per-slot idempotency | repeated tick: `duplicate_slots == 1`; still exactly one run and one report |
| report creation | `report_generation_queue` row with `generated_content` |
| report-version creation | `report_versions` row, `report_id` matches, `is_current=true` |
| audit record | exactly one `audit_trail` row `action_type='report_schedule_run_succeeded'` for the schedule |
| correlation ID | `record_id = schedule id` |

All core persistence assertions are **row-level** (not status-code-only); no mock
is substituted for persistence.

## 15. Runner result — **VERIFIED**

`backend/domain/report_schedule.py` and
`backend/services/report_schedule_runner.py` exist and are wired; the runner
reads due schedules from the **persisted** `next_run_at`, claims the slot via the
UNIQUE `(schedule_id, scheduled_for)` key, records outcomes, and writes an audit
entry with `correlation_id = schedule id`. `backend/workers/report_schedules.py`
is started and stopped from `backend/main.py` (lifespan, lines 313-315, 450-452),
disabled by `CT_REPORT_SCHEDULES_ENABLED=0`. `backend/api/dependencies.py` and
`backend/data/report_schedules.py` bind the real repository/producer/audit sink.

## 16. Idempotency result — **VERIFIED**

A repeated tick on the same due slot cannot create a second run or report:
`duplicate_slots == 1`, exactly one `report_schedule_runs` row and one report for
the schedule under test. The duplicate path deliberately does not advance
`next_run_at`.

## 17. Report / version linkage result — **VERIFIED**

The run's `report_id` resolves to a `report_generation_queue` row with content
and its `report_version_id` resolves to a `report_versions` row whose
`report_id` equals the run's `report_id` and whose `is_current` is true.

## 18. Audit result — **VERIFIED**

Every run outcome is audited with `record_id` (correlation id) equal to the
schedule id. The canonical guard functions are attached to the evidence tables:
`audit_trail` → `ct02_audit_trail_no_truncate`; `audit_logs` /`activity_logs` →
`ct02_audit_logs_no_truncate` + `ct02_audit_logs_immutable` (and the
activity-log equivalents) — matching the migration's own trigger→function map.

## 19. Frequency result — **VERIFIED**

Canonical persisted vocabulary = **`weekly`, `monthly`, `quarterly`, `annual`**
(schema CHECK `report_schedule_definitions_frequency_check`).
The API advertises exactly these four, generated from the domain constants, on
**both** surfaces:

* `daily` is **not advertised**;
* `daily` (and every non-canonical value) is **rejected with 422** and **nothing
  is persisted** (`SELECT count(*) … WHERE organization_id = $1` → 0);
* rejection is clear and names the retired advertisement;
* `GET /api/v3/reports/schedules/frequencies` (canonical) and
  `GET /api/reports/schedule/frequencies` (legacy, `Deprecation` header) return
  the same list and delegate to the same canonical behaviour.

## 20. Legacy route result — **VERIFIED**

`backend/main.py` registers both `reports.router` (canonical
`/api/v3/reports`) and the legacy `legacy_reports.router` (`/api/reports`). The
legacy schedule surface (`POST/GET/DELETE /api/reports/schedule*`) and the legacy
share surface (`POST /api/reports/{id}/share`, `GET /api/reports/shared`) persist
to and read from the canonical tables; the legacy schedule surface returns the
canonical frequency list with a `Deprecation` header. End-to-end tests 9 and 10
confirm delegation and canonical persistence.

## 21. Sharing result — **VERIFIED (register only)**

Reproduced: share creation (201) writing a `report_shares` row bound to a
`report_versions` row; a `created` access event; a canonical audit entry;
register listing; access history; one-way revocation with the reason preserved
and a `revoked` event; a second revoke does not rewrite the first; sharing a
`DRAFT` version is refused (409) and persists nothing; a plain member cannot
share (403); the recipient-scoped `GET /shares/received` returns the share to its
recipient. The legacy `POST /{report_id}/share` and `GET /shared` delegate to the
canonical implementation.

## 22. G-2 result — **share consumption remains gated; no false claim**

The task's instruction was heeded: sharing is **not** marked implemented merely
because creation/revocation/history work. Share **consumption/delivery**
(returning report content to a recipient; recording `access`/`download`/`denied`)
is **not implemented** — no consumption/delivery route exists in the canonical
surface, and the implementation report states this explicitly (§18 limitations,
§21 Q13). The schema's event vocabulary exists but is unused. G-2 is genuinely a
product decision (they require a delivery/download policy), not a technical
defect.

## 23. G-3 result — **VERIFIED as a product decision**

Deleting a schedule that has executed returns **409** with a business message
("has execution history, which is immutable; pause it instead of deleting it")
and the row survives. The same cascade (`report_schedule_definitions` →
`report_schedule_runs`, `ON DELETE CASCADE`) plus the append-only run guard means
deleting the **owning organisation** also fails. The fresh clone retained the
rows the guards protect (`report_schedule_runs=6`, `report_shares=6`,
`report_share_access_events=9`, `audit_trail=66`) even after the suite's teardown
attempted removal — direct evidence that executed schedules cannot be silently
deleted and that history is protected. G-3 (organisation deletion vs immutable
history) is an **architecture/product decision**, not an application defect.

## 24. G-4 result — **VERIFIED (guard intact, not weakened)**

Attempting `TRUNCATE public.audit_trail` / `audit_logs` / `activity_logs`
directly on the fresh target is refused by `ct02_audit_truncate_guard()` with:
*"append-only ledger (CT-IMPLEMENT-02): TRUNCATE of <table> is not permitted (set
`ct.audit_purge_authorised=on` only from an authorised purge run)"*.

* The guard prevents the prohibited destructive operations and was **not**
  weakened; the GUC gate (`ct.audit_purge_authorised`) is the only escape and is
  **not** set anywhere in this change-set.
* The shared `backend/tests/integration/conftest.py` **pool** fixture (destructive
  `TRUNCATE … RESTART IDENTITY CASCADE`) is **unmodified by CT-IMPLEMENT-03**
  (`git diff --stat HEAD -- …/conftest.py` is empty), so its behaviour against a
  canonical database is unchanged — it still cannot start, which is exactly why
  the CT-IMPLEMENT-03 module defines its own non-destructive fixture. Production
  semantics are unaltered; the workaround is test-local and uses no guard
  exception.

## 25. N-3 result — **VERIFIED (deterministic across runs)**

The canonical E2E suite was run **three consecutive times on the same clone**:
`.......... EXIT=0` each time (10/10). The fix scopes artefact assertions to the
schedule under test (run rows and `DISTINCT report_id` for that schedule) and
pauses each schedule it creates so a leftover can never be due again; tick-level
counts are lower bounds. No test relies on leftovers from a previous test;
cleanup does not violate audit immutability; repeated runs are deterministic.

## 26. Legacy mismatch result

| Name | Classification | Evidence |
|---|---|---|
| `defra_conversion_factors` | **ACTIVE_RUNTIME references remain (stale legacy code) — REPLACED-BY-CANONICAL-STRUCTURE** | Live table absent from the canonical DB. Active code references persist in `backend/routes/reports.py:279,1290`, `backend/report_generator.py:595,621,764`, `backend/routes/emissions.py:153,199`, `backend/routes/organizations/{exports,dashboard,data}.py`, `backend/routes/admin/defra.py` (many). **Do not recreate the table** — superseded by the canonical `emission_factors` architecture (multi-source: DEFRA/SEAI/EU). This is the known R-1 gap, **outside** CT-IMPLEMENT-02/03 scope. |
| `report_history` | **DEAD_LEGACY / TEST_ONLY / DOCUMENTATION_ONLY** | Docstring at `backend/data/report_shares.py:7`; retired-table regexes in the delegation test; the migration's fail-closed guard; the verifier's forbidden list. No active access. Replaced by `report_shares` + `report_share_access_events`. |
| `report_schedules` | **DEAD_LEGACY (no active access) — replaced by canonical** | Reconciled with §4/§13. |
| `notification_delivery_log` | **ACTIVE_RUNTIME reference remains (stale legacy code)** | `backend/routes/admin/audit_logs.py:404` (`from_('notification_delivery_log')`) plus a Prisma model (`prisma/schema.prisma:1959`). Table absent from the canonical DB; outside CT-IMPLEMENT-02/03 scope. |

**Independent observation (material):** the retired-table elimination claimed by
CT-IMPLEMENT-02/03 is accurate **for `report_schedules` and `report_history`
only**. Two *other* legacy names still carry active runtime references to tables
absent from the canonical schema. These are explicitly out of the
CT-IMPLEMENT-02/03 remit (R-1) and are **not** regressions introduced by these
tasks, but they remain real active dependencies and should not be mistaken for
resolved by the canonicalization.

## 27. FIEW boundary

The CT-IMPLEMENT-02 statement remains accurate: **schema blockers removed;
runtime verification is separate.** This verification confirms *runtime*
behaviour only for the canonical schedule and share paths it exercised. The
"57 previously runtime-unverified capabilities" are **not** all verified here;
only the schedule/share canonicalization was runtime-verified by this independent
task. No feature was promoted merely because its schema object exists.

## 28. Production boundary

Production was **not** accessed for writes and was not touched:

* **no push** — the CT-IMPLEMENT-02/03 commits are local (confirmed: they appear
  in `origin/…..HEAD` and `github/…..HEAD`);
* **no deployment** — no Render/Vercel change; no deployment descriptor modified;
* **no production migration** — migrations applied only to the disposable
  `ct_verify03` container;
* **no production database/Auth/Storage** was contacted; no signed URL was
  generated or logged;
* the investor demo dataset and the local Supabase main database were untouched.

**Deployment-state observation:** production state was **not** compared to local
canonical state (out of scope, and no production credentials were used).
Whether production currently matches this canonical schema is **unknown** and
was deliberately not reconciled in this task.

## 29. Verifier-integrity findings

1. **Index-count definition mismatch (self, corrected).** The verifier's first
   index query returned 445 vs the recorded 569; investigation showed the
   recorded metric includes system schemas (`count(*) from pg_indexes`). Corrected
   and re-run → **569**. The original value and the correction are both recorded;
   the implementation is unaffected.
2. **No async predicate bug or typo-based false green found.** The E2E
   assertions are row-level and were re-executed three times; the canonical
   assertions read the database directly.
3. **No stale-HEAD assumption in the verifier.** The implemented provenance checks
   are *state-aware*: HEAD-minus-CT-IMPLEMENT-02 must reproduce a recorded
   baseline anchor, and the working-tree-vs-HEAD comparison uses
   `git status --porcelain` (which reports both tracked modifications and
   untracked additions). Independently confirmed: the only file differing from
   HEAD under `supabase/migrations` is the authorised D32 revision; the three
   CT-IMPLEMENT-02 migrations are already in HEAD.
4. **No untracked-file blindness in the migration-set check** (the F-6 fix is
   present and effective).
5. **Independence caveat (disclosed).** The extended *inventory* fingerprint was
   originally recorded from the same class of run it later enforces. It therefore
   proves **cross-environment reproducibility**, not independent correctness of
   the pinned value. It is not a comparison of the implementation against itself
   in a single run (my recomputation used a different host database), but the
   reader should treat it as a determinism proof, not an external ground truth.
6. **Implementation-agent artefacts were not treated as independent evidence** —
   all four implementation reports were treated as claims to be re-tested, and
   every headline claim in scope was reproduced on infrastructure the verifier
   created.

## 30. Exact tests and results

| # | Command | Result |
|---|---|---|
| 1 | `bash e2e/environment/scripts/canonical_schema_rebuild.sh --prefix ct_verify03 --port 55491 --profile ct-implement-02 --evidence /tmp/ct_verify03_evidence` | `ALL CHECKS PASSED (94 pass, 0 fail)`, `REBUILD VERIFIED`, **EXIT=0**; 92 applied / 0 failed |
| 2 | Independent fingerprint + inventory script (verifier-authored, `/tmp`) | ext fp `36d5d85b…`; baseline 89 fp `40b168b3…`; inventory fp `5291cd91…`; all counts match — **EXIT=0** |
| 3 | `bash e2e/environment/scripts/d32_search_path_regression.sh --port 55491 --password <disposable>` | `13 passed, 0 failed` — **EXIT=0** |
| 4 | `cd backend && INTEGRATION_DATABASE_URL=…ct_verify03_e2e python3 -m pytest tests/integration/test_ct03_report_schedule_share_canonical.py -q -p no:cacheprovider` (×3) | `10 passed` each run — **EXIT=0** |
| 5 | `cd backend && python3 -m pytest tests/unit/domain/test_report_schedule.py tests/unit/services/test_report_schedule_runner.py tests/unit/services/test_report_schedules_service.py tests/unit/services/test_report_schedule_producer.py tests/unit/services/test_report_shares_service.py tests/unit/routes/test_ct03_legacy_canonical_delegation.py` | **105 passed** — **EXIT=0** |
| 6 | `TRUNCATE public.audit_trail / audit_logs / activity_logs` on the fresh target | all three **refused** by `ct02_audit_truncate_guard()` (fail-closed) |
| 7 | Repository-wide `report_schedules` / `report_history` / `defra_conversion_factors` / `notification_delivery_log` audit | classification per §13 / §26 |
| 8 | `git rev-parse HEAD`, `git status --porcelain`, `git log origin/…..HEAD`, `git diff --stat HEAD -- …conftest.py` | HEAD `b313fc2…`; dirty worktree (pre-existing); 11 unpushed commits; `conftest.py` unmodified |

## 31. Limitations

1. **Harness reproducibility is worktree-scoped, not HEAD-scoped.** The canonical
   rebuild depends on files that are **uncommitted** at HEAD:
   `e2e/environment/scripts/apply_migrations.sh` (modified), the **symlink**
   `e2e/environment/supabase/migrations`, `supabase/config.toml`, `.gitignore`,
   and — critically — the untracked `d32_storage_operator.sql` (and
   `verify_d32_policy_semantics.sql`). A clean checkout of HEAD alone therefore
   **cannot** reproduce the 92-migration rebuild (PHASE C would fail for want of
   the operator script). The rebuild *is* reproducible on the current worktree,
   which is what this verification exercised. This is disclosed by
   CT-IMPLEMENT-02 §12.
2. **Share consumption/delivery is not implemented** (G-2) — verified only that
   creation/revocation/history/recipient-read work and that consumption is not
   falsely claimed.
3. **Runner failure/retry/backoff/pause and producer failure paths are
   unit-tested only** — not E2E-verified (no fault injection was added).
4. **Active legacy dependencies remain for `defra_conversion_factors` and
   `notification_delivery_log`** (§26) — outside CT-IMPLEMENT-02/03 scope (R-1).
5. **Production state is unknown/not reconciled** (§28).
6. **Extended inventory fingerprint is a determinism proof, not external ground
   truth** (§29.5).
7. The worktree is dirty with substantial pre-existing, unrelated changes; this
   verification did not clean or alter any of it, and results should be read as
   describing the worktree at HEAD `b313fc2`.

## 32. Final verdict

**`CT_VERIFY_03_INDEPENDENTLY_VERIFIED_PASS_WITH_LIMITATIONS`**

Independently verified on a brand-new disposable PostgreSQL 17.6 target:

* the canonical chain builds from zero with **92 migrations, 0 failures**, with
  deterministic order, correct **D32 platform prerequisites and ordering**, and
  an **independently recomputed** extended fingerprint (`36d5d85b…`), unchanged
  89-file baseline fingerprint (`40b168b3…`), inventory fingerprint
  (`5291cd91…`) and inventory counts (149/149/0 · 235 · 0 · 182 · 569 · 37 · 100
  · 4,652);
* the **D32/search_path** defect is fixed, fail-closed, and not weakened
  (13/13);
* **no active runtime code depends on `report_schedules`**;
* the **canonical schedule path** (create/read/pause/resume/due/execute/report/
  version/audit/correlation) and **per-slot idempotency** work end-to-end against
  real PostgreSQL (10/10 E2E × 3 runs; 105 unit tests);
* the **frequency contract** is canonical on both surfaces and `daily` is
  rejected with nothing persisted;
* **legacy routes delegate** to the canonical implementation;
* the **share register** (create/bind/revoke/history/received) works, with
  **consumption correctly gated by G-2** and not falsely claimed;
* **N-1/G-3** deletion refusal (409) and **N-2/G-4** audit guard hold, with the
  guard unweakened and the shared fixture unmodified;
* **N-3** isolation is deterministic across three consecutive runs.

The verdict is **not a clean PASS** because: the canonical rebuild is
reproducible only on the current (dirty) worktree, not from committed HEAD, since
several harness dependencies are uncommitted (§31.1); share consumption/delivery
and the runner's failure/retry paths remain unimplemented or unit-only; and two
*other* legacy names (`defra_conversion_factors`, `notification_delivery_log`)
still carry active runtime references to tables absent from the canonical schema
(§26, out of scope).

No repository code, migration, configuration, production system or Git history
was modified by this verification. The only artefact written is this report.

---

*Independent verification agent — CT-VERIFY-03. Nothing was fixed, pushed,
deployed, or reconciled.*
