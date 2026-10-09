# CT-CARBONTALLY-FOUNDATION-VERIFICATION-03

## Phase 3 — Targeted independent verification of three gating findings (B-06, B-01, B-04)

| Field | Value |
|---|---|
| Task | `CT-CARBONTALLY-FOUNDATION-VERIFICATION-03` (read-only, document-only) |
| Verifies | `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` (Phase 1, Cline) and `docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md` (Phase 2, Cline) |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (before and after) | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Databases inspected (read-only) | `carbontally_demo_local` (oid 517928), `ct_local_93d5cdd` (oid 424413) on the cluster at `127.0.0.1:54426` |
| Container inspected | `supabase_db_carbon_ledger` (PostgreSQL, `log_statement = ddl`) |
| Agent | CoStrict (independent verification) |
| Deliverable | this file (the only repository change) |
| Status | `VERIFICATION COMPLETE — BASELINE CORRECTED` (see §8) |

**Truth vocabulary.** `CONFIRMED` / `REFUTED` / `INCONCLUSIVE` describe whether *this* pass reproduced a
claim. `DIRECT` / `INFERRED` / `ANALOGOUS` label the strength of the evidence behind a statement. Nothing
in this document is an acceptance verdict (AGENTS.md §73). No Product Owner decision is taken here.

---

## 1. Executive summary

One line per task, with the single most important new fact.

| Task | Claim | Verdict | Most important new fact |
|---|---|---|---|
| **1** | **B-06** — the runtime DB contains objects created by migrations that exist in the working tree only as uncommitted files | **CONFIRMED** | **`ORIGIN = MANUAL_APPLICATION`**, established from the Postgres DDL log: at **2026-10-04 13:13:19 UTC** the *entire* `supabase/migrations/*.sql` chain was replayed against `carbontally_demo_local` by the repository's own Demo Lab provisioner (`tools/demo_lab/stack.py`, one `docker exec … psql` per file), which globs the working-tree migration directory and therefore applies untracked files. `manual_processing_processors` and `consultant_mp_allocations` were created in that pass; `consultant_mode_change_requests`/`consultant_relationship_requests` were created later (2026-10-06) by targeted manual application. |
| **2** | **B-01** — 2,537 collected under `backend/tests/unit` excluding `api`, exactly 7 failures | **CONFIRMED** | Counts, failure IDs and failure reasons reproduced **exactly**; additionally the pass/skip split **is** machine-readable (**2,522 passed, 8 skipped, 7 failed**) even though pytest 9.1.1 omits its final tally line. |
| **3** | **B-04** — `backend/.env` says `:8060` / `19999` while the stack runs `:8070` / `:54430` | **CONFIRMED** | Confirmed, and the environment source chain is now proven: the running process carries **exactly the six keys** of `~/ct_local_env/demo_lab/backend.env` and **none** of the repo `backend/.env` keys; `PORT` is absent from the process environment entirely (the port comes from the uvicorn command line, not from any env file). |

**Effect on PD-E.** PD-E asked whether to commit the five uncommitted migrations. Task 1 now answers the
question PD-E was blocked on: the runtime drift is **not** an unexplained anomaly, a lost commit, or a
different checkout. It is the **expected, reproducible behaviour of the project's own Demo Lab
provisioner**, which builds the lab schema from whatever `*.sql` files are present in the working tree.
PD-E is therefore a **commit-hygiene / release-baseline decision**, not a defect investigation — see §2.8.

---

## 2. Task 1 — Origin of the runtime-DB objects

### 2.1 Object presence and row counts (`DB:` — read-only)

Measured independently in `carbontally_demo_local`:

| Object | Kind | Present? | Rows (exact `count(*)`) | Cline's probe | Match |
|---|---|---|---|---|---|
| `consultant_mp_allocations` | table (`r`) | **yes** | **13** | 13 | ✅ |
| `manual_processing_processors` | table (`r`) | **yes** | **1** | 1 | ✅ |
| `consultant_mode_change_requests` | table (`r`) | **yes** | **2** | 2 | ✅ |
| `consultant_relationship_requests` | table (`r`) | **yes** | **0** | 0 | ✅ |
| `instrument_allocations` | table (`r`) | **yes** | **0** | (Phase 2: "runtime only") | ✅ |
| `insight_concurrency_leases` | table (`r`) | **yes** | **4** | (Phase 2: "runtime only") | ✅ |

**Cline's probe is accurate — this is not an artefact.** `ORIGIN = PROBE_ARTEFACT` is **REFUTED**.

Controls measured in the same pass (to prove the query path is sound):
`manual_processing_grants` 1, `consultant_clients` 8, `organizations` 14, `emission_factors` 7,049.

**Complete object set introduced by `20261030`–`20261104`.** Grepping the five files for object-creating
DDL yields exactly **four** tables and no views:

| Migration | Objects created |
|---|---|
| `20261030000000_manual_processing_routing.sql` | `manual_processing_processors` (+2 indexes) |
| `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | `consultant_mp_allocations` (+3 indexes) |
| `20261102000000_ct_consultant_model_02_capability_admission.sql` | *(none — `ALTER TABLE consultant_firm_members` + comments)* |
| `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | `consultant_relationship_requests`, `consultant_mode_change_requests` (+2 indexes; `ALTER` on `consultant_clients`, `consultant_profiles`, `system_settings`) |
| `20261104000000_ct_consultant_client_identity_04.sql` | *(none — `ALTER TABLE user_invitations` + 1 index)* |

All four tables are present. No other table or view in `carbontally_demo_local` has a `20261030`–`20261104`
migration as its only candidate creator.

> **Discrepancy D-1 (see §5).** `instrument_allocations` and `insight_concurrency_leases` are **not**
> orphaned objects: they are created by `20261011000000_p17c_contractual_instruments_and_allocations.sql`
> and `20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` respectively — both present in the
> working tree and both committed-era files.

### 2.2 Object age — relfilenode clustering (`DB:`)

`pg_class.relfilenode` is allocated monotonically, so ordering it reveals creation **order**.
All 154 public tables ordered by `relfilenode DESC` show four sharp clusters that map onto migration
generations:

| Batch | relfilenode range | Representative objects | Reading |
|---|---|---|---|
| base | 518,549 – 519,572 | `activity_categories`, `roles`, `units`, `organizations`, `users`, `organization_members`, `emission_factors`, `customer_subscriptions` | the release base schema |
| mid | 521,385 – 521,927 | `disclosure_*`, `evidence_line_items`, `manual_processing_grants`, `carbontally_insight_*`, `insight_concurrency_leases` | P8 / P16 / P17-era additions |
| P17/CT02 | 739,214 – 739,526 | `contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records`, `report_shares`, `report_schedule_definitions`, `backup_jobs` | P17 + CT02-era additions |
| **MP** | **742,524 – 742,545** | **`manual_processing_processors` (742,524), `consultant_mp_allocations` (742,545)** | **created together, immediately after the 739k batch** |
| **CT03** | **755,163 – 755,188** | **`consultant_relationship_requests` (755,163), `consultant_mode_change_requests` (755,188)** | **created together; the two highest relfilenodes in the entire schema — i.e. the most recently created tables** |

This is decisive: the four objects were **not** created in one batch. The MP pair precedes the CT03 pair,
and the CT03 pair is the newest object creation in the database — consistent with the migration
timestamps (`20261030`/`20261101` < `20261103`) and with two distinct application events.

Corroborating filesystem mtimes (`docker exec … ls -la /var/lib/postgresql/data/base/517928/`), noting
that a table *file* mtime is the last write, so it is an **upper bound** on creation:

| relfilenode | object | size | file mtime (UTC) |
|---|---|---|---|
| 742,524 | `manual_processing_processors` | 8,192 B | **2026-10-04 18:07** |
| 742,545 | `consultant_mp_allocations` | 8,192 B | **2026-10-05 02:07** |
| 755,163 | `consultant_relationship_requests` | 0 B | **2026-10-06 11:49** |
| 755,188 | `consultant_mode_change_requests` | 8,192 B | **2026-10-06 12:31** |

`consultant_relationship_requests` is 0 bytes and has never been written — so for that object the mtime
**is** its creation time: **2026-10-06 11:49 UTC**.

### 2.3 Object age — `pg_stat_user_tables` (`DB:` — uninformative, reported as such)

`last_vacuum`, `last_autovacuum`, `last_analyze`, `last_autoanalyze` are **NULL** and
`n_live_tup` = `n_tup_ins` = `n_tup_upd` = **0** for *every* object probed — including
`consultant_clients` (8 rows), `organizations` (14 rows) and `emission_factors` (7,049 rows).
`pg_stat_database.stats_reset` is also **NULL**.

**Conclusion:** the statistics collector holds no usable history for this database (never vacuumed or
analysed, and no `stats_reset` recorded). The vacuum-history method requested in the task brief is
therefore **unavailable** here, and the age evidence rests on relfilenodes + file mtimes + the DDL log
instead. This is reported as a method limitation, **not** as a contradiction of Cline.

`pg_stat_file()` was attempted and **denied**: `ERROR: permission denied for function pg_stat_file`.
`pg_relation_filenode()` was available and used (`relfilenode` == `pg_relation_filenode(oid)` for all six).

### 2.4 Non-migration appliers in the repository (`CODE:`) — **found**

Two distinct appliers exist, both intended, both repo-owned:

**(a) The Demo Lab provisioner — `tools/demo_lab/stack.py`.** This is the primary mechanism:

```python
# tools/demo_lab/stack.py
def psql_stdin(sql_text: str, *, timeout: int = 900):
    """Run SQL through stdin (used for migrations and schema dumps)."""
    return lab.run(
        ["docker", "exec", "-i", lab.STACK_DB_CONTAINER, "psql", "-v", "ON_ERROR_STOP=0",
         "-q", "-U", lab.STACK_DB_USER, "-d", lab.LAB_DB],
        stdin_text=sql_text, timeout=timeout)
...
files = sorted(lab.MIGRATIONS_DIR.glob("*.sql"))      # globs the WORKING TREE
summary["migration_files"] = len(files)

def _apply(paths: list, phase: str) -> None:
    for path in paths:
        result = psql_stdin(path.read_text())          # one psql invocation PER FILE
```

Three properties matter, and all three are load-bearing for B-06:

1. `MIGRATIONS_DIR.glob("*.sql")` reads `supabase/migrations/` **from the working tree** — it has no
   concept of commits, and **no migration-tracking/ledger table** (confirming Phase 1 §8.2). Untracked
   migration files are applied exactly like tracked ones.
2. `_apply()` issues **one `docker exec psql` per file**, so a full chain replay produces one backend
   PID per migration file.
3. `ON_ERROR_STOP=0` plus explicit tolerance of `"already exists"` / `"must be owner"` — i.e. the chain is
   **idempotent by replay**, not by ledger.

Module docstring, verbatim: *"builds the **release schema** in it from `supabase/migrations/*.sql` (the
authoritative source)"*.

**(b) Targeted per-file re-application.** `docs/architecture/CT-CONSULTANT-CLIENT-ACCESS-UX-01.md:196–207`
documents the exact command used when the lab DB was found to predate a migration:

> `docker exec -i supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -v ON_ERROR_STOP=1 < supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`

and states the cause plainly: *"the lab rebuilds from `supabase/migrations/*.sql` with no tracking table,
so the fix was to (re)apply the additive, idempotent CT-04 migration to the disposable lab DB."*

`docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-03.md:14` likewise records the `20261103` migration
as **"APPLIED to the local Demo Lab database"** (§8: *"additive, idempotent, applied cleanly to the local
Demo Lab database (`carbontally_demo_local`) and verified there"*).

Explicitly **not** an applier: `tools/demo_lab/fixture_mp_coverage.py:38` — *"it does not apply any
migration"*; its `precondition()` is fail-closed and *names* the missing migration instead of applying it
(the PD-6 gate).

### 2.5 Direct DDL-log evidence (`RUN:` — decisive)

The container runs with `log_statement = ddl`, so every DDL statement executed is logged **with its
timestamp, backend PID and database name**. Extracting the window `2026-10-04T13:12:00`–`13:25:00`:

**The trigger event — the object did not exist beforehand:**

```
2026-10-04T08:10:32Z  [604334] postgres@carbontally_demo_local ERROR: relation "public.manual_processing_processors" does not exist at character 16
2026-10-04T08:10:32Z  [604334] postgres@carbontally_demo_local STATEMENT: SELECT id FROM public.manual_processing_processors LIMIT 1;
```

**The creation event:**

```
2026-10-04T13:13:19.828Z  [645510] postgres@carbontally_demo_local LOG: statement: CREATE TABLE IF NOT EXISTS public.manual_processing_processors (
2026-10-04T13:13:19.836Z  [645510] postgres@carbontally_demo_local LOG: statement: ALTER TABLE public.manual_processing_processors ENABLE ROW LEVEL SECURITY;
2026-10-04T13:13:19.901Z  [645518] postgres@carbontally_demo_local LOG: statement: CREATE TABLE IF NOT EXISTS public.consultant_mp_allocations (
2026-10-04T13:13:19.908Z  [645518] postgres@carbontally_demo_local LOG: statement: ALTER TABLE public.consultant_mp_allocations ENABLE ROW LEVEL SECURITY;
```

**And the signature of a whole-chain replay in the same window:**

- **1,672** statements against `postgres@carbontally_demo_local`;
- **dozens of distinct backend PIDs** (`644571, 644578, 644585, 644677 …`, ascending, one per migration
  file) — matching `stack.py`'s one-`psql`-per-file loop;
- the window begins with the **base schema** being re-created statement by statement
  (`CREATE TABLE public.activity_categories`, `…document_types`, `…roles`, `…units`, `…organizations`,
  `…users`, `…organization_members`) — i.e. a full replay starting from
  `00000000000000_init_schema.sql`;
- **97** `ERROR: … already exists` lines (e.g. `relation "activity_categories" already exists`), tolerated
  under `ON_ERROR_STOP=0`.

That combination — full chain from init, one PID per file, `already exists` tolerated, untracked files
applied — is `tools/demo_lab/stack.py::ensure_database()` reproducing byte-for-byte.

### 2.6 Git history — no commit-then-revert, no stash, no second checkout (`GIT:`)

| Check | Command | Result |
|---|---|---|
| Any commit containing `20261030000000_…` | `git log --all --oneline -- supabase/migrations/20261030000000_manual_processing_routing.sql` | **empty** |
| Any commit containing the other four | `git log --all --oneline -- 'supabase/migrations/2026110*'` | **empty** |
| Deletion commits in the migration dir | `git log --all --diff-filter=D --oneline -- supabase/migrations/` | 2 commits: `d3af816`, `dbe72aa` (*"checkpoint: verified V2.1 and V3 database foundation"*) — an older workstream; the five paths appear in **no** commit, so no revert of them exists |
| Stashes | `git stash list` | **empty** |
| Worktrees | `git worktree list` / `ls .git/worktrees/` | one worktree (`/home/shomonrobie/ct_93d5cdd 3fec874 [p8-release-reconciled]`); `.git/worktrees/` **does not exist** |
| Branches | `git branch -vv` | exactly one local branch, `p8-release-reconciled` @ `3fec874` (ahead 230 of `origin/…`) |
| Tags | `git tag` | `rc2-final`, `v2.1-phase4`, `v2.1.1-phase3` — none relevant |
| Other refs | `git for-each-ref` | only `refs/cline/checkpoints/<id>/<n>` (Cline's own session checkpoints) + remotes |
| Reflog | `git reflog --all` (first 100) | normal linear history: `3fec874` → `375a48d` → `cabdca8` → … Only amends of `docs(CT-FINAL-01)` reports. **No revert of a migration commit.** |

**`ORIGIN = COMMITTED_THEN_REVERTED` — REFUTED.**
**`ORIGIN = DIFFERENT_CHECKOUT` — REFUTED** (single worktree, single branch, HEAD == the baseline's HEAD).
**`ORIGIN = UNAPPLIED_LEDGER_STATE` — REFUTED** (migration files for the objects *do* exist; they are
merely untracked).

Application logs (a further independent corroboration of "applied from the working tree"):
`docs/architecture/CT-MP-SUB-004-PD5-FIXTURE-01-report.md` §4.1 and §5.5 map each table back to its
migration file, and `docs/architecture/CT-COMMERCIAL-SUBSCRIPTION-INDEPENDENT-ASSESSMENT-01.md:1428`
lists *"Apply the authored migrations `20261010000000` …, `20261030000000` …, `20261101000000` …"* as a
follow-up action — i.e. these files were knowingly applied out-of-band.

### 2.7 Postgres log accessibility and its **evidence gap** (reported, not hidden)

The log **is** accessible without privilege escalation (`docker logs supabase_db_carbon_ledger`), and
`log_statement = ddl` means DDL is recorded. **However:**

| Property | Value |
|---|---|
| Earliest retained log entry | `2026-09-01T11:41:52Z` |
| **Latest retained log entry** | **`2026-10-05T15:06:20Z`** |
| Total retained lines | 1,530,800 |
| Container `StartedAt` / `FinishedAt` | `2026-10-07T08:27:25Z` / `2026-10-07T08:27:17Z` (restarted) |
| `pg_postmaster_start_time()` | `2026-10-07 08:27:31.931838+00` |
| Log driver | `json-file`, no rotation config (`Config: map[]`) |

**The DDL log therefore stops on 2026-10-05 15:06 UTC and covers *none* of 2026-10-06.** Grepping the
entire retained log for `consultant_mode_change_requests`, `consultant_relationship_requests` and
`client_access_profile` returns **zero** matches — not because those objects were not created by DDL, but
because the window in which they were created is not retained.

**Consequence:** the 2026-10-04 application of `20261030`/`20261101` is proven **directly** from the log.
The 2026-10-06 application of `20261103` is established by **convergent indirect evidence** (relfilenode
being the newest in the schema, a 0-byte never-written table file mtime-stamped `2026-10-06 11:49`, and
the implementation report dated the same day asserting the migration was applied) — **not** by a log
entry. This distinction is stated rather than papered over.

### 2.8 Conclusion and consequences for PD-E

> ## `ORIGIN = MANUAL_APPLICATION`
>
> **Applier identified:** `tools/demo_lab/stack.py::ensure_database()` (invoked via the Demo Lab stack),
> which globs `supabase/migrations/*.sql` **from the working tree** and pipes each file through
> `docker exec -i supabase_db_carbon_ledger psql -v ON_ERROR_STOP=0 -q -U postgres -d carbontally_demo_local`.
> A full-chain replay ran at **2026-10-04 13:13 UTC**, creating `manual_processing_processors` and
> `consultant_mp_allocations`. `consultant_mode_change_requests` / `consultant_relationship_requests` were
> created on **2026-10-06** by the targeted manual re-application documented in
> `CT-CONSULTANT-MODEL-IMPLEMENTATION-03.md` §8 and `CT-CONSULTANT-CLIENT-ACCESS-UX-01.md` §11.

**What this means for PD-E (whether to commit the five migrations).**

1. **The drift is explained, benign and reproducible — it is not lost work.** The objects exist because
   the project's own provisioning tool applies everything in the migrations directory, tracked or not.
   No commit was lost; no revert occurred; no foreign checkout was involved.
2. **The runtime DB cannot be used as evidence of "what is released".** Because `stack.py` globs the
   working tree and there is no ledger in either database, `carbontally_demo_local`'s schema is a function
   of *which files happened to be on disk at build time*, not of Git state. Any future statement of the
   form "the runtime DB proves X shipped" is unsound while this remains true.
3. **PD-E is therefore reframed as a release-baseline question, not a forensic one:**
   *commit* — the five files become the release baseline, the migration-order tests can be re-pinned
   against a committed chain, and the lab DB becomes explainable from Git; or
   *hold* — the untracked set must be treated as a first-class, documented input to the lab provisioner,
   and no "runtime == released" claim may be made.
4. **PD-E does not require a Wave 1 code fix.** There is no defect to repair: `stack.py` did what its
   docstring says, and the two 2026-10-06 applications were deliberate and documented. The finding is a
   **process/governance** item.

---

## 3. Task 2 — Unit test baseline

### 3.1 Reproduced counts (exact)

`cd /home/shomonrobie/ct_93d5cdd/backend && .venv/bin/python -m pytest <scope> -q --tb=no`

| # | Scope | Collected | Passed | Failed | Skipped | Files |
|---|---|---:|---:|---:|---:|---:|
| 1 | `tests/unit --ignore=tests/unit/api` | **2,537** | **2,522** | **7** | **8** | 133 |
| 2 | `tests/unit/engines` | **389** | **386** | **3** | 0 | 20 |
| 3 | the four migration-pin files | **80** | 76 | **4** | 0 | 4 |
| 4 | `tests/unit/api --collect-only` | **2,788** | *not run* | — | — | 144 |

Every number matches Cline's: **2,537** (Phase 1 §13.1 run 1), **389** (run 2), **4 failures** (run 3),
**2,788** (run 4). ✅

### 3.2 The 7 failures — exact IDs and exact reasons

| # | Test ID | Observed assertion (verbatim from `--tb=short`) |
|---|---|---|
| 1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `AssertionError: assert 103 == 71` — `+ where 103 = len(['00000000000000_init_schema.sql', '20260800000000_rc2_schema.sql', …])` |
| 2 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | `assert '20261104000000_ct_consultant_client_identity_04.sql' == '20261007000000_p8_insight_data_quality_reproducibility.sql'` |
| 3 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | `AssertionError: ['20261102000000_ct_consultant_model_02_capability_admission.sql', '20261103000000_ct_consultant_model_03_client_access_and_mode.sql', '20261104000000_ct_consultant_client_identity_04.sql']` (`assert later in (…)`) |
| 4 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | `AssertionError: unexpected migration after the P16 baseline: 20261029000000_ct_final_03_staff_workload_rls.sql` |
| 5 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | `AssertionError: assert '2026-01-15' == '15/01/2026'` (line 30) |
| 6 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | `assert {'extraction_evidence': {'supplier_header': {'candidates': [], 'reason': 'no candidate line', 'strategy': 'header_block'}}} == {}` (line 54) |
| 7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | same shape as #6 (line 81) |

**All 7 reproduce, and all 7 match Cline's reported IDs and causes exactly** — 4 migration-order pins
(Group A) and 3 extraction-suggestion expectation drifts (Group B).
`ORIGIN = PROBE_ARTEFACT`-style doubt does not apply: the failure set is exact and stable across runs.

### 3.3 Is the final `N failed, M passed` line still missing? — **CONFIRMED still missing**

A single-file run (`pytest tests/unit/data/test_i1_insight_migration.py -q --tb=no`) terminates with:

```
F........                                                                [100%]
=========================== short test summary info ============================
FAILED tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
```

…and **no tally line**. `--collect-only -q` likewise omits `N tests collected`, emitting per-file counts
(`tests/unit/engines/test_workflow.py: 21`) and then the docs link. `pytest --version` → **`pytest 9.1.1`**.
Cline's observation is confirmed for **both** run mode and collection mode.

### 3.4 New fact — the counts **are** extractable anyway

Although the tally line is absent, the per-test progress characters are emitted and can be counted
directly, giving an exact pass/skip split without `-p` plugins or XML artefacts:

```bash
.venv/bin/python -m pytest tests/unit --ignore=tests/unit/api -q --tb=no 2>&1 \
  | grep -aE '\[[ 0-9]+%\]' | sed -E 's/\[[ 0-9]+%\]//' | tr -d ' \n' | fold -w1 | sort | uniq -c
#   2522 .
#      7 F
#      8 s
```

`2,522 + 7 + 8 = 2,537` ✅ (engines: `386 + 3 = 389` ✅, 0 skips).

So the baseline's position — *"the passed count is deliberately not asserted where it is not
machine-readable"* — was **over-cautious**: the passed count **is** derivable, and the baseline's §13.1
understated the available evidence. No number in the baseline is wrong; it is simply incomplete.

### 3.5 Task 2 conclusion

**CONFIRMED — 7 failures / 2,537 collected, IDs and causes exactly as reported, baseline still RED.**
The only refinement is that 8 skips and 2,522 passes are now quantified, and the failing migration-pin
tests are demonstrably a *direct consequence of the Task 1 mechanism*: the pins count the working-tree
migration directory, and the working tree contains files the repository never committed.

---

## 4. Task 3 — Environment drift

### 4.1 `backend/.env` (repo, git-ignored) — key **names** only, secrets masked

Key names present: `BROWSER DATABASE_URL ENVIRONMENT FOUNDER_EMAIL PORT REACT_APP_API_URL`(×2)
`RESEND_API_KEY SMTP_HOST SMTP_PASSWORD SMTP_PORT SMTP_USERNAME SMTP_USE_TLS_SSL SUPABASE_ACCESS_TOKEN
SUPABASE_ANON_KEY SUPABASE_JWT_SECRET SUPABASE_LIVE_POSTGRES_DATABASE_URL SUPABASE_LIVE_SERVICE_KEY
SUPABASE_LIVE_URL SUPABASE_SERVICE_KEY SUPABASE_URL`

Non-secret endpoint values:

| Key | Value |
|---|---|
| `PORT` | **`8060`** |
| `SUPABASE_URL` | **`http://127.0.0.1:19999`** |
| `DATABASE_URL` | `postgresql://postgres:<redacted>@127.0.0.1:54426/ct_local_93d5cdd` |
| `REACT_APP_API_URL` (line 5) | `http://localhost:8060` |
| `REACT_APP_API_URL` (line 20) | `http://localhost:8000` |
| `SMTP_HOST` / `SMTP_PORT` | `mail.carbontally.co.uk` / `465` |
| `SUPABASE_LIVE_URL` | `https://pvwiojoyaqywtydzcpbg.supabase.co` |
| `SUPABASE_LIVE_POSTGRES_DATABASE_URL` | `<redacted — contains an inline credential>` |

✅ Baseline §5.3's `PORT=8060` and `SUPABASE_URL=http://127.0.0.1:19999` are reproduced exactly.

### 4.2 The running backend — actual environment (`RUN:`)

`ss -ltnp` → `127.0.0.1:8070 … users:(("uvicorn",pid=1014820,fd=10))`.

`ps eww -p 1014820`, selected keys:

| Key | Actual value in the running process |
|---|---|
| `SUPABASE_URL` | **`http://127.0.0.1:54430`** |
| `DATABASE_URL` | `postgresql://postgres:<redacted>@127.0.0.1:54426/carbontally_demo_local` |
| `PORT` | **absent** |

✅ Baseline §5.3's `:8070` / `http://127.0.0.1:54430` / `carbontally_demo_local` are reproduced exactly.

### 4.3 Port liveness (`RUN:`)

| Port | Expected by | Listening? |
|---|---|---|
| `19999` | `backend/.env` `SUPABASE_URL` | **NO** — nothing listening |
| `8060` | `backend/.env` `PORT` | **NO** — nothing listening |
| `8070` | running uvicorn (pid 1014820) | **YES** (`LISTEN 127.0.0.1:8070`) |
| `54430` | lab gateway (runtime `SUPABASE_URL`) | **YES** (`LISTEN 127.0.0.1:54430`) |
| `54426` | Postgres cluster | **YES** (`LISTEN 0.0.0.0:54426`, `[::]:54426`) |
| `3000` | React dev server | **YES** (`LISTEN 0.0.0.0:3000`) |

✅ Baseline §5.1/§5.2/§5.3 reproduced exactly.

### 4.4 Is `~/ct_local_env/demo_lab/backend.env` the running environment source? — **YES, proven**

| File | Keys declared |
|---|---|
| `~/ct_local_env/demo_lab/backend.env` | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `TESSERACT_CMD` (**6**) |
| Running uvicorn process | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `TESSERACT_CMD` (**the same 6**) |

Presence checks on the live process (`ps eww`, names only): `TESSERACT_CMD` **PRESENT**;
`PORT` **absent**; `RESEND_API_KEY` **absent**; `FOUNDER_EMAIL` **absent**; `BROWSER` **absent**;
`ENVIRONMENT` **absent**; `REACT_APP_API_URL` **absent**.

`~/ct_local_env/demo_lab/backend.env` values: `SUPABASE_URL=http://127.0.0.1:54430`,
`DATABASE_URL=postgresql://postgres:<redacted>@127.0.0.1:54426/carbontally_demo_local`.

**The key sets are identical and disjoint from the repo `backend/.env` key set** (which declares
`RESEND_API_KEY`, `FOUNDER_EMAIL`, `BROWSER`, `ENVIRONMENT`, `PORT`, `SUPABASE_LIVE_*`, `SMTP_*` — **none**
of which appear in the process). This is a stronger result than a value match: it excludes the
possibility that the repo `.env` is also loaded. `TESSERACT_CMD` — the OCR dependency AGENTS.md §20
requires and that the repo `.env` lacks — comes from this file, confirming baseline §5.3's reading.

Supervisor state (`~/ct_local_env/demo_lab/supervisor.status.json`): backend pid **1014820**, `running: true`,
`restarts: 0`, url `http://127.0.0.1:8070/health`; frontend pid **1014827** — matching baseline §5.1.

**Why `8060` is not the runtime port, stated precisely:** `PORT` is not in the environment at all, so
`backend/.env`'s `PORT=8060` is inert for this process; the port is supplied on the uvicorn command line
by the supervisor.

### 4.5 Task 3 conclusion

**CONFIRMED.** `backend/.env` (`PORT=8060`, `SUPABASE_URL=http://127.0.0.1:19999`) does not describe the
running stack (`:8070`, `http://127.0.0.1:54430`); neither `8060` nor `19999` is bound by any process; and
`~/ct_local_env/demo_lab/backend.env` is the running environment source, now demonstrated by exact key-set
identity rather than by value similarity.

---

## 5. Discrepancies from the baseline

Numbered. Each is something Cline reported that did not reproduce as stated, or a material fact the
baseline omitted.

**D-1 — REFUTED: "objects with no corresponding migration in this checkout" includes two objects that
plainly have one.** Phase 2 §11.3 and §5.5 list `instrument_allocations` and `insight_concurrency_leases`
(alongside `consultant_mode_change_requests`, `consultant_relationship_requests`, `consultant_mp_allocations`)
as *"Objects without a corresponding migration in this checkout"*. Both are created by ordinary migrations
present in the working tree:

- `instrument_allocations` ← `supabase/migrations/20261011000000_p17c_contractual_instruments_and_allocations.sql`
- `insight_concurrency_leases` ← `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql`

Only the three `consultant_*` objects and `manual_processing_processors` genuinely lacked a *committed*
migration. The Phase 2 list is 5 entries long and 2 of them are wrong, which materially overstates the
drift. (Phase 2 §11.4 phrased the same point as an open question — *"whether the runtime database's extra
objects were introduced by uncommitted migrations, manual DDL, or a different seed path"* — and that
question is answered in §2 above.)

**D-2 — INCOMPLETE: the pass/skip split was declared unobtainable when it is obtainable.** Baseline §2.4,
§13.1 and §15.1 state the passed count is not machine-readable in this environment. The tally line is
indeed absent (`CONFIRMED`), but counting progress characters yields exactly **2,522 passed / 8 skipped /
7 failed** for the non-API scope. The baseline's caution was unnecessary, not wrong.

**D-3 — OMITTED: `backend/.env` declares `REACT_APP_API_URL` twice with conflicting values.**
Line 5 → `http://localhost:8060`; line 20 → `http://localhost:8000`. Baseline §4.3 and §5.3 report the file
without noting the duplicate. Last-wins semantics mean `8000` is effective — a third, different port
alongside the `8060` and `8070` already in play.

**D-4 — OMITTED: `backend/.env` holds a plaintext credential.**
`SUPABASE_LIVE_POSTGRES_DATABASE_URL` embeds an inline database password for the production-shaped
Supabase pooler host. Baseline §4.3 says *"key names inspected only"* and §12.5 says *"no credential …
was read, printed or recorded"* — the second statement is stronger than the method supports, because the
file does contain an inline credential. No secret value is reproduced anywhere in this report.

**D-5 — UNSTATED: the running process has no `PORT` variable.** Baseline §5.3 tabulates the running
process as "API port **8070**", which reads as an environment value. It is not: `PORT` is **absent** from
the process environment, and `8060` is inert rather than overridden. The distinction matters for anyone
later trying to "fix" the drift by editing an env file.

**D-6 — INCOMPLETE: Phase 1 §13.1 run 3 records no collected count.** The four-file migration scope
collects **80** tests (76 pass, 4 fail), measured here.

**D-7 — OMITTED (method): the DDL log is truncated.** Phase 1 §8 and Phase 2 §11.4 correctly left the
origin open but did not note that `docker logs supabase_db_carbon_ledger` — the one artefact that could
have answered the question — retains nothing after `2026-10-05T15:06:20Z`, despite the container having
restarted on `2026-10-07`. Anyone repeating this investigation should know the window's upper bound
before spending time on it. The 2026-10-04 events are inside the window; the 2026-10-06 events are not.

**D-8 — not a discrepancy, recorded for completeness.** Two baseline observations were re-confirmed
incidentally: Phase 1's `pg_stat_user_tables`-class evidence does not exist in this database at all
(all counters zero, all timestamps NULL, `stats_reset` NULL); and `pg_stat_file()` is not available to
the connection role (`permission denied`). Neither was relied on by the baseline, so nothing in it is
undermined — but the task's proposed age method is unavailable here.

---

## 6. Corrections required to the baseline

*Listed only. The baseline documents were not edited.*

| Finding / location | Current status in baseline | Should become | Why |
|---|---|---|---|
| **B-06** (Phase 1 §14.3) | `P2`, class `F` — "runtime DB has been provisioned from them … how those objects came to exist" unexplained | **Explanation established → reclassify.** Recommend retaining as a finding but moving to `P3` with cause `KNOWN — Demo Lab working-tree provisioning`, and rewording from "drift" to "expected provisioning behaviour with no ledger" | `ORIGIN = MANUAL_APPLICATION`, proven from the DDL log (§2.5). This is not a defect; it is `tools/demo_lab/stack.py` behaving as documented |
| **B-06** — consequence text (§14.3, §15.2 PD-E) | "PD-E: … The red migration-order tests cannot be resolved while the intent is unresolved" | **PD-E reframed** as a commit-hygiene release-baseline decision; explicitly *not* a Wave 1 code fix (§2.8) | The question PD-E was gating on — how the DB drifted — is now answered |
| **B-01** (Phase 1 §13.1/§13.3) | `P1`, `RED`, 7 failures / 2,537 collected, passed count not asserted | **Uphold as `P1`/`RED`; add the pass/skip split** (2,522 passed, 8 skipped, 7 failed) | All counts and all 7 failure IDs/reasons reproduced exactly; the split is obtainable (§3.4) |
| **B-04** (Phase 1 §14.3) | `P2`, class `F` — runtime config drift | **Uphold as `P2`/`CONFIRMED`; add two sub-facts**: (i) `PORT` is absent from the process env, so `8060` is inert, not overridden; (ii) `backend/.env` is not loaded at all — the running env is exactly the 6-key `~/ct_local_env/demo_lab/backend.env` | §4.2/§4.4 |
| **Phase 1 §2.4 / §13.1 / §15.1** (method statement, not a B-ID) | "the passed count is deliberately not asserted where it is not machine-readable" | **Correct to**: the tally line is not emitted (config `CONFIRMED`), but the passed/skipped counts **are** extractable from progress characters | §3.4 — discrepancy D-2 |
| **Phase 2 §11.3 / §5.5** (inventory claim, not a B-ID) | `instrument_allocations`, `insight_concurrency_leases` listed as "Objects without a corresponding migration in this checkout" | **Remove those two from the list.** Correct list: `manual_processing_processors`, `consultant_mp_allocations`, `consultant_relationship_requests`, `consultant_mode_change_requests` | §2.1 — discrepancy D-1 |
| **Phase 1 §4.3 / §12.5** (secret hygiene) | "key **names** inspected only"; "no credential … was read, printed or recorded" | **Soften the second claim**: `backend/.env` **does** contain an inline credential in `SUPABASE_LIVE_POSTGRES_DATABASE_URL`; it was not printed or reproduced, but the file must not be treated as credential-free | §4.1 — discrepancy D-4 |
| **B-02, B-03, B-05, B-07…B-15** | unchanged | **No change** — out of scope for this pass and not contradicted by any evidence gathered here | — |

---

## 7. Read-only attestation

### 7.1 Git state — before and after

| Command | Before verification | After verification | Delta |
|---|---|---|---|
| `git rev-parse HEAD` | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` | **none** |
| `git branch --show-current` | `p8-release-reconciled` | `p8-release-reconciled` | none |
| `git status --porcelain` counts | `78 M`, `193 ??` | `78 M`, `193 ??` | **none** |
| `git diff --stat` totals | `78 files changed, 7440 insertions(+), 928 deletions(-)` | `78 files changed, 7440 insertions(+), 928 deletions(-)` | **none** |
| `git diff --cached --name-only` | 0 paths (nothing staged) | 0 paths | none |
| New path created | — | `docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md` | **+1 untracked file** |

The counts `78 M` / `193 ??` match the task brief's stated pre-existing dirty state and Phase 2 §12.2's
final capture. The single untracked addition is this report; writing it raises `??` from 193 to 194 as the
final act of this task.

### 7.2 Safety confirmation

| Control | Confirmation |
|---|---|
| Files modified | **None.** One new untracked document created (`docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md`). No tracked file touched; nothing staged; no commit, push, or amend |
| Git history operations | **None.** No `reset`, `clean`, `checkout`, `restore`, `stash` (list only), `rebase`, `commit` or `amend`. Reflog, worktree list, branch/reference/tag listings were read-only inspections |
| Database writes | **None.** Every statement was a `SELECT`, a `count(*)`, a `pg_class`/`pg_namespace`/`pg_stat_*` catalogue read, or a `SHOW`. No `INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`ALTER`/`DROP`/`CREATE`/`GRANT`/`REVOKE` was issued by this session |
| Migrations | **None applied.** Task 1 asked about *already-applied* state only |
| Seeds / truncates / drops | **None** |
| Services started/stopped/restarted | **None.** `docker exec`, `docker logs`, `docker inspect` and `ss`/`ps` are read-only inspections of already-running components. No container, worker, harness or browser was started or stopped |
| Runtime suites | The unit suite was executed in **run mode** as the task explicitly required (Task 2); `tests/unit/api` was executed with `--collect-only` only. **Integration, e2e, frontend and API-unit suites were never run in execute mode** |
| Database targets touched | `carbontally_demo_local` (read queries) and `ct_local_93d5cdd` (read only from `pg_database`). The ~71 disposable `ct_*` clones were **not** touched |
| Production | **Not contacted.** No outbound request to any non-localhost address. `SUPABASE_LIVE_*` values in `backend/.env` were read as text and **never dialled** |
| Investor demo data | **Not mutated.** `carbontally_demo_local` was read only |
| Secrets | No secret value appears in this report. `DATABASE_URL` DSNs are masked; `SUPABASE_LIVE_POSTGRES_DATABASE_URL` and all `*_KEY` / `*_SECRET` / password values are referenced by **key name only** |

### 7.3 Method limitations of this pass

1. **The DDL log is truncated at `2026-10-05T15:06:20Z`** (§2.7). The 2026-10-04 application is proven
   directly; the 2026-10-06 application of `20261103` is supported by relfilenode ordering, a 0-byte table
   file mtime, and two same-day implementation reports — **not** by a log entry.
2. `pg_stat_file()` was denied (§2.3), so file sizes/mtimes were obtained with `docker exec ls` instead,
   which gives minute-level mtimes without a `--time-style` option (BusyBox `ls`).
3. `pg_stat_user_tables` carries no history in this database, so the task's proposed vacuum-history age
   method could not be used at all.
4. Only the SQL of the five `20261030`–`20261104` migrations was inspected for created objects; the other
   ~98 migrations were not re-enumerated for orphan objects, so §2.1's "no other object" statement is
   scoped to those five files.
5. Row counts are exact `count(*)` values at the moment of measurement; the environment is live, so counts
   can drift. Cline's numbers were reproduced exactly at a later time, which supports stability.

---

## 8. Verdict

> # `VERIFICATION COMPLETE — BASELINE CORRECTED`

**All three gated findings are CONFIRMED. None is REFUTED.**

- **Task 1 (B-06) — CONFIRMED, and the origin question is now answered:**
  **`ORIGIN = MANUAL_APPLICATION`.** The objects exist (13 / 1 / 2 / 0; plus
  `insight_concurrency_leases` 4 and `instrument_allocations` 0 — Cline's probe was accurate). They were
  created by the repository's own Demo Lab provisioner, `tools/demo_lab/stack.py`, which globs
  `supabase/migrations/*.sql` from the working tree and pipes each file through
  `docker exec -i supabase_db_carbon_ledger psql … -d carbontally_demo_local`, with `ON_ERROR_STOP=0`.
  A full-chain replay on **2026-10-04 13:13 UTC** created `manual_processing_processors` and
  `consultant_mp_allocations` (1,672 statements, one psql PID per file, 97 tolerated `already exists`
  errors); `consultant_relationship_requests` / `consultant_mode_change_requests` followed on
  **2026-10-06** via targeted manual re-application. No commit was lost, nothing was reverted, and no
  second checkout exists.
- **Task 2 (B-01) — CONFIRMED.** 2,537 collected / 7 failed / 8 skipped / 2,522 passed for
  `tests/unit --ignore=tests/unit/api`; 389 collected / 3 failed for `engines`; 2,788 collected for
  `tests/unit/api`. The 7 failing test IDs and their assertion messages match Cline's report exactly. The
  absent tally line is confirmed; the pass/skip split nonetheless proved extractable.
- **Task 3 (B-04) — CONFIRMED.** `backend/.env` = `PORT=8060`, `SUPABASE_URL=http://127.0.0.1:19999`;
  running uvicorn (pid 1014820) = `http://127.0.0.1:54430`, `DATABASE_URL … /carbontally_demo_local`;
  `8060` and `19999` are unbound; `8070`, `54430`, `54426`, `3000` are listening.
  `~/ct_local_env/demo_lab/backend.env` is the running environment source — now proven by **exact
  key-set identity**, not merely by matching values.

**Why "CORRECTED" and not "CONFIRMED".** Two baseline statements require amendment and neither is
cosmetic: (i) Phase 2 §11.3/§5.5 lists two objects as having *no* corresponding migration when both have
one (D-1), which overstates the drift; and (ii) B-06's framing as an unexplained `P2` drift should change
now that the mechanism is proven and PD-E can be reframed (D-2…D-8 are additive). The corrections are
**peripheral** — they do not touch the substance of B-01, B-04 or B-06, and no gated finding is refuted.

**Consequence for the next implementation wave.** The three findings this pass was asked to gate are
solid and can be relied upon. PD-E is unblocked and is a **commit-hygiene / release-baseline decision**,
not a defect to fix in Wave 1: either commit the five migrations so the runtime DB becomes explainable
from Git, or accept the untracked set as a documented input to the Demo Lab provisioner and stop treating
`carbontally_demo_local` as evidence of released state. B-01 remains **RED** and must not be quoted as
green. B-04 remains open and is a documentation/configuration decision, not a code defect.

---

*End of `CT-CARBONTALLY-FOUNDATION-VERIFICATION-03`. No file other than this document was created or
modified; no database write, migration application, service change or git history operation occurred.*
