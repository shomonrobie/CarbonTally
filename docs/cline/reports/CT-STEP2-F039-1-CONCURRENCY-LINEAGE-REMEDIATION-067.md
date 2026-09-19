# CT-STEP2-F039-1-CONCURRENCY-LINEAGE-REMEDIATION-067

```text
TASK            D-F039-1-J — exactly ONE adjudication lineage per bounded context
STARTING SHA    e907e4b893b2675a57c085f6495bcf4a7be46649
BRANCH          p8-release-reconciled (no reset / rebase / force-push)
SCHEMA CHANGE   YES — one additive PARTIAL UNIQUE INDEX (new migration 20260931000000)
PRODUCTION      not deployed · not modified · no Render action · no PO closure
VERDICT         IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
```

## 1. BOUNDED-CONTEXT IDENTITY (discovered, not assumed)

The shipped effective read has always been bounded by four columns, and the 065
`_CURRENT_FOR_UPDATE_SQL` uses the same four:

```text
_EFFECTIVE_SQL / _CURRENT_FOR_UPDATE_SQL
   WHERE organization_id = $1
     AND effective_context_key = $2
     AND activity_key         = $3
     AND original_activity    = $4
     AND is_current
```

⇒ **the F-039-1 bounded context is `(organization_id, effective_context_key,
activity_key, original_activity)`.**

The API establishes it as `context_key = item_id` (falling back to `activity_key`), with
`activity_key = context_key` and `original_activity = the extracted activity`; the repository
uses `effective_context_key = context_key or record.activity_key`. No new notion of context
was introduced — the enforcement key is exactly this tuple.

## 2. ROOT CAUSE OF THE CONCURRENCY RACE

`activity_clarifications_current_unique` is `UNIQUE (adjudication_id) WHERE is_current` — it
bounds current rows *within a lineage*, so it cannot stop a writer from starting a **second
lineage** for the same context. The 065 mechanism (lock the current row, retire it, insert the
next version in one transaction) therefore has a READ COMMITTED hole:

```text
Writer A: locks the current row, retires it, inserts the new current row, COMMITS.
Writer B: its statement snapshot was taken BEFORE A committed; it waits on the old row's
          lock; when A commits, B's EvalPlanQual re-check finds that the old row no longer
          satisfies is_current, and A's newly inserted current row is NOT visible to B's
          snapshot ⇒ B observes "no current row" and creates a SECOND lineage (version 1,
          new adjudication_id) as current.
```

Concurrent *first* writes have the same hole with nothing to lock at all. Reproduced against
the real schema with a **warmed** pool (5 writers, 5 rounds, disposable database):

```text
$ python /tmp/r67/repro.py 5 5
  [first-writes  r0..r4] lineages=4 current=4 versions=[1,1,1,1] errors=[] fork=True   ×5
  [existing      r0..r4] lineages=4 current=4 versions=[1,1,1,1,2] errors=[] fork=True ×5
RESULT concurrent FIRST writes  : forked 5/5
RESULT concurrent EXISTING writes: forked 5/5
cleanup: adjudications 9->9 orgs 8->8 RESTORED=True
```

No writer errored — the duplicate lineages were created **silently**, exactly as OHD reported.

## 3. ENFORCEMENT MECHANISM SELECTED (and why)

Two distinct properties are required, and each is provided by the smallest mechanism that can
provide it:

```text
(a) GUARANTEE   — a second current row for one bounded context must be IMPOSSIBLE, on every
                  path (repository, service, script, future code, direct SQL).
    MECHANISM   — additive partial unique index on the bounded context:
                    CREATE UNIQUE INDEX activity_clarifications_context_unique
                        ON public.activity_clarifications
                           (organization_id, effective_context_key, activity_key,
                            original_activity)
                        WHERE is_current;
                  This is the same pattern the schema already uses for "one current version
                  per lineage", applied to the PO's actual invariant. A current row IS the
                  row that carries the context, so "one current row per context" ≡ "one
                  lineage per context".

(b) CONVERGENCE — the PO requires racing writers to JOIN that lineage, not merely to fail.
    MECHANISM   — a transaction-scoped advisory lock keyed on the bounded context, taken as
                  the first statement of the transition transaction:
                    SELECT pg_advisory_xact_lock(hashtextextended($1, 0))
                  with $1 = the four context columns. Writers queue per context, so each
                  one's read observes the previous writer's committed state and versions that
                  lineage; the lock is released automatically on commit AND on rollback, so a
                  failed attempt cannot leak it. A hash collision can only over-serialise two
                  unrelated contexts — never admit a second lineage, because (a) is
                  authoritative.
    PLUS        — a bounded retry (3 attempts) for the residual case of a writer that
                  bypassed the lock (ops script / future code): it loses to the unique index,
                  then retries and converges. If every attempt loses it raises
                  AdjudicationConcurrencyConflict — it never forks, and never returns a
                  duplicate lineage.
```

Rejected alternatives (recorded per §5E):

```text
* row lock only (065): proven insufficient — this is the defect.
* index only, no lock: correctness would depend on an unbounded retry storm (one winner per
  round ⇒ N rounds for N writers); measured: pre-fix code + index ⇒ 0 forks but every loser
  errors (no convergence).
* deterministic adjudication_id derived from the context: would change the meaning of an
  existing identifier and require rewriting historical rows — forbidden by D-039-1-D/-H.
* a new lineage/context anchor table: a larger model change than the invariant needs, and it
  would have to be referenced by every writer anyway.
```

## 4. WHY ONE LINEAGE IS GUARANTEED FOR CONCURRENT **FIRST** WRITES

```text
Concurrent first writes for an empty context: there is no row to lock, so the 065 mechanism
had nothing to serialise on. Now:
  1. every writer takes the CONTEXT lock first ⇒ they queue; the first one to hold it reads
     "no current row", inserts version 1 as current and commits (releasing the lock);
  2. each queued writer then runs its read AFTER that commit ⇒ it sees version 1 as the
     current row of the context and therefore creates version 2, 3, … **in that same
     lineage** (supersedes chain preserved, one current row at every commit);
  3. if a writer ever bypasses the lock, its duplicate current row is refused by
     activity_clarifications_context_unique — the invariant cannot be violated even by code
     that does not know about it (proved: a raw INSERT with is_current=true is rejected with
     constraint_name = activity_clarifications_context_unique).
```

Measured (`forked 0/5`, versions contiguous, zero errors):

```text
  [first-writes  r0] lineages=1 current=1 versions=[1, 2, 3, 4]   errors=[] fork=False
  [first-writes  r1..r4] lineages=1 current=1 versions=[1, 2, 3, 4, 5] errors=[] fork=False
```

(The r0 `[1,2,3,4]` shape is correct idempotency: two of the five writers submitted the same
semantic clarification in sequence, so the second was a replay rather than a new version.)

## 5. WHY ONE LINEAGE IS GUARANTEED FOR CONCURRENT **SUBSEQUENT** WRITES

```text
  1. the writer holding the context lock retires the current row and inserts the next version
     in ONE transaction, so the retired row is committed-as-retired only together with its
     successor — no window with zero current rows;
  2. a queued writer's read happens after that commit, so it never observes the stale "no
     current row" state that produced the fork; it versions the new current row (its
     supersedes_id points at the version it replaced);
  3. a writer that bypassed the lock and reached the stale state cannot do damage: its insert
     is refused by the context index, the retry converges onto the winning lineage, and the
     retire of the losing attempt is rolled back by the failure.
```

## 6. MIGRATION — REQUIRED, AND WHY

A schema change **is** required: the invariant is a statement about *data* ("exactly one
lineage per bounded context"), and the existing schema enforces the analogous invariant only
per `adjudication_id`. No application-only mechanism can make the guarantee hold for writers
outside the application (§3a), and the PO decision is absolute ("shall maintain", "must
converge"), so the invariant is expressed where it can be enforced.

```text
supabase/migrations/20260931000000_p8_fs_adjudication_context_lineage.sql
  1. a non-destructive PRE-FLIGHT that refuses to proceed (with an explicit message) if any
     bounded context already has more than one current row — it never deletes, merges or
     rewrites data and invents no reconciliation policy;
  2. CREATE UNIQUE INDEX IF NOT EXISTS activity_clarifications_context_unique
        (organization_id, effective_context_key, activity_key, original_activity)
        WHERE is_current;
  3. COMMENT ON INDEX … recording D-F039-1-J.
```

Apply + verification on the disposable database (fresh apply, idempotent re-apply, index
definition, comment, RLS untouched):

```text
APPLY 1: OK        APPLY 2 (re-apply): OK
index present: True
index def: CREATE UNIQUE INDEX activity_clarifications_context_unique ON
  public.activity_clarifications USING btree (organization_id, effective_context_key,
  activity_key, original_activity) WHERE is_current
RLS enabled: True | policies: tenant_delete, tenant_insert, tenant_select, tenant_update
all indexes: … context_unique, current_unique, effective_idx, history_idx, replay_unique,
  version_unique, pkey, activity_idx, batch_idx, item_idx, org_created_idx
```

Data-safety pre-check on every disposable database available here (read-only):

```text
ct_f0391_065   : rows=9  current=4 duplicate_current_contexts=0
carbontally_test: rows=0 current=0 duplicate_current_contexts=0
ct_f0391_067_pre (a clone the PRE-FIX code had already raced in): 6 duplicate contexts
```

The fail-safe path was verified for real on that pre-index clone (two current rows seeded for
one bounded context, then the migration applied):

```text
seeded rows: 2 current rows for ONE bounded context (the pre-fix duplicate-lineage shape)
RESULT: migration REFUSED — "D-F039-1-J pre-flight: 6 bounded context(s) already have more
        than one current adjudication row. Resolve them under a PO decision before applying
        this uniqueness index; this migration never deletes, merges or rewrites rows."
index created by the failed migration: False (must be False)
rows still present: 2 (must be 2 — nothing deleted or merged)
probe rows removed: remaining=0
```

⇒ The migration cannot silently "fix" or destroy a pre-existing fork; it stops and hands the
condition to a PO decision, exactly as §10 requires. Production-shaped data could not be
inspected from this environment, so this refusal — not a cleanup policy — is the guarantee
offered to the applying release, and the exact pre-check query is in the migration file.



## 7. FILES CHANGED (exact)

```text
NEW  supabase/migrations/20260931000000_p8_fs_adjudication_context_lineage.sql
     D-F039-1-J enforcement: non-destructive pre-flight + activity_clarifications_context_unique

MOD  backend/data/activity_clarifications.py
     + _CONTEXT_LOCK_SQL, _context_lock_key(), _MAX_CONVERGENCE_ATTEMPTS,
       _CONTEXT_UNIQUE_INDEX, AdjudicationConcurrencyConflict, _ContextConvergenceRetry
     * apply_versioned()       → bounded convergence wrapper (3 attempts), raises
                                 AdjudicationConcurrencyConflict instead of ever forking
     + _apply_versioned_once() → the 065 transition (unchanged semantics) + the context lock
                                 as its first statement + translation of a context-index
                                 unique violation into a convergence retry
     * docstring records the one-lineage invariant and the lock/index division of labour

NEW  backend/tests/integration/test_f039_1_adjudication_concurrency_runtime.py
     9 real-schema concurrency tests (A–F), reusing the lifecycle module's helpers

MOD  backend/tests/unit/data/test_activity_clarifications_repository.py
     2 order-sensitive tests updated for the new first statement (the lock), and now
     ASSERT the lock ordering/key instead of merely tolerating it
MOD  backend/tests/unit/api/test_v3_activity_clarifications_api.py
     2 order-sensitive tests updated likewise (lock at index 0)

NEW  docs/cline/reports/CT-STEP2-F039-1-CONCURRENCY-LINEAGE-REMEDIATION-067.md
```

No API contract, RLS policy, authorization rule, factor policy, evidence-signature field or
frontend file was touched. `record()`, `supersede()`, `delete()` and every read path are
unchanged.

## 8. TESTS ADDED / CHANGED

`tests/integration/test_f039_1_adjudication_concurrency_runtime.py` — every race warms the
pool explicitly (`_warm(pool, N)` opens N live connections), so **no test depends on
connection-pool warm-up side effects**:

```text
TEST A  test_a_concurrent_first_writes_converge_on_one_lineage
        5 concurrent writes, empty context ⇒ 1 lineage · 1 current · versions [1..5] ·
        every successful write carries that lineage id · no lost successful update
TEST B  test_b_concurrent_writes_to_an_existing_lineage_stay_in_it
        seeded v1 + 4 concurrent modifications ⇒ 1 lineage · versions [1..5] · v1 keeps its
        id/clarification (immutable history) · no lost update
TEST C  test_c_concurrent_identical_requests_are_idempotent
        5 identical concurrent requests ⇒ 1 row, version 1, one semantic result
TEST D  test_d_failed_transaction_leaves_no_orphan_or_duplicate_current
        real FK failure after the retire ⇒ retire rolled back, no orphan, chain resumes at v2
        test_d_failing_writer_concurrent_with_a_good_writer_stays_consistent
        a failing writer racing a good one ⇒ 1 lineage · 1 current · versions [1,2]
        test_d_a_writer_that_bypasses_the_lock_cannot_fork_the_context
        a raw second current row is REJECTED (constraint_name ==
        activity_clarifications_context_unique) ⇒ the guarantee is the database's
        test_d_bounded_retry_converges_without_timing_dependence
        deterministic retry proof (1 injected lost attempt ⇒ convergence in 2 attempts;
        exhausted attempts ⇒ AdjudicationConcurrencyConflict and NOTHING written)
TEST E  test_e_race_is_detected_with_an_already_warm_pool
        two consecutive races in one session, pool already warm in both
TEST F  test_f_api_concurrent_clarifications_converge_on_one_lineage
        5 concurrent HTTP POSTs through the real router (real repository, real DB, member
        auth) using the engine's own eligible semantic options ⇒ 1 lineage · versions
        [1..N] · /effective reports version N · /history is the same single chain
```

**Adversarial proof that the tests detect the defect** (sandbox copy of e907e4b + a clone
without the index; the repository was never modified for this):

```text
pre-fix  : FF...FFFF  6 failed / 3 passed   (A, B, D-bypass, D-retry, E, F all fail)
post-fix : .........  9 passed

## 9. REAL PostgreSQL CONCURRENCY RESULTS

Real schema, real asyncpg pool, disposable databases (`ct_f0391_065`, `ct_f0391_067_pre`),
5 writers × 5 rounds unless stated:

```text
state 1  pre-fix code + NO index   : forked 5/5 (first) and 5/5 (existing) — SILENT forks
state 2  pre-fix code + index      : forked 0/3, but every loser raised UniqueViolationError
                                     (enforced by the DB, not converged by the application)
state 3  remediated code + index   : forked 0/5 and 0/5, zero errors, contiguous versions
```

In-suite results (post-fix, disposable clone):

```text
tests/integration/test_f039_1_adjudication_concurrency_runtime.py   9 passed
tests/integration/test_f039_1_adjudication_lifecycle_runtime.py     6 passed
combined run                                                        15 passed (exit 0)
```

## 10. API-LEVEL CONCURRENCY RESULTS

```text
test_f_api_concurrent_clarifications_converge_on_one_lineage  PASSED
5 concurrent POST /api/v3/activity-clarifications/clarify (httpx.ASGITransport sharing the
test event loop, real router + real repository + real DB, member auth, real engine options)
⇒ [201]×5 · 1 lineage · 1 current row · versions [1..5] · /effective version 5 ·
  /history one chain [1..5] · no 409/5xx
```

## 11. WARM-POOL RESULTS

```text
python /tmp/r67/repro.py 5 5   (pool min_size=N, warmed with N concurrent queries before
                                every round, N writers per round, 5 rounds)
  pre-fix  : forked 5/5 (first) · 5/5 (existing)
  post-fix : forked 0/5 (first) · 0/5 (existing)
TEST E (two consecutive races in one session on an already-warm pool): PASSED
⇒ the race is detected when it exists and converges when it is fixed; no warm-up dependency
  remains anywhere in the suite.
```

## 12. ROLLBACK / FAILURE RESULTS

## 13. REGRESSION RESULTS AND BASELINE COMPARISON

```text
FOCUSED F-039-1 / related suites (all exit 0)
  tests/unit/data/test_activity_clarifications_repository.py              17 passed
  tests/unit/api/test_v3_activity_clarifications_api.py                   55 passed (+1 new 409 test)
  tests/unit/services/test_automatic_processing.py                        38 passed
  tests/unit/engines/test_activity_clarification_041.py                   16 passed
  tests/unit/engines/test_activity_clarification_043.py                   13 passed
  tests/unit/engines/test_factor_selection_followup_039.py                14 passed
  tests/unit/engines/test_factor_selection_policy.py                      19 passed
  tests/unit/engines/test_d_a_natural_gas_discovery.py + test_d_a_…basis    9 + 26 passed
  tests/unit/test_units.py + test_units_family_compat.py + …qualifier      13 + 35 + 27 passed

INTEGRATION (real PostgreSQL, disposable clone; run together — the conftest truncates first)
  tests/integration/test_f039_1_adjudication_lifecycle_runtime.py           6 passed
  tests/integration/test_f039_1_adjudication_concurrency_runtime.py         9 passed
  combined                                                                15 passed (exit 0)

RLS / TENANCY REGRESSION
  verify_activity_clarifications_rls.py (F-063-1 harness)    28/28 PASS · RESIDUE_FREE True

BROAD BASELINE — tests/unit, identical command, pytest 9.1.1 / Python 3.14.4
  baseline (e907e4b, sandbox)       : 6 failed, 2734 passed, 2 skipped, 2742 collected
  remediated (working tree)         : 6 failed, 2736 passed, 1 skipped, 2742 collected
  failure-set diff                  : EMPTY  (0 lines) — no new failure, none removed
  pre-existing failures (unchanged, identical set):
    tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_operations_surface
    tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_pe_surface
    tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
    tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
    tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
    tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
  movement explained (neither item is caused by this change):
    +1 passed : the new test_convergence_conflict_is_reported_as_409_not_500
    +1 pass / -1 skip : test_d17_…migration_revision.py:255 skips in the sandbox with
      "release commit not available locally" because a `git archive` has no .git directory;
      in the real working tree it runs and passes. That file is UNTOUCHED by this change
      (git status: clean).
    note: the D17 pin (assert len(names) == 71) fails in BOTH runs; the count it reports is
      now 75 rather than 74 — the same pre-existing pin (F-051-1 class), same failure id,
      same failure kind; this change adds exactly one migration.
```

No pre-existing failure was reclassified, silenced or removed, and no new failure was
introduced.


```text
FK failure injected AFTER the retire (real constraint, real transaction):
  ⇒ no orphan version · the retired row is STILL current (retire rolled back) ·
    the next write succeeds as version 2 with supersedes_id = the surviving current row
Failing writer concurrent with a good writer:
  ⇒ 1 lineage · 1 current · versions [1,2] · the failure left no residue
Advisory-lock release on failure:
  ⇒ pg_advisory_xact_lock is transaction-scoped, released with the rollback; the peer
    proceeded — no deadlock, no leaked lock (verified by the concurrent-failure test)
Exhausted convergence attempts:
  ⇒ AdjudicationConcurrencyConflict and ZERO rows written (never a fork)
```

```

## 14. REMAINING LIMITATIONS

```text
1. Two behaviours were deliberately NOT touched (out of scope by instruction): F-064-1
   (/history contract/parameter mismatch) and F-064-2 (consumption-exception observability).
   The effective-adjudication ORDER BY/LIMIT question likewise remains open; it is not a
   correctness hole for D-F039-1-J because the context index now makes a second current row
   per context impossible, so a context read cannot return an arbitrary one of several.
2. ClarificationResultOut still does not expose version/is_current/supersedes_id (L-3) — a
   contract/UX decision, unchanged by this work.
3. AdjudicationConcurrencyConflict maps to 409 at the two write endpoints. Reaching it
   requires a non-repository writer to win the same context three attempts in a row; it was
   verified deterministically at the repository level and its HTTP mapping is covered by a
   unit test, but it was not reproduced as an end-to-end race (by construction it needs an
   out-of-application writer).
4. The advisory lock is per bounded context, so writers of the SAME context serialise: this
   is the intended trade-off (a different context is unaffected), and hash collisions can
   only over-serialise two unrelated contexts — never admit a second lineage.
5. The migration was applied and verified only in disposable databases. Production promotion
   is a separate release action; the pre-flight refuses to apply if any context already has
   two current rows, and no data-reconciliation policy was invented.
6. record()/supersede() remain lower-level primitives: they cannot be used to fork a context
   (the index refuses it) but they do not themselves acquire the context lock. Only
   apply_versioned — the sole application write path — is lineage-safe by design.
7. Lock ordering is fixed and therefore deadlock-free (context lock → current-row lock →
   insert), but a queued writer holds a pooled connection while it waits. Concurrent writers
   of ONE context are serialised by design and bounded by the pool's max size; a large burst
   for a single activity can therefore occupy several pool connections briefly (no starvation
   of other contexts was observed in the runs above, and no writer timed out).
8. The context index is a plain (non-CONCURRENT) CREATE UNIQUE INDEX, like every existing
   index in this migration set; on a very large table the applying release should schedule it
   as a migration (build time scales with row count) — functional behaviour is unaffected.
```

## 15/16/17. GIT STATE

```text
branch  p8-release-reconciled          (no reset, no rebase, no force-push)
base    e907e4b893b2675a57c085f6495bcf4a7be46649
commit  dab6af1a82d72f6fb6095d3c64f7783252b47f97
        "fix(p8/fs): F-039-1 one adjudication lineage per bounded context (D-F039-1-J)"
push    pushed to origin/p8-release-reconciled: e907e4b..dab6af1 (verified with ls-remote:
        refs/heads/p8-release-reconciled == dab6af1a82d72f6fb6095d3c64f7783252b47f97)
files   7 (3 new: migration, concurrency suite, this report; 4 modified: repository, API,
        and the two unit test files whose statement-order assertions the new lock affects)
        1101 insertions(+), 37 deletions(-)
tree    clean after the commit
secrets none introduced (diff scanned for JWTs, keys, private keys, service-role material
        and non-local connection strings: 0 hits)
scope   no unrelated change absorbed
```

## STOP-CONDITION CHECK

```text
bounded context uniquely definable?          YES — the four existing effective-read columns
mechanism needs a new product decision?      NO  — D-F039-1-J is the decision; no policy invented
production-shaped data violating the index?  unknown in production, none in any environment
                                             available here; migration is fail-safe (refuses,
                                             never mutates) and requires no cleanup policy
concurrency reproducible reliably?           YES — 5/5 forks pre-fix with a warm pool
correctness proven only by a timing test?    NO  — the index guarantee, the deterministic
                                             retry proof and the bypass-rejection test are all
                                             timing-independent
unrelated scope expansion required?          NO
production modification required?            NO
```

## DATABASE STATE AT HAND-OFF (verified read-only after the final run)

```text
ct_f0391_065   (remediation clone, DISPOSABLE) : D-F039-1-J index present; 41 rows, all from
                                                integration-test fixtures; no QA-probe orgs
                                                remain (the probes proved RESTORED=True)
ct_f0391_067_pre (pre-fix clone, DISPOSABLE)   : index ABSENT (the pre-fix state used to show
                                                the 6/9 test failures); no QA-probe orgs remain
carbontally_test (template)                    : index ABSENT · 0 rows — UNTOUCHED
production                                     : not contacted, not modified, nothing deployed
```

The pre-flight refusal probe cleaned up every row it created (verified: remaining=0), and no
row belonging to any other party was deleted, merged or rewritten anywhere.

## VERDICT

```text
IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
```

