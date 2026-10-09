# CSTR-FINAL03-RLS-R1-VERIFY-001 — Independent Verification of R1 (Stale Migration-Chain Assertion)

**Verifier:** CoStrict (independent verifier — **not** the implementation agent)
**Date:** 2026-10-03
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**HEAD at verification:** `cabdca8380415e73a25cf23eb393d0b15c0af391` (unchanged throughout)
**Implementation under verification:** `docs/audit/cline/CT-FINAL03-RLS-R1-001-IMPLEMENTATION-20261003.md`

---

## 1. Task ID

**CSTR-FINAL03-RLS-R1-VERIFY-001** — independent verification that **R1**
(`tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain`)
was correctly resolved by the test-only correction reported as
**CT-FINAL03-RLS-R1-001**.

The broader **FINAL-03 RLS Security Remediation** was already independently verified
(`docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md`). It was **not reopened**;
this verification only establishes that the R1 change did not alter it.

---

## 2. Scope

### Verified

| Item | Result |
|---|---|
| The exact R1 test change (before/after) | Verified from repository + independent prior-report evidence |
| The invariant the test should protect | Re-derived independently; matches the ratified repository convention |
| R1 test / owning class / owning file | 1 passed / 10 passed / 83 passed |
| Full `tests/unit` suite | 7 failed, 4767 passed, 8 skipped, 0 errors (4,782 collected) |
| Classification of all 7 remaining failures | Established by deterministic predicate replay, not by assertion |
| FINAL-03 migration files unchanged by R1 | Verified (line counts, structural fingerprints, mtimes, write-window scan) |
| No other artefact changed by R1 | Verified (repository-wide write-window scan) |
| No commit / push / deploy / production contact by R1 **or** by this verification | Verified |

### Explicitly out of scope (boundaries honoured)

No code, test, migration, RLS, policy or database data was modified; no other failing
test was repaired; the R1 test was **not** renamed; the four other stale migration-chain
tests were **not** updated; no deploy, no production/Render/Vercel contact, no commit,
no push. This verification was read-only apart from running tests and writing **this**
report.

---

## 3. Files inspected

| # | Path | Purpose |
|---|---|---|
| 1 | `backend/tests/unit/backup/test_jobs.py:1024-1105` | The R1 test, its constants, and its sibling guards |
| 2 | `backend/tests/unit/api/test_storage_management_step2.py:840-877` | The ratified "adjacency, not chain-tip" convention and its documented rationale |
| 3 | `supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql` (name/position only) | The migration BACKUP-01 must follow |
| 4 | `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql` | FINAL-03 Migration 1 integrity |
| 5 | `supabase/migrations/20261029000000_ct_final_03_staff_workload_rls.sql` | FINAL-03 Migration 2 integrity |
| 6 | `docs/audit/cline/CT-FINAL03-RLS-R1-001-IMPLEMENTATION-20261003.md` | Cline's implementation claim (checked, not trusted) |
| 7 | `docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md` | Pre-change baseline (independent, written **before** the R1 edit) |
| 8 | `backend/tests/unit/data/test_d17_provider_ownership_migration_revision.py:261-269` | Remaining failure #1 logic |
| 9 | `backend/tests/unit/data/test_i1_insight_migration.py:50-88` | Remaining failure #2 logic |
| 10 | `backend/tests/unit/data/test_i2_insight_authorization_contracts.py:71-94` | Remaining failure #3 logic |
| 11 | `backend/tests/unit/data/test_p17_migrations.py:107-114` (+ constants) | Remaining failure #4 logic |
| 12 | `supabase/migrations/` (98 `.sql` files) | Migration chain state |

Test-run artefacts produced by this verification: `/tmp/cstr_r1_verify_unit.xml` (JUnit XML),
terminal transcripts. No other file was written.

---

## 4. Exact R1 change verified

Current content of `backend/tests/unit/backup/test_jobs.py:1069-1087`:

```python
class TestMigrationAlignment:
    def test_the_backup_migrations_are_the_newest_in_the_chain(self) -> None:
        names = sorted(path.name for path in _MIGRATIONS_DIR.glob("*.sql"))

        assert BACKUP_01_MIGRATION in names
        assert BACKUP_02_MIGRATION in names
        assert names.index(BACKUP_01_MIGRATION) > names.index(_PREVIOUS_MIGRATION)
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

**Verified change shape (line 1077):**

| Before | After |
|---|---|
| `assert names[-1] == BACKUP_02_MIGRATION` | 10-line explanatory comment + `assert names.index(BACKUP_02_MIGRATION) == names.index(BACKUP_01_MIGRATION) + 1` + `assert names.index(BACKUP_01_MIGRATION) == names.index(_PREVIOUS_MIGRATION) + 1` |

The four preceding assertions and all constants (`test_jobs.py:1025-1030`) are unchanged.
Assertions in this test: **5 → 6** (1 removed, 2 added).

### Evidence of the before-state (independent)

`docs/audit/costrict/CSTR-FINAL03-RLS-VERIFY-001-20261002.md` — written by the **prior independent
verification agent** at **2026-10-03 01:08:59**, i.e. **47 minutes before** the R1 edit
(`test_jobs.py` mtime **2026-10-03 01:56:43**) — records (§16 row 1):

> Asserts `names[-1] == 20261027000000_ct_backup_02_…`

and, identically, in §18 R1:

> A stale hard-coded "newest migration" assertion (the same anti-pattern explicitly
> avoided in `tests/unit/api/test_storage_management_step2.py:863-875`).

This is **pre-change, implementation-independent** evidence that the obsolete assertion
existed exactly as Cline reported. A second, pre-fix failure transcript exists at
`/tmp/ct_r1_before.txt` (mtime 2026-10-03 01:56:05 — 38 seconds **before** the edit),
whose pytest traceback quotes the old line at `test_jobs.py:1077`:

```
>       assert names[-1] == BACKUP_02_MIGRATION
E       AssertionError: assert '202610290000...kload_rls.sql' == '202610270000...ification.sql'
```

Because `backend/tests/unit/backup/test_jobs.py` is **untracked** (`??`, confirmed via
`git ls-files --error-unmatch` → *"did not match any file(s) known to git"*), no VCS diff
baseline exists; the two pre-change records above are the best available before/after
evidence, and they corroborate Cline's §4 and §11 exactly.

---

## 5. Intended invariant (independently re-derived)

### What the sibling convention says

`backend/tests/unit/api/test_storage_management_step2.py:863-876` — the ratified pattern in
this repository:

```python
assert migrations.index(step2) > migrations.index(step1)
# Step 2 is the migration that immediately follows Step 1 — the invariant this
# test owns.  It deliberately does NOT claim to be the chain tip: a later
# revision (BACKUP-01's 20261026000000 backup_jobs migration) legitimately
# sorts after it, and asserting `migrations[-1] == step2` would make every
# subsequent migration fail this test for no reason.
assert migrations.index(step2) == migrations.index(step1) + 1
```

### What the backup migrations actually require

| Fact (independently read from the migrations) | Consequence |
|---|---|
| BACKUP-01 (`20261026000000_ct_backup_01_backup_jobs.sql`) `CREATE TABLE IF NOT EXISTS public.backup_jobs` | must apply **after** the table's predecessor migration |
| BACKUP-02 (`20261027000000_ct_backup_02_backup_sets_and_verification.sql`) `ADD COLUMN IF NOT EXISTS …` (additive) | must apply **after** BACKUP-01, i.e. the backup pair must be **adjacent and correctly ordered** |
| `test_only_the_backup_migrations_touch_the_table` (`:1089-1105`) | the pair are the **only** migrations touching/creating `public.backup_jobs` |

The invariant the test owns is therefore **ordering/adjacency of the backup block** relative
to its required predecessor — **not** membership of the chain tip. A chain-tip assertion
(`names[-1] == …`) can never be an invariant, because the chain grows by design: FINAL-03
legitimately added `20261028000000` / `20261029000000` **after** BACKUP-02. The new
assertions test exactly the invariant that exists; the removed assertion tested a historical
snapshot of feature recency.

Actual chain tail (98 migrations) and the positions the test pins:

```
idx 93  20261025000000_ct_step2_documents_bucket_size_alignment.sql     <- _PREVIOUS_MIGRATION
idx 94  20261026000000_ct_backup_01_backup_jobs.sql                     <- BACKUP_01 (+1)
idx 95  20261027000000_ct_backup_02_backup_sets_and_verification.sql    <- BACKUP_02 (+1)
idx 96  20261028000000_ct_final_03_rls_security_remediation.sql         <- later, legitimate
idx 97  20261029000000_ct_final_03_staff_workload_rls.sql               <- later, legitimate (tip)
```

### Test name: naming mismatch, not incorrect semantics

The name `test_the_backup_migrations_are_the_newest_in_the_chain` is now a **misnomer**:
the body asserts adjacency within the backup block and no longer claims chain-tip
membership (which is factually false — BACKUP-02 is index 95 of 98). The **assertions are
correct**; only the label is stale. Renaming was correctly **not** performed (the node ID
is the traceability key for R1 and an out-of-scope change). Risk noted in §11.

---

## 6. Test commands and results

All commands run from `/home/shomonrobie/ct_93d5cdd/backend` with the project interpreter
`./.venv/bin/python` (Python 3.14.4). No extra `-q` was added (`backend/pyproject.toml`
already sets `addopts = "-q"`; a second `-q` would suppress the summary line).

| # | Command (exact) | Result |
|---|---|---|
| 1 | `./.venv/bin/python -m pytest 'tests/unit/backup/test_jobs.py::TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain' --no-header -rf` | **1 passed in 0.06s** (`EXIT=0`) |
| 2 | `./.venv/bin/python -m pytest 'tests/unit/backup/test_jobs.py::TestMigrationAlignment' --no-header -rf` | **10 passed in 0.08s** (`EXIT=0`) |
| 3 | `./.venv/bin/python -m pytest tests/unit/backup/test_jobs.py --no-header -rf` | **83 passed in 0.25s** (`EXIT=0`) |
| 4 | `./.venv/bin/python -m pytest tests/unit --no-header -rf --junitxml=/tmp/cstr_r1_verify_unit.xml` | **7 failed, 4767 passed, 8 skipped, 14 warnings in 459.45s (0:07:39)** (`EXIT=1`) |

No other test was modified to make these pass (this verification wrote no test file).

**Machine-readable corroboration** of run 4 (`/tmp/cstr_r1_verify_unit.xml`, parsed with
`xml.etree`):

```
<testsuite name="pytest" errors="0" failures="7" skipped="8" tests="4782" time="459.392" ...>
```

| Metric | Prior IV baseline | Cline (post-fix) | This verification (independent) |
|---|---|---|---|
| collected | 4,782 | 4,782 | **4,782** |
| passed | 4,765 | 4,767 | **4,767** |
| failed | 9 | 7 | **7** |
| skipped | 8 | 8 | **8** |
| errors | 0 | 0 | **0** |
| duration | 412s | 407s | 459.45s |

**R1 is not in the failure set.** The JUnit node
`tests.unit.backup.test_jobs.TestMigrationAlignment::test_the_backup_migrations_are_the_newest_in_the_chain`
is present with **no `<failure>` and no `<skipped>` child** → it was collected, executed and
passed (it was not silently deselected or skipped).

The suite is **not** green and is **not** claimed to be green.

---

## 7. Full unit-suite result and remaining-failure classification

Observed set (7 failures, verified from the JUnit XML, not from the implementation report):

| # | Failing test | Class | Independent evidence for the class |
|---|---|---|---|
| 1 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **PRE-EXISTING** | Test asserts `len(names) == 71` (`:264`); true chain size is **98**, and **96** with both FINAL-03 migrations removed — **96 ≠ 71**, so it fails with *or* without FINAL-03. Observed error: `assert 98 == 71`. |
| 2 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | **PRE-EXISTING** | Test requires `later` (migrations after I1) to be one of 6 hard-coded literal lists, the largest ending at `20261007000000_p8_insight_data_quality_reproducibility.sql` (`:63-88`). Actual: **22** entries (20 without FINAL-03), last = `20261029…` (without FINAL-03: `20261027…_ct_backup_02…`) — fails either way. |
| 3 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | **PRE-EXISTING** | Test asserts `names[-1] == "20261007000000_p8_insight_data_quality_reproducibility.sql"` (`:79`). Observed tip = `20261029…`; **without** FINAL-03 the tip is `20261027…_ct_backup_02…` — fails either way; superseded by migrations that predate FINAL-03. |
| 4 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | **PRE-EXISTING** | Test requires every migration with stamp > `_P16_BASELINE = 20261009000000` to be in the fixed P17 set (`:107-114`). Offenders: **9** with FINAL-03, **7** without (ct02 `20261021-23`, final-01 `20261024`, step2 `20261025`, backup `20261026/27`) — fails either way. |
| 5 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | **PRE-EXISTING / UNRELATED** | Failure is `AssertionError: assert '2026-01-15' == '15/01/2026'` (`:30`) — date-normalisation behaviour of the extraction-suggestion engine. No migration, RLS, ordering or backup code participates. Already failing in the prior IV baseline (§16 rows 6-8). |
| 6 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | **PRE-EXISTING / UNRELATED** | Failure is `AssertionError: assert {…} == {}` (`:54`) — engine output shape, same file/mechanism as #5. |
| 7 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | **PRE-EXISTING / UNRELATED** | Failure is `AssertionError: assert {…} == {}` (`:81`), same mechanism as #5/#6. |

Method for rows 1-4 (**not** reliance on Cline's statement): each test's own constants and
predicates were imported and **replayed deterministically** against the live migration
filename list, once as-is (98 files) and once with the two FINAL-03 files excluded (96 files).
All four fail in **both** configurations, which is the definition of pre-existing with
respect to FINAL-03 and R1. The four are instances of the same absolute-count / chain-tip
anti-pattern as R1 and are the natural candidates for a **separate** authorised cleanup item —
**not** repaired here.

Eighth previously-listed failure, `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`:
**did not fail** in this run (consistent with the prior IV's environment-dependence note).
It was not modified.

**Classification confidence.** Rows 1-4: HIGH (deterministic replay). Rows 5-7: HIGH for
"unrelated to R1/FINAL-03" (assertion content is engine behaviour; the file was last written
before the R1 window and is not touched by R1); the prior IV independently observed the same
three failures. Whether an earlier change-set introduced them was **not** established here
and is out of scope.

---

## 8. Evidence that the FINAL-03 migrations were unchanged

The prior IV recorded structural facts but **no sha256 digests** (searched: no hash/checksum
in `CSTR-FINAL03-RLS-VERIFY-001-20261002.md`), so byte-identity cannot be compared to a
recorded digest. Cline reported `ca461c9c…` / `0775fa68…`; this verification **recomputed**
them and obtained the same values — which confirms the report's numbers but is not, by
itself, prior-state evidence. Prior-state evidence is established by the following five
independent facts:

| Check | Result |
|---|---|
| 1. **Line counts** (IV recorded 312 / 222 for M1 / M2) | `wc -l` → **312** and **222** — identical. Any inserted/removed line would change these. |
| 2. **M1 structural line citations** (IV cited M1:96, M1:178-185, M1:258) | `group_a text[] := ARRAY[` at **:96**; arithmetic guard `group_a <> 41 OR group_b <> 2 OR retained_policies <> 4` at **:178-181**; `RAISE EXCEPTION` at :181-184; the only `EXECUTE … ENABLE ROW LEVEL SECURITY` at **:258** — **all exact matches**. |
| 3. **M2 structural fingerprints** (IV cited M2:104, M2:117-120, M2:179) | `fail_closed text[] := ARRAY['staff_workload']` present at **:103** (single target); arithmetic guard `array_length(fail_closed,1) <> 1` at **:116-119**; the only `EXECUTE … ENABLE ROW LEVEL SECURITY` at **:178**; `FOREACH t IN ARRAY fail_closed` at :177. Same structure, citations **+1** off. |
| 4. **File mtimes** | M1 `2026-10-02 21:53:41`, M2 `2026-10-02 22:57:52` — both **predate** the IV report (`01:08:59`) and the R1 edit (`01:56:43` on 2026-10-03). |
| 5. **Repository-wide write-window scan** | `find … -newermt "2026-10-03 00:00:00"` over `backend frontend admin supabase docs` → only `backend/tests/unit/backup/test_jobs.py`, `docs/audit/cline/CT-FINAL03-RLS-R1-001-IMPLEMENTATION-20261003.md`, the IV report itself (its own authoring, 01:08:59) and `backend/.pytest_cache/*`. **No `supabase/` file was written.** `git status --porcelain -- supabase/` shows only the five pre-existing untracked (`??`) migrations, no `M` entry. |

**Recomputed digests (stable across runs):**

```
ca461c9c5be712b8c5bfaaa8200e2a3be83c5fb55990c3e118446b86904ecb15  20261028000000_ct_final_03_rls_security_remediation.sql
0775fa68388a5e697965b7500284a653df4a96336218ea5b2abbb2b98f7b1cb3  20261029000000_ct_final_03_staff_workload_rls.sql
```

**Note on the IV's M2 line citations (+1).** The M2 citations in the prior IV report are one
line higher than the current file, while its M1 citations match exactly and its recorded M2
length (222 lines) equals the current `wc -l`. Since M2's mtime predates the IV report and no
`supabase/` file was written afterwards, the consistent explanation is a one-line citation
error in the IV report, **not** a content change. Recorded here as an evidence-quality note;
it is **not** evidence of mutation and **not** a finding against R1.

### Other no-change confirmations

| Check | Result |
|---|---|
| Files written in the R1 window (after 2026-10-03 01:50) | Exactly **two**: `backend/tests/unit/backup/test_jobs.py` (01:56:43) and `docs/audit/cline/CT-FINAL03-RLS-R1-001-IMPLEMENTATION-20261003.md` (02:19:37) |
| Application / backend / frontend / admin code changed by R1 | **None** (write-window scan) |
| RLS / policy / privilege / schema / data changed by R1 | **None** (no `supabase/` write; migrations unmodified) |
| Tracked working-tree change-set | `58 files changed, 4417 insertions(+), 790 deletions(-)` — identical to the pre-R1 state reported in both the IV and R1 reports (pre-existing FINAL-01/02/03/BACKUP WIP; **no new entry in the R1 window**) |
| Commit / push by R1 | **None** — HEAD still `cabdca8380415e73a25cf23eb393d0b15c0af391` (last commit dated 2026-09-29), no new reflog entry, `git stash list` empty |
| Production / Render / Vercel contact, deploy | **None** (by R1 and by this verification) |
| Commit / push by **this verification** | **None** |
| Secrets/credentials introduced | **None** (the only write is a test file edit and two markdown reports; no credential material appears in them) |

---

## 9. Security and test-coverage assessment

### Does the correction weaken the intended invariant? — **No; it is equivalent-or-stronger**

The removed assertion (`names[-1] == BACKUP_02_MIGRATION`) was not an invariant: it asserted
that the backup feature happened to be the most recently added work. The prior IV itself
classified it as *"a stale hard-coded 'newest migration' assertion (the same anti-pattern
explicitly avoided in `test_storage_management_step2.py:863-875`)"*. No security control,
RLS property, policy, privilege or migration-correctness property was carried by it.
Nothing was deleted, skipped, `xfail`ed, `skipif`-ed, deselected, weakened to `assert True`,
or reduced in scope:

* `TestMigrationAlignment` still contains **10 tests** (10 passed); `test_jobs.py` still
  contains **83 tests** (83 passed).
* The four original ordering assertions remain; **two strict adjacency assertions were added**
  (6 assertions vs 5).
* The sibling guards remain untouched and still pass:
  `test_only_the_backup_migrations_touch_the_table` (the pair are the only migrations
  referencing `public.backup_jobs`, and BACKUP-01 is the only one creating it),
  `test_the_column_projection_matches_the_table_exactly`,
  `test_the_scripted_row_is_shaped_like_the_real_one`,
  `test_the_status_check_matches_the_python_vocabulary`,
  `test_the_scope_check_matches_the_python_vocabulary`,
  `test_the_single_flight_guard_matches_the_active_states`,
  `test_the_table_is_internal_only`.
* **No RLS, policy, authorisation or FINAL-03 test was modified, skipped or weakened.**
  `backend/tests/unit/backup/test_jobs.py` contains **no** `skip`/`xfail`/`skipif` marker.

### Mutation sensitivity (evaluated, per the mandated checks)

Each hypothesis was evaluated against the test's own predicates (deterministic replay over
synthetic name lists — **no file on disk was modified**):

| Scenario | Detected? | Which assertion fails |
|---|---|---|
| **as-is** (current chain) | — | all 6 pass |
| BACKUP-01 placed **before** `_PREVIOUS_MIGRATION` | **YES** | `idx(B01) == idx(PREV)+1` **and** `idx(B01) > idx(PREV)`, plus the BACKUP-01 membership assertion once the renumbering changes the file name (evaluated as a re-stamp to `20261024000000`) |
| BACKUP-02 placed **before** BACKUP-01 | **YES** | membership (`idx(B02) > idx(B01)`, `idx(B02) == idx(B01)+1`) fail under timestamp renumbering |
| Either backup migration **separated from its required predecessor** (e.g. BACKUP-02 re-stamped `20261027000001`) | **YES** | `idx(B02) == idx(B01)+1` fails |
| Required backup ordering **otherwise violated** | **YES** | adjacency assertions fail |
| **Legitimate later migration added** (e.g. a future `20261101…`) | correctly **NOT** detected | all 6 still pass — the regression that caused R1 cannot recur |

Two consequences worth recording (both **intended**, not regressions):

1. The adjacency form is **stricter** than the previous `>` form: inserting any new migration
   with a historical stamp between `_PREVIOUS_MIGRATION` and BACKUP-01 (e.g. `20261025500000…`)
   now fails the test. This is the ratified repository convention (see
   `test_storage_management_step2.py:863-876`) and matches the independent P17/D17 principle
   that historical timestamps must not be reused — i.e. the flag is correct.
2. The test is now **monotone under legitimate chain growth**, which removes the whole class
   of false failure that R1 belonged to.

**Conclusion: no security or test-coverage regression.** `CT-FINAL03-RLS-R1-001` is a
strengthening correction, not a weakening one.

---

## 10. Verdict criteria applied

| Required condition | Outcome |
|---|---|
| Removes the obsolete absolute chain-tip assertion | Yes — `assert names[-1] == BACKUP_02_MIGRATION` gone |
| Verifies `_PREVIOUS_MIGRATION → BACKUP_01_MIGRATION` | Yes (`:1087`) |
| Verifies `BACKUP_01_MIGRATION → BACKUP_02_MIGRATION` | Yes (`:1086`) |
| Verifies the intended adjacency/order invariant | Yes; matches the ratified sibling convention |
| Not a mere weakening | Yes — 2 assertions added, 1 stale non-invariant removed; 5 → 6 |
| No new hard-coded obsolete chain tip | Yes — no absolute tip assertion remains |
| Not skipped / xfailed / deleted | Yes — no marker; node executed and passed in the JUnit XML |
| Test passes | Yes — 1 passed; class 10 passed; file 83 passed |
| Name vs semantics | **Naming mismatch only** (stale label); assertions are correct |
| FINAL-03 migrations unchanged | Yes — §8, five independent checks |
| No other artefacts changed / no commit / no deploy | Yes — §8 |

---

## 11. Limitations

1. **No VCS baseline for the changed test.** `backend/tests/unit/backup/test_jobs.py` is
   untracked (`??`), so `git diff` is empty by construction; byte-level proof of the before
   state is impossible. The before state is established by two pre-change records: the
   **independent** prior IV report (2026-10-03 01:08:59, quoting the old assertion at line
   1077) and the pre-fix pytest transcript `/tmp/ct_r1_before.txt` (01:56:05). No later
   modification of other parts of that file can be excluded by byte comparison; only the
   write-window scan (this file is the **only** test file written after 2026-10-03 00:00) and
   the test-run outcome support it.
2. **No recorded prior digest for the migrations.** Byte-identity is argued from line counts,
   structural line citations, structural fingerprints, mtimes and the write-window scan (§8)
   — strong and mutually consistent, but not a cryptographic comparison. The prior IV's M2
   line citations are +1 relative to the current file (explained in §8; M1's are exact and
   the recorded line counts match).
3. **Pre-existing failure provenance is bounded.** For rows 1-4 of §7 the *pre-existing*
   property (fails with or without FINAL-03) is established deterministically. For rows 5-7
   (extraction engine) only *unrelatedness to R1/FINAL-03* and recurrence in the prior IV
   baseline are established; which earlier change-set introduced them was not investigated.
4. **The R1 test name remains a misnomer.** `test_the_backup_migrations_are_the_newest_in_the_chain`
   no longer asserts chain-tip membership. It was deliberately **not** renamed (out of scope;
   it is the traceability key for R1). Residual clarity risk for future maintainers, who could
   otherwise "restore" the deleted anti-pattern; recommend a **separate** authorised rename.
5. **Working-tree noise.** 181 porcelain entries (123 untracked) and a 58-file / +4417 / −790
   tracked change-set belong to earlier FINAL-01/02/03/BACKUP and other WIP. This verification
   established only that nothing in them was written during the R1 window; their provenance
   was not audited (out of scope).
6. **Four further stale migration-chain tests remain red** (§7 rows 1-4) and were left
   untouched as mandated. They are the natural next authorised cleanup item.
7. **The full unit suite is not green** (7 failed / 4,767 passed / 8 skipped). No claim of a
   green suite, of FINAL-03 closure, or of investor acceptance is made.
8. **Test durations vary** with machine load (459s here vs 407-412s in earlier runs); counts,
   not timings, are the comparison basis.

---

## 12. Final verdict

**CT-FINAL03-RLS-R1-001 — INDEPENDENTLY VERIFIED**

Supporting basis:

* The obsolete absolute assertion `assert names[-1] == BACKUP_02_MIGRATION` is gone; the test
  now pins `_PREVIOUS_MIGRATION → BACKUP_01 → BACKUP_02` adjacency, which is the invariant the
  test owns and the ratified repository convention
  (`backend/tests/unit/api/test_storage_management_step2.py:863-876`).
* The exact R1 test passes (**1 passed**), the owning class passes (**10 passed**) and the
  owning file passes (**83 passed**); in the JUnit XML the test node carries no failure and no
  skip.
* Full `tests/unit`: **7 failed, 4,767 passed, 8 skipped, 0 errors** (4,782 collected) — R1 is
  absent from the failure set. All 7 remaining failures are classified (§7) and none was
  repaired; the four migration-chain failures are proven pre-existing by deterministic replay
  of each test's own predicate with and without the two FINAL-03 migrations.
* **No test-coverage regression**: nothing was skipped, xfailed or deleted; two strict
  adjacency assertions were added; every mutation scenario the test is meant to catch is still
  detected, and legitimate chain growth no longer causes a false failure.
* The R1 task changed only the authorised test file and its implementation report; the two
  FINAL-03 migrations are unchanged by every available measure; no application, frontend,
  admin, RLS, policy or schema change; no production contact, no deploy, no commit, no push.
* The broader, previously verified FINAL-03 RLS remediation was **not reopened** and remains
  independently verified. **FINAL-03 itself is not declared closed here.**

Residual items carried forward to the FINAL-03 gate:

| ID | Item | Owner action |
|---|---|---|
| R1-a | Test name is a misnomer (adjacency asserted under a "newest in the chain" label) | Separate authorised rename (do not fold into R1) |
| R1-b | 4 stale migration-chain tests remain red (`d17`, `i1`, `i2`, `p17`) | Separate authorised cleanup item |
| R1-c | 3 extraction-engine unit failures remain red | Separate investigation (unrelated to migrations/RLS) |
| R1-d | Prior IV report contains a one-line off-by-one in its M2 citations | Documentation-quality, optional |
