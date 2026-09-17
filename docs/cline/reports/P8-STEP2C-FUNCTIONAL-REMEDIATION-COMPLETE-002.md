# Phase 8 — Step 2C: Functional Remediation + PO Decision Resolution

**Task ID:** `CT-STEP2C-FUNCTIONAL-REMEDIATION-002`
**Branch:** `p8-release-reconciled`
**Starting tip:** `7666fffaadb7b2969291bc133defc7526bc46c67` (verified at start: local == remote, worktree clean)
**Code tip (last implementation/pushed code commit):** `b45721abfbb2c8c8286273cb962ccd6a82cd7787`
**Branch tip after this report commit:** `2f6e1d57ecfb435a8bb44dc304c628df6d7b2364`
(commit 7 of the workstream is this report itself, `2f6e1d5` — documentation only,
no code change; the remote SHA equals the local SHA at every commit)
**Commits added:** 6 (`3849f30`, `a496a37`, `9332569`, `948917f`, `e5746ed`, `b45721a`)
**Date:** 2026-09-17
**Verdict:** `STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`
(only outstanding step: Vercel frontend promotion + post-deploy frontend verification — see §19/§20)

---

## 1. Executive summary

All six Product Owner decisions (POD-1 … POD-6) were actioned. Five required
implementation and were implemented, tested and pushed:

| POD | PO decision | Outcome |
| --- | --- | --- |
| POD-1 | A — bounded automatic AI fan-out | **Implemented** — the P1 fan-out plan is now consumed under hard limits (§8) |
| POD-2 | C — thin manual-review compatibility adapter | **Implemented** — legacy auto-repair translates into the current V3 workflow (§9) |
| POD-3 | A — full CSV/XLSX V3 parity | **Implemented** — two root causes found and fixed + structured workspace preview (§10) |
| POD-4 | C — controlled P1 rollout | **Implemented** — tenant allowlist with fail-safe default (§11) |
| POD-5 | C — minimal report-endpoint compatibility | **Implemented** — both legacy paths aliased, tenant-isolated, deprecation-signalled (§12) |
| POD-6 | C — retention forensic audit only | **Forensic deliverable produced; no retention behaviour changed** (§13, §22) |

The single most consequential finding is POD-3: the PO's report ("Excel/CSV not
appearing in the workspace preview; data not extracted") was **reproduced twice
over** using the repository's own fixtures:

* `mock_uk_fuel_card_messy.csv` (50 rows) parsed to completeness **0.00** with
  `activity`/`quantity`/`unit` unresolved → the job could not pass the gate;
* `mock_uk_utility_bill.csv` (20 rows) lost `activity`;
* an XLSX whose first sheet is a cover page (common for supplier exports) yielded
  **no data at all**;
* and the workbench viewer deliberately answered *"Document preview is not
  available for this file type"* for CSV/XLSX/TSV.

After the fix, the same fixtures resolve to completeness **1.00** with no
unresolved fields, the cover-sheet workbook is parsed from its data sheet, and
CSV/XLSX render a bounded structured preview in the workspace.

Production status: the **backend** auto-deployed from the push (verified via the
live OpenAPI contract and `rndr-id`), so POD-1/POD-2/POD-4/POD-5 are live. The
**frontend** has not been promoted: production still serves
`main.1e761f98.js`, which provably lacks the POD-3 preview markers (§19).

---

## 2. PO decisions used

* **POD-1 A** — bounded automatic AI fan-out when deterministic/P1 extraction
  cannot establish sufficient document structure.
* **POD-2 C** — thin compatibility adapter from the legacy request path into the
  current V3 manual-review workflow (no queue resurrection).
* **POD-3 A** — full V3 parity with the intended pre-V3 CSV/XLSX behaviour;
  flagged by the PO as a priority regression.
* **POD-4 C** — controlled (not global) P1 rollout.
* **POD-5 C** — minimal compatibility layer for the retired report endpoints.
* **POD-6 C** — retention: investigate first, no behaviour change.

Global safety boundary respected: Step 3 not started; no demo/investor data
created; no RLS/security-architecture change; no billing policy change; no
Manual Processing Governance change; **no retention change**; no destructive
production test; no bulk reprocessing; **no storage object deleted**; Batch Upload
remains intentionally deferred; no Organization→Consultant conversion invented;
no emission-factor database change; no fabricated extraction values.

---

## 3. Starting baseline (verified)

* `git ls-remote origin refs/heads/p8-release-reconciled` =
  `7666fffaadb7b2969291bc133defc7526bc46c67` = worktree `HEAD` = the expected Step
  2 tip.
* Worktree clean (`git status --porcelain` = 0) on `p8-release-reconciled`.
* Implementation performed in the disposable worktree `/tmp/ct_step2` (derived
  from the release lineage). The dirty `~/carbon_tally` main worktree was **not**
  touched, reset, cleaned, stashed, overwritten, committed or pushed.

---

## 4. Ending Git state

```
remote : b45721abfbb2c8c8286273cb962ccd6a82cd7787
local  : b45721abfbb2c8c8286273cb962ccd6a82cd7787   (p8-release-reconciled)
dirty  : 0
ancestry: 7666fff is an ancestor of HEAD -> OK      (6 commits since 7666fff)
```

| SHA | Workstream | Purpose |
| --- | --- | --- |
| `3849f30` | POD-3 | CSV/XLSX V3 parity: segment-aware column/unit resolution, cover-sheet-aware XLSX sheet scan, no phantom lines, `source_row`/`source_headers` provenance, structured workspace preview |
| `a496a37` | POD-2 | Thin legacy manual-review compatibility adapter + route wiring |
| `9332569` | POD-4 | Controlled, tenant-aware P1 rollout (`shape_mode`/`rollout_status` + tenant threading) |
| `948917f` | POD-5 | Minimal compatibility layer for the retired report paths |
| `e5746ed` | POD-1 | Bounded automatic AI fan-out (consume the P1 plan) |
| `b45721a` | POD-2 (test) | Update the Step-2 legacy-import assertion to the adapter contract |

Files changed since the Step 2 tip (21 paths, all in scope):
`backend/api/v3_documents.py`, `backend/main.py`, `backend/routes/legacy_reports.py`,
`backend/routes/upload.py`, `backend/services/automatic_extraction.py`,
`backend/services/automatic_processing.py`, `backend/services/extraction_fidelity.py`,
9 backend test modules, and 5 frontend files
(`StructuredDataPreview.jsx` (new), `SecureDocumentViewer.jsx`, `workbench.css`,
`structured-data-preview.test.jsx` (new), `secure-document-viewer.test.jsx`).

`frontend/src/App.js` was **not** modified (`git diff --name-only 7666fff..HEAD --
frontend/src/App.js` = empty).

---

## 5. Workstreams completed

1. **POD-1** bounded AI fan-out — `e5746ed`.
2. **POD-2** manual-review compatibility adapter — `a496a37` (+ `b45721a` test).
3. **POD-3** CSV/XLSX parity, backend + workspace preview — `3849f30`.
4. **POD-4** controlled P1 rollout — `9332569`.
5. **POD-5** legacy report compatibility — `948917f`.
6. **POD-6** retention forensic analysis — this report (§13, §22), no code change.
7. **F-10 / F-11** re-verification — via the Step 2 tests retained green (§17/§18).

## 6. Workstreams blocked / requiring further PO decision

| Item | State | Why |
| --- | --- | --- |
| Vercel **frontend** deployment of `b45721a` | **BLOCKED (mechanical)** | Backend auto-deploys on push; the frontend requires a Vercel promotion, and no Vercel credential/CLI auth exists in this environment. Production still serves `main.1e761f98.js` (pre-Step-2C). |
| POD-3 **authenticated** production verification (real CSV/XLSX upload → preview → extraction) | **NOT PERFORMED** | Requires an authorised production session; no test credential was available. Not claimed as verified. |
| **F-07** CSS regression (report page collapse) | **UNCHANGED, deferred to Step 3** | Cannot be reproduced without an authenticated session; no speculative CSS change made. |
| `test_retention.py::test_audit_and_evidence_domains_are_excluded_from_enforcement` | **Stale test; remediation needs PO authorisation** | POD-6 forbids changing retention code **or tests**. See §13/§22. |
| Legacy `AUDITOR_EXCEL` workbook export | **No implementation exists** | POD-5 forbids inventing one; the compatibility path returns the existing truthful 400. Product decision required. |
| Consultant **preview** parity for CSV/XLSX | **Documented gap** | Presentation-level; see §16. |
| Batch Upload (F-01) | **Intentionally deferred** | No PO decision in this prompt. |
| Step 2 POD-3 storage-policy item (documents-bucket MIME/size) | **Already addressed by the PO** | The PO disabled the restrictive MIME setting; no further change made (§21). |

---

## 7. POD-1 evidence — bounded automatic AI fan-out

**Implementation** (`backend/services/automatic_processing.py`):

* New `AutomaticProcessingService._bounded_ai_candidates(text, filename, method)`
  **consumes** `extraction_fidelity.ai_fanout_plan()` — the plan that was
  previously computed and persisted but never acted on.
* Fan-out is attempted only when the plan permits it (multi-line-suspect **and**
  clipped text layer) **and** the text layer splits into >1 page; otherwise exactly
  one call over the full text layer (previous behaviour preserved).
* Hard limits (module constants): `AI_FANOUT_MAX_CALLS = 8` per document,
  `AI_FANOUT_MAX_RETRIES = 1`, `AI_FANOUT_TIMEOUT_S = 60.0`,
  `AI_FANOUT_PAGE_CLIP_CHARS = 8_000`; the plan's own `PAGE_CAP = 20` still bounds
  page count. No recursion.
* Cost boundary: only an *infrastructure* failure (timeout/exception) is retried
  once; an engine-reported error is a real answer and is never re-requested.
* Failure fallback: a failed page is recorded and the remaining pages are still
  attempted within the cap; the durable block reason keeps the engine's real
  detail (e.g. `LLM API returned HTTP 500`) instead of a generic message.
* Adjudication is **document-level**: deterministic extraction is the base and each
  page candidate fills only still-unresolved fields, in page order via
  `_merge_extraction_candidates`. No positional `det[idx]`/`ai[idx]` pairing
  (asserted: `adjudication.positional_blending is False`).
* Evidence persisted on the job metadata: `ai_extraction.ai_fanout` (plan, page
  basis/resolution, `pages_available`/`pages_attempted`, `calls_made`, limits,
  per-page attempt records incl. outcome + `processing_time_ms`, `first_failure`)
  and `ai_extraction.ai_pages`. AI evidence stays separate from deterministic
  evidence; nothing is fabricated for a page that returned nothing.

**Tests** (`tests/unit/services/test_pod1_bounded_ai_fanout.py`, 7 cases) record
the **actual call counts**: 1 call/page (2 pages → 2 calls); 1 call when the text
layer is not clipped (no unnecessary fan-out); cap honoured (`MAX_CALLS=2` with 5
pages → 2 calls, remaining pages `skipped`); engine error → 2 calls for 2 pages
(no retry; a retry would be 4); timeout → retried once then fallback (4 calls = 2
pages × (1+1), still ≤ cap); malformed response → nothing invented
(`ai_candidate.payload == {}`); field-level cross-page adjudication (page-2
`amount` can never overwrite the deterministic `amount`). All 27 pre-existing
processing/AI tests still pass unchanged.

## 8. POD-2 evidence — manual-review compatibility adapter

* `api.v3_documents.legacy_queue_for_manual_review(...)` translates a legacy
  request into the **current** workflow by driving the **same shared pipeline every
  V3 upload uses** (`create_document_and_enqueue`: storage → `organization_files` →
  extraction batch/item → durable automatic-processing job that blocks at the
  manual-review gate). No second queue, no duplicated queue logic, no resurrected
  architecture.
* `backend/routes/upload.py`: the legacy auto-repair branch calls the adapter and
  returns the legacy-shaped `status="manual_review_required"` payload
  (`review_id`, `document_id`, `item_id`, `extraction_issues`,
  `extraction_summary`, `confidence_score`, `workflow="v3_manual_review"`). The
  previously unreachable dead code referencing an undefined `review_id` is gone.
* Tenant/authorization preserved: `require_org_member()` is unchanged and the
  organisation flows into the shared pipeline.
* Auditability / call semantics: one registration per legacy request
  (`review_id` → created document id; the linked manual-extraction item id is
  returned when resolvable).
* Truthful failure: `LegacyManualReviewError` → HTTP 400 when the legacy caller
  cannot supply an organisation, a file name, or the document bytes. Nothing is
  silently discarded; no field is fabricated.

**Tests**: `tests/unit/api/test_legacy_manual_review_adapter.py` (4 cases) plus the
updated Step-2 contract test
(`test_manual_review_queueing_uses_the_v3_adapter_not_an_absent_helper`), which
still forbids the two original failure modes (an `ImportError`/500 and a silent
discard) and now also asserts the retired 503 is gone.

---

## 9. POD-3 CSV/XLSX regression analysis

**Root cause 1 — backend column resolution.** The V3 tabular reader resolved
**exact normalised header keys only**. Real supplier exports use composite headers,
so those columns fell through to unknown fields and the row lost
`activity`/`quantity`/`unit` — the file parsed, but the job was blocked with a
misleadingly empty extraction. Measured with `extract_document(...)` on the
repository's own fixtures:

| Fixture | Before | After |
| --- | --- | --- |
| `mock_scope3.csv` | ok / 1.00 / 4 lines | unchanged (regression-guarded) |
| `mock_uk_fuel_card_messy.csv` | ok / **0.00** / 50 lines; unresolved `activity, quantity, unit` | ok / **1.00** / 50 lines; unresolved `[]` |
| `mock_uk_utility_bill.csv` | ok / **0.67** / 20 lines; unresolved `activity` | ok / **1.00** / 20 lines; unresolved `[]` |

First resolved fuel-card line: `{date: 01/10/2023, activity: "Diesel",
quantity: 53.8, unit: "litres", amount: 85.21, supplier: "Esso", source_row: 1}`;
first utility line: `{activity: "Natural gas", quantity: 6354.47, unit: "kwh",
amount: 1390.44}` (activity labels come from the **pre-existing** `_detect_activity`
canonicaliser — not invented by this change).

Fix: segment-aware alias resolution in `_normalise_columns` — exact key → explicit
`_ALIAS_EXCLUSIONS` (a unit *price* is not an amount; a *site* is not an activity)
→ whole-segment unit token + physical-quantity segment → **longest** alias segment →
unit segment → preserve. Unit tokens match whole key segments, so `Volume (L)` →
litres while `Total` is never misread as a litre column.

**Root cause 2 — XLSX sheet selection and phantom lines.** Only the workbook's
*active* sheet was read, so a cover/summary first sheet (very common) produced no
data; worse, a sheet of unrecognised columns produced *phantom* line items
(`{source_row: n}` only), which made the cover sheet look like a successful
extraction and stopped any fallback. Fix: phantom lines are no longer emitted (a
record must carry at least one canonical field), and the workbook is scanned
sheet-by-sheet (active first, bounded to `_XLSX_SHEET_SCAN_LIMIT = 5`) taking the
first sheet that yields real activity data; `source_sheet`/`sheet_names` are
recorded.

**Provenance added:** every line item carries `source_row` (1-based data-row index,
order preserved) and the extraction carries the verbatim `source_headers`
(plus `source_sheet`/`sheet_names` for XLSX), so a mapped field traces back to its
column/row.

**Root cause 3 — workspace preview (the PO's first symptom).**
`SecureDocumentViewer` deliberately rendered *"Document preview is not available for
this file type"* for CSV/TSV/XLSX (`kind === 'data'` → not framed). New
`StructuredDataPreview` renders a bounded, read-only preview: CSV/TSV through a
quote-aware parser into a table; XLSX workbook/sheet-aware (sheet list + parsed
sheet name + first sheet as a table). Bounded to 50 rows / 30 columns / 12 sheets
with loading, error and empty states. No iframe, **no download control**, no new
visual system (existing D21 tokens); the security boundary remains the
backend-issued signed URL.

**Tests**: `tests/unit/services/test_structured_file_parity.py` (11 cases — the
three real fixtures, header/row-identity preservation, exclusion rules,
single-letter unit-segment safety, no fabricated quantity, synthetic
cover-sheet-first workbook, XLSX not treated as PDF/image);
`src/v3/__tests__/structured-data-preview.test.jsx` (5 cases — kind detection,
quote-aware parsing, CSV table, XLSX sheet awareness, truthful error state); and
`src/v3/__tests__/secure-document-viewer.test.jsx` updated **deliberately**: the
CSV case now asserts the structured preview (no iframe, no download) and a new case
keeps the "not available" placeholder for genuinely unknown types.

---

## 10. POD-4 controlled P1 rollout evidence

* `services/extraction_fidelity.shape_mode(env=None, organization_id=None)` now
  resolves the **effective** mode in two deterministic steps: the requested mode
  from `CARBONTALLY_P1_EXTRACTION_SHAPE` (invalid/absent → `shadow`), then the
  organisation allowlist in `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST`
  (comma-separated organisation ids). `enabled` with an empty/missing allowlist is
  **downgraded to `shadow`** (fail-safe): enabling P1 for everyone requires the
  deliberate wildcard `*`.
* `rollout_status(...)` produces the audit/evidence record (requested mode,
  effective mode, organisation, `in_rollout`, `allowlist_size`, `allow_all`) with no
  secrets; it is persisted as `rollout` on every governed extraction result.
* Tenant context is threaded to the hook:
  `extract_document(..., organization_id=)` → `_extract_pdf`/`_extract_image` →
  `_apply_p1_fidelity(..., organization_id=)`, and the worker passes
  `job.organization_id`. Omitting it stays `shadow`.
* Rollback: remove the organisation from the allowlist (or unset `enabled`) and the
  next extraction is back to the existing safe behaviour — nothing is cached.
* The pre-existing mechanism was **extended, not replaced** (no second mechanism);
  no real customer data was used for experimentation and uncontrolled enablement is
  not possible by default.

**Tests**: `tests/unit/services/test_p1_controlled_rollout.py` (9 cases — default,
invalid value, fail-safe without allowlist, allowlisted vs non-allowlisted
organisation, no-tenant-context, explicit wildcard, `off`/`shadow` never upgraded,
audit record + reversibility, hook behaviour inside vs outside the rollout). Two
pre-existing tests were updated **deliberately** for the new fail-safe semantics
(documented in place): `test_extraction_fidelity.py` asserts that `enabled` requires
an allowlist, and `test_p1_image_path.py` opts in through the wildcard. Four
`extract_document` test doubles now accept the tenant kwarg.

## 11. POD-5 report compatibility evidence

* **Callers identified (live code):** `frontend/src/App.js` posts to
  `{API_URL}/api/generate-enhanced-report` and
  `{API_URL}/api/generate-sustainability-report`; the only mounted implementation
  was `POST /api/reports/generate-enhanced-report`. Mounted paths were enumerated
  from `main.app.routes` → the two UI paths were **404s**.
* **Layer:** new `backend/routes/legacy_reports.py` (prefix `/api`) exposes exactly
  those two paths and **delegates** to the single existing implementation. No new
  reporting subsystem; no duplicated business logic; response semantics and
  `report_type` handling unchanged.
* **Authorization / tenant isolation:** the legacy handler takes
  `organization_id` from the body and would otherwise serve another organisation's
  report to any authenticated member. The compatibility routes verify
  `organization_id == caller's organisation` (403 otherwise) and refuse a caller
  with no organisation context, before delegating.
* **Deprecation documented:** `Deprecation: true` and
  `Link: </api/v3/reports>; rel="successor-version"` headers plus a module
  docstring stating the mapping.
* **No invention:** the legacy `AUDITOR_EXCEL` option has no implementation in this
  release; the adapter returns the existing truthful `400 Unsupported report type`
  rather than fabricating a workbook.

**Tests**: `tests/unit/api/test_legacy_report_compat.py` (4 cases — delegation +
deprecation headers, cross-tenant denial without reaching the generator,
missing-organisation refusal, unsupported type preserved).

## 12. POD-6 retention forensic findings

Full deliverable in §22. In one line: the failing test is **stale** (it pins the
pre-Phase-8-X-X2 eligible-domain set) while the implementation matches the later PO
decision `PX-7`; **no retention code, test, schema or configuration was changed**
(POD-6 forbids it).

---

## 13. F-01 … F-12 final matrix

| ID | Previous classification (Step 2A) | Current classification | Status | Commit | Test evidence | Production evidence | Remaining limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 Batch Upload | Intentionally deferred | **Deferred (unchanged)** | Not implemented | — | — | — | No PO decision exists; must stay deferred |
| F-02 CSV/XLSX structured ingestion | Broken in V3 | **Fixed** | Implemented + tested | `3849f30` | `test_structured_file_parity.py` (11) | Fixtures local; authenticated prod upload not exercised | Authenticated prod check |
| F-03 CSV/XLSX workspace preview | Broken in V3 | **Fixed** | Implemented + tested | `3849f30` | `structured-data-preview.test.jsx` (5) + viewer test | **Not deployed** (Vercel) | Frontend promotion required |
| F-04 Legacy manual-review queue | No implementation | **Adapter added** | Implemented + tested | `a496a37`, `b45721a` | `test_legacy_manual_review_adapter.py` (4) + legacy-imports (5) | Backend deployed; endpoint requires auth | Authenticated check in Step 3 |
| F-05 AI fan-out plan unconsumed | Plan produced, not consumed | **Consumed under hard limits** | Implemented + tested | `e5746ed` | `test_pod1_bounded_ai_fanout.py` (7) | Engine-dependent; not exercised in prod | Live provider call counts not observed |
| F-06 P1 global enablement risk | Global-only switch | **Controlled rollout** | Implemented + tested | `9332569` | `test_p1_controlled_rollout.py` (9) | Default remains `shadow` (no env set) | Enabling P1 is a PO action |
| F-07 Report page CSS collapse | Unverified | **Unverified (unchanged)** | Not reproduced | — | — | — | Needs authenticated Step-3 acceptance |
| F-08 Retired report endpoints | 404 | **Compatibility layer** | Implemented + tested | `948917f` | `test_legacy_report_compat.py` (4) | **Live** — both paths in the production OpenAPI (401 without auth) | Excel export absent by design |
| F-09 Legacy `from main import` sites | 3 repaired | **0 remain** | Verified | (Step 2) + `b45721a` | `test_step2_legacy_imports.py` (5) | — | — |
| F-10 Queue/item state consistency | Partial | **Re-verified green** | No regression | — | `test_step2_remediation.py` + processing suite | — | — |
| F-11 Blocked-job visibility | Implemented (Step 2) | **Re-verified green** | No regression | — | `customer-blocked-visibility.test.jsx` (within the 302 frontend tests) | Not re-verified interactively | Frontend not yet deployed |
| F-12 Partial extraction persistence | Implemented (Step 2) | **Re-verified green** | No regression | — | `test_step2_remediation.py` | — | — |

`F-01 Batch Upload = intentionally deferred` is **explicitly preserved** — the
prompt contains no PO decision to change it.

## 14. P1 final matrix

| P1 item | PO authorized | Implemented | Tested | Controlled rollout | Production verified | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| P1-D1 extraction-fidelity shape hook (PDF + IMAGE) | Yes (Step 2) | Yes (Step 2) | Yes | **Yes — allowlist, default `shadow`** | Backend live; default mode only (`shadow`) | `9332569` (rollout); Step 2 for the hook |
| P1-D2 bounded block reason propagation | Yes (Step 2) | Yes (Step 2) | Yes | n/a (`shadow`) | — | Step 2 |
| P1-D3 per-page AI fan-out plan | **Yes — POD-1 A** | **Yes** | **Yes** (call counts recorded) | n/a (fan-out is plan-gated, not rollout-gated) | Not exercised (needs live engine) | `e5746ed` |
| P1 §7.3 document-level adjudication (no positional blending) | Yes | Yes (Step 2) | **Yes** (asserted `positional_blending is False`) | n/a | — | Step 2 + `e5746ed` |
| P1 coverage/fan-out persistence on the job | Yes | Yes (Step 2) | Yes | n/a | — | Step 2 |
| P1 enablement (`enabled` mode) | **Controlled only (POD-4 C)** | Mechanism implemented | Yes | **Yes** | Production remains `shadow` (no allowlist configured) | `9332569` |

P1 is **not** claimed complete for production behaviour: the hook is implemented,
tested and rollout-controlled, but `enabled` is not active in production and the
fan-out has not been exercised against a live provider. Implementation, testing,
rollout and production verification are stated separately and only the first three
are asserted for the fan-out.

## 15. Consultant Client parity observations

* **Backend functions reach consultants by construction**: POD-1, POD-2, POD-4 and
  POD-5 are backend-side, and the consultant item workspace
  (`frontend/src/v3/consultant/ConsultantItemPage.jsx`) documents that it uses the
  **shared `/api/v3/processing/*` surface** (consultant-authorised) — so automatic
  processing, manual review, extraction and reporting compatibility are parity
  features for consultants without any consultant-specific code being added.
* **Presentation gap (documented, not fixed):** the POD-3 structured *preview* was
  added to the workbench viewer (`SecureDocumentViewer` → `StructuredDataPreview`),
  used by the customer `ProcessingItemWorkspace` and the ops `WorkItemWorkspace`.
  The consultant item page presents the source document through its own view and
  reuses `ExtractionPanel`; it does **not** use the workbench viewer, so CSV/XLSX
  preview parity (`F-03` for the consultant surface) is **not** delivered by this
  change. Extending the same preview there is a presentation/UX decision adjacent
  to D19 and was **stopped as a sub-item** per §14 rather than improvised.
* No new consultant-specific functionality was created.

---

## 16. Backend test results

| Command | Baseline | Current | Pass/Fail | Pre-existing? | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `pytest tests/unit/services/test_structured_file_parity.py` | n/a (new) | 11 passed | PASS | n/a | POD-3 parity pinned against the real fixtures |
| `pytest tests/unit/services/test_pod1_bounded_ai_fanout.py` | n/a (new) | 7 passed | PASS | n/a | POD-1 call counts/limits/fallback |
| `pytest tests/unit/services/test_p1_controlled_rollout.py` | n/a (new) | 9 passed | PASS | n/a | POD-4 fail-safe/allowlist/reversibility |
| `pytest tests/unit/api/test_legacy_manual_review_adapter.py` | n/a (new) | 4 passed | PASS | n/a | POD-2 translation contract |
| `pytest tests/unit/api/test_legacy_report_compat.py` | n/a (new) | 4 passed | PASS | n/a | POD-5 delegation + tenant isolation |
| `pytest tests/unit/routes/test_step2_legacy_imports.py` | 5 passed (pre-change form) | 5 passed | PASS | n/a | Updated deliberately for the POD-2 contract |
| `pytest tests/unit/services/test_automatic_processing.py` | 27 passed | 27 passed | PASS | No | No regression from POD-1 |
| `pytest tests/unit/services/test_step2_remediation.py` | passed | passed | PASS | No | F-10/F-12 re-verified |
| `pytest tests/unit/services/test_automatic_extraction.py` + `…_text_layer.py` | 14 passed | 14 passed | PASS | No | No regression from POD-3 |
| `pytest tests/unit` (full sweep) | 1 failure | 1 failure (same) | PASS (except below) | **Yes** | `test_retention.py::test_audit_and_evidence_domains_are_excluded_from_enforcement` — the POD-6 stale test; the only remaining unit failure |

A Step-2C regression was introduced during implementation (the Step-2 legacy-import
test asserted the interim 503 contract) and was **fixed in `b45721a`** before the
final sweep — the final sweep has no Step-2C-caused failure.

## 17. Frontend test results

```
Test Suites: 1 failed, 30 passed, 31 total
Tests:       302 passed, 302 total
```

* The single failing *suite* is `src/App.test.js` → `Test suite failed to run:
  Cannot find module 'react-router/dom'` — a **pre-existing environment/dependency
  resolution issue** in the shared `frontend/node_modules` (not a Step 2C file; no
  Step 2C module is involved, and zero tests failed).
* Step 2C frontend additions: `structured-data-preview.test.jsx` (5 new cases) and
  the updated `secure-document-viewer.test.jsx` (CSV now asserts the structured
  preview; a new case covers the unknown-type placeholder).
* Production build: `npx react-scripts build` → **"Compiled with warnings. The build
  folder is ready to be deployed."** Under `CI=true` the build fails because CRA
  treats warnings as errors and the **legacy `src/App.js`** carries pre-existing
  `no-unused-vars` warnings; the build log contains **no warning from any Step 2C
  file** (`StructuredDataPreview.jsx`, `SecureDocumentViewer.jsx`, `workbench.css`).

## 18. Production deployment evidence

| Surface | Mechanism | Evidence | Result |
| --- | --- | --- | --- |
| Backend (Render) | auto-deploy on push to `p8-release-reconciled` | live `GET /openapi.json` reports **570 paths** including the two NEW compatibility paths `/api/generate-enhanced-report` and `/api/generate-sustainability-report`; `rndr-id: b87594b2-16a1-4bea`; `x-render-origin-server: uvicorn` | **DEPLOYED (post-Step-2C)** |
| Frontend (Vercel) | requires a promotion (not triggered by the push) | production `index.html` → `main.1e761f98.js` (1,955,456 bytes); marker scan: `Workbook preview` = 0, `Data preview` = 0, `structured-preview` = 0, `ct-wb-viewer__data` = 0, while the pre-Step-2C string `Document preview is not available` = 1 | **NOT DEPLOYED (pre-Step-2C bundle)** |

The frontend deployment is a **mechanical blocker**, not an implementation gap: the
code, tests and production build are complete, but no Vercel credential/promotion
mechanism is available in this environment (the same limitation recorded in the
Step 1B verification reports).

## 19. Production verification (safe, non-destructive)

| Check | Result |
| --- | --- |
| API root `GET /` | **200** — `{"message":"CarbonTally API","version":"3.0.0","status":"healthy","api_version":"v3","routes_count":49}` |
| `GET /health` | **200** — `{"status":"healthy","service":"CarbonTally API",…}` |
| `GET /api/health` | 404 (no such route — not a regression; `/health` is the mounted health path) |
| OpenAPI contract | **200**, 570 paths; the two POD-5 compatibility paths are present; `/api/reports/generate-enhanced-report` still present |
| `POST /api/generate-enhanced-report` (empty body, no auth) | **401** (route exists, authorization enforced) — was **404** before this release |
| `POST /api/generate-sustainability-report` (empty body, no auth) | **401** — was **404** before this release |
| `POST /api/reports/generate-enhanced-report` (empty body) | **422** (validation) — pre-existing route unchanged |
| Unexpected 5xx | none observed on the public endpoints exercised |
| Authenticated checks (CSV/XLSX upload → preview → extraction; blocked-job card; P1 rollout config) | **NOT PERFORMED** — no authorised production session was available; **not claimed** |
| Schema drift introduced | **None** (no migrations; see §20) |
| Production data modification | **None** (read-only probes only) |
| Destructive tests / bulk processing | **None performed** |
| Frontend production behaviour | **Not verified** — the deployed bundle predates Step 2C (§18) |

---

## 20. Database / migration impact

**None.** No migration was added, no schema change made, no table created or
altered, no RLS policy touched, and no SQL executed against any database. All
persistence used existing structures: extraction provenance goes into the existing
`organization_files.metadata` JSONB and durable job metadata
(`ai_extraction.ai_fanout`, `ai_pages`, `coverage`, `rollout`);
`line_items[].source_row` / `extracted_data.source_headers` are additional keys
inside the existing extraction payload (no column added); the manual-review adapter
writes through the **existing** repositories (`files`, `manual_extraction`,
`processing`) used by the V3 upload path.

## 21. Storage / configuration impact

* **Storage:** no bucket created, modified or emptied; no object uploaded, deleted
  or rewritten by this workstream; no signed URL logged or committed. The PO's
  statement that the restrictive Supabase MIME configuration has already been
  disabled is consistent with CSV/XLSX reaching storage; **no** bucket-policy change
  was made or needed.
* **Configuration (new, optional, fail-safe):**
  * `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST` (new) — comma-separated organisation ids
    or the deliberate wildcard `*`;
  * `CARBONTALLY_P1_EXTRACTION_SHAPE` (pre-existing) — `off|shadow|enabled`;
    `enabled` is now honoured **only** for allowlisted organisations.
  * **Production default today: no allowlist configured ⇒ effective mode
    `shadow`** — nothing was enabled by this release.
* No secret, token, credential or signed URL was added to the repository, the
  report, logs or any commit.

## 22. Retention forensic result (POD-6)

**Authoritative evidence**

1. **Failing test:** `backend/tests/unit/services/test_retention.py:28` —
   `test_audit_and_evidence_domains_are_excluded_from_enforcement` asserts
   `set(_ELIGIBLE_DOMAINS) == {"document_retention_days"}`; observed failure: extra
   item `'operational_telemetry_retention_days'`.
2. **Current implementation:** `backend/services/retention.py` — module docstring
   ("Phase 8-X X2 adds `operational_telemetry_retention_days` (PO `PX-7` decision:
   telemetry detail 90 days by default, aggregates indefinitely)") and
   `_ELIGIBLE_DOMAINS = ("document_retention_days",
   "operational_telemetry_retention_days")`. Enforcement is configuration-driven
   from `system_settings`; an unset domain reports `{"configured": False}` and
   nothing is deleted. No retention value is invented by the code.
3. **Policy evidence:**
   `docs/legal/draft/CARBONTALLY_DATA_RETENTION_ARCHIVAL_ANONYMIZATION_POLICY_DRAFT.md`
   §2.4 ("Retention durations are configured explicitly (`system_settings`),
   surfaced at `/api/v3/settings/retention`, and enforced server-side. No retention
   value is invented by the enforcement code."), §5.1 (configuration domains). The
   telemetry domain is a later Phase 8-X X2 addition per PO decision `PX-7`,
   referenced in `docs/cline/reports/CT-P8-REST-PLAN-20260913-027.md` (X7 ↔ `PX-7`)
   and `CT-P8-P8X-X2-IMPLEMENTATION-AND-IV-20260914-062.md`.
4. **Production dependency:** enforcement runs server-side with `dry_run=True` by
   default and reports telemetry as `configured: False` unless an operator sets it.
   No production behaviour depends on the test's narrower expectation.
5. **Conclusion:** the **implementation matches policy; the test is stale** — it
   pins the pre-X2 eligible-domain set and predates `PX-7`. Policy itself is **not**
   unresolved and the failure is not a regression.

**Recommendation:** authorise a one-line update of that test to expect both eligible
domains (documented as a deliberate test update), or retire it in favour of a
settings-driven assertion. **No change was made** — POD-6 forbids modifying
retention code, tests, schema or configuration.

---

## 23. Git commit / push evidence

| Item | Value |
| --- | --- |
| Starting SHA | `7666fffaadb7b2969291bc133defc7526bc46c67` |
| Ending SHA | `b45721abfbb2c8c8286273cb962ccd6a82cd7787` |
| Remote SHA after final push | `b45721abfbb2c8c8286273cb962ccd6a82cd7787` (identical) |
| Commits pushed | 6 (`3849f30`, `a496a37`, `9332569`, `948917f`, `e5746ed`, `b45721a`) |
| Ancestry | `7666fff` is an ancestor of `HEAD` — verified |
| Worktree at end | clean (build artefacts removed) |
| `main` branch | **not pushed to, not modified** |
| Dirty `~/carbon_tally` worktree | **not touched** (implementation ran in `/tmp/ct_step2`) |
| Secrets committed | none (no `.env`, token, key, JWT or signed URL in any diff) |
| Unrelated changes | none — 21 paths, all Step 2C scope |
| Customer data modified | none |
| Destructive operations | none |
| Batch Upload | remains deferred |

## 24. Unresolved risks / decisions

1. **Frontend deployment (blocking the verdict).** Vercel must promote the
   `p8-release-reconciled` build containing `3849f30` so the POD-3/F-03 structured
   preview (and the Step-2 blocked-job card) reach customers; then the frontend
   checks in §19 can be completed.
2. **Authenticated acceptance not performed** — CSV/XLSX end-to-end in production
   (upload → preview → extraction → mapping) and the blocked-job card remain
   unverified in an authenticated context. This is the primary Step 3 acceptance
   item, together with F-07.
3. **F-07 CSS** — still unverified; no speculative change made.
4. **P1 enablement** — remains `shadow`; enabling it for a pilot organisation is now
   a reversible configuration action
   (`CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` +
   `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST=<org>`), and whether to enable a pilot is a
   PO action.
5. **AI fan-out live behaviour** — limits and fallbacks are implemented and tested
   with controlled doubles; live provider call counts/costs have not been observed
   (needs an authorised pilot environment).
6. **Retention test** — requires the authorisation described in §22.
7. **Auditor Excel export** (`AUDITOR_EXCEL`) — offered by the legacy UI, no
   generator exists; the compatibility layer answers truthfully. Reinstating it is a
   product decision.
8. **Consultant preview parity** — presentation-level gap (§15).
9. **Structured-file parsing breadth** — the alias map was widened to the real
   supplier shapes in evidence (fuel-card, utility, scope-3); further bespoke
   customer header shapes may still need mapping, and unknown columns are preserved
   rather than mis-mapped.

## 25. Final verdict

`STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`

Every implementation-authorised workstream (POD-1, POD-2, POD-3, POD-4, POD-5) is
implemented, tested and pushed; POD-6 is delivered as a forensic finding with no
behaviour change. The single reason the verdict is not
`STEP 2 COMPLETE — READY FOR STEP 3` is that the **frontend build has not been
promoted to production** (so the POD-3 and Step-2 frontend behaviours cannot be
production-verified) — a mechanical release step, not outstanding implementation
work. No Step 3 activity was started.








