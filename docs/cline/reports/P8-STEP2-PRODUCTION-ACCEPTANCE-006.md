# Phase 8 — Step 2 Production Acceptance + Authenticated Functional Triage

**Task ID:** `CT-STEP2-PRODUCTION-ACCEPTANCE-006`
**Task type:** FINAL AUTHENTICATED PRODUCTION ACCEPTANCE + READ-ONLY DEFECT TRIAGE
**Branch:** `p8-release-reconciled` — HEAD == origin == `b2596adef94c2385814765b8f5d42ba2f54126d6`
**Date:** 2026-09-17
**Verdict:** `STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`
(no fix applied, nothing committed/pushed; see §26/§30)

---

## 1. Task identity

Attempt the authenticated production acceptance that was blocked in
`CT-STEP2-PRODUCTION-ACCEPTANCE-005`, and perform a **read-only** triage of the Product
Owner's three observations (CSV preview, CSV extraction, PDF extraction). Acceptance/triage
only — no implementation, no Git writes, no production modification.

## 2. Objective

Determine, with evidence, **whether** each reported symptom is reproducible, **where**
exactly it fails, and **whether** the Step 2 implementation is actually deployed and
contradicts the verified source/test evidence.

## 3. Authorization boundary

Honoured: no source, test, migration, database, storage, RLS, Render, Vercel or environment
change; no user or organisation created; no test data uploaded anywhere; nothing deleted; no
destructive test; no commit; no push; no deploy; no Git reset/clean/stash; the protected
dirty `~/carbon_tally` worktree was **not** touched (read-only `git status`/`rev-parse`
only). All production interaction was anonymous, read-only HTTP, plus local in-process code
execution against fixtures.

## 4. Git baseline

```
HEAD   : b2596adef94c2385814765b8f5d42ba2f54126d6
origin : b2596adef94c2385814765b8f5d42ba2f54126d6   (identical)
branch : p8-release-reconciled    staged: 0
worktree delta: 1 untracked file = the CT-...-005 acceptance report (deliberately
                uncommitted per that task's §15) — no tracked modifications
ancestry (all IN-ANCESTRY): 2009d2f 0d21e46 f5e07ed eb6a0c2 5d143ac c8b8d81 55be3d2
                            7666fff 3849f30 a496a37 b45721a 9332569 948917f e5746ed
                            2f6e1d5 6beb281 503d186 b2596ade
protected dirty tree ~/carbon_tally : HEAD 20b7a92 (branch main), dirty 298 — untouched
```

No Git repair was required or performed.

## 5. Deployment identity

**Frontend (production, `carbontally.co.uk`)**

| Evidence | Value |
| --- | --- |
| Live index asset references | `/static/js/main.9febc8f0.js`, `/static/css/main.a66f5596.css` |
| Index `last-modified` | **Thu, 17 Sep 2026 13:22:47 GMT** (promotion time of the served build) |
| Index cache policy | `cache-control: public, max-age=0, must-revalidate`, `etag: "aa3dd28d75d7903c2a858e070cc70a8d"`, `x-vercel-cache: HIT`, `age: 1235` |
| Security headers | HSTS `max-age=63072000`; **no `content-security-policy` header at all**; `access-control-allow-origin: *` |
| Bundle sizes | JS 2,286,957 bytes; CSS 298,520 bytes |
| POD-3 markers in the **deployed** bundle | `structured-preview` (JS), `ct-wb-viewer__data` (**JS and CSS**), `preview unavailable` |
| WS-H markers | `manual_review_reason`, ` - awaiting manual review.`, `Job re-enqueued.`, `Failed to retry job`, `Job confirmed - the pipeline will resume it.` |
| S6 markers | `Changes requested`, `Approved. It can now be finalised.`, `Changes were requested. A revised version is needed.`, `Final and locked. Finalised reports are immutable.`, `No action is available to you on this version.`, `calculated_emissions_kg_co2e` |
| Old bundle | `main.1e761f98.js` is **not referenced** by the live index (its path still resolves 200 = Vercel immutable-asset retention, expected) |

**Backend (production, `carbontally-api.onrender.com`)**

| Evidence | Value |
| --- | --- |
| `/health` | 200 — `status healthy`, `supabase_connected true`, `pool_connected true`, components database/pool connected, `api running (routes 49)` |
| `/` | 200 — `CarbonTally API v3.0.0`, `api_version v3`, `routes_count 49` |
| `/api/v2/health` | **200** — `{"status":"ok","service":"carbontally-api-v2","version":"1.0"}` |
| `/openapi.json` | 200, **570 paths** — includes `/api/generate-enhanced-report`, `/api/generate-sustainability-report` (POD-5), `/api/upload-pdf` (POD-2), `/api/v3/documents`, `/api/v3/reports` |
| Render identity | `rndr-id: f29579ed-9ce8-474a` — **different from task 005's `b87594b2-16a1-4bea`**: the service was redeployed between 005 and 006 with an **unchanged route contract** (same 570 paths, same Step 2 endpoints); `x-render-origin-server: uvicorn`, `server: cloudflare` |

The platform does **not** expose the deployed git SHA, so SHA identity is **not** claimed;
the deployed backend is identified by route-surface equivalence to the release
(`routes/legacy_reports.py` and `/api/upload-pdf` can only exist in the Step 2 build).

## 6. Authenticated account / organisation context

**Not available in a usable form — authenticated acceptance is blocked at the access layer
(§29).** The task states an authorised user is logged into **Babui Technologies UK
Limited**, but no session token, credential or authenticated browser profile was supplied to
this agent, and §1/§4 explicitly forbid credential discovery. Checks performed (names/paths
only; **no secret value was printed or stored**):

| Suspected mechanism | Finding |
| --- | --- |
| Session/token file supplied for this task | none (`/tmp` token-like files: only `/tmp/f29_tokens.txt`) |
| `/tmp/f29_tokens.txt` (13,050 bytes, 14:41 today) | **not an authentication session** — it is **another workstream's CSS-01 / F-07 audit dump** (grep output referencing `CSS-01`, `v3.css:301-304`, `reports.css:263-276`, `main.2356c9d3.css`); **0 JWT-shaped strings** |
| `~/carbon_tally/.env.production` (present, 640 bytes) | a production **configuration** file, not a user session. Reading it for credentials is prohibited by §1/§4, and a service-role key would bypass the very authorization boundary under test. **Not used.** |
| `QA_*`/`TEST_*`/`DEMO_*`/`PROD_*` environment variables | none |
| Documented production/QA acceptance account | none found; the only credential store (`tools/seed_investor_demo/DEMO_IDENTITIES.md`, `.local-demo-credentials.md`) is explicitly **LOCAL-ONLY** |

Consequence: every item requiring an authenticated production session is recorded as
`UNVERIFIABLE` (class **G**); per §24 the blocker is documented and all independent
non-credential checks were completed instead.

## 7. Browser / environment

| Capability | Status |
| --- | --- |
| Chrome headless (real browser) | **available** — `google-chrome` 152.0.7977.64 |
| Firefox | available |
| Selenium (backend venv) | available — 4.47.0 (chromedriver not installed; Selenium Manager would fetch it) |
| QA harness browser driver | available — `qa_harness/.venv` with **playwright present** |
| Authenticated production browser profile | **not provided** — this is the single blocker |
| Anonymous real-browser smoke of production (executed in task 005) | `/` (33,009-byte DOM, `#root`, 0 JS error lines) and `/login` (5,451-byte DOM, 0 JS error lines) |

---

## 8. CSV upload result

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** (no upload was performed or
possible).

Source-level facts (verified, read-only):

* `api/v3_documents.py::_classify` maps `csv`, `xlsx`, `xls` → **`SPREADSHEET`**
  (lines 155–163); the upload endpoint performs **no MIME allow-list check**, so the earlier
  Supabase MIME restriction (already disabled by the PO) is not duplicated in code.
* `_RENDERABLE_MIME_BY_EXT` covers only PDF/images, so a CSV keeps its client-supplied
  content type (`text/csv`) or falls back to `application/octet-stream` — irrelevant to the
  server-side parser, which reads raw bytes.
* **Silent-failure point (important):** the durable job enqueue is best-effort and its
  failure is only printed — `api/v3_documents.py:353`
  `⚠️ automatic-processing enqueue failed: {exc}` and `:355`
  `⚠️ extraction enqueue failed: {exc}`. If this fires in production the upload **succeeds**,
  the item appears in the workspace, and **no extraction ever runs** — with no user-visible
  error. This is a plausible mechanism for both extraction symptoms.

## 9. CSV preview result

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** (the pane was not observed), but
the **component chain is verified in source and the component is deployed**:

```
customer/ProcessingItemWorkspace.jsx:24   import WorkbenchShell from '../components/workbench/WorkbenchShell'
customer/ProcessingItemWorkspace.jsx:891  <WorkbenchShell … sourceUrl={source.viewer_url} sourceTitle={source.file_name} …/>
components/workbench/WorkbenchShell.jsx:17/43  → <SecureDocumentViewer src={sourceUrl} title={sourceTitle} …/>
SecureDocumentViewer.detectKind: /\.(csv|xlsx?|tsv)$/ → 'data' → <StructuredDataPreview/>
```

Deployed-bundle markers confirm this code is live (`structured-preview`,
`ct-wb-viewer__data` in JS **and** CSS, `preview unavailable`).

**Ruled out by evidence:** a CSP blocking the preview fetch (the production app sends **no
CSP header at all**); the wrong bundle being *deployed* (markers present); a missing file-type
classification (CSV → `SPREADSHEET`).

**Remaining candidate causes, each with a discriminating on-screen string:**

| # | Candidate | What the pane shows | Next read-only check |
| --- | --- | --- | --- |
| 1 | `source.viewer_url` missing / signing failed | **"No source document available for this item."** | the workspace API response for the item (`source.viewer_url`) |
| 2 | cross-origin `fetch()` of the signed storage URL fails (bucket CORS / network / expiry) — PDF & image use an `<iframe>` and need no CORS | **"Structured preview is not available for this file (…)."** | browser console + the signed-URL response's `access-control-allow-origin` |
| 3 | the browser was still running the **pre-promotion** bundle (index `last-modified` = today **13:22:47**) | the **old** text: "Document preview is not available for this file type." | hard reload and re-observe |
| 4 | a different surface (document list, not the workbench item page) | no preview area at all | confirm the observed route/URL |

The symptom is **not** explainable by the deployed code path alone.

## 10. CSV parsing result

**Result: `PASS` (code-level, executed under the release code).** Local in-process execution
of the release `services.automatic_extraction.extract_document` (no DB, no writes, no
client):

| Fixture | Status | Completeness | Line items | Unresolved |
| --- | --- | --- | --- | --- |
| `mock_uk_fuel_card_messy.csv` | ok | **1.0** | **50** | `[]` |
| `mock_uk_utility_bill.csv` | ok | **1.0** | **20** | `[]` |
| `mock_scope3.csv` | ok | **1.0** | **4** | `[]` |

CSV parsing and canonical mapping are therefore **not** defective in the release code.

## 11. CSV extraction result — forensics

Classification against the A–H taxonomy:

| Hypothesis | Verdict |
| --- | --- |
| **A. Parser failure** | **Ruled out** — §10 (all fixtures parse; completeness 1.0) |
| **B. Extraction failure (no usable data)** | **Ruled out** for the shipped code path — §10 |
| **C. Persistence failure** | Cannot be excluded without DB access; the persistence path is the one the tests exercise (`_persist_partial_extraction` on block, job metadata on success) |
| **D. Processing failure (pipeline does not continue)** | **Prime candidate** — the job may never have been enqueued (swallowed `⚠️ … enqueue failed`) or the in-process worker may not be running (§14/§29); both are invisible to `/health` and to the customer |
| **E. Mapping/factor failure** | Cannot be excluded; it would appear as a *later* stage failure and is only reachable if D is clean |
| **F. Frontend-only failure** | Cannot be excluded — emitted extraction may not be surfaced in the UI |
| **G. Configuration/environment** | Cannot be excluded (no session/DB/log access) |
| **H. Other** | — |

**Exact stage where the workflow stops: not determinable from outside the environment.**
The decisive read-only evidence set is:

1. `document_processing_queue` row for the uploaded file (exists? `stage`, `status`,
   `attempt_count`, `block_reason`, `pipeline_version`);
2. `organization_files` metadata (`file_type`, `mime_type`, `ocr`);
3. `manual_extraction_items` row (item created? `file_type`, status);
4. Render logs for `⚠️ automatic-processing enqueue failed`,
   `⚠️ extraction enqueue failed`, `⚠️ automatic-processing worker failed to start`;
5. the browser network response for the preview `fetch` (§9 candidate 2).

## 12. XLSX result

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`.**

* Code-level: `.xlsx`/`.xls` → `SPREADSHEET` → XLSX reader; cover-sheet-aware bounded sheet
  scan (`_XLSX_SHEET_SCAN_LIMIT = 5`) and phantom-line suppression are test-pinned
  (`test_structured_file_parity.py`, 11 cases green).
* Dependency level: **`openpyxl>=3.1.5` is declared in `requirements.txt`** → XLSX parsing is
  dependency-safe in production (unlike the OCR fallback chain, §14).
* XLSX extraction is therefore *expected* to work in production; no claim is made without a
  session.

## 13. PDF upload result

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`.** No PDF was uploaded. The upload
path is the same pipeline as CSV (§8), so the same silent enqueue/worker failure modes apply.

## 14. PDF extraction result — forensics

**Result: `FAIL` (behaviour mismatch) — with two independent, evidenced causes.**
Text-layer PDF extraction and OCR/scan extraction are different failures.

**(i) Text-layer PDF → extracts partially, then blocks** (deliberate behaviour, but a
customer-visible "extraction not working"). Local execution of the release code on a
generated text-layer PDF (reportlab, a declared dependency):

```
PDF text-layer: status=ok  method=pdf_text  pages=1  completeness=0.3333
                extracted={'activity': 'Diesel'}
                unresolved=['date', 'invoice_number', 'quantity/unit', 'supplier']
```

`0.3333` is **below the 0.50 completeness gate**, so the job blocks for manual review (the
durable block reason carries the gate message, e.g. *"… deterministic completeness 0.33 below
0.50 threshold"*). This is **by design while the P1 fidelity hook is in `shadow` mode**
(POD-4 C — controlled rollout; default `shadow`, no allowlist configured): multi-line invoices
are **not** structured into per-line items in production, so structured invoices cannot clear
the gate. The customer experiences this as "PDF extraction is not working".
Classify as **E (intentional/deferred — PO decision)**, see §30.

**(ii) Scanned / image-only PDF (and images) → no workable OCR path in production.** Local
execution produced:

```
PDF no-text-layer: status=no_text  method=pdf_text
                   detail=no usable text extracted (blank page, or image too low quality)
OCR extraction failed: tesseract is not installed or it's not in your PATH
```

The fallback chain (`services/automatic_extraction.py::_pdf_text`) is: `_extract_text_direct`
(pdfplumber — works) → `_extract_text_ocr` (needs **tesseract + poppler system binaries**) →
`pypdfium2` render + **`rapidocr_onnxruntime`/`onnxruntime`** (pip). Verified against the
deploy manifest:

| Requirement | Declared? |
| --- | --- |
| `pytesseract`, `pdf2image` (python wrappers) | declared in `requirements.txt` |
| **tesseract-ocr**, **poppler-utils** (system binaries the wrappers require) | **declared nowhere** — no `Dockerfile`, `render.yaml`, `apt.txt` or `nixpacks.toml` exists in the release |
| **`pypdfium2`, `rapidocr_onnxruntime`, `onnxruntime`** (the pip-only fallback) | **NOT declared in `requirements.txt`** |

This environment has those modules installed ad hoc (all imports succeed here), which is
exactly why local ≠ production: Render installs from `requirements.txt`, so the pip-only
fallback is **likely absent in production**, leaving **no working OCR path** for scanned
PDFs/images. Classify as **C (configuration/environment parity)** — a render
build-declaration gap, not a logic defect.

**(iii) Cross-cutting invisibility.** If the job was never enqueued or the worker never
started, extraction silently does nothing (§8, §17, §29) — indistinguishable to the customer
from (i)/(ii).

## 15. P1-D1 runtime result

Source facts re-verified **in the current release** (not from historical reports):

| Check | Verified value |
| --- | --- |
| Pipeline version | `domain/automatic_processing.py:45` `PIPELINE_VERSION = "v3-auto-1.1"`; `services/extraction_fidelity.py:44` `PIPELINE_VERSION_P1 = "v3-auto-1.1"` |
| Logger repair, row candidates, coverage, multi-line, page split | implemented in `services/extraction_fidelity.py` (`classify`, `find_source_lines`, `split_pages`, `build_line_items`, `ai_fanout_plan`, `block_reason`) |
| P1 tests present | `test_extraction_fidelity.py` **24** test functions + `test_p1_image_path.py` **4** = **28** P1 cases, green in the release worktree |
| IMAGE path wired | yes — the shared hook applies to the IMAGE path (`c8b8d81`) |
| Adjudication | document-level, field-level; `positional_blending is False` asserted |
| **Runtime mode** | **`shadow`** — the resolver's fail-safe default, **no allowlist configured**; the hook *measures* coverage and does **not** rewrite the customer-visible extraction |

Classification: **SOURCE-ONLY (F)** for customer behaviour — **not** `FAIL`, because `shadow`
is the ratified PO decision (POD-4 C). Runtime consequence, stated plainly: **production
extraction still collapses multi-line documents to a flat record** and therefore frequently
scores below the gate (§14(i)).

## 16. AI extraction / fan-out result

| Question | Answer |
| --- | --- |
| Deterministic extraction runs? | yes — always first (proven by §10/§14 local runs) |
| Is AI configured in production? | **UNVERIFIABLE** — needs an authenticated run or Render env inspection; **nothing was enabled or changed** |
| Is the AI gate reached? | only when deterministic completeness is below the gate (path exists, test-covered) |
| Bounded fan-out limits (POD-1) | `AI_FANOUT_MAX_CALLS = 8`/document, `AI_FANOUT_MAX_RETRIES = 1` (infrastructure failures only), `AI_FANOUT_TIMEOUT_S = 60.0`, `AI_FANOUT_PAGE_CLIP_CHARS = 8_000`, plan-gated by `P1 PAGE_CAP = 20`, no recursion |
| Retries | one, only for timeout/exception; an engine-reported error is never re-requested |
| Persisted/auditable | yes — `ai_extraction.ai_fanout` (plan, calls made, per-page attempts, `first_failure`) and `ai_pages` |
| Adjudicated without positional blending | **verified in code and tests** |
| Production shadow-only? | **yes** — the P1 hook is `shadow`; no AI/provider configuration was touched |

## 17. Partial extraction persistence result

* `_persist_partial_extraction` exists and is exercised by the Step 2 tests
  (`test_step2_remediation.py`, green): the partial payload is persisted **before** the
  completeness gate, so a blocked job still carries `extracted_data`, the manual-extraction
  item, job metadata, completeness and `block_reason`.
* No fabrication: unresolved fields stay absent (`unresolved=[…]`; §14(i) shows `activity`
  present with four fields unresolved).
* Production runtime for a real blocked document: **SOURCE-ONLY (F)**.

## 18. Processing → emission-factor continuity result

* **Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`.**
* Dependency identified explicitly: because extraction for the observed documents does not
  reach the gate (§11, §14), the pipeline **cannot reach** mapping or factor lookup — the EF
  engine is therefore **not** implicated and is not reported as defective on this evidence.
* No factor was read, inserted, modified or deleted; no calculation was fabricated.
* The release worktree's mapping/calculation unit suites are green, and the deployed backend
  exposes the mapping/processing surfaces (570 OpenAPI paths; anonymous 401).

## 19. Blocked-job customer visibility result

**Result: `UNVERIFIABLE` (interactive) — deployed markers verified.** The deployed bundle
contains `manual_review_reason` and the blocked card text ` - awaiting manual review.`, plus
the retry/confirm continuity strings (§5). Given §14(i), the *most likely real production
state* for the PO's documents is **blocked → awaiting manual review**; whether the customer
sees that card, and with which reason, must be confirmed in the authenticated session. No
blocked production job was manufactured and no document was modified.

## 20. Report lifecycle (S6) result

**Result: `UNVERIFIABLE` (interactive) — deployed markers verified.** The deployed bundle
contains the lifecycle strings and `calculated_emissions_kg_co2e` (§5); `/api/v3/reports` and
`/api/v3/reports/types` refuse anonymous access (401). No report was created, approved,
finalised or deleted.

## 21. Consultant Client parity result

**Result: `UNVERIFIABLE — CONSULTANT SESSION REQUIRED`.** No authorised consultant QA context
exists and none was created (forbidden by §1/§16). Code-level position unchanged: the
consultant item page uses the **shared** `/api/v3/processing/*` surface and the shared
`ExtractionPanel`, so extraction/pipeline parity is shared by construction, while the
**CSV/XLSX preview parity gap remains** (the POD-3 preview lives in the customer/ops workbench
viewer). Not fixed here (no implementation authorised).

## 22. F-07 CSS result

**Result: `CONFIRMED DEFECT PRESENT IN THE DEPLOYED CSS` (class B, artifact-level) — visual
reproduction still requires an authenticated browser.**

Source mechanism (verified in the release, not taken on trust):

* `frontend/src/v3/v3.css:302-304` defines the meta row as **flex**:
  `.v3-meta-item{display:flex;gap:12px;font-size:14px;min-width:0}` with
  `.v3-meta-item .k{width:190px;flex:none}` and `.v3-meta-item .v{…overflow-wrap:anywhere}`.
* `frontend/src/v3/reports/reports.css:328-345` then **overrides** for the report surface:
  `.v3-meta-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 20px}`
  and re-declares `.v3-meta-item .k{font-size:12px;text-transform:uppercase;…}` /
  `.v3-meta-item .v{margin-top:2px;…}` **without** `min-width:0` or `overflow-wrap`.
* **Deployed-bundle evidence (production artifact):** in `main.a66f5596.css` the `v3.css`
  rules occur at byte **205493+** and the `reports.css` overrides at byte **269378+** —
  verified window: `…ate-columns:repeat(auto-fit,minmax(200px,1fr))}.v3-meta-item
  .k{color:var(--ct-color-text-muted);font-size:12px;letter-spacing:.04em;
  text-transform:uppercase}.v3-meta-item .v{font-weight:500;margin-top:2px;
  word-break:break-word}`. Because `reports.css` is later in the same bundle, the **grid**
  rule wins over the flex rule → the fixed-width label sits inside a collapsing grid cell and
  the value becomes unreadable/wrapped.
* `writing-mode` occurs **0 times** in the deployed CSS → the cause is **layout collapse, not
  writing-mode**.
* Third-party corroboration (attributed, not blindly trusted): the independent audit dump at
  `/tmp/f29_tokens.txt` documents the same CSS-01 root cause and records the recommended fix
  as **not applied**.

Objective browser capture (screenshot / computed styles) was **not** possible without an
authenticated session. **No CSS was modified.**

## 23. Tenant-isolation result

| Check | Result |
| --- | --- |
| Anonymous `GET /api/v3/documents` | **401** |
| Anonymous `POST /api/v3/documents` | 405 (method not allowed — correct) |
| Anonymous `/api/v3/reports`, `/api/v3/reports/types` | **401**, **401** |
| Anonymous Step 2 endpoints (`/api/generate-enhanced-report`, `/api/generate-sustainability-report`, `/api/upload-pdf`) | **401** each |
| Staff-only `/api/v3/ops/reporting/platform` anonymous | **401** |
| Authenticated own-organisation read | **UNVERIFIABLE in production** (no session); local closure run recorded **200** |
| Authenticated cross-tenant denial | **UNVERIFIABLE in production**; local closure run recorded **403** |
| Organisation enumeration / real customer data access | **not performed** (deliberately) |
| Records modified | **none** |

Note: `access-control-allow-origin: *` on the static site is a CDN asset policy, **not** an
API authorization control; the API refused every anonymous probe.

## 24. Error-handling result

Verified in source (`frontend/src/v3/api.js`):

* `api.js:67` → `raw = body.detail || body.error?.message || raw;` — the V3 client **does**
  read the backend's `detail` / `error.message` (required contract) ✓
* `api.js:21/77` → the message is displayed through `friendlyError(raw, status)`, while the
  **real backend text is preserved** on `error.raw` and **logged to the browser console**
  (`console.error('[CarbonTally V3] METHOD path → status:', raw)`) unless the caller opts into
  a quiet probe.
* Upload (`api.js:953-960`) and download/PDF (`api.js:223-230`) paths also surface
  `body.detail` ✓

Consequence for this triage: any real backend failure is recoverable from the **browser
console** even when the UI shows a friendly message — an actionable instruction for the next
acceptance run.

## 25. Previous acceptance reconciliation (`P8-STEP2-PRODUCTION-ACCEPTANCE-005`)

| # | Item in 005 | 005 result | 006 result | Change |
| --- | --- | --- | --- | --- |
| 1 | Frontend deployment identity | PASS | **PASS** (re-verified; marker set + promotion time + no-CSP finding) | unchanged |
| 2 | Backend deployment identity | PASS | **PASS** (re-verified; rndr-id changed, contract unchanged) | unchanged |
| 3 | CSV upload | UNVERIFIABLE | **still UNVERIFIABLE** (no session); silent-enqueue mechanism identified | deepened |
| 4 | CSV preview | UNVERIFIABLE | **still UNVERIFIABLE**; chain proven present in the customer path; four candidates with discriminating strings | deepened |
| 5 | CSV extraction | UNVERIFIABLE | **still UNVERIFIABLE for production**; **parser/extraction logic ruled out** (fixtures 1.0) | deepened |
| 6 | XLSX upload / preview / extraction | UNVERIFIABLE | **still UNVERIFIABLE**; `openpyxl` declared → dependency-safe | deepened |
| 7 | PDF extraction | UNVERIFIABLE | **now `FAIL` (behaviour mismatch) with two evidenced causes** | **upgraded** |
| 8 | Processing → EF continuity | UNVERIFIABLE | **still UNVERIFIABLE**; EF not implicated (upstream dependency) | unchanged |
| 9 | Blocked-job visibility | UNVERIFIABLE | **still UNVERIFIABLE** (markers deployed; likely the real state per §14(i)) | deepened |
| 10 | Report lifecycle | UNVERIFIABLE | **still UNVERIFIABLE** (markers deployed; anonymous 401) | deepened |
| 11 | Consultant parity | UNVERIFIABLE | **still UNVERIFIABLE**; preview gap confirmed to remain | unchanged |
| 12 | F-07 CSS | UNVERIFIABLE | **CONFIRMED PRESENT in the deployed CSS** (cascade + byte-order proof) | **upgraded** |
| 13 | Authenticated tenant isolation | UNVERIFIABLE | **still UNVERIFIABLE** (anonymous boundary re-verified PASS) | unchanged |

## 26. Defect classification

| Item | Class | Basis |
| --- | --- | --- |
| Frontend deployment identity, markers, no 5xx, no CSP | **A — PASS** | §5, §23 |
| Anonymous authorization boundary | **A — PASS** | §23 |
| CSV parsing/mapping (release code) | **A — PASS** | §10 (executed) |
| CSV preview (production) | **G — UNVERIFIABLE** | §9 (session required); four candidates listed |
| CSV extraction (production) | **G — UNVERIFIABLE** (code path = **F**) | §11 |
| XLSX (production) | **G — UNVERIFIABLE** (code = **F**) | §12 |
| PDF text-layer behaviour (blocks below gate) | **E — INTENTIONAL/DEFERRED** (PO decision: P1 `shadow`) | §14(i) |
| PDF/image OCR extraction in production | **C — CONFIGURATION/ENVIRONMENT** (undeclared OCR stack) | §14(ii) |
| Silent enqueue / worker-start failures | **B/C — OBSERVABILITY DEFECT** (invisible; `/health` says healthy) | §8, §11, §14(iii), §29 |
| F-07 CSS-01 unreadable/vertical meta text | **B — CONFIRMED PRODUCTION DEFECT** (deployed CSS; visual capture pending) | §22 |
| Blocked-job visibility, report lifecycle, consultant parity, authenticated tenant isolation | **G — UNVERIFIABLE** | §19–§21, §23 |
| Batch Upload | **E — INTENTIONAL/DEFERRED** | F-01, unchanged |

## 27. Production evidence

| Evidence | Source |
| --- | --- |
| Live index asset references, `last-modified`, cache policy, absence of CSP | live HTTP index/header probes (§5) |
| Deployed JS/CSS bundle contents and marker scans | downloaded production assets (`main.9febc8f0.js`, `main.a66f5596.css`) |
| CSS cascade byte offsets in the deployed bundle | byte-window extraction from `main.a66f5596.css` (§22) |
| Backend `/health`, `/`, `/api/v2/health`, `/openapi.json` (570 paths) | live HTTP probes (§5) |
| Anonymous 401/405/422 boundary; zero 5xx | live probes (§23) |
| Render identity change between 005 and 006 | `rndr-id` header comparison |
| Local execution of the release extraction code (CSV fixtures; text-layer PDF; no-text PDF; import availability) | in-process, no DB writes (§10, §14) |
| Git baseline/ancestry; protected-tree state | read-only Git inspection (§4, §28) |

## 28. Git / change-control proof

| Proof | Value |
| --- | --- |
| HEAD == origin | `b2596adef94c2385814765b8f5d42ba2f54126d6` == `origin/p8-release-reconciled` |
| Commits created / pushes performed | **none** |
| Source / test / migration / config changes | **none** |
| Database / storage writes by this task | **none** (extraction runs were in-process on bytes; nothing uploaded or touched) |
| Destructive operations | **none** |
| Staged files / tracked modifications | **none** |
| Worktree delta | the untracked 005 report (pre-existing) **plus** this new report — documentation only |
| Protected dirty `~/carbon_tally` | untouched (HEAD `20b7a92`, branch `main`, dirty 298) |
| Secrets | none printed, stored or committed (credential checks were name/path-only) |
| Step 3 | **not started**; no demo/investor data created |

## 29. Remaining blockers

1. **Authenticated production session (the single acceptance blocker).** No session token,
   credential or authenticated browser profile was supplied, and credential discovery is
   prohibited. Consequence: §8–§14, §19–§21, the §23 authenticated rows and the F-07 visual
   capture are `UNVERIFIABLE`.
2. **No worker/queue observability.** The worker starts in-process on app startup and its
   failure is only printed (`main.py:307`
   `⚠️ automatic-processing worker failed to start: {exc!r}`); `/health` does **not** check the
   worker and no worker/queue endpoint exists (`/health/detailed`, `/api/v3/ops/health` → 404).
   A stalled worker is invisible to operators, customers and health checks.
3. **No production DB/log access** in this task, so the decisive stage-level evidence in §11
   (queue row, item row, Render log strings) could not be collected.
4. **CI-build strictness:** `CI=true` builds fail on pre-existing legacy `src/App.js` lint
   warnings (unchanged; not a Step 2 regression).

## 30. Final verdict

`STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`

**What passed:** deployment identity (frontend + backend, marker-verified), the anonymous
authorization boundary, the release **CSV parsing/extraction code** (all three fixtures
completeness 1.0, executed), the P1 source implementation and its limits, partial-extraction
persistence, V3 error handling (`body.detail` / `body.error.message` surfaced, with the raw
message kept on `error.raw` and logged to the console), Git completeness and change control.

**What failed / is confirmed:**

* **F-07 CSS-01 — CONFIRMED DEFECT PRESENT IN THE DEPLOYED PRODUCTION CSS.** `reports.css`
  overrides `v3.css` (grid replaces flex; `.k` fixed at 190px inside a collapsing grid cell);
  the cascade byte-order is proven inside `main.a66f5596.css`; `writing-mode` appears nowhere.
  Visual capture still requires an authenticated browser.
* **PDF extraction — `FAIL` with two evidenced causes.** (a) Text-layer PDFs extract at **0.33**
  completeness, below the **0.50** gate, and therefore block — deliberate while the P1 hook is
  `shadow`. (b) Scanned/OCR PDFs and images have **no declared OCR path in production**
  (`tesseract`/`poppler` system binaries declared nowhere; `pypdfium2`,
  `rapidocr_onnxruntime`, `onnxruntime` absent from `requirements.txt`).

**Are the PO's three observations confirmed defects?** *Not as stated*, on this evidence:

* **"CSV extraction is not working"** → **not** a parser/extraction code defect (§10). The cause
  lies in the async chain (job enqueue / worker), the UI state, or the environment;
  confirmation requires the §11 evidence set.
* **"CSV preview is not working"** → **not** a missing or un-deployed implementation (§9). It is
  one of four candidates (missing `viewer_url`; cross-origin `fetch`/CORS failure; a
  pre-13:22 browser bundle; the wrong surface), each distinguishable by an exact on-screen
  string.
* **"PDF extraction is not working"** → **CONFIRMED real customer-visible failure**, with the two
  root causes above: one intentional (P1 `shadow` gate) and one a production dependency gap.

**Recommended next tasks (each requires its own unique ID, authorisation and cycle):**

| Proposed ID | Type | Scope |
| --- | --- | --- |
| `CT-STEP2-ACCEPT-007` | Acceptance, no code | With a PO-supplied session, execute §8–§14/§19–§21/§23 on **Babui Technologies UK Limited**; capture the §9 discriminating strings, the §11 queue/item/log evidence and the F-07 browser capture |
| `CT-STEP2-RENDER-DEPS-008` | Implementation | Declare the production extraction runtime (`tesseract-ocr`/`poppler-utils` via a render build declaration and/or pip `pypdfium2`, `rapidocr_onnxruntime`, `onnxruntime`) so scanned PDFs/images can be extracted |
| `CT-STEP2-WORKER-OBS-009` | Implementation | Make worker/queue failures non-silent and observable (worker health/heartbeat, queue depth, surfaced enqueue failures) |
| `CT-STEP2-F07-CSS-010` | Implementation | Scope/normalise the report-surface meta rules so `.v3-meta-item` cannot collapse (the CSS-01 remediation already documented) |
| `CT-STEP2-P1-ROLLOUT-011` | PO decision (+ config) | Decide/enable the controlled P1 rollout (or AI) for named customer organisations so multi-line documents can clear the completeness gate |

**No code was changed, no commit was created, no push occurred, and no production
configuration, data or storage was modified by this task. This task ends with this report.**









