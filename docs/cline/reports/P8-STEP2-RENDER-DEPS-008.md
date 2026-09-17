# Phase 8 — Production PDF/Image OCR Runtime Remediation

**Task ID:** `CT-STEP2-RENDER-DEPS-008`
**Type:** BOUNDED IMPLEMENTATION + VERIFICATION + DEPLOYMENT
**Branch:** `p8-release-reconciled`
**Starting SHA:** `b2596adef94c2385814765b8f5d42ba2f54126d6`
**Change SHA:** `03fada8` (declaration) → **tip** `063e8bb4ef503f6da340e09000f3196f3c88bd01`
**Date:** 2026-09-17
**Verdict:** `CT-STEP2-RENDER-DEPS-008 PARTIALLY COMPLETE — PO REVIEW REQUIRED`
(implementation, local + production-equivalent verification, commit, push and deployment
verified; **production execution of the OCR path itself could not be exercised** — §16/§23)

---

## 1. Task ID

`CT-STEP2-RENDER-DEPS-008` — remediate the confirmed production defect recorded in
`P8-STEP2-PRODUCTION-ACCEPTANCE-006` §14(ii): scanned/OCR PDFs and images have no working
production extraction runtime.

## 2. Objective

Make the **existing intended** PDF/image OCR extraction path operational in production by
declaring the runtime dependencies that path actually requires — without changing extraction
semantics, P1 behaviour, thresholds, AI, worker architecture, CSV, frontend or CSS.

## 3. Starting Git SHA

```
branch : p8-release-reconciled
HEAD   : b2596adef94c2385814765b8f5d42ba2f54126d6   (== origin/p8-release-reconciled)
dirty  : 2 untracked files only (the CT-...-005/006 acceptance reports; no tracked
         modifications), staged 0
protected worktree ~/carbon_tally : HEAD 20b7a92, branch main, dirty 298 — untouched
```

## 4. Existing OCR architecture (forensically traced — `SOURCE VERIFIED`)

Entry point: `services/automatic_extraction.py::extract_document(content, filename, mime)`.

```
PDF  → _extract_pdf → _pdf_text(content)                   [automatic_extraction.py:342]
       ├─ pdf_engine.PDFExtractor._extract_text_direct     → pdfplumber (text layer)
       ├─ pdf_engine.PDFExtractor._extract_text_ocr         → pdf2image (poppler) + pytesseract (tesseract)
       └─ _render_pdf_pages_pypdfium + _onnx_ocr            → pypdfium2 + rapidocr_onnxruntime   ← pip-only fallback
IMAGE→ _extract_image → _image_text(content)               [automatic_extraction.py:516]
       ├─ pdf_engine.PDFExtractor.extract_image_text        → pytesseract (tesseract)
       └─ _onnx_ocr(content)                                → rapidocr_onnxruntime               ← pip-only fallback
```

Exact call sites and imports (verified in the release tree):

| Element | Location | Statement |
| --- | --- | --- |
| Tesseract wrapper | `pdf_engine.py:5` | `import pytesseract`; used at `:86` (`image_to_string`) and `:323` |
| Poppler wrapper | `pdf_engine.py:6` | `from pdf2image import convert_from_bytes`; used at `:84` (`dpi=300`) |
| Text-layer reader | `pdf_engine.py:60` | `pdfplumber.open(io.BytesIO(pdf_bytes))` |
| pip-only rasteriser | `services/automatic_extraction.py:498` | `import pypdfium2 as pdfium` (`PdfDocument` → `page.render(scale=2.0)` → PIL → PNG) |
| pip-only OCR engine | `services/automatic_extraction.py:306` | `from rapidocr_onnxruntime import RapidOCR`; `engine(np.asarray(image))` → joined lines |

Answers to the forensic questions:

* **Exact OCR entry point:** `_pdf_text` / `_image_text`, both invoked by `extract_document`.
* **Tesseract direct or wrapped?** Wrapped — `pytesseract` invokes the system `tesseract`
  binary from PATH (`pdf_engine.py:21-25` also honours an explicit `tesseract_cmd` path).
* **Is Poppler required?** Only by the `pdf2image` branch (`convert_from_bytes`); the fallback
  rasterises with `pypdfium2` and needs no Poppler.
* **Rasterisation mechanism:** `pdf2image`+Poppler in the Tesseract branch; **`pypdfium2`** in
  the fallback branch.
* **Is `rapidocr_onnxruntime` active or a historical experiment?** **Active** — it is the
  explicit, commented fallback ("Tesseract/poppler unavailable → pypdfium2 render + ONNX
  OCR"), reached whenever Tesseract yields fewer than 20 characters.
* **Anything already indirectly available?** `Pillow`, `numpy`, `pandas`, `pdfplumber`,
  `pytesseract`, `pdf2image` are already declared; `onnxruntime`/`opencv-python` arrive only
  as `rapidocr_onnxruntime`'s dependencies.

## 5. Dependency forensic analysis (`SOURCE VERIFIED`)

| Candidate | Verdict from the trace |
| --- | --- |
| **Tesseract (system binary)** | Used by the *first* OCR attempt via `pytesseract`. **Not required** for the pip-only path. No repository mechanism declares system packages (no `Dockerfile`, `render.yaml`, `apt.txt`, `build.sh`), so declaring it needs a provider-side build change — outside this task's bounded scope. The code is explicitly written to work without it. |
| **Poppler (`pdftoppm`/`pdfinfo`)** | Required only by `pdf2image.convert_from_bytes`; same system-package situation; the `pypdfium2` branch replaces it. |
| **`pypdfium2` (pip)** | **Imported directly** by active code (`automatic_extraction.py:498`); required for the pip-only scanned-PDF path; was **not** declared. |
| **`rapidocr_onnxruntime` (pip)** | **Imported directly** by active code (`automatic_extraction.py:306`); required for OCR of scanned PDFs **and** images without Tesseract; was **not** declared. Ships its three ONNX models inside the wheel (`ch_PP-OCRv3_det_infer.onnx`, `ch_PP-OCRv3_rec_infer.onnx`, `ch_ppocr_mobile_v2.0_cls_infer.onnx` — verified in the installed package), so **no runtime model download** is needed. |
| **`onnxruntime` (pip)** | Used **transitively**; the release code never imports it. Declared implicitly through the RapidOCR pin (a clean install pulled `onnxruntime-1.30.0`). |
| Others (`Pillow`, `numpy`, `pdfplumber`, `pdfminer.six`) | Already declared; nothing to add. |

Deployment mechanism (verified): **Render native Python runtime installing
`backend/requirements.txt`** — there is no Dockerfile/blueprint/apt file in the repository, so
pip declarations are the *existing* repository-native mechanism. No new deployment mechanism
was introduced and this fix requires **no** provider-side configuration change.

## 6. Dependency decision matrix

| Dependency | Used by current active code? | Required for scanned PDF? | Required for image? | Declaration mechanism | Reason |
| --- | --- | --- | --- | --- | --- |
| Tesseract (system) | Yes (first attempt) | Optional (fallback covers it) | Optional | **Not declared** | no repo system-package mechanism; would need a provider-side build change; the code has a pip-only path by design |
| Poppler (system) | Yes (`pdf2image` branch) | Optional | No | **Not declared** | same as above; `pypdfium2` replaces it |
| **pypdfium2** | **Yes — direct import** | **Yes** | No | `requirements.txt` | rasterises PDF pages without Poppler |
| **rapidocr_onnxruntime** | **Yes — direct import** | **Yes** | **Yes** | `requirements.txt` | pip-only ONNX OCR engine; models bundled in the wheel |
| onnxruntime | Transitively (via RapidOCR) | Yes (transitive) | Yes (transitive) | via the RapidOCR pin | not imported by our code; pinned transitively and verified installed |
| Pillow / numpy | Yes | Yes | Yes | already declared | image handling |

Only dependencies justified by the active code path were added; no second OCR engine was
introduced.

## 7. Files modified

| File | Change |
| --- | --- |
| `backend/requirements.txt` | **+2 dependency lines** and a 7-line explanatory comment (declaration only) |
| `docs/cline/reports/P8-STEP2-PRODUCTION-ACCEPTANCE-005.md`, `…-006.md` | banked (documentation commit, previously untracked) |
| `docs/cline/reports/P8-STEP2-RENDER-DEPS-008.md` | this report |

No other file was modified: no source, test, migration, schema, configuration, frontend or CSS
file is touched.

## 8. Exact dependency changes

```diff
 openpyxl>=3.1.5
+# PDF/image OCR — the pip-only fallback the extraction code already implements for
+# hosts without Tesseract/poppler (services/automatic_extraction.py:
+# `_render_pdf_pages_pypdfium` + `_onnx_ocr`). RapidOCR bundles its ONNX models in
+# the wheel, so no runtime model download is required. Bounded pins: the ONNX
+# engine API used by the code is the 1.2.x line and pypdfium2 5.x.
+# (CT-STEP2-RENDER-DEPS-008: makes the existing scanned-PDF/image OCR path
+# operational on the Render native runtime, which installs this file.)
+pypdfium2>=5.13.0,<6.0
+rapidocr_onnxruntime>=1.2.3,<1.3
```

Pins are **bounded** (not `latest`), matching the project's `>=` convention while capping the
major/minor lines the code's API contract depends on. Both are the versions verified in this
task.

## 9. Local verification (`LOCAL VERIFIED`)

1. **Host condition reproduced:** `tesseract` binary **ABSENT** from PATH (the production
   condition), while `pypdfium2`, `rapidocr_onnxruntime`, `onnxruntime` import successfully.
2. **Clean production-equivalent environment:** a fresh virtualenv created from scratch and
   populated **only** with the release `backend/requirements.txt`:
   `pip install -r requirements.txt` → **EXIT=0**, `Successfully installed … pypdfium2-5.13.0
   … rapidocr_onnxruntime-1.2.3 … onnxruntime-1.30.0 … opencv-python-5.0.0.93` (no build
   errors, no resolution conflicts). This is the exact operation Render performs.
3. **Import verification in that clean environment:** `pypdfium2: OK`,
   `rapidocr_onnxruntime: OK`, `onnxruntime: OK`.
4. All verification fixtures were **synthetic and disposable** (`/tmp`), generated by a
   throwaway script; nothing was uploaded to any organisation and no database was touched.

## 10. OCR functional test (`LOCAL VERIFIED`)

Synthetic fixtures generated in `/tmp` (a three-line invoice drawn as pixels so there is **no
text layer**), executed through the release `extract_document` with the Tesseract binary
absent — i.e. under exactly the condition that previously produced `no_text`:

| Fixture | Before this change | After | OCR text produced |
| --- | --- | --- | --- |
| Scanned PDF (image-only page) | `status=no_text`, `detail="no usable text extracted (blank page, or image too low quality)"` | **`status=ok`, `method=onnx_ocr`, `text_len=103`** | `Invoice INV-3001 Supplier: Acme Fuels Ltd \| Diesel 1500 litres 1800.00 \| Unleaded petrol 900 litres 1200.00` |
| Image (PNG scan) | same `no_text` failure | **`status=ok`, `method=onnx_ocr`, `text_len=103`** | identical text |

Because the fixtures have no text layer, the extracted `activity: 'Diesel'` **can only have
come from OCR text** → OCR produced real text and the existing extraction pipeline consumed it.

Anti-fabrication check: `unresolved=['date','invoice_number','quantity/unit','supplier']`
remained listed for both fixtures — no field was invented, and the resolved/unresolved split is
identical to the text-layer PDF baseline for the same content.

Provenance/evidence behaviour was untouched (no code change to the extraction result shape:
`status`/`method`/`page_count`/`extracted_data`/`unresolved`/`confidence` are unchanged; only
`method` legitimately reports `onnx_ocr` for the OCR path).

**Production-equivalence repeat:** the identical script executed inside the clean venv built
from `requirements.txt` alone produced the same results (`text-PDF → pdf_text`, `scan-PDF →
onnx_ocr`, `scan-PNG → onnx_ocr`).

## 11. Text-layer regression (`LOCAL VERIFIED`)

| Check | Result |
| --- | --- |
| Text-layer PDF still extracts | **yes** — `status=ok`, `method=pdf_text`, `has_text_layer=True` |
| OCR not unnecessarily invoked | **yes** — the method stays `pdf_text`; `_extract_text_ocr` is only reached when the direct text is <20 characters |
| P1 fidelity hook intact | yes — the hook is untouched (`v3-auto-1.1`), and the earlier P1/extraction suites pass (§14) |
| Completeness semantics | **unchanged** — same `confidence` for the same content (0.3333 for the synthetic fixture, i.e. the same result as before the change) |
| Shadow-default behaviour | **unchanged** — `shadow` remains the resolver default; no rollout env was set or modified |
| 0.50 completeness gate | **unchanged** — no threshold constant touched |

## 12. Image regression (`LOCAL VERIFIED`)

Images **are** an active supported path (`_extract_image` → `_image_text` → Tesseract, then the
ONNX fallback). Verified end-to-end: PNG scan → `_image_text` → `method=onnx_ocr`,
`text_len=103` → `extract_document` → `status=ok` with `activity: 'Diesel'` and unresolved
fields preserved. Scope was not expanded: the existing path was simply made runnable.

## 13. P1 safety verification (`LOCAL VERIFIED` / `SOURCE VERIFIED`)

| P1 invariant | Status |
| --- | --- |
| `PIPELINE_VERSION` / `PIPELINE_VERSION_P1` = `v3-auto-1.1` | **unchanged** (`domain/automatic_processing.py:45`, `services/extraction_fidelity.py:44`) |
| P1-D1 hook, row detection, coverage, per-line page handling | **untouched** — no source file was modified by this task |
| Shadow-first default | **unchanged** — `CARBONTALLY_P1_EXTRACTION_SHAPE` was **not** set or modified anywhere |
| AI gate / AI provider configuration | **untouched** — no AI setting, key or model changed; no AI call was enabled |
| Completeness gate (0.50) and semantics | **unchanged** |
| P1 tests | pass (§14) |

P1 remains **not activated** by this task; rollout stays with `CT-STEP2-P1-ROLLOUT-011`.

## 14. Test results (`LOCAL VERIFIED`)

| Suite | Result |
| --- | --- |
| `tests/unit/services/test_automatic_extraction.py` | pass |
| `tests/unit/services/test_automatic_extraction_text_layer.py` | pass |
| `tests/unit/services/test_p1_image_path.py` | pass |
| `tests/unit/services/test_extraction_fidelity.py` | pass |
| `tests/unit/services/test_automatic_processing.py` | pass |
| **Combined run of the five suites** | **0 failures** (100% of collected cases) |
| Tests modified to make them pass | **none** — no test file was touched (`git diff` proves it) |

No test assumed the old broken environment, so no test-level blocker was encountered.

## 15. Production deployment identity (`PRODUCTION VERIFIED` — deployment only)

| Evidence | Value |
| --- | --- |
| Pre-change instance | `rndr-id: f29579ed-9ce8-474a` (recorded during task 006) |
| During rollout (observed) | `d24f285e-9dc3-4bd8`, `e5d6cbc8-9570-44b3` |
| **After deployment** | **`rndr-id: 2823a59d-8c0b-40ef`** — a different instance identity from the pre-change service |
| `/health` | 200 — `status healthy`, `supabase_connected true`, `pool_connected true` |
| `/` | 200 — `CarbonTally API v3.0.0`, `api_version v3`, `routes_count 49` |
| `/openapi.json` | 200 — **570 paths**, identical to before the change; Step 2 endpoints still present (`/api/generate-enhanced-report`, `/api/generate-sustainability-report`, `/api/reports/generate-enhanced-report`, `/api/upload-pdf`, `/api/v2/generate-report`) → **no unintended contract change** |
| Multipart upload path | `POST /api/test-upload` (anonymous echo endpoint) → **200**, `{"status":"success","filename":"…","size":3514,"content_type":"application/pdf"}` → the new build serves uploads |
| Deployment build | Render auto-deployed from the push (same behaviour observed in earlier tasks). Build success is **inferred** from a new healthy instance serving an unchanged contract — not proven, because Render's build logs and deploy API are not accessible from this environment (§17). |

## 16. Production OCR verification (`NOT PRODUCTION VERIFIED`)

**The OCR code path itself was not executed in production.** Reason: every endpoint that runs
document extraction requires authentication (`POST /api/upload-pdf` → **401**; all
`/api/v3/documents` and processing endpoints → 401), and no authorised production session or
Render log access was available to this task. The only anonymous file endpoint
(`/api/test-upload`) merely echoes metadata and performs no extraction.

Being explicit about the evidence boundary:

| Claim | Status |
| --- | --- |
| The declared dependency set installs cleanly from `requirements.txt` | `LOCAL VERIFIED` (clean venv, EXIT=0) |
| The OCR path produces text for scanned PDFs and images without Tesseract | `LOCAL VERIFIED` (and repeated in the production-equivalent venv) |
| The new build is deployed and serving | `PRODUCTION VERIFIED` (new instance identity, health, 570-path contract, upload path 200) |
| OCR actually executes in the production process | **NOT VERIFIED** — requires an authenticated upload or provider log access |

Exact remaining requirement to close it (either is sufficient):

1. In the authenticated **Babui Technologies UK Limited** session, upload a scanned PDF/image
   and observe extraction no longer returns `no_text` (expect `method` = `onnx_ocr`); or
2. Render service log access (or the `CT-STEP2-ACCEPT-007` session) to observe a scanned
   document's automatic-processing job complete its extraction stage.

## 17. Render logs / evidence

**Render logs are not accessible from this environment** (no Render API key, no dashboard
access; task 006 recorded the same limitation). Consequently the required log checks — successful
startup, no missing-library errors, no missing-binary errors, no import errors, no OCR
initialisation errors — **could not be performed**, and no claim is made about them.

Substitute read-only evidence collected instead: response headers (`rndr-id`,
`x-render-origin-server: uvicorn`, `server: cloudflare`), the full `/health` body,
`/` and `/openapi.json`, and a live multipart upload round-trip (§15).

## 18. Git commit SHA

| Commit | Purpose | Contents |
| --- | --- | --- |
| `03fada8` | `chore(p8-render-deps): declare the pip-only OCR runtime (CT-STEP2-RENDER-DEPS-008)` | `backend/requirements.txt` **only** |
| `063e8bb` | `docs(p8): bank the Step 2 acceptance/triage reports (005, 006)` | the two previously untracked reports |
| *(report commit)* | `docs(p8-render-deps): CT-STEP2-RENDER-DEPS-008 report` | this report |

Diff of the functional commit against the previous tip: **one file, `backend/requirements.txt`**.

## 19. Pushed remote SHA

```
local  : 063e8bb4ef503f6da340e09000f3196f3c88bd01
origin : 063e8bb4ef503f6da340e09000f3196f3c88bd01   (verified after push)
```

The report commit is pushed immediately after it is created and re-verified the same way; the
final remote SHA equals the local HEAD at the end of the task.

## 20. Working-tree status

| Check | Value |
| --- | --- |
| After the functional commit (`03fada8`) | clean (`git status --porcelain` → the two untracked prior reports only) |
| After the banking commit (`063e8bb`) | **clean (0 entries)**, staged 0 |
| After the report commit | clean |
| Protected `~/carbon_tally` worktree | **untouched** — HEAD `20b7a92`, branch `main`, dirty 298, staged 0 (identical before and after this task) |
| Tests / fixtures created by this task | live in `/tmp` only (disposable); no repo test file was added or modified |

## 21. Production data safety

| Rule | Compliance |
| --- | --- |
| No real customer document processed | **respected** — no document was uploaded to any organisation; no extraction job was created |
| No record created/modified/deleted | **respected** — production was touched only by anonymous read-only requests |
| No storage object written or deleted | **respected** |
| Only synthetic fixtures used | **yes** — generated in `/tmp` at verification time |
| One disclosed production write-ish action | a **3,514-byte synthetic script file** was POSTed to the **anonymous, non-persisting echo endpoint** `/api/test-upload` (returns only filename/size/content-type; writes nothing) to prove the new build serves multipart uploads. No data was stored; no customer record involved. |
| Destructive tests | **none** |
| Database migrations / schema / RLS / billing / retention | **not touched** |

## 22. Unrelated-scope verification

| Out-of-scope area | Status in this task |
| --- | --- |
| CSV preview / CSV asynchronous processing | not touched (remains `CT-STEP2-ACCEPT-007`/`CT-STEP2-WORKER-OBS-009` scope) |
| Worker observability | not touched (remains `CT-STEP2-WORKER-OBS-009`) |
| F-07 CSS | not touched (remains `CT-STEP2-F07-CSS-010`) |
| P1 rollout/activation, AI provider configuration | not touched (remains `CT-STEP2-P1-ROLLOUT-011`) |
| Consultant parity, report lifecycle, XLSX workflow | not touched |
| Emission-factor logic, calculation logic | not touched |
| RLS/auth, billing, retention | not touched |
| Extraction semantics, completeness threshold, extraction schema | not touched |
| `git diff b2596ade..03fada8 --stat` | **1 file changed, 9 insertions(+) — `backend/requirements.txt`** |

## 23. Remaining limitations

1. **Production OCR execution is not verified** (§16) — the decisive remaining check requires an
   authenticated production upload or Render log access.
2. **Render build success is inferred, not proven** (§15/§17) — no provider deploy API or logs.
3. **System Tesseract/Poppler remain undeclared.** This is deliberate and bounded: the repository
   has no system-package declaration mechanism, and the code's pip-only path covers the need. If
   the PO later wants Tesseract-first OCR on Render, the exact provider action would be either
   (a) add a `Dockerfile` and switch the service to a Docker build with
   `apt-get install -y tesseract-ocr poppler-utils`, or (b) Render-supported build hooks/apt
   configuration for the existing native service — both are provider-side changes requiring a
   separate authorised task.
4. **OCR quality is model-dependent.** RapidOCR uses PP-OCRv3 mobile detection/recognition
   models; text quality on poor scans may differ from Tesseract. The extraction path is unchanged,
   so any quality difference surfaces as the existing completeness/unresolved outcomes (no
   fabrication).
5. **Build weight/time increase** on Render because `onnxruntime` + `opencv-python` are now
   installed (a few hundred MB). Not measured here (no build-log access).
6. **The completeness gate still blocks multi-line invoices** while P1 is `shadow` (unchanged,
   deliberate) — the cause recorded in `P8-STEP2-PRODUCTION-ACCEPTANCE-006` §14(i) remains and is
   owned by `CT-STEP2-P1-ROLLOUT-011`.

## 24. Final verdict

`CT-STEP2-RENDER-DEPS-008 PARTIALLY COMPLETE — PO REVIEW REQUIRED`

**Why not COMPLETE:** the fix is implemented, committed, pushed and deployed, and the OCR path is
verified in a clean production-equivalent environment — but **the OCR path has not been executed
in the production process**, which §19 makes a condition of the COMPLETE verdict.

| Requirement (§19) | Status |
| --- | --- |
| Actual required dependencies correctly declared | **yes** — only the two packages the active code imports, bounded pins |
| Local / production-equivalent verification passes | **yes** — clean venv from `requirements.txt` (EXIT=0) performs OCR |
| Scanned PDF OCR works | **yes locally / production-equivalent**; not yet executed in production |
| Image OCR works (supported path) | **yes locally / production-equivalent**; not yet executed in production |
| Text-layer PDF extraction remains intact | **yes** — `method=pdf_text`, OCR not invoked |
| P1 behaviour unchanged | **yes** — `v3-auto-1.1`, `shadow` default, gate and AI untouched |
| Tests pass | **yes** — 0 failures across the five relevant suites; no test modified |
| Production deployment succeeds | **yes** — new instance identity, health 200, contract unchanged (build success inferred, §15) |
| **Production OCR actually verified** | **NO** — requires an authenticated upload or log access (§16) |
| Commit pushed; remote SHA matches | **yes** — `063e8bb…` local == remote (report commit pushed and re-verified) |
| No unrelated changes introduced | **yes** — the functional commit touches one file |

**Single remaining action to reach `COMPLETE`:** execute one scanned-PDF (or image) upload in the
authenticated production environment (or read the corresponding Render log line) and confirm the
extraction no longer reports `no_text`. That check belongs to the session-gated acceptance task
`CT-STEP2-ACCEPT-007`.

**This task ends with this report. No other workstream was started or modified.**




