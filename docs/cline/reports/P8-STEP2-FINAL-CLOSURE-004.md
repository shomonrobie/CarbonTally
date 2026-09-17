# Phase 8 — Step 2 Final Closure

**Task ID:** `CT-STEP2-FINAL-CLOSURE-003`
**Branch:** `p8-release-reconciled`
**Starting tip (verified):** `6beb281cb9128a16d9c25459ad4fe53ef350d539` — local == `origin/p8-release-reconciled`, worktree clean
**Code/test tip (banked this task):** `503d18611cf040852468b31b7705e74acce9ffe2`
**Report commit (this file):** the commit that adds `docs/cline/reports/P8-STEP2-FINAL-CLOSURE-004.md`
**Date:** 2026-09-17
**Verdict:** `STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`
(blocking items: frontend production promotion; authenticated production acceptance. See §22, §23, §30.)

---

## 1. Executive summary

The closure audit produced four decisive results.

1. **Git completeness: nothing is unbanked.** All fifteen expected Step 1/Step 2/Step 2C
   commits are **IN-ANCESTRY** of the release tip (`git merge-base --is-ancestor` per
   commit, §5). The protected dirty `~/carbon_tally` tree contains **none** of the Step 2C
   workstream markers (`_ALIAS_SEGMENTS`, `ROLLOUT_ALLOWLIST_ENV`,
   `legacy_queue_for_manual_review`, `_bounded_ai_candidates`, `StructuredDataPreview`
   → 0 hits each; `backend/routes/legacy_reports.py` absent), and the stray
   `fx12-publish` branch holds an **older** variant of those files. The release is
   strictly ahead of both; nothing had to be recovered, so **no recovery commit was
   created**.
2. **POD-6 closed.** The stale retention test was corrected under PO authorisation as a
   **test-only, one-file** commit (`503d186`, +30/−3). The **full backend unit suite now
   has zero failures** (previously the single failing test in the whole unit suite).
3. **The release build was served and probed from its own SHA.** `uvicorn main:app` from
   the release worktree at `503d186` (no startup DDL; read-only usage) reports
   `/health` 200, **570 OpenAPI paths** including both POD-5 compatibility aliases and
   `/api/upload-pdf` (POD-2 route); authenticated `GET /api/v3/documents?organization_id=<own org>`
   → **200**, anonymous → **401**, and a cross-organisation request → **403** (server-side
   tenant isolation).
4. **Two items are blocked by missing provider access, not by implementation.**
   There is no Vercel credential, CLI or auth directory in this environment
   (`vercel`/`render` CLIs absent, no `~/.vercel`, no deployment keys in the project env
   files), so the **frontend cannot be promoted**; production still serves the
   pre-Step-2C bundle. There is **no browser automation** (no Playwright/Puppeteer
   anywhere), so authenticated UI acceptance (F-07 CSS, CSV/XLSX preview rendering,
   blocked-job card) cannot be executed here.

Consequently the release is complete, tested, banked and pushed, with a verified route
surface, but frontend production deployment and authenticated production acceptance
remain open — therefore the verdict is **not** `STEP 2 COMPLETE`.

---

## 2. PO decisions

| Decision | Scope |
| --- | --- |
| **POD-1 A** | bounded automatic AI fan-out |
| **POD-2 C** | thin compatibility adapter into the current V3 manual-review workflow |
| **POD-3 A** | full V3 parity with the intended pre-V3 CSV/XLSX behaviour |
| **POD-4 C** | controlled (not global) P1 rollout |
| **POD-5 C** | minimal compatibility layer for the retired report endpoints |
| **POD-6 C → authorised correction** | forensic first; the PO then explicitly authorised the one-line stale-test correction (test only) |
| **Closure authorisation** | final Git completeness/reconciliation, banking of verified Step 2 work, the approved Step 2 remediation, the POD-6 test correction, frontend production promotion, final authenticated production acceptance where safely possible, and final closure verification |

Safety boundaries honoured: Step 3 not started; no demo/investor data created or
modified; no destructive production action; no RLS/billing/governance/retention
**implementation** change; no storage object deleted; Batch Upload still deferred; no
customer record modified; no secrets committed.

---

## 3. Starting Git state (verified, not assumed)

```
release worktree /tmp/ct_step2 : HEAD 6beb281cb9128a16d9c25459ad4fe53ef350d539
                                 origin/p8-release-reconciled 6beb281c…  (identical)
                                 branch p8-release-reconciled, dirty 0
protected tree ~/carbon_tally  : HEAD 20b7a928bb73fdfacf8271ff537a8fd245f62c79, branch main,
                                 dirty 298 paths, staged 0
```

Local branches: `p8-release-reconciled` (current), `main` (ahead 4/behind 5 of
`origin/main`), `fx12-publish` (separate workstream, worktree `prunable`),
`openhands/*` (separate workstreams). Remote branches include `p8-release-reconciled`,
`main`, `openhands/*`. The twelve expected Step 2C-era commits were present exactly as
documented.

---

## 4. Final Git state

```
local  : 503d18611cf040852468b31b7705e74acce9ffe2  (code/test tip, pushed)
origin : 503d18611cf040852468b31b7705e74acce9ffe2  (identical, verified after push)
dirty  : 0        (build artefacts removed; report committed separately)
ancestry: 6beb281 -> 503d186 ; every Step 1/Step 2/Step 2C commit remains an ancestor
```

Commits added by this closure task: **2** — `503d186` (POD-6 test correction; code/test)
and the documentation commit that adds this report. Diff of the code/test commit against
the previous tip is **exactly one file**:

```
backend/tests/unit/services/test_retention.py | 33 ++++++++++++++++++++++++---
1 file changed, 30 insertions(+), 3 deletions(-)
```

---

## 5. Git completeness audit

Ancestry verified per commit (`git merge-base --is-ancestor <sha> HEAD`):

| # | Commit | Workstream | Ancestry | Remote contains | Classification |
| --- | --- | --- | --- | --- | --- |
| 1 | `0d21e46` | F-046-1 protected-persistent-target guard (Step 1) | IN | yes | **R1** |
| 2 | `f5e07ed` | P1-D1 extraction-fidelity hook + pipeline v3-auto-1.1 (Step 1) | IN | yes | **R1** |
| 3 | `eb6a0c2` | S6 report-lifecycle visibility (Step 1) | IN | yes | **R1** |
| 4 | `5d143ac` | Step 2 WS-A: partial extraction persistence + P1 §7.3 document-level adjudication + P1-D2 block reason + coverage persistence | IN | yes | **R1** |
| 5 | `c8b8d81` | Step 2 WS-B B3: P1 hook on the IMAGE path | IN | yes | **R1** |
| 6 | `55be3d2` | Step 2 WS-C: legacy `from main import` repairs → truthful handling | IN | yes | **R1** |
| 7 | `7666fff` | Step 2 WS-H: customer-visible blocked jobs with reason | IN | yes | **R1** |
| 8 | `3849f30` | Step 2C POD-3 CSV/XLSX parity (backend + preview) | IN | yes | **R1** |
| 9 | `a496a37` | Step 2C POD-2 compatibility adapter | IN | yes | **R1** |
| 10 | `b45721a` | Step 2C POD-2 test-contract update | IN | yes | **R1** |
| 11 | `9332569` | Step 2C POD-4 controlled P1 rollout | IN | yes | **R1** |
| 12 | `948917f` | Step 2C POD-5 report compatibility layer | IN | yes | **R1** |
| 13 | `e5746ed` | Step 2C POD-1 bounded AI fan-out | IN | yes | **R1** |
| 14 | `2f6e1d5` | Step 2C report (documentation) | IN | yes | **R1** |
| 15 | `6beb281` | Step 2C report header correction (documentation) | IN | yes | **R1** |
| 16 | `503d186` | **POD-6 stale-test correction (this task)** | tip | yes (pushed, verified) | **R1** |

**Outside the release** (`R2`–`R7` scan):

* **`fx12-publish`** (worktree `/tmp/fx12_pub_wt`, marked `prunable`): `git diff --stat
  fx12-publish HEAD` for the Step 2 files shows the release **adds** 1 341 lines across 8
  files (`legacy_reports.py` +97, `StructuredDataPreview.jsx` +154, POD-3/POD-1/POD-4
  changes). That branch carries an **older** variant of those files and no Step 2
  verification evidence → classified **R7 (not Step 2 work)**, not merged.
* **Protected dirty `~/carbon_tally`**: contains **none** of the Step 2C markers
  (0 hits for each of 5 patterns; `legacy_reports.py` absent) and divergent pre-Step-2
  content for the six Step 2 files (hashes differ, release is newer) → **R5/R7**, per
  §6 rule "never reconstruct work that cannot be safely located as the original
  implementation". Nothing to recover.
* Reflog for `p8-release-reconciled` shows a linear, expected history (12 entries, all
  the commits above) — no orphaned verified commit.
* No clones/checkpoints beyond the agent `cline checkpoint` commits on the stray
  `fx12-publish` worktree lineage; those are session snapshots, not verified
  implementations.

## 6. Recovered / banked work

* **Recovered:** none required — every workstream was already in the release (R1).
* **Banked new work (this task):** `503d186` — POD-6 stale-test correction
  (`backend/tests/unit/services/test_retention.py`), tested (23 passed), committed
  narrowly, pushed, remote SHA verified.

## 7. Step 1 recovery verification

| Item | Implementation | Commit | Tests present | In release | Production status |
| --- | --- | --- | --- | --- | --- |
| **F-046-1** protected-persistent-target guard | `backend/tests/integration/conftest.py` guard refusing `qa`/`demo`/`investor`/`prod`/`live` targets | `0d21e46` | guard exercised by the integration fixtures (no destructive run performed in this task) | yes | server-side/infra control; unaffected by deployment |
| **P1-D1** extraction-fidelity hook | `services/extraction_fidelity.py` + wiring in `services/automatic_extraction.py` (PDF and, since `c8b8d81`, IMAGE) | `f5e07ed` | `tests/unit/services/test_extraction_fidelity.py`, `test_p1_image_path.py`, `test_automatic_processing.py` — green | yes | live backend (default `shadow` mode only, §13) |
| **S6** report-lifecycle visibility | server-authoritative `allowed_actions` + lifecycle panel | `eb6a0c2` | report-lifecycle frontend tests within the 302 passing frontend tests | yes | backend live; **frontend not promoted** |

## 8. Step 2 remediation verification

| Step 2 workstream | Commit | Evidence re-run in this task | Status |
| --- | --- | --- | --- |
| WS-A partial extraction persistence + P1 §7.3 adjudication + block reason + coverage | `5d143ac` | `test_step2_remediation.py` green in the full unit sweep | PASS |
| WS-B B3 P1 hook on the IMAGE path | `c8b8d81` | `test_p1_image_path.py` green | PASS |
| WS-C legacy `from main import` repairs | `55be3d2` | `test_step2_legacy_imports.py` (5) green | PASS |
| WS-H customer-visible blocked jobs | `7666fff` | `customer-blocked-visibility.test.jsx` within the 302 frontend tests | PASS (frontend not deployed) |

---

## 9. POD-1 verification — bounded automatic AI fan-out

* Implementation: `AutomaticProcessingService._bounded_ai_candidates(...)` consumes
  `extraction_fidelity.ai_fanout_plan()`; fan-out only when the plan permits it
  (multi-line-suspect **and** clipped text layer) **and** the text splits into >1 page.
* Limits enforced in the loop: `AI_FANOUT_MAX_CALLS = 8` per document,
  `AI_FANOUT_MAX_RETRIES = 1`, `AI_FANOUT_TIMEOUT_S = 60.0`,
  `AI_FANOUT_PAGE_CLIP_CHARS = 8_000`; plan `PAGE_CAP = 20`; no recursion. Only
  infrastructure failures (timeout/exception) are retried once; an engine-reported error
  is never re-requested.
* Adjudication is document-level and field-level; `adjudication.positional_blending` is
  asserted `False` — no positional deterministic/AI pairing.
* Evidence persisted: `ai_extraction.ai_fanout` (plan, page basis/resolution, pages
  available/attempted, calls made, limits, per-page attempts, `first_failure`) and
  `ai_extraction.ai_pages`; block reasons keep the engine's real detail.
* Tests re-run: `tests/unit/services/test_pod1_bounded_ai_fanout.py` (7 cases recording
  real call counts: 2 calls/2 pages; 1 call when not clipped; cap 2 honoured with 5 pages;
  engine error not retried; timeout retried once then fallback; malformed response
  fabricates nothing) **PASS**, plus the 27 pre-existing processing/AI tests **PASS**.
* Production limitation: fan-out has not been exercised against a live provider (needs an
  authorised pilot); the plan-gated path is proven with controlled doubles only.

## 10. POD-2 verification — manual-review compatibility adapter

* `api.v3_documents.legacy_queue_for_manual_review(...)` translates the legacy request by
  driving the **same shared pipeline** as a V3 upload (`create_document_and_enqueue`:
  storage → `organization_files` → batch/item → durable job blocking at the manual-review
  gate). No second queue, no duplicated queue logic.
* `routes/upload.py` auto-repair branch returns the legacy-shaped
  `status="manual_review_required"` payload; missing organisation/file-name/bytes →
  truthful `400` (`LegacyManualReviewError`); nothing is silently discarded.
* Tenant/authorization preserved: `require_org_member()` unchanged; the organisation flows
  into the shared pipeline. Idempotency: one registration per legacy request (legacy call
  semantics preserved).
* Tests re-run: `tests/unit/api/test_legacy_manual_review_adapter.py` (4) and
  `tests/unit/routes/test_step2_legacy_imports.py` (5) **PASS**.
* Release-build evidence: `/api/upload-pdf` is present in the release OpenAPI
  (570 paths); anonymous access is refused (401).

## 11. POD-3 verification — CSV/XLSX parity

Fixture parity re-measured through the release code path (`extract_document`) and locked
by `tests/unit/services/test_structured_file_parity.py` (11 cases, **PASS**):

| Fixture | Before | After |
| --- | --- | --- |
| `mock_uk_fuel_card_messy.csv` | 50 rows, completeness **0.00**, unresolved `activity, quantity, unit` | **1.00**, unresolved `[]` |
| `mock_uk_utility_bill.csv` | 20 rows, **0.67**, `activity` unresolved | **1.00**, unresolved `[]` |
| `mock_scope3.csv` | 1.00 | unchanged (regression guard) |
| synthetic cover-sheet-first XLSX | no data (active-sheet-only read + phantom lines) | data sheet parsed (`source_sheet = "Readings"`), `sheet_names` recorded, headers/rows preserved |

Preview: `StructuredDataPreview` renders CSV/TSV tables and a workbook/sheet-aware XLSX
preview with bounded rows/columns and loading/error/empty states (no iframe, no download
control); frontend tests `structured-data-preview.test.jsx` (5) plus the updated
`secure-document-viewer.test.jsx` **PASS**.

**Production status: NOT verified** — the deployed frontend bundle predates this change
(§20/§22). Local release build evidence: the `structured-preview` marker is present (§18).

## 12. POD-4 verification — controlled P1 rollout

* `shape_mode(env, organization_id)` resolves the effective mode: requested mode (invalid
  → `shadow`) then the organisation allowlist (`CARBONTALLY_P1_ORGANIZATION_ALLOWLIST`);
  `enabled` without an allowlist is downgraded to `shadow` (fail-safe); global enablement
  requires the deliberate wildcard `*`. `rollout_status(...)` is the audit record,
  persisted per extraction; resolution is deterministic, reversible and uncached.
* Tenant context is threaded: `extract_document(..., organization_id=)` →
  `_extract_pdf`/`_extract_image` → `_apply_p1_fidelity(..., organization_id=)`, with the
  worker passing `job.organization_id`.
* Tests re-run: `tests/unit/services/test_p1_controlled_rollout.py` (9) **PASS**;
  `test_extraction_fidelity.py` and `test_p1_image_path.py` updated deliberately and
  **PASS**.
* Production status: **safe default confirmed** — no allowlist is configured, so the
  effective mode remains `shadow`; nothing was enabled by this release.

---

## 13. POD-5 verification — report compatibility layer

* `routes/legacy_reports.py` exposes the two paths the live legacy UI actually calls and
  **delegates** to `reports.generate_enhanced_sustainability_report`. No new reporting
  subsystem, no duplicated business logic.
* Tenant isolation is enforced on the compatibility path
  (`organization_id == caller's organisation`, else 403; no organisation context → 403)
  because the legacy handler trusts the body's organisation id.
* Deprecation signalling: `Deprecation: true`, `Link: </api/v3/reports>;
  rel="successor-version"`. `AUDITOR_EXCEL` keeps the existing truthful
  `400 Unsupported report type` (no workbook fabricated).
* Tests re-run: `tests/unit/api/test_legacy_report_compat.py` (4) **PASS**.
* Production/release-build evidence: both aliases and the legacy
  `/api/reports/generate-enhanced-report` are present in the release OpenAPI (570 paths);
  in production they answer **401** anonymously (previously 404).

## 14. POD-6 retention evidence

* Authorised change: **test only** — `backend/tests/unit/services/test_retention.py`
  (`503d186`, +30/−3). No implementation, schema, policy or configuration change.
* Why: the test pinned the pre-Phase-8-X-X2 eligible-domain set
  (`{"document_retention_days"}`) while `services/retention.py` already carries
  `operational_telemetry_retention_days` under the later PO decision **`PX-7`** (telemetry
  detail 90 days by default, aggregates indefinitely), referenced in
  `docs/cline/reports/CT-P8-REST-PLAN-20260913-027.md` (X7 ↔ `PX-7`) and the X2
  implementation report.
* The correction keeps the invariant: the PX-7 eligible set is asserted, the
  audit/evidence/backup domains must remain ineligible, and the telemetry rule must never
  purge business/evidence/audit tables (asserted via the module's public
  `telemetry_excluded_tables()` accessor).
* Tests: `test_retention.py` + `test_v3_settings.py` + `test_b2_migration.py` → **23
  passed, 0 failed**; the **full backend unit suite now reports 0 failures**.

## 15. F-01 … F-12 final matrix

| ID | Finding | Status | Commit | Evidence | Production status | Remaining limitation |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 | Batch Upload | **Intentionally deferred — unchanged** | — | — | — | No PO decision exists; stays deferred |
| F-02 | CSV/XLSX ingestion broken | **Fixed, tested** | `3849f30` | `test_structured_file_parity.py` (11) | Backend live; **not** exercised with a live upload (see §17) | Authenticated end-to-end acceptance |
| F-03 | CSV/XLSX workspace preview | **Fixed, tested** | `3849f30` | `structured-data-preview.test.jsx` (5) + viewer test | **Not deployed** (frontend promotion pending) | Vercel promotion + UI acceptance |
| F-04 | Legacy manual-review queue absent | **Adapter added, tested** | `a496a37`, `b45721a` | adapter tests (4) + legacy-imports (5) | `/api/upload-pdf` live (401 unauth) | Authenticated retry check |
| F-05 | AI fan-out plan unconsumed | **Consumed under hard limits** | `e5746ed` | POD-1 tests (7) | Engine-dependent; not exercised in prod | Live provider call counts |
| F-06 | P1 global enablement risk | **Controlled rollout** | `9332569` | POD-4 tests (9) | Default `shadow` (no allowlist set) | Enabling a pilot is a PO action |
| F-07 | Report page CSS collapse | **Unverified — unchanged** | — | — | — | No browser automation available (§10) → authenticated audit |
| F-08 | Retired report endpoints 404 | **Compatibility layer** | `948917f` | POD-5 tests (4) | **Live** — both aliases in production OpenAPI (401 unauth) | Excel export absent by design |
| F-09 | Legacy `from main import` sites | **0 remain** | `55be3d2` | legacy-imports (5) | n/a | — |
| F-10 | Queue/item state consistency | **Green, no regression** | Step 2 + POD-1 | `test_step2_remediation.py`, processing suite | n/a | — |
| F-11 | Customer blocked-job visibility | **Green, no regression** | `7666fff` | `customer-blocked-visibility.test.jsx` (302 frontend tests) | Backend live; card not deployed | Vercel promotion + UI acceptance |
| F-12 | Partial extraction persistence | **Green, no regression** | `5d143ac` | `test_step2_remediation.py` | Backend live | — |

**`F-01 Batch Upload = intentionally deferred`** — explicitly preserved.

## 16. P1 final matrix

| P1 requirement | PO authorised | Implemented | Tested | Controlled rollout | Production verified | Commit | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1-D1 fidelity shape hook (PDF + IMAGE) | Yes | Yes | Yes | **Yes** (allowlist; default `shadow`) | Backend live in `shadow` only | `f5e07ed`, `c8b8d81`, `9332569` | `enabled` not active |
| P1-D2 bounded block reason | Yes | Yes | Yes | n/a (`shadow`) | Backend live | `5d143ac` | — |
| P1-D3 per-page AI fan-out | **Yes (POD-1 A)** | Yes | Yes (call counts) | Plan-gated | **Not verified** (no live engine) | `e5746ed` | Live pilot needed |
| P1 §7.3 document-level adjudication | Yes | Yes | Yes (`positional_blending is False`) | n/a | Backend live | `5d143ac`, `e5746ed` | — |
| P1 coverage/fan-out persistence | Yes | Yes | Yes | n/a | Backend live | `5d143ac`, `e5746ed` | — |
| P1 enablement (`enabled`) | Controlled only | Mechanism | Yes | **Yes** | Production remains `shadow` | `9332569` | PO enablement decision |

P1 is **not** claimed fully production-complete: D1/D2/D3 are implemented, tested and
rollout-controlled, but `enabled` is inactive in production and D3 has not been exercised
against a live provider.

---

## 17. CSV/XLSX acceptance

**Verified (code + fixtures + tests)**

* All three real fixtures resolve to completeness **1.00** with `unresolved == []` and
  preserved `source_headers` / `source_row` (§11); the cover-sheet-first workbook parses
  from its data sheet with `sheet_names` recorded.
* Mapping/factor continuity is covered by the existing mapping suites in the green unit
  sweep; the extraction gate (0.50 completeness) now clears for the fixtures that
  previously scored 0.00.

**Authenticated acceptance actually executed (local stack, read-only)**

| Check | Result |
| --- | --- |
| Local GoTrue password grant with a documented demo identity | **token obtained** |
| Release build served from the release SHA (`uvicorn main:app`, 8050) | `/health` **200** |
| `GET /api/v3/documents` anonymous | **401** (authorization enforced) |
| `GET /api/v3/documents?organization_id=<own org>` authenticated | **200**; caller's visible documents = **0** |
| RLS read of `organization_files`, `document_processing_queue`, `manual_extraction_items` as the demo owner | **200**, 0 rows each (tenant-scoped) |
| `GET /api/v3/documents?organization_id=<other org>` authenticated | **403** — server-side tenant isolation |

**Not performed (documented limitation)**

* A live CSV/XLSX **upload → workspace → preview → extraction** acceptance was **not**
  executed. Reasons: (a) the authorised local demo organisation holds **0 documents**, so
  there is nothing to preview without creating data; (b) creating data would mutate the
  protected investor-demo dataset (§55/§14); (c) production requires a session that is
  unavailable (§23); (d) no browser automation exists for the UI preview.
* Per §22 this is recorded as a **clearly documented non-production limitation** rather
  than an unverified claim. Proposed safe path for Step 3: use a dedicated disposable QA
  clone/CLI-seeded QA organisation (not the investor demo) to upload the three fixtures.

## 18. Frontend acceptance

| Check | Evidence | Result |
| --- | --- | --- |
| Frontend unit/integration suite | `Test Suites: 1 failed, 30 passed, 31 total` / `Tests: 302 passed, 302 total` | PASS (1 pre-existing suite-load failure, §21) |
| Production build (non-CI) | `Compiled with warnings. The build folder is ready to be deployed.` | PASS |
| Local build asset (from release SHA) | `build/static/js/main.06974f3e.js` | present |
| Step 2 marker in the local build | `structured-preview` = **1** | **present** |
| Old-behaviour marker | `Document preview is not available` = 1 — *expected*: kept deliberately for genuinely unknown file types; it is **not** the CSV/XLSX path any more | explained |
| Deployed production bundle | `main.1e761f98.js`; `structured-preview` = **0** | **pre-Step-2C build** |
| UI acceptance (preview render, blocked card, CSS) | no browser automation (Playwright/Puppeteer absent; local frontend not serving on :3000) | **NOT performed** |

Note on marker method: the caption phrases (`Workbook preview`, `Data preview`) are built
from template literals and are not reliable string markers after minification; the
stable markers are the `structured-preview` test id and the `ct-wb-viewer__data` class.

## 19. Consultant Client parity

* **Shared by construction (server-side):** POD-1, POD-2, POD-4 and POD-5 are
  backend-side changes, and the consultant item workspace
  (`frontend/src/v3/consultant/ConsultantItemPage.jsx`) documents that it uses the
  **shared `/api/v3/processing/*` surface** with consultant-authorised evidence from the
  same repositories — so automatic processing, manual review, extraction, processing
  status, reporting compatibility and blocked-job data are parity features without any
  consultant-specific code being added.
* **Reuse observed:** the consultant item page imports the shared ops component
  `ExtractionPanel` (the same extraction review surface), and a consultant-specific
  reporting endpoint exists in the API surface
  (`/api/v3/consultants/clients/{client_id}/reports`).
* **Parity gap (documented, not fixed):** the POD-3 structured-file *preview* was added to
  the workbench viewer (`SecureDocumentViewer` → `StructuredDataPreview`) used by the
  customer `ProcessingItemWorkspace` and the ops `WorkItemWorkspace`. The consultant item
  page presents the source document through its own view, so **CSV/XLSX preview parity is
  not delivered to the consultant surface by this change**. Extending it is a
  presentation/UX decision adjacent to D19 and was **stopped as a sub-item** rather than
  improvised (no new consultant functionality invented).
* No consultant-specific functionality was created, and no consultant architecture was
  redesigned.

## 20. Backend tests

| Suite | Result |
| --- | --- |
| **Full unit sweep** (`pytest tests/unit -q`) | **0 failures** (green) — the previously failing retention test is now corrected |
| `test_retention.py`, `test_v3_settings.py`, `test_b2_migration.py` | 23 passed, 0 failed (POD-6) |
| `test_structured_file_parity.py` | 11 passed (POD-3) |
| `test_pod1_bounded_ai_fanout.py` | 7 passed (POD-1; real call counts) |
| `test_p1_controlled_rollout.py` | 9 passed (POD-4) |
| `test_legacy_manual_review_adapter.py` | 4 passed (POD-2) |
| `test_legacy_report_compat.py` | 4 passed (POD-5) |
| `test_step2_legacy_imports.py` | 5 passed (POD-2 contract) |
| `test_automatic_processing.py` (27) / extraction suites (14) / `test_step2_remediation.py` | all passed — no regression |
| Pre-existing failures remaining | **none** in unit scope |
| Integration suites | **not run** — the harness performs destructive `TRUNCATE … RESTART IDENTITY CASCADE` setup and §14/§55 forbid pointing it at the investor-demo database; no disposable clone was created in this task |

---

## 21. Frontend tests

```
Test Suites: 1 failed, 30 passed, 31 total
Tests:       302 passed, 302 total
```

* The failing **suite** is `src/App.test.js` → `Test suite failed to run: Cannot find
  module 'react-router/dom'` — a **pre-existing dependency-resolution issue** in the
  shared `frontend/node_modules` (inherited by the worktree; no Step 2 file involved, zero
  tests failed). It must **not** be reclassified as a Step 2 defect: Step 2 changed none of
  `src/App.js` or its imports, and the failure is a module-resolution error, not an
  assertion failure.
* `CI=true` build note: the CI build fails on **pre-existing legacy `src/App.js`
  `no-unused-vars` warnings** (CRA treats warnings as errors under CI). The non-CI
  production build succeeds and contains **no warning from any Step 2 file**.

## 22. Production deployment evidence

### Backend — **deployed** (auto-deploy on push to `p8-release-reconciled`)

| Evidence | Value |
| --- | --- |
| Deployment marker | `rndr-id: b87594b2-16a1-4bea`, `x-render-origin-server: uvicorn`, `server: cloudflare` |
| `GET /health` | **200** `{"status":"healthy","service":"CarbonTally API","version":"3.0.0",…}` |
| `GET /` | **200** `{"message":"CarbonTally API","version":"3.0.0","status":"healthy","api_version":"v3","routes_count":49}` |
| `GET /openapi.json` | **200**, **570 paths** |
| POD-5 aliases live | `/api/generate-enhanced-report`, `/api/generate-sustainability-report` — anonymous **401** (previously **404**) |
| Legacy route unchanged | `/api/reports/generate-enhanced-report` — anonymous **422** (validation) |
| Unexpected 5xx | none observed |

The deployed backend build was verified **by route surface**, not by timestamp: the two new
aliases can only exist in a build containing `routes/legacy_reports.py` (POD-5). The same
route surface was reproduced locally from the release worktree at `503d186` (570 paths,
identical alias set).

### Frontend — **NOT deployed** (blocked: no provider access)

| Evidence | Value |
| --- | --- |
| Production `index.html` asset | `main.1e761f98.js` (1,955,456 bytes) |
| `structured-preview` marker | **0** (absent) |
| Conclusion | production serves the **pre-Step-2C** bundle; the Step 2 frontend work is not live |
| Blocker | `vercel` CLI **absent**; no `~/.vercel` / `~/.config/vercel` auth; no Vercel/Render deployment keys in the environment or project env files; Vercel production promotion needs dashboard/credential access this environment lacks |

**Required PO action (one step):** promote the `p8-release-reconciled` build (code tip
`503d186`) to Vercel production, then re-run the frontend acceptance checks in §18/§23.

## 23. Production acceptance

| Check | Result |
| --- | --- |
| API health (`/health`, `/`) | **200** both |
| OpenAPI contract | **200**, 570 paths; Step 2 endpoints present |
| Legacy report aliases (anonymous) | **401** (authorization enforced) |
| Legacy report route (anonymous) | **422** (validation; unchanged) |
| Frontend build identity | **not the Step 2 build** (marker absent) |
| Authenticated production acceptance (CSV/XLSX upload→preview→extraction; blocked card; reports lifecycle; consultant surface) | **NOT PERFORMED** — no production session/credentials available; **not claimed** |
| Local authenticated acceptance instead (read-only) | anonymous 401; authenticated `GET /api/v3/documents` **200**; cross-organisation **403**; RLS reads tenant-scoped |
| Destructive tests / bulk processing / storage changes | **none performed** |
| Production data modified | **none** (read-only probes only) |
| Schema drift introduced | **none** |

---

## 24. Database / storage / configuration impact

* **Database:** no migration added, no schema change, no RLS change, no SQL executed. POD-6
  changed only a test file. All Step 2 persistence uses existing JSONB/metadata fields.
* **Storage:** no bucket created/modified/emptied; no object uploaded, deleted or
  rewritten; no signed URL logged. The documents-bucket MIME situation was already
  addressed by the PO; no bucket-policy change was made.
* **Configuration:** one new optional, fail-safe variable
  (`CARBONTALLY_P1_ORGANIZATION_ALLOWLIST`); the pre-existing
  `CARBONTALLY_P1_EXTRACTION_SHAPE` now honours `enabled` only for allowlisted
  organisations. **Production currently has no allowlist ⇒ effective mode `shadow`.**
* **Local environment note:** the read-only acceptance probe served the release build
  locally (`uvicorn main:app` on 127.0.0.1:8050, environment read from the existing
  `backend/.env`). The server was stopped at the end of the probe; no project file was
  modified and no secret values were printed.
* **Secrets:** none added to the repository, the report, logs or any commit.

## 25. Complete commit / push ledger

| SHA | Purpose | Pushed | In remote |
| --- | --- | --- | --- |
| `0d21e46` | F-046-1 protected-persistent-target guard | yes | yes |
| `f5e07ed` | P1-D1 extraction-fidelity hook + pipeline `v3-auto-1.1` | yes | yes |
| `eb6a0c2` | S6 report-lifecycle visibility | yes | yes |
| `5d143ac` | Step 2 WS-A partial extraction persistence, P1 §7.3 adjudication, P1-D2 block reason, coverage persistence | yes | yes |
| `c8b8d81` | Step 2 WS-B B3 P1 hook on the IMAGE path | yes | yes |
| `55be3d2` | Step 2 WS-C legacy `from main import` repairs | yes | yes |
| `7666fff` | Step 2 WS-H customer-visible blocked jobs | yes | yes |
| `3849f30` | Step 2C POD-3 CSV/XLSX parity | yes | yes |
| `a496a37` | Step 2C POD-2 compatibility adapter | yes | yes |
| `b45721a` | Step 2C POD-2 test-contract update | yes | yes |
| `9332569` | Step 2C POD-4 controlled P1 rollout | yes | yes |
| `948917f` | Step 2C POD-5 report compatibility | yes | yes |
| `e5746ed` | Step 2C POD-1 bounded AI fan-out | yes | yes |
| `2f6e1d5` | Step 2C report (docs) | yes | yes |
| `6beb281` | Step 2C report header correction (docs) | yes | yes |
| **`503d186`** | **POD-6 stale-test correction (this task, test-only)** | **yes** | **yes (verified)** |
| *(report commit)* | **This closure report (docs)** | **yes** | **yes (verified after push)** |

## 26. Unresolved risks

1. **Frontend not promoted** — the customer-visible Step 2 improvements (structured
   CSV/XLSX preview, blocked-job card, S6 lifecycle panel) are not live. Primary blocker.
2. **No authenticated production acceptance** — not performed; production behaviour of the
   Step 2 changes is asserted from route surface plus local authenticated probes.
3. **F-07 CSS** — unverifiable here (no browser automation); must be closed by an
   authenticated audit in Step 3.
4. **Consultant preview parity** — presentation-level gap (§19); defect fix vs product
   decision still to be chosen by the PO.
5. **AI fan-out live behaviour** — limits/fallbacks proven with doubles; live call counts
   and costs unobserved.
6. **P1 enablement** — remains `shadow`; enabling a pilot is a PO action.
7. **Integration suites not run** — the harness is destructive by design; a disposable
   clone is required first.
8. **Auditor Excel export** — offered by the legacy UI; no generator exists; the adapter
   answers truthfully.

## 27. Deferred items

| Item | Disposition |
| --- | --- |
| **F-01 Batch Upload** | **Intentionally deferred** (no PO decision) |
| F-07 CSS report-page collapse | Deferred to Step 3 authenticated acceptance |
| Consultant CSV/XLSX preview parity | Deferred — needs a product/UX decision |
| Auditor Excel export (`AUDITOR_EXCEL`) | Deferred — needs a product decision |
| P1 `enabled` rollout for a pilot organisation | Deferred — PO configuration action |
| Disposable QA clone for integration/e2e acceptance | Deferred — Step 3 environment work |
| Documents-bucket MIME/size policy | Already actioned by the PO; no residual work |

---

## 28. Final release identity

| Surface | Identity |
| --- | --- |
| Release branch | `p8-release-reconciled` |
| Code/test tip | `503d18611cf040852468b31b7705e74acce9ffe2` (== origin, verified) |
| Backend deployed | **live**, verified by route surface (570 OpenAPI paths incl. both POD-5 aliases and `/api/upload-pdf`), `rndr-id: b87594b2-16a1-4bea`, `/health` 200, `/` 200 |
| Frontend deployed | **`main.1e761f98.js`** — pre-Step-2C; the Step 2C artefact built from `503d186` is `main.06974f3e.js` (contains the `structured-preview` marker, 1) and is **not yet promoted** |
| Pipeline version | `v3-auto-1.1` (P1 stamp from `f5e07ed`) |
| Remote SHA at closure | the report commit — verified equal to local `HEAD` after push |

## 29. Change-control proof

| Proof | Value |
| --- | --- |
| Starting SHA (verified) | `6beb281cb9128a16d9c25459ad4fe53ef350d539` (== remote at start) |
| Ending SHA | the report commit (== remote after push); code/test tip `503d186` |
| Commits added by this task | 2 — 1 test-only code commit + 1 documentation commit |
| Files changed by this task | `backend/tests/unit/services/test_retention.py` (test-only) + this report |
| Diff vs previous closure tip (before the report commit) | exactly **1 file**: `backend/tests/unit/services/test_retention.py` (+30/−3) |
| Every changed file explained | the retention test = POD-6 authorised stale-expectation correction; no other file touched |
| Worktree | clean; no staged changes; generated artefacts (`frontend/nohup.out`) removed |
| `main` branch | **not pushed to, not modified** |
| Protected dirty tree | HEAD `20b7a92`, branch `main`, dirty **298 → 298**, staged 0 before and after (untouched) |
| Secrets | none committed (no `.env`, token, key, JWT or signed URL in any diff; no secret value printed) |
| Destructive operations | none (no reset/clean/stash/delete/force-push; no TRUNCATE; no storage deletion) |
| Production data | unmodified (read-only probes only) |
| Batch Upload | remains deferred |
| Step 3 | **not started** |

## 30. Final verdict

`STEP 2 FUNCTIONAL REMEDIATION PARTIALLY COMPLETE — PO REVIEW REQUIRED`

Why not `STEP 2 COMPLETE — READY FOR STEP 3`: the §22 criteria require **frontend production
deployment verified** and **authenticated production acceptance** (CSV/XLSX end-to-end,
blocked-job visibility, consultant parity through the live surface). Neither could be
performed here because this environment has **no Vercel credential/CLI access**, no browser
automation, and no production session. Everything else in the criteria set is satisfied:

* all authorised Step 2 implementation is committed, tested and pushed;
* local and remote release SHAs match (`503d186`, verified);
* **no verified implementation remains unbanked** (16 workstream commits all in release
  ancestry; the protected dirty tree and the stray `fx12-publish` branch contain no Step 2
  work);
* backend production deployment is verified by route surface, not by timestamp;
* the retention test is corrected and the **full backend unit suite is green (0 failures)**;
* no critical Step 2 regression remains;
* every remaining item is explicitly deferred or requires a future PO decision.

**Immediate PO actions to reach `STEP 2 COMPLETE` (both mechanical — no code work):**

1. Promote `p8-release-reconciled` (code tip `503d186`) to Vercel production.
2. Provide an authenticated production or QA session (or authorise a disposable QA clone)
   so CSV/XLSX end-to-end, blocked-card, report-lifecycle and consultant-parity acceptance
   can be executed and F-07 CSS closed.

**Step 3 has not been started.** The PO will review this report before Step 3 begins.









