# CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037

**Task ID:** `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037`
**Title:** Separate Workstream P1 (PDF/IMAGE Extraction Fidelity) — **authorisation / decision package**
**Task type (per the master playbook):** **F/E — decision package only**
**Date:** 2026-09-13
**Governing instruction:** `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049` line 193 ("Authorise `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037` (decision package only)") · PO blanket authorisation `…050` · explicit PO instruction to execute `…037`
**Environment:** local non-production development tree + `carbontally_qa_phase8` inspection only — **no production access, no production data or storage writes, no historical backfill/re-extraction**
**Baseline:** `main` · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · no commits

---

## 1. Scope executed

`…037` is defined by the playbook as a **P1 decision package with no decision prerequisite** — its gate is authorisation only, and that authorisation is now held (`…050` + the explicit instruction). Accordingly this task:

1. **re-verified** every load-bearing forensic fact in the P1 contract `…020` against the **current** tree and runtime;
2. established whether later batches (B2/B3/B4) changed anything in the extraction path;
3. produced the **P1 Authorisation & Decision Package** — the `P1-D1…P1-D8` register in PO-answerable form, the exact authorisation requested, the gate-evidence plan and the verification requirements;
4. verified the P1 **baseline** is green so an authorised implementation starts from a known-good state.

**No implementation was performed** — implementing extraction fidelity is P1 proper and is gated on the `P1-D1` authorisation this package requests.

## 2. Sources inspected

| Source | Used for |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md` (889 lines, task `…020`) | the P1 boundary, forensic findings FM-1…FM-7, the `P1-D1…P1-D8` register, gate/rollout plan (§16–§18), test-amendment list (§16.3) |
| `docs/cline/reports/CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049.md` | task definition, `…037` gate, `D-15` (P1 implementation ⇒ `P1-D1…P1-D8`) |
| `backend/services/automatic_extraction.py`, `services/automatic_processing.py`, `services/ai_document_extraction.py`, `engines/ai_extraction.py`, `data/evidence_line_items.py`, `backend/pdf_engine.py`, `backend/routes/upload.py` | live verification of V1–V5 |

## 3. Fresh verification evidence (executed this task)

| # | Claim re-verified | Result |
|---|---|---|
| **V1** | a per-source-line producer exists only for **tabular** documents | `services/automatic_extraction.py`: `_rows_to_line_items(...)` + `line_items.append(...)` (CSV/XLSX row path); no PDF/IMAGE per-line producer |
| **V2** | the AI text clip persists and is **duplicated** | `services/ai_document_extraction.py:39` **and** `engines/ai_extraction.py:43` both define `DEFAULT_MAX_TEXT_CHARS = 20_000` |
| **V3** | page semantics are document-level, not per line | `services/automatic_processing.py:1151` — `source_page=job.metadata.get("page_count")`; no per-line `page` producer |
| **V4** | the deterministic+AI blending path is as `-020` describes | `services/automatic_processing.py:166–188` — `det_lines` + `ai_lines` → `merged_lines` |
| **V5** | the legacy parallel extraction/emissions surface still exists | `backend/pdf_engine.py` and `backend/routes/upload.py` present and reachable |
| **V6** | the P1 baseline is **green** | `pytest` on `test_automatic_extraction`, `test_automatic_extraction_text_layer`, `test_automatic_processing`, `test_ai_document_extraction`, `engines/test_ai_extraction`, `engines/test_extraction`, `engines/test_extraction_suggestions` → **85 tests, EXIT=0** |
| **V7** | the extraction **fidelity behaviour** is unchanged since `-020` | `line_items` is still tabular-only, the clip is still `20_000` in two modules, `source_page` is still `page_count`. **Precision (correction):** `backend/services/automatic_processing.py` does carry **pre-existing, uncommitted B2-era modifications** (`source_line_item_id` ordinal→line **lookup** under B2 §13.2, plus a `method_stamp` argument on `save_extracted_data`) — 19 insertions/1 deletion versus HEAD. Those are **provenance plumbing added by B2**, not extraction-fidelity changes: they resolve an existing line id for the tabular path and never create a per-line producer for PDF/IMAGE. They were part of the standing 219 tracked modifications throughout the B4 work, and **this task changed nothing** in any extraction file. |

**Conclusion:** every forensic precondition the P1 contract rests on is **still true**, no `P1-Dn` decision has become moot or been overtaken by later batches, and the P1 surface starts from a verified green baseline.

## 4. Deliverable

**`docs/architecture/CARBONTALLY_PHASE8_P1_AUTHORISATION_DECISION_PACKAGE_20260913.md`** (§0–§9):

* the P1 one-sentence definition and the binding root boundary (extraction fidelity only);
* the verified current state (V1–V7) plus the delta-since-`-020` statement;
* the **complete `P1-D1…P1-D8` register** as PO-answerable items (question · why it is a PO decision · options · the `-020` recommendation · blast radius);
* **exactly what authorisation would permit** (five permitted changes, including the amended-never-deleted test list) and the explicit non-grants (no migration, no backfill, no B2/B3/B4 change, no `source_page` semantics change, no legacy-surface removal, no production rollout, no commit);
* the gate-evidence plan (shadow-first, new uploads only, pipeline-version stamp, selective-trigger evidence before enabling AI) and the verification the implementation must satisfy;
* risks/mitigations and a one-page answer sheet.

## 5. What was deliberately NOT done

No source, test, migration, schema, RLS or configuration change. No database mutation. No OCR or AI-gate change. No `source_page` change. No evidence-classification change. No B1/B2/B3/B4 object change. No `FactorizationEngine` change. No historical re-extraction or backfill. No production operation. No frontend change. No commit and no push.

## 6. Observations recorded (not defects, not fixed here)

1. **`DEFAULT_MAX_TEXT_CHARS` is defined twice** (`services/ai_document_extraction.py`, `engines/ai_extraction.py`) — a real duplication risk for the `P1-D3` decision, since a future clip change could be applied in only one place. Recorded for the P1 implementation scope.
2. **`source_page` is populated from `page_count`** — today's value is a *count*, not a page number (V3). Consistent with `-020` and with `P1-D5`/`P1-D7`; recorded so the implementation does not mistake the existing value for a page producer.
3. The `-020` §16.2 baseline ("21 tests") is now **85 tests across seven suites** — the extraction surface gained coverage since `-020`, and the baseline is green, so P1 starts from a larger regression net than the contract assumed (**a strengthening, not a conflict**).

## 7. Repository state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged by this task) |
| Commits | **none** |
| Staged | 0 |
| Tracked modifications | 219 pre-existing + 2 F-030-1 test repairs (per `…052`) — **this task added none** |
| Files created by this task | the P1 decision package (`docs/architecture/…`) and this report |
| Production | untouched; no storage writes; no backfill/re-extraction |
| Unrelated worktree changes | preserved |

## 8. Verdict

### `P1 DECISION PACKAGE COMPLETE AND VERIFIED — HOLDING AT THE P1-D1…P1-D8 PO RULING (AUTHORISATION-GATED, AS THE PLAYBOOK SPECIFIES)`

The next governed action is the PO ruling on `P1-D1` (authorise the multi-line `line_items[]` shape for new documents, gated on shadow evidence) together with `P1-D2…P1-D8`. On receipt, P1 implementation becomes eligible — it is **not** eligible now, and no part of it was performed.

Constraints restated: **no Phase 9**; Phase 8-X remains inside the Phase 8 programme; no production changes or storage writes; no historical backfill or re-extraction; unrelated worktree changes preserved; no commit/push without separate authorisation.

| The 7 extraction test suites | baseline verification (V6) |
| B-batch closures (B2 `…028`, B3 `…051`, B4 `…052`) + their migrations | confirming the extraction path was untouched by B2/B3/B4 (V7) |
