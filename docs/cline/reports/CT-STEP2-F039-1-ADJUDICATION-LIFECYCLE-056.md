# CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-056

```text
1  BASELINE SHA   3e11155e5beeb98098de0ca2d933983f75d319fd
2  FINAL SHA       recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH          p8-release-reconciled (no reset / rebase / force-push)
4  HEAD==origin    verified after push
5  GIT STATUS      clean at finish
6  COMMITS         the repository-lifecycle commit (see summary)
7  FILES CHANGED
     backend/data/activity_clarifications.py                    (lifecycle: versioned writes + reads)
     backend/tests/unit/data/test_activity_clarifications_repository.py  (+4 lifecycle tests; 2 assertions
                                                                         updated for the 055 constraint rename)
     backend/tests/unit/api/test_v3_activity_clarifications_api.py       (2 assertions updated, same rename)
     docs/cline/reports/CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-056.md
8  MIGRATIONS       NONE added or changed — the 055 schema is used exactly as delivered
9  API CHANGES      NONE  (existing endpoints keep working against the lifecycle schema)
10 SERVICE CHANGES  NONE
11 PRODUCTION       NOT touched · nothing applied to production · NOTHING DEPLOYED
12 UI / D19         NOT modified (not authorised)
```

## WHAT IS IMPLEMENTED (repository layer, tested)

```text
A. Create initial adjudication
   `record()` now writes the 055 lifecycle columns (adjudication_id, version,
   supersedes_id, is_current, effective_context_key, evidence_signature,
   evidence_context) — generated identity, version 1, is_current when none is supplied.
   Factor metadata still comes only from the engine's ClarificationRecord.

B. Context-bounded effective lookup — `effective(organization_id, activity_key,
   original_activity, context_key)` requires the FULL boundary (organization_id AND
   effective_context_key AND activity_key AND original_activity AND is_current). It
   deliberately cannot be queried by activity text alone — exactly what D-039-1-C
   forbids. Test asserts the SQL carries that boundary.

C. Modification creates a version — `apply_versioned(...)`:
     no effective adjudication           → version 1
     SAME clarification already effective → replay (no insert, no overwrite)
     DIFFERENT clarification             → version+1, same adjudication_id,
                                           supersedes_id = previous row id, then
                                           `supersede()` flips the old row's is_current.
   `supersede()` sets is_current (+ updated_at) ONLY — asserted: no clarification,
   outcome or factor column is touched, so prior versions keep their own factor
   metadata (D-039-1-D/-H).

D. History — `history(adjudication_id, organization_id)`: all versions,
   `ORDER BY version ASC`, tenant-scoped.

E. Replay/idempotency — the INSERT conflicts on
   `activity_clarifications_replay_unique` (activity_key, original_activity,
   clarification, version), then re-reads that exact version: replay returns the stored
   row rather than duplicating or overwriting.

F. Factor metadata — unchanged and still server-only
   (`test_no_authoring_method_accepts_factor_metadata` still passes).
```
Integration point worth noting: 055 replaced `activity_clarifications_unique` with the
version-aware constraints, so the repository's conflict target moved to
`activity_clarifications_replay_unique` and the re-read now filters `version`. That is a
necessary consequence of the accepted 055 schema — not a schema change.

## TESTS ADDED / CHANGED AND EXACT RESULTS

```text
ADDED (repository, 4): effective lookup requires the full context boundary ·
      modification creates a new version and retires the previous (asserting that
      adjudication_id/version/supersedes_id reach the INSERT and that only is_current
      changes on the old row) · identical clarification is a replay, not a new version ·
      history is deterministic oldest-first and tenant-scoped
CHANGED (assertions only, 4): conflict target renamed to
      activity_clarifications_replay_unique (2 API + 1 repository) and the version
      filter added to the replay re-read (1 API)
SUITE RESULTS (executed; pytest exit code 0 = all collected tests passed)
  tests/unit/data/test_activity_clarifications_repository.py        12 tests · exit 0
  tests/unit/api/test_v3_activity_clarifications_api.py             27 tests · exit 0
  tests/unit/services                                              exit 0
  tests/unit/engines/test_factor_selection_policy.py (D-A / D-FS)   exit 0
  tests/unit/engines/test_activity_clarification_041.py            exit 0
```
No aggregate beyond these files is claimed, and no previously recorded total is presented
as re-run.


## NOT IMPLEMENTED — REMAINING SCOPE (nothing half-written)

```text
F1  consumption of the effective adjudication by automatic processing —
    `services/automatic_processing.py` still returns clarification_required because the
    gate does not load the effective adjudication. What it needs is now in place: the
    schema (055), the bounded context rule and the repository `effective()` lookup.
F2  HTTP provenance derivation (item_key / batch_key / source_evidence_ref from the
    persisted item → batch → organization) — the endpoints still persist NULL provenance
F3  the decline gate — `/decline` still accepts a decline for a deterministic activity
F4  authoritative unit/scope — the request body can still supply unit/scope as policy inputs
API  no history/current-read endpoint and no narrow modification endpoint were added
TESTS  service-lifecycle, API-lifecycle and RLS-extension tests not written (dependent on F1–F4)
DB VERIFICATION  no NEW DDL or lifecycle round-trip was executed this window. The standing
    evidence remains the 055 verification (schema applied, one-current invariant enforced,
    v1 preserved, replay rejected). The new repository code path was verified by unit tests
    ONLY — not against the live disposable database. That limitation is stated, not glossed.
```

## KNOWN PRE-EXISTING FAILURES (untouched)

`F-051-1` still pins 71 migrations; the tree holds 74 (unchanged this window — I added no
migration). NOT modified. `test_review_sla_surfaces`, `test_p6_1b_*`, the stale disposable
integration environment and the missing 7049-factor dataset were not touched, and no
baseline comparison was run for them, so no claim is made either way. The services suite —
the most relevant regression surface for F1 — passes.

## VERDICT

**IMPLEMENTATION PARTIAL — the adjudication repository lifecycle (versioned create, bounded
effective lookup, immutable history, replay, supersede) is implemented and tested; F1
consumption, F2 provenance, F3 decline gate, F4 authoritative unit/scope, the narrow
history/modification API and the service/API/RLS lifecycle tests remain unimplemented.**

No independent verification was performed, no PO closure is claimed, production was not
touched, and nothing was deployed.
