# CarbonTally — Phase 9 Readiness Audit v1.0

**Audit type:** READ-ONLY · no code, schema, data or migration changes
**Scope:** Frozen Backend v2.1 Implementation Preparation Pack — Phase 9
(9.1 ValidationEngine · 9.2 BenchmarkingEngine · 9.3 ReportGenerationEngine ·
9.4 Integration tests)
**Reference:** `docs/cline/CarbonTally Backend v2.1 — Implementation Preparation Pack.md`
**Date:** 2026-08-09

---

## 1. Database verification

The audit was asked to verify the current development database state. The
command shell/`psql` was **unavailable in this session** (every command failed
to start), so a live read-only SQL round-trip could not be executed here. The
state below is corroborated by the authoritative import record
(`docs/cline/CarbonTally-SEAI-Development-DB-Import-v1.0.md`) and the verified
SEAI artifacts:

| Check | Expected | Status |
|---|---|---|
| `SELECT count(*) FROM public.emission_factors;` | **7,049** | Corroborated by documented import record |
| `factor_source='DEFRA-DESNZ' AND country='GB'` | **7,029** | Corroborated |
| `factor_source='SEAI' AND country='IE'` | **20** | Corroborated |

Recommended confirmation when the shell is available (read-only):

```sql
SELECT count(*) FROM public.emission_factors;
SELECT factor_source, country, count(*) FROM public.emission_factors
GROUP BY factor_source, country ORDER BY factor_source;
SELECT count(*) FROM public.emission_factors
WHERE factor_source='SEAI' AND factor_set='SEAI-2025' AND country='IE'
  AND import_batch_id IS NOT NULL;  -- expect 20
```

The SEAI/DEFRA factor data does not block Phase 9. Do not re-import or modify it.

---

## 2. Phase 9 engine implementation status

| Task | Spec deliverable (prep pack lines 458–468, 643–648) | Current status |
|---|---|---|
| 9.1 ValidationEngine | `backend/engines/validation.py` | **NOT IMPLEMENTED** — file does not exist |
| 9.2 BenchmarkingEngine | `backend/engines/benchmarking.py` | **NOT IMPLEMENTED** — file does not exist |
| 9.3 ReportGenerationEngine | `backend/engines/report_generation.py` | **NOT IMPLEMENTED** — file does not exist (building blocks exist, see §4/§9) |
| 9.4 Integration tests | Engine + repository integration | **NOT YET** — no `test_validation.py` / `test_benchmarking.py` / `test_report_generation.py` in the test inventory |

`backend/engines/__init__.py` currently exports: `AIExtractionEngine`,
`CalculationEngine`, `DocumentExtractionEngine`, `FactorMatchingEngine`,
`WorkflowOrchestrator`, and the six matching stages. It exports **none** of the
three Phase 9 engines (nor the Phase 5 `ImportMappingEngine`).

This absence is the *expected starting state* for Phase 9 — the three engines
are the phase's own deliverables. It is not, by itself, a readiness blocker.

---

## 3. Existing domain models relevant to Phase 9

| File | Models | Relevant to |
|---|---|---|
| `backend/domain/report.py` | `ReportRequest`, `GeneratedReport`, `ReportSection`, `ReportTemplate` | 9.3 |
| `backend/domain/calculation.py` | `CalculationSnapshot`, `CalculationResult`, `VerificationResult`, `CalculationMethodology`, `EmissionLog`, `EmissionsAggregate` | 9.1/9.2/9.3 |
| `backend/domain/organization.py` | `Organization`, `OrganizationMember`, `Facility`, `Asset`, `OrganizationMetadata` | 9.1/9.2 |
| `backend/domain/workflow.py` | `ValidationFailed`, `ReportGenerated` events + `DomainEvent` hierarchy | 9.1/9.3 |
| `backend/domain/factor.py` | `EmissionFactor` (provider_key via batch) | 9.1 |

**Missing:** no validation-specific domain types (e.g. `ValidationReport` /
`ValidationIssue` for emissions data quality) and no benchmarking domain types.
(Provider-side `ValidationReport` classes exist only under `src/providers/defra`
and `src/providers/seai`, outside the v2.1 backend — they are import validators,
not the Phase 9 emissions-validation engine.)

---

## 4. Existing repositories required by Phase 9

All repositories the three engines need (prep pack §4.1) exist and are
integration-tested:

| Repository | File | Phase 9 engine(s) |
|---|---|---|
| `EmissionsLogsRepository` | `backend/data/emissions_logs.py` (create, save, aggregate, find_by_org_period, save_snapshot) | Validation, Benchmarking, Report |
| `OrganizationsRepository` | `backend/data/organizations.py` (get_by_id, members, facilities, assets, update_metadata) | Validation, Benchmarking, Report |
| `EmissionFactorsRepository` | `backend/data/emission_factors.py` | Validation |
| `ReportsRepository` | `backend/data/reports.py` (create_generation_request, complete_generation, get_by_org, get, save, delete) | Report |
| `AuditRepository` / `EventsRepository` / `FactorAliasesRepository` | `backend/data/audit.py`, `events.py`, `factor_aliases.py` | all (side effects) |

---

## 5. Existing CalculationEngine integration

- `backend/engines/calculation.py` — implemented; `CalculationEngine` injects
  `FactorMatchingEngine` per §4.2 and writes snapshots/logs through a
  `CalculationSink` (production sink = `EmissionsLogsRepository`).
- Unit tests: `backend/tests/unit/engines/test_calculation.py`.
- Integration tests: `backend/tests/integration/test_calculation.py` (correct
  co2e + snapshot persistence, events, audit, content-hash verifiability, unit
  mismatch rejection, existing-log update).
- Cross-provider regression: `src/providers/seai/tests/test_defra_regression.py`
  confirms `CalculationEngine` produces the expected `co2e_kg` with an SEAI
  factor (2.682327 × 100 → 268.2327) — the Phase 9 report engine can rely on it.

**Status: COMPLETE and tested.**

---

## 6. `calculation_snapshots` implementation

- Table: `supabase/migrations/20260807020000_add_calculation_snapshots.sql`
  (includes `import_batch_id` FK → `import_batches`).
- Domain: `CalculationSnapshot` (immutable, `build_content_hash()`,
  `verify_reproducibility()`).
- Persistence: `EmissionsLogsRepository.save_snapshot()` writes the full
  provenance set (activity, activity_type, factor_source, factor_set,
  import_batch_id, calculated_by, request_id).
- Tests: unit + integration (`test_calculation.py`).

**Status: COMPLETE.** Minor deviation noted in §11 (D3).

---

## 7. `emissions_logs` implementation

- Table: `supabase/migrations/00000000000000_init_schema.sql`.
- Domain: `EmissionLog` (frozen, validated quantities).
- Repository: `EmissionsLogsRepository` with scope/month/year/asset/facility
  grouping (`EmissionsAggregate`) — directly reusable by Validation and
  Benchmarking engines.
- Tests: `tests/integration/test_emissions_logs.py`.

**Status: COMPLETE.** Known mapping (documented in the repository):
`emissions_logs` has no `facility_id` column, so `facility_id` round-trips via
the `metadata` JSONB column (D5).

---

## 8. `organizations` / `facilities` / `assets` implementation

- Tables exist (init schema + RC2, incl. `eircode` on facilities).
- Domain: `Organization`, `OrganizationMember`, `Facility`, `Asset`,
  `OrganizationMetadata` (floor area, FTE, revenue, sector — the intensity
  denominators benchmarking/reporting need).
- Repository: `OrganizationsRepository` (org + members + facilities + assets +
  metadata).
- Tests: `tests/integration/test_organizations.py`, unit `test_organization.py`.

**Status: COMPLETE.** Minor: `Facility` domain model does not carry `eircode`
(D8).

---

## 9. Report-related database structures

| Table | Exists | Used by |
|---|---|---|
| `report_templates` | Yes (init schema) | 9.3 |
| `report_generation_queue` | Yes (init schema; status, progress, AI-cost, final_report_url/bytes, generated_content JSONB) | 9.3 (`ReportsRepository`) |
| `report_versions` | Yes (init schema; UNIQUE(report_id, version_number)) | 9.3 (optional) |
| `report_comments` | Yes (init schema) | 9.3 (optional) |

**Status: COMPLETE.** Note: the RC2 schema has no dedicated `generated_reports`
table; `ReportsRepository` maps `GeneratedReport` onto `report_generation_queue`
(storing `page_count` inside `generated_content` JSONB) — documented in the
repository docstring (D4). A legacy PDF generator exists at
`backend/report_generator.py` (`EnhancedSustainabilityReportGenerator`, FPDF)
with routes in `backend/routes/reports.py` — legacy backend, not the v2.1
engine, but reusable as an artefact renderer (optional, §15).

---

## 10. Existing tests relevant to Phase 9

| Test file | Covers |
|---|---|
| `tests/integration/test_reports.py` | `ReportsRepository` request/complete/get/delete |
| `tests/integration/test_calculation.py` | snapshots, hash, events, audit |
| `tests/integration/test_emissions_logs.py` | aggregation/grouping by scope |
| `tests/integration/test_organizations.py` | org + metadata |
| `tests/integration/test_emission_factors.py`, `test_imports.py`, `test_event_bus.py`, `test_audit.py` | foundation used by the engines |
| `tests/unit/domain/test_report.py`, `test_workflow.py`, `test_organization.py` | domain contracts (incl. `ValidationFailed`/`ReportGenerated` events) |
| `tests/unit/engines/test_calculation.py` | engine unit behaviour |

Integration conftest targets the isolated `carbontally_test` DB and truncates
only tables-under-test (never the authoritative DB) — the Phase 9.4 suite must
use the same isolation.

**Missing (Phase 9.4 deliverable):** engine-level integration tests for the
three new engines, and a benchmark-data test dataset (none exists in the
schema, see D6/D7).

---

## 11. Deviations and spec gaps (file · class · behaviour · spec · severity · action)

| # | File / class | Current behaviour | Frozen spec requirement | Severity | Recommended action |
|---|---|---|---|---|---|
| D1 | `backend/providers/` (missing) | No v2.1 provider plugin architecture (`providers/base.py`, `registry.py`, `defra/plugin.py`, `seai/plugin.py`). DEFRA/SEAI imports are standalone CLI importers under repo-root `src/commands/` + `src/providers/` writing via psycopg2. | Prep pack §5 package structure + Phase 5.1/5.2 | HIGH (Phase 5 deviation; **not** a Phase 9 blocker) | Record as pre-existing deviation; decide whether Phase 9 engines read factors via `EmissionFactorsRepository` (current path) vs plugin layer |
| D2 | `backend/engines/import_mapping.py` (missing) | No `ImportMappingEngine`; imports bypass v2.1 `ImportsRepository`/event bus | Phase 5.3 deliverable | HIGH (Phase 5 deviation; not a Phase 9 blocker) | Track separately from Phase 9; do not expand Phase 9 scope |
| D3 | `domain/calculation.py` `CalculationSnapshot` | Domain carries `match_request_id`/`created_at`; provenance fields (`activity`, `activity_type`, `factor_source`, `factor_set`, `import_batch_id`, `calculated_by`, `request_id`) are passed to `save_snapshot()`, not on the domain object | Prep pack §2.2 inventory lists those fields on the snapshot | LOW | Accept (DB coverage complete); align docstring/inventory when touching Phase 9 |
| D4 | `data/reports.py` `ReportsRepository` | Maps `GeneratedReport` to `report_generation_queue`; `page_count` in `generated_content` JSONB | Prep pack §3.8 report repository over a report table | LOW (documented) | Keep; consider a `generated_reports` migration only if Phase 10 needs it |
| D5 | `data/emissions_logs.py` | `facility_id` round-trips through `metadata` JSONB (no column) | Repo spec implies facility dimension | LOW (documented) | Keep for Phase 9; benchmarking by facility works via metadata->>'facility_id' |
| D6 | Prep-pack Phase 9 vs `CarbonTally_Backend_V2_Final_Implementation_Instructions.md` CT-ARCH-003 | Prep pack schedules 9.2 BenchmarkingEngine; FINAL Instructions list `BenchmarkEngine` under **Future** | Two frozen documents disagree on benchmarking timing | MEDIUM | Confirm 9.2 is in scope before implementing; prep pack (dated later, "single source of truth") suggests yes |
| D7 | No benchmark reference data | No benchmark/industry-reference tables, domain models, or datasets exist anywhere in the schema | 9.2 needs peer/intensity comparisons (prep pack engine deps: logs_repo + org_repo + audit_logger only — no reference repo) | MEDIUM | Define the benchmarking data source (static reference table vs computed peer aggregates) as a design decision for 9.2 |
| D8 | `domain/organization.py` `Facility` | No `eircode` field (RC2 table has it) | RC2 facility schema | LOW | Add field if IE facility reporting is needed in Phase 9 reports |

---

## 12. Missing dependencies from Phases 1–8 (impact on Phase 9)

- **Phase 5** — v2.1 provider plugin architecture and `ImportMappingEngine`
  (D1/D2): not implemented under `backend/`. **Not a Phase 9 prerequisite**
  (Phase 9 depends on Phase 6 only). SEAI/DEFRA data is already in the DB.
- **Phase 3 infra** — `event_bus.py`, `search_index.py`, `audit_logger.py`,
  `supabase.py`, `config.py`, `llm_client.py` all present and tested.
  `infra/cache.py` (spec structure) not required by Phase 9.
- **Phase 10 `api/` layer** — intentionally absent (Phase 10 scope).
- **Phase 12 providers (epa/ademe/ipcc/custom)** — intentionally absent.

**Conclusion: no Phase 1–8 dependency required by Phase 9 is missing.**

---

## 13. Can Phase 9 begin immediately?

**Yes.** Every Phase 9 dependency is satisfied:
- Phase 6 CalculationEngine + snapshot/verification — complete and tested.
- All repositories, infra singletons (event bus, audit logger, search index)
  and DB tables the three engines need — present.
- Report/emissions/organization data surfaces — present.

What does not yet exist is precisely the Phase 9 scope itself (three engines +
their integration tests). That is the work to be done, not a blocker.

---

## 14. Blockers that MUST be resolved before implementation

None are hard blockers to starting 9.1/9.3. Before or during implementation,
resolve:

1. **9.2 BenchmarkingEngine scope (D6/D7).** Confirm benchmarking is in Phase 9
   (prep pack) vs Future (CT-ARCH-003), and define the reference data source —
   no benchmark tables exist. This is the only item that could turn into a
   mid-phase blocker if left undefined.
2. **Live DB re-verification.** Re-run the §1 read-only queries when the shell
   is available to reconfirm 7,049/7,029/20 before Phase 9.4 integration runs.

---

## 15. Optional improvements (NOT blockers)

- Reuse the legacy `EnhancedSustainabilityReportGenerator`
  (`backend/report_generator.py`) as the 9.3 PDF renderer behind the v2.1
  `ReportGenerationEngine`.
- Add v2.1 validation domain types (`ValidationReport`/`ValidationIssue`) and
  benchmark domain types as part of Phase 9, mirroring the report domain style.
- Add a benchmark reference table + seed dataset design for 9.2.
- Register Phase 9 engines in `backend/engines/__init__.py` exports.
- Re-run the full integration suite once the environment permits (Phase 9.4
  will add the new engine tests on top of the existing isolation).

---

## 16. Final status

PHASE 9 READY WITH CONDITIONS


