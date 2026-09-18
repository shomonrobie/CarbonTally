# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-045 — FIX AND VALIDATE THE REAL-DATA DIVERSION GATE

```text
1  BASELINE SHA  db28991af81eea60ceb8f4cb9e7796e03fefb522 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (commit + push; HEAD == origin)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push)
4  GIT STATUS    CLEAN at finish; changed files in §16
```

## 5. EXACT ROOT CAUSE OF THE 044 FALSE POSITIVES (measured this window)

```text
The 044 rule ("families with disjoint scopes ⇒ material conflict") was wrong — but fixing that was only
half the story. The refined rule (§7) was implemented and the service suite STILL produced exactly
22 failed / 242 passed, the same set, which isolates the real cause:

  the 026/031 fixture corpus drives mapping from the row's LITERAL SOURCE TEXT whenever no canonical
  activity resolved (`_mapping_input_text` prefers `activity`, else the row's literal `description`), e.g.
  rows whose text is 'Waste …' or the explicit 'Unmappable row 1 kWh' — see
  tests/unit/services/test_multiline_provenance_mapping.py. For those rows the retrieved window genuinely
  contains a treatment/material family AND a combustion family sharing the concept token, so the gate
  diverts — which is exactly the F-039-1 behaviour the PO authorised for a bare 'Waste'.

⇒ The residue is NOT a false positive of the compatibility rule. It is a genuine CONFLICT between ratified
  pre-F-039-1 expectations (such a row reaches the matcher and is resolved/unresolved by the old path) and
  the authorised product rule (such a row must not be resolved). STEP 8 instructs STOP and report in that
  situation, so the wiring was reverted and is not retained (§16).
```

## 6–7. EXISTING SEMANTIC FIELDS USED, AND THE EXACT COMPATIBILITY RULE

```text
Representations reused (no new taxonomy, no new field, no schema change):
  family_of(factor)   taxonomy prefix ('Waste disposal', 'Material use', 'Fuels', 'Bioenergy', …)
  factor.scope        Scope 1 / Scope 2 / Scope 3 / 'Outside of Scopes'
  is_upstream(factor) the policy's WTT boundary marker
  treatment_route() / variant_of()   within-family route / variant
  request_tokens()    the shared relevance tokeniser
  the policy's own treatment/material vocabulary ('waste disposal', 'material use') — the D-FS-4 constant

RULE — assess_family_conflict(activity, candidates, *, unit, scope, preferred_unit):
  1. run the EXISTING select_factor(); a deterministic winner → "sufficient" (no diversion);
  2. policy status "ambiguous" → "policy_ambiguous" (D-FS-5 owns it; never diverted);
  3. no concept-bearing, non-upstream family → "no_candidates" (no options invented);
  4. exactly one family → "not_required";
  5. classify each remaining family as "treatment" (prefix in the policy's treatment/material vocabulary),
     else "combustion" (candidates are Scope 1/Scope 2 energy rows), else neither; divert
     ("clarification_required") ONLY when BOTH a treatment and a combustion family are present — i.e. the
     same concept is readable as “something is done to the material” and as “the material is burned as
     fuel”. Otherwise "not_required".
```

## 8–10. WHY SCOPE DIFFERENCE ALONE IS NOT A CONFLICT, AND WHAT IS

```text
8  Scope is an accounting dimension, not a meaning. An ordinary activity legitimately retrieves Scope-1
   combustion factors together with Scope-3 upstream/travel/generation siblings (plus WTT siblings, which
   the policy excludes by its own boundary rule). Treating that coexistence as ambiguity produced the 044
   false positives — and correcting only that was not sufficient (§5).
9  Ordinary Scope-1 + Scope-3 coexistence now yields "not_required": the families differ in accounting or
## 11–15. REAL-DATA RESULTS, SERVICE SUITE, TESTS, COUNTS

```text
11 REAL DATA (7,049 factors; 043 harness evidence, revalidated against the refined rule)
   'Waste'            61 candidates · policy not_applicable → **clarification_required**
                      families: fuels [scope 1] · material use [scope 3] · waste disposal [scope 3]
                      options: 7 real semantics (Landfill, Open-loop, Closed-loop, Incineration,
                      Composting, Material use · Composting, Fuel combustion) — treatment+combustion clash.
   CAVEAT: the bounded real-data harness completed 10 of 14 planned cases before the read-only session hit
   an asyncpg error in the alias-resolver path (harness artefact). The remaining cases are covered by the
   041/043 suites and the tests below; no fresh measurement is claimed for them.
12 SCENARIOS  'Waste disposal' → policy_ambiguous (5 real routes) · 'Waste Landfill' → sufficient
   (Landfill be0d681d…) · 'Waste Waste oils' → sufficient (faf9991d…) · 'Waste oils' → sufficient ·
   'Diesel' → policy_ambiguous (two real products) · 'Diesel 100% mineral diesel' → sufficient
   (7de17915…) · 'Diesel average biofuel blend' → sufficient (ae0c1488…) · 'Natural gas' → sufficient with
   the D-A Net-CV aggregate · WTT → upstream excluded from classification, 'Natural gas WTT' still selects
   the WTT factor · Water → not diverted · 'Gas usage' → combustion families only → not_required ·
   'Power consumption' → no_candidates · no candidates → no_candidates with options == ().
13 SERVICE SUITE with the gate wired (both the 044 rule and the refined rule): 22 failed / 242 passed —
   the same failing set, which is what localised §5. After the revert the suite is green: services
   264 passed (1 warning); engines 340 passed throughout.
14 TESTS ADDED THIS WINDOW: none. The 043 suite (13) is retained and passes unchanged against the refined
   rule; the 041 suite (16) is unchanged.
15 TEST COUNTS (final tree): services 264 · engines 340 · 041 clarification 16 · 043 trigger 13 ·
   D-A policy 26 · D-A discovery 9 · units 13/27/35 — NEW FAILURES: none.
```

## 16–21. FILES, DATA, SCHEMA, UI, DEPLOYMENT, REMAINING DEPENDENCIES

```text
16 FILES CHANGED  backend/engines/activity_clarification.py (refined compatibility rule: `_family_classes`
                  + treatment-vs-combustion conflict test, replacing the disjoint-scope test) ·
                  docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-045.md
                  IS THE 044 SERVICE WIRING RETAINED?  **NO** — reverted again
                  (`git checkout -- backend/services/automatic_processing.py`) because §5 is a genuine
                  ratified-test vs authorised-rule conflict and STEP 8 says STOP in that case.
17 FACTOR DATA CHANGES  NONE.   18 SCHEMA CHANGES  NONE.   19 API/UI CHANGES  NONE.
20 DEPLOYMENT  NONE (no production access, no migration, no Render/Vercel action, P1 remains SHADOW).
21 REMAINING DEPENDENCIES
   F-045-1 (BLOCKING — needs a PO ruling) The 026/031 corpus asserts that a row carrying literal source text
     such as 'Waste …' reaches the matcher and is resolved/unresolved by the pre-F-039-1 path; the
     authorised rule requires the opposite. Either (a) those fixture expectations are formally amended for
     the authorised rule — a governance decision about ratified tests, not an implementation choice — or
     (b) the diversion is scoped to rows whose evidence is a CANONICAL ACTIVITY rather than free source
     text, which is itself a product decision because it decides when CarbonTally may decline to guess.
   F-045-2 The 041/044 persistence package (migration, RLS, repository, endpoints, D19 UI) remains
     unchanged and unbuilt.
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D / Phase 9 / G0-D / RLS steps 3–5 / MPG / billing /
  beta / demo / P1 remediation NOT touched · no factor-data, schema, API/UI or deployment change
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

The compatibility rule is fixed and better grounded than 043: scope difference alone no longer causes
clarification, and diversion now requires a genuine treatment-vs-combustion *meaning* collision, derived
entirely from existing representations (taxonomy family, scope, the policy's upstream boundary, and the
policy's own treatment-family vocabulary). The gate suites are green (043 13, 041 16, engines 340) and the
mandated real-data scenarios behave as required. Service integration nevertheless still fails against the
real 026/031 fixture corpus — not because the rule is wrong, but because those ratified expectations encode
the pre-F-039-1 behaviour for rows whose evidence is literal source text. Per the task's own stop
instruction the wiring was reverted rather than made green by special-casing, and the residue is handed to
the PO as F-045-1.

   representation, not in the meaning of the user's activity, and the policy remains authoritative.
10 A conflict diverts only on a *meaning* collision — a treatment/material family and a combustion family
   for the same concept — because the policy can choose only within a class and the user has not said which
   meaning they intend.
```
