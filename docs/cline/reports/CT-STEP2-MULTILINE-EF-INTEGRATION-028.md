# CT-STEP2-MULTILINE-EF-INTEGRATION-028 — Real Mapping → Authoritative EF → Calculation Integration

Bounded integration task, **read-only against real data**. P1 untouched; no production access; no code
change made (the forensic evidence below shows the two unresolved rows need a product/data decision, not
a code edit inside this window).

---

## 1. Task ID

`CT-STEP2-MULTILINE-EF-INTEGRATION-028`

## 2. Baseline

| Item | Value |
| --- | --- |
| Branch / worktree | `p8-release-reconciled` · `/tmp/ct_step2` |
| Baseline SHA | `923dda5` (`HEAD == origin`, working tree clean — verified) |
| Upstream | `023` (candidates 2→5, production PASS) · `026` `efd50fd` (provenance) · `027` `923dda5` (unit families) |

## 3. Code-trace map of the real pipeline

```text
extracted line_items      services/extraction_fidelity.build_line_items()
mapping stage             services/automatic_processing._map()
  mapping input text      services/automatic_processing._mapping_input_text()      (026)
  request                 domain.matching.MatchRequest(id, activity, country, reporting_year, unit,
                                                      organization_id, max_stages)
  engine                  engines.factor_matching.FactorMatchingEngine.match()
  stages                  engines.factor_matching.build_matching_pipeline(
                              MatchingPipelineConfig(), alias_resolver=RepositoryAliasResolver(...))
  stage order observed    exact_match → natural_key → alias_match → keyword_search → fuzzy_match
  search index            infra.search_index.FactorSearchIndex
  customer factors        data.customer_factors.CustomerFactorsRepository (checked first when org given)
  aggregate preference    services.automatic_processing._prefer_aggregate_factor()  [service level]
unit compatibility        core.units.resolve_unit_for_factor()  (027) → engines/validation.py
factor arithmetic         domain.factor.EmissionFactor.calculate_emissions()  (exact unit compare →
                          UnitMismatchError → VAL_UNIT_MISMATCH)
calculation sink          engines/calculation.CalculationEngine(sink=EmissionsLogsRepository)  [not
                          exercised: it writes; see §15]
```

Production wiring confirmed identical in `api/dependencies.py` (per-request) and
`workers/automatic_processing.py` (worker). The 026 stub matcher was **not** used.

## 4. Existing matcher identified

`engines/factor_matching.py::FactorMatchingEngine` over the stage pipeline built by
`build_matching_pipeline(MatchingPipelineConfig(), alias_resolver=RepositoryAliasResolver(aliases))`,
with candidates from the in-memory `FactorSearchIndex`.

## 5. Authoritative EF source identified

`public.emission_factors` in the **local authoritative database** (`supabase_db_carbon_ledger` @
`127.0.0.1:54426`, reached through the repository's own `DATABASE_URL`), loaded through the
repository's own `data.emission_factors.EmissionFactorsRepository.load_all_for_index()`:

```text
rows loaded into the real index : 7 049
reporting_year                  : 2025
provenance fields               : factor_source DEFRA-DESNZ · factor_set DEFRA-2025 · scope · unit
unit spread (top)               : km 2515 · miles 2181 · tonne.km 754 · kg 405 · tonnes 379 ·
                                  passenger.km 205 · kWh (Gross CV) 155 · kWh (Net CV) 155
```
No factor was created, modified, substituted or invented; the dataset was read only.

## 6. Five-row source oracle (source values unchanged)

```text
1 Gas usage 5,362.2000 kWh    2 Diesel supply 4,434.4000 L    3 Waste disposal 60 t
4 Water supply 163.2000 m³    5 Power consumption 24,620.5000 kWh
```
Detector: `candidate_lines = 5`, `line_items = 5` — the 023 property is intact.

## 7–10. Row-by-row results (real matcher + real EF)

**ROW 1 — Gas usage 5362.2 kWh**
```text
normalised unit      kWh
detected activity    Natural gas          (real _detect_activity)
mapping input        'Natural gas'
match status         no_match (confidence 0.000)
stages executed      exact_match, natural_key, alias_match, keyword_search, fuzzy_match
factor               none — no factor fabricated
calculation          not attempted
provenance           line_number 1 · page 1 · source_line preserved
classification       CODE/MAPPING reachability question (see §20a)
```

**ROW 2 — Diesel supply 4434.4 L**
```text
normalised unit      litres
mapping input        'Diesel'
match status         matched (confidence 1.000)
factor id            c3afa542-1daf-419c-88ea-94252d4dba18
factor activity      Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]
factor unit/scope/yr litres | Scope 1 | 2025        source/set DEFRA-DESNZ / DEFRA-2025
unit resolution      'litres' + 'litres' → 'litres'  (027 semantics honoured)
calculation          4434.4 × 0.03705 = 164.294520 kg CO2e
provenance           line_number 2 · source_line preserved
note                 factor-CHOICE quality concern (§20b)
```

**ROW 3 — Waste disposal 60 t**
```text
normalised unit      tonnes
mapping input        'Waste'
match status         matched (confidence 1.000)
factor id            5b8f5355-6828-4e5c-a152-6f445b265ba0
factor activity      Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]
factor unit/scope/yr tonnes | Scope 1 | 2025        source/set DEFRA-DESNZ / DEFRA-2025
unit resolution      'tonnes' + 'tonnes' → 'tonnes'
calculation          60.0 × 3.5504 = 213.024000 kg CO2e
provenance           line_number 3 · source_line preserved
note                 component sub-factor pick (CH4 only) — §20b
```

**ROW 4 — Water supply 163.2 m³**
```text
normalised unit      cubic metres
mapping input        'Water'
match status         matched (confidence 1.000)
factor id            c1d6c919-baad-4b7b-9702-a147867bde43
factor activity      Water supply > Water supply > Water supply (kg CO2e) [cubic metres]
factor unit/scope/yr cubic metres | Scope 3 | 2025   source/set DEFRA-DESNZ / DEFRA-2025
unit resolution      'cubic metres' + 'cubic metres' → 'cubic metres'
calculation          163.2 × 0.1913 = 31.220160 kg CO2e
provenance           line_number 4 · source_line preserved
```

**ROW 5 — Power consumption 24620.5 kWh**
```text
normalised unit      kWh
detected activity    (none — no taxonomy keyword)
mapping input        'Power consumption kWh € €'   (literal source text preserved by 026)
match status         no_match (confidence 0.000)
factor               none — no factor fabricated
calculation          not attempted
provenance           line_number 5 · source_line preserved
classification       TAXONOMY COVERAGE GAP (§11)
```

## 11. Power-consumption taxonomy finding (decided with real data)

```text
taxonomy (repo _detect_activity)   no keyword resolves "Power consumption"
factors with activity_type LIKE '%power%'        0
factors that would fit, with a compatible unit   Fuels > Electricity > Electricity consumption
                                                 (kg CO2) [kWh]  and  Gross electricity supply [kWh]
unit compatibility                               'kWh' ↔ 'kWh' → compatible; and
                                                 unit_matches_with_qualifier("kWh","kWh (Gross CV)") = True
```
**Classification: TAXONOMY COVERAGE GAP** — an authoritative factor *does* exist for the physical
quantity, but no canonical activity/keyword maps "Power consumption" onto it. This is a **product/data
decision** (which synonym set is authoritative), and per §15 I did **not** add an activity-name
shortcut. The row stays preserved and unresolved.

## 12. Unit compatibility findings

* Every source unit normalised correctly through the existing single normaliser
  (`kwh→kWh`, `l→litres`, `t→tonnes`, `m³→cubic metres`).
* For all three matched rows, `resolve_unit_for_factor(source, factor.unit)` returned the factor's unit
  — i.e. **same-unit aliases only**, exactly the 027 contract.
* No cross-family coercion was observed anywhere on the real path; a hypothetical `t` row paired with a
  `litres` factor would now be returned unchanged and rejected by `calculate_emissions`
  (asserted by the 027 suite, re-run below).

## 13. 027 regression result

Green: `tests/unit/test_units_family_compat.py` (35) + `tests/unit/test_units.py` +
`tests/unit/test_units_qualifier.py` (40) — 75 passed, 0 failed. The real path above used the 027
resolver and produced no cross-family substitution.

## 14. 026 provenance regression result

Green: `tests/unit/services/test_multiline_provenance_mapping.py` 16/16 passed, and the live run
confirmed per-row provenance on the real document (`line_number` 1–5, verbatim `source_line`,
`description` retained).

## 15. Test methodology (and its honest limits)

* **Primary oracle** (`/tmp/v28_real_oracle.py`): real detector (`build_line_items`) → real mapping input
  text (`_mapping_input_text`) → real `FactorMatchingEngine` + real stage pipeline + real alias resolver →
  real `EmissionFactorsRepository.load_all_for_index()` over the local authoritative DB (7 049 factors)
  → real `resolve_unit_for_factor` (027) → real factor arithmetic
  (`EmissionFactor.calculate_emissions`). **Read-only: no rows written.**
* **Deliberately not exercised, stated as such**: service-level
  `_prefer_aggregate_factor()` and the `CalculationEngine` → `EmissionsLogsRepository` sink. The sink
  **writes** calculation snapshots, so it was skipped to avoid mutating the database. Consequence: the
  factor *choice* in §7–10 is the engine's direct choice, **not** the service's final choice; the
  arithmetic (quantity × real multiplier under 027 unit resolution) is real.
* Unit tests using doubles remain where their purpose is isolation, and are **not** presented as real-EF
  evidence.

## 16. Real matcher vs stub distinction

| Run | Matcher | EF data | Used as 028 evidence |
| --- | --- | --- | --- |
| 026 suite (stub `_RecordingMatcher`) | stub | none | provenance coverage only (**not** EF evidence) |
| 028 oracle (§7–10) | **real `FactorMatchingEngine`** | **real 7 049-row dataset** | **YES** |

## 17. Test results

```text
026 provenance suite                                      16 passed
027 unit-family + existing unit suites                    75 passed
tests/unit/services (P1, extraction, mapping, processing) 0 failures
tests/unit/engines                                        0 failures
newly failing tests                                       0
pre-existing failures                                     none observed
integration suites                                        NOT run (destructive TRUNCATE — F-046-1)
production verification                                   NOT performed
```

## 18. Code changes

**NONE.** The evidence identifies (a) a taxonomy/synonym gap and (b) a factor-selection question, both
requiring a product/data decision; neither may be "fixed" here by an activity-name shortcut or by
altering selection behaviour. No file was modified except this report.

## 19. Schema limitations

None. The identifiers the task requires (`source_item_id`, `source_line_item_id`, `source_ordinal`,
`line_number`, `source_line`, factor identity) are all representable in the existing schema; no migration
was created or needed.

## 20. EF / taxonomy coverage gaps and findings

**(a) ROW 1 — natural-gas reachability (CODE/MAPPING vs EF-quality question, UNRESOLVED).**
`activity='Natural gas'`, `unit='kWh'` returned `no_match` after all five stages, **yet** the dataset holds
10–11 factors per unit for natural gas across `cubic metres`, `kWh (Gross CV)`, `kWh (Net CV)` and
`tonnes`, and `unit_matches_with_qualifier("kWh","kWh (Gross CV)")` is `True`. Every natural-gas row in the
sample is a per-component sub-factor (`… of CH4 per unit`, `… of CO2 per unit`, `… of N2O per unit`), and
the service has `_prefer_aggregate_factor()` to avoid component picks. So this is either (i) a
matcher-reachability defect for short canonical activities, or (ii) governed refusal because only
component factors exist for that activity/unit. **Distinguishing (i) from (ii) needs a service-path run
(with aggregate preference) plus a review of the natural-gas factor set — NOT done here.**

**(b) Factor-CHOICE quality on matched rows (observed; not a demonstrated defect).** Row 2 matched
`Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]` (0.03705) and Row 3 matched
`Waste oils (kg CO2e of CH4 per unit) [tonnes]` (3.5504) — both real DEFRA-DESNZ/2025 factors, but
semantically weak picks for "Diesel supply" and "Waste disposal" (a combustion factor and a
waste-disposal factor would be expected). Because `_prefer_aggregate_factor` was bypassed, the service may
already re-select; no conclusion is drawn before a service-path run.

**(c) ROW 5 — `"Power consumption"` = TAXONOMY COVERAGE GAP** (§11): factor exists, keyword does not.

## 21. Production state

**No production mutation.** No production access, uploads, jobs, queue operations, database writes, EF
changes, configuration/Render/Vercel changes or deployments. The protected job
`9ef61662-1c0a-497a-b5e9-c179e2134784` was not touched. All database activity was **read-only** against the
**local** authoritative database.

## 22. P1 state

**`shadow`, unchanged** — no rollout, allowlist, flag or environment change; `candidate_lines = 5`
re-confirmed locally.

## 23. Git commits

Report only — `docs/cline/reports/CT-STEP2-MULTILINE-EF-INTEGRATION-028.md` (no code, no test changes).
Pushed to `origin/p8-release-reconciled`; SHA reported in the completion response.

## 24. Final verdict

### `PARTIAL`

The **real** matcher and the **real** authoritative factor dataset were exercised (7 049 factors,
DEFRA-DESNZ/2025) against a real five-row extraction: three rows (`Diesel`, `Waste`, `Water`) resolved to
real, unit-compatible factors with traceable identity and correct factor arithmetic under 027 unit
semantics; provenance survived on all five rows; nothing was fabricated for the unresolved rows. The
pipeline is therefore **exercised end to end for supported rows**.

Not `PASS — VERIFIED` because two of five material rows remain unresolved (one taxonomy gap, one
reachability/selection question), the aggregate-preference step and the calculation sink were not
exercised (deliberately, to avoid database writes), and the factor *choice* recorded is the engine's
direct pick rather than the service's final one.

## 25. Remaining limitations

1. `_prefer_aggregate_factor()` (service level) not exercised → factor selection not final (§15).
2. `CalculationEngine` + snapshot sink not exercised (writes) → persistence of the calculation record and
   of `source_line_item_id` during a real calculation was **not** verified here (the field is passed by
   the 026-verified service path and covered by its tests).
3. Rows 1 and 5 unresolved; (a)/(b) not yet classified as code vs data.
4. The **local** authoritative database was used; whether it matches the production factor set was **not**
   established.
5. No report was generated (explicitly out of scope, §14).

## 26. Recommended next PO gate

1. **Taxonomy decision** for synonyms such as "Power consumption" → the authoritative electricity activity
   (factor already exists: `Electricity consumption (kg CO2) [kWh]`), delivered as a bounded
   taxonomy/synonym change with tests — **not** an activity-name shortcut.
2. **Classify ROW 1** by running the *service* path (aggregate preference + read-only sink) for
   `'Natural gas' + kWh` and reviewing the natural-gas factor set: matcher-reachability defect vs
   component-only data coverage.
3. **Factor-selection quality review** with the PO (combustion vs biofuel/development diesel; waste disposal
   vs waste oils), since it directly affects reported figures.
4. Re-run the 028 oracle through the **service** path once (1) and (2) are decided, with a read-only sink,
   to convert `PARTIAL` into `PASS — VERIFIED`.



