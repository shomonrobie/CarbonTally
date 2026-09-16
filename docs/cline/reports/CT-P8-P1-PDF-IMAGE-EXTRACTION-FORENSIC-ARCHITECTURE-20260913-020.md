# CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020

**Task identity:** `CT-P8-P1-PDF-IMAGE-EXTRACTION-FORENSIC-ARCHITECTURE-20260913-020`
**Task type:** FORENSIC INVESTIGATION + ARCHITECTURE / REMEDIATION CONTRACT ONLY — **implementation not authorised**
**Date:** 2026-09-13
**Workstream:** Phase 8 Reporting / Disclosure — **separate workstream P1: PDF/IMAGE extraction fidelity**
**Primary deliverable:** `docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md`
**Verdict:** `P1 FORENSIC + REMEDIATION CONTRACT COMPLETE — READY FOR PO REVIEW`

**Evidence tags:** **[OBSERVED]** repository/runtime fact · **[INFERRED]** reasoned conclusion ·
**[RECOMMENDED]** proposed architecture · **[DECISION REQUIRED]** unresolved PO decision ·
**[OUT OF SCOPE]** explicitly excluded · **[U]** unresolved

---

## 1. Task identity and scope

Produce a code-traced, evidence-based forensic investigation of CarbonTally's current PDF/IMAGE extraction
pipeline and a bounded remediation architecture/implementation contract answering Q1–Q12, resolving the
`source_page` semantics question, and defining the P1↔B2 and P1↔calculation interfaces — **without
implementing anything**.

**In scope:** the complete PDF/IMAGE extraction flow (upload → queue → automatic processing → PDF/IMAGE
extraction → OCR → deterministic pass → suggestions → AI extraction → completeness → AI preference/force
decisions → method stamping → persistence → manual extraction compatibility → `line_items[]` →
`mapped_data` → calculation handoff → page/location metadata → evidence classification → downstream
provenance); the `source_page` defect; the remediation contract.

**Out of scope [OUT OF SCOPE]:** implementing the remediation; modifying extraction/OCR/AI gates;
modifying `source_page`; modifying evidence classification; B2; FactorMatchingEngine; historical
re-extraction; production operations; commits/pushes.

## 2. Baseline Git / worktree state (recorded before analysis)

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) |
| Staged changes | 0 |
| Tracked modifications (pre-existing, unrelated) | 208 (`M` only) |
| Tracked deletions | 0 |
| Untracked paths (pre-existing) | 74 at first check → 75 later → 76 after this task's writes. **Delta attribution:** this task added **one** new top-level untracked entry (the contract; this report lands inside the already-untracked `docs/cline/reports/`). The earlier 74→75 step is **not** this task's: `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` has mtime `2026-09-13 10:58:19` (during this session) and was written by another/concurrent process. No cache-like path is untracked; `__pycache__`/`.pytest_cache` are gitignored |
| Migrations on disk | 57; newest `supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` |
| Worktree operations performed | **none** — no reset / clean / stash / checkout / amend / stage / commit / push |
| Files written by this task | `docs/architecture/CARBONTALLY_PHASE8_P1_PDF_IMAGE_EXTRACTION_REMEDIATION_CONTRACT_20260913.md`; this report |

**Pre-existing large untracked set preserved untouched** (e.g. `docs/architecture/CARBONTALLY_PHASE8_B2_*`,
`supabase/migrations/20260914*`/`20260915*`, `backend/domain/disclosure.py`, `qa_harness/`,
`tools/seed_investor_demo/`).

## 3. Files inspected

**Backend code:** `services/automatic_extraction.py`, `services/extraction_suggestions.py`,
`services/ai_document_extraction.py`, `services/automatic_processing.py`, `pdf_engine.py`,
`domain/automatic_processing.py`, `domain/evidence.py`, `domain/calculation.py`, `engines/calculation.py`,
`engines/extraction.py`, `engines/ai_extraction.py` (usage), `engines/workflow.py` (usage),
`workers/automatic_processing.py`, `infra/ai_runtime.py`, `core/units.py`, `api/v3_documents.py`,
`api/v3_operations.py`, `api/v3_processing_workflow.py`, `api/v3_manual_extraction.py`,
`api/v3_automatic_processing.py`, `api/v3_emissions.py`, `api/business.py`, `api/contracts.py`,
`routes/upload.py`, `main.py`, `data/manual_extraction.py`, `data/document_processing.py`,
`data/emissions_logs.py`, `data/exports.py`, `data/reporting.py`, `data/reports.py`.

**Frontend:** `src/v3/ops/ExtractionPanel.jsx`, `src/v3/customer/ProcessingItemWorkspace.jsx`,
`src/v3/components/EvidenceRecordPanel.jsx`, `src/v3/api.js`, `src/UploadManager.js`, `src/App.js`.

**Migrations (read):** `20260823010000_d33_evidence_traceability.sql`,
`20260829000000_v3m9_durable_automatic_processing.sql`, `20260905010000_gate5_t1_automation_provenance.sql`,
`20260905020000_gate5_t6_automation_write_once_guard.sql`,
`20260906010000_gate6_w1_automation_extracted_output.sql`,
`20260914000000_p8_b1_disclosure_model_foundation.sql` (B2 §7.1 DDL reference); global scan for
`source_page` and `source_location` across all 57 migrations.

**Tests:** `tests/unit/engines/test_extraction_suggestions.py`, `tests/unit/services/test_automatic_extraction.py`,
`tests/unit/services/test_automatic_extraction_text_layer.py`, `tests/unit/services/test_ai_document_extraction.py`
(existence/scope), `tests/unit/api/test_evidence_record.py`, `tests/unit/api/test_evidence_traceability.py`.

**Governance/operations docs:** `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`;
`docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (§1.2, §6.1, §7.1, §11, §23
B2-D2/D4/D8, §27.1/§27.4); `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`;
`docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` (§9–§11);
`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`;
`docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`; `AGENTS.md`.

**Environment files:** variable **names only** were listed for `.env`, `.env.local`, `.env.production`,
`.env.test`. **No secret value was read, printed or recorded.**

## 4. Code paths traced

### 4.1 V3 production PDF/IMAGE path (the defect path)

```
POST /api/v3/uploads  (api/v3_documents.py:210)
  → create_document_and_enqueue (api/v3_documents.py:240)
      page_count = _pdf_page_count(content) if PDF else 1   (:125-143, :317)
      document_processing_queue.create(metadata={mime, page_count, document_id})  (:333-347)
  → worker claim: claim_next(FOR UPDATE SKIP LOCKED)   (workers/automatic_processing.py:100-113)
  → process_job (services/automatic_processing.py:238) → _run_stage (:291)
      _ingest   (:321) → advance_stage(page_count=job.metadata["page_count"])  (:338)
      _extract  (:362)
          extract_document (:379) → _extract_pdf (services/automatic_extraction.py:226)
              _pdf_text (:199) → PDFExtractor._extract_text_direct (pdf_engine.py:60)
                               → _extract_text_ocr (pdf_engine.py:74, "[page N]")
                               → pypdfium2 render + _onnx_ocr (services/automatic_extraction.py:251, 150)
              suggest_text(text[:200_000]) (services/extraction_suggestions.py:105)
                  _ENGINE.suggest_fields (engines/extraction.py:267)
                  _FIELD_ALIASES copy (services/extraction_suggestions.py:129-132)
                  _suggest_quantity_unit (:75-102)
                  _ACTIVITY_KEYWORDS first match (:39-47, :147-150)
              → ONE FLAT record (:238-248)
          completeness gate (:438) ; optional AI (:404-437, _run_ai_candidate :521)
          advance_stage(extracted_data=…, automation_extracted_data=…) (:485-508)
          _audit_extraction (:617-659)
      _map      (:665)   → targets = line_items or [dict(extracted)] (:684-685)
      _validate (:794)
      _calculate(:945) → request_ids per index (:970-979) → _calculate_line (:1055)
      → review (D5) → completed
```

IMAGE is identical via `_extract_image` (`services/automatic_extraction.py:291-313`).

### 4.2 Path classification (V3 production vs legacy vs dead vs test-only)

| Path | Class | Basis |
|---|---|---|
| `automatic_extraction._extract_pdf` / `_extract_image` → `suggest()` | **V3 PRODUCTION** | reached from `POST /api/v3/uploads` → durable job |
| `ai_document_extraction.AIDocumentExtractionEngine` | **V3 production, conditionally unreachable** | `automatic_processing.py:404-437`; `infra/ai_runtime.py:43-63` |
| `_extract_csv`/`_extract_xlsx` → `_rows_to_line_items` | **V3 PRODUCTION, line-aware** | `automatic_extraction.py:349-471` |
| `pdf_engine.PDFExtractor.extract_and_parse(_image)` + `_parse_utility_bill`/`_parse_fuel_invoice`/`_parse_scope3_document` | **LEGACY, reachable, non-V3** | `routes/upload.py:184,272,301,552`; mounted `main.py:212`; legacy frontend `UploadManager.js:216`, `App.js:957` |
| `engines/extraction.DocumentExtractionEngine.extract()` (pages/tables) | **not production for PDF/IMAGE** (only `suggest_fields` is used); `extract()` used by V2.1 `engines/workflow.py`, no production constructor outside tests | `engines/__init__.py:23` |
| `engines/ai_extraction.AIExtractionEngine` | **not V3 production** (V2.1 workflow + tests) | `engines/workflow.py:61` |
| `pdf_engine._parse_scope3_document` | **dead / unimplemented** | `pdf_engine.py:300-315` |
| `suggest()` | shared deterministic single-line pass | `_extract_pdf`, `_extract_image` |

## 5. Current-state findings

| ID | Finding | Tag | Evidence |
|---|---|---|---|
| F-P1-1 | The deterministic PDF/IMAGE path models the whole document as **one record**; there is no line/row abstraction anywhere in it | [OBSERVED] | `automatic_extraction.py:226-248, 291-313`; `extraction_suggestions.py:105-161` |
| F-P1-2 | `activity` and `quantity`/`unit` are chosen by **two independent whole-document scans** with different selection rules (keyword-tuple order vs text order), so they can describe different source rows | [OBSERVED] | `extraction_suggestions.py:39-47, 75-102, 147-150` |
| F-P1-3 | `_suggest_quantity_unit` scans only **key/value field values**, never data rows | [OBSERVED] | probe §6.2 |
| F-P1-4 | `_suggest_quantity_unit`'s fallback to all field values is **dead** when a quantity-like key exists but is unparseable | [OBSERVED] | `extraction_suggestions.py:83-98`; probe §6.2 |
| F-P1-5 | `_completeness` measures **field presence of the produced record**, not source coverage, so a lossy flat record scores 1.0 | [OBSERVED] | `automatic_extraction.py:179-195` |
| F-P1-6 | The AI rescue is gated on that score (`< 0.5`), so AI is suppressed exactly when the document is lossy | [OBSERVED] | `automatic_processing.py:404-409`; `domain/automatic_processing.py:52` |
| F-P1-7 | The AI engine is **optional and possibly absent** (3 env vars; not present in repo env files; Render config NOT VERIFIED) | [OBSERVED]/[U] | `infra/ai_runtime.py:43-63`; env var-name scan; Render config doc §4 |
| F-P1-8 | The AI merge is **positional**, can drop all deterministic identity fields, and can fabricate cross-line field pairs | [OBSERVED] | `automatic_processing.py:154-200`; probes §6.3 |
| F-P1-9 | The AI text layer is clipped to 20 000 chars (`DEFAULT_MAX_TEXT_CHARS`) although `extract_document_text` returns up to 200 000 | [OBSERVED] | `ai_document_extraction.py:39, 206`; `automatic_extraction.py:531, 538` |
| F-P1-10 | AI output is capped at `max_tokens=1024`, a hard bound on the number of lines an AI pass can return | [OBSERVED] | `ai_document_extraction.py:212` |
| F-P1-11 | A reachable **legacy** extraction+emissions path exists (`/api/upload*`, `pdf_engine`) with hard-coded factor multipliers, hard-coded demo assets, fuel-type aggregation (not line-level) and an unimplemented Scope 3 parser | [OBSERVED] | `pdf_engine.py:192, 227-298, 300-315`; `routes/upload.py:211-214` |
| F-P1-12 | `rapidocr_onnxruntime` and `pypdfium2` (the ONNX OCR fallback) are **not declared** in `requirements.txt` or `backend/requirements.txt`, yet `_onnx_ocr`/`_render_pdf_pages_pypdfium` depend on them | [OBSERVED] | `automatic_extraction.py:150-176, 251-269`; requirements files |
| F-P1-13 | The digital text layer discards page boundaries (`"\n"` join); `[page N]` markers exist only on the OCR path | [OBSERVED] | `pdf_engine.py:60-72` vs `:90` |
| F-P1-14 | `mapped_data.line_items` is **overwritten** with per-line calculation results on the ops path, so it is not a durable source of original line identity | [OBSERVED] | `api/v3_operations.py:571-576` |
| F-P1-15 | The automatic and ops paths write **different semantics** into the same `mapped_data.line_items` key (mapping records vs calculation results) | [OBSERVED] | `automatic_processing.py:1029` vs `api/v3_operations.py:571-576` |
| F-P1-16 | `source_location` (sheet/row/column/json_path) has **no persistence anywhere**; `domain/evidence.py` reads it from a snapshot key that no migration creates, so it is always absent | [OBSERVED] | `domain/evidence.py:150-155`; zero `source_location` in any `.sql` |
| F-P1-17 | The frontend **already** has a line-item editor and always posts `line_items` (seeded with one empty line when none exist) — so `line_items[]` is already the human contract, contradicting the predecessor's "no line-level surface" statement | [OBSERVED] | `ExtractionPanel.jsx:98-110, 237-241`; `ProcessingItemWorkspace.jsx:107-115, 247`; `api/v3_operations.py:1648-1664` |
| F-P1-18 | `reenqueue(stage="extracting")` is a **silent no-op** for a job that already has `extracted_data` (the resume marker), and no operation exists to clear/supersede an extraction | [OBSERVED] | `automatic_processing.py:364-370`; `data/document_processing.py:471-501` |
| F-P1-19 | The CSV/XLSX path is line-aware but treats row 1 as a header unconditionally; a headerless CSV silently loses its first data row | [OBSERVED] | `automatic_extraction.py:413-414`; probe §6.4 |
| F-P1-20 | The CSV path does not canonicalise units from cells (`kwh` stays lowercase) while the AI path uses `core.units.normalize_unit` | [OBSERVED] | `automatic_extraction.py:137-143`; `ai_document_extraction.py:71-76`; probe §6.4 |

## 6. Root-cause analysis (with reproducible evidence)

### 6.1 Root cause

**The deterministic PDF/IMAGE extractor represents a document as one record, and the pipeline's only gate
measures that record's field completeness. Nothing in the architecture represents "how many lines the
source contains", so line loss is invisible by construction — and the AI path that could recover lines is
switched off by the very score the loss inflates.** [INFERRED, from F-P1-1…F-P1-6]

### 6.2 Execution evidence — the real production entry point

An 8-line, single-page invoice PDF was generated (reportlab) and passed through the **unmodified**
`services.automatic_extraction.extract_document`:

```
envelope: {"status": "ok", "method": "pdf_text", "page_count": 1,
           "unresolved": ["supplier"], "confidence": 1.0}
extracted_data: {"invoice_number": "INV-10482", "date": "14/03/2026",
                 "net_amount": "2800.00", "quantity": 38.4, "unit": "m3",
                 "activity": "Waste"}
```

* 8 source lines → **1** extracted object. `[OBSERVED]`
* `activity="Waste"` comes from one source line; `quantity=38.4 / unit="m3"` comes from a different
  source row (`Total consumption: 38.4 m3`). This reproduces the previously recorded `Waste + 38.4 m³`
  observation exactly. `[OBSERVED]`
* `confidence = 1.0` ⇒ `1.0 < 0.5` is **False** ⇒ the AI branch at `automatic_processing.py:404-409` is
  **not entered**. `[OBSERVED]`

`_suggest_quantity_unit` returned `(None, None, ["quantity/unit"])` for the same text **without** the
`Total consumption:` key/value line, proving quantity/unit is never taken from data rows (F-P1-3) and that
the `or list(fields.values())` fallback cannot run while a quantity-like key exists but is unparseable
(F-P1-4 — proven separately with `consumption: "unreadable-glyph"` alongside `diesel: "500 litres"` →
`(None, None, ["quantity/unit"])`, discarding a perfectly readable quantity). `[OBSERVED]`

### 6.3 Execution evidence — the merge fabricates and discards

`_merge_extraction_candidates` probed directly:

* deterministic flat record + AI `line_items` → returned `{"line_items": [...]}` with the deterministic
  `supplier`, `invoice_number` and `date` **discarded entirely**. `[OBSERVED]`
* deterministic lines `[{General waste, 12.5, tonnes}, {Diesel}]` + AI lines in a different order →
  `[{General waste, 12.5, tonnes}, {Diesel, 12.5, tonnes}]` — the Diesel line now asserts a quantity lifted
  from the waste line, i.e. **fabricated cross-line data**. `[OBSERVED]`

### 6.4 Execution evidence — the tabular path for contrast

`extract_document` on `activity,quantity,unit / Diesel,100,litres / Electricity,250,kWh` returns two
`line_items` with `confidence = 1.0` — the capability already exists for CSV/XLSX. A headerless CSV returns a
single orphan `{"unit": "kwh"}` line (first data row consumed as header), and units from cells are not
canonicalised. `[OBSERVED]`

### 6.5 Why the loss survives to the database

Each extracted target yields exactly one request id and one snapshot
(`automatic_processing.py:684-685, 962-979`), so the collapsed record becomes exactly **one** immutable
snapshot and **one** emissions log — the point at which traceability is lost is upstream of persistence, as
the predecessor concluded (its §18 "Primary = A (extraction)"). This investigation confirms that conclusion
and adds the *mechanism* and the merge-side fabrication.

### 6.6 Contradictions / refinements reported explicitly

1. **Refinement of the predecessor's §8–§9 attribution.** The deterministic quantity is the first
   `<number><unit>` token in the first *quantity-like key/value field value* — normally a document-level
   **aggregate** (`Total consumption: …`) — not a row value. With no such key, quantity is *unresolved*, not
   row-derived. Primary classification upheld; specific attribution refined. [OBSERVED]
2. **Contradiction of the predecessor's §14.** The predecessor states the UI has "no line-level breakdown
   surface". In fact both `ExtractionPanel.jsx` and `ProcessingItemWorkspace.jsx` render and post a
   `line_items` editor, and the ops save endpoint accepts free-form `extracted_data`
   (`api/v3_operations.py:1648-1664`). The usability defect is narrower than recorded: the flat record is
   rendered *and* a line editor exists, so a human can repair the collapse manually — but the *machine*
   path never produces lines. [OBSERVED]
3. **`source_page` writer count.** The predecessor/B2 record names
   `automatic_processing.py:1134` and `v3_processing_workflow.py`. This investigation finds **four** writers
   (two of them legacy client-facing contracts) and confirms `page_count` — not a page number — is the value
   in the automatic path (§8). [OBSERVED]
4. **Known fact 17 (silent re-extraction prohibited) is reinforced**, not contradicted: no mechanism for
   explicit re-extraction exists at all today (F-P1-18). [OBSERVED]
5. Known facts 1–16 were otherwise **not** disproved. [OBSERVED]

## 7. `source_page` finding (separate investigation, as required)

### 7.1 Exact source of the value

`job.metadata["page_count"]` ← `api/v3_documents.py:341` ← `page_count = _pdf_page_count(content)` for PDFs
(`api/v3_documents.py:317`, implemented `:125-143`; pdfplumber page count with a `/Count` regex fallback and
a `max(1, …)` default) or the literal `1` for non-PDFs. `[OBSERVED]`

### 7.2 Every writer

| # | Writer | Value | Validation |
|---|---|---|---|
| W1 | `services/automatic_processing.py:1134` — `source_page=job.metadata.get("page_count")` | **page COUNT** | none (it is metadata) |
| W2 | `api/v3_emissions.py:689` ← contract `:122` | caller-supplied integer | **none** (no `ge=1`) |
| W3 | `api/business.py:143` ← contract `api/contracts.py:223` | caller-supplied integer | **none** |
| W4 | `api/v3_processing_workflow.py:896` ← contract `:139` | caller-supplied integer | **none** (`Optional[int]`) |
| — | `api/v3_operations.py:_run_line_calculation` (`:529-560`) | **never set** → NULL | n/a |
| — | `engines/calculation.py:329, :499`; `domain/calculation.py:59` | plumbing | n/a |

DB: `supabase/migrations/20260823010000_d33_evidence_traceability.sql:26` adds `source_page integer` with
**no CHECK constraint** (unlike B2's planned `CHECK (source_page IS NULL OR source_page >= 1)`). `[OBSERVED]`

### 7.3 Every consumer

| # | Consumer | Behaviour on non-NULL | Evidence |
|---|---|---|---|
| C1 | Evidence completeness | `has_page = page is not None` ⇒ **COMPLETE** ("Document + extracted line + source page + calculation + factor") | `domain/evidence.py:145, 160-167, 26-47` |
| C2 | Evidence location precision / technical details | presented as `page N`; `technical_details.source_page` | `domain/evidence.py:54-103, 330` |
| C3 | Export label | COMPLETE vs PARTIAL | `data/exports.py:45-59` |
| C4 | Audit-readiness aggregate | counted as `complete` | `data/reporting.py:1093-1103` |
| C5 | Reporting read model | selected/surfaced | `data/reporting.py:1166` |
| C6 | Snapshot read model + APIs | exposed | `data/emissions_logs.py:324, 493`; `api/contracts.py:289`; `api/v3_emissions.py:505` |
| C7 | UI | "Source page" tile | `frontend/src/v3/components/EvidenceRecordPanel.jsx:87-88` |

### 7.4 Semantic contract and conflation

**There is no single semantic contract.** `source_page` currently means "page count" (W1), "a
caller-asserted page" (W2–W4), or NULL. It is conflated with `page_count` in exactly one place (W1) but is
conflated *conceptually* everywhere, because no consumer distinguishes the provenances. `[OBSERVED]`

**Does any path store a true page number?** No. `[OBSERVED]` Page boundaries are discarded on the digital
path (F-P1-13) and `[page N]` markers are never parsed into structured output.

**Other conflations found:** (a) `report_generation_queue` / `generated_reports` also carry a `page_count`
(`data/reports.py:36-54`) — a *different* meaning of "page" in the same codebase, not conflated with
`source_page` but a naming hazard; (b) `organization_files.metadata.ocr.page_count` vs
`document_processing_queue.page_count` vs `manual_extraction_items.page_count` are three independent copies
of the same document fact. `[OBSERVED]`

### 7.5 Effect on evidence classification, audit and provenance

An automatically processed **multi-page** PDF is presented, exported and aggregated as evidence with an
**exact** source page that is actually the page count. Single-page PDFs are unaffected (count = 1 = a valid
page number), which is why the defect is invisible on the common case. Additionally, because W2–W4 accept an
unvalidated client integer, an authenticated staff user can assert a page and lift an emission to COMPLETE
evidence with no verification — an evidence-integrity (not access-control) issue. `[INFERRED]`

### 7.6 Correct future data model (conceptual — not implemented)

Separate the concepts: `page_count` (document extent; ingest metadata only), `page_number` (genuine 1-based
per-line page; P1's new producer → B2 §11.7 `page` → `evidence_line_items.source_page`), source-row ordinal
(array index → B2 `line_number`), `row_reference` (printed reference; stays NULL per B2-D8), and
`bounding_box`/`text_span` (extraction-internal only, never persisted).

### 7.7 Which workstream owns the remediation — determination

**It belongs to a separate provenance/evidence remediation, NOT to P1, and not to B2.** Reasons: B2-D4
(CLOSED) already deferred it to a separate bounded workstream; fixing it changes evidence classification for
**existing** persisted rows; and this task explicitly forbids altering `source_page` or evidence
classification. **P1's obligation is the producer side only:** emit a genuine per-line `page` (or nothing),
and never write `page_count` into any location field. Sequencing and ownership are recorded as
**[DECISION REQUIRED] P1-D5**. `[RECOMMENDED]`

## 8. Target architecture

1. **A new bounded "row-candidate" sub-stage** in the deterministic PDF/IMAGE extractor, built only on the
   text layer already produced (pdfplumber `extract_tables()` → else `extract_words()` clustered by `top`;
   OCR text lines as candidates), declaring **multi-line** only when ≥2 independent row candidates share the
   same extracted shape. `[RECOMMENDED]`
2. **`extracted_data.line_items[]` remains the single canonical line contract**, with the B2-recognised key
   vocabulary plus optional per-line `page` / `extraction_method` (B2 §11.7). Flat **or** lines, never both;
   never a single placeholder line. `[RECOMMENDED]`
3. **A coverage block at the envelope level** (`shape`, `source_row_candidates`, `lines_extracted`,
   `coverage_ratio`, `ambiguous_fields`) recorded in job metadata + audit, so line loss becomes observable
   rather than invisible. `[RECOMMENDED]`
4. **A structure-aware AI decision table** replacing the single confidence trigger, using the existing AI
   engine and the existing completeness score (whose semantics are unchanged). `[RECOMMENDED]`
5. **Document-level adjudication instead of positional blending** in
   `_merge_extraction_candidates`: accept one candidate whole, retain both as evidence, record the choice.
   `[RECOMMENDED]`
6. **No change** to persistence shapes, schema, RLS, calculation, factor matching, B2, or `source_page`.
   `[RECOMMENDED]`
7. **Per-line page emission** so the evidence workstream (P1-D5) has a truthful producer. `[RECOMMENDED]`

Full normative detail: contract §§6–14.

## 9. Alternatives considered (Q5)

| Option | Verdict | Reason |
|---|---|---|
| A. Deterministic only | Insufficient alone | the defect persists with no rescue |
| B. AI only | Rejected | AI is optional/unverified (F-P1-7); non-deterministic; hallucination risk; no output when unconfigured |
| C. Deterministic-first + conditional AI fallback (structure-aware) | **RECOMMENDED** | deterministic default; AI only on multi-line-suspect documents; bounded cost |
| D. Deterministic + AI field-level reconciliation (as currently coded) | **Rejected as implemented** | proven to discard deterministic identity and to fabricate cross-line field pairs (F-P1-8) |
| D′. Deterministic + AI **document-level** adjudication | **RECOMMENDED** (the reconciliation rule inside C) | one candidate accepted wholly; disagreement visible; no blending |
| E. Mandatory AI on every document | Not recommended | highest cost, non-determinism on clean documents, no accuracy justification |

## 10. Recommended architecture

**C + D′** — deterministic-first with a structure-aware AI trigger and document-level adjudication; coverage
recorded and used instead of field-presence alone; `line_items[]` as the single canonical contract; per-line
`page` emitted honestly; nothing else changed. See contract §7.5 and §8.

## 11. B2 boundary

**P1 provides:** (1) real `line_items[]` with ≥1 recognised B2 key per element for genuinely multi-line
documents; (2) source order / stable ordinals (= B2 `line_number`); (3) optional per-element `page` ≥1 and
`extraction_method`; (4) `unit` as read (B2 `raw_unit`); (5) flat **or** lines, never both; (6) the flat
record unchanged for genuine single-line documents.

**P1 must not:** touch `evidence_line_items`, `calculation_snapshots.source_line_item_id`,
`disclosure_value_evidence`, or any B2 migration; emit `line_reference` (no producer → B2-D8 keeps
`row_reference` NULL); emit bounding boxes/confidence/other Class-C fields into the element; emit synthetic
lines for flat records; require B2 to change.

**B2 must not change:** no re-parsing, no re-extraction, no inference from aggregates, no `mapped_data`
identity, no retro-linking of historical snapshots. The P1↔B2 interface is exactly B2 contract §11.1/§11.2 /
§11.7 — no more, no less. **Neither workstream may be used to widen the other.** [OBSERVED for the interface;
RECOMMENDED for the boundary]

## 12. EF-E boundary

EF-E (exact-unit-equality in the processing mapping picker) is a **confirmed independent defect**
(`CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912` §9–§11) belonging to batch **P2**. P1 does **not**
redesign `FactorMatchingEngine`, does not change factor precedence, and does not touch unit matching.
**Documented dependency only:** P1 changes the *inputs* the matcher receives (per-line `(activity, unit)`
pairs). Better inputs will make EF-E *more visible* (a correct line can still fail on exact-unit equality),
which is an argument for keeping the two batches separate, not for bundling them. [OBSERVED]

## 13. Historical-data policy

| Class | Policy |
|---|---|
| H1 flat PDF/IMAGE records (no persisted `line_items[]`) | **Unchanged by default.** Evidence stays PARTIAL/UNAVAILABLE. No transformation, no inference, no manufactured lines |
| H2 records with persisted `line_items[]` (CSV/XLSX, AI-line, human line entry) | unaffected; already B2-eligible |
| H3 explicit re-extraction of an H1 record | only as a **separate, explicit, audited, per-document** operation: never overwrite `automation_extracted_data` (write-once), record actor/reason/timestamp/version/line counts, never rewrite snapshots, never run from a read/report/B2 backfill |
| H4 bulk historical reprocessing | **[DECISION REQUIRED] P1-D4** — recommendation: **not at all** in P1 |

**Precondition discovered:** `reenqueue(stage="extracting")` does not re-extract (F-P1-18), so an explicit
supersede operation must be designed and authorised separately; it cannot be a side effect of the extraction
change. [OBSERVED]

## 14. Test / verification contract

18 mandatory cases (single-line PDF; multi-line PDF; multi-page invoice; table invoice; image invoice;
scanned PDF; OCR-poor document; mixed activity/unit lines; confidently-correct deterministic document;
incomplete deterministic document; **deterministic-appears-complete-but-lossy**; AI/deterministic
disagreement; repeated extraction; corrected extraction; historical flat PDF; historical `line_items[]`;
page number vs page count; provenance preservation) — full mapping in contract §16.1. Layers: unit
(extractor, decision table, adjudication), DB-backed integration (pipeline end-to-end, one snapshot per
line; failure/idempotency; negative assertions), and the §16.3 amendment list. **Runtime/database-backed
verification is required** wherever persistence or downstream behaviour is involved; static-only tests are
insufficient. Existing suites were run read-only during this task: `test_extraction_suggestions.py` +
`test_automatic_extraction.py` + `test_automatic_extraction_text_layer.py` = **21 passed**. [OBSERVED]

**Existing tests that must be AMENDED, NEVER DELETED** (mirroring B2-D3/§20.6 practice): the four
`test_suggest_*` cases that pin the single-document contract, the public `completeness_score` semantics test,
the `test_merge_*` blending tests (whose blending assertions must be removed deliberately and documented),
and the CSV/XLSX tests (unchanged). Contract §16.3.

## 15. Migration / data implications

**No migration. No schema change. No new table/column. No RLS change. No data mutation.** Per-line `page`
and `extraction_method` travel inside existing JSONB; the coverage block is envelope/job-metadata only (so it
cannot perturb B2's `payload_hash`, which covers only recognised element keys). No historical backfill.
**Two consequences to record:** (a) `automation_extracted_data` write-once means a re-extracted historical
document keeps its original flat machine output permanently while its working `extracted_data` becomes
line-aware — truthful history, but must be expected by evidence/UX layers; (b) adding any key to a line
element changes `_calc_payload_digest` (`automatic_processing.py:74-92`), so a re-extraction deliberately
produces **new** snapshots via the existing G6-D rule, and cosmetic keys must never be added. [OBSERVED]

## 16. Implementation scope

**IN:** `services/automatic_extraction.py` (row-candidate sub-stage, wiring, coverage block, "flat or lines"
rule); `services/automatic_processing.py` (decision table, adjudication, coverage in audit/metadata);
`domain/automatic_processing.py` (`PIPELINE_VERSION` bump, trigger constants);
`services/ai_document_extraction.py` (only if prompt/limits need bounded adjustment — no new engine);
tests + docs.

**OUT [OUT OF SCOPE]:** B2 objects/migrations; `calculation_snapshots.source_line_item_id`;
`source_page` semantics and evidence classification; `engines/factor_matching.py` and EF-E;
`engines/calculation.py` and request-id derivation; RLS/auth; billing; retention; frontend/manual-extraction
UI; `routes/upload.py` + `pdf_engine.py` legacy surface; historical bulk reprocessing;
`pdf_engine._parse_scope3_document`.

## 17. Unresolved PO decisions

| ID | Decision |
|---|---|
| **P1-D1** | Authorise the extraction **shape** change for new documents (multi-line PDF/IMAGE ⇒ `line_items[]`), gated on shadow evidence? |
| **P1-D2** | When multi-line is detected but AI is unavailable/failed: **block for human review** (recommended) or continue as single-line? (Not deciding = the defect persists) |
| **P1-D3** | May AI run **per page/chunk** for long documents (bounded cost), or stay single-call over a 20 000-char clip? |
| **P1-D4** | Historical reprocessing: per-document opt-in, admin bulk batch with dry-run, or not at all (recommended)? |
| **P1-D5** | Ownership/sequencing of the `source_page` remediation vs P1's new `page` producer, and who reclassifies historical evidence? |
| **P1-D6** | Is the reachable legacy `/api/upload*` + `pdf_engine` surface (hard-coded factors, incomplete Scope 3) in scope for a deprecation/consolidation review? |
| **P1-D7** | May OCR-marker-derived (lower-trust) pages be emitted as per-line `page`? |
| **P1-D8** | Are AI-extracted lines acceptable as B2 evidence lines when explicitly stamped `ai:*` / `{det}+{ai}`? |

## 18. Risks

| # | Risk | Tag |
|---|---|---|
| R1 | Coverage heuristic misclassifies (multi-column fusing, OCR wrapping, single-line header blocks) and either loses lines again or triggers needless AI/review | [INFERRED] |
| R2 | Increased AI usage raises external-LLM data exposure and cost; document text leaves the platform | [OBSERVED] (existing behaviour; frequency change is) [INFERRED] |
| R3 | AI unavailability silently reverts to the lossy behaviour unless P1-D2 is decided | [OBSERVED] |
| R4 | `_calc_payload_digest` sensitivity creates additional snapshots on re-extraction; must not be mistaken for duplicate-prevention failure | [OBSERVED] |
| R5 | Undeclared OCR dependencies (`rapidocr_onnxruntime`, `pypdfium2`) mean the scanned path may not exist in a clean deploy | [OBSERVED] |
| R6 | Sibling/parallel batch collisions (B2, P2/EF-E, source_page workstream) if boundaries are not enforced | [INFERRED] |
| R7 | The legacy `/api/upload*` path continues to bypass the authoritative calculation engine with hard-coded factors | [OBSERVED] |
| R8 | Evidence currently claims a **false** exact page for auto-processed multi-page PDFs (existing data) | [OBSERVED] |

## 19. Dependency / blocker matrix

| Item | Depends on | Status |
|---|---|---|
| P1 implementation | PO authorisation + P1-D1/P1-D2 (shape + AI-unavailable policy) | **BLOCKED — PO decision** |
| Row-candidate detection | nothing external (pdfplumber already a dependency) | ready to implement (not authorised) |
| Coverage/observability | existing audit + job metadata | ready (not authorised) |
| AI decision table | `configured_ai_extraction_engine()` availability in the target environment | **[U]** — Render env NOT VERIFIED |
| Shadow/observation rollout | no new capability required | ready (not authorised) |
| B2 implementation | independent of P1 (B2 §1.2); interface already declared (§11.7) | ready (separately authorised) |
| `source_page` remediation | P1's `page` producer (P1-D5) + its own authorisation | **BLOCKED — separate workstream, PO decision** |
| EF-E (P2) | nothing from P1; must not be bundled | separate batch |
| Historical re-extraction (H3/H4) | a designed supersede operation (F-P1-18) + P1-D4 | **BLOCKED — PO decision** |
| Legacy `/api/upload*` review | P1-D6 | **BLOCKED — PO decision** |
| OCR dependency declaration | deployment change authorisation | **BLOCKED — separate change** |

## 20. Explicit verdict

**`P1 FORENSIC + REMEDIATION CONTRACT COMPLETE — READY FOR PO REVIEW`**

* Root cause established, with an **execution-level reproduction** through the real production entry point
  (8 source lines → 1 object at completeness 1.0, AI suppressed) and unit-level proof of the merge
  fabrication and the dead quantity fallback.
* Five predecessor statements are refined or corrected explicitly (§6.6) — notably that the deterministic
  quantity normally comes from a **document-level aggregate field**, not a data row, and that a frontend
  line-item editor **does** exist. None of these changes the predecessor's primary classification
  (Primary = extraction).
* The `source_page` defect is fully enumerated (4 writers, 7 consumers, no writer produces a true page
  number, DB has no `CHECK`) and is allocated to a **separate provenance/evidence remediation**, with P1
  supplying only the genuine per-line `page` producer.
* The remediation contract is **bounded**: no new dependency, no schema change, no new AI engine, no new
  calculation engine, no unrestricted parser, no rules engine, no historical re-extraction.
* **Eight PO decisions (P1-D1…P1-D8) remain open**; implementation is **not** authorised.

**Not implemented. Not verified in production. No commit. No push.**
