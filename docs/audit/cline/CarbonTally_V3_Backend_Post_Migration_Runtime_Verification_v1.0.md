---
Document Type: Runtime Verification Report
Project: CarbonTally
Architecture Decision: Backend V2.1 → V3 (post-migration)
Version: 1.0
Status: RUNTIME VERIFICATION BLOCKED
Created: 2026-08-14
Author: Cline
Related ADR: ADR-V3-001, ADR-V3-002, ADR-V3-009, ADR-V3-014
---

# CarbonTally V3 — Backend Post-Migration Runtime Verification v1.0

# RUNTIME VERIFICATION BLOCKED

Test execution was **not possible** in this session. The implementation
remains **statically reviewed only**. No claim of passing tests is made for
any suite.

---

## Runtime Verification Attempt 1

**Date:** 2026-08-14 · **Status:** FIX APPLIED — TEST RERUN PENDING

- **Command executed:** `cd backend && python -c "import data.issues; import data; import api.router"` then `python -m pytest tests/unit/domain tests/unit/engines tests/unit/api -q`.
  (Executed by the restored runtime environment that produced the failure
  report; **not executable from this authoring tool's shell**, which still
  cannot observe any command completion.)
- **Failure:** `SyntaxError: '(' was never closed` at `backend/data/issues.py:29`,
  surfaced through the import chain `api → api.router → api.admin_aliases →
  api.contracts → engines → ... → data → data.issues`.
- **Root cause:** In `data/issues.py::_row_to_issue`, the `return Issue(`
  constructor call (opened at line 29) was left **unclosed** — the closing `)`
  and the `created_by` / `updated_by` field mappings had been consumed during
  the chunked file-creation edit, so lines 50–51 were blank and the
  `class IssuesRepository` began before the constructor closed.
- **File changed:** `backend/data/issues.py` (single function,
  `_row_to_issue`).
- **Exact minimal fix:** restored the two consumed field mappings and closed
  the constructor, consistent with `domain/issue.py` (`created_by`,
  `updated_by` fields) and the V3M-5 column list already declared in
  `_ISSUE_COLUMNS`:

  ```python
          created_at=r.get("created_at"),
          updated_at=r.get("updated_at"),
          created_by=str(r["created_by"]) if r.get("created_by") else None,
          updated_by=str(r["updated_by"]) if r.get("updated_by") else None,
      )
  ```

- **Test result after fix:** **Not verified from this tool** — the shell here
  cannot execute processes, so the rerun must be performed in the restored
  runtime environment. Static verification: the constructor now opens and
  closes correctly, all `Issue` fields are mapped, and the remainder of the
  file (get / list_for_org / list_for_entity / list_open / save /
  update_status / delete) is syntactically coherent.
- **Next blocker, if any:** none known from the reported run beyond the
  rerun itself. If the rerun surfaces another failure, it must be reported
  separately under the same minimal-change discipline.


---

## Runtime Verification Attempt 2

**Date:** 2026-08-14 · **Status:** FIX APPLIED — TEST RERUN PENDING

- **Command executed:** `cd backend && python -c "import api.issues; print('IMPORT_OK')"` then `python -m pytest tests/unit/domain tests/unit/engines tests/unit/api -q`. (Executed by the restored runtime environment that produced the failure report; **not executable from this authoring tool's shell**, which still cannot observe any command completion.)
- **Failure:** `NameError: name 'entity_id' is not defined` at `backend/api/issues.py:178`, raised at module import / route-construction time.
- **Root cause:** `list_entity_issues` declared `current_user: AuthUser = Depends(require_entity_member(entity_id))`. The argument `require_entity_member(entity_id)` is evaluated **at route-definition time**, but `entity_id` is the route's path parameter — it exists only per-request, never in the module scope, so the factory call cannot be resolved at import time.
- **Established pattern (no new auth model):** the V3 backend consistently enforces value-scoped authorization **inside the handler** using the path/body value — `ensure_org_access(current_user, organization_id)` (`api/dependencies.py:116`), called at the top of handlers in `api/business.py`, `api/customer_factors.py`, and the org-scoped routes of `api/issues.py` itself.
- **File changed:** `backend/api/issues.py` — `list_entity_issues` only (route + handler).
- **Exact minimal fix:** switched the dependency to `Depends(get_current_user)` and invoked the existing `require_entity_member` factory **inside the handler** where `entity_id` is in scope, preserving the exact entity-scoped authorization (own-entity → allow, other-entity → 403, CarbonTally staff with `entity_id=None` → allow):

  ```python
  @router.get("/admin/entity/{entity_id}", response_model=IssueListOut)
  async def list_entity_issues(
      entity_id: str,
      current_user: AuthUser = Depends(get_current_user),
      repos: RepositoryBundle = Depends(get_repositories),
  ) -> IssueListOut:
      """List issues scoped to one processing entity (entity staff see their own
      entity only; CarbonTally internal staff see any)."""
      await require_entity_member(entity_id)(current_user)
      issues = await repos.issues.list_for_entity(entity_id)
      return IssueListOut(total=len(issues), issues=[issue_out(i) for i in issues])
  ```

  Both `get_current_user` and `require_entity_member` were already imported in the module; no import changes, no auth.py changes, no schema/RLS/ADR changes, no authorization weakening (verified against `tests/unit/api/test_v3_issues.py` expectations: `entity_id == "pe-1"` on `pe-1` → 200; `entity_id == "pe-2"` on `pe-1` → 403).
- **Test result after fix:** **Not verified from this tool** — the shell here cannot execute processes, so the rerun must be performed in the restored runtime environment. Static verification: route construction no longer evaluates the path parameter at import time, and the checker logic in `require_entity_member` satisfies both entity-scoped unit-test cases.
- **Next blocker, if any:** none known from the reported run beyond the rerun. If the rerun surfaces another failure, it must be reported separately under the same minimal-change discipline.

---

## 1. Environment Diagnosis

| Check | Result | Evidence |
|---|---|---|
| Shell / process execution | **UNAVAILABLE** | Every `run_commands` invocation — including trivial `echo hello` and `pwd > file` — never completes observably; the tool reports "Command completion could not be observed … terminal remains open". This is an environment-layer failure of the execution tool, not a code or test defect. |
| Python interpreter | **UNVERIFIABLE** | `python --version` could not be executed. |
| pytest availability | **UNVERIFIABLE** | `pytest --version` could not be executed. |
| Virtual environment | **UNVERIFIABLE** | No venv is committed (normal); existence of a local `backend/.venv` or `venv` cannot be confirmed without the shell. |
| Dependencies | **STATIC-ONLY** | `backend/requirements.txt` lists the runtime deps (fastapi, supabase, pydantic, …) but **not** `pytest` / `pytest-asyncio` / `asyncpg`; these are dev deps that must exist in the interpreter. `backend/pyproject.toml` requires `asyncio_mode = "auto"` (pytest-asyncio). |
| `.env` | Present | `backend/.env` holds **remote** Supabase credentials (`https://pvwiojoyaqywtydzcpbg.supabase.co`) but **no `DATABASE_URL`/`SUPABASE_DB_URL`** — repository pool connection would need env config. |
| Test database | **UNVERIFIABLE** | `tests/integration/conftest.py` defaults to the local Supabase stack `postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test` (overridable via `INTEGRATION_DATABASE_URL`); reachability cannot be confirmed without the shell. |
| pytest cache | Present (historical) | `backend/.pytest_cache/` exists — pytest ran in a past session; does not prove current availability. |

**Missing / blocking:** the ability to execute any process. Without it, the
Python interpreter, dependency state, and database connectivity are all
unverifiable, and no test can be run.

## 2. Tests Executed

**NONE.** All test execution steps (Phase 2 commands) could not be invoked.

## 3. Initial Failures

No test run was possible, therefore no observed initial failures. The
migration session's static review identified and already fixed: dataclass
field-ordering, O1 sink signatures, `MatchResult` validation, and RLS test
seeding. (See the Migration Report §7.)

## 4. Fixes Made (this session, static/implementation only)

1. **Customer-factor validation wired (Phase 4)** — `api/customer_factors.py`
   now invokes the existing `engines.validation.validate_customer_factor` on
   create and edit (the single validation implementation — no second one).
   This guards the update path where `dataclasses.replace` bypasses the domain
   `__post_init__` (e.g. a negative `co2e_multiplier` is rejected with 422).
2. **RLS behaviour tests added (Phase 5)** — new
   `tests/integration/test_v3_rls_behavior.py` exercises the V3M-3/V3M-5/V3M-6
   policies with a real `authenticated` role (emulated via `SET ROLE
   authenticated` + `request.jwt.claims`), covering org isolation,
   customer-factor isolation, issue org/entity storeys, processing-entity
   deny-by-default, and `is_entity_member` access. Session state is reset on
   exit so pooled connections never leak.
3. **Unit tests added for the validation wiring** — `test_v3_customer_factors.py`
   gained `test_create_factor_invalid_country_rejected` and
   `test_update_factor_negative_multiplier_rejected`.

## 5. Customer-Factor Validation Result

- Confirmed: `validate_customer_factor` existed but was not wired into the
  create/edit API paths.
- Wired into both `POST /api/v3/customer-factors` and
  `PUT /api/v3/customer-factors/{id}` (reject-on-error with HTTP 422).
- Added tests: invalid factor rejected (422), valid factor accepted (201),
  draft-only edit rule preserved (409 on active), approval rules preserved
  (approve → active), no-self-approval preserved (403).
- **Not executed:** the new tests cannot be run in this environment.

## 6. RLS Verification

- **Tests added** (not executed): `tests/integration/test_v3_rls_behavior.py`
  verifies organisation isolation, customer-factor isolation, issue
  org/entity storeys, processing-entity deny-by-default, and
  entity-membership access, all under the real `authenticated` role.
- **No RLS policy was weakened or bypassed.** No SQL/policy file was modified;
  the tests assert existing V3M-3/V3M-5/V3M-6 behaviour.

## 7. V2.1 Regression Result

- **Not executed.** The existing V2.1 unit/integration suites could not be
  run. Static review confirms: no existing test file was removed; two test
  sink signatures were updated to the extended O1 protocol
  (`tests/unit/engines/test_calculation.py`,
  `src/providers/seai/tests/test_defra_regression.py`), `fakes.py` was extended
  (not replaced), and `integration/conftest.py` added V3 tables to the
  truncate list only.

## 8. V3 Feature Verification

| Feature | Test file(s) added | Executed? |
|---|---|---|
| Processing Entity create/retrieve/auth | `tests/unit/api/test_v3_entities.py`, `tests/integration/test_v3_rls_behavior.py` | No |
| Customer Factors CRUD/approve/deactivate/precedence/snapshot | `tests/unit/api/test_v3_customer_factors.py`, `tests/unit/engines/test_customer_factor_integration.py` | No |
| Issues create/retrieve/status/triage/auth | `tests/unit/api/test_v3_issues.py`, `tests/integration/test_v3_rls_behavior.py` | No |
| Matching — existing behaviour + approved-customer precedence | `tests/unit/engines/test_customer_factor_integration.py` | No |
| Calculation — existing behaviour + customer provenance + snapshot persistence | `tests/unit/engines/test_customer_factor_integration.py` | No |
| Existing V2.1 routes/engines/calculations/extraction | existing suites (unchanged) | No |

All V3 feature tests are present but **not executed** (blocked environment).

## 9. Final Test Counts

**Not obtainable.** No suite was executed. Estimated (by file, unverified):
V2.1 unit suites (pre-existing) + 8 V3 test files added during migration +
1 RLS-behaviour file added this session + 2 validation-wiring tests.

## 10. Remaining Failures

Unknown — no run was possible. Items that can only be confirmed at runtime:

- Python/pytest import graph for the new modules (syntax, dataclass
  construction, import cycles).
- pytest-asyncio availability for `asyncio_mode = "auto"`.
- Local `carbontally_test` connectivity for the integration/RLS suites.
- Remote Supabase env-config for any run that hits repository pools.

## 11. Deferred Architecture Boundaries (not touched)

ADR-V3-004 (dpq producer/consumer), `/process/*`, `/jobs/*`, Work Items,
auto-assignment, SLA, assignment/reassignment, queue retirement, provider
plugin architecture — all remain out of scope; nothing was implemented for
them in this session, and no test depends on them.

## 12. Final Recommendation

1. **Restore the execution environment** — the shell/process layer must work
   (or the repository must be checked out in a normal terminal) before any
   runtime claim.
2. Run, in order:
   - `cd backend && python -m pytest tests/unit/domain tests/unit/engines tests/unit/api`
   - `python -m pytest tests/integration/test_v3_repositories.py`
   - `python -m pytest tests/integration/test_v3_rls_behavior.py`
   - the complete backend suite.
3. Fix only failures traceable to the V3 migration; do not redesign anything.
4. Then update this document with real counts and re-issue it.

---

## Runtime Verification Attempt 3 — Test Defects

**Date:** 2026-08-14 · **Status:** TEST-ONLY FIXES APPLIED — RUNTIME RERUN PENDING

No production code was changed in this attempt. Three defects were identified,
and all three are **test-only**, all in
`backend/tests/unit/engines/test_customer_factor_integration.py`:

1. **Incorrect import of `build_matching_pipeline`.** The test originally
   imported the builder from `engines.matching_stages`, which has never
   contained it. `build_matching_pipeline` is defined only in
   `engines/factor_matching.py` and is the established import path used by
   `api/dependencies.py` and every other consumer. The test import was
   corrected to `from engines.factor_matching import FactorMatchingEngine,
   build_matching_pipeline`. Production code was already correct; nothing in
   `engines/matching_stages.py` or `engines/factor_matching.py` was modified.

2. **Undefined `_make_matching_engine` helper.** All four D-cf-5 matching
   tests referenced a module-level helper that was never written (zero
   definitions repo-wide). The helper was added to the test file, mirroring
   the established production construction pattern from
   `api/dependencies.get_matching_engine`:

   ```python
   def _make_matching_engine(lookup) -> FactorMatchingEngine:
       return FactorMatchingEngine(
           _EmptyIndex(),
           build_matching_pipeline(MatchingPipelineConfig()),
           customer_factor_lookup=lookup,
       )
   ```

3. **`_RecordingSink` persistence behaviour.** `create()` and `save()`
   previously raised `AssertionError`, but `CalculationEngine.calculate()`
   legitimately calls them through `_persist_log` whenever `log_id is None`
   (as in `test_snapshot_records_customer_provenance`). The sink now records
   the log instead of raising, following the established `_MemorySink` pattern
   in `tests/unit/engines/test_calculation.py`.

**Production matching code confirmed unchanged:** `engines/matching_stages.py`,
`engines/factor_matching.py`, `domain/matching.py`, `engines/calculation.py`,
and `api/dependencies.py` were not modified. No new production API, pipeline,
database, migration, RLS, or ADR change was made.

**No test run was executed from the tool environment — runtime execution
remains pending.**

---

## Runtime Verification Attempt 4 — Two Unit-Suite Failures Fixed

**Date:** 2026-08-14 · **Status:** FIXES APPLIED — TARGETED/FULL RERUN PENDING
IN WORKING POWERSHELL

Baseline recorded from the executed unit-suite run:

```
503 passed
2 failed
1 warning

37.50 seconds
```

### Failure 1 — `tests/unit/domain/test_issue.py::TestIssue::test_status_transitions`

**Root cause.** The final assertion was semantically incorrect:

```python
assert all(
    target in ISSUE_STATUSES for target in ISSUE_TYPES
)
```

`ISSUE_TYPES` (`defect`, `exception`, `escalation`) and `ISSUE_STATUSES`
(`open`, `in_progress`, `on_hold`, `escalated`, `resolved`, `closed`) are two
**intentionally different vocabularies** — none of the three issue types is
ever a lifecycle status, so the assertion could never pass. The preceding
comment ("the allowed set stays within the vocabulary") shows the intended
invariant: transition targets must stay within the status vocabulary.

**Fix (test-only).** `backend/tests/unit/domain/test_issue.py` now imports
`_ISSUE_TRANSITIONS` and asserts the actual invariant — every target reachable
from the transition table is a member of `ISSUE_STATUSES`:

```python
assert all(
    target in ISSUE_STATUSES
    for targets in _ISSUE_TRANSITIONS.values()
    for target in targets
)
```

Production Issue behaviour unchanged: `can_transition_to()`,
`_ISSUE_TRANSITIONS`, `ISSUE_TYPES`, `ISSUE_STATUSES`, and
`Issue.__post_init__` are untouched.

### Failure 2 — `tests/unit/api/test_v3_customer_factors.py::TestV3CustomerFactors::test_update_factor_negative_multiplier_rejected`

**Root cause.** Expected HTTP 422; actual HTTP 500. Runtime traceback:

```
api/customer_factors.py:148   updated = replace(...)
  -> domain/customer_factor.py:90   ValueError: co2e_multiplier must be >= 0
```

`dataclasses.replace()` constructs the new object through the generated
`__init__`, which invokes `CustomerFactor.__post_init__`; the negative
multiplier therefore raised `ValueError` inside the handler (unhandled → 500)
before the wired `validate_customer_factor`/`_reject_invalid` path could
return the intended 422. (The test comment claiming `replace` bypasses
`__post_init__` was incorrect.)

**Fix (`backend/api/customer_factors.py`) — correct validation order.** The
update handler now validates the merged field values **before** constructing
the frozen domain object:

1. the merged update kwargs are computed once;
2. `_reject_invalid(_validation_candidate(existing, **merged))` rejects an
   invalid update with HTTP 422 — still the single existing
   `validate_customer_factor` implementation, no second validator;
3. `replace(existing, **merged)` constructs the real object only after the
   values are known-good.

`_validation_candidate(existing, **changes)` is a small private helper that
builds a validation-only `CustomerFactor` without running `__post_init__`
(`object.__new__` + `object.__setattr__` — the class is
`@dataclass(frozen=True, slots=True)`); it is only ever passed to the
validator.

Preserved unchanged: the domain invariant (`__post_init__` still enforces
`co2e_multiplier >= 0`), the single-validator design, draft-only edit rule
(409), 404, no-self-approval (403), approval/deactivation behaviour, and
error-severity-only 422 semantics (`ValidationReport.ok` is false only when a
blocking error-severity issue exists — warnings never block).

### Files changed

- `backend/tests/unit/domain/test_issue.py` — corrected the transition
  invariant assertion (test-only).
- `backend/api/customer_factors.py` — validation-before-construction in the
  update handler plus the `_validation_candidate` helper (production, minimal).

### Targeted test result

`py -m pytest tests/unit/domain/test_issue.py tests/unit/api/test_v3_customer_factors.py -q`
— to be executed from the working PowerShell (the tool shell cannot observe
command completion in this environment). **Not yet claimed green here.**

### Full unit-suite result

`py -m pytest tests/unit/domain tests/unit/engines tests/unit/api` — to be
executed from the working PowerShell. **Not yet claimed green here.**

### Remaining failures

Unknown until the reruns above execute. Next steps after a green unit suite:
`py -m pytest tests/integration/test_v3_repositories.py` and
`py -m pytest tests/integration/test_v3_rls_behavior.py`.

---

## Runtime Verification — Local Database Configuration

**Date:** 2026-08-14 · **Status:** CONFIGURATION CHANGED — RUNTIME RERUN PENDING

### Decision

For the current V3 verification phase the integration-test harness now uses the
**existing local Supabase PostgreSQL database** as the integration-test
database:

```
postgresql://postgres:postgres@127.0.0.1:54326/postgres
```

This is an **intentional, disposable local integration database**: the local
stack is fully rebuildable (`supabase db reset` replays the entire migration
chain; the DEFRA/SEAI factor baseline is re-imported via
`src.commands.import_defra` / `src.commands.import_seai`). No separate
`carbontally_test` database is created or used.

### Previous `carbontally_test` dependency

The harness previously defaulted to a dedicated sibling database
(`postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test`). That
database is not created by any repository mechanism — `supabase db reset`
manages only the primary `postgres` database — so the suite failed at session
setup with:

```
asyncpg.exceptions.InvalidCatalogNameError:
database "carbontally_test" does not exist
```

at `backend/tests/integration/conftest.py:72`.

### Configuration change

`backend/tests/integration/conftest.py` (test configuration only):

- `TEST_DB_URL` default changed from `.../carbontally_test` to
  `postgresql://postgres:postgres@127.0.0.1:54326/postgres`.
- Module docstring updated to document that the local database is intentionally
  the disposable integration-test database for this verification phase.
- No other change: fixture behaviour, the truncate list, and the
  `INTEGRATION_DATABASE_URL` override are unchanged.

### Cleanup behaviour — tables affected by integration-test cleanup

The session `pool` fixture executes `TRUNCATE ... RESTART IDENTITY CASCADE` on
the following **17 tables** inside the local database at session start, so every
assertion is deterministic:

```
emissions_logs, calculation_snapshots, factor_aliases, domain_events,
audit_trail, customer_documents, report_generation_queue, import_batches,
emission_factors, organization_metadata, assets, facilities,
organization_members, organizations, issues, customer_factors,
processing_entities
```

Note: `emission_factors` is truncated too, so after an integration run the
local database's factor baseline is cleared and must be re-imported (or the
database recreated via `supabase db reset` + the import commands) before
app-level factor work resumes. `_seed_system_member` additionally inserts the
service-role `organizations` / `users` / `organization_members` rows referenced
by repository NOT NULL actor columns.

### Remote Supabase is NOT used

The integration suite connects **only** to `127.0.0.1:54326` (the local stack).
The harness forces `os.environ["DATABASE_URL"]` to the local URL inside the
test process, so repository pools can never be redirected at the remote project
(`pvwiojoyaqywtydzcpbg.supabase.co`). The remote Supabase project is **not**
used by any integration test.

### Production/remote data safety statement

- **No production or remote data is affected.** Only the local, disposable
  database is truncated by the tests.
- Everything the tests touch in the local database is rebuildable from the
  migration chain + factor imports.
- No database, migration, RLS, Storage, or ADR file was changed; application
  code and repository implementations were not modified.

### Runtime status

Runs (`py -m pytest tests/integration/test_v3_repositories.py`,
`py -m pytest tests/integration/test_v3_rls_behavior.py`) are to be executed
from the working PowerShell — **not yet claimed green here.**

---

**Scope discipline:** no database, migration, RLS, Storage, or ADR changes.
No existing test was removed. Nothing was committed or pushed. Factor baseline
unchanged (DEFRA 7,029 · SEAI 20 · TOTAL 7,049).
