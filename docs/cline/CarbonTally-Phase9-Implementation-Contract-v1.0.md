# CarbonTally — Phase 9 Implementation Contract v1.0

**Type:** DESIGN/ARCHITECTURE RESOLUTION · read-only · no code/schema/data/migration changes
**Resolves:** Phase 9 Readiness Audit conditions (ValidationEngine scope, BenchmarkingEngine scope, benchmark reference data)
**Scope:** 9.1 ValidationEngine · 9.2 BenchmarkingEngine · 9.3 ReportGenerationEngine · 9.4 Integration tests
**References:**
- `docs/cline/CarbonTally Backend v2.1 — Implementation Preparation Pack.md` (FROZEN, 2026-08-06 — **single source of truth**)
- `docs/cline/CarbonTally_Backend_V2_Final_Implementation_Instructions.md` (CT-ARCH-001…016)
- `docs/cline/CarbonTally-Phase9-Readiness-Audit-v1.0.md`
- Current repository code (`backend/domain`, `backend/data`, `backend/engines`, `backend/infra`)

**Precedence:** where the two frozen documents disagree (D6), the Implementation Preparation Pack — dated later and self-declared "FROZEN — Single Source of Truth for Implementation" — governs. CT-ARCH-003 is treated as the earlier engine catalogue and is reconciled in Part B.

---

## PART A — ValidationEngine scope (9.1)

**Definition.** `ValidationEngine` (`backend/engines/validation.py`) is the
emissions data-quality and calculation-integrity engine. Per the frozen
architecture (prep pack §4.1) it depends on `EmissionsLogsRepository`,
`OrganizationsRepository`, `EmissionFactorsRepository` and `AuditLogger`; it
also publishes the existing `ValidationFailed` domain event (domain/workflow.py,
§14 event platform), so `EventBus` is an additional wiring dependency.

Every validation capability below is justified by the frozen spec or the
already-shipped domain/repository contracts. None invents new requirements.

| # | Capability | Requirement/source | Input | Validation rule | Output/result | Severity | Phase 9 | Future |
|---|---|---|---|---|---|---|---|---|
| A1 | Input/activity validation | CT-ARCH-005 (standardised activity object); `MatchRequest`/`CalculationRequest` `__post_init__` invariants | activity, quantity, unit, country, reporting_year, scope | activity non-empty; quantity ≥ 0; year ∈ 1990–2100; unit present when factor requires it | issue(s) | error (blocking) | ✅ | |
| A2 | Calculation validation (reproducibility) | §13 Calculation Platform; Phase 6 completion criteria; `CalculationSnapshot.verify_reproducibility()` / `build_content_hash()` | `CalculationSnapshot` + factor + quantity | recompute quantity×multiplier == stored `co2e_kg`; `content_hash` == `build_content_hash()` | pass/mismatch; tampered flag | error (blocking); warning on rounding tolerance | ✅ | |
| A3 | Factor/match validation | §11 matching platform; CT-ARCH-006/014 (no silent guessing, explainability) | `MatchResult` + originating `MatchRequest` | status=matched → factor present; factor active; `factor.country == request.country`; `preferred_provider` respected; factor unit == request unit | issues (wrong country/provider = error; low confidence / no_match = warning) | error / warning | ✅ | |
| A4 | Scope/unit consistency | RC2 natural key (unit/scope are factor identity); `CalculationEngine.UnitMismatchError` contract | log/factor pair | `log.unit == factor.unit` (exact string); scope present and consistent with factor (fuels → Scope 1, electricity → Scope 2); scope in known set | issues | error | ✅ | |
| A5 | Snapshot validation | §13; ADR-5 (append-only, immutable) | stored snapshot row | content_hash valid; provenance populated when factor is batch-linked (SEAI: factor_source/factor_set/import_batch_id); snapshot never updated | issues | error on hash mismatch; warning on missing optional provenance | ✅ | |
| A6 | Data integrity | RC2 CHECKs (quantity ≥ 0, co2e_kg ≥ 0); repository invariants | emissions_logs rows, factors, snapshots | non-negative; factor_id resolves; snapshot_id resolves when set; no orphaned child rows | issues | error | ✅ | |
| A7 | Reporting-period validation | `CalculationRequest` carries date + reporting_year | date, reporting_year, period | date.year == reporting_year; date inside requested period; start/end consistency (repo stores start_date=end_date) | issues | warning (year mismatch); error (out-of-period in strict mode) | ✅ | |
| A8 | Organization/facility validation | `OrganizationsRepository` + `OrganizationMetadata` contracts | org, facilities, assets, metadata | org is_active; entity belongs to org; metadata present when intensity metrics are requested | issues | error (inactive); warning (missing metadata) | ✅ | |
| A9 | Verification / audit-time check | §13 verification; Phase 6 admin verify endpoint (R21) | batch of snapshots | run A2+A5 across the set; produce aggregate pass/fail | `VerificationResult`-style report | error | ✅ | |
| A10 | Statistical anomaly detection | not in frozen spec (proposed) | historical log series | spike vs historical distribution | anomaly warnings | warning | | ✅ |
| A11 | Source-document completeness validation | Phase 7/8 domain | documents + extracted fields | every reported line traces to a reviewed document | issues | warning | | ✅ |
| A12 | AI-extraction confidence gating | Phase 7/10 | AI fields + confidence | low-confidence routing | warnings | warning | | ✅ |
| A13 | Provider import-file validation | Phase 5 | DEFRA/SEAI workbook rows | (already implemented in `src/providers/*/validator.py`) | — | — | ❌ (not Phase 9) | — |

**Non-goals (9.1):** import-file validation (Phase 5, exists), AI confidence
gating (Phase 7/10), statistical anomaly thresholds (future), cross-org checks.

---

## PART B — BenchmarkingEngine scope (9.2)

**Determination.** In the frozen architecture "benchmarking" is **internal
benchmarking computed from an organisation's own data** — there is no external
reference dataset, no benchmark repository and no benchmark table anywhere in
the prep pack (the §4.1 engine deps are `logs_repo` + `org_repo` +
`audit_logger` only). `BenchmarkingEngine` therefore computes comparisons from
the already-shipped capabilities:

- `EmissionsLogsRepository.aggregate(org_id, period, group_by)` with
  `group_by ∈ {scope, month, year, asset, facility}` and `by_scope`
  breakdowns (§3.3 of the prep pack);
- `OrganizationsRepository` metadata: `total_floor_area_sqm`,
  `occupied_floor_area_sqm`, `average_employees`, `annual_revenue`,
  `industry_sector` — the intensity denominators.

**Reconciliation with CT-ARCH-003 (D6).** CT-ARCH-003 lists `BenchmarkEngine`
under *Future*, while the prep pack schedules 9.2 in Phase 9. Under the
precedence rule (Part 0) **9.2 is in Phase 9**, but the *content* of Phase 9
benchmarking is scoped to what both documents can support today: internal,
self-referential benchmarks. External "BenchmarkEngine" features (peer/sector
comparison) remain future. This is the recommended reading; it is the one
item requiring human confirmation (Part G, decision 1).

| Capability | Supported in Phase 9? | Data source | Notes |
|---|---|---|---|
| B1 Internal historical (YoY) benchmarking | ✅ | `aggregate(group_by='year')` | total + per-scope deltas vs prior year(s) |
| B2 Facility benchmarking | ✅ | `aggregate(group_by='facility')` via `metadata->>'facility_id'` | facility-vs-facility within the org (same tenant, RLS-safe) |
| B3 Scope benchmarking | ✅ | `by_scope` + `count_by_scope` | scope distribution and YoY per scope |
| B4 Emissions per FTE | ✅ | total / `organization_metadata.average_employees` | warning when metadata absent |
| B5 Emissions per floor area | ✅ | total / `total_floor_area_sqm` | warning when metadata absent |
| B6 Emissions per revenue | ✅ | total / `annual_revenue` | warning when metadata absent |
| B7 Activity intensity benchmarking | ✅ | logs + factor data (e.g. kg CO2e per kWh electricity) | YoY activity-intensity comparison |
| B8 Month / asset granularity | ✅ (optional) | `aggregate(group_by='month'/'asset')` | useful for operational reports |
| B9 Organisation-vs-organisation | ❌ future | none | RLS forbids cross-tenant reads; requires service-role + explicit consent — outside the frozen tenant model |
| B10 Sector benchmarking (vs "UK average") | ❌ future | needs curated reference data (Part C) | no data exists today |
| B11 Supplier benchmarking | ❌ future | no supplier-emissions schema support | feature-list item only |
| B12 AI insights / forecasting / target tracking | ❌ future | — | no spec basis |

---

## PART C — Benchmark reference data

**Decision: NO external benchmark reference dataset is required for the
Phase 9 MVP.** `BenchmarkingEngine` is useful without one because every Phase 9
metric (B1–B8) is derived from the organisation's own `emissions_logs` and
`organization_metadata` — YoY deltas, facility comparisons, scope breakdowns,
intensity ratios and activity intensity are all self-referential.

This is not a convenience decision; it is what the frozen architecture
prescribes. The prep pack gives BenchmarkingEngine **no benchmark-reference
repository** (only `logs_repo`, `org_repo`, `audit_logger`), and the schema
contains no benchmark table. Adding a table "because one seems useful" would be
an unjustified schema change — explicitly excluded by this task.

**If external sector benchmarking is later required (useful later, NOT Phase 9):**

1. **Data required:** curated sector-level intensity statistics (e.g. "tCO2e
   per FTE, UK technology sector, 2025") with provenance.
2. **Minimum fields (future table `benchmark_reference`):** `id`, `sector`,
   `country`, `reporting_year`, `metric` (e.g. `tco2e_per_fte`), `unit`,
   `value`, `source_label`, `source_url`, `as_of_date`, `created_at`.
3. **Storage:** a new small reference table (not emission_factors, not
   organization_metadata — it is neither a factor nor tenant data). Must be
   clearly separated from tenant tables for RLS hygiene.
4. **First data source:** **manually curated public reference data** (published
   sector statistics with licence/attribution). Internal CarbonTally customer
   data must **not** be used for cross-tenant benchmarks without explicit
   opt-in and a service-role aggregation path — out of the frozen tenant model.
5. **Source required before production use:** a licensed, published sector
   intensity dataset (e.g. UK DESNZ/ONS or equivalent IE data) with version +
   as-of date, plus a curation/review process.
6. **Triage:** *Required for Phase 9 MVP* — none. *Useful later* — the
   `benchmark_reference` table + sector comparison. *Out of scope* —
   third-party customer comparisons, real-time peer networks.

---

## PART D — ReportGenerationEngine boundary (9.3)

**Consumption contract** (constructor injection per §4.2):

| Dependency | Consumption | Purpose |
|---|---|---|
| `CalculationEngine` | injected (spec §4.2) | `verify()` every reported figure (reproducibility); recompute where a snapshot is missing |
| `ValidationEngine` | injected (Phase 9 composition) | run A1–A9 over the report period; embed a validation section; block generation on blocking errors when the report requires clean data |
| `BenchmarkingEngine` | injected (Phase 9 composition) | produce the benchmarking section (B1–B8 content) |
| `ReportsRepository` | injected (spec §4.1) | `create_generation_request` → persist sections → `complete_generation(storage_url, file_size, page_count)` |
| `OrganizationsRepository` | injected (spec §4.1) | org identity (name, country, sector), metadata (intensity denominators), report-type applicability (SECR = GB orgs; IE → "not applicable in beta" guidance per product inventory) |
| `EmissionsLogsRepository` | injected (spec §4.1) | source aggregates + per-figure provenance (factor_source/factor_set/import_batch_id via snapshots) |
| `EventBus` + `AuditLogger` | injected (spec §4.1) | publish `ReportGenerated` (report_id, organization_id, storage_url); audit `report.generated` |

**Phase 9 (in scope):** engine assembles ordered `ReportSection[]` from a
`ReportTemplate`, computes figures from log aggregates verified through
`CalculationEngine`, embeds validation + benchmarking sections, persists the
`GeneratedReport` via `ReportsRepository`, publishes `ReportGenerated`, audits,
and returns the `GeneratedReport`.

**Phase 10 (out of scope):** HTTP routes (`POST /generate-report`),
`api/contracts.py`, middleware, PDF rendering service wiring (the legacy
`EnhancedSustainabilityReportGenerator` is a Phase 10 renderer option),
`report_versions` / `report_comments` workflows, admin report endpoints,
report download/export.

**Non-goals (9.3):** PDF rendering is *not* required for the Phase 9 engine —
structured content is persisted in `report_generation_queue.generated_content`
and `storage_url` may be empty. No versioning, no comments, no API.

---

## PART E — SEAI / multi-country implications

The DB now holds DEFRA-DESNZ/GB (7,029) and SEAI/IE (20) factors. **No schema
change is required**; the impact is logic and labelling:

| Dimension | Impact on Phase 9 engines |
|---|---|
| `country` | ValidationEngine A3 must assert `factor.country == request.country` (GB vs IE). No engine may assume GB/DEFRA. |
| `provider` | provider_key is derived via `import_batches` (SEAI rows carry it). Validation/reporting must read provider through `EmissionFactorsRepository` (which joins the batch) — never hard-code DEFRA. |
| `reporting_year` | 2025 factors exist for both countries; A7 year/date consistency applies equally. |
| `scope` | SEAI fuels = Scope 1, SEAI electricity = Scope 2 (matches DEFRA semantics) — A4 rules are country-agnostic. |
| `unit` | SEAI uses the same canonical units as DEFRA (`litres`, `kg`, `cubic metres`, `kWh`) — no new unit handling. |
| **CO2 vs CO2e provenance** | **Key requirement.** SEAI factors are **CO2-only** (CH₄/N₂O excluded by source design); DEFRA factors are CO2e. Both are stored in `co2e_multiplier`. Phase 9 rules: (1) ValidationEngine must **not** treat SEAI CO2-only as a defect — `factor_source`/`factor_set` are provenance, not errors; (2) ReportGenerationEngine must render per-figure provenance (factor_source, factor_set, country, reporting_year, unit, scope) and label SEAI figures **"kg CO2"** (not "kg CO2e") — per the SEAI implementation report §1 note and CT-ARCH-014 explainability; (3) BenchmarkingEngine aggregates totals without mixing provenance in a single labelled figure. |
| `factor_source` / `factor_set` | Must flow from snapshots (`factor_source`, `factor_set`, `import_batch_id` already on `calculation_snapshots`) into report sections. |

**Test consideration.** The verified state (DEFRA 7,029 + SEAI 20) is used as a
multi-country fixture: matching already covers GB-vs-IE diesel (SEAI regression
suite); Phase 9 tests must add validation/report fixtures that include one IE
row to prove country/provider/provenance handling without modifying either
factor set.

---

## PART F — Phase 9 implementation contract

### 9.1 ValidationEngine

| Item | Contract |
|---|---|
| **File** | `backend/engines/validation.py` (+ export in `backend/engines/__init__.py`) |
| **Domain objects (new)** | `backend/domain/validation.py`: `ValidationSeverity` (StrEnum: `error`/`warning`/`suggestion`), `ValidationIssue` (code, severity, message, entity_type, entity_id, field, context: dict), `ValidationReport` (issues: tuple, `ok` property = no errors, counts by severity, blocking_errors), `ValidationRequest` (organization_id, reporting_year, period: DateRange, scope_filter, entity_ids, strict: bool) |
| **Repository dependencies** | `EmissionsLogsRepository`, `OrganizationsRepository`, `EmissionFactorsRepository` |
| **Infrastructure dependencies** | `AuditLogger`, `EventBus` (publish `ValidationFailed`) |
| **Inputs** | `ValidationRequest`, or targeted methods: `validate_logs(org, period)`, `validate_snapshot(snapshot, factor)`, `validate_match(request, result)`, `validate_org(org_id, year)`, `verify_snapshots(snapshots)` |
| **Outputs** | `ValidationReport` (issues + ok + counts) |
| **Error behaviour** | Warnings never raise. `ValidationFailedError` (422) raised only when `strict=True` and blocking errors exist. Internal failures raise `CarbonTallyError` subclasses. |
| **Audit** | `audit` decorator on public methods: action `validation.completed`, entity_type `organization`, entity_id org id, after = issue counts |
| **Events** | `ValidationFailed` (entity_type, entity_id, errors) when strict mode blocks |
| **Database requirements** | none (reads only) |
| **Tests required** | Unit: one test per capability A1–A9 (fake repos). Integration: seed org/logs/factor/snapshot rows in `carbontally_test`, assert report content and strict raise. Multi-country: one SEAI/IE fixture row must validate clean (A3/A4/E-provenance). |
| **Non-goals** | import-file validation (Phase 5), AI confidence (Phase 7/10), statistical anomaly (future), cross-org checks |

### 9.2 BenchmarkingEngine

| Item | Contract |
|---|---|
| **File** | `backend/engines/benchmarking.py` (+ export in `backend/engines/__init__.py`) |
| **Domain objects (new)** | `backend/domain/benchmarking.py`: `BenchmarkRequest` (organization_id, reporting_year, compare_years: tuple, group_by: tuple (year/facility/scope/month/asset), metrics: tuple (`total`, `per_fte`, `per_area`, `per_revenue`, `activity_intensity`), facility_filter), `BenchmarkMetric` (key, label, unit, value: Decimal, baseline_value, delta_pct, comparison: str, source: str), `BenchmarkResult` (organization_id, reporting_year, metrics: tuple, by_scope: dict, by_group: dict, generated_at) |
| **Repository dependencies** | `EmissionsLogsRepository` (`aggregate`, `count_by_scope`), `OrganizationsRepository` (metadata + facilities) |
| **Infrastructure dependencies** | `AuditLogger` |
| **Inputs** | `BenchmarkRequest` |
| **Outputs** | `BenchmarkResult` |
| **Error behaviour** | `BenchmarkDataInsufficientError` (404) when no logs in the period, or when a requested intensity metric has missing metadata (details identify the metric). Never fabricates a value. |
| **Audit** | action `benchmark.completed`, entity_type `organization`, after = metric keys + counts |
| **Events** | none in Phase 9 (no `BenchmarkCompleted` in the frozen event set; do not invent one) |
| **Database requirements** | none (reads existing `emissions_logs` / `organization_metadata` only) |
| **Tests required** | Unit: aggregate arithmetic, YoY deltas, facility grouping, intensity denominators (fake logs/metadata). Integration: real seeded logs; assert B1–B8 outputs; assert 404 on insufficient data. |
| **Non-goals** | external/peer/sector benchmarks, cross-org comparison, forecasting, AI insights, supplier benchmarking (all future) |

### 9.3 ReportGenerationEngine

| Item | Contract |
|---|---|
| **File** | `backend/engines/report_generation.py` (+ export in `backend/engines/__init__.py`) |
| **Domain objects** | reuse existing `domain/report.py` (`ReportRequest`, `GeneratedReport`, `ReportSection`, `ReportTemplate`). Internal section builders only — no new public domain types required |
| **Repository dependencies** | `ReportsRepository`, `OrganizationsRepository`, `EmissionsLogsRepository` |
| **Infrastructure dependencies** | `AuditLogger`, `EventBus` (publish `ReportGenerated`) |
| **Engine dependencies (injected, §4.2)** | `CalculationEngine` (verify figures), `ValidationEngine` (validation section), `BenchmarkingEngine` (benchmarking section) |
| **Inputs** | `ReportRequest` (organization_id, report_type, reporting_year, template_id, options) |
| **Outputs** | `GeneratedReport` persisted via `ReportsRepository.complete_generation`; `ReportGenerated` event |
| **Error behaviour** | `ReportGenerationFailedError` (500) on engine failure; propagates `ValidationFailedError` when strict validation is configured and blocking errors exist; `BenchmarkDataInsufficientError` is caught and rendered as an "insufficient data" section warning — it must not fail the whole report |
| **Audit** | action `report.generated`, entity_type `report`, entity_id report id, after = {report_type, reporting_year, sections, page_count} |
| **Events** | `ReportGenerated` (report_id, organization_id, storage_url) |
| **Database requirements** | none new — persists to existing `report_generation_queue`; reads `organizations`, `organization_metadata`, `emissions_logs`, `calculation_snapshots`, `emission_factors` |
| **Tests required** | Unit: template ordering, section assembly, figure computation, provenance labelling, validation/benchmark section embedding (fake repos + fake sub-engines). Integration: end-to-end generation in `carbontally_test`; assert pending→completed lifecycle, `ReportGenerated` persisted, audit row, and a GB report vs an IE "not applicable" report. |
| **Non-goals** | HTTP routes / contracts / middleware (Phase 10), PDF rendering (Phase 10), report versioning + comments (Phase 10), admin endpoints (Phase 10) |

### 9.4 Integration tests

- New files under `backend/tests/integration/`: `test_validation.py`,
  `test_benchmarking.py`, `test_report_generation.py` (reuse the existing
  `conftest.py` isolation: `carbontally_test`, truncate tables-under-test,
  service-role placeholders).
- Add fixtures: org + metadata + facilities + assets + emission_factors +
  emissions_logs + calculation_snapshots (helpers already exist: `make_org`,
  `make_user`, `make_snapshot`).
- Multi-country coverage: include one SEAI/IE factor + log fixture alongside
  GB rows to prove A3/A4/provenance handling and GB-vs-IE report applicability.
- Register the three engines in `backend/engines/__init__.py` so imports and
  DI are verified by the suite.

---

## PART G — Decision gate

### 1. FINAL VALIDATIONENGINE SCOPE
Emissions data-quality and calculation-integrity validation for an organisation
over a period (capabilities A1–A9), with an error/warning/suggestion severity
model, `ValidationReport` output, strict-mode `ValidationFailedError`,
`ValidationFailed` event, and audit logging. No schema change. Statistical
anomaly and AI-confidence rules are future scope.

### 2. FINAL BENCHMARKINGENGINE SCOPE
**Internal-only benchmarking** (B1–B8): YoY historical, facility-vs-facility,
scope breakdowns, emissions-per-FTE / per-area / per-revenue, and activity
intensity — all computed from existing `emissions_logs` aggregation and
`organization_metadata`. Organisation-vs-organisation, sector, supplier,
forecasting and AI-insight benchmarks are explicitly future scope.

### 3. BENCHMARK DATA DECISION
**No external benchmark reference dataset and no benchmark table in Phase 9.**
The engine is useful with internal data alone, and the frozen architecture
provides no benchmark-reference repository. Future option (if the product wants
sector comparison): a curated `benchmark_reference` reference table fed by
manually curated public sector-intensity statistics — never raw customer data.

### 4. FINAL REPORTGENERATIONENGINE SCOPE
Engine that composes ordered `ReportSection[]` from a template, computes and
**verifies** figures via `CalculationEngine`, embeds Validation (9.1) and
Benchmarking (9.2) sections, persists via `ReportsRepository`, publishes
`ReportGenerated`, and audits. Structured content only. HTTP, PDF rendering,
versioning/comments and admin endpoints are Phase 10.

### 5. REQUIRED DATABASE CHANGES
**NONE.** All data surfaces exist (`emissions_logs`, `calculation_snapshots`,
`organizations`, `organization_metadata`, `emission_factors`,
`report_generation_queue`). No migration, no new tables, no new columns.

### 6. REQUIRED DOMAIN CHANGES
- **Add** `backend/domain/validation.py` (ValidationSeverity, ValidationIssue,
  ValidationReport, ValidationRequest).
- **Add** `backend/domain/benchmarking.py` (BenchmarkRequest, BenchmarkMetric,
  BenchmarkResult).
- Reuse existing `domain/report.py`, `domain/calculation.py`,
  `domain/organization.py`, `domain/workflow.py` unchanged.

### 7. REQUIRED REPOSITORY CHANGES
- **None strictly required.** `EmissionsLogsRepository.aggregate` already
  supports scope/month/year/asset/facility grouping and by_scope breakdowns.
- Optional (verify during 9.2): a `OrganizationsRepository.get_metadata(org_id)`
  read accessor if the current implementation lacks a standalone metadata
  getter (only `update_metadata` was confirmed in the audit).

### 8. REQUIRED INFRASTRUCTURE CHANGES
**NONE.** EventBus, AuditLogger, search index, config and supabase pool all
exist. No new singletons required.

### 9. TEST PLAN
1. Unit — `backend/tests/unit/domain/test_validation.py`,
   `test_benchmarking.py`; `backend/tests/unit/engines/test_validation.py`,
   `test_benchmarking.py`, `test_report_generation.py`.
2. Integration — `test_validation.py`, `test_benchmarking.py`,
   `test_report_generation.py` under `backend/tests/integration/` against
   `carbontally_test` with the existing conftest isolation.
3. Regression — keep the existing integration suite green (calculation,
   matching, reports repository, SEAI/DEFRA multi-country matching).
4. Multi-country fixture (GB + one SEAI/IE row) in each engine suite.

### 10. PHASE 9 IMPLEMENTATION ORDER
1. `domain/validation.py` → `engines/validation.py` → unit tests → integration tests.
2. `domain/benchmarking.py` → `engines/benchmarking.py` → unit tests → integration tests.
3. `engines/report_generation.py` (wiring Calculation + Validation + Benchmarking + ReportsRepository) → unit tests → integration tests.
4. Phase 9.4 integration suite pass + `engines/__init__.py` exports + mypy/compile checks.
5. Full integration regression run (once the environment permits).

---

## FINAL STATUS

PHASE 9 DESIGN REQUIRES HUMAN DECISION

**Exact decisions requested (human sign-off):**

- Confirm **9.2 BenchmarkingEngine is in Phase 9** despite CT-ARCH-003 listing "BenchmarkEngine" under Future (recommended: yes — the later prep pack is the single source of truth).
- Confirm Phase 9 benchmarking is **internal-only** (YoY, facility, scope, intensity per FTE/area/revenue, activity intensity) with no external/peer/sector comparison (recommended: approve).
- Confirm **no benchmark reference table/data and no schema change** in Phase 9 (recommended: approve).
- Confirm ReportGenerationEngine **composes Validation + Benchmarking sections and persists structured content only**, with HTTP/PDF/versioning deferred to Phase 10 (recommended: approve).
- Confirm the **CO2-vs-CO2e labelling requirement** (SEAI figures labelled "kg CO2"; ValidationEngine treats SEAI CO2-only factors as valid) is a Phase 9 deliverable (recommended: approve).





