# CT-STEP2-FACTOR-SELECTION-F039-1-USER-ASSISTED-AMBIGUITY-040

```text
BASELINE SHA   bcadbfc923bbce511ded1a6d52605284335e602d  (branch p8-release-reconciled)
               origin/p8-release-reconciled = bcadbfc…2d
               working tree: clean except the previously-uncommitted 039 verification report (left
               uncommitted by that task's instruction; committed here so the tree finishes clean)
FINAL SHA      recorded in the completion summary. THIS WINDOW MADE NO SOURCE/TEST/SCHEMA CHANGE:
               the deliverable is this gap report and the verdict is BLOCKED.
FILES CHANGED  docs/cline/reports/CT-STEP2-FACTOR-SELECTION-F039-1-USER-ASSISTED-AMBIGUITY-040.md (new)
               docs/cline/reports/…-039-INDEPENDENT-VERIFICATION.md (previously generated, now committed)
               NO application, test, configuration, schema or factor-data file was modified.
```

## 4. EXISTING AMBIGUITY ARCHITECTURE (inspected — what actually exists)

```text
ENGINE / POLICY SIDE — DELIVERED AND VERIFIED at this baseline (039):
  · FactorMatchingEngine returns MatchResult(status="ambiguous", suggestions=…) — the pre-existing
    ambiguity mechanism;
  · factor_selection_policy.select_factor() returns SelectionOutcome(status="ambiguous", eligible=(…),
    groups=(…)) where groups are (family, treatment route, product variant) tuples — i.e. the ELIGIBLE
    SEMANTIC GROUPS a clarification UI needs are ALREADY computed and exposed;
  · verified real-data behaviour: bare 'Waste' → the policy abstains (not_applicable) and the keyword
    stage resolves 'Waste oils (kg CO2e of CH4 per unit) [tonnes]'; 'Waste disposal' → ambiguous across 5
    treatment routes; named routes select deterministically.

APPLICATION SIDE — WHAT EXISTS TODAY:
  · item status lifecycle (free-text values passed to manual_extraction.set_item_status):
      extracted · mapping · mapped · validated · calculated · reviewed · customer_review
      → there is NO clarification-required / clarification-supplied / clarified state;
  · manual mapping surface: api/v3_operations.py `mapping_options` (:1576) returns, for an item,
      facilities/assets/suppliers + `factors` (from factors.find_by_activity) + customer_factors +
      `no_factors_reason` + `spend_suggestion`; `map_item` (:1718) writes the mapping and sets the item
      status to "mapping"/"validated". That is a FACTOR-ORIENTED picker — the PO decision explicitly
      forbids making factor choice the user's clarification surface;
  · a separate, DIFFERENT "clarification" concept exists: MEDIATED clarifications (entity staff →
      CarbonTally, "NEVER customer-facing") in v3_operations.py (:1045, :1339), v3_pe.py (:477) and
      domain/issue.py — an internal issues lifecycle, not customer/consultant semantic adjudication of an
      ambiguous activity;
  · authorization: operations_auth.ensure_entity_review_scope · consultant_auth.ensure_consultant_
      review_authorized · pe_auth capability map (read_work/process/review/qc/communicate) — a review
      model exists and could gate an adjudication action, but NO capability is defined for "clarify an
      ambiguous activity";
  · persistence: manual_extraction exposes save_extracted_data / save_mapped_data / set_item_status and
      items carry extracted_data / mapped_data payloads. There is NO structure representing an
      ADJUDICATION EVENT (actor + timestamp + original activity + user-supplied semantics + policy re-run
      outcome) distinct from those data payloads.
```

## 5–6. REQUIRED FLOW vs AVAILABLE ARCHITECTURE

```text
REQUIRED BY THE PO DECISION                     AVAILABLE?
1 ambiguity with eligible semantic groups        YES  (select_factor → eligible/groups; verified)
2 re-run the policy with augmented activity      YES  (select_factor is pure; a caller can pass the
                                                       original activity plus the user's semantics)
3 present SEMANTIC choices (not factor IDs)      NO   (mapping_options is factor-oriented; its
                                                       no_factors_reason/spend guidance is mapping
                                                       guidance, not semantic clarification)
4 persist "clarification required" per row       NO   (no such value in the item lifecycle)
5 persist clarification + actor + timestamp,     NO   (no adjudication-event structure; writing it into
  separate from document evidence                       extracted_data/mapped_data would be the ad-hoc
                                                        mechanism the task forbids)
6 authorization for the new action               PARTIAL (review/QC capabilities exist; none is defined
                                                        for clarifying an ambiguous activity)
7 keep the item review-required if declined      YES  (mapping / reviewed / customer_review exist)
```

## 7–10. BARE-WASTE / WASTE-OILS / DISPOSAL / ROUTE EVIDENCE (verified 039 baseline)

```text
CASE 1 'Waste' (60 t)  → engine: matched 'Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit)
                          [tonnes]' 3.5504 via keyword_search; policy: not_applicable (the bare token
                          carries no treatment marker) ⇒ the PO's "must not select Waste oils
                          automatically" is NOT yet satisfied.
CASE 2 'Waste oils'    → matched waste-oil aggregate 2.74924 (litres) — sufficient evidence; no
                          clarification needed (already correct).
CASE 3 'Waste disposal'→ ambiguous across 5 routes; Waste oils excluded with the reason "fuel concept
                          where a waste treatment/disposal concept was requested".
CASE 4 '… Landfill'    → matched Landfill 1.26338 (no clarification required).
CASE 5 '… Open-loop'   → matched Open-loop 1.00835.
CASE 6/7 clarification → NOT IMPLEMENTABLE IN THIS WINDOW (§4/§5 gaps 3–5).
CASE 8 "I don't know"  → the engine has no-match/ambiguous states that leave an item unresolved, but no
                          persistence of the user's refusal exists.
CASE 9 stale choice    → the policy would return ambiguous or no_eligible_candidate; surfacing that
                          explanation needs the same missing API surface.
⇒ Cases 2–5 are ALREADY satisfied by the verified 039 baseline; cases 1 and 6–9 depend on the same
  missing application-level capability.
```

## 11. USER ADJUDICATION PROVENANCE

```text
Required: original evidence | original activity | user clarification | actor | timestamp | selected factor
| factor metadata | policy stages — with document evidence and user adjudication kept DISTINCT and the
original activity never overwritten.
CAN DO: keep document evidence intact (extraction output is separate from any mapping write) and expose
the selected factor with full metadata plus the policy stage list (039).
CANNOT DO: record the adjudication EVENT — no per-row clarification field, no documented clarification
status, no adjudication provenance record. The only "clarification" artefact in the schema is the mediated
internal issue, a different CarbonTally-internal workflow. Writing an adjudication event into
extracted_data/mapped_data would be the uncontrolled ad-hoc mechanism the task forbids.
```

## 12. AUTHORIZATION EVIDENCE

```text
PRESENT: staff/consultant/PE review authorization (operations_auth.ensure_entity_review_scope ·
consultant_auth.ensure_consultant_review_authorized · pe_auth capability map), organization-scoped staff
contexts (require_staff, StaffContext) and RLS-backed repositories. Nothing in this window bypassed
authorization — no endpoint was added or changed.
ABSENT: an authorization decision for the NEW action ("clarify an ambiguous activity for this row"). Which
role may clarify (customer Owner/Member? consultant? PE operator? CarbonTally QC?) is a PO/product
authorization decision; inventing it — or silently reusing an unrelated capability — would breach the
task's rule against introducing a new role and would weaken the isolation guarantees it requires.
```

## 13–14. D-A AND D-FS REGRESSION

```text
## 18. RECOMMENDED SMALLEST BOUNDED OPTIONS FOR THE PO

```text
OPTION 1 (recommended) — a first-class clarification capability, smallest correct shape: one new table
  `activity_clarifications` (item_id, original_activity, offered_groups, chosen_semantics, actor_id,
  actor_role, created_at, policy_outcome, selected_factor_id, factor_set/source/year) plus one item status
  value `clarification_required`; two endpoints (GET semantic choices derived from select_factor
  eligible/groups; POST clarification → re-run the policy → matched | still_ambiguous |
  no_eligible_candidate) and D19 UI wiring. Requires a migration and a PO decision on who may clarify. No
  change to retrieval, the policy, D-A or D-FS.
OPTION 2 (interim, no migration) — do not offer clarification yet: make the ambiguity EXPLICIT in the
  existing review flow by routing any ambiguous item (and any bare 'Waste'-class activity whose policy
  verdict is not_applicable) into the existing mapping/review queue with the eligible-groups evidence
  attached, so a human resolves it through the EXISTING factor-mapping surface and statuses. Satisfies
  "never guess" with no schema change, but does not implement the semantic clarification UI.
OPTION 3 — extend the existing mediated-issue model (domain/issue.py) with an activity-clarification
  subtype. Reuses an existing lifecycle, but that model is CarbonTally-internal mediation ("never
  customer-facing"), so it does not satisfy the customer/consultant flow without redefining that boundary
  — needs an explicit PO ruling.
```

## VERDICT

**BLOCKED — ARCHITECTURAL / DATA / AUTHORIZATION GAP**

The task's stop conditions are met precisely: the required state model (ambiguous → clarification requested
→ user clarification supplied → resolved) is **not representable** by the existing ambiguity/review
lifecycle; persisting the user's adjudication as a distinct, auditable artefact requires a schema addition
(and writing it into the existing item data payloads would be the ad-hoc persistence mechanism the task
forbids); and the authorization model has no decision for who may clarify an ambiguous activity.
Implementing any of that by invention would silently expand scope, so this window modified **no** code,
tests, configuration, schema or factor data.

The good news is that the hard half is already done and verified: `factor_selection_policy.select_factor()`
already computes and exposes the eligible semantic groups a clarification UI must offer, and the engine
already returns an explicit ambiguity result — so the remaining work is a bounded application-surface
decision, not an engine redesign. The PO now has three options (Option 1 full clarification capability with
a migration; Option 2 route ambiguity into the existing review queue with no migration; Option 3 extend the
internal issue model), plus the open question of which role may clarify.

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D NOT STARTED
· NO factor-data changes · NO schema/migration change · NO configuration change
· NO production deployment · NO P1 activation (P1 remains SHADOW)
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```

NO CODE WAS CHANGED, so no regression can arise from this window. At the verified baseline (bcadbfc,
verification 039): 'Natural gas' kWh → Scope 1 aggregate 'Net CV' 0.20270 at confidence 1.0 (D-A intact);
D-FS-1 aggregate-over-component, D-FS-2 combustion/WTT separation, D-FS-3 scope eligibility, D-FS-4
treatment vs waste-oil separation, D-FS-5 explicit ambiguity and D-FS-6 hierarchy all remain as verified.
```

## 15. TESTS AND RESULTS

```text
NO TESTS WERE ADDED OR MODIFIED — the required 20 focused tests cannot be written against a capability
that does not exist, and placeholder tests would misrepresent the state.
BASELINE STATUS at the same SHA (039 verification): 039 suite 14 passed · policy 19 · engines 311 ·
services 264 · D-A policy 26 · D-A discovery 9 · units 13/27/35 · FULL tests/unit 2631 passed / 0 failed.
Not re-run here because nothing changed.
```

## 16. SCHEMA / DATA IMPACT

```text
NONE — no migration, schema file or factor-data row was touched. The blocking gap is precisely that the PO
workflow needs a persisted clarification state and an adjudication event the current schema does not
represent; that is a PO schema/data-model decision, not something to smuggle in under this bounded task.
```

## 17. LIMITATIONS OF THIS ANALYSIS

```text
· The signatures/columns behind save_mapped_data / save_extracted_data were not exhaustively read (the
  grep form used failed); they are item data payloads for the mapping flow and neither is documented as an
  adjudication record — a full contract read is the ONE remaining confirmation step before the PO chooses.
· The frontend (D19 workbench) surfaces were not re-inspected here; the API contract (mapping_options,
  map_item) indicates a factor-oriented mapping UI with no semantic-clarification step — consistent with
  the gap, but worth confirming visually before UI work is scoped.
· No production environment, queue, job or cloud surface was accessed.
```
