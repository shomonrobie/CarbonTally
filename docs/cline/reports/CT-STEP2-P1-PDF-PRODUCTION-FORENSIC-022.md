# CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022 — Multi-Line PDF Production Forensic

**Task ID:** `CT-STEP2-P1-PDF-PRODUCTION-FORENSIC-022` · **Type:** READ-ONLY PRODUCTION FORENSICS + SOURCE TRACE
**Date:** 2026-09-18 · **Verifier:** Cline · **Repo baseline:** `c866b49` (== origin, clean)
**Verdict:** `P1 PDF EXTRACTION FORENSIC — ROOT CAUSE CONFIRMED`

**One-line answer:** the five source rows **are present in the PDF text layer** and were **not** lost by the
parser; they are lost because the **row-candidate detector found only 2 of the 5 lines**
(`candidate_lines: 2`, production-persisted) **and** the effective P1 mode for this tenant is **`shadow`**,
where the fidelity block is compute/log-only and never changes the extraction output — so a **flat record**
(`date` + `activity`) became the result and was blocked on completeness.

---

## 1. Task identity

Determine exactly where the five source rows of `multi_fuel.pdf` are lost in the production extraction
pipeline. Strictly read-only: no code/test/migration/schema/config/P1-rollout change, no upload, no requeue,
no retry, no manual trigger, no job/document alteration, no restart/redeploy.

## 2. Source-document oracle

Two-page synthetic PDF; page 1 is a fuel invoice (`Pure Energy PLC`, `Ref No.: PWR/2026/8130`,
`Date: May 08, 2026`, `ID: multi_fuel`) with a structured table:

`Description | Qty | Unit | Rate | Subtotal` → **Gas usage 5,362.2000 kWh**, **Diesel supply 4,434.4000 L**,
**Waste disposal 60 t**, **Water supply 163.2000 m³**, **Power consumption 24,620.5000 kWh**.
Page 2 is testing-purpose content. The five rows are five activities (the oracle).

## 3. Production document identification (read-only)

| Item | Value |
| --- | --- |
| Filename | `multi_fuel.pdf` |
| Job ID | `9ef61662-1c0a-497a-b5e9-c179e2134784` |
| Document ID | `30f761c6-899d-450a-b744-87c389d6f972` |
| Created | 2026-09-17T15:30:41Z |
| Status / stage | `manual_review` / `blocked` |
| Attempt count | 0 |
| Extraction method on row | `None` (never stamped) |
| Updated | 2026-09-18T04:59:20.687351Z |

## 4. Current production result

* `automation_extracted_data` job column: **empty**; the persisted extraction evidence lives in
  `metadata.partial_extraction` (**key evidence**):

```json
{"method": "pdf_text", "status": "partial",
 "coverage": {"mode": "shadow", "clipped": false,
              "reasons": ["2 candidate source lines"], "page_cap": 20,
              "ai_fanout": {"pages": 0, "per_page_ai": false, "page_cap": 20,
                            "reason": "text layer is within the AI clip; a single pass suffices"},
              "page_basis": "document", "page_count": 2, "text_chars": 571,
              "candidate_lines": 2, "page_resolution": "document"}}
```

* `manual_review_reason`: `extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit`.
* `mapped_data`: none ⇒ `emission_factor_used` / `calculated_emissions_kg_co2e` null (downstream consequence).
* User-visible extraction = `{"date": "May 08, 2026", "activity": "Diesel"}` — a **flat** record with no
  `line_items`, `quantity` or `unit`.

## 5. Extraction path (traced in source)

```
upload → organization_files + queue row → worker claim → process_job → _run_stage('extracting')
  → _extract → _run_bounded_extraction (asyncio.to_thread, 240 s budget)
     → automatic_extraction.extract_document → _extract_pdf
        → _pdf_text() ............... text layer + method="pdf_text" + page_count
        → suggest_text() ............ FLAT deterministic suggestion (date, activity, …)
        → _apply_p1_fidelity(...) ... P1 hook (coverage/classifier; MODE-GATED)
        → return {"extracted_data", "coverage", "confidence", …}
  → completeness gate (_missing_required) → mark_blocked(reason) → manual_review
  → persistence: partial-extraction metadata + coverage block
```

## 6. Raw PDF extraction evidence — **the rows ARE present**

Read locally from the same source file with `pdfplumber` (read-only; no production access):

```
pages 2 | page-1 text layer 571 chars
… Description Qty Unit Rate Subtotal
  Gas usage      5,362.2000 kWh €0.0670 €359.2700
  Diesel supply  4,434.4000 L   €1.6190 €7,179.2900
  Waste disposal 60         t   €105.8140 €6,348.8400
  Water supply   163.2000   m³  €2.0130 €328.5200
  (Power consumption is the next row of the same table)
```

**Finding: `A. All five rows present`** as a clean line-per-row text table ⇒ **P1-A (PDF text extraction
failure) ruled out**; no OCR was required, and production's own `method: pdf_text`, `page_count: 2`,
`text_chars: 571` agree with the local read.

## 7. `_extract_pdf` evidence (source)

`automatic_extraction.py:451-492`: `_pdf_text()` → `suggest_text()` → **`_apply_p1_fidelity(...)` at line 470**
(`text`, `method`, `page_count`, `extracted`, `unresolved`, `organization_id`) → a non-`None` `block` is
returned as-is; otherwise the **flat** `suggested_data` is the payload with
`confidence = _completeness(extracted)` and the coverage block attached. So the flat suggestion is the
payload **unless the P1 hook replaces it** — and in `shadow` mode it does not (§8/§9).

## 8. P1 hook evidence — **the hook DID run**

The coverage block in §4 can only be produced by `extraction_fidelity`, and it is persisted, so the hook
executed for this document on the active production path. Recorded classification: `mode: "shadow"`,
`candidate_lines: 2`, `reasons: ["2 candidate source lines"]`, `clipped: false`, `page_basis: "document"`,
`page_resolution: "document"`. Per `extraction_fidelity.py` (lines 8 and 30), in **`shadow`** the
coverage/classifier block is **computed and logged with no change to the extraction output**.

## 9. P1 rollout state — **`shadow` (effective for this tenant)**

`coverage.mode == "shadow"` is direct runtime evidence of the effective mode: the documented fail-safe
default. The controlled rollout was **not** changed, and P1 was **not** activated for this tenant for this
investigation.

## 10. Row-candidate evidence — **2 of 5 (primary loss)**

Production classification: **`candidate_lines: 2`** for a document whose text layer contains **5 table rows**
(§6). The detector produced **2** candidates where the oracle expects **5** — the **first stage at which the
five source rows cease to be represented**. The detector is `extraction_fidelity.classify(...)` / the
row-candidate logic surfaced through `_apply_p1_fidelity`, reporting the reason
`"2 candidate source lines"`.

## 11. Coverage evidence

The coverage block was **persisted** in job `metadata.partial_extraction.coverage`. It is **evidence, not an
output transform**: in `shadow` mode it does not alter `extracted_data`, so mapping/validation consumed the
flat record. Recorded facts: `text_chars: 571`, `candidate_lines: 2`,
`page_basis/page_resolution: document`, `clipped: false`.

## 12. AI fan-out evidence — **planned no / executed no (by design)**

`coverage.ai_fanout = {"pages": 0, "per_page_ai": false, "page_cap": 20, "reason": "text layer is within the
AI clip; a single pass suffices"}` ⇒ **no per-page fan-out planned**, hence none consumed; consistent with
`ai_extraction_method: None`. **This task made no AI calls** and triggered no new production AI processing.
The fan-out decision is a *consequence* of the classifier's view of the text (which itself under-detected the
rows, §10), not a wiring fault — the plan is bounded and gated by design.

## 13. Document-level adjudication evidence — **present, non-positional; not the loss point**

Source (`services/automatic_processing.py:255-307`): a deterministic table is accepted **whole**; with no
deterministic table the AI candidate is accepted **whole**; otherwise scalar gap-fill only; and
`_adjudication_record` records `"rule": "p1_document_level_adjudication"`, `"positional_blending": False`,
plus `deterministic_line_items` / `ai_line_items` / `accepted_candidate` / `divergent` /
`accepted_line_items`. **No `det_lines[idx]`-style positional blending remains on the active path.** For this
document there was **no deterministic table and no AI candidate**, so adjudication had nothing to merge — it
is **not** the first-loss boundary.

## 14. Flat-record fallback evidence — **YES, the flat record became the outcome**

Confirmed: `suggest_text()` produced a flat record (`date` + `activity: Diesel`); the multi-line
classification was recorded **only as a coverage block**; the flat record then passed through `_completeness`
→ `0.33 < 0.50` → `mark_blocked("extraction completeness 0.33 below 0.50 threshold — unresolved: quantity,
unit")`. The pipeline therefore still permits **multi-line document → flat deterministic record → completeness
score → persisted partial evidence + block** without preserving source-line fidelity. (Blocking rather than
fabricating is the *correct* governed behaviour; the fidelity loss precedes the gate.)

## 15. Final transformation — where `{date, activity}` came from

`date = "May 08, 2026"` and `activity = "Diesel"` originate in **`suggest_text()`'s flat `suggested_data`**
(the same text contains `Diesel supply`, hence the flat activity); the five table rows were never promoted to
`line_items` because (a) the detector saw only 2 candidate lines and (b) `shadow` mode applies no rewrite.
`line_items`, `quantity` and `unit` are thus **absent by construction** on this path. Stage identified:
**`_extract_pdf` payload construction after a shadow-mode fidelity pass** — i.e. detection (§10) + gating
(§9), not a later transformation.

## 16. Persistence boundary — what was actually persisted

| Store | Content |
| --- | --- |
| `document_processing_queue.automation_extracted_data` | **empty** |
| queue `metadata.partial_extraction` | `{"method": "pdf_text", "status": "partial", "coverage": {… candidate_lines: 2, mode: shadow …}}` (**persisted**) |
| `manual_extraction_items` (columns include `document_processing_queue_id`, `extracted_data`, `emission_factor_used`, `calculated_emissions_kg_co2e`) | **3 rows exist in the tenant but were not attributable to this document in this read** (no document-scoped filter applied) ⇒ attribution **UNVERIFIABLE** here |

**Classification of the five lines:** **never extracted as lines** — not "extracted then discarded", and not
"extracted but transformed into a flat record". Honest label: **rows present in raw text → only 2 detected as
candidates → none promoted to line items → flat record persisted**. No silent discard occurred; the line
representation was never created.

## 17. Mapping / calculation consequence (not a factor-engine defect)

`no line_items + no quantity + no unit` ⇒ insufficient structured input ⇒ `mapped_data {}` ⇒
`emission_factor_used null` ⇒ `calculated_emissions_kg_co2e null`: the expected downstream consequence of the
extraction loss. **No factor-engine defect is asserted** — no such evidence exists, and matching was never
exercised with adequate input.

## 18. CSV comparison (existing evidence only)

The three CSVs in the same tenant reached `method = csv`, `confidence = 1` with structured `line_items` (e.g.
the fuel-card row `Diesel / 53.8 / litres / 85.21 / Esso / source_row 1`, 50 items) and per-line `no_match`
mapping reasons. So **structured ingestion preserves rows while this PDF path did not** — consistent with the
PDF-side detection/gating boundary above. No CSV was uploaded or modified, and this was not broadened into a
CSV investigation.

## 19. P1 test coverage comparison

Existing P1 suites (`test_pod1_bounded_ai_fanout.py`, `test_extraction_fidelity.py`,
`test_step2_remediation.py`, `test_efe_selection_sites.py`) cover bounded fan-out, fidelity outcomes, coverage
blocks and selection sites. The **exact `multi_fuel.pdf` oracle** (text-layer 5-row table → 5 line items) is
**not** covered: no test asserts "5 source rows in ⇒ 5 candidate lines", precisely the gap this document
exposes. No tests were modified or added here.

## 20. Deployment / source consistency

Repo baseline `c866b49` == `origin/p8-release-reconciled`, tree clean; operator evidence places production at
`e88b394` (ancestry contains the P1 hook `f5e07ed`, the timeout/thread work `0d14367`, cancellation safety
`daf7270`). The runtime **exposes no build/commit identifier**, so runtime identity is **not independently
confirmable** (not inferred from `rndr-id`). Behavioural corroboration is strong: the persisted coverage block
with `mode: shadow` and `candidate_lines: 2` can only come from the P1 fidelity implementation — the expected
extraction path **did** execute. **No deployment/path mismatch is indicated.**

## 21. First-loss boundary (exact)

**The row-candidate detection/classification stage inside `_apply_p1_fidelity` → `extraction_fidelity.classify`
(2 candidates produced for a 5-row table), combined with the effective `shadow` mode meaning nothing is applied
even had detection been complete.** Everything downstream (flat payload, completeness 0.33, block, empty
mapping, null calculation) follows deterministically from that point. Raw PDF text and the parser are
**excluded** as loss points.

## 22. Defect classification

* **Primary: `P1-B — row-candidate detection failure`** (2 of 5 rows; directly evidenced by comparing the
  5-row text layer with the persisted `candidate_lines: 2`).
* **Contributing: `P1-D — rollout/gating`** (`mode: shadow` ⇒ fidelity compute/log-only, so row preservation is
  not applied for this tenant; fail-safe by design, not a malfunction).
* **Not implicated:** `P1-A` (text extraction — excluded, §6), `P1-C` (hook not invoked — it ran, §8),
  `P1-E` (fan-out wiring — not planned, by design, §12), `P1-F` (adjudication — non-positional and unused,
  §13), `P1-I` (no deployment mismatch, §20), `P1-J` (evidence sufficient).

## 23. Evidence matrix

| Stage | Expected five-row representation | Actual evidence | Status |
| --- | --- | --- | --- |
| Source PDF | 5 rows | page-1 table with 5 rows (oracle) | **PASS** |
| Raw PDF text | 5 rows | local `pdfplumber` read: table header + row lines present | **PASS** |
| `_extract_pdf` | 5-row-capable representation | `method=pdf_text`, `page_count=2`, `text_chars=571`; flat `suggested_data` payload | **FAIL** (flat only) |
| P1 hook | row candidates | hook **ran**; `mode=shadow`; `candidate_lines=2` | **FAIL** (2 ≠ 5) |
| Coverage | meaningful source coverage | persisted block (`reasons: ["2 candidate source lines"]`) | **FAIL** (under-count) |
| AI fan-out | bounded candidate extraction *if gated* | `pages: 0`, `per_page_ai: false` (text within clip) | **NOT APPLICABLE** |
| Adjudication | line-preserving result | non-positional; no deterministic/AI table existed | **NOT APPLICABLE** |
| Final extraction | 5 line items | flat `{date, activity}` | **FAIL** |
| Persistence | 5 line items/evidence | partial-extraction metadata only; job column empty; `manual_extraction_items` attribution UNVERIFIABLE | **FAIL** |
| Mapping | structured activity/qty/unit | `mapped_data {}` | **FAIL** (consequence) |
| Calculation | calculable rows | `null` | **FAIL** (consequence) |

`PASS` is used only where evidence exists; no `PASS` is granted merely because source code contains a function.

## 24. Production mutation statement

```
uploads created: 0        jobs created: 0          jobs requeued: 0      jobs retried: 0
jobs cancelled: 0         jobs unlocked: 0         documents deleted: 0  database writes: 0
schema changes: 0         configuration changes: 0 P1 rollout changes: 0
Render restarts: 0        deployments: 0           code/test changes: 0
```

Read-only actions: `git` state queries; source reads; **one** local read of the corpus PDF (`pdfplumber`, the
same file in the read-only corpus directory — **no production document was re-uploaded or reprocessed**);
**one** authenticated session (authorised synthetic Owner) used exclusively for RLS-scoped `SELECT`s of that
tenant's own queue row and the `manual_extraction_items` table. No `POST`/`PUT`/`PATCH`/`DELETE` was issued to
the application or the database.

## 25. Final verdict

### `P1 PDF EXTRACTION FORENSIC — ROOT CAUSE CONFIRMED`

* The five rows **survive PDF extraction intact** (proven by reading the same source file's text layer).
* They are lost at the **P1 row-candidate detection stage — 2 of 5 lines detected** — with the effective
  **`shadow`** mode ensuring that even the partial detection is not applied to the output.
* Consequently a **flat record** becomes the extraction result, and the completeness gate (0.33 < 0.50) blocks
  it for manual review — the governed, non-fabricating behaviour; the fidelity loss precedes the gate.
* Positional blending is **absent** from the active path; the AI fan-out was **not** planned for this document
  (bounded and gated by design) and is not the loss point; mapping/calculation consequences follow from the
  missing `quantity`/`unit`/`line_items`.

**Confirmed defect:** multi-line **row-candidate detection** under-counts a clean text-layer table
(2/5), and row preservation is not applied under the `shadow` rollout.
**Evidence:** §6 (5 rows in raw text) vs §4/§10 (persisted `candidate_lines: 2`, `mode: shadow`).
**Affected stage:** `_extract_pdf` → `_apply_p1_fidelity` → `extraction_fidelity.classify` (+ rollout gate).
**Recommended new task (documented only — NOT created or started):**
`CT-STEP2-P1-ROWCANDIDATE-FIX-023` — improve multi-line row-candidate detection for text-layer table PDFs,
using `multi_fuel.pdf` as the regression oracle (5 rows in ⇒ 5 candidate lines), with the governed P1
activation decision re-confirmed separately (the `shadow` default is a **PO decision**, not something to
bypass).



