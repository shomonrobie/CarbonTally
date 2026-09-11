# CarbonTally WS4 / Gate 3 — Workstream 4A Report
## Item-Level Assignment Foundation (Database + RLS)

- **Date:** 3 September 2026
- **PO decision:** Option B approved (item-level processing assignment) per the WS4 Gate 3 Architecture Reconciliation.
- **Scope executed:** database + RLS foundation ONLY. No service/API/UI/workflow/notification code was changed. Gate 3 remains BLOCKED pending later workstreams.
- **Environment:** local stack (Supabase Postgres `127.0.0.1:54426`, PostgREST `127.0.0.1:54425`).
- **No commit/push was made.**

---

## 1. Implementation

### Files changed

| File | Change |
| --- | --- |
| `supabase/migrations/20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | **New migration** (forward-only, additive) |

### Schema decision

No new table and no new column were required. The existing D38 `work_item_assignments`
ledger is already the canonical item-level current assignment source (single-open
partial unique index, `assignee_kind internal_staff|processing_entity`, `previous_*`
history fields, `close_action` vocabulary). No second assignment table was created and
no assignment state was duplicated.

### Helper created

`public.work_item_effective_entity(p_item uuid) returns uuid` — `STABLE`,
`SECURITY DEFINER`, `SET search_path = public`. It returns the item's effective
**processing entity**:

1. open `work_item_assignments` row with `assignee_kind = processing_entity` → that
   `processing_entity_id` (item-level override wins);
2. open row with `assignee_kind = internal_staff` → `NULL` (internal overrides the
   batch default and is never PE-visible);
3. no open row → `manual_extraction_batches.entity_id` (batch default);
4. otherwise → `NULL` (unassigned).

`EXECUTE` was revoked from `PUBLIC` and granted to `authenticated` + `service_role`
(verified: `fn_exec_public=false`, `fn_exec_auth=true`, `fn_exec_svc=true`). Processing
origin columns are never read or written by the helper.

### RLS policy changed

`manual_extraction_items_entity_select` (replaced in place, same policy name):

- **Before (D22):** items visible to PE staff when `EXISTS (… b.entity_id IS NOT NULL
  AND is_entity_member(b.entity_id))` — i.e. inherited from the **batch**.
- **After:** items visible to PE staff when `work_item_effective_entity(id) IS NOT NULL
  AND is_entity_member(work_item_effective_entity(id))` — i.e. authorised per **item**
  by its effective assignment.

## 2. Data

| Metric | Pre-migration | Post-migration |
| --- | --- | --- |
| emission_factors | 7,049 | 7,049 |
| organizations | 975 | 975 |
| manual_extraction_items | 260 | 260 |
| manual_extraction_batches | 56 | 56 |
| work_item_assignments | 0 | 0 |
| conversations / messages / participants / notifications | 34 / 52 / 62 / 0 | unchanged |
| E2E users/profiles | 0 | 0 |
| schema_migrations | 45 | **46** (new migration recorded) |

No business/demo/investor row was inserted, updated or deleted. All test fixtures were
removed (fixture org count after run = 0; ledger total = 0).

## 3. Security — RLS ALLOW/DENY matrix (six required cases, executed through PostgREST)

Fixture: disposable org with six batch/item scenarios; test identities are the
established demo PE personas (`pe-staff-1.demo` → Alpha, `pe-manager-2.demo` → Beta).

| Case | Setup | Alpha | Beta | Result |
| --- | --- | --- | --- | --- |
| 1 | Batch default Alpha; item no override | ALLOW | DENY | PASS |
| 2 | Batch default Alpha; item open assignment Beta | DENY | ALLOW | PASS |
| 3 | Batch no default; item no assignment | DENY | DENY | PASS |
| 4 | Batch default Alpha; item open internal assignment | DENY | DENY | PASS |
| 5 | Batch default Alpha; item history = closed Alpha + open Beta | DENY | ALLOW | PASS |
| 6 | One batch default Alpha with A→(default)Alpha, B→Beta, C→(default)Alpha, D→Internal | sees A,C only | sees B only | PASS (no cross-PE enumeration) |

## 4. Regression

- RLS default single-party behaviour preserved (Case 1 ALLOW; batch entity policy
  unchanged; item policy only narrows access by effective assignment).
- Hermetic backend unit suites green after migration:
  - `tests/unit/domain/test_v1_2_dual_origin_workflow.py` — 5 passed;
  - `tests/unit/api/test_v3_entity_extraction.py` +
    `tests/unit/api/test_v3_processing_workflow.py` — 31 passed.
- No backend/API/UI code was touched in this workstream, so existing D38/D39/D40
  behaviour is unchanged by code; the migration is additive and preserves existing rows,
  constraints and indexes.

## 5. Risks / notes

- The new RLS predicate calls a per-row SQL function; it is correct for the current
  (small) PE-visible item volumes but should be revisited for performance if a PE
  workspace ever lists very large item sets directly through PostgREST.
- Service/API-level effective-assignment enforcement (PE `/pe` and Ops processing
  endpoints) is **not yet** switched to the item-level helper — that is the next
  bounded workstream (4B) and is required before the one-batch multi-party fixture can
  be exercised through the application.
- `work_item_effective_entity` treats a `status='open'` internal-staff assignment as an
  override of the batch default (per the approved decision). An ops service workstream
  must keep the D38 close/open semantics consistent with that rule.

## 6. Gate Status

**Gate 3 remains BLOCKED** pending the subsequent item-assignment service/API work and
the final Gate 3 execution. This workstream did not and cannot claim Gate 3 passed.

## 7. Git

No commit and no push were made. Working tree changes from this workstream: the single
new migration file above. Test/evidence scripts live under `/tmp` (not committed).

Evidence files: `/tmp/w4a_rls_test_out.txt`, `/tmp/w4a_rls_results.json`,
`/tmp/w4a_final_evidence_out.txt`, `/tmp/w4a_apply_out2.txt`, `/tmp/w4a_counts_out.txt`.


Additional verified properties:
- helper `work_item_effective_entity` returned the exact expected entity for all nine
  test items (Alpha/Beta/NULL incl. internal-override and history-override);
- D38 **single-open invariant** still enforced (duplicate open insert rejected);
- Alpha has zero visibility of Beta/internal/unassigned items and vice-versa;
- internal/customer/consultant paths are unaffected (no service code changed; items
  table remains deny-by-default for non-entity policies).


`manual_extraction_batches_entity_select` is **unchanged** (batch container default
view preserved). `manual_extraction_items` retains no other authenticated policy
(deny-by-default preserved). `work_item_assignments` remains RLS-on / no-policy /
API-only with no authenticated grants.
