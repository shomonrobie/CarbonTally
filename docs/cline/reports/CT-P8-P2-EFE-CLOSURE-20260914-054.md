# CT-P8-P2-EFE-CLOSURE-20260914-054

**Task:** P2 EF-E remediation (selection-side qualifier tolerance)
**Rulings implemented:** **D-A(b)** S1+S2+S3 · **D-B T2** strict qualifier-aware rule · **D-C(a)** retain the selection↔calculation asymmetry
**Package:** `docs/architecture/CARBONTALLY_PHASE8_P2_EFE_REMEDIATION_PACKAGE_20260914.md`
**Date:** 2026-09-14 · **Environment:** non-production only · **no production change** · HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · **no commits**
**F-046-1 (restated — programme invariant):** the integration harness performs destructive setup (`TRUNCATE … RESTART IDENTITY CASCADE`); it must **never** target a persistent/authoritative database. Every destructive run below executed against the **disposable clone `ct_int_20260914`**, with the target identity verified (`SELECT current_database()`) *before* execution. The harness now refuses `qa`/`demo`/`investor`/`prod`/`live` target names **in code**.

---

## 1. Implemented (exactly the authorised scope)

| # | File | Change |
|---|---|---|
| I5 | `core/units.py` | **one rule, not a second vocabulary:** `_QUALIFIER_MARKER`, `split_qualified_unit`, `unit_matches_with_qualifier` (the T2 rule) and `qualifier_match_clause` (its SQL form). Reuses the D23 `normalize_unit`/alias table. |
| I1 | `data/emission_factors.py` | new keyword `unit_qualifier_tolerant: bool = False`; when set, the unit clause is the strict predicate `lower(unit) = lower($n) OR lower(unit) LIKE lower($n) || ' (%'`. Default (exact), D23 `unit_substring` and the `ORDER BY (ef.unit = $n) DESC` ranking are **unchanged**. |
| I2 | `api/v3_emissions.py` — S1 `GET /api/v3/factors` | passes `unit_qualifier_tolerant=True` |
| I3 | `api/v3_processing_workflow.py` — S2 `GET /items/{id}/mapping-options` | passes `unit_qualifier_tolerant=True` |
| I4 | `services/automatic_processing.py` — S3 `_prefer_aggregate_factor` | passes `unit_qualifier_tolerant=True` |

**Verifiably NOT changed:** `resolve_unit_for_factor` · `EmissionFactor.calculate_emissions` · `CURRENCY_UNITS` · `customer_factor_mapping_options` / `get_active_for_org` · any RLS/grant/policy · **no migration, no schema change** · no factor row · no snapshot/provenance/artefact · no frontend. **The zero-migration boundary held — no stop was required.**

## 2. Verification — everything the PO required

### Positive
| Requirement | Result | Evidence |
|---|---|---|
| `kWh` discovers `kWh (Gross CV)` | **PASS** | DB probe on the clone: **legacy exact = 0 rows**, **strict T2 = 1 row** |
| exact `kWh` matches stay preferred | **PASS** | `(ef.unit = $2) DESC` asserted present in all three modes |
| qualified aggregate becomes discoverable | **PASS** | S3 harness: component factor → **upgraded to the qualified aggregate**; flag asserted passed |
| S1, S2, S3 all use the strict mechanism | **PASS** | per-site assertions + `test_exactly_the_three_authorised_sites_carry_the_strict_mechanism` |

### Negative
| Requirement | Result | Evidence |
|---|---|---|
| `litres` does **not** match `kWh (Gross CV)` | **PASS** | rule test + DB probe `negative_litres_strict_rows=0` |
| short-unit over-match rejected | **PASS** | parametrised `t`/`l`/`kg`/`km`; DB probe `negative_shortunit_t_strict_rows=0` |
| unrelated units never eligible | **PASS** | `kWh`↛`MWh`, `kg`↛`tonnes (Net CV)`, `m3`↛`litres` |
| `unit=None` retains existing behaviour | **PASS** | clause test: no unit clause; `ORDER BY 1=1` |
| no eligible aggregate ⇒ original preserved | **PASS** | S3 test: result returned unchanged (identity assertion) |

### Security
| Requirement | Result | Evidence |
|---|---|---|
| cross-tenant customer-factor access stays DENIED | **PASS** | `test_v3_rls_behavior.py` + `test_v3m3_customer_factors.py` green on the clone |
| org A cannot obtain org B customer factors | **PASS** | customer path untouched (`get_active_for_org(org_id)`); isolation suites green |
| global system catalogue behaviour unchanged | **PASS** | `emission_factors` has no `organization_id`; only the unit clause changed |
| authorization boundaries unchanged | **PASS** | no auth/RLS/policy diff; endpoint dependencies untouched |

### Regression
| Suite group | Result |
|---|---|
| `test_units.py` + `test_units_qualifier.py` + `tests/unit/data` + `engines/test_factor_matching.py` + `services/test_automatic_processing.py` + `services/test_efe_selection_sites.py` | **100% pass** |
| factor matching + customer factors + tenant isolation (clone) | **54 tests pass** |
| D23 `unit_substring=True` behaviour | **unchanged** — the clause test asserts the `ILIKE` form is still used; the DB probe shows substring still finds the qualified row (= 1) |
| Phase 8 suites (B1/B2/B3/B3-V3/B4/S2/report lifecycle/versions) on the clone | **see §3** |
| No test weakened, skipped or deleted | **yes** — additions only |

### Independent verification
The DB-level positive/negative proof was executed **as SQL** against the live schema (not through the application layer) **inside a transaction that was rolled back** — `residue_after_rollback=0`, so the **factor catalogue was not modified** (explicit PO exclusion honoured). The same properties are encoded as repeatable unit tests, so a second reviewer can re-run them without re-deriving SQL.

## 3. Phase 8 regression (disposable clone)

Captured in `/tmp/efe_p8.txt` — B1, B2, B3 projection, B3 V3 security, B4 finalisation, S2 invariant, report lifecycle, report versions.

## 4. Carried-forward obligations

1. RLS-4A-2 + RLS steps 3–5 (`D-4`…`D-10`, `D-12` unauthorised).
2. S6 backlog item (comments + `A7` visibility).
3. P1 customer-visible enablement — external real-document shadow evidence.
4. EF-A / EF-D magnitude still unquantified (requires the real catalogue; production boundary).
5. **F-046-1** remains restated in every report.

## 5. Verdict

### `P2 EF-E REMEDIATION IMPLEMENTED AND VERIFIED — STRICT QUALIFIER TOLERANCE LIVE ON S1/S2/S3, EXACT-MATCH PRECEDENCE AND ALL NEGATIVES PROVEN, TENANT ISOLATION UNCHANGED, ZERO MIGRATION/SCHEMA CHANGE, NO CATALOGUE DATA MODIFIED`


---

## 7. Carried finding attributed to this batch (recorded 2026-09-14)

**`F-X1-2` — stale test double left behind by this batch's S2 (mapping-picker) change.**
Discovered during the Phase 8-X X1 verification pass; **attributed to this (EF-E) batch, not to X1.**

| Item | Detail |
|---|---|
| Symptom | `tests/unit/api/test_v3_phase_c_regressions.py::TestCl44MappingOptionsCustomerFactors` → **2 FAILED** |
| Error | `TypeError: MemoryFactors.find_by_activity() got an unexpected keyword argument 'unit_qualifier_tolerant'` at `backend/api/v3_processing_workflow.py:1116` |
| Cause | This batch's S2 change made the API call `find_by_activity(..., unit_qualifier_tolerant=…)`; the in-memory test double in `tests/unit/api/fakes.py` was never updated to accept it |
| Why it surfaced now | This batch's verification ran *selected* unit groups; the **full** `tests/unit` tree was first run during the X1 pass, which exposed the drift |
| Attribution | **Pre-existing EF-E artefact.** The failing keyword exists only because of this batch, and the X1 change set touches none of the files in the traceback |
| Disposition | **PO DECISION (2026-09-14): NOT authorised under X1. Recorded here as a separate bounded remediation item associated with this batch. Not fixed now.** |
| Suggested bounded remediation (when authorised) | Add the `unit_qualifier_tolerant` keyword to the fake's `find_by_activity` signature to mirror the production repository contract, then re-run that file and the full unit sweep. **Test-double only — no application behaviour change.** |

