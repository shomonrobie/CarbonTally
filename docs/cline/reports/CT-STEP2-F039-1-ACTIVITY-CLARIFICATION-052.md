# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-052

```text
1  BASELINE SHA  bd966917409d6b641a069f0c03adbb26fdcde7ff
2  FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH        p8-release-reconciled (no reset / rebase / force-push)
4  HEAD==origin  verified after push
5  GIT STATUS    clean at finish
6  COMMITS       the API commit (see summary)
7  FILES CHANGED
     backend/api/v3_activity_clarifications.py                            (new — router + schemas)
     backend/api/dependencies.py                                          (bundle wiring + import)
     backend/api/router.py                                                (registration)
     backend/tests/unit/api/fakes.py                                      (fake bundle gains clarifications)
     backend/tests/unit/api/test_v3_activity_clarifications_api.py         (new — 18 HTTP tests)
8  PRODUCTION / DEPLOYMENT  production NOT touched · NOTHING applied to production · NOTHING DEPLOYED
9  D19 UI  NOT implemented — out of scope for this window
```

## 8 — ROUTES IMPLEMENTED (registered in the real app router)

```text
GET  /api/v3/activity-clarifications/options        → ClarificationStateOut
POST /api/v3/activity-clarifications/clarifications → ClarificationResultOut  (201)
POST /api/v3/activity-clarifications/decline        → ClarificationResultOut  (201)
```
Verified in-process against the real composition root:
`from api.router import router` → the three paths are present alongside the existing
routes. Naming follows the established `v3_*` prefix/tag convention
(`prefix="/api/v3/activity-clarifications"`, `tags=["V3 — Activity Clarification"]`).

## 9 — REQUEST / RESPONSE SCHEMAS (Part C)

`ClarificationSubmitIn` accepts **meaning only**: `organization_id`, `activity`,
`clarification`, `activity_key`, and the policy *inputs* `unit`, `scope`, `country`,
`reporting_year`. `ClarificationDeclineIn` accepts `organization_id`, `activity`,
`activity_key`. Both declare `model_config = ConfigDict(extra="forbid")`, so
`selected_factor_id`, `selected_factor_name`, `factor_set`, `factor_source`,
`outcome_status`, `actor_id` — and any other extra key — are **rejected with 422**
rather than silently accepted (Part C's "reject them", chosen over "ignore" because it
is unambiguous and testable).

`ClarificationStateOut` carries the verdict/reason/policy-status and **semantic**
options only (`id` is the engine's semantic key, never an emission-factor id).
`ClarificationResultOut` reports the server-generated state, including the policy's own
factor metadata when it selected one, and `resolved` is true only when a factor was
actually selected.

## 10–14 — AUTHORIZATION · ANTI-BYPASS · SEMANTIC · PROVENANCE · IDEMPOTENCY (executed)

The HTTP suite drives the **real router** over the **real** authorization path
(`ensure_processing_org_access`) with the **real** clarification engine. Only the
transport dependencies are substituted (`get_current_user`, `get_repositories`,
`get_matching_engine`) via FastAPI's standard `dependency_overrides`; **no
authorization function is mocked**, so the denials below are genuine code-path outcomes.

```text
AUTHENTICATION / AUTHORIZATION
  GET/POST unauthenticated → 401 (all three endpoints), nothing persisted        PASS
  member ORG_A → ORG_B : GET 403 · POST clarify 403 · POST decline 403            PASS
AUTH CONTEXT TRUST
  POST decline stores actor_id = the authenticated AuthUser.user_id
  and actor_scope = "organization_member" (server-derived)                        PASS
ANTI-BYPASS (extra="forbid" → 422, and nothing reached persistence)
  selected_factor_id · selected_factor_name · factor_set · factor_source ·
  outcome_status · actor_id submitted on /clarifications                          PASS x6
  outcome_status · unit · selected_factor_id submitted on /decline                PASS x3
DECLINE SEMANTICS + PROVENANCE
  outcome_status = unresolved_declined · selected_factor_id NULL · resolved False PASS
  SQL params: [3]=organization_id (authorised context) · [4]="Waste" (original
  evidence) · [6]="i_dont_know" (user statement) — evidence and adjudication are
  stored as distinct values and the original is never overwritten                 PASS
IDEMPOTENCY / RETRY
  retry hits ON CONFLICT ON CONSTRAINT activity_clarifications_unique DO NOTHING,
  then re-reads the stored row (no second row, no overwrite)                      PASS
  the same decline submitted twice returns identical state                        PASS
OPTIONS
  verdict/policy status returned; options never invented ([] when none);
  no emission-factor id offered as the user's choice                              PASS
NO GUESSING
  /clarifications against a non-ambiguous context → 409 with zero DB interaction   PASS
```

## 15 — REPOSITORY INTEGRATION

The endpoints call `repos.clarifications.apply_clarification` / `apply_decline`; the
repository is now wired into `RepositoryBundle`
(`clarifications: ActivityClarificationsRepository`, constructed over the service-role
pool), and its field was added to the API test fake so the pre-existing API suite keeps
constructing the bundle. The repository's own suite still passes (8/8) after the wiring.

## 16–17 — SUITES ACTUALLY RUN, WITH EXACT TOTALS

```text
tests/unit/api/test_v3_activity_clarifications_api.py    14 collected · 14 passed · 0 failed · 0 skipped · 0 errors
                                                         (9 test functions, one parametrised over 6 anti-bypass cases;
                                                          pytest exit code 0)
tests/unit/data/test_activity_clarifications_repository.py   8 passed · 0 failed · 0 skipped · 0 errors
in-process route registration check                      PASS — 3/3 clarification routes present
D-A / D-FS / 039 / 040 / 041 / 043 / 045                 NOT re-run in this window (no policy file touched)
22 service-level regressions (Part H of 051)             NOT IMPLEMENTED — unchanged by this window
RLS behavioural harness (050)                            not re-run; 050's 27/27 stands
```
No aggregate total is claimed and no previously recorded total is presented as re-run.
This window modified **no** factor-selection, D-A, D-FS, 039, 041, 043 or 045 file, and
did not touch the 045 mapping-boundary gate.


A deliberate design point: `unit`/`scope`/`country`/`reporting_year` are *policy inputs*
used for candidate lookup — they are accepted, but the factor metadata **recorded** is
always the server-selected factor's own, so a request value can never become the stored
answer.

## 18 — KNOWN D17 TEST ISSUE (F-051-1) — unchanged, still untouched

`tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`
still expects 71 migrations while the tree holds 73 (the two F-039-1 migrations). This
window added **no** migration, so the issue is unrelated to this work and was **not**
modified, per instruction. It remains F-051-1 and still needs an authorised decision.

## 19–21 — STATUS, LIMITATIONS, BLOCKERS

* **D19 UI:** NOT implemented (out of scope for this window).
* **Production / deployment:** production NOT touched; nothing applied to production;
  **nothing deployed**; no RLS weakened; no parallel authorization system created; no
  factor-selection logic duplicated; `select_factor` untouched.
* **Deliberately not exercised in this window** (stated, not implied covered):
  * the consultant path over HTTP (authorised consultant allowed / unauthorised denied)
    — it flows through the same `ensure_processing_org_access` branch that 050's RLS
    matrix and the existing API suite already cover, but a dedicated HTTP test needs the
    consultant repository doubles → **F-052-1**;
  * a *positive* semantic adjudication over HTTP (Waste + Landfill, Waste + Waste oils
    resolving through the policy) — the stub engine returned no candidates, so the
    ambiguity branch could not be produced without real candidate fixtures → **F-052-2**
    (the engine semantics themselves remain covered by 041/043/045);
  * conflicting clarification after an existing adjudication at the API seam → **F-052-3**;
  * the 22 service-level regressions → **F-052-4**.

```text
F-052-1  consultant / consultant-client HTTP authorization tests
F-052-2  positive semantic clarification over HTTP (Waste + Landfill / Waste oils)
F-052-3  conflicting clarification after an existing adjudication (API level)
F-052-4  the 22 service-level regression tests (carried from 051)
F-051-1  D17 migration-count guard (needs an authorised decision)
```

## VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

The API layer now exists and is tested. Three routes are registered on the real app
composition root; the request contracts accept *meaning only* and **reject** forged factor
metadata and forged actors with 422; authorization is the existing
`ensure_processing_org_access` gate (unauthenticated 401, cross-tenant 403, actor and
scope server-derived); declines persist `unresolved_declined` with a NULL factor while
preserving the original extracted evidence alongside the user's statement; retries are
idempotent through the database's own unique constraint; and the endpoint refuses to
adjudicate when the engine has not asked, with zero database interaction. Remaining: the
four deferred test areas and F-051-1. No independent verification is claimed and no PO
closure is claimed.

