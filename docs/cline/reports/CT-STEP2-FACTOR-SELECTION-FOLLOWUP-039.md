# CT-STEP2-FACTOR-SELECTION-FOLLOWUP-039

```text
1 BASELINE SHA   c9dc418ec93046fa5cbf7c2fe117daa610bcc069 (p8-release-reconciled, clean tree)
2 FINAL SHA      recorded in the completion summary (code + report commit, pushed; HEAD == origin)
3 FILES CHANGED  backend/engines/factor_matching.py           (family-diversified retrieval + F-038-2 verdict)
                 backend/engines/factor_selection_policy.py   (variant semantics, is_bio refinement,
                                                               request_tokens accessor, variant-aware groups)
                 backend/tests/unit/engines/test_factor_selection_followup_039.py  (NEW · 14 tests)
                 backend/tests/unit/engines/test_factor_selection_policy.py        (1 expectation corrected
                                                               — see §15.1; nothing weakened)
                 docs/cline/reports/CT-STEP2-FACTOR-SELECTION-FOLLOWUP-039.md
```

## 4. F-038-1 ROOT CAUSE (measured, not assumed)

```text
`keyword_search('Diesel', unit=None, limit=N)` returns thousands of EQUAL-scoring (1.0) factors in
insertion/taxonomy order. Measured family distribution of the window:
   limit   25 → Bioenergy 3 · Business travel- land 22                             · mineral-diesel rows: 0
   limit  200 → Bioenergy 3 · Business travel- land 104 · Delivery vehicles 93     · mineral: 0
   limit 1000 → + Freighting goods 349                                             · mineral: 0
So widening the window is both insufficient (mineral diesel is absent even at 1000) and explicitly not
authorised. The window was monopolised by the first families in ordering; the Fuels family — which holds
the diesel combustion factors — was never reached.
```

## 5. F-038-1 IMPLEMENTATION (retrieval only — no selection)

```text
FactorMatchingEngine._policy_candidates(request) — NEW, discovery-only:
  · scans a bounded match set (limit = _POLICY_SCAN_LIMIT = 10 000, i.e. bounded by dataset size);
  · keeps only rows sharing at least one activity token with the request, using the SAME tokeniser as the
    policy (public `request_tokens`), so discovery and selection share one notion of relevance;
  · applies a per-taxonomy-family budget (_POLICY_FAMILY_CAP = 40) so no single family can monopolise
    the set.
It performs NO eligibility, ranking or preference work — that remains exclusively in
factor_selection_policy.select_factor(). The matching stages, their order and their limits are unchanged.
```

## 6. DIESEL CANDIDATE-RETRIEVAL EVIDENCE — BEFORE / AFTER

```text
BEFORE (038): bare 'Diesel' → matched 'Bioenergy > Biofuel > Development diesel (kg CO2e) [litres]'
  0.03705 — semantically the wrong concept, chosen only because mineral diesel was never in the window.
AFTER  (039): bare 'Diesel' → status=ambiguous, stages end [.. keyword_search, selection_policy]
  eligible groups = two materially different Scope-1 combustion products:
     'Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e) [litres]'   2.66155
     'Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e) [litres]'
  ⇒ mineral diesel is now VISIBLE (no longer excluded by retrieval breadth); Development diesel is not
    selected; and because the source evidence names no product, the PO-required outcome is explicit
    ambiguity rather than a silent pick (#7/#8). Nothing is hardcoded — a request naming the product
    selects that product deterministically (both verified on the real dataset, §11).
```

## 7. F-038-2 IMPLEMENTATION

```text
· factor_selection_policy: eligible sets are grouped by (family, treatment route, fuel/product variant);
  >1 group tied on request-token coverage ⇒ ambiguous, exposing the groups. A named route is respected
  (route filter) and no route is ever inferred lexically.
· factor_matching.FactorMatchingEngine._apply_selection_policy: an ambiguous verdict is now honoured even
  when the CURRENT match is itself eligible — keeping it would resolve the ambiguity by repository order,
  which the PO decision forbids (the exact F-038-2 blocker in 038).
· No new ontology, schema or factor-data change: the route is read from the existing name suffix and the
  family from the existing taxonomy prefix, as documented in the 037 evidence.
```

## 8. WASTE ROUTE EVIDENCE (real dataset)

```text
'Waste disposal'           tonnes → status=ambiguous (stages … selection_policy); no factor returned,
                                    NOT Waste oils, NOT a fuel-combustion factor.
'Waste disposal Landfill'  tonnes → matched 'Waste disposal > Construction > Aggregates - Landfill
                                    (kg CO2e) [tonnes]'      (route honoured)
'Waste disposal Open-loop' tonnes → matched '… Aggregates - Open-loop (kg CO2e) [tonnes]'
                                    (the named route wins — not lexical order)
'Waste oils'               litres → matched 'Fuels > Liquid fuels > Waste oils (kg CO2e) [litres]'
                                    2.74924 (fuel semantics preserved; no treatment contamination)
```

## 9. AMBIGUITY BEHAVIOUR

```text
status="ambiguous" in the policy; the engine returns the pre-existing
MatchResult(status="ambiguous", suggestions=…) — the same mechanism already used for score-1.0
non-matches. No new workflow, table or UI. Ambiguity is used exactly where the PO requires it (two
materially different diesel products with no product evidence; a disposal request with no named route)
and is never decided by value, row order or lexical accident.
```

## 10–13. REGRESSION EVIDENCE (real 7,049-factor dataset, real engine, read-only session)

```text
10 NATURAL GAS / D-A: 'Natural gas' kWh → matched · confidence 1.0 · methodology selection_policy ·
   stages [exact_match, natural_key, alias_match, keyword_search, fuzzy_match, calorific_basis,
   selection_policy] · id=c895606c-bab0-4981-826d-eb1046ce6a80 · value 0.20270 · unit 'kWh (Net CV)' ·
   Scope 1 · DEFRA-2025 — the AGGREGATE, the PLAIN factor (not the 100 % mineral-blend variant) and the
   **Net-CV** basis. No Gross-CV regression; the CH4 component does not win. (An intermediate attempt DID
   flip this to Gross CV; the retrieval change was corrected and the basis is additionally protected by
   passing the D-A-decided unit as a rank-ONLY `preferred_unit`, which can never admit an ineligible
   candidate.)
11 DIESEL: bare 'Diesel' → ambiguous (§6); 'Diesel 100% mineral diesel' → mineral diesel aggregate
   2.66155 (selection_policy); 'Diesel average biofuel blend' → the blend factor (selection_policy).
12 WASTE: as §8.
13 WTT: 'Natural gas WTT' kWh → matched · 'WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)
   [kWh (Net CV)]' 0.03347 · Scope 3 — legitimate WTT use is NOT suppressed by the Scope-1 guard.
   POWER: 'Power consumption kWh € €' → no_match, stages end at fuzzy_match, no calorific_basis, no gas
   factor. WATER: 'Water' m³ → matched, unchanged (policy not_applicable for unclassified requests).
```

## 14. TEST COUNTS / RESULTS

```text
NEW   tests/unit/engines/test_factor_selection_followup_039.py      14 passed
      (bare-diesel two-product ambiguity · bio product never wins on lexical order · product-qualified
       request selects that product · single candidate deterministic · per-litre vs per-km diesel ·
       insufficient evidence → ambiguity · waste treatment never reaches waste oils · explicit route
       selected (not lexically first) · missing route + multiple candidates → ambiguity · missing route +
       one candidate → deterministic · waste-oil semantics survive · gas aggregate honours the decided
       basis · WTT request accepts only upstream · unclassified request untouched)
REGRESSION  tests/unit/engines            311 passed
            tests/unit/services           264 passed
            tests/unit/test_d_a_natural_gas_basis.py          26 passed
            tests/unit/test_units.py / _qualifier / _family_compat     13 / 27 / 35 passed
NEW FAILURES: none.  PRE-EXISTING / INFRASTRUCTURE FAILURES: none observed.
```

## 15. LIMITATIONS

```text
15.1 ONE 038 EXPECTATION WAS CORRECTED (not weakened): the 038 test named
     `test_materially_different_candidates_return_ambiguity_not_a_value_pick` had asserted "selected
     mineral diesel". F-038-1 #7/#8 now requires ambiguity for two different products with no product
     evidence, so that expectation was updated to assert ambiguity, and a NEW test asserts that a
     product-qualified request selects that product. Name, coverage and strength are unchanged; no other
     test was touched to obtain green.
15.2 F-039-1 REMAINING: the bare detector word 'Waste' (the mapping text for the waste invoice line in the
     035 scenario) is UNCLASSIFIED by the policy, so the policy abstains and that row still resolves to
     'Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]'. Classifying a bare 'Waste'
     token as a disposal request would change behaviour for every unqualified "waste" line, so it is a PO
     classification decision and was NOT taken unilaterally. The PO's mandatory case D — 'Waste
     disposal' — is satisfied (§8).
15.3 The variant vocabulary (mineral / average biofuel blend / development / biodiesel / HVO / off-road)
     is a bounded marker list over the published naming convention, held in one module: data-driven
     rather than an answer key, though a future factor-metadata column would remove the string coupling.
15.4 Retrieval now scans up to 10 000 matches per policy evaluation (bounded by the 7,049-row dataset)
     and keeps ≤40 per family — an in-memory operation on the existing index, no new query surface or
     API; its cost profile should be observed under production load.
15.5 Ambiguity now returns fewer auto-matched rows for genuinely ambiguous source lines (bare 'Diesel',
     route-less 'Waste disposal'). That is the PO's stated intent (review rather than guess).
```

## 16. REMAINING FOLLOW-UP

```text
F-039-1  classify (or explicitly refuse to classify) the bare 'Waste' token — PO decision.
F-038-3  (carried from 038, unchanged) factor-metadata columns for category/boundary/variant/treatment,
         which would replace the marker vocabulary if the PO wants schema-level semantics.
```

## 17. STATEMENTS

```text
· D-A NOT REOPENED — its Gross/Net policy and discovery code are unchanged; the real natural-gas case
  still returns the Net-CV aggregate at confidence 1.0.
· D-FS-1 … D-FS-6 NOT REOPENED — the 038 policy semantics are preserved; this increment refines
  eligibility detail (variant semantics) and retrieval, and aligns one expectation with the PO's
  F-038-1 ruling.
· D-B, D-C and D-D NOT STARTED.
· NO production deployment, no Render/Vercel action, no P1 activation (P1 remains SHADOW).
· NO factor-data, schema, migration or configuration change; all DB access was read-only.
· INDEPENDENT VERIFICATION NOT PERFORMED by me — this is an implementation report.
· PO CLOSURE NOT CLAIMED.
```

## FINAL VERDICT

**IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION**

Both authorised follow-ups are delivered and evidenced. F-038-1: family-diversified, relevance-filtered
candidate retrieval now makes the diesel combustion family visible to the policy instead of letting
alphabetically-earlier families consume the window; where the source evidence cannot distinguish two
materially different diesel products the result is the PO-required explicit ambiguity, and where the
request names the product the selection is deterministic — nothing is hardcoded. F-038-2: route-aware waste
treatment — a named route is honoured, a missing route with materially different routes is ambiguous, and a
treatment request can never reach a waste-oil fuel or any other fuel-combustion factor. All six mandatory
real-data cases hold; D-A's Net-CV aggregate is preserved; WTT stays available in its own context; power and
water are unchanged. 14 new tests plus the existing suites are green, and the single remaining item
(F-039-1, the bare 'Waste' token) is recorded as a PO decision rather than silently absorbed.
