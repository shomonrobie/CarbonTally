# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-051

```text
1  BASELINE SHA  df92c63e670ce03841fd4cc53482a13455bebdf1
2  FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH        p8-release-reconciled (no reset / rebase / force-push)
4  HEAD==origin  verified after push
5  GIT STATUS    clean at finish
6  COMMITS       the repository commit (see summary)
7  FILES CHANGED
     backend/data/activity_clarifications.py                              (new)
     backend/data/__init__.py                                             (export the new repository)
     backend/tests/unit/data/test_activity_clarifications_repository.py   (new, 8 tests)
8  PRODUCTION / DEPLOYMENT  production NOT touched · NOTHING applied to production · NOTHING DEPLOYED
9  D19 UI  NOT implemented — out of scope for this window by instruction
```

## PART A — REPOSITORY — IMPLEMENTED AND TESTED

The convention was traced before writing anything: repositories live in
**`backend/data/*.py`** (not `backend/repositories/`) and subclass
`AbstractRepository[T]` from `backend/data/base.py`, taking the service-role
`asyncpg.Pool` and using `_fetch_one` / `_fetch_all` / `_execute`. The new
`data/activity_clarifications.py` follows that, plus the explicit-column-list and
tenant-resolution conventions of `data/evidence_line_items.py`.

Operations implemented:
* `resolve_context(item_id)` — **server-side** tenant + parent keys from the
  extraction item (`manual_extraction_items.batch_id → manual_extraction_batches.organization_id`;
  the item has no `organization_id`), returning `None` for an unknown item so an
  orphan adjudication is never persisted;
* `record(...)` — persists one engine-produced `ClarificationRecord`
  (`ON CONFLICT ON CONSTRAINT activity_clarifications_unique DO NOTHING`);
* `apply_clarification(...)` — re-enters the **existing** policy
  (`engines.activity_clarification.resolve_clarification` → `select_factor`) and stores
  whatever it returns;
* `apply_decline(...)` — stores `unresolved_declined`, no factor, nothing to calculate;
* `get` / `get_adjudication` / `list_for_organization` — retrieval/provenance reads,
  each requiring `organization_id`;
* `delete(id, *, organization_id)` — tenant-scoped removal;
* `save(...)` — **refused** (`ValueError`): rows are produced by the engine, so the
  engine remains the only author;
* `decode_eligible_groups(row)` — JSONB decode for callers/tests.

Requirements honoured:
* **factor metadata comes only from the engine's record** — `record()` copies the
  factor fields from `ClarificationRecord` and accepts no factor argument;
* **`original_activity` is the extracted value and is never rewritten**; the user's
  statement is stored separately in `clarification`;
* `clarification_type`, `policy_input`, `outcome_status` are persisted from the record;
* `unit`/`scope`/`preferred_unit` are *policy inputs* (used by the policy), while the
  **stored** `unit`/`scope` come from the selected factor — so client-supplied
  metadata cannot become the recorded answer;
* **no factor-selection logic is duplicated** — `select_factor` is untouched and only
  invoked through the engine;
* unresolved/declined rows carry no selected factor (engine sets none, repository
  persists NULL).

**Tests — 8 passed, 0 failed** (`tests/unit/data/test_activity_clarifications_repository.py`),
executed in this window:
```text
test_decline_persists_no_factor_and_is_unresolved                PASS
test_insert_is_idempotent_and_returns_the_stored_row             PASS
test_organization_id_is_mandatory_for_a_write                    PASS
test_reads_and_deletes_are_tenant_scoped                         PASS
test_resolve_context_is_server_side_and_unknown_item_is_none     PASS
test_retrieval_uses_the_database_unique_key                      PASS
test_save_is_refused_so_the_engine_stays_the_only_author         PASS
test_no_authoring_method_accepts_factor_metadata                 PASS   (anti-bypass by construction)
```

## PARTS B — API — NOT IMPLEMENTED

The API half was **not** built in this window. It is the largest remaining slice
(router + dependency wiring + request/response schemas + its own tests) and the
window's budget was consumed by the repository, the FK/RLS follow-ups already
reported in 050, and the pre-existing failure analysed below. Nothing was
half-written: no router, no schema and no endpoint was added.

What was traced for the next window (so it is reuse, not invention):
`backend/api/dependencies.py` already provides `RepositoryBundle` + `get_repositories`
and the authorisation helper used by org-scoped business endpoints —
internal staff allowed, **entity staff denied**, org member via `ensure_org_access`,
otherwise consultant via `ensure_consultant_org_access` (active client grant) —
which is exactly the consultant/client parity required by Part J. The new
repository therefore needs only to be added to that bundle, and the routes must
take `actor_id` from `AuthUser` and `organization_id` from `resolve_context`.

Consequently the following have **no result to report**: API authentication and
authorisation behaviour, API-level anti-bypass, API-level idempotency, the semantic
end-to-end tests through HTTP, and Parts C/D/E/F as specified for the API surface.
They are deferred, not claimed.


## PRE-EXISTING FAILURE FOUND (must not be silenced) — F-051-1

Running the broader unit suites surfaced a **failing ratified test**:

```text
tests/unit/data/test_d17_provider_ownership_migration_revision.py
  ::TestRevisionScope::test_migration_ordering_is_unchanged
  assert len(names) == 71        -> actual 73
```

Attribution, verified rather than assumed:
* the test pins the **D17 revision's** migration set (`len(names) == 71`, ordering, no
  duplicates, D32 before D35) — a ratified structural guard;
* the tree now holds **73** migrations because the F-039-1 migrations
  (`20260928000000_p8_fs_activity_clarifications.sql`,
  `20260929000000_p8_fs_activity_clarifications_fks.sql`) were added by the **048 and
  050 windows**, both of which reported that broad suites were *not* re-run;
* `git status --porcelain` this window shows only the three `backend/` files in §7 —
  **this window changed no migration**, so the failure is demonstrably pre-existing at
  the baseline `df92c63`, not introduced here.

**I did not touch it.** Correcting it means editing a ratified test's pinned count
(from 71 to the new total), which this window forbids without authorisation. It is
recorded as F-051-1 requiring a PO/verification decision: either the pinned count is
ratified-bumped as migrations legitimately accumulate, or the guard is re-expressed
(e.g. counted relative to the release SHA) so future feature migrations do not
red-flag a D17-scope guard.

## PARTS H / I — SUITE RESULTS (exact, only what actually ran)

```text
tests/unit/data/test_activity_clarifications_repository.py   8 passed · 0 failed · 0 skipped · 0 errors
tests/unit/data + engines + services                         NOT COMPLETED in this window — the run exceeded
                                                             the window's time budget while the broadest unit
                                                             suite was still executing; the single failure
                                                             identified is F-051-1 above.
D-A / D-FS / 039 / 040 / 041 / 043 / 045 targeted re-run     NOT COMPLETED in this window
22 service-level regressions (Part H)                        NOT IMPLEMENTED
RLS regression harness (050)                                 not re-run; 050's 27/27 stands
```
No aggregate total is claimed, and no previous total is presented as if re-run.

## PART J — CONSULTANT CLIENT — NOT EXERCISED

No API exists yet, so the consultant/client parity behaviour has no result here. What is
established is the layer beneath it: the 050 RLS matrix proved authorised consultant
SELECT / denied DML, unauthorised consultant denial and consultant-client confinement;
and the repository enforces the tenant predicate on every statement. No
consultant-specific bypass and no consultant-specific factor-selection path was created.

## REMAINING BLOCKERS

```text
F-051-1  D17 migration-count guard failing (pre-existing; needs an authorised decision)
F-051-2  API surface: options · clarify · decline (router + dependencies + schemas + tests)
F-051-3  API/repository anti-bypass tests through the HTTP seam (Part C/E)
F-051-4  Semantic + idempotency tests through the API (Parts D/E/F at HTTP level)
F-051-5  The 22 service-level regression tests (Part H)
F-051-6  Full regression run to completion (Part I) with exact totals
F-051-7  Non-null positive FK reference exercise (carried from 050)
```

## VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

Delivered and tested this window: the repository persistence layer for activity
clarification — server-side tenant resolution, engine-only factor authorship, immutable
original evidence, ledger-style idempotency on the database's own unique key, declined
rows with no factor, and `save()` refused so no caller can author a row — with 8 focused
tests passing. Delivered previously and unchanged: the FKs and the 27/27 behavioural RLS
proof (050). Not delivered: the API surface and everything that depends on it (Parts B,
C, D, E, F, H at the HTTP level, and the full Part I run). One pre-existing ratified-test
failure (F-051-1) is reported with its verified cause rather than silenced, and was
deliberately left untouched because fixing it requires editing a ratified test.

No independent verification was performed and no PO closure is claimed.
