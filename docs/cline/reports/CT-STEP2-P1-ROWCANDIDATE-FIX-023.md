# CT-STEP2-P1-ROWCANDIDATE-FIX-023 — Multi-Line PDF Row Candidate Detection Remediation

Task: `CT-STEP2-P1-ROWCANDIDATE-FIX-023`
Phase: Phase 8 / Step 2 Functional Remediation
Type: IMPLEMENTATION + TESTING + VERIFICATION + GIT BANKING
Owning agent: Cline

---

## 1. Task identity

Remediate defect `P1-B` established by `CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022`: the P1
row-candidate detector identified only **2** candidates in a PDF text layer that contains
**5** genuine activity rows.

Explicitly out of scope (per the task statement): the P1 rollout decision (activation
remains a PO decision), the AI fan-out architecture, OCR dependencies, Render
configuration and the Render memory incident.

## 2. Baseline

| Item | Value |
| --- | --- |
| Release branch | `p8-release-reconciled` |
| Forensic predecessor | `CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022`, report commit `3e7e25d` |
| Baseline SHA at task start | `3e7e25d` (== `origin/p8-release-reconciled`, tree clean) |
| P1 implementation under test | `backend/services/extraction_fidelity.py` (introduced by `f5e07ed`) |
| Working tree used | `/tmp/ct_step2` (`p8-release-reconciled`); the dirty `~/carbon_tally` main worktree was **not** modified |
| Test interpreter | `backend` pytest suite, `pytest tests/unit/...` |

## 3. Forensic evidence from `022` (the contract this task must satisfy)

```text
source PDF rows                 5
raw PDF text rows (text layer)  5      <- parser proven innocent
P1 hook invoked                 YES
P1 mode                         shadow
candidate_lines (persisted)     2      <- DEFECT
coverage                        2 / 5
first-loss boundary             _apply_p1_fidelity -> extraction_fidelity.classify
                                -> row-candidate detection
```

Oracle document: `multi_fuel.pdf`, job `9ef61662-1c0a-497a-b5e9-c179e2134784`,
doc `30f761c6-899d-450a-b744-87c389d6f972`. The verification in this task read the same
corpus file locally (**no production upload, no requeue, no production mutation**).

## 4. Root defect (mechanism)

`find_source_lines()` admitted a line only when `_has_unit(lowered)` matched one of:

```python
_UNIT_TOKENS = ("kwh", "mwh", "litre", "liter", "kg", "tonne", "ton ", "m3",
                "mile", "km", "night", "gbp", "£", "eur", "usd", "therm", "gallon")
```

as a **substring of the whole lowercased line**. The oracle document's five rows are:

| # | row | unit | pre-fix unit match |
| --- | --- | --- | --- |
| 1 | `Gas usage 5,362.2000 kWh €0.0670 €359.2700` | kWh | ✅ `"kwh"` |
| 2 | `Diesel supply 4,434.4000 L €1.6190 €7,179.2900` | L | ❌ no token |
| 3 | `Waste disposal 60 t €105.8140 €6,348.8400` | t | ❌ no token (`"ton"` ≠ `t`) |
| 4 | `Water supply 163.2000 m³ €2.0130 €328.5200` | m³ | ❌ `m3` ≠ superscript `m³` |
| 5 | `Power consumption 24,620.5000 kWh €0.1710 €4,210.1100` | kWh | ✅ `"kwh"` |

Two rows with `kWh` → **exactly the 2 candidates production persisted**. The defect was a
unit-vocabulary/encoding gap, not a row-splitting failure: the detector never had to split
rows (the text layer is one row per line) — it was **dropping** three complete rows because
their unit spelling was not expressible by the token list. A second, latent loss existed in
`build_line_items()`: a detected row with neither a canonical activity nor a unit was
`continue`d, i.e. silently discarded even though it had already been recognised as a
genuine source line.

## 5. Detector analysis (before editing)

* `find_source_lines(page_text)` — per physical line: length bounds (6–300), not invoice
  furniture, ≥3 alpha characters in the description, ≥1 number, `_has_unit()`, then the
  **first** non-zero number becomes the quantity.
* `classify()` — `candidate_lines = Σ len(find_source_lines(page))`; `MULTI_LINE_MIN_LINES = 2`.
* `build_line_items()` — same detection, then `activity`/`quantity`/`unit` plus provenance
  (`page`, `page_basis`, `page_trust`, `extraction_method`, `line_number`, `source_line`).
* Downstream (`automatic_extraction._make_extraction_result`) — in **shadow** mode only
  `classify()` runs (evidence/log only); `build_line_items()` is called only when
  `mode == MODE_ENABLED and multi_line_suspect`.

## 6. Implementation

File changed: `backend/services/extraction_fidelity.py` (single module, no new
dependencies, no schema change, no API change, no frontend change).

1. **Symbol/short unit vocabulary.** Added `_SHORT_UNIT_TOKENS` / `_SHORT_UNIT_SET`
   (`litres, litre, ltr, gallons, gallon, gal, tonnes, tonne, kg, kwh, mwh, m3, km, m, l, t`)
   with `_matched_short_unit()`.
2. **Superscript folding.** `_fold_units()` maps `³²¹` → `321` and `µ/μ` → `u`, so a
   text-layer `m³` matches the existing `m3` token. Applied to unit detection only — the
   stored `source_line` keeps the original glyph (`m³`) untouched.
3. **Structural admission rule (not keyword matching).** A row is a candidate when either
   * a long unit token is present anywhere (`_matched_unit`, unchanged semantics), **or**
   * the line carries **≥2 numeric columns** (quantity + rate/subtotal, i.e. table shape)
     **and** a short/symbolic unit occupies a real **unit column**: the token sits directly
     after the quantity token and is followed by the rate/subtotal token (or is the row's
     final token).

   Two guards are deliberately layered so selectivity is not weakened: the numeric-column
   count keeps prose out, and the unit-column adjacency keeps mangled fragments out.
4. **Quantity from the table structure.** `_quantity_column()` takes the number in the token
   **immediately preceding the unit column** (the way a table is read); the legacy
   first-number scan is the fallback when no unit column can be located. This closed a
   second fidelity hole the fix would otherwise have exposed: on
   `Diesel delivery - REF-89015 3,900 L $1.61 $6,294.60` the legacy scan returned
   `890.0` (digits of the reference code) — now `3900.0`.
5. **`unit_hint` provenance.** The recognised unit is returned on each found line and used
   by `build_line_items()` as `_detect_unit(raw) or unit_hint`, so a candidate carries its
   unit even when `_detect_unit()` (whole-string match) cannot resolve a full row.
6. **No silent row drop.** A detected row with no canonical activity/unit now keeps its
   literal `description` instead of being dropped (`P1-B`: a recognised source line must
   stay addressable). Records are otherwise unchanged.

Nothing was hard-coded for the oracle document: no activity names, no file names, no row
counts. The oracle row texts appear only in the **test fixtures**.

## 7. `multi_fuel.pdf` regression

| Stage | Evidence | Result |
| --- | --- | --- |
| Text layer (local `pdfplumber`) | 5 rows on page 1, ~569 chars, 2 pages | 5 rows present |
| `find_source_lines()` per line | exactly 5 `HIT`s, every other line rejected | ✅ |
| `classify().candidate_lines` | `5`, `multi_line_suspect = True`, reason `"5 candidate source lines"` | ✅ (was `2`) |
| `build_line_items()` | `line_items = 5`, `coverage.line_items = 5`, `candidate_lines = 5` | ✅ (was 0 items / flat record) |
| Independent corpus sweep (576 PDFs) | `multi_fuel.pdf` before = 2, after = 5 | ✅ |

## 8. Candidate count before / after

```text
                              before (baseline 3e7e25d)   after
candidate_lines               2                          5
line_items (enabled path)     0 (flat record)            5
coverage.line_items           n/a                        5
```

## 9. Candidate identity verification

```text
1  Gas usage          qty 5362.2   kwh   activity "Natural gas"
2  Diesel supply      qty 4434.4   l     activity "Diesel"
3  Waste disposal     qty 60.0     t     activity "Waste"
4  Water supply       qty 163.2    m3    activity "Water"
5  Power consumption  qty 24620.5  kwh   (no canonical activity match; literal text kept in source_line)
```

Source order is preserved (`line_number` 1–5; the `source_line` sequence equals the table
order), and each candidate retains `source_line` (verbatim, `m³` glyph intact), `quantity`,
`unit`, `page = 1`, `page_basis = document`, `page_trust = standard`,
`extraction_method = det:pdf_text`. No page number was invented: with no page boundary in
the text layer the basis is honestly reported as `document`.

## 10. Quantity / unit preservation

| Row | quantity | unit | unit source |
| --- | --- | --- | --- |
| Gas usage | 5362.2 | `kwh` | long token `kwh` (unit column adjacent to quantity) |
| Diesel supply | 4434.4 | `l` | short token `l` (unit column, followed by the rate column) |
| Waste disposal | 60.0 | `t` | short token `t` |
| Water supply | 163.2 | `m3` | superscript-folded `m³` → `m3` |
| Power consumption | 24620.5 | `kwh` | long token |

Additional fidelity evidence introduced **by** the fix (corpus `border_decorative_fuel.pdf`):

```text
before:  Diesel delivery - REF-89015 3,900 L ...   quantity 890.0   <- reference-code digits
after:   Diesel delivery - REF-89015 3,900 L ...   quantity 3900.0  <- quantity column
```

A candidate's `source_line` keeps the verbatim text (including `m³`), so the unit hint is
traceable back to the source. No unit and no quantity is synthesised: both come from the
source row's own columns; where no unit column can be located the conservative path is
unchanged (no candidate).

## 11. Negative tests (no over-detection)

Rejected by the detector on the oracle document (each asserted):

```text
Description Qty Unit Rate Subtotal      Subtotal: €18,426.0300
Sales Tax: €3,685.2000                  Net Payable: €22,111.2300
Ref No.: PWR/2026/8130                  Date: May 08, 2026
Period: Apr 01, 2026 – Apr 30, 2026     Buyer: Power Power & Co
967 Renewable Road                      IV47 7UK
Pure Energy PLC / FUEL INVOICE          Terms: Net 30 days.
For testing purposes only (page 2)
```

`Subtotal`, `Sales Tax` and `Net Payable` are rejected by the existing furniture list plus
the structural gate (a single amount column with no unit column is not a row). Also
asserted as *not* candidates: a row with no unit column (`Standing charge 45 45.0000`), a
number-without-unit line (`Electricity 12,500 2,340.00`) and prose containing a stray
`t`/`l` word (`We reviewed the site t 12 times …`). Only the five genuine activity rows are
ever admitted from the whole document (asserted exhaustively, line by line).

## 12. Synthetic corpus regression

Existing corpus (unmodified, not regenerated): 576 PDFs under
`~/carbon_tally_synthetic_documents/output_all_variations/documents`, run through the
detector before/after (`_has_unit` legacy gate vs the new detector, per page):

```text
files scanned                                    576
files where candidate count DECREASED             0     <- no regression
files where candidate count CHANGED              42     <- all increases
scan_light_gas.pdf (OCR-only, empty text layer)  0 -> 0
multi_fuel.pdf                                   2 -> 5
border_decorative_fuel.pdf                       0 -> 3
color_01_fuel.pdf                                0 -> 3
diff_edge_waste.pdf                              0 -> 5
diff_difficult_water.pdf                         0 -> 4
```

Every increase was inspected at line level: each new candidate is a genuine
`description + quantity + unit (+ rate/subtotal)` row (`Diesel delivery … 3,900 L $1.61`,
`Recycling services 53 t $158.86`, `Water supply 236.6600 m³ €2.0340`, nested-list
`diff_edge_waste`) — no prose, no total, no fabricated row.

**Iterative finding during this task (recorded for honesty).** The first version of the
short-unit rule accepted a mangled text-layer fragment in `edge_trav.pdf`
(`Period: 20T26-01-01 – 2026-01-31 T T` → false candidate). Rather than accept an
over-detection, the rule was tightened to require a real **unit column** (token directly
after the quantity and followed by the rate/subtotal column, or final in the row); the
false positive disappeared and the genuine mileage rows in the same document were kept.
Corpus result after tightening: still 0 decreases, 42 increases, and the two previously
mis-flagged files (`edge_trav.pdf`, `diff_edge_gen.pdf`) revert to their legacy counts.

## 13. P1 contract preservation

* one source line → one candidate line (unchanged 1:1 mapping);
* source order preserved (`line_number`);
* genuine page information only — no fake page numbers, `source_page` semantics untouched;
* no positional deterministic/AI blending introduced (not touched by this change);
* no fabricated quantity/unit (both read from the row's own columns);
* no placeholder lines, no silent lossy fallback — the previous silent `continue` of a
  detected row was removed;
* `MULTI_LINE_MIN_LINES`, `PAGE_CAP`, `CLIP_CHARS`, the `P1-D2` block and the `P1-D8`
  stamps are unchanged.

## 14. Shadow rollout preservation

`shape_mode()` and `rollout_status()` were **not** modified. Asserted in the new suite:
`shape_mode(env={}) == "shadow"`, `enabled` without an allowlist still resolves to
`shadow`, `rollout_status(env={})["in_rollout"] is False`. In shadow mode the fix changes
only the **evidence** (`candidate_lines` 2 → 5, `reasons`), exactly as `P1-D1` requires:
detection is measured, not applied. No rollout policy, allowlist or environment default was
touched.

## 15. AI fan-out impact

None. `ai_fanout_plan()` and its inputs are unchanged; for the oracle document the plan
remains `per_page_ai = False, pages = 0` (the text layer is inside the 20 000-char clip).
No AI call limit, timeout, retry count or parsing behaviour was modified, and no AI parsing
was added.

## 16. Flat-record boundary

`POST-CANDIDATE` observation (documented, **not** fixed here): in `enabled` mode the shape
now contains 5 line items, but a candidate whose canonical activity cannot be matched
(`Power consumption` → no `_detect_activity` keyword) carries quantity + unit +
`source_line` and no `activity`/`description` field, because `record["description"]` is only
added when both activity and unit are missing. This is a keyword-coverage matter downstream
of candidate detection, within the existing `unresolved` mechanism, and out of scope for
this defect. The `P1-D2` block remains the governed behaviour when items cannot be built.

## 17. Test results

Run from `/tmp/ct_step2/backend`, in the staged order the task requires:

| # | Command | Result |
| --- | --- | --- |
| 1 | `python -m pytest tests/unit/services/test_p1_row_candidates_multiline.py -q` | **48 passed**, exit 0 |
| 2 | `python -m pytest tests/unit/services -q` (all P1/service suites) | **238 passed**, exit 0 |
| 3 | `python -m pytest tests/unit -q` (broader unit regression) | **2510 passed**, exit 0 |
| 4 | corpus sweep, 576 PDFs (before/after detector) | 0 decreases, 42 increases, `multi_fuel.pdf` 2 → 5 |
| 5 | line-level evidence dumps (`multi_fuel.pdf`, `border_decorative_fuel.pdf`, `color_01_fuel.pdf`, `diff_edge_waste.pdf`, `diff_difficult_water.pdf`, `edge_trav.pdf`) | all candidates genuine rows |

Interpretation notes: **no pre-existing failures were observed** in any suite, so nothing had
to be classified as pre-existing; the only pytest output besides passes is an unrelated
`RequestsDependencyWarning` (urllib3/chardet version notice) from
`test_efe_selection_sites.py`. Integration suites were deliberately **not** run: their
`conftest.py` performs destructive `TRUNCATE … RESTART IDENTITY CASCADE` (`F-046-1`), and
this task requires no database mutation — no database was contacted.

New suite coverage mapping (`backend/tests/unit/services/test_p1_row_candidates_multiline.py`,
48 tests): Test 1 oracle (text layer + real PDF), Test 2 order, Test 3 quantity/unit,
Test 4 furniture/prose rejection, Test 5 single-line, Test 6 standard multi-line table,
Test 7 difficult/edge fixtures, Test 8 OCR-marker parity, Test 9 shadow rollout,
Test 10 prose guard, Test 11 quantity column (added while fixing the ref-code finding).

## 18. Production-data safety

```text
uploads created: 0            production documents re-uploaded: 0        jobs requeued: 0
jobs retried: 0               jobs unlocked: 0                           jobs cancelled: 0
production extraction results modified: 0    production test jobs created: 0
database writes: 0            schema changes: 0                          migrations: 0
P1 rollout changes: 0         Render configuration changes: 0             deployments: 0
```

`multi_fuel.pdf` was read **locally** from the read-only synthetic corpus
(`~/carbon_tally_synthetic_documents/output_all_variations/documents/multi_fuel.pdf`); the
production copy, the production job `9ef61662-1c0a-497a-b5e9-c179e2134784` and the production
document `30f761c6-899d-450a-b744-87c389d6f972` were **not touched**, not requeued and not
retried. Production verification of this fix is deferred to a separate post-deployment task.

## 19. Git commits

Branch: `p8-release-reconciled` (all commits pushed to `origin`).

| Commit | Type | Content |
| --- | --- | --- |
| `06add05` | implementation | `fix(p1): candidate-detect table rows with short/symbolic units (P1-B)` — `backend/services/extraction_fidelity.py`, 1 file, +123/−16 |
| `a8d59f0` | tests | `test(p1): lock multi-line row-candidate detection on the multi_fuel oracle` — new suite, 1 file, +332 |
| `86458e7` | implementation + test | `fix(p1): treat 'payable' as invoice furniture and lock it in tests` (small follow-up found while writing this report: `Net Payable: £…` could otherwise satisfy the currency-token gate) |
| *(this report)* | document | `docs/cline/reports/CT-STEP2-P1-ROWCANDIDATE-FIX-023.md` |

Sequencing note: commit B was banked before the small A2 follow-up, so the history is
A → B → A2 → report. Every commit was pushed and verified against `origin`.

## 20. Final SHA / deployment

| Item | Value |
| --- | --- |
| Baseline | `3e7e25d` |
| Implementation commit | `06add05` (+ `86458e7`) |
| Test commit | `a8d59f0` (+ test additions in `86458e7`) |
| Report commit | the commit that adds this file (SHA stated in the completion response) |
| Final HEAD | == `origin/p8-release-reconciled`, working tree clean |

**Deployment: NOT PERFORMED.** Git push is not production deployment, and no authorised
automatic deployment mechanism was invoked from this task (and this task must not be combined
with the Render memory workstream). The Render service `carbontally-api` therefore still runs
the previously observed release (`e88b394` per the `019`/`022` evidence), which means
**production still reports the old behaviour (2 candidates) until a deployment occurs**;
production runtime verification of this fix is consequently **UNVERIFIED** and belongs to a
separate, bounded post-deployment verification task. The existing blocked production job must
not be requeued as a shortcut.

## 21. Remaining limitations

1. **Production runtime verification unavailable** (no deployment performed; see §20). The
   fix is verified locally against the oracle, the corpus and the unit suites only.
2. **Quantity fidelity in garbled text layers.** Quantity now comes from the token left of the
   unit column, which fixed the reference-code class (`REF-89015 → 3900.0`), but where the
   text layer itself is corrupt the number can still be wrong: in
   `diff_difficult_water.pdf`, `Water charges T I211.1700 m³ …` yields `2.916`
   (the rate) and `Water charges 30L9.0600 m³ …` yields `30.0`, because the quantity digits
   are glued to stray letters/characters. Row *detection* for that document is fixed (0 → 4
   candidates); the residual is a text-layer-quality/column-reconstruction matter tracked
   below as a proposed follow-up — it is **not** claimed as solved.
3. **`Power consumption` has no canonical activity** (`_detect_activity` keyword coverage) —
   the candidate retains quantity/unit/`source_line`; this is a `POST-CANDIDATE` matter (§16).
4. **`Net Payable` now rejected currency-independently** (`payable` added to `_FURNITURE`,
   `86458e7`). Other single-amount furniture lines that carry no furniture keyword and no unit
   column are rejected structurally (single amount column), so no general weakness is claimed;
   the guard remains the row-shape rule.
5. **No change to page semantics** (`source_page`, `page_basis`) — deliberately out of scope,
   as instructed.
6. **Corpus sweep is text-layer only** (pdfplumber text extraction): it measures the detector,
   not the OCR/image path; `scan_light_gas.pdf` has an empty text layer and is unaffected
   (0 → 0), as expected.

Proposed follow-ups (documented, **not started**): post-deployment production verification of
`023`; a bounded quantity-column improvement for corrupt text layers; optional `_detect_activity`
keyword coverage review.

## 22. Render memory incident — separate workstream (explicitly recorded)

While this task was in flight, the operator reported a **separate real infrastructure event**:
Render Web Service `carbontally-api` exceeded its memory limit and was automatically restarted.

* This task did **not** investigate, remediate or touch it. No Render instance size, memory
  limit, worker concurrency, OCR configuration, timeout, memory-management code or Render
  setting was changed, and the service was not restarted by this task.
* **No causal link to `multi_fuel.pdf` is assumed.** This change adds only line-level
  pure-Python scanning over text already held in memory; it introduces no new dependency, no
  large structure, no thread and no background work, so it does not plausibly change memory
  behaviour either way. Memory causality remains unestablished.
* The event belongs to the separate forensic workstream already named by the task statement:
  `CT-STEP2-RENDER-MEMORY-FORENSIC-024` (OCR / ONNX Runtime / pypdfium2 / concurrency /
  threads / leak / traffic / sizing / lifecycle). **Not started from here**, and its report
  path must not be written by this task.

## 23. Final verdict

### `IMPLEMENTED + VERIFIED + BANKED`

Justification against the task's own conditions:

| Condition | Evidence |
| --- | --- |
| row-candidate defect fixed | unit vocabulary/encoding gap closed; structural unit-column rule; no silent row drop (§4–§6) |
| `multi_fuel.pdf` produces five correct candidates | 2 → 5 candidates; 5 line items with correct order, quantity and unit (§7–§10) |
| focused tests pass | 48 passed (§17) |
| relevant regressions pass | `tests/unit/services` 238 passed; `tests/unit` 2510 passed; 576-file corpus sweep with **0 decreases** (§12, §17) |
| rollout remains correctly gated | `shape_mode`/`rollout_status` untouched, shadow default asserted (§14) |
| all modifications committed and pushed | `06add05`, `a8d59f0`, `86458e7` + this report (§19) |
| local == remote, tree clean | verified after each push (§20) |

Production verification is **not** part of this verdict: it is deployment-dependent and is
explicitly deferred (deployment **NOT PERFORMED**, production runtime **UNVERIFIED**).
`CT-STEP2-RENDER-MEMORY-FORENSIC-024` was **not** started, P1 remains in `shadow`, and
`CT-STEP2-ACCEPT-007` was **not** resumed.



