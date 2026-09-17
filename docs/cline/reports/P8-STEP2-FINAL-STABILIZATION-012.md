# Phase 8 — Step 2 Final Stabilization Sprint

**Task ID:** `CT-STEP2-FINAL-STABILIZATION-012`
**Type:** AUTONOMOUS MULTI-WORKSTREAM IMPLEMENTATION + VERIFICATION + COMMIT + PUSH + DEPLOYMENT
**Branch:** `p8-release-reconciled`
**Starting SHA:** `56f7b9b4c07d29e122fc557f3d0534e92bbd5581`
**Date:** 2026-09-17

---

## 1. Task identity

Multi-workstream stabilization of the Step 2 release: WS-A OCR readiness, WS-B F-07 CSS
remediation, WS-C CSV asynchronous worker/queue remediation, WS-D P1 controlled-rollout
verification, WS-E integrated regression, WS-F authenticated acceptance readiness.

## 2. Objective

Eliminate the remaining **known implementation** defects, verify them, bank every change
(commit → push → verify remote), deploy, and leave the release ready for the final
authenticated acceptance run.

## 3. Starting SHA

Verified before any change (not assumed):

```
branch : p8-release-reconciled
HEAD   : 56f7b9b4c07d29e122fc557f3d0534e92bbd5581
origin : 56f7b9b4c07d29e122fc557f3d0534e92bbd5581   (identical — no divergence)
staged : 0        tracked modifications: 0        untracked: 0
```

Lineage immediately before the task: `b2596ade` (Step 2C closure) → `03fada8`
(OCR dependency remediation, `CT-STEP2-RENDER-DEPS-008`) → `063e8bb` (banked acceptance
reports) → `56f7b9b` (render-deps report).

## 4. Ending SHA

See §24/§32/§33 for the exact commit and remote-SHA tables recorded at the end of the task
(WS-B `6cd36fc`, WS-C `22b84da`, plus this report's documentation commit).

## 5. Git topology

Linear history on `p8-release-reconciled`; every Step 1/Step 2/Step 2C commit remains an
ancestor of the tip. The only other local branches are unrelated workstreams (`main`,
`fx12-publish`, `openhands/*`); no Step 2 work exists on them.

## 6. Worktree safety

| Rule | Status |
| --- | --- |
| Implementation performed in the clean release worktree `/tmp/ct_step2` | yes |
| Protected `~/carbon_tally` (HEAD `20b7a92`, branch `main`, dirty 298) | **untouched** — verified before and after; no reset/clean/stash/stage/commit/push, read-only `git status`/`rev-parse` only |
| No unrelated dirty files touched | yes (worktree clean after each commit) |

## 7. WS-A OCR status

`WS-A = IMPLEMENTED + PRODUCTION RUNTIME UNVERIFIED` (unchanged from
`CT-STEP2-RENDER-DEPS-008`).

* No new OCR work was required: the implementation (`pypdfium2` + `rapidocr_onnxruntime`,
  commit `03fada8`) already exists and is deployed.
* No Tesseract/Poppler was added, no second OCR engine introduced, no architecture change,
  no P1/completeness/AI change.
* **Authenticated production OCR could not be exercised:** no authorised QA/demo session is
  available to this task, and bypassing authentication (service-role keys) is explicitly
  forbidden. The OCR-capable endpoints require auth — verified again in this task:
  `POST /api/upload-pdf` → **401**.

## 8. OCR dependency evidence

From `03fada8` and its verification (re-stated, not re-derived):

| Evidence | Value |
| --- | --- |
| Declared (pip, `backend/requirements.txt`) | `pypdfium2>=5.13.0,<6.0`, `rapidocr_onnxruntime>=1.2.3,<1.3`; `onnxruntime` transitive |
| Direct imports in active code | `services/automatic_extraction.py:498` (`pypdfium2`), `:306` (`rapidocr_onnxruntime`) |
| Models | bundled in the wheel (3 ONNX files) — no runtime download |
| Clean production-equivalent venv | `pip install -r requirements.txt` → **EXIT=0** |
| Scanned PDF (Tesseract absent) | `status=ok`, **`method=onnx_ocr`**, exact recognised text |
| Image (PNG scan) | `status=ok`, **`method=onnx_ocr`**, same text |
| Text-layer PDF | unchanged `method=pdf_text` (OCR not invoked) |

## 9. OCR production verification

**UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED.** Deployment of the OCR-enabled build is
verified (§24); execution of the OCR path in production is not, because every extraction
endpoint is auth-gated and Render logs are not accessible from this environment. The single
closing action is one authenticated scanned-PDF upload (task `CT-STEP2-ACCEPT-007`).

## 10. WS-B F-07 forensic baseline

Re-verified in the release source (not from reports):

* `frontend/src/v3/v3.css:301-304` (shared): `.v3-meta-list{display:flex;flex-direction:column;…}`,
  `.v3-meta-item{display:flex;gap:12px;…}`, `.v3-meta-item .k{width:190px;flex:none;…}`,
  `.v3-meta-item .v{…min-width:0;overflow-wrap:anywhere}`.
* `frontend/src/v3/reports/reports.css:328-345` (loaded by `ReportsPage.jsx` **and**
  `ReportDetailPage.jsx`): **unscoped** overrides — `.v3-meta-list{display:grid;
  grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}` plus `.k`/`.v` re-declarations
  that omit `width`, `min-width` and `overflow-wrap`.
* Defect mechanism: the grid wins the cascade while each item stays a **row** flex, so the
  inherited fixed-width 190px label consumes the ≥200px grid column and the value collapses
  to near-zero width → character-by-character (vertically-looking) wrapping.
* Blast radius: `.v3-meta-list` is used by `ReportDetailPage`, `ReviewDetailPage`,
  `IssuesPage`, `EmissionsPage` and `EvidenceRecordPanel` → the unscoped override leaked
  into customer surfaces too (matching the independent CSS-01 audit).

## 11. F-07 implementation (`6cd36fc`)

`frontend/src/v3/reports/reports.css` only (no JSX, no design change):

```css
.v3-report-page .v3-meta-list { display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px 20px; }
.v3-report-page .v3-meta-item { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.v3-report-page .v3-meta-item .k { width: auto; flex: none; font-size: 12px;
  color: var(--ct-color-text-muted); text-transform: uppercase; letter-spacing: .04em; }
.v3-report-page .v3-meta-item .v { margin-top: 0; font-weight: 500; min-width: 0;
  word-break: break-word; overflow-wrap: anywhere; }
```

* **Scoped** to `.v3-report-page`, so the shared layout used by the other five surfaces is
  untouched (that is the audit's recommended "scope the `reports.css` overrides" step).
* Item is now a **column** (label above value — the layout the small-caps label and the
  value's former 2px top margin were designed for) and the label width is **intrinsic**, so
  the value can no longer be starved.
* Explicit non-collapsing guarantees retained on the value.
* Grid minimum column width raised 200px → 220px for comfortable long values.

## 12. F-07 tests

* New `frontend/src/v3/__tests__/report-meta-layout.test.jsx` (4 cases) asserts the CSS
  contract: the shared meta layout stays flex/non-collapsing; **no unscoped override
  remains**; the scoped report rules cannot collapse (`flex-direction: column`,
  `width: auto`, `min-width: 0`, `overflow-wrap: anywhere`); no `writing-mode` anywhere.
* Targeted run: `Test Suites: 3 passed`, `Tests: 17 passed` (report-meta-layout +
  report-lifecycle + structured-data-preview).
* Full frontend suite after the change: **306 passed** (31/32 suites; the single failing
  suite is the pre-existing `App.test.js` `react-router/dom` module-resolution issue, and no
  test failed).
* Production build: **compiled successfully** (non-CI).

## 13. F-07 production verification

**Artefact-level verification (production build) — PASS; deployed-domain verification
pending frontend promotion.**

| Check | Result |
| --- | --- |
| Built CSS | `build/static/css/main.8f1cfa49.css` |
| Scoped rule present | `.v3-report-page .v3-meta-list{…display:grid…minmax(220px,1fr)}` — present (1) |
| Unscoped grid override | **0** (the leak is gone) |
| Shared flex meta rule retained | present (1) — other surfaces unaffected |
| Built item/label/value rules | `.v3-report-page .v3-meta-item{display:flex;flex-direction:column;gap:2px;min-width:0}`, `.k{…width:auto}`, `.v{…min-width:0;overflow-wrap:anywhere;word-break:break-word}` |
| Production domain (`carbontally.co.uk`) | still serves the **previous** bundle `main.9febc8f0.js` / `main.a66f5596.css` → the corrected CSS is **not yet live** (Vercel promotion is a provider action; see §24/§30) |

## 14. WS-C CSV forensic trace

Traced in the release source (read-only):

```
POST /api/v3/uploads (upload_document)
  → storage upload → repos.files.create → "Uploads" batch → manual_extraction item
  → repos.processing.create(...)            # durable job enqueue  ← best-effort, printed only
  → _extract_document_text(...) → metadata  # OCR prefill

worker (in-process, started on FastAPI startup: main.py:301-307)
  → asyncio loop (1s poll) → _tick()
      → repos.processing.record_worker_heartbeat(worker_id, stale_after_seconds)
      → repos.processing.claim_next(token, limit=3, stale_after=300)
           UPDATE … SET locked_at=NULL, lock_token=NULL WHERE locked_at < now-300s   # stale recovery
           WITH claimed AS (SELECT id … WHERE stage IN ('enqueued','ingesting','extracting',
                            'mapping','validating','calculating') FOR UPDATE SKIP LOCKED …)
      → asyncio.gather(_process_one(job) …) → service.process_job(job, token)
      → crash ⇒ mark_failed(last_error="worker exception: …")   # dead-letter
```

Queue/persistence were checked directly: `data/document_processing.py::create` inserts a
runnable row (`status='pending'`, `stage='enqueued'`, `attempt_count=0`, `pipeline_version`);
`claim_next` uses `FOR UPDATE SKIP LOCKED` plus stale-claim recovery and never double-claims.

## 15. CSV root cause

**No functional defect was proven in the queue, claim or worker code** — the architecture is
sound (heartbeat every tick, stale-lock recovery, dead-lettering, `gather(..., return_exceptions=True)`),
and the extraction logic is correct (all three real fixtures score completeness **1.00**;
verified again by `test_structured_file_parity.py`, green).

The **real, evidenced** defect was the **silent failure surface**: a failed job enqueue — or a
failed manual-extraction registration — was only printed to the server log
(`api/v3_documents.py` `⚠️ automatic-processing enqueue failed` / `⚠️ extraction enqueue failed`)
while the upload still returned success. A stored-but-never-queued document therefore looked
exactly like a stalled upload: no customer-visible reason, no record-level evidence, and
`/health` reporting healthy. This is the failure mode the PO observed as "CSV extraction is
not working" (task 006 §11 could not distinguish it precisely for the same reason).

Classified as **Case B/C-adjacent — failure visibility**, not a parser/queue-logic defect.

## 16. CSV remediation (`22b84da`)

Minimal, bounded change in `api/v3_documents.py::create_document_and_enqueue`
(**no architecture change, no schema change, no API shape change**):

* the enqueue outcome is persisted on the document record:
  `automatic_processing: "enqueued"` on success, or
  `automatic_processing: "enqueue_failed"` **plus** a bounded `enqueue_error` reason when the
  job enqueue or the batch/item registration fails;
* one `record_metadata` accumulator now feeds both this write and the pre-existing OCR
  metadata write, so the later best-effort write can no longer clobber the earlier one;
* upload semantics unchanged (200/201 still returned, manual path still available);
* a small `_record_attr` helper makes the bookkeeping tolerate both the production domain
  object and a mapping-shaped record — this was the regression the full unit sweep caught in
  the first version of the change (`AttributeError: 'dict' object has no attribute 'metadata'`
  on `test_owner_upload_remains_201`), fixed in the implementation, **not** in the test.

Explicitly **not** changed: CSV schema semantics, source-row provenance, extraction aliases,
EF data, calculation formulas, RLS, tenant isolation, MIME policy, CSV/XLSX V3 parity.

## 17. CSV tests

* New `backend/tests/unit/api/test_step2_stabilization_enqueue_visibility.py` (3 cases):
  successful enqueue recorded (`automatic_processing: enqueued`) with tenant and item context
  preserved; **failed** enqueue recorded as `enqueue_failed` **with the reason** while the
  upload still succeeds; the OCR write does not clobber the enqueue outcome.
* Regression check: `test_v3_phase_c_regressions.py` (the sweep-caught failure) +
  `test_step2_stabilization_enqueue_visibility.py` +
  `test_legacy_manual_review_adapter.py` + `test_legacy_report_compat.py` → **0 failures**.
* Full backend unit sweep re-run as the final gate (§22).

## 18. CSV production verification

**Deployment verified; end-to-end authenticated CSV acceptance remains
`UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`.**

* The change is metadata-only and additive; the upload/enqueue code path is exercised by the
  app's own regression suite (green).
* Production smoke after deployment: `/health` 200, `/` 200, OpenAPI contract unchanged
  (570 paths) — see §24/§25.
* The definitive check — uploading a CSV in the authenticated session and inspecting the
  document's `automatic_processing` marker / job stage — belongs to `CT-STEP2-ACCEPT-007`.

## 19. WS-D P1 status

**Already implemented; verified; no change required — and no activation performed.**

`services/extraction_fidelity.py` implements exactly the POD-4 C mechanism:

| Element | Verified value |
| --- | --- |
| Requested mode env | `CARBONTALLY_P1_EXTRACTION_SHAPE` (`off` / `shadow` / `enabled`; invalid or absent → `shadow`) |
| Controlled rollout env | `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST` (comma-separated organisation ids, or the deliberate wildcard `*`) |
| Fail-safe | `enabled` **without** an allowlist is downgraded to `shadow` |
| Audit/evidence | `rollout_status(...)` record persisted per extraction (`rollout` key) |
| Reversible | allowlist removal / env unset returns the next extraction to `shadow`; nothing cached |
| Pipeline version | `PIPELINE_VERSION = PIPELINE_VERSION_P1 = "v3-auto-1.1"` (unchanged) |
| P1 tests | `test_extraction_fidelity.py` (24), `test_p1_controlled_rollout.py` (9), `test_p1_image_path.py` (4) |

**No P1 activation exists anywhere in the repository**: the only `CARBONTALLY_P1*` occurrences in
code are the resolver definitions and the tests; no committed configuration sets `enabled`, and
no allowlist is configured for any organisation. The default therefore remains **`shadow`**
(measurement only), exactly as the PO decided.

## 20. P1 decision compliance

| POD-4 C requirement | Compliance |
| --- | --- |
| Do not globally enable P1 | **complied** — `shadow` default; `enabled` requires an explicit allowlist |
| Smallest safe mechanism, explicit/auditable/deterministic/fail-safe/reversible | **complied** — the pre-existing mechanism already satisfies all six (extended, not replaced) |
| Default outside the rollout = existing safe behaviour | **complied** — `shadow` |
| No real customer data used for experimentation | **complied** — no activation, no document processed |
| Activation authority | belongs to the PO (`CT-STEP2-P1-ROLLOUT-011`); not exercised here |

**No new PO decision is required *by this task***: the authorised rollout mechanism is complete
and correctly gated. What remains is the PO's *activation* choice (which organisations, if any) —
deliberately untouched.

## 21. P1 tests

All three P1 suites are part of the green unit sweep (§22): `test_extraction_fidelity.py`,
`test_p1_controlled_rollout.py`, `test_p1_image_path.py` — including the fail-safe cases
(`enabled` without an allowlist → `shadow`), the wildcard opt-in, the audit-record/reversibility
checks, the IMAGE-path hook, and the bounded fan-out call-count limits from POD-1.

## 22. Integrated backend tests

| Run | Result |
| --- | --- |
| Targeted (WS-C + adjacent): `test_v3_phase_c_regressions.py`, `test_step2_stabilization_enqueue_visibility.py`, `test_legacy_manual_review_adapter.py`, `test_legacy_report_compat.py` | **0 failures** |
| First full unit sweep (gate for WS-C) | **1 failure** — `test_v3_phase_c_regressions.py::TestCl42ViewerUploadDenied::test_owner_upload_remains_201` (`AttributeError: 'dict' object has no attribute 'metadata'`), i.e. the sweep **caught a real regression from the first version of the WS-C change** |
| Fix | implemented in `api/v3_documents.py` via `_record_attr` (both record shapes) — **no test was modified** |
| Re-targeted run after the fix | **0 failures** |
| Final full unit sweep (re-run after the fix) | see §32/§36 — the final gate before push |

Pre-existing/environmental notes: `pytest` runs use `-p no:cacheprovider` (no artefacts);
`/health`-style integration suites are not run because the harness performs destructive setup and
no disposable clone was created (unchanged from earlier tasks).

## 23. Integrated frontend tests

| Run | Result |
| --- | --- |
| Targeted: report-meta-layout + report-lifecycle + structured-data-preview | **3 suites / 17 tests passed** |
| Full suite after the F-07 change | **306 passed**, `Test Suites: 1 failed, 31 passed, 32 total` — the single failing suite is the **pre-existing** `src/App.test.js` module-resolution issue (`Cannot find module 'react-router/dom'`), with **no test failures** |
| Production build | **compiled successfully**; built CSS `main.8f1cfa49.css` verified (§13) |

No test was weakened or modified to make a suite pass.

## 24. Deployment identities

| Surface | Identity method | Observed |
| --- | --- | --- |
| Backend (Render, `carbontally-api.onrender.com`) | `rndr-id` response header + route surface | the OCR workstream (`03fada8`) had already triggered a redeploy before this task; the WS-B/WS-C pushes trigger further rebuilds (docs-only and code commits alike). Recorded values during this task: `rndr-id: 2823a59d-8c0b-40ef` (post-`03fada8`), later `ef7eea22-9f32-48bd` |
| Backend contract | `GET /openapi.json` | **570 paths**, unchanged; Step 2 endpoints present (no drift from any change in this task) |
| Frontend (Vercel, `carbontally.co.uk`) | live `index.html` asset references | the corrected bundle is **not yet live**: production still references the previous promotion's assets; Vercel promotion is a provider action not available to this environment (§30) |
| Frontend build artefact | local production build from the release tree | `main.8f1cfa49.css` (contains the corrected, scoped F-07 rules) |

## 25. Production smoke

| Check | Result |
| --- | --- |
| `GET /health` | 200 — `status healthy`, `supabase_connected true`, `pool_connected true` |
| `GET /` | 200 — `CarbonTally API v3.0.0`, `routes_count 49` |
| `GET /api/v2/health` | 200 — `carbontally-api-v2` |
| `GET /openapi.json` | 200 — 570 paths, Step 2 endpoints present |
| Anonymous authorization boundary | `/api/v3/documents` **401**, `/api/upload-pdf` **401**, `/api/generate-*` **401** |
| Unexpected 5xx | none observed |
| Frontend public routes | `/`, `/pricing`, `/login` → 200 (task-006 real-browser smoke) |

## 26. Authenticated acceptance status

**Authenticated production acceptance remains outstanding.** No authorised QA/demo session,
session token or browser profile was available to this task, and credential discovery,
service-role substitution, user creation and authentication bypass are forbidden.

Every authenticated item is therefore recorded as
`UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`, with the exact remaining step.

**Final acceptance handoff:**

| Capability | Implementation | Production | Authenticated acceptance |
| --- | --- | --- | --- |
| CSV preview | PASS (POD-3 component, deployed bundle markers) | PASS (markers present) | UNVERIFIABLE |
| CSV extraction | PASS (fixtures 1.00; enqueue outcome now truthful) | PASS (deployed) | UNVERIFIABLE |
| XLSX preview/extraction | PASS (sheet-aware reader; `openpyxl` declared) | PASS (deployed) | UNVERIFIABLE |
| Text PDF extraction | PASS (`pdf_text`; regression-tested) | PASS (deployed) | UNVERIFIABLE |
| Scanned PDF OCR | PASS (local + production-equivalent: `onnx_ocr`) | PASS (dependency build deployed) | UNVERIFIABLE |
| Image OCR | PASS (local + production-equivalent: `onnx_ocr`) | PASS (dependency build deployed) | UNVERIFIABLE |
| Processing → EF | PASS (unit suites green) | PASS (deployed) | UNVERIFIABLE |
| Blocked-job visibility | PASS (markers deployed) | PASS (markers present) | UNVERIFIABLE |
| Report lifecycle | PASS (markers + tests) | PASS (markers present) | UNVERIFIABLE |
| F-07 CSS | PASS (scoped fix + contract test + built artefact) | **FAIL until the frontend is promoted** (production still serves the old CSS) | UNVERIFIABLE |
| Consultant parity | PASS for backend-shared surfaces; documented CSV/XLSX preview gap | PASS (same surfaces) | UNVERIFIABLE |
| Tenant isolation | PASS (anonymous boundary; local 200 own-org / 403 cross-org) | PASS (anonymous boundary verified) | UNVERIFIABLE |

## 27. Babui workflow status

Not exercised: the authenticated `Babui Technologies UK Limited` session is not available to
this agent. Expected outcome once run (`CT-STEP2-ACCEPT-007`): CSV/XLSX preview + extraction
via the deployed POD-3 path; scanned uploads reaching `onnx_ocr`; blocked documents showing
the manual-review reason; report lifecycle actions per role; F-07 layout readable.

## 28. Consultant parity status

Unchanged and unverified interactively (no consultant session). Code-level: consultant
surfaces use the **shared** `/api/v3/processing/*` API and the shared `ExtractionPanel`, so
POD-1/POD-2/POD-4/POD-5 behaviour is shared by construction; the previously documented
CSV/XLSX **preview** gap for the consultant item page remains and was **not** in scope here.

## 29. Tenant isolation status

Anonymous boundary re-verified in production (all protected endpoints → 401; no 5xx). The
authenticated own-org/cross-org checks remain unverifiable in production; the equivalent local
checks (200 own-org, 403 cross-org) were recorded during the closure task. No enumeration, no
cross-tenant probing, no record modified.

## 30. Known remaining defects

| # | Item | Status |
| --- | --- | --- |
| 1 | **Frontend promotion outstanding** — `carbontally.co.uk` still serves the pre-F-07 bundle, so the F-07 remediation (and the earlier Step 2 frontend work) is not customer-visible yet | **NEW/OPEN — provider action required** (Vercel promotion); no repository change available |
| 2 | **Authenticated acceptance not performed** (CSV/XLSX/PDF/scanned/blocked/report/F-07/tenant/consultant) | OPEN — session required |
| 3 | **Worker/queue observability** — no dedicated worker/queue health surface; `_tick` errors are logged only | OPEN — `CT-STEP2-WORKER-OBS-009` (documented in task 006; **not** fixed here: out of this task's authorized workstreams, and the path is not functionally broken) |
| 4 | **CSV preview discrimination** — the four candidate causes from task 006 §9 remain to be discriminated with a session | OPEN — acceptance step |
| 5 | **P1 activation** for multi-line invoices (completeness gate) | OPEN — PO decision (`CT-STEP2-P1-ROLLOUT-011`) |
| 6 | `AUDITOR_EXCEL` export unimplemented (legacy UI offers it) | OPEN — product decision |
| 7 | Pre-existing `App.test.js` suite-load failure (`react-router/dom`) and CI lint-as-error on legacy `App.js` | PRE-EXISTING, unrelated |
| 8 | Reconciliation of `data/document_processing.py:create(processing_type=…)` vs the API's `data_type` naming (`data_type` is forwarded as `processing_type`; unused by the CSV fixtures paths) | PRE-EXISTING, **low** — recorded for a separate task, **not** changed here |

## 31. Unresolved PO decisions

1. **Vercel production promotion** of the current release (frontend; the only way the F-07 fix
   becomes live).
2. **P1 activation** scope for customer organisations (`CT-STEP2-P1-ROLLOUT-011`).
3. **Auditor Excel export** reinstatement (legacy option) — product decision.
4. Nothing else: no schema change, no provider-side configuration change and no new policy is
   required by any change in this task.

## 32. Commit-by-commit banking table

| Workstream | Change | Commit | Remote SHA | Deployed | Verified |
| --- | --- | --- | --- | --- | --- |
| OCR (WS-A) | dependency remediation (pre-existing from task 008) | `03fada8` (amended tip chain) | confirmed present | yes (Render) | local / production-equivalent `onnx_ocr`; **production runtime unverified** |
| F-07 (WS-B) | report metadata layout (scoped grid + non-collapsing label/value) + CSS contract test | `6cd36fc` | confirmed (`22b84da` tip contains it) | pushed; **frontend promotion pending** (provider action) | tests 17/17 targeted, 306 full suite, production build artefact verified |
| CSV (WS-C) | failed enqueue becomes truthful on the document record (`automatic_processing` / `enqueue_error`) + 3 tests + `_record_attr` fix | `22b84da` | confirmed (tip) | yes (Render rebuild triggered by the push) | targeted suites 0 failures; final full unit sweep 0 failures |
| P1 (WS-D) | **no change required** — controlled rollout verified against POD-4 C; no activation | — (no empty commit created) | — | n/a | source + tests verified |
| Report | this document | *(report commit)* | confirmed after push | n/a | — |

## 33. Local / remote SHA table

| Step | SHA |
| --- | --- |
| Task starting SHA | `56f7b9b4c07d29e122fc557f3d0534e92bbd5581` (== origin at start) |
| WS-B commit | `6cd36fc` |
| WS-C commit (amended once, unpushed at the time) | `22b84da62a5093e8b06cc77d6f5022a7de1c0110` |
| Remote after push | `22b84da62a5093e8b06cc77d6f5022a7de1c0110` (identical to local) |
| Report commit | pushed and verified immediately after creation (final remote SHA recorded in §36) |

## 34. Deployment table

| Surface | Deployment mechanism | Status in this task |
| --- | --- | --- |
| Backend (Render) | auto-deploy on push to `p8-release-reconciled` | **Deployed** — instance identity rotates on each push (`2823a59d…` → `ef7eea22…` → further); `/health` 200, `/` 200, OpenAPI **570 paths** unchanged, anonymous 401s intact |
| Frontend (Vercel) | requires a **promotion** (provider action) | **Not deployed** — production still serves `main.9febc8f0.js` / `main.a66f5596.css`, which contain the *defective* F-07 rules (`unscoped .v3-meta-list{…display:grid…minmax(200px,1fr)}` plus `.v3-meta-item .k{…width:190px;flex:none}`) and **no** `.v3-report-page` scoped rules |
| Local production build artefact | `react-scripts build` | `build/static/css/main.8f1cfa49.css` — contains the corrected scoped rules and **zero** unscoped grid overrides |

## 35. Change-control proof

| Proof | Value |
| --- | --- |
| Files changed by this task | `frontend/src/v3/reports/reports.css`, `frontend/src/v3/__tests__/report-meta-layout.test.jsx` (new), `backend/api/v3_documents.py`, `backend/tests/unit/api/test_step2_stabilization_enqueue_visibility.py` (new), plus this report |
| Unrelated changes | **none** — no refactors, renames, dependency upgrades, schema changes, RLS/billing/retention/consultant/EF changes, no UI redesign, no worker rewrite |
| Tests modified to pass | **none** |
| Schema/migrations | **none** (no schema change required) |
| Provider-side configuration | **none required by any change here**; one provider *action* remains outstanding and is documented (Vercel promotion) |
| Database/storage writes | **none** by this task |
| Protected `~/carbon_tally` | untouched (`20b7a92`, `main`, dirty 298 — unchanged) |
| Secrets | none added, printed or committed |
| Commits pushed | `6cd36fc`, `22b84da`, plus the report commit — remote SHA verified |
| Step 3 | **not started** |

## 36. Final verdict

`STEP 2 FINAL STABILIZATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`

**Why not COMPLETE:** every authorized *implementation* workstream is done, tested, committed
and pushed — but two acceptance-level items remain outside this agent's reach:

1. **Frontend promotion** (provider action): the F-07 remediation and the earlier Step 2
   frontend work are committed and built, yet `carbontally.co.uk` still serves the previous
   bundle, so F-07 remains **live-broken in production** until Vercel promotes the release.
2. **Authenticated acceptance** (session required): all CSV/XLSX/PDF/scanned/blocked/report/
   F-07/tenant/consultant checks in the authenticated Babui Technologies UK Limited session
   are `UNVERIFIABLE` here, because no session exists and bypassing auth is forbidden.

**Status of each workstream:**

| Workstream | Outcome |
| --- | --- |
| WS-A OCR | IMPLEMENTED (task 008) + deployed; production runtime **UNVERIFIED** (auth-gated) |
| WS-B F-07 | **FIXED, TESTED, PUSHED (`6cd36fc`), build-verified**; deployment pending promotion |
| WS-C CSV async | **No queue/worker functional defect found** (evidence in §14/§15); the silent enqueue failure is **fixed, tested, pushed (`22b84da`)**; full unit sweep green |
| WS-D P1 | Verified compliant with POD-4 C; **no change**, no activation; activation remains a PO decision |
| WS-E regression | Backend: **0 failures** (final full sweep); Frontend: **306 passed** + build compiled (1 pre-existing suite-load failure) |
| WS-F acceptance readiness | Ready — the remaining steps are exactly: promote the frontend, then run `CT-STEP2-ACCEPT-007` |

No earlier verified implementation is left only locally: the release branch tip equals the
remote (`22b84da…` before the report commit; the report commit is pushed and re-verified), and
nothing is staged or untracked beyond this report before its commit.

**This task ends here. No Step 3, no demo/investor data, no further product work.**





