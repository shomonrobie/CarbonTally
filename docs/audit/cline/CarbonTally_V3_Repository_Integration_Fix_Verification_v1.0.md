# CarbonTally V3 — Repository Integration Fix Verification v1.0

**Status:** FIXES APPLIED — RUNTIME VERIFICATION PENDING IN WORKING POWERSHELL
**Date:** 2026-08-14

---

## 1. Baseline

`py -m pytest tests/integration/test_v3_repositories.py -q` against the local
PostgreSQL database produced **5 failures / 5 tests**, diagnosed in
`CarbonTally_V3_Repository_Integration_Diagnosis_v1.0.md`:

1. `test_processing_entities_repo_lifecycle` — `updated_by="sys"` written to
   `processing_entities.updated_by UUID` (invalid test fixture).
2. `test_customer_factors_repo_org_scope` — `_row_to_customer_factor` undefined
   (mapper accidentally omitted during the V3 migration).
3. `test_customer_factors_repo_no_hard_delete` — same missing mapper.
4. `test_issues_repo_scoped_queries` — `sla_breached_at` referenced but the V3M-5
   migration defines `sla_breached BOOLEAN` (backend inherited plan-doc naming).
5. `test_issues_repo_no_hard_delete` — same `sla_breached_at` mismatch.

## 2. Fixes Applied

| Fix | File | Exact change |
|---|---|---|
| 1. Missing mapper | `backend/data/customer_factors.py` | Added `_row_to_customer_factor(row)` (18 columns → `CustomerFactor`), mirroring `_row_to_factor` / `_row_to_entity` |
| 2. Issue domain alignment | `backend/domain/issue.py` | `sla_breached_at: Optional[datetime]` → `sla_breached: Optional[bool]` (field + docstring) |
| 3. Issue repository alignment | `backend/data/issues.py` | `sla_breached_at` → `sla_breached` in `_ISSUE_COLUMNS`, `_row_to_issue`, INSERT list, ON-CONFLICT SET, VALUES |
| 4. Issue API contract alignment | `backend/api/contracts.py` | `IssueOut.sla_breached_at` → `IssueOut.sla_breached: Optional[bool]`; `issue_out()` mapper updated |
| 5. Test fixtures | `backend/tests/integration/test_v3_repositories.py` | `updated_by="sys"`, `"admin"`, `"member"` → `updated_by=new_id()` (3 sites) |

## 3. Static Verification (post-edit, repo-wide)

- `_row_to_customer_factor`: **1 definition** (customer_factors.py:29) + **5 call
  sites** (get, get_org_factors, get_active_for_org, save, update_status).
- `sla_breached_at`: **0 references** in backend code (remaining hits are historical
  docs only).
- `updated_by="sys" / "admin" / "member"`: **0 references** in test code.
- Column/placeholder counts match the migrations: `customer_factors` INSERT 18 columns
  (V3M-3), `issues` INSERT 22 columns (V3M-5); `RETURNING` lists use the same mappers.

## 4. Runtime Verification

An attempt was made from the tool environment, but **pytest cannot be executed there**:
the tool shell has no usable Python launcher on PATH (`py` not found; `python` resolves
to the Windows Store stub) and command completion is unobservable. **No passing claim is
made here.**

Run in the working PowerShell:

```powershell
cd backend
py -m pytest tests/integration/test_v3_repositories.py -q
```

Record the actual result in this section once executed (expected: 6 passed, given the
static verification above — to be confirmed at runtime).

## 5. Scope Discipline

- No database column added or modified (V3M-5 `sla_breached BOOLEAN` untouched).
- No migration, RLS, Storage, or ADR change.
- No SLA logic, ADR-V3-004, Work Items, DPQ, `/process/*`, `/jobs/*`, or unrelated
  refactoring.
- Nothing committed or pushed.
