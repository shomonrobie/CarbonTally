# CarbonTally V3 — OCR Synthetic Test Report

**Date:** 26 August 2026
**Task:** OCR Runtime + V3 Document Extraction Pipeline (dedicated engineering task)
**Status:** COMPLETE (end-to-end V3 pipeline verified; remaining gaps documented in §13/§14)

---

## 1. Runtime environment

| Item | Value |
|---|---|
| Host | Ubuntu Linux (`apt 3.2.0`), x86_64 |
| Python | 3.14.4 (backend venv) |
| Tesseract | 5.5.0 (provisioned from Ubuntu `.deb`s, extracted to a user prefix — **no root required**) |
| Leptonica | 1.86.0 |
| Poppler (`pdftoppm`) | present (`/usr/bin/pdftoppm`) |
| Backend | FastAPI/uvicorn on `localhost:8050` (local Supabase stack `127.0.0.1:54425/54426`) |
| Frontend | CRA dev server on `localhost:3000` |
| Factor baseline | 7,049 rows in `emission_factors` (7,029 DEFRA-2025 + 20 SEAI-2025), reproduced locally via the **approved** seed files (`output/sql/emission_factors.sql`, `output/seai_2025/sql/emission_factors_seai_2025.sql`) |

## 2. Tesseract version

`tesseract 5.5.0` / `leptonica-1.86.0`, `eng.traineddata` (English).

Provisioning is reproducible without root: `tools/provision_tesseract_local.sh [prefix]` downloads
`tesseract-ocr`, `libtesseract5`, `libleptonica6`, `tesseract-ocr-eng` via `apt-get download`,
extracts them with `dpkg-deb -x`, and writes `tesseract-env.sh` exporting
`TESSERACT_CMD`, `TESSDATA_PREFIX`, `LD_LIBRARY_PATH`. Container/Render provisioning (documented
in the script): `apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract5 poppler-utils`.

## 3. Extraction engine used

`backend/pdf_engine.py::PDFExtractor` — the existing hybrid engine (preserved, not rewritten):

- PDF: pdfplumber direct text; falls back to Tesseract OCR for scanned pages (using the
  `convert_from_bytes` fix, page markers `[page N]`, and env-driven `TESSERACT_CMD`).
- Images (JPG/PNG): PIL decode + Tesseract via `extract_image_text` (new additive primitive,
  reused by `extract_and_parse_image`).

## 4. Test documents

Generated deterministically by `tools/generate_synthetic_documents.py` into `/tmp/synth_docs`
(fixture supplier "Meridian Fuel Supplies Ltd", electricity invoice, ground truth embedded):

| Document | Type | Ground-truth fields |
|---|---|---|
| `electricity_digital.pdf` | digital text PDF (reportlab) | supplier, invoice no., date, **12500 kWh**, amounts (3125.00 / 3750.00 GBP), activity "Electricity" |
| `electricity_scanned.pdf` | scanned-style PDF (text rendered to image, wrapped in PDF) | same |
| `electricity_invoice.jpg` | JPG image | same |
| `electricity_invoice.png` | PNG image | same |

## 5. Extraction results

| Document | Method | Key terms found | Notes |
|---|---|---|---|
| digital PDF | `pdf_text` | **6/6** | pdfplumber text layer |
| scanned PDF | `tesseract_ocr` | **6/6** | OCR with `[page 1]` marker; `convert_from_bytes` path exercised |
| JPG | `tesseract_ocr` | **6/6** | |
| PNG | `tesseract_ocr` | **6/6** | |

Key terms: `Meridian`, `Electricity`, `12500`, `kWh`, `INV-2026-0417`, `3750.00`.


## 8. Mapping result

The extracted electricity activity was mapped to the existing DEFRA factor
`7913f01f-f328-4eaa-ac6d-ba37b42be652` — "Managed assets- electricity > Electricity generated >
Electricity: UK > kWh (kg CO2e) [kWh]", `co2e_multiplier = 0.177`, `unit = kWh`, country GB,
DEFRA-2025. `POST /api/v3/processing/items/{id}/map` persisted `emission_factor_used` + `factor_id`.

## 9. Calculation result

`POST /api/v3/processing/items/{id}/calculate` (authoritative engine):

- **12,500 kWh × 0.177 kg CO₂e/kWh = 2,212.5 kg CO₂e** (≈ 2.21 t CO₂e).
- Persisted `calculation_snapshots` row (immutable; `content_hash = 64d11b…`, `factor_id`,
  `quantity`, `quantity_unit`, `scope = Scope 2`, `methodology = direct_multiply`,
  `source_file`, `source_page`) and an `emissions_logs` row (`snapshot_id` linked).
- The same numeric result matches the seed-demo figure of 2,212.50 kg for 12,500 kWh — the
  calculation path is independently reproduced through the current production API.

## 10. Traceability result

Full chain verified via the live API and database:

```
organization_files (a29a305c…)
   ↑ file_id
manual_extraction_items (9d533a30…)
   ↑ source_item_id
calculation_snapshots (347888c9…; factor 7913f01f…; content_hash; source_file/source_page)
   ↑ snapshot_id
emissions_logs (0369326a…; 2212.5 kg CO2e; Scope 2)
```

`GET /api/v3/documents/{file_id}/emissions` reverse-lookup returns the linked emissions with
`evidence_status: "COMPLETE"` (document + extracted line + page + factor + calculation).

## 11. Security result

- **Org isolation:** `/ocr` is `require_org_member` + `ensure_org_access`; cross-org access is
  denied (unit-tested 403). Live: a same-org viewer is correctly allowed; a non-member is denied.
- **No document download/leak:** the OCR endpoint reads the private object server-side and returns
  only the extraction summary. Storage remains private with signed URLs only (D32).
- **RLS untouched.** **Processing-Entity restrictions untouched** (entity staff remain
  structurally outside the manual-extraction pipeline; no new download surface).
- OCR failure paths are fail-soft for the *upload* (item stays `pending` for human entry) but the
  OCR **endpoint** itself returns the summary/status only to the owning org.

## 12. Failure tests

| Case | Result |
|---|---|
| Digital PDF | `ok / pdf_text` |
| Scanned PDF | `ok / tesseract_ocr` |
| JPG/PNG | `ok / tesseract_ocr` |
| Unsupported type (`.txt`) | `unsupported` (upload succeeded; OCR status reported; no orphan record) |
| Empty/blank PDF | `no_text` (graceful; item remains `pending` for human entry) |
| Missing document id | `404` (unit-tested) |
| Missing storage object | `404` (unit-tested) |
| Engine failure | `_extract_document_text` never raises; returns `error` with detail (unit-tested) |
| Cross-org OCR | `403` (unit-tested) |

No orphan records are created by OCR paths; uploads always succeed; authorization is never
bypassed; document content is never returned.

## 13. Known limitations

- OCR quality depends on the tesseract runtime and source scan quality; low-quality/rotated scans
  will need human correction (the workflow is designed for that).
- OCR text is a reference surface; auto-structuring into `extracted_data` (deterministic field
  pre-fill) is not yet wired — a human confirms/enters the structured values (per the Product
  Owner decision register: extraction is reviewed by people).
- The legacy `/upload` surface still exists alongside V3 (see the finalization report §5 for the
  decommissioning sequence).

## 14. Remaining gaps

- **Deterministic field pre-fill:** feeding OCR text through `engines/extraction.py` into a
  suggested `extracted_data` (pre-fill, not auto-approve) is the natural next increment.
- **Synthetic corpus breadth:** the current set covers text PDF, scanned PDF, JPG, PNG with a
  single realistic layout. The external synthetic-documents-generator corpus (1,688 documents)
  remains the reference for broader coverage (multi-page, tables, rotations) once available.
- **Production tesseract provisioning** must be applied to the deployment image/Render build
  (documented in `tools/provision_tesseract_local.sh`).

---

# UPDATE 2 (26 Aug 2026) — Remaining OCR gaps closure

The three OCR-specific gaps from the dedicated OCR report were addressed. Status key:
**completed** · **verified** · **deferred** · **unavailable (external dependency)**.

## Gap 1 — Deterministic OCR → extracted_data field pre-fill: COMPLETED + VERIFIED

- New adapter `backend/services/extraction_suggestions.py::suggest(text)` reuses the existing
  deterministic engine (`engines.extraction.DocumentExtractionEngine`) — the engine gained an
  additive, side-effect-free `suggest_fields(text)` method. No new extraction system, no schema
  change.
- Suggested fields map to the existing V3 `extracted_data` keys (subset): `supplier`,
  `invoice_number`, `date`, `quantity`, `unit`, `activity`, `currency`, `net_amount`,
  `gross_amount`. Missing/ambiguous fields are reported in `unresolved` — never fabricated.
- Persisted on `organization_files.metadata.ocr` (`suggested_data` + `unresolved`) and surfaced in
  both item-workspace responses as `source.ocr_suggestions`, alongside `source.ocr_text`
  (reference) and `data.extracted_data` (human-confirmed). **No automatic approval:** the item
  stays `pending` with empty `extracted_data` until a human confirms via `POST .../items/{id}/extract`.
- Verified live: a synthetic electricity invoice upload produced
  `ocr_suggestions = {date, unit, activity, quantity: 12500.0, net_amount, gross_amount,
  invoice_number}` with `supplier` correctly left unresolved (the fixture's supplier line has no
  "Supplier:" label) and `extracted_data = {}`.

## Gap 2 — Broader synthetic corpus evaluation: COMPLETED (external corpus available)

The canonical external generator repository
(`github.com/shomonrobie/carbon_tally_synthetic_documents_generator`, HEAD `8ade2bf`) **was
available** and was cloned read-only to `/tmp/synth_gen_probe` (not into the CarbonTally repo; no
unrelated repository was modified). Corpus inspected: `samples/` with 1,909 PDFs + 1,896
ground-truth JSONs across `defra_aligned` (6), `scan_degradation` (2), `multi_currency` (3),
`visual_variations` (3), `hierarchical_structure` (1,895 pairs with JSON ground truth).

**Evaluation run** (deterministic seed 42): 14 curated PDFs + a 40-document random sample of the
hierarchical pairs (54 documents total). Results (factual; digital PDFs via text layer, scanned
docs via Tesseract):

| Metric | Result |
|---|---|
| Documents run | 54 (14 curated + 40 hierarchical) |
| Extraction failures (no text / error) | **0** |
| Method mix | `pdf_text` 48 · `tesseract_ocr` 6 |
| Field: supplier | 39/40 = **97.5%** |
| Field: invoice_number | 39/40 = **97.5%** |
| Field: invoice_date | 13/40 = 32.5% (dates often rendered in the layout in a non-ISO form) |
| Field: currency (ISO code in text) | 0/40 = 0% (the code "GBP" is not printed; £/€/$ symbols are) |
| Field: quantity+unit (any line item) | 19/40 = 47.5% (per-line values sit inside tables) |
| Field: document_type (semantic label) | 0/40 = 0% (the type is not a printed token) |

**Interpretation (honest):** the high supplier/invoice-number fidelity is on **digital** PDFs'
text layer, not OCR. Currency and document_type "misses" reflect that the ground-truth values are
not printed verbatim (not extraction failures). invoice_date and per-line quantity/unit are the
fields that most often require **human review/correction** — consistent with the human-reviewed
product contract. No claim of 100% OCR accuracy is made. The full 1,895-pair corpus remains
available for a larger run later.

## Gap 3 — Production Tesseract provisioning: INVESTIGATED — blocked on authorized deployment access (handoff provided)

Investigation result (conclusive, not "no file in repo"):

- **Deployment mechanism verified:** the backend runs on **Render's Native Python runtime**
  (dashboard-configured; start `uvicorn main:app --host 0.0.0.0 --port $PORT` from `backend/`;
  `pip install -r backend/requirements.txt`; Python 3.11 via root `runtime.txt`). Confirmed from
  `docs/audit/cline/CarbonTally_V3_Render_Runtime_Readiness_Audit_v1.0.md` (native-runtime
  traceback paths `/opt/render/project/src/backend/...`) and git history (the Render-prep commits
  added `requirements.txt` and `runtime.txt`).
- **No authorized access exists in this environment:** no Render CLI, no `RENDER_API_KEY` (or any
  Render env key) set, no `render.yaml` in the repo or on disk, no `.github/workflows`, and the
  production endpoint returns HTTP 000 from here (service asleep/unreachable) — so a production
  change cannot be made or verified from this environment.
- **Render's own documentation:** native runtimes are Debian 12 "bookworm" and do **not** bundle
  `tesseract`/`poppler-utils`; Render's documented path for non-bundled system tools is **Docker**.
  A custom Build Command with `apt-get` on the native runtime is possible to attempt but is not
  Render's supported path and is unverifiable from here; converting to Docker is a deployment
  redesign requiring a Product Owner decision.
- **Deliverable:** precise deployment handoff in
  `docs/audit/cline/CARBONTALLY_V3_RENDER_OCR_PRODUCTION_PROVISIONING_HANDOFF.md` — exact dashboard
  settings (Option A: Build Command with the five apt packages) or reference Dockerfile (Option B),
  unchanged env vars, exact verification commands, and the exact access required.
- **Conclusion:** *"Application code is complete; production provisioning requires authorized
  access to the deployment configuration."*



## 6. OCR accuracy observations

- Clean synthetic scans OCR at ~100% field fidelity for the target fields.
- Real-world imperfections remain (e.g. a low-res "Electricity" rendered as "lectriity" in one
  probe) — consistent with the decision-register position that extraction is **human-reviewed**
  before it moves downstream; OCR output is surfaced as a pre-fill/reference, not auto-accepted.
- OCR text is capped at 200,000 chars in the JSONB copy (raw object is authoritative).

## 7. V3 wiring result

Implemented and verified live:

- `POST /api/v3/uploads` now runs deterministic text/OCR **inline** (best-effort; never fails the
  upload) and persists the result on `organization_files.metadata.ocr` (JSONB — **no schema
  change**).
- New `POST /api/v3/uploads/{file_id}/ocr` re-run endpoint (org-scoped; reads the private object
  server-side; returns only the extraction summary — never the document).
- Both item-workspace surfaces (`/api/v3/ops/items/{id}/workspace`,
  `/api/v3/processing/items/{id}/workspace`) expose `source.ocr_text` for the human reviewer.

Live evidence: upload of the digital PDF returned `metadata.ocr = {status: ok, method: pdf_text,
text: 415 chars}`; explicit `/ocr` confirmed `12500 kWh` present; image upload → `/ocr` → `ok /
tesseract_ocr`.
