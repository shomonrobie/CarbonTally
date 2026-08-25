# CarbonTally V3 — D30 Reporting Completeness Report

**Date:** 2026-08-22 · **Mode:** read-only requirements audit → missing reporting implemented
**Author:** Cline

---

## 1. Reference requirements

Authoritative sources consulted:
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (actor model A1–A14, role
  model, permission model, workspace model, access matrices, D15/D20/D22 records).
- `docs/architecture/CarbonTallyCustomerPortal.md` (customer portal text UI/UX: reporting
  progress, pending uploads, documents processing, waiting for approval, completed calculations,
  total emissions, recent activity, quick actions).
- `docs/architecture/UI2/*` (legacy reports centre / emissions-reports reference: per-scope,
  per-month, per-facility, per-asset and compliance report concepts).
- Existing implementation (frontend dashboards, backend report/export/operations APIs,
  report-generation engine).

The D30 task itself specifies the per-actor reporting requirements (Parts 3–11). The reference
docs are the business source of truth; no generic SaaS reporting terminology was introduced.

## 2. Actor / report matrix

| Actor | Dashboard | Operational metrics | Data/emissions reports | Processing reports | Quality/SLA/issue reports | Audit/activity |
|---|---|---|---|---|---|---|
| A1/A2 Customer owner/admin | `/home` + reporting overview | documents processed/pending/attention; processing progress; emissions total/scope/period | emissions by scope/month; document status | batches/items by stage; mapped vs unmapped | open issues; SLA-breached issues | — |
| A3/A4 Customer member/viewer | `/home` (member-read) | same as owner within org scope | same | same | open issues | — |
| A9–A12 Consultant | `/consultant` + portfolio health | active/suspended/ended counts; per-client documents/items/issues/reports | per-client emissions (via client workspace reports) | per-client processing progress | per-client open issues | — |
| A5 Staff operator | `/ops` dashboard + platform reporting | batches/items/complete%; failed/rejected; organizations/entities/staff | — | pipeline by stage | review/QC/issue status | — |
| A6 Reviewer | `/ops` Review + review reporting | review queue counts | — | — | aging, SLA breached | — |
| A7 QC | `/ops` QC + QC reporting | QC outcomes; avg quality score | — | internal vs entity outcomes | quality distribution | — |
| A8 Staff admin / platform owner | `/ops` platform reporting | organizations, entities, staff, processing volume | — | backlog, failures | review/QC/issues | — |
| A13/J/K Entity staff/admin | `/ops` entity workspace + entity performance | assigned batches/items; complete %; staff workload | — | own-entity batches/items | — | — |

## 3. Existing implementation (audit)

| Surface | Existing UI | Existing API | Existing data | Complete? | Gap |
|---|---|---|---|---|---|
| Customer dashboard | Stat cards (reports/documents/members/emissions) + latest reports | `listReports`/`v3ListDocuments`/`v3ListEmissions`/`listMembers` | org-scoped tables | PARTIAL | No emissions-by-scope/period/trend; no document status; no processing stage progress; no attention panel; no data-quality view |
| Emissions export | `/emissions` page + CSV/JSON export | `/api/v3/exports/emissions.{csv,json}` | `emissions_logs` | PARTIAL | Export exists; no dashboard aggregation |
| Customer manager | `/organization` tabs | `/api/v3/organizations/*` | org tables | PARTIAL | No aggregate "how is my org performing" view |
| Consultant dashboard | Stat cards (client counts, issues, reports) | `/api/v3/consultants/me/dashboard` | firm + client grants | PARTIAL | No per-client health; ended clients not surfaced; no portfolio view |
| Ops dashboard | Batches/items/QC/issues/staff strip + pipeline table | `/api/v3/ops/dashboard` | ops aggregates | PARTIAL | No aging, SLA, failures, platform counts |
| Reviewer | Review queue table | `/api/v3/ops/queues/review` | `manual_review_queue` | PARTIAL | No aging/SLA aggregate |
| QC | QC queue table | `/api/v3/ops/queues/qc`, `/api/v3/qc/*` | items QC fields | PARTIAL | No outcome/quality aggregate |
| Entity workspace | Batches/items/extraction panels | `/api/v3/ops/entities/{id}/*` | entity-scoped tables | PARTIAL | No staff performance aggregate |
| Platform admin | (ops dashboard only) | — | — | GAP | No platform overview (orgs/users/entities/processing/quality) |
| Audit | — | `data/audit.py` (write-side) | `audit_logs` | GAP | No read-side audit report surface |

## 4. Missing reports → implemented

| # | Report | Priority | Actor | Implementation |
|---|---|---|---|---|
| R1 | Customer dashboard reporting aggregate | P1 | A1–A4 | `GET /api/v3/reporting/customer-dashboard` + DashboardPage panel |
| R2 | Consultant portfolio health | P1 | A9–A12 | `GET /api/v3/reporting/consultant-portfolio` + ConsultantPage panel |
| R3 | Platform overview (orgs/entities/staff/processing/quality) | P2 | A5/A8 | `GET /api/v3/ops/reporting/platform` + OpsDashboard strip |
| R4 | Reviewer reporting (aging, SLA) | P2 | A6 | `GET /api/v3/ops/reporting/review` + ReviewQueue card |
| R5 | QC reporting (outcomes, quality, scope) | P2 | A7 | `GET /api/v3/ops/reporting/qc` + QcQueue card |
| R6 | Entity performance (own entity + staff workload) | P2 | A13/J/K | `GET /api/v3/ops/entities/{id}/performance` + entity workspace strip |

## 5. Metric definitions (source of truth — no invented metrics)

| Metric | Source table(s) | Calculation | Authorization scope | Time basis |
|---|---|---|---|---|
| Total emissions (kg CO₂e) | `emissions_logs` | `SUM(calculated_kg_co2e)` | current authorized org | optional `start_date`–`end_date` (log period) + `scope` |
| Emissions by scope | `emissions_logs` | `GROUP BY scope` | current org | period |
| Emissions by month | `emissions_logs` | `to_char(start_date,'YYYY-MM')` grouped | current org | period |
| Documents total/processed/pending | `organization_files`, `document_processing_queue` | count files; queue status buckets | current org | current |
| Documents requiring attention | `document_processing_queue` | count with `workflow_error_count > 0` | current org | current |
| Processing items by stage | `manual_extraction_items` + batches | bucket item `status` via `WORKFLOW_STAGE_STATUSES` | current org (via batch.organization_id) | current |
| % complete | items | (approval+qc stages)/total × 100 | current org | current |
| Mapped / unmapped | `manual_extraction_items` | items with any `mapped_*_id` vs total | current org | current |
| Open issues / SLA breached | `issues` | count by status; `sla_breached=TRUE` | current org | current |
| Reports ready/queued/failed | `report_generation_queue` | count by status | current org | current |
| Consultant portfolio counts | `consultant_clients` | count by status | caller's firm profile grants | current |
| Per-client documents/items/issues/reports | org tables per client grant | counts scoped by `organization_id` | ACTIVE grants only (D15) | current |
| Platform orgs/entities/staff | `organizations`, `processing_entities`, `staff_profiles` | counts | internal staff `can_view_all` | current |
| Platform items/batches/failures | items + batches | stage buckets; `rejected`/`qc_rejected` | internal staff `can_view_all` | current |
| Review aging/SLA | `manual_review_queue` | age buckets; `sla_breached` | internal staff `can_review` | current |
| QC outcomes / quality score | `manual_extraction_items` | status counts; `AVG(quality_score)`; internal vs entity by batch.entity_id | internal staff `can_review` | current |
| Entity performance + staff workload | batches/items/staff | counts scoped to `entity_id` | own entity (or internal any) | current |

## 6. Authorization model (D15/D20/D22 preserved — no weakening)

| Endpoint | Guard |
|---|---|
| `/api/v3/reporting/customer-dashboard` | `get_current_user` + `ensure_org_access` (org member own org only; internal staff any-org bypass preserved; **Processing Entity staff denied**) |
| `/api/v3/reporting/consultant-portfolio` | `require_consultant` (active firm member); ACTIVE client grants only — ended/suspended counted but never detailed |
| `/api/v3/ops/reporting/platform` | `require_staff` + `require_internal_staff` + `can_view_all` |
| `/api/v3/ops/reporting/review` | `require_staff` + `require_internal_staff` + `can_review` |
| `/api/v3/ops/reporting/qc` | `require_staff` + `require_internal_staff` + `can_review` |
| `/api/v3/ops/entities/{id}/performance` | `require_staff` + `require_entity_scope` (entity staff own entity only; internal staff any) |

Entity staff never obtain customer-wide reporting; consultant reporting only ever spans the
caller's own ACTIVE grants; internal reporting requires internal scope + the relevant permission.
No fallback bypass: every denied path returns 403.

## 7. UX changes

- **Customer dashboard**: new "Reporting overview" panel — emissions total/scope/latest month,
  documents total/processed/pending/attention, processing items/complete%/mapped/stages,
  "Needs your attention" (open issues, unmapped, pending customer review).
- **Consultant dashboard**: "Portfolio health" — active/suspended/ended counts + per-client
  documents/items/open issues/ready-reports table (ended clients never listed).
- **Ops dashboard**: "Platform & quality" strip — organizations, entities, staff, items complete,
  failed/rejected, review SLA breached, open issues.
- **Review tab**: "Review reporting" card — pending/in-review/completed, SLA breached, aging buckets.
- **QC tab**: "QC reporting" card — QC approved/rejected, avg quality score, outcomes by scope.
- **Entity workspace**: "Entity performance" — batches/items/complete% + staff workload table.

## 8. Screenshots

Captured under `screenshots/d30_reporting/` (Selenium 4.47.0 + geckodriver 0.36.0 + headless
Firefox 149.0.2, 1366×682):
- `customer-dashboard-reporting.png`, `customer-emissions-reporting.png`,
  `customer-manager-reporting.png`
- `consultant-portfolio-reporting.png`, `consultant-client-reporting.png`
- `operations-dashboard-reporting.png`
- `reviewer-dashboard-reporting.png`, `reviewer-queue-reporting.png`
- `qc-dashboard-reporting.png`, `qc-queue-reporting.png`
- `platform-admin-reporting.png`
- `entity-admin-staff-reporting.png`

## 9. Tests

`backend/tests/unit/api/test_reporting.py` (16 tests):
- pure metric helpers: stage distribution buckets, completion ratio, unknown-status fallback,
  full status vocabulary coverage
- customer dashboard: aggregate composition, cross-org denial, entity-staff denial, 401
- consultant portfolio: ended clients excluded from detail (counted only), non-consultant denial
- staff permission gates: platform `can_view_all` (allow/entity-deny), review `can_review`
  (allow/operator-deny), QC `can_review`
- entity performance: own entity allow, other entity deny

Live smoke (real tokens, :8001): all 6 endpoints + denials verified (12/12 PASS).

Full backend unit suite: **960 tests, 0 failures** (includes the 16 new reporting tests).

## 10. Remaining gaps (documented, not implemented)

| Gap | Why | Recommendation | Priority |
|---|---|---|---|
| Customer emissions **trend chart** (per-month visual) | aggregate returned by month; no charting library wired | add a lightweight chart (existing deps only) on `/emissions` | P3 |
| Customer manager **staff activity / workload** view | no per-member activity aggregate exists | extend `activity_logs` read-side reporting scoped to org | P3 |
| Consultant **per-client emissions** detail in portfolio | portfolio lists counts; emissions detail lives in the client workspace reports | add per-client emissions block to the portfolio table | P3 |
| Ops **queue aging** drill-down on the ops dashboard | review aging exists; batch/item aging aggregate not surfaced | extend `/api/v3/ops/reporting/platform` with batch/item aging buckets | P3 |
| **Audit report surface** (read-side) | `audit_logs`/`activity_logs` write-side only | add an internal staff `can_view_all` audit read endpoint | P3 |
| **Exportable** reporting (CSV of the new aggregates) | not required by the reference for dashboards | add exports when the reference specifies them | P4 |

## 11. Files changed (D30)

Backend:
- `backend/data/reporting.py` (new — ReportingRepository, pure SQL aggregates)
- `backend/api/v3_reporting.py` (new — 6 reporting endpoints)
- `backend/api/dependencies.py` (reporting repo in the bundle)
- `backend/api/router.py` (reporting router registered)
- `backend/tests/unit/api/test_reporting.py` (new — 16 tests)
- `backend/tests/unit/api/fakes.py` (MemoryReporting in the in-memory world)

Frontend:
- `frontend/src/v3/api.js` (6 reporting client functions)
- `frontend/src/v3/customer/DashboardPage.jsx` (reporting overview panel)
- `frontend/src/v3/consultant/ConsultantPage.jsx` (portfolio health)
- `frontend/src/v3/ops/OpsDashboard.jsx` (platform & quality strip)
- `frontend/src/v3/ops/ReviewQueue.jsx` (review reporting card)
- `frontend/src/v3/ops/QcQueue.jsx` (QC reporting card)
- `frontend/src/v3/ops/EntityExtractionWorkspace.jsx` (entity performance)

No schema/RLS/migration changes. No new analytics warehouse. No 5,787-PDF work started.

## 12. RLS integration-suite hazard + local-database restoration

**Hazard (pre-existing):** `backend/tests/integration/conftest.py` defaults
`INTEGRATION_DATABASE_URL` to `postgresql://postgres:postgres@127.0.0.1:54326/postgres` —
port 54326 IS the local Supabase **main** database (`supabase_db_carbon_ledger`). The session
fixture TRUNCATEs ~22 tables (incl. `organizations`, `processing_entities` — which CASCADE to
`staff_profiles`/`organization_files`/`manual_extraction_batches|items`/`manual_review_queue`)
and then seeds its own fixture data. Running the RLS suite against that default therefore wipes
the local demo data.

**What happened (D30):** after the D30 evidence was captured, the RLS suite was run to satisfy
Part 20. It truncated the demo data (orgs 97→~11, staff 10→3, entities 12→6, items/review/files/
reports→0) and left RLS-test residue. The D30 screenshots/smoke evidence were captured BEFORE
that run and remain valid.

**Restoration applied (idempotent):**
1. `local_backups/seed_demo_data.sql` minus the factor-dependent blocks (section 18 —
   `calculation_snapshots` + `emissions_logs`, lines 279–304) which reference
   `emission_factors` UUIDs absent after the truncate (same skip D29 used).
2. Processing Entity fixtures: Entity Alpha (`84069bf1-…`), Entity Beta (`f77e6b5f-…`),
   `entity-staff@demo.carbontally.local` staff profile (Entity Beta, operator role).
3. Consultant-member fixture (`consultant-member@demo.carbontally.local`): own firm profile,
   firm membership + ACTIVE client grant.

**Post-restore verification:** D30 smoke suite 12/12 PASS (customer dashboard + denials,
consultant portfolio owner/member, platform/review/QC reporting + denials, entity performance +
isolation); UI panels re-verified rendering.

**Recommended fix (pre-existing hazard):** point `INTEGRATION_DATABASE_URL` at a dedicated test
database (e.g. `carbontally_test`) in the shell before running the integration suite — the D30
RLS evidence (11 passed) was gathered against the main database by mistake and the data was
restored afterwards. Do NOT re-run the integration suite against the default URL.

**Residual state (vs D29):** the production data restored on 2026-08-20
(`carbon_tally_live_public_data.sql`, a non-idempotent pg_dump COPY) is NOT re-applied — the demo
org + demo accounts + entity fixtures are present and functional; `organizations` now holds 11
rows (demo + RLS-test residue). Restoring the 97-org production snapshot requires re-running that
dump after cleaning the RLS-test residue.



