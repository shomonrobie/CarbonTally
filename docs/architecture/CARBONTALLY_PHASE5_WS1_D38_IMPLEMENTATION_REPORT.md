# CarbonTally Phase 5 — WS1 / D38 Implementation Report

- **Status:** WS1 — D38 IMPLEMENTATION COMPLETE AND VERIFIED.
- **Scope:** D38 Assignment / Reassignment / Attribution only. No D39, D40,
  WS4 UI or Phase-6 work performed.
- **Date:** 2 September 2026
- **Governing docs:** V1.2 blueprint (frozen), approved Phase 5 plan,
  ADR-V3-005, N1/PE-MSG-001, WS0 baseline notes.

## 1. WS1 status
IMPLEMENTED and VERIFIED (positive, negative, provenance, audit, concurrency,
idempotency, data-integrity and regression gates all green).

## 2. Baseline (before migration)
`emission_factors=7049`, `migrations=42`, `organizations=975`,
`manual_extraction_items=260`, `batches=56`, `conversations=34`,
`notifications=0`. No data modified before implementation.

## 3. Existing assignment architecture (CURRENT FACT)
- Batch assignment carrier: `manual_extraction_batches.entity_id` (D22),
  recorded through V3 `audit_trail` (`/api/v3/ops/batches/{id}/assign`).
- Immutable V1.2 provenance: item `processing_origin` /
  `processing_entity_id` (never rewritten).
- Legacy/staff-centric attribution: `review_assignment_history`
  (review-based); dormant `processing_assignments` / `reassignment_history` /
  `staff_workload` untouched (ADR-V3-016 retirement deferred).
- No per-item current-assignment ledger existed for V3.

## 4. WorkItem architecture implemented
Canonical work item = existing `manual_extraction_items` (NO competing
persistence model). Assignment attribution = new append-only
`work_item_assignments` ledger + a canonical V3 service
(`backend/services/work_items.py`) exposed through BOTH canonical access
contracts (`/api/v3/ops/items/{id}/work/*` internal Operations and
`/api/v3/pe/items/{id}/work/*` Processing Entity) so identical semantics apply
regardless of workspace.

## 5. Assignment semantics
- One open assignment per item (partial unique index
  `(manual_extraction_item_id) WHERE status='open'`).
- Internal domain: `claim` (to self), `assign` (to an internal staff member —
  validated active CarbonTally-internal staff only). PE-assigned batches are
  denied to internal staff (403).
- PE domain: `claim` (own ACTIVE entity only, capability `process`).
  Same-entity re-claim is idempotent (no duplicate row).

## 6. Reassignment semantics
- `reassign` (internal): closes the previous open row
  (`close_action='reassigned'`) and opens to the new internal staff member in
  one atomic statement; `previous_assigned_to` is preserved on the new row.
- PE reassignment of individual items is NOT authorized (403 route absence +
  service denial for other-entity open claims); PE batch reassignment remains
  the existing D22 batch-level operation.
- Immutable V1.2 provenance is never touched.

## 7. Partial-work recovery
- `recover` (internal): closes any stale open assignment
  (`close_action='recovered'`) and reopens for the target internal staff.
- Concurrency: DB partial-unique-index + single-statement CTE guarantee at
  most one owner; duplicate/concurrent claims resolve to a single open row
  (verified: simultaneous claims → one 200, one 409).

## 8. Authorization matrix (server-side)
| Operation | Internal staff | PE member | Customer/Consultant |
|---|---|---|---|
| ops claim/assign/reassign/recover/release/complete | can_process OR can_review + internal (entity NULL); PE-batch items 403 | denied | 403 (require_staff) |
| PE claim/release/complete | denied (require PE member) | own active entity + capability `process` | 403 |
| work read (ops) | can_view_all/can_process/can_review | own entity via /pe (CAP_READ_WORK) | 403 |

## 9. PE isolation
PE A cannot read/claim/reassign/complete PE B items (verified 403). PE
members cannot operate internal-origin items via /pe (403). Internal staff
cannot operate PE-assigned items via /ops (403).

## 10. Internal authorization
Only active CarbonTally-internal staff (staff_profiles entity NULL) with
`can_process`/`can_review` may mutate; assign/reassign/recover targets are
validated as active internal staff (non-staff target → 422). No user_type,
URL, entity or org parameter is ever trusted.

## 11. API changes
- `POST /api/v3/ops/items/{id}/work/claim|assign|reassign|recover|release|complete`
- `GET /api/v3/ops/items/{id}/work`
- `POST /api/v3/pe/items/{id}/work/claim|release|complete`
- `GET /api/v3/pe/items/{id}/work`
All canonical V3; no parallel legacy API.

## 12. Database changes
New additive table `work_item_assignments` (append-only event ledger; open
row = current assignment; closed rows = history) with unique-open index,
assignee/entity indexes, RLS enabled deny-by-default (V3 API is the only
access path). No existing table/column changed; no factors touched.

## 13. Migration details
`supabase/migrations/20260902030000_phase5_work_item_assignments.sql` —
idempotent (`IF NOT EXISTS`), additive, applied locally. Migration count
42 → **43**.

## 14. Audit implementation
Every state-changing action writes an immutable `audit_trail` event
(`table_name='manual_extraction_item'`, `record_id=item`,
`action_type='work_item:<action>'`, actor, timestamp, changed_fields incl.
assignee/previous-assignee and immutable origin context). 11 events verified
(5 claim, 2 complete, 1 reassign, 1 recover, 2 release).

## 15. Concurrency / idempotency
- Unique partial index prevents duplicate open assignments (409 on race).
- Same-assignee claim and duplicate complete are idempotent (200 changed=false).
- Verified: concurrent duplicate claims → one open row (codes [200,409]).

## 16. Frontend changes
None in WS1 (backend-first). Any D38 UI (assignment state/history views,
PE claim/release controls) is deferred to WS4 and documented there. No
PEShell, navigation or route changes were made.

## 17. Test results
- WS1 live verification (isolated fixtures; no demo data touched): all 28
  functional gates PASS — internal claim/reassign/release/claim/complete/
  idempotent-complete/recover/history; PE claim/same-entity-idempotent/
  complete/claim+release/history; concurrency; audit.
- Regression subset (23 tests): test_v3_context, test_pe_auth,
  test_processing_origin_qc, test_v1_2_dual_origin_workflow — all PASS.

## 18. Negative security results
All DENY gates PASS (403/404/422 as designed): cross-PE claim & read; PE
operator on internal item; customer→ops; customer→PE; consultant→ops;
consultant→PE; internal ops on PE-assigned item; ops assign to non-staff
(422); forged work item ops (404) and PE (404).

## 19. Data-integrity results
After fixture teardown: emission_factors=7049; migrations=43;
organizations=975; items=260; batches=56; conversations=34; notifications=0;
assignment ledger=0 (all WS1 fixture rows + 11 test audit rows removed). No
customer/consultant/PE/staff/demo data mutated.

## 20. V1.2 conformance
Immutable processing provenance preserved through every operation (verified:
internal CARBONTALLY_INTERNAL, PE PROCESSING_ENTITY unchanged); PE roles
unchanged; PE QC / CT QC / customer approval untouched; no ownership
redesign; no RLS changes; no auth changes; no V1.3.

## 21. Files created
- supabase/migrations/20260902030000_phase5_work_item_assignments.sql
- backend/services/work_items.py
- docs/architecture/CARBONTALLY_PHASE5_WS1_D38_IMPLEMENTATION_REPORT.md

## 22. Files modified
- backend/data/manual_extraction.py (ledger repository methods +
  is_active_internal_staff)
- backend/api/v3_operations.py (ops D38 endpoints)
- backend/api/v3_pe.py (PE D38 endpoints)

## 23. Files deleted
None.

## 24. Known limitations
- PE item-level reassignment is intentionally not authorized (PE reassignment
  stays batch-level via D22); documented design decision, not a defect.
- Ledger operations do not change manual_extraction_items.status; completion
  here is assignment-completion attribution, distinct from the existing
  workflow stage transitions (start/extract/map/validate/calculate/review).
- WS1 UI intentionally deferred to WS4.

## 25. Deferred UI work
Assignment/history visibility in Ops queues and PEShell, claim/assign/
reassign/release/complete controls, and any notification of assignment
events (D40 producers) — deferred to WS4/WS3 respectively.

## 26. WS1 acceptance checklist
- [x] Canonical V3 WorkItem capability (over manual_extraction_items)
- [x] assignment / reassignment / claim / release / complete / recover
- [x] attribution preserved (previous-assignee, actor, timestamps, reasons)
- [x] partial-work recovery with concurrency control
- [x] immutable V1.2 origin preserved
- [x] audit trail complete (immutable, actor + resource)
- [x] authorization matrix enforced (internal + PE + cross-domain deny)
- [x] cross-PE isolation verified
- [x] internal/PE boundaries verified
- [x] idempotency / duplicate-prevention verified
- [x] 7,049 factors preserved; migration count 43 (baseline 42 + approved WS1)
- [x] E2E fixtures removed; no demo/business data mutated
- [x] V1.2 regression green

IMPLEMENTED / VERIFIED — see §1. DEFERRED — UI integration (WS4). No commits,
no pushes; working tree left for Product Owner review.
