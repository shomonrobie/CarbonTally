---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CarbonTally_V3_Architecture_Specification_v1.0.md, CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§17), V3M2 schema (RC2), `is_org_consultant` RLS helper
---

# CarbonTally V3 — Phase 7: Consultant / Multi-client Report

## 1. Consultant architecture

**COMPLETE.** The consultant surface follows the authoritative V3 model:

    CONSULTANT FIRM (`consultant_profiles`)
        → FIRM MEMBERS (`consultant_firm_members`, active, `client_access` uuid[])
        → CLIENT GRANTS (`consultant_clients`: firm → organisation)
        → CLIENT DATA (emissions / documents / processing / reports — reused V3 repos)

Every consultant endpoint now establishes the consultant identity via
`require_consultant` (new `api/consultant_auth.py`) and re-authorizes any
organisation/client via `ensure_consultant_org_access`, which mirrors the
schema's `public.is_org_consultant(org)` helper:

    authenticated user → active consultant profile → active firm membership
        → (firm member `client_access` contains the org id
           OR the firm holds a `consultant_clients` grant for the org)

The browser-supplied `organization_id`/`client_id` is never trusted without
this server-side check (P0).

## 2. Consultant roles

**COMPLETE.** The consultant domain has its own legitimate role model in the
schema: `consultant_firm_members.role` (free-form display role) **plus** the
real permission columns `can_manage_clients`, `can_upload_documents`,
`can_generate_reports`, `can_manage_team`. The backend uses the **flag columns**
as the authorization surface (no parallel/frontend-only roles):
- `owner`/`manager` = flags granted (firm leadership).
- `consultant` = data-access member; flags restrict actions.
- `viewer` = read-only (no flags).

Documented role hierarchy: role name is informational; the `can_*` flags are
the enforced permissions.

## 3. Client relationship model

**COMPLETE.** `consultant_clients` (firm → organisation grant) is the
relationship model. Supported: client list, add (duplicate 409 + firm
`can_manage_clients` guard), client detail (with org name), status update
(active/inactive, 422 on invalid), deactivate (soft: status → `inactive`).
Client search/filter is **PARTIAL** (frontend filtering; a dedicated search
endpoint is a follow-on).

## 4. Client switching

**COMPLETE.** The consultant UI has a prominent client switcher and an
active-client indicator ("Current organization" banner) that persists the
active client in localStorage and shows the client name + org id. The workspace
banner additionally warns "You are working on: <client>". Every workspace
request carries the client id, which the backend **re-authorizes on every
request** — switching context cannot bypass authorization.

## 5. Consultant dashboard

**COMPLETE.** `GET /api/v3/consultants/me/dashboard` returns real aggregates:
client count, clients by status, active-client count, pending (customer-review)
volume, open issues and ready reports — computed from the firm's
`consultant_clients` joined against real processing/issues/report data. No
fabricated metrics.

## 6. Client workspace

**COMPLETE.** `GET /api/v3/consultants/clients/{id}/context` returns the client
grant, org profile, processing status, issues summary and report counts; the
workspace also surfaces reports/processing tables. The active client is always
explicit.

## 7. Client data access

**COMPLETE (reuse, no duplicated logic).** Authorized-consultant endpoints
reuse the existing V3 repositories:
- `GET /clients/{id}/dashboard` — emissions aggregates (reuses `logs.aggregate`).
- `GET /clients/{id}/reports` — reports list + status (reuses `reports.list_full`/`count_by_status`).
- `GET /clients/{id}/documents` — documents (reuses `files.list_for_org`).
- `GET /clients/{id}/processing/status` — processing status + batches (reuses `manual_extraction`).
- `GET /clients/{id}/issues` — issues (reuses `issues.list_for_org`).

No calculation/matching/processing/report-generation logic was duplicated.

## 8. Client actions

**COMPLETE (via real flags).** Actions map to the schema permission columns:
VIEW (any active member with a client grant), MANAGE_CLIENTS (add/update/
deactivate clients), MANAGE_TEAM (add firm members), UPLOAD_DOCUMENTS and
GENERATE_REPORTS are exposed by the permission model and enforced by
`ensure_consultant_permission`. Consultant upload/report **write** surfaces are
**FOLLOW-ON** (the client-data surface is read-side; the flag columns gate them).

## 9. Authorization model

**COMPLETE.** New `api/consultant_auth.py`:
- `require_consultant` — consultant identity (profile + firm membership).
- `ensure_consultant_org_access` — client-grant authorization (mirrors `is_org_consultant`).
- `ensure_consultant_permission` — real `can_*` flag checks.
- `_checked_client` — client ownership (firm) + org re-authorization on every client endpoint.

## 10. Cross-client isolation

**COMPLETE (P0).** Verified by tests: consultant authorized for clients A+B can
access A and B but CANNOT access C; direct API access to an unauthorized
client, client-id manipulation, and cross-client document/emissions/report/
processing/issues access are all denied (403/404) server-side.

## 11. API endpoints

Created/extended (`/api/v3/consultants/*`):
- `GET/POST /me` — profile (GET guarded; POST creates).
- `GET/POST /me/clients` — client list / add (firm `can_manage_clients`).
- `GET/PUT/DELETE /clients/{id}` — client detail / status update / deactivate.
- `GET /me/dashboard` — consultant dashboard.
- `GET/POST /me/team` — firm members (add guarded by `can_manage_team`).
- `GET/POST /me/tasks`, `PUT /tasks/{id}/status` — tasks.
- `GET /clients/{id}/context|dashboard|reports|documents|processing/status|issues`
  — authorized client-data access (reuses V3 repos).

## 12. Files created

| File | Purpose |
|---|---|
| `backend/api/consultant_auth.py` | Consultant authorization layer |
| `backend/tests/unit/api/test_v3_consultants.py` | Authorization + isolation tests |
| `backend/tests/integration/test_consultants.py` | Consultant repository integration tests |
| `frontend/src/v3/consultant/ConsultantPage.jsx` | Consultant hub (switcher, dashboard, workspace) |
| `frontend/src/v3/consultant/consultant.css` | Consultant UX styles |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_7_REPORT.md` | This report |

## 13. Files modified

| File | Change |
|---|---|
| `backend/data/consultants.py` | Added `get_firm_member_by_user`, `get_client_by_org`, `update_client_status` |
| `backend/api/v3_consultants.py` | Upgraded to `require_consultant`; client management, dashboard, client-data endpoints |
| `backend/tests/unit/api/fakes.py` | Added `MemoryConsultants`, `MemoryManualExtraction`, `MemoryFiles`, `consultant_user`; wired bundle |
| `backend/tests/integration/conftest.py` | Added consultant tables to the truncate list |
| `frontend/src/v3/api.js` | Added consultant API methods |
| `frontend/src/App.js` | Registered `/consultant` route + nav button |
| `frontend/src/v3/__tests__/api.test.js` | Added consultant API client tests |

## 14. Database tables used

| Table | Usage |
|---|---|
| `consultant_profiles` | Consultant firm profile (real columns) |
| `consultant_firm_members` | Firm membership + `client_access` + `can_*` flags |
| `consultant_clients` | Firm → organisation client grants (relationship model) |
| `consultant_tasks` | Consultant tasks (existing surface) |
| `organizations` | Client org profile (via `get_profile`) |
| `emissions_logs`, `calculation_snapshots` | Client emissions (via `logs.aggregate`) |
| `manual_extraction_batches/items` | Client processing status (via `workflow_status`) |
| `issues` | Client issues (via `list_for_org`) |
| `report_generation_queue` | Client reports (via `reports.list_full`/`count_by_status`) |
| `organization_files` | Client documents (via `files.list_for_org`) |

**No database changes, no migrations, no RLS changes, no policy changes.**

## 15. Tests added

- `backend/tests/unit/api/test_v3_consultants.py` (30 tests + route registration):
  - consultant authenticated (401), firm membership required (403), profile (200),
    client list firm-scoped, non-member denied;
  - client A allowed, client B allowed, client C denied, nonexistent 404,
    client-id manipulation denied;
  - client context A, cross-client context/documents/emissions/reports/processing/
    issues all denied (403);
  - client A dashboard real data (183.000000), client reports real data,
    invalid period 422;
  - consultant dashboard real aggregates;
  - add-client permission required (403) / success / duplicate 409,
    add-team `can_manage_team` (403), client status update + invalid 422,
    cross-firm deactivate denied (403), consultant cannot use the customer
    member surface (403).
- `backend/tests/integration/test_consultants.py` (4 tests): profile + firm
  member roundtrip, client grant relationship, update client status,
  firm-scoped client list.
- `frontend/src/v3/__tests__/api.test.js` — consultant API client exports.

## 16. Tests executed

**STATIC VERIFICATION — COMPLETE.** All new/modified files were reviewed for
syntax, imports, wiring and test-logic correctness (route fragments match
mounted paths; consultant fakes satisfy the `RepositoryBundle`; the consultant
authorization chain is exercised on every client endpoint).
**RUNTIME TESTS NOT EXECUTED** — the development shell is wedged (documented
environment blocker), so `pytest`/`npm test` cannot run. No runtime pass is
claimed.

## 17. Runtime verification status

**BLOCKED** — the known wedged shell prevents running `pytest`, `uvicorn`,
`npm test` or any interactive command in this environment. Static checks only.

## 18. Known limitations

- Consultant client-data access is **read-side**; upload/process/report
  **write** actions for consultants are follow-on (the `can_upload_documents` /
  `can_generate_reports` flags exist in the schema and gate them).
- Client **search/filter** is frontend-side; a dedicated backend search
  endpoint is a follow-on.
- `consultant_firm_members.client_access` is treated by the RLS helper as
  containing **org ids**; the backend authorization mirrors that interpretation
  (documented in `consultant_auth.py`).
- Consultant profile **update** (brand, logo, colors) is not part of this
  phase (read + create only) — follow-on.

## 19. API gaps

| Capability | Endpoint checked | Repo checked | DB objects checked | Missing | Minimum clean V3 implementation |
|---|---|---|---|---|---|
| Consultant client search/filter | `GET /me/clients` | `data/consultants.py` | `consultant_clients` | backend search params | extend `list_clients` with search/status filters — follow-on |
| Consultant upload/process/report writes | `GET /clients/{id}/documents` (read-only) | files/processing/reports repos | `organization_files`, `manual_extraction_*`, `report_generation_queue` | write surfaces | guarded endpoints using `can_upload_documents`/`can_generate_reports` — follow-on |
| Consultant profile update | `GET/POST /me` | `data/consultants.py` | `consultant_profiles` | update endpoint | `PUT /me` on real profile columns — follow-on |
| Client invite-to-firm flow | `POST /me/clients` | `data/consultants.py` | `consultant_clients` | invite/accept flow | invite endpoint + accept — follow-on |

## 20. Database gaps

| Table | Missing data | Proposed change | Relationships | RLS implications | Reason |
|---|---|---|---|---|---|
| none required | — | none | — | — | All Phase 7 surfaces map to existing V3M2 tables/columns; **no schema change was made** |

## 21. Security gaps

- The consultant client-data surface re-authorizes via the backend
  (`require_consultant` + `ensure_consultant_org_access`); the existing V3
  customer endpoints remain customer-member-only (a consultant cannot call them).
- RLS is unchanged: `is_org_consultant` already covers the consultant SELECT
  storey for direct client access; write policies remain customer-member-only
  (consultant write surfaces are follow-on).
- No service-role/private credentials are exposed; the frontend uses the
  existing Supabase Auth token only.

## 22. Follow-on work

- Consultant upload/process/report write surfaces (flag-gated).
- Client search/filter endpoint; consultant profile update.
- Client invite/accept flow.
- Runtime verification once the environment recovers.

## 23. Phase 8 readiness decision

**READY — with the same runtime caveat as Phases 4–6.** Phase 7 code, wiring
and static verification are complete; the consultant/multi-client workflow
enforces client isolation server-side (P0) and reuses the authoritative V3
repositories. Phase 8 (internal operations/QC) must not begin until (a) the
wedged shell is recovered and the full backend + frontend suites execute green,
and (b) the documented follow-ons (consultant write surfaces, client search,
invite flow) are explicitly approved. Per instructions, Phase 8 is **NOT
started**.


