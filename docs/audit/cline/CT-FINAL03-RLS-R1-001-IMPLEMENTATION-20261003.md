# CT-FINAL03-RLS-R1-001 — Resolve the Stale Migration-Chain Assertion (R1)

**Implemented by:** Cline
**Date:** 2026-10-03
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**HEAD at implementation:** `cabdca8380415e73a25cf23eb393d0b15c0af391`

---

## 1. Task ID

**CT-FINAL03-RLS-R1-001**

Authorised scope (single item): resolve **R1**, the one change-set-introduced
unit-test regression reported by the independent CoStrict verification of the
FINAL-03 RLS remediation:

> R1 — `tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain`
> is a **stale hard-coded assertion** about the newest migration in the chain.

Source recommendation: `docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md`
(recommends updating the test expectation, not the migrations).

Classification: **test-only correction**. No migration, RLS, schema, application,
frontend, admin, backup-implementation or production change was permitted or made.

---

## 2. Original Failure

### 2.1 Reproduction (pre-fix)

Command (exact):

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
./.venv/bin/python -m pytest \
  'tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain' \
  -q -p no:cacheprovider --no-header
```

Result: **1 failed** (evidence: `/tmp/ct_r1_before.txt`, exit code 1)

```
F                                                                        [100%]
=================================== FAILURES ===================================
_ TestMigrationAlignment.test_the_backup_migrations_are_the_newest_in_the_chain _

        assert names.index(BACKUP_01_MIGRATION) > names.index(_PREVIOUS_MIGRATION)
        assert names.index(BACKUP_02_MIGRATION) > names.index(BACKUP_01_MIGRATION)
>       assert names[-1] == BACKUP_02_MIGRATION
E       AssertionError: assert '202610290000...kload_rls.sql' == '202610270000...ification.sql'
E
E         - 20261027000000_ct_backup_02_backup_sets_and_verification.sql
E         + 20261029000000_ct_final_03_staff_workload_rls.sql

tests/unit/backup/test_jobs.py:1077: AssertionError
```

### 2.2 Baseline context

The independent-verification baseline for `tests/unit` was
**4,765 passed / 9 failed / 8 skipped**. Of those 9 failures:

* **1** was introduced by the FINAL-03 change-set — **R1** (this item);
* **8** were classified pre-existing / unrelated.

R1 was therefore the only failure this task was authorised to address.

---

## 3. Root Cause

The test conflated **two different invariants**:

| Invariant the test *owns* | Invariant the test *asserted* |
|---|---|
| The backup migrations are **adjacent and correctly ordered** within the strictly ordered migration chain. | The backup migration `BACKUP_02` is the **absolute tip** (`names[-1]`) of the whole chain. |

`names[-1] == BACKUP_02_MIGRATION` encodes a snapshot of the chain at the moment
the backup feature happened to be the newest work. It is an **absolute**
assertion about a **moving** target.

The chain has since legitimately grown — BACKUP-01/BACKUP-02 are no longer the
newest migrations:

```
20261024000000_ct_final_01_documents_bucket_size_limit.sql
20261025000000_ct_step2_documents_bucket_size_alignment.sql
20261026000000_ct_backup_01_backup_jobs.sql                   <-- BACKUP-01
20261027000000_ct_backup_02_backup_sets_and_verification.sql  <-- BACKUP-02
20261028000000_ct_final_03_rls_security_remediation.sql       <-- later, legitimate
20261029000000_ct_final_03_staff_workload_rls.sql             <-- later, legitimate (tip)
```

Because `20261028…` / `20261029…` sort after `20261027…`, `names[-1]` is no
longer BACKUP-02 and the assertion fails. **The failure is entirely a stale test
expectation.** It is not evidence of a migration-ordering defect: the corrected
transaction positions of the two migrations are, and always were, correct
(BACKUP-01 → BACKUP-02 adjacent). The RLS remediation is unaffected and was
**not** reopened.

The anti-pattern is already documented in this repository
(`backend/tests/unit/api/test_storage_management_step2.py:871-876`), which
contains an explicit comment explaining why an adjacency assertion is used
instead of a chain-tip assertion.

---

## 4. Exact Test Change

**File:** `backend/tests/unit/backup/test_jobs.py`
(test: `TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain`)

### Before (line 1077)

```python
        assert names.index(BACKUP_02_MIGRATION) > names.index(BACKUP_01_MIGRATION)
        assert names[-1] == BACKUP_02_MIGRATION
```

### After (lines 1077-1087)

```python
        assert names.index(BACKUP_02_MIGRATION) > names.index(BACKUP_01_MIGRATION)
        # The backup pair are the newest *in their own block* — the invariant this
        # test owns is adjacency: BACKUP-02 immediately follows BACKUP-01, and
        # BACKUP-01 immediately follows the migration it depends on. It
        # deliberately does NOT claim to be the chain tip: later features (e.g.
        # FINAL-03's 20261028000000/20261029000000 RLS migrations) legitimately
        # sort after the backup block, so asserting
        # ``names[-1] == BACKUP_02_MIGRATION`` would fail every subsequent
        # migration for no reason — the anti-pattern avoided in
        # ``tests/unit/api/test_storage_management_step2.py``.
        assert names.index(BACKUP_02_MIGRATION) == names.index(BACKUP_01_MIGRATION) + 1
        assert names.index(BACKUP_01_MIGRATION) == names.index(_PREVIOUS_MIGRATION) + 1
```

**Change shape:** one obsolete absolute assertion removed; two **adjacency**
assertions added (BACKUP-02 immediately follows BACKUP-01; BACKUP-01 immediately
follows `_PREVIOUS_MIGRATION`). The four pre-existing assertions were left
untouched, so the test is strictly *stronger* than before on ordering within the
backup block (it now pins exact positions, not merely relative order). The
assertion count in this single test went **from 5 to 6**.

Constants referenced (unchanged, `test_jobs.py:1025-1030`):

```python
BACKUP_01_MIGRATION = "20261026000000_ct_backup_01_backup_jobs.sql"
BACKUP_02_MIGRATION = "20261027000000_ct_backup_02_backup_sets_and_verification.sql"
_PREVIOUS_MIGRATION = "20261025000000_ct_step2_documents_bucket_size_alignment.sql"
```

---

## 5. Why the New Assertion Is the Intended Invariant

1. **It tests what the test can own.** A unit test that reads the live
   `supabase/migrations` directory cannot know the future tip of the chain; it
   *can* know that the backup migrations exist and are correctly, adjacently
   ordered relative to the migration they depend on. That is exactly the
   property the backup feature requires for `CREATE TABLE` (BACKUP-01) followed
   by `ADD COLUMN … IF NOT EXISTS` (BACKUP-02) to apply correctly.
2. **It matches the ratified repository convention.**
   `backend/tests/unit/api/test_storage_management_step2.py::
   test_the_alignment_migration_follows_the_existing_chain` uses precisely this
   pattern (`migrations.index(step2) == migrations.index(step1) + 1`) and carries
   the identical documented rationale.
3. **It is monotone under legitimate growth.** Adding any later migration — as
   FINAL-03 did with `20261028000000` / `20261029000000` — leaves the assertion
   true. The test can now only fail on a *real* ordering violation (a migration
   inserted between the backup pair, or between BACKUP-01 and its predecessor).
4. **Nothing was weakened or suppressed.** The test was not deleted, skipped,
   `xfail`ed, excluded, or reduced to `assert True`; no additional migration
   number was hard-coded; no production code was touched.
5. **The sibling test still guards the harder properties.**
   `test_only_the_backup_migrations_touch_the_table` continues to assert that the
   backup pair are the *only* migrations reading / creating `public.backup_jobs`.

---

## 6. Exact Files Changed

| # | Path | Change | Status |
|---|---|---|---|
| 1 | `backend/tests/unit/backup/test_jobs.py` | Replaced 1 line (obsolete chain-tip assertion) with 2 adjacency assertions + explanatory comment (net +10/−1 lines) | Modified |
| 2 | `docs/audit/cline/CT-FINAL03-RLS-R1-001-IMPLEMENTATION-20261003.md` | This report (new) | Created |

**One functional file changed.** No other file was written in this task.

> Note on Git status: `backend/tests/unit/backup/test_jobs.py` is **untracked**
> (`??`) in this working tree — the entire BACKUP-01/BACKUP-02 feature
> (implementation + tests) is uncommitted WIP. Consequently `git diff` for that
> path is empty by construction; the file's own state is the evidence. See §11.

---

## 7. Exact Test Commands

All commands were run from `/home/shomonrobie/ct_93d5cdd/backend` using the
project virtualenv interpreter `./.venv/bin/python` (Python 3.14.4, pytest 9.1.1).

| # | Purpose | Exact command |
|---|---|---|
| 1 | Exact previously failing test (pre-fix) | `./.venv/bin/python -m pytest 'tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain' -q -p no:cacheprovider --no-header` |
| 2 | Exact previously failing test (post-fix) | `./.venv/bin/python -m pytest 'tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain' --no-header -rf` |
| 3 | Owning class | `./.venv/bin/python -m pytest 'tests/unit/backup/test_jobs.py::TestMigrationAlignment' --no-header` |
| 4 | Relevant backup unit-test file | `./.venv/bin/python -m pytest tests/unit/backup/test_jobs.py --no-header -rf` |
| 5 | Complete unit suite | `./.venv/bin/python -m pytest tests/unit --no-header -rf --junitxml=/tmp/ct_unit2.xml` |

**Configuration note (matters for reproducibility).** `backend/pyproject.toml`
sets `addopts = "-q"`. Passing an *additional* `-q` on the command line makes it
`-qq`, which **suppresses pytest's final "N passed … in Xs" summary line** —
a known property of this repository, already recorded in
`docs/cline/CARBONTALLY_P6_2E_INDEPENDENT_VERIFICATION_REPORT.md` (§6) and
`docs/architecture/CT-FINAL-01-20260928-SECURITY-FIX-AND-FINALIZE-REPORT.md`
(§14). Commands 2-5 therefore pass **no** extra `-q` (so the summary line is
emitted), and command 5 additionally writes a JUnit XML so the counts are
independently machine-readable rather than dependent on terminal text. Command 1
retained `-q` because it was the original reproduction and its result is
unambiguous (`F` + `FAILED …` + `EXIT=1`).

---

## 8. Exact Results

### 8.1 Exact previously failing test

| Run | Command # | Result |
|---|---|---|
| Pre-fix | 1 | **1 failed** — `AssertionError` at `test_jobs.py:1077`; `EXIT=1` (`/tmp/ct_r1_before.txt`) |
| Post-fix | 2 | **1 passed in 0.10s** — `EXIT=0` (`/tmp/ct_small.txt`) |

Post-fix output:

```
.
1 passed in 0.10s
```

### 8.2 Owning class and backup unit-test file

| Scope | Command # | Result |
|---|---|---|
| `TestMigrationAlignment` | 3 | **10 passed in 0.29s** |
| `tests/unit/backup/test_jobs.py` | 4 | **83 passed in 0.26s** |

The whole backup unit-test file — including every BACKUP-01/BACKUP-02 migration,
column-projection, job-claim and worker test — is green.

### 8.3 Complete unit suite (`pytest tests/unit`)

Command 5 output (`/tmp/ct_unit3.txt`):

```
7 failed, 4767 passed, 8 skipped, 14 warnings in 407.32s (0:06:47)
```

| Metric | Baseline (pre-fix, IV) | This run (post-fix) | Delta |
|---|---|---|---|
| passed | 4,765 | **4,767** | **+2** |
| failed | 9 | **7** | **−2** |
| skipped | 8 | **8** | 0 |
| errors | 0 | **0** | 0 |
| total | 4,782 | 4,782 | 0 |

**R1 no longer fails.** `tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain` does **not** appear in the failure
summary, and the whole `tests/unit/backup/` file is green (§8.2).

The second failure that disappeared is the environment-dependent
`tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
(§9 row 8) — it asserts `verification_delivered is False`, which depends on
whether the local environment has email delivery configured, and the independent
verification had already flagged it as environment-driven. It passed in this run.
**No test was repaired, edited or suppressed to achieve this** — the only edit in
this task is the one described in §4.

Exact failing tests in this run (7):

```
FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
FAILED tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
FAILED tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
FAILED tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
FAILED tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
```

**All 7 are pre-existing / unrelated to R1 and to FINAL-03** (§9). The suite is
**not** claimed to be green.

Independent machine-readable corroboration of the counts — JUnit XML written by
command 5 (`/tmp/ct_unit2.xml`, 684,502 bytes):

```
<testsuites name="pytest tests">
  <testsuite name="pytest" tests="4782" failures="7" errors="0" skipped="8" />
```

Parsing the XML for `<testcase>` elements containing a `<failure>`/`<error>` child
returns exactly the same 7 tests listed above; no other test failed.

---

## 9. Remaining Failures

R1 is fixed. The pre-existing / unrelated failures were **not repaired** and none
was edited (out of scope; repairing them would exceed the authorised test-only
correction and touch unrelated features). **7 of the 8** reproduce after the fix;
the 8th (row 8 below) is environment-dependent and passed in this run.

Authoritative classification, carried forward from the independent verification
(`docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md` §16, rows 2-9):

| # | Failing test | Class (per IV) | Root reason |
|---|---|---|---|
| 1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | PRE-EXISTING | Asserts `len(names) == 71`; repo holds 98 migration files (p16/p17/ct02/backup already present pre-FINAL-03) |
| 2 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | PRE-EXISTING | Superseded by later migrations predating FINAL-03 |
| 3 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | PRE-EXISTING | Asserts `names[-1] == "20261007000000_…"`; superseded before FINAL-03 |
| 4 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | PRE-EXISTING | Requires all stamps > P16 baseline to be in the P17 set; ct02/step2/backup already violate this |
| 5 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | PRE-EXISTING / unrelated | Extraction-suggestion engine; no relation to migrations or RLS |
| 6 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | PRE-EXISTING / unrelated | as above |
| 7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | PRE-EXISTING / unrelated | as above |
| 8 | `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | PRE-EXISTING / unrelated | Environment-dependent: asserts `verification_delivered is False` but local env has email delivery configured |

**Observed in this post-fix run: 7 failed, and every one of them is a row from
the table above (rows 1-7).** Row 8 (`test_create_request_as_admin`) **passed**
in this run — it is environment-dependent, as the independent verification
already noted, and it was not modified. **R1 is absent from the failure set**,
and the `tests/unit/backup/` file is fully green (§8.2).

The observed set is therefore a strict subset of the pre-existing set: 7 of the
8 pre-existing failures reproduce, 0 new failures appear, and 0 failures were
repaired to produce this. Post-fix totals: **4,767 passed / 7 failed / 8 skipped
/ 0 errors** (baseline 4,765 / 9 / 8 / 0), i.e. **+2 passed / −2 failed / totals
unchanged at 4,782**.

> Note: rows 1-4 are themselves instances of the *same* anti-pattern as R1
> (hard-coded absolute migration counts / chain-tip assertions). They are
> genuinely pre-existing — they failed identically **before** FINAL-03 added
> `20261028…`/`20261029…` — so they are **out of scope** for CT-FINAL03-RLS-R1-001
> and were left untouched. Only R1 was change-set-introduced, and only R1 was
> authorised and corrected here.

**No FINAL-03-relevant test fails.** No security test was deleted, skipped or
weakened.

---

## 10. Confirmation: No Migration / RLS / Application / Production Change

Verified after the edit (mandatory repository check):

| Check | Command | Result |
|---|---|---|
| No migration modified/created | `git status --porcelain supabase/migrations/` | Only pre-existing untracked (`??`) migrations from the FINAL-03 and BACKUP work: `20261025000000…`, `20261026000000…`, `20261027000000…`, `20261028000000…`, `20261029000000…`. **None modified by this task.** |
| FINAL-03 migration bytes intact | `sha256sum supabase/migrations/*20261028000000* supabase/migrations/*20261029000000*` | `20261028000000_ct_final_03_rls_security_remediation.sql` → `ca461c9c5be712b8c5bfaaa8200e2a3be83c5fb55990c3e118446b86904ecb15`<br>`20261029000000_ct_final_03_staff_workload_rls.sql` → `0775fa68388a5e697965b7500284a653df4a96336218ea5b2abbb2b98f7b1cb3` |
| Migration mtimes unchanged | `ls -l --time-style=full-iso supabase/migrations/` | `…20261028000000…` → `2026-10-02 21:53:41`; `…20261029000000…` → `2026-10-02 22:57:52` — **both predate this task** (edit at 2026-10-03 01:56) |
| No RLS / policy / privilege change | repository status + sha256 above | No file under `supabase/` was written by this task |
| No application / backend / frontend / admin change | `git status --porcelain`, `git diff --stat` | The tracked working-tree change-set is **byte-identical** to its pre-task state: 58 files changed, 4417 insertions(+), 790 deletions(-). No application file was written by this task. |
| Only file written | `ls -l --time-style=full-iso backend/tests/unit/backup/test_jobs.py` | mtime `2026-10-03 01:56:43` — the single edit of this task |
| No production / Render / Vercel access | — | No deploy and no production command was issued |
| No commit / push | `git rev-parse HEAD` | HEAD still `cabdca8380415e73a25cf23eb393d0b15c0af391` (unchanged) |

**Conclusion: this task changed exactly one functional file — the unit test.**
No migration, RLS policy, privilege, schema, data, backup implementation or
production artefact was touched. The independently verified FINAL-03 RLS
remediation was **not** reopened.

---

## 11. Git Status

```
HEAD   : cabdca8380415e73a25cf23eb393d0b15c0af391
Branch : p8-release-reconciled
```

Targeted status of the changed file:

```
$ git status --porcelain -- backend/tests/unit/backup/test_jobs.py
?? backend/tests/unit/backup/test_jobs.py

$ git ls-files --error-unmatch backend/tests/unit/backup/test_jobs.py
error: pathspec 'backend/tests/unit/backup/test_jobs.py' did not match any file(s) known to git
Did you forget to 'git add'?
```

`backend/tests/unit/backup/test_jobs.py` is **untracked** — it is part of the
uncommitted BACKUP-01/BACKUP-02 working-tree feature. Therefore `git diff` for
that path is empty by construction; the file's own content (§4) and its mtime
(§10) are the evidence of the change. No `git add`, commit, push, reset, clean,
rebase or force-push was performed.

Other untracked entries visible in `git status` (e.g. `.costrict/`,
`.p18_audit_tmp/`, `backend/backup/*.py`, `supabase/migrations/2026102*…`) are
**pre-existing WIP from earlier FINAL-01/02/03 and BACKUP tasks** and were not
created, modified or removed by this task.

---

## 12. Final Implementation Status

**CT-FINAL03-RLS-R1-001 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

* R1 (the single change-set-introduced unit regression) is resolved by a
  minimal, test-only, invariant-based correction.
* The exact previously failing test passes; the owning class and the whole
  backup unit-test file pass.
* 7 of the 8 pre-existing/unrelated failures reproduce; none was repaired and
  none was edited. The 8th (`test_create_request_as_admin`, environment-dependent)
  passed in this run.
* No migration, RLS, application, backup-implementation or production change
  occurred; FINAL-03 remains closed and **was not reopened**.
* Not claimed: FINAL-03 closure, investor acceptance, or a green unit suite
  while pre-existing failures remain.

**Remaining limitations / unknowns**

1. This is an implementation report, **not** independent verification. The fix
   still requires an independent re-run (OHD/CoStrict) at the FINAL-03 gate.
2. 7 pre-existing failures remain red in `tests/unit` (an 8th is
   environment-dependent and passed this run); four of them (rows 1-4 of §9) use
   the same absolute-migration anti-pattern as R1 and are the natural candidates
   for a **separate** authorised cleanup item — they must not be folded into this
   task.
3. `backend/tests/unit/backup/test_jobs.py` is untracked, so the change is not
   captured by `git diff`; it will enter version control only when the BACKUP
   feature is committed.
4. **The test's own name is now a slight misnomer.** It is still called
   `test_the_backup_migrations_are_the_newest_in_the_chain`, but it no longer
   asserts chain-tip membership — it asserts *adjacency within the backup block*.
   It was **deliberately not renamed**: the exact node ID
   `tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain`
   is how R1 is referenced by the independent verification and by this task, so
   renaming would break that traceability. A future authorised item may rename it
   and update the sibling references. This is a naming/clarity issue only; it has
   no functional effect and does not weaken the assertion (§5).
