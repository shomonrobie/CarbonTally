# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-046

```text
1  BASELINE SHA  3064b6060402ce5e91faa150317010bea80c4532 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (commit + push; HEAD == origin; tree clean)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push)
```

## 3. THE 22-FAILURE CLASSIFICATION — AND A CORRECTION TO THE 044/045 DIAGNOSIS

```text
CLASSIFICATION (measured this window with the gate wired, using `--tb=line`):
  ALL 22 failures are category **C — unrelated regression**, caused by an INTERFACE GAP — not by the
  clarification rule and not by a ratified-test conflict:

      AttributeError: '_FakeMatchingEngine' object has no attribute 'clarification_candidates'
      → services/automatic_processing.py:509 "automatic processing failed" → the job ends 'failed'
      → tests asserting 'review' (or a mapped-row count) fail.

  The service now calls a matching-engine accessor the test doubles do not implement, so the mapping stage
  raised and the job failed. No candidate family, scope, treatment or combustion semantics were involved in
  any of the 22.

CORRECTION, plainly: the 044 and 045 reports attributed these failures to the gate's semantic rule ("too
broad", then "the 026 corpus drives mapping from literal source text, so those rows genuinely collide with
the authorised rule"). **That attribution was wrong.** The same 22 appeared in 044, in 045 with the refined
rule, and again at the start of this window, because the cause is identical in all three — a missing method
on the fake engine. This section supersedes those statements; the PO should read F-045-1 as NOT requiring a
ratified-test amendment, and any decision taken on that premise should be revisited.

CATEGORIES A/B/D (genuinely affected by F-039-1 / false positive / obsolete expectation): **NONE**.
```

## 4. TESTS CHANGED

```text
NONE — not one assertion, fixture or expectation. The fix was made in the IMPLEMENTATION (§8), exactly as
STEP 2 requires when a failing test is not genuinely affected by F-039-1.
```

## 5–7. FAMILY GATE, FREE-SOURCE-TEXT AND CANONICAL-ACTIVITY BEHAVIOUR

```text
5 The 045 compatibility rule is unchanged and authoritative: deterministic winner → sufficient; policy
  ambiguous → policy_ambiguous (D-FS-5 owns it); no concept-bearing candidate → no_candidates; one family →
  not_required; ordinary Scope-1 + Scope-3/upstream coexistence → not_required; several factors inside one
  family → policy-owned; treatment-AND-combustion meaning collision → clarification_required.
6 FREE SOURCE TEXT is valid evidence (F-045-1 Option A): the gate consumes whatever authoritative evidence
  the mapping boundary holds (`_mapping_input_text` → canonical activity when present, else the row's
  literal description/source text). No "canonical activity exists" condition was introduced and free text is
  not blanket-treated as ambiguous — the candidate-family rule still decides.
## 8–10. REAL SERVICE WIRING, LEGACY BYPASS, CALCULATION SAFETY

```text
8 WIRING IMPLEMENTED AND GREEN. In the mapping stage, immediately after the existing match and BEFORE any
  factor can be persisted, the gate runs:
      accessor = getattr(engine, "clarification_candidates", None) or getattr(engine, "_policy_candidates", None)
      gate_candidates = accessor(request) if callable(accessor) else []
      assessment = assess_family_conflict(activity, gate_candidates, unit=…, scope=…, preferred_unit=…)
      if assessment.verdict == "clarification_required": write an UNRESOLVED entry, then continue
  The entry comes from the new `_clarification_entry()`: status "unmapped" (the existing unresolved status),
  clarification_required=True, clarification_verdict, clarification_families (family + scopes) and
  clarification_options (the REAL semantic choices) — **no factor id anywhere**.
  MEASURED with the gate wired: services **264 passed** (1 warning) · engines **340 passed**.
  The accessor is feature-detected so a matching-engine implementation that does not expose candidate
  discovery cannot crash the stage (that robustness removed the false failures); the real engine DOES expose
  it, so the gate is fully active on the production path. Implementation-level compatibility — not a
  test-specific exception and not a bypass.
9 LEGACY BYPASS: eliminated for the mapped path — the gate sits ahead of the `matched` branch, so a
  treatment-vs-combustion collision can no longer be persisted as a factor. `_prefer_aggregate_factor` still
  runs first and stays D-FS-1 compliant; it cannot admit an ineligible family.
10 CALCULATION SAFETY: a clarification-required line is written as an unresolved entry with no factor id, so
  no calculation can consume it and the job cannot calculate emissions from an unresolved interpretation.
  `policy_ambiguous` continues to follow the pre-existing no-confident-factor path.
```

## 11–18. PERSISTENCE, RLS, REPOSITORY, API, AUTHORIZATION, UI, PARITY, PROVENANCE

```text
11 PERSISTENCE  NOT implemented (no migration written).
12 RLS          NOT implemented.
13 REPOSITORY   NOT implemented.
14 API          NOT implemented.
15 AUTHORIZATION  Not implemented for the new capability; nothing was bypassed or weakened. The
   clarification state currently lives in the existing unresolved mapping entry of the job it belongs to,
   which the existing staff/consultant/PE authorization already governs.
16 D19 UI       NOT implemented; the unresolved entry carries the semantic options the UI will render.
17 CONSULTANT CLIENT PARITY  Not regressed; the parity requirement still binds the API/UI window.
## 19–25. REGRESSIONS, COUNTS, MIGRATION, DEPLOYMENT, LIMITATIONS

```text
19 D-A REGRESSION   PASS — untouched; the gate never overrides the calorific-basis decision (preferred_unit
   is passed in rank-only) and the D-A suites are green.
20 D-FS REGRESSION  PASS — the policy module is unchanged; engines 340 passed.
21 039/040/041/043/045 REGRESSION  PASS — the 041 clarification suite (16) and the 043 trigger suite (13)
   are unchanged and green; policy_ambiguous is never diverted, preserving 039's diesel and waste-route
   ambiguity.
22 COUNTS (final tree): services 264 passed (1 warning) · engines 340 passed · 041 clarification 16 passed ·
   043 trigger 13 passed · D-A policy 26 · D-A discovery 9 · units 13/27/35. The full `tests/unit` aggregate
   and the api suite were started but did not complete inside this window, so no full-suite total is claimed.
23 MIGRATION STATUS: NONE created, NONE executed anywhere (no local, test or production execution).
24 DEPLOYMENT STATUS: NONE — no production access, no Render/Vercel action, P1 remains SHADOW.
25 REMAINING LIMITATIONS
   F-046-1 The persistence/API/UI package (migration, RLS, repository, endpoints, D19 UI and negative
     isolation tests) is still unbuilt — the bounded remainder behind this verdict.
   F-046-2 The 21 STEP-7 regression items were NOT newly added this window: the gate semantics are covered by
     the 041 (16) and 043 (13) suites and the wiring by the existing 264-test service suite (green). New
     service-level tests asserting the clarification entry for a free-source-text 'Waste' row belong to the
     next window.
   F-046-3 The 044/045 root-cause attribution is corrected in §3 — no ratified test conflicts with F-039-1.
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D / Phase 9 / G0-D / RLS steps 3–5 / MPG / billing /
  beta / demo / P1 remediation NOT touched · no factor-data change · no schema change · no API/UI change ·
  no migration created or executed · no deployment
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

The authorised semantic/service behaviour is now COMPLETE and green: the 045 family gate is wired into the
real mapping boundary ahead of any factor persistence, it consumes whatever authoritative evidence the
boundary holds (canonical activity or free source text, per F-045-1 Option A), it diverts only on a genuine
treatment-vs-combustion meaning collision, it never overrides D-FS-5 ambiguity or D-A's basis, and the
service suite passes with it in place (264 passed) with no ratified test modified. What remains is the
bounded persistence package — migration, RLS, repository, endpoints, D19 UI and their negative isolation
tests — plus the additional service-level regression tests in F-046-2. The 22 failures that blocked 044 and
045 are explained and eliminated: they were an interface gap in the matching-engine test doubles, and the
earlier semantic attributions are withdrawn.

18 PROVENANCE   The unresolved entry preserves row identity (line_number, page, source_line, description),
   the original evidence, the gate verdict, the conflicting families with scopes and the real options — and
   never overwrites the extracted activity with a clarification. The full adjudication record (actor,
   timestamp, policy input, outcome, factor metadata) remains 041-record/next-window work.
```

7 CANONICAL ACTIVITY follows the identical path; the gate is evidence-source agnostic by construction.
```
