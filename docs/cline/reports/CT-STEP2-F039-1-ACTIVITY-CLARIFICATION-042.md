# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-042

```text
1  BASELINE SHA  1c203b6f77ed9e2cc2bf819ffef96923aaa35d5f (p8-release-reconciled; origin equal; tree clean)
2  FINAL SHA     recorded in the completion summary (commit + push; HEAD == origin)
3  BRANCH        p8-release-reconciled (only branch touched; no reset/rebase/force-push)
4  GIT STATUS    clean at finish; only the files below changed
5  FILES CHANGED backend/engines/factor_matching.py  (+9/-0 — public `clarification_candidates(request)`
                 accessor delegating to the existing discovery helper; NO behaviour change)
                 docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-042.md
   REVERTED IN THIS WINDOW (see §11): the service-layer clarification gate I implemented in
                 services/automatic_processing.py and its wiring test file were removed with
                 `git checkout` / `rm` because they introduced a MEASURED regression. No service, engine,
                 schema, config or factor-data change from that attempt survives.
6  MIGRATION     NOT created — no migration file, no schema change applied anywhere.
7  MIGRATION EXECUTED locally/test-env?  NO — nothing was created and nothing was executed.
8  RLS           NOT implemented this window (the design specified in the 041 report §6–§7 stands).
9  REPOSITORY    NOT implemented this window.
10 API           NOT implemented this window.
11 SERVICE/ENGINE WIRING  NOT delivered — attempted, measured, and reverted:
     Implemented: after `_prefer_aggregate_factor`, call
       assess_activity_evidence(activity, engine.clarification_candidates(request), unit=…, preferred_unit=…)
     and, when the verdict was insufficient_evidence / clarification_required, write the line through the
     EXISTING `_unresolved_mapping_entry` path as status="unmapped" + clarification_required + the real
     eligible semantic groups (no factor id); `_clarification_entry()` was added for that purpose, and its
     unit behaviour was correct (bare 'Waste' → truthful unresolved entry, no factor id, real groups).
     MEASURED RESULT: including `clarification_required` → 23 service tests failed; narrowed to
     `insufficient_evidence` only → still 22 failed, e.g.
       tests/unit/services/test_multiline_provenance_mapping.py::
         test_row_without_a_keyword_reaches_the_matcher_with_its_source_text
         test_calculation_carries_per_row_provenance
     ROOT CAUSE (measured, not guessed): the generic-category rule is too blunt for the real fixtures — it
     fires for any activity whose whole token set is a category word, and the fixtures legitimately contain
     'Gas usage' (tokens {gas}) and 'Power consumption' (tokens {power}), which are NOT the PO's F-039-1
     scenario. Diverting those contradicts ratified 026/031 provenance behaviour, and narrowing by listing
     specific words would be the "special-case the strings" the task forbids. The action taken was to
     REVERT rather than amend ratified tests to hide the regression.
     CONSEQUENCE, stated plainly: the mandated end-to-end rule is NOT yet in force — the automated path
     can still let the keyword stage resolve a bare 'Waste' to 'Waste oils'.
12 LEGACY KEYWORD BYPASS ELIMINATED?  NO. The 041 clarification layer detects and records the ambiguity;
     the engine/service boundary does not yet divert on it (§11).
```

## Why this window delivered less than the full task

STEP 6 is the item that makes F-039-1 real, so I implemented it first — and it produced hard evidence
against shipping as written. At the unit level the gate works exactly as intended (a truthful `unmapped`
entry carrying the real eligible groups for bare 'Waste', no factor id, provenance intact), but in the
real service fixtures the same trigger also fires on activities that are not the PO's scenario, breaking 22
## Remaining items 13–22

```text
13 D19 UI        NOT implemented this window.
14 CONSULTANT CLIENT PARITY  Unchanged and NOT regressed (no behaviour change survives). The parity
     requirement still binds the follow-up: the clarification capability must appear in the Consultant
     Client workspace wherever the Organisation activity workflow exists, with no cross-client access and
     no factor-library privilege.
15 AUTHORIZATION / ISOLATION TESTS  NOT added (no endpoint or table exists to test against). The required
     negatives remain: org A→B read/write, consultant→unauthorised client read/write, consultant client→
     another client, unauthorised actor, unauthenticated actor.
16 PROVENANCE TESTS  Partially covered by the 041 suite (16 tests: original activity preserved,
     clarification kept separately, actor/scope/timestamp/policy input/outcome/factor metadata retained,
     declined clarification auditable). No new provenance tests this window.
17 D-A REGRESSION  PASS — unchanged; D-A policy 26 passed and discovery 9 passed re-run green; the engine
     still returns the Net-CV aggregate.
18 D-FS REGRESSION PASS — the policy module was not changed this window (the 041 `treatment_route`
     accessor is read-only and predates this window); engines 327 passed.
19 039 REGRESSION   PASS — 039 suites unchanged and green (diesel ambiguity, waste routes, WTT, power,
     water as independently verified).
20 TEST COUNTS (final state of this window's tree)
     tests/unit/services 264 passed (1 warning) · tests/unit/engines 327 passed ·
     tests/unit/engines/test_activity_clarification_041.py 16 passed ·
     tests/unit/test_d_a_natural_gas_basis.py 26 passed · D-A discovery 9 passed · units 13 passed
     NEW FAILURES: none — the transient regression was reverted, not concealed.
21 REMAINING LIMITATIONS / FOLLOW-UPS
     F-042-1 (blocks the product rule) Define, at PO level, when the automated path must divert to
       clarification. The evidence supports a FAMILY-level test — divert when the request's semantic class
       cannot be established AND the retrieved candidates span materially different factor families
       (e.g. waste disposal vs fuel) — rather than a category-word test. That definition must precede
       re-applying the gate, and the 026/031 fixtures must be re-checked against it.
     F-042-2 F-041-1 remainder: migration + RLS + repository + endpoints + D19 UI + the negative isolation
       tests (design specified in the 041 report §6–§7; nothing applied).
     F-042-3 F-041-3: NOT implemented and NOT required — the activity_clarification record can safely be
       the source of truth, so no global item lifecycle value was introduced (the task preferred avoiding
       unnecessary lifecycle complexity).
22 PRODUCTION DEPLOYMENT STATUS  NONE. No production access, no migration executed anywhere, no Render or
     Vercel action, no P1 activation (P1 remains SHADOW).
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D NOT STARTED · Phase 9 / G0-D / RLS steps 3–5 /
  MPG / billing / beta / demo-environment / P1 remediation NOT touched
· NO factor-data changes · NO schema change applied · NO configuration change · NO deployment
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

Not IMPLEMENTED, because the mandated end-to-end rule (bare 'Waste' must not auto-resolve) is not in force
and the persistence/API/UI half is absent. Not BLOCKED, because both remainders are bounded and specified:
F-042-1 needs a PO definition of the diversion trigger (family-level, with the 026/031 fixtures re-checked),
and F-042-2 is the already-designed migration/RLS/API/UI package. The 041 clarification engine remains
intact, tested and green, and no regression survives this window.

ratified tests. The two wrong ways forward were both forbidden (special-casing the offending strings;
amending ratified tests to make the gate look safe), so I reverted the wiring and left the tree green,
keeping only a harmless public accessor.
