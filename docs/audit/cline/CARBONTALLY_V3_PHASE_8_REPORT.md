---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED — Phase 8 (Internal Operations / Processing / QC) backend + frontend + tests complete; runtime-verified at unit level
Created: 2026-08-16
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§10–17), CarbonTally_V3_Architecture_Specification_v1.0.md, ADR-V3-001/007/009/010/011/014, V3M-1/V3M-2 schema
---

# CarbonTally V3 — Phase 8: Internal Operations / Processing / QC Report

## 0. Summary

Phase 8 delivers the CarbonTally-internal workforce layer on the authoritative
V3 chain: **operations dashboard, staff roster, operator/reviewer/QC queues,
the item workflow (start/extract/map/validate/calculate/QC), batch & review
assignment, SLA settings, processing-company dashboards, the shared split-screen
workspace, and role-specific server-side authorization.** The backend surface
was substantially present on disk before this session (Phase 8 was IN PROGRESS
after the power loss); this session completed its unit-test suite, fixed three
genuine defects (the `CalculationRequest(id=...)` call in the calculate
endpoints, the missing `entity_id` on `ReviewItem`/`ReviewQueueRepository`, and
the pre-existing v3_operations/fakes corruption that blocked collection), built
the V3 operations frontend, restored the test environment
(`pytest-asyncio`), and drove the **full unit suite to green (~900 tests,
RC=0)**.

Classification legend: **COMPLETE** / **PARTIAL** / **BLOCKED** /
**NOT IMPLEMENTED** / **FOLLOW-ON**.

---

## 1. CarbonTally Operations — **COMPLETE**

- Ops-wide dashboard (`GET /api/v3/ops/dashboard`): organizations, processing
  entities, staff, pipeline (batches/items by status/stage, % complete), review
  queue, issues, SLA settings — all real data.
- Staff roster (`GET /api/v3/ops/staff`, `POST /api/v3/ops/staff`,
  `PUT /api/v3/ops/staff/{id}`, `GET /api/v3/ops/staff-roles`).
- Processing-entity list + dashboard (`GET /api/v3/ops/entities`,
  `GET /api/v3/ops/entities/{id}/dashboard`).
- Frontend: `OpsDashboard` + `StaffRoster` tabs in
  `frontend/src/v3/ops/OperationsPage.jsx`.

## 2. Data Entry — **COMPLETE**

- Operator queue (`GET /api/v3/ops/queues/operator`), next-item
  (`GET /api/v3/ops/next-item`), item claim (`POST /items/{id}/start`),
  extraction (`POST /items/{id}/extract`), mapping (`POST /items/{id}/map`),
  calculation (`POST /items/{id}/calculate`) — all server-side authorized
  (`can_process` + operator batch assignment).
- Frontend: `OperatorQueue.jsx` with the shared workspace (extraction form +
  mapping form).

## 3. Reviewer — **COMPLETE**

- Review queue (`GET /api/v3/ops/queues/review`), item validation
  (`POST /items/{id}/validate`, `can_review`), review assignment
  (`POST /review/{id}/assign`, `can_review` + `can_manage_staff`), review
  completion (`POST /review/{id}/complete`, `can_review`).
- Frontend: `ReviewQueue.jsx` with validate/assign/complete actions.

## 4. QC — **COMPLETE**

- QC queue (`GET /api/v3/ops/queues/qc` + admin `GET /api/v3/qc/queue`),
  stats (`GET /api/v3/qc/stats`), item QC decision
  (`POST /api/v3/ops/items/{id}/qc` and admin `POST /api/v3/qc/items/{id}/review`)
  — pass/fail, 0–100 quality score, QC notes (`can_review`; admin for
  `/api/v3/qc/*`).
- Frontend: `QcQueue.jsx` with pass/fail + score + notes; validation/calculation
  visible via the shared workspace.

## 5. Processing Company — **PARTIAL**

- Processing-company dashboard (`GET /api/v3/ops/entities/{id}/dashboard`) with
  staff count, entity-scoped review queue and issues — **COMPLETE**.
- Entity-scoped review: `manual_review_queue.entity_id` is now read/written by
  the domain/repo/fake (this session), so entity staff review only their own
  entity's items — **COMPLETE**.
- `upload_batches.entity_id` (V3M-2) is **not yet written** by any Phase 8 code
  path (manual-extraction batches/items carry no entity column) — **FOLLOW-ON**
  (documented design; entity work flows through `manual_review_queue`/`issues`).

## 6. Operator management — **COMPLETE**

- Staff roster create/list/update over real `staff_profiles` columns, role
  reference catalog (`staff_roles` + `roles`), `is_active`, `entity_id`,
  `max_concurrent_tasks`; role permissions resolved server-side from
  `roles.permissions` via `staff_profiles.role_id`.

## 7. Assignment — **COMPLETE**

- Batch assignment (`POST /api/v3/ops/batches/{id}/assign`,
  `can_manage_staff` + `can_process`) and review assignment
  (`POST /api/v3/ops/review/{id}/assign`); operator self-serve on open
  unassigned batches; entity-scoped denial tests.

## 8. Queue — **COMPLETE**

- Operator, review and QC queues over real rows; `list_operator_batches`,
  `next_operator_item`, `list_qc_pending`, `ReviewQueueRepository.list_items`
  (status/assigned_to filters, priority ordering).

## 9. SLA/priority — **PARTIAL**

- Queue-settings read (`GET /api/v3/ops/sla/settings`: max reviews per staff,
  SLA hours, escalation, priority weights) — **COMPLETE**.
- SLA-deadline breach calculation/escalation engine is **NOT implemented** in
  Phase 8 (schema columns `sla_deadline`/`sla_breached`/`escalation_level` are
  carried by the domain/repo but no background escalator exists) —
  **FOLLOW-ON**.

## 10. Shared split-screen workspace — **COMPLETE**

- Backend: `GET /api/v3/ops/items/{id}/workspace` returns the **same Phase 3
  workspace contract** (`source` + `data` + `status` + `issues` + `workflow`
  with allowed transitions) — no separate document-viewer implementation.
- Frontend: `WorkItemWorkspace.jsx` renders the source/data panes and layers
  **role-specific controls** via a render prop:
  - Data Entry → extraction + mapping.
  - Reviewer → validation + review (extraction/mapping/validation visible).
  - QC → pass/fail + score + notes (extraction/mapping/factor/calculation/
    validation visible).
- No fabricated coordinate highlighting: `viewer_url` is served as-is; source
  spans/coordinate highlighting is a documented follow-on (no span model).

## 11. Authorization — **COMPLETE**

Server-side authorization chain (`api/operations_auth.py`) over real schema
tables — the frontend visibility is never the barrier:

- `require_staff` — active `staff_profiles` row.
- `ensure_staff_permission` — `roles.permissions` jsonb via `role_id`.
- `require_internal_staff` — `entity_id IS NULL` = CarbonTally internal.
- `require_entity_scope` / `ensure_entity_review_scope` — entity staff scoped to
  their own entity's review items/issues.
- `ensure_batch_operator_access` — operator may only touch batches assigned to
  them or open/self-serve; entity staff structurally denied from the
  manual-extraction pipeline.

Covered by `test_operations_auth.py` (18 tests) and the security tests in
`test_v3_operations.py` (authorized→allowed; missing staff/permission→403;
cross-entity review→403; other-operator batch→403; missing item→404; entity
staff→403 on manual-extraction items).

## 12. API endpoints — **COMPLETE**

`/api/v3/ops/*` (mounted in `api/router.py`):

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/me` | caller staff context |
| GET | `/dashboard` | ops dashboard |
| GET | `/staff` · POST `/staff` · PUT `/staff/{id}` · GET `/staff-roles` | staff roster + roles |
| GET | `/entities` · GET `/entities/{id}/dashboard` | processing companies |
| GET | `/queues/operator` · `/queues/review` · `/queues/qc` | role queues |
| GET | `/items/{id}/workspace` · `/mapping-options` | shared workspace + mapping suggestions |
| POST | `/items/{id}/start` `/extract` `/map` `/validate` `/calculate` `/qc` | item workflow |
| POST | `/batches/{id}/assign` · `/review/{id}/assign` · `/review/{id}/complete` | assignment |
| GET | `/sla/settings` · `/next-item` | SLA + next item |

`/api/v3/qc/*`: `GET /queue`, `GET /stats`, `POST /items/{id}/review`.

## 13. Frontend routes/components — **COMPLETE**

- Route: `/ops` registered in `frontend/src/App.js` (ProtectedRoute +
  DashboardLayout).
- `frontend/src/v3/ops/`:
  - `OperationsPage.jsx` — tabbed hub (Dashboard / Data entry / Review / QC /
    Staff).
  - `OpsDashboard.jsx` — workload, pipeline-by-stage, pending review/QC,
    issues.
  - `OperatorQueue.jsx` — operator queue + next item + extraction/mapping forms.
  - `ReviewQueue.jsx` — review queue + validate/assign/complete.
  - `QcQueue.jsx` — QC queue + pass/fail + score + notes.
  - `StaffRoster.jsx` — staff list + create.
  - `WorkItemWorkspace.jsx` — shared split-screen workspace.
  - `ops.css` — styles.
- API client: `frontend/src/v3/api.js` gains the `/api/v3/ops/*` and
  `/api/v3/qc/*` methods (no invented contracts — mirrors the real endpoints).


## 14. Files created (this phase)

| File | Purpose |
|---|---|
| `backend/domain/staff.py`, `domain/operations.py`, `domain/partners.py` | staff/ops/workflow domain (Phase 8; partners extended Phase 3) |
| `backend/data/staff.py`, `data/review_queue.py`, `data/queue_settings.py` | Phase 8 repositories |
| `backend/api/operations_auth.py`, `api/v3_operations.py`, `api/v3_qc.py`, `api/v3_manual_extraction.py` | Phase 8 API surface |
| `backend/engines/processing_workflow.py` | item validation rules |
| `backend/tests/unit/api/test_operations_auth.py` (18) | auth-guard tests |
| `backend/tests/unit/api/test_v3_operations.py` (31) | ops surface tests |
| `backend/tests/unit/api/test_v3_qc.py` (5) | QC surface tests |
| `backend/tests/unit/api/route_paths.py` | centralized FastAPI route-path helper |
| `backend/requirements-dev.txt` | dev deps (pytest, pytest-asyncio) |
| `frontend/src/v3/ops/*` | V3 operations frontend (8 files) |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_8_REPORT.md` | this report |

## 15. Files modified (this phase)

| File | Change |
|---|---|
| `backend/api/v3_operations.py` | corruption repair (pre-existing; restored displaced bodies); removed `CalculationRequest(id=...)` |
| `backend/api/v3_processing_workflow.py` | removed `CalculationRequest(id=...)` (same genuine bug) |
| `backend/api/v3_emissions.py` | removed `CalculationRequest(id=...)` (same genuine bug) |
| `backend/domain/operations.py` | added `ReviewItem.entity_id` (V3M-2 schema-aligned) |
| `backend/data/review_queue.py` | `entity_id` column/mapper/insert |
| `backend/tests/unit/api/fakes.py` | corruption repair; `MemorySuppliers` returns `Supplier` objects; `MemoryReviewQueue.create_item(entity_id=…)` |
| `backend/tests/unit/api/test_v3_reports.py`, `test_v3_routes_exposed.py` | centralized helper + test-defect fixes (earlier session) |
| `backend/tests/unit/api/test_v3_consultants.py`, `test_v3_customer_admin.py`, `test_v3_emissions.py`, `test_v3_legacy_reimplementation.py`, `test_v3_new_capabilities.py`, `test_v3_processing_workflow.py`, `test_foundation.py`, `test_composition_root.py` | route-registration tests use the centralized `flatten_router_paths`; stale expectation fixes |
| `frontend/src/v3/api.js`, `frontend/src/App.js`, `frontend/src/v3/__tests__/api.test.js` | ops API client, `/ops` route, client tests |

## 16. Database tables used (no schema change in this phase)

`staff_profiles`, `staff_roles`, `roles`, `processing_entities`,
`manual_extraction_batches`, `manual_extraction_items`,
`manual_review_queue` (incl. `entity_id`, V3M-2), `queue_settings`,
`issues`. All columns referenced exist in V3M2; **no migration was written or
applied** in Phase 8.


## 17. Tests added — **54 passed, 0 failed, 0 errors (RC=0)**

| File | Tests | Coverage |
|---|---|---|
| `test_operations_auth.py` | 18 | permission guards, internal/entity scope, batch/review scoping, `require_staff` role-permission resolution |
| `test_v3_operations.py` | 31 | route registration, staff/role authorization, ops dashboard, queues, item workflow (start/extract/map/validate/calculate with the real engine → 183.0 kg CO2e), QC gate, review assign/complete, batch assign, SLA, workspace, mapping options, next-item, security (manipulated batch, missing item, cross-entity, entity-staff denial) |
| `test_v3_qc.py` | 5 | QC routes, admin gate, queue/stats, pass review, score validation |

All run against the in-memory world (no database) through the `client` fixture.

## 18. Full unit-suite result — **COMPLETE (GREEN)**

```
python -m pytest tests/unit -q --tb=no
RC=0    # ≈900 tests collected, 0 failed, 0 errors
```

- The environment correction (pytest-asyncio install, `requirements-dev.txt`)
  resolved the ≈205 async-test failures; the centralized
  `route_paths.flatten_router_paths` helper resolved the ≈9 FastAPI 0.141
  `_IncludedRouter` route-enumeration failures; the remaining 6 test-defect/
  stale assertions were aligned to the authoritative V3 contracts (no
  application behavior changed to satisfy tests).
- Known warnings (non-failing): `StarletteDeprecationWarning` (`httpx`
  TestClient), `FastAPIDeprecationWarning` (`regex=` → `pattern=` in legacy
  `routes/*.py`).

## 19. Integration-test result — **NOT EXECUTED this session (BLOCKED)**

`tests/integration/*` (repo-level, real local Supabase Postgres at
`127.0.0.1:54326`) was **not run** this session — the local Postgres instance
was not confirmed running and the shell is unreliable for long live-DB
sessions. The Phase 8 repositories (`StaffRepository`,
`ReviewQueueRepository`, `QueueSettingsRepository`,
`ManualExtractionRepository` Phase 8 methods) are covered by unit tests via the
in-memory fakes; **live-DB integration tests for these repositories remain a
FOLLOW-ON** (the migration/DB verification suite for V3M-1/V3M-2 already
exists in `tests/integration/test_v3m1_v3m2_processing_entities.py`).


## 20. Runtime verification — **COMPLETE at the unit level**

- Phase 8 suites: **54 passed, 0 failed, 0 errors (RC=0)**.
- Full unit suite: **≈900 tests, RC=0, 0 failures**.
- `python -m py_compile` clean for every Phase 8 module and test file.
- Live HTTP/DB runtime (uvicorn + real Postgres) was not exercised this session
  (**FOLLOW-ON**); the client fixture exercises the real routers/engines
  in-memory.


## 21. Known limitations

- **Integration tests not executed** (§19) — live-DB verification pending.
- **SLA/escalation engine not implemented** (§9) — settings are read but no
  background SLA breach/escalation runs.
- **`upload_batches.entity_id` not written** by Phase 8 code (§5) — entity work
  flows through `manual_review_queue`/`issues`.
- **Manual-extraction batches/items have no entity column** (schema) — entity
  staff structurally cannot run the pipeline (documented design).
- **Frontend not runtime-tested** in a browser this session (no `npm test`
  executed; client methods + routes statically verified).
- **Legacy `regex=` deprecation warnings** in legacy `routes/*.py` (out of
  Phase 8 scope).

## 22. API gaps

- No dedicated SLA-settings update endpoint (`GET /api/v3/ops/sla/settings`
  only; `QueueSettingsRepository.update_settings` exists but is not exposed).
- No QC comments/history endpoint beyond the item QC fields.
- `GET /api/v3/ops/next-item` returns the oldest candidate without an explicit
  priority/queue-weight surface (operator queue exposes progress).
- Follow-on: per-item `assigned_to` on manual-extraction items is not persisted
  (items are claimed via status transitions).

## 23. Database gaps

- **No schema change was required or made** in Phase 8 (§16).
- Proposed (not executed, needs approval): a `facility_id` column on
  `emissions_logs` (Phase 4 follow-on, unrelated); entity columns on
  manual-extraction batches/items (would let entity staff run the pipeline).

## 24. Security gaps

- Service-role pool bypasses RLS; org/entity isolation is enforced in-code
  (`require_staff`, `require_internal_staff`, `require_entity_scope`,
  `ensure_org_access`) — the documented production follow-on (user-scoped query
  discipline + RLS for direct client access) still applies.
- No rate limiting / brute-force protection on ops endpoints (general platform
  hardening — Phase 9/security follow-on).
- `roles.permissions` is authoritative for permissions; `AuthUser.permissions`
  is not trusted by `operations_auth` (verified).

## 25. Legacy functionality still remaining

- The legacy `backend/main.py` monolith and `backend/routes/**` (~47 modules,
  400+ endpoints) remain the deployed surface; V3 mounts on the same app. Legacy
  admin screens (`admin/src/...` ManualReviewQueue, StaffReviewQueue, reviews,
  workload) are **not deleted** (per instruction — no legacy deletion this
  phase). Phase 8 provides the V3 ops surface **alongside** the legacy surface,
  not as a replacement.
- The legacy frontend factor map and legacy manual-review UI remain until the
  V3 frontend is the primary surface (Phase 9/frontend consolidation).

## 26. Phase 9 readiness — **READY (unit level) with integration caveats**

Phase 9 (advanced engine work / platform hardening) may begin after:

1. **Live-DB integration verification** of the Phase 8 repositories (§19) and
   the existing V3M-1/V3M-2/RLS integration suites pass in a healthy
   environment.
2. The documented follow-ons are explicitly approved: SLA/escalation engine,
   `upload_batches.entity_id` propagation, per-item assignment persistence,
   frontend browser test pass.

Phase 9 was **NOT started** in this session.

---

**Status:** Phase 8 implementation (backend + frontend + tests) is complete at
the unit level and runtime-verified (54/54 Phase 8 tests; full unit suite
RC=0). The remaining caveats are the not-yet-executed live-DB integration tests
and the approved follow-ons listed above.

