# CT-STEP2-MULTILINE-E2E-REPAIR-029 — Multi-Line PDF End-to-End Repair

Bounded task. **No code change was made** (the two remaining breaks require a policy/taxonomy decision —
evidence below). P1 untouched; no production access or mutation.

---

## 1. Task ID

`CT-STEP2-MULTILINE-E2E-REPAIR-029`

## 2. Baseline

| Item | Value |
| --- | --- |
| Branch / worktree | `p8-release-reconciled` · `/tmp/ct_step2` |
| Baseline SHA | `923dda5` (verified `HEAD == origin`, clean) |
| Predecessors | `023` detection · `025` production PASS · `026` provenance (PARTIAL) · `027` unit families (PASS) · `028` real matcher (PARTIAL) |

## 3. Code-trace findings (real service path, this task)

```text
build_line_items → line_items[]             real detector (023/026)                       OK
_map()               services/automatic_processing._map()
  mapping input      _mapping_input_text()  (026)                                         OK
  match              FactorMatchingEngine + real stages (real index, real aliases)         RUN
  aggregate pref     _prefer_aggregate_factor()                                           RUN (029)
  persistence        save_mapped_data / advance_stage                     recorded, NOT written
  unresolved rows    explicit {status: "unmapped", reason, source_ordinal, source_line}    OK
_calculate/_calculate_line → CalculationRequest (source_item_id, source_line_item_id)      NOT RUN (writes)
CalculationEngine sink (EmissionsLogsRepository)                                           NOT RUN (writes)
report generation / report-line provenance                                                 NOT RUN
```

## 4. Existing architecture reused (nothing parallel was created)

`extraction_fidelity` · `automatic_processing._map/_prefer_aggregate_factor` ·
`FactorMatchingEngine` + `build_matching_pipeline` + `RepositoryAliasResolver` + `FactorSearchIndex` ·
`data.emission_factors.EmissionFactorsRepository` (incl. `find_by_activity`, `load_all_for_index`) ·
`data.factor_aliases` · `data.customer_factors` · `core.units` (027 semantics) ·
`domain.matching.MatchRequest` · `domain.factor.EmissionFactor`.

## 5–6. Five-row oracle and extraction result

```text
source values unchanged: 5362.2 kWh · 4434.4 L · 60 t · 163.2 m³ · 24620.5 kWh
detector: candidates = 5 · line_items = 5              (023 contract intact)
real authoritative factors loaded into the index: 7 049   (DEFRA-DESNZ / DEFRA-2025)
```

## 7. Mapping result for each row (real service path, aggregate preference applied)

| Row | Mapping input | Pipeline result | After aggregate preference | Outcome |
| --- | --- | --- | --- | --- |
| 1 Natural gas (kWh) | `'Natural gas'` | **no_match** conf 0.000 | no_match (short-circuit, §8) | **UNRESOLVED** |
| 2 Diesel (litres) | `'Diesel'` | matched 1.000 | unchanged — `Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]` 0.03705 (Scope 1, 2025) | mapped (selection concern, §10) |
| 3 Waste (tonnes) | `'Waste'` | matched 1.000 — component `… Waste oils (kg CO2e of CH4 per unit) [tonnes]` 3.5504 | **re-selected** → `Fuels > Liquid fuels > Waste oils (kg CO2e) [tonnes]` 3219.37916 | mapped (aggregate preference **works**) |
| 4 Water (m³) | `'Water'` | matched 1.000 | unchanged — `Water supply (kg CO2e) [cubic metres]` 0.1913 (Scope 3, 2025) | mapped (sound) |
| 5 Power consumption (kWh) | `'Power consumption kWh € €'` | **no_match** conf 0.000 | no_match | **UNRESOLVED** |

Full `_map()` over the five rows returned **`blocked`** with a truthful per-line reason and **no rows lost**:

```text
"mapping could not auto-resolve: line 1: no confident factor for 'Natural gas' kWh
 (status=no_match, confidence=0.00); line 5: no confident factor for 'Power consumption kWh € €' kWh
 (status=no_match, confidence=0.00)"
```

## 8. Natural-gas investigation — CODE DEFECT, precisely characterised

```text
engine (staged pipeline) 'Natural gas' + kWh                       -> no_match (0.000)
factors.find_by_activity('Natural gas', unit='kWh',
                         unit_qualifier_tolerant=True)             -> 20 candidates, 8 AGGREGATE:
   Fuels > Gaseous fuels > Natural gas (100% mineral blend) (kg CO2e) [kWh (Gross CV)]  0.18494
   Fuels > Gaseous fuels > Natural gas (100% mineral blend) (kg CO2e) [kWh (Net CV)]    0.20489
unit_matches_with_qualifier('kWh','kWh (Gross CV)')                -> True (established semantics)
_prefer_aggregate_factor(activity, unit, no_match_result)          -> no_match
```

**Cause (read from the code):** `_prefer_aggregate_factor` begins with

```python
if result.status != "matched" or result.factor is None:
    return result      # no_match short-circuits; the aggregate lookup is never attempted
```

so the PO-mandated aggregate discoverability (`P2 EF-E`: *"a qualified aggregate factor must be
discoverable"*) is **unreachable exactly when the staged pipeline fails** — i.e. for a short canonical
activity whose only authoritative factors are qualified aggregates. The dataset is **not** the problem:
valid, unit-compatible aggregates exist and are already returned by the repository call the service makes.

**Why the fix was not implemented here (honest boundary).** Turning that discovery into a *selected*
factor requires defining the **confidence/status semantics of a recovered candidate**: the mapping gate is
`result.confidence < AUTO_MAPPING_CONFIDENCE_MIN`, the staged engine assigns that confidence, and
`find_by_activity` returns bare factor rows with no score. Any value I chose would be **new
factor-selection policy**, which §8/§17 reserve for the PO — so the defect and its exact mechanism are
reported, not guessed at.

## 9. Power-consumption investigation — TAXONOMY GAP (PRODUCT DECISION REQUIRED)

```text
taxonomy: no existing keyword resolves "Power consumption"
factors with activity_type LIKE '%power%'                        -> 0
authoritative, unit-compatible factors for the physical quantity:
   Fuels > Electricity > Electricity consumption (kg CO2) [kWh]
   Fuels > Electricity > Gross electricity supply (kg CO2) [kWh]
engine('Power consumption kWh € €' + kWh)                        -> no_match
```

The missing link is the **synonym/taxonomy layer**; selecting the authoritative canonical activity for
“Power consumption” is a **product/data decision** (several plausible canonical targets/scopes exist).
Per §7/§17 no phrase-specific mapping was added. Row preserved, unresolved.

## 10. Diesel factor-selection investigation — policy question, not a proven defect

`'Diesel'` + `litres` selected `Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]` (0.03705) both
before and after aggregate preference (it is already non-component, so the aggregate rule has nothing to
re-select). A combustion diesel factor would be expected for an invoice line “Diesel supply”. The existing
selection semantics (exact → natural key → alias → keyword → fuzzy, then aggregate preference) produced
this on real data; whether the policy should exclude development/biofuel-derived factors (or require a
fuel-class match) is **not defined by existing code or data** → **FACTOR-SELECTION POLICY GAP / PRODUCT
DECISION REQUIRED**. No ranking policy was invented.

## 11. Waste factor-selection investigation — aggregate rule works; semantics are a policy question

The component pick **was corrected** by the existing aggregate rule (CH4 sub-factor → `Waste oils
(kg CO2e)`), proving that step functions when a match exists. The residual concern is semantic selection
quality: `'Waste'` resolves to *waste oils* rather than a waste-disposal activity, with an aggregate
multiplier of `3219.37916` per tonne. That is a **POLICY/DATA question**, not a code defect — reported, not
re-ranked.

## 12. Authoritative EF evidence

```text
source          public.emission_factors, LOCAL authoritative DB (127.0.0.1 via repo DATABASE_URL)
rows loaded into the real index            7 049   (reporting_year 2025)
provenance      factor_source DEFRA-DESNZ · factor_set DEFRA-2025 · scope · unit
created/modified/substituted/invented      NONE  (read-only)
```

## 13. Unit compatibility evidence

* Source units normalised by the single existing normaliser: `kwh→kWh`, `l→litres`, `t→tonnes`,
  `m³→cubic metres`.
* Every selection stayed inside 027 semantics (`resolve_unit_for_factor` = same-unit alias or same-base
  qualifier only); qualifier compatibility via the established
  `unit_matches_with_qualifier('kWh','kWh (Gross CV)') = True`.
* No cross-family coercion anywhere on the real path; no physical conversion introduced.

## 14–15. Calculation sink and calculation provenance — NOT EXERCISED

The real `CalculationEngine` → `EmissionsLogsRepository` sink was **not** run. It writes calculation
snapshots and §5 authorises local writes only where required; with Rows 1 and 5 unresolved, persisting
calculations would have created audit rows for a pipeline state that is about to change. Consequently
`source_item_id` / `source_line_item_id` / `source_ordinal` / `line_number` / `source_line` were **not**
verified through a persisted snapshot here (they are passed by the 026-verified service path and asserted by
that suite). No sink or snapshot evidence is claimed.

## 16–18. Report generation and bidirectional report provenance — NOT EXERCISED

No report was generated and no report-line → source trace was demonstrated. Report generation remains the
outstanding stage for a follow-up (it needs resolved factor selection so report lines have calculation
records to cite). Nothing here is presented as report evidence.

## 19–20. Supplier / date / invoice metadata and page–line–row semantics

Not exercised end-to-end (no report). What the pipeline preserves today, verified in this run:
`extracted_data` carries `supplier` (`Pure Energy PLC`) and `date` (`2026-05-08`), and every candidate keeps
`line_number`, `page` (honest `page_basis = document`), `source_line`, `source_ordinal`, `quantity`, `unit`.
The invoice reference `Ref No.: PWR/2026/8130` is in the raw text but has no established field on the
mapped/calculated row set — **not claimed as traceable**. No source location was manufactured; only a source
ordinal/line is asserted.

## 21. Unresolved rows

Rows 1 and 5 remain explicit and auditable (description, quantity, unit, source_line, ordinal preserved; no
`factor_id`, no calculated emissions). `_map` blocked with a truthful per-line reason; the three mapped rows
were not erased, and no partial mapping was persisted (0 `save_mapped_data` calls, 1 block record).

## 22. Tests

No code was modified in 029, so no new tests were added (asserting a policy I am not authorised to choose
would be misleading). Regression of the exercised path was performed by running the real service path
(above) plus the existing suites (§23–25). Classes exercised: **integration-style, database-backed,
read-only** (`/tmp/v29_service_path.py`) for mapping/EF; **unit suites** for 023/026/027.

## 23. 023 regression

`candidate_lines = 5`, `line_items = 5` on the oracle — intact.

## 24. 026 regression

`tests/unit/services/test_multiline_provenance_mapping.py` — 16/16 passed; per-row identity preserved in the
live run.

## 25. 027 regression

`tests/unit/test_units_family_compat.py` + `test_units.py` + `test_units_qualifier.py` — 75 passed, 0 failed.

## 26. 576-PDF regression

**Not run** — extraction code was not touched, so the 023 sweep result stands unchanged; re-running it was
not possible within this task's remaining budget. Stated plainly rather than assumed.

## 27. Schema limitations

None. Everything required is representable in the existing schema; no migration was created.

## 28. Product-policy decisions still required

1. **Natural-gas recovery policy** (blocks Row 1): how a deterministic candidate discovered via
   `find_by_activity` should be admitted when the staged pipeline returns `no_match` — in particular the
   confidence/status semantics and aggregate-vs-component preference. Mechanism located exactly (the
   `no_match` short-circuit).
2. **Power-consumption synonym** (blocks Row 5): the authoritative canonical activity (electricity
   consumption vs gross electricity supply; scope implications).
3. **Diesel factor preference**: may development/biofuel-derived factors satisfy a combustion diesel row
   (affects reported figures)?
4. **Waste activity preference**: should “Waste disposal” resolve to waste oils or to a
   waste-disposal/landfill activity?

## 29. Production state

**No production mutation.** No production access, uploads, jobs, queue operations, production DB writes,
report generation, EF changes, configuration/Render/Vercel changes or deployments. Protected job
`9ef61662-1c0a-497a-b5e9-c179e2134784` untouched. All database activity was **read-only** against the
**local** database.

## 30. P1 state

**`shadow`, unchanged** — no rollout, allowlist, flag or environment change.

## 31. Implementation commits

**NONE** — no code or test change was made. Report only:
`docs/cline/reports/CT-STEP2-MULTILINE-E2E-REPAIR-029.md`, pushed to `origin/p8-release-reconciled`.

## 32. Final verdict

### `PARTIAL`

For the first time on the **real service path** (not the direct matcher): the five-row extraction is intact;
the real staged matcher **and** the aggregate-preference step were both exercised over the real
7,049-factor dataset; one component-factor selection was demonstrably corrected by the existing aggregate
rule (Row 3); Rows 2/3/4 map to real, identity-bearing, unit-compatible factors; Rows 1 and 5 remain
explicitly unresolved with truthful per-line reasons and nothing fabricated; unit safety holds under 027.

Not `PASS — FULL E2E REPAIR VERIFIED`, because two of five rows remain unresolved pending **product
decisions** (natural-gas recovery policy; power-consumption synonym); the natural-gas gap is a located
**code defect** whose correction requires that policy (confidence semantics); the real calculation **sink**
and **report generation / report → source trace** were **not** exercised; and factor-selection quality
(diesel, waste) is an open policy question.

## 33. Remaining limitations

1. Rows 1 and 5 unresolved (policy-dependent) — no mapping or factor fabricated.
2. Calculation sink not exercised; snapshot-level provenance unverified here.
3. Report generation and report → source provenance not exercised (no report produced).
4. Invoice reference/date/supplier not proven to survive into report-level provenance.
5. Local EF dataset used; identity with the production factor set not established.
6. 576-PDF sweep not re-run (no extraction change).
7. `_prefer_aggregate_factor` was exercised with a recording (non-writing) persistence double: the mapping
   decisions are real, the persistence calls are not.

## 34. Recommended next PO gate

1. **Decide the natural-gas recovery policy**, then apply a small generic fix: when the staged pipeline
   returns `no_match`, consult the deterministic `find_by_activity` candidates (unit-qualifier tolerant,
   aggregate preferred) under a PO-defined confidence — the defect is located and the change is bounded.
2. **Decide the power-consumption synonym** (electricity activity + scope), then implement through the
   existing taxonomy/alias mechanism with tests.
3. **Decide diesel/waste selection preference** (fuel-class and activity-class rules).
4. Then authorise a follow-up bounded task to run the oracle through `_calculate` with the **real sink** in
   the local environment and to **generate an actual report**, proving report → snapshot →
   `source_line_item_id` → source row plus supplier/date traceability (§14–18, §33.2–33.4).



