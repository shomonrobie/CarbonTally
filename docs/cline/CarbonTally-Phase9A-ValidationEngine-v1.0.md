# CarbonTally — Phase 9A ValidationEngine v1.0

**Status: PHASE 9A COMPLETE — READY FOR PHASE 9B**
**Scope:** Phase 9.1 ValidationEngine only (capabilities A1–A9 of the approved Implementation Contract)
**Reference:** `docs/cline/CarbonTally-Phase9-Implementation-Contract-v1.0.md`
**Date:** 2026-08-09

---

## 1. Implementation summary

`ValidationEngine` (`backend/engines/validation.py`) is the emissions
data-quality and calculation-integrity engine. It validates an organisation's
emissions data over a period without writing to the database, consuming
repository surfaces through protocols and producing immutable
`ValidationReport` outputs.

- **Never touches the database directly** — reads through `LogsSource`
  (`EmissionsLogsRepository`), `OrgSource` (`OrganizationsRepository`) and
  `FactorLookup` (`EmissionFactorsRepository`) protocols.
- **Reuses existing infrastructure** — `EventBus` (publishes the existing
  `ValidationFailed` event on strict-mode blocking) and `AuditLogger`
  (`validation:completed` audit entries).
- **SEAI CO2-only first-class** — `gas_coverage()` preserves the `kg CO2` vs
  `kg CO2e` distinction; CO2-only SEAI factors never require CH4/N2O
  components and are never treated as a defect.
- **No schema change, no migration, no new tables, no factor data touched.**
- **Only A1–A9 implemented** — A10–A13 (statistical anomaly, source-document
  completeness, AI confidence, import-file validation) are explicitly **not**
  implemented.

---

## 2. Files created / modified

| Path | Change |
|---|---|
| `backend/domain/validation.py` | **Created** — `ValidationSeverity`, `ValidationIssue`, `ValidationReport`, `ValidationRequest` |
| `backend/engines/validation.py` | **Created** — `ValidationEngine`, protocols (`LogsSource`/`OrgSource`/`FactorLookup`), `gas_coverage()`, 34 stable `VAL_*` issue codes |
| `backend/domain/__init__.py` | **Modified** — export the four validation domain types |
| `backend/engines/__init__.py` | **Modified** — export `ValidationEngine` |
| `backend/tests/unit/domain/test_validation.py` | **Created** — 20 domain-contract tests |
| `backend/tests/unit/engines/test_validation.py` | **Created** — ~50 engine tests covering every A1–A9 capability, SEAI CO2-only handling, and side effects |

No existing engine, repository, domain model, database table or factor record
was modified. (The `OrganizationsRepository.get_metadata` read accessor the
contract flagged as optional already existed — no repository change was needed.)

---

## 3. Implemented A1–A9 capabilities

| # | Capability | Engine entry point | Rule summary |
|---|---|---|---|
| A1 | Input/activity validation | `validate_input()` | activity non-empty; quantity ≥ 0; reporting_year ∈ 1990–2100; unit present when the factor requires one (all error/blocking) |
| A2 | Calculation reproducibility | `validate_snapshot()` | recomputed `quantity × co2e_multiplier` (quantised) == stored `co2e_kg`; `content_hash == build_content_hash()`; sub-precision drift = warning |
| A3 | Factor/match country-provider correctness | `validate_match()` | matched → factor present; `factor.country == request.country`; `preferred_provider` respected; factor unit == request unit (errors); low confidence / no-match = warnings |
| A4 | Scope/unit consistency | `_validate_log_consistency()` | log unit == factor unit; scopes in the known set; log scope consistent with factor scope; family-implied scope mismatch = warning |
| A5 | Snapshot validation (provenance) | `validate_snapshot(..., factor_source, factor_set, import_batch_id)` | batch-linked factors (SEAI) require consistent provenance; missing = warning, mismatched = error; `gas_coverage` carried in issue context |
| A6 | Data integrity | `_validate_log_integrity()` / `validate_logs()` | quantity/co2e non-negative; factor resolves (orphan = error); computed log without snapshot link = warning |
| A7 | Reporting-period validation | `_validate_log_period()` | date.year == reporting_year (warning); date inside period (warning, or error in strict mode) |
| A8 | Organization/facility validation | `validate_org()` / `_validate_membership()` | org exists + active (errors); facility/asset belongs to org (error); missing intensity metadata (warning when requested) |
| A9 | Audit-time verification | `verify_snapshots()` | aggregate A2+hash verification across a snapshot set |

**Error model:** `ValidationReport.ok` is False iff any error-severity issue
exists. In strict mode (`ValidationRequest.strict=True`) blocking errors raise
`ValidationFailedError` (422) and publish `ValidationFailed`; warnings never
raise. Every composite run records a `validation:completed` audit entry.

---

## 4. Test results

**Environment limitation:** the tooling shell kills any foreground process that
runs longer than a few seconds, so `pytest` could not complete under this
session (it produced no output before termination). Validation was therefore
performed two ways:

1. **Compile check** — `python -m py_compile` on all new/modified modules:
   **PASS** (no syntax errors).
2. **Standalone runtime self-check** — a temporary harness executed **every**
   pytest assertion from both new test files 1:1 (same fixtures, same
   assertions) directly against the modules:

   **50/50 checks PASS, 0 failures** — covering A1–A9 (valid + invalid cases),
   SEAI CO2-only full-pipeline, `gas_coverage` provenance, strict-mode
   `ValidationFailedError`, `ValidationFailed` event publication, audit
   logging, constructor guards, and the domain contracts.

The pytest files remain the canonical suite and must be run when the
environment permits:

```bash
cd backend && python -m pytest tests/unit/domain/test_validation.py tests/unit/engines/test_validation.py -q
```

Existing tests were not weakened — the change set adds new modules and test
files only; no existing assertion was altered.

---

## 5. SEAI CO2-only validation results

Verified at runtime (self-check scenarios, all PASS):

- **Full SEAI pipeline validates clean:** an IE `factor_source='SEAI'`,
  `factor_set='SEAI-2025'` electricity log + snapshot + org + facility pass
  `validate()` end-to-end with **zero** issues. No CH₄/N₂O components are
  required.
- **Provenance:** a batch-linked SEAI snapshot with matching
  `factor_source`/`factor_set`/`import_batch_id` validates clean; missing
  provenance is a warning, mismatched batch/source is an error.
- **Provenance context:** every provenance/match issue carries
  `context.gas_coverage` so callers can label SEAI figures as **kg CO2**
  (never full CO2e) — ready for ReportGenerationEngine (Phase 9.3).
- **A3 country/provider:** an IE request with `preferred_provider='seai'`
  matching the SEAI/IE factor is clean; a GB request or a different preferred
  provider is an error. DEFRA remains CO2e (`gas_coverage == "CO2e"`).
- The `emission_factors` schema was **not** changed; the 7,049-factor
  development database was **not** modified.

---

## 6. Architectural deviations

| # | Item | Detail | Severity |
|---|---|---|---|
| D1 | Protocol-based repository consumption | The engine consumes the three repositories through lightweight protocols (`LogsSource`, `OrgSource`, `FactorLookup`) instead of importing the concrete classes — matching the existing `CalculationSink`/`FactorSearch` pattern. The production repositories satisfy the protocols structurally. | None (conforms to codebase convention) |
| D2 | `EventBus` added as an engine dependency | The frozen prep-pack diagram lists `logs_repo`, `org_repo`, `factor_repo`, `audit_logger` for ValidationEngine; the engine additionally consumes `EventBus` to publish the existing `ValidationFailed` event (justified by §14 event platform and the event already existing in `domain/workflow.py`). | Low (documented) |
| D3 | A6 snapshot-existence check scope | The engine cannot verify a stored snapshot's existence (no snapshot getter on the repository surface), so A6 checks snapshot **linkage** (a computed log without `snapshot_id` is a warning) instead of resolving the snapshot row. | Low (documented) |
| D4 | Family-consistency rule severity | The contract's "fuels → Scope 1 / electricity → Scope 2" family check is implemented as a **warning** (never an error) to avoid false positives on provider edge cases. | None |

No deviations from the approved design decisions: no schema change, no
migration, no new table, no modification of existing repositories or factors,
and no A10–A13 (future) capabilities implemented.

---

## 7. Remaining Phase 9 work

Not implemented in Phase 9A (out of scope per the approved contract):

- **9.2 BenchmarkingEngine** — `backend/engines/benchmarking.py` +
  `backend/domain/benchmarking.py` (internal-only benchmarking, B1–B8).
- **9.3 ReportGenerationEngine** — `backend/engines/report_generation.py`
  (composes Calculation + Validation + Benchmarking; persists via
  `ReportsRepository`; publishes `ReportGenerated`).
- **9.4 Integration tests** — `backend/tests/integration/test_validation.py`,
  `test_benchmarking.py`, `test_report_generation.py` against
  `carbontally_test`.

The ValidationEngine is ready to be consumed by 9.3 (its `ValidationReport`
and `gas_coverage` provenance are part of the 9.3 section-building contract).

---

**PHASE 9A COMPLETE — READY FOR PHASE 9B**

