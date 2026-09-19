# CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-055

```text
1  BASELINE SHA   0be7438ddbd1f05c004246cbafc844cbdb1af319
2  FINAL SHA       recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH          p8-release-reconciled (no reset / rebase / force-push)
4  HEAD==origin    verified after push
5  GIT STATUS      clean at finish
6  COMMITS         the schema-increment commit (see summary)
7  FILES CHANGED
     supabase/migrations/20260930000000_p8_fs_adjudication_lifecycle.sql   (new)
     docs/cline/reports/CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-055.md      (new)
   NO Python / API / service / frontend file was modified in this window.
8  MIGRATIONS ADDED      1
9  TESTS ADDED/CHANGED   0 (see "Why no test file was added")
10 PRODUCTION           NOT touched · nothing applied to production · NOTHING DEPLOYED
11 D19/UI               NOT modified (not authorised)
```

## 15/17 — DISPOSABLE DATABASE VERIFICATION (actually executed)

Environment: the dedicated disposable `carbontally_test`
(`postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test`), guarded by the F-046-1
invariant. Production was never contacted.

```text
MIGRATION APPLIED ✓ · RE-APPLIED (idempotent) ✓
new columns: adjudication_id · version · supersedes_id · is_current ·
             effective_context_key · evidence_signature · evidence_context ·
             re_evaluation_required
old constraint dropped: activity_clarifications_unique removed ✓
constraints now: version_unique(adjudication_id, version) ·
                 replay_unique(activity_key, original_activity, clarification, version) ·
                 supersedes_fkey → self (ON DELETE SET NULL)
indexes: current_unique (partial, WHERE is_current) · effective_idx · history_idx
rls: ENABLED ✓ · policies: 4 (unchanged tenant matrix)

LIFECYCLE BEHAVIOUR PROVEN AT RUNTIME
  v1 Landfill      inserted → is_current true
  v1 superseded    is_current=false, then version 2 inserted (supersedes_id = v1.id)
  history          [(1,'Landfill',False), (2,'Incineration',True)]
  current versions 1   (exactly one effective version)
  v1 preserved     clarification 'Landfill' and factor_set 'DEFRA-2025' unchanged      ✓
  one-current rule enforced by the partial unique index — an out-of-order insert was
      REJECTED with UniqueViolationError on activity_clarifications_current_unique   ✓
  replay of an existing (clarification, version) REJECTED by replay_unique             ✓
  cleanup: 0 rows left (only rows this verification created were deleted)              ✓
```

## WHAT IS IMPLEMENTED vs NOT (exact scope)

```text
IMPLEMENTED + RUNTIME-VERIFIED IN THE DISPOSABLE DB
  D-F039-1-D  immutable versioned history schema: stable adjudication identity, version
              number, supersedes linkage, exactly one current/effective version
  D-F039-1-A  the row can now carry the full adjudication record A requires (identity,
              context, actor, timestamps, outcome, factor metadata, evidence context)
  D-F039-1-C  bounded reuse scope is representable (effective_context_key). NO global /
              organization-wide / consultant-wide / cross-client rule was introduced
  D-F039-1-F  provenance context column (evidence_context jsonb) for authoritative linkage
  D-F039-1-G  compatibility/conflict signal column (evidence_signature)
  D-F039-1-H  factor-set context is preserved per version and flagged rather than rewritten
              (re_evaluation_required); no factor migration system was added
  RLS/GRANTs  unchanged — RLS still enabled, same four tenant policies, same grants

NOT IMPLEMENTED — REMAINING SCOPE (not started, nothing half-written)
  Finding 1  consuming the effective adjudication in automatic processing — the gate in
             `services/automatic_processing.py` still returns clarification_required because
             nothing reads the persisted adjudication
  Finding 2  HTTP provenance linkage (item_key/batch_key/source_evidence_ref derived
             server-side from the persisted extraction item; forged provenance rejected)
  Finding 3  the decline gate (`/decline` still permits a decline on a deterministic activity)
  Finding 4  authoritative unit/scope (the body can still supply unit/scope as policy inputs;
             `manual_extraction_items` has NO unit/scope columns — the authoritative values
             live in `extracted_data` JSONB, which is where the derivation must read them)
  Repository versioning methods (new-version-on-modification, effective lookup, history read)
  Narrow adjudication history/current-read API surface
  All focused lifecycle tests
```

## WHY NO TEST FILE WAS ADDED

The mandate requires every modification to be tested before it is committed. The only artefact
here is a migration, and its verification is runtime DDL/invariant verification in the
disposable database (recorded above), not pytest. A test file now would have to assert on the
repository/API/service code that does not exist yet, so none was added.

## WHY I STOPPED AT THE SCHEMA BOUNDARY

The remaining work is the code layer. The service-consumption path changes behaviour inside the
live automatic-processing gate (whose suite is currently green), and the unit/scope correction
requires deriving authoritative values from `extracted_data` JSONB line items. Landing either
without being able to run and verify it would be the half-tested commit the mandate's

## 15 — KNOWN PRE-EXISTING FAILURES (untouched by this increment)

```text
F-051-1  test_d17_provider_ownership_migration_revision.py pins 71 migrations; the tree now
         holds 74 (this window added one). NOT modified — it remains a separately recorded
         issue needing an authorised decision. For the record: this increment necessarily
         increases the count that guard pins, so that decision is now more pressing.
test_review_sla_surfaces · test_p6_1b_* route-introspection failures · stale disposable
integration environment · missing 7049-factor dataset — none touched, none investigated.
```
No baseline-vs-increment comparison was run for these (no code changed this window), so no
claim is made about them either way.

## AUTHORIZATION / RLS VERIFICATION STATUS

Not re-exercised, because no code changed. RLS remains **enabled** on the table with the same
four tenant policies and the same grants (verified above); the standing behavioural evidence
remains the 27/27 matrix recorded in 050. No permission was broadened, no role added, no policy
altered.

## 20 — REMAINING BLOCKERS / LIMITATIONS

```text
F-055-1  Independent-verification Findings 1–4 remain OPEN (none started)
F-055-2  repository versioning + effective/history reads not implemented
F-055-3  service consumption of the effective adjudication not implemented
F-055-4  narrow adjudication history/current API surface not implemented
F-055-5  focused lifecycle tests not written (blocked on F-055-1…4)
F-051-1  D17 migration-count guard (needs an authorised decision; 74 vs 71)
```

## VERDICT

**IMPLEMENTATION PARTIAL — the versioned-adjudication schema (D-F039-1-A/C/D/F/G/H support) is
implemented, applied and runtime-verified in the disposable database; Findings 1–4 and the
repository / API / service layers that consume it are NOT implemented.**

No independent verification was performed, no PO closure is claimed, production was not
touched, and nothing was deployed.

discipline forbids, so the schema layer is delivered complete and verified, and the remainder
is reported rather than claimed.
