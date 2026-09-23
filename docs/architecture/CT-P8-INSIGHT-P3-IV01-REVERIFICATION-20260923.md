# CarbonTally Insight — P3-IV-01 Independent Re-Verification

Date: 2026-09-23
Verifier: Independent verification (restricted verifier agent)
Repository: `/home/shomonrobie/ct_93d5cdd`
Branch: `p8-release-reconciled`
Authoritative remote: `github` (`https://github.com/shomonrobie/CarbonTally.git`)
Model: `deepseek/deepseek-flash`

```text
VERIFICATION TYPE: TARGETED INDEPENDENT RE-VERIFICATION (not the implementing agent)
TARGET: P3-IV-01 — insight_data_quality reporting reason="all_checks_passed"
        when no record could actually be checked
```

This pass is verification-only. No source, test, migration, configuration,
frontend or pre-existing documentation file was modified. The only repository
artifact created by this pass is this report. The remediation report
`CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md` and the previous independent
verification `CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md` are used
**only as claim/evidence sources to be independently confirmed**.

Evidence classes used below:

* **OBSERVED** — the verifier executed it and quotes the raw result.
* **DERIVED** — inferred from repository files / Git history without execution.
* **UNVERIFIABLE** — could not be checked in this environment, with the reason.
* **CLINE CLAIM** — an assertion made by the remediation report, not necessarily
  confirmed here.

---

## 1. Verification identity

| Item | Value |
| --- | --- |
| Working directory | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD (full) | `b39caadc8dbfb3065cf23b8ee4ad6930c0f6b693` |
| HEAD subject | `docs(p8): record the P3-IV-01 remediation commit SHA and push/alignment result in the remediation report` |
| `github/p8-release-reconciled` (local ref) | `b39caadc8dbfb3065cf23b8ee4ad6930c0f6b693` |
| `git ls-remote github refs/heads/p8-release-reconciled` | `b39caadc8dbfb3065cf23b8ee4ad6930c0f6b693` |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | `0	0` (aligned) |
| Verification timestamp (UTC) | 2026-09-23T14:38:11Z (Phase 0) |
| Tool versions | Python 3.14.4; pytest 9.1.1 (backend `.venv`); Node v24.21.0; Docker 29.1.3; Docker Compose 2.40.3; `psql` 18.6 |

Tool version commands (OBSERVED):

```bash
backend/.venv/bin/python --version     # Python 3.14.4
backend/.venv/bin/python -m pytest --version   # pytest 9.1.1
node --version                          # v24.21.0
docker --version                        # Docker version 29.1.3
docker compose version                  # Docker Compose version 2.40.3+ds1-0ubuntu1
psql --version                          # psql (PostgreSQL) 18.6
```

---

## 2. Git ground truth (OBSERVED)

Remotes (OBSERVED `git remote -v`): `origin` → `/tmp/ct_step2` (local, **not**
contacted); `github` → `https://github.com/shomonrobie/CarbonTally.git`
**(authoritative)**.

Ancestry of the claimed commits (OBSERVED `git merge-base --is-ancestor`):

| Commit | Role | Ancestor of HEAD |
| --- | --- | --- |
| `466c159` | P3 implementation | **YES** |
| `6605475` | MIG-1 migration remediation | **YES** |
| `8554b78` | P3-IV-01 remediation | **YES** |
| `b39caad` | remediation report SHA record | **YES** |
| `0c34908` | previous independent P3 verification | **YES** |

Parentage (OBSERVED `git log --format="%h parent=%p %s" -3`):

```text
b39caad parent=8554b78 docs(p8): record the P3-IV-01 remediation commit SHA ...
8554b78 parent=0c34908 fix(p8): remediate P3-IV-01 - the data-quality scan ...
0c34908 parent=f116ed1 docs(p8): independent OHD verification of P3 data quality ...
```

`8554b78` is the direct child of the previous-verification commit `0c34908`;
`b39caad` is its direct child. HEAD == local ref == remote ref == `b39caad`.

Working tree at Phase 0 and at end of verification (`git status --porcelain`) —
**identical both times, unchanged by this pass**:

```text
 M .gitignore
?? .costrict/
?? 8
?? =
?? costrict-p3-ov-01-independent-re-verification.txt
?? docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md
?? docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22-Insight-Strategy-v2.md
?? docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22.md
?? docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md
?? docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md
?? docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md
?? docs/architecture/CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md
?? docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md
```

The single modified tracked file (`.gitignore`) and all untracked entries
**pre-existed at Phase 0** and were not authored or touched by this pass.

> **Worktree caveat (OBSERVED):** the worktree is **not clean**. These files are
> not P3-IV-01 artifacts. Key verified source/test files match the committed
> objects at HEAD (hashes in §13), so the results below are anchored to HEAD and
> are not invalidated by the unrelated dirt.

---

## 3. Previous defect being re-verified (CLINE CLAIM / prior-verifier OBSERVED)

Finding **P3-IV-01** from
`CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md` §15/§17: when a period
contains rows but **every** row is uncheckable (`snapshot_from_row(row) → None`),
`insight_data_quality` returned:

```text
status=success
reason=all_checks_passed
records_checked=0
uncheckable_records=1
records_passing=0
```

This contradicted the P3 answer-state contract in
`CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md`
(line 77: *"…than silently reported as clean ('not checked' never reads as
'checked')"*; line 139: *"not applicable / not checkable → `success` +
`checkable=false` / `uncheckable_records` (**never a pass**)"*). The structured
counts were truthful; only the reason was false.

---

## 4. Remediation evidence (OBSERVED)

`git show 8554b78` changes exactly three files (numstat):

```text
12	0	backend/services/insight_tools.py
14	1	backend/tests/unit/api/test_p8_insight_data_quality.py
385	0	docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md
```

The production change is a single new branch in `_data_quality`, inserted
**between** the empty-period branch and the zero-findings branch (OBSERVED, now
lines 1139–1150):

```python
    if checked == 0 and uncheckable > 0:
        # Rows exist in the period but not one of them could be checked, so no
        # check ran and therefore nothing passed. "Not checked" must never read as
        # "checked and fine": the scan reports that nothing was checkable instead
        # of an all-clear, while the counts stay exactly as the scan computed them.
        return _result(
            TOOL_INSIGHT_DATA_QUALITY,
            ToolStatus.SUCCESS,
            reason="no_checkable_records",
            data=data,
            truncated=truncated,
        )
```

The test change strengthens the **existing** function
`test_not_checked_is_never_reported_as_passed` (no new test function) by adding
`records_with_findings == 0`, `findings == []`, `reason != "all_checks_passed"`,
`reason == "no_checkable_records"`, `status.value == "success"`.

`git diff --name-status 0c34908..HEAD` (OBSERVED) lists **only** those three
files:

```text
M	backend/services/insight_tools.py
M	backend/tests/unit/api/test_p8_insight_data_quality.py
A	docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md
```

`git diff --name-status 8554b78^..8554b78 -- supabase/` and
`git diff --name-status 0c34908..HEAD -- supabase/` are both **empty** — the
migration was not touched (OBSERVED).

---

## 5. Independent reproduction of the old failure condition (OBSERVED)

The verifier independently loaded the **pre-remediation** module source from the
Git object store (`git show 0c34908:backend/services/insight_tools.py`) and
executed it **in memory** (no file written, no checkout, no Git mutation),
alongside the current HEAD module, over identical controlled fixtures:

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
PYTHONPATH=. .venv/bin/python - <<'PY'
import asyncio, subprocess, types, sys
old_src = subprocess.run(["git","show","0c34908:backend/services/insight_tools.py"],
                         capture_output=True, text=True, cwd="/home/shomonrobie/ct_93d5cdd").stdout
old = types.ModuleType("services._old_insight_tools"); old.__dict__["__file__"]="<old>"
sys.modules["services._old_insight_tools"]=old
exec(compile(old_src, "<old>", "exec"), old.__dict__)
# ... build fixtures, call old.invoke_tool / new.invoke_tool for the same inputs ...
PY
```

Raw result (OBSERVED):

```text
CASE               | OLD(0c34908) status/reason                 | NEW(HEAD) status/reason                    | (checked/uncheck/pass/finding)
ALL-UNCHECKABLE    | success/all_checks_passed                  | success/no_checkable_records               | (0, 1, 0, 0)
EMPTY              | no_data/no_rows_in_period                  | no_data/no_rows_in_period                  | (None, None, None, None)
HEALTHY            | success/all_checks_passed                  | success/all_checks_passed                  | (1, 0, 1, 0)
FINDINGS           | success/findings_reported                  | success/findings_reported                  | (1, 0, 0, 1)
PARTIAL-nofind     | success/all_checks_passed                  | success/all_checks_passed                  | (1, 1, 1, 0)
PARTIAL-find       | success/findings_reported                  | success/findings_reported                  | (1, 0, 0, 1)
```

The **old** module reproduces the defect verbatim
(`success / all_checks_passed`, 0/1/0) on the all-uncheckable fixture. This is
the failure condition from P3-IV-01, independently reproduced — not adopted from
the remediation report.

## 6. Independent reproduction of the corrected condition (OBSERVED)

Same run, **current HEAD** module: the all-uncheckable fixture returns

```text
status  = success
reason  = no_checkable_records
records_checked = 0
uncheckable_records = 1
records_passing = 0
records_with_findings = 0
findings = []
```

which is exactly the corrected condition Cline claims. Independently confirmed:

* `reason != "all_checks_passed"` — **TRUE**
* new reason is exactly the implementation contract string `no_checkable_records`
  — **TRUE**
* `status` remains `success` — **TRUE**
* structured counts remain truthful (`0 / 1 / 0`) — **TRUE**
* `findings` remains empty — **TRUE**

## 7. Normal P3 behavior checks (OBSERVED)

| Case | Fixture | Result | Verdict |
| --- | --- | --- | --- |
| A. Empty period | `_Repos(factors=_factors())`, no rows | `no_data / no_rows_in_period` | preserved |
| B. Healthy checkable, no findings | one `_row()` + `_factors()` | `success / all_checks_passed` | preserved |
| C. Checkable with findings | one `_row(unit="")` + `_factors()` | `success / findings_reported` | preserved |
| D. All-uncheckable | one `_row()` with `quantity=None` | `success / no_checkable_records` | **corrected** |

The four cases are **distinguishable and deterministic** (D re-run 3× identical;
the strengthened P3 test re-run 3× → `1 passed` each time, §9). The new branch is
strictly between cases A and B and does not change A, B or C.

---

## 8. Partially-uncheckable case analysis (OBSERVED + DERIVED)

Fixture: one checkable healthy record (`snap-a`) **plus** one uncheckable record
(`snap-b`, `quantity=None`). Raw result (OBSERVED, deterministic 3/3 runs):

```text
run0: success/all_checks_passed checked=1 uncheckable=1 passing=1 findings=0
run1: success/all_checks_passed checked=1 uncheckable=1 passing=1 findings=0
run2: success/all_checks_passed checked=1 uncheckable=1 passing=1 findings=0
```

Also OBSERVED with a finding on the checkable record: `success / findings_reported`
(checked=1, uncheckable=1).

The remediation report discloses this boundary exactly (its §10.2):
*"partially uncheckable periods … still answer `all_checks_passed`, unchanged by
design, with `uncheckable_records` remaining the truthful carrier."*

### Verification question

> Does `reason="all_checks_passed"` in this partially-uncheckable case contradict
> the established P3 contract that "not-checked must never read as checked"?

### Trace of the contract semantics (DERIVED from repository files)

* **Contract statements (P3 implementation report):**
  * L77 — the "not checked must never read as checked" principle is stated for the
    case where *a check could not run* (empty activity, unresolved factor), and the
    remedy is that the record is *counted* in `records_with_unresolved_factor`
    rather than silently reported clean.
  * L139 — the answer-state table maps the "not applicable / not checkable"
    **semantic** to `success` + `checkable=false` / `uncheckable_records`
    (**never a pass**). The carrier of that semantic is `uncheckable_records`.
* **Same design pattern for the sibling partial-coverage field (OBSERVED in
  code):** a period with a checkable record whose factor is unresolvable, and
  otherwise no findings, already returns `all_checks_passed` with
  `records_with_unresolved_factor > 0` as the truthful carrier. Partial coverage
  is carried by a structured count, not by the reason string. This pattern
  predates the remediation and is unchanged.
* **The defect P3-IV-01 as defined** is the case where **no record could actually
  be checked** (`records_checked == 0`). The partial case has a record that
  *could* be checked, so it is outside the finding's own definition.
* **In the partial case the uncheckable record is not represented as checked** —
  it is carried as `uncheckable_records=1`; `all_checks_passed` describes the one
  check that actually ran and passed.

### Classification

```text
2. NON-BLOCKING OBSERVATION
```

Reasoning: under the "reason describes the checks that actually ran; counts
describe coverage" reading — which is the established P3 design and matches the
documented carrier (`uncheckable_records`, L139) — the partial case is consistent
with the contract. A stricter reading ("any uncheckable record ⇒ the period must
never return a pass reason") would make it a residual tension: `all_checks_passed`
is a machine-readable string that could be consumed without inspecting the counts.
The verifier does **not** classify this as a genuine P3 defect because (a) the
truthful structured carrier is present, (b) the reason is not a fabricated pass
(a check ran and passed), (c) it matches the established partial-coverage
pattern, (d) it was explicitly and prominently disclosed rather than hidden, and
(e) the remediation's authorized scope was the `records_checked == 0` condition.
It is recorded as a non-blocking observation for the Product Owner to confirm
intent. **If** the owner intends the strict reading, a follow-on authorization
would be required to condition the reason on `uncheckable_records == 0` as well;
**this verifier performed no such change and expanded no scope.**

---

## 9. P3 test results (OBSERVED)

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_data_quality.py \
    -p no:cacheprovider -o addopts="" --no-header -q
# => 48 passed, 1 warning in 0.18s   (exit 0)
```

Exact totals: **48 collected, 48 passed, 0 failed, 0 skipped, 0 errors.**
`grep -cE "^(async )?def test_"` = **48** at `0c34908` and **48** at HEAD.
No `skip`/`xfail`/`pytest.mark` occurrences in the file (OBSERVED). The
strengthened test `test_not_checked_is_never_reported_as_passed` was re-run in
isolation 3× → `1 passed` each time (deterministic, not flaky).

Test file line count: **871** at `0c34908` → **884** at HEAD (+14/−1 = +13).

## 10. P2 regression results (OBSERVED)

```bash
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py \
    -p no:cacheprovider -o addopts="" --no-header -q
# => 43 passed, 1 warning in 0.21s   (exit 0)
```

* P2 inventory: `grep -cE "^(async )?def test_"` = **43** (unchanged).
* Catalogue pin remains an exact count: `test_p8_insight_temporal_comparison.py:711`
  `assert len(TOOL_REGISTRY) == 10` (OBSERVED), `TOOL_REGISTRY` = 10 tools.
* P2 production/migration files unchanged since the P2 commit:

```bash
git diff --name-status f2e4568..HEAD -- \
  backend/services/insight_temporal_comparison.py \
  backend/domain/insight_query.py \
  supabase/migrations/20261006000000_p8_insight_temporal_comparison.sql \
  frontend/src
# => (empty)
```

**Conclusion: no P2 regression; P2 is not reopened.**

## 11. Insight regression results (OBSERVED)

The 19-file Insight-scoped set enumerated in the remediation report was executed:

```bash
.venv/bin/python -m pytest <19 insight files> -o addopts="" -p no:cacheprovider --no-header -q
# => 398 passed, 5 warnings in 2.44s   (exit 0)
```

This **preserves** the previous independent verifier's 398-test result exactly.

Whole unit suite (collateral regression check):

```bash
.venv/bin/python -m pytest tests/unit -o addopts="" -p no:cacheprovider -q --tb=no -rf
# => 4 failed, 3208 passed, 8 skipped, 13 warnings in 239.54s
```

The 4 failures are the **pre-existing / unrelated** ones previously classified
(not caused by this remediation):

| # | Failing test | Classification |
| --- | --- | --- |
| 1 | `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | pre-existing Review-SLA `_IncludedRouter` |
| 2 | `test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered` | pre-existing Review-SLA |
| 3 | `test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained` | pre-existing Review-SLA |
| 4 | `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | pre-existing D17 migration-count pin (`81 == 71`) |

None of these files is touched by the remediation (diff = 3 files, §4). None was
repaired. (No frontend test was run this pass; the DR007 failure previously
reported is outside the Insight regression and no frontend file was changed.)

## 12. Test-integrity findings (OBSERVED)

* P3 inventory remains exactly **48** tests (was 48 at `0c34908`; still 48 at HEAD).
* No test was removed, disabled, renamed to evade collection, or marked
  `skip`/`xfail`.
* No collection configuration was changed (`git diff 0c34908..HEAD` changes only
  the three files in §4; no `conftest.py`, `pytest.ini`, `pyproject.toml`,
  `setup.cfg` or CI file is in the diff).
* `test_not_checked_is_never_reported_as_passed` **now actually asserts the reason
  contract** (`reason == "no_checkable_records"`, `reason != "all_checks_passed"`,
  `status == "success"`, `findings == []`), fixing the previously-noted weakness
  where the name overstated what was pinned.
* P2 inventory remains exactly **43**; P2 catalogue pin remains an exact `== 10`.
* The new reason string `no_checkable_records` occurs only in the implementation
  (`services/insight_tools.py:1147`), the P3 test (`:779`) and the remediation
  report — there is no reason registry or consumer allowlist to update
  (OBSERVED `grep -rn` across `.py/.sql/.ts/.tsx/.js/.json`).

## 13. Scope / diff integrity (OBSERVED)

`git diff --name-status 0c34908..HEAD` contains **only** the three authorized
files (§4). Consequently, unchanged:

* **I3 ToolStatus vocabulary** — still exactly 6 values
  (`success, no_data, not_authorized, invalid_input, provider_unavailable, error`).
* **I4 answer-state vocabulary** — the I4 migration is untouched
  (`supabase/` diff empty); `ci_interactions_answer_status_check` is unchanged
  (14 states in the I4 migration + `multiple_matches` added by the INS-01
  migration `20261005000000…`, unchanged).
* **P3 migration** — untouched (empty diff).
* **Authorization / tenant isolation / rate limiting / provenance / Source
  Evidence Viewer / reproducibility & validation methodology** — untouched (the
  only production edit is the new branch in `_data_quality`; the diff's 12 added
  lines are those 12 lines and nothing else).
* **P2** and **frontend** — untouched.

No new Scope 1/2/3, supplier analytics, variance/attribution, factor history,
RAG, L7, L8, billing, P12 or production capability was introduced: a keyword scan
of the remediation's added lines (`git show 8554b78 -- backend/ | grep '^+'`)
for `scope3|supplier|variance|attribution|factor.histor|rag|knowledge|billing|
subscription|l7|l8|p12|deploy` returned **NONE FOUND**.

Key file SHA-1 at end of verification (OBSERVED `git hash-object`):

```text
566cfb7eb2d1f5c5dc395b1d97910c75035f46a1  backend/services/insight_tools.py
e73a31f543797c465fbb79e266c97498df20d58b  backend/tests/unit/api/test_p8_insight_data_quality.py
880276302842874e422b562d2c2f44d9aeb759ee  backend/domain/insight_quality.py
413e0fc2a7ddd5a0057c4aa50e3614948eaca048  supabase/migrations/20261007000000_p8_insight_data_quality_reproducibility.sql
```

### Non-interference evidence

| Item | Phase 0 | End | Verdict |
| --- | --- | --- | --- |
| HEAD | `b39caadc…` | `b39caadc…` | unchanged |
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | unchanged |
| `github/p8-release-reconciled` | `b39caadc…` (`0 0`) | `b39caadc…` (`0 0`) | unchanged |
| `git status --porcelain` | 13 entries (see §2) | identical | unchanged by this pass |

No Git mutation (no commit/push/reset/checkout/rebase/merge/stash/clean/amend/
tag) was performed **during verification**. No database was contacted at all by
this pass; no shared, staging or production database was touched.

---

## 14. Remaining observations / limitations

### Non-blocking observations that remain

1. **Partial coverage (§8)** — a period with at least one checkable record and at
   least one uncheckable record still answers `reason="all_checks_passed"` with
   `uncheckable_records > 0` as the truthful carrier. Classified **NON-BLOCKING
   OBSERVATION** (consistent with the established partial-coverage design; see §8
   for the reasoning and the strict-reading caveat). A PO/owner ruling on intent
   is invited; no change was made.
2. **P3-IV-02** — foreign-id existence oracle (pre-existing, shared with the
   ratified `calculation_snapshot_lookup`) — **not in scope, still open**.
3. **P3-IV-03** — stale pre-rename migration filename in the historical P3
   implementation report — **not in scope, still open**.
4. **P3-IV-04** — the "13-file / 299" regression set is not enumerated — **not in
   scope, still open** (this pass reproduced the 398-test superset, all green).
5. **P3-IV-05** — pre-existing D17 migration-count pin (`81 == 71`) — **not in
   scope, still open** (one of the 4 unrelated unit-suite failures).

### Limitations

* **Database-level behavior was not exercised** (UNVERIFIABLE by design this
  pass): the remediation changes no SQL and no migration, so there is no
  migration applicability/correctness question to answer for P3-IV-01. The
  migration chain was not re-applied.
* **Frontend behavior** — no frontend file changed, so no frontend run was
  performed.
* The defect and its remediation were reproduced at the **tool layer**
  (`invoke_tool` → `_data_quality`), which is the relevant execution path; the
  HTTP route was exercised indirectly by the unchanged passing suite.

### Claims reproduced vs claims left as claims

| Claim | Verifier result |
| --- | --- |
| Remediation commit `8554b78` is the child of `0c34908` | **REPRODUCED** (OBSERVED) |
| Report SHA record `b39caad`; HEAD == `b39caadc8…` | **REPRODUCED** (OBSERVED) |
| `8554b78` and `b39caad` are ancestors of HEAD | **REPRODUCED** (OBSERVED) |
| Old defect: `success/all_checks_passed 0 1 0` | **REPRODUCED** (old module exec, OBSERVED) |
| Corrected: `success/no_checkable_records 0 1 0` | **REPRODUCED** (HEAD module, OBSERVED) |
| Normal empty/healthy/findings unchanged | **REPRODUCED** (OBSERVED) |
| P3 = 48 passed | **REPRODUCED** (48 passed) |
| P2 = 43 passed, catalogue 10 | **REPRODUCED** (43 passed; `== 10`) |
| Insight regression 398 passed | **REPRODUCED** (398 passed) |
| Exactly three files changed; no migration/catalogue/vocabulary change | **REPRODUCED** (OBSERVED) |
| Partial-coverage boundary unchanged | **REPRODUCED** (OBSERVED; §8) |

---

## 15. Final verdict

```text
PASS WITH NON-BLOCKING OBSERVATIONS
```

**P3-IV-01 is independently re-verified remediated.** The original reproduction
no longer yields `all_checks_passed`; the corrected result is exactly
`success / no_checkable_records` with truthful counts and empty findings; the
empty/healthy/findings paths are preserved; P3 = 48/48, P2 = 43/43, Insight =
398/398; the diff is limited to the authorized three files; and no material
regression was introduced.

**What remains, and why it is non-blocking:**

* The **partially-uncheckable** boundary (§8) answers `all_checks_passed` with
  `uncheckable_records` as the truthful carrier — classified **NON-BLOCKING
  OBSERVATION**, consistent with the established partial-coverage design and
  explicitly disclosed by the remediation; a PO ruling on the strict reading is
  invited.
* **P3-IV-02, P3-IV-03, P3-IV-04, P3-IV-05** remain open governance items
  (explicitly outside this remediation's scope); none is a security, tenancy,
  provenance, accounting or data-integrity defect.

**Governance boundary honoured by this pass:** no fix, no test/migration/
documentation change (other than this single authorized report), no Git history
rewrite, no PO closure of P3 or MIG-1, no P12/L7/L8/production action, and no
attempt to fix P3-IV-02/03/04/05 or the unrelated failing tests.
