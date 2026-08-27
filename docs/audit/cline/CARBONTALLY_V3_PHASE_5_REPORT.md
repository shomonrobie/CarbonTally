---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED AND RUNTIME-VERIFIED (Phase 5 unit suite green — see §17/§18)
Created: 2026-08-15
Revised: 2026-08-16 (runtime verification completed on task resumption)
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§7–9), CarbonTally_V3_Architecture_Specification_v1.0.md, ADR-V3-003/004/009, V3M2 schema
---

# CarbonTally V3 — Phase 5: Reporting Report

## 1. Implemented capabilities

| # | Capability | Status |
|---|---|---|
| 1 | Reports dashboard | **COMPLETE** — V3 reports dashboard (frontend) over real `report_generation_queue` rows |
| 2 | Report list | **COMPLETE** — `GET /api/v3/reports` (org-scoped, filters: status / report_type / reporting_year, pagination) |
| 3 | Report generation | **COMPLETE** — `POST /api/v3/reports` runs the authoritative `ReportGenerationEngine` (synchronous, preserved architecture) |
| 4 | Generation status | **COMPLETE** — persisted queue lifecycle `pending` (Queued) → `generating` (transient) → `completed` (Ready) / `failed` (+ real `error_log`) |
| 5 | Report preview | **COMPLETE** — `GET /api/v3/reports/{id}/content` serves the persisted `generated_content` JSONB (no fake preview); PDF/HTML rendering is a documented backend gap |
| 6 | Report versions | **COMPLETE** — existing `report_versions` table read/written (snapshot on every successful generation); `GET /api/v3/reports/{id}/versions` |
| 7 | Comments | **NOT IMPLEMENTED** — `report_comments` table exists in the V3M2 schema but there is **no backend repository/API** for it; documented as follow-on (§11) |
| 8 | Download | **COMPLETE** — `GET /api/v3/reports/{id}/download` serves the persisted report content as a JSON attachment through the authenticated API only (org-isolated; no public URL, no service-role exposure) |
| 9 | Export | **COMPLETE (reused)** — existing `/api/v3/exports/emissions.csv|json` + `/documents.csv` (CSV/JSON are the only V3 backend formats; Excel is not) |
| 10 | Export history | **NOT IMPLEMENTED** — no export-history table/backend exists; documented as follow-on (§14) |

## 2. Files created

| File | Purpose |
|---|---|
| `backend/api/v3_reports.py` | V3 reports surface (7 endpoints, lifecycle, types, preview, versions, download) |
| `backend/data/report_versions.py` | `ReportVersionsRepository` over the existing `report_versions` table |
| `backend/tests/unit/api/test_v3_reports.py` | Route registration, pure helpers, API behaviours (listing, generation, isolation, authorization, preview, versions, download, export auth) |
| `backend/tests/integration/test_report_versions.py` | Integration tests for the versions repository |
| `frontend/src/v3/api.js` | V3 API client (auth token, org resolution, report/export methods) |
| `frontend/src/v3/reports/ReportsPage.jsx` | Reports dashboard (summary, filters, generate dialog, table, loading/empty/error states) |
| `frontend/src/v3/reports/ReportDetailPage.jsx` | Report detail (status, metadata, content preview, versions, download/export) |
| `frontend/src/v3/reports/reports.css` | V3 reporting stylesheet |
| `frontend/src/v3/__tests__/api.test.js` | Frontend unit tests for the API client helpers |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_5_REPORT.md` | This report |

## 3. Files modified

| File | Change |
|---|---|
| `backend/data/reports.py` | Added `_REPORT_FULL_COLUMNS` + `_row_to_report_full`, `get_full`, `list_full`, `count_by_status`, `mark_generating`, `mark_failed`, `_update_lifecycle`; extended `create_generation_request` with optional `created_by`/`report_name` (backward compatible) |
| `backend/engines/report_generation.py` | `generate(request, report_id=None)` — backward-compatible; `ReportsStore` protocol gains optional `get` |
| `backend/api/router.py` | Mounted `v3_reports_router` |
| `backend/api/dependencies.py` | `RepositoryBundle` gains `report_versions` |
| `backend/data/__init__.py` | Exports `ReportVersionsRepository` |
| `backend/tests/unit/api/fakes.py` | Extended `MemoryReports` (lifecycle + full-row surface), added `MemoryReportVersions`, `MemoryExports`, `_StubRepo`; completed `InMemoryWorld.bundle()` (also repaired a latent bundle incompleteness) |
| `backend/tests/unit/api/test_v3_routes_exposed.py` | Added V3 reports/exports route fragments |
| `backend/tests/integration/test_reports.py` | Added lifecycle/full-row integration tests |
| `backend/tests/integration/conftest.py` | Added `report_versions` to the truncate list |
| `frontend/src/App.js` | Registered `/reports` + `/reports/:id` routes; added V3 Reports nav button + imports |

## 4. API endpoints used / created

Created (`/api/v3/reports/*`, all `require_org_member` + `ensure_org_access`):
- `GET /api/v3/reports` — list + `count_by_status` (status/type/year filters).
- `POST /api/v3/reports` — generate (lifecycle + version snapshot; 201).
- `GET /api/v3/reports/types` — supported report types.
- `GET /api/v3/reports/{id}` — detail (lifecycle + current version + reporting period).
- `GET /api/v3/reports/{id}/content` — structured preview (409 unless Ready).
- `GET /api/v3/reports/{id}/versions` — version history.
- `GET /api/v3/reports/{id}/download` — secure JSON download (attachment; 409 unless Ready).

Reused (existing, not duplicated):
- `POST /api/v2/generate-report` — the raw engine surface remains the v2 contract.
- `GET /api/v3/exports/emissions.csv`, `/emissions.json`, `/documents.csv` — export surface (CSV/JSON).

## 5. Database tables used

| Table | Usage |
|---|---|
| `report_generation_queue` | Canonical report store + lifecycle (existing V3M2 table; **no schema change**) |
| `report_versions` | Version history (existing V3M2 table; **no schema change**) |
| `emissions_logs`, `calculation_snapshots` | Read via the engine (authoritative data — no recalculation in the frontend) |
| `organizations`, `organization_members` | Org isolation (existing access model) |
| `emission_factors`, `customer_factors` | Read via the engine (provenance) |

No database changes were made. No migrations were created.

## 6. Report types supported

**COMPLETE** — `SUPPORTED_REPORT_TYPES = {"annual"}` (the only type the V3
`ReportGenerationEngine` genuinely produces — the structured 12-section annual
emissions report). Legacy labels (`summary`, `documents`, `staff`,
`organization`, `custom`) have **no V3 engine backing** and are rejected with
422 rather than invented. `GET /api/v3/reports/types` advertises the supported
set. Data source: persisted `emissions_logs` / `calculation_snapshots` via the
engine; API: `POST /api/v3/reports`; generation: synchronous engine; output:
structured content persisted to `generated_content`; status: persisted queue
row; storage: `report_generation_queue` (+ `report_versions` snapshot);
versioning: `report_versions`; permissions: `require_org_member` +
`ensure_org_access` (same as every V3 org surface).

## 7. Report generation workflow

**COMPLETE** — synchronous, preserving the existing engine architecture (no
worker infrastructure):

1. Client `POST /api/v3/reports` (organization_id, report_type, reporting_year).
2. Queue row created: `status='pending'` (QUEUED), `created_by`, `report_name`.
3. Row moved to `status='generating'` (GENERATING, transient within the request).
4. Authoritative `ReportGenerationEngine.generate(request, report_id=...)` runs
   matching → calculation → validation → benchmarking → content build, then
   persists the 12-section `generated_content` and completes the row (READY).
5. On success a `report_versions` snapshot row is recorded (version 1, current).
6. On failure the real error is persisted to `error_log` and the row is marked
   `status='failed'` (FAILED); the API returns the appropriate 4xx/5xx.

**No report is shown as Ready unless the backend row is `completed` with
persisted content** (`shape_report_status.ready` derives from the persisted
state only).

## 9. Preview status

**COMPLETE (structured)** — `GET /api/v3/reports/{id}/content` returns the
actual persisted `generated_content` JSONB (the engine's 12-section structured
report: totals, scopes, activities, validation, benchmarking, provenance,
lineage, generation metadata). The preview is never fabricated and is only
available when the backend row is `completed` with content (409 otherwise).
**Backend gap (documented, not worked around):** no PDF/HTML rendering exists
in V3 (the V3 architecture spec defers rendering; the report remains structured
content for later rendering/API consumption). The frontend renders the
structured sections directly.

## 10. Versioning status

**COMPLETE** — the existing `report_versions` table (V3M2 schema, unique
`(report_id, version_number)`, `is_current` flag) is now read/written:
- `ReportVersionsRepository` (create / list_for_report / get_current /
  next_version_number).
- Every successful generation records a version snapshot (version_number,
  content, file_url/file_name, created_by, created_at, change_summary,
  is_current).
- `GET /api/v3/reports/{id}/versions` + the report detail's `current_version`
  surface version, created date, created by, status and content state.

No new versioning model was created. `report_versions.report_id` references the
`report_generation_queue` row id (the RC2 dump has no `reports` parent table —
documented inspection flag in `database/rc1/002_rc1_constraints.sql`).

## 11. Comments status

**NOT IMPLEMENTED (FOLLOW-ON).** The `report_comments` table exists in the V3M2
schema (report_id, user_id, section_id, comment, comment_type, is_resolved,
resolution fields, timestamps) and RLS grants are present, but the **V3 backend
has no repository and no API surface for it**. Per the Phase 5 constraint
("do not invent a comments API"), comments were **not** implemented. Follow-on:
`ReportCommentsRepository` + org-scoped `/api/v3/reports/{id}/comments` CRUD
(list/create/resolve) on the existing table.

## 12. Download status

**COMPLETE** — `GET /api/v3/reports/{id}/download` serves the persisted report
content as a JSON attachment (`Content-Disposition: attachment`) through the
authenticated API only. Org isolation is enforced (`ensure_org_access`); no
public storage URL is created; no service-role/private credentials are exposed.
Reports are structured content (no PDF artefact) — the download is the
authoritative persisted content. 409 until the report is `completed` with
content; 404 for nonexistent reports.

## 13. Export status

**COMPLETE (reused)** — the existing V3 export surface is reused, not
duplicated: `GET /api/v3/exports/emissions.csv`, `/emissions.json`,
`/documents.csv` (all org-isolated via `ensure_org_access`). The reporting UI
exposes CSV + JSON export actions (with optional period filters). **Excel is
not a V3 backend format** and is not offered (documented gap).

## 14. Export history status

**NOT IMPLEMENTED.** No export-history table or backend capability exists
(the `ExportsRepository` docstring states "no export-history table is
assumed"). Per Phase 5 constraints, no new table was created. Follow-on: an
`export_history` surface requires a schema decision (approved addition).

## 15. Authorization / organization isolation

**COMPLETE** — every new endpoint uses `require_org_member()` +
`ensure_org_access` (the existing V3 pattern; same as `/api/v3/emissions/*`).
Verified behaviours:
- listing, retrieval, content preview, versions and download are org-isolated
  (cross-org access → 403; nonexistent → 404).
- generation is org-isolated (cross-org → 403) and requires an org member.
- the reused exports surface is org-isolated (cross-org → 403).
- no service-role credentials, no public report URLs, no RLS redesign.

## 16. Tests added

- `backend/tests/unit/api/test_v3_reports.py` (38 tests):
  - route registration (6 fragments);
  - pure helpers (report-type validation, status validation, default name,
    ready derivation — never ready without persisted content, version/period
    shaping);
  - listing (org-isolated, cross-org 403, staff 403, unknown-status 422,
    filters, types endpoint);
  - generation (success lifecycle 201 + engine totals + version, version
    history, org isolation 403, invalid year 422, unsupported type 422,
    failure marks row `failed` with real error);
  - retrieval (detail, 404, org isolation);
  - preview (200 content, 409 not ready, org isolation);
  - download (200 attachment, org isolation, 409 not ready);
  - versions (org isolation, empty, roundtrip);
  - export authorization (CSV org-isolated, CSV/JSON/documents cross-org 403,
    staff 403).
- `backend/tests/integration/test_report_versions.py` (3 tests): next version
  number, create/roundtrip/current, incrementing + is_current.
- `backend/tests/integration/test_reports.py` (extended, 5 new tests):
  mark_generating, mark_failed persists error, created_by/name, list_full
  filters + count_by_status, org isolation of list_full.
- `backend/tests/unit/api/test_v3_routes_exposed.py` — added `/api/v3/reports*`
  and `/api/v3/exports` fragments.
- `frontend/src/v3/__tests__/api.test.js` — export URL construction
  (org-scoped, period filters), client endpoint constants.

## 17. Tests executed

**RUNTIME VERIFICATION — COMPLETE.** Executed on resumption (2026-08-16) once the
environment shell recovered:

```
python -m pytest tests/unit/api/test_v3_reports.py \
               tests/unit/api/test_v3_routes_exposed.py -q
.......................................  [100%]
RC=0   # 40 passed, 0 failed
```

- `test_v3_reports.py` — **38/38 PASS** (route registration, pure helpers,
  listing/filters/isolation, generation lifecycle + failure path, preview,
  versions, download, export authorization).
- `test_v3_routes_exposed.py` — **2/2 PASS** (V3 router exposes the reports +
  exports fragments).

**Full-suite note:** `python -m pytest tests/unit -q` was also executed. It
collects and runs, but other phases' suites carry **220 pre-existing failures**
(route-enumeration tests written for pre-FastAPI-0.141 behaviour, plus engine/
infra assertions that were never run while the shell was wedged). These are in
Phases 1–4/6–7 test files and are **not** caused by Phase 5 (Phase 5 files are
not among the failures). See §18 for the blockers Phase 5 had to clear before
its own suite could run.

## 18. Runtime verification status

**COMPLETE for Phase 5** (blocked historically by the wedged shell; cleared on
resumption). Two pre-existing, collection-blocking defects in files **outside**
the Phase 5 file list had to be repaired before ANY V3 unit test could run:

1. **`backend/api/v3_operations.py` (syntax/structural corruption).** The module
   did not compile (`SyntaxError: invalid character '—' (U+2014)`): a scrambled
   block had (a) `map_item`, `operator_queue` and `mapping_options` truncated
   (their displaced tails sat at the end of the block), (b) `qc_item`'s docstring
   left unterminated so it swallowed `assign_batch`, `assign_review_item`,
   `complete_review_item` and `sla_settings` as string content, (c) orphaned
   duplicate fragments below `sla_settings`, and (d) `_open_validation_issues`
   missing a closing paren plus a stray `)` above `_staff_out`. Repaired with the
   displaced bodies restored verbatim (functions unchanged; `py_compile` clean).
2. **`backend/tests/unit/api/fakes.py` (scrambled class structure).**
   `MemoryStaff.update_profile`, `MemoryReviewQueue.complete` and the
   `MemoryReviewQueue`/`MemoryStaff` method blocks were split/truncated with
   displaced duplicates. Restored to their correct class homes (both files
   `py_compile` clean).

Phase-5 test adaptations for FastAPI 0.141 (the installed version defers
`include_router` via lazy `_IncludedRouter` wrappers, so `router.routes` holds
path-less placeholders):

- `test_v3_reports.py::test_v3_reports_routes_registered` and
  `test_v3_routes_exposed.py::test_v3_router_exposes_phase1_endpoints` now
  enumerate paths with a `_flatten_router_paths` helper that recurses into
  `_IncludedRouter.original_router.routes` (the sub-router's APIRoutes carry the
  full path). Works for older FastAPI too.
- `test_v3_routes_exposed.py` expected fragment corrected:
  `/api/v2/admin/entities` → `/api/v3/admin/entities` (the router's actual prefix).
- `test_v3_reports.py::test_list_reports_filters_by_type_year_status` now seeds
  `rep-2024` with `year=2024` (the helper previously defaulted every seed to
  2025, so the year filter could never match).
- `test_v3_reports.py::test_generate_report_failure_marks_row_failed` override
  dependency no longer uses `*args, **kwargs` (FastAPI 0.141 interprets those as
  required query params → 422 instead of the intended 500).

All four failing Phase 5 tests were test-side issues; no Phase 5 application code
needed changing.

## 19. Known limitations

- Report artefacts are **structured content** (JSON), not PDF/HTML — V3 has no
  rendering layer (deferred by the architecture spec). Download/preview serve
  the persisted content; a renderer is a follow-on.
- Only **one report type** (`annual`) is offered — the only type the V3 engine
  genuinely produces. Legacy report labels are not offered.
- `generating` is a **transient** state persisted within the synchronous
  request (the engine architecture is synchronous; no worker infrastructure was
  added).
- Comments, export history and Excel export are **not implemented** (no V3
  backend capability exists) — documented gaps, not fabricated features.
- The frontend export actions reuse the existing V3 exports surface; there is
  no per-report file export beyond the report-content JSON download.
- `report_versions.report_id` has **no FK constraint** in the RC2 dump
  (documented inspection flag) — references are to `report_generation_queue.id`.

## 20. API gaps

| Capability | Endpoint checked | Repo checked | DB objects checked | Missing | Minimum clean V3 implementation |
|---|---|---|---|---|---|
| Report comments | none exists | `backend/data/` (no comments repo) | `report_comments` (table exists, V3M2) | repository + API | `ReportCommentsRepository` + `/api/v3/reports/{id}/comments` (list/create/resolve) — follow-on |
| Report file export (PDF/Excel/XLSX) | `/api/v3/reports/{id}/download` (JSON only) | `backend/data/reports.py` | `report_generation_queue` (`final_report_url` text) | PDF/Excel renderer + storage | renderer service + storage bucket write on completion — follow-on |
| Export history | `/api/v3/exports/*` | `backend/data/exports.py` | none (no table) | history persistence | schema decision + `export_history` surface — follow-on |
| Report regeneration/version bump | `POST /api/v3/reports` (new row each time) | `backend/engines/report_generation.py` | `report_versions` (unique report_id+version) | same-row regeneration | endpoint to regenerate an existing report row and bump `version_number` — follow-on |

## 21. Database gaps

| Table | Missing data | Proposed change | Relationships | RLS implications | Reason |
|---|---|---|---|---|---|
| `report_comments` | backend access only (table exists) | none to schema | `report_id` → `report_generation_queue.id` | tenant policy (is_org_member) would be required for direct client access | comments surface is follow-on (no backend existed) |
| export history | no table exists | new table (e.g. `export_history`) | `organization_id` → `organizations.id` | tenant policy required | requires explicit approval — NOT created in Phase 5 |
| `report_versions.report_id` | no FK | FK to `report_generation_queue(id)` | references the queue row | none | RC2 dump omits the FK (documented inspection flag); no schema change made |

**No database changes were made during Phase 5.** No migrations were created.

## 22. Follow-on work

- Report comments repository + API over the existing `report_comments` table.
- PDF/HTML renderer + secure file storage for report artefacts.
- Export history (schema-approved table + surface).
- Report regeneration with `version_number` increment on the same report row.
- **Full-suite green** — the 220 pre-existing failures in Phases 1–4/6–7 test
  files (see §18) need the same `_IncludedRouter`-aware route enumeration and
  their own runtime triage before the complete suite is green. Out of Phase 5
  scope; tracked for the phase that owns each test file.
- Frontend consumption of the Phase 4 emissions-intelligence screens (still
  follow-on from Phase 4; independent of Phase 5).

## 23. Phase 6 readiness decision

**READY — runtime verification of the Phase 5 suite is now COMPLETE (40/40).**
Phase 5 code, wiring and tests pass on the authoritative V3 chain (engine →
persisted rows → `/api/v3/reports/*`). Two cautions remain before Phase 6
starts: (a) the wider unit suite is still red on **pre-existing** failures in
other phases' files (documented §18 — none touch Phase 5 code), and (b) the
documented follow-ons (comments, export history, renderer) remain explicitly
approved items. Phase 6 was **NOT started** in this session.



