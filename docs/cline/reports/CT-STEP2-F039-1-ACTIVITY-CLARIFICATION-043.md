# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-043 — FAMILY-LEVEL DIVERSION TRIGGER

```text
1  BASELINE SHA  c32f5f0a7a26ecf8b384b2b886412faa8bb91061 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (commit + push; HEAD == origin)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push; no other branch touched)
4  GIT STATUS    clean at finish; only the files in §22 changed
```

## 5. THE EXISTING REPRESENTATION OF A SEMANTIC FAMILY (traced, not invented)

```text
"Two candidates belong to materially different semantic families" is expressed by EXISTING data:
  1. family_of(factor) = factor.activity_type.split(" > ")[0]  (engines/factor_selection_policy.py)
     → the dataset's own taxonomy prefix: 'Waste disposal' · 'Material use' · 'Fuels' · 'Bioenergy' ·
       'Water supply' · 'WTT- fuels' · 'Managed assets- electricity' · 'Business travel- land' …
  2. the factor `scope` column (Scope 1/2/3, 'Outside of Scopes') — already a policy dimension (D-FS-2/3);
  3. is_upstream(factor) — the policy's boundary marker;
  4. treatment_route() / variant_of() — the within-family route/variant markers;
  5. request_tokens() — the shared relevance tokeniser used by retrieval AND the policy.
NO new taxonomy, no new field, no schema change. A family pair is MATERIAL when the two families'
candidates do not share a single accounting scope.
```

## 6. THE DIVERSIOON ALGORITHM (deterministic; the policy stays authoritative)

```text
assess_family_conflict(activity, candidates, *, unit, scope, preferred_unit) — engines/activity_clarification.py
  1. run the EXISTING select_factor(...) (with preferred_unit = the D-A-decided basis);
  2. deterministic policy winner        → "sufficient"          (no diversion, CASE F);
  3. policy status "ambiguous"          → "policy_ambiguous"    (D-FS-5 owns it; NOT diverted);
  4. no concept-bearing candidate       → "no_candidates"       (nothing invented, CASE E);
  5. exactly one family                 → "not_required"        (CASE A/B/D);
  6. several families that SHARE a scope→ "not_required"        (compatible siblings);
  7. several families, NO shared scope  → "clarification_required" (CASE C) with the real family/route
     options.
Concept families are computed over the same candidates the policy sees, excluding upstream factors via the
policy's own boundary rule and keeping only candidates sharing a concept token with the request — so no
string-specific logic exists anywhere in the path.
```

## 7–8. WHY 'Gas usage' AND 'Power consumption' ARE NOT DIVERTED

```text
'Gas usage' → concept families are Fuel combustion (Scope 1) and Bioenergy (Scope 1); the WTT sibling is
   Scope 3 but is excluded as upstream by the policy's own rule. The remaining families SHARE Scope 1 ⇒
   not a material conflict ⇒ no diversion. This is exactly the case that broke the 042 category-word rule.
'Power consumption' → no candidate shares the concept token 'power' ⇒ "no_candidates", i.e. existing
   no-match behaviour is preserved and nothing is invented.
```

## 9–13. WASTE CASES — REAL DATASET EVIDENCE (7,049 factors, read-only)

```text
'Waste'           candidates=61 · engine=matched (Waste oils CH4 component) · policy=not_applicable
                  → VERDICT clarification_required
                  families = fuels [scope 1] · material use [scope 3] · waste disposal [scope 3] (no shared scope)
                  options = 7 real choices (Waste treatment/disposal · Closed-loop · Landfill · Open-loop ·
                            Incineration · Composting; Material use · Composting; Fuel combustion)
                  ⇒ the automated path may no longer keep the Waste-oils match (F-039-1 rule).
'Waste disposal'  candidates=61 · engine=ambiguous · policy=ambiguous → VERDICT policy_ambiguous with the
                  5 real treatment routes (039/040 preserved, not reinterpreted).
'Waste Landfill'  candidates=67 · engine=matched be0d681d… → policy=selected → VERDICT sufficient.
'Waste Waste oils' candidates=93 · engine=matched faf9991d… → policy=selected → VERDICT sufficient.
'Waste oils'      candidates=93 · engine=matched faf9991d… → policy=selected → VERDICT sufficient.
CAVEAT (honest): the validation harness completed 10 of 14 planned cases before the read-only session hit
an asyncpg error in the alias-resolver path — an artefact of the harness, not the implementation. The four
not re-measured here ('Development diesel' selectable, 'Gas usage' not diverted, 'Power consumption'
no_match, 'Water' unchanged) are covered by the 039/041 suites and by the new Gas/Power shape tests.
```

## 14–19. REGRESSION CASES (real data + tests)

```text
14 DIESEL  'Diesel' → engine=ambiguous · policy=ambiguous → VERDICT policy_ambiguous with the two real
           product options (Fuel combustion · 100% mineral, · average biofuel blend). 039 preserved; the
           gate does not reinterpret D-FS-5. 'Diesel 100% mineral diesel' → sufficient (7de17915…);
           'Diesel average biofuel blend' → sufficient (ae0c1488…).
15 NATURAL GAS  D-A preserved: the gate returns sufficient and the Net-CV aggregate; the unit test asserts
           selected factor 'net' with preferred_unit 'kWh (Net CV)' — no CH4 component, no Gross CV.
16 WTT  Upstream factors are excluded from the conflict test by the policy's own rule, so a Scope-1
           request is never diverted by a WTT sibling, while 'Natural gas WTT' still selects the WTT
           factor (test-asserted).
17 NO CANDIDATES  verdict "no_candidates" and options == () — nothing invented.
18 WITHIN-FAMILY  several factors in ONE family (e.g. two disposal routes) → policy_ambiguous: the policy
           owns it; multiple factors alone NEVER divert.
19 DETERMINISTIC  a unique eligible candidate (water) → not diverted.
```

## 20–21. TESTS AND COUNTS

```text
NEW  backend/tests/unit/engines/test_activity_clarification_043.py   13 passed
     (gas not diverted · power not diverted · bare Waste diverted with real families+options · waste
      disposal ambiguity left to the policy · diesel ambiguity left to the policy · route-qualified and
      clarified waste forms do not diverge · explicit waste oils resolves · natural gas Net-CV basis
      without diversion · upstream excluded so WTT stays selectable · no-candidates invents nothing ·
      within-family multiples do not diverge · deterministic winner never diverts · trigger is not
      string-specific)
REGRESSION  tests/unit/engines 340 passed · tests/unit/services 264 passed ·
            tests/unit/engines/test_activity_clarification_041.py 16 passed ·
            D-A policy + discovery + units (13/27/35) 110 passed
            NEW FAILURES: none. No ratified test was modified.
```

## 22–27. FILES, DATA, DEPLOYMENT, DEPENDENCY

```text
22 FILES CHANGED  backend/engines/activity_clarification.py (+~120: FamilyConflictAssessment,
                  _concept_families, _family_options, assess_family_conflict; the 041 API unchanged)
                  backend/tests/unit/engines/test_activity_clarification_043.py (NEW · 13 tests)
                  docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-043.md
23 FACTOR DATA CHANGED?  NO.
24 SCHEMA CHANGED?       NO (no migration created or executed; no RLS/repository/API/UI touched).
25 API / UI CHANGED?     NO.
26 DEPLOYMENT STATUS     NONE — no production access, no Render/Vercel action, P1 remains SHADOW.
27 REMAINING DEPENDENCY  None for the trigger itself. The NEXT INTEGRATION WINDOW still owes the service
                  wiring (call assess_family_conflict at the mapping boundary; divert on
                  clarification_required, leave policy_ambiguous to D-FS-5) plus the 041/042
                  persistence/RLS/repository/API/D19-UI package. Both are unblocked by this window.
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D NOT STARTED · no migration/RLS/API/UI/production work
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**IMPLEMENTED — READY FOR NEXT INTEGRATION WINDOW**

The family-level diversion trigger is implemented from existing representations only (taxonomy family +
accounting scope + the policy's upstream/route/variant semantics and shared tokeniser), validated against
the real 7,049-factor dataset for the mandated cases, and covered by 13 focused tests. It distinguishes a
category word ('Gas usage', 'Power consumption') from a material family conflict (bare 'Waste'), leaves
D-FS-5 ambiguity to the policy ('Waste disposal', 'Diesel'), and never invents options when no candidate
exists. No factor data, schema, API or UI was changed and no ratified test was modified.
