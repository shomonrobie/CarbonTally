# CarbonTally — Phase 9C ReportGenerationEngine v1.0

**Status: PHASE 9C COMPLETE — READY FOR PHASE 9D**
**Scope:** Phase 9.3 ReportGenerationEngine only (structured report generation of the approved Implementation Contract)
**References:** `docs/cline/CarbonTally-Phase9-Implementation-Contract-v1.0.md`, `docs/cline/CarbonTally-Phase9A-ValidationEngine-v1.0.md`, `docs/cline/CarbonTally-Phase9B-BenchmarkingEngine-v1.0.md`, Frozen Backend v2.1 Implementation Preparation Pack
**Date:** 2026-08-09

---

## 1. Implementation summary

`ReportGenerationEngine` (`backend/engines/report_generation.py`) composes
structured, JSON-serialisable report content for later rendering/API
consumption (Phase 10). It is strictly a *content composer* — no HTTP, no
FastAPI, no PDF/HTML, no template rendering.

- **Read-only over source data.** The engine consumes repository surfaces
  through protocols (`ReportsStore`, `OrgSource`, `LogsSource`,
  `FactorLookup`) and never writes outside the approved persistence path.
- **Engine composition via constructor injection (§4.2).** The Phase 9A
  `ValidationEngine`, Phase 9B `BenchmarkingEngine` and Phase 6
  `CalculationEngine` (verify) are injected as surfaces; the report engine
  adds no validation/benchmarking logic of its own.
- **Mandatory CO2/CO2e provenance.** Every emissions figure carries a
  provenance-aware unit (`kg CO2` / `kg CO2e` / `kg CO2/CO2e mixed`), and the
  provenance section lists `gas_coverage`, `factor_sources`, `factor_sets` and
  `countries`. SEAI CO2-only results are never relabelled as `kg CO2e`, and
  mixed aggregations are explicitly labelled mixed.
- **No fabricated data.** Insufficient data is represented explicitly
  (`insufficient_data`, `not_configured`, availability states) — never as a
  silent zero.
- **Strict validation respected.** When strict validation is configured and
  blocking errors exist, `ValidationFailedError` propagates from the injected
  ValidationEngine and **no report row is created**.
- **Persistence.** Lifecycle + structured content are persisted through the
  existing `ReportsRepository` (`create_generation_request` →
  `complete_generation`) into `report_generation_queue`. The only supporting
  repository change is an optional `content` parameter on
  `complete_generation` that merges the structured content into the existing
  `generated_content` JSONB (backward compatible; `{"page_count": …}`
  behaviour unchanged when omitted).
- **Side effects.** `ReportGenerated` is published to the EventBus and
  `report:generated` is written to the AuditLogger (both fire-and-forget).

**New/changed files:**

| File | Change |
|---|---|
| `backend/engines/report_generation.py` | **New** — `ReportGenerationEngine`, `ReportContent`, `ReportGenerationResult`, protocols |
| `backend/data/reports.py` | **Extended** — `complete_generation(..., content=None)` merges structured content into `generated_content` |
| `backend/engines/__init__.py` | **Extended** — exports `ReportContent`, `ReportGenerationEngine`, `ReportGenerationResult` |
| `backend/tests/unit/engines/test_report_generation.py` | **New** — 33 Phase 9C tests |
| `docs/cline/CarbonTally-Phase9C-ReportGenerationEngine-v1.0.md` | **New** — this report |

No new database table, no migration, no factor import, no dev-DB change. The
development baseline remains DEFRA 7,029 + SEAI 20 = 7,049.

---

## 2. Report structure

The engine produces an ordered, stable section set. Each section is a
JSON-serialisable payload; `ReportContent.render()` yields the domain
`ReportSection[]` (string content) and `ReportContent.to_dict()` the full
dict persisted into `generated_content`.

| order | section_id | content (keys) |
|---|---|---|
| 0 | `metadata` | report_type, reporting_year, template_id, organization_id |
| 1 | `organization` | status, organization_id, name, country, is_active, metadata (sector, fte_count, total_floor_area_sqm, annual_revenue_gbp) |
| 2 | `period` | start_date, end_date, reporting_year |
| 3 | `totals` | status (`available`/`insufficient_data`), total_co2e_kg, **unit (provenance-aware)**, source, total_rows |
| 4 | `scopes` | status, per-scope co2e_kg + unit, source |
| 5 | `activities` | status, top-N activity summaries (activity_type, co2e_kg, quantity, unit, row_count), total_activities |
| 6 | `validation` | status (`passed`/`failed`/`not_configured`), ok, counts, issues[] (code, severity, message, entity_type, entity_id, field, context) |
| 7 | `benchmarking` | status (`available`/`insufficient_data`/`not_configured`), metrics[] (key, label, unit, status, value, numerator, denominator, baseline_value, delta, delta_pct, comparison, source, scope, facility_id, activity_type, note), by_scope |
| 8 | `provenance` | gas_coverage (`CO2`/`CO2e`/`CO2/CO2e mixed`/`unknown`), factor_sources, factor_sets, countries, note |
| 9 | `calculation` | status (`available`/`verified`/`verification_failed`/`insufficient_data`), methodology, algorithm_version, figures_from, unit, snapshot_verification[] |
| 10 | `lineage` | emissions_logs (count, reporting_year), emission_factors (resolved, factor_ids), aggregate (total_rows, by_scope_count), source |
| 11 | `generation` | generated_at, engine, engine_version, template_id |

Template ordering: when `request.options["template"]` (a `ReportTemplate`) or
`request.sections` provides a skeleton, the built sections are re-ordered to
match; template sections with no engine section are omitted (nothing is
fabricated) and engine sections not in the template are appended. Otherwise
the default order above is used.

---

## 3. Engine dependencies

Constructor (protocol-typed, structural typing — fakes satisfy the same
surfaces as the production repositories):

| Parameter | Surface | Production implementation |
|---|---|---|
| `reports_repo` | `ReportsStore` | `ReportsRepository` |
| `org_repo` | `OrgSource` (`get`, `get_metadata`) | `OrganizationsRepository` |
| `logs_repo` | `LogsSource` (`aggregate`, `find_by_org`) | `EmissionsLogsRepository` |
| `factor_lookup` (optional) | `FactorLookup` (`get`) | `EmissionFactorsRepository` |
| `validation_engine` (optional) | `ValidationSurface` (`validate`) | Phase 9A `ValidationEngine` |
| `benchmarking_engine` (optional) | `BenchmarkingSurface` (`benchmark`) | Phase 9B `BenchmarkingEngine` |
| `calculation_engine` (optional) | `CalculationSurface` (`verify`) | Phase 6 `CalculationEngine` |
| `event_bus` (optional) | `EventBus` | `infra.event_bus.EventBus` |
| `audit_logger` (optional) | `AuditLogger` | `infra.audit_logger.AuditLogger` |

Engines are injected — never imported/constructed internally (CT-ARCH-009 /
prep-pack §4.2). The report engine holds **no validation rules** and **no
benchmarking rules**; it renders the outputs of the injected engines.

---

## 4. ValidationEngine integration

- The report engine builds `ValidationRequest(organization_id,
  reporting_year, period, strict)` where `strict` defaults to **True**
  (`request.options["strict_validation"]` overrides).
- `ValidationEngine.validate` is awaited during `build_content`. If strict and
  blocking errors exist, `ValidationFailedError` propagates unchanged out of
  `generate()` — **no `report_generation_queue` row is created** (verified by
  test `test_validation_failures_block_generation` and the real-engine
  regression `test_real_validation_engine_strict_blocking_error`).
- A passing run (clean data or warnings-only) is rendered into the
  `validation` section: status (`passed`/`failed`), `ok`, `counts` by
  severity, and every issue (code, severity, message, entity, field,
  context). Warnings are included in the report and do **not** block
  generation.
- No validation rules are duplicated in the report engine.
- If no validation engine is injected, the section is
  `{"status": "not_configured"}` (explicit, not a fabricated pass).

---

## 5. BenchmarkingEngine integration

- The report engine builds `BenchmarkRequest(organization_id,
  reporting_year, compare_years, metrics, group_by)` with defaults
  `compare_years=()`, `metrics=(total, per_fte, per_area, per_revenue,
  activity_intensity)`, `group_by=(scope,)`; overridable via
  `request.options["compare_years"]` / `["benchmark_metrics"]` /
  `["benchmark_group_by"]`.
- `BenchmarkingEngine.benchmark` is awaited during `build_content`.
- `BenchmarkDataInsufficientError` (empty reporting period) is **caught** and
  rendered as `{"status": "insufficient_data", "detail": …}` — it does **not**
  fail the report (verified by `test_insufficient_benchmark_data_caught` and
  the real-engine empty-period regression).
- Every metric keeps its Phase 9B availability status
  (`available` / `not_available` / `zero_denominator` /
  `invalid_denominator` / `insufficient_data` / `incompatible_unit` /
  `incompatible_period`) with `value=None` when not available — **never** a
  fabricated zero (verified by
  `test_unavailable_benchmark_metric_not_zeroed`).
- If no benchmarking engine is injected, the section is
  `{"status": "not_configured"}`.

---

## 6. CO2/CO2e provenance handling

Mandatory and enforced end-to-end:

1. **Resolution** — the engine resolves every distinct `factor_id` referenced
   by the period's logs via `FactorLookup` and applies the shared
   `domain.factor.gas_coverage()` classifier (SEAI → `CO2`; DEFRA-DESNZ → `CO2e`).
2. **Coverage** — all `CO2` ⇒ `CO2`; all `CO2e` ⇒ `CO2e`; a mix ⇒
   `CO2/CO2e mixed`; none ⇒ `unknown`.
3. **Unit labels** — every emissions figure (totals, scopes, calculation)
   carries `kg CO2` / `kg CO2e` / `kg CO2/CO2e mixed`; SEAI-only results are
   **never** relabelled `kg CO2e`, and mixed results are clearly labelled.
4. **Provenance section** — `gas_coverage`, `factor_sources`
   (`DEFRA-DESNZ`, `SEAI`, …), `factor_sets` (`DEFRA-2025`, `SEAI-2025`, …)
   and `countries`, plus a note explaining that SEAI factors are CO2-only by
   source design and that mixed aggregations are not relabelled.

Verified by `TestProvenance` (SEAI-only, DEFRA-only, mixed, factor
source/set/country) and by the real-engine regressions. No CO2→CO2e
conversion is applied anywhere (no approved methodology exists for it).

---

## 7. Persistence behavior

- **Approved persistence only.** `generate()` calls
  `ReportsRepository.create_generation_request(...)` (pending row) and then
  `ReportsRepository.complete_generation(report_id, storage_url="",
  file_size=len(json), page_count=len(sections), content=content_dict)`.
- The structured content is persisted inside the existing
  `generated_content` JSONB as `{"page_count": …, "content": {…}}` via the
  new optional `content` parameter — backward compatible (callers omitting it
  get the previous page-count-only payload; existing integration tests
  unchanged).
- `storage_url` stays `""` because no renderable artefact exists in Phase 9C
  (Phase 10 rendering writes the artefact and its URL).
- No other repository method is called; `_load_factors`, `aggregate` and
  `find_by_org` are read-only. Verified by
  `test_no_database_side_effects_outside_approved_persistence` and
  `test_repository_persistence`.
- On `ValidationFailedError` no row is created (persistence happens only
  after successful content build).

---

## 8. Events / audit behavior

- **Event** — `ReportGenerated(report_id, organization_id, storage_url)` is
  published to the EventBus (fire-and-forget; a failing publisher is logged
  and does not break generation). Verified by
  `test_eventbus_publishes_report_generated`.
- **Audit** — `AuditLogger.log_action(action="report:generated",
  entity_type="report", entity_id=<report id>, correlation_id=<report id>,
  actor="report_generation_engine", after={report_type, reporting_year,
  sections[], page_count})` (matches the contract table). A failing audit is
  logged and does not break generation. Verified by
  `test_audit_logger_records_generation`.

---

## 9. Test results

Focused Phase 9C suite: `backend/tests/unit/engines/test_report_generation.py`
— **33 tests covering all 26 required scenarios.**

| Requirement | Test(s) |
|---|---|
| 1 basic report generation | `test_basic_report_generation` (+ template ordering) |
| 2 organisation metadata | `test_organization_metadata` |
| 3 reporting period | `test_reporting_period` |
| 4 total emissions | `test_total_emissions` |
| 5 scope summaries | `test_scope_summaries` |
| 6 category/activity summaries | `test_activity_summaries` |
| 7 validation results | `test_validation_results_passed` |
| 8 validation warnings | `test_validation_warnings_included` |
| 9 validation failures | `test_validation_failures_block_generation`, `test_real_validation_engine_strict_blocking_error` |
| 10 benchmark results | `test_benchmark_results_available`, `test_real_benchmarking_engine_composition` |
| 11 unavailable benchmark metrics | `test_unavailable_benchmark_metric_not_zeroed` |
| 12 insufficient benchmark data | `test_insufficient_benchmark_data_caught`, `test_real_engines_empty_period_insufficient` |
| 13 CO2-only SEAI report | `test_seai_co2_only_report` |
| 14 CO2e DEFRA report | `test_defra_co2e_report` |
| 15 mixed SEAI + DEFRA | `test_mixed_seai_and_defra_provenance` |
| 16 factor source/factor set provenance | `test_factor_source_and_factor_set_provenance` |
| 17 calculation snapshot provenance | `test_calculation_snapshot_verification`, `test_calculation_snapshot_tamper_detected` |
| 18 source lineage | `test_source_lineage` |
| 19 empty/insufficient input | `test_empty_input_explicit_insufficient_data` |
| 20 serialization | `test_serialization` |
| 21 repository persistence | `test_repository_persistence` |
| 22 EventBus behaviour | `test_eventbus_publishes_report_generated` |
| 23 AuditLogger behaviour | `test_audit_logger_records_generation` |
| 24 no DB side effects | `test_no_database_side_effects_outside_approved_persistence`, `test_engine_failure_wrapped` |
| 25 Phase 9A regression | `test_real_validation_engine_composition` + full 9A suite re-run |
| 26 Phase 9B regression | `test_real_benchmarking_engine_composition` + full 9B suite re-run |

**Environment limitation:** the tooling shell in this session could not
sustain foreground processes reliably (same class of constraint documented in
Phases 9A/9B), so validation was performed with the approved fallback:

1. **Import/compile sweep** — 31/31 checks PASS
   (`core`, `domain.*`, `data.reports`, `engines.validation`/`benchmarking`/
   `report_generation`/`engines`, plus `py_compile` on all changed/new and
   existing 9A/9B modules).
2. **Standalone runtime self-check** — **33/33 Phase 9C checks PASS, 0
   failures** (the pytest test module loaded directly and every async test
   executed under a single asyncio loop).
3. **9A/9B regression re-run** — **44/44 PASS** (15 ValidationEngine + 29
   BenchmarkingEngine engine tests) — existing tests not weakened.

The pytest files remain the canonical suite (run when the environment
permits):

```bash
cd backend && python -m pytest \
  tests/unit/domain/test_validation.py \
  tests/unit/domain/test_benchmarking.py \
  tests/unit/engines/test_validation.py \
  tests/unit/engines/test_benchmarking.py \
  tests/unit/engines/test_report_generation.py -q
```

---

## 10. Serialization results

- `ReportContent.to_dict()` returns the full structured content keyed by
  section id; every value is JSON-serialisable (`Decimal` → `str`,
  `datetime`/`date` → ISO string; recursion handles nested lists/dicts).
- Round-trip verified: `json.loads(json.dumps(to_dict())) == to_dict()`
  (test 20).
- Each `ReportSection.content` is a compact JSON string
  (`separators=(",", ":")`, `sort_keys=True`) that re-parses to the section
  payload.
- The persisted `generated_content` column receives the same dict under the
  `content` key (test 21) — the structured report survives the
  pending→completed lifecycle for Phase 10/API consumption.

---

## 11. Deviations / interpretations

| # | Item | Detail | Severity |
|---|---|---|---|
| D1 | `ReportGenerationResult` returned | The contract lists `GeneratedReport` as the output; the engine returns a small result object carrying the persisted `GeneratedReport` **plus** the structured `ReportContent` so callers can consume the content without a second fetch. `GeneratedReport` is still persisted via `complete_generation` exactly as contracted. | None (documented superset) |
| D2 | `FactorLookup` dependency added | Provenance (CO2 vs CO2e), factor source/set/country and activity summaries require factor metadata not present on `EmissionLog`; `FactorLookup` (`EmissionFactorsRepository.get`) is consumed as an optional surface — consistent with ValidationEngine and BenchmarkingEngine. | Low (documented) |
| D3 | `ReportsRepository.complete_generation` gained an optional `content` param | The existing repository only ever wrote `{"page_count": …}` into `generated_content`, so the structured content could not be persisted without a repository change. The optional param merges content into the same JSONB, preserving existing behaviour when omitted. | None (minimal, backward compatible) |
| D4 | Section content is JSON strings | `ReportSection.content` is a `str` in the frozen domain; each section carries its structured payload as compact JSON so the content stays serialisable and stable for Phase 10/API. | None |
| D5 | Default `strict_validation=True` | The report engine defaults to strict validation so a falsely "valid" report is never produced; callers can opt out per request. | None (aligns with the contract's error behaviour) |
| D6 | Calculation section figures | Figures come from `EmissionsLogsRepository.aggregate`; snapshot-level verification is performed via the injected `CalculationEngine.verify` only for snapshots supplied through `request.options["snapshots"]` (no snapshot read API exists yet). The section states `figures_from: "emissions_logs_aggregation"` and never invents verification. | Low (documented) |
| D7 | Audit action label `report:generated` | Uses the colon convention of the existing engines (`calculation:completed`, `validation:completed`, `benchmark:completed`) rather than the contract's dot notation. | None |
| D8 | Activity summaries computed in-engine | `EmissionsLogsRepository.aggregate` has no activity grouping dimension, so the top-N activity summary is computed in-engine from `find_by_org` + resolved factors (pure composition over repository reads — no DB logic duplicated). | Low (documented) |

---

## 12. Remaining Phase 9 work

Not implemented in Phase 9C (out of scope per the approved contract):

- **9.4 Integration tests** — `backend/tests/integration/test_report_generation.py`
  (and 9A/9B integration files) against `carbontally_test`: end-to-end
  pending→completed lifecycle, `ReportGenerated` persistence, audit rows, and
  a GB (CO2e) report vs an IE "not applicable/insufficient" report.
- **Phase 10** — HTTP/API routes, FastAPI contracts, PDF/HTML rendering and
  report download endpoints (explicitly out of Phase 9 scope).
- No external benchmark data, no new factor sources, no schema/migration work.

The ReportGenerationEngine is ready for Phase 9D consumption: its
`ReportContent` / section payloads and persisted `generated_content` are the
structured input for the Phase 10 rendering/API layers.

---

**PHASE 9C COMPLETE — READY FOR PHASE 9D**




