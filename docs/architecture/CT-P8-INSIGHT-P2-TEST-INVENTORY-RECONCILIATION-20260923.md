# CarbonTally Insight — P2 Test-Inventory Reconciliation

Date: 2026-09-23
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`

Evidence labelling used throughout: **OBSERVED** (directly executed/read),
**DERIVED** (concluded from evidence), **UNVERIFIABLE** (cannot be established
from the repository or logs).

## 1. Task scope and authorization

PO-authorized bounded P2-only reconciliation after the CoStrict read-only verifier
observed that the historical "P2 79 tests" / "P2+P3 127 tests" claims are not
reproducible, while the dedicated P2 file collects 43 and the P2 implementation
report states 43.

In scope: forensic investigation with no pre-emptive changes; then exactly one of
Path A (documentation-only correction), Path B (add genuinely missing authorized
tests) or Path C (document the ambiguity and stop). Out of scope and untouched:
P3, MIG-1, I1/I2/I4 migrations, I3 architecture, I4 answer states, rate limiting,
Source Evidence Viewer, Scope 1/2/3, supplier persistence, variance/attribution,
factor history, L7, L8, billing, investor-demo, deployment, and the unrelated
pre-existing failures (D17 pin, Review-SLA, frontend DR-007, stale `origin`).

## 2. Starting git state — OBSERVED

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD at start | `1fb2a8475de97923c2886819604ae439231cf8aa` |
| `github/p8-release-reconciled` | identical; `git rev-list --left-right --count HEAD...remote` = `0 0` |
| P2 implementation commit | `f2e4568` — `feat(p8): bounded Insight temporal comparison (P2, capability family 11)` |
| P2 test-file history | exactly two commits touch it: `f2e4568` (created) and `6605475` (MIG-1 catalogue-pin edit) |
| Working tree | **not** clean, and not because of this task: ` M .gitignore` plus untracked `.costrict/`, `8`, `=`, and the pre-existing PO/ChatGPT reference documents. These are **pre-existing verifier/environment artifacts, not created by this task, and deliberately left untouched** |

## 3. Evidence inspected — OBSERVED

1. Commit `f2e4568` and its version of the P2 test file.
2. `docs/architecture/CT-P8-INSIGHT-TEMPORAL-COMPARISON-IMPLEMENTATION-20260922.md`.
3. `docs/architecture/CT-P8-INSIGHT-P2-P3-CLINE-VERIFICATION-20260923.md`.
4. `docs/architecture/CT-P8-INSIGHT-P2-P3-MIG1-REMEDIATION-20260923.md`.
5. `backend/tests/unit/api/test_p8_insight_temporal_comparison.py` (current and at `f2e4568`).
6. pytest collection and execution output (current runs).
7. Retained session logs in `/tmp` from the verification and remediation passes
   (`t1.log`, `t2.log`, `t3.log`, `t4.txt`, `p3final.txt`, `p3reg3.txt`, `vf1.txt`,
   `i4.txt`, `i6.txt`).
8. Every repository file mentioning the P2 tool, to enumerate P2-related coverage
   beyond the dedicated file.

## 4. Historical reconstruction of the 43 vs 79 discrepancy — OBSERVED + DERIVED

**OBSERVED facts:**

* At the P2 implementation commit `f2e4568`, the P2 test file contained **43** test
  functions and **0** occurrences of `parametrize`/`skip`/`xfail`. It contains
  **43** test functions today, with the same zero markers.
* `git diff f2e4568 -- backend/tests/unit/api/test_p8_insight_temporal_comparison.py`
  shows **one hunk only**: the authorized MIG-1 catalogue-pin change
  (`== 8` → `== 10` plus a docstring). No test function was ever added, renamed,
  deleted, disabled or weakened.
* `pytest --collect-only` on the file reports **43** collected tests; a full run
  reports **43 passed**.
* The P2 implementation report states "**43 tests.** Structure:" — i.e. the
  original record was correct.
* **No retained session log contains any pytest summary line mentioning 79 or
  127.** The only numeric summaries present are `299 passed` (13-file regression,
  `t4.txt`) and `1 passed, 47 deselected` (a `-k` filtered run, `vf1.txt`).
* The strings "79" and "127" appear in the repository **only** inside two of my own
  later records: the combined verification report (4 places) and the MIG-1
  remediation report (2 places).

**DERIVED conclusion:** the "79" figure was never measured. It was produced during
the verification pass by arithmetic rather than by reading pytest's output (the
combined P2+P3 run's stdout was truncated by the terminal, and the per-file split
was inferred instead of collected). "127" is simply `48 (real P3) + 79 (invented
P2)`. The correct split is **43 + 48 = 91**. The figures then propagated into the
MIG-1 remediation report by inheritance from the verification report. The 13-file
total of **299** was a real pytest summary and is unaffected.

**UNVERIFIABLE:** the exact keystroke-level reasoning that produced "79" (the
intermediate terminal output is not retained). This does not affect the factual
inventory, which is established directly from git and pytest.

## 5. Actual P2 test inventory — OBSERVED

| Measurement | Result |
| --- | --- |
| Test functions in the dedicated P2 file | **43** |
| `pytest --collect-only` | **43** |
| `pytest` execution | **43 passed, 0 failed** |
| Parametrised cases | **0** |
| Skipped / xfail | **0** |
| Dynamically generated tests | **0** (no collection hooks, no `pytest_generate_tests`) |
| Same figure at `f2e4568` | **43** |

Coverage beyond the dedicated file (P2-referencing shared suites, for completeness
— not counted as "P2 tests"): `test_v3_insight_i3_tools.py` (23 test functions,
includes the I3 catalogue/registry contract), `test_i1_insight_migration.py`
(9), `test_p8_insight_analytics_sql.py` (25). No arithmetic combination of these
produces 79 either.


## 6. Whether missing P2 tests were found — DERIVED

**No.** Every authorized P2 behaviour is covered by the committed 43-test suite
and no gap was identified:

* explicit two-period comparison and the bounded period contract;
* `absolute_change = B − A` and `percentage_change = ((B − A) / A) × 100`;
* zero baseline → percentage unavailable/null with an explicit `zero_baseline`
  basis (no division by zero, no fabricated figure);
* empty period distinguished from a genuine zero (dedicated `no_data` path);
* grouping restricted to `scope` / `activity` / `facility` / `asset`, with
  `month`, `year` and `supplier` rejected as unsupported rather than ignored;
* deterministic ordering and repeatability;
* period-boundary inclusion/exclusion and reversed/invalid-period rejection;
* tenant isolation (cross-organisation denial, foreign identifiers,
  unauthenticated access);
* the existing INS-01 rate-limited execution path;
* provenance via `insight_aggregate_provenance` + the existing Source Evidence
  Viewer, with no second evidence system and no raw text/signed-URL leakage;
* no causal, variance or restatement functionality.

Independent corroboration: the suite passes **43/43**, and the earlier arithmetic
probe against the committed `compare_totals` helper passed 12/12. Nothing in the
file was ever removed, disabled or weakened (§4). Therefore no test was added.

## 7. Whether any implementation defect was found — DERIVED

**No.** The P2 implementation still satisfies the P2 authorization (checklist in
§6) and the reconciliation produced no evidence of an implementation defect. No
production behaviour was changed — and none was needed.

## 8. Decision taken — Path A

**PATH A — No P2 defect; the historical count was simply wrong.**

Per the decision rule, **no test was changed.** The only permitted action was the
minimum documentation correction so the permanent record no longer states a false
P2 test count.

## 9. Exact files changed — OBSERVED

| File | Change |
| --- | --- |
| `docs/architecture/CT-P8-INSIGHT-P2-P3-CLINE-VERIFICATION-20260923.md` | 3 numeric corrections (`79/78`→`43/42`; body `78/79`→`42/43`; §23 table `79`→`43` and `127`→`91`) + CORRECTION note |
| `docs/architecture/CT-P8-INSIGHT-P2-P3-MIG1-REMEDIATION-20260923.md` | 2 numeric corrections (§12 `79 tests: 79 passed`→`43 tests: 43 passed`; §20 `P2 (79)`→`P2 (43)`) + CORRECTION note |
| `docs/architecture/CT-P8-INSIGHT-P2-TEST-INVENTORY-RECONCILIATION-20260923.md` | **new** — this report |

**No test file, no production file, no migration, no frontend file and no
configuration file was modified.** The P2 implementation report already stated 43
and was deliberately left unchanged; the P3 implementation report contains no
79/127 claim, so it needed no touch.

## 10. Tests run and exact results — OBSERVED

| Command (from `backend/`) | Result |
| --- | --- |
| `python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py --collect-only -q -p no:randomly` | **43 collected** |
| `python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py -p no:randomly` | **43 passed, 1 warning** (`43 passed, 1 warning in 0.12s`) |
| `python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py -p no:randomly -v -k 'tenant or cross or unauth or rate or limit or provenance or authoriz or scope'` | collected 43 / **38 deselected / 5 selected → 5 passed** |
| `grep -cE '^(async )?def test_'` on the P2 file | **43** (identical at `f2e4568`) |
| `grep -cE 'parametrize\|skip\|xfail'` on the P2 file | **0** |

The 13-file Insight regression total previously reported (`299 passed`) was
re-measured during the remediation pass and is a genuine pytest summary
(`/tmp/t4.txt`); it is unaffected by this reconciliation.

## 11. P2 behavior verification — OBSERVED + DERIVED

The P2 test file is byte-identical to the implementation commit except for the
authorized MIG-1 catalogue pin, so P2 runtime behaviour is unchanged by
construction; the suite passes 43/43 including tenant, cross-tenant,
unauthenticated, rate-limit and provenance cases (§10). No P2 production file was
modified in this task — the diff contains documentation only.

## 12. Confirmation that P3 and MIG-1 were not modified — OBSERVED

The changed-file set is entirely under `docs/architecture/`. Nothing under
`supabase/migrations/`, `backend/` or `frontend/` was touched:
`20261007000000_p8_insight_data_quality_reproducibility.sql` and its ordering are
unchanged, and no P3 test or implementation file appears in the diff.

## 13. Final Git SHA/alignment

Recorded after committing this reconciliation: commit SHA, push range and
`git rev-list --left-right --count HEAD...github/p8-release-reconciled` = `0 0`
(values recorded in the commit-record follow-up).

## 14. Remaining unrelated failures/issues — OBSERVED, not touched

| Item | Status |
| --- | --- |
| `test_d17_provider_ownership_migration_revision.py` — `assert 81 == 71` | pre-existing, untouched |
| Review-SLA failures | pre-existing, untouched |
| frontend `dr007-investor-display-fixes.test.jsx` | pre-existing, untouched |
| stale `origin` remote | untouched |
| Worktree artifacts ` M .gitignore`, `.costrict/`, `8`, `=` | **pre-existing verifier/environment artifacts**, not created by this task, deliberately not staged |

## 15. No artificial test-count manipulation

**No artificial test-count manipulation was performed.** No test was deleted,
renamed to alter collection, disabled, duplicated, softened or added; no pytest
configuration or discovery setting was changed; and the reconciliation target was
truthfulness, not a number. The inventory was established from git history and
pytest collection, and the only repository changes are documentation corrections
plus this report.

## 16. Final verdict

```text
RECONCILED — NO P2 DEFECT; DOCUMENTATION CORRECTED
```

P2's dedicated test inventory is **43 tests, 43 passing**; it has been 43 since the
implementation commit; no authorized P2 test was ever missing, removed or
weakened; the implementation satisfies the P2 authorization; and the `79`/`127`
figures were mis-derived reporting errors, now corrected in the two affected
records and superseded by this report.

This is **not** independent verification and **not** PO closure. Independent
verification of P2 remains a separate activity.

