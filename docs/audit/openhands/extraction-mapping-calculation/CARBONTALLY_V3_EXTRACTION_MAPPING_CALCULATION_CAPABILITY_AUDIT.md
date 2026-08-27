# CarbonTally V3 — Extraction → Mapping → Calculation Capability Audit

| | |
|---|---|
| Audit type | Independent, read-only technical/product capability audit |
| Repository | https://github.com/shomonrobie/CarbonTally |
| Baseline audited | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (HEAD of `origin/main`) |
| Audit date | 2026-08-24 |
| Audit mode | READ-ONLY (no source/schema/data changes; no dependency installs; no commits) |
| Report status | Complete |

---

## 1. Executive Summary

**CarbonTally V3 does NOT yet implement a demonstrable end-to-end
"document → OCR → structured activity → factor match → calculation → evidenced
result" pipeline over HTTP.** What is implemented and production-wired is a
**human-assisted manual extraction pipeline** (upload → human data entry →
manual factor mapping → rule-based validation → engine calculation → human/QC
review → persisted evidenced result). OCR exists only as a **legacy,
not-currently-production-path** capability, and the AI-assisted extraction and
workflow orchestrator engines are **implemented but not wired to any HTTP
route**.

The core "calculation half" of the product (DEFRA/SEAI factor data, factor
matching, calculation, immutable snapshots, evidence traceability, persistence,
human review, exports, reporting) is **substantially implemented, wired and
tested**. The "extraction half" (PDF text, scanned-PDF OCR, JPG OCR, AI field
extraction) is **implemented in code but either not wired, not wired
correctly, or not tested**.

The most important product-truth findings, in order:

1. **There is no OCR in the production V3 HTTP workflow.** The primary upload
   route `POST /api/v3/uploads` (`backend/api/v3_documents.py`) stores the file
   and enqueues a pending `manual_extraction_item`; it never extracts text. All
   OCR code lives in `backend/pdf_engine.py` and is reachable only through the
   **legacy** routes `/api/upload`, `/api/upload-pdf`, `/api/repair-pdf`
   (`backend/routes/upload.py`).
2. **AI-assisted extraction is not wired.** `AIExtractionEngine`
   (`backend/engines/ai_extraction.py`) and `WorkflowOrchestrator`
   (`backend/engines/workflow.py`) are referenced only by tests and the engines
   package — no API route, `main.py` or `main_v2.py` constructs or calls them.
3. **JPG OCR is broken in the only route that attempts it.** The legacy
   `/api/upload` route calls `extract_and_parse` (the PDF path) for IMAGE files
   instead of `extract_and_parse_image`, so images cannot actually be OCR'd
   through that route.
4. **OCR output is not persisted anywhere.** There is no OCR text/confidence
   column in the schema, no OCR table, and no OCR text surface in the human
   review workspace (the operator views the raw document via a signed URL and
   types values by hand).
5. **The calculation half is strong.** DEFRA-2025 factors (7,029-row SQL
   artifact) and SEAI-2025 (20 rows, dev-DB import documented) share one
   `emission_factors` table; the `FactorMatchingEngine` (exact/natural-key/
   alias/keyword/fuzzy stages, country-filtered) and `CalculationEngine`
   (immutable snapshots with SHA-256 content hash, `verify()`, source
   provenance) are wired into `POST /api/v3/emissions/calculate` and the
   ops/manual pipeline, and are covered by unit + integration tests.
6. **Irish/SEAI matching works at the engine level** (verified by committed
   tests and an independent in-memory check), but there is **no end-to-end
   HTTP-level Irish test**, and the live/production database factor contents
   are **not verifiable from the repository** (only a dev-DB import document).
7. **Unit normalization does not exist.** The calculation engine requires an
   exact unit match and raises `UnitMismatchError`; there is no litres→kg /
   miles→km conversion. A limited "qualifier" normalizer exists only in the
   ops route.
8. **The known demo figure 10,732.4 kg CO2e is NOT in the repository.** It
   could not be traced to any production pipeline artifact; the legacy CSV
   demo output (`clean_emissions_output.json`) is produced by a separate legacy
   calculation path with hardcoded per-row factors.

---

## 2. Current Pipeline Architecture

The repository contains **two coexisting surfaces** (see `docs/architecture/
CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` §12, §15.13):

- **`backend/main.py`** — legacy FastAPI app (legacy `/api/*` routes) which
  conditionally mounts the V3 router `api.router` (`backend/api/router.py`)
  when it imports. Mounted routers include the V3 surfaces
  `/api/v3/*` (documents, emissions, ops, processing-workflow,
  manual-extraction, QC, review, reports, exports, …) and the V2.1 surface
  `/api/v2/*` (business engine routes).
- **`backend/main_v2.py`** — alternative uvicorn entry point
  (`from api.router import create_app`); serves only the V2.1/V3 router.

The de-facto production pipeline that is **wired over HTTP** today is the
**manual-extraction pipeline** (`backend/api/v3_processing_workflow.py`,
`backend/api/v3_operations.py`):

```
Upload (POST /api/v3/uploads)
  → organization_files row + Supabase Storage object (bucket "documents", private)
  → manual_extraction_item (status "pending", auto-created "Uploads" batch, D23)
  → human data entry  POST /items/{id}/extract      (extracted_data JSONB)
  → human mapping     POST /items/{id}/map          (mapped_data + factor selection)
  → validation        POST /items/{id}/validate     (deterministic rules → issues)
  → calculation       POST /items/{id}/calculate    (CalculationEngine → snapshot + log)
  → customer review   POST /items/{id}/customer-review  (approve/reject)
  → QC (staff)        POST /api/v3/qc/items/{id}/review
```

The **implemented-but-unwired automated pipeline** is
`engines/workflow.py::WorkflowOrchestrator`:

```
text → DocumentExtractionEngine → AIExtractionEngine → FactorMatchingEngine
     → CalculationEngine → snapshot+log   (driven by event bus, retries, latches)
```

The **legacy OCR pipeline** is `backend/pdf_engine.py::PDFExtractor`
reachable through `/api/upload`, `/api/upload-pdf`, `/api/repair-pdf`
(`backend/routes/upload.py`) only.

Engines and their wiring state (details in later sections):

| Engine | File | HTTP wiring |
|---|---|---|
| PDF/OCR extractor | `backend/pdf_engine.py` | Legacy `/api/upload*` only; JPG broken |
| Deterministic text extraction | `backend/engines/extraction.py` | NOT wired |
| AI extraction | `backend/engines/ai_extraction.py` | NOT wired |
| Workflow orchestrator | `backend/engines/workflow.py` | NOT wired |
| Factor matching | `backend/engines/factor_matching.py` | Wired (`/api/v3/emissions/calculate`, `/api/v2/factor-match`) |
| Calculation | `backend/engines/calculation.py` | Wired (`/api/v3/emissions/calculate`, `/api/v3/processing/.../calculate`, `/api/v3/ops/.../calculate`) |
| Validation | `backend/engines/validation.py` + `engines/processing_workflow.py` | Wired (validate endpoint, issues) |
| Report generation | `backend/engines/report_generation.py` | Wired (`/api/v3/reports`) |
| White-label PDF output | `backend/engines/pdf_render.py` | Wired (`/api/v3/reports/{id}/pdf`) |

---

## 3. Document Ingestion (audit section A)

### A.1 Which formats are accepted?

- **V3 path** (`POST /api/v3/uploads`, `backend/api/v3_documents.py`): **any
  uploaded file** is accepted and classified by extension/MIME via
  `_classify(filename, mime)` (line 54): `PDF | IMAGE | SPREADSHEET | OTHER`.
  There is **no format rejection, no size limit, no MIME sniffing** in this
  route.
- **Legacy path** (`backend/routes/upload.py`): formats governed by
  `system_settings.allowed_file_types` (default `['pdf','csv','xlsx','jpg',
  'jpeg','png']`) with a 50 MB limit (`validate_file_upload`, lines 78–105).
  `/api/upload-csv` further restricts to `.csv/.xlsx`; `/api/upload-pdf` to
  `.pdf`; `/api/upload-batch` is disabled for beta ("premium_feature").
- PDF/JPG/JPEG/PNG/CSV/XLSX are therefore "accepted" at some route; XLS (old
  binary) is classified as SPREADSHEET in both routes but only the legacy CSV
  route reads Excel (`pd.read_csv` on `.xlsx` would actually fail for xlsx —
  only `.csv` is robustly parsed; `pd.read_csv` is used for both, so `.xlsx`
  handling is nominal).

### A.2 Which routes accept them?

| Route | File | Notes |
|---|---|---|
| `POST /api/v3/uploads` | `backend/api/v3_documents.py:65` | Primary V3 upload; Storage + `organization_files` + auto-enqueue extraction item |
| `POST /api/upload` | `backend/routes/upload.py:552` | Legacy; Storage (public URL) + `organization_files` + optional `pdf_engine` extraction |
| `POST /api/upload-csv` | `backend/routes/upload.py:123` | Legacy CSV/Excel → pandas → `process_fuel_data` etc. |
| `POST /api/upload-pdf` | `backend/routes/upload.py:184` | Legacy PDF → `pdf_engine.PDFExtractor` |
| `POST /api/upload-batch` | `backend/routes/upload.py:272` | Bulk upload — premium, disabled |

### A.3–A.5 Storage; Supabase Storage; privacy

- Source documents are stored in **Supabase Storage**, bucket **`documents`**,
  path `uploads/{organization_id}/{YYYY}/{MM}/{DD}/{uuid4}_{filename}`
  (`v3_documents.py:83-89`; legacy `upload.py:608`).
- **Supabase Storage: yes.**
- **Privacy:** For the V3 surface, yes — migration
  `supabase/migrations/20260823000000_d32_private_documents_storage.sql` sets
  `storage.buckets.public = FALSE` for `documents`, enables RLS on
  `storage.objects` with org-scoped policies (`d32_documents_*_org_member`),
  and the API serves documents only via short-lived signed URLs
  (`services/storage.py::storage_signed_url`; `/api/v3/documents/{id}/signed-url`).
  The **legacy** `/api/upload` route still calls
  `supabase.storage.from_(bucket).get_public_url(...)` (upload.py:610) — a
  private bucket would not return a usable public URL, so this legacy path is
  inconsistent with the D32 hardening.

### A.6 Document metadata

- `organization_files` table (`supabase/migrations/00000000000000_init_schema.sql:541`):
  `name, path, size_bytes, file_type, mime_type, bucket, status, metadata jsonb`.
  V3 metadata carries `{data_type, file_url}`; `file_url` is a signed URL.
- `customer_documents` (legacy parallel store) — see glossary §15.3 conflict.

### A.7–A.10 Document → Processing Work / batches / multiple items

- **Entry into Processing Work:** automatic. `upload_document` creates a
  `manual_extraction_item` in a reusable auto-created **"Uploads"** batch
  (`v3_documents.py:119-146`, D23). Failures to enqueue never fail the upload.
- **Batch association:** `manual_extraction_items.batch_id →
  manual_extraction_batches.id` (init schema:1139). Batches can also be created
  explicitly via `POST /api/v3/manual-extraction/batches` and items added via
  `POST .../batches/{id}/items`.
- **Multiple documents per batch:** yes.
- **One document → multiple extraction items:** no. Each upload creates exactly
  one item; a document is multi-record via `extracted_data.line_items[]`
  (D23 multi-line), not via multiple items.

### A.11–A.12 File-type/size checks; malicious-file handling

- V3 upload: **no size limit, no type allow-list, no content sniffing**
  (client `Content-Type` and filename extension only). Legacy routes do
  enforce size + allowed types.
- Malicious/untrusted-file handling: **none** — no magic-byte validation, no
  virus scanning, no decompression-bomb protection; `content-type` is taken
  from the client. `python-magic` is in requirements but not used in the upload
  paths examined.

---

## 4. PDF Processing (audit section B)

Implementation under audit: `backend/pdf_engine.py` (`PDFExtractor`) — **there
is no `backend/engines/pdf_ocr.py`**; the closest file
`backend/engines/pdf_render.py` is the **white-label report PDF output
renderer** (reportlab), not an input-document OCR engine.

| Question | Answer | Evidence |
|---|---|---|
| 1. Read text-based PDF | **Yes (legacy path only)** | `_extract_text_direct` uses `pdfplumber` page loop (`pdf_engine.py:57-69`); triggered from `extract_and_parse` |
| 2. Detect image/scanned PDF | **Yes (heuristic)** | `extract_and_parse` falls back to OCR when extracted text `< 50` chars (`pdf_engine.py:33-37`) |
| 3. Render PDF pages | **Yes (legacy)** | `_extract_text_ocr` → `pdf2image.convert_from_path(..., dpi=300)` (`pdf_engine.py:73-85`) |
| 4. OCR scanned pages | **Yes (legacy)** | `pytesseract.image_to_string(img)` |
| 5. Multi-page PDF | **Yes (legacy)** | loop over all rendered pages; `_get_page_count` via pdfplumber |
| 6. Preserve page references | **No** | parsed `data_streams` carry no page numbers; page_count only in `file_metadata` |
| 7. Preserve source coordinates | **No** | tesseract data output not used |
| 8. Store OCR output | **No** | no OCR column/table in schema; extraction result only returned in the HTTP response or stored in `organization_files.metadata.extraction_result` / `manual_review_queue.auto_extraction_result` (legacy) |
| 9. Associate extracted values with evidence | **No** | legacy parser output has no pointer to page/region; V3 chain evidence stops at `source_page` which is typed by a human |
| 10. OCR failure handling | **Partial** | returns `{"status":"error"}`; legacy `/api/upload-pdf` then queues manual review or returns error (`upload.py:206-262`) |
| 11. Poor-quality scans | **Not handled** | no preprocessing/deskew; only a `< 50` char threshold |
| 12. Rotated pages | **Not handled** | no rotation detection/normalisation |
| 13. Tables | **Partial/naive** | fuel-invoice parser is line-regex based (`_parse_fuel_invoice`); utility bill uses regex; `_parse_scope3_document` explicitly returns "not implemented" |
| 14. Invoices/statements/utility bills | **Partial** | `_parse_utility_bill`, `_parse_fuel_invoice` exist; Scope-3 documents return "not implemented"; **hardcoded demo assets** ("Birmingham Hub Main Floor") are used when no assets are passed (`upload.py:206-208`) |

**Execution-path trace:** `POST /api/upload-pdf`
(`backend/routes/upload.py:184`) → `validate_file_upload` → `PDFExtractor()
.extract_and_parse(bytes, filename, data_type, assets)` (`pdf_engine.py:28`)
→ `_extract_text_direct` (pdfplumber) → fallback `_extract_text_ocr`
(tesseract) → `_parse_utility_bill/_parse_fuel_invoice/_parse_scope3_document`.
`POST /api/upload` (`upload.py:552`) runs the same `extract_and_parse` for both
PDF **and** IMAGE. **No V3 route invokes `PDFExtractor`.**

---

## 5. JPG / Image Processing (audit section C)

- Image OCR method exists: `PDFExtractor.extract_and_parse_image`
  (`pdf_engine.py:284-339`) — `PIL.Image.open` → `pytesseract.image_to_string`
  → same parsers.
- **It is NOT reachable from any production route.** The only route that
  classifies images (`/api/upload`, `upload.py:588-592`) calls
  `extract_and_parse` (PDF path) for `IMAGE` files (`upload.py:664-675`).
  `pdfplumber.open()` will raise on a JPG/PNG, then `_extract_text_ocr` runs
  `convert_from_path(io.BytesIO(image_bytes))` which also fails, so the
  extraction returns `{"status":"error"}` and the file is routed to
  `staff_review`/`manual_review_queue` without any OCR text. The
  `extract_and_parse_image` method is referenced only by the non-production
  backup files `backend/main copy.py` / `main copy 2.py`.
- **Trace (actual):**
  ```
  image → /api/upload (legacy) → extract_and_parse (PDF path) → fails → error
          → organization_files.status='staff_review' + manual_review_queue row
  ```
- Preprocessing: none. Confidence: fixed per-field constants (0.95/0.90/…),
  not real OCR confidence. Failure behavior: error status + manual-review
  fallback. Persistence of OCR text: none.

---

## 6. OCR Engine (audit section D — `backend/engines/pdf_ocr.py` does not exist)

The audit's named file `backend/engines/pdf_ocr.py` **does not exist**.
OCR capability lives in `backend/pdf_engine.py` (legacy) and
`backend/routes/upload.py` `/api/repair-pdf`.

| Question | Answer |
|---|---|
| 1. Engine implemented? | Yes (`backend/pdf_engine.py::PDFExtractor`) |
| 2. Actually called? | Only by legacy routes `/api/upload`, `/api/upload-pdf` (+ `/api/repair-pdf` uses its own inline tesseract); **not** by any `/api/v3/*` route |
| 3. Providers | Local **Tesseract** (via `pytesseract`), rendered by `pdf2image` (poppler). No cloud OCR, no OCR-space; AI extraction is a separate LLM engine (unwired) |
| 4. Deterministic/local/external | **Local, deterministic** (same bytes → same text) |
| 5. OCR output persisted? | **No** |
| 6. Linked to source documents? | No (transient in response / legacy `metadata.extraction_result`) |
| 7. Linked to extraction items? | No |
| 8. Available for human review? | **No** — the V3 ops workspace shows only the signed-URL document viewer; OCR text is never surfaced (`item_workspace` returns `file_url`, no text) |
| 9. Page/source references | Page count only; no per-page mapping to extracted values |
| 10. OCR confidence stored? | No (hardcoded parser confidences in response only) |
| 11. OCR errors handled? | Partially (error status → manual review in legacy) |
| 12. Unit tests | **None** (no test imports `pdf_engine`) |
| 13. Integration tests | **None** |
| 14. Document→OCR E2E test | **None** |

---

## 7. AI-Assisted Extraction (audit section E)

- **Engine implemented:** Yes — `backend/engines/ai_extraction.py::AIExtractionEngine`
  (LLM via `infra.llm_client.LLMClient`, deterministic JSON parsing, confidence
  bounds, `AIExtractionFailedError` → HTTP 502). Unit tests:
  `backend/tests/unit/engines/test_ai_extraction.py`; integration test:
  `backend/tests/integration/test_ai_extraction.py::test_ai_extraction_end_to_end`.
- **Orchestrator implemented:** Yes —
  `backend/engines/workflow.py::WorkflowOrchestrator` (stages, retries, latches,
  event persistence, DOCUMENT_STATUS_MAP, `InvoiceActivityResolver`,
  `auto_review` default `True`). Tests: `backend/tests/unit/engines/test_workflow.py`
  and `backend/tests/integration/test_workflow.py`
  (`test_workflow_end_to_end_completes_with_persisted_state` — runs
  text→extraction→AI→match→calculate→DB with a mocked LLM).
- **Production HTTP wiring: NOT WIRED.** `grep -rln "AIExtractionEngine"`
  across `backend/api/ backend/routes/ backend/main*.py` returns **nothing**.
  `WorkflowOrchestrator` is referenced only by `engines/__init__.py`,
  `engines/workflow.py` and tests. The DI composition root
  (`backend/api/dependencies.py`) wires matching/calculation/validation/
  benchmarking/report engines but **not** the extraction engines or the
  orchestrator.
- Which routes use deterministic/manual extraction? The manual pipeline:
  `/api/v3/processing/items/{id}/extract`, `/api/v3/ops/items/{id}/extract`
  (human-supplied `extracted_data`).
- Inputs/outputs: text → `ExtractionField[]` (field/value/confidence/source="ai").
  Input text for the orchestrator is whatever the caller passes (there is no
  route that produces it from a PDF/OCR).
- Human review mandatory? In the orchestrator: only below
  `ai_confidence_threshold=0.5` or when no activity/no match — **`auto_review`
  defaults to `True`**, so a successful high-confidence match auto-approves
  customer review. In the manual pipeline review is a separate gate.
- AI results persisted? Only as `domain_events` + audit entries **if the
  orchestrator runs** (it doesn't over HTTP). No dedicated table.
- PDF/OCR/JPG input to AI extraction: no route feeds PDF/OCR output into
  `AIExtractionEngine`.
- E2E tested? At **engine** level with mocked LLM (integration test) — not at
  the HTTP level.

**Distinction used:** ENGINE IMPLEMENTED ✓ · PRODUCTION ROUTE WIRED ✗ ·
END-TO-END VERIFIED ✗.

---

## 8. Structured Extraction (audit section F)

| Question | Answer |
|---|---|
| 1. Tables storing extracted data | `manual_extraction_items.extracted_data` (JSONB), `mapped_data` (JSONB); legacy `manual_review_queue.auto_extraction_result/manual_extraction_result` |
| 2. Fields | Free-form JSONB; D23 convention: header `{supplier, invoice_date}` + `line_items[] {activity, description, quantity, unit, amount}` (see `backend/api/v3_operations.py::_run_line_calculation`, `backend/engines/processing_workflow.py::_validate_line_items`); single-line legacy: `{supplier, date, activity, quantity, unit}` |
| 3. Multiple activity records from one document | Yes — multiple `line_items` on one item (one document → one item → N lines); not N items |
| 4. One activity → one or more evidence locations | `calculation_snapshots.source_item_id → manual_extraction_items`, `source_file`, `source_page` (single page integer). Multi-evidence locations (several pages per line) not supported |
| 5. Human edit extracted values | Yes — `extract`/`map` endpoints overwrite `extracted_data`/`mapped_data` |
| 6. Edits audited | **No** — `save_extracted_data`/`save_mapped_data` (`backend/data/manual_extraction.py:390-437`) overwrite in place with no old-value audit; the routes do not record `audit_trail` entries. (Calculation and evidence-access are audited.) |
| 7. Original values preserved | **No** — in-place overwrite |
| 8. Extraction → mapping | Yes — status machine `pending→extracting→extracted→mapping→mapped→…` (`backend/domain/partners.py::ITEM_STATUS_FLOW`) |

---

## 9. Emission Factor Database (audit section G)

- **Table:** `emission_factors`
  (`supabase/migrations/00000000000000_init_schema.sql:621`; extended with
  `import_batch_id` in `20260807010000_add_emission_factors_import_batch.sql`).
  Columns: `reporting_year, activity_type, co2e_multiplier, unit, scope,
  factor_source, factor_set, country, import_batch_id` (domain model
  `backend/domain/factor.py::EmissionFactor` adds `provider_key`,
  `natural_key`).
- **DEFRA factors:** committed SQL artifact `output/sql/import_defra_2025.sql`
  = **7,029 `INSERT … WHERE NOT EXISTS` statements** — `factor_source='DEFRA-DESNZ'`,
  `factor_set='DEFRA-2025'`, `country='GB'`, `reporting_year=2025`.
- **SEAI (Irish) factors:** importer `src/commands/import_seai.py` +
  provider `src/providers/seai/` (parser/mapper/validator/exporter) reading the
  committed source workbook `tools/carbon_data_factory/factors/
  SEAI-conversion-and-emission-factors.xlsx` (28 source rows → 20 factors,
  factor_set `SEAI-2025`, country `IE`, year 2025). **No SEAI SQL artifact is
  committed** (`output/seai_2025/` is referenced by docs but absent from the
  repo). `docs/cline/CarbonTally-SEAI-Development-DB-Import-v1.0.md` records a
  **development-database** import of 20 SEAI rows (batch
  `9e3b2c8a-…`, total 7,049).
- **Reporting years:** only 2025 in committed artifacts.
- **Countries:** GB (DEFRA), IE (SEAI); schema `country` CHECK allows
  `GB|IE` (glossary §3).
- **Units:** diverse — tonnes, litres, kWh (Gross/Net CV), km, miles, m3, kg,
  passenger-km, etc. (visible in the DEFRA SQL).
- **Scopes:** `Scope 1 | Scope 2 | Scope 3` (+ `Outside of Scopes` canonical
  vocabulary in `core/types.py`).
- **Factor identification:** natural key
  `(reporting_year, activity_type, country, unit, scope)`; unique index
  `emission_factors_year_activity_country_uniq` (init schema:2160).
- **Versioning:** `import_batches` table (provider, batch metadata, checksum,
  `status`); `factor_source`/`factor_set` labels; factors are deactivated by
  clearing `import_batch_id` (`deactivate_by_batch`), never hard-deleted
  (snapshot FK `ON DELETE RESTRICT`).
- **Multiple sets coexist:** yes (same table, discriminated by
  `factor_source`/`factor_set`/`country`).
- **Factor source recorded:** yes (`factor_source`, `import_batch_id`).
- **Reporting year recorded:** yes. **Country recorded:** yes.
- **Customer-org factor selection:** not automatic (see §12).

**Caveat:** The **live database contents cannot be verified from the
repository** (no connection available; no committed SEAI artifact). "Database
contains factors" is therefore: DEFRA — strongly evidenced (committed SQL);
SEAI — evidenced only by documentation of a dev-DB import.

---

## 10. Irish / SEAI Factor Set (audit section I)

| Question | Answer |
|---|---|
| 1. Dataset actually present in DB? | **NOT VERIFIED FROM REPOSITORY.** 20-row import documented against the *development* DB (`docs/cline/CarbonTally-SEAI-Development-DB-Import-v1.0.md`); no committed SEAI artifact. |
| 2. Source | SEAI "Conversion and emission factors" 2025 workbook (committed xlsx) |
| 3. Reporting years | 2025 |
| 4. Country | `IE` |
| 5. Factor-set identifier | `SEAI-2025` |
| 6. Units normalized? | Mapped to canonical DEFRA-style unit strings (`litres`, `kWh`, `kg`); no dimensional conversion |
| 7. Categories normalized? | Mapped to RC2 activity labels with `(kg CO2)` suffix to preserve CO2-only semantics (`domain/factor.py::gas_coverage`) |
| 8. Coexist with DEFRA | Yes — same table, same index |
| 9. Matching engine selects Irish factors? | **Yes at engine level** — stages filter by `request.country`; verified by `src/providers/seai/tests/test_defra_regression.py` (`test_country_selection_prevents_gb_ie_confusion`) and by an independent in-memory run in this audit (GB→DEFRA, IE→SEAI) |
| 10. Country/factor-set selection configurable? | Per-request `country` field (default `"GB"`) in `CalculateIn`; `preferred_provider` optional in `MatchRequest` but not set by the composition root; **no org-level factor-set config** |
| 11. Connected to same matching engine | Yes |
| 12. Separate Irish mapper | No — same engine, country filter |
| 13. Calculation works with Irish factors | Yes — `CalculationEngine` applies any `EmissionFactor`; `test_calculation_with_seai_factor_unchanged` |
| 14. Selected Irish factor persisted? | Yes — snapshot `factor_id`/`factor_source`/`factor_set` |
| 15. Source/version persisted | `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `import_batch_id` |
| 16. E2E test using an Irish factor | **Partial** — engine-level matching + calculation tests in `src/providers/seai/tests/` (needs test DB); **no HTTP-level E2E test** |

**Distinction used:** DATABASE — documented dev import only · MATCHING —
engine verified · CALCULATION — engine verified · PERSISTENCE — schema verified.

---

## 11. Factor Matching / DEFRA Mapping (audit sections H & J)

- **Matching method:** deterministic staged pipeline
  (`engines/factor_matching.py::FactorMatchingEngine` +
  `engines/matching_stages.py`): `exact_match → natural_key → alias_match →
  keyword_search → fuzzy_match` (default `MatchingPipelineConfig`; semantic
  stage disabled). Keyword scoring = query-token coverage of
  `activity_type` (`infra/search_index.py::FactorSearchIndex.keyword_search`),
  deterministic ordering; fuzzy = `difflib.SequenceMatcher` ≥ 0.85.
- **Deterministic:** yes. **Fuzzy:** yes (enabled by default). **AI:** no
  (semantic disabled; not wired).
- **Candidate matches retained:** yes — `MatchResult.suggestions` for
  ambiguous/no-match; `/api/v3/emissions/factors` search; ops
  `/mapping-options` returns up to 20 candidates
  (`EmissionFactorsRepository.find_by_activity`).
- **Selected factor stored:** `manual_extraction_items.emission_factor_used`
  (manual pipeline) and `calculation_snapshots.factor_id` (engine).
- **Factor version/source stored:** snapshot `factor_source`, `factor_set`,
  `import_batch_id` (`engines/calculation.py::calculate → save_snapshot`).
- **Unit conversion stored:** none (exact-match only).
- **Human override:** yes — `map_item` accepts an arbitrary
  `emission_factor_used`/`factor_id` (`v3_processing_workflow.py::map_item`).
- **Override audited:** no.
- **Mapping confidence stored:** no (manual pipeline); engine confidence is
  returned in `MatchResult` but not persisted for the manual path.
- **Unmatched/ambiguous retained for review:** in the (unwired) orchestrator
  they route to `manual_review`; in the manual pipeline the human resolves
  them; `POST /api/v3/emissions/calculate` returns HTTP 422 on non-match.
- **Connected to extraction workflow:** in the manual pipeline yes (map stage);
  in the automated orchestrator not wired.

**Factor-set selection:** currently **per-request/user selection**, not
org-driven:
- `CalculateIn.country` default `"GB"` (frontend dropdown in
  `EmissionsPage.jsx`), `reporting_year` default current year.
- `organizations.country` and `organizations.default_factor_year` are stored
  but **not** read by the calculate/matching path
  (`default_factor_year` only appears in the org repo/API model).
- `MatchingPipelineConfig.prefer_provider/restrict_country` exist but are not
  set by `get_matching_engine` (`api/dependencies.py:344`).

---

## 12. Unit Normalization (audit section K)

| Question | Answer |
|---|---|
| 1. Unit normalization implemented? | **No general conversion.** Only an exact-unit contract plus a **qualifier normalizer** in the ops route: `_resolve_unit_for_factor` (`backend/api/v3_operations.py:323`) promotes `"kWh"` → `"kWh (Gross CV)"` when one string contains the other. Not present in `/api/v3/processing/*/calculate`. |
| 2. Conversion deterministic? | N/A — there is no dimensional conversion (litres→kg, miles→km, m3→kg, passenger-km) anywhere |
| 3. Incompatible units rejected? | Yes — `EmissionFactor.calculate_emissions` raises `UnitMismatchError` → HTTP 422 (`domain/factor.py:110-120`, verified in this audit) |
| 4. Conversions recorded? | No |
| 5. Original quantity preserved? | Yes — snapshot `quantity` + `quantity_unit` (raw) |
| 6. Normalized quantity preserved? | No such concept; unit only rewritten in ops request, original `extracted_data.unit` untouched |
| 7. Factor unit preserved? | Yes — snapshot `co2e_multiplier` + factor row |

---

## 13. Calculation Engine (audit section L)

`backend/engines/calculation.py` is **implemented, wired and tested**:

1. Accepts mapped factors — yes (`CalculationRequest.factor` / `customer_factor`).
2. Calculates CO2e — yes (`_compute_co2e`, `RESULT_PRECISION` quantise).
3. Unit conversion — no (strict match; see §12).
4. Preserves inputs — yes (snapshot: quantity, quantity_unit, multiplier, date,
   reporting_year, activity, activity_type, scope, methodology).
5. Snapshots the selected factor — yes (`co2e_multiplier` copied; `factor_id`
   FK `ON DELETE RESTRICT`).
6. Factor source/version — yes (`factor_source`, `factor_set`,
   `import_batch_id`, D33 adds `source_item_id`, `source_file`, `source_page`).
7. Result traceable to source document — yes via
   `emissions_logs.snapshot_id → calculation_snapshots.source_item_id →
   manual_extraction_items.file_id → organization_files` (D33 migration
   `20260823010000_d33_evidence_traceability.sql`; reverse lookup
   `/api/v3/documents/{id}/emissions`).
8. Results persisted — yes (`calculation_snapshots` + `emissions_logs` +
   `manual_extraction_items.calculated_emissions_kg_co2e`).
9. Recalculation — yes, each call creates a new snapshot; `verify(snapshot)`
   re-computes and checks `content_hash` (`CalculationEngine.verify`).
10. Previous results preserved — yes (append-only snapshots).
11. Errors validated — yes (`UnitMismatchError`, negative quantity, unknown
    methodology, no-factor). Note: snapshot write and emissions-log write are
    two separate repo calls with **no explicit DB transaction** wrapping both.

---

## 14. Evidence / Traceability (audit section M)

Persisted chain (D33):

```
organization_files (id)
   ↑ file_id (FK, ON DELETE SET NULL)
manual_extraction_items (id)
   ↑ source_item_id (FK)
calculation_snapshots (id: factor_id, factor_source, factor_set,
                       quantity, quantity_unit, co2e_multiplier, co2e_kg,
                       source_file, source_page, content_hash)
   ↑ snapshot_id
emissions_logs (calculated_kg_co2e, scope, date)
```

Exposed evidence surfaces:
- `GET /api/v3/emissions/{log_id}/evidence`
  (`v3_emissions.py:372`, domain `backend/domain/evidence.py`).
- `GET /api/v3/documents/{file_id}/emissions` (reverse lookup; D33.1).
- Evidence completeness is classified **honestly** (`COMPLETE` requires
  document + extracted line + **page** + calculation + factor; `PARTIAL`
  without a page; `UNAVAILABLE` otherwise) — `classify_evidence_completeness`,
  `source_location_precision` never fabricate a page.
- `source_page` is currently human-supplied (`CalculatePayload.source_page`)
  or absent; the automatic pipeline does not extract it.

---

## 15. Database Persistence (audit section N)

| Item | Persisted | Table |
|---|---|---|
| Source document | Yes | Supabase Storage `documents` bucket + `organization_files` |
| Extraction | Yes | `manual_extraction_items.extracted_data` |
| Mapped activity | Yes | `manual_extraction_items.mapped_data`, `emission_factor_used`, `mapped_facility/asset/supplier_id` |
| Selected factor | Yes | `emission_factor_used` + `calculation_snapshots.factor_id` |
| Calculation | Yes | `calculation_snapshots` + `emissions_logs` + item `calculated_emissions_kg_co2e` |
| Evidence | Yes | D33 snapshot source columns + evidence endpoints |
| Validation status | Yes | item `status` + `issues` rows (`work_item_id`/`batch_id`) |
| Review status | Yes | item `customer_approved/customer_reviewed_by/at`, `qc_by/qc_at/quality_score` |
| Audit history | Partial | `audit_trail` (calculation, evidence access, batch assignment, workflow events); **not** extract/map edits |

No changes were made to any database or schema.

---

## 16. Human Review (audit section O)

1. Extraction reviewable — yes (re-save via `extract`; multi-line editing in
   `ExtractionPanel.jsx`).
2. Mapping reviewable — yes (`map`; validation requires a factor).
3. Calculation reviewable — yes (`customer-review` approve/reject;
   rejection routes back to `mapping`/`extracting` per `ITEM_STATUS_FLOW`).
4. Human edits persisted — yes.
5. Original values remain available — **no** (in-place overwrite).
6. Review status persisted — yes (item statuses + columns).
7. Reviewer identity persisted — yes (`extracted_by`, `qc_by`,
   `customer_reviewed_by`, `calculated_by` on snapshot).
8. Changes auditable — **partially** (engine actions + evidence access are
   audited; human extract/map edits are not recorded with before/after values).

---

## 17. Production HTTP Wiring (audit section R)

| Capability | Wired route | Engine behind it |
|---|---|---|
| Upload (any file) | `POST /api/v3/uploads` | Storage + `organization_files` + enqueue (no extraction) |
| PDF text extraction | `POST /api/upload-pdf`, `/api/upload` (legacy) | `pdf_engine.PDFExtractor` |
| Scanned-PDF OCR | legacy only | `pdf_engine._extract_text_ocr` |
| JPG OCR | **none functional** (route calls wrong method) | `extract_and_parse_image` dead code |
| AI extraction | **none** | `AIExtractionEngine` (engine-only) |
| Automated workflow | **none** | `WorkflowOrchestrator` (engine-only) |
| Manual extraction (human) | `/api/v3/processing/items/{id}/extract`, `/api/v3/ops/.../extract` | data repo (JSONB) |
| Factor matching | `POST /api/v3/emissions/calculate` (match branch), `/api/v2/factor-match` | `FactorMatchingEngine` |
| Calculation | `/api/v3/emissions/calculate`, `/api/v3/processing/items/{id}/calculate`, `/api/v3/ops/.../calculate` | `CalculationEngine` |
| Validation | `/api/v3/processing/items/{id}/validate`, `/api/v3/ops/items/{id}/validate` | `validate_processing_item` + issues |
| Report generation / PDF output | `/api/v3/reports`, `/api/v3/reports/{id}/pdf` | `ReportGenerationEngine`, `pdf_render.py` |

Implemented in Python but **not reachable** through the production HTTP path:
`engines/extraction.py`, `engines/ai_extraction.py`, `engines/workflow.py`,
`pdf_engine.extract_and_parse_image`.

---

## 18. End-to-End Tests (audit section P)

| Scenario | Status | Evidence |
|---|---|---|
| 1. PDF → extraction/OCR → activity → DEFRA → calc → DB | **NOT TESTED** | No test opens a PDF; the closest is `backend/tests/integration/test_workflow.py::test_workflow_end_to_end_completes_with_persisted_state`, which feeds **raw text** to the orchestrator (not wired over HTTP) |
| 2. Scanned PDF → OCR → activity → DEFRA → calc → DB | **NOT TESTED** | No OCR tests anywhere |
| 3. JPG → OCR → activity → DEFRA → calc → DB | **NOT TESTED** | No image tests |
| 4. Document → extraction → Irish matching → calc → DB | **PARTIAL** | `src/providers/seai/tests/test_defra_regression.py` covers **matching + calculation** with real IE/GB factors at engine level (requires test DB); no full HTTP E2E |
| 5. Document → extraction → human correction → mapping → calc → DB | **PARTIAL** | `backend/tests/unit/api/test_v3_d23_extraction_ux.py` (`test_internal_operator_multi_line_calculate`, `test_entity_staff_multi_line_calculate`, `test_upload_enqueue_reuses_uploads_batch_and_creates_item`) exercises the API with in-memory fakes; not a full document run |

Additional relevant automated tests (safe, engine-level):
- `backend/tests/integration/test_calculation.py` — snapshot persistence,
  content-hash verification, unit-mismatch rejection.
- `backend/tests/integration/test_factor_matching.py` — pipeline, suggestions,
  events, audit.
- `backend/tests/unit/api/test_evidence_traceability.py`,
  `test_evidence_record.py` — evidence chain + honesty rules.
- `backend/tests/unit/api/test_v3_emissions.py` — calculate endpoint contract.

Running the suites: **not performed.** `pytest` is not installed in the audit
environment and installing dependencies was prohibited by the audit's
READ-ONLY mandate. An independent, non-destructive in-memory verification of
`domain.factor.calculate_emissions` (unit mismatch rejection), `gas_coverage`
(SEAI=CO2, DEFRA=CO2e) and `FactorMatchingEngine` country routing
(GB→DEFRA-DESNZ, IE→SEAI) was executed successfully against the checked-out
source.

---

## 19. Demo Data Analysis (audit section Q)

- The claimed demo result **10,732.4 kg CO2e does not appear anywhere in the
  repository** (searched code, SQL, JSON, CSV, Markdown, TS). It cannot be
  traced to the production calculation path.
- `clean_emissions_output.json` (repo root) is an output of the **legacy CSV
  pipeline** (`process_fuel_data`, `backend/utils/emissions.py`) — per-row
  `Total kgCO2e = Volume(L) × DEFRA Factor (kgCO2e/L)` with factors from the
  legacy `defra_conversion_factors`/DB lookups, **not** the V3
  `CalculationEngine` snapshot path. Its figures (e.g. 2.54 kgCO2e/L diesel)
  also differ from the committed DEFRA-2025 value.
- `backups/seed.sql` is a **legacy-schema pg_dump** (UTF-16) that predates the
  V3 tables (`emission_factors`, `calculation_snapshots`,
  `manual_extraction_items` are absent); it contains no V3 pipeline evidence.
- `demodatagen/generators/carbon/*.py` are **empty files** — the demo data
  generator does not actually produce emissions logs.
- Conclusion: **no demo result in the repository proves end-to-end
  processing.** The demo figures that exist are static/legacy-path artifacts.

---

## 20. Failure Handling (audit section S)

| Failure | Behavior | Recoverable/Reviewable? |
|---|---|---|
| OCR fails | Legacy: `{"status":"error"}` → manual-review queue (auto-repair) or error; V3: OCR never runs | Partially (legacy queue row) |
| Document unreadable | Same as OCR failure; `<50` chars triggers OCR fallback then error | Partially |
| No factor matches | `/calculate` → HTTP 422 `no factor matched`; orchestrator (unwired) → `manual_review` | Yes — item remains reviewable |
| Multiple factors match | Matching → `ambiguous`; `/calculate` → 422; orchestrator → `manual_review` | Yes |
| Unit incompatible | `UnitMismatchError` → 422; nothing persisted | Yes — item stays `mapped`/`validated` |
| Calculation fails | Engine raises; item status unchanged; snapshot not created | Yes |
| AI extraction fails | `AIExtractionFailedError` → 502 (engine only; not wired) | N/A over HTTP |
| DB persistence fails | Error propagates (500); snapshot/log writes are separate calls without an explicit transaction | Partial |
| Human review rejects | Item → `rejected`; `ITEM_STATUS_FLOW` allows rework to `mapping`/`extracting` | Yes |

---

## 21. Capability Matrix (audit section T)

| Capability | Implemented | Wired | Tested | End-to-End Verified | DB Persisted | Notes |
|---|---|---|---|---|---|---|
| PDF upload | ✅ | ✅ (`/api/v3/uploads`, legacy) | ✅ (upload repo test) | ❌ | ✅ (`organization_files`) | No extraction at upload |
| PDF text extraction | ✅ (legacy engine) | ⚠️ legacy only | ❌ | ❌ | ❌ | `pdf_engine`; not in V3 HTTP path |
| Scanned PDF OCR | ✅ (legacy engine) | ⚠️ legacy only | ❌ | ❌ | ❌ | tesseract fallback; output not persisted |
| JPG OCR | ⚠️ method exists | ❌ (wrong method called) | ❌ | ❌ | ❌ | `extract_and_parse_image` dead code |
| Multi-page PDF | ⚠️ legacy loop | ⚠️ legacy | ❌ | ❌ | ❌ | page count only |
| Structured extraction | ✅ (manual JSONB + D23 lines) | ✅ | ✅ (unit API tests) | ⚠️ engine test only | ✅ | Human data-entry |
| AI-assisted extraction | ✅ engine | ❌ | ✅ (unit/integration engine) | ❌ | ⚠️ events only | Not in DI graph / no route |
| Human extraction | ✅ | ✅ | ✅ (D23 UX tests) | ⚠️ | ✅ | Core ops UX |
| Human review | ✅ (customer/QC/review gates) | ✅ | ✅ (some) | ⚠️ | ✅ | Edits not audited; originals not kept |
| DEFRA factors | ✅ (7,029 SQL artifact) | ✅ | ✅ (repo/matching tests) | ⚠️ | ⚠️ (artifact; live DB unverified) | Year 2025 only |
| DEFRA matching | ✅ | ✅ (`/calculate`, `/api/v2/factor-match`) | ✅ | ⚠️ engine | ✅ (snapshot factor_id) | Deterministic staged |
| Irish/SEAI factors | ✅ (importer + docs of dev import) | ⚠️ (data load is CLI/doc) | ✅ (import/mapper/parser tests) | ⚠️ | ⚠️ NOT VERIFIED for production | No committed artifact |
| Irish/SEAI matching | ✅ engine | ✅ (country param) | ✅ (SEAI regression) | ❌ HTTP | ✅ (snapshot) | Manual country selection |
| Factor-set selection | ⚠️ per-request country | ✅ (payload) | ✅ (contracts) | ⚠️ | ❌ (no org-level config) | Not org-driven |
| Unit normalization | ❌ (exact-match only + ops qualifier helper) | ⚠️ ops only | ✅ (mismatch rejected) | ❌ | ❌ | No dimensional conversion |
| Calculation | ✅ | ✅ | ✅ | ⚠️ engine | ✅ | Snapshots + verify |
| Evidence | ✅ (D33 chain + endpoints) | ✅ | ✅ | ⚠️ | ✅ | Page human-supplied |
| Persistence | ✅ | ✅ | ✅ | ⚠️ | ✅ | See §15 |
| Audit trail | ⚠️ | ✅ (partial) | ✅ | ⚠️ | ✅ `audit_trail` | extract/map edits not audited |
| Export | ✅ | ✅ | ✅ | ⚠️ | ✅ | emissions.csv/json, documents.csv |

Legend: ✅ fully present · ⚠️ partial/conditional · ❌ absent.

---

## 22. Gap Matrix (audit section U)

| Gap | Evidence | Current State | Expected State | Priority |
|---|---|---|---|---|
| OCR not in production V3 workflow | `v3_documents.py` upload does no extraction; `pdf_engine` only in legacy routes | Extraction is 100% human data entry | Document OCR runs on upload for the V3 pipeline | **P0** (core promise) |
| AI extraction + orchestrator not wired | `grep AIExtractionEngine` in api/routes/main → empty; not in `dependencies.py` | Engines exist, tests pass, zero HTTP routes | Wire into upload/extraction route or worker | **P0/P1** |
| JPG OCR route calls wrong method | `upload.py:664` `extract_and_parse` for IMAGE; `extract_and_parse_image` unused in prod | Image OCR broken in the only route that attempts it | Call `extract_and_parse_image` for IMAGE files | **P0** (if images are a product requirement) |
| OCR output not persisted/surfaced | no OCR column/table; workspace shows only signed URL | Operators retype documents by hand; no OCR text for review | Persist OCR text+confidence; show in review UI | **P1** |
| No unit normalization | `domain/factor.py::calculate_emissions` exact match only | `UnitMismatchError` on litres vs kg etc. | Conversion layer (deterministic) before calculation | **P1** |
| extract/map edits not audited; originals overwritten | `data/manual_extraction.py` in-place UPDATE; routes don't audit | No before/after history for human corrections | Audit entries + original-value retention | **P1** |
| Irish factor presence not verifiable in production | no committed SEAI artifact; dev-DB doc only | Matching works at engine level; data load unverifiable | Commit/verify SEAI import for production DB | **P1** |
| No factor-set selection from org config | `default_factor_year` unused; country manual GB default | Per-request selection only | Org-driven default country/year/factor-set | **P2** |
| No document→OCR→result E2E test | no test opens PDF/JPG; no OCR tests | Engine-level E2E only (text input) | Add E2E with real sample bills (docs/sample_bills) | **P1** |
| Multi-page/source-coordinate evidence | no page refs in extraction; `source_page` human-typed | Page evidence not automatic | Preserve page per extracted line | **P2** |
| Legacy public-URL path inconsistent with D32 | `upload.py:610 get_public_url` vs private bucket | Legacy upload may produce unusable URLs | Migrate legacy path to signed URLs or retire | **P2** |
| V3 upload lacks size/type/magic validation | `v3_documents.py` no checks | Any file accepted; no malware handling | Enforce allow-list, size cap, content sniffing | **P2** |
| Cross-entity transaction for snapshot+log | `calculation.py` two separate sink calls | Partial-write risk on mid-failure | Single transaction or compensating write | **P3** |
| `demo result 10,732.4` not reproducible from repo | number absent; legacy output differs | No evidence of demo E2E | Re-derive demo through production path | **P2** |

---

## 23. Minimum Viable End-to-End Path

Minimum work to demonstrate a REAL document → emission-result pipeline through
the **production HTTP** stack:

1. **Wire OCR into the V3 upload path.** After `POST /api/v3/uploads` stores
   the file, run `pdf_engine`-style extraction (pdfplumber → tesseract) for
   PDF/IMAGE, fix the JPG branch to call `extract_and_parse_image`, and store
   the OCR text + per-page output on the `manual_extraction_item` (schema
   column or `extracted_data` seed) so it is reviewable.
2. **Wire the existing engines.** Expose a route (or extend the extract
   endpoint) that runs `DocumentExtractionEngine`/`AIExtractionEngine` over the
   stored OCR text, then `FactorMatchingEngine`, then `CalculationEngine` —
   all already built and tested; the composition root
   (`api/dependencies.py`) must add the extraction engines and optionally the
   `WorkflowOrchestrator`.
3. **Human review gate.** Keep `extract`/`map`/`validate`/`customer-review`
   endpoints (already wired) so an operator can accept/correct the automatic
   result; record audit entries and retain the original OCR/auto values.
4. **Confirm factor data in the production DB.** Verify DEFRA-2025 rows and
   import/commit the SEAI-2025 SQL artifact; confirm `get_factor_search_index`
   loads both (it already loads the whole `emission_factors` table).
5. **Add E2E tests** using the committed sample bills (`docs/sample_bills/*.pdf`)
   covering the five scenarios in §18.

No new architecture is required — the missing pieces are **wiring, one bug fix,
OCR persistence, and verification data**.

---

## 24. Recommended Next Engineering Steps

1. **P0 — Fix and wire OCR (upload-time).** Route extraction through the
   existing `pdf_engine` for PDF/IMAGE in the V3 pipeline; fix the image branch.
2. **P0 — Wire AI extraction / orchestrator** behind the extract endpoint
   (auto-extract with human override), reusing `AIExtractionEngine` and the
   stage logic of `WorkflowOrchestrator`.
3. **P1 — Persist OCR + auto-extraction output** (text, per-page, confidence,
   source) and surface it in the `item_workspace` UI for review.
4. **P1 — Audit human edits.** Record before/after for `extract`/`map`
   (reuse `audit_trail`); stop overwriting originals blindly.
5. **P1 — Unit conversion layer.** Add deterministic conversions for the units
   present in the factor DB (litres, kWh, tonnes, kg, miles, km, m3,
   passenger-km) with recorded conversion metadata, or reject explicitly.
6. **P1 — Factor-set selection by Customer Organisation.** Drive
   `country`/`reporting_year`/`factor_set` from the org record
   (`organizations.country`, `default_factor_year`) with user override.
7. **P1 — Verify and commit SEAI dataset** and add an HTTP-level Irish E2E
   test.
8. **P2 — Upload hardening** (size/type/magic checks) and legacy-path
   retirement or signed-URL migration.

---

## Appendix — Required Final Answers (audit section V)

1. **Can CarbonTally currently extract structured data from PDF documents?
   NO (over HTTP).** A legacy `pdf_engine` can parse digital PDFs, but no
   production V3 route invokes it; the V3 extraction is human data entry.
2. **Scanned PDFs? NO.** OCR exists only in legacy routes; not wired, not
   persisted, not tested.
3. **JPG/scanned documents? NO.** The only route that would OCR images calls
   the PDF method; image OCR is effectively dead code.
4. **Is OCR wired into the production workflow? NO.** Legacy `/api/upload*`
   only; the V3 upload does not extract.
5. **Is AI-assisted extraction wired into production HTTP? NO.** Engine +
   orchestrator exist and are tested; no route references them.
6. **Can extracted data be mapped against DEFRA factors? YES (manually).**
   The manual map step selects any factor; the engine can also match
   automatically. DEFRA-2025 artifact committed.
7. **Against Irish/SEAI? YES at engine level**, via `country=IE`; dataset
   presence in the live DB is **NOT VERIFIED FROM REPOSITORY**.
8. **Are DEFRA and Irish sets in the same database architecture? YES** —
   one `emission_factors` table discriminated by `factor_source/factor_set/
   country`; coexistence documented (7,049 total in dev DB).
9. **Can CarbonTally select the appropriate factor set? PARTIALLY** — per
   request/user (`country`, year, manual factor pick), not from Customer
   Organisation configuration.
10. **Can the calculation engine calculate from either factor set? YES** —
    any `EmissionFactor` (GB or IE) flows through `CalculationEngine`.
11. **Are selected factor and factor source/version persisted? YES** —
    `emission_factor_used`, snapshot `factor_id/factor_source/factor_set/
    import_batch_id`.
12. **Are extraction results persisted? YES** — `extracted_data` JSONB
    (human-entered); automatic/AI output is not persisted (unwired).
13. **Are mappings persisted? YES** — `mapped_data`, `emission_factor_used`.
14. **Are calculation results persisted? YES** — snapshots + `emissions_logs`
    + item value.
15. **Is the complete evidence chain persisted? YES at the schema level**
    (D33 chain), with honest completeness classification; page evidence is
    human-supplied.
16. **Can a human review and correct extraction/mapping before final
    calculation? YES** — extract/map/validate/review gates, rework loops.
    Edits are not audited and originals are not retained.
17. **Is the entire workflow demonstrably end-to-end? NO.** Document→OCR→
    result over HTTP is not wired; only engine-level and manual-path
    components are proven.
18. **Implemented but not production-wired:** OCR in V3 pipeline; AI
    extraction; workflow orchestrator; deterministic text extraction engine;
    image OCR method; semantic matching stage (disabled).
19. **Database-ready but not connected:** OCR output storage (no column);
    org-level factor-set config (`default_factor_year` unused);
    auto-extraction event replay (domain_events written only by unwired
    engines).
20. **Five most important capability gaps:** (1) OCR not in the production
    workflow; (2) AI extraction/orchestrator not wired; (3) JPG OCR broken;
    (4) no unit normalization; (5) extract/map edits unaudited with no
    original-value retention.
21. **Minimum work to demonstrate a REAL end-to-end pipeline:** wire the
    existing engines behind the upload/extract route (OCR → extraction → AI →
    matching → calculation), fix the image branch, persist and surface OCR
    output, verify the factor data (incl. SEAI) in the production DB, and add
    E2E tests with the committed sample bills (§23).

---

*End of audit. The repository was not modified; the canonical baseline
`d4dcca1eb11f86bcae497815c8592d688a7e305f` was inspected in an isolated clone.
No credentials, keys or personal data were reproduced.*
