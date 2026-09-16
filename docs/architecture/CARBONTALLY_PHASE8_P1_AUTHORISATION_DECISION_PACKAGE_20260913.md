# CarbonTally — Phase 8 · Separate Workstream P1 (PDF/IMAGE Extraction Fidelity)
## P1 AUTHORISATION & DECISION PACKAGE

**Task identity:** `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037` — *P1 decision package (F/E)*
**Task type:** AUTHORISATION PREPARATION ONLY — **nothing is implemented, no source/test/migration/DB change, no production action, no commit**
**Date:** 2026-09-13
**Governing instruction:** master sequential playbook `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049` (line 193 authorises this package) + PO blanket authorisation `…050`
**Parent contract (authoritative, unmodified):** `docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md` (889 lines, task `…020`) and its forensic report `CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020.md`
**Fresh verification for this package:** see `docs/cline/reports/CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037.md` §3
**Baseline in this environment:** branch `main` · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · 219 pre-existing tracked modifications (+2 F-030-1 test repairs) · no commits

---

## 0. Status and boundary

This package turns the already-written P1 remediation contract into **PO-answerable decisions** and states **exactly what authorisation would permit**. It implements nothing, changes nothing, and authorises nothing by itself.

[OUT OF SCOPE, respected] no source/test/migration change · no database mutation · no OCR/AI-gate change · no `source_page` change · no evidence-classification change · no B2/B3/B4 change · no `FactorizationEngine` change · no historical re-extraction · no production operation · no frontend change · no commit/push.

---

## 1. What P1 is (unchanged from `-020`)

> **P1 makes the extraction layer faithful to the source: a document containing N genuine source lines must produce N addressable extracted lines — or explicitly say it could not — and a one-line document must still produce exactly one.**

**Binding root boundary:** P1 is **extraction fidelity** only. It is **not** evidence addressability (B2), **not** factor matching (P2/EF-E), **not** calculation, **not** reporting, **not** UI.

---

## 2. Verified current state (re-verified for this package, 2026-09-13)

| # | Fact | Evidence (fresh) |
|---|---|---|
| V1 | `line_items[]` is produced by the **tabular (CSV/XLSX)** path only (`_rows_to_line_items`); the PDF/IMAGE path still has no per-source-line producer | `services/automatic_extraction.py` (`_rows_to_line_items`, `line_items.append`) |
| V2 | The AI text clip persists and is **duplicated** in two modules | `services/ai_document_extraction.py:39` and `engines/ai_extraction.py:43` — both `DEFAULT_MAX_TEXT_CHARS = 20_000` |
| V3 | Page semantics remain **document-level only** (`source_page = job.metadata["page_count"]`), never per line | `services/automatic_processing.py:1151`; `data/evidence_line_items.py` carries `source_page` but no per-line producer feeds it |
| V4 | The deterministic+AI **merge/blend** path is still the one `-020` described | `services/automatic_processing.py:166–188` (`det_lines`, `ai_lines` → `merged_lines`) |
| V5 | The legacy parallel extraction/emissions surface still exists (reachable, hard-coded factors) | `backend/pdf_engine.py`, `backend/routes/upload.py` |
| V6 | **Baseline is green** — the extraction suites pass, so P1 starts from a verified, non-broken baseline | 7 suites, **85 tests, EXIT=0** (`test_automatic_extraction`, `..._text_layer`, `test_automatic_processing`, `test_ai_document_extraction`, `engines/test_ai_extraction`, `engines/test_extraction`, `engines/test_extraction_suggestions`) |
| V7 | the extraction **fidelity behaviour** is unchanged since `-020`; B2/B3/B4 added evidence addressability, disclosure projection/intensity and narrative/finalisation/artefact objects **without** changing what extraction produces | worktree inspection + B-batch closures; the B-batch migrations add disclosure/evidence objects only. **Precision:** `services/automatic_processing.py` carries **pre-existing B2-era uncommitted changes** (a `source_line_item_id` ordinal→line *lookup* and a `method_stamp` argument) — provenance plumbing, not fidelity changes; this package changed nothing |
**Conclusion:** every forensic precondition that `-020` rests on is **still true today**; no `P1-Dn` decision has become moot, and none has been silently overtaken by later batches.

---

## 3. Decision register — the complete P1 set as PO-answerable items

Each item states the question, why it is a PO decision (not an implementation choice), the options, the `-020` recommendation, blast radius and reversal cost.

| ID | Question | Why PO | Options | `-020` recommendation | Blast radius |
|---|---|---|---|---|---|
| **P1-D1** | Is the extraction **shape** change authorised for **new** documents (multi-line PDF/IMAGE emits `line_items[]`)? | it changes what the product extracts and what customers see; it is the core of P1 | (a) authorise, gated on shadow evidence; (b) authorise but keep the shape internal; (c) do not authorise | **(a) proceed, gated on §18.1 shadow evidence** | extraction output contract for new jobs; customers see per-line rows; no migration |
| **P1-D2** | When deterministic extraction is multi-line-suspect **and** AI is unavailable/fails: **block for human review**, or continue as a single-line document? | customer-visible workflow and manual-review queue volume — policy, not technique; not deciding keeps FM-4 alive | (a) block with a bounded reason; (b) continue as single line; (c) continue but flag | **(a) block** (continuing silently preserves the defect) | job state becomes `blocked`; review queue volume; no data loss |
| **P1-D3** | For long documents may AI run **per page/chunk** instead of once over a clipped layer? | direct, unbounded **cost** implication (one LLM call per page) | (a) per-page only when multi-line-suspect **and** the text exceeds the clip, with a page cap; (b) never; (c) always per page | **(a)**, capped | AI cost per long document; latency |
| **P1-D4** | Historical reprocessing policy: opt-in per document, admin bulk batch (dry-run + report), or not at all? | can churn snapshots, consume AI/OCR budget, touch customer evidence history | (a) not at all in P1; (b) per-document opt-in with audit; (c) admin bulk with dry-run | **(a) not at all in P1** | none if (a) |
| **P1-D5** | Ownership/sequencing of the `source_page` remediation relative to P1 | B2-D4 deferred it; P1 supplies the genuine per-line `page`, but reclassifying **historical** rows is a storage/interpretation change | (a) P1 supplies per-line `page`; a **separate** evidence/provenance workstream owns historical reclassification; (b) P1 also reclassifies history | **(a)** | (b) would make P1 a data-migration batch — explicitly contrary to the P1 boundary |
| **P1-D6** | Is the legacy `/api/upload*` + `pdf_engine` surface (parallel extraction + hard-coded factors) to be deprecated/consolidated? | it is a parallel path that **bypasses the authoritative calculation engine** — a product-contract question | (a) separate bounded review task, out of P1; (b) fold into P1; (c) leave indefinitely | **(a) separate task** | (b) would expand P1 beyond extraction fidelity |
| **P1-D7** | Does P1 emit `page` for OCR documents where boundaries come only from `[page N]` markers? | marker-derived pages are weaker than digital page numbers — a provenance-trust policy | (a) yes, with the OCR method stamp, treated as lower trust; (b) no page for OCR | **(a)** | evidence trust labelling; input to P1-D5 |
| **P1-D8** | Are AI-extracted lines acceptable as B2 evidence lines, stamped `extraction_method = ai:*`? | provenance-trust policy for downstream reporting/disclosure | (a) yes but explicitly stamped, never relabelled deterministic; (b) no, AI lines never become evidence lines | **(a)** | provenance labelling in evidence and disclosure drill-down |

---

## 4. The authorisation this package requests

If the PO grants `P1-D1(a)` (and rules on D2–D8), the implementation task may, **and may only**:

1. change the extraction path so that a multi-line PDF/IMAGE produces `line_items[]` (per-source-line), for **new** uploads only;
2. add the deterministic **multi-line-suspect classifier** and coverage block, **shadow-first (default off)**;
3. apply the ruled AI decision behaviour (`P1-D2`), the ruled AI fan-out policy (`P1-D3`), and the ruled page/method stamping (`P1-D7`);
4. bump `PIPELINE_VERSION` so extraction generations are distinguishable;
5. amend — **never delete** — the tests that pin single-line behaviour (`-020` §16.3): `engines/test_extraction_suggestions.py` (`test_suggest_parses_clean_invoice`, `test_suggest_gas_invoice_activity`, `test_suggest_quantity_not_invented`, `test_suggest_no_fabrication_on_garbage`), `services/test_automatic_extraction_text_layer.py` (`test_completeness_score_public_semantics`; the `test_merge_*` blending assertions replaced by adjudication tests, with the change **documented**), and leave the CSV/XLSX line-aware cases unchanged;
6. add new line-aware tests beside the preserved single-line cases.

**Explicitly not granted by any option:** no database migration; no historical backfill or re-extraction (§`P1-D4`); no change to B2/B3/B4 objects; no `source_page` semantics change (`P1-D5`); no legacy-surface removal (`P1-D6`); no calculation or factor change; no production rollout, deployment or storage write; no commit/push without separate authorisation.

---

## 5. Gate evidence required before the shape change is enabled

Per `-020` §18: (1) **shadow mode first** — compute and log the coverage block on real institutional-shaped documents **without** changing the gate or the output contract, and measure the classifier's FM-1/FM-2/FM-3 rates; (2) enable for **new uploads only**, behind the pipeline-version stamp; (3) enable the AI decision table only once shadow evidence shows the trigger is **selective**, not "every document"; (4) re-extraction remains separately authorised; (5) no production rollout.

---

## 6. Verification required of the implementation (stated now, in advance)

1. extraction suites green (the same 7 suites, 85 tests) **plus** the new line-aware cases;
2. an explicit **single-line regression case** per amended suite (proving one-line documents still yield exactly one line);
3. a multi-line fixture proving N genuine source lines → N addressable lines (or an explicit "could not extract" block);
4. provenance assertions: `extraction_method` stamped (`det:*`, `ai:*`, `{det}+{ai}`), never relabelled deterministic;
5. no-migration / no-backfill proof (schema unchanged, historical rows untouched);
6. independent verification of the shadow-mode evidence before the gate is enabled.

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Shape change alters customer-visible extraction | shadow-first; enable for new uploads only; pipeline-version stamp |
| AI cost explosion | `P1-D3(a)` cap; selective trigger proven by shadow evidence |
| Silent single-line fallback hides the defect | `P1-D2(a)` blocks with a bounded reason instead |
| Historical rows mutate unexpectedly | `P1-D4(a)` + write-once `automation_extracted_data` documented as truthful history |
| Scope creep into evidence/calculation/UI | the P1 boundary is binding; `P1-D5`/`P1-D6` push those to separate workstreams |

---

## 8. One-page answer sheet

| ID | Recommended answer |
|---|---|
| `P1-D1` | **Authorise** the multi-line `line_items[]` shape for new documents, gated on shadow evidence |
| `P1-D2` | **Block** (bounded reason) when multi-line-suspect and AI is unavailable |
| `P1-D3` | **Allow per-page AI** only when multi-line-suspect **and** the text layer exceeds the clip, with a page cap |
| `P1-D4` | **No historical reprocessing in P1** |
| `P1-D5` | **P1 supplies per-line `page`; historical reclassification is a separate workstream** |
| `P1-D6` | **Separate bounded review task; out of P1** |
| `P1-D7` | **Emit marker-derived `page` with the OCR method stamp (lower trust)** |
| `P1-D8` | **AI lines allowed as evidence lines only when explicitly stamped `ai:*`** |

---

## 9. Verdict

### `P1 DECISION PACKAGE COMPLETE — 8 DECISIONS READY FOR PO RULING; NO IMPLEMENTATION AUTHORISED OR PERFORMED BY THIS PACKAGE`

Governing constraints restated for the record: **no Phase 9**; Phase 8-X remains inside the Phase 8 programme; no production changes or storage writes; no historical backfill or re-extraction; unrelated worktree changes preserved; no commit/push without separate authorisation.
