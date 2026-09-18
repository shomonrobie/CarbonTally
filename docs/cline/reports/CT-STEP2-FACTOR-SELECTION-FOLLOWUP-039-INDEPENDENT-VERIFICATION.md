# CT-STEP2-FACTOR-SELECTION-FOLLOWUP-039 — INDEPENDENT VERIFICATION

**Role:** Cline as independent verifier. **Verification only**: no source, test, configuration, schema or
factor-data change; no deployment; no commit/push; D-A and D-FS-1…6 not reopened; D-B/C/D not started.
Evidence below comes from the pinned commit and the real 7,049-factor dataset, not from the report.

```text
TARGET SHA        bcadbfc923bbce511ded1a6d52605284335e602d   (039 implementation)
PREVIOUS SHA      c9dc418ec93046fa5cbf7c2fe117daa610bcc069   (038)
ACTUAL HEAD       bcadbfc923bbce511ded1a6d52605284335e602d   (identical to target)
BRANCH            p8-release-reconciled
ORIGIN            origin/p8-release-reconciled = bcadbfc…2d · git ls-remote refs/heads/p8-release-reconciled
                  = bcadbfc…2d
WORKING TREE      CLEAN (git status --porcelain → empty; git diff --stat HEAD → empty)
COMMIT CONTENTS   5 files, +492/-13: engines/factor_matching.py · engines/factor_selection_policy.py ·
                  tests/unit/engines/test_factor_selection_followup_039.py ·
                  tests/unit/engines/test_factor_selection_policy.py · the 039 report
                  ⇒ the code under test IS the committed, pushed artefact.
DATA ACCESS       local authoritative dataset (7,049 factors) via EmissionFactorsRepository; every DB
                  session forced `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`.
```

## 1. CODE TRACE (from `git show bcadbfc:<path>`, not from the report)

```text
A. RETRIEVAL LAYER — engines/factor_matching.py
   · family-diversified retrieval IS implemented: _policy_candidates (:244) with
     _POLICY_SCAN_LIMIT = 10 000 (:241) and _POLICY_FAMILY_CAP = 40 (:242); rows bucketed by the taxonomy
     prefix (activity_type.split(' > ')[0]).
   · it uses the SHARED tokeniser (imported `request_tokens`, :53; used :272 and :279) — one notion of
     relevance, not two.
   · it contains NO selection/ranking policy: grepping the method body for
     eligib|rank|is_component|is_upstream|variant|select_factor|mineral returns only docstring prose
     ("neither decides eligibility or preference") — no executable selection code.
   · it does NOT hardcode mineral diesel (the string 'mineral' is absent from the method body).
   · it does NOT globally widen the ordinary window: the matching stages and their limits are untouched;
     the bounded scan exists only inside the policy-candidate helper.
B. SELECTION POLICY — engines/factor_selection_policy.py
   · semantic eligibility remains here (pure function; no I/O, DB or model calls);
   · scope compatibility enforced (explicit scope filter; 'Scope 3'/'Outside of Scopes' excluded for
     fuel/energy requests when no scope is supplied);
   · combustion/WTT separation enforced by the 'WTT-' boundary marker in both directions;
   · aggregate/component preference preserved (components dropped when an aggregate exists in context);
   · basis preference cannot be overridden by retrieval breadth: the basis enters ONLY as the rank input
     `preferred_unit`, never as an eligibility rule, so breadth cannot admit an ineligible candidate;
   · ambiguity is explicit: SelectionOutcome(status="ambiguous", groups=…), tied on request-token
     COVERAGE across (family, treatment route, product variant) groups.
C. LEGACY PATH — services/automatic_processing.py
   · _prefer_aggregate_factor DELEGATES to the same module and applies the verdict only when it names a
     different factor; it no longer picks a candidate itself. No second selection implementation.
D. ENGINE VERDICT HANDLING — factor_matching.py
   · `if decision.status == "selected" and decision.factor is not None:` (:315) corrects only an
     excluded/outranked match; `if decision.status == "ambiguous":` (:328) honours ambiguity
     UNCONDITIONALLY — even when the current match is itself eligible (the F-038-2 requirement).
```

## 2. F-038-1 DIESEL — INDEPENDENT RESULTS (real dataset)

```text
RETRIEVAL (bare 'Diesel', litres): 358 candidates across 13 families — Bioenergy 3 · Business travel-
   land 40 · Delivery vehicles 40 · Freighting goods 40 · **Fuels 32** · Managed assets- vehicles 40 ·
   Outside of scopes 6 · Passenger vehicles 40 · SECR kWh pass & delivery vehs 40 · WTT- bioenergy 3 ·
   WTT- delivery vehs & freight 40 · WTT- fuels 8 · WTT- pass vehs & travel- land 26
   ⇒ the Fuels family (which holds the diesel combustion factors) is now represented — precisely the
     failure measured in the 039 root cause — and NOT by widening the matching window (stages unchanged).

CASE A bare 'Diesel' → status=ambiguous · confidence 0.0 · factor=NONE
   stages=[exact_match, natural_key, alias_match, keyword_search, selection_policy]
   POLICY eligible = exactly 2 (both Scope 1, litres, family 'Fuels'):
      'Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e) [litres]'   2.66155
      'Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e) [litres]'
   POLICY groups = (('fuels','','mineral'), ('fuels','','biofuel blend')) — two materially different
      products, no product evidence in the request ⇒ explicit ambiguity (PO #7/#8 satisfied)
   Development diesel NOT selected; 349 excluded, predominantly by semantic/unit rules
      ('unit incompatible' for km/miles/GJ; 'upstream/WTT factor for a non-upstream request')
   ORDER INDEPENDENCE: reversed candidate list ⇒ still ambiguous
CASE B 'Diesel 100% mineral diesel' → matched · selection_policy · id 7de17915-… · 2.66155 · 'litres' ·
      Scope 1 · DEFRA-2025 (eligible set = the mineral product only; components removed by the aggregate
      rule)
CASE C 'Diesel average biofuel blend' → matched · selection_policy · id ae0c1488-… · 2.57082 · 'litres' ·
      Scope 1 · DEFRA-2025
CASE D 'Development diesel' → matched · id c3afa542-… · 0.03705 · 'litres' · Scope 1 · DEFRA-2025;
      eligible = {Development diesel, Development petrol}; diesel wins on token COVERAGE (2/2 vs 1/2),
      not on magnitude ⇒ Development diesel remains selectable, not globally suppressed
NO numeric preference: case A exposes both values and chooses neither. NO repository-order preference:
reversal changes no verdict.
```

## 3. D-A NATURAL GAS REGRESSION — INDEPENDENTLY REPRODUCED

```text
'Natural gas' · kWh · GB · 2025 → status=matched · confidence=1.0 · methodology=selection_policy
   stages=[exact_match, natural_key, alias_match, keyword_search, fuzzy_match, calorific_basis,
           selection_policy]
   factor id=c895606c-bab0-4981-826d-eb1046ce6a80 · value 0.20270 · unit 'kWh (Net CV)' · Scope 1 ·
   2025 · DEFRA-2025 · DEFRA-DESNZ · GB
   name 'Fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]'
   ⇒ Scope 1 combustion · natural gas · AGGREGATE (not CH4) · **Net CV** · no Gross-CV regression.
   POLICY eligible = the two PLAIN aggregates (Gross CV and Net CV); the CH4/CO2/N2O components and the
   '100% mineral blend' variants were excluded (unit/aggregate rules) — i.e. D-FS-1 still applies.
   ⚠ VERIFIER OBSERVATION (non-blocking): when `select_factor` is called on the same real candidate list
   WITHOUT `preferred_unit`, reversed ordering selects the Gross-CV aggregate (13a95d01-…) because both
   bases are equally eligible and the tie then falls to the identifier rule. The engine path passes
   `preferred_unit` (the D-A-decided unit), which is what preserves Net CV. The D-A protection is
   therefore load-bearing and correct in the shipped path, but any future caller of select_factor must
   also supply the decided unit; this is a hardening note, not a defect in the authorized scope.
```

## 4. POWER / WTT REGRESSION — INDEPENDENTLY REPRODUCED

```text
POWER  'Power consumption kWh € €' · kWh → status=no_match · confidence 0.0 · factor=NONE
   stages=[exact_match, natural_key, alias_match, keyword_search, fuzzy_match] — NO calorific_basis stage,
   no natural-gas/CNG factor. (No gas redirection.)
WTT    'Natural gas WTT' · kWh → status=matched · confidence 1.0 · methodology=calorific_basis
   factor id=2330c084-… · 0.03347 · 'kWh (Net CV)' · Scope 3 · DEFRA-2025
   name 'WTT- fuels > Gaseous fuels > Natural gas (kg CO2e) [kWh (Net CV)]'
   POLICY eligible = 25 upstream candidates; every combustion candidate was excluded with
   'not an upstream/WTT factor for an upstream request'; the WTT candidates remain selectable.
   ⇒ WTT is not globally suppressed, and for the Scope-1 combustion request (§3) the WTT factor was
     excluded ('upstream/WTT factor for a non-upstream request') and did not enter the eligible set.
```
## 5. F-038-2 WASTE — INDEPENDENT RESULTS (real dataset)

```text
8A 'Waste disposal' · tonnes → status=ambiguous · confidence 0.0 · factor=NONE
   stages=[exact_match, natural_key, alias_match, keyword_search, selection_policy]
   RETRIEVAL: 61 candidates — families {Waste disposal 40, Fuels 16, WTT- fuels 3, Material use 2}
   POLICY eligible = 42, ALL in the treatment/disposal taxonomy
      ('Waste disposal > Construction > Aggregates - Closed-loop/-Landfill/-Open-loop …')
   POLICY groups = 5 distinct treatment routes: closed-loop · compost · incinerat · landfill · open-loop
      ⇒ missing route + materially different routes = ambiguity (PO #3/#4 satisfied)
   NOT selected: 'Fuels > Liquid fuels > Waste oils …', excluded with the explicit reason
      "fuel concept where a waste treatment/disposal concept was requested" (8 rows)
   NO fuel-combustion factor in the eligible set; ORDER-INDEPENDENCE: reversal ⇒ still ambiguous
8B 'Waste disposal Landfill'  · tonnes → matched · id be0d681d-… · 1.26338 · 'tonnes' · Scope 3 ·
      'Waste disposal > Construction > Aggregates - Landfill (kg CO2e) [tonnes]'
8C 'Waste disposal Open-loop' · tonnes → matched · id b74bd1c0-… · 1.00835 · 'tonnes' · Scope 3 ·
      'Waste disposal > Construction > Aggregates - Open-loop (kg CO2e) [tonnes]'
   ⇒ two materially different routes each select their own factor; neither wins by lexical order.
8D 'Waste oils' · litres → matched · selection_policy · id cd53db21-… · 2.74924 · 'litres' · Scope 1 ·
      'Fuels > Liquid fuels > Waste oils (kg CO2e) [litres]' (fuel semantics intact); with unit 'tonnes' →
      id faf9991d-… · 3219.37916 (aggregate, not the CH4 component).
```

## 6. F-039-1 — BARE 'Waste' (independently investigated; NOT fixed)

```text
9.1 activity='Waste' · tonnes → status=matched · confidence 1.0 · methodology=keyword_search
    factor id=5b8f5355-6828-4e5c-a152-6f445b265ba0 · 3.5504 · 'tonnes' · Scope 1 · 2025 · DEFRA-2025
    name 'Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]'
    POLICY verdict: not_applicable ("request outside the policy's semantic classes") — the bare token
    'Waste' carries no treatment marker, so nothing corrects the keyword-stage match; the reversed call
    returns the same not_applicable.
    ⇒ CONFIRMED: an unqualified 'Waste' request still reaches a Waste-oils factor, and it is a CH4
      COMPONENT of a fuel rather than any disposal factor.
9.2 'Waste treatment' · tonnes → policy ambiguous (5 treatment routes + 2 material-use compost
    candidates); engine result no_match (the stages do not match that wording) ⇒ no factor fabricated.
9.3 'Waste disposal' → ambiguous (§5).   9.4 'Waste oils' (tonnes) → matched waste-oil aggregate.
RETRIEVAL for 'Waste' = the same 61 candidates as 'Waste disposal' — the CORRECT candidates are already
retrieved; only the request CLASSIFICATION is missing.
CLASSIFICATION: **separate follow-up requiring a PO decision**; the implementation report's F-039-1 is
accurate and not understated. NOT introduced by 039: the behaviour is pre-existing, 039 made the disposal
candidates visible, and treating a bare 'Waste' token as a disposal request would change behaviour for
every unqualified "waste" mapping line. NOT blocking: mandatory case D ('Waste disposal') is satisfied and
no authorised rule claims 'Waste' means disposal.
```

## 7. AMBIGUITY INTEGRITY

```text
· current match eligible ≠ override: 'Waste disposal' matched a disposal factor at the keyword stage yet
  the engine returned ambiguous (:328 honours the verdict unconditionally) — the 038 behaviour where an
  eligible current match suppressed ambiguity is gone.
· repository ordering: reversing the real candidate list changed no verdict in any tested case.
· numeric value: the ambiguous diesel case exposes 2.66155 vs 2.57 and selects neither; selected cases win
  on token COVERAGE (Development diesel 2/2 vs Development petrol 1/2), never on magnitude.
· lexical order: 'Waste disposal Landfill' selects Landfill although 'Closed-loop' sorts earlier.
· aggregate preference neither creates nor resolves ambiguity.
· factor-set context: every selected factor is DEFRA-2025 · GB · 2025 · DEFRA-DESNZ in all cases.
```


## 8. TEST RESULTS (independently run, tests unmodified)

```text
tests/unit/engines/test_factor_selection_followup_039.py    14 passed
tests/unit/engines/test_factor_selection_policy.py          19 passed
tests/unit/engines                                          311 passed
tests/unit/services                                         264 passed, 1 warning
tests/unit/test_d_a_natural_gas_basis.py                    26 passed
tests/unit/engines/test_d_a_natural_gas_discovery.py         9 passed
tests/unit/test_units.py / _qualifier / _family_compat      13 / 27 / 35 passed
FULL tests/unit                                             2631 passed, 1 warning, 0 failed (351.00s)
passed 2631 · failed 0 · errors 0 · skipped (none reported)
pre-existing failures: none observed · infrastructure failures: none observed
No test file was modified by this verification; the 039 report's claimed counts are CONFIRMED.
```

## 9. PROVENANCE / AUDITABILITY

```text
· selected factors carry id, activity_type, unit, scope, reporting_year, factor_set, factor_source and
  country in every verified case — no provenance field was lost.
· the deciding stage is visible in `stages_executed` ('selection_policy' appended when the policy decides;
  'calorific_basis' retained from D-A).
· on ambiguity the engine returns the pre-existing MatchResult(status="ambiguous", suggestions=…), so the
  candidate list remains available for adjudication — no evidence surface was removed.
```

## 10. DATA / SECURITY SAFETY

```text
· every database session was forced READ ONLY; no INSERT/UPDATE/DELETE was issued;
· no factor row was modified (no write path was used at all);
· no schema or migration file was touched (git status clean before and after);
· no deployment, no Render/Vercel action, no P1 activation (P1 remains SHADOW);
· no commit and no push were performed by this verification window.
```

## FINAL VERDICT

**VERIFICATION PASS WITH NON-BLOCKING FOLLOW-UP**

F-038-1 and F-038-2 are independently reproduced against the real 7,049-factor dataset and satisfy the
authorised PO policy: the diesel combustion family is now visible to the selection policy without widening
the matching window; a bare diesel request yields explicit ambiguity rather than an arbitrary pick;
product-qualified requests, named treatment routes and waste-oil requests resolve deterministically;
route-less disposal is ambiguous and never a fuel; and no result is decided by numeric value, repository
order or lexical accident. D-A is intact (Net-CV aggregate, Scope 1, no CH4, no Gross-CV regression), power
is untouched, and WTT remains selectable in its own context while being excluded for Scope-1 combustion.
All suites are green (2631/2631).

Non-blocking follow-ups: **F-039-1** (a bare 'Waste' request still reaches a Waste-oils CH4 component
factor — a real, pre-existing semantic imperfection whose correction needs a PO classification decision)
and the verifier's hardening note that D-A's basis is preserved by the caller passing `preferred_unit`
into `select_factor`. Neither contradicts the authorised policy; neither blocks the next PO gate.

**PO is not closed by this report. D-B, D-C and D-D were not started.**
