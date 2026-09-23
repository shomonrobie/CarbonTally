# CarbonTally Insight — P3-IV-01 Targeted Remediation (Answer-Contract Honesty)

Date: 2026-09-23
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`
Finding remediated: **P3-IV-01** from
`docs/architecture/CT-P8-INSIGHT-P3-INDEPENDENT-VERIFICATION-20260923.md` (§15, summarized §17).

```text
Remediation type: Cline targeted remediation — NOT independent verification.
The defect was found and reported by an independent verifier; this report claims
remediation only. No PO closure of P3 is claimed and P3 is NOT closed.
Independent re-verification of P3-IV-01 (and of the resulting P3 state) is the
next step and is not performed here.
```

Evidence classes used below: **OBSERVED** (executed in this pass and quoted raw) /
**DERIVED** (read from repository files or Git history without execution).

---

## 1. Defect statement (P3-IV-01)

`insight_data_quality` could answer `reason="all_checks_passed"` for a period whose
stored rows existed but **not one of them could be checked**.

```text
status=success
reason=all_checks_passed
records_checked=0
uncheckable_records=1
records_passing=0
```

This contradicts the P3 honesty contract stated in the P3 implementation report
(`CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md`,
§6 line 77: *"…than silently reported as clean ('not checked' never reads as
'checked')"*, and §10 line 139: *"not applicable / not checkable → `success` +
`checkable=false` / `uncheckable_records` (**never a pass**)"*).

The structured counts were already truthful; only the machine-readable **answer
reason** was false. Severity as assessed by the verifier: **LOW–MEDIUM (honesty /
contract)**, non-blocking, no security/tenancy/accounting/data-integrity impact.

---

## 2. Independent-verification evidence

Quote from the independent verification report §15 (OBSERVED by the verifier):

> **P3-IV-01 — `insight_data_quality` reports `all_checks_passed` when nothing could
> be checked.** … with rows present but `records_checked == 0` and
> `uncheckable_records > 0`, the tool returns `status=success` and
> `reason="all_checks_passed"`.

The verifier's reproduction, re-executed **before any edit** in this pass against
HEAD `0c34908d6f49aedf1b46e22cf6816eba881c9f2a` (OBSERVED — identical result, defect
confirmed against current code):

```text
DEFECT REPRO: success all_checks_passed 0 1 0
```

The verifier also recorded that the existing regression test
`test_not_checked_is_never_reported_as_passed` asserted **only the counts** and not
the `reason`, so the test name overstated what was pinned (§15). That observation was
confirmed by directly reading the pre-change test (lines 758–767: three count
assertions, no reason assertion).

Also confirmed by reading the code (DERIVED): the repository holds `reason` as a
tool-contract string (`ToolResult.reason`, `backend/domain/insight_tool.py`), not as
part of the ratified I3 status vocabulary and not as an I4 answer state. No central
reason registry exists and no consumer allowlist references these reason strings in
any `.py`, `.sql`, `.ts`, `.tsx`, `.js` or `.json` file (grep: no hits).

---

## 3. Root cause

`backend/services/insight_tools.py :: _data_quality` decided its answer in this
order (pre-change line numbers):

| # | Condition | Answer |
| --- | --- | --- |
| 1 | `checked == 0 and uncheckable == 0` (line 1134) | `no_data` / `no_rows_in_period` |
| 2 | `with_findings == 0` (line 1139) | `success` / **`all_checks_passed`** |
| 3 | otherwise | `success` / `findings_reported` |

Branch 1 covered only a *genuinely empty* period. Nothing between branch 1 and
branch 2 represented "rows were fetched, but none of them was checkable", so an
all-uncheckable period fell straight through to branch 2: `with_findings` is
necessarily `0` when no check ran, and `0 == 0` produced the all-clear.

Root cause, stated precisely: **the zero-findings answer was reached by "no findings
were produced" rather than by "checks were performed and produced no findings"** — a
missing distinguishing condition, not a wrong count. Fixing it therefore required no
change to any count, to any check, or to any engine.

---

## 4. Forensic inspection performed before changing anything

* Exact branch inspected: `_data_quality`, lines 1049–1154 (pre-change), including the
  loop that classifies each row (`snapshot_from_row(row) is None → uncheckable += 1`,
  lines 1079–1083) and the factor-resolution counter
  (`records_with_unresolved_factor`, lines 1086–1092).
* Existing P3 test inspected: `test_not_checked_is_never_reported_as_passed`
  (lines 758–767 pre-change) — counts only.
* Verifier reproduction re-executed: defect reproduced verbatim (§2).
* The verifier's suggested area was confirmed as correct, and the verifier's
  direction ("the answer must not claim a pass") was confirmed against the code
  rather than adopted on trust. The concrete branch condition and the concrete
  reason string used here are this pass's determination.
* Precedent checked: the sibling P3 tool already expresses "row exists but cannot be
  checked" as `ToolStatus.SUCCESS` + `reason="snapshot_not_checkable"`
  (`_calculation_reproducibility`, lines 1214–1246). The remediation reuses that
  existing convention, so **no new status, no new vocabulary and no new answer state**
  was introduced.

---

## 5. Minimal remediation performed

Exactly one branch was added to `_data_quality`, between the empty-period branch and
the zero-findings branch:

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

Design justifications (each is a scope decision, recorded so the re-verifier can
disagree explicitly):

1. **`ToolStatus.SUCCESS` is retained.** The I3 status vocabulary is ratified and
   closed at six values (PO §9), and the documented answer-state table already places
   not-checkable at `success` + `uncheckable_records` (`never a pass`). The defect was
   the *reason*, not the status. The sibling P3 tool does the same
   (`snapshot_not_checkable`).
2. **`no_data` / `no_rows_in_period` was rejected.** Rows *do* exist in the period;
   reusing that reason would replace one false statement with another.
3. **`reason="no_checkable_records"`** is the new machine-readable string. It states
   the observed situation ("no record could be checked"), not a verdict.
4. **No count, no check and no engine changed.** `data` is returned unchanged (all
   deterministic counts, `checks_performed`, `open_issue_count`, `qc_state_basis`,
   `scan_limit`, `basis`, `population_truncated`), and `truncated` is still
   propagated. `records_checked == 0` and `uncheckable_records > 0` remain the
   truthful population facts.
5. **The decision stays deterministic and pre-narration.** The branch is evaluated in
   Python over the engine's own output, before any LLM narration; nothing was moved
   into the LLM. P3's architecture
   (`existing validation/reproducibility signals → deterministic structured result →
   LLM narration`) is unchanged.
6. **No new quality methodology** — no score, grade, weighting, rating, index or
   heuristic was added.

---

## 6. Exact files changed

| File | Change | Kind |
| --- | --- | --- |
| `backend/services/insight_tools.py` | +12 lines: one new answer branch in `_data_quality` (now lines 1139–1150) | production |
| `backend/tests/unit/api/test_p8_insight_data_quality.py` | strengthened one existing test (docstring + 5 assertions); **no new test function** | test |
| `docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md` | this report (new) | documentation |

Not touched: P2 implementation, P2 tests, the P3 migration, the I3 tool catalogue,
I4 vocabulary, rate limiting, authorization, tenant isolation, provenance, the Source
Evidence Viewer, reproducibility/validation methodology, Scope 1/2/3, suppliers,
variance/attribution, factor history, RAG/knowledge, L7, L8, P12, billing, production
configuration, `.gitignore`, or the PO's untracked reference documents.

### Pre-change → post-change answer behaviour (OBSERVED)

| Situation | Before | After |
| --- | --- | --- |
| rows present, **none** checkable | `success` / `all_checks_passed` ← **defect** | `success` / **`no_checkable_records`** |
| rows present, all checkable, no findings | `success` / `all_checks_passed` | `success` / `all_checks_passed` (unchanged) |
| rows present, findings produced | `success` / `findings_reported` | unchanged |
| no rows in period | `no_data` / `no_rows_in_period` | unchanged |

Raw post-remediation observation (OBSERVED, same script as §2 with the healthy /
empty / findings cases added):

```text
AFTER FIX : success no_checkable_records 0 1 0
HEALTHY   : success all_checks_passed 1 0 1
EMPTY     : no_data no_rows_in_period
FINDINGS  : success findings_reported 1
```

---

## 7. Regression test added/updated

The **existing** test was strengthened rather than a new one added, because the defect
was precisely the gap the verifier identified (counts pinned, reason not pinned). The
P3 test-file inventory therefore remains **48 test functions** (unchanged).

`backend/tests/unit/api/test_p8_insight_data_quality.py :: test_not_checked_is_never_reported_as_passed`
now additionally asserts the answer contract itself:

```python
    assert result.data["records_with_findings"] == 0
    assert result.data["findings"] == []
    assert result.reason != "all_checks_passed"
    assert result.reason == "no_checkable_records"
    assert result.status.value == "success"
```

The pre-existing count assertions (`records_checked == 0`,
`uncheckable_records == 1`, `records_passing == 0`) are retained, so the test now pins
both the truthful counts and the answer contract — i.e. it now pins what its name
claims.

The normal path is pinned by the unchanged, still-passing
`test_complete_record_produces_no_findings` (line 262: `status == "success"`,
`reason == "all_checks_passed"`, `records_passing == 1`). No artificial broad
coverage was added.

---

## 8. Test results

Counts are from pytest JUnit XML reports (authoritative file-based totals; the shell in
this environment did not flush pytest's final terminal summary line to the redirect).

| Suite | Scope | Result (JUnit XML) |
| --- | --- | --- |
| `tests/unit/api/test_p8_insight_data_quality.py` | **P3** (required run 1) | `tests=48 failures=0 errors=0 skipped=0` — exit 0 |
| `tests/unit/api/test_p8_insight_temporal_comparison.py` | **P2** (required run 2) | `tests=43 failures=0 errors=0 skipped=0` — exit 0 |
| Insight regression set — 19 files (required run 3) | all Insight-scoped unit modules | `tests=398 failures=0 errors=0 skipped=0` — exit 0 |
| `tests/unit` (whole unit suite) | collateral-regression check | `tests=3220 failures=4 errors=0 skipped=8` |

Reproduction commands used (from `backend/`):

```bash
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_data_quality.py --junit-xml=/tmp/p3.xml -q --tb=no -rf
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py --junit-xml=/tmp/p2.xml -q --tb=no -rf
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_aggregation.py tests/unit/api/test_p8_insight_data_quality.py \
  tests/unit/api/test_p8_insight_discovery.py tests/unit/api/test_p8_insight_temporal_comparison.py \
  tests/unit/api/test_v3_insight_endpoints.py tests/unit/api/test_v3_insight_i2_authorization.py \
  tests/unit/api/test_v3_insight_i3_tools.py tests/unit/api/test_v3_insight_i3_wiring.py \
  tests/unit/api/test_v3_insight_i4_interactions.py tests/unit/api/test_v3_insight_i4_wiring.py \
  tests/unit/api/test_v3_insight_i5_context_integration.py tests/unit/data/test_i1_insight_migration.py \
  tests/unit/data/test_i2_insight_authorization_contracts.py tests/unit/data/test_i4_insight_migration.py \
  tests/unit/data/test_i4_repository_sql_and_jsonb.py tests/unit/data/test_p8_insight_analytics_sql.py \
  tests/unit/services/test_insight_i5_context.py tests/unit/services/test_insight_query_planner.py \
  tests/unit/services/test_insight_rate_limit.py --junit-xml=/tmp/reg.xml -q --tb=no -rf
.venv/bin/python -m pytest tests/unit --junit-xml=/tmp/unit.xml -q --tb=no -rf
```

The verifier's documented "13-file / 299" regression set is not enumerated in the
repository (that ambiguity is observation **P3-IV-04**, deliberately out of scope
here), so this pass used an explicitly enumerated, larger Insight-scoped set (19
files / 398 tests) and recorded the file list above so the re-verifier can reproduce
it exactly.

### Failure classification (whole unit suite)

| Failing test | Classification | Evidence |
| --- | --- | --- |
| `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | **pre-existing / unrelated** | asserts ops route registration (`assert "/api/v3/ops/sla/settings" in _paths()`); the file contains **zero** references to Insight (`grep -c -i insight` → `0`); the task authorization explicitly excludes Review-SLA failures from this remediation |
| `test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered` | **pre-existing / unrelated** | same file, same cause (adjacent surface assertions in the same test module) |
| `test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained` | **pre-existing / unrelated** | same file, same cause |
| `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | **pre-existing** | `assert 81 == 71` — identical to observation **P3-IV-05** independently recorded by the verifier ("pre-existing D17 migration-count pin (`81 == 71`)", verification report §17 item 5); the file contains zero Insight references |

No failure occurred in any P3, P2 or Insight-scoped suite. No unrelated failure was
repaired, silenced, skipped or re-pinned by this pass.

---

## 9. Confirmation of unchanged P2/P3 boundaries

### P2 protection (P2 is PO-closed and was not reopened)

| Requirement | Result |
| --- | --- |
| P2 production files unchanged | **Confirmed** — `git diff --name-only` lists no P2 file; the only production file changed is `backend/services/insight_tools.py`, and the change is inside the P3-only `_data_quality` function |
| P2 test inventory exactly 43 | **Confirmed** — JUnit XML `tests=43` for `test_p8_insight_temporal_comparison.py` |
| No P2 behaviour changes | **Confirmed** — no P2 code path touched; P2 suite green (43/43) |
| P2 catalogue pin exactly 10 | **Confirmed** — `test_p8_insight_temporal_comparison.py` line 711 `assert len(TOOL_REGISTRY) == 10` passes in the P2 run |

### P3 architecture preserved

* **No migration changed** — the P3 migration is untouched; no schema impact.
* **No I3 catalogue change** — `TOOL_REGISTRY` still holds exactly 10 tools; no tool
  added, removed or repurposed; no `output_fields` change (`reason` is a
  `ToolResult` contract field, not a declared `output_field`).
* **No I4 vocabulary change** — `ToolStatus` still holds exactly its six ratified
  values; no answer state added, renamed or redefined. `reason` was already a
  free-form machine-readable contract string (`ToolResult.reason`) with no registry
  and no consumer allowlist (verified by grep across `.py`, `.sql`, `.ts`, `.tsx`,
  `.js`, `.json`).
* **No new quality methodology** — no score, grade, weighting, rating or heuristic;
  every finding still originates from the existing `ValidationEngine`
  (A1/A2/A5) and `CalculationEngine.verify`, unchanged.
* **Determinism and the narration boundary preserved** — the answer is still decided
  deterministically in Python before any narration; the LLM narrates, it does not
  decide.
* **Honesty contract now mechanically pinned** — `records_checked == 0` with
  `uncheckable_records > 0` can no longer produce `reason == "all_checks_passed"`.

---

## 10. Known remaining observations

1. **P3-IV-02, P3-IV-03, P3-IV-04, P3-IV-05 are NOT addressed** (explicitly excluded
   from this task): the pre-existing foreign-id existence-oracle behaviour, the stale
   migration filename in the historical P3 implementation report, the "13-file / 299"
   regression-set documentation ambiguity, and the pre-existing D17 migration-count pin
   (`81 == 71`). All four remain live governance items.
2. **Deliberate, documented boundary (not a hidden one): partial coverage is
   unchanged.** A period with at least one checkable record plus uncheckable records,
   where the checkable records produce no findings, still returns
   `reason="all_checks_passed"`. This is exactly the authorized scope ("normal P3
   success behavior remains unchanged when records are actually checkable"), and
   `uncheckable_records` remains the truthful structured carrier for partial coverage,
   unchanged by this remediation. Flagged here so the re-verifier can raise it
   explicitly if the owner wants the reason conditioned on `uncheckable_records > 0` as
   well.
3. **Database-level verification of the scan remains an integration task** (unchanged
   limitation, identical to the P3 implementation report and Cline O-3): the SQL is
   verified structurally only; F-046-1 forbids pointing the destructive integration
   harness at a persistent environment.
4. **The pre-existing Review-SLA failures and the D17 pin are untouched** and were not
   repaired, per authorization.
5. **No new reason string is registered anywhere**, because no reason registry exists;
   the string is pinned by the P3 regression test only.

---

## 11. Git state

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| Pre-remediation HEAD | `0c34908d6f49aedf1b46e22cf6816eba881c9f2a` |
| Pre-remediation HEAD subject | `docs(p8): independent OHD verification of P3 data quality + audit/reproducibility (PASS WITH NON-BLOCKING OBSERVATIONS)` |
| `github/p8-release-reconciled` at start | identical; `git rev-list --left-right --count HEAD...github/p8-release-reconciled` → `0 0` |
| `git describe` at start | `v2.1-phase4-371-g0c34908` |
| Working tree at start and end | **dirty, unaffected by this pass**: ` M .gitignore` (pre-existing PO change, **not** authored here and **not** committed) plus untracked pre-existing artefacts (`?? .costrict/`, `?? 8`, `?? =`, and eight untracked `docs/` PO/ChatGPT reference documents) — all left exactly as found |
| Remediation commit | the direct child of `0c34908d…` on `p8-release-reconciled`; it contains **exactly three files** — `backend/services/insight_tools.py`, `backend/tests/unit/api/test_p8_insight_data_quality.py`, `docs/architecture/CT-P8-INSIGHT-P3-IV01-REMEDIATION-20260923.md` (its SHA is the branch head after this commit, verifiable with `git log -1 --stat`) |
| Pushed to | `github/p8-release-reconciled` |
| Post-push alignment | `git rev-list --left-right --count HEAD...github/p8-release-reconciled` → `0 0`; `git ls-remote github p8-release-reconciled` equals local HEAD |
| Unauthorized tracked changes | **none** — no P2, migration, catalogue, vocabulary, configuration or frontend file is in the commit |

No history was rewritten, no force-push, no reset, no clean, no tag. `origin` (the
local `/tmp/ct_step2` remote) was not contacted; `github` is the authoritative remote.

---

## 12. Final implementation status

```text
P3-IV-01 REMEDIATED — READY FOR INDEPENDENT RE-VERIFICATION
```

* The defect is fixed at the only place it existed: `_data_quality`'s answer selection.
* The defect is mechanically pinned by a strengthened P3 regression test that asserts
  the answer contract (not merely the counts).
* The verifier's exact reproduction now yields
  `success no_checkable_records 0 1 0` instead of `success all_checks_passed 0 1 0`.
* Normal success behaviour (all checkable → `all_checks_passed`), the findings path and
  the empty-period path are unchanged.
* P2 is untouched and still exactly 43 tests with the catalogue pinned at 10.
* No unrelated failure was repaired; the only remaining unit-suite failures are
  pre-existing (3 × Review-SLA, 1 × D17 pin).

**Not claimed by this report:**

* P3 is **not** PO-closed, and this report does not close it.
* This is **not** independent verification; the verification above is the implementing
  agent's own testing, which is evidence of *testing*, not of *acceptance*.
* P3-IV-02/03/04/05 remain open governance items and were deliberately not touched.
* Nothing was deployed; P12, L7 and L8 were not started.
