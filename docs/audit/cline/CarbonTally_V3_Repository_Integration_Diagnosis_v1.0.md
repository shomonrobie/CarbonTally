# CarbonTally V3 — Repository Integration Diagnosis v1.0

**Status:** DIAGNOSIS COMPLETE — NO CHANGES MADE
**Date:** 2026-08-14 · **Scope:** classify the 5 integration-test failures from the
real local PostgreSQL run (`py -m pytest tests/integration/test_v3_repositories.py`).
Read-only: no code, test, schema, migration, RLS, or database changes; nothing
committed or pushed.

---

## 1. Run Context

The integration suite now runs against the **existing local Supabase PostgreSQL
database** (`postgresql://postgres:postgres@127.0.0.1:54326/postgres` — see the
"Runtime Verification — Local Database Configuration" section of the Post-Migration
Runtime Verification doc). The session fixture truncates the 17 tables under test
before the run. Result: **5 failures / 5 tests**, all in
`backend/tests/integration/test_v3_repositories.py`.

---

## 2. Failure 1 — `test_processing_entities_repo_lifecycle`

### Symptom

```
repo.update_status(entity_id, "suspended", updated_by="sys")
# PostgreSQL rejects "sys": processing_entities.updated_by is UUID
```

### Chain

`data/processing_entities.py::update_status` (line 97) executes
`UPDATE public.processing_entities SET status = $2, updated_at = NOW(), updated_by = $3 …`
with `updated_by="sys"`. The V3M-1 migration
(`supabase/migrations/20260810000000_v3m1_processing_entities.sql`, line 55) declares
`updated_by UUID`. PostgreSQL therefore rejects the non-UUID literal.

### Analysis

- `domain/entity.py::ProcessingEntity.updated_by` is `Optional[str]` — a **UUID string**.
- The repository contract is: `updated_by` is a UUID string (or `None`). The API layer
  (`api/admin_entities.py`) always passes `current_user.user_id`, a UUID string.
- The migration (DB truth) declares `updated_by UUID` — the constraint is intentional.

**Conclusion: test fixture defect.** `"sys"` is an invalid actor value for a UUID
column. The repository/domain/migration are mutually consistent; the correct minimal
fix is for the test to pass a real UUID (e.g. `new_id()` from the conftest).

---

## 3. Failures 2 & 3 — `CustomerFactorsRepository.save()` → `_row_to_customer_factor` undefined

### Symptom

```
CustomerFactorsRepository.save() calls _row_to_customer_factor(row)
NameError: name '_row_to_customer_factor' is not defined
```

Affects `test_customer_factors_repo_org_scope` and
`test_customer_factors_repo_no_hard_delete`.

### Evidence

- `backend/data/customer_factors.py` references `_row_to_customer_factor` at **five
  call sites** (get, get_org_factors, get_active_for_org, save, update_status) — lines
  38, 47, 61, 113, 133.
- **Repo-wide search: zero definitions** of `_row_to_customer_factor` anywhere.
- Every sibling repository defines its own row mapper in the same module:
  `_row_to_entity` (`data/processing_entities.py`), `_row_to_issue` (`data/issues.py`),
  `_row_to_factor` (`data/emission_factors.py`), `_row_to_log`
  (`data/emissions_logs.py`), `_row_to_org`/`_row_to_member`/`_row_to_asset`
  (`data/organizations.py`), `_row_to_report`, `_row_to_document`, `_row_to_batch`,
  `_row_to_entry`, `_row_to_alias`.
- The domain (`domain/customer_factor.py`) and the V3M-3 table
  (`supabase/migrations/20260810020000_v3m3_customer_factors.sql` — `co2e_multiplier
  NUMERIC NOT NULL CHECK >= 0`, `metadata JSONB`, `created_by/updated_by UUID`, …)
  both exist and are consistent; only the row→domain mapper is missing.

**Conclusion: genuine production defect** — `_row_to_customer_factor` was accidentally
omitted during the V3 migration. Minimal fix: add it to `data/customer_factors.py`,
mirroring the established patterns (`co2e_multiplier=Decimal(str(r["co2e_multiplier"]))`
as in `_row_to_factor`; `metadata=loads_jsonb(r.get("metadata")) or {}` as in
`_row_to_entity`).

### Latent secondary issue (same test class)

`test_customer_factors_repo_org_scope` also calls
`repo.update_status(cf_id, "active", updated_by="admin")` — `"admin"` is a non-UUID
string for a UUID column. This is masked today by the mapper NameError but will fail
after the mapper is added (same test-fixture class as Failure 1).

---

## 4. Failures 4 & 5 — `column "sla_breached_at" of relation "issues" does not exist`

Affects `test_issues_repo_scoped_queries` and `test_issues_repo_no_hard_delete`.

### Trace

**Issue domain** (`domain/issue.py`) — `sla_deadline`, `sla_breached_at`, `reopened_at`,
`assignee_id`, `escalation_level`, … (docstring: "mirroring the V3M-5 ``issues`` table").

**Issue repository** (`data/issues.py`) —
`_ISSUE_COLUMNS` selects `…, sla_deadline, sla_breached_at, reopened_at, …`; the INSERT
and ON-CONFLICT lists include `sla_breached_at`; `_row_to_issue` maps
`sla_breached_at=r.get("sla_breached_at")`.

**Issues table (actual V3M-5 migration** —
`supabase/migrations/20260810040000_v3m5_issues.sql`, CREATE TABLE lines 48–98):

```
owner_id UUID, assignee_id UUID,
sla_deadline TIMESTAMPTZ,
sla_breached BOOLEAN DEFAULT FALSE,      -- boolean, reuse existing vocabulary
escalation_level INTEGER NOT NULL DEFAULT 0 CHECK (escalation_level >= 0),
escalated_at TIMESTAMPTZ,
resolution_notes TEXT, resolved_at TIMESTAMPTZ, closed_at TIMESTAMPTZ,
reopened_at TIMESTAMPTZ, metadata JSONB,
created_by UUID, created_at, updated_by UUID, updated_at
```

The migration's header says: *"SLA / escalation (reuse existing vocabulary)."* The
boolean `sla_breached` deliberately mirrors the legacy `manual_review_queue.sla_breached`
convention. **No migration in the repository defines `sla_breached_at`.**

**All V3 issue migrations reviewed:** V3M-1 (processing_entities), V3M-2
(entity relationships), V3M-5 (issues), V3M-6 (entity RLS). None create
`sla_breached_at`.

**ADR-V3-009** (Architectural Decisions Register §ADR-V3-009, DECIDED, Option B):
conceptual only — it lists "SLA" among issue attributes but explicitly states
*"This register does not invent final database columns or enums."*

**ADR-V3-006** (SLA/Priority/Escalation/Capacity — PROVISIONALLY DECIDED): *"Reuse
existing … sla_* … No duplicate systems."*

**Source of the mismatch:** `docs/cline/CarbonTally_Backend_V3_Migration_Plan_v1.0.md`
§8.1 described the issues table with *"SLA timestamps (`sla_deadline`/`sla_breached_at`)"*.
The **actual migration deviated** from that description by using `sla_breached BOOLEAN`.
The backend Issue domain/repository/contracts were written against the **plan doc**, not
the **migration** — i.e. the repository accidentally inherited a field from the
descriptive plan, while the implemented (and migration-inventory-deferred) SLA surface
uses the boolean.

### A–G answers

- **A. Is `sla_breached_at` part of the V3 Issue model?** **No** — not in the
  implemented model. The DB truth (V3M-5) is `sla_breached BOOLEAN`. ADR-V3-009 is
  conceptual and explicitly does not fix final columns.
- **B. Is it defined in any migration?** **No.** Only `sla_deadline TIMESTAMPTZ` and
  `sla_breached BOOLEAN DEFAULT FALSE` exist.
- **C. Was it intentionally deferred?** The SLA *system* (definitions, computation,
  breach detection) is deferred — migration inventory: *"NOT BUILT (deferred): dpq
  producer/consumer, /process//jobs, WorkItem service, auto-assignment, SLA."* The
  migration kept only minimal passthrough columns reusing existing vocabulary.
- **D. Did the repository inherit future/deferred fields?** **Yes.** `sla_breached_at`
  came from the migration-plan doc's descriptive column list, not from the migration.
- **E. Is the test testing something V3 does not promise?** **No.** The tests exercise
  generic CRUD, lifecycle transitions, scoped queries, and no-hard-delete — all promised
  by ADR-V3-009 / V3M-5. They surface the repo↔schema mismatch, nothing more.
- **F. Remove the SLA field or add the column?** **Remove/rename in the backend.** Align
  `sla_breached_at` to the table's `sla_breached` (boolean) in `domain/issue.py`,
  `data/issues.py`, and `api/contracts.py`. Do **not** add the column to the database —
  the migration deliberately omitted it, and "no schema changes" applies.
- **G. Is there an existing ADR/decision that resolves this?** Yes — ADR-V3-009
  (DECIDED, conceptual), ADR-V3-006 (PROVISIONALLY DECIDED — reuse existing `sla_*`
  vocabulary), and the V3M-5 migration itself. All resolve to `sla_breached BOOLEAN`.

### Latent secondary issue

`test_issues_repo_scoped_queries` calls `repo.update_status(issue_id, "resolved",
updated_by="member")` — `"member"` is a non-UUID string for `issues.updated_by UUID`
(same test-fixture class as Failure 1; masked until the column mismatch is fixed).

---

## 5. Classification Table

| # | Failure | Root cause | Production defect? | Test defect? | Schema defect? | ADR conflict? | Recommended minimal fix |
|---|---|---|---|---|---|---|---|
| 1 | `test_processing_entities_repo_lifecycle` | `updated_by="sys"` written to `processing_entities.updated_by UUID` (V3M-1) | **No** — repo/domain/API contract correct (API passes UUID `user_id`) | **Yes** — invalid fixture; must be a UUID | No | No | Test: use a UUID (e.g. `new_id()`) |
| 2 | `test_customer_factors_repo_org_scope` | `_row_to_customer_factor` undefined → `save()` raises NameError | **Yes** — mapper accidentally omitted in `data/customer_factors.py` | Yes (latent): `updated_by="admin"` → UUID error after mapper fix | No | No | Add `_row_to_customer_factor` mapper; then test uses a UUID |
| 3 | `test_customer_factors_repo_no_hard_delete` | same missing mapper | **Yes** (same) | No | No | No | Same mapper fix |
| 4 | `test_issues_repo_scoped_queries` | `sla_breached_at` referenced; V3M-5 table defines `sla_breached BOOLEAN` | **Yes** — domain/repo/contracts inherited plan-doc naming, not the migration | Yes (latent): `updated_by="member"` → UUID error after alignment | No — migration internally consistent | No | Backend alignment: `sla_breached_at` → `sla_breached` (bool) in domain/repo/contracts; no SLA logic |
| 5 | `test_issues_repo_no_hard_delete` | same `sla_breached_at` mismatch | **Yes** (same) | No | No | No | Same alignment fix |

---

## 6. Recommended Fix Order

1. **`backend/data/customer_factors.py`** — add `_row_to_customer_factor(row)`,
   mirroring `_row_to_factor` / `_row_to_entity` (`Decimal(str(r["co2e_multiplier"]))`,
   `loads_jsonb(r.get("metadata")) or {}`, str/UUID coercion). Unblocks #2 and #3.
2. **Issue backend alignment** — replace `sla_breached_at` with the migration's actual
   `sla_breached: Optional[bool]` field in `domain/issue.py`, `data/issues.py`
   (`_ISSUE_COLUMNS`, `_row_to_issue`, INSERT and ON-CONFLICT column lists), and
   `api/contracts.py` (`IssueOut` + `issue_out`). Unblocks #4 and #5. No migration, DB,
   or RLS change; passthrough mirror only — **no SLA logic is implemented**.
3. **`backend/tests/integration/test_v3_repositories.py`** — replace the three
   non-UUID `updated_by` literals (`"sys"`, `"admin"`, `"member"`) with UUIDs (e.g.
   `new_id()`). Fixes #1 and the two latent UUID failures that steps 1–2 expose in #2/#4.
4. **Verify** — rerun `py -m pytest tests/integration/test_v3_repositories.py`, then
   `py -m pytest tests/integration/test_v3_rls_behavior.py`.

---

## 7. Deferred-Architecture Check

None of the recommended fixes require ADR-V3-004 (DPQ producer/consumer), Work Items,
`/process/*`, `/jobs/*`, SLA computation, auto-assignment, or assignment architecture.
They are exactly:

- one omitted row→domain mapper (`_row_to_customer_factor`),
- one backend column-name alignment to the **already-implemented** V3M-5 migration
  (`sla_breached_at` → `sla_breached` boolean),
- three test-fixture UUID corrections.

No database, migration, RLS, ADR, or application-behaviour change is implied or needed.

---

## 8. Scope Statement

This document is diagnosis only. **Nothing was changed:** no code, no tests, no schema,
no migrations, no RLS, no database, no commit, no push. Git history was reviewed where
available (prior audits record 8 commits on `main`, with the V3 backend and migrations as
uncommitted working-tree additions); the plan-doc-vs-migration mismatch is established by
cross-referencing the migration-plan description against the actual V3M-5 SQL and the
backend code.

---

## 9. Implementation Addendum — Confirmed Fixes Applied (2026-08-14)

**Status:** fixes implemented per §6; runtime verification pending in the working
PowerShell (the tool shell cannot observe command completion and has no usable Python
launcher on its PATH).

### Files changed

1. **`backend/data/customer_factors.py`** — added `_row_to_customer_factor(row)` (lines
   29–51), mirroring `_row_to_factor` / `_row_to_entity` (`Decimal(str(...))` multiplier,
   `loads_jsonb` metadata, str/UUID coercion). Resolves Failures 2 & 3.
2. **`backend/domain/issue.py`** — `sla_breached_at: Optional[datetime]` →
   `sla_breached: Optional[bool]` (field + docstring). Aligns the domain with the
   implemented V3M-5 schema.
3. **`backend/data/issues.py`** — `sla_breached_at` → `sla_breached` in `_ISSUE_COLUMNS`,
   `_row_to_issue`, INSERT list, ON-CONFLICT SET, and VALUES. Resolves Failures 4 & 5.
4. **`backend/api/contracts.py`** — `IssueOut.sla_breached_at` →
   `IssueOut.sla_breached: Optional[bool]` and the `issue_out()` mapper.
5. **`backend/tests/integration/test_v3_repositories.py`** — `updated_by` fixture
   values `"sys"`, `"admin"`, `"member"` → `new_id()`. Resolves Failure 1 and the two
   latent UUID failures exposed by fixes 1–2.

### Confirmed no-op scope

- No database column added or modified (V3M-5 `sla_breached BOOLEAN` unchanged).
- No migration, RLS, ADR, or repository-interface change.
- No SLA logic, ADR-V3-004, Work Items, DPQ, or `/process/*` / `/jobs/*` work.

### Runtime status

`py -m pytest tests/integration/test_v3_repositories.py -q` — to be executed from the
working PowerShell; see `CarbonTally_V3_Repository_Integration_Fix_Verification_v1.0.md`.




