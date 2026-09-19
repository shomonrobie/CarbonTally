# CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-063

```text
STARTING SHA   45e8c2b919fb13bb2a8fa8baada1183f398f1b1c
PART A COMMIT  a50959303ddc4573eac841bea9dc5a42f9ef6031
PART B/C COMMIT 52c9ef0bb2929bc848f5e2013ddfbb3a798653ef
BRANCH         p8-release-reconciled — no reset / rebase / force-push
MIGRATIONS     NONE — no new migration, no DDL, no schema change
PRODUCTION     NOT touched · nothing deployed · no production credentials used
UI / D19       NOT modified · F-051-1 NOT modified
TENANCY        no RLS policy changed; no authorization function mocked anywhere
```

## 0. BASELINE VERIFICATION (and why the checkout differs from the brief)

```text
$ git branch --show-current                  → main   (in /home/shomonrobie/carbon_tally)
$ git rev-parse HEAD                         → 20b7a928bb73fdfacf8271ff537a8fd245f62c79
$ git rev-parse origin/p8-release-reconciled → 45e8c2b919fb13bb2a8fa8baada1183f398f1b1c
$ git status --porcelain                     → 298 unrelated entries (long-standing dirty main)
```

The brief's baseline is a *branch*, and this repository keeps one worktree per branch.
`git worktree list` shows the branch checked out elsewhere at exactly the required revision:

```text
worktree /home/shomonrobie/carbon_tally   HEAD 20b7a92…  [main]
worktree /tmp/ct_step2                    HEAD 45e8c2b…  [p8-release-reconciled]
```

All work in this window was therefore performed in **/tmp/ct_step2**, where the baseline was
verified exactly as the brief requires:

```text
$ git branch --show-current                  → p8-release-reconciled
$ git rev-parse HEAD                         → 45e8c2b919fb13bb2a8fa8baada1183f398f1b1c
$ git rev-parse origin/p8-release-reconciled → 45e8c2b919fb13bb2a8fa8baada1183f398f1b1c
$ git status --porcelain                     → (empty — clean)
```

The dirty `main` worktree was **not** touched, reset, cleaned or stashed.


---

## PART A — F1 SERVICE TESTS (`a509593`)

### A.1 What changed

```text
backend/tests/unit/services/test_automatic_processing.py   (fixtures + Tests A1–A8)
backend/services/automatic_processing.py                   (+4 lines — a defect fix, see A.3)
```

Fixture extensions (exactly as the brief prescribes, and no wider):

```text
_FakeRepos            now carries `clarifications` — the REAL
                      ActivityClarificationsRepository over the capturing fake connection
                      already used by the API tests (`_ClarificationConn` / `_ClarificationPool`),
                      so the service runs the genuine server-side derivation + SQL predicates.
_FakeMatchingEngine   now implements `clarification_candidates()` and records every `match()`
                      request. It DEFAULTS TO EMPTY, which reproduces the previous
                      no-diversion behaviour for all 27 pre-existing tests; only the lifecycle
                      tests pass the real 041/039 `Waste` window.
activity              `Waste` (not Diesel): it produces the treatment-vs-combustion family
                      collision and therefore reaches the real clarification diversion.
                      `_FakeMatchingEngine.match()` still returns `_FACTOR` for the
                      post-clarification processing assertion.
```

The fake connection's read semantics mirror the real SQL rather than answering
unconditionally: an adjudication row is visible only when it is `is_current` **and** its
`organization_id` equals the organisation in `$1`, so a retired version or a foreign tenant's
row is genuinely never handed to the service.

### A.2 Exact results (Part A)

```text
$ cd /tmp/ct_step2/backend
$ .venv/bin/python -m pytest tests/unit/services/test_automatic_processing.py -q
exit 0   ·   38 passed   (27 pre-existing + 11 new A1–A8)
```

Per-scenario mapping — every scenario drives the real workflow through `process_job`
(never a bare helper call):

```text
A1  no adjudication ............ job blocks; the reason carries the ENGINE's own family-conflict
                                 explanation; mapped_data is None; the current-row lookup ran;
                                 no write was issued.
A2  compatible adjudication .... job reaches `review`; the policy was re-entered with the
                                 stored SEMANTIC clarification ("Waste Landfill"); the mapped
                                 factor is the matcher's result; lookup tuple is
                                 (org, item, item, "Waste") — the full bounded context.
A3  selected_factor_id bypass .. adjudication clarification "Landfill" (policy → "lf") while the
                                 stored `selected_factor_id` is "ol": the mapped factor is
                                 neither — the matcher was asked for the POLICY's input.
A4  evidence changed ........... stored signature is for tonnes, persisted evidence now litres:
                                 NOT consumed, diversion preserved, row unchanged, no write.
A5  signature missing .......... a NULL signature is not proof of compatibility: NOT reused,
                                 diversion preserved, row unchanged, no write.
A6  still ambiguous ............ clarification "Waste disposal" leaves the policy ambiguous:
                                 unresolved, matcher never asked, stored id not used as fallback.
A7  versioning ................. v1 (retired, "Incineration") + v2 (current, "Landfill"): only v2
                                 reaches the policy; neither version mutated; no write; the
                                 effective read is the `is_current` predicate.
                                 (+ a retired-version-only case → not consumed.)
A8  tenant / bounded context ... A consumes A; B's row is invisible; the lookup tenant comes from
                                 the PERSISTED ITEM, not the job (a job claiming A whose item is
                                 B's is scoped to B and consumes nothing).
```

### A.3 DEFECT FOUND BY PART A AND FIXED — F-063-2 (production-blocking)

The brief recorded F1 consumption as "implemented" (059 / `0c06105`). It was **not reachable**:

```text
backend/services/automatic_processing.py:1260  →  NameError: name 'MatchRequest' is not defined
```

`MatchRequest` is imported only locally inside `_map()`, and `_consume_effective_adjudication()`
referenced it unqualified. Its broad `except Exception: return None` swallowed the NameError, so
**every** adjudication consumption silently fell back to the clarification diversion — the
persisted adjudication could never actually be consumed in production.

Evidence (before the fix, Part A tests A2/A3 failed):

```text
ERROR services.automatic_processing: F-039-1: adjudication consumption failed for job …
  File "…/services/automatic_processing.py", line 1260, in _consume_effective_adjudication
    clarified_request = MatchRequest(
NameError: name 'MatchRequest' is not defined
→ assert final.stage == "review"  failed: 'blocked' == 'review'   (A2 and A3)
```

Fix (4 lines, in `a509593`): the same local import this module already uses for the symbol,
placed after the policy has re-selected. Nothing about the consumption contract was weakened,
widened or redesigned; A2/A3 then pass, which is the direct proof the path now executes.

---

## PART B / C — THE ADJUDICATION READS (`52c9ef0`)

### B/C.1 What changed

```text
backend/api/v3_activity_clarifications.py              (+224 lines: two read endpoints + projection)
backend/tests/unit/api/test_v3_activity_clarifications_api.py  (+20 tests: 9 Part B, 11 Part C)
```

Two narrow, authenticated, item-bounded reads added to the existing clarification router:

```text
GET /api/v3/activity-clarifications/effective
      ?organization_id=…&item_id=…&activity=…
      → {found: bool, adjudication: AdjudicationVersionOut | null}

GET /api/v3/activity-clarifications/history
      ?organization_id=…&item_id=…&activity=…&adjudication_id=…
      → {adjudication_id, count, current_version, versions:[…oldest→newest]}
```

Reuse rather than invention:

```text
authorization   ensure_processing_org_access (unchanged, real) — org members for their own
                organisation; consultants only with an ACTIVE consultant_clients grant;
                Processing Entity staff denied; internal staff allowed. NOT mocked.
context         resolved from the PERSISTED extraction item through the SAME helper the write
                paths use (`_item_evidence` → `resolve_evidence`): tenant from
                item → batch → organization; 404 for an unknown item; 403 when the item belongs
                to another organisation. The client cannot name an organisation, actor,
                version, currency flag, evidence signature or factor.
reads           the repository's own `effective(...)` and `history(...)` — no new SQL, no
                duplicated statement, and no organisation-wide / global lookup:
                organisation + effective_context_key + activity_key + original_activity +
                is_current for the current read; organisation + adjudication_id (+ ORDER BY
                version ASC) for the history read.
history id      the named adjudication is first resolved inside the authorised tenant
                (`get(id, organization_id=…)`) and then checked against the asserted bounded
                context (context key, activity key, original activity); anything else is 404.
                A history read is therefore impossible for another tenant or another context.
```

### B/C.2 Exact results

```text
$ .venv/bin/python -m pytest tests/unit/api/test_v3_activity_clarifications_api.py -q
exit 0   ·   51 collected items (26 pre-existing functions + 20 new tests + 6 parametrised cases)
```

Part B (current/effective) — 9 tests:

```text
own organisation                     → 200, found=true, projected row; lookup tuple asserted
other organisation                   → 403, NO SQL executed
item belongs to another org          → 403 (server-derived tenant wins over the request)
authorized consultant client         → 200
unauthorized consultant client       → 403 · ended grant → 403 · no firm membership → 403
unauthenticated                      → 401, NO SQL executed
unknown item / invalid context       → 404, no adjudication read
no current adjudication              → 200 {found:false, adjudication:null} (empty, not invented)
missing item_id (global lookup try)  → 422, NO SQL executed
```

Part C (immutable history) — 11 tests:

```text
v1 only                               → count 1, current_version 1, is_current true
v1 + v2                               → count 2, ordered [1, 2]
deterministic order                   → the repository's `ORDER BY version ASC` is in the SQL
v2 identified as current              → current_version 2; v1 is_current false, v2 true
v1 unchanged                          → the stored rows are byte-identical after the read
other organisation                    → 403, NO SQL executed
authorized consultant client          → 200; tenant-scoped params asserted
unauthorized / ended-grant consultant → 403, NO SQL executed
unauthenticated                       → 401, NO SQL executed
id from another context / activity    → 404, the history statement is never issued
unknown adjudication / unknown item   → 404
no global lookup                      → every adjudication statement carries
                                        `organization_id = $1` and a WHERE clause
```


---

## PART D — REGRESSION (exact commands and results)

All runs: `cd /tmp/ct_step2/backend`, interpreter `python -m pytest …` from
`/tmp/ct_step2/backend/.venv/bin/python`, with `-v` so every test's own PASSED line is recorded;
the trailing summary line is present in the captured files and is quoted verbatim below.

```text
# 01 activity-clarification repository
python -m pytest tests/unit/data/test_activity_clarifications_repository.py -v
exit 0 · 17 passed in 0.51s

# 02 activity-clarification API (writes + the new reads)
python -m pytest tests/unit/api/test_v3_activity_clarifications_api.py -v
exit 0 · 51 passed, 1 warning in 1.12s     (warning = pre-existing Starlette/httpx notice)

# 03 automatic-processing service (A1–A8)
python -m pytest tests/unit/services/test_automatic_processing.py -v
exit 0 · 38 passed in 0.63s

# 04 D-A (natural-gas basis/discovery)
python -m pytest tests/unit/test_d_a_natural_gas_basis.py \
                 tests/unit/engines/test_d_a_natural_gas_discovery.py -v
exit 0 · 35 passed in 0.55s

# 05 D-FS (factor-selection policy)
python -m pytest tests/unit/engines/test_factor_selection_policy.py -v
exit 0 · 19 passed in 0.65s

# 06 039
python -m pytest tests/unit/engines/test_factor_selection_followup_039.py -v
exit 0 · 14 passed in 0.49s

# 07 041
python -m pytest tests/unit/engines/test_activity_clarification_041.py -v
exit 0 · 16 passed in 0.49s

# 08 043 + 045 (the family-conflict/compatibility rule has no separate 045 module —
#    its assertions live in this file, as the 045 report records)
python -m pytest tests/unit/engines/test_activity_clarification_043.py -v
exit 0 · 13 passed in 0.50s

# 09 broader backend suite
python -m pytest tests/unit -v
exit 1 · 6 failed, 2732 passed, 1 skipped, 4 warnings in 289.72s (0:04:49)
```

### D.0 Final combined confirmation (after all edits, immediately before this report)

```text
python -m pytest tests/unit/services/test_automatic_processing.py \
                 tests/unit/api/test_v3_activity_clarifications_api.py \
                 tests/unit/data/test_activity_clarifications_repository.py -q
exit 0 · 106 collected items (38 + 51 + 17) — all passed
```

(The trailing "N passed" line was suppressed by this environment in that invocation; the exit
code plus the collected-item count and the per-file summaries in D.1 are the evidence.)

### D.1 Pre-existing vs introduced — established by a pristine baseline run

A detached worktree at the exact starting SHA was used, and the identical command run there:

```text
$ cd /tmp/ct_step2 && git worktree add --detach /tmp/ct_baseline 45e8c2b919fb13bb2a8fa8baada1183f398f1b1c
$ cd /tmp/ct_baseline/backend && python -m pytest tests/unit -v
exit 1 · 6 failed, 2701 passed, 1 skipped, 4 warnings in 249.57s (0:04:09)
```

```text
failure-set diff (baseline vs changed tree)   → IDENTICAL (same 6 node ids)
passed delta                                  → +31  (2732 − 2701)
skipped / failed delta                        → 0 / 0
```

The +31 is fully reconciled to the new tests: 11 in `test_automatic_processing.py`
(27 → 38 items) and 20 in `test_v3_activity_clarifications_api.py` (31 → 51 collected items:
26 pre-existing functions, one of which is parametrised into 6 cases). No pre-existing test was
shadowed, renamed, skipped, deleted or weakened, and no test was lost.

The 6 failures (all present at the baseline SHA, unrelated to F-039-1):

```text
tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_operations_surface
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_pe_surface
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
```


### D.2 RLS / integration

```text
$ cd /tmp/ct_step2/backend
$ INTEGRATION_DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test' \
  .venv/bin/python tests/integration/verify_activity_clarifications_rls.py
exit 1
asyncpg.exceptions.NotNullViolationError: null value in column "adjudication_id" of relation
"activity_clarifications" violates not-null constraint
```

**BLOCKED — pre-existing defect F-063-1, not introduced by this window and not fixed here.**
Migration `…_p8_fs_adjudication_lifecycle.sql` (commit `3e11155`, the 055 work) adds
`adjudication_id uuid` and then `ALTER COLUMN adjudication_id SET NOT NULL` with no default, but
the RLS verification script's fixture `INSERT` predates it: the script was last written in
`df92c63`, the commit immediately before `3e11155`, and never supplies the column. Confirmed by
history and by the live column state read from the disposable database:

```text
adjudication_id       nullable=NO  default=None
effective_context_key nullable=NO  default=None
version               nullable=NO  default=1
is_current            nullable=NO  default=true
```

The script is self-contained and non-destructive by design (it seeds only its own `qa:`-labelled
rows and deletes them), but it additionally requires an ACTIVE member in the alphabetically-first
organisation of the target. That single precondition was supplied explicitly against the
disposable `carbontally_test`, then removed, and the database was shown to be unchanged:

```text
SEEDED_MEMBERSHIP_ID 3dd62c67-d27f-4e9b-9659-0a82080faf36
BEFORE orgs/active_members/adjudications/users/firms: (23, 13, 0, 652, 2)
AFTER  orgs/active_members/adjudications/users/firms: (23, 13, 0, 652, 2)
RESTORED_TO_BASELINE True
```

The seed still failed the script at its first fixture insert, which is exactly the F-063-1
evidence above. Nothing else was mutated; no persistent environment (QA, demo, investor,
production) was touched; F-046-1's refusal guard was not bypassed (`carbontally_test` is an
explicitly permitted target).

Because the behavioural matrix cannot run until F-063-1 is fixed, the RLS layer was evidenced
**read-only** from the disposable database — sufficient for this window's claim, since no DDL,
migration, policy or repository SQL was changed:

```text
RLS enabled on public.activity_clarifications: True (forced: False)
policy select : (is_org_member(organization_id) OR is_org_consultant(organization_id))
policy insert : WITH CHECK is_org_member(organization_id)
policy update : USING is_org_member(organization_id) WITH CHECK is_org_member(organization_id)
policy delete : USING is_org_member(organization_id)
```

The database-level tenant boundary is intact and still admits the consultant-client read path the
new endpoints rely on as defence in depth.

The DB-dependent `tests/integration` pytest tree was **not** run: its `conftest.py` performs
destructive setup (`TRUNCATE … RESTART IDENTITY CASCADE`), and this window changes no schema,
migration, RLS policy or repository SQL, so a destructive run was neither necessary nor
appropriate (F-046-1 / AGENTS.md §55). Recorded as such rather than claimed.

---

## KNOWN PRE-EXISTING ISSUE — F-051-1

Unchanged and untouched, as instructed: the migration tree contains 74 migrations while a
historical test pins 71. That test was not modified, not weakened and is not counted as an
F-039-1 defect; it is one of the six pre-existing unit failures listed in D.1 and behaves
identically at the baseline SHA. This window adds **no** migration (verified:
`git diff --name-only 45e8c2b…HEAD | grep -iE 'migration|\.sql'` → NONE), so F-051-1's numbers
cannot have moved.

## FINDINGS RAISED THIS WINDOW

```text
F-063-1  Pre-existing, BLOCKING for RLS behaviour re-verification (not F-039-1 code).
         tests/integration/verify_activity_clarifications_rls.py cannot execute against the 055
         schema: its fixture INSERT omits the now NOT NULL `adjudication_id` (migration commit
         3e11155; script commit df92c63). Remedy (not applied — outside this window's
         authorisation): supply `adjudication_id` (e.g. gen_random_uuid()) in the script's
         fixture INSERT.

F-063-2  FIXED in `a509593`. F1 adjudication consumption raised `NameError: name 'MatchRequest'
         is not defined` on every attempt, and its broad exception handler disguised this as
         "no compatible adjudication", so the persisted adjudication could never be consumed in
         production. Fixed with the module's own local-import convention; A2/A3 prove the path
         now executes end-to-end.
```


## GIT STATE

```text
45e8c2b919fb13bb2a8fa8baada1183f398f1b1c   starting SHA (baseline verified)
a50959303ddc4573eac841bea9dc5a42f9ef6031   Part A (F1 defect fix + service tests A1–A8)
52c9ef0bb2929bc848f5e2013ddfbb3a798653ef   Part B/C (reads + 20 tests)
c5eeadb…                                    this report
4bd04862…                                   correction of record (Part B/C count)
FINAL SHA      the branch tip after this report's own commits — HEAD == origin verified at
               hand-off (this report's text cannot contain the SHA of the commit that
               introduces it; the exact tip is recorded in the hand-off summary)
```

After every commit: `git rev-parse HEAD == git rev-parse origin/p8-release-reconciled` and
`git status --porcelain` empty. No reset, no rebase, no force-push, no unrelated change absorbed,
no secret, credential, token or signed URL introduced.

**Correction note:** the Part B/C commit message (`52c9ef0`) says "…21 authorization/isolation/
versioning tests". The verified count is **20** (9 Part B + 11 Part C), as recorded everywhere
else in this report and reconciled against the baseline in D.1. The message was not amended,
because amending would require rewriting already-pushed shared history (forbidden); this note is
the correction of record.

Change footprint of the two code/test commits (no SQL, no migration, no DDL, no UI):

```text
backend/api/v3_activity_clarifications.py                      +224
backend/services/automatic_processing.py                       +4
backend/tests/unit/api/test_v3_activity_clarifications_api.py  +20 tests
backend/tests/unit/services/test_automatic_processing.py       +11 tests (fixtures + A1–A8)
```

## SUCCESS CRITERION — IMPLEMENTED AND TESTED

```text
clarification → persistent adjudication → version/history → server-derived evidence signature
   ▼
later automatic processing → effective adjudication lookup → compatibility check
   → semantic clarification consumed → existing factor-selection policy
   → factor OR ambiguity/unresolved
   ▼
selected_factor_id never bypasses policy ............ A3 (and no write path accepts one)
changed evidence prevents silent reuse ............. A4 (and A5 for a missing signature)
tenant/client isolation ............................ A8 (service) + Parts B/C (HTTP, real gate)
   ▼
current/effective adjudication read endpoint ....... Part B — 9 tests
immutable history read endpoint .................... Part C — 11 tests
direct service/API tests proving the lifecycle ..... 31 new tests, all green
```

## REMAINING INCOMPLETE SCOPE

```text
1. F-063-1 (pre-existing) blocks the behavioural RLS matrix for activity_clarifications; the
   one-line fixture remedy above is required before that evidence can be produced.
2. The D19/UI consumption of the two new reads is NOT implemented and was explicitly out of
   scope (no UI change authorised).
3. Service-path runtime verification against a real database was not performed (unit-level only,
   as in 055/056/058/059); no DDL changed, so the 055/056 disposable-DB verification stands.
4. The DB-dependent destructive integration tree was not run (see D.2 for the reason).
```

## VERDICT

VERDICT: IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION

Scope completed: A (F1 service tests A1–A8, plus the production defect that prevented F1 from
working), B (current/effective read endpoint + tests), C (history read endpoint + tests),
D (regression recorded, failures classified against a pristine baseline).

Nothing is claimed beyond what is evidenced above: the lifecycle is **implemented and tested at
the unit/service/HTTP seams with the real repository, real engine, real policy and real
authorization gate**; independent verification has NOT been performed; no Product Owner closure
is claimed; production, migrations and the investor demo were not touched, and nothing was
deployed. F-063-1 remains open and blocks one item of Part D.

