---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md (§7–9), ADR-V3-002/014, D-cf-3/D-cf-5
---

# CarbonTally V3 — Phase 4: Emissions Intelligence Report

## 1. Implemented capabilities

| # | Capability | Status |
|---|---|---|
| 1 | Emissions dashboard | **COMPLETE** — `GET /api/v3/emissions/dashboard` |
| 2 | Scope breakdown | **COMPLETE** — `GET /api/v3/emissions/scope-breakdown` (+ dashboard `by_scope`) |
| 3 | Activity/category breakdown | **COMPLETE** — dashboard `by_activity` (from `calculation_snapshots.activity_type`) |
| 4 | Supplier analysis | **COMPLETE** — dashboard `by_supplier` (`emissions_logs.supplier_id` join) |
| 5 | Facility analysis | **COMPLETE** — dashboard `by_facility` (`metadata->>'facility_id'`) |
| 6 | Asset analysis | **COMPLETE** — dashboard `by_asset` (`asset_id`) |
| 7 | Reporting-period views | **COMPLETE** — every view takes `start_date`/`end_date` (inclusive `DateRange`) |
| 8 | Emission-factor interface | **COMPLETE** — `GET /factors` search + `GET /factors/{id}` detail |
| 9 | Customer factor management | **COMPLETE (existing)** — `/api/v3/customer-factors` (list/create/update/approve/deactivate) reused, not duplicated |
| 10 | Factor provenance | **COMPLETE** — factor detail returns source/set/batch/provider/year/country/unit/scope/natural key + usage stats |
| 11 | Calculation history | **COMPLETE** — `GET /calculations` (persisted snapshots, paginated) |
| 12 | Calculation details | **COMPLETE** — `GET /calculations/{id}` (inputs → factor → result) |
| 13 | Calculation provenance | **COMPLETE** — details `provenance` block + `POST /calculations/{id}/verify` (hash + recompute check) |

**Phase 3 correction (authoritative calculation):** the workflow
`POST /api/v3/processing/items/{id}/calculate` no longer accepts a
client-supplied result. It now runs the authoritative `engines/calculation.py`
from the item's extracted quantity/unit and mapped factor, persists the
immutable snapshot + `emissions_logs` row, and only then stamps the item.

## 2. Files created

- `backend/api/v3_emissions.py` — V3 emissions-intelligence router (7 endpoints).
- `backend/tests/unit/api/test_v3_emissions.py` — route registration + pure-helper tests.
- `docs/audit/cline/CARBONTALLY_V3_PHASE_4_REPORT.md` — this report.

## 3. Files modified

- `backend/data/emissions_logs.py` — added the Phase 4 read surface:
  `aggregate_by_supplier`, `aggregate_by_activity`, `count_snapshots`,
  `list_snapshots`, `get_snapshot`, `snapshot_count_for_factor`,
  `factor_usage_span` (+ `_SNAPSHOT_COLUMNS`).
- `backend/api/v3_processing_workflow.py` — corrected the item `/calculate` to
  run the authoritative engine (`CalculationEngine`), removed the client
  `calculated_emissions_kg_co2e` field from `CalculatePayload`.
- `backend/api/router.py` — mounted `v3_emissions_router`.

## 4. Endpoints used / created

Created (`/api/v3/emissions/*`, all `require_org_member` + `ensure_org_access`):
- `GET /dashboard` — total, scope, month, asset, facility, supplier, activity.
- `GET /scope-breakdown` — Scope 1/2/3 (+ Outside of Scopes).
- `GET /calculations` — history (paged, period-filtered).
- `GET /calculations/{id}` — detail + provenance.
- `POST /calculations/{id}/verify` — reproducibility check.
- `GET /factors` — search (query/year/country/scope/unit/source/set/provider).
- `GET /factors/{id}` — detail + provenance + usage.
- `POST /calculate` — authoritative chain (explicit factor/customer-factor, or
  auto-match via the V3 `FactorMatchingEngine` → `CalculationEngine`).

Reused (correct, already mounted — not duplicated):
- `POST /api/v2/factor-match` — authoritative standalone matching.
- `POST /api/v2/calculate` — authoritative calculation contract (same engine).
- `POST /api/v3/customer-factors` + `/approve` + `/deactivate` — customer
  factor management (D-cf-3, org-isolated).

## 5. Database tables used

- `emissions_logs` — scope/unit/asset/supplier/month/facility aggregations
  (`supplier_id` column confirmed present; facility via `metadata`).
- `calculation_snapshots` — immutable forensic records (history/details/verify).
- `emission_factors` (+ `import_batches` join) — factor interface.
- `customer_factors` — customer factor management (existing surface).
- `manual_extraction_items` / `manual_extraction_batches` — workflow `/calculate`
  source inputs and result stamping.

**No schema, RLS, Supabase configuration or .env was modified.**

## 6. Calculation engine status

**COMPLETE.** The authoritative `engines/calculation.py` is used directly by:
- the corrected workflow item `/calculate` (`Depends(get_calculation_engine)`),
- the new `POST /api/v3/emissions/calculate`,
- the existing `POST /api/v2/calculate` (unchanged).

No second calculation implementation was introduced. The engine performs
unit-match validation (`UnitMismatchError` → 422), `RESULT_PRECISION`
quantisation, snapshot content-hash construction, and persistence through the
`CalculationSink` protocol (`EmissionsLogsRepository.save_snapshot` + `create`/`save`).
The frontend never calculates.

## 7. Factor matching status

**COMPLETE.** The authoritative `engines/factor_matching.py` (staged pipeline
over the search index, customer-factor precedence D-cf-5) is used by:
- `POST /api/v3/emissions/calculate` auto-match path (`Depends(get_matching_engine)`),
- the existing `POST /api/v2/factor-match` (unchanged, correct — reused).

Aliases are supported through the pipeline's `alias_match` stage
(`RepositoryAliasResolver`), reporting year/country/scope/unit are matching
inputs, and factor source/set/provenance are returned on results/snapshots.
No matching logic was duplicated in the frontend or reimplemented.

## 8. Emissions dashboard status

**COMPLETE.** `GET /api/v3/emissions/dashboard` returns real aggregates from
persisted rows only — no invented metrics. Each breakdown maps to a real
column (see §5). Empty organisations return zeroed/empty breakdowns.

## 9. Factor-management status

**COMPLETE.** Managed factors: search + detail with provenance. Customer
factors: the existing org-isolated `/api/v3/customer-factors` surface (draft →
create/edit → admin approve with no self-approval → soft deactivate) is reused.

## 10. Provenance status

**COMPLETE.** Calculation detail returns the human-readable provenance block
(factor_kind, factor_source, factor_set, import_batch_id, reporting_year,
methodology, algorithm_version, content_hash, calculated_at/by, request_id).
`POST /verify` recomputes `quantity × co2e_multiplier` (RESULT_PRECISION) and
the SHA-256 content hash and compares to the stored snapshot (`tampered` flag).
Factor detail returns source/set/batch/provider + usage span. Historical
results are never recomputed by the frontend — they come from
`calculation_snapshots`.

## 11. Calculation-history status

**COMPLETE.** `GET /api/v3/emissions/calculations` lists persisted snapshots
(activity, activity_type, quantity, unit, co2e_kg, factor refs, factor source/set,
methodology, algorithm version, content hash, calculated_at, factor_kind,
customer_factor_id) with period filter and pagination; each row links to its
detail/verify endpoints. Nothing is recomputed client-side.

## 12. Tests added

- `tests/unit/api/test_v3_emissions.py`:
  - route registration for all 8 `/api/v3/emissions/*` paths;
  - regression guard: workflow `CalculatePayload` no longer accepts
    `calculated_emissions_kg_co2e` (frontend cannot supply the result);
  - `verify_snapshot_row`: passes for untampered, detects tampered result,
    detects tampered hash;
  - `shape_snapshot` human-readable contract;
  - `build_period` valid + inverted-range rejection;
  - `filter_factors` scope/source/set filtering.
- Existing suites remain: `test_calculation.py` (engine), `test_customer_factor_integration.py`
  (customer-factor matching + isolation + snapshot provenance), `test_v3_customer_factors.py`,
  `test_v3_routes_exposed.py`, `test_v3_processing_workflow.py` (unchanged).

## 13. Tests executed

**NOT EXECUTED (runtime).** The local shell/runtime environment remains wedged
(a hung `docker exec` from earlier sessions blocks every command), so
`pytest`/`py_compile`/`uvicorn` could not run in this session. No claim of a
passing runtime test is made. Static review was performed instead: imports,
route wiring, repository-method usage, and pure-helper logic were verified
against the authoritative engine/domain contracts.

## 14. Runtime verification status

**BLOCKED (environmental).** Same limitation as Phases 2–3: the shell tool
cannot execute processes. The V3 layer was previously verified as importable in
Phase 1; the new modules follow the identical wiring pattern. Commands to run
when the environment recovers:

```bash
cd backend
python -m py_compile api/v3_emissions.py api/v3_processing_workflow.py \
    data/emissions_logs.py tests/unit/api/test_v3_emissions.py
python -m pytest tests/unit/api/test_v3_emissions.py tests/unit/api/test_v3_routes_exposed.py -q
python -m pytest tests/unit -q
uvicorn main:app --host 0.0.0.0 --port 8000   # then curl /openapi.json
```

## 15. Known limitations

- Runtime verification pending (see §14).
- `GET /calculations` filters snapshots by their business `date`; historical
  rows created before a log row existed still appear (snapshots are always
  written with a log by the engine, so coverage is complete).
- `POST /emissions/calculate` returns the engine's `CalculationOut` but does not
  yet return the linked `emissions_logs` row id (the log is created by the
  engine; a follow-on can surface it for row-level drill-down).
- Facility breakdown relies on `metadata->>'facility_id'` (no `facility_id`
  column on `emissions_logs` — documented RC2 design).
- The dashboard `by_activity` joins snapshots to logs via `snapshot_id`; logs
  without a snapshot (legacy/backfilled) do not appear in the activity
  breakdown but do appear in the scope/asset/facility/supplier breakdowns.

## 16. API gaps

- No V3 standalone `factor-match` alias — `POST /api/v2/factor-match` remains
  the authoritative contract (deliberately reused, not duplicated).
- No per-log drill-down endpoint exposing `emissions_logs` row details
  (e.g. `supplier_id`, `data_source`, `confidence_score`) — **FOLLOW-ON**.
- Customer-factor search is not merged into `GET /emissions/factors`; customer
  factors are surfaced by their own org-isolated endpoint — **FOLLOW-ON** if the
  dashboard needs a combined factor picker.

## 17. Database gaps

- **No schema change was required or made.** All Phase 4 reads map to existing
  columns (`emissions_logs.supplier_id`, `asset_id`, `metadata`, `scope`, `unit`;
  `calculation_snapshots.*`).
- Proposed (not executed) additive improvements for later phases:
  - a `facility_id` column on `emissions_logs` (removes the metadata round-trip);
  - a `verified`/`confidence` display surface using existing
    `data_source`/`confidence_score`/`verified_by`/`verified_at` columns.

## 18. Security concerns discovered

- Org isolation is enforced in-code (`ensure_org_access`) on every new
  endpoint; the service-role pool bypasses RLS, so this is the only barrier —
  the existing production-security follow-on (user-scoped query discipline +
  RLS for direct client access) still applies.
- `calculation_snapshots` read surface is org-filtered but `get_snapshot` is
  checked against the caller's org after the read — same pattern as
  `api/issues.py` (accepted in this codebase; keep consistent).
- `POST /calculate` with a `customer_factor_id` re-verifies the caller is a
  member of the factor's org and that the factor is `active` — an inactive or
  cross-org customer factor cannot be used.

## 19. Follow-on work

- Surface the `emissions_logs` row id + supplier/facility from `/calculate`.
- Combined managed+customer factor picker on the emissions surface.
- Frontend screens (dashboard, history, factor browser) consuming the new
  endpoints with loading/empty/error states (V3 design system) — backend only
  was built in this phase.
- Row-level drill-down (log → snapshot → verify) and export.
- Runtime verification once the environment recovers (§14).

## 20. Phase 5 readiness decision

**READY — with one dependency.** Phase 4 backend is complete and wired; Phase 5
should begin only after (a) runtime verification of Phase 4 passes in a healthy
environment, and (b) the frontend consumes the authoritative endpoints (the
legacy frontend factor map must be removed as part of that work).


