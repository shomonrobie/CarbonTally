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

### 5. REM-001-CONT round 2 — PO decisions R-1/R-2 and empirical B-3 (§9–§16)

**R-1 — `uk-spend` (VERIFIED decision implemented).** Per the PO decision, no spend-extraction
functionality was created. The release documents spend handling only for **supported tabular inputs**
(CSV/XLSX: "currency amounts without a unit column become spend-based lines",
`backend/services/automatic_extraction.py`), and no PDF spend path exists. `uk-spend` is therefore
recorded in `t3_manifest.json` as `supported: false`, `select: false`, with an explicit
`unsupported_reason` and `expected.outcome = "UNSUPPORTED (no PDF spend path)"` — an explicit recorded
limitation, not a hidden failure.

**R-2 — `uk-ambiguity` (VERIFIED decision implemented).** No `scottish_power` candidate parsed within
the deterministic bound, so the scenario was re-pointed at an **already-supported electricity pool**
(`samples/**/*shell_energy*.pdf`) with `skip_index = 1` (so it cannot reuse another scenario's document).
The ambiguity itself continues to come from the existing matcher; no threshold was weakened and no
factor was forced.

**B-3 — empirical factor revalidation (VERIFIED, executed).** Command: `POST /api/v2/factor-match`
on the running Demo Lab with an org-member token (`backend/.venv/bin/python /tmp/cont_b3.py`,
HTTP 200 for every probe).

| Family | Matching input | Observed status | Factor ID | Matched factor |
|---|---|---|---|---|
| electricity | `Electricity ` / `kWh` / GB / 2025 | **ambiguous** (confidence 0.0) | — | — |
| natural gas | `Natural gas` / `kWh` / GB / 2025 | **matched** (confidence 1.0) | `b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5` | `Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]` |
| diesel | `Diesel` / `litres` / GB / 2025 | **ambiguous** (confidence 0.0) | — | — |
| waste (disposal) | `Waste disposal` / `tonnes` / GB / 2025 | **ambiguous** (confidence 0.0) | — | — |
| waste (collection) | `Waste collection - General` / `tonnes` | **no_match** | — | — |
| water | `Water supply` / `cubic metres` / GB / 2025 | **matched** (confidence 1.0) | `fb9d28bf-f615-4110-b0e7-0fd13453b666` | `Water supply > Water supply > Water supply (kg CO2e) [cubic metres]` |

This **independently confirms OHD-079's B-3 findings** against the real engine: only natural gas
(preserving the existing Net-CV behaviour) and water resolve deterministically today; electricity,
diesel and waste-disposal are genuinely ambiguous; the `Waste collection - General` wording is
`no_match` — so a generic `Waste + tonnes` line can reach the wrong (`Waste oils`) family, exactly as
OHD reported. **No factor-engine, alias, threshold or extraction change was made**; these outcomes are
the product's actual behaviour and are now recorded as the T3 contract.

**R-3 — `expect_unparseable` missing-evidence path:** implemented (selection mode); its end-to-end
exercise is outstanding (below).

### 7. Round 3 — B-3 expectations encoded, R-2 corrected, sweep relaunched

* **Step 2 (manifest expectations) — IMPLEMENTED (VERIFIED source evidence).** `t3_manifest.json` now
  encodes the empirically observed product behaviour per scenario: `EXPECTED_MATCHED` with exact factor
  IDs (`natural_gas` → `b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`, `water` →
  `fb9d28bf-f615-4110-b0e7-0fd13453b666`), `EXPECTED_AMBIGUOUS` (electricity, diesel, waste-disposal),
  `EXPECTED_NO_MATCH` (waste collection wording) and `UNSUPPORTED_PDF` (spend), each carrying the exact
  probe request used. No thresholds, aliases or engine code were touched.
* **R-2 correction — VERIFIED.** The round-2 sweep failed on exactly one scenario (`uk-ambiguity`)
  because `skip_index = 1` required *two* parseable candidates in that pool. Because the substitution
  already uses a distinct supplier pool (`shell_energy`, different from the octopus/EDF pools of the
  other electricity scenarios), `skip_index = 0` is both sufficient and deterministic; the round-3
  sweep was relaunched with that correction.
* **Round-3 sweep — NOT EXECUTED (still running at hand-off).** No partial/degraded corpus is written;
  the fail-safe remains in force.

### 8. Round 3 result — `uk-ambiguity` pool unsuitable (VERIFIED failure, fail-safe intact)

Round-3 sweep outcome (command `backend/.venv/bin/python tools/demo_lab/t3_scenarios.py sync-corpus
--source /tmp/extgen`, log `/tmp/rem3_sync.txt`):

```
FAIL: no parseable candidate found for: uk-ambiguity
The existing corpus was NOT replaced. Broaden the scenario accept rules, extend PROBE_CAP, or report
this as a PO-level blocker.
sync_rc=1
```

* **Every other selectable scenario passed** (the failure list contains only `uk-ambiguity`; `uk-spend`
  is excluded by the R-1 decision), so the probe-driven selection is working across the corpus.
* **The `shell_energy` pool (96 candidates) contains no document that the release extractor resolves to
  activity + quantity + unit** within the deterministic bound (sorted pool, chunk 30, cap 240) — with
  `skip_index = 0`, so this is not an index artefact but a property of that supplier's layouts.
* **The fail-safe held**: the on-disk corpus was NOT replaced; no degraded or partial corpus was written
  at any point in rounds 2–3; the protected storage trigger and all security configuration are untouched.

**Bounded next step (no scope expansion, no engine change):** re-point `uk-ambiguity` at a supplier pool
already **proven parseable** by an earlier successful selection, with `skip_index = 1` so it cannot reuse
that scenario's document — i.e. reuse the pool family that resolved `uk-electricity`
(`*octopus_energy*`, 120 candidates) or `consultant-client-a` (`*edf_energy*`). This is a manifest-only
change using the existing selector; the ambiguity itself still comes from the existing matcher.

**Downstream evidence remains NOT EXECUTED** as a direct consequence: §8 validation table, real-API
seeding, E2E extraction/evidence/factor/calculation, missing-evidence execution, reset/preservation/
reseed, authenticated-user JWT/JWKS test, storage-isolation re-assertion, consultant-client parity
checks, idempotency and the §30 matrix. `uk-spend` = **UNSUPPORTED** (PO decision R-1);
B-3 outcomes = **EXPECTED PRODUCT BEHAVIOUR** (empirically verified).


The corrected corpus sweep was relaunched after the R-1/R-2 changes (detached, `real-extractor` probe,
sorted pool, chunk 30, cap 240) and had not finished at hand-off; consequently the §8 validation table,
the §19 seeding/§20–§21 calculation-reachability, the §23–§24 reset/reseed proof, §25–§26 authenticated
JWT and isolation re-assertion, §29 idempotency and the §30 matrix remain **NOT EXECUTED**. `uk-spend`
is **UNSUPPORTED** by the existing product for PDF documents (PO-recorded).


**DEMO-T3-REM-001 IMPLEMENTATION BLOCKED — PO REVIEW REQUIRED**

The single PO-level decision that unblocks the remainder is **R-1 (spend)**: whether the T3 spend
scenario should exercise an existing *supported* path (e.g. the tabular/spend-suggestion workflow or a
supported currency-based activity) or be recorded as unsupported for PDF documents. R-2 may then be
completed in-bound, followed by the validation table, B-3, seeding, calculation reachability, reset and
storage re-assertions.

Evidence classification for this continuation: items marked VERIFIED were executed and observed in this
session; the B-1/B-2/O-A/O-B implementations remain **PREVIOUSLY VERIFIED (implementer-run, pre-OHD)**
plus OHD-079's independent reproduction of the defects; everything in R-4 is **NOT VERIFIED**.
