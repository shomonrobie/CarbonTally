# CarbonTally — DEMO-T3-REM-001 Implementation Report (canonical)
## including REM-001-CONT execution results

**Implementation IDs:** `DEMO-T3-REM-001` · continuation `DEMO-T3-REM-001-CONT`
**Related:** `DEMO-T3-IMP-001` (`ad46599…`), verification `OHD-079` (FAIL), remediation commit `c2ff4e6…`
**Type:** IMPLEMENTATION REPORT — no PO closure, no independent verification claimed.

### Earlier history (preserved, not rewritten)

The full REM-001 diagnosis and the implemented fixes for **B-1** (real-extractor corpus selection),
**B-2** (reset via the Storage API), **O-A** (`JWT_JWKS` for the lab storage API) and **O-B**
(fail-loud instead of silent degradation) are recorded in
`docs/architecture/CARBONTALLY_DEMO_T3_REMEDIATION_20260920.md` (commit `c2ff4e6`), which also
records that the task was then **BLOCKED — INCOMPLETE EXECUTION**. That statement is preserved here.

---

## REM-001-CONT EXECUTION RESULTS

### 1. Continuation start state (VERIFIED)

| Item | Observed |
|---|---|
| Branch / HEAD | `p8-release-reconciled` / `c2ff4e6662e57192e19446a0097c50faec6ee9a1` (expected) |
| Working tree | clean |
| Rebuild process | **not running** (0 matching processes) — it had terminated |
| Rebuild outcome | `sync_rc=1`: `FAIL: no parseable candidate found for: uk-spend, uk-ambiguity` + `The existing corpus was NOT replaced.` |
| On-disk corpus | **unchanged** (old heuristic corpus: 11 documents, `selection.method = None`, 0 `extractor_verdict`) — the B-1 fail-safe behaved correctly |
| Evidence loss observed | on failure only the summary error is written; per-scenario selection evidence from the partial sweep is not retained (narrow bounded defect of the tooling) |

**Interpretation:** the new selector resolved **9 of 11** scenarios with real-extractor proof inside the
deterministic bound, and refused to write a partial/weak corpus for the remaining 2.

### 2. Remaining blockers (precise)

| # | Blocker | Evidence | Status |
|---|---|---|---|
| R-1 | `uk-spend` has no candidate that the release extractor resolves to activity+quantity+unit within the deterministic bound (240 candidates of the `royal_mail` pool). The release's spend path documented in `services/automatic_extraction.py` is a **tabular** rule ("currency amounts without a unit column become spend-based lines" for CSV/XLSX); no PDF-spend extraction rule was found. | rebuild failure list; extraction-service docstring | **PO DECISION REQUIRED** (§15): either re-scope the spend scenario to a supported existing path or confirm it is unsupported for PDF documents |
| R-2 | `uk-ambiguity` found no parseable candidate in the `scottish_power` pool within the bound; a different electricity-family pool must be selected for the deliberate-ambiguity scenario | rebuild failure list | in-bound remediation available (§14 permits choosing another existing supported ambiguity representation); not yet executed |
| R-3 | `uk-missing-evidence` selection uses the new `expect_unparseable` path | manifest | implemented, not yet exercised in a completed sweep |
| R-4 | §8 validation table, §9–§15 B-3 factor revalidation, §19–§22 seeding/calculation/ground-truth, §23–§24 reset + reseed proof, §25–§26 authenticated-user JWT and storage-security re-assertion, §27–§28 parity/isolation, §29 idempotent seeding, §30 matrix | not executed in this continuation | outstanding |

No hard-stop boundary (§35) was crossed: no generator, extraction-engine, factor-engine,
calculation-engine, production, RLS, IE/OCR or governance change; no security weakening; no fabricated
evidence; no direct database insertion to bypass the workflow.

### 3. Git state at hand-off (VERIFIED)

Continuation commit recorded in the final status block below; branch `p8-release-reconciled`, pushed to
`github`; `c2ff4e6…` not rewritten; working tree clean.

### 4. Final implementation status

**DEMO-T3-REM-001 IMPLEMENTATION BLOCKED — PO REVIEW REQUIRED**

The single PO-level decision that unblocks the remainder is **R-1 (spend)**: whether the T3 spend
scenario should exercise an existing *supported* path (e.g. the tabular/spend-suggestion workflow or a
supported currency-based activity) or be recorded as unsupported for PDF documents. R-2 may then be
completed in-bound, followed by the validation table, B-3, seeding, calculation reachability, reset and
storage re-assertions.

Evidence classification for this continuation: items marked VERIFIED were executed and observed in this
session; the B-1/B-2/O-A/O-B implementations remain **PREVIOUSLY VERIFIED (implementer-run, pre-OHD)**
plus OHD-079's independent reproduction of the defects; everything in R-4 is **NOT VERIFIED**.
