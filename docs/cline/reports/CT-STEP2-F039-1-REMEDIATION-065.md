# CT-STEP2-F039-1-REMEDIATION-065

```text
TASK            F-039-1 remediation — versioning against the real shipped schema,
                real-schema proof, API lifecycle proof, F-063-1 harness
STARTING SHA    ca509d4ceee4bfa986825a88e10ef679443c29e9
BRANCH          p8-release-reconciled (no reset / rebase / force-push)
SCHEMA          CHANGED? NO — application-layer transactional correction only
PRODUCTION      not deployed · no production migration · no production data/RLS/config
PO DECISIONS    D-F039-1-A … -I unchanged (no decision was reopened or reinterpreted)
VERDICT         IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
```

## A. BASELINE

```text
$ git branch --show-current                  → p8-release-reconciled
$ git rev-parse HEAD                         → ca509d4ceee4bfa986825a88e10ef679443c29e9
$ git rev-parse origin/p8-release-reconciled → ca509d4ceee4bfa986825a88e10ef679443c29e9
$ git status --porcelain                     → clean except one untracked audit artifact
                                               (the 064 OHD report — committed in this window, §17)
```

Work was performed in the existing `p8-release-reconciled` worktree (`/tmp/ct_step2`);
the separate dirty `main` checkout was not touched.

## B. ROOT CAUSE OF THE BLOCKING DEFECT (reproduced, not inferred)

The 055 migration (`…_p8_fs_adjudication_lifecycle.sql`) enforces "exactly one current
version per lineage" with a **PARTIAL UNIQUE INDEX**:

```sql
CREATE UNIQUE INDEX activity_clarifications_current_unique
    ON public.activity_clarifications (adjudication_id)
    WHERE is_current;
```

A partial index cannot be deferred, so the previous version MUST be retired before the new
current row is written. The shipped `apply_versioned()` did the opposite, and did it across
**three separate pool acquisitions** (three implicit transactions):

```text
old order:  effective()  →  INSERT (is_current = true)  →  UPDATE previous is_current = false
```

Reproduced against the real shipped schema on the disposable database (`carbontally_test`,
isolated QA organisation, removed afterwards):

```text
V1 OK: {'version': 1, 'is_current': True, 'supersedes_id': None, 'adjudication_id': c5d0e77d…}
V2 FAILED: UniqueViolationError: duplicate key value violates unique constraint
           "activity_clarifications_current_unique"
           DETAIL: Key (adjudication_id)=(c5d0e77d-…) already exists
ROWS after attempt: [{'version': 1, 'is_current': True, 'supersedes_id': None}]
effective(): 1
cleanup: activity_clarifications 0 → 0 | organizations 23 → 23 | RESTORED: True
```

**Version 2 could never be created.** Because the three statements were separate implicit
transactions, the transition was also non-atomic: had the order merely been swapped without
transactional control, a failed insert would have left the lineage with ZERO current
versions. The pre-existing F-039-1 persistence tests could not see any of this — they used a
scripted fake connection, so the real constraint was never exercised (the 064 report is
corrected on this point: a correction banner was added at the top of that artifact in this
window).

## C. FIX (application layer; no schema, no RLS, no policy change)

`backend/data/activity_clarifications.py`:

```text
1. NEW  _CURRENT_FOR_UPDATE_SQL   the same bounded-context predicates as _EFFECTIVE_SQL,
                                  plus FOR UPDATE — the current version is resolved under a
                                  row lock, which also serialises concurrent modifiers of
                                  the same lineage.
2. NEW  _VersionReplayConflict    private sentinel raised inside the transaction when
                                  ON CONFLICT DO NOTHING fires; raising ABORTS the
                                  transaction, undoing the retire.
3. NEW  _insert_params(...)       one authoritative parameter tuple for _INSERT_SQL, shared
                                  by record() and the transition (no drift possible).
4. apply_versioned() rewritten    ONE transaction on ONE connection:
                                     lock current → (replay? return) → retire → insert
                                  and, on a replay conflict, the same semantics as record():
                                  return the row stored for that exact key
                                  (get_adjudication(...)), else the effective row.
```

Statement order in the corrected implementation:

```text
[0] SELECT … WHERE organization_id=$1 AND effective_context_key=$2 AND activity_key=$3
            AND original_activity=$4 AND is_current FOR UPDATE
[1] UPDATE … SET is_current = false, updated_at = now() WHERE organization_id=$1 AND id=$2
[2] INSERT INTO public.activity_clarifications (…) … ON CONFLICT … DO NOTHING RETURNING …
```

## D. TRANSACTION SEMANTICS (why v1 → v2 is atomic)

```text
* one pool acquisition, one `async with conn.transaction()` for lock + retire + insert, so
  the lineage is never observable (to any other session) with zero or two current versions;
* if the insert fails for ANY reason (constraint, FK, cancellation) the whole transaction
  rolls back and the previous version remains current — the all-or-nothing property the
  brief requires;
* the retire is a conditional UPDATE … WHERE id = $2 on the row the lock just read, so it
  cannot retire a different version;
* concurrency: a second modifier of the same lineage blocks on the FOR UPDATE lock; after
  the first commits, its predicate re-evaluates and it versions the row that is now current
  (proven by test: two parallel writes produced versions 2 and 3, exactly one current row);
* the replay path returns from inside the transaction without writing, so an idempotent
  retry costs one statement and leaves no side effects;
* a replay-key conflict aborts the transaction (undoing the retire) and then answers with
  the row actually stored for that key — the caller never sees a lineage without a current
  version.
```

Honest limitation (reported, not silently changed):

```text
If two writers race for the FIRST adjudication of a context where no current row exists yet,
nothing in the schema prevents both creating their own single-version lineage (the partial
unique index is per adjudication_id). This is a pre-existing property of the adjudication
model; §6 of the brief forbids inventing a uniqueness rule, so it is raised as a PO-decision
item in §L instead of being changed here. The same applies to effective() having no explicit
ORDER BY/LIMIT: with a single lineage per context (which the lifecycle now guarantees for
every normal path) it is deterministic, but it carries no ordering guarantee if duplicate
lineages ever exist.
```

## E. SCHEMA

**No schema change and no new migration.** The shipped constraints are exactly right for the
approved PO decisions; only the write sequence violated them. Verified:

```text
$ git diff --name-only <start>..HEAD | grep -iE 'migration|\.sql'   → NONE
shipped constraints relied on (unchanged): activity_clarifications_current_unique
   UNIQUE(adjudication_id) WHERE is_current · activity_clarifications_version_unique
   UNIQUE(adjudication_id, version) · activity_clarifications_replay_unique
   UNIQUE(activity_key, original_activity, clarification, version) · the four RLS policies
```

## F. REAL-SCHEMA PROOF (`tests/integration/test_f039_1_adjudication_lifecycle_runtime.py`)

Six tests against a real asyncpg pool, the real repository, the real router, the real
authorization gate and the real database (`ct_f0391_065`, a disposable clone; the session
fixture truncates its target per F-046-1):

```text
$ INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_f0391_065 \
  python -m pytest tests/integration/test_f039_1_adjudication_lifecycle_runtime.py -q
exit 0 · 6 passed
```

```text
test_v1_then_v2_lifecycle_against_the_real_schema
    v1: version 1 · is_current true · supersedes_id NULL · adjudication_id set
    v2: version 2 · is_current true · supersedes_id = v1.id · SAME adjudication_id
    rows: [(1, False), (2, True)] — exactly one current; v1's clarification untouched
    effective() == v2      history() == [v1, v2] ordered, v1 immutable
test_replay_is_idempotent_and_changed_evidence_signature_is_enforced
    identical write twice → same row, still version 1 (no extra version)
    a changed clarification → version 2 with supersedes linkage
    effective_compatible(): tonnes evidence (stored) compatible, litres incompatible
test_concurrent_modifications_serialise_on_the_lineage
    two parallel writes → versions [2, 3]; current == 1; total == 3 (no collision, no gap)
test_api_create_change_effective_history
    POST #1 → 201 · POST changed #2 → 201 · GET effective → v2 · GET history → [1, 2]
    (the second POST is the one that used to raise UniqueViolationError)
test_api_rejects_foreign_tenant_anonymous_and_forged_factor
test_api_rejects_malformed_identifiers_with_422_not_500
```

### F.1 The test fails against the pre-fix implementation (mandatory adversarial check)

The identical test file was run against a read-only `git archive` sandbox of the pre-fix
revision, against the same disposable database:

```text
PRE-FIX  →  FFFF.   exit 1
  UniqueViolationError: duplicate key value violates unique constraint
    "activity_clarifications_current_unique"
  FAILED test_v1_then_v2_lifecycle_against_the_real_schema
  FAILED test_replay_is_idempotent_and_changed_evidence_signature_is_enforced
  FAILED test_concurrent_modifications_serialise_on_the_lineage
  FAILED test_api_create_change_effective_history
POST-FIX →  ......   exit 0
```

So the new coverage is a genuine detector of the blocking defect, and it exercises the real
constraint and real transaction behaviour rather than a fake.


## G. API PROOF (create → change → effective → history, real path)

From `test_api_create_change_effective_history` (real router, real gate, real engine, real
repository, real database — driven in-loop through `httpx.ASGITransport` so the asyncpg pool
is used from the same event loop):

```text
POST /api/v3/activity-clarifications/clarifications  {"clarification": "Landfill"}   → 201
     actor_id = the authenticated user · actor_scope = "organization_member"
     policy_input = "Waste Landfill"            (the policy's own text, never a factor id)
POST …                                                {"clarification": "Incineration"} → 201
GET  /effective   → 200 {found: true, adjudication: {version: 2, is_current: true,
                                                     clarification: "Incineration"}}
GET  /history?adjudication_id=<current row id>
     → 200 {versions: [1, 2], current_version: 2}
       v1: clarification "Landfill", is_current false, immutable
       v2: supersedes_id == v1.id
lineage rows in the database: [(1, False), (2, True)]
```

API error behaviour (§9 of the brief) — investigated and fixed:

```text
FINDING (pre-fix): a malformed identifier reached asyncpg and raised DataError, which the
  endpoints do not translate → HTTP 500 for a plain input error.
  Evidence (real schema): resolve_evidence("not-a-uuid", …) → DataError:
    invalid input for query argument $1: 'not-a-uuid' (invalid UUID …)
  and the same for a malformed organization_id.
FIX: boundary validation in backend/api/v3_activity_clarifications.py —
  * write payloads: a Pydantic field validator on organization_id/item_id (extra="forbid"
    models) → the project's normal 422 validation response;
  * read endpoints: `_uuid_query(...)` for organization_id/item_id/adjudication_id → 422.
  The value is passed through unchanged, so authorization comparisons and context keys are
  unaffected (asserted).
VERIFIED: unit 3 new tests + 1 real-schema test → POST/GET with malformed identifiers = 422
  with ZERO statements executed and nothing persisted; well-formed identifiers still yield
  200/201 with identical lookup parameters.
No genuine database/programming error is hidden: 500s remain for real faults, and the
lifecycle's legitimate conflicts are now resolved inside the repository instead of surfacing.
```

## H. AUTHORIZATION (unchanged and re-verified over the real database)

```text
foreign organisation    → 403 and nothing persisted for that organisation (asserted by query)
foreign item            → 403 (server-derived tenant wins over the request)
anonymous               → 401
forged factor id        → 422 (never a selection)
server-derived provenance → actor_id = authenticated user; actor_scope = server-derived;
                            factor metadata = the policy's own result
```

The full pre-existing authorization matrix (31 write-path cases: org member own/other,
consultant with/without/ended grant, PE staff, internal staff, unaffiliated, anonymous,
anti-bypass) still passes unchanged (`tests/unit/api/test_v3_activity_clarifications_api.py`
→ exit 0). No authorization function was mocked, relaxed or bypassed.

## I. RLS

F-063-1 is repaired (§J) and the behavioural matrix now runs green against the shipped
schema and policies, with residue proven absent:

```text
$ INTEGRATION_DATABASE_URL=…/carbontally_test python tests/integration/verify_activity_clarifications_rls.py
=== RLS MATRIX: 28/28 PASS ===   exit 0
BEFORE {'activity_clarifications': 0, 'organizations': 23, 'organization_members': 13,
        'users': 652, 'consultant_profiles': 2, 'consultant_firm_members': 2,
        'consultant_clients': 2}
AFTER  … identical …  RESIDUE_FREE: True
```

Highlights: member own-org SELECT/INSERT/UPDATE/DELETE allowed; member A→B SELECT 0 rows,
INSERT rejected by RLS, UPDATE/DELETE 0 rows, B's row unmodified; consultant with an ACTIVE
grant SELECTs the authorised client's row (explicitly asserted) but cannot INSERT/UPDATE/
DELETE; consultant denied for an unauthorised client; anonymous denied on all four verbs;
service_role allowed (BYPASSRLS). No RLS policy, schema or authorization semantic was altered
to make this pass — only the fixture and the identity-selection logic were repaired.

## J. F-063-1 — HARNESS REPAIRED

```text
Reported problem 1 (fixture vs 055 schema): the harness's `INS` omitted `adjudication_id`
   (NOT NULL, no default since migration 3e11155) and `effective_context_key` (NOT NULL).
   REPAIRED: both are now supplied (gen_random_uuid() / the QA activity key).
Reported problem 2 (member precondition): the harness assumed the alphabetically-first
   organisation owned an active member, otherwise it exited.
   REPAIRED: the (org A, actor) pair is now resolved from the data — the first organisation
   that actually has an active member — with a different second organisation as org B; the
   explicit precondition error is retained if the data cannot satisfy the matrix.
Additional harness-quality defect found while verifying (also repaired, not a product
   defect): the mutation checks COMMITTED their transactions, and the DELETE consumed the very
   row the later allow-checks had to observe — so several "allow" results were satisfied by
   "no error" on 0 rows (including the consultant allow-case, which returned 0 rows before).
   REPAIRED: destructive checks use their own row (`qa:rls:seedA_mut`), and the consultant
   allow-path now carries an explicit row-level assertion.
RESULT: 28/28 PASS, exit 0, zero residue. No production/schema/RLS/authorization semantic was
   changed to achieve this.
```


## K. REGRESSION (exact counts)

Baseline = an identical run against a read-only `git archive` of the pre-remediation target
`ca509d4`; remediated = this window's working tree. Both `python -m pytest tests/unit -v
-p no:cacheprovider` from `backend/`.

```text
BASELINE ca509d4    exit 1 · 6 failed, 2731 passed, 2 skipped   (collected 2739)
REMEDIATED HEAD     exit 1 · 6 failed, 2735 passed, 1 skipped   (collected 2742)
failure-set diff (baseline vs remediated) ...................... IDENTICAL
new failures .................................................... NONE
pre-existing failures ........................................... 6 (unchanged, see below)
collected delta ................................................. +3 = the three new
                                                                  malformed-identifier API tests
passed/skipped delta ............................................ +4 / −1: the single
   environment-dependent skip that the archive sandbox shows either way (collected reconciles
   exactly: 2742 − 2739 = 3)
```

Pre-existing failures (present at the pre-remediation SHA, untouched by this window):

```text
tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
    → F-051-1 (pins 71 migrations against the tree's 74); NOT modified, NOT counted as F-039-1
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_operations_surface
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_pe_surface
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
```

Focused suites (all exit 0) plus the real-infrastructure suites:

```text
tests/unit/data/test_activity_clarifications_repository.py          17  exit 0
tests/unit/api/test_v3_activity_clarifications_api.py               54  exit 0
tests/unit/services/test_automatic_processing.py                    38  exit 0
D-A (natural_gas_basis 26 + discovery 9)                            35  exit 0
D-FS (factor_selection_policy)                                      19  exit 0
039 (factor_selection_followup_039)                                 14  exit 0
041 (activity_clarification_041)                                    16  exit 0
043 + 045 (activity_clarification_043)                              13  exit 0
units (family_compat 35 + qualifier 27 + units 13)                  75  exit 0
tests/integration/test_f039_1_adjudication_lifecycle_runtime.py       6  exit 0 (real schema)
verify_activity_clarifications_rls.py                          28/28 PASS exit 0 (real RLS)
```

Numbering note: the API file went 51 → 54 items (three malformed-identifier tests) and the
integration file is new (6). No pre-existing test was weakened, skipped, renamed or deleted —
the two order-sensitive fake-backed tests were re-scripted for the corrected statement order
and strengthened (single-transaction/single-connection, FOR UPDATE lock, retire-before-insert).


## L. REMAINING ISSUES

```text
FIXED IN THIS WINDOW
  F-039-1-065-A  version 2 (and later) can be created against the shipped schema; the
                 transition is atomic and concurrency-safe.
  F-039-1-065-B  no F-039-1 persistence test exercised the real constraint — there is now a
                 real-schema suite that fails pre-fix and passes post-fix.
  F-039-1-065-C  the API lifecycle (create → change → effective → history) is proved end to
                 end over the real router/gate/engine/repository/database.
  F-039-1-065-D  legitimate input errors (malformed uuid identifiers) escaped as HTTP 500 —
                 now 422 at the boundary, with no statement executed.
  F-063-1        RLS harness repaired (NOT NULL columns + data-driven identity pair + a
                 non-vacuous consultant allow-assertion): 28/28 PASS, residue-free.

VERIFIED (unchanged by this window)
  D-A / D-FS / 039 / 041 / 043 / 045 semantics; the family-conflict diversion; no-guess on
  ambiguity; tenant and consultant-client isolation; server-derived provenance; the
  D-F039-1-I compatibility gate; the four RLS policies; immutability of history.

PRE-EXISTING, NOT F-039-1 (deliberately untouched)
  F-051-1  migration-count pin (71 vs 74), plus the other five unit failures listed in §K.

STILL BLOCKED / REQUIRES PO DECISION (reported, not changed — brief §6)
  1. Two concurrent FIRST writes for a bounded context with no current row can still create
     two single-version lineages (the partial unique index is per adjudication_id). The
     lifecycle guarantees one lineage per context on every normal path, but the schema does
     not forbid the duplicate. Decide whether "one lineage per bounded context" is the rule
     (then a per-context current-uniqueness constraint is needed) or whether duplicates stay
     legal (then a deterministic resolution rule and an ORDER BY/LIMIT guarantee on the
     effective read are needed).
  2. `effective()` has no explicit ORDER BY/LIMIT: deterministic whenever one lineage exists
     per context, unspecified otherwise. Coupled to item 1.
  3. `ClarificationResultOut` (the write response) does not surface `version` /
     `supersedes_id` / `is_current`; a client must read `/effective` or `/history` to learn
     the new version. Not a defect (the required proof reads those endpoints), but a small
     contract/UX decision for D19.

NOT IN SCOPE / NOT DONE
  No deployment, no production migration, no production data/RLS/config change, no UI work,
  no change to any D-F039-1 decision, no change to factor-selection policy or authorization
  semantics.
```

## M. FINAL VERDICT

```text
IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
```

The blocking defect is fixed at the application layer with no schema change; the corrected
lifecycle is proved against the real shipped schema (including an adversarial pre-fix run of
the same test file); the API lifecycle is proved end to end; the F-063-1 harness is repaired
and green with zero residue; and the broad unit suite shows an identical pre-existing failure
set with only additive coverage.

No Product Owner decision was changed, no Product Owner closure is claimed, and §L item 1
needs a PO decision before any uniqueness semantics are altered.

