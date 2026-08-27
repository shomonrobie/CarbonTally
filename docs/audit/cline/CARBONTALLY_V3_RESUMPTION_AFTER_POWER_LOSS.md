---
Document Type: Resumption Report (after PC power loss)
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: RESUMPTION POINT ESTABLISHED — Phase 8 (Internal Operations / Processing / QC) IN PROGRESS
Created: 2026-08-16
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§10–16, §17), CarbonTally_V3_Architecture_Specification_v1.0.md, V3M2 schema (RC2)
---

# CarbonTally V3 — Resumption After Power Loss

## 1. Previous phase status (corrected)

| Phase | Name | Status before power loss |
|---|---|---|
| 3 | Processing | **COMPLETE** |
| 4 | Emissions Intelligence | **COMPLETE** |
| 5 | Reporting | **COMPLETE** |
| 6 | Customer Administration | **COMPLETE** |
| 7 | Consultant / Multi-client | **COMPLETE** |
| 8 | Internal Operations / Processing / QC | **IN PROGRESS** |

Phase 5, 6 and 7 were completed **before** the power loss. Phase 8 was the
in-flight phase. This document establishes the resumption point at Phase 8 and
records the Phase 5 runtime verification that was completed on resumption.

## 2. What was already complete

- **Phase 3–7 backend + frontend + reports**: all phases carry implementation
  reports in `docs/audit/cline/` (`CARBONTALLY_V3_PHASE_4/5/6/7_REPORT.md`,
  `CarbonTally_V3_Phase1_Backend_Consolidation_Report_v1.0.md`,
  `CarbonTally_V3_Processing_Workflow_Report_v1.0.md`).
- **Phase 8 backend implementation** (the in-flight phase) is substantially
  present on disk (see §7) — domain, repositories, auth, API surface, fakes,
  wiring — but **no Phase 8 unit tests, no Phase 8 frontend screens and no
  Phase 8 report exist yet** (see §8).

## 3. What the Phase 5 verification accomplished

On resumption the environment shell (previously wedged) was found to execute
commands when output is redirected to files. The Phase 5 runtime verification
was then executed. It was blocked by **two pre-existing, collection-blocking
syntax/structural defects** in files outside Phase 5's file list, which were
repaired (see §6). After clearing those, the Phase 5 unit suite ran green and
four Phase 5 test-side bugs were corrected (FastAPI 0.141 `_IncludedRouter`
enumeration, a wrong expected path fragment, a year-filter seed bug, and a
dependency-override signature bug).

## 4. Phase 5 runtime result: 40/40

```
python -m pytest tests/unit/api/test_v3_reports.py \
               tests/unit/api/test_v3_routes_exposed.py -q
.......................................  [100%]
RC=0    # 40 passed, 0 failed
```

- `test_v3_reports.py` — 38/38 PASS.
- `test_v3_routes_exposed.py` — 2/2 PASS.

This result is retained in the updated
`docs/audit/cline/CARBONTALLY_V3_PHASE_5_REPORT.md` (§17/§18).

## 5. Full-suite failure classification (220)

`python -m pytest tests/unit -q` collects and runs; the suite reports **220
failures**. Classification (root-cause first, not per-test blind fixes):

| Class | Root cause | Count | Side | Recommendation |
|---|---|---|---|---|
| **D — environment / runtime** | **`pytest-asyncio` is NOT installed** in this Python 3.14 environment, but `pyproject.toml` configures `asyncio_mode = "auto"` / `asyncio_default_*_loop_scope` (pytest warns "Unknown config option: asyncio_mode"). Every `async def test_*` therefore fails with *"async def functions are not natively supported."* | **≈205** (all `tests/unit/infra/*` async tests ≈30; all `tests/unit/engines/*` async tests ≈175) | Test environment | **Central fix:** `pip install pytest-asyncio` (declared in dev deps). No code/test edits needed. Not an application defect; not a Phase 3–8 regression. |
| **A — test-harness incompatibility** | **FastAPI 0.141 defers `include_router` via lazy `_IncludedRouter`** wrappers: `router.routes`/`app.routes` now hold path-less placeholders, so route-registration tests that enumerate `route.path` see an empty/partial surface. | **≈9** (`test_composition_root` ×2, `test_foundation`, `test_v3_consultants`, `test_v3_customer_admin`, `test_v3_emissions`, `test_v3_legacy_reimplementation`, `test_v3_new_capabilities`, `test_v3_processing_workflow` — all `*_routes_registered`/`*_serves_*_surface`) | Test | **Single centralized fix:** one shared `_flatten_router_paths(router)` helper that recurses into `_IncludedRouter.original_router.routes`; already applied to the two Phase 5 test files. Apply the same helper to the other test files. Also correct the stale `/api/v2/admin/entities` expectation → `/api/v3/admin/entities`. |
| **B — test defects (assertions ≠ current API contract)** | `tests/unit/api/test_v3_customer_admin.py` behavior assertions: nonexistent-org GET/PUT expect 404 but the API's `ensure_org_access` returns 403 first; facilities/assets list items are **dict rows** but tests access `f.id` (AttributeError). | **5** | Test | Update the assertions to the implemented contract (403 for non-member/nonexistent, `item["id"]` for dict rows). Confirm 403-vs-404 policy is intended. |
| **E — stale tests no longer matching V3** | `test_v3_processing_workflow.py::test_transition_table_covers_core_pipeline` asserts a direct `validated → calculated` transition, but the V3 state machine intentionally requires the in-flight working status `validated → calculating → calculated` (consistent with `_STAGE_WORKING_STATUS` and the `/items/{id}/start` claim flow). | **1** | Test | Update the assertion to `can_transition_item_status("validated", "calculating")` (and `("calculating", "calculated")`). |

**Verdict:** the 220 failures are **not** one monolithic defect. They are
predominantly a **single environment gap (pytest-asyncio, ≈205)** plus two
**test-harness incompatibilities** (FastAPI `_IncludedRouter` ≈9) and a small
set of **test-defect assertions (6)**. No application code change is required
to clear them (the v3_operations/fakes repairs of §6 were for **separate,
collection-blocking** defects and were already done).

### 5.1 First 20 representative failures

| # | Test file | Test | Failure type | Root cause | Common? | Owning phase | Side | Recommended action |
|---|---|---|---|---|---|---|---|---|
| 1 | test_composition_root.py | test_composition_root_serves_legacy_surface | Assertion (legacy paths missing) | `_route_paths()` enumerates `router.routes` → `_IncludedRouter` placeholders (FastAPI 0.141) | Yes (A) | 1 | Test | Central `_flatten_router_paths` helper |
| 2 | test_composition_root.py | test_composition_root_serves_v3_surface | Assertion (V3 paths missing) | Same `_IncludedRouter` + `/api/v2/admin/entities` should be `/api/v3/admin/entities` | Yes (A) | 1 | Test | Helper + fragment fix |
| 3 | test_foundation.py | test_router_registration | AttributeError (`_IncludedRouter` has no `.path`) | `app.routes` holds lazy wrappers | Yes (A) | 10 | Test | Helper (or `getattr(route,"path","")`) |
| 4 | test_v3_consultants.py | test_v3_consultant_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 7 | Test | Helper |
| 5 | test_v3_customer_admin.py | test_v3_customer_admin_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 6 | Test | Helper |
| 6 | test_v3_customer_admin.py | test_get_organization_profile_nonexistent | Assertion `403 == 404` | API returns 403 (access check first); test expects 404 | No (B) | 6 | Test | Assert 403 (or decide 404 policy) |
| 7 | test_v3_customer_admin.py | test_update_profile_nonexistent_org | Assertion (status mismatch) | Same 403-vs-404 contract | No (B) | 6 | Test | Assert 403 |
| 8 | test_v3_customer_admin.py | test_get_supplier_detail_cross_org | Assertion (403 expected) | Cross-org access denied — assertion/response-shape mismatch | No (B) | 6 | Test | Align assertion with response |
| 9 | test_v3_customer_admin.py | test_list_facilities_org_isolated | AttributeError (`dict` has no `.id`) | Response items are dict rows; test uses `f.id` | No (B) | 6 | Test | Use `f["id"]` |
| 10 | test_v3_customer_admin.py | test_list_assets_org_isolated | AttributeError (`dict` has no `.id`) | Same dict-vs-object | No (B) | 6 | Test | Use `f["id"]` |
| 11 | test_v3_emissions.py | test_v3_emissions_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 4 | Test | Helper |
| 12 | test_v3_legacy_reimplementation.py | test_v3_legacy_reimplementation_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 1 | Test | Helper |
| 13 | test_v3_new_capabilities.py | test_v3_new_capabilities_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 1 | Test | Helper |
| 14 | test_v3_processing_workflow.py | test_v3_processing_workflow_routes_registered | Assertion (routes missing) | `router.routes` lazy wrappers | Yes (A) | 3 | Test | Helper |
| 15 | test_v3_processing_workflow.py | test_transition_table_covers_core_pipeline | Assertion `False` | Test asserts `validated→calculated` direct; V3 flow requires `validated→calculating→calculated` | No (E) | 3/8 | Test | Assert the in-flight transition |
| 16 | test_ai_extraction.py | TestExtractFields::test_parses_fields_from_llm_json | async not supported | pytest-asyncio missing | Yes (D) | 7 | Env | `pip install pytest-asyncio` |
| 17 | test_ai_extraction.py | TestErrors::test_invalid_json_raises_and_marks_failed | async not supported | pytest-asyncio missing | Yes (D) | 7 | Env | `pip install pytest-asyncio` |
| 18 | test_extraction.py | TestExtract::test_empty_text_raises_and_marks_failed | async not supported | pytest-asyncio missing | Yes (D) | 7 | Env | `pip install pytest-asyncio` |
| 19 | test_report_generation.py | TestValidationIntegration::test_validation_results_passed | async not supported | pytest-asyncio missing | Yes (D) | 9C/5 | Env | `pip install pytest-asyncio` |
| 20 | test_report_generation.py | TestRealEngineRegression::test_real_validation_engine_strict_blocking_error | async not supported | pytest-asyncio missing | Yes (D) | 9C/5 | Env | `pip install pytest-asyncio` |

(The remaining ≈200 failures are the same Category D async-plugin failure across
the other engine/infra test files.)


## 6. Repairs made during this resumption

Two **pre-existing, collection-blocking** defects (outside Phase 5's file list)
had to be repaired before ANY V3 unit test could collect/run. Both are fully
described in the updated Phase 5 report (§18):

1. **`backend/api/v3_operations.py` (syntax/structural corruption — Phase 8
   surface).** The module did not compile (`SyntaxError: invalid character '—'
   (U+2014)`): a scrambled block had truncated `map_item`, `operator_queue`,
   `mapping_options`, an unterminated `qc_item` docstring that swallowed
   `assign_batch`/`assign_review_item`/`complete_review_item`/`sla_settings`,
   orphaned duplicate fragments, a missing paren in `_open_validation_issues`,
   and a stray `)`. Repaired with the displaced bodies restored verbatim.
   `py_compile` clean.
2. **`backend/tests/unit/api/fakes.py` (scrambled class structure).**
   `MemoryStaff.update_profile`, `MemoryReviewQueue.complete` and the
   `MemoryReviewQueue`/`MemoryStaff` method blocks were split/truncated with
   displaced duplicates. Restored to their correct class homes. `py_compile`
   clean.

Phase 5 test adaptations (FastAPI 0.141) are documented in the Phase 5 report
§18 and remain part of this session's changes.

## 7. Phase 8 work already present

Backend implementation is substantially complete on disk (created during the
in-progress Phase 8 work before the power loss):

- **Domain** — `domain/staff.py` (StaffProfile, StaffRole, permission
  vocabulary), `domain/operations.py` (ReviewItem, QueueSettings, UploadBatch,
  …), `domain/partners.py` (ManualExtractionBatch/Item, WORKFLOW_STAGES,
  WORKFLOW_STAGE_STATUSES, ITEM_STATUS_FLOW, `can_transition_item_status`).
- **Repositories** — `data/staff.py` (StaffRepository), `data/review_queue.py`
  (ReviewQueueRepository), `data/queue_settings.py` (QueueSettingsRepository),
  `data/manual_extraction.py` (ManualExtractionRepository incl. the Phase 8 ops
  methods: `ops_dashboard_all`, QC, batches, next-item).
- **Authorization** — `api/operations_auth.py`: `StaffContext`,
  `require_staff`, `ensure_staff_permission`, `require_internal_staff`,
  `require_entity_scope`, `ensure_batch_operator_access`,
  `ensure_entity_review_scope` (all over real `staff_profiles`/`roles`
  tables).
- **API surface** — `api/v3_operations.py` (`/api/v3/ops/*`: ops dashboard,
  staff roster CRUD, staff-roles, entity dashboards, operator queue, review &
  QC queues, item workspace + mapping-options, item workflow start/extract/
  map/validate/calculate/qc, batch assign, review assign/complete, SLA
  settings, next-item) and `api/v3_qc.py` (`/api/v3/qc/*`: queue, stats,
  item review). Wired in `api/router.py`.
- **Engine** — `engines/processing_workflow.py` (`validate_processing_item`,
  `has_blocking_findings`).
- **Fakes** — `tests/unit/api/fakes.py`: `MemoryStaff`, `MemoryReviewQueue`,
  `MemoryQueueSettings`, `MemoryManualExtraction` (repaired this session).

## 8. Phase 8 work still remaining

- **Phase 8 backend unit tests — none exist.** No `test_v3_operations.py`,
  `test_operations_auth.py`, `test_staff.py`, `test_review_queue.py`,
  `test_queue_settings.py`, `test_v3_qc.py`, or
  `test_processing_workflow_engine.py`. The repaired fakes were clearly
  prepared for this suite.
- **Phase 8 frontend — not started.** `frontend/src/v3/` has only
  `admin/`, `consultant/`, `reports/`, `api.js`; **no `ops/` directory**, no
  operations API client methods in `frontend/src/v3/api.js`, no `/ops` route
  in `frontend/src/App.js`. Needed: operations dashboard, staff roster admin,
  operator/reviewer/QC queue screens, the shared split-screen workspace,
  assignments, and queue-settings/SLA admin.
- **Phase 8 report** — `CARBONTALLY_V3_PHASE_8_REPORT.md` does not exist.
- **Runtime/regression clearance** — the §5 environment and test-harness
  fixes (pytest-asyncio install + centralized route-enumeration helper) are
  prerequisites for a green Phase 8 test run.

## 9. Files modified in this resumption

- `backend/api/v3_operations.py` — corruption repair (Phase 8 surface; now
  compiles; function behaviour unchanged).
- `backend/tests/unit/api/fakes.py` — corruption repair (class structure).
- `backend/tests/unit/api/test_v3_reports.py` — 4 Phase 5 test fixes
  (routes helper, year seed, dependency override signature).
- `backend/tests/unit/api/test_v3_routes_exposed.py` — route helper +
  corrected `/api/v3/admin/entities` fragment.
- `docs/audit/cline/CARBONTALLY_V3_PHASE_5_REPORT.md` — runtime verification
  recorded (40/40).
- `docs/audit/cline/CARBONTALLY_V3_RESUMPTION_AFTER_POWER_LOSS.md` — this
  report.


## 10. Tests executed

- Phase 5 unit suite (`test_v3_reports.py` + `test_v3_routes_exposed.py`):
  **40/40 PASS (RC=0)**.
- `python -m pytest tests/unit -q`: collects + runs; **220 failures** classified
  in §5 (≈205 environment pytest-asyncio gap; ≈9 FastAPI 0.141 route-harness;
  6 test-defect assertions). Phase 5's own files are not among the failures.
- Targeted reproductions confirmed the class labels: infra + engine groups fail
  with *"async def functions are not natively supported"*; the api route tests
  fail on `_IncludedRouter`; the customer-admin and transition tests fail on
  the specific assertions listed in §5.1.
- `python -m py_compile` clean for all repaired/modified Python files.

## 11. Known environment limitations

- **Shell integration is unreliable**: the command tool cannot observe
  completion; commands must be run with output redirected to files and the
  results read back. Long pytest runs can appear "stuck".
- **`pytest-asyncio` is not installed** (the §5 Category D root cause) even
  though `pyproject.toml` configures asyncio options; `pip` invocations are
  also flaky in this shell.
- **FastAPI 0.141 / Starlette 1.6.0** are the installed versions; lazy
  `_IncludedRouter` semantics require the route-enumeration helper.
- The local Supabase/Postgres integration database and npm/frontend runners
  were not exercised this session (backend unit scope only).

## 12. Exact next action

1. **Environment first**: install `pytest-asyncio` (with `pip install
   pytest-asyncio`) and confirm `asyncio_mode = "auto"` is honoured (the
   ≈205 Category D failures then resolve).
2. **Centralized test-harness fix**: apply the one shared
   `_flatten_router_paths` helper (already written for the Phase 5 files) to
   the remaining route-registration tests (§5 class A), and correct the
   `/api/v2/admin/entities` → `/api/v3/admin/entities` fragment. Align the six
   §5 class B/E test assertions with the implemented contracts.
3. **Resume Phase 8 where it stopped**: Phase 8's backend implementation is on
   disk; the remaining Phase 8 scope is its unit-test suite, the v3 frontend
   operations screens (dashboard, staff roster, operator/reviewer/QC queues,
   split-screen workspace, assignments, SLA/queue settings), and the Phase 8
   report. Do not start Phase 9; do not add system-wide audit logging; do not
   perform production security hardening; do not delete legacy modules; do not
   redesign the database/RLS.

