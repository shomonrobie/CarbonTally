# CarbonTally — Phase 8 Reporting / Disclosure
## Separate Workstream P1 — PDF/IMAGE Extraction Fidelity — REMEDIATION ARCHITECTURE CONTRACT

**Task identity:** `CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020`
**Task type:** FORENSIC INVESTIGATION + ARCHITECTURE / REMEDIATION CONTRACT ONLY — **implementation is NOT authorised**
**Date:** 2026-09-13
**Repository baseline:** branch `main` · HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) · staged 0 · 208 pre-existing tracked modifications · 74–75 pre-existing untracked paths · 57 migrations
**Evidence tags:** **[OBSERVED]** repository/runtime fact · **[INFERRED]** reasoned conclusion · **[RECOMMENDED]** proposed architecture · **[DECISION REQUIRED]** unresolved PO decision · **[OUT OF SCOPE]** explicitly excluded

**Predecessors (authoritative):**
`docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` ·
`docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (§6.1, §7.1, §11, §27.1, §27.4) ·
`docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` (B2-D4, B2-D8, B2-D12) ·
`docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` (`DM-7`) ·
`docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` (EF-E, P2) ·
`AGENTS.md`

---

## 0. Status, authority and boundary of this document

This document defines *why* the current PDF/IMAGE extraction path collapses a multi-line invoice, *what* the
correct bounded architecture is, and *exactly what a future authorised implementation may and may not touch*.

**It authorises nothing.**

**Explicitly outside this task (respected, verified in §21):** no implementation; no source/test/migration
change; no database mutation; no OCR change; no AI-gate change; no `source_page` change; no evidence
classification change; no B2 change; no `FactorizationEngine` change; no historical re-extraction; no
production operation; no commit; no push. Exactly two files were written — this contract and
`docs/cline/reports/CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020.md`.

**One-sentence definition of P1:**

> **P1 makes the extraction layer faithful to the source: a document that contains N genuine source lines
> must produce N addressable extracted lines (or explicitly say it could not), and a document that contains
> one line must keep producing exactly one.**

**The root boundary (binding):** P1 is **extraction fidelity**. P1 is **not** evidence addressability (that is
B2), **not** factor matching (that is P2 / EF-E), **not** calculation, **not** reporting, **not** UI.

---

## 1. Scope

**In scope of this contract:** the complete current PDF/IMAGE extraction flow and its remediation contract —
entry points, text/OCR resolution, deterministic suggestion, completeness scoring, AI invocation and merging,
timestamping, persistence, `line_items[]` representation, downstream handoff, page/location semantics,
correction/version semantics, historical-data policy and the P1↔B2 / P1↔calculation interfaces.

**Out of scope [OUT OF SCOPE]:** implementing any of it; B2 objects; `evidence_line_items`;
`calculation_snapshots.source_line_item_id`; the `source_page` semantics remediation (separate workstream,
§12); EF-E (P2); RLS/auth; billing; retention; frontend redesign; the legacy `/api/upload*` surface (§10);
bulk historical reprocessing (§13).

---

## 2. Baseline and investigation method

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) |
| Staged changes | 0 |
| Tracked modifications (pre-existing) | 208 |
| Untracked paths (pre-existing) | 74 at first check; 75 later in the session; 76 after this task's writes. **Attribution:** +1 = this task's contract file (new top-level untracked entry; this report lands inside the already-untracked `docs/cline/reports/`, adding no entry); the earlier 74→75 step was **not** caused by this task — the path that changed is `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` (mtime `2026-09-13 10:58:19`, i.e. during this session), written by another/concurrent process. No cache-like path is untracked; `__pycache__`/`.pytest_cache` are gitignored |
| Migrations on disk | 57 (newest `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql`) |
| Worktree operations performed | **none** — no reset / clean / stash / checkout / stage / amend / commit / push |
| Files written by this task | this contract; `docs/cline/reports/CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020.md` |

**Method.** Code trace of the V3 path with exact line references, plus **execution of the real, unmodified
production entry point** on a generated 8-line PDF (§3.2) and unit-level probes of the real
`automatic_extraction` / `automatic_processing` functions. No database was queried; no source file was
modified; the existing extraction unit tests were run read-only (§16.7).

---

## 3. Current architecture (evidence-established)

### 3.1 The V3 production path

```text
POST /api/v3/uploads                                  api/v3_documents.py:210
  → create_document_and_enqueue                        api/v3_documents.py:240
      storage upload + organization_files.create       api/v3_documents.py:273-295
      page_count = _pdf_page_count(content) if PDF else 1   api/v3_documents.py:125-143, 317
      manual_extraction_items.create_item(page_count)  api/v3_documents.py:318
      document_processing_queue.create(metadata={mime, page_count, document_id})
                                                       api/v3_documents.py:333-347
      organization_files.metadata.ocr = text layer     api/v3_documents.py:356-361
  → durable worker claim (FOR UPDATE SKIP LOCKED)      workers/automatic_processing.py:100-113
  → AutomaticProcessingService.process_job             services/automatic_processing.py:238
      ingesting  → _ingest                             services/automatic_processing.py:321
      extracting → _extract                            services/automatic_processing.py:362
          extract_document(content, file_name, mime)   services/automatic_extraction.py:474
              _extract_pdf                             services/automatic_extraction.py:226
                  _pdf_text                            services/automatic_extraction.py:199
                      PDFExtractor._extract_text_direct  pdf_engine.py:60  (page.extract_text())
                      PDFExtractor._extract_text_ocr     pdf_engine.py:74  (pdf2image + Tesseract, "[page N]")
                      pypdfium2 render + ONNX OCR        services/automatic_extraction.py:150, 251
                  suggest_text(text[:200_000])         services/extraction_suggestions.py:105
                      DocumentExtractionEngine.suggest_fields  engines/extraction.py:267
                      _suggest_quantity_unit           services/extraction_suggestions.py:75
                      _ACTIVITY_KEYWORDS first match   services/extraction_suggestions.py:39-47, 147
                  → ONE FLAT record                    services/automatic_extraction.py:238-248
          completeness gate                            services/automatic_processing.py:438
          optional AI candidate                        services/automatic_processing.py:404-437, 521
          persist extracted_data (write-once original) services/automatic_processing.py:485-508
      mapping   → _map                                 services/automatic_processing.py:665
      validating→ _validate                            services/automatic_processing.py:794
      calculating→ _calculate / _calculate_line        services/automatic_processing.py:945, 1055
  → review (D5 customer verification) → completed       domain/automatic_processing.py:63-93
```

The identical flat record is produced for **IMAGE** (`_extract_image`,
`services/automatic_extraction.py:291-313`). `[OBSERVED]`

### 3.2 Reproduced defect (execution, not inference)

A single-page PDF containing eight genuine invoice lines was generated and passed through the **real,
unmodified** production entry point `services.automatic_extraction.extract_document`:

| Input | Result |
|---|---|
| 8 invoice lines (General waste 12.5 tonnes; Mixed recycling 3.2 tonnes; Hazardous waste 4.0 tonnes; Water supply 210 m3; Business travel 640 km), plus a `Total consumption: 38.4 m3` header value | `status=ok`, `method=pdf_text`, `page_count=1`, `confidence=1.0`, `unresolved=["supplier"]` |
| — | `extracted_data = {"invoice_number": "INV-10482", "date": "14/03/2026", "net_amount": "2800.00", "quantity": 38.4, "unit": "m3", "activity": "Waste"}` |

**8 source lines → 1 extracted object**, whose `activity` comes from one source line and whose
`quantity`/`unit` come from a *different* source row, at a completeness score of **1.0**.
This reproduces the previously recorded `Waste + 38.4 m³` observation exactly. `[OBSERVED]`

### 3.3 Classification of every PDF/IMAGE extraction path

| # | Path | Classification | Evidence |
|---|---|---|---|
| 1 | `services/automatic_extraction._extract_pdf` / `_extract_image` → `suggest()` | **V3 PRODUCTION (deterministic)** | `services/automatic_processing.py:379`; reached by `POST /api/v3/uploads` |
| 2 | `services/ai_document_extraction.AIDocumentExtractionEngine` | **V3 PRODUCTION (candidate AI), conditionally unreachable** | `services/automatic_processing.py:404-437`; `infra/ai_runtime.py:43-63` |
| 3 | `services/automatic_extraction._extract_csv` / `_extract_xlsx` → `_rows_to_line_items` | **V3 PRODUCTION (deterministic, line-aware)** | `services/automatic_extraction.py:402-471` |
| 4 | `pdf_engine.PDFExtractor.extract_and_parse` / `extract_and_parse_image` and `_parse_utility_bill` / `_parse_fuel_invoice` / `_parse_scope3_document` | **LEGACY, reachable, non-V3** — mounted at `/api/upload`, `/api/upload-pdf`, `/api/upload-batch`, `/api/repair-pdf` (`routes/upload.py:184, 272, 301, 552`; mounted `main.py:212`) and called by the legacy frontend (`frontend/src/UploadManager.js:216`, `frontend/src/App.js:957`). **Not** the V3 pipeline. | §10 |
| 5 | `engines/extraction.DocumentExtractionEngine.extract` (`_build_result`, `_extract_tables`) | **NOT PRODUCTION for PDF/IMAGE** — only `suggest_fields` is used by the extraction path; `extract()` (with pages/tables) is used by the V2.1 `engines/workflow.py` orchestrator, which has **no production constructor** outside tests | `engines/__init__.py:23`; `grep` shows no non-test construction |
| 6 | `engines/ai_extraction.AIExtractionEngine` | **NOT V3 PRODUCTION** — used only by `engines/workflow.py` (V2.1) and tests | `engines/workflow.py:61`; tests only |
| 7 | `pdf_engine._parse_scope3_document` | **UNIMPLEMENTED** (returns `not_implemented`) | `pdf_engine.py:300-315` |
| 8 | `services/extraction_suggestions.suggest` | Shared deterministic pass (single-line) | used by path 1 |

---

## 4. Q1 — Why an 8-line PDF becomes one extracted record (exact mechanism)

The previous forensic established *that* it happens and its primary classification. This investigation
establishes the **mechanism**, at six independent levels:

**(M1) The deterministic pass has no line concept at all.** `suggest()` receives the whole document as one
string; its unit of analysis is the document, not a row. There is no loop over lines, rows, pages, blocks,
words or coordinates anywhere in `_extract_pdf` / `_extract_image` / `suggest`. `[OBSERVED]`
`services/extraction_suggestions.py:105-161`, `services/automatic_extraction.py:226-248, 291-313`.

**(M2) Two independent whole-document scans with different selection rules pick fields from different rows.**
`activity` = **first keyword in tuple order** that matches anywhere in the text
(`extraction_suggestions.py:39-47, 147-150`). `quantity`/`unit` = **first `<number><unit>` token in text order**
inside the first quantity-like *key/value field value* (`extraction_suggestions.py:75-102`). The two scans
overlap on no row boundary. Result: a deterministic cross-line field mixture. `[OBSERVED]`

**(M3) The quantity scan reads only key/value field values, never the document's data rows.** In the probe,
`_suggest_quantity_unit` returned `(None, None, ["quantity/unit"])` for a text whose eight data rows each
contained `qty unit`, because no `Consumption:`/`Quantity:` key/value line existed to scan. Adding one
aggregate header line (`Total consumption: 38.4 m3`) supplied *both* quantity and unit for the whole
document. `[OBSERVED]` — this is why the injected value is an **aggregate/document-level** number, not the
value of the water line as previously interpreted (`[INFERRED]` in the predecessor, refined here).

**(M4) `_suggest_quantity_unit` also has a dead fallback.** The `for value in quantity_fields or
list(fields.values())` loop breaks after the first value that yields candidates; when a quantity-like field
exists but its value carries no parseable unit, the `or` fallback to *all* field values never executes.
Probe: `consumption: "unreadable-glyph"` plus `diesel: "500 litres"` → `(None, None, ["quantity/unit"])`,
so a readable quantity was discarded solely because an unreadable quantity-like key existed. `[OBSERVED]`
`services/extraction_suggestions.py:83-102`.

**(M5) The completeness score is field-presence, not coverage, and therefore cannot see the loss.**
`_completeness` (`services/automatic_extraction.py:179-195`) = resolved ÷ 3 over
`("activity","quantity","unit")` for a flat record, or resolved ÷ (3 × lines) over `line_items`. A flat record
with all three fields present scores **1.0 regardless of how many source lines were dropped.** `[OBSERVED]`

**(M6) The AI rescue is gated on that score, so it is suppressed exactly in the failure case.**
`services/automatic_processing.py:404-409`:

```python
if self._ai_extraction_engine is not None and (
    confidence < AUTO_EXTRACT_CONFIDENCE_MIN      # 0.5 of the flat record's own 3 fields
    or job.metadata.get("prefer_ai") or job.metadata.get("force_ai")
    or job.metadata.get("ai_required")):
```

`AUTO_EXTRACT_CONFIDENCE_MIN = 0.5` (`domain/automatic_processing.py:52`). A flat record scoring 1.0 never
triggers AI. **There is no signal anywhere in the decision that the document contains more lines than the
one extracted** — the gate tests the *produced record's* completeness, not the *source's* coverage.
`[OBSERVED]`

**(M7 — compounding) The AI engine may not exist at all.** `configured_ai_extraction_engine()` requires
`CARBONTALLY_AI_BASE_URL` + `CARBONTALLY_AI_API_KEY` + `CARBONTALLY_AI_MODEL`
(`infra/ai_runtime.py:43-63`). None of these names appears in `.env`, `.env.local`, `.env.production` or
`.env.test` (variable names inspected only; values never read). Whether Render sets them is recorded as
**NOT VERIFIED** (`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md:60`). For any
deployment without them, the deterministic flat record is the *only* outcome and no AI fallback exists.
`[OBSERVED]` for the repository; `[U]` for production.

**(M8 — compounding) The AI merge is positional and lossy.** `_merge_extraction_candidates`
(`services/automatic_processing.py:154-200`) aligns `ai_lines[idx]` with `det_lines[idx]`. Two empirically
proven defects:

* *Total loss of deterministic document identity:* deterministic flat `{supplier, invoice_number, date,
  activity, quantity, unit}` + AI `line_items` → the returned dict is `dict(ai)` only; **all deterministic
  top-level fields are discarded** (probe output: `{"line_items": [...]}` with no `supplier`/`date`/
  `invoice_number`). `[OBSERVED]`
* *Fabricated cross-line field pairs:* deterministic lines `[{General waste, 12.5, tonnes}, {Diesel}]` +
  AI lines in a different order → `[{General waste, 12.5, tonnes}, {Diesel, 12.5, tonnes}]`. The second line
  now asserts Diesel consumed 12.5 tonnes — a value lifted from the waste line. `[OBSERVED]`

**(M9 — consequence) One line in ⇒ one calculation out.** `_map` builds `targets = line_items if line_items
else [dict(extracted)]` (`:684-685`); `_calculate` does the same (`:962-963`) and derives one request id per
target index (`:971-979`). A flat record therefore produces exactly one snapshot and one `emissions_logs`
row. `[OBSERVED]`

**Root cause statement.** The deterministic PDF/IMAGE extractor models a document as *one record*, and the
pipeline's single gate measures *that record's* field completeness. Nothing in the architecture represents
"how many lines the source contains", so the loss is undetectable by construction — and the AI path that
*could* recover lines is switched off by the very score the loss inflates. `[INFERRED]`

**Contradiction/discrepancy reported (per task instruction).** The predecessor
(`CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912` §7–§9) states the `38.4 m³` came from "the water line" and
that `Waste` beat `Water` "regardless of which line the activity actually belongs to". The **primary
classification is upheld** (activity and quantity are selected by two independent whole-document scans with
different rules). The **specific attribution is refined**: the deterministic quantity is the first
`<number><unit>` token in the first *quantity-like key/value field value*, i.e. normally a document-level
aggregate (here `Total consumption: 38.4 m3`), not a row value. If no quantity-like field exists, the
quantity is *unresolved* rather than taken from a data row (M3). This is a refinement of interpretation, not
a change of the verdict. `[OBSERVED]`

---

## 5. Q2 / Q6 — Can deterministic extraction produce multiple lines, and how should a multi-line
document be detected?

### 5.1 Available signals (all already in the dependency set)

| Signal | Available today? | Evidence |
|---|---|---|
| Text-line structure | **Yes** — `page.extract_text()` preserves newlines; the test PDF yielded 11 non-empty text lines for 8 data lines + 3 header/footer lines | `pdf_engine.py:64-68`; execution |
| Per-page boundaries | **Yes** — `_pdf_text` iterates pages and computes `page_count`; the OCR path already emits `[page N]` markers; the digital path discards page boundaries when joining with `"\n"` | `pdf_engine.py:60-72, 90`; `services/automatic_extraction.py:199-223` |
| Word-level coordinates | **Yes** — `pdfplumber 0.11.6` `page.extract_words()` returns `text, x0, x1, top, bottom, doctop, height, width, direction`; `page.page_number` is available. Clustering by `top` reproduced the 11 text rows 1:1 on the test PDF | execution (unused by the current code) |
| Table structure | **Yes, but insufficient alone** — `page.extract_tables()` returned **0** tables for an unruled invoice table layout | execution |
| OCR block structure | **Partially** — `_extract_text_ocr` wraps each page (`[page N]`) and Tesseract returns one text line per visual line; the ONNX fallback joins recognised spans with `"\n"` and discards their boxes although `RapidOCR` returns them | `pdf_engine.py:74-94`; `services/automatic_extraction.py:150-176` |
| Existing parsers | `engines/extraction._extract_tables` (tab-delimited) and `pdf_engine._parse_fuel_invoice` exist but are **not** the V3 path and are not line-level (`_parse_fuel_invoice` aggregates by fuel type) | §3.3, §10 |

### 5.2 Verdict

**Deterministic multi-line extraction is feasible with the existing dependency set and does not require a
new library, a layout model, or an unrestricted parser.** `[INFERRED]`

The reason it does not exist is architectural, not technical: `suggest()` is a *document-level field
suggester* by design (§6 of the predecessor; its own docstring, `services/extraction_suggestions.py:1-19`),
and no separate *row* abstraction was ever built for PDF/IMAGE.

**Bounded detection strategy `[RECOMMENDED]`** — a new, explicitly bounded "row-candidate" sub-stage, in this
priority order, all derived from the text layer already produced:

1. **Structured rows first:** if `page.extract_tables()` yields ≥1 table whose data rows have a consistent
   column count and ≥1 column maps to a quantity-like header, take those rows as row candidates.
2. **Row clustering otherwise:** group `page.extract_words()` by `top` within a small tolerance (a
   font-metric-derived tolerance, not a magic per-document constant), row-major; a *row candidate* is a
   cluster that contains **both** a description-like token run **and** a `<number>`+unit token run.
3. **Repeated-shape test:** declare the document **multi-line** only when **≥2 independent row candidates
   share the same extracted shape** (same field roles in the same order) **and** at least one of them is not
   the document's aggregate/total row. One row candidate alone never triggers multi-line.
4. **Repeated-unit/every-row heuristic** is *supporting*, not decisive: a repeated unit token across
   candidates raises confidence but cannot by itself declare multi-line.
5. **OCR path:** reuse the existing `[page N]` markers and treat OCR text lines as row candidates under the
   same rule 3.
6. **Below the bar:** the document stays **single-line** (existing behaviour) and, where a multi-line
   suspicion remains, escalates per §7 rather than guessing.

**Explicitly rejected `[OUT OF SCOPE]`:** an unrestricted document parser; a general layout/ML model; a
user-configurable rules engine; invoice-template matching as the primary mechanism; adopting
`pdf_engine._parse_utility_bill` / `_parse_fuel_invoice` (see §10).

**Known bounded failure modes of this strategy** (must be tested, §16): multi-column page layouts that fuse
unrelated blocks into one `top` cluster; OCR line-wrapping that splits one source line into two candidates
(over-count); a single-line utility bill whose header block looks row-like (under/over-count); rotated or
multi-column text where `top` ordering is not reading order.

---

## 6. Q3 — The authoritative extraction output contract

### 6.1 Decision

**Keep one persisted envelope. Keep `extracted_data.line_items[]` as the canonical line array.** `[RECOMMENDED]`

Rationale (evidence, not preference):

* The array already **is** the cross-surface contract: the CSV/XLSX path emits it
  (`services/automatic_extraction.py:415`), the AI path emits it
  (`services/ai_document_extraction.py:262`), the human path writes it (`api/v3_operations.py:1648-1664`
  with free-form `ExtractPayload.extracted_data`; frontend `ExtractionPanel.jsx:237-241` always posts
  `line_items`), the mapper/calculator consume it (`api/v3_operations.py:467-474, 573`,
  `services/automatic_processing.py:684, 962`), and B2 materialises from it
  (`B2 contract §11.1-§11.2`). Inventing a second representation would create a competing contract.
* The element key vocabulary B2 recognises (`activity`, `description`, `item`, `quantity`, `unit`, `amount`,
  `currency`, `supplier`, `date`, `invoice_number`) is a superset of what the deterministic and AI paths
  already can produce. No new vocabulary is required.

### 6.2 Normative shape

```jsonc
// extracted_data (unchanged envelope; flat document identity remains)
{
  "supplier": "...", "invoice_number": "...", "date": "YYYY-MM-DD",
  "net_amount": "...", "gross_amount": "...", "currency": "...",
  // Single-line document: unchanged flat fields
  "activity": "...", "quantity": 0, "unit": "...",
  // Multi-line document: the array replaces the single activity/quantity/unit triple
  "line_items": [
    {
      "description": "<source row text, as read>",   // preferred when the row has prose
      "activity":    "<canonical activity label>",   // when determinable
      "quantity":    0,
      "unit":        "<as read, pre-normalisation>",
      "amount":      0,            // optional
      "page":        1,            // optional, genuine 1-based page (B2 §11.7)
      "extraction_method": "pdf_text"  // optional per-line override (B2 §11.7)
    }
  ]
}
```

**Mutual exclusivity rule `[RECOMMENDED]`:** a document emits **either** the flat triple **or**
`line_items[]` — never both. Today `_map`/`_calculate` already implement exactly this precedence
(`line_items` wins: `services/automatic_processing.py:684-685, 962-963`), and producing both would create an
ambiguous "which is the document?" question for B2 and for the UI. **`line_items[]` must never be emitted
with exactly one placeholder element that merely restates the flat record** — that would manufacture a line
identity B2 would then persist (violates `DM-7` and B2 §11.1's "never falls back to the flat record").

**Rejected representations `[OUT OF SCOPE]`:**
* nested page → block → row trees persisted as the contract (over-models; B2 needs a flat ordered array);
* page/block coordinate references in the persisted element (B2 has no column and B2-§7.3 rejected them);
* OCR spans as durable record identity (OCR geometry is not stable across engines/reruns);
* a second `extracted_lines` document beside `extracted_data` (competing source of truth).

**Not changed by P1:** the flat document-level keys, `mapped_data`, `manual_extraction_items.extracted_data`
semantics, B2's element interface, `evidence_line_items`.

---

## 7. Q4 / Q5 — Completeness, the AI decision model, and deterministic/AI/hybrid

### 7.1 What the current gate actually measures

| Concept | Measured today? | Evidence |
|---|---|---|
| Field completeness of the produced record | **Yes** | `services/automatic_extraction.py:179-195` |
| Document/source *coverage* | **No** | no source-row enumeration exists |
| Line completeness | **No** (only intra-`line_items` field presence) | `:182-191` |
| Semantic confidence / ambiguity | **No** | no ambiguity signal exists |
| Whether activity and quantity come from the same row | **No** | M2 |
| Extraction-method trust | **No** | `method` is recorded, never scored |

### 7.2 Corrected decision model `[RECOMMENDED]`

Keep `_completeness` **exactly as it is** (it is the field-completeness score, it is unit-tested, and B2/UX
depend on its published semantics via `completeness_score` and `AutomaticProcessingJob.completeness`).
**Add** a separate, document-level *coverage assessment* produced by the extractor and carried in the
**envelope** (not inside `extracted_data`, so no persisted-shape change and no B2 `payload_hash` impact):

```jsonc
{
  "status": "ok", "method": "pdf_text", "page_count": 1,
  "extracted_data": { ... },
  "unresolved": [...], "confidence": 1.0,          // unchanged semantics
  "coverage": {                                     // NEW (envelope-level)
    "shape": "single_line" | "tabular" | "unknown",
    "source_row_candidates": 8,   // row-like clusters found in the source
    "lines_extracted": 8,
    "coverage_ratio": 1.0,        // min(1, lines_extracted / max(1, source_row_candidates))
    "ambiguous_fields": ["quantity"],   // fields whose source row differs from the activity's row
    "reason": "..."                     // bounded, human-readable, never document text
  }
}
```

Then **replace the single-trigger gate with a decision table** (evaluated in
`services/automatic_processing._extract`, reusing the existing engine and merge — no new AI engine):

| # | Condition | Action |
|---|---|---|
| 1 | `confidence < AUTO_EXTRACT_CONFIDENCE_MIN` | Run AI (existing behaviour, preserved) |
| 2 | `coverage.shape != "single_line"` **and** `coverage.lines_extracted < coverage.source_row_candidates` | Run AI |
| 3 | `coverage.ambiguous_fields` non-empty | Run AI |
| 4 | `metadata.prefer_ai` / `force_ai` / `ai_required` | Run AI (existing) |
| 5 | Otherwise | Deterministic-only (existing) |

And **never silently accept a lossy flat record**: if `coverage.shape != "single_line"` and AI did not run
(or failed) and coverage is not satisfied, the job is **not** allowed to continue as a "complete"
single-line document (§7.4).

### 7.3 Why not AI-only, and why not the current positional merge

* **AI availability is not guaranteed** (M7) — an AI-only architecture would make extraction dependent on an
  optional, unverified deployment variable. `[OBSERVED]`
* **Reproducibility:** deterministic output is byte-stable across reruns, which is what the pipeline's resume
  markers, `_calc_payload_digest` idempotency and `DM-7` rely on. LLM output at `temperature=0.0` is not
  contractual determinism. `[INFERRED]`
* **The current merge fabricates data** (M8) — blending is positionally index-aligned, which asserts
  cross-line field pairs that exist in no source. Any hybrid architecture must **never** blend two candidate
  line arrays field-by-field. `[OBSERVED]`

### 7.4 Options assessed

| Option | Accuracy risk | Cost | Latency | Reproducibility | Explainability / auditability | Failure modes | Impl. complexity | Effect on historical data | Verdict for CarbonTally |
|---|---|---|---|---|---|---|---|---|---|
| **A. Deterministic only** | High for multi-line PDFs (the defect persists); no rescue path | Lowest (no LLM) | Lowest | Highest | Best | silent line loss | Low (but does not solve P1) | none | **Insufficient alone** |
| **B. AI only** | Model-dependent; unavailable where unconfigured; hallucinated lines/units | Highest + unbounded per page | Highest, variable | Lowest | Poor without strict provenance | silent fabrication; no output when unconfigured | Medium | Historical docs unserved | **Rejected** |
| **C. Deterministic-first with conditional AI fallback (structure-aware gate)** | Low–medium; deterministic wins on genuine single-line docs | AI only when structure says multi-line | Bounded by one extra call on suspect docs | High (deterministic by default) | Good — method stamp already persisted | AI unavailable → must not claim completeness (§7.4/§15) | Medium | Historical docs untouched by default | **RECOMMENDED** |
| **D. Deterministic + AI reconciliation (field-blend, as currently coded)** | **High — proven to fabricate cross-line pairs and to drop deterministic identity** | as C | as C | Low | Low (mixed provenance inside one line) | invented lines | Medium | as C | **Rejected as implemented**; acceptable only as C′ (document-level choice) |
| **D′. Deterministic + AI document-level adjudication (C′)** | Low — one candidate is accepted whole, the other retained as evidence | as C | as C | High | **Best** — both candidates persisted, acceptance recorded | disagreement is visible, never blended | Medium | as C | **RECOMMENDED as the reconciliation rule inside C** |
| **E. Hybrid with mandatory AI on every document** | Lower line-loss risk; higher fabrication/inconsistency risk | Highest | Highest | Lowest | Poor | cost blow-out, non-determinism on clean documents | Medium | as C | **Not recommended** |

### 7.5 Recommendation

**Adopt C + D′:** deterministic-first with a **structure-aware** AI trigger, and **document-level
adjudication instead of positional field-blending**. Both candidates remain persisted (they already are:
`automation_extracted_data`, `ai_extraction_result`, `job.metadata["ai_extraction"]`), and the accepted
candidate plus its method stamp is recorded. `[RECOMMENDED]`

---

## 8. Q7 — Line identity: what must be preserved

**Class A — required for extraction to work (in-flight only; never a durable identity):** the row candidate's
cluster id, word offsets, `top`/`x0`/`x1` bounds, the raw row text used for parsing, and the extraction
confidence inputs. These may exist in memory and in **job metadata / audit**, and are **not** part of the
persisted element. `[RECOMMENDED]`

**Class B — required for B2 (must be in the persisted element):** exactly the B2 §11.2 recognised keys
(`activity` / `description` / `item`, `quantity`, `unit` as-read, `amount`, `currency`, `supplier`, `date`,
`invoice_number`) plus the B2 §11.7 optional keys (`page`, `line_reference`, `extraction_method`), and the
**array-ordinal position** that becomes B2's `line_number`. Nothing else. `[RECOMMENDED]`

**Class C — UI/debugging only (must NOT be persisted into the element):** bounding boxes, OCR spans,
per-line confidence, prompt/model identifiers, cluster tolerance. Putting any of these into the element would
(a) change B2's `payload_hash` semantics for a non-payload fact, and (b) change `_calc_payload_digest` so
that a cosmetic extractor change creates new snapshots. `[RECOMMENDED]`

**Explicitly excluded from P1's line identity:** factor candidates (mapping's job), normalised units
(`core.units` owns aliasing — `AGENTS.md` §23), scope/methodology (calculation's job), and any per-line
confidence as a *durable* B2 fact (B2 has no column for it; B2-D10 confirmed the field list).

**Ordinal stability requirement `[RECOMMENDED]`:** within one extraction attempt, `line_items` order must be
**source order, stable across reruns of the same extractor version on the same bytes**. Reordering between
attempts is a *new extraction version* (§11), because B2's `line_number` is the array index.

---

## 9. Q8 — Page / location semantics (and the `source_page` defect)

### 9.1 The finding (evidence-complete)

`calculation_snapshots.source_page` has ≥3 mutually incompatible provenances.

**Writers (all of them):**

| # | Writer | Value written | Evidence |
|---|---|---|---|
| W1 | Automatic pipeline | **the document's page COUNT** | `services/automatic_processing.py:1134` — `source_page=job.metadata.get("page_count")`; the value originates at `api/v3_documents.py:317` (`_pdf_page_count`, `:125-143`) via job metadata (`api/v3_documents.py:341`) |
| W2 | V3 emissions API | **caller-supplied**, no validation | `api/v3_emissions.py:122` (contract), `:689` (write) |
| W3 | V2 calculation API | **caller-supplied**, no validation | `api/contracts.py:223` (contract), `api/business.py:143` (write) |
| W4 | V3 processing workflow (single-line path) | **caller-supplied**, no validation | `api/v3_processing_workflow.py:139` (contract), `:896` (write) |
| — | Ops multi-line path `_run_line_calculation` | **never set** → NULL for every multi-line document | `api/v3_operations.py:529-560` (no `source_page=` argument) |
| — | Plumbing | pass-through only | `engines/calculation.py:329` (`from_match_result`), `:499` (snapshot build); `domain/calculation.py:59` |

**Consumers (all of them):**

| # | Consumer | Effect of a non-NULL value | Evidence |
|---|---|---|---|
| C1 | Evidence record classification | `has_page = page is not None` → evidence classified **COMPLETE** ("exact source location") | `domain/evidence.py:145, 166, 36-47` |
| C2 | Evidence location precision | presented as `"page N"` precision and in `technical_details.source_page` | `domain/evidence.py:54-103, 330` |
| C3 | Export completeness label | `COMPLETE` / `PARTIAL` per emission | `data/exports.py:45-59` |
| C4 | Audit-readiness aggregate | counted as `complete` in `audit_readiness` | `data/reporting.py:1093-1103` |
| C5 | Reporting read model | selected and surfaced | `data/reporting.py:1166` |
| C6 | Snapshot read model / API | exposed | `data/emissions_logs.py:324, 493`; `api/contracts.py:289`; `api/v3_emissions.py:505` |
| C7 | UI | rendered as "Source page" | `frontend/src/v3/components/EvidenceRecordPanel.jsx:87-88` |

**Consequences `[INFERRED]`:** an automatically processed multi-page PDF records `source_page = page_count`
and is presented, exported and aggregated as evidence with an **exact page location**; a single-page PDF
records `1`, which happens to be both the correct page number *and* the page count — so the defect is
invisible on single-page documents and only falsifies multi-page ones. Consumers C1/C3/C4 do not verify the
value. Additionally `source_page` is **client-assertable** (W2–W4) with no `ge=1` validation and no database
`CHECK` (`supabase/migrations/20260823010000_d33_evidence_traceability.sql:26` adds a plain `integer`), so an
authenticated staff user can assert a page and flip an emission to COMPLETE evidence.

**Is any true page number stored today?** No. `[OBSERVED]` — no writer derives a genuine source page. The
digital text layer discards page boundaries when joining pages (`pdf_engine.py:64-68`); `[page N]` markers
exist only on the OCR path (`pdf_engine.py:90`) and are not parsed into structured output.

### 9.2 Correct future data model `[RECOMMENDED]`

Keep the four concepts **separate**:

| Concept | Meaning | Where it lives | Populated by |
|---|---|---|---|
| `page_count` | document extent | `document_processing_queue.page_count`, `organization_files`/item metadata | ingest/upload |
| `page_number` | the 1-based page a line appeared on | per-line optional key (`element.page`) → B2 `evidence_line_items.source_page` (B2 §11.7) | **P1 extractor** (new) |
| source row ordinal | position of the line in the source | array index → B2 `line_number` | P1 ordering + B2 materialisation |
| `row_reference` | a reference printed on the source | B2 `row_reference` — stays NULL (B2-D8) | nothing today |
| bounding box / text span | geometry | extraction-internal only (Class C) | P1, never persisted |

**Explicit prohibition `[RECOMMENDED]`:** `page_count` must **never** be written to `source_page`; a
non-NULL location must mean a genuine per-line page.

### 9.3 Which workstream owns the remediation? — **NOT P1**

`[RECOMMENDED]` The `source_page` remediation belongs to the **separate provenance/evidence remediation
workstream**, exactly as already ruled by **B2-D4 (CLOSED)**: it is a semantics problem in an existing write
path that changes evidence classification for existing data, and neither B2 nor P1 may fix it
(`B2 contract §23 B2-D4`, `§27.1`). P1's obligation is narrower and additive: **its new extractor must
produce a genuine per-line `page` so the remediation workstream has a truthful producer to consume**, and
P1 must **not** write, reinterpret, transform or propagate the existing `source_page` value. P1 must also
never derive a page from `page_count`. Ordering therefore is: **P1 supplies the fact; the evidence workstream
changes the storage/interpretation and the classification of historical rows** (`[DECISION REQUIRED]` P1-D5
for sequencing/ownership confirmation).

---

## 10. Legacy surface — recorded, not adopted

`pdf_engine.PDFExtractor.extract_and_parse` **is reachable in production** (mounted at `/api/upload`,
`/api/upload-pdf`, `/api/upload-batch`, `/api/repair-pdf` — `routes/upload.py:184, 272, 301, 552`;
`main.py:212`) and is called by the legacy frontend (`frontend/src/UploadManager.js:216`,
`frontend/src/App.js:957`). `[OBSERVED]`

It must **not** be adopted as the P1 architecture, for reasons established by inspection rather than
assumption:

1. **It is not line-level either.** `_parse_fuel_invoice` splits lines but then **groups records by fuel type
   and emits one aggregate stream per fuel type** with a summed `total_volume_litres`
   (`pdf_engine.py:227-298`). It loses individual lines in the same way.
2. **It bypasses the authoritative calculation engine** and embeds hard-coded factor multipliers
   (`pdf_engine.py:192`, `:289`, `:292`) — contradicting "calculation is server-authoritative via
   `engines/calculation.py`" (`AGENTS.md` §25).
3. **It contains hard-coded demo assets** (`routes/upload.py:211-214`).
4. **Its Scope 3 parser is unimplemented** (`pdf_engine.py:300-315`).
5. Its output shape (`data_streams[]`, `extracted_fields{}`, `defra_factor{}`) matches no persisted contract,
   no B2 element, and no mapper input.

**Verdict `[RECOMMENDED]`:** treat the legacy surface as a **separate finding (F-P1-11)** requiring its own
review (is it still part of the product contract? does it write to production tables?) — **not** a source of
P1 architecture, and **not** modified by P1. `[DECISION REQUIRED]` P1-D6: is the legacy `/api/upload*` +
`pdf_engine` surface in scope for a future deprecation/consolidation task?

---

## 11. Q9 — Corrections, versions and historical reproducibility

### 11.1 What already exists (do not reinvent)

| Mechanism | What it guarantees | Evidence |
|---|---|---|
| `document_processing_queue.automation_extracted_data` — **write-once** (COALESCE + trigger) | the original machine-produced extraction is permanently recoverable even after human edits | `data/document_processing.py:394-398, 584-624`; `supabase/migrations/20260906010000_gate6_w1_automation_extracted_output.sql:50,72` |
| `ai_extraction_result`, `ai_extracted_at`, `ai_processing_time_ms`, `metadata.ai_extraction`, `automation_provider/model/model_version` (write-once) | which AI pass ran, with which model, and its candidate confidence | `services/automatic_processing.py:458-500` |
| Append-only audit `automatic_processing:extracted` with machine actor + method stamp + confidence | per-execution extraction audit | `services/automatic_processing.py:617-659` |
| Human-edit audit (`org_item_extraction:edited`, `pe_extract:applied`) with changed-key list | attributable human correction | `api/v3_manual_extraction.py:142-167`; `api/v3_operations.py:1089-1107` |
| `_calc_payload_digest` in the per-line request id | corrected data ⇒ **new** snapshot; identical data ⇒ exact same request id ⇒ no duplicate snapshot | `services/automatic_processing.py:74-92, 970-991` |
| `PIPELINE_VERSION = "v3-auto-1.0"` | the extractor/pipeline version stamped on every job | `domain/automatic_processing.py:45` |

**Conclusion:** the minimum necessary architecture for extraction versioning **already exists**. P1 must
**reuse** it and must not invent a versioning subsystem. `[RECOMMENDED]`

### 11.2 Required semantics `[RECOMMENDED]`

| Question | Required answer |
|---|---|
| Is the original extraction recoverable after a correction? | **Yes** — `automation_extracted_data` is write-once; the corrected working payload lives in `extracted_data` |
| Is line identity stable? | Within an extraction attempt, yes (ordinal = array index, source order). Across attempts, a reorder/add/remove **changes what "line 3" means for future materialisation**; already-materialised rows are immutable and the change surfaces as a B2 `payload_hash` **divergence**, not a rewrite (B2 §11.3) |
| AI and deterministic differ? | Both candidates are persisted; **one candidate is accepted whole and recorded**; fields are never blended positionally (§7.3). Divergence must be visible in the audit/metadata |
| What happens to downstream calculations? | Corrected `extracted_data` ⇒ different digest ⇒ **new** snapshots; historical snapshots are immutable and never rewritten (D15 preserved) |
| What counts as a new extraction version? | (a) a different extractor/pipeline version (`PIPELINE_VERSION` bump), or (b) an explicit re-extraction of the same document. Both must leave the previous `automation_extracted_data` intact — which write-once already guarantees |
| What must P1 add? | (i) keep ordinals stable for a given version; (ii) bump `PIPELINE_VERSION` when the extractor's output contract changes; (iii) record the accepted candidate + coverage in the job metadata/audit (no schema change); (iv) ensure a re-extraction is an explicitly invoked, audited operation (§13) |

**No new table, no new migration, no new column is required for §11.** `[RECOMMENDED]`

---

## 12. Q10 — Historical documents: bounded future policy

**Absolute rules (unchanged, PO-governed):**

1. No silent historical PDF/IMAGE re-extraction (`DM-7`; predecessor §17.4).
2. No automatic reinterpretation of old flat records into lines.
3. No manufactured lines, no invented `row_reference`, no retroactive provenance.
4. Line-level evidence is materialised **only** from persisted `line_items[]` (B2 §11.1/§11.5). Historical
   flat records stay flat and their evidence stays PARTIAL forever unless explicitly re-extracted.

**Recommended bounded policy `[RECOMMENDED]`:**

| Class | Records | Policy |
|---|---|---|
| H1 | Flat PDF/IMAGE records, no persisted `line_items[]` | **Unchanged by default.** Optional, explicit, per-document re-extraction by an authorised human (H3) |
| H2 | Records that already persisted `line_items[]` (CSV/XLSX, AI-line, human line entry) | Nothing to do; already eligible for B2 forward/backfill materialisation |
| H3 | Explicit re-extraction of an H1 document | Must be a **separate, explicitly invoked, audited** operation that: (a) is per-document and human-initiated (or an explicitly named, dry-run-first administrative operation); (b) never overwrites `automation_extracted_data` (write-once) — the pre-existing flat output remains permanent evidence; (c) writes the new output as the working `extracted_data`; (d) records actor, reason, timestamp, extractor version and both old/new line counts in the audit trail; (e) never rewrites existing snapshots/emissions — recalculation produces *new* snapshots via the existing digest rule; (f) never runs as part of a read, a report, or a B2 backfill |
| H4 | Bulk historical reprocessing | **`[DECISION REQUIRED]` P1-D4** — opt-in per document, or an admin batch with dry-run + run report, or not at all. P1 recommends **not at all in this workstream** |

**Precondition discovered (must be part of any re-extraction work):** `reenqueue(stage="extracting")` is a
**silent no-op** for a job that already has `extracted_data`, because `_extract` returns early on the resume
marker (`services/automatic_processing.py:364-370`). There is currently **no** operation that clears or
supersedes an existing extraction. Therefore "explicit re-extraction" cannot be delivered by re-enqueue
alone: it requires a deliberately designed, authorised and audited supersede operation. `[OBSERVED]`

---

## 13. Q11 — The P1 → B2 interface (exact)

**B2 is a consumer; P1 is a producer. Neither absorbs the other.** `[RECOMMENDED]`

**P1 MUST provide:**

1. `extracted_data.line_items[]` as a real JSON array of JSON objects for every document that genuinely
   contains ≥2 source lines, with ≥1 recognised B2 key (§8 Class B) carrying a non-empty value per element
   (B2 §11.1/§11.2).
2. **Source order** and stable ordinals within an extraction attempt (B2 `line_number` = array index).
3. Optional per-element `page` (integer ≥ 1) when the extractor genuinely knows the line's page (B2 §11.7) —
   otherwise **absent**, never `page_count`, never a guess.
4. Optional per-element `extraction_method` when it differs from the document-level stamp (B2 §11.7).
5. `unit` **as read** (pre-normalisation) in the element — B2 records it as `raw_unit`; normalisation stays
   in `core.units`.
6. Exactly one representation per document (flat **or** `line_items[]`), never both (§6.2).
7. Nothing at all (i.e. the flat record) for genuine single-line documents — B2 must then materialise zero
   lines and the evidence chain stays document-level.

**P1 MUST NOT:**

* modify `evidence_line_items`, `calculation_snapshots.source_line_item_id`, `disclosure_value_evidence` or
  any B2 migration;
* emit `line_reference` (P1 has no producer for a printed reference; B2-D8 keeps `row_reference` NULL);
* emit bounding boxes, per-line confidence or any other Class-C field into the element (§8);
* emit synthetic/placeholder lines for flat records, or `line_items: []` as a substitute for a flat record;
* require B2 to change, or make B2's materialisation depend on P1's *optional* keys.

**B2 MUST NOT change** (restated so the boundary is unambiguous): no re-parsing, no re-extraction, no
inference from aggregate fields, no use of `mapped_data` for identity, no retro-linking of historical
snapshots. **P1 must not be used as a reason to widen B2, and B2 must not be used as a reason to widen P1.**

---

## 14. Q12 — Calculation interface (unchanged engine)

**No new calculation engine. No change to factor matching, methodology derivation, rounding, snapshot
identity, or the request-id derivation.** `[RECOMMENDED]`

**Interface check (evidence):**

* `_map` already consumes `line_items[]` or the flat record (`services/automatic_processing.py:684-685`).
* `_calculate` already iterates targets and derives `{job.id}::calc::{idx}::c1::{digest}` per index
  (`:962-963, 970-979`) — **unchanged and must stay unchanged**.
* `_calculate_line` reads only `activity`, `quantity`, `unit` from the line and `factor_id`/`activity`/`scope`
  from the mapped line (`:1067-1140`). Additional element keys are ignored — so `page` and
  `extraction_method` need **no** calculation change.
* `core.units.resolve_unit_for_factor` continues to own unit alias resolution (`:1102-1107`).

**Required interface changes: none.** Two consequences must be recorded, however:

1. **Digest sensitivity:** `_calc_payload_digest` hashes the whole `extracted_data` (and `mapped_data`)
   (`:74-92`). Adding `page`/`extraction_method` to a line therefore **changes the digest**, so any
   re-extraction of an already-calculated document produces **new** snapshots rather than reusing the old
   one. That is the desired behaviour for a corrected extraction (G6-D), but it must be *expected*: it is not
   a duplicate-prevention failure. It also means P1 must not add cosmetic keys to the element, because doing
   so would churn snapshots for unchanged documents.
2. **Single-line continuity:** the flat-record path (`targets = [dict(extracted)]`) must remain byte-identical
   for genuine single-line documents so no existing calculation is invalidated.

---

## 15. Failure modes, idempotency, performance and cost

### 15.1 Failure modes (must all be tested — §16)

| # | Failure | Consequence if unhandled | Bounded mitigation |
|---|---|---|---|
| FM-1 | Row clustering fuses multi-column blocks | wrong line count | require ≥2 same-shape row candidates (§5.2 rule 3); tolerance derived from font metrics; document-wide consistency check |
| FM-2 | OCR line-wrap splits one source line | over-count | merge adjacent candidates whose numeric token set is a subset and whose cluster gap is below the inter-line gap |
| FM-3 | Single-line document misclassified multi-line | needless AI call or needless human review | rule 3 + the "no single placeholder line" rule (§6.2) |
| FM-4 | AI unavailable while structure says multi-line | silent lossy flat record | §7.2 must not let this clear the gate (§7.4) |
| FM-5 | AI returns fewer/more lines than deterministic | fabricated blending | document-level adjudication only (§7.3) |
| FM-6 | Digital path discards page boundaries | line gets no/wrong page | carry page boundaries through per-page parsing; if unknown → **absent**, never `page_count` |
| FM-7 | AI text clipped at `DEFAULT_MAX_TEXT_CHARS = 20_000` while the text layer is up to 200 000 chars | later lines never seen by the AI | persist/document the clipping; consider per-page AI passes for long documents (`[DECISION REQUIRED]` P1-D3 on cost) |
| FM-8 | AI `max_tokens=1024` truncates long line arrays | silently truncated line set | detect non-JSON/incomplete response (already → `error`), and bound expectations for large invoices |
| FM-9 | ONNX OCR fallback unavailable (`rapidocr_onnxruntime`, `pypdfium2` are **not** declared in `requirements.txt`) | scanned-PDF path degrades to `no_text` → blocked | declare the dependencies and verify at deploy (`AGENTS.md` §20) |
| FM-10 | Tesseract/poppler absent on host | OCR unavailable | already falls back to pypdfium2+ONNX; must be an explicit deployment prerequisite |
| FM-11 | Coverage heuristic silent regression on a new layout | silent line loss returns | coverage must be *recorded* per extraction (observability), not just used |
| FM-12 | Re-extraction churns snapshots unexpectedly | duplicate-looking emissions | requested-digest rule is unchanged; the operation must be explicit, audited and reported |

### 15.2 Idempotency `[RECOMMENDED]`

* Deterministic-only extraction of the same bytes with the same extractor version must produce **byte-identical**
  `extracted_data`, so the resume marker (`job.extracted_data`) and the calculation digest remain stable and
  no duplicate snapshot is created by a crash/retry.
* AI-assisted extraction is **not** byte-guaranteed; therefore the accepted candidate must be persisted
  (it is) and a rerun must not silently flip the accepted candidate without an audit record.
* Line ordering must be deterministic (source order), or B2 `line_number` and the digest become unstable.

### 15.3 Performance / cost (qualitative; no fabricated benchmarks)

* **CPU:** pdfplumber already parses every page once for text (`pdf_engine.py:64-68`). Word extraction adds a
  bounded per-page pass over tokens already decoded; clustering is linear in word count. Memory should be
  bounded **per page** (stream page → words → clusters → rows) rather than accumulating all pages, because
  multi-page documents are the case where the current `"\n"`-join loses page identity anyway.
* **OCR cost:** unchanged trigger (text < 20 chars → OCR). The dominant OCR cost is the pypdfium2 render at
  `scale=2.0` plus ONNX inference, proportional to **page count × pixels**. Multi-page scans are the cost
  driver.
* **AI calls:** the corrected policy (§7.2) *increases* AI usage for multi-line documents (today the score
  suppresses it). Each call is one request over ≤20 000 characters at `temperature=0.0`, `max_tokens=1024`
  (`services/ai_document_extraction.py:39, 206-213`). AI is invoked only on suspect documents (rows 2–3 of
  the decision table), not on every document.
* **Latency:** deterministic path latency is essentially unchanged; a triggered AI pass adds one LLM round
  trip to the `extracting` stage of an already-asynchronous durable job, so it is not user-blocking.
* **Large/multi-page documents:** word-count growth is linear; the practical bounds are the AI text clip
  (FM-7), the AI output-token cap (FM-8) and the OCR page cost.
* **Retries:** unchanged — `max_attempts = 3` (`domain/automatic_processing.py:48`), stale-lock recovery
  (`workers/automatic_processing.py:44`), extraction failures remain durable `blocked` events.
* **Idempotency:** per §15.2.

### 15.4 Observability / audit `[RECOMMENDED]`

Extend (do not replace) the existing `automatic_processing:extracted` audit event
(`services/automatic_processing.py:617-659`) with the bounded coverage facts — `shape`,
`source_row_candidates`, `lines_extracted`, `coverage_ratio`, `ambiguous_fields`, `extractor_version`,
`accepted_candidate` (`deterministic` | `ai`) — and **never** with document text, OCR text, prompts or
credentials. Job metadata may carry the same block. This makes FM-11 detectable.

---

## 16. Test / verification contract

Runtime/database-backed verification is **required** wherever persistence or downstream behaviour is
involved. Static-only tests are explicitly insufficient (`[RECOMMENDED]`).

### 16.1 Required fixtures (real files, not mocks)

| # | Case | Purpose |
|---|---|---|
| 1 | Single-line PDF (key/value utility bill) | flat contract preserved |
| 2 | Multi-line PDF (the §3.2 fixture) | 8 lines in ⇒ 8 lines out |
| 3 | Multi-page invoice (lines continue across pages) | per-line `page` correctness; no `page_count` leakage |
| 4 | Table invoice with ruled lines | table-structure path (rule 1) |
| 5 | Image invoice (PNG/JPG) | OCR path produces the same line contract |
| 6 | Scanned PDF (image-only pages) | OCR path, `[page N]` handling |
| 7 | OCR-poor document (low quality / partial text) | honest `no_text`/`blocked`, no fabrication |
| 8 | Mixed activity/unit lines (waste + water + diesel + travel) | no cross-line field mixing |
| 9 | Document where deterministic extraction is confidently correct | AI **not** invoked (no wasted cost) |
| 10 | Document where deterministic extraction is incomplete | AI invoked, gap filled |
| 11 | Document where deterministic **looks** complete but is lossy (the root-cause case) | AI invoked; lossy record never accepted as complete |
| 12 | AI/deterministic disagreement (different line counts) | **no positional blending**; accepted candidate recorded |
| 13 | Repeated extraction of the same document | byte-identical output; no duplicate snapshot |
| 14 | Corrected extraction (human edit including add/remove/reorder) | new snapshot via digest; original preserved |
| 15 | Historical flat PDF record | untouched: no re-extraction, evidence stays PARTIAL |
| 16 | Historical structured `line_items[]` record | B2-eligible; unaffected by P1 |
| 17 | Page number vs page count (multi-page, auto-processed) | P1 emits genuine page or nothing; **`page_count` never becomes a page** |
| 18 | Provenance preservation across re-extraction | `automation_extracted_data` unchanged; audit shows actor/reason/version |

### 16.2 Test layers

1. **Unit — deterministic extractor:** row-candidate detection, ordinal stability, per-line `page`, the
   "no single placeholder line" rule, "flat or lines, never both".
2. **Unit — decision table:** each of the five §7.2 rows, including AI-unavailable behaviour.
3. **Unit — merge/adjudication:** prove that no positional blending is possible and that deterministic
   identity fields are never dropped.
4. **Integration — pipeline (DB-backed):** upload → enqueue → extracting → mapping → validating →
   calculating → review, asserting **one snapshot per extracted line** and the correct `line_items` shape in
   `document_processing_queue.extracted_data` and `manual_extraction_items.extracted_data`.
5. **Integration — failure/idempotency (DB-backed):** crash/retry produces no duplicate snapshot;
   `no_text` and OCR-unavailable paths become durable `blocked` jobs with reasons.
6. **DB-backed negative tests:** a flat record with multi-line structure must **not** reach `review` as a
   complete single-line document when AI is unavailable (whatever P1-D2 decides, the chosen behaviour must be
   asserted).
7. **Existing tests:** run the current suites before and after (`services/automatic_extraction.py` and
   `extraction_suggestions.py` suites currently pass — 21 tests, verified read-only during this task).

### 16.3 Existing tests that must be **AMENDED, NEVER DELETED** (B2-D3 analogue)

These pin the current single-document behaviour and must be preserved as explicit single-line cases, with new
line-aware cases added beside them:

* `backend/tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice`
* `backend/tests/unit/engines/test_extraction_suggestions.py::test_suggest_gas_invoice_activity`
* `backend/tests/unit/engines/test_extraction_suggestions.py::test_suggest_quantity_not_invented`
* `backend/tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage`
* `backend/tests/unit/services/test_automatic_extraction_text_layer.py::test_completeness_score_public_semantics`
* `backend/tests/unit/services/test_automatic_extraction_text_layer.py::test_merge_*` (must be replaced by
  adjudication tests, with the blending assertions **removed deliberately and documented**, never silently)
* `backend/tests/unit/services/test_automatic_extraction.py` (CSV/XLSX line-aware cases — unchanged)

---

## 17. Idempotency, migration and data implications

* **No database migration.** No schema change, no new table, no new column, no RLS change. Per-line page and
  method travel inside existing JSONB; the coverage block is envelope/job-metadata only. `[RECOMMENDED]`
* **No historical backfill** in P1. Historical flat records are not transformed (§12).
* **No snapshot or emissions mutation.** Recalculation of a corrected payload creates new snapshots through
  the existing digest rule; existing rows are untouched.
* **Write-once interplay (must be documented, not "fixed"):** because `automation_extracted_data` is
  write-once, a *re-extracted* historical document keeps its **original flat** machine output permanently
  while its working `extracted_data` becomes line-aware. This is truthful history (the flat record *was* the
  original automated output) and must be expected by the evidence/UX layers. `[INFERRED]` — flagged for PO
  awareness in the P1-D4 discussion.
* **Pipeline version:** bump `PIPELINE_VERSION` when the extractor's output contract changes, so extraction
  generations are distinguishable on the job.

---

## 18. Rollout strategy `[RECOMMENDED]`

1. **Shadow / observation mode first (default off):** compute and log the coverage block for real documents
   **without** changing the gate or the output contract; measure the classifier against real institutional
   documents (FM-1/FM-2/FM-3 rates) before it can block anything.
2. **Enable for new uploads only**, behind the existing pipeline-version stamp. Historical jobs are untouched
   by construction (their `extracted_data` is the resume marker).
3. **Enable the AI decision table** only after §18.1 shows the trigger is selective (not "every document").
4. **Explicit re-extraction** (§12 H3) is a **separately authorised** capability with its own audit and
   verification — it must not ship as part of the extraction-shape change, because it can churn snapshots.
5. **No production rollout** is authorised by this contract. Deployment remains a separate gated step.

---

## 19. Implementation boundary (what a future authorised implementation touches)

**IN scope for a future P1 implementation:**

1. `backend/services/automatic_extraction.py` — a new bounded row-candidate sub-stage plus the
   `_extract_pdf` / `_extract_image` wiring, the coverage block, and the "flat or lines, never both" rule.
2. `backend/services/automatic_processing.py` — the §7.2 AI decision table, the document-level adjudication
   replacing positional blending (§7.3), and the coverage facts in the existing audit event and job metadata.
3. `backend/domain/automatic_processing.py` — `PIPELINE_VERSION` bump; constants for the new trigger rows
   (no change to `AUTO_EXTRACT_CONFIDENCE_MIN` semantics).
4. `backend/services/ai_document_extraction.py` — only if the prompt/limits need adjustment for line
   extraction within the existing bounded envelope (FM-7/FM-8); **no new AI engine**.
5. `backend/core/units.py` — **no change** (aliasing stays put); extraction emits units as read.
6. Tests: new fixtures + unit/integration/DB-backed tests per §16, plus the amendments in §16.3.
7. Documentation and audit/observability per §15.4.

**OUT of scope (must not be absorbed):** `evidence_line_items` and all B2 objects/migrations;
`calculation_snapshots.source_line_item_id`; the `source_page` semantics remediation (§9.3);
`domain/evidence.py` classification; `engines/factor_matching.py` and EF-E; `engines/calculation.py` and the
request-id derivation; RLS/auth; billing; retention; frontend and manual-extraction UI;
`api/routes/upload.py` + `pdf_engine.py` legacy surface (§10); historical bulk reprocessing;
`pdf_engine._parse_scope3_document`.

---

## 20. Unresolved PO decisions `[DECISION REQUIRED]`

| ID | Decision | Why a PO decision | P1 recommendation |
|---|---|---|---|
| **P1-D1** | Is the extraction **shape** change authorised for new documents (multi-line PDF/IMAGE emits `line_items[]`)? | It changes what the product extracts and what customers see in the workspace; it is the core of P1 | Proceed, gated on §18.1 shadow evidence |
| **P1-D2** | When deterministic extraction is multi-line-suspect but AI is unavailable (or fails), must the job **block for human review**, or continue as a single-line document? | Changes customer-visible workflow and the manual-review queue volume; it is a policy choice, not a technical one. **Not deciding it means FM-4 persists** | Block (`blocked` with a bounded reason), because continuing silently preserves the defect |
| **P1-D3** | For long documents, may AI run **per page** (or per chunk) rather than once over a clipped text layer? | Direct, unbounded cost implication (one LLM call per page) | Allow per-page AI **only** when the document is multi-line-suspect **and** the text layer exceeds the clip; cap pages per document |
| **P1-D4** | Historical reprocessing policy: opt-in per document, admin bulk batch (dry-run + run report), or not at all? | It can churn snapshots, consume AI/OCR budget, and touches customer evidence history | **Not at all in P1.** If later required, per-document opt-in with full audit |
| **P1-D5** | Ownership/sequencing of the `source_page` remediation vs P1 | B2-D4 deferred it; P1's new `page` producer must precede or accompany it, and someone must own the existing-row classification change | P1 supplies the genuine per-line `page`; a **separate** evidence/provenance workstream changes storage/interpretation and reclassifies historical evidence |
| **P1-D6** | Is the legacy `/api/upload*` + `pdf_engine` surface (reachable, hard-coded factors, incomplete Scope 3) in scope for deprecation/consolidation? | It is a parallel extraction + emissions path that bypasses the authoritative calculation engine — a product-contract question | Separate bounded review task; out of P1 |
| **P1-D7** | Does P1 emit `page` for OCR documents where page boundaries come from `[page N]` markers only? | Marker-derived pages are more reliable than nothing but weaker than digital page numbers | Yes, emit with the OCR method stamp; evidence must treat method-stamped pages as lower trust (input to P1-D5) |
| **P1-D8** | Are AI-extracted lines acceptable as B2 evidence lines with `extraction_method` = `ai:*`? | Provenance-trust policy for downstream reporting/disclosure | Yes but explicitly stamped (`ai:*` / `{det}+{ai}`), never relabelled as deterministic |

---

## 21. Change-control statement

**What this task did NOT do (verified):** no implementation; no source, test, migration, RLS, RPC, config or
frontend change; no database mutation/query; no extraction/OCR/AI-gate/`source_page`/evidence-classification
change; no B2 object created or altered; no FactorMatchingEngine change; no historical re-extraction; no
production operation; no commit; no push; no `git reset`/`clean`/`stash`/`checkout`/`amend`/`stage`. The only
writes are the two mandated documents. Read-only code execution (the §3.2 reproduction and §16.7 test run)
created no tracked-file change; `__pycache__`/`.pytest_cache` artefacts are gitignored.

## 22. Verdict

**`P1 FORENSIC + REMEDIATION CONTRACT COMPLETE — READY FOR PO REVIEW`**

Root cause established with an execution-level reproduction: the deterministic PDF/IMAGE extractor models a
document as **one record**, the pipeline's single gate measures **that record's** field completeness, and the
AI path that could recover lines is suppressed by the very score the loss inflates. The bounded remediation
(deterministic-first, structure-aware detection, coverage instead of field-presence gating, document-level
adjudication instead of positional blending) is specified above and authorises nothing. Seven PO decisions
(P1-D1…P1-D8) remain open; implementation is **not** authorised.
