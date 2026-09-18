# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-044

```text
1  BASELINE SHA  e124c626dfa83dc2036c70d36fbbf4d59abbf060 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (report commit; HEAD == origin; tree clean)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push; no other branch touched)
4  GIT STATUS    CLEAN — this window's only surviving change is this report (see §10/§30)
5  MIGRATION CREATED?   NO — no migration file was written.
6  MIGRATION EXECUTED?  NO — nothing created, so nothing was executed locally, in test or in production.
7  RLS IMPLEMENTED?     NO (the 041 report §6–§7 design stands, unimplemented).
8  REPOSITORY           NOT implemented.
9  API                  NOT implemented.
10 REAL SERVICE WIRING  NOT delivered — implemented, MEASURED against the real fixtures, REVERTED:
     · built: after the existing match, `assess_family_conflict(activity,
       engine.clarification_candidates(request), unit, scope, preferred_unit)` (the 043 gate), diverting
       ONLY on verdict == "clarification_required" into the existing `unmapped` path via a new
       `_clarification_entry()` carrying clarification_required, clarification_verdict,
       clarification_families and the real clarification_options — no factor id anywhere;
     · measured: tests/unit/services → **22 failed, 242 passed** (engines 340 passed). Head of the list:
         test_multiline_provenance_mapping.py::test_row_without_a_keyword_reaches_the_matcher_with_its_source_text
         test_multiline_provenance_mapping.py::test_calculation_carries_per_row_provenance
     · WHY (newly measured — the reason the synthetic tests missed it): the 043 gate is safe on hand-built
       candidate sets but over-diverted against REAL retrieval sets. Its "families with disjoint scopes ⇒
       material conflict" rule fires for ordinary activities whose candidate window legitimately spans
       Scope-1 combustion families AND Scope-3 siblings (e.g. a 'Gas usage' row). The 043 tests used
       two-family fixtures and could not surface this.
     · action: REVERTED (`git checkout -- backend/services/automatic_processing.py`), re-verified green
       (services 264 passed, engines 340 passed), reported instead of amending ratified tests.
11 LEGACY BYPASS ELIMINATED?  NO — the automated path can still let the keyword stage resolve a bare
     'Waste' to a Waste-oils component. Stated plainly: this is the remaining blocking item.
12 LIFECYCLE      Not implemented and still not required — the clarification record can be the source of
     truth, so no global item lifecycle change was made (same reasoning as 042/043).
13 PROVENANCE     The 041 value-level provenance is unchanged and tested (original activity, clarification,
     actor, scope, timestamp, policy input, outcome, factor metadata). No persistence exists to carry it.
14 D19 UI         NOT implemented.
15 CONSULTANT CLIENT PARITY  Not regressed (no behaviour change survives). Parity still binds the
     follow-up: the same clarification capability in the Consultant Client workspace, no cross-client
     access, no factor-library privilege.
```

## Why this window delivered less than the task, stated plainly

The mandated item is the real service wiring, so I built it first — the 043 gate at the mapping boundary,
## Items 16–30

```text
16 AUTHORIZATION/ISOLATION TESTS  NOT added (no table, repository or endpoint exists to test against).
     The required negatives remain: org A→B read/write, consultant→unauthorised client read/write,
     consultant client→another client, unrelated authenticated actor, unauthenticated actor.
17 SERVICE TESTS   264 passed (unchanged baseline) — no service test could be added for a wiring that is
     not in force.
18 PERSISTENCE TESTS  NOT added.      19 API TESTS  NOT added.      20 UI TESTS  NOT added.
21 D-A REGRESSION        PASS — unchanged; D-A policy 26 + discovery 9 green in this window's runs.
22 D-FS REGRESSION       PASS — policy module untouched; engines 340 passed.
23 039 REGRESSION        PASS — diesel ambiguity and waste-route semantics unchanged.
24 040/041/043 REGRESSION PASS — the 041 clarification suite (16 passed) and the 043 trigger suite
     (13 passed) are unchanged and green; the 043 gate is preserved exactly as delivered.
25 TEST COUNTS (final tree of this window)
     services 264 passed (1 warning) · engines 340 passed · 041 clarification 16 passed ·
     043 trigger 13 passed · D-A policy 26 · D-A discovery 9 · units 13/27/35
     NEW FAILURES: none — the transient 22-failure regression was reverted, not hidden.
26 FILES CHANGED  docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-044.md (this report only).
     The `automatic_processing.py` helper + gate edits were reverted and are NOT in the commit.
27 FACTOR DATA CHANGES   NONE.
28 PRODUCTION MIGRATION  NONE.
29 PRODUCTION DEPLOYMENT NONE (no production access, no Render/Vercel action, P1 remains SHADOW).
30 REMAINING LIMITATIONS / DEPENDENCIES
     F-044-1 (BLOCKING, precisely characterised) Refine the 043 gate's compatibility rule before wiring.
       "Families with disjoint scopes" is too coarse against real retrieval sets, because an ordinary
       activity's candidate window legitimately contains Scope-3 siblings. The evidence points to a rule
       that crosses the COMBUSTION vs NON-COMBUSTION/TREATMENT boundary explicitly — require the conflict
       to include a Scope-3 treatment/material family AND a Scope-1 combustion family for the same concept
       token, while treating Scope-1/Scope-2 combustion families as mutually compatible — and that rule
       must be validated against the real service fixtures (the 026 fixture corpus is the natural oracle)
       BEFORE any wiring. This is the mistake 042 made and 044 re-measured from the other direction.
     F-044-2 F-041-1 remainder: migration + RLS + repository + endpoints + D19 UI + negative isolation
       tests (design in the 041 report §6–§7; nothing applied).
     F-044-3 Lifecycle: still not required (same reasoning as 042/043).
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D / Phase 9 / G0-D / RLS steps 3–5 / MPG / billing /
  beta / demo environment / P1 remediation NOT touched · no factor-data change · no schema change ·
  no API/UI change · no migration created or executed · no deployment
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

This window could not deliver the mandated end-to-end path: the migration, persistence, RLS, repository,
API, D19 UI and — most importantly — the real service wiring all remain undone, and the legacy keyword
bypass is still in force for a bare 'Waste'. The one decisive new result is a measurement: the 043 gate is
correct on controlled candidate sets but its family-compatibility rule over-fires against real retrieval
windows (22 service failures), so it needs the narrower combustion-vs-treatment boundary described in
F-044-1 and validation against the real fixtures before wiring is attempted again. Everything already
delivered (D-A, D-FS-1…6, 039, 040, 041, 043) is intact and green, and no ratified test was modified.

diverting only on `clarification_required`, recording the real semantic groups through the existing
`unmapped` path with no factor id. The real suite then answered: 22 failures. The cause is a property of the
*gate*, not of the wiring — its disjoint-scope compatibility rule is too coarse once it meets the candidate
windows real retrieval produces, where ordinary activities legitimately see Scope-3 siblings. The synthetic
043 tests could not reveal that because they used two-family fixtures. That is now measured evidence rather
than a hypothesis, and the right response is neither to special-case the failing strings nor to amend 22
ratified tests, so I reverted and left the tree green.
