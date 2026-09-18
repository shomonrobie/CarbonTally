# CT-STEP2-UNIT-ALIAS-027 — Unit-Family Alias / Conversion Correctness

Bounded calculation-correctness fix. P1 was not activated; no production data was touched.

---

## 1. Task ID

`CT-STEP2-UNIT-ALIAS-027`

## 2. Baseline

| Item | Value |
| --- | --- |
| Branch / worktree | `p8-release-reconciled` · `/tmp/ct_step2` |
| Baseline SHA | `efd50fd` (`HEAD == origin`, clean) |
| Originating finding | `CT-STEP2-MULTILINE-PROVENANCE-MAPPING-026` (§18.2) |
| Predecessors not reopened | `022` forensic · `023` candidate detection · `025` production PASS · `026` provenance repair |

## 3. Original reproducer (before the fix)

```text
resolve_unit_for_factor("t",   "litres") -> "litres"   <-- mass unit became a volume unit
resolve_unit_for_factor("kwh", "litres") -> "kwh"      (looked safe, by coincidence of letters)
```

## 4. Code trace (call chain, traced before editing)

```text
core/units.normalize_unit(value)            exact 1:1 alias table (UNIT_ALIASES, lower-cased keys)
core/units.units_equivalent(a, b)           canonical equality; explicitly NO substring test
core/units.split_qualified_unit(unit)       "kWh (Gross CV)" -> ("kWh", "Gross CV"), base normalised
core/units.unit_matches_with_qualifier()    qualifier-aware match used for FACTOR SELECTION
core/units.resolve_unit_for_factor(u, f)    <-- the defective seam (line 212 pre-fix)
services/automatic_processing._calculate_line()
    quantity_unit = resolve_unit_for_factor(line.unit, factor.unit)
domain.factor.EmissionFactor.calculate_emissions(quantity, quantity_unit)
    if self.unit is not None and quantity_unit != self.unit: raise UnitMismatchError
engines/validation.py  CODE_UNIT_MISMATCH = "VAL_UNIT_MISMATCH"   (governed outcome)
```

The engine's guard is an **exact string comparison**, so whatever spelling
`resolve_unit_for_factor` returns is authoritative for the calculation.

## 5. Existing unit taxonomy / family mechanism (reused, not replaced)

The repository already has exactly one vocabulary: the canonical targets of `UNIT_ALIASES`, which
encode the physical families implicitly and completely:

| Family | Canonical units |
| --- | --- |
| volume | `litres`, `cubic metres` |
| mass | `tonnes`, `kilograms`, `grams` |
| energy | `kWh`, `kWh (Gross CV)`, `kWh (Net CV)`, `MWh`, `MJ`, `GJ` |
| distance / freight | `km`, `miles`, `tonne.km`, `passenger.km` |
| spend / currency | `CURRENCY_UNITS` (separate, already handled — no physical factor applies) |

No parallel taxonomy was invented; the fix adds no new vocabulary and no new unit strings.

## 6. Root cause (exact)

```python
# core/units.py, pre-fix line 212 (inside resolve_unit_for_factor)
    if unit in factor_unit_s or factor_unit_s in unit:
        return factor_unit_s
```

A **raw substring containment test on the un-normalised strings**, intended (per the module
docstring) only as a fallback for qualifier-bearing factor units. It fires whenever one unit
spelling happens to occur inside the other:

```text
"t"    in "litres"  -> True   -> returns "litres"   CROSS-FAMILY  (mass -> volume)
"g"    in "kg"      -> True   -> returns "kg"       same family, 1000x magnitude error
"m"    in "km"      -> True   -> returns "km"       same family, 1000x magnitude error
"t"    in "tonnes"  -> True   -> returns "tonnes"   benign (alias; normalisation covers it anyway)
"kwh"  in "litres"  -> False  -> unchanged          (letter coincidence hid the bug)
```

Substring containment is a property of the *letters*, not of the *physical quantity*. Every
legitimate case the fallback was meant to serve is already covered exactly by canonical
normalisation plus the trailing-qualifier rule (available as the proper helper
`split_qualified_unit`).

## 7. Can this affect real calculations?

**YES — the mechanism is proven; whether it has occurred in production is NOT established.**

* The engine's only guard is exact string equality, so a coerced unit **defeats** the
  `UNIT_MISMATCH` check: a quantity measured in `t` could be multiplied by a per-`litres`
  multiplier and returned as a confident emissions figure, while the calculation record carried the
  **factor's** unit instead of the source unit — a silent, unauditable change of physical meaning.
* Demonstrated before the fix (`resolve_unit_for_factor("t","litres") == "litres"`, so
  `calculate_emissions(Decimal("60"), "litres")` proceeded with no exception); after the fix the
  same call raises `UnitMismatchError` (§11).
* Reachability requires factor selection to have paired the row with a factor whose unit string
  contains the source unit as a substring; the selection path
  (`unit_matches_with_qualifier`) normally prevents that pairing — which is the honest reason no
  production incident has been observed. **No production data was inspected**, so a historical
  occurrence is neither claimed nor ruled out.

## 8. Implementation change (smallest generic correction)

`backend/core/units.py::resolve_unit_for_factor` — the substring fallback is **removed** and
replaced with an exact, generic rule:

```python
    if normalize_unit(unit) == normalize_unit(factor_unit_s):
        return factor_unit_s
    unit_base, _ = split_qualified_unit(unit)
    factor_base, _ = split_qualified_unit(factor_unit_s)
    if unit_base and unit_base == factor_base:      # kWh vs kWh (Gross CV)
        return factor_unit_s
    return unit                                     # engine decides (UNIT_MISMATCH)
```

Deliberate design decision (the obvious alternative is *worse*): the fix does **not** adopt the
factor's spelling merely because two units share a physical family. No quantity is converted at this
seam and the factor multiplier is per-unit, so rewriting `litres` → `cubic metres` (or `grams` →
`kilograms`) would mis-scale the quantity by 1000× while looking "compatible". This seam resolves
**spellings**, never **conversions**.

No unit string, activity, factor, file name or row is hard-coded.

## 9. Valid conversion / alias regression results (all preserved)

```text
L        + litres            -> litres            l/ltr/litre + litres -> litres
m3       + cubic metres      -> cubic metres      m³ + cubic metres    -> cubic metres
kwh/KWH  + kWh               -> kWh               MWh + MWh            -> MWh
kg       + kilograms         -> kilograms         t/ton + tonnes       -> tonnes
km       + km                -> km                miles + miles        -> miles
kWh      + "kWh (Gross CV)"  -> "kWh (Gross CV)"  kwh + "kWh (Net CV)" -> "kWh (Net CV)"
litres   + "kWh (Gross CV)"  -> litres            (unchanged, as before)
```

## 10. Invalid cross-family regression results (all now rejected, not coerced)

```text
resolve_unit_for_factor("t",       "litres") -> "t"        (was "litres")
resolve_unit_for_factor("tonnes",  "litres") -> "tonnes"
resolve_unit_for_factor("kg",      "litres") -> "kg"
resolve_unit_for_factor("t",       "kWh")    -> "t"
resolve_unit_for_factor("tonnes",  "kWh")    -> "tonnes"
resolve_unit_for_factor("litres",  "km")     -> "litres"
resolve_unit_for_factor("m3",      "tonnes") -> "m3"
resolve_unit_for_factor("kwh",     "tonnes") -> "kwh"
resolve_unit_for_factor("miles",   "kWh")    -> "miles"
resolve_unit_for_factor("litres",  "cubic metres") -> "litres"   (same family, different unit)
resolve_unit_for_factor("tonnes",  "kilograms")    -> "tonnes"
```

The failure representation is the **existing** contract: the unit is returned unchanged and
`domain.factor.EmissionFactor.calculate_emissions` raises the established `UnitMismatchError`
(surfacing as `VAL_UNIT_MISMATCH`). No new exception model and no new workflow was introduced.

## 11. Calculation safety result

```text
source unit 't', factor unit 'litres'
  resolved unit            -> 't'    (the factor's unit is NOT substituted)
  engine                   -> UnitMismatchError: consumption unit 't' does not match factor
                              unit 'litres' for factor factor-litres
valid control: L + litres  -> 250.000000 kg CO2e   (unchanged behaviour)
```

No silent substitution, no fabricated conversion, no incompatible-factor calculation, and no
falsely compatible unit. The governed outcome for an incompatible pair remains the existing
mismatch/validation path.

## 12. Provenance result

The 026 provenance guarantees are untouched (its code was not modified): the source unit continues
to travel with the row (`line_items[].unit`, `source_line`), and because the resolver no longer
rewrites a unit across families, the calculation record now shows the **source** unit for an
incompatible pair rather than the factor's. A reader can therefore distinguish
"source unit = tonnes" from "factor unit = litres" and see the incompatibility, instead of reading a
fabricated match.

## 13. Multi-line regression result

The five-row oracle's units remain valid: `kwh → kWh`, `l → litres`, `t → tonnes`,
`m³ → cubic metres` all resolve to their same-unit canonical spelling, and the 026 suite
(16 tests) still passes. No row, activity or document special-casing was added.

## 14. Broader regression result

```text
new focused suite  tests/unit/test_units_family_compat.py        35 passed  (new)
existing unit tests test_units.py + test_units_qualifier.py      40 passed  (no change in expectations)
tests/unit/services (extraction, mapping, processing, P1, calc)  passed, 0 failures
tests/unit/engines                                               269 passed, 0 failures
newly failing tests                                              0
pre-existing failures                                            none observed
integration suites                                               NOT run (destructive conftest TRUNCATE, F-046-1)
broad tests/unit                                                 partially observed (no failures in the suites run)
affects existing calculations unexpectedly?                      NO — the only behaviour change is that a
                                                                 unit which is not the same unit (by exact
                                                                 alias/qualifier comparison) is no longer
                                                                 rewritten to the factor's spelling
```

The existing qualifier expectations were explicitly preserved
(`resolve_unit_for_factor("kWh", "kWh (Gross CV)") == "kWh (Gross CV)"`,
`("L","litres") == "litres"`, `("litres","kWh (Gross CV)") == "litres"`,
`("m3","litres") == "m3"`).

## 15. Production state

**No production mutation and no production verification.** No uploads, no jobs created/requeued/
retried/unlocked, no database writes, no schema/rollout/EF-dataset/Render/Vercel/billing changes,
no deployments. Protected job `9ef61662-1c0a-497a-b5e9-c179e2134784` untouched.

## 16. P1 state

**`shadow`, unchanged.** No rollout, allowlist or environment change; the fix touches a unit
resolution seam only and does not alter extraction shape behaviour.

## 17. Git commits

| Commit | Content |
| --- | --- |
| *(fix)* | `backend/core/units.py` — remove the substring fallback, add the exact alias/qualifier rule |
| *(tests)* | `backend/tests/unit/test_units_family_compat.py` — 35 regression tests |
| *(report)* | this file |

Pushed to `origin/p8-release-reconciled`; exact SHAs are reported in the completion response.

## 18. Final verdict

### `PASS — FIX IMPLEMENTED`

The cross-family coercion is confirmed as a genuine calculation-safety defect (the substring
fallback defeated the engine's exact-match `UNIT_MISMATCH` guard and could substitute the factor's
unit for the source unit), it is corrected generically at the unit-family/alias level with no
hard-coding, every documented alias/qualifier behaviour is preserved, and the invalid cross-family
cases are now rejected through the existing governed path with the source unit retained.

## 19. Remaining limitations

1. **Historical exposure not assessed** — no production calculation records were inspected, so
   whether any stored calculation used a coerced unit is unknown. A targeted audit (search stored
   calculation inputs for units that are not aliases of their factor's unit) is proposed below.
2. **No 1000×-magnitude regression case in the code** — the same-family substring cases
   (`"g" in "kg"`, `"m" in "km"`) are now also impossible at this seam, but they were only
   *reachable* when a factor with exactly that unit string was selected; this was proven by
   inspection, not by an end-to-end document run.
3. **Broader `tests/unit` was only partially observed** in the time available (the suites run for
   this task — units, services, engines — all passed).
4. Conversions themselves (kWh↔MWh, litres↔m³, kg↔tonnes, miles↔km quantity conversion) are **out of
   scope** here and remain unimplemented at this seam: the platform continues to require the source
   quantity to be expressed in the factor's unit, which is now enforced honestly instead of being
   faked.

## 20. Next PO gate

1. **Accept the fix** (`PASS — FIX IMPLEMENTED`) and keep P1 in `shadow`.
2. Optional but recommended: authorise a **read-only audit** of stored calculation inputs for
   unit/factor pairs that are not exact aliases — this bounds any historical exposure created before
   this fix. It requires a database read, so it needs its own authorisation.
3. If same-family *conversion* (e.g. `L` entered against a `cubic metres` factor) is a required
   product capability, that is a **new feature decision** (conversion factors + provenance for the
   conversion), not part of this bounded fix.
4. Production verification of this fix is not required for correctness of the change but, if wanted,
   follows the 025 pattern (fresh synthetic execution) as a separate bounded task.


