# P17 IMPLEMENT-08 — Scope 3 API & Persistence Completion

**Task ID:** `P17-IMPLEMENT-08-20260925-SCOPE3-API-PERSISTENCE-COMPLETION`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `c3996158c50702315a55e5d28a995b52723f2998` (verified actual HEAD before any change)
**Nature:** IMPLEMENTATION. No UI/marketing change, **no migration**, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-08-20260925-SCOPE3-API-PERSISTENCE-COMPLETION`

## 2. Starting SHA

`c3996158c50702315a55e5d28a995b52723f2998` — the IMPLEMENT-07 report commit, confirmed with
`git rev-parse HEAD` before any edit. All four prior P17-07 commits (`4505e6f`, `b68bf7b`,
`7739ed7`, `c399615`) verified present; tree clean apart from the pre-existing `.gitignore`
and unrelated untracked files (see §15).

## 3. Ending SHA

`PENDING` — recorded in the final commit for this report (§4).

## 4. Exact commit SHA(s)

| # | SHA | Message |
|---|---|---|
| 1 | *(this change)* | `feat(p17-08): persist Scope 3 estimation records and complete the API path` |
| 2 | *(this report)* | `docs(p17): record IMPLEMENT-08 report and the stale test-database finding` |

**Not pushed.** No amend/rebase/reset/force-push; all prior P17 history preserved.

## 5. Files created / modified

**Created**

| File | Purpose |
|---|---|
| `backend/data/estimation_records.py` | `EstimationRecordsRepository` — the single persistence path for estimation evidence |
| `backend/tests/unit/api/test_p17_08_scope3_api.py` | 50 tests: the endpoint path, all 15 categories, security, lifecycle, idempotency, estimation + supplier persistence |
| `backend/tests/integration/verify_p17_08_scope3_persistence_schema.py` | READ-ONLY probe certifying the real-PostgreSQL persistence target (§10) |
| `docs/architecture/CT-PO-P17-IMPLEMENT-08-SCOPE3-API-PERSISTENCE-COMPLETION-20250925.md` | This report |

**Modified**

| File | Change |
|---|---|
| `backend/api/dependencies.py` | Registered `estimation_records` on `RepositoryBundle` (default `None`) |
| `backend/api/v3_scope3.py` | Persists the estimation record after a successful calculation; response gained `estimation_record_id` |
| `backend/services/scope3_calculation.py` | Factor governance (factor must be `Scope 3` and match `reporting_year`) |

## 6. Database / API / frontend implications

**Database:** none. No migration was added or altered. `public.estimation_records` **already
existed** in `supabase/migrations/20261013000000_p17h_estimation_and_assumption_records.sql`,
linking to a calculation via `calculation_snapshot_id` with `ON DELETE CASCADE`. The
repository was written against that existing table — no schema change was required, and
none was made.

**API:** one additive response field (`estimation_record_id`) on the existing
`POST /api/v3/scope3/calculate`. No route added, removed or renamed. The route's own
lifecycle claim is unchanged (`CALCULATED`); it still does **not** mark anything `REPORTABLE`
(§9).

**Frontend:** none.

## 7. Tests

| Suite | Result |
|---|---|
| `tests/unit/api/test_p17_08_scope3_api.py` (new) | **50 passed** |
| All `tests/unit -k p17` | **430 passed**, 3338 deselected |
| `tests/unit/{domain,engines,services,api,data}` (wider regression) | **3382 passed, 8 skipped, 9 failed (all pre-existing — §12)** |

Regression on the earlier P17 work was re-run explicitly: **P17-05/06/07 = 155 passed**
(98 + 28 + 14 + 15), confirming IMPLEMENT-08 did not regress the IMPLEMENT-07 framework.

## 8. Runtime verification

Real `starlette.testclient.TestClient` against the live ASGI app with only repositories and
the acting-for authorizer faked. Verified end-to-end through the route:

* all **15** Scope 3 categories reach a persisted snapshot;
* the architecture statuses are reported **verbatim** — `2,10 NOT_IMPLEMENTED`;
  `11,14,15 DEFERRED`; `3,4,5,6 SUPPORTED`; `1,7,8,9,12,13 PARTIAL`;
* every invalid input (missing category, out-of-range category, missing required
  assumption, incompatible factor, wrong factor year) returns a **structured 4xx** with
  no snapshot written and no emissions number produced;
* a successful calculation persists the snapshot and then the estimation record.

A spinner was never used as evidence of processing; the persisted row is the authority
(AGENTS.md §19, §74).


## 9. Security verification

Ownership is **never** taken from the request body. The body's `organization_id` is treated
as a claim and reconciled against the resolved context; the persisted owner is the resolved
owner. Verified DENY and ALLOW cases:

| Case | Expectation | Result |
|---|---|---|
| Acting-for context fails authorization | `403`, nothing persisted | **PASS** |
| Payload names another tenant | persisted owner = **resolved** owner, never the claim | **PASS** |
| Consultant acting for its own firm | attribution stays distinct (`organization_id == performed_by == firm`) | **PASS** |
| Consultant acting for a delegated client | `acting_for == client`, `performed_by == firm`, never conflated | **PASS** |
| Factor the caller cannot see | `422`, no snapshot | **PASS** |
| Estimation record for a refused calculation | **not written** (no phantom evidence) | **PASS** |

Cross-tenant factor and cross-tenant supplier resolution are refused through the existing
repository-scoped lookups; no RLS was disabled and no service-role shortcut was introduced.

## 10. Real-PostgreSQL round-trip — **BLOCKED (F-046-1)**

The task required a real PostgreSQL round-trip proving snapshot + log + estimation record +
supplier attribution persist for all 15 identities. The persistence **target** was probed
read-only before any write, and the probe found it is **not migrated to P17**:

```
TARGET postgresql://***@127.0.0.1:54426/carbontally_test
CONNECTED database= carbontally_test
TABLE calculation_snapshots = present
TABLE emissions_logs = present
TABLE suppliers = present
TABLE estimation_records = MISSING
TABLE contractual_instruments = MISSING
TABLE instrument_allocations = MISSING
COL calculation_snapshots.scope3_category = MISSING   (and every other P17 dimension column)
COL calculation_snapshots.acting_for_organization_id = MISSING
COL emissions_logs.supplier_id = present              (P12-era column only)
FUNCTION p17_instrument_over_allocated = MISSING
```

The dedicated integration database `carbontally_test` (port 54426 — the target the F-046-1
guard **permits**) is at a **P12-era schema**. Its documented bootstrap is a `createdb` +
**restore from a dump**, not a migration run, and it has not been restored since the P17
work landed.

**Consequence:** a round-trip cannot be executed without first changing that database's
schema. The integration harness is also **destructive** — `conftest.py` performs
`TRUNCATE … RESTART IDENTITY CASCADE` — so no write was attempted.

**Decision (deliberate, not an oversight):**

> **BLOCKED — SAFE MUTATION NOT AVAILABLE (F-046-1).**

The four P17 migrations were **not** applied. Applying migrations to a database whose exact
migration level is unverified risks a partial apply and would leave the sanctioned test
database in a worse state than it was found — a direct violation of "preserve working
functionality" and of §55/§66. AGENTS.md §55.1 prescribes an explicit BLOCKED verdict for
exactly this situation, and that verdict is recorded here rather than being papered over.

This is a **material finding**, not a test failure: it means *no* Scope 2/3 integration
suite could have been passing against this database since P17 landed.

**Exact unblock action (for the next session):**

1. restore `carbontally_test` from a current dump, **or** apply the four P17 migrations
   (`2026101{0,1,2,3}000000_p17*.sql`) after confirming its exact level;
2. re-run the probe — every line above must read `present`;
3. then run the round-trip for ≥1 activity/factor category, ≥1 estimation category,
   ≥1 supplier-linked category and ≥1 boundary-controlled category, asserting all 15
   identities persist.

## 11. Verification matrix

| Item | Status |
|---|---|
| Unified 15-category framework preserved (one service, one endpoint, one persistence path) | **IMPLEMENTED** · **TESTED** |
| API path exercised with a real ASGI client | **IMPLEMENTED** · **TESTED** |
| `estimation_records` persistence + idempotency per calculation | **IMPLEMENTED** · **TESTED** |
| Supplier attribution on the canonical path | **VERIFIED** (pre-existing P12 column; no duplicate system built) |
| Factor governance (scope + reporting year) | **IMPLEMENTED** · **TESTED** |
| Security (ownership from context, not the body) | **IMPLEMENTED** · **TESTED** |
| Real-PostgreSQL round-trip | **BLOCKED** — F-046-1, safe mutation unavailable (§10) |
| No material regression | **VERIFIED** (§12) |

**IMPLEMENTED ≠ TESTED ≠ VERIFIED ≠ ACCEPTED.** No acceptance verdict is claimed.

## 12. Regression assessment — the 9 wider-suite failures are pre-existing

The 9 failures in `tests/unit/{domain,engines,services,api,data}` are **not** attributable to
IMPLEMENT-08. Verified by stashing this task's three source changes
(`git stash push -- backend/api/dependencies.py backend/api/v3_scope3.py
backend/services/scope3_calculation.py`): the failures **reproduce on the clean tree**, then
the changes were restored (`git stash pop`, working tree confirmed intact).

| Failing suite | Count | Assessment |
|---|---|---|
| `engines/test_extraction_suggestions.py` | 3 | Pre-existing; **observed failing with this task's changes stashed** |
| `api/test_review_sla_surfaces.py` | 3 | Pre-existing; route-registration assertions unrelated to Scope 3 |
| `data/test_d17_provider_ownership_migration_revision.py`, `data/test_i1_insight_migration.py`, `data/test_i2_insight_authorization_contracts.py` | 3 | Pre-existing by construction: they assert a migration "is the **latest** migration", which the earlier P17-01..07 migrations legitimately superseded. **IMPLEMENT-08 adds no migration**, so it cannot have caused these. |

These are **historical findings**, carried as regression targets only — not current
IMPLEMENT-08 defects.

## 13. F-046-1 restatement (carried forward as required)

> The integration harness's `pool` fixture executes
> `TRUNCATE … RESTART IDENTITY CASCADE` against whatever `INTEGRATION_DATABASE_URL` names.
> It must **NEVER** be pointed at a persistent, demo, QA or production environment. It must
> target a disposable clone (`ct_*`) or the dedicated `carbontally_test` database. The guard
> is enforced in code: `PROTECTED_PERSISTENT_MARKERS = ("qa","demo","investor","prod","live")`
> refuses such targets with an explicit F-046-1 error **before** any destructive statement
> runs. Before every integration suite, verify the target's identity and confirm whether
> setup is destructive.

This report's probe respected that invariant: it connected only to `carbontally_test`,
refused any other database name, and performed **no** write.

## 14. Read-projection decision (`scope3_category` / `data_quality`)

Deferred, and documented rather than half-done. Adding these to the canonical read
projection touches the shared analytics allow-list and its callers, which is outside the
smallest-correct-change boundary for this task; the persisted columns already exist on
`emissions_logs`, so the projection is a pure follow-on with no schema dependency.
**Left explicitly deferred** to avoid widening this change into the analytics layer.

## 15. Git state

Starting state verified before work: `HEAD = c3996158c50702315a55e5d28a995b52723f2998`,
branch `p8-release-reconciled`. No `reset --hard`, no `clean -fd`, no force-push, no rebase,
no history rewrite. Commits are additive and scoped to this task's files (§5). Unrelated
pre-existing untracked files (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-*.txt`,
`docs/ChatGPT/*`, older `docs/architecture/*`) were **left untouched and not committed**.

## 16. Secret hygiene

No secrets introduced. No credentials, keys, JWTs, signed URLs or connection strings were
committed or logged; the probe masks the URL (`://***@`) before printing.

## 17. Acceptance status / verdict

> **`P17_IMPLEMENTATION_PARTIAL`**

Everything IMPLEMENT-08 was written to fix is **implemented and tested**: the API path is
exercised end-to-end, `estimation_records` persistence works with real idempotency, supplier
attribution was verified as already owned by the canonical path (no duplicate system built),
all 15 category paths are valid, and no material regression was introduced. **430 P17 tests
pass**, including the new **50**.

The verdict is PARTIAL, not COMPLETE, for exactly **one** reason — the real-PostgreSQL
round-trip is **BLOCKED** by a stale, un-migrated dedicated test database, and AGENTS.md
§55.1 forbids forcing that through by mutating a database whose safety could not be
guaranteed (§10). No acceptance verdict is claimed: "tests pass" does not mean "investor
accepted" (AGENTS.md §73).

## 18. Remaining work

| # | Item | Owner | Evidence required |
|---|---|---|---|
| 1 | Restore/migrate `carbontally_test` to the P17 schema | infra | probe output all `present` |
| 2 | Real-PG round-trip for ≥1 activity/factor, ≥1 estimation, ≥1 supplier-linked and ≥1 boundary-controlled category; all 15 identities persist | implementation | committed integration test + captured DB rows |
| 3 | Read projection for `scope3_category` / `data_quality` (§14, deferred) | implementation | projection test |
| 4 | Repair the 3 migration-ordering assertions superseded by P17 (pre-existing) | implementation | updated "latest migration" contract |
| 5 | Repair `test_extraction_suggestions.py` (3) and `test_review_sla_surfaces.py` (3) | implementation | suite green |

## 19. Limitations and unknowns

* **Unverified:** persistence against a real PostgreSQL instance. All persistence evidence in
  this task is at the repository-contract and HTTP-layer level.
* **Not established:** whether any *other* environment holds a P17-correct schema. Only
  `carbontally_test` was probed; the main/demo databases were deliberately **not** contacted.
* **Not attempted:** applying the P17 migrations anywhere. Zero migrations were run.
* The wider suite contains 9 pre-existing failures (§12); they are reported, not fixed, to
  keep this change scoped to IMPLEMENT-08.

## 20. Evidence index

| Evidence | Location |
|---|---|
| New API suite (50 tests) | `backend/tests/unit/api/test_p17_08_scope3_api.py` |
| Read-only persistence-target probe | `backend/tests/integration/verify_p17_08_scope3_persistence_schema.py` |
| Estimation repository | `backend/data/estimation_records.py` |
| Existing table definition (unchanged) | `supabase/migrations/20261013000000_p17h_estimation_and_assumption_records.sql` |
| Stale-target probe output | §10 of this report |

## 21. Reporting-standard compliance and final principle

This report states task, scope, files changed, database/migration status (**none**), API
changes, frontend changes (**none**), tests with exact counts, runtime verification, security
verification (ALLOW **and** DENY), Git state, verdict and remaining limitations — per
AGENTS.md §84.

No false completion is claimed. Uploading or calculating is not processing completion; a
passing unit test is not acceptance (AGENTS.md §74). Where the required evidence could not be
obtained safely, the outcome is recorded as **BLOCKED with its precise cause and the exact
action needed to unblock it**, rather than converted into a misleading success state
(AGENTS.md §46, §85).

**INSPECT → VERIFY → IMPLEMENT → TEST → REPORT.**

