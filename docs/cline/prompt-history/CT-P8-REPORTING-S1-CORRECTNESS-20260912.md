# CT-P8-REPORTING-S1-CORRECTNESS-20260912

**Prompt ID:** `CT-P8-REPORTING-S1-CORRECTNESS-20260912`
**Date:** 2026-09-12
**Task purpose:** Bounded Phase 8 Reporting **S1** correctness fixes — the `report_versions.is_current`
invariant, `current_version` in the report listing, the stale `download_report` docstring, and
regression coverage — before the broader ratified report lifecycle proceeds.
**Type:** IMPLEMENTATION (bounded). No report lifecycle, no Insight, no migration, no RLS change.
**Task status:** `COMPLETED — S1 IMPLEMENTED`

## Starting Repository State

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `d204fdaa3ccc914a565b81011e363bda073a2850` |
| Relation to origin | 11 commits ahead of `origin/main`, **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

All pre-existing dirty/untracked work was treated as immutable.

## Discovery Findings (traced from the actual implementation)

| # | Finding | Evidence |
|---|---|---|
| 1 | The mounted V3 reporting API is `backend/api/v3_reports.py` (prefix `/api/v3/reports`), not `backend/data/reporting.py` | `router = APIRouter(prefix="/api/v3/reports", ...)` |
| 2 | **S1-A defect confirmed.** `ReportVersionsRepository.create()` was a plain `INSERT` with `is_current` defaulting to `True`, and **never demoted** prior current rows → multiple `is_current = TRUE` rows per report were reachable | `backend/data/report_versions.py` (pre-change `create()`) |
| 3 | `get_current()` masked the defect with `ORDER BY version_number DESC LIMIT 1`, so a single-row read looked correct while the invariant was violated | `backend/data/report_versions.py::get_current` |
| 4 | The schema has **no** protection: `report_versions` has `UNIQUE (report_id, version_number)` only; `is_current BOOLEAN DEFAULT FALSE` is unconstrained → an application-level fix is required and sufficient | `init_schema.sql:1003-1016`, `report_versions_report_version_uniq` |
| 5 | **S1-B defect confirmed.** `GET /api/v3/reports` returned `shape_report_status(r)` — **no `current_version` at all**. The detail endpoint *does* expose it via `shape_report_out` | `v3_reports.py::list_reports`, `::get_report` |
| 6 | The frontend expects `current_version` to be an **object** and reads `r.current_version?.version_number`, falling back to `'v1'` when absent — which is why every completed report rendered as `v1` | `frontend/src/v3/reports/ReportsPage.jsx:243-246` |
| 7 | **S1-C defect confirmed.** `download_report`'s docstring claimed *"no PDF rendering exists in V3 — documented backend gap"*, but `GET /{report_id}/pdf` renders a branded PDF via `render_branded_pdf` | `v3_reports.py::download_report` vs `::download_report_pdf`, `engines/pdf_render.py:245` |
| 8 | There **is** an established `conn.transaction()` pattern in `backend/data/`, with an exact analogue of this invariant (`imports.activate_batch` enforces a single-active batch) | `data/billing.py:193`, `data/imports.py:168` |
| 9 | There **is** a real-database harness: dedicated `carbontally_test` DB, session `pool` fixture, `make_org`, and an existing `tests/integration/test_report_versions.py` | `tests/integration/conftest.py` |
| 10 | The unit API in-memory `MemoryReportVersions` fake **also** lacked demotion and the batch read | `tests/unit/api/fakes.py:950-1005` |

**No stop condition was encountered.** No migration, RLS change, authorization change, lifecycle
work, Phase 7 change, frontend change, or API contract redesign was required.

## Implementation Performed

### S1-A — `is_current` invariant
**File:** `backend/data/report_versions.py`

`ReportVersionsRepository.create()` now runs inside the established
`async with self._pool.acquire() as conn: async with conn.transaction():` pattern (the same shape as
`data.imports.activate_batch`). When `is_current=True` it first executes

```sql
UPDATE public.report_versions SET is_current = FALSE
 WHERE report_id = $1 AND is_current = TRUE
```

then inserts the new row **in the same transaction**, so a successful call leaves exactly one
current version and a failure rolls back to the previous state. `is_current=False` never touches the
existing current version. No migration; no new persistence abstraction.

### S1-B — `current_version` in the report listing
**Files:** `backend/data/report_versions.py`, `backend/api/v3_reports.py`

* New repository method `current_by_reports(report_ids) -> dict[str, dict]` — **one** query
  (`WHERE report_id = ANY($1::uuid[]) AND is_current = TRUE ORDER BY version_number DESC`),
  returning the current version per report. Reports with no current version are **absent** from the
  result (no fabricated version 1). `ORDER BY … DESC` + `setdefault` mirrors `get_current()` so
  legacy duplicate-current rows resolve identically in both read paths.
* New pure helper `shape_report_list_row(report, current_version)` — the dashboard row plus
  `current_version` (`{}` when absent). It deliberately does **not** add the detail-only
  `reporting_period`, keeping the list contract minimal.
* `list_reports` now performs **one batched read** for the page's report ids and attaches
  `current_version` to each row — no N+1, no hard-coded 1, no `MAX(version_number)` inference.
* No frontend change was needed: the response now satisfies the existing
  `r.current_version?.version_number` contract.

### S1-C — stale PDF documentation
**File:** `backend/api/v3_reports.py`

The `download_report` docstring was corrected to describe the endpoint accurately as the
machine-readable JSON export and to name the real branded-PDF path
(`GET /api/v3/reports/{report_id}/pdf` → `render_branded_pdf`). Documentation only — no behaviour
change; no PDF/frozen-PDF/hashing work.

### S1-D — regression coverage
**Files:** `backend/tests/integration/test_report_versions.py`,
`backend/tests/unit/api/test_v3_reports.py`, `backend/tests/unit/api/fakes.py`

* **Real-database (production repository boundary):**
  * `test_create_current_version_demotes_previous_version` — v1 current → v2 current → exactly one
    current, newest is current, previous demoted; `get_current` and `current_by_reports` agree.
  * `test_create_non_current_version_leaves_current_intact` — a non-current create does not disturb
    the current version.
  * `test_current_by_reports_returns_absent_for_no_current_version` — the batch read returns only
    genuine current versions; a report without one is absent; empty input fabricates nothing.
  * Each test cleans up **only** the rows it created (`report_versions` +
    `report_generation_queue`) in a `finally` block.
* **Unit API:**
  * `test_shape_report_list_row_exposes_current_version` / `..._never_invents_version_one`.
  * `test_list_reports_exposes_real_current_version_not_one` — the listing shows the real version (2),
    not the `v1` fallback, and exactly one current version survives.
  * `test_list_reports_without_versions_reports_empty_current_version` — absence stays absent.
  * `test_list_reports_current_version_is_org_scoped` — a foreign org's versions never leak.
  * `test_list_reports_reads_current_versions_in_one_batch` — **no-N+1 guard**: the listing performs
    exactly one batched read.
* **Test double:** `MemoryReportVersions` was made faithful to the corrected repository contract
  (demote-on-current-create, `current_by_reports`, plus a `current_by_reports_calls` probe). This is
  a test-double correction, not duplicated production logic.

## Tests Run

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/unit/api/test_v3_reports.py tests/unit/api/test_reporting.py -q` | **87 passed**, EXIT=0 |
| `.venv/bin/python -m pytest tests/unit/api -q` | **all passed** (EXIT=0, 0 failures) |
| `.venv/bin/python -m pytest tests/integration/test_report_versions.py -q` | 5 passed, **1 pre-existing failure** (below) |
| `.venv/bin/python -m pytest tests/integration/test_report_versions.py tests/integration/test_reports.py -q` | 11 passed, **4 pre-existing failures** (same cause) |

### Unrelated pre-existing failures (NOT caused by S1)

`test_create_and_roundtrip_version`, `test_mark_generating`, `test_mark_failed_persists_error`,
`test_create_request_records_created_by_and_name`.

All four fail with `asyncpg.exceptions.DataError: invalid input for query argument …: 'user-1'
(invalid UUID 'user-1': length must be between 32..36 characters, got 6)` — the pre-existing tests
pass the non-UUID literal `"user-1"` into UUID columns.

**Proven pre-existing:** the failing parameter binding was executed against the **HEAD (pre-change)**
version of the module, extracted to a temp path and called directly against the test database:

```
RESULT: HEAD module create(created_by='user-1') FAILED -> DataError: invalid input for query
argument $6: 'user-1' (invalid UUID 'user-1': length must be between 32..36 characters, got 6)
```

The HEAD `create()` used `self._fetch_one(...)` → `conn.fetchrow(...)` with the identical argument
list, so parameter encoding is unchanged by S1. `backend/data/reports.py` is **unmodified** by this
task. These are latent test-data defects for a separate, authorised task.

## Verification

| Check | Result |
|---|---|
| S1-A invariant (exactly one current; newest current; previous demoted) | ✔ real-DB test |
| S1-B real `current_version` (no fallback to 1) | ✔ unit test |
| S1-B absence preserved (no invented 1) | ✔ unit test |
| S1-B no N+1 (one batched read) | ✔ unit test |
| S1-C docstring matches `/pdf` behaviour | ✔ stale claim gone; route + renderer + 3 passing PDF tests |
| Existing `test_v3_reports.py` suite | ✔ all pass |
| Organization scope / authorization unchanged | ✔ `ensure_org_access` / `require_org_member` untouched; org-isolation and denial tests pass |
| Secret scan of changed files | ✔ 0 matches |

## Database / RLS / Lifecycle

| Item | Answer |
|---|---|
| Migration created or changed | **NO** |
| Historical data modified / backfilled / repaired | **NO** |
| RLS policy changed / added / removed / disabled / `FORCE` changed | **NO** |
| Report lifecycle implemented (DRAFT/REVIEW/APPROVED/FINAL, approval, comments, narrative overlay, frozen PDF, hashing) | **NO** |
| Frontend changed | **NO** |
| Phase 7 changed | **NO** |
| CarbonTally Insight / RAG / LangChain / AI provider touched | **NO** |

## Final Git State

| Item | Value |
|---|---|
| Starting HEAD | `d204fdaa3ccc914a565b81011e363bda073a2850` |
| Files changed by this task | `backend/data/report_versions.py`, `backend/api/v3_reports.py`, `backend/tests/unit/api/fakes.py`, `backend/tests/unit/api/test_v3_reports.py`, `backend/tests/integration/test_report_versions.py`, plus this prompt-history file |
| Pre-existing work | preserved exactly (208 modified / 52 untracked) |
| Push | **not pushed** |

## Scope Confirmation

No report lifecycle implementation · no CarbonTally Insight implementation · no RAG · no LangChain ·
no Phase 7 reopening · no unrelated refactoring · no migration · no RLS change · no push.

## Final Status

**S1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

I1 (CarbonTally Insight) was **not** begun. This task is Cline implementation work; the Product Owner
performs independent review/verification.
