# CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-059

```text
STARTING SHA  c83233fb4ffc6f2279e085c42cff62f7d062d662  (baseline verified: branch correct,
              HEAD == origin, working tree clean)
FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
BRANCH        p8-release-reconciled — no reset / rebase / force-push
MIGRATIONS    NONE — the 055 schema is untouched
PRODUCTION    NOT touched · no production migration · NOTHING DEPLOYED
UI / D19      NOT modified · F-051-1 NOT modified
```

## F1 — IMPLEMENTED (`0c06105`)

`backend/services/automatic_processing.py`, two changes:

1. **New private method `_consume_effective_adjudication(...)`**, defined immediately before
   `_map()` (the gate's enclosing method):

```text
context      bounded to `job.source_item_id` — the extraction item identity the service already
             uses for every other item-scoped operation (source_item_id=job.source_item_id in the
             calculation step). No broader scope, no global/organization/consultant rule.
evidence     `resolve_evidence(item_id, activity)` → the 058 server-derived provenance plus the
             authoritative unit/scope from the persisted extracted_data line.
compat       `effective_compatible(...)` (D-F039-1-I): reuse only when the stored signature equals
             the CURRENT evidence signature. A missing signature, a different signature, or
             `re_evaluation_required` all return None → the existing diversion is preserved and the
             adjudication is never silently reused or overwritten.
policy       `resolve_clarification(activity, stored_clarification, candidates, unit, scope)` — the
             EXISTING policy. If it selects nothing, the row is not consumed: ambiguity stays
             unresolved and nothing is guessed.
mapping      the match is re-issued through `self._matching_engine.match(...)` with
             `record.policy_input` — the same pipeline the gate already trusts — and the caller's
             existing confidence check then decides.
bypass       the stored `selected_factor_id` is NEVER read; it stays historical/audit metadata.
resilience   any exception inside consumption is caught, logged and returns None, so consumption can
             never break processing.
```

2. **The gate** now calls that method before diverting. If it returns `None` the original
   `clarification_required` diversion (reason + `_clarification_entry`) runs unchanged; otherwise the
   consumed result flows into the pre-existing confidence checks, which still route to the unresolved
   path when the match is not confident.

Invariant preserved: `persisted evidence → effective adjudication → compatibility check → semantic
clarification → existing policy → factor / ambiguity / unresolved`.

## FILES CHANGED

```text
0c06105  backend/services/automatic_processing.py   (F1 — the only code change this window)
         docs/cline/reports/CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-059.md
```

## TESTS RUN AND EXACT RESULTS

```text
tests/unit/services                                        exit 0
tests/unit/api/test_v3_activity_clarifications_api.py      exit 0
tests/unit/data/test_activity_clarifications_repository.py exit 0
```
**Honest qualification:** these prove *no regression*, not the new path. Every existing service test
exercises the old behaviour (its repo bundle has no `clarifications` attribute, so consumption returns
None by design). The dedicated service-level lifecycle tests (Tests 1–8) were **not written**, so the
new behaviour is currently unverified beyond code inspection. That is the precise remaining gap. No
test was weakened or modified.

## AUTHORIZATION / TENANT ISOLATION

Unchanged. F1 adds no authorization surface: it reuses the already-authorised `job` and the
repository's tenant predicates (`organization_id` on every read). No new role, grant, policy or
reuse scope was introduced.


## REMAINING SCOPE (nothing half-written)

```text
1. Service-level lifecycle tests — Tests 1–8 of the brief (no adjudication · compatible consumption ·
   selected-factor bypass protection · changed signature · ambiguous after clarification · v1/v2
   effective-version · tenant isolation · consultant client). This is the verification of the code
   added here and is the largest open item.
2. Current/effective read endpoint and history read endpoint (narrow, authenticated, tenant- and
   consultant-client-scoped, using the existing `effective()` / `history()` repository methods rather
   than new queries).
3. API read tests for those two endpoints.
4. Broader regression run — D-A, D-FS, 039, 041, 043, 045 were green in 058 and are untouched by this
   service-only change, but were NOT re-run in this window; no total is claimed for them.
5. Disposable-DB verification for F1: not performed (no DDL changed; 055's verification stands).
```

## KNOWN PRE-EXISTING FAILURES

`F-051-1` still pins 71 migrations against the tree's 74. NOT modified, as instructed. The other known
baseline failures were not touched and no baseline comparison was run for them in this window.

## VERDICT

**IMPLEMENTATION PARTIAL — F1 automatic-processing consumption is implemented and committed
(regression-green), but its dedicated service-level lifecycle tests, plus the current/history read
endpoints and their API tests, remain outstanding.**

No independent verification was performed, no PO closure is claimed, production was not touched, and
nothing was deployed.
