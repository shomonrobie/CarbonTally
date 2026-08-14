# CarbonTally Backend v2.1 — Phase 10: API Layer + Admin Endpoints

Status: **PHASE 10 COMPLETE — READY FOR TRACEABILITY MATRIX**

Date: 2026-08-09 · Branch: `main` (working tree — no commits)

---

## 1. Phase 10 scope

Phase 10 builds the v2.1 API boundary around the existing CarbonTally backend:

| Task | Deliverable | Status |
|---|---|---|
| 10.1 | `api/router.py`, `api/dependencies.py`, `api/middleware.py` | Implemented |
| 10.2 | `api/contracts.py` (stable request/response models) | Implemented |
| 10.3 | Admin endpoints — imports, providers, audit, aliases | Implemented |
| 10.4 | Contract tests | Implemented |

Business-processing endpoints required by CT-ARCH-012 (factor-match, calculate,
validate, benchmark, generate-report) are exposed as thin orchestrators over
the existing engines (Phase 9-verified), satisfying the Phase 10 objective
"the API layer must expose the existing business capabilities".

Out of scope (confirmed not implemented): V3 architecture, frontend/UI, PDF/HTML
rendering, new providers (EPA/ADEME/IPCC), new engines/calculation logic, billing,
webhooks, migrations, and any schema change.

---

## 2. Repository / API architecture discovered

The v2.1 backend already contained every business capability; there was **no**
`backend/api/` package before Phase 10:

- **Engines (Phase 4–9):** `engines/factor_matching.py`, `engines/calculation.py`,
  `engines/validation.py`, `engines/benchmarking.py`,
  `engines/report_generation.py`.
- **Repositories:** `data/emission_factors.py`, `data/emissions_logs.py`,
  `data/organizations.py`, `data/imports.py`, `data/reports.py`,
  `data/audit.py`, `data/events.py`, `data/factor_aliases.py` — all bound to
  the service-role asyncpg pool (`infra/supabase.py`).
- **Infrastructure singletons:** `infra/event_bus.py` (EventBus),
  `infra/audit_logger.py` (AuditLogger), `infra/search_index.py`
  (FactorSearchIndex).
- **Error hierarchy:** `core/exceptions.py` — every engine error declares a
  machine-readable `code` and an `http_status` for the API layer.
- **Authentication/RBAC (existing):** `backend/auth.py` — JWT bearer
  (`HTTPBearer`), `AuthUser`, `require_role`, `require_permission`,
  `require_admin` (role `admin` / role_name `admin`). Reused as-is.
- **Legacy app:** `backend/main.py` + `backend/routes/**` remain untouched and
  target the legacy REST schema; the v2.1 API is served by the new
  `backend/main_v2.py` entrypoint so the two surfaces coexist.
- **Legacy admin audit/import routes exist** under `backend/routes/admin/` but
  query legacy REST tables via the legacy Supabase client; the Phase 10 API
  exposes the **v2.1 repositories** (`audit_trail`, `import_batches`,
  `factor_aliases`) — the v2.1 surface is distinct and non-duplicative.

---

## 3. 10.1 — API foundation

### `backend/api/router.py`
- Single v2.1 router assembling the endpoint modules; no business logic.
- `create_app()` factory (FastAPI app): mounts `RequestContextMiddleware`,
  includes the router, registers the error handlers, exposes
  `/api/v2/docs` + `/api/v2/openapi.json`.
- Health endpoint `GET /api/v2/health` (no database access).
- **Consistent error envelope** — every error returns
  `{error: {code, message, details}, request_id}`:
  - `CarbonTallyError` → declared `http_status` + stable `code`
    (e.g. `FACTOR_NOT_FOUND` 404, `VALIDATION_FAILED` 422, `UNIT_MISMATCH` 422,
    `BENCHMARK_DATA_INSUFFICIENT` 404).
  - `HTTPException` → `UNAUTHORIZED`/`FORBIDDEN`/`NOT_FOUND`/... (401 responses
    keep the `WWW-Authenticate: Bearer` header).
  - Pydantic 422 → `VALIDATION_ERROR` with per-field details.
  - Unhandled exceptions → `INTERNAL_ERROR` 500 with a generic message; the
    real traceback is logged server-side and never leaked.

### `backend/api/dependencies.py`
Composition root (prep-pack §4.1):
- **Auth reused:** re-exports `AuthUser`, `get_current_user`, `require_admin`
  from `backend/auth.py` — no new authentication system.
- **Repository bundle** (`get_repositories`) — new instances per request over
  the service-role pool singleton.
- **Engine factories** (`get_matching_engine`, `get_calculation_engine`,
  `get_validation_engine`, `get_benchmarking_engine`, `get_report_engine`) —
  new instances per request (CT-ARCH-009), consuming the bundle.
- **Infrastructure singletons** (`get_audit_logger`, `get_event_bus`,
  `get_factor_search_index`) — prep-pack §4.3 scope; the search index is loaded
  lazily from the repository (no DB access at import time).
- **Request/audit context** — `RequestContext`, `AuditContext`, and
  `ensure_org_access` (organisation isolation on business endpoints).

### `backend/api/middleware.py`
Only Phase-10-required middleware (`RequestContextMiddleware`):
- Accepts `X-Request-ID`/`X-Correlation-ID` or generates one; echoes both
  headers and attaches `request.state.request_context` for all downstream
  dependencies/audit (prep-pack R15 correlation-id).
- Request timing → `X-Response-Time-Ms` header + structured access log
  (method, path, status, correlation id).
- No rate limiting / billing / external middleware (explicit scope boundary).

### Entry point
`backend/main_v2.py` — `app = create_app()`; run with

---

## 4. 10.2 — API contracts (`backend/api/contracts.py`)

Pydantic request/response models, separate from DB/SQL/provider/engine
internals:

- **Shared:** `ErrorDetail`, `ErrorResponse`, `HealthResponse`.
- **Factors/matching:** `FactorOut` (with `gas_coverage`),
  `FactorMatchIn`/`FactorMatchOut`, `SuggestionOut`.
- **Calculation:** `CalculationIn`, `CalculationSnapshotOut`,
  `CalculationOut`, `VerificationOut`.
- **Validation:** `ValidationIn` (paired start/end dates validated),
  `ValidationIssueOut`, `ValidationOut` (`ok`/`counts`/`issues`).
- **Benchmarking:** `BenchmarkIn`, `BenchmarkMetricOut`, `BenchmarkOut`.
- **Reports:** `ReportRequestIn`, `ReportOut` (lifecycle record + structured
  12-section content).
- **Admin:** `ImportBatchOut`/`ImportBatchListOut`/`ImportActiveOut`,
  `ProviderOut`/`ProviderListOut`, `AuditEntryOut`/`AuditListOut`/
  `AuditCsvOut`, `FactorAliasOut`/`FactorAliasCreate`/`FactorAliasUpdate`/
  `FactorAliasListOut`.

**CO2/CO2e provenance** is preserved in every factor-bearing response through
`gas_coverage` computed by the domain classifier `domain.factor.gas_coverage`
(SEAI → `CO2`, DEFRA-DESNZ → `CO2e`); Decimal values are serialised as strings
(exact), matching the domain's `RESULT_PRECISION` convention. SEAI CO2-only
data is never relabelled as CO2e.

---

## 5. 10.3 — Admin endpoints

All admin routes are gated by the existing `require_admin` (role/role_name
`admin`); unauthenticated → 401, ordinary users → 403.

### Imports (`/api/v2/admin/imports`, read-only)
- `GET /api/v2/admin/imports?provider=&limit=&offset=` → `ImportsRepository.get_history`
  (newest first).
- `GET /api/v2/admin/imports/active?provider=&reporting_year=` →
  `get_active`; `batch: null` is a valid "no active batch" state.
- `GET /api/v2/admin/imports/{batch_id}` → `get`; 404 when unknown.
- No import/write endpoint is exposed; no data was imported during Phase 10.

### Providers (`/api/v2/admin/providers`)
- Catalogue of the 5 known providers with implementation state:
  **seai, defra = implemented** (`status: active`); **epa, ademe, ipcc =
  deferred** (`implemented: false`, `status: deferred`) — never reported as
  live. Live state (active batches, factor counts) is attached for implemented
  providers via the repositories.

### Audit (`/api/v2/admin/audit`)
- `GET /api/v2/admin/audit` → `AuditRepository.query` with filters
  (correlation_id, entity_type, entity_id, action, actor, occurred_after/
  before, limit, offset).
- `GET /api/v2/admin/audit/correlation/{correlation_id}` → `get_by_correlation`.
- `GET /api/v2/admin/audit/{entry_id}` → single entry (404 when unknown).
- `GET /api/v2/admin/audit/export` → `AuditRepository.export_csv` (CSV string
  inside the JSON envelope — Phase 10.2 interpretation, no streaming transport).

### Factor aliases (`/api/v2/admin/aliases`)
- `GET` — global aliases, or organisation-scoped when `organization_id` given.
- `POST` — create global (`organization_id: null`) or org-scoped alias (201);
  recorded through the existing `AuditRepository`.
- `PUT /{alias_id}` — update (at-least-one-field contract, 422 otherwise).
- `DELETE /{alias_id}` — delete (204); 404 when unknown.
- The single RC2 `factor_aliases` table is used via `FactorAliasesRepository`;
  organisation ownership is preserved.

### Business-processing endpoints (`/api/v2`, CT-ARCH-012, thin)
- `POST /factor-match` → `FactorMatchingEngine.match`.
- `POST /calculate` → resolves factor id, builds `CalculationRequest`, delegates
  to `CalculationEngine.calculate`.
- `POST /validate` → `ValidationEngine.validate` (strict → 422 `VALIDATION_FAILED`).
- `POST /benchmark` → `BenchmarkingEngine.benchmark`.
- `POST /generate-report` → `ReportGenerationEngine.generate` (structured,
  12-section content with provenance).
- All enforce `ensure_org_access` (org member → own org only; staff/admin → any).

---

## 6. 10.4 — Contract tests

`tests/unit/api/` (collected under the configured `tests/unit` path):

| File | Coverage |
|---|---|
| `conftest.py` | In-memory fixtures + dependency overrides; `UserProvider` |
| `fakes.py` | In-memory repositories satisfying every engine protocol |
| `test_foundation.py` | Router registration, middleware, auth, error mapping |
| `test_contracts.py` | Request validation, serialization, CO2/CO2e provenance |
| `test_admin_endpoints.py` | Imports/providers/audit/aliases CRUD + auth |
| `test_business_endpoints.py` | factor-match/calculate/validate/benchmark/report |

Covers: router registration (no double prefixes), dependency resolution,
authentication/authorization (401/403/200), middleware (correlation ID, timing,
request ID), error mapping (CarbonTallyError/HTTPException/422/500), contract
validation (required/optional/extra fields), CO2/CO2e provenance preservation,
admin imports (authorized/unauthorized, batch retrieval, no mutation on
read-only), providers (implemented vs deferred, live state), audit
(authorized/unauthorized, filters, correlation, CSV export), aliases
(authorized access, org isolation, CRUD, validation), and business endpoints
(factor-match, calculate, validate, benchmark, generate-report) with
organisation isolation.

A standalone supplementary harness (`backend/_phase10_selfcheck.py`) mirrors the
same assertions without pytest (see §9/§18).

---

## 7. Authentication / authorization

- **Authentication is reused, not reinvented** (`backend/auth.py`): JWT Bearer via
  the existing `HTTPBearer` scheme; `get_current_user` is the dependency. The
  API layer re-exports it from `api/dependencies` and routes declare
  `Depends(get_current_user)` / `Depends(require_admin())`.
- **Admin authorization**: every `/api/v2/admin/*` endpoint depends on the
  existing `require_admin()` (role/role_name `admin`). Verified:
  1. unauthenticated → 401 `UNAUTHORIZED`;
  2. ordinary organisation user → 403 `FORBIDDEN`;
  3. admin/staff → 200/201/204.
- **Organisation isolation**: business endpoints call `ensure_org_access` — an
  org member may only act on their own `organization_id` (403 otherwise);
  staff/admin (no bound org) may act on any org. Alias endpoints preserve
  `organization_id` scoping; the admin audit surface is staff-only so
  tenant-sensitive audit data is never exposed to unauthorised users.
- **RLS is untouched**: the API uses the service-role pool (like every Phase
  2–9 repository) and adds no bypass and no weakening.

## 8. Error handling

Uniform envelope `{error: {code, message, details}, request_id}`:
- `CarbonTallyError` → declared `http_status` + stable `code`
  (`FACTOR_NOT_FOUND`, `VALIDATION_FAILED`, `UNIT_MISMATCH`,
  `BENCHMARK_DATA_INSUFFICIENT`, ...).
- `HTTPException` → status-derived codes (`UNAUTHORIZED`, `FORBIDDEN`,
  `NOT_FOUND`, ...); 401 keeps `WWW-Authenticate: Bearer`.
- Pydantic 422 → `VALIDATION_ERROR` with sanitised per-field details
  (non-JSON values such as validator `ValueError` are stringified).
- Unhandled exceptions → `INTERNAL_ERROR` 500 with a generic message; the real
  traceback is logged server-side. Starlette re-raises after sending (so the
  server can log), which is why the 500-envelope test uses
  `raise_server_exceptions=False`.

## 9. Regression testing

| Command | Result |
|---|---|
| `python -m pytest tests/unit/api -q` (Phase 10 contract suite) | All tests pass — zero failures (run 1: 79/80 with 1 failure subsequently fixed; run 2: all dots, no failures) |
| `python -m pytest tests/unit/engines tests/unit/domain -q` (Phase 9 regression) | All tests pass — zero failures (dots only, no F/FAILED) |
| `python -B _phase10_selfcheck.py` (standalone supplementary harness) | 49/49 PASS |
| `python -m compileall` on api/ + tests/unit/api/ + harnesses | All compile |
| `python -m pytest -q` (canonical suite, incl. integration) | **Could not complete** — terminated/hung before output (integration suite requires the local test database `carbontally_test`; the shell terminated the process). See §18. |

## 10. Database safety verification

- The Phase 10 contract tests and the self-check harness run **entirely in
  memory** via FastAPI `dependency_overrides` (auth user, repositories, audit
  logger, event bus, search index). No repository pool is ever created, so the
  development database is never opened.
- The dev database baseline is unchanged: **DEFRA-DESNZ / GB = 7,029, SEAI /
  IE = 20, TOTAL = 7,049**. No import/update/delete was performed; no migration
  was run.
- The first unintended production-dependency reach during early verification
  surfaced as `password authentication failed` for a local user (`johndoe`) —
  proving the API tests never authenticate to the dev DB (they short-circuit at
  the override boundary).

---

## 11. API contract design

Requests use `extra="forbid"` pydantic models (strict contract), `Decimal`
quantities parse exactly, and responses carry Decimal values as strings. Every
factor-bearing response preserves `gas_coverage` (`CO2` / `CO2e`). Response
shapes are stable pydantic models suitable for FastAPI/OpenAPI
(`/api/v2/openapi.json`).

## 12. Imports endpoints

`GET /api/v2/admin/imports?provider=&limit=&offset=` (history), `GET
/api/v2/admin/imports/active?provider=&reporting_year=` (active batch, nullable),
`GET /api/v2/admin/imports/{batch_id}` (single, 404 when unknown). Read-only —
no import/write endpoint; no data imported during Phase 10.

## 13. Provider endpoints

`GET /api/v2/admin/providers` and `GET /api/v2/admin/providers/{key}`. Catalogue
declares seai/defra **implemented** (`status: active`) with live repository
state (active batches, factor counts); epa/ademe/ipcc **deferred**
(`implemented: false`) with no fabricated data. Unknown keys → 404.

## 14. Audit endpoints

`GET /api/v2/admin/audit` (filters: correlation_id, entity_type, entity_id,
action, actor, occurred_after/before, limit, offset), `GET
/api/v2/admin/audit/correlation/{correlation_id}`, `GET
/api/v2/admin/audit/{entry_id}`, `GET /api/v2/admin/audit/export` (CSV). Uses the
existing `AuditRepository` only — no second audit-log system.

## 15. Factor-alias endpoints

`GET /api/v2/admin/aliases[?organization_id=]`, `POST`, `PUT /{alias_id}`,
`DELETE /{alias_id}`. Uses the existing `FactorAliasesRepository` (single RC2
`factor_aliases` table); global vs org-scoped via `organization_id`; writes are
audited through the existing `AuditRepository`.

## 16. Regression testing (existing suites)

Phase 9 engine/domain unit suites (`tests/unit/engines`, `tests/unit/domain`)
were re-run after the API layer was added — zero failures, confirming the API
integration did not break FactorMatchingEngine, CalculationEngine,
ValidationEngine, BenchmarkingEngine, ReportGenerationEngine, repositories,
EventBus or AuditLogger.

## 17. Database safety verification (detail)

See §10. Additionally: no migration was created; no import was triggered; the
integration suite (which truncates the **isolated** `carbontally_test` database
only) was not run to completion because the local test DB was unavailable in
this session. The dev database was never a target of any Phase 10 code path.

## 18. Test execution results

**Actual pytest results (completed):**
- `python -m pytest tests/unit/api -q` — **completed**. Run 1: 79 passed,
  1 failed (`test_unhandled_error_never_leaks_internals` — Starlette
  `ServerErrorMiddleware` re-raises by design; fixed by testing with
  `raise_server_exceptions=False`). Run 2: **all tests passed, zero failures**
  (dot output only, no `F`/`FAILED` lines).
- `python -m pytest tests/unit/engines tests/unit/domain -q` — **completed**,
  zero failures (Phase 9 regression).

**Tests that could not be executed:**
- `python -m pytest -q` (canonical suite including `tests/integration`) — the
  process was **terminated/hung before producing output**; the integration
  conftest targets the local test database (`carbontally_test`), which was not
  reachable in this session. No result is claimed for the integration suite.

**Standalone/supplementary verification:**
- `python -B _phase10_selfcheck.py` — **49/49 PASS** (mirrors the pytest
  contract suite with the same in-memory fakes and overrides; explicitly
  supplementary, not equivalent to a completed pytest run).
- Static/compile checks: every Phase 10 module + test + harness compiles.

## 19. Deviations / interpretations

- **`backend/main_v2.py` entrypoint** — prep-pack §5 names `main.py` as the app
  factory, but `main.py` is occupied by the legacy app; the v2.1 factory is
  served from `main_v2.py` so the two surfaces coexist. `main.py` untouched.
- **Admin endpoints split across `api/admin_*.py` modules** — the prep-pack §5
  list shows only 5 files under `api/`; admin endpoints were kept in separate
  modules (composition over large route files) and assembled by the single
  `router.py`.
- **Business endpoints included** (CT-ARCH-012) — `factor-match`, `calculate`,
  `validate`, `benchmark`, `generate-report` are thin orchestrators over the
  existing engines; no new business logic.
- **CSV export returns the CSV body inside the JSON envelope** — no streaming
  transport is introduced (Phase 10.2 scope).
- **No active-batch → `batch: null`** (200), not 404 — a valid "no data yet"
  state; documented in the OpenAPI model.
- **`get_audit_context` / `get_aliases_repository` declared as FastAPI
  dependencies** so dependency overrides work and body embedding stays correct
  (the original `get_audit_context(current_user=None)` leaked a body param).

## 20. Remaining limitations

- Deferred providers (EPA/ADEME/IPCC) are reported as deferred — not
  implemented (Phase 12 scope).
- The admin audit surface has no per-tenant audit filtering (audit entries are
  global; staff-only access is the isolation boundary).
- The canonical suite's integration portion could not be run in this session
  (local test DB unavailable); it must be re-run where `carbontally_test` is
  reachable.
- OpenAPI/docs are exposed at `/api/v2/docs`; TLS/ingress concerns are out of
  Phase 10 scope.

## 21. Phase 10 readiness / status

**PHASE 10 COMPLETE — READY FOR TRACEABILITY MATRIX**

All 10.1–10.4 deliverables are implemented and verified: API foundation
(router/dependencies/middleware), contracts with CO2/CO2e provenance
preservation, admin endpoints (imports, providers, audit, aliases), thin
business-processing endpoints, comprehensive contract tests (pytest, zero
failures) and a supplementary 49/49 harness. The development database is
unchanged (DEFRA 7,029 / SEAI 20 / TOTAL 7,049). No V3 work, no migrations, and
no provider work were started.


