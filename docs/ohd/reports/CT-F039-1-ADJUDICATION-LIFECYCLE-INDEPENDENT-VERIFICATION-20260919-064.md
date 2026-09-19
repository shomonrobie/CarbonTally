> **CORRECTION (added by CT-STEP2-F039-1-REMEDIATION-065).** This verification returned
> "PASS WITH FINDINGS — NO BLOCKING DEFECT FOUND" and it was **wrong about that**. A
> subsequent OHD pass identified, and a real-database reproduction confirmed, a **blocking
> defect the checks below could not see**: `apply_versioned()` inserted the new
> `is_current = true` row BEFORE retiring the previous current row, so version 2 could never
> be created against the shipped schema (partial unique index
> `activity_clarifications_current_unique` on `(adjudication_id) WHERE is_current`), and the
> three statements were not even one transaction. Root cause of the miss: every persistence
> check in this window — the F1 service probe, the API probe and the repository tests — was
> driven through a **scripted fake connection**, so the real uniqueness constraint and real
> transaction behaviour were never exercised. The lifecycle is remediated and proved against
> the real database in `docs/cline/reports/CT-STEP2-F039-1-REMEDIATION-065.md`; the
> recommendation for future verification is to include at least one real-schema persistence
> test for any invariant that is enforced by a database constraint.


```text
OBJECT          Independent read-only verification of the F-039-1 Activity Clarification
                Adjudication Lifecycle implementation
TARGET SHA      ca509d4ceee4bfa986825a88e10ef679443c29e9
BRANCH          p8-release-reconciled  (HEAD == origin/p8-release-reconciled; tree clean)
VERIFIED AT     tree was clean at verification start; no commit, no push, no code/test/
                migration/config/documentation change was made during this verification
METHOD          independent probes written from scratch (own fakes), the REAL repository,
                REAL engines, REAL router and REAL authorization gate; the implementer's
                report was NOT used as evidence and its numbers were re-derived
DATABASES       disposable only (127.0.0.1:54426 carbontally_test) — read-only inspection
                plus isolated 'qa:iv064'-labelled fixtures, all removed and restored
PRODUCTION      not touched · not deployed · no Render/DB/customer change
CLOSURE         no PO closure claimed
VERDICT         PASS WITH FINDINGS — NO BLOCKING DEFECT FOUND  (see §16)
```

## 1. RELEASE BASELINE (independently verified)

```text
$ git branch --show-current                  → p8-release-reconciled
$ git rev-parse HEAD                         → ca509d4ceee4bfa986825a88e10ef679443c29e9
$ git rev-parse origin/p8-release-reconciled → ca509d4ceee4bfa986825a88e10ef679443c29e9
$ git status --porcelain                     → (empty)
```

Commit chain 058 → 059 → 063 (5 commits from the 45e8c2b starting SHA):

```text
ca509d4  docs(063): finalise report git-state block
4bd0486  docs(063): correct Part B/C test count of record
c5eeadb  docs(063): report
52c9ef0  feat(p8/fs): F-039-1 B/C — item-bounded adjudication reads + 20 tests
a509593  fix(p8/fs): F1 — import MatchRequest in consumption + service tests A1–A8
```

Implementation footprint (058→target) — the target contains the expected implementation,
not merely a claim:

```text
$ git diff --stat c83233f..ca509d4
 backend/api/v3_activity_clarifications.py                      | 224 +
 backend/services/automatic_processing.py                       | 101 +-
 backend/tests/unit/api/test_v3_activity_clarifications_api.py  | 312 +
 backend/tests/unit/services/test_automatic_processing.py       | 558 +
 docs/cline/reports/…-059.md, …-063.md                          | 589 +
$ git diff --name-only 45e8c2b9..ca509d4 | grep -iE 'migration|\.sql'  → NONE
```

No migration, no DDL, no RLS policy, no UI change is part of this range.

## 2. COMMANDS EXECUTED (all read-only w.r.t. the repository)

```text
# baseline
git branch --show-current | git rev-parse HEAD | git rev-parse origin/p8-release-reconciled
git status --porcelain | git log --oneline -8 | git diff --stat c83233f..ca509d4
git diff --name-only 45e8c2b9..ca509d4 | grep -iE 'migration|\.sql'

# baseline sandbox WITHOUT touching git state
git archive 45e8c2b919fb13bb2a8fa8baada1183f398f1b1c | tar -x -C /tmp/iv/base

# independent probes (own fakes; real service/repository/engines/policy/router/auth)
python /tmp/iv/probe_f1.py          # F1 end-to-end consumption invariant     21 checks
python /tmp/iv/probe_api.py         # read endpoints + access matrix + bypass 48 checks
python /tmp/iv/probe_sig.py         # signature + repository + provenance     27 checks
python /tmp/iv/defect_repro.sh      # baseline reproduction of the MatchRequest defect
python /tmp/iv/compare_runs.py      # failure-set comparison target vs baseline
python /tmp/iv/collect_delta.py     # collected-item reconciliation

# focused suites (target tree)
python -m pytest tests/unit/data/test_activity_clarifications_repository.py -q
python -m pytest tests/unit/api/test_v3_activity_clarifications_api.py -q
python -m pytest tests/unit/services/test_automatic_processing.py -q
python -m pytest tests/unit/test_d_a_natural_gas_basis.py \
                 tests/unit/engines/test_d_a_natural_gas_discovery.py -q
python -m pytest tests/unit/engines/test_factor_selection_policy.py -q
python -m pytest tests/unit/engines/test_factor_selection_followup_039.py -q
python -m pytest tests/unit/engines/test_activity_clarification_041.py -q
python -m pytest tests/unit/engines/test_activity_clarification_043.py -q
python -m pytest tests/unit/test_units_family_compat.py tests/unit/test_units_qualifier.py \
                 tests/unit/test_units.py -q

# broad suites — target and pristine baseline (420-440 s each)
python -m pytest tests/unit -v -p no:cacheprovider                 (target)
(cd /tmp/iv/base/backend && python -m pytest tests/unit -v)         (baseline)

# database (disposable only)
python /tmp/iv/rls_schema.py        # read-only schema/policy/index/constraint inspection
python /tmp/iv/rls_behavior.py      # behavioural RLS matrix with isolated QA fixtures
python /tmp/iv/f063_check.py        # harness INS executed inside a rolled-back transaction

# registration/contract
python -c "import main; p=main.app.openapi()['paths']; …"           # composed app OpenAPI
```

## 3. TEST RESULTS (re-derived, not copied)

Focused suites — every one exit 0 (item counts from `--collect-only`):

```text
tests/unit/data/test_activity_clarifications_repository.py      17 items  exit 0
tests/unit/api/test_v3_activity_clarifications_api.py           51 items  exit 0
tests/unit/services/test_automatic_processing.py                38 items  exit 0
D-A (natural_gas_basis 26 + natural_gas_discovery 9)            35 items  exit 0
D-FS (factor_selection_policy)                                  19 items  exit 0
039  (factor_selection_followup_039)                            14 items  exit 0
041  (activity_clarification_041)                               16 items  exit 0
043 + 045 (activity_clarification_043; the 045 rule has no separate module) 13 items  exit 0
units (family_compat 35 + qualifier 27 + units 13)              75 items  exit 0
```

Broad suite — independent run in the target tree:

```text
tests/unit → exit 1 · 6 failed, 2732 passed, 1 skipped, collected 2739
```

This **matches the implementer's reported 6 / 2732 / 1** exactly. See §12 for the
baseline comparison.


## 4. F1 EVIDENCE — AUTOMATIC-PROCESSING CONSUMPTION (Part 2 items 1–11)

Code path (read directly): `_map()` builds the `MatchRequest` from the persisted job, runs the
family gate `assess_family_conflict(...)`, and on `clarification_required` calls
`_consume_effective_adjudication(job=job, activity=…, unit=…, candidates=gate_candidates,
request=request)`; a `None` return preserves the pre-existing diversion
(`reasons.append("line N: clarification required …")` + `_clarification_entry` + `continue`);
a consumed result falls through to the SAME confidence/`matched` checks as any other match.

My own probe (`/tmp/iv/probe_f1.py`) drives the real `AutomaticProcessingService` with the real
repository/engine/policy — **21/21 PASS**:

```text
C1  no adjudication            → blocked; mapped_data None; no factor guessed; the reason is
                                 the ENGINE's own family-conflict text; the bounded-context
                                 lookup really ran
C2  compatible adjudication    → reaches review; policy re-entered with "Waste Landfill";
                                 mapped factor = matcher result (≠ stored "lf")
C3  stored selected_factor_id  → stored clarification "Landfill" (policy "lf") while the row
                                 stores "ol": the mapped factor is neither — the policy is the
                                 only selection path
C4  re_evaluation_required     → NOT consumed
C5  changed persisted unit     → NOT consumed (signature differs)
C6  NULL stored signature      → NOT reused
C7  still ambiguous            → unresolved; the matcher is never invoked with the adjudication
C8  v1 retired + v2 current    → only v2 reaches the policy; v1 never consumed; rows unmutated;
                                 ZERO writes issued by the consumption path
C9  another tenant's row       → invisible (lookup parameterised by the resolved tenant)
C10 injected evidence-layer error → conservative diversion; job NOT marked failed and NOT
                                 reported as a success
C11 job without source_item_id → diversion, and no adjudication query issued at all
```

Bounded context: the lookup tuple is `(org, item, item, "Waste")` and the predicate set is
`organization_id = $1 AND effective_context_key = $2 AND activity_key = $3 AND
original_activity = $4 AND is_current` — the context comes from `job.source_item_id`, never
from the activity text alone.

### 4.1 The reported `MatchRequest` defect — independently reproduced

Against a pristine baseline code sandbox (read-only `git archive` of `45e8c2b9`; no git state
was altered):

```text
target module exposes MatchRequest as a module global ..... False
baseline module exposes MatchRequest as a module global ... False
(the symbol exists only as a local import inside functions)

target's own A2/A3 tests run against BASELINE code:
  exit=1
  ERROR services.automatic_processing: F-039-1: adjudication consumption failed for job …
  NameError: name 'MatchRequest' is not defined        (A2 and A3)
  assert final.stage == "review"  →  'blocked' == 'review'

my own probe against BASELINE code: 16/21 (C2/C3 fail; 3 NameError occurrences)
```

Against the target the same probe is 21/21 and the same tests pass ⇒ the defect was real, the
fix resolves it, and the new tests are genuine detectors rather than vacuous helper assertions.


## 5. REPOSITORY LIFECYCLE EVIDENCE (Part 4)

`tests/unit/data/test_activity_clarifications_repository.py` → 17 items, exit 0. My own probe
additionally asserts at the SQL/statement level (`/tmp/iv/probe_sig.py`):

```text
R1  v1 creation supplies a NON-NULL adjudication_id (36-char uuid) — the 055 NOT NULL
    constraint is satisfied by the production write path
R1b v1 row carries version 1, is_current true, and the server-derived organisation
R1c every READ/UPDATE/DELETE statement carries `organization_id = $1`
R2  replay of the SAME clarification returns the stored version and issues no INSERT/UPDATE
R3  a changed clarification creates version 2 with the SAME adjudication_id and
    supersedes_id = v1's row → one lineage, versioned
R3b the ONLY statement touching v1 is
    `UPDATE … SET is_current = false, updated_at = now() WHERE organization_id = $1 AND id = $2`
    — no clarification/outcome/factor column is touched (audit data preserved)
R4  history is tenant-scoped, lineage-bounded and `ORDER BY version ASC`
R5  effective() requires org + effective_context_key + activity_key + original_activity
    + is_current (never the activity text alone)
R6  no authoring method accepts selected_factor_id/factor_set/factor_source/reporting_year
    → historical factor metadata is projection/audit data, not an authoring capability
```

Database-level invariants (read-only, disposable DB) confirm the same properties are enforced
by the schema, not only by code:

```text
UNIQUE (adjudication_id) WHERE is_current        → exactly one current version per lineage
UNIQUE (adjudication_id, version)                → version identity
UNIQUE (activity_key, original_activity,
        clarification, version)                  → replay identity
FKs: item_key, batch_key, organization_id, selected_factor_id, supersedes_id
indexes: effective_idx ON (organization_id, effective_context_key, activity_key,
         original_activity) WHERE is_current; history_idx ON (adjudication_id, version DESC)
```

## 6. EVIDENCE-SIGNATURE EVIDENCE (Part 5, D-F039-1-I)

```text
S1  evidence_signature(original_activity, unit, scope) — EXACTLY three parameters
S1b none of filename / file_name / ocr_text / raw_text / invoice_number / supplier /
    quantity / date / metadata / batch_key / item_key is accepted (structurally absent)
S2  identical evidence ⇒ identical signature; case/whitespace normalised
S3  changed ACTIVITY ⇒ different signature
S4  changed UNIT     ⇒ different signature
S5  changed SCOPE    ⇒ different signature
S6  NULL/absent evidence produces its own signature, never equal to real evidence
S7  a stored NULL signature is NOT compatible ⇒ no silent reuse
S8  a matching stored signature IS compatible
S9  the write payloads declare NO unit/scope/actor/outcome/factor fields and are
    extra="forbid": a body carrying selected_factor_id, actor_id, factor_set, factor_source,
    outcome_status, unit or scope is rejected 422 with nothing persisted
S10 `reporting_year`/`country` ARE accepted — they are declared matching-scope inputs; a
    client-supplied reporting_year (1999) does not become the recorded year (the persisted
    value is the policy's own factor year, 2025)
```

No expansion of the signature beyond the three PO-approved fields was found.

## 7. PROVENANCE EVIDENCE (Part 6)

```text
P1b the context query derives the tenant by joining the parent batch:
      LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id → b.organization_id
P1c the context query keys on the persisted item id only (`WHERE i.id = $1`)
P2  resolve_evidence(self, item_id, activity) — a caller cannot supply organisation,
    provenance, unit or scope
P3  authoritative unit/scope come only from the persisted extracted_data line
    (unit keys ('unit','raw_unit'), scope keys ('scope',))
P4  a zero-match or multiple-match line yields (None, None) — nothing is invented and no
    client value is substituted; exactly one exact (case-insensitive) match is required
P5  server-derived provenance: 201 responses persist the authenticated user as actor_id and
    the server-derived actor_scope ('organization_member' / 'consultant'); the factor recorded
    is the policy's own result ('lf'), not anything from the body
P6  forged organisation rejected, forged item rejected (403, no INSERT):
      - member of A naming organisation B ......... 403, zero statements executed
      - member of A naming B's item ............... 403 after the tenant-validation read only;
                                                    no INSERT/UPDATE/DELETE issued
      - an id from another tenant ................. 404 (tenant-scoped by-id read)
      - an id from another context/activity ....... 404, the history statement never runs
```


## 8. CURRENT/EFFECTIVE READ ENDPOINT EVIDENCE (Part 7)

Registered in the production composition root (not just in the test harness):

```text
$ python -c "import main; p=main.app.openapi()['paths']; …"
main file        /tmp/ct_step2/backend/main.py
V3 available     True
paths            575
/api/v3/activity-clarifications/effective  present
/api/v3/activity-clarifications/history    present
/api/v3/activity-clarifications/options    present (pre-existing)
```

Behaviour — my own probe (`/tmp/iv/probe_api.py`, 48/48 PASS overall), driving the REAL router
over the REAL `ensure_processing_org_access` chain and the REAL repository:

```text
B1  own-org member       200 found=true; the projection carries the server's own recorded state
B1  lookup is the repository's bounded effective() query (org + context + activity +
    original_activity + is_current) — no duplicated/global SQL
B13 unknown item         404 "extraction item not found"; no adjudication statement runs
B14 no current adjudication → 200 {"found": false, "adjudication": null} (empty, not invented)
B15 no item_id           422; zero statements (no organisation-wide/global lookup)
B16 wrong activity in an existing context → found=false (the predicates, not the caller,
    decide) 
```

## 9. HISTORY READ ENDPOINT EVIDENCE (Part 8)

```text
C1  v1 + v2             200; count 2; versions [1, 2] (oldest→newest); current_version 2;
                        v1 is_current false, v2 true; stored rows echoed unchanged
C1  ordering + tenant scope come from the repository SQL:
      … WHERE organization_id = $1 AND adjudication_id = $2 ORDER BY version ASC
C2  v1 only             200; count 1; current_version 1
C2b no current version  200; count 1; current_version null
C3  adjudication from ANOTHER CONTEXT → 404; the history statement never runs
C3b adjudication for a different ACTIVITY → 404; history never runs
C10 unknown adjudication id → 404
C9  client org B asking for A's adjudication id → 404 (tenant-scoped by-id read)
```

### 9.1 FINDING F-064-1 — the history `adjudication_id` parameter resolves against the ROW id

Reproduced with a faithful fake (row `id` ≠ lineage `adjudication_id`, which is the real shape
for every lineage created after the 055 migration):

```text
FINDING-EVIDENCE | history via lineage adjudication_id -> 404 adjudication not found in this
                        extraction context
FINDING-EVIDENCE | history via version row id          -> 200 count=2
```

Root cause: `get_adjudication_history` calls `repos.clarifications.get(adjudication_id,
organization_id=…)`, and `get()` binds its argument to the **`id` column**
(`_SELECT_BY_ID_SQL = … WHERE organization_id = $1 AND id = $2`) while its docstring says
"read by adjudication id". The 055 schema makes these different values:

```text
id               NOT NULL, default gen_random_uuid()
adjudication_id  NOT NULL, NO default (supplied by record() as str(uuid.uuid4()))
```

So a client that takes the value the effective endpoint publishes as `adjudication_id` (its
sibling field `id` is the row id) gets a 404 for any post-055 lineage. The endpoint remains
usable via the `id` value the effective response also returns, and cross-tenant/cross-context
access still fails closed — hence non-blocking — but the parameter name and the documented
contract do not match the resolution, and the natural call fails. **Fix required** (choose one
and record it): resolve the lineage seed by `adjudication_id` (tenant-scoped), or rename the
parameter to `version_id`/`row_id` and say so; the effective response should then be aligned.
Note that the implementer's own API tests cannot catch this: their fake connection returns the
scripted row regardless of the id argument.


## 10. AUTHORIZATION / RLS EVIDENCE (Parts 9 and 10)

### 10.1 HTTP access matrix (real gate chain; none of the authorization functions mocked)

```text
authenticated org member, own org ............ 200 (reads) / 201 (writes)
organization member, other org ............... 403, zero statements executed
authorized consultant (active grant) ......... 200 / 201
consultant without grant ..................... 403, zero statements
consultant with ENDED grant .................. 403
consultant granted A asking for B ............ 403, zero statements
consultant client, own client org ............ 200
consultant client, other organisation ........ 403
internal staff (is_staff, entity_id NULL) .... 200 (operational oversight)
Processing Entity staff (entity_id set) ...... 403, zero statements
unaffiliated authenticated user .............. 403, zero statements
anonymous .................................... 401, zero statements
```

No path was found that allows cross-tenant access; the item-resolution 403
("extraction item belongs to another organisation") means a caller authorised for org A cannot
reach org B's context even though the gate for A passed.

### 10.2 RLS at the database (disposable `carbontally_test`, read-only + isolated fixtures)

```text
RLS enabled on public.activity_clarifications ... True (forcerowsecurity False)
policies: SELECT  (is_org_member(organization_id) OR is_org_consultant(organization_id))
          INSERT  WITH CHECK is_org_member(organization_id)
          UPDATE  USING + WITH CHECK is_org_member(organization_id)
          DELETE  USING is_org_member(organization_id)
```

Independent behavioural matrix — the project harness was NOT modified; I ran my own
role-playing probe (`/tmp/iv/rls_behavior.py`, **16/16 PASS**) with
`SET LOCAL ROLE authenticated/anon/service_role` + `request.jwt.claim.sub`, creating only my
own `qa:iv064`-labelled rows and consultant artefacts:

```text
member/own SELECT 1 row · INSERT allowed · UPDATE allowed
member A→B: SELECT 0 rows · INSERT rejected by RLS · UPDATE 0 · DELETE 0
B's row survived A's attempts unmodified (unit still NULL)
consultant with ACTIVE grant on A: SELECT allowed (consultant read path intact)
consultant INSERT/UPDATE denied (member-only policies)
consultant → unauthorised client B: SELECT 0 rows
anon: SELECT/INSERT denied
service_role: allowed (BYPASSRLS)
cleanup: before == after on all seven tables (activity_clarifications, organizations,
         organization_members, users, consultant_profiles, consultant_firm_members,
         consultant_clients); activity_clarifications 0 rows before and after
```

## 11. ANTI-BYPASS EVIDENCE (Part 11)

```text
D1  body carrying selected_factor_id ................. 422, nothing persisted
D2  body carrying actor_id / factor_set / factor_source /
    outcome_status / unit / scope .................... 422 each, nothing persisted
D2b client-supplied reporting_year (1999) ............ does NOT become the recorded year
D3  member of A naming organisation B ................ 403, zero statements
D4  member of A naming B's item ...................... 403 (validation read only; NO insert)
D5  legitimate clarification ......................... persists org = resolved tenant,
                                                       actor_id = authenticated user,
                                                       actor_scope = server-derived,
                                                       factor = the policy's own result ("lf");
                                                       the stored id "ol" never appears
D6  consultant decline ............................... actor_scope "consultant", NO factor
D7  control fields in a decline body ................. 422
D8  decline-style text submitted as a clarification ... rejected (not a factor bypass)
R6  no authoring method accepts factor metadata (repository, by construction)
C3  a persisted selected_factor_id ("ol") does not influence the factor later mapped
C8  a retired version's clarification/factor data is never consulted
```

Conclusion: no client-controlled path to factor selection, actor identity, provenance,
outcome or version state was found, and historical `selected_factor_id` values are inert.


## 12. REGRESSION COMPARISON (Part 12)

```text
TARGET   tests/unit → exit 1 · 6 failed, 2732 passed, 1 skipped · collected 2739
BASELINE tests/unit → exit 1 · 6 failed, 2673 passed, 2 skipped · collected 2681
         (baseline = read-only `git archive` of 45e8c2b9 into /tmp/iv/base)

failure-set diff (baseline vs target) ................ IDENTICAL (same 6 node ids)
collected-item reconciliation ........................ target 2739 vs baseline 2681 = +58
   +20  tests/unit/api/test_v3_activity_clarifications_api.py  (31 -> 51)
   +38  tests/unit/services/test_automatic_processing.py       (0 -> 38, because the
        sandbox copy of that file was deliberately removed to obtain a pristine baseline;
        it contributes 27 baseline items, so the corrected comparison is 2681+27 = 2708)
=> target 2739 − 2708 = +31 items = exactly the 11 service + 20 API tests added by 063
```

The 6 failures (identical in both trees; none of these files imports either changed module —
checked: 0 matches for `automatic_processing` / `v3_activity_clarifications`):

```text
tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
    → asserts `len(migrations) == 71` against the tree's 74  = F-051-1 (pre-existing)
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_operations_surface
tests/unit/api/test_p6_1b_membership_workspace_authorization.py::test_consultant_cannot_reach_pe_surface
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
```

No pre-existing failure is caused or worsened by F-039-1/063; the implementer's reported
numbers are reproduced exactly. One environment-dependent skip differs between the sandbox
baseline and the worktree (1 vs 2); it does not affect the failure set, the changed files or
the collected reconciliation above.

## 13. F-063-1 ASSESSMENT (pre-existing RLS-harness incompatibility)

Independently determined by executing the harness's OWN `INS` constant against the disposable
database inside a transaction that is always rolled back (zero rows written, before == after):

```text
HARNESS INS (exact, from the module):
  INSERT INTO public.activity_clarifications (activity_key, organization_id, original_activity,
    clarification, policy_input, outcome_status)
    VALUES ($1,$2,'QA','QA','QA','clarification_required')
supplies adjudication_id: False
OUTCOME: NotNullViolationError: null value in column "adjudication_id" of relation
         "activity_clarifications" violates not-null constraint
rows before/after: 0 0 | unchanged: True
```

```text
1. Genuine harness incompatibility?  YES. The fixture INSERT omits adjudication_id; the 055
   migration (…_p8_fs_adjudication_lifecycle.sql, commit 3e11155, post-dating the harness
   commit df92c63) made the column NOT NULL with no default — confirmed from history and from
   the live column definition (id default gen_random_uuid(); adjudication_id no default).

2. Do the RLS policies/schema remain correct?  YES. RLS enabled; the four tenant policies are
   present and behave correctly (independent 16/16 behavioural matrix, §10.2); the
   one-current-version and version-identity constraints/indexes exist. The failure is a
   fixture bug, not a policy or schema defect.

3. Does it affect production behaviour?  NO. The production write path always supplies a
   non-NULL adjudication_id (repository `record()` → `_as_uuid(adjudication_id) or
   str(uuid.uuid4())`, verified at statement level), so the NOT NULL constraint is satisfied
   for real inserts. The defect is confined to the verification script.

4. Can an RLS conclusion be made without modifying the harness?  YES — demonstrated: an
   independent probe in the disposable database produced the full tenant matrix (§10.2) with
   isolated, self-cleaning fixtures. This verification therefore did not depend on the broken
   harness, and the harness itself was not repaired (out of scope).
```


## 14. FINDINGS

```text
F-064-1  HISTORY-READ ADDRESSING CONTRACT (functional; NON-BLOCKING)
  The `/history` parameter named `adjudication_id` is resolved by `get()`, which binds to the
  row `id` column. For every lineage created after 055 (id ≠ adjudication_id by construction),
  passing the value the `/effective` endpoint publishes as `adjudication_id` returns 404, while
  passing a version row id returns the full lineage. Impact: the history read is unusable in the
  natural/documented way; no data, tenant or factor-safety consequence. Remedy (a product/
  implementation decision, not taken here): resolve the seed by `adjudication_id`, or rename and
  document the parameter as a version/row id and align `/effective`'s output accordingly.
  Reproduction: §9.1. Not fixed here (verification only).

F-064-2  CONSUMPTION EXCEPTIONS INDISTINGUISHABLE FROM "NO ADJUDICATION" (robustness)
  `_consume_effective_adjudication` catches every exception, logs it and returns None, so a
  broken consumption path degrades into the ordinary clarification diversion. That direction is
  safe (no false success, no guessed factor — verified C10), but it is exactly what concealed
  the NameError defect until dedicated tests existed. Recommendation: give a consumption failure
  a durable, observable job-level signal instead of only a log line. Non-blocking.

F-063-2  FIXED in a509593 (independently confirmed): `MatchRequest` was unbound in the
  consumption path, so no persisted adjudication could ever be consumed. Reproduced on baseline
  code; demonstrated resolved on the target (§4.1).

F-063-1  PRE-EXISTING, confirmed, repaired nowhere — see §13.

F-051-1  PRE-EXISTING, separate: migration-count pin 71 vs the tree's 74; it is one of the six
  pre-existing failures and was not modified.
```

## 15. REMAINING GAPS / LIMITS OF THIS VERIFICATION

```text
- No live end-to-end run against a real database through the SERVICE path was performed (no DDL
  change is in scope); the F1 invariant was verified at the service/repository/HTTP seams with
  the real components and scripted persistence.
- The destructive `tests/integration` pytest tree was deliberately NOT run (its conftest
  TRUNCATEs the target); the table's RLS behaviour was verified by an independent,
  non-destructive probe instead.
- No UI/D19 consumption of the two reads exists to verify (out of scope by instruction).
- F-064-1 and F-064-2 are reported, not repaired.
- The repository was not modified: no commit, no push, no tracked-file change.
```

## 16. VERDICT

```text
VERDICT: PASS WITH FINDINGS — NO BLOCKING DEFECT FOUND
```

Justification: the primary end-to-end invariant is independently reproduced and holds —
authorized clarification → persisted, versioned, tenant-scoped adjudication → server-derived
evidence signature → later automatic processing → bounded effective lookup → compatibility
check → semantic clarification re-entered into the existing policy → factor or unresolved →
`selected_factor_id` never bypasses the policy → changed/missing evidence blocks silent reuse →
tenant/client isolation. Both new read endpoints are registered in the real composed
application and behave correctly for authentication, authorization, context bounding,
determinism, ordering and immutability.

The blocking criteria named in the brief — F-039-1 requirements, tenant isolation,
factor-selection safety, evidence compatibility, and the adjudication-consumption invariant —
are all satisfied on the evidence above. F-064-1 is a real functional/contract defect in the
new history read that must be corrected before a client consumes that endpoint, but it neither
leaks across tenants nor affects factor selection or consumption; F-064-2 is a robustness and
observability recommendation; F-063-1 and F-051-1 are pre-existing and unchanged.

This is verification only: no Product Owner closure is claimed, no independent acceptance of
the release is claimed, and no production artefact was touched.

