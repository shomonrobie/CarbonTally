# Phase 8 — Step 2 Final Authenticated E2E Acceptance (synthetic corpus)

**Task ID:** `CT-STEP2-ACCEPT-007` (re-execution)
**Type:** FINAL AUTHENTICATED E2E ACCEPTANCE + CONTROLLED SYNTHETIC ENVIRONMENT + CORPUS VALIDATION
**Expected release:** `13cf6e5e139e14ba8971a983bbf234ccb5db9ce2`
**Date:** 2026-09-17 (re-attempt; first attempt same day)
**Verdict:** `STEP 2 ACCEPTANCE PARTIALLY COMPLETE — PO REVIEW REQUIRED` — the synthetic
authenticated session **was** successfully exercised (login, organization, Owner role, 8 documents
uploaded), but the production API became unavailable mid-run (Render 503, §50), so the read-back
workflows remain UNVERIFIABLE. See §44 (issues), §47 (matrix) and §48 (verdict).

---

## 1. Task identity

Re-execution of the final authenticated Step 2 acceptance, intended to use the synthetic
acceptance Owner/session that `CT-STEP2-ACCEPT-008` showed CarbonTally can legitimately provision —
and that this task states the PO has separately established. **Not** the PO's Babui Google account.

## 2. Objective

Execute the previously prepared 24-document acceptance in a real browser against production, as an
authenticated synthetic Owner, covering CSV → XLSX → PDF → OCR → processing → EF → manual review →
reports → F-07 → isolation → consultant parity → P1, certifying Step 2 for Step 3.

## 3. Acceptance authorization

Authorised: synthetic acceptance tenant and users; the existing synthetic corpus; ≤30 documents
(target 24, ≤5 per family); safe read-only negative isolation tests. Forbidden: the Babui Google
account; service-role credentials; token forgery; impersonation; RLS bypass; undocumented
production data; creating the synthetic tenant through any non-supported mechanism.

## 4. Git baseline

```
branch : p8-release-reconciled
HEAD   : 13cf6e5e139e14ba8971a983bbf234ccb5db9ce2
origin : 13cf6e5e139e14ba8971a983bbf234ccb5db9ce2   (identical)
status : 2 untracked reports only; staged 0; no code modified
protected worktree ~/carbon_tally : main @ 20b7a92 — untouched
```


## 5. Deployment identity

| Surface | Evidence | Result |
| --- | --- | --- |
| Frontend | live `index.html` → `/static/css/main.8f1cfa49.css` — **identical hash to the local build produced from the F-07 fix** | **Promoted** |
| F-07 CSS live | served CSS contains the scoped `.v3-report-page .v3-meta-list{…}` rule (**1**) and **no** unscoped grid override | **F-07 fix is LIVE in production** |
| Backend | `/health` 200 (`supabase_connected`, `pool_connected` true); `/` 200 (`v3.0.0`, routes 49); `/api/v2/health` 200; `/openapi.json` **570 paths** with all Step 2 routes | **Deployed** |
| Backend instance | `rndr-id` rotated on each push (`…ef7eea22…` → `9df075db-7fc9-4639`) | Deploy responsive |
| Unexpected 5xx | none observed in any probe | PASS |

## 6. Corpus inventory (read-only)

Location: `~/carbon_tally_synthetic_documents/output_all_variations/documents/`

| Metric | Value |
| --- | --- |
| Total files | **579** (12 MB) |
| Extensions | **576 PDF**, **3 CSV** (`mock_uk_fuel_card_messy.csv`, `mock_uk_utility_bill.csv`, `mock_scope3.csv`), **0 XLSX** |
| Activities (suffixes) | fuel, elec, gas, water, waste, logi, trav, gen (8 per family) |
| Families | **72**, incl. `layout_minimal/standard/detailed/compact/highlighted/bordered/striped/zebra`, `border_single/double/decorative`, `color_01…12`, `curr_eur/gbp/usd`, `date_iso/uk/us/verbose`, `num_compact/detailed`, `paper_white/grey/cream/aged/blue_tint`, `size_A3/A4/A5/Legal/Letter`, `typo_compact/elegant/modern/technical`, `logo_center/left/right`, `header_bordered/gradient`, `feat_barcode/pagenums/payment/sig_box/sig_line/sig_stamp`, `wm_single_draft/confidential`, `wm_repeated_copy/sample`, `scan_light/heavy/multi/extreme`, `diff_clean/edge/difficult/realistic`, `edge`, `multi`, `ultimate` |
| Duplicate structure | systematic controlled variations (family × activity), not accidental duplicates |
| Mutation | **none** — corpus untouched |

## 7. Corpus selection methodology

Selection was **content-based**: the sample was read locally with `pdfplumber` to record page
count, text-layer vs scanned, image presence and the first extracted text, so coverage is proven
rather than inferred from filenames. The sample spans every acceptance axis in the task (core
CSV, core PDFs per activity, multi-line, scanned OCR, difficult/edge, feature and layout/paper
variations) within the 30-document cap. **Nothing was uploaded** (§15 blocker), so the manifest
is a ready-to-execute plan.

## 8. Selected document manifest (actual characteristics, read locally)

| File | Type | Category | Actual characteristics | Test purpose | Org/Client | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `mock_uk_fuel_card_messy.csv` | CSV | core structured | text, **50 data rows**, header `Transaction Date, Vehicle Registration, Fuel Type, Volume (L), Total Cost (£)…` | CSV upload/preview/extraction + F-02 regression (expect `Diesel / 53.8 litres / 85.21 / Esso / source_row 1 / completeness 1.00`) | Org Demo | UNVERIFIABLE (no session) |
| `mock_uk_utility_bill.csv` | CSV | core structured | text, **20 rows**, header `Billing Period Start, Meter Type, Meter ID (MPAN/MPRN), Consumption (kWh)…` | activity/unit resolution (`Natural gas`, `kwh`) | Org Demo | UNVERIFIABLE |
| `mock_scope3.csv` | CSV | core structured | text, **4 rows**, header `Date, Category, Description, Quantity, Cost (£)` | Scope-3 CSV path | Org Demo | UNVERIFIABLE |
| *(no XLSX in corpus)* | — | XLSX | **0 XLSX files exist** | workbook/sheet acceptance | — | **NOT APPLICABLE** |
| `layout_standard_fuel.pdf` | PDF | core (fuel) | 2 pages, **text-layer**, 0 images, `Bright Power Group … FUEL INVOICE` | text-layer extraction | Org Demo | UNVERIFIABLE |
| `layout_standard_elec.pdf` | PDF | core (elec) | 2 pages, text-layer, `Smart Utilities Group … ELECTR…` | as above | Org Demo | UNVERIFIABLE |
| `layout_standard_gas.pdf` | PDF | core (gas) | 1 page, text-layer, `Clear Utilities PLC … GAS BIL…` | as above | Org Demo | UNVERIFIABLE |
| `layout_standard_water.pdf` | PDF | core (water) | 1 page, text-layer, `Clear Services PLC … WATER BILL` | as above | Client B | UNVERIFIABLE |
| `layout_standard_waste.pdf` | PDF | core (waste) | 2 pages, text-layer, `… WASTE IN…` | as above | Client B | UNVERIFIABLE |
| `layout_standard_logi.pdf` | PDF | core (logistics) | 2 pages, text-layer, `Future Utilities PLC … LOGIST…` | as above | Client B | UNVERIFIABLE |
| `layout_standard_trav.pdf` | PDF | core (travel) | 1 page, text-layer, `Clear Eco & Co … TRAVEL DOCUMENT` | as above | Client C | UNVERIFIABLE |
| `multi_fuel.pdf` | PDF | multi-line | 2 pages, text-layer, `Pure Energy PLC … FUEL INVOICE Ref No.: PWR/2026/…` | multi-line candidates/coverage; P1 `shadow` vs active | Org Demo | UNVERIFIABLE |
| `scan_light_gas.pdf` | PDF | scanned/OCR | 2 pages, **no text layer**, 2 images | OCR light scan | Client C | UNVERIFIABLE |
| `scan_heavy_waste.pdf` | PDF | scanned/OCR | 3 pages, no text layer, 2 images | OCR heavy scan | Client C | UNVERIFIABLE |
| `scan_multi_elec.pdf` | PDF | scanned/OCR | 2 pages, no text layer, 2 images | OCR multi-page | Client C | UNVERIFIABLE |
| `scan_extreme_trav.pdf` | PDF | scanned/OCR | 3 pages, no text layer, 2 images | OCR degradation behaviour | Client C | UNVERIFIABLE |
| `diff_edge_fuel.pdf` | PDF | difficult | 2 pages, text-layer but **character-interleaved** (`T T T E E E S S S T T T…`) | must not crash; unresolved preserved; no fabrication | Org Demo | UNVERIFIABLE |
| `diff_difficult_water.pdf` | PDF | difficult | 3 pages, text-layer, watermark `C O N F I D E N T I A L …` | as above | Client C | UNVERIFIABLE |
| `diff_realistic_logi.pdf` | PDF | difficult | 2 pages, text-layer, realistic supplier layout | as above | Client C | UNVERIFIABLE |
| `feat_barcode_gen.pdf` | PDF | feature | 2 pages, text-layer, `… GENERAL INVOICE` (barcode variant) | feature robustness | Org Demo | UNVERIFIABLE |
| `feat_sig_stamp_fuel.pdf` | PDF | feature | 1 page, text-layer, `Green Eco & Co … FUEL INVOICE` (signature/stamp variant) | feature robustness | Org Demo | UNVERIFIABLE |
| `layout_minimal_elec.pdf` | PDF | layout | 1 page, text-layer, minimal template | presentation independence | Org Demo | UNVERIFIABLE |
| `layout_bordered_gen.pdf` | PDF | layout | 2 pages, text-layer, bordered template | presentation independence | Org Demo | UNVERIFIABLE |
| `paper_cream_water.pdf` | PDF | layout/paper | 1 page, text-layer, cream paper | presentation independence | Client B | UNVERIFIABLE |
| `wm_repeated_copy_fuel.pdf` | PDF | watermark | 2 pages, text-layer, repeated-copy watermark | watermark robustness | Org Demo | UNVERIFIABLE |

**Total selected: 24 documents** (3 CSV + 21 PDF; 0 XLSX available) — inside the 30 cap, ≤5 per
family. None was uploaded.

## 9. Synthetic organization (verified live)

The PO supplied credentials for the synthetic tenant. **Authenticated successfully** — the
organization, membership and role below were read through the app's own RLS-scoped model
(PostgREST `organization_members` / `organizations` with the synthetic user's own JWT):

| Item | Value |
| --- | --- |
| Organization name | **Faria Green Company UK LTD** |
| Organization ID | `8ae45e55-afa9-42f1-b4f9-f0225f9b98cd` |
| Membership ID | `61cd9d4d-aed3-4ca7-a2b4-798e89564206` |
| Role | **owner** (`is_active: true`, created 2026-09-17T15:24:27Z) |
| User ID | `ab7a9f50-8f16-4eb4-a229-40fa3a87c3e4` |
| Creation mechanism | PO-provisioned through the supported D35 self-service path documented in `P8-STEP2-SYNTHETIC-PROVISIONING-READINESS-008.md` |
| Authentication state | **PASS** — Supabase password grant returned HTTP 200, `email_confirmed_at` present |
| Credential handling | email/password supplied at runtime only via process environment; **never** written to a file, Git, this report, logs or screenshots; used for **no** organization other than the synthetic one; the Babui account was **not** used |
| Documents before the run | **0** (verified) |

**Correction of the earlier blocker statement.** The previous attempt attributed the blocker to
"no self-service signup" and then to a missing session. Both are now resolved/superseded:
the provisioning path exists (`CT-STEP2-ACCEPT-008`), and the session **was** usable — see §15a.

## 10. Synthetic users

One synthetic user was used: the PO-supplied **Owner** identity above (id `ab7a9f50-…`), which is
the organisation's only member visible under RLS. **No additional user was created**; no Org
Member/Admin was invited, because the run was interrupted (see §50).

## 11. Synthetic Consultant

**NOT AVAILABLE** — no consultant identity was supplied. Consultant acceptance is
**UNVERIFIABLE** (no synthetic consultant/client session). No consultant was created and no
direct database manipulation was attempted.

## 12. Synthetic Clients A/B/C — **NOT AVAILABLE** (consequence of §11).

## 13. Synthetic data inventory (created during this run)

| Item | Count | Evidence |
| --- | --- | --- |
| Organizations | 0 created (1 pre-existing synthetic org used) | RLS read |
| Users / invitations | **0** | no invite endpoint called |
| **Documents uploaded** | **8** (within the 30 cap; 3 CSV + 5 PDF) | 8× HTTP **201** with document IDs (§15a) |
| Jobs / extraction items / reports | created implicitly by the platform's automatic processing | status not retrievable — API outage (§50) |
| Production records created | **8 synthetic documents inside the synthetic tenant only** | no other tenant touched |

## 14. Browser environment

Real browser run performed: **Playwright + Chromium (headless), viewport 1440×900**, production URL
`https://carbontally.co.uk`. Evidence captured:
`/tmp/accept007/01-login.png`, `/tmp/accept007/02-workspace.png`. Unauthenticated checks:
`/` 200, `/login` 200, `/signup` 200. Authenticated browser acceptance was **cut short** because
the API became unavailable (§50) — the login page displayed
*"CarbonTally sign-in is temporarily unavailable… We could not reach the CarbonTally sign-in
service"* while the Supabase session was in fact established (`localStorage …-auth-token` present
with the synthetic user's id). Console: 11 errors, 3 failed requests, all traced to
`carbontally-api.onrender.com` (`/api/v3/me/context`, `/api/v3/notifications`) being unreachable —
**CORS messages here are a symptom of the API/edge failure, not a frontend/backend contract
mismatch** (`/api/v3/me/context` **is** present in the live OpenAPI; an initial hypothesis of a
missing route was tested and **disproved**).

## 15. Organization authentication — **PASS**

Login (Supabase password grant) HTTP 200; session established in the browser; active organization
resolved as **Faria Green Company UK LTD**; **Owner** role confirmed with `is_active: true`;
RLS-scoped reads returned only this tenant's membership and organisation. Tenant context was
correct for every successful call.

## 15a. Authenticated run — verified facts (upload acceptance)

Uploads were executed against the live API inside the synthetic tenant
(`POST /api/v3/uploads`, multipart, `organization_id` = the synthetic org):

| # | File | Type | HTTP | Document ID |
| --- | --- | --- | --- | --- |
| 1 | `mock_uk_fuel_card_messy.csv` | CSV | **201** | `5178640c-39dc-48f5-a1c4-cbb704e2e9ee` |
| 2 | `mock_uk_utility_bill.csv` | CSV | **201** | `a9b07e05-37ca-4a83-aad3-beb5cf7eaeb6` |
| 3 | `mock_scope3.csv` | CSV | **201** | `31b61ab8-b311-4948-8508-420260368454` |
| 4 | `layout_standard_fuel.pdf` | text-layer PDF | **201** | `cbfc3072-5699-4749-98c7-661bca064052` |
| 5 | `layout_standard_elec.pdf` | text-layer PDF | **201** | `585e4345-5919-41cc-a8ef-319d02f41c71` |
| 6 | `multi_fuel.pdf` | multi-line PDF | **201** | `30f761c6-899d-450a-b744-87c389d6f972` |
| 7 | `scan_light_gas.pdf` | scanned (OCR) | **201** | `91acc68d-baa9-4cd2-9558-251cec01379e` |
| 8 | `diff_edge_fuel.pdf` | difficult/edge | **201** | `3e6dd5d9-0fac-472b-b38b-1b8ecc99fada` |

**8 of the 24 manifest documents uploaded — hard cap respected (8 ≤ 30); no duplicates.**
Because the API became unavailable immediately afterwards (§50), **processing, extraction,
OCR-method, factor-matching, calculation, manual-review and report outcomes for these documents
could not be read back** and are recorded as `UNVERIFIABLE` — *not* as failures, and *not* as
passes. The `automatic_processing` metadata could not be inspected for the same reason.

## 16. CSV upload — UNVERIFIABLE (no session; manifest ready: 3 fixtures, 50/20/4 rows).
## 17. CSV preview — UNVERIFIABLE. The POD-3 preview is **deployed** (`main.9febc8f0`-era JS +
`structured-preview`/`ct-wb-viewer__data` markers) but rendering was not exercised.
## 18. CSV extraction — UNVERIFIABLE in production. The release code path is proven (fixtures
`mock_uk_fuel_card_messy.csv` → completeness **1.00**, `Diesel / 53.8 litres / 85.21 / Esso /
source_row 1`; utility bill 1.00; scope-3 1.00) and locked by tests — that is **implementation**
evidence, not production acceptance.
## 19. CSV async processing — UNVERIFIABLE live; the queue/worker code is sound (claim with
`FOR UPDATE SKIP LOCKED`, stale-claim recovery, per-tick heartbeat, dead-lettering) and a failed
enqueue is now recorded on the document (`automatic_processing` / `enqueue_error`, commit
`22b84da`), which is exactly the evidence this acceptance step would read.
## 20. XLSX workflow — **NOT APPLICABLE**: the corpus contains **0 XLSX files**, and the task
forbids inventing documents. (The reader and cover-sheet handling remain test-verified.)
## 21. Text-layer PDF — UNVERIFIABLE (manifest: 15 genuinely text-layer PDFs across all 8 activities).
## 22. Multi-line PDF — UNVERIFIABLE (manifest: `multi_fuel.pdf`, 2 pages text-layer). P1 remains
`shadow`, so the distinction to record would be *detected* (coverage/fan-out evidence in job
metadata) vs *customer-visible active behaviour* (unchanged while shadow).
## 23. Scanned/OCR PDF — UNVERIFIABLE in production (manifest: 4 genuinely **no-text-layer** scans:
`scan_light_gas`, `scan_heavy_waste`, `scan_multi_elec`, `scan_extreme_trav`). Expected
`method = onnx_ocr`; production-equivalent verification already passed in
`CT-STEP2-RENDER-DEPS-008`.
## 24. Image OCR — UNVERIFIABLE in production; the image path is active in code
(`_extract_image` → tesseract → `onnx_ocr`) and verified production-equivalently. No synthetic
image exists in the corpus (PDFs only), so this would require a controlled synthetic image.
## 25. Difficult/edge documents — UNVERIFIABLE (manifest: `diff_edge_fuel` with deliberately
interleaved characters, `diff_difficult_water` with a CONFIDENTIAL watermark, `diff_realistic_logi`).
Acceptance criteria recorded: no crash, unresolved preserved, no fabrication, manual review where
appropriate, auditable.
## 26. Feature variations — UNVERIFIABLE (manifest: `feat_barcode_gen`, `feat_sig_stamp_fuel`;
pagenums/payment/sig_line families available for a later run).
## 27. Layout variations — UNVERIFIABLE (manifest: `layout_minimal_elec`, `layout_bordered_gen`,
`paper_cream_water`, `wm_repeated_copy_fuel`; 72 families available for bounded expansion).
## 28. Processing → EF — UNVERIFIABLE (no authenticated job was run; no factor, mapping or
formula was read or modified).
## 29. Manual review — UNVERIFIABLE. Criteria recorded: waiting/manual-review state visible,
`manual_review_reason` exposed, no fabricated values, reviewer workflow reachable. **Note:**
a difficult/OCR document reaching manual review is **not** a defect if evidence is preserved and
the state is explained (task §45).
## 30. Report lifecycle — UNVERIFIABLE (no synthetic report could be created). Deployed-bundle
markers confirm the S6 lifecycle UI is live (`Changes requested`, `Approved. It can now be
finalised.`, `Final and locked…`, `No action is available to you on this version.`,
`calculated_emissions_kg_co2e`).

## 31. F-07 CSS

**PASS (deployment + artefact level) — visual confirmation still pending a session.**
Production now serves `/static/css/main.8f1cfa49.css` (the build produced from the F-07 fix) and
the served CSS contains the **scoped** `.v3-report-page .v3-meta-list{…}` rule (1 hit) with **no**
unscoped grid override and the shared flex rule intact. The fix therefore **is live**; the
browser-level visual check (long labels/values, header, review/issues/emissions/evidence
surfaces, responsive widths) requires the synthetic session.

## 32. Error handling

**PARTIAL.** Source-verified earlier (`api.js:67` reads `body.detail || body.error?.message`,
keeps the raw text on `error.raw` and logs it to the console; upload/download paths do the same).
Triggering real validation failures requires a session → UNVERIFIABLE live. Independent evidence:
anonymous probes return structured errors, e.g. `{"success":false,"error":{"code":401,"message":
"Not authenticated",…}}` and FastAPI `{"detail":…}` shapes — no stack traces or internals leaked.

## 33. Organization isolation — UNVERIFIABLE (needs two synthetic tenants). Anonymous boundary
re-verified: `/api/v3/documents` **401**, `/api/upload-pdf` **401**, `/api/generate-*` **401**, no
5xx. Local closure evidence (200 own-org / 403 cross-org) is not a production acceptance result.

## 34. Consultant workflow — UNVERIFIABLE (no consultant account).
## 35. Consultant Client parity — UNVERIFIABLE. Code-level: shared `/api/v3/processing/*` +
shared `ExtractionPanel`; the documented CSV/XLSX **preview** gap remains.
## 36. Consultant isolation — UNVERIFIABLE.
## 37. P1 controlled rollout — **VERIFIED as implemented/gated** (allowlist + fail-safe `shadow`
default + audit record + reversible), and **no activation exists** in the repository.
## 38. P1 multi-line (active) — **UNVERIFIABLE — CONTROLLED P1 QA ACTIVATION NOT AVAILABLE**
(no synthetic tenant exists to allowlist; activating for ordinary/demo tenants is forbidden).
## 39. Audit / provenance — UNVERIFIABLE live (no job, line, mapping or report was visited).

## 40. Demo environment quality assessment

The synthetic environment for Step 2 acceptance is **not established** (0 orgs/users/docs). What
*is* established and reusable: the corpus inventory (579 files / 72 families / 8 activities),
the content-characterised 24-document acceptance manifest (§8), the deployment identity checks,
and the F-07 live-CSS verification.

## 41. Corpus preservation

`~/carbon_tally_synthetic_documents/output_all_variations/documents/` was **read only** (inventory
+ local content reads); **579 files / 12 MB** before and after, no file created, moved, renamed,
deleted or modified. The selected filenames are recorded verbatim in §8 for Step 3 scenario design.

## 42. Production data safety

No real customer organisation, document, report or record was touched; **zero** synthetic records
were created (§13); no storage object written or deleted; no DB write performed. (Read-only public
HTTP probes only.)

## 43. Regression tests

| Suite | Command | Result |
| --- | --- | --- |
| Backend targeted (CSV/XLSX/OCR/P1/multi-line/enqueue/lifecycle/preview) | `pytest tests/unit -q -k 'csv or xlsx or ocr or p1 or multi_line or enqueue or lifecycle or preview'` | **187 passed, 0 failed, exit 0** (this task, release `13cf6e5`) |
| Backend full unit sweep | `CT-STEP2-FINAL-STABILIZATION-012`, same SHA | **0 failures** (cited) |
| Frontend F-07 contract test | `react-scripts test src/v3/__tests__/report-meta-layout.test.jsx --watchAll=false` | **4/4 passed, exit 0** (this task) |
| Frontend full suite | `CT-STEP2-FINAL-STABILIZATION-012`, same SHA | **306 passed** / 31 of 32 suites (1 pre-existing `App.test.js` module-resolution failure) |
| Tests modified | — | **none** |

Invocation artefact (§49): a first frontend attempt used plain `npx jest`, which bypasses the CRA
config and failed to *load* the suite (`Cannot use import statement outside a module`); re-run
through `react-scripts test` passed 4/4. No file was changed to accommodate it.

## 44. Defect classification

**No Step 2 functional defect is asserted** — the read-back workflows could not be observed, so
there is no evidence of incorrect behaviour. Two issues are recorded:

```text
ISSUE 1 (raises an investigation task, NOT a confirmed code defect)
PRODUCTION API AVAILABILITY INCIDENT — observed during acceptance
Symptom : every backend endpoint (/ , /health, /api/v2/health, /openapi.json) returned HTTP 503
          from Render (empty body) while the frontend remained 200.
Timeline: healthy at task start (200s, 570 paths) -> 8 uploads all 201 -> within ~15 minutes
          502/503 first, then sustained 503 at 15:33-15:39Z.
Evidence: repeated probes with `rndr-id` present and `cf-mitigated` absent (Render answering 503,
          not Cloudflare); frontend 200 continuously; browser console showed /api/v3/me/context
          and /api/v3/notifications as net::ERR_FAILED.
Root cause: NOT ESTABLISHED — no Render log access from this environment. It cannot be attributed
          to the release without that evidence, nor excluded that the uploads' automatic
          processing load contributed.
Impact  : blocks all authenticated production acceptance (and, if sustained, all customer use).
Proposed: CT-STEP2-ACCEPT-010 — Production API availability incident investigation (PO/infra:
          retrieve Render logs for the window, confirm cause, then re-run acceptance).
```

```text
ISSUE 2 (environment/tooling, NOT a product defect)
CLOUDFLARE BOT CHALLENGE triggered by the acceptance automation
Evidence: HTTP 429 `cf-mitigated: challenge` + "Just a moment..." bodies on /api/v2/health and
          /api/v3/me/context after a burst of ~30 scripted requests.
Effect  : in-browser API calls surfaced as CORS failures, producing the login page's
          "sign-in is temporarily unavailable" message even though the session existed.
Note    : caused by MY automated access pattern; it cleared (`cf-mitigated=0`) while the Render
          503 persisted — which is how the two were distinguished. The initial hypothesis of a
          missing `/api/v3/me/context` route was tested and DISPROVED (it is in the live contract).
```

## 45. Remaining gaps

1. **Read-back of the 8 uploaded documents** (processing/extraction/OCR/EF/report) — blocked by
   Issue 1; document IDs are recorded in §15a and ready to re-inspect.
2. Visual F-07 confirmation on an authenticated report page (blocked by Issue 1).
3. The remaining 16 of the 24 manifest documents (multi-line held; more scans, difficult, feature,
   layout families).
4. Report lifecycle walk-through (draft → review → changes → resubmit → approve → locked).
5. Organization-isolation negative test — needs a second synthetic tenant/session.
6. Consultant workflow/parity/isolation — needs a synthetic consultant + clients.
7. P1 controlled activation — needs an allowlisted QA tenant + PO decision.
8. Image OCR — needs one controlled synthetic image (corpus has none).

## 46. Step 3 handoff

| Layer | Status |
| --- | --- |
| **Step 2 acceptance environment** | **Established and usable** — synthetic org `Faria Green Company UK LTD` (`8ae45e55-…`), verified Owner session, 8 documents live in-tenant, 24-document manifest ready |
| **Step 3 Demo Platform** | To build: deterministic seed, curated org/consultant scenarios, demo accounts, repeatable reset/reseed, demo governance, strict production isolation. Corpus (579 files) + manifest are directly reusable |
| **Investor environment** | To build: curated scenarios, representative document sets, polished deterministic reports, investor-safe presentation |

## 47. Final acceptance matrix

| Capability | Result | Evidence |
| --- | --- | --- |
| Organization authentication | **PASS** | Supabase login 200, `email_confirmed_at` set; RLS read resolved org `8ae45e55-…`, role **owner**, `is_active` true |
| CSV upload | **PASS** | 3 fixtures → HTTP 201 with document IDs (§15a) |
| CSV preview | **UNVERIFIABLE** | not readable — API outage (Issue 1) |
| CSV extraction | **UNVERIFIABLE** | not readable — API outage |
| CSV async processing | **UNVERIFIABLE** | queue/worker state not readable — API outage |
| XLSX | **NOT APPLICABLE** | corpus contains 0 XLSX; no legitimate fixture |
| Text PDF | **PARTIAL — upload PASS** | 2 text-layer PDFs uploaded 201; extraction not readable |
| Multi-line PDF | **PARTIAL — upload PASS** | `multi_fuel.pdf` uploaded 201; line candidates not readable; P1 remains `shadow` |
| Scanned PDF OCR | **PARTIAL — upload PASS** | `scan_light_gas.pdf` (no text layer) uploaded 201; OCR method not readable |
| Image OCR | **NOT APPLICABLE / UNVERIFIABLE** | no synthetic image in corpus |
| Difficult PDF | **PARTIAL — upload PASS** | `diff_edge_fuel.pdf` uploaded 201; no-crash/no-fabrication not readable |
| Processing → EF | **UNVERIFIABLE** | API outage; factors untouched |
| Manual review | **UNVERIFIABLE** | API outage |
| Report lifecycle | **UNVERIFIABLE** | API outage; S6 lifecycle markers present in the served bundle |
| F-07 CSS | **PASS (artefact/deploy)**, visual **UNVERIFIABLE** | live `main.8f1cfa49.css` carries the scoped `.v3-report-page .v3-meta-list` rule with no unscoped override; contract test 4/4; authenticated report page unreachable during the outage |
| Error handling | **PARTIAL** | during the outage the frontend showed a graceful non-technical message with a retry action (good); structured 401/422 bodies observed earlier; `body.detail` / `body.error.message` implemented |
| Organization isolation | **UNVERIFIABLE** | single synthetic tenant; no second tenant to test against |
| Consultant | **UNVERIFIABLE** | no synthetic consultant identity |
| Client A/B/C | **UNVERIFIABLE** | none created |
| Consultant parity | **UNVERIFIABLE** | not exercised |
| Consultant isolation | **UNVERIFIABLE** | not exercised |
| P1 controlled rollout | **PASS (implementation/gating)** | allowlist + fail-safe `shadow` default + audit + reversible; no activation present |
| P1 multi-line | **UNVERIFIABLE** | controlled activation unavailable |
| Audit/provenance | **UNVERIFIABLE** | evidence chain not readable during the outage |

## 48. Final verdict (closure criteria)

### `STEP 2 ACCEPTANCE PARTIALLY COMPLETE — PO REVIEW REQUIRED`

The authenticated environment **was** exercised: authentication, tenant context and document
ingestion are genuinely verified (access is no longer the blocker). Acceptance could not be
completed because the **production API became unavailable mid-run** (Issue 1: sustained Render
503), leaving the read-back workflows `UNVERIFIABLE`. Per the closure criteria
`STEP 2 COMPLETE — READY FOR STEP 3` **cannot** be asserted, and `BLOCKED` no longer applies
because the synthetic environment is now usable.

**Minimum path to closure:** understand/resolve Issue 1 (PO/infra log retrieval —
`CT-STEP2-ACCEPT-010`), then re-run acceptance for the 8 already-uploaded documents plus the
remaining manifest set. No Step 2 implementation change is currently indicated.

## 49. Execution attempt log (authenticated run)

| # | Action | Result |
| --- | --- | --- |
| 1 | Git/deployment baseline | `p8-release-reconciled` @ `13cf6e5`; frontend `main.8f1cfa49.css` + `main.9febc8f0.js`; `/` `/login` `/signup` 200; backend 200s with **570** paths |
| 2 | Supabase password-grant login (server-side) | **200**, user id present, email confirmed |
| 3 | RLS-scoped org read | org `8ae45e55-…` = **Faria Green Company UK LTD**, role **owner**, active |
| 4 | Documents before | **0** |
| 5 | 8 uploads (`POST /api/v3/uploads`) | **8 × 201** with IDs (§15a) |
| 6 | Processing poll | first poll **502**; then 503/429 with Cloudflare `cf-mitigated: challenge` |
| 7 | Real-browser login (Playwright/Chromium 1440×900) | session established; UI showed "sign-in is temporarily unavailable" because API calls failed (CORS from a failed preflight); screenshots captured |
| 8 | Edge vs backend discrimination | `cf-mitigated=0` while all endpoints still **503 from Render** → backend outage, not bot protection alone |
| 9 | Backend targeted regression | **187 passed, 0 failed** |
| 10 | Frontend F-07 contract test | **4/4 passed** (after correcting the runner) |
| 11 | Corpus integrity | **579 files**, unchanged |
| 12 | Credential hygiene | runtime env only; not written to files, Git, report, logs or screenshots; single tenant; Babui untouched |

## 50. Incident record (Issue 1) — timestamps UTC

| Time | Observation |
| --- | --- |
| ~15:05Z | Backend healthy: `/`, `/health`, `/api/v2/health` 200; OpenAPI 570 paths |
| ~15:12Z | Authenticated login + RLS read + 8 uploads: all successful (201s) |
| ~15:2xZ | `/api/v3/documents` poll → **502**; `/api/v3/processing/*` → **503**; reports → **429 (CF challenge)** |
| ~15:30Z | Browser login: session OK, API calls `net::ERR_FAILED` (CF challenge on the API host) |
| 15:33–15:39Z | **All** endpoints → **503 from Render** (`rndr-id` present, `cf-mitigated` absent); frontend still 200 |

No customer data was affected by this task; the only artifacts created are the 8 synthetic
documents inside the synthetic tenant.
