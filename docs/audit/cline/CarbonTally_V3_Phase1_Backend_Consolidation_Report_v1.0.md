---
Document Type: Phase 1 Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + tests); RUNTIME VERIFICATION PENDING (shell unavailable in this session)
Created: 2026-08-15
Author: Cline
Aligned With: docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md,
              docs/architecture/CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md,
              docs/architecture/CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md
---

# CarbonTally V3 — Phase 1: Backend Consolidation & API Exposure Report

## 1. Executive Summary

Phase 1 was implemented in the working tree:

- **Startup/Render blockers** (already fixed in a prior turn) were verified as still in place: `routes/admin/staff.py` imports `Client`; `routes/admin/workload.py` no longer shadows its block-1 router.
- **One V3 FastAPI composition root** was established in `backend/main.py`: it now mounts the existing **V3 (v2.1) API** (`api.router`) alongside the legacy route tree, registering the v2.1 `CarbonTallyError` handler, with a defensive fallback so the legacy app still starts if the V3 layer cannot import.
- **`asyncpg==0.30.0` was added to `backend/requirements.txt`** — required at import time by the V3 repository layer (`data/*`, `infra/supabase.py`); without it the V3 mount would become a new startup blocker.
- **Two tests were added** (`tests/unit/api/test_v3_routes_exposed.py`, `tests/unit/api/test_composition_root.py`) covering endpoint exposure and the single composition root.
- **The 7 Phase-1 capabilities are now reachable** on the composition root: factor-match, calculate, validate, customer-factors, issues, reports (generate-report), processing entities — plus the supporting v2.1 admin surfaces (aliases, imports, providers, audit, benchmark).
- **No legacy code was deleted** (item 8) and **no database/schema/RLS/migration was modified** (item 9).

**Constraint:** the interactive shell tool in this session is wedged on a hung `docker exec` from a previous session, so `pytest`/`uvicorn`/engine-vs-DB verification could NOT be executed here. Static verification was performed on every change, and the exact verification commands are provided in §7.

## 2. Item-by-item status

| # | Phase-1 item | Status | Notes |
|---|---|---|---|
| 1 | Fix startup/Render blockers | DONE (prior turn, verified) | staff.py `Client` import; workload.py duplicate-module fix; asyncpg added so the V3 mount cannot break startup |
| 2 | Establish ONE V3 FastAPI composition root | DONE | `backend/main.py` mounts legacy routes + V3 (`api.router`) on one `app` |
| 3 | Mount the existing V2.1 API | DONE | `app.include_router(api_router)` guarded by `V3_API_AVAILABLE` |
| 4 | Verify V2.1 engines against V3 DB | PARTIAL | Static review of engines/repositories completed; DB-backed verification blocked (shell) — commands in §7 |
| 5 | Run all existing tests | BLOCKED (env) | Shell wedged; commands in §7 |
| 6 | Add missing tests | DONE | 2 new unit tests added |
| 7 | Expose factor-match, calculate, validate, customer-factors, issues, reports, processing entities | DONE (mount) | endpoints listed in §4 |
| 8 | Do NOT delete legacy code | COMPLIED | no deletions |
| 9 | Do NOT modify the database | COMPLIED | no schema/RLS/migration changes |
| 10 | Produce report | DONE | this document |

## 3. Files changed

| File | Change |
|---|---|
| `backend/main.py` | Added V3 (v2.1) API import block with defensive fallback (`V3_API_AVAILABLE`); mounted `api_router` + `CarbonTallyError` handler after legacy includes; close asyncpg pool on shutdown |
| `backend/requirements.txt` | Added `asyncpg==0.30.0` (runtime dep of the V3 repository layer) |
| `backend/tests/unit/api/test_v3_routes_exposed.py` | NEW — asserts the 12 V3/v2.1 route groups are registered on `api.router` |
| `backend/tests/unit/api/test_composition_root.py` | NEW — imports `main` and asserts both legacy and V3 surfaces are on the one app |

Unchanged (verified still in place from the prior fix turn): `backend/routes/admin/staff.py` (Client import), `backend/routes/admin/workload.py` (router include fix).

## 4. Exposed V3 (v2.1) endpoints

Via `backend/api/router.py` (mounted on the composition root):

| Capability | Path(s) | Source |
|---|---|---|
| FACTOR MATCH | `POST /api/v2/factor-match` | api/business.py |
| CALCULATE | `POST /api/v2/calculate` | api/business.py |
| VALIDATE | `POST /api/v2/validate` | api/business.py |
| REPORTS | `POST /api/v2/generate-report` | api/business.py |
| BENCHMARK | `POST /api/v2/benchmark` | api/business.py |
| CUSTOMER FACTORS | `/api/v3/customer-factors/*` | api/customer_factors.py |
| ISSUES | `/api/v3/issues/*` | api/issues.py |
| PROCESSING ENTITIES | `/api/v2/admin/entities/*` | api/admin_entities.py |
| ALIASES | `/api/v2/admin/aliases/*` | api/admin_aliases.py |
| IMPORTS | `/api/v2/admin/imports/*` | api/admin_imports.py |
| PROVIDERS | `/api/v2/admin/providers/*` | api/admin_providers.py |
| AUDIT | `/api/v2/admin/audit/*` | api/admin_audit.py |
| HEALTH (V3) | `GET /api/v2/health` | api/router.py |

Notes: the V3 endpoints require a `DATABASE_URL` at request time (the asyncpg service-role pool in `infra/supabase.py` is created lazily); authentication reuses `auth.py` (JWT + `require_*` guards). On Render, `DATABASE_URL` (Supabase pooler) is required before these endpoints can serve; the legacy surface is unaffected.

## 5. Design decisions

1. **Single composition root, not two apps.** `backend/main.py` remains the canonical entrypoint (`uvicorn main:app`); it now mounts both the legacy `routes/` tree (transition surface) and the V3 (`api.router`) surface on the same `app`, so there is ONE OpenAPI contract.
2. **Defensive fallback.** The V3 import is wrapped so that if the V3 layer cannot import (e.g., a missing dependency in a fresh environment), the legacy app still boots and prints a clear warning. `app.add_exception_handler(CarbonTallyError, carbon_tally_error_handler)` is applied only when the V3 layer is available, and it is type-specific — the legacy error envelope for `HTTPException`/generic exceptions is preserved, so existing frontends are not broken (full v2.1 error-envelope adoption is deferred to the legacy-retirement phase).
3. **`asyncpg` added to runtime requirements** because the V3 repository layer imports it at module level; without it the mount would fail at import.
4. **Pool lifecycle.** The asyncpg pool is closed on application shutdown (guarded).
5. **No schema or deletion changes.** Item 9 (no DB modification) and item 8 (no legacy deletion) are fully respected.

## 6. Verification status

**Executed:**
- Re-read every modified/created file after edit; confirmed syntax and logic (composition-root guard, mount order, handler registration, test assertions against real route objects/prefixes).
- Confirmed v2.1 router prefixes from source: `/api/v2/*`, `/api/v3/customer-factors`, `/api/v3/issues`, `/api/v2/admin/*`.
- Confirmed `auth.py:461` defines `require_entity_member` (imported by `api/dependencies.py`), so the V3 layer is import-safe on the auth path; `infra/supabase.py` pool creation is lazy (no DB access at import).

**Could NOT be executed in this session (environmental):** the shell tool is wedged on a hung `docker exec … psql` from a prior session, so `pytest`, `uvicorn`, `python -m py_compile`, and engine-vs-DB checks could not run. This is not a code defect; it is an environment limitation. Git history/CI should be used to run the suite, or the commands in §7 run from a healthy terminal.

## 7. Commands to run (from a healthy shell)

```bash
cd backend
python -m pip install -r requirements.txt     # includes asyncpg; Python 3.11 recommended
python -m py_compile main.py routes/admin/staff.py routes/admin/workload.py
python -m pytest tests/unit/api/test_v3_routes_exposed.py -q
python -m pytest tests/unit/api/test_composition_root.py -q
python -m pytest tests/unit -q                 # full unit suite
python -m pytest tests/integration -q          # needs local Supabase stack (127.0.0.1:54326)
uvicorn main:app --host 0.0.0.0 --port 8000    # startup smoke test
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/openapi.json        # single OpenAPI: legacy + V3
```

## 8. Limitations & next steps

- **Runtime verification pending** (see §6). Once a shell/CI is available, run §7 before considering Phase 1 closed.
- V3 engine endpoints need `DATABASE_URL` to serve; set it (local stack or Supabase pooler) for engine-vs-DB verification.
- Legacy error-envelope unification and the removal of legacy routes are Phase 2+ items (no deletions performed).
- Next phases (from the approved plans): typed result contracts, consultant/processing-company/QC/supplier/manual-extraction APIs, async workers, split-screen span model, production security.

## 9. Risks

1. If `DATABASE_URL` is not set, V3 endpoints return 500 (pool creation) — expected until env configured; legacy unaffected.
2. Importing the V3 layer adds `asyncpg` as a hard runtime dependency — now declared in `requirements.txt`.
3. Route count/OpenAPI grows (legacy + V3) — intended during transition; reduced when legacy is retired.

