# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-041

```text
1 BASELINE SHA  f7eee2762ab9c15b0f42cf84f24f7928788e2eba (p8-release-reconciled; origin equal; clean tree)
2 FINAL SHA     recorded in the completion summary (code + report commit; pushed; HEAD == origin)
3 FILES CHANGED backend/engines/activity_clarification.py                     (NEW · clarification layer)
                backend/engines/factor_selection_policy.py                     (+9: public read-only
                                                                                treatment_route accessor)
                backend/tests/unit/engines/test_activity_clarification_041.py  (NEW · 16 tests)
                docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-041.md
                NO factor data, NO schema/migration, NO config, NO API/UI change, NO deploy.
```

## 4. ARCHITECTURE BEFORE / AFTER

```text
BEFORE (040): activity → retrieval → select_factor() → selected | ambiguous. For a bare generic activity
  ('Waste') the policy ABSTAINS (not_applicable) and the keyword stage silently resolved
  'Waste oils (kg CO2e of CH4 per unit)' — the PO's forbidden outcome. No first-class clarification
  concept, no lifecycle state, no adjudication record existed.

AFTER (041): the same chain, wrapped by a clarification layer —
  activity → retrieval candidates → select_factor()
     sufficient             → existing behaviour unchanged (D-A / D-FS / 039 intact)
     clarification_required → semantic options from the ACTUAL eligible groups + re-run path
     insufficient_evidence  → bare generic category (the F-039-1 rule) + re-run path
     not_required           → outside the policy's classes (e.g. water) → untouched
  A clarification is fed back as TEXT into the SAME select_factor() call
  (policy_input = "<original activity> <clarification>"); no factor id enters the flow.
```

## 5. LIFECYCLE DESIGN (value level; persistence is follow-up §6)

```text
clarification_required  ← ActivityEvidence.verdict (policy ambiguous, or a bare generic category)
clarification_supplied  ← ClarificationRecord.status on submission
resolved                ← outcome_status == "selected"
still_unresolved        ← outcome_status in {ambiguous, no_eligible_candidate, not_applicable}
unresolved_declined     ← decline_clarification(): status="declined", no factor, nothing calculated
New values belong to the clarification concept only — no existing item status was renamed, redefined or
removed, so existing lifecycle semantics are preserved and nothing was repurposed.
```

## 6. SCHEMA / MIGRATION — SPECIFIED, **NOT IMPLEMENTED** IN THIS WINDOW

```text
Split rationale: this window could not also produce a migration, its RLS, the repository, the HTTP
endpoints, the UI wiring and the API/RLS isolation tests, and shipping unverified migration + RLS would be
worse than specifying it. No migration file was created and no schema change was applied anywhere.

CONVENTIONS INSPECTED: supabase/migrations/<YYYYMMDDHHMMSS>_<slug>.sql; `CREATE TABLE IF NOT EXISTS
public.<t>`; `ALTER TABLE … ENABLE ROW LEVEL SECURITY`; RLS predicates on auth.uid() + org membership.

PROPOSED (next window) — public.activity_clarifications:
  id uuid PK · activity_key text NOT NULL · batch_id uuid FK→processing_batches ON DELETE CASCADE ·
  organization_id uuid FK→organizations ON DELETE CASCADE · original_activity text (SOURCE EVIDENCE,
  never mutated) · clarification text (USER EVIDENCE, separate) · clarification_type text
  (semantic_activity|declined) · offered_groups jsonb · policy_input text · outcome_status text
  (selected|ambiguous|no_eligible_candidate|not_applicable|unresolved_declined) ·
  selected_factor_id uuid FK→emission_factors ON DELETE SET NULL · factor_set/factor_source text ·
  reporting_year int · unit text · scope text · actor_id uuid · actor_scope text ·
  created_at timestamptz DEFAULT now() · UNIQUE (activity_key, original_activity, clarification)
  INDEX (organization_id, created_at DESC) · INDEX (activity_key)
  The UNIQUE constraint is what makes duplicate submissions idempotent at the persistence layer.
```

## 7. RLS DESIGN (specified)

```text
SELECT/INSERT scoped to the caller's organization membership for the affected organization_id; consultant
access only for authorized consultant-client organizations (mirroring the existing boundary); no
cross-organization read or write; internal access only via an existing authorized mechanism; the capability
is deliberately unrelated to factor administration. Negative isolation tests (org A→B, consultant→
unauthorised client) are mandatory in the window that applies the migration.
```

## 8. AUTHORIZATION DESIGN

```text
REQUIRED actors: organization users authorized for the organization's activity data; consultants
authorized for the affected client; consultant-client users per existing workspace permissions; internal
actors only through an existing authorized capability.
IMPLEMENTED: every record carries actor_id and actor_scope (attribution guaranteed by construction); the
layer grants no privilege of its own.
## 9–12. API / UI / FLOW / PROVENANCE

```text
API + UI: NOT IMPLEMENTED this window (no endpoint, no UI change). The smallest coherent integration for
the follow-up is one addition to the EXISTING workbench surface: the item view (which already renders
mapping candidates) gains a clarification panel when the verdict is clarification_required /
insufficient_evidence, showing the semantic options the layer returns; a POST submits the chosen
semantic_term → resolve_clarification(...) → the existing matching/selection continuation. No standalone
page, no new factor picker.

FLOW (implemented): activity + candidates → assess_activity_evidence() → options (family|route|variant
keys, human labels, semantic_term) → resolve_clarification(activity, term, candidates) → policy_input →
select_factor() → record(outcome_status, factor metadata) | decline_clarification() → unresolved.

PROVENANCE (value level): every record carries original_activity (document evidence, never mutated),
clarification (user evidence, separate), clarification_type, actor_id, actor_scope, created_at,
policy_input, outcome_status, selected_factor_id/name, factor_set, factor_source, reporting_year, unit,
scope, eligible_group_count and the eligible groups when still ambiguous. The chain document → extracted
activity → ambiguity → clarification → policy → factor → calculation survives intact, and user evidence is
never represented as document evidence.
```

## 13–15. REAL WASTE / LANDFILL / WASTE-OILS EVIDENCE (tests + 039-verified baseline)

```text
Bare 'Waste' (real dataset, 039 evidence): the engine matched 'Fuels > Liquid fuels > Waste oils (kg CO2e
  of CH4 per unit)' — forbidden. With the clarification layer (tested): verdict insufficient_evidence,
  selected_factor_id None, options = the real eligible groups (Waste treatment/disposal · Landfill /
  Open-loop / Incineration with energy recovery …). No Waste-oils option is offered for the bare term
  because the waste-oils candidate is not part of the eligible disposal groups.
'Landfill' clarification: policy_input 'Waste Landfill' → Landfill factor selected; the record keeps
  original 'Waste' and clarification 'Landfill' separately.
'Waste oils' clarification: policy_input 'Waste Waste oils' → the waste-oil aggregate is selected THROUGH
  the policy, never by id.
'Waste disposal' (no route): still clarification_required across the real 5 routes.
'Waste oils' evidence: verdict sufficient — no unnecessary clarification.
```

## 16–19. I-DON'T-KNOW / DIESEL / D-A / D-FS REGRESSIONS

```text
I don't know: decline_clarification() → outcome_status 'unresolved_declined', no factor; the declination
  word is never appended to the policy input (tested).
Diesel (039 regression): verdict clarification_required with both products eligible; clarification
  '100% mineral diesel' → the mineral factor is selected.
D-A (closed): the engine returns the Net-CV aggregate and the clarification layer returns sufficient /
  factor 'net' with preferred_unit 'kWh (Net CV)' — no CH4, no Gross CV.
D-FS: aggregate-over-component, Scope-1 vs WTT separation, scope eligibility, treatment vs waste-oils,
  explicit ambiguity and the deterministic hierarchy all unchanged (same policy module; the new code is an
  additive layer). Power still no_match through the engine; water → verdict not_required (untouched).
```

## 20. TEST RESULTS

```text
NEW  tests/unit/engines/test_activity_clarification_041.py   16 passed
     (bare Waste not resolved · no Waste-oils option · disposal needs a route · Waste oils sufficient ·
      route-specific sufficient · Landfill resolution through the policy · Waste oils not a bypass ·
      decline selects nothing · declination word not fed to the policy · stale/invalid clarification
      unresolved · deterministic + idempotent repeat · diesel ambiguity → clarification · Scope-1
      aggregate beats component and excludes WTT · WTT still selectable · water untouched · D-A Net CV
      through the engine)
REGRESSION  tests/unit/engines 327 passed · tests/unit/services 264 passed · D-A policy 26 passed ·
            D-A discovery 9 passed · units 13 passed — no new, pre-existing or infrastructure failures.
No existing test was modified.
```

## 21. MIGRATION SAFETY

```text
No migration was written or applied, so nothing can endanger existing data from this window. The proposed
design adds a NEW table only (no ALTER of existing tables), follows the existing FK/delete conventions,
introduces no factor-data change, and its UNIQUE constraint is additive. When applied it must be verified
against a disposable local clone per the project's destructive-test-safety invariant.
```

NOT IMPLEMENTED: the server-side permission check on an HTTP endpoint (no endpoint exists yet) — the
follow-up must reuse require_staff / operations_auth / consultant_auth / RLS and must not invent a role.
```

## 22. LIMITATIONS / FUTURE FOLLOW-UPS

```text
F-041-1  Apply the authorized migration + RLS + repository + endpoints + D19 UI wiring, with negative
         isolation tests (org A→B, consultant→unauthorised client, unauthorised actor) — the specific
         follow-up for this increment.
F-041-2  Wire the clarification verdict into the engine/service so a bare generic activity no longer
         proceeds to a silent keyword match in the automated path. Today the layer DETECTS and RECORDS the
         ambiguity, but the engine's keyword stage can still resolve it until the wiring lands — which is
         why the F-039-1 product rule is not yet end-to-end satisfied.
F-041-3  Optional item lifecycle value for "clarification required" (may be unnecessary if the
         clarification table is the source of truth for review queues).
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · D-B/C/D NOT STARTED
· NO factor-data changes · NO schema change applied (migration specified only) · NO configuration change
· NO production deployment · migration executed nowhere · NO P1 activation (P1 remains SHADOW)
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PO CLOSURE NOT CLAIMED
```
