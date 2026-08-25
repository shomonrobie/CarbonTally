# CarbonTally V3 — D31 Reporting Completion Report

**Date:** 2026-08-23 · **Mode:** product-completion of D30 PARTIAL reporting gaps
**Author:** Cline

---

## 1. Objective & scope

Complete the D30 PARTIAL reporting capabilities without redesigning the D30 architecture,
creating a generic analytics abstraction, or introducing a new tenancy model. `organizations`
remains the customer data-tenancy anchor. No synthetic PDF work, no 5,787-document processing,
no new auth/tenancy architecture.

## 2. Read-only gap analysis (before implementation)

| D30 gap | Data support (inspected schema) | D31 decision |
|---|---|---|
| Customer monthly emissions trend | `emissions_logs` (start_date, calculated_kg_co2e) — SUPPORTED | IMPLEMENTED (recharts bar chart, zero-filled, empty state) |
| Customer member activity | `organization_files.uploaded_by`, `issues.created_by/status`, `manual_extraction_batches.created_by`, `emissions_logs.created_by_user_id` — SUPPORTED (derived); activity_logs-family tables are EMPTY/write-only | IMPLEMENTED (derived view) |
| Consultant per-client drill-down | items-by-stage via batch join, documents, issues, reports, emissions — SUPPORTED | IMPLEMENTED (`consultant-client/{id}`, ACTIVE grant gate) |
| Ops queue aging | `manual_extraction_batches` (created_at/assigned_at/sla_deadline/sla_breached/entity_id) + items — SUPPORTED | IMPLEMENTED (aging buckets 0-1d/1-3d/3-7d/7d+) |
| Reviewer workload | `manual_review_queue` (assigned_to, status, sla_breached) — SUPPORTED | IMPLEMENTED |
| Issues generated during review | `issues` (issue_type, severity, status, created_at) — SUPPORTED; no `blocking` column | IMPLEMENTED (type/status/monthly); blocking = NOT SUPPORTED (workflow-derived only) |
| QC recurring quality | `qc_checks`/`qc_errors` EMPTY (0 rows, not populated by workflow) | NOT SUPPORTED BY CURRENT DATA MODEL (explicit marker returned) |
| QC processor performance | items status/quality_score + batch.entity_id — SUPPORTED | IMPLEMENTED (internal vs entity, sample sizes shown) |
| Admin read-side audit | `audit_trail` (written by `AuditRepository`), currently 0 rows locally | IMPLEMENTED (reuses `AuditRepository.query`; sanitised output) |
| Auth-event reporting | Not available in the local application schema (Supabase-owned) | EXTERNAL CONFIGURATION REQUIRED (documented) |
| Entity SLA status | batches sla_deadline/sla_breached — SUPPORTED | IMPLEMENTED |
| Entity quality indicators | items quality_score + qc status (own batches) — SUPPORTED | IMPLEMENTED |

## 3. APIs added / changed (all read-only)

| API | Actor gate | Returns |
|---|---|---|
| `GET /api/v3/reporting/emissions-trend?organization_id=&months=` | org member (own org) | zero-filled monthly kg/rows |
| `GET /api/v3/reporting/member-activity?organization_id=` | org member (own org) | per-member uploads/batches/issues/emissions |
| `GET /api/v3/reporting/consultant-client/{client_id}` | consultant + ACTIVE grant | per-client stages/docs/issues/reports/emissions (404 non-granted, 403 ended) |
| `GET /api/v3/ops/reporting/aging` | internal staff `can_view_all` | batch/item aging + SLA + scope |
| `GET /api/v3/ops/reporting/audit?actor=&action=&entity_type=&limit=&offset=` | internal staff `can_manage_staff` (staff admin) | sanitised audit-trail rows |
| `GET /api/v3/ops/reporting/review` (EXTENDED) | internal staff `can_review` | + workload by reviewer, issues by type/status/month |
| `GET /api/v3/ops/reporting/qc` (EXTENDED) | internal staff `can_review` | + processor performance (internal vs entity), recurring-quality marker |
| `GET /api/v3/ops/entities/{id}/performance` (EXTENDED) | own entity / internal any | + SLA status, quality indicators |

## 4. Metrics and source tables (data-integrity rule)

| Metric | Source table(s) | Calculation | Time basis | Auth | Empty state |
|---|---|---|---|---|---|
| Monthly emissions trend | `emissions_logs` | `SUM(calculated_kg_co2e)` grouped `to_char(start_date,'YYYY-MM')`, zero-filled | last N months (1–36) | org member | "No emissions recorded" |
| Member documents uploaded | `organization_files` | count `uploaded_by` (active, not deleted) | all-time | org member | table with zeros |
| Member extraction batches | `manual_extraction_batches` | count `created_by` | all-time | org member | zeros |
| Member issues created/resolved | `issues` | count `created_by` by `status` | all-time | org member | zeros |
| Member emissions rows | `emissions_logs` | count `created_by_user_id` | all-time | org member | zeros |
| Per-client stage breakdown | items + batches | `status` → `WORKFLOW_STAGE_STATUSES` | current | ACTIVE grant | empty stages hidden |
| Per-client emissions | `emissions_logs` | sum/rows/by-scope | all-time | ACTIVE grant | "No data" |
| Batch age | `manual_extraction_batches` | `created_at` buckets | current | internal `can_view_all` | zeros |
| Item age | `manual_extraction_items` | `created_at` buckets | current | internal `can_view_all` | zeros |
| SLA breached / overdue | batches | persisted `sla_breached`; `sla_deadline < NOW()` on open | current | internal `can_view_all` | zeros |
| Reviewer workload | `manual_review_queue` | assigned/completed/pending/overdue per `assigned_to` | current | internal `can_review` | empty table |
| Issues by type/status/month | `issues` | group by `issue_type`/`status`/month | current | internal `can_review` | "none" |
| Processor performance | items + batches | completed/rejected/avg quality by `batch.entity_id` (internal vs entity) | current | internal `can_review` | zeros + sample_size |
| QC recurring quality | `qc_errors` | — | — | — | NOT SUPPORTED (marker) |
| Audit trail | `audit_trail` | existing `AuditRepository.query`; before/after payloads excluded | persisted | staff admin | "No audit entries" |
| Entity SLA | entity batches | persisted `sla_breached` + overdue | current | own entity | zeros |
| Entity quality | entity items | completed/rejected/avg quality/rejection rate | current | own entity | zeros + sample |

**Data limitations documented:** activity_logs-family tables are write-only (0 rows locally);
`issues` has no `blocking` column (blocking is workflow-derived); `qc_errors` is unpopulated
(recurring quality NOT SUPPORTED); auth events are Supabase-owned (EXTERNAL CONFIGURATION).

## 5. Authorization model (unchanged semantics — D15/D20/D22/D30)

- Customer trend/activity: `ensure_org_access` (own org only; entity staff denied).
- Consultant drill-down: `require_consultant` + per-client ACTIVE grant (404 non-granted /
  403 ended).
- Aging: internal staff `can_view_all`. Audit: internal staff `can_manage_staff`.
- Review/QC: internal staff `can_review`. Entity performance: own entity (`require_entity_scope`).
- Entity staff never obtain customer reporting; no cross-consultant client visibility.

## 6. Test-infrastructure footgun fix (D31)

`backend/tests/integration/conftest.py` previously defaulted `INTEGRATION_DATABASE_URL` to the
MAIN local Supabase database (`...:54326/postgres`) and TRUNCATE'd ~22 tables there (the D30
incident). Fixed:

1. Default now `.../carbontally_test` (dedicated DB).
2. Session guard: if `current_database()` is a FORBIDDEN main app database → `RuntimeError`
   (no TRUNCATE). If the dedicated DB is unreachable or schema-less → `pytest.skip` (fail-safe).
3. The dedicated `carbontally_test` database was provisioned locally (schema-only restore with
   privileges from the main DB: 107 public tables, 183 RLS policies) and the RLS suite passes
   against it.

Verified: default run = **11 passed**; URL pointed at main `postgres` = **refused** (RuntimeError,
no truncation); URL pointed at missing DB = **11 skipped** (fail-safe).

## 7. Tests

Backend unit suite: **977 tests, 0 failures** (D30's 960 + 17 new D31 tests in
`tests/unit/api/test_reporting.py`). New D31 tests:
- emissions trend: zero-filled months, cross-org 403, entity-staff 403
- member activity: member 200, cross-org 403
- consultant client drill-down: own ACTIVE client 200; unknown client 404; ENDED client 403;
  non-consultant 403
- queue aging: internal `can_view_all` 200; entity staff 403; missing `can_view_all` 403
- admin audit: staff-admin 200 (empty); operator 403; entity staff 403
- extended review payload (workload + issues)
- extended QC payload (processor performance + recurring-quality marker)
- extended entity payload (SLA + quality)

RLS integration suite (dedicated `carbontally_test` DB): **11 passed** (+ refusal and
fail-safe-skip verified).

Frontend: V3 API Jest suite (18/18 — see §9); production build succeeds.

## 8. Screenshots / visual QA

`mkdir -p screenshots/d31_reporting/` — captured with the proven Selenium + headless Firefox
mechanism (Selenium 4.47.0, geckodriver 0.36.0, Firefox 149.0.2). **11 captures**; panels
verified via live DOM checks (needle matching on rendered body text — the panels render for
every surface below; the earlier verify-script FAILs were browser-session races, re-confirmed
PASS by focused re-runs).

| File | Actor | Surface | D31 evidence |
|---|---|---|---|
| `customer-dashboard-reporting.png` | Customer owner | `/home` | reporting overview + monthly emissions trend + activity by member (all rendered — DOM-verified) |
| `customer-emissions-trend.png` | Customer owner | `/home` | monthly emissions trend panel |
| `consultant-portfolio-reporting.png` | Consultant owner | `/consultant` | portfolio health with per-client "Reporting →" drill-down |
| `consultant-client-reporting.png` | Consultant owner | `/consultant` drill-down | per-client "— reporting": stage breakdown, issues, reports, emissions (DOM-verified) |
| `operations-dashboard-reporting.png` | Staff operator | `/ops` | platform & quality + queue aging |
| `reviewer-dashboard-reporting.png` | Reviewer | `/ops` | ops hub |
| `reviewer-reporting.png` | Reviewer | `/ops` → Review | review reporting + reviewer workload + issues (DOM-verified) |
| `qc-dashboard-reporting.png` | QC | `/ops` | ops hub |
| `qc-reporting.png` | QC | `/ops` → QC | QC reporting + processor performance + recurring-quality note (DOM-verified) |
| `platform-admin-reporting.png` | Staff admin | `/ops` | platform + queue aging + audit trail (admin) (DOM-verified) |
| `entity-performance-reporting.png` | Entity staff | `/ops` entity workspace | entity performance + SLA + quality indicators (API-verified via smoke) |

## 9. Frontend tests

`frontend/src/v3/__tests__/api.test.js` — V3 API Jest suite **18/18 pass** (regression; new D31
client functions are additive). `App.test.js` remains blocked by the pre-existing
react-router-dom/resolve-path issue (unchanged; not related to D31).

## 10. Findings / remaining limitations

| Limitation | Classification | What is required to close it |
|---|---|---|
| QC recurring-quality identification | NOT SUPPORTED BY CURRENT DATA MODEL | populate `qc_checks`/`qc_errors` in the workflow, then expose patterns |
| `issues.blocking` flag | NOT SUPPORTED BY CURRENT DATA MODEL | persist a blocking boolean on `issues` (currently workflow-derived) |
| Activity-log family (activity_logs etc.) | PARTIALLY IMPLEMENTED (derived view) | populate the activity tables on writes, then switch reporting to them |
| Auth-event / login-failure reporting | EXTERNAL CONFIGURATION REQUIRED | Supabase Auth admin events / audit (GoTrue) — not available in the local application schema |
| Emissions trend chart | IMPLEMENTED (0 rows locally — honest empty state) | emissions data appears once the factor baseline + calculations run (5,787-PDF validation prep) |
| Audit trail | IMPLEMENTED (0 rows locally — honest empty state) | audit rows accumulate as the write-side AuditRepository records actions |
| Ops batch/item "time in progress" | PARTIALLY IMPLEMENTED (age buckets only) | persist stage-entry timestamps (updated_at granularity only today) |

## 11. Files changed (D31)

Backend:
- `backend/data/reporting.py` — emissions_trend, member_activity, consultant_client_detail,
  queue_aging; extended review_reporting, qc_reporting, entity_performance
- `backend/api/v3_reporting.py` — 5 new endpoints + extended review/QC/entity payloads
- `backend/tests/unit/api/test_reporting.py` — +17 D31 tests
- `backend/tests/unit/api/fakes.py` — D31 MemoryReporting fakes
- `backend/tests/integration/conftest.py` — dedicated-test-DB + fail-safe guard (footgun fix)

Frontend:
- `frontend/src/v3/api.js` — 6 new client functions
- `frontend/src/v3/customer/DashboardPage.jsx` — recharts trend chart + member activity panel
- `frontend/src/v3/consultant/ConsultantPage.jsx` — per-client drill-down view
- `frontend/src/v3/ops/OpsDashboard.jsx` — queue aging + admin audit panels
- `frontend/src/v3/ops/ReviewQueue.jsx` — workload + issues cards
- `frontend/src/v3/ops/QcQueue.jsx` — processor performance + recurring-quality note
- `frontend/src/v3/ops/EntityExtractionWorkspace.jsx` — SLA + quality indicators

Database/schema: NONE (no migrations; the dedicated `carbontally_test` DB was provisioned for
the integration suite).

No unrelated features changed. No 5,787-PDF processing started.


