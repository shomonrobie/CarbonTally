# Phase 8 — Step 2 Final Production Acceptance

**Task ID:** `CT-STEP2-PRODUCTION-ACCEPTANCE-005`
**Task type:** FINAL PRODUCTION ACCEPTANCE / VERIFICATION ONLY (no code changes, no commits, no pushes)
**Branch:** `p8-release-reconciled`
**Expected production release SHA:** `b2596adef94c2385814765b8f5d42ba2f54126d6`
**Date:** 2026-09-17
**Verdict:** `STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`
(no production defect found; the outstanding gate is **authenticated production acceptance**, which requires an authorised production/QA account — see §7, §23, §27)

---

## 1. Task identity

Final acceptance gate for Step 2 Functional Remediation. Scope: verify that the Step 2
release is actually deployed and that the customer-facing functionality works in
production. **Verification only** — this task implemented nothing, fixed nothing, committed
nothing and pushed nothing (§25 proves it).

## 2. Authorization

The Product Owner authorised this task as the final acceptance gate for Step 2, with the
release recorded as: Production / `carbontally.co.uk` / branch `p8-release-reconciled` /
commit `b2596adef94c2385814765b8f5d42ba2f54126d6` / status Ready. Backend Step 2C
deployment had previously been verified. All acceptance actions performed were read-only.

## 3. Production release identity (independently verified)

| Surface | Identity | Verification method |
| --- | --- | --- |
| Frontend | `https://carbontally.co.uk` → live `index.html` references **`/static/js/main.9febc8f0.js`** and `/static/css/main.a66f5596.css` | fetched the live index and parsed its asset references (not a timestamp) |
| Frontend bundle content | 2,286,957 bytes; contains Step 1/S6 + Step 2C + WS-H markers (§5) | downloaded and string-scanned the deployed asset |
| Backend | `carbontally-api.onrender.com`: `/health` 200 (database/pool connected), `/` 200 (v3, routes 49), `/openapi.json` **570 paths** | live HTTP probes |
| Backend deploy identity | `rndr-id: b87594b2-16a1-4bea`, `x-render-origin-server: uvicorn` | response headers |
| Old frontend bundle | `main.1e761f98.js` is **not referenced** by the live index; its path still resolves 200 because Vercel retains previous deployments' immutable assets (expected — **not** evidence of the old build being served) | live index + asset probe |

## 4. Git identity

```
HEAD   : b2596adef94c2385814765b8f5d42ba2f54126d6
origin : b2596adef94c2385814765b8f5d42ba2f54126d6   (identical)
branch : p8-release-reconciled
dirty  : 0      staged : 0
commits after the expected release : none
protected dirty tree ~/carbon_tally : HEAD 20b7a92 (branch main), dirty 298 — unchanged, untouched
```

## 5. Frontend deployment evidence

Markers scanned in the **deployed** JS/CSS (string literals that survive minification —
caption phrases are template-built and are not reliable markers):

| Feature | Marker | Deployed JS | Deployed CSS |
| --- | --- | --- | --- |
| POD-3 structured preview (test id) | `structured-preview` | **1** | 0 |
| POD-3 preview stylesheet | `ct-wb-viewer__data` | **1** | **1** |
| POD-3 preview error state | `preview unavailable` | **1** | 0 |
| Unknown-type placeholder (deliberately retained) | `Document preview is not available` | 1 | 0 |
| WS-H blocked visibility | `manual_review_reason` | **1** | 0 |
| WS-H blocked card text | ` - awaiting manual review.` | **1** | 0 |
| WS-H retry/confirm continuity | `Job re-enqueued.`, `Failed to retry job`, `Job confirmed - the pipeline will resume it.` | **1 each** | 0 |
| S6 report lifecycle | `Changes requested`, `Approved. It can now be finalised.`, `Changes were requested. A revised version is needed.`, `Final and locked. Finalised reports are immutable.`, `No action is available to you on this version.`, `calculated_emissions_kg_co2e` | **1 each** | 0 |

Conclusion: the deployed frontend **is** the Step 2 release build (Step 1 S6 + Step 2C
POD-3 + Step 2 WS-H present) and is **no longer** the pre-Step-2C bundle.

## 6. Backend deployment evidence

| Check | Result |
| --- | --- |
| `GET /health` | **200** — `status healthy`, `supabase_connected true`, `pool_connected true`; components: `database connected`, `pool connected`, `api running (routes 49)` |
| `GET /` | **200** — `CarbonTally API v3.0.0`, `api_version v3`, `routes_count 49` |
| `GET /openapi.json` | **200**, **570 paths** |
| POD-5 report aliases | `/api/generate-enhanced-report`, `/api/generate-sustainability-report` **present** (anonymous POST → **401**) |
| POD-2 route | `/api/upload-pdf` **present** (anonymous POST → **401**) |
| Pre-existing report route | `/api/reports/generate-enhanced-report` present (anonymous POST → **422** validation) |
| Current V3 surfaces | `/api/v3/documents`, `/api/v3/reports` present (anonymous → **401**) |
| Worker/queue health | **no dedicated worker endpoint in this build** (`/health/detailed` 404, `/api/v3/ops/health` 404; `/api/v3/ops/reporting/platform` 401 = present, staff-only). `/health` reports API/database/pool only — see §23 (observability limitation, not a defect) |
| Unexpected 5xx | **none observed** |

## 7. Authentication method / status

**Status: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED` for every authenticated item.**

* Tooling **is available** (new information versus earlier Step 2 reports):
  `google-chrome` 152.0.7977.64, `firefox`, `selenium 4.47.0` (backend venv), and the QA
  harness browser driver (`qa_harness/.venv` → **playwright present**,
  `qa_harness/browser/playwright/controller.py`). The blocker is therefore **not** browser
  capability.
* The blocker is **credentials**: no authorised production/QA account exists. Searches found
  no documented production test/QA/acceptance account and no
  `QA_*`/`TEST_*`/`DEMO_*`/`PROD_*` environment variables. The only credential store present
  is documented as **LOCAL-ONLY** (`tools/seed_investor_demo/DEMO_IDENTITIES.md` plus the
  gitignored `.local-demo-credentials.md`: "these do not exist in production").
* Consequently: no production login was attempted, no production user was created, no other
  customer's organisation was touched, and **no credential value appears in this report**.
* What was executed instead (all read-only): live HTTP probes (§6, §15, §16) and a
  **real-browser** DOM smoke of the public routes with Chrome headless (§16).
* Exact remaining requirement: an authorised production QA/demo account (any role) — or an
  approved disposable QA organisation — supplied to the acceptance agent so the
  authenticated items (§8–§13 and F-07) can be executed.

---

## 8. CSV acceptance

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** (workflow not executed; not claimed as passed).

| Step of the required workflow | Status | Evidence / reason |
| --- | --- | --- |
| CSV upload | UNVERIFIABLE | requires an authenticated organisation session; none available (§7) |
| Workspace registration | UNVERIFIABLE | same |
| Left-side workspace preview | UNVERIFIABLE | same (the deployed bundle contains the preview component — §5 — but rendering was not exercised) |
| Structured/tabular preview | UNVERIFIABLE | same |
| Extraction | UNVERIFIABLE | same |
| Extracted data visible | UNVERIFIABLE | same |

Supporting (non-substitute) evidence that the described regression is addressed in the
deployed build and in the release code:

* the deployed bundle contains the POD-3 preview component and its stylesheet (§5);
* in the release code path the Step 2C regression fixture `mock_uk_fuel_card_messy.csv`
  resolves from completeness **0.00 → 1.00** (50 rows, `unresolved = []`, first line
  `Diesel / 53.8 litres / Esso / 01/10/2023 / source_row 1`), pinned by
  `tests/unit/services/test_structured_file_parity.py` (11 cases, green);
* `mock_uk_utility_bill.csv` **0.67 → 1.00**; `mock_scope3.csv` unchanged at 1.00.

Exact remaining acceptance: upload the three fixtures through the authenticated production
workspace and confirm preview + extraction + provenance visually.

## 9. XLSX acceptance

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** (no XLSX upload performed).

| Requirement | Status | Evidence / reason |
| --- | --- | --- |
| XLSX uploads | UNVERIFIABLE | no authenticated production session |
| Appears in workspace | UNVERIFIABLE | same |
| Preview renders | UNVERIFIABLE | same |
| Workbook/sheet information available | UNVERIFIABLE in production | deployed build exposes it (`sheet_names`/`source_sheet`); not exercised |
| Correct sheet/data discovered; cover sheets produce no phantom lines | Verified in **code**, UNVERIFIABLE in production | synthetic cover-sheet-first workbook test: `source_sheet = "Readings"`, `sheet_names = ["Summary","Readings"]`, phantom lines suppressed |
| Rows/columns preserved; extraction occurs; provenance retained | Verified in code, UNVERIFIABLE in production | `source_row` / `source_headers` implemented and test-pinned |
| XLSX not treated as PDF/image | **PASS (code-level)** | `test_xlsx_is_never_treated_as_a_pdf_or_image` asserts `method == "xlsx"`, `page_count == 0` |

Limitation recorded: **no production XLSX fixture was uploaded** and no production XLSX
document was inspected (no session). No XLSX document was invented.

## 10. Processing / emission-factor continuity

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** for the live
extraction → mapping → factor lookup → calculation chain.

* Not verified in production: no authenticated job was run; running one would create
  production data (forbidden by this task's data-safety rules).
* Not reported as passing merely because the code exists.
* The release worktree's unit sweep is green, including the mapping/calculation suites, and
  the deployed backend exposes the mapping/processing surfaces (570 OpenAPI paths,
  anonymous 401).
* No emission factor was read, modified or inserted; no calculation was fabricated; the
  emission-factor database was not touched.

## 11. Blocked-job customer visibility

**Result: `UNVERIFIABLE` (interactive) — partial supporting evidence PASS.**

| Requirement | Status | Evidence |
| --- | --- | --- |
| Blocked item visible to the customer | UNVERIFIABLE (interactive) | no session; **deployed bundle contains `manual_review_reason` and the blocked-card text ` - awaiting manual review.`** |
| Blocked state counts appropriately in the processing view | UNVERIFIABLE | the deployed bundle contains the processing view; not exercised |
| `manual_review_reason` (or equivalent) visible | UNVERIFIABLE (interactive) | marker present in the deployed bundle (partial evidence) |
| Normal completed items remain correct | UNVERIFIABLE | not exercised |
| Tenant isolation for blocked items | Partially verified | anonymous access → **401** (§15); the cross-tenant case needs two sessions → UNVERIFIABLE |
| No manufactured blocked production job | **Respected** | no production job was created or modified |

## 12. Report lifecycle (S6) acceptance

**Result: `UNVERIFIABLE` (interactive) — partial supporting evidence PASS.**

| Requirement | Status | Evidence |
| --- | --- | --- |
| Report state | UNVERIFIABLE | no authenticated report was opened |
| Applicable allowed actions | UNVERIFIABLE | deployed bundle contains the lifecycle strings and `calculated_emissions_kg_co2e` |
| Version/lifecycle presentation | UNVERIFIABLE | same |
| Locked / no-action behaviour | UNVERIFIABLE | deployed strings `Final and locked. Finalised reports are immutable.` and `No action is available to you on this version.` present |
| Authorization | Partially verified | `/api/v3/reports` → **401**, `/api/v3/reports/types` → **401** (§15) |
| No report modified to create a test state | **Respected** | no report created/modified/approved/finalised |

## 13. Consultant Client parity

**Result: `UNVERIFIABLE — AUTHENTICATED SESSION REQUIRED`** for the interactive surface
check; the code-level position is unchanged from Step 2C/closure.

* The deployed backend exposes the consultant-authorised shared surfaces
  (`/api/v3/processing/*` and `/api/v3/consultants/clients/{client_id}/reports` are in the
  OpenAPI path list); all are authorization-protected (anonymous 401).
* The deployed frontend contains the shared extraction/processing surface used by the
  consultant item page, so extraction/pipeline parity is shared by construction.
* **The previously documented CSV/XLSX preview parity gap for the consultant item page
  remains** (the POD-3 preview lives in the customer/ops workbench viewer; the consultant
  item page presents the source document through its own view). Recorded accurately and
  **not fixed** in this task.
* No new consultant functionality was invented; no consultant architecture was changed.

## 14. F-07 CSS result

**Result: `UNVERIFIABLE — AUTHENTICATED BROWSER SESSION REQUIRED`.**

* Browser capability is present (Chrome 152 headless + harness Playwright, §7), so this is
  **not** a tooling limitation.
* The F-07 page (report metadata/detail) requires an authenticated session; without an
  authorised production account the page cannot be loaded, therefore the reported
  collapse/vertical-rendering behaviour could **not** be reproduced or refuted in the
  current production build.
* No source change was made (nothing speculative), in line with §2 of this task.
* Exact remaining requirement: load the affected report page in production with an
  authorised account, capture the rendered evidence (page, element, computed layout), and
  close F-07 as PASS or FAIL in the follow-up acceptance run.

## 15. Tenant-isolation result

| Check | Result |
| --- | --- |
| Anonymous access to `/api/v3/documents` (no token) | **401** — rejected |
| Anonymous access with an arbitrary `organization_id` | **401** — rejected |
| Anonymous access to `/api/v3/reports`, `/api/v3/reports/types` | **401** — rejected |
| Anonymous access to the Step 2 endpoints (`/api/generate-enhanced-report`, `/api/generate-sustainability-report`, `/api/upload-pdf`) | **401** — rejected |
| Staff-only surface `/api/v3/ops/reporting/platform` anonymous | **401** — rejected |
| Authenticated own-organisation access | **UNVERIFIABLE in production** (no session). Verified in the **local** environment during closure: `GET /api/v3/documents?organization_id=<own org>` → **200** |
| Authenticated cross-organisation access denial | **UNVERIFIABLE in production** (needs two sessions). Verified in the **local** environment during closure: request for another organisation → **403** |
| Organisation enumeration / real customer data access | **Not performed** (deliberately) |
| Records modified | **None** |

## 16. Production error smoke

| Check | Result |
| --- | --- |
| `/health`, `/` | 200, 200 — no errors |
| `/openapi.json` | 200 |
| POST smokes on protected endpoints | 401 ×3 (authorization, expected) — **not** failures |
| `/api/v3/documents` via POST | 405 (method not allowed — correct for a GET-only route) |
| `/api/v3/documents` via GET (anonymous) | 401 (authorization, expected) |
| Pre-existing report route with an empty body | 422 (validation, expected) |
| 5xx observed | **none** |
| Real-browser (Chrome headless) DOM smoke, `https://carbontally.co.uk/` | DOM 33,009 bytes, `#root` present, **0** `Uncaught`/`SyntaxError`/`TypeError` lines on Chrome stderr |
| Real-browser DOM smoke, `https://carbontally.co.uk/login` | DOM 5,451 bytes, `#root` present, **0** JS error lines |
| Public routes `/`, `/pricing`, `/login` | 200, 200, 200 |
| Browser console/network errors on authenticated pages | **UNVERIFIABLE** — requires a session |
| Extraction failures | **UNVERIFIABLE** — no authenticated job was run |

---

## 17. Final acceptance matrix

| Acceptance item | Result | Evidence | Production verified |
| --- | --- | --- | --- |
| Frontend deployment identity | **PASS** | live index → `main.9febc8f0.js` + `main.a66f5596.css`; deployed bundle carries POD-3 (`structured-preview`, `ct-wb-viewer__data` in JS **and** CSS), WS-H (`manual_review_reason`, ` - awaiting manual review.`) and S6 lifecycle markers; old `main.1e761f98.js` no longer referenced (§3, §5) | yes |
| Backend deployment identity | **PASS** | `/health` 200 (db+pool connected), `/` 200, OpenAPI **570 paths** incl. both POD-5 aliases and `/api/upload-pdf`; `rndr-id` present (§6) | yes |
| CSV upload | **UNVERIFIABLE** | no authenticated production session (§7) | no |
| CSV preview | **UNVERIFIABLE** | requires a session; the preview component is confirmed present in the deployed bundle | no |
| CSV extraction | **UNVERIFIABLE** | requires a session; fixture parity (`0.00 → 1.00`) proven in release code/tests only | no |
| XLSX upload | **UNVERIFIABLE** | no authenticated production session | no |
| XLSX preview | **UNVERIFIABLE** | requires a session | no |
| XLSX extraction | **UNVERIFIABLE** | requires a session; sheet-scan / no-phantom-line behaviour proven in code tests | no |
| Processing → EF continuity | **UNVERIFIABLE** | would create production data; deliberately not executed | no |
| Blocked-job visibility | **UNVERIFIABLE** (partial evidence PASS) | deployed bundle contains the blocked reason and card text; no production job exercised | no |
| Report lifecycle | **UNVERIFIABLE** (partial evidence PASS) | lifecycle strings + `calculated_emissions_kg_co2e` present in the deployed bundle; `/api/v3/reports` anonymous 401 | no |
| Consultant Client parity | **UNVERIFIABLE** | consultant-authorised shared API surfaces present in the deployed OpenAPI; interactive check needs a session; documented preview gap remains | no |
| F-07 CSS | **UNVERIFIABLE** | browser available, **production session required** | no |
| Tenant isolation | **PASS (anonymous boundary)** / **UNVERIFIABLE (authenticated cross-tenant)** | all anonymous probes → 401/405/422, never 200 and never 5xx; local closure run recorded 200 own-org / 403 cross-org | partial |
| Production error smoke | **PASS** | no 5xx anywhere; real-browser DOM smoke of `/` and `/login` with **0** JS error lines; public routes 200/200/200 | yes |

## 18. F-01 … F-12 reconciliation

Reconciled against `P8-STEP2A-FUNCTIONAL-RECOVERY-AUDIT-001`,
`P8-STEP2-FUNCTIONAL-REMEDIATION-COMPLETE-001`,
`P8-STEP2C-FUNCTIONAL-REMEDIATION-COMPLETE-002` and `P8-STEP2-FINAL-CLOSURE-004`.

| ID | Previous status | Current **production** status | Evidence | Remaining limitation |
| --- | --- | --- | --- | --- |
| F-01 Batch Upload | **DEFERRED** | **DEFERRED** (unchanged) | no decision exists; not implemented | **`F-01 Batch Upload = DEFERRED`** — preserved |
| F-02 CSV/XLSX structured ingestion | Fixed, tested | Backend live; **production behaviour UNVERIFIED** | fixture parity `0.00 → 1.00` in release code; deployed backend exposes the pipeline; no authenticated upload run | authenticated end-to-end acceptance |
| F-03 CSV/XLSX workspace preview | Fixed, tested | **Deployed** (markers in the production bundle); **rendering UNVERIFIED** | `structured-preview` + `ct-wb-viewer__data` in deployed JS/CSS | UI acceptance with a session |
| F-04 Legacy manual-review queue | Adapter added | **Deployed** (`/api/upload-pdf` present, anonymous 401) | OpenAPI 570 paths | authenticated retry/manual-review check |
| F-05 AI fan-out plan unconsumed | Consumed under hard limits | **Deployed in code**; not exercised | POD-1 tests (7) green | live provider/pilot exercise |
| F-06 P1 global enablement risk | Controlled rollout | **Deployed; effective mode remains `shadow`** (no allowlist configured) | POD-4 tests (9) | enabling a pilot is a PO action |
| F-07 Report page CSS collapse | Unverified | **UNVERIFIED (production session required)** | browser available; no account | authenticated CSS/layout audit |
| F-08 Retired report endpoints 404 | Compatibility layer | **Production-verified** — both aliases present, answering 401 anonymously (previously 404) | live OpenAPI + probes | `AUDITOR_EXCEL` export remains unimplemented by design |
| F-09 Legacy `from main import` sites | 0 remain | **Deployed** | legacy-imports tests (5) green | none |
| F-10 Queue/item state consistency | Green | **Deployed in code**; interactive state not exercised | `test_step2_remediation.py` green | authenticated queue-state check |
| F-11 Blocked-job visibility | Green (Step 2) | **Deployed** (markers present); **interactive UNVERIFIED** | `manual_review_reason`, ` - awaiting manual review.` in the deployed bundle | authenticated blocked-job walkthrough |
| F-12 Partial extraction persistence | Green | **Deployed in code** | `test_step2_remediation.py` green | authenticated extraction acceptance |

## 19. P1 acceptance

| P1 aspect | Code exists | Deployed | Controlled-enabled | Real customer behaviour verified |
| --- | --- | --- | --- | --- |
| P1-D1 extraction-fidelity hook | Yes | **Yes** (backend live) | Effective mode `shadow` (no allowlist configured) | **No** — needs a pilot/allowlist or an authenticated run |
| Row detection / candidate lines / coverage | Yes | Yes | `shadow` = measured, not customer-visible | No |
| Multi-line extraction (PDF) | Yes | Yes | `shadow` | No |
| Multi-line extraction (IMAGE, WS-B B3) | Yes | Yes | `shadow` | No |
| Document-level adjudication (non-positional merging) | Yes | Yes | `shadow` / POD-1 path | No |
| Bounded AI fan-out (POD-1) | Yes | Yes (code) | Plan-gated; not enabled by any env | No — live provider call counts unobserved |
| Block reason | Yes | Yes (deployed bundle exposes the reason to the customer) | n/a | No (interactive) |
| Provenance (`source_row`, coverage, `ai_fanout`, `rollout`) | Yes | Yes | n/a | No (no authenticated job) |
| Controlled rollout mechanism | Yes | Yes | **Default `shadow`** — nothing enabled | No |

P1 is **not** claimed operational in production on the basis of code presence: the
implementation and tests are green and the code is deployed, but the feature is deliberately
**not enabled** (fail-safe default) and no real customer behaviour was observed.

## 20. Git ancestry verification

All 17 expected commits verified **IN-ANCESTRY** of `HEAD` (`git merge-base --is-ancestor`,
read-only), with no commits after the expected release:

`0d21e46` ✓ `f5e07ed` ✓ `eb6a0c2` ✓ `5d143ac` ✓ `c8b8d81` ✓ `55be3d2` ✓ `7666fff` ✓
`3849f30` ✓ `a496a37` ✓ `b45721a` ✓ `9332569` ✓ `948917f` ✓ `e5746ed` ✓ `2f6e1d5` ✓
`6beb281` ✓ `503d186` ✓ `b2596ade` ✓

**No expected verified commit is absent → no STOP condition was triggered and no Git repair
is required.** No Git write of any kind was performed.

## 21. Test evidence

| Suite | Result |
| --- | --- |
| `tests/unit/services/test_retention.py` (POD-6 corrected test) | **4 passed, 0 failed** — retention test is **green** |
| `tests/unit/services/test_structured_file_parity.py` (POD-3) | 11 passed |
| `tests/unit/services/test_pod1_bounded_ai_fanout.py` (POD-1) | 7 passed |
| `tests/unit/services/test_p1_controlled_rollout.py` (POD-4) | 9 passed |
| `tests/unit/api/test_legacy_manual_review_adapter.py` (POD-2) | 4 passed |
| `tests/unit/api/test_legacy_report_compat.py` (POD-5) | 4 passed |
| `tests/unit/routes/test_step2_legacy_imports.py` | 5 passed |
| Full backend unit sweep (closure task, same SHA) | 0 failures |
| Frontend suite (closure task, same SHA) | 302 passed (30/31 suites; the 1 suite-load failure is the pre-existing `react-router/dom` resolution issue in `App.test.js`) |

Test execution in this task was read-only (no cache artefacts: run with
`-p no:cacheprovider`).

## 22. Evidence references

| Artefact | Reference |
| --- | --- |
| Live frontend index + asset references | `/tmp/e2_idx.html`, `/tmp/e2_hdr.txt` |
| Deployed frontend bundle / stylesheet | `/tmp/e4_main.js` (2,286,957 bytes), `/tmp/e4_main.css` (298,520 bytes) |
| Marker scan results | `/tmp/e5_scan.txt`, `/tmp/e7_wsh.txt` |
| Backend health / root / probes | `/tmp/e2_health.json`, `/tmp/e2_root.json`, `/tmp/e9_backend.txt`, `/tmp/e10_more.txt` |
| Live OpenAPI document | `/tmp/e8_oa.json` |
| Chrome headless DOM smokes | `/tmp/e17_dom.html`, `/tmp/e17_chrome_err.txt`, `/tmp/e17_smoke.txt` |
| Git baseline / ancestry | `/tmp/e1_git.txt` |
| Browser/credential capability survey | `/tmp/e13_browser.txt`, `/tmp/e15_harness.txt`, `/tmp/e16_creds.txt` |
| Retention test result | `/tmp/e11_ret.txt`, `/tmp/e12_ret_summary.txt` |

No screenshots of authenticated pages exist because no session could be established; no
screenshot is claimed. The Chrome DOM dumps above are the browser-level artefacts obtained.

---

## 23. Failures

**No production defect was found during this acceptance.** Nothing is classified FAIL: the
unmet items are unmet for **absence of credentials**, which is recorded as UNVERIFIABLE, not
as a defect.

Non-defect observations recorded for accuracy (no action taken in this task):

1. **No dedicated worker/queue health endpoint** in this backend build
   (`/health/detailed` and `/api/v3/ops/health` → 404; `/health` reports API, database and
   pool only). This is an **observability gap**, not a functional defect, and it is outside
   Step 2 scope. A future item with a new Task ID could add a worker/queue health surface.
2. **Old frontend assets remain fetchable** (`main.1e761f98.js` → 200) because Vercel
   retains previous deployments' immutable assets. The live index does **not** reference
   them, so this is expected platform behaviour and **not** evidence of the old build being
   served.
3. `/api/v3/documents` via POST → **405** — correct method-not-allowed response for a
   GET-only route, not a failure.

## 24. Unverifiable items (with the exact remaining requirement)

Every item below needs **one** thing: an authorised production account/session. Browser
tooling and backend availability are both confirmed (§7).

| # | Unverifiable item | Exact remaining requirement |
| --- | --- | --- |
| 1 | CSV upload → workspace → preview → extraction | authenticated production organisation session; upload `mock_uk_fuel_card_messy.csv`, `mock_uk_utility_bill.csv`, `mock_scope3.csv`; inspect preview, extracted fields and provenance |
| 2 | XLSX upload → workspace → sheet-aware preview → extraction | the above plus an available XLSX fixture |
| 3 | Processing → mapping → factor lookup → calculation continuity | authenticated session with an approved test organisation (creates test data — requires explicit authorisation of that write path) |
| 4 | Blocked-job visibility (interactive) | authenticated session; either an existing blocked job or authorisation to create one in an approved QA organisation |
| 5 | Report lifecycle (interactive) | authenticated session plus an existing report in an approved organisation |
| 6 | Consultant Client parity (interactive) | consultant-authorised session |
| 7 | F-07 CSS | authenticated session; load the report detail page and record the rendered layout/computed styles |
| 8 | Authenticated tenant isolation (own-org allow / cross-org deny) | two authenticated organisations in an approved test environment (local closure evidence: 200 own-org, 403 cross-org) |
| 9 | Browser console/network errors on authenticated pages | authenticated browser session |

## 25. Deferred items

| Item | Disposition |
| --- | --- |
| **F-01 Batch Upload** | **DEFERRED** (unchanged; no PO decision) |
| F-07 CSS report-page collapse | Deferred — authenticated audit required |
| Consultant CSV/XLSX preview parity | Deferred — product/UX decision |
| `AUDITOR_EXCEL` export | Deferred — product decision |
| P1 `enabled` pilot rollout | Deferred — PO configuration action |
| Worker/queue health endpoint (observability) | Deferred — would require a new task ID |
| Integration suites (destructive harness) | Deferred — needs a disposable clone |

---

## 26. Change-control proof

| Proof | Value |
| --- | --- |
| Source changes | **none** |
| Test changes | **none** |
| Migration / database changes | **none** (no SQL executed; no schema, RLS or retention change) |
| Configuration changes | **none** |
| Storage changes | **none** (no upload, no deletion) |
| Commits created | **none** |
| Pushes performed | **none** (release remote SHA unchanged at `b2596ade`) |
| Staged files | **none** |
| Worktree at end | contains only the **untracked** report file created by this task |
| Database writes by this task | **none** (no authenticated workflow executed) |
| Destructive operations | **none** |
| Protected dirty `~/carbon_tally` tree | untouched (HEAD `20b7a92`, branch `main`, dirty 298 before and after) |
| Credentials in this report | **none** |
| Step 3 | **not started**; no demo/investor data created; no Phase 9 work |

## 27. Final release SHA

`b2596adef94c2385814765b8f5d42ba2f54126d6` — verified equal to
`origin/p8-release-reconciled`, clean worktree, with all 17 Step 1/Step 2/Step 2C commits in
ancestry. Production frontend serves the build of this release (`main.9febc8f0.js`,
carrying Step 1/S6, Step 2C POD-3 and WS-H markers); production backend serves the Step 2
backend with the 570-path contract.

## 28. Final verdict

`STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`

**Deployment acceptance PASSES; authenticated functional acceptance is outstanding.**

* Final release SHA verified ✓
* Frontend production deployment verified (markers + real-browser DOM smoke) ✓
* Backend production deployment verified (`/health`, OpenAPI 570 paths, Step 2 endpoints) ✓
* Git completeness verified (all 17 commits in ancestry; nothing unbanked) ✓
* Retention test green (4 passed, 0 failed) ✓
* No 5xx, no JS errors on the public surface, and **no production defect found** ✓
* `F-01 Batch Upload = DEFERRED` preserved ✓
* Remaining gate: the **authenticated production acceptance set** (§8–§13, §14 F-07,
  authenticated tenant isolation), blocked solely by the absence of an authorised
  production/QA account — tooling (Chrome 152, Selenium, harness Playwright) and the
  environment are ready.

This is **not** `STEP 2 BLOCKED`: no critical production failure or regression exists; the
missing evidence is credential-gated, not quality-gated.

**To reach `STEP 2 COMPLETE — READY FOR STEP 3`, the PO needs to provide exactly one
thing:** an authorised production QA/demo account (or an approved disposable QA
organisation) for the acceptance agent, after which the §24 items can be executed and
recorded in a follow-up acceptance report. Any defect discovered then must be handled by a
**new uniquely identified task** (authorization → implementation → verification → report →
commit → push → deployment → acceptance).

**This acceptance task is complete with the writing of this report. STOP.**







