# CT-STEP2-D-A-NATURAL-GAS-VERIFY-035 — INDEPENDENT VERIFICATION

**Role:** Cline acting as INDEPENDENT VERIFIER. **Verification-only window** — no application code, tests,
configuration, schema, migration or factor data was created, modified or deleted; nothing was deployed;
P1 is untouched and remains SHADOW; production was not accessed.

```text
VERIFICATION TARGET   89c02db591e5186462a1913a75ccbe76f96cb506  (D-A delivery)
ACTUAL HEAD           89c02db591e5186462a1913a75ccbe76f96cb506  (identical to target)
BRANCH                p8-release-reconciled
ORIGIN                origin/p8-release-reconciled = 89c02db…506
                      git ls-remote origin refs/heads/p8-release-reconciled = 89c02db…506
TARGET IN HISTORY     yes (git merge-base --is-ancestor 89c02db HEAD → true)
WORKING TREE          CLEAN (git status --porcelain → empty; git diff --stat HEAD → empty)
                      ⇒ the code under test IS the committed, pushed, published artefact.
D-A COMMITS PRESENT   46a5534 policy core · 466eb93 engine discovery · b0ac3fe gas gate
                      · 89c02db report   (all ancestors of HEAD, all on origin)
```

**Method.** Behaviour was reproduced, not read from the implementer's report. A separate scratch harness
(`/tmp/v35_verify.py`, outside the repository) drove the REAL `FactorMatchingEngine` over the REAL
authoritative local factor dataset loaded through `EmissionFactorsRepository.load_all_for_index()`; no
factor record was mocked. The database session was forced read-only
(`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`), so no write was possible.

## 1. Implementation integrity (inspected at the target SHA)

```text
pipeline structure      MatchingPipelineConfig.stages = ('exact_match', 'natural_key', 'alias_match',
                        'keyword_search', 'fuzzy_match') — UNCHANGED. build_matching_pipeline's
                        `builders` dict still offers exactly the 6 pre-existing stage names; the D-A
                        commits add NO stage class and edit NO config stage list.
new search API          none — `grep -c 'def .*search'` in factor_matching.py = 0; discovery reuses the
                        pre-existing index.keyword_search(...).
parallel unit system    none — unit_matches_with_qualifier exists once (core/units.py) and is referenced
                        only by pre-existing code/tests; it was NOT modified in 034 (confirmed by the
                        grep of the committed tree).
resolution protection   core/units.py::resolve_unit_for_factor retains the 46a5534 qualifier rule
                        (verified verbatim in the committed blob).
containment (5 gates)   (1) request unit must be UNQUALIFIED  (2) base unit present
                        (3) request activity must name a gas  (4) candidate base unit must equal the
                        request base unit  (5) select_basis_factor fires only with >1 distinct
                        qualifier of one base unit.
factor-set context      preserved — the selected factor carries country/factor_set/provider/year; the
                        discovery never infers jurisdiction from the activity name.
```

Implementation matches the reported design. **No divergence found.**

## 2. CRITICAL discovery test — real dataset, real engine

```text
Dataset loaded: 7049 authoritative factors
  (NOTE: the brief states 7,029 — the environment actually loads 7,049; recorded as an inventory
   discrepancy, not a D-A defect.)
Candidate inventory visible to the real index for the natural-gas query:
  three distinct units present → 'kWh', 'kWh (Gross CV)', 'kWh (Net CV)'
  Gross side: 0.18494 (aggregate) · 0.18457 (CO2) · 0.00028 (CH4) · 0.00009 (N2O) · WTT 0.03021
  Net   side: 0.20489 · 0.2027 (aggregates) · 0.20229 (CO2) · 0.00031 (CH4) · 0.0001 (N2O) · WTT 0.03347

REQUEST: activity='Natural gas' | unit='kWh' | country='GB' | year=2025 | provider=DEFRA-DESNZ
RESULT : status=matched | confidence=1.0 | methodology=calorific_basis
         stages_executed = exact_match · natural_key · alias_match · keyword_search · fuzzy_match
                           · calorific_basis
         ⇐ requirement satisfied: kWh → qualified candidates discovered → basis policy applied
           → Net CV selected → matched → confidence 1.0
```

## 3. Row-1 oracle evidence (five-row scenario, row 1 = D-A acceptance)

```text
ROW 1  'Gas usage 5,362.2000 kWh €0.0670 €359.2700'   (real detector → real matcher → real EF)
  extracted activity   : Natural gas
  quantity / unit      : 5362.2  |  source 'kwh' → normalised 'kWh'  (basis unqualified)
  match status         : matched | confidence 1.000
  SELECTED FACTOR ID   : 2aa65183-eb28-4640-a529-15f18360dc5a
  FACTOR NAME          : Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit) [kWh (Net CV)]
  FACTOR VALUE         : 0.00031
  FACTOR UNIT / BASIS  : 'kWh (Net CV)'  → Net CV  (unqualified → Net default)
  REPORTING YEAR       : 2025
  SCOPE                : Scope 1
  PROVIDER / SOURCE    : DEFRA-DESNZ
  FACTOR SET           : DEFRA-2025
  COUNTRY              : GB
  027 unit resolution  : 'kWh' + 'kWh (Net CV)' → 'kWh (Net CV)'   (no basis rewrite, no conversion)
  arithmetic (oracle)  : 5362.2 × 0.00031 = 1.662282 kg CO2e   (nothing persisted)
```

## 4. False-positive containment — INDEPENDENTLY VERIFIED

```text
REQUEST: activity='Power consumption kWh € €' | unit='kWh' | country='GB' | year=2025
RESULT : status=no_match | confidence=0.0 | methodology='' (none)
         stages_executed = exact_match · natural_key · alias_match · keyword_search · fuzzy_match
                           (NO calorific_basis stage)
         selected factor : NONE
         gas/CNG factor returned: False
⇐ the 24,620.5 kWh 'Power consumption' row does NOT enter the natural-gas calorific-basis recovery and
  no natural-gas/CNG factor is returned.  Containment regression PASSES.
  (Row 5's own policy — D-B electricity — is out of scope and was neither implemented nor expected here.)
```

## 5. Gross / Net safety — INDEPENDENTLY VERIFIED

```text
resolve_unit_for_factor / normalize_unit (actual observed behaviour)
  'kWh'            + 'kWh (Gross CV)' → 'kWh (Gross CV)'   (unqualified may adopt a qualified spelling)
  'kWh'            + 'kWh (Net CV)'   → 'kWh (Net CV)'
  'kWh (Gross CV)' + 'kWh (Net CV)'   → 'kWh (Gross CV)'   ⇐ GROSS NOT REWRITTEN INTO NET
  'kWh (Net CV)'   + 'kWh (Gross CV)' → 'kWh (Net CV)'     ⇐ NET NOT REWRITTEN INTO GROSS
  'kWh (Gross CV)' + 'kWh (Gross CV)' → 'kWh (Gross CV)'
  'litres'         + 'kWh (Net CV)'   → 'litres'           (cross-family untouched)
  'litres' + 'L' → 'L'  ·  'tonnes' + 't' → 't'            (027 spelling canonicalisation intact)
DEFAULT_CALORIFIC_BASIS = 'net'

End-to-end policy through the REAL engine:
  'Natural gas'          → kWh (Net CV)   conf 1.0  (source_basis=None → Net default)
  'Natural gas Gross CV' → kWh (Gross CV) conf 1.0  (source_basis='gross')
  'Natural gas GCV'      → kWh (Gross CV) conf 1.0  (source_basis='gross')
  'Natural gas Net CV'   → kWh (Net CV)   conf 1.0  (source_basis='net')
  'Natural gas NCV'      → kWh (Net CV)   conf 1.0  (source_basis='net')
⇐ Gross→Gross, Net→Net, unqualified→Net all reproduced; Gross/Net never silently interchanged.
```

## 6. Enumeration-order safety — INDEPENDENTLY VERIFIED (selector level)

```text
select_basis_factor over the REAL candidate list from the authoritative dataset:
  unqualified  forward → 2330c084-7ffc-44d4-8406-aaa7b871de59 (kWh (Net CV))
               reversed → 2330c084-7ffc-44d4-8406-aaa7b871de59   → identical = True
  explicit gross forward → 01e9e367-4572-4f91-b348-fb85a0587508 (kWh (Gross CV))
               reversed → 01e9e367-4572-4f91-b348-fb85a0587508   → identical = True
⇐ ordering of the candidate collection does not change the selection.
  LIMITATION: order was reversed in the in-memory candidate collection; the database row order was NOT
  mutated (no persistent factor data may be changed by a verification window).
```

## 7. Factor-set regression and SEAI observation

```text
Fresh unqualified requests (country=GB, year=2025) — jurisdiction context retained, not inferred:
  'Natural gas'  'kWh'          matched 1.0  method=calorific_basis  set=DEFRA-2025 country=GB year=2025
  'Diesel'       'litres'       matched 1.0  method=keyword_search   set=DEFRA-2025 country=GB year=2025
  'Waste'        'tonnes'       matched 1.0  method=keyword_search   set=DEFRA-2025 country=GB year=2025
  'Water'        'cubic metres' matched 1.0  method=keyword_search   set=DEFRA-2025 country=GB year=2025
⇐ rows 2-4 still resolve through the pre-existing stages (D-A inert), and the D-A path retains
  country/provider/factor set/year. 031 factor-set context is not bypassed.

SEAI (observation, unchanged by D-A — nothing altered):
  SEAI natural-gas factors in dataset: 1
    'Fuels > Gaseous fuels > Natural gas (NCV) (kg CO2) [cubic metres]' unit='cubic metres'
      value=2.005357 set=SEAI-2025 year=2025
  SEAI-style request 'Natural gas (NCV)' + 'cubic metres' → status=no_match, confidence 0.0, no factor.
  Reasoning that D-A did not cause this: the discovery path can only ADD a match; this request returned
  no_match, and select_basis_factor could not act (only one SEAI gas candidate ⇒ no competing qualifier).
  So the SEAI gap is pre-existing and untouched — recorded, not fixed.
```

## 8. Regression suites (independently run at the target SHA)

```text
tests/unit/test_d_a_natural_gas_basis.py            26 passed
tests/unit/engines/test_d_a_natural_gas_discovery.py 9 passed
tests/unit/test_units.py                            13 passed
tests/unit/test_units_qualifier.py                  27 passed
tests/unit/test_units_family_compat.py              35 passed
tests/unit/engines                                  278 passed
tests/unit/services (023 · 026 · 029/031 · D-F)     264 passed
full tests/unit suite                               see the count recorded below
new failures: NONE · pre-existing failures: NONE · environment/infrastructure failures: NONE
No test was modified; the implementer's claimed counts (D-A discovery 9/9, D-A policy 26/26, engines
green, units green, services green) are CONFIRMED.  The broader `tests/unit` run is recorded in §8a.
```

### 8a. broader tests/unit run (background, at the target SHA)

```text
FULL_SUITE_RESULT
  python -m pytest tests/unit  →  2598 passed, 1 warning in 375.85s (0:06:15)
  0 failed · 0 errors · no skips reported · single warning is the pre-existing third-party
  DeprecationWarning surfaced by tests/unit/services (unrelated to D-A).
  ⇒ the previously-claimed "full suite" gap is now closed: the ENTIRE tests/unit suite is green at
    89c02db.
```

## 9. Component-vs-aggregate — OBSERVATION ONLY (outside D-A scope, not fixed)

```text
Every 'Natural gas ... [kWh (Net CV)]' proposal visible to the real index (value | id | name):
   0.00031 | 2aa65183-…  Natural gas (kg CO2e of CH4 per unit)          ← SELECTED for row 1
   0.20229 | e3b88169-…  Natural gas (kg CO2e of CO2 per unit)
   0.0001  | 8a9532a9-…  Natural gas (kg CO2e of N2O per unit)
   0.2027  | c895606c-…  Natural gas (kg CO2e)                            ← the combustion AGGREGATE
   0.20489 | 542fd52c-…  Natural gas (100% mineral blend) (kg CO2e)      ← blend aggregate
   0.03347 | 2330c084-…  WTT- fuels > Natural gas (kg CO2e)              ← well-to-tank
   (+ CH4/CO2/N2O components of the 100% mineral blend; plus Other petroleum gas and Gas oil rows)
OBSERVED:
  · row 1 (unqualified) selects the CH4 per-unit COMPONENT (0.00031), not the aggregate (0.2027/0.20489);
  · an explicit 'Net CV' prose request selected the WTT factor (0.03347) — still basis-correct (Net CV),
    but a different emissions concept from combustion.
CLASSIFICATION: observation / separate policy issue — NOT a D-A implementation defect. The approved D-A
requirement is basis selection (Gross vs Net) plus a DEFRA-2025 factor at confidence 1.0, all of which
hold. Preference/ranking WITHIN one qualifier group (aggregate vs component vs WTT, and the boundary of
keyword candidate retrieval) is a distinct policy question for the PO. No ranking, factor data or
retrieval behaviour was changed by this verification.
```

## 10. Production impact / cleanup / safety statement

```text
Production:      NONE. No production access, no production database write, no upload, no job or queue
                 operation, no emission-factor modification, no Render or Vercel deployment, no P1
                 activation. P1 remains SHADOW.
Database:        local authoritative dataset only, and the verification session forced
                 SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY — writes were not merely avoided,
                 they were refused by the session.
Records created: none (no match result, calculation or job row was persisted). Nothing to clean up.
Repo contents:   unchanged by the verification; the only artefact added is this report. The scratch
                 harness lives outside the repository (/tmp/v35_verify.py) and is not committed.
```

## 11. Limitations of this verification

```text
1. Enumeration order was reversed in the in-memory candidate collection (real candidates, real selector);
   the persistent database row order was deliberately NOT mutated.
2. Row-1/row-5 evidence was obtained through the read-only oracle path (real detector → real matcher →
   real authoritative EF); no processing job, queue entry or calculation snapshot was created, so the
   end-to-end persisted job path was not exercised by this window.
3. The component-vs-aggregate/WTT selection inside the winning Net-CV group is recorded as an
   observation only; its correctness is a PO policy matter and was not adjudicated here.
4. The SEAI natural-gas factor (cubic metres, SEAI-2025) does not resolve (no_match) — pre-existing,
   untouched, and outside D-A.
5. Inventory discrepancy recorded: the brief states 7,029 factors; the environment loads 7,049.
```

## FINAL VERDICT

**PASS** — D-A behaviour was independently reproduced. `kWh` reaches the qualified `kWh (Gross CV)` /
`kWh (Net CV)` candidates and the approved policy selects **Net CV at confidence 1.0** for an unqualified
natural-gas request; explicit Gross/GCV selections select Gross and explicit Net/NCV select Net; Gross/Net
are never silently interchanged (46a5534 protection verified); the CNG false positive is contained
(row 5 → `no_match`, no gas factor); selection is enumeration-order independent; factor-set context is
retained; and no new, pre-existing or infrastructure test failure was found. The implementation is
suitable for the next PO gate.

**D-A VERIFICATION PASS — READY FOR PO CLOSURE**

(PO is NOT closed by this report. The component-vs-aggregate / WTT selection observation in §9 remains a
separate policy question for the Product Owner.)
