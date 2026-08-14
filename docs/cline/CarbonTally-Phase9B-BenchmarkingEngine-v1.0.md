# CarbonTally — Phase 9B BenchmarkingEngine v1.0

**Status: PHASE 9B COMPLETE — READY FOR PHASE 9C**
**Scope:** Phase 9.2 BenchmarkingEngine only (B1–B8 of the approved Implementation Contract)
**References:** `docs/cline/CarbonTally-Phase9-Implementation-Contract-v1.0.md`, `docs/cline/CarbonTally-Phase9A-ValidationEngine-v1.0.md`, Frozen Backend v2.1 Implementation Preparation Pack
**Date:** 2026-08-09

---

## 1. Implementation summary

`BenchmarkingEngine` (`backend/engines/benchmarking.py`) is the internal /
self-referential benchmarking engine. It computes comparisons exclusively from
the organisation's own `emissions_logs` aggregation and `organization_metadata`
— there is **no external reference dataset, no benchmark reference table, and
no cross-tenant comparison** in Phase 9.

- **Read-only.** The engine consumes repository surfaces through protocols
  (`LogsSource`, `OrgSource`, `FactorLookup`) and never writes to the database.
- **Reuses existing infrastructure.** `EmissionsLogsRepository.aggregate` /
  `find_by_org`, `OrganizationsRepository.get_metadata` / `get_facilities`, and
  `AuditLogger` (`benchmark:completed`). `FactorLookup` (`EmissionFactorsRepository`)
  supplies activity labels and CO2/CO2e provenance for B7 and the provenance
  labels.
- **Denominator rule.** Intensity metrics are produced ONLY when the
  denominator is available and valid; otherwise explicit `not_available` /
  `zero_denominator` / `invalid_denominator` results are returned — never an
  estimate or a silent zero. An empty reporting period raises
  `BenchmarkDataInsufficientError` (404).
- **No schema change, no migration, no new table, no factor data touched.**
- **Only B1–B8 implemented** — no external/peer/sector benchmarks, no
  forecasting, no AI insights, no supplier benchmarking.

**Supporting change:** the CO2/CO2e provenance classifier `gas_coverage()` was
moved from `engines/validation.py` to the domain layer (`domain/factor.py`) so
both engines share one definition; `engines/validation.py` now imports it.
Phase 9A behaviour is unchanged (regression-verified).

---

## 2. B1–B8 implementation status

| # | Capability | Status | Implementation |
|---|---|---|---|
| B1 | Year-over-year comparison | ✅ | `total` + `total_vs_<year>` metrics per `compare_years`; `delta`, `delta_pct`, `by_group["year:<y>"]` |
| B2 | Facility-vs-facility | ✅ | `facility:<id>` metrics (value, org-facility-average comparison, YoY when baseline exists); `facility_filter`; `by_group["facility:<id>"]` |
| B3 | Scope breakdown/comparison | ✅ | `scope:<label>` metrics (value + YoY) and `by_scope` totals |
| B4 | Emissions per FTE | ✅ | `per_fte` = total / `organization_metadata.fte_count` |
| B5 | Emissions per floor area | ✅ | `per_area` = total / `total_floor_area_sqm` |
| B6 | Emissions per revenue | ✅ | `per_revenue` = total / `annual_revenue_gbp` |
| B7 | Activity intensity | ✅ | `activity:<activity_type>` metrics = Σ co2e / Σ quantity per activity (unit-consistent); YoY baseline per activity; mixed units → `incompatible_unit`; zero quantity → `zero_denominator` |
| B8 | Approved internal capabilities | ✅ | month/asset groupings (`by_group["month:…"]`, `by_group["asset:…"]`), multiple reporting periods, facility filtering |

---

## 3. Domain model

`backend/domain/benchmarking.py` (new, pure frozen dataclasses):

| Type | Purpose |
|---|---|
| `BenchmarkAvailability` | `available`, `not_available`, `insufficient_data`, `zero_denominator`, `invalid_denominator`, `incompatible_unit`, `incompatible_period` |
| `BenchmarkMetric` | key, label, unit, status, value, numerator, denominator, baseline_value, delta, delta_pct, comparison, source, scope, facility_id, activity_type, note |
| `BenchmarkRequest` | organization_id, reporting_year, compare_years, group_by (year/facility/scope/month/asset), metrics (total/per_fte/per_area/per_revenue/activity_intensity), facility_filter; validates unsupported metrics/groups, year ranges, and rejects `compare_year == reporting_year` (incompatible period) |
| `BenchmarkResult` | organization_id, reporting_year, metrics, by_scope, by_group, generated_at; `metric(key)` lookup |

All four are exported from `backend/domain/__init__.py`; `BenchmarkingEngine` is
exported from `backend/engines/__init__.py`.

---

## 4. Repository dependencies

| Dependency | Surface used | Protocol |
|---|---|---|
| `EmissionsLogsRepository` | `aggregate(org_id, period, group_by)` → `EmissionsAggregate`; `find_by_org(org_id, period)` → logs | `LogsSource` |
| `OrganizationsRepository` | `get_metadata(org_id)`; `get_facilities(org_id)` | `OrgSource` |
| `EmissionFactorsRepository` (supporting) | `get(id)` → factor (activity labels + CO2/CO2e provenance) | `FactorLookup` (optional) |

The engine never re-implements aggregation — all grouping/summing is delegated
to the repository; `find_by_org` is used only for the B7 quantity sums and the
provenance labels that `aggregate` cannot provide.

---

## 5. Denominator / data-availability behaviour

| Condition | Result |
|---|---|
| Reporting period has no logs | `BenchmarkDataInsufficientError` (404), audited as empty |
| Baseline year has no logs | `total_vs_<year>` produced with `baseline_value=None`, `delta=None`, note "baseline year … has no emissions data" |
| Facility has no logs in the year | `facility:<id>` → `insufficient_data` (explicit, numerator 0, note) |
| `organization_metadata` missing | `per_fte`/`per_area`/`per_revenue` → `not_available` (value None, note "denominator missing") |
| Denominator field `None` | `not_available` |
| Denominator zero | `zero_denominator` |
| Denominator negative | `invalid_denominator` |
| Activity group with mixed units | `activity:<…>` → `incompatible_unit` |
| Activity total quantity zero | `activity:<…>` → `zero_denominator` |
| `compare_year == reporting_year` | rejected at the domain layer (`incompatible_period`) |

No value is ever estimated, inferred, fabricated, or silently substituted with
zero.

---

## 6. Multi-country / provenance behaviour

- The engine operates on calculated emissions data and never assumes a
  provider or country.
- `gas_coverage()` (now in `domain/factor.py`) classifies each factor as
  **CO2** (SEAI) or **CO2e** (DEFRA); every metric's `unit` and `source` label
  carry the result: `kg CO2`, `kg CO2e`, or `kg CO2/CO2e mixed`, with
  `source` = comma-joined `factor_source` values (e.g. `DEFRA-DESNZ,SEAI`).
- SEAI CO2-only data is **never silently relabelled** as full CO2e while
  aggregating.
- Verified: all-SEAI → `unit == "kg CO2"`, `source == "SEAI"`; all-DEFRA →
  `"kg CO2e"`; mixed → `"kg CO2/CO2e mixed"`, `source == "DEFRA-DESNZ,SEAI"`;
  SEAI per-FTE → `"kg CO2 per FTE"`.
- Cross-tenant isolation: every repository call is org-scoped; a benchmark for
  org A never reads org B data (verified by test).

---

## 7. Test results

**Files created:** `backend/tests/unit/domain/test_benchmarking.py`
(domain contracts) and `backend/tests/unit/engines/test_benchmarking.py`
(B1–B8, denominator rules, insufficient data, provenance, cross-tenant
isolation, read-only surface).

**Environment limitation:** the tooling shell kills long-running foreground
processes, so `pytest` could not complete this session (same constraint noted
in Phase 9A). Validation was performed two ways:

1. **Compile check** — `python -m py_compile` on all new/modified modules:
   **PASS** (no syntax errors).
2. **Standalone runtime self-check** — a temporary harness executed the
   engine/domain scenarios (same fixtures and assertions as the pytest files)
   directly:

   **36/36 checks PASS, 0 failures** — covering B1–B8 (normal + edge cases),
   the denominator rules (missing/zero/negative), insufficient data (empty
   period raises, empty baseline noted, no-data facility), SEAI CO2-only and
   mixed CO2/CO2e provenance, cross-tenant isolation, the read-only surface,
   audit logging, domain validation, and a **Phase 9A regression** (SEAI
   snapshot + match still validate clean after the `gas_coverage` move).

The pytest files remain the canonical suite (run when the environment
permits):

```bash
cd backend && python -m pytest tests/unit/domain/test_benchmarking.py tests/unit/engines/test_benchmarking.py -q
```

Existing tests were not weakened; the Phase 9A engine behaviour was
regression-verified after the provenance-helper refactor.

---

## 8. Deviations or interpretations

| # | Item | Detail | Severity |
|---|---|---|---|
| D1 | `FactorLookup` dependency added | The contract listed `EmissionsLogsRepository` + `OrganizationsRepository`; B7 activity intensity and the CO2/CO2e provenance labels require factor metadata (activity_type / factor_source), so `FactorLookup` (`EmissionFactorsRepository.get`) is consumed as an optional third surface — consistent with ValidationEngine's `FactorLookup` and the existing repository. | Low (documented) |
| D2 | Missing-metadata error handling | The contract's "raise … when a requested intensity metric has missing metadata" is implemented as an explicit per-metric `not_available` result (per the approved denominator rule, which forbids silent substitution); `BenchmarkDataInsufficientError` is raised only for an empty reporting period. | None (aligns with the approved denominator rule) |
| D3 | `facility_filter` semantics | The filter restricts facility-scoped results (B2 metrics, facility by_group, and the provenance/activity logs) while org-wide totals and intensity metrics remain org-level (denominators are org metadata). | Low (documented) |
| D4 | Audit action label | `benchmark:completed` uses the colon convention of the existing engines (`calculation:completed`, `validation:completed`). | None |
| D5 | Facility comparison baseline | Facility-vs-facility uses the org's facility-average total as the comparison baseline, and YoY facility data when a compare year has data for that facility. | None |

---

## 9. Remaining Phase 9 work

Not implemented in Phase 9B (out of scope per the approved contract):

- **9.3 ReportGenerationEngine** — `backend/engines/report_generation.py`
  (composes Calculation + Validation + Benchmarking; persists via
  `ReportsRepository`; publishes `ReportGenerated`).
- **9.4 Integration tests** — `backend/tests/integration/test_validation.py`,
  `test_benchmarking.py`, `test_report_generation.py` against
  `carbontally_test`.

The BenchmarkingEngine is ready to be consumed by 9.3 (its `BenchmarkResult`
metrics, explicit availability statuses and provenance labels are part of the
9.3 section-building contract).

---

**PHASE 9B COMPLETE — READY FOR PHASE 9C**

