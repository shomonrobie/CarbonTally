# CT-STEP2-FACTOR-SELECTION-POLICY-IMPLEMENTATION-038

**Scope executed:** the narrowly bounded PO-authorised increment implementing **D-FS-1 … D-FS-6**. No D-A
reopening, no D-B/C/D, no new factor DB/engine, no AI, no unrelated refactor, no schema change, no
factor-data change, no deployment, no P1 activation.

```text
1  BASELINE SHA        5da7a33b084716a46d3f1cbe056e450938b241a1 (p8-release-reconciled, tree clean)
2  FINAL SHA           recorded in §21 (commit + push; tree clean)
3  FILES CHANGED        backend/engines/factor_selection_policy.py              (NEW · the single policy)
                        backend/engines/factor_matching.py                      (import + boundary hook)
                        backend/services/automatic_processing.py                (_prefer_aggregate_factor
                                                                                 now DELEGATES)
                        backend/tests/unit/engines/test_factor_selection_policy.py (NEW · 18 tests)
                        docs/cline/reports/CT-STEP2-FACTOR-SELECTION-POLICY-IMPLEMENTATION-038.md
4  IMPLEMENTATION LOCATION
   · the DECISION lives in engines/factor_selection_policy.py::select_factor(...) — pure, deterministic,
     no I/O, no DB, no model calls;
   · it is APPLIED at the factor-selection boundary in FactorMatchingEngine
     (``_apply_selection_policy``): the semantic decision is explicit where the match is created;
   · the legacy service hook (``_prefer_aggregate_factor``) no longer decides anything itself — it calls
     the same module, so there is ONE implementation and no competing logic.
```

## 5–10. D-FS IMPLEMENTATION BEHAVIOUR

```text
D-FS-1 AGGREGATE VS COMPONENT
  The four name markers ("of CH4/CO2/N2O/CO2e per unit") define the component class. When an aggregate
  exists inside the same eligible context, components are removed from the eligible set, so a component
  can never win on text similarity alone. A component that is the ONLY eligible candidate is retained
  (no fabrication). Real-data evidence: the natural-gas case now returns the aggregate 0.20489, not CH4.

D-FS-2 COMBUSTION vs WTT  (semantic ELIGIBILITY, not a score)
  An upstream factor (``WTT-`` / well-to-tank prefix) is EXCLUDED from every non-upstream request, and an
  upstream request is satisfied only by upstream factors. The test is the boundary marker, not text
  similarity, so WTT cannot survive into a Scope-1 combustion set. Real evidence: 'Natural gas' excludes
  the 0.03347 WTT factor; 'Natural gas WTT' selects it (Scope 3).

D-FS-3 SCOPE AS SEMANTIC DIMENSION
  If the caller supplies a scope, any candidate whose stored scope differs is EXCLUDED (a real filter, not
  an annotation). When no scope is supplied, a fuel/energy request excludes 'Scope 3' and 'Outside of
  Scopes' candidates — the evidence-backed signal separating combustion from upstream/travel factors.
  (The service currently passes no scope, so the rule is conservative; a supplied scope is authoritative.)

D-FS-4 WASTE / WASTE OILS / TREATMENT
  The token "waste" is explicitly NOT treated as evidence. Requests are separated by markers: a waste
  TREATMENT request (disposal/treatment/landfill/recycl/compost/incinerat/energy recovery/anaerob)
  excludes every 'Fuels…'/'Bioenergy…' candidate (killing the Waste-oils contamination) and restricts
  eligibility to the disposal/material-use taxonomy; a waste FUEL request ('waste oils') excludes the
  disposal taxonomy and requires a waste-derived fuel candidate. A named treatment route is required of
  the candidate. No route named + several routes remaining → ambiguity; no route is fabricated.

D-FS-5 MULTIPLE MATERIALLY DIFFERENT VALID CANDIDATES
  After the mandatory filters, candidates tied on request-token COVERAGE that sit in different semantic
  groups (family, treatment route) produce status "ambiguous" — never a pick by numeric magnitude, row
  order or lexical accident. At the boundary this maps to the EXISTING
  MatchResult(status="ambiguous", suggestions=…) mechanism (already used by the engine for score-1.0
  non-matches); no new workflow or UI surface was invented.

D-FS-6 DETERMINISTIC HIERARCHY
  (1) activity semantics → eligibility filters; (2) scope compatibility; (3) boundary/purpose
  (upstream vs combustion); (4) methodology/treatment compatibility; (5) factor set, (6) reporting year
  and (7) geography are inherited from the index query/context and never re-derived from text; (8) unit
  compatibility is a hard filter; (9) calorific basis is owned by the closed D-A policy and only RANKS
  (``preferred_unit``) — it can never admit an ineligible candidate; (10) aggregate over component;
  (11) specificity (token coverage, then fewest excess qualifiers); (12) stable id ordering purely as the
  reproducibility tie-break. No lower level can override a higher-level incompatibility: steps 1–4 are
  exclusions and only 10–12 rank what survived.
```

## 11. CANDIDATE-SELECTION FLOW — BEFORE / AFTER

```text
BEFORE: keyword_search(activity, unit=request.unit, …) → first matching stage wins → the service may swap
        a component for the first non-component candidate returned by find_by_activity() → result.
        Cross-concept selection (WTT / waste-oils / biofuel diesel) was reachable; ordering decided ties.

AFTER : identical stages and ordering, then at the boundary:
        keyword_search(activity, unit=None, …) → [current match] ∪ candidates
        → select_factor(candidates, activity, unit, scope, preferred_unit) →
             selected  → adopt the deterministic winner (confidence 1.0, methodology "selection_policy")
                         ONLY IF the current factor was excluded/outranked;
             ambiguous → downgrade to MatchResult(status="ambiguous", suggestions=…) when the current
                         factor is itself not in the eligible set;
             no_eligible_candidate / not_applicable → leave the existing match untouched.
        The service hook applies the same verdict and never re-orders or fabricates a candidate.
```

## 12–17. REAL 7,049-FACTOR REGRESSION EVIDENCE (read-only, real engine + real dataset)

```text
=== A NATURAL GAS (Gas usage 5362.2 kWh → activity 'Natural gas', unit kWh) ===  ✅
   status=matched confidence=1.0 methodology=selection_policy
   stages=[exact_match, natural_key, alias_match, keyword_search, fuzzy_match, calorific_basis,
           selection_policy]
   id=542fd52c-3717-4102-8e5e-49b958198736 value=0.20489 unit='kWh (Net CV)' scope=Scope 1
   name='Fuels > Gaseous fuels > Natural gas (100% mineral blend) (kg CO2e) [kWh (Net CV)]'
   set=DEFRA-2025 source=DEFRA-DESNZ country=GB year=2025
   ⇒ Net-CV basis (D-A honoured), AGGREGATE (not CH4), Scope 1, DEFRA-2025.

=== B POWER CONSUMPTION (24620.5 kWh) ===  ✅ no change from D-A
   status=no_match confidence=0.0 · stages end at fuzzy_match (no calorific_basis, no selection_policy)
   factor=NONE ⇒ no redirection to CNG/natural gas; no calorific-basis gas selection.

=== C DIESEL SUPPLY (4434.4 L) ===  ⚠ POLICY DID NOT CORRECT
   status=matched confidence=1.0 methodology=keyword_search
   id=c3afa542-1daf-419c-88ea-94252d4dba18 value=0.03705 unit='litres' scope=Scope 1
   name='Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]'
   ⇒ still the BIOFUEL/development concept, not mineral diesel (2.66155). Root cause: the policy can only
     judge the candidates the index window returns for the activity string 'Diesel', and that window
     contains no non-bio diesel candidate, so there is nothing for the non-bio preference to prefer.
     WTT was correctly excluded and no Scope-3 factor was admitted. This is follow-up F-038-1.

=== D WASTE DISPOSAL (60 t) ===  ✅ family correct · ⚠ route chosen without an authorized rule
   status=matched confidence=1.0 methodology=keyword_search
   id=bc48f31d-bad0-4498-9699-a2ea25ae70b7 value=1.00835 unit='tonnes' scope=Scope 3
   name='Waste disposal > Construction > Aggregates - Closed-loop (kg CO2e) [tonnes]'
   ⇒ NOT redirected to a Scope-1 waste-oil fuel (the D-FS-4 objective holds). Because the current factor
     is already inside the eligible disposal set, the policy does not intervene, so the route
     (Closed-loop) came from the keyword stage rather than from an authorized rule → follow-up F-038-2.
   (Note: with the shorter activity text 'Waste' the keyword stage previously reached Waste oils
     — the request-class exclusion now blocks that path, which is the D-FS-4 fix.)

=== E WASTE OILS (fuel request) ===  ✅
   status=matched confidence=1.0 methodology=selection_policy
   id=cd53db21-2dc4-4fd3-a547-ae23cae6fda8 value=2.74924 unit='litres' scope=Scope 1
   name='Fuels > Liquid fuels > Waste oils (kg CO2e) [litres]'
   ⇒ waste-derived FUEL semantics preserved; no treatment-family candidate contaminated the set.

=== F WTT FUEL CASE ===  ✅ WTT remains available in its own context
   activity='Natural gas WTT', unit kWh
   status=matched confidence=1.0 methodology=calorific_basis
   value=0.03347 unit='kWh (Net CV)' scope=Scope 3
   name='WTT- fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]'
   ⇒ the Scope-1 combustion guard does NOT globally suppress legitimate WTT use.

=== G CONTROL: WATER ('Water', m³) ===  ✅ untouched
   status=matched confidence=1.0 methodology=keyword_search (policy not_applicable — unclassified request)
   value=0.1913 name='Water supply > Water supply > Water supply (kg CO2e) [cubic metres]'
```

## 17. AMBIGUITY BEHAVIOUR

```text
Unit-level: two materially different candidates with equal coverage in different groups → status
"ambiguous"; both disposals routes in the focused test demonstrate it, and the selection is never made by
value, row order or lexical accident. Boundary-level: an ambiguous verdict downgrades only when the
CURRENT match is itself ineligible (so a legitimate match is never destroyed); otherwise the existing
match is preserved. The mechanism reused is the engine's pre-existing ambiguous/suggestions result.
```

## 18. TEST COUNTS AND RESULTS

```text
NEW   tests/unit/engines/test_factor_selection_policy.py          18 passed
      (aggregate vs CH4 / CO2 / N2O · component-only fallback · WTT ineligible for combustion · WTT
       request satisfied only by upstream · scope-mismatch exclusion · waste-treatment not redirected to
       waste-oil fuel · treatment route respected · waste-oil fuel not contaminated by treatment ·
       specific-not-numeric pick · stable identifier tie-break · unrelated concept cannot win · engine
       aggregate selection · engine waste downgrade · D-A Gross/Net regression · factor-set context ·
       pipeline structure & P1 shadow unchanged)
REGRESSION  tests/unit/engines                296 passed
            tests/unit/services               264 passed
            tests/unit/test_d_a_natural_gas_basis.py        26 passed
            tests/unit/engines/test_d_a_natural_gas_discovery.py  9 passed
            tests/unit/test_units.py                         13 passed
            tests/unit/test_units_qualifier.py               27 passed
            tests/unit/test_units_family_compat.py           35 passed
NEW FAILURES: none.  PRE-EXISTING/INFRASTRUCTURE FAILURES: none observed.
No existing test was modified to obtain green.

## 19. LIMITATIONS / CASES REQUIRING A FUTURE BOUNDED DECISION

```text
F-038-1 (case C) — RETRIEVAL BREADTH FOR GENERIC FUEL ACTIVITIES. The policy's verdict is only as good as
  the candidate window it receives. For the bare activity 'Diesel' the window holds bio/development diesel
  rows and no mineral-diesel candidate, so the non-bio preference has nothing to prefer. MEASURED: raising
  the window from 25 to 60 did NOT bring mineral diesel in — and it DID change the natural-gas outcome
  from Net CV to Gross CV (because the basis is only a rank input, not an eligibility rule), i.e. a
  D-A regression risk. The window was therefore REVERTED to 25 and the basis was additionally protected by
  passing ``preferred_unit`` (the D-A-decided unit) into the ranking. A correct fix needs a bounded
  decision about retrieval scope for generic fuel names (e.g. a unit/quantity-typed widening), with its
  own authorization and its own oracle — it is NOT a safe silent tweak.

F-038-2 (case D) — ROUTE-ABSENT DISPOSAL AMBIGUITY. When a disposal activity names no treatment route, the
  policy would return ambiguous if several routes were visible, but when the keyword stage already lands
  inside the eligible disposal family the policy leaves that match in place (by design: never destroy a
  legitimate match). The route is then a keyword-stage accident rather than an authorized rule. A bounded
  follow-up is to make route ambiguity explicit *inside* the eligible family (e.g. require route evidence
  or emit ambiguous), which is a policy choice for the PO.

Not attempted, by instruction: no schema/metadata columns, no factor-data edits, no new search API, no
  engine redesign, no D-B/C/D, no AI.

## 20. STATEMENT

**No D-B, D-C or D-D work was started.** D-A was not reopened and its calorific-basis policy is unchanged
(its decision is now additionally protected as a rank input). No schema, migration, factor-data,
deployment or P1 change was made; P1 remains SHADOW.

## 21. GIT / RELEASE CONTROL

```text
BASELINE    5da7a33b084716a46d3f1cbe056e450938b241a1 (verified: branch p8-release-reconciled, clean tree)
FINAL SHA   recorded in the completion summary (code commit + this report commit, both pushed; local HEAD
            == origin/p8-release-reconciled; working tree clean). main untouched; no rebase/reset/pull.
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

Delivered and verified: D-FS-1 (aggregate defeats the CH4 component on real data), D-FS-2 (WTT excluded
from combustion, still available for upstream requests), D-FS-3 (scope as an eligibility filter when
supplied, plus the combustion-scope rule), D-FS-4 (waste-treatment requests no longer reach a waste-oil
fuel; waste-fuel requests keep their own semantics), D-FS-5 (ambiguity surface instead of a value/order
pick, via the pre-existing ambiguous mechanism), D-FS-6 (the full deterministic precedence with the
identifier tie-break last), the case-A/B/E/F/control real-data results, 18 new focused tests, and the
regression suites — all green, no test modified for green.

Not delivered: the two evidence-grounded gaps **F-038-1** (candidate-window breadth for a bare 'Diesel'
activity — case C still selects the biofuel/development concept) and **F-038-2** (route-absent disposal
still inherits the route from the keyword stage — case D is family-correct but not route-authorized).
Neither can be closed inside this increment without either a retrieval-scope decision (which measurably
perturbs D-A basis selection when widened naively) or a PO route-ambiguity ruling. Both are recorded
rather than silently patched.

**Not PO-closed. Not independently verified by me.**
