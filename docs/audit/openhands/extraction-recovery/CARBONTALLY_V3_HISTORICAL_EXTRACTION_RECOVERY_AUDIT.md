# CarbonTally V3 — Historical PDF / Image / OCR Extraction Recovery Audit

| | |
|---|---|
| Audit type | Independent, read-only historical extraction recovery audit |
| Auditor | OpenHands (DeepSeek) |
| Repository | https://github.com/shomonrobie/CarbonTally |
| Canonical baseline | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`, 2026-08-25) |
| Audit clone | `/tmp/audit_carbontally_publish/repo` (fresh clone of `origin/main`; working tree otherwise untouched) |
| Product Owner decision baseline | `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (present in developer working dir only — not committed; decision §5.2 read read-only) |
| Status | READ-ONLY. No commits. No pushes. No file modifications to the repository. |

---

# 1. Executive Summary

**The Product Owner's claim is substantially correct in its essence but must be qualified:**

1. **CarbonTally DID have a working PDF **and** image OCR extraction implementation in early development (committed 2026-07-21).** The engine (`backend/pdf_engine.py`, `PDFExtractor`) and the HTTP routes (`/upload-pdf`, `/upload-image`, `/upload-batch`) existed, were wired to a real frontend (`PDFIngestionPortal.jsx`), and were exercised against at least one real fuel-invoice image committed to the repository (`uploads/uk-fuel-invoice-1.png`).

2. **What happened during the V3-era migration is a disconnection, not a deletion.** The engine file survived almost byte-for-byte; what was lost was **wiring**:
   - The dedicated `/upload-image` route was **removed** at commit `c09ad51` (2026-07-27), while the frontend kept calling it — image OCR became unreachable (dead endpoint → 404).
   - The consolidated `/upload` route that replaced it calls the **PDF method (`extract_and_parse`) for image files too** — a dispatch regression that still exists today in `backend/routes/upload.py`.
   - The correct image dispatch survives only in the **backup files `backend/main copy.py` / `main copy 2.py`** and in git history.

3. **The scanned-PDF OCR path was broken as written from its first commit.** `PDFExtractor._extract_text_ocr` calls `pdf2image.convert_from_path(io.BytesIO(...))`, which `pdf2image` never accepted (it requires a path; the bytes API is `convert_from_bytes`). Verified live in this environment: `TypeError`. The exception is swallowed, so scanned PDFs silently return "Could not extract text". This is a small, well-understood defect, not an architectural gap.

4. **"AI extraction" was never implemented in early development** — the 2026-07-24 commit message ("CSV, PDF, Image upload with AI extraction") is aspirational wording for the deterministic regex parser + Tesseract OCR + human review queue. An actual `AIExtractionEngine` (LLM) was written later (Phase 7, 2026-08-07) but has never been wired to any HTTP route in any commit.

5. **No committed test ever exercised PDF/image/OCR extraction — historically or today.** "Tested during early development" is therefore **NOT PROVEN FROM GIT HISTORY** as automated testing. What the evidence supports is *exercised in development* (real committed fixtures, working UI, live route wiring) rather than *covered by an automated test suite*.

6. **Recovery is low-risk and mostly re-wiring.** The digital-PDF path works today (verified against a real DEFRA PDF). The image path needs a 1-line re-wire plus a production OCR runtime. The scanned-PDF path needs a 1-line API fix plus page tracking. No component requires a from-scratch rebuild, consistent with decision §5.2 (D → B).

---

# 2. Product Owner Historical Claim

From `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (§5.2 "Historical document extraction — LOCKED ENGINEERING DIRECTION", read read-only from the developer working directory — the file is **not committed** to the canonical repo):

> "CarbonTally had PDF/image extraction functionality early in development. Do NOT assume that current V3 route gaps mean the historical functionality never worked. First: 1. locate historical extraction implementation; 2. locate historical tests; 3. locate sample inputs/expected outputs; 4. determine what still works; 5. identify what was lost or disconnected during V3 migration; 6. reuse/fix sound historical implementation. Only rebuild functionality where the historical implementation is unsuitable."

The target workflow (§5.3, LOCKED): Upload → File Classification → PDF/Image Processing → OCR when required → Internal/Local AI-assisted extraction where appropriate → Human correction → Mapping → Processing Entity Validation/Review/QC → CarbonTally Validation/Review/QC → Calculation → Evidence → Customer Final Approval.

**This audit executes steps 1–6 of §5.2.**

---

# 3. Historical Git Evidence

## 3.1 Repository timeline (all dates from `git log --date=short`)

| Commit | Date | Significance for extraction |
|---|---|---|
| `b322ab3` | 2026-07-17 | Clean-slate monorepo. **CSV-only**: `process_emissions.py`, `main.py` (191 lines), sample messy CSVs, `clean_emissions_output.json`. No PDF/OCR code. |
| `134a1d2` | 2026-07-21 | **First extraction commit.** `pdf_engine.py` (337 lines, root + `backend/`), `backend/main.py` (1,465 lines), routes `/upload-csv`, `/upload-pdf`, **`/upload-image`**, `/upload-batch`, `/approve-pdf-batch`; frontend `PDFIngestionPortal.jsx` (348 lines), `BulkUpload.jsx`, `StaffDashboard.jsx`; fixture `uploads/uk-fuel-invoice-1.png`. |
| `77b15fa` | 2026-07-24 | "Feature complete: CarbonTally v3.0 … CSV, PDF, Image upload with AI extraction …". `/upload-image` → `extract_and_parse_image` (correct dispatch). |
| `c09ad51` | 2026-07-27 | "Major update: Manual Entry, Staff Review Queue, Admin Assignment, Document Status, and Log Viewer". **`/upload-image` removed**; new consolidated `routes/upload.py` `/upload` route dispatches **both PDF and IMAGE to `extract_and_parse`** (regression). Frontend `PDFIngestionPortal.jsx` still posts to `/upload-image`. |
| `de94363`/`00cff1d`/`eed55d6` | 2026-08-04/06 | RC1/RC2 database baselines. `backend/tests/` first appears (ad-hoc smoke scripts). |
| `ea5eddd` … `fafa94b` | 2026-08-07/08 | Phases 0–8 (V2.1 architecture): `engines/` (extraction, ai_extraction, matching, matching_stages, calculation, validation, workflow, report_generation), `data/` repositories, `tests/unit`, `tests/integration`. `AIExtractionEngine` created — never wired to a route. |
| `d3af816` | 2026-08-14 | "checkpoint: verified V2.1 and V3 database foundation". |
| `38ae49e`/`840e14a` | 2026-08-15 | V3 baseline / Render-ready backend checkpoints. |
| `d4dcca1` | 2026-08-25 | `feat(v3): commit D20-D37 commercial platform release` — current canonical baseline. |

## 3.2 Key historical file evidence

- **`pdf_engine.py` is essentially unchanged from `134a1d2` to `d4dcca1`.** `git diff 77b15fa d4dcca1 -- backend/pdf_engine.py` shows only one comment line (`#backennd\pdf_engine.py`) and a trailing-newline difference. The engine was **never modified** during the V3 transition.
- **`extract_and_parse_image` has existed continuously** in `backend/pdf_engine.py` from `77b15fa` to `d4dcca1`, and is **called by nothing** in the current tree (verified with `grep`): it is dead code today.
- **`/upload-image` route timeline** (verified by `grep "def upload_image"` per commit): present at `134a1d2` and `77b15fa` (in both root `main.py` and `backend/main.py`); **absent** from `c09ad51`, `eed55d6`, `840e14a`, `d4dcca1`.
- **Backup copies preserve the correct dispatch**: `backend/main copy.py:973` and `backend/main copy 2.py:1308` contain `extraction_result = pdf_extractor.extract_and_parse_image(` guarded by `file_type = 'PDF' if file.filename.lower().endswith('.pdf') else 'IMAGE'`. These backup files are still present in `d4dcca1`.
- **Pre-commit evidence**: commit `134a1d2` also contains `__pycache__/pdf_engine.cpython-314.pyc` (5,034 bytes) — an **earlier, smaller compiled `pdf_engine`** that predates the committed 337-line source (the backend copy's `.pyc` is 15,363 bytes, matching the committed source). `strings` on the old `.pyc` already shows `_extract_text_ocr`, `extract_and_parse_image`, `Tesseract OCR Engine v2.4`, `image_to_string` — the OCR design predates the first committed source.

---

# 4. Historical PDF Extraction

**Commit of record:** `134a1d2` (2026-07-21) — `backend/pdf_engine.py`, class `PDFExtractor`.

- **Digital PDF text extraction** — `PDFExtractor.extract_and_parse()` → `_extract_text_direct()` uses `pdfplumber.open(io.BytesIO(pdf_bytes))`, extracting text per page. This is sound code that needs no external binary.
  - **Verified live in this audit** against a real PDF (`tools/carbon_data_factory/factors/Carbon-Dioxide-Calculation-Factors-for-2025.pdf`): pdfplumber opened it, 1 page, text extracted correctly ("Version 24- December 2025 / Country Specific Net Calorific Values and CO Emission Factors…"). The digital-PDF path works.
- **Scanned-PDF fallback** — `extract_and_parse()` falls back to `_extract_text_ocr()` when extracted text is `< 50` characters. See §5.
- **Structured parsing** — after text extraction, one of three deterministic, regex-based parsers runs: `_parse_utility_bill`, `_parse_fuel_invoice`, `_parse_scope3_document`. Output schema: `{"batch_id", "file_metadata": {"filename", "file_type", "extraction_method", "page_count"}, "data_streams": [{"stream_id", "activity_type", "extracted_fields": {field: {"value", "confidence", "status"}}, ...}]}`.
  - Fuel example (`_parse_fuel_invoice`): regex per line for date (`\d{1,2}[/-]\d{1,2}[/-]\d{2,4}`), vehicle registration (`[A-Z]{2}\d{2}\s*[A-Z]{3}`), volume litres (`\d+\.?\d*\s*[Ll]`), amount (`£?\d+\.\d{2}`), fuel type keywords (diesel/petrol/adblue); groups records by fuel type into data streams.
  - Utility example (`_parse_utility_bill`): regex patterns for consumption (kWh/m³) each with a confidence score (0.9/0.6/0.4 …), billing start/end, supplier.
- **Multi-page PDF** — pdfplumber opens the whole document; OCR loops all rendered pages; but `file_metadata.page_count` is only informational. No per-page field attribution.
- **Tables** — no table-structure extraction (no pdfplumber table API usage); parsing is line-oriented regex.

**Classification: PROVEN WORKING for digital (text-based) PDFs; wiring present historically and still present today.**

---

# 5. Historical Scanned-PDF OCR

**Engine:** `PDFExtractor._extract_text_ocr()` (unchanged since `134a1d2`):

```python
images = convert_from_path(io.BytesIO(pdf_bytes), dpi=300)
for img in images:
    page_text = pytesseract.image_to_string(img)
    text += page_text + "\n"
```

**Defect (verified live):** `pdf2image.convert_from_path` requires a filesystem path (`Union[str, PurePath]`); passing `io.BytesIO` raises `TypeError: expected str, bytes or os.PathLike object, not BytesIO`. The correct API for bytes is `convert_from_bytes`. The `except` swallows the error and returns `""`, so `extract_and_parse` then returns `{"status": "error", "message": "Could not extract text from file."}`.

- This bug is present in the **first committed version** and unchanged in the current code → **scanned-PDF OCR has never worked through this production code path**.
- Tesseract itself (external binary) is additionally required at runtime; the engine hard-codes a Windows tesseract path in `__init__` with a Linux/Render fallback to PATH.
- No page/source references are preserved by the OCR loop (no page numbers attached to extracted fields).
- No OCR confidence is captured (only the regex-parser's per-field confidence).

**Classification: BROKEN AS WRITTEN since first commit. Small, well-scoped defect (1-line API fix + page tracking).**

---

# 6. Historical JPG/Image Extraction

**Engine:** `PDFExtractor.extract_and_parse_image()` (unchanged since `134a1d2`):

```python
image = Image.open(io.BytesIO(file_bytes))
text = pytesseract.image_to_string(image)
```

then the same three regex parsers as the PDF path, returning `file_metadata.file_type == "IMAGE"`, `extraction_method == "Tesseract OCR Engine v2.4"`, `page_count == 1`.

**Wiring history (the crucial part):**
- `134a1d2` and `77b15fa`: `@app.post("/upload-image")` → `pdf_extractor.extract_and_parse_image(...)` — **correctly dispatched** (verified in both `main.py` and `backend/main.py`).
- `c09ad51`: `/upload-image` **deleted**; frontend `PDFIngestionPortal.jsx:51` (`const endpoint = isImage ? '/upload-image' : '/upload-pdf';`) kept calling it → **dead endpoint**.
- Current `d4dcca1`: `backend/routes/upload.py` `/upload` route classifies `IMAGE` (`file_type in ['PDF','IMAGE']`) and calls **`extract_and_parse`** (the PDF method) for both — the image bytes are fed to pdfplumber, which fails, then to `_extract_text_ocr`, which fails; result: extraction error or empty text for JPG/PNG.
- Correct dispatch survives only in `backend/main copy.py` / `main copy 2.py` and in git history.

**Fixture:** `uploads/uk-fuel-invoice-1.png` — PNG 1641×835 RGB (verified via PIL), a fuel-invoice image committed at `134a1d2` and still in the current tree. Its existence alongside the working `/upload-image` route indicates the image-OCR path was exercised in development.

**Runtime dependency:** Tesseract binary must be installed and on PATH (or at the hard-coded Windows path). In this audit environment `tesseract` is **not** installed, so the image path could not be executed live; its code is correct and would run given the binary.

**Classification: PROVEN WORKING *as an engine*; historically WIRED (2026-07-21 → 2026-07-27); currently DEAD CODE (defined, never called).**

---

# 7. Historical Tests

**Finding: no committed test — historical or current — ever exercised PDF/image/OCR extraction.**

- Early era (`77b15fa`, `c09ad51`): the only test files in the tree are the default React `frontend/src/App.test.js` and `setupTests.js` (template smoke test). No backend tests exist.
- RC2 era (`eed55d6`): `backend/tests/` appears with ad-hoc scripts — `test_all_endpoints.py`, `test_api.py`, `audit_code.py`, `check_imports.py`, `create_test_users.py`, `setup_test_data.py`, etc. `test_all_endpoints.py` references only `GET /api/admin/extraction/reviews/pending` (a smoke check) — nothing opens a PDF or an image.
- Phase 7+ (V2.1, `5633e48` onwards): `backend/tests/unit/engines/test_extraction.py`, `test_ai_extraction.py`, `backend/tests/integration/test_extraction.py`, `test_documents.py`, `test_workflow.py` — **all feed text (already-extracted strings) to the engines**; none exercise `pdf_engine.py`, Tesseract, or pdf2image. Verified via `git log -S "extract_and_parse" -- "test*.py"` → no hits.
- The dedicated integration test `test_workflow_end_to_end_completes_with_persisted_state.py` (current) runs the whole V3 workflow with synthetic text — again no files.

**Therefore the claim "core functionality was tested during early development" is NOT PROVEN as an automated test.** The evidence supports *development-time exercising* (committed real fixtures, fully wired UI, live routes) rather than a committed test suite. (This audit additionally ran safe, read-only checks: pdfplumber on the committed DEFRA PDF — works; `convert_from_path(BytesIO)` — fails; PIL on the committed PNG — works.)

---

# 8. Historical Fixtures / Sample Data

| Fixture | Location / commit | Status |
|---|---|---|
| Fuel-invoice image | `uploads/uk-fuel-invoice-1.png` (PNG 1641×835 RGB), committed `134a1d2`, still in `d4dcca1` | **Real, usable image fixture** |
| UI screenshots | `uploads/carbon_tally_ui_upload.png`, `carbon_tally_ui_over_view.png`, `carbon_tally_upload.gif` | Historical UI evidence |
| Sample bills in repo | `docs/sample_bills/*.pdf` (8 files) | **NOT PDFs** — verified with `file`: every one is an **HTML document mislabeled `.pdf`** (saved DEFRA guidance web pages). Not usable as extraction fixtures. |
| Real DEFRA PDF | `tools/carbon_data_factory/factors/Carbon-Dioxide-Calculation-Factors-for-2025.pdf` (also `docs/cline/…2025.pdf`) | Real UK-Gov PDF; readable by pdfplumber (verified) |
| Messy CSVs | `mock_uk_fuel_card_messy.csv`, `mock_uk_utility_bill.csv`, `mock_scope3.csv`, `generate_messy_*.py` (since `b322ab3`) | CSV-pipeline fixtures (core capability) |
| Synthetic document corpus (developer working dir, **not committed**) | `/home/shomonrobie/carbon_tally_synthetic_documents/` — `generate_carbontally_demo_pdfs.py`, `generation_report.md` (2026-08-23: 27 orgs, **1,688 PDFs**, 8 document types, difficulty mix Clean 20%/Realistic 60%/Difficult 15%/Edge 8%, scan degradation/watermarks/signatures/barcodes), outputs `output_test|output_paper_test|output_carbontally_demo_pdfs` each with `documents/`, `ground_truth/`, `manifests/`. Ground truth JSON schema: `schema_version, document_type, difficulty, is_scanned, pages, line_item_count, supplier, customer, invoice_number, invoice_date, billing_period_start/end, currency, line_items[], net_total, vat_total, gross_total, edge_cases, variations`. | **Modern (2026-08-21/23) evaluation corpus** — real PDFs + machine-readable ground truth for extraction validation. Customer data: none (synthetic). |

The sample corpus proves real document *generation*, not real extraction results. There is **no committed expected-output file for PDF/image extraction** (no ground truth tied to `pdf_engine` in git history).

---

# 9. Historical Capability Classification

| Capability | Classification | Evidence basis |
|---|---|---|
| PDF text extraction (digital) | **PROVEN WORKING** | Code sound (`pdfplumber` on bytes); historically wired (`/upload-pdf`); live-verified in this audit on a real PDF |
| Scanned-PDF OCR | **BROKEN as written** | `convert_from_path(io.BytesIO(...))` raises `TypeError`; swallowed → silent error. Present since first commit |
| JPG/PNG image OCR | **PARTIALLY WORKING / now disconnected** | Engine code correct; route wired 07-21→07-27; removed at `c09ad51`; dead code in current tree |
| Multi-page PDF | **IMPLEMENTED BUT UNPROVEN** | pdfplumber + OCR loop iterate all pages; no committed test/fixture result |
| Table extraction | **NOT IMPLEMENTED** | Line-regex parsing only; no table-structure extraction |
| Source-page tracking | **NOT IMPLEMENTED** | No page numbers preserved on extracted fields |
| Extraction confidence | **IMPLEMENTED BUT INCOMPLETE** | Regex-parser per-field confidence; no OCR confidence, no image confidence |
| Evidence/source references | **NOT IMPLEMENTED** | No coordinates/pages/line-links; only `file_metadata` + `raw_text` in streams |
| "AI extraction" (early era) | **EXPERIMENTAL / aspirational** | No LLM/OpenAI code in any pre-Phase-7 commit; commit message wording only |
| Structured extraction → mapping | **IMPLEMENTED BUT NOT CONNECTED** | `data_streams` output never fed the matching engine directly; human re-entry via review queue |

---

# 10. V2/V3 Transition Analysis

What actually happened, stage by stage:

1. **Early product (2026-07-17 → 07-27).** Extraction was a single-file FastAPI app (`main.py`) with dedicated endpoints. Uploads went to Supabase Storage bucket `documents`; low-confidence extractions were queued to `manual_review_queue` (see `queue_for_manual_review`, `77b15fa:backend/main.py:1915` — uploads the file under `manual_review/{org_id}/…`, extracts issues, inserts a review record, emails). `/approve-pdf-batch` was a **stub** (returns success without writing extracted streams).

2. **Consolidation regression (2026-07-27, `c09ad51`).** Routes moved to `backend/routes/upload.py`. The `/upload-image` route was dropped; the new `/upload` route branched on file type but called `extract_and_parse` for IMAGE. The frontend was not updated — `PDFIngestionPortal.jsx` continued to call `/upload-image`. **This is the single most damaging change: image OCR went from wired to unreachable in one commit.**

3. **Database baselines (2026-08-04/06).** RC1/RC2 schemas reorganized document storage (`organization_files`), review queues, and admin surfaces. Extraction engine untouched.

4. **V2.1 architecture (2026-08-07/08, Phases 0–8).** A clean engine architecture was layered on: `engines/extraction.py` (deterministic text→structured), `engines/ai_extraction.py` (LLM), `engines/matching*.py`, `engines/calculation.py`, `engines/workflow.py`, `data/` repositories, and a real test suite. **No PDF/OCR engine was built into this architecture** — the new `DocumentExtractionEngine.extract(document, text)` accepts *text*, not files. The legacy `pdf_engine.py` was left as legacy.

5. **Planning oversight.** `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md` (§3) groups `report_generator.py / pdf_engine.py / report_templates` under **"Legacy report renderers — PDF/HTML rendering DEFERRED"** — i.e., the planning documents classified the *input OCR engine* (`pdf_engine.py`) as an *output report renderer*. `docs/cline/CarbonTally_Backend_Module_Inventory_V3.md` classifies `backend/pdf_engine.py` as **"uncategorized — NO DIRECT V3 IMPACT"**. The input-side extraction capability was therefore invisible to the V3 migration plan.

6. **V3 product surfaces (2026-08-15 → 08-25).** The authoritative V3 flow is `/api/v3/uploads` → private `documents` bucket (D32) → creates a **manual extraction batch + item per file (D23)** → human enters data in the extraction workspace → mapping → validation → calculation. **No automatic text/OCR step exists in the V3 HTTP surface.** The legacy `upload.router` (including `/upload-pdf`, `/upload`) is still registered (`backend/main.py:212`, `app.include_router(upload.router)`).

7. **Net effect:** the extraction capability was **preserved but disconnected** — preserved as engine code (`pdf_engine.py`), preserved in backups (`main copy*.py`), preserved in git history, and partially preserved as a still-rendered (but route-less) frontend component. It was never deleted and never replaced; it was *left behind* by the new architecture and *misclassified* in the migration planning.

---

# 11. Current V3 Extraction Components

| Component | Path | Role | Wired to HTTP? |
|---|---|---|---|
| Legacy PDF/image engine | `backend/pdf_engine.py` (`PDFExtractor`) | Digital-PDF text + (broken) scanned OCR + (correct but dead) image OCR | `/upload-pdf`, `/upload` (PDF); image path **never called** |
| Legacy upload router | `backend/routes/upload.py` | `/upload`, `/upload-pdf`, `/upload-batch`, `/repair-pdf`, `/upload-csv`, `/test-upload` | Registered at `main.py:212`; IMAGE dispatch regression present |
| V3 document upload | `backend/api/v3_documents.py` `POST /uploads` | Private storage + classify + create manual-extraction batch/item | **YES** (D23/D32) |
| V3 extraction engine | `backend/engines/extraction.py` (`DocumentExtractionEngine.extract(document, text)`) | Deterministic text→`ExtractionResult` | Reached via V3 ops extraction-batch endpoints (text input only) |
| V3 AI extraction engine | `backend/engines/ai_extraction.py` (`AIExtractionEngine.extract_fields`) | LLM field extraction (text input) | **NO route in any commit** |
| V3 workflow engine | `backend/engines/workflow.py` | Orchestration stages (source→extraction→mapping→validation→calculation→review→approval) | Not reachable via production HTTP (Phase 8 artifact) |
| Manual extraction model | `manual_extraction_items` / `manual_extraction_batches` tables | Human entry + review workspace | `backend/api/v3_operations.py` (extraction batches/items/workspace routes) |
| Frontend portal | `frontend/src/PDFIngestionPortal.jsx` (still rendered by `App.js:1764`) | Legacy PDF/image ingestion UI | **Calls dead `/upload-image`** → 404 for images |
| Frontend V3 documents | `frontend/src/v3/customer/DocumentsPage.jsx`, `frontend/src/v3/api.js` | Upload → storage, then manual extraction | `POST /api/v3/uploads` |

---

# 12. Historical vs Current Comparison

| Capability | Historical (07-2026) | Current (08-2026, `d4dcca1`) | Delta |
|---|---|---|---|
| Digital PDF text extraction | Engine + `/upload-pdf` + UI | Engine + `/upload-pdf` + UI (legacy router still registered) | **Unchanged, still wired** |
| Image (JPG/PNG) OCR | Engine + `/upload-image` + UI | Engine only (dead); V3 route calls PDF method | **Wiring lost at `c09ad51`** |
| Scanned-PDF OCR | Broken (`convert_from_path(BytesIO)`) | Same broken code | **No change** |
| Structured output | `data_streams` (regex, per-field confidence) | `ExtractionResult` / `ManualExtractionItem` (V3 schema) | **Schema diverged** — legacy output not consumed by V3 |
| Human review | `manual_review_queue` + `/approve-pdf-batch` (stub) | V3 extraction workspace + review/QC workflow + audit trail | **Replaced by superior V3 machinery** |
| Storage | Supabase `documents` bucket (public URLs historically) | Supabase `documents` bucket, **private** + signed URLs (D32) | **Improved** |
| AI extraction | None (aspirational) | `AIExtractionEngine` (unwired) | **Added, still unwired** |
| Tests | None for extraction | Text-input engine tests only | **No PDF/image test ever** |

---

# 13. What Was Lost / Disconnected / Replaced

**Lost (deleted):**
- The `/upload-image` HTTP route (`c09ad51`). The only true deletion of working extraction wiring.
- Any committed automated test of file-based extraction (never existed).

**Disconnected (still present, unreachable):**
- `PDFExtractor.extract_and_parse_image` — defined, called by nothing.
- `backend/main copy.py` / `main copy 2.py` — correct image dispatch, not a registered router.
- `frontend/src/PDFIngestionPortal.jsx` — rendered but posts to a non-existent endpoint.
- `engine/workflow.py` orchestrator and `AIExtractionEngine` — implemented, never HTTP-wired.

**Replaced:**
- `manual_review_queue` + stub approval → full V3 `manual_extraction_batches/items` + review/QC/approval workflow.
- Public storage URLs → private bucket + signed URLs (D32).
- Monolithic `main.py` → layered `api/`, `domain/`, `engines/`, `data/`, `services/`.

**Never existed (despite commit-message wording):**
- Early-era "AI extraction" (no LLM code in any pre-Phase-7 commit).
- Scanned-PDF OCR (broken from first commit).
- Page/source coordinates, OCR confidence, table extraction.

---

# 14. Reuse Assessment

| Component | Recommendation | Evidence |
|---|---|---|
| `PDFExtractor.extract_and_parse` + `_extract_text_direct` (digital PDF text) | **REUSE AS-IS** | Sound; live-verified; already wired (`/upload-pdf`) |
| `PDFExtractor._extract_text_ocr` (scanned PDF) | **REWRITE SMALL COMPONENT** | 1-line API fix (`convert_from_bytes`), add page numbering, handle OCR failure explicitly, make tesseract path configurable |
| `PDFExtractor.extract_and_parse_image` (image OCR) | **REUSE WITH ADAPTATION** | Correct core; re-wire to a route (restore `/upload-image` or a V3 `/api/v3/uploads/{id}/ocr`); tesseract runtime; add error/confidence surfacing |
| Regex parsers (`_parse_utility_bill`, `_parse_fuel_invoice`, `_parse_scope3_document`) | **REUSE WITH ADAPTATION** | Valuable domain rules (UK reg, litre/date patterns, confidence weights); must map `data_streams` → V3 `ExtractionResult`/`ManualExtractionItem` or the CT-ARCH-005 standardized activity object |
| `engines/extraction.py` (V3 deterministic) | **REUSE AS-IS** | Already the V3 extraction engine; feed OCR text into it |
| `engines/ai_extraction.py` | **REUSE WITH ADAPTATION** (future) | Sound engine; wire only under decision §5.4 (production language) and the locked controlled-AI-provider direction |
| `engines/workflow.py` orchestrator | **REWRITE/WIRE SMALL** | Needs HTTP surface + work-item context per migration plan (§line 581: "no engine change; orchestration only") |
| Old `/upload-image` handler (`main copy*.py`) | **REUSE AS REFERENCE** | 3-line pattern for correct dispatch |
| Synthetic document factory + ground truth | **REUSE AS-IS** | Modern evaluation corpus for regression-testing recovered OCR (convert to committed fixtures when publishing) |

**Overall: no major rewrite required.** Recovery is re-wiring + a 1-line fix + adapter, matching decision §5.2 (reuse/fix sound historical implementation).

---

# 15. CSV/Excel Integration Compatibility

The locked principle (CT-ARCH-005, `docs/cline/CarbonTally_Backend_V2_Final_Implementation_Instructions.md`): *every importer must transform its source into one common internal (standardized) activity object before matching* — manual entry, PDF, OCR, Excel, CSV, API all converge.

Current state:
- CSV/Excel → `process_fuel_data`/`process_utility_data`/`process_scope3_data` (`backend/routes/upload.py`) → standardized activity rows → matching engine → calculation. **Fully wired and core.**
- PDF/image (legacy) → `data_streams` → **dead end**; never feeds the matching engine.
- V3 manual extraction → `ManualExtractionItem` → mapping options → matching engine → calculation. **Wired.**

**Can recovered extraction feed the same downstream architecture? Yes** — with one adapter:
1. Run OCR/text extraction (`pdf_engine` fix + re-wire) to get text.
2. Feed text to `engines/extraction.py` (V3 deterministic engine) → `ExtractionResult` → materialize as `manual_extraction_items` (existing V3 path).
3. From there, mapping/validation/calculation are the **same** code path as CSV/Excel and manual entry (factor matching engine is format-agnostic by design — CT-ARCH-004).

Row-level traceability: achievable by persisting per-item `source_document_id` (already in the schema) plus, after the small OCR fix, page numbers; coordinates would require new work (not currently in any schema).

**Conclusion: PDF/image and CSV/Excel can converge at the `ManualExtractionItem`/standardized-activity layer without changing the matching, factor, or calculation engines.**

---

# 16. Custom Factor Compatibility

The factor-resolution architecture is database-driven: DEFRA factors, Irish/SEAI factors, and **Customer Custom Emission Factors** (`customer_factors`, with merge/snapshot rules) all resolve through the same matching engine (`engines/factor_matching.py`, staged pipeline exact→natural_key→alias→keyword→fuzzy, threshold 0.85), and the calculation engine snapshots the resolved factor (`calculation_snapshots`, append-only).

Extracted document activity records, once normalized to the standardized activity object (see §15), are indistinguishable from CSV-derived or manually-entered records at the mapping boundary. **The existing architecture already supports Customer Custom Emission Factors for extracted records — no new factor machinery is required.** Only the extraction→activity-model adapter and the OCR re-wiring are needed.

---

# 17. Target V3 Integration Path

Conceptual path (locked §5.3) mapped onto existing components — **design only, nothing built**:

```
PDF / JPG / scanned document
   │
   ├─ POST /api/v3/uploads  (EXISTS — v3_documents.py, D32 private bucket, D23 batch+item creation)
   │
   ▼
Document stored + classification (EXISTS — _classify, _pdf_page_count)
   │
   ▼
OCR / text extraction  ←  MISSING WIRING:
      • digital PDF  → pdf_engine._extract_text_direct          (EXISTS, works)
      • scanned PDF  → pdf_engine._extract_text_ocr             (EXISTS, 1-line fix)
      • JPG/PNG      → pdf_engine.extract_and_parse_image       (EXISTS, re-wire)
   │
   ▼
Structured activity data (EXISTS — engines/extraction.py → ExtractionResult;
   adapter needed: legacy data_streams OR OCR text → V3 extraction result)
   │
   ▼
ManualExtractionItem (EXISTS — v3_operations.py extraction workspace,
   human review/edit, audit trail)
   │
   ▼
Mapping (EXISTS — matching engine, DEFRA/Irish/custom sets)
   │
   ▼
Processing Entity QC → CarbonTally QC → Calculation (EXISTS — v3_processing,
   v3_review, v3_qc, calculation engine + snapshots)
   │
   ▼
Evidence → Customer Final Approval (EXISTS — evidence model, reports)
```

**Missing wiring (the only gaps):** (1) re-wire image OCR to a route; (2) fix scanned-PDF OCR; (3) an adapter that turns OCR text (or legacy `data_streams`) into the V3 extraction result / manual extraction item; (4) optional page-number persistence. Everything downstream already exists.

---

# 18. Recommended Recovery Plan

Phase 0 — **Verify (no code)**
1. Confirm tesseract binary is deployed (or containerized) in target environments; document the OCR runtime requirement.
2. Re-run the synthetic ground-truth corpus (1,688 PDFs) through the current `pdf_engine` to quantify the digital-PDF extraction baseline.

Phase 1 — **Restore wiring (small, low-risk)**
3. Fix `_extract_text_ocr`: `convert_from_bytes`; loop pages with page numbers; raise/record explicit OCR failure instead of silent `""`.
4. Re-wire image OCR: either restore an `/upload-image`-style endpoint or add a V3 `POST /api/v3/uploads/{file_id}/ocr` (prefer V3 surface) that calls `extract_and_parse_image`.
5. Wire the V3 extraction workspace to accept OCR-produced text (feed `engines/extraction.py`, then materialize `manual_extraction_items`), or add an adapter from `data_streams`.

Phase 2 — **Quality**
6. Persist page numbers (and later coordinates if the product requires) on extraction items for evidence.
7. Surface per-field confidence and OCR-failure states to the human reviewer (schema has review-status columns; add error/issue mapping).
8. Add tests using the synthetic corpus as committed fixtures: digital PDF, scanned PDF (degraded), and JPG/PNG scenarios asserting extracted values against ground truth — the first real file→extraction tests.

Phase 3 — **AI-assisted extraction (only after Phases 1–2, per locked decisions)**
9. Wire `AIExtractionEngine` as a controlled, opt-in post-OCR stage with human confirmation, under §5.4 production-language rules.

---

# 19. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Tesseract not available in production runtime | HIGH | Containerize OCR; verify binary; Poppler also required for pdf2image |
| Silent OCR failure pattern (swallowed exceptions) | MEDIUM | Fix error handling to surface failures to reviewers |
| Legacy `data_streams` schema diverges from V3 `ManualExtractionItem` | MEDIUM | Adapter layer; keep V3 schema as the single downstream truth |
| Planning re-classification of `pdf_engine.py` as "report renderer" could recur | MEDIUM | Add module-inventory entry for input-side OCR engine; reference this audit |
| Publicly claiming "AI extraction" while unwired (locked §5.4) | HIGH (reputational) | Production-capability language strictly limited to wired+verified features |
| Frontend `PDFIngestionPortal.jsx` renders a dead upload path | LOW | Update or retire the component |
| Sample-bill PDFs in `docs/sample_bills/` are HTML masquerading as PDFs | LOW | Replace with real fixtures from the synthetic corpus |

---

# 20. Evidence Register

| # | Claim | Evidence |
|---|---|---|
| E1 | PDF/image extraction existed early | `134a1d2` (2026-07-21): `backend/pdf_engine.py` (337 lines), `backend/main.py`, `frontend/src/PDFIngestionPortal.jsx` |
| E2 | `/upload-image` route existed with correct dispatch | `134a1d2:main.py:391-410` and `77b15fa:backend/main.py:826-841` → `pdf_extractor.extract_and_parse_image(...)` |
| E3 | `/upload-image` removed at consolidation | `c09ad51`: absent from `backend/routes/upload.py` (grep per commit); route set `upload-csv/upload-pdf/upload-batch/repair-pdf/upload` only |
| E4 | Consolidated `/upload` dispatches IMAGE to PDF method | `backend/routes/upload.py:587-591` (file_type branch) and `:675` (`extract_and_parse` for `['PDF','IMAGE']`) — current `d4dcca1` |
| E5 | Frontend kept calling dead endpoint | `frontend/src/PDFIngestionPortal.jsx:51` (`isImage ? '/upload-image' : '/upload-pdf'`); still rendered by `frontend/src/App.js:1764` |
| E6 | Correct image dispatch preserved in backups | `backend/main copy.py:973`, `backend/main copy 2.py:1308` (`extract_and_parse_image`) |
| E7 | Engine unchanged through V3 | `git diff 77b15fa d4dcca1 -- backend/pdf_engine.py` → only a comment + newline |
| E8 | `extract_and_parse_image` is dead code today | `grep -rn "extract_and_parse_image" backend/ frontend/` → only the definition |
| E9 | Scanned-PDF OCR broken as written | `backend/pdf_engine.py:72-83` uses `convert_from_path(io.BytesIO(...))`; live check → `TypeError expected str, bytes or os.PathLike object, not BytesIO` |
| E10 | Digital-PDF text extraction works | Live check: pdfplumber reads `tools/carbon_data_factory/factors/Carbon-Dioxide-Calculation-Factors-for-2025.pdf` |
| E11 | No committed extraction tests | `git log -S "extract_and_parse" -- "test*.py"` → no hits; early-era tests = React template only |
| E12 | V2.1+ engines take text, not files | `backend/engines/extraction.py:125` `async def extract(self, document, text)`; `ai_extraction.py:98` `extract_fields` |
| E13 | AIExtractionEngine never HTTP-wired | `git grep -ln "AIExtractionEngine"` per Phase 7/8 commits → `engines/` only |
| E14 | Migration plan misclassified pdf_engine | `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md` §3 "Legacy report renderers: report_generator.py / pdf_engine.py / report_templates — PDF/HTML rendering DEFERRED"; Module Inventory: "uncategorized — NO DIRECT V3 IMPACT" |
| E15 | V3 upload does not OCR | `backend/api/v3_documents.py:65-144` — storage upload + batch/item creation only |
| E16 | Legacy router still registered | `backend/main.py:212` `app.include_router(upload.router)` |
| E17 | V2 architecture mandates standardized activity object | `docs/cline/CarbonTally_Backend_V2_Final_Implementation_Instructions.md` CT-ARCH-005 |
| E18 | Real image fixture exists | `uploads/uk-fuel-invoice-1.png` (PNG 1641×835 RGB) |
| E19 | Repo "sample bills" are not PDFs | `file docs/sample_bills/*.pdf` → HTML documents |
| E20 | Early-era "AI extraction" not implemented | No `openai/anthropic/gpt/claude` matches in `77b15fa` tree (`git grep`) |
| E21 | Demo figure 10,732.4 not reproducible | `clean_emissions_output.json` sums to **4,156.04 kg CO2e** (49 records); "10732"/"10,732" absent from all committed files and from the developer working dir |

---

# Required Capability Matrix

| Capability | Historical Evidence | Historical Status | Current V3 Status | Reusable? | Missing Wiring | Confidence |
|---|---|---|---|---|---|---|
| PDF | `134a1d2` `pdf_engine.py`; `/upload-pdf`; live pdfplumber check | **PROVEN WORKING** (digital) | Engine + legacy `/upload-pdf` still registered; V3 uploads store-only | **YES (as-is)** | None (V3 surface optional) | HIGH |
| Scanned PDF | `_extract_text_ocr` since `134a1d2` | **BROKEN as written** (`convert_from_path(BytesIO)`) | Same broken code | **YES (1-line fix)** | Route + runtime (tesseract/poppler) | HIGH |
| JPG | `extract_and_parse_image` since `134a1d2`; `/upload-image` 07-21→07-27 | **PARTIALLY WORKING** (engine right, wiring removed) | Dead code (defined, never called) | **YES (adaptation)** | Re-wire route | HIGH |
| JPEG/PNG | Same engine (PIL decode) | PARTIALLY WORKING | Dead code | YES (adaptation) | Re-wire route | MEDIUM |
| OCR | Tesseract via pytesseract + pdf2image | BROKEN for scanned PDF; UNVERIFIED live for images (no tesseract in audit env) | Same | YES | Runtime + fix | MEDIUM |
| Multi-page | pdfplumber all pages; OCR loops pages | IMPLEMENTED BUT UNPROVEN | Same | YES | Page-number persistence | MEDIUM |
| Table extraction | None (line-regex only) | NOT IMPLEMENTED | Not implemented | N/A | New (P3) | HIGH (absent) |
| Source-page tracking | None | NOT IMPLEMENTED | Not implemented | N/A | New (P2) | HIGH (absent) |
| Structured extraction | `data_streams` (regex + per-field confidence) | PROVEN WORKING (engine); never fed matching | V3 `ExtractionResult`/`ManualExtractionItem` | **YES (adapter)** | data_streams→V3 item adapter | HIGH |
| Factor mapping | Not connected historically | IMPLEMENTED BUT NOT CONNECTED (to extraction) | Wired for manual/CSV items | **YES (no change)** | Feed V3 items | HIGH |
| Calculation | Not connected historically | IMPLEMENTED BUT NOT CONNECTED | Wired, snapshots, append-only | **YES (no change)** | None | HIGH |
| Persistence | `manual_review_queue` + Supabase `documents`; `/approve-pdf-batch` stub | PARTIALLY WORKING (stub approval) | `manual_extraction_*` + D32 private storage + audit | **YES (no change)** | None | HIGH |

---

# Required Final Answers

1. **Was PDF extraction historically implemented?**
   **Yes.** `PDFExtractor` with digital-PDF text extraction (`pdfplumber`) and three regex parsers has been in the repository since `134a1d2` (2026-07-21), wired to `/upload-pdf` and the legacy `/upload` route. Live-verified in this audit against a real DEFRA PDF.

2. **Was scanned-document OCR historically implemented?**
   **Implemented as a design, but BROKEN as written from the first commit.** `_extract_text_ocr` passes `io.BytesIO` to `pdf2image.convert_from_path`, which raises `TypeError` (needs a path; the bytes API is `convert_from_bytes`); the exception is swallowed, so scanned PDFs return "Could not extract text". It has never worked through the production code path.

3. **Was JPG/image extraction historically implemented?**
   **Yes — implemented and briefly wired.** `extract_and_parse_image` (`PIL` + `pytesseract`) existed from `134a1d2`; the `/upload-image` route called it correctly from 2026-07-21 to 2026-07-27; a real fuel-invoice PNG fixture (`uploads/uk-fuel-invoice-1.png`) was committed alongside. The route was removed at `c09ad51`.

4. **Was this functionality actually tested?**
   **Not by any committed automated test.** No test in any commit opens a PDF or image through the extraction engine. The evidence supports *development-time exercising* (working UI, live routes, committed fixtures), not an automated suite. "Tested" as automation: **NOT PROVEN FROM GIT HISTORY**.

5. **What historical evidence proves it?**
   Committed engine (`backend/pdf_engine.py`, unchanged since `134a1d2`); committed routes with correct dispatch (`134a1d2`/`77b15fa` `main.py`); committed working frontend (`PDFIngestionPortal.jsx`, `BulkUpload.jsx`); committed real image fixture (`uploads/uk-fuel-invoice-1.png`); pre-commit `.pyc` bytecode showing the same OCR methods existed even earlier; backups `backend/main copy*.py` retaining the correct dispatch.

6. **What happened to it during V3 migration?**
   **It was preserved but disconnected.** The engine file survived unchanged; the `/upload-image` route was deleted at `c09ad51` (2026-07-27) during route consolidation; the replacement `/upload` route dispatched images to the PDF method; the migration-plan and module-inventory documents misclassified `pdf_engine.py` as a report renderer / "NO DIRECT V3 IMPACT"; the V2.1/V3 architecture built new text-input engines and a manual-extraction workspace without an OCR stage.

7. **Is current V3 missing functionality or mainly missing wiring?**
   **Mainly missing wiring**, plus one small engine defect. Functionality that exists: digital-PDF text extraction (works), image OCR engine (correct, dead), V3 structured extraction (text-input), manual review/QC, matching (DEFRA/Irish/custom), calculation, evidence, private storage. Missing: the `/upload-image`-style route, the 1-line scanned-PDF fix, the OCR-text→V3-extraction-item adapter, and (optionally) page-number persistence.

8. **Which historical components should be reused?**
   `extract_and_parse`/`_extract_text_direct` (as-is), `extract_and_parse_image` (adaptation), the regex parsers (adaptation), the old `/upload-image` handler (as reference), and — from the V3 side — `engines/extraction.py`, `ai_extraction.py`, `workflow.py` (all reusable once wired). Also reuse the synthetic document corpus + ground truth as test fixtures.

9. **Which should be rewritten?**
   Only the scanned-PDF OCR path (`_extract_text_ocr`) — and that is a small rewrite (use `convert_from_bytes`, page numbers, explicit error handling, configurable tesseract). Table extraction and coordinate-level evidence would be new work (P2/P3), not rewrites.

10. **Can recovered extraction feed the existing CSV/Excel-style downstream mapping/calculation architecture?**
    **Yes.** Per CT-ARCH-005 all sources converge on a standardized activity object. Route OCR text through `engines/extraction.py` (or an adapter from `data_streams`) into `manual_extraction_items`; from there mapping/validation/calculation are the same engine path as CSV/Excel and manual entry.

11. **Can it work with DEFRA?**
    **Yes.** The matching engine resolves DEFRA factors for any standardized activity record; no change needed.

12. **Can it work with Irish/SEAI?**
    **Yes.** The Irish/SEAI factor set coexists in the same database/matching architecture (`filter_factors` supports factor_source/factor_set); extracted records would use the same resolution path.

13. **Can it work with Customer Custom Emission Factors?**
    **Yes.** Custom factors are part of the same database-driven resolution architecture (`customer_factors` merge/snapshot); no new factor machinery required.

14. **What is the minimum engineering work required to restore the capability into V3?**
    (a) Fix `_extract_text_ocr` (`convert_from_bytes` + page numbers + error surfacing) — ~1 day incl. tests.
    (b) Re-wire image OCR to a V3 endpoint (`POST /api/v3/uploads/{file_id}/ocr` or equivalent) — ~0.5 day.
    (c) Adapter: OCR text / `data_streams` → `ExtractionResult` / `manual_extraction_items` — ~1–2 days.
    (d) Ensure OCR runtime (tesseract + poppler) in the deployment/container — ops.
    (e) Tests against the synthetic ground-truth corpus (digital PDF, scanned PDF, JPG scenarios) — ~1–2 days.
    **Total ≈ 4–6 engineering days** plus runtime provisioning. No rebuild.

15. **What should Cline NOT rebuild because it already exists?**
    - The PDF text extraction engine (`pdf_engine.py`).
    - The image OCR engine (`extract_and_parse_image`).
    - The regex parsers (utility/fuel/scope3) and their confidence logic.
    - The V3 structured extraction engine (`engines/extraction.py`).
    - The AI extraction engine (`engines/ai_extraction.py` — to be wired, not rewritten).
    - The workflow orchestrator (`engines/workflow.py`).
    - The factor matching engine, DEFRA/Irish/custom factor data, calculation engine + snapshots, review/QC/approval workflow, evidence model, private storage + signed URLs, and the synthetic document corpus.
    - The historical `/upload-image` dispatch logic (in `main copy*.py` and git history) — copy, don't reinvent.

---

*End of audit. READ-ONLY. No repository files were modified; no tests were created or modified; no credentials reproduced. The report is intentionally not committed or pushed; publication is the Product Owner's decision.*
