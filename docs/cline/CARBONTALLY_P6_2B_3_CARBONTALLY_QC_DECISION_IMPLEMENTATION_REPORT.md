# CarbonTally P6-2B-3 — CarbonTally QC Decision Boundary (implementation report)

- **Date:** 2026-09-06
- **Status:** `P6-2B-3 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`
- **Authorities:** Accepted/closed Gate 3–6, P6-0, P6-BILL-0/1, P6-1B/1C, P6-2A,
  P6-2B-1, P6-2B-2. Frozen decisions D1–D3, D5–D7, D9.
- Bounded P6-2B-3 workstream. Branch `main`, HEAD `1639121` (unchanged). No
  commit/push/PR.

## 1. Objective

Make the existing CarbonTally QC decision boundary work correctly for
Consultant-submitted items (which enter CT-QC as `reviewed` via P6-2B-2),
including QC approval/rejection and safe rework routing — without creating a
parallel Consultant QC system. Target flow:
`Consultant Processing → Consultant Review → Consultant Submit → CarbonTally QC
→ Customer Review → Customer Approval`.

## 2. Scope

- **Implemented:** one small additive hardening of the existing CT-QC decision
  endpoint (duplicate/race decision safety + audit correctness); in-memory test
  scaffolding for the CT-QC surfaces; a focused P6-2B-3 regression suite.
- **Verified existing behavior (no production change required):** consultant-
  submitted `reviewed` items are listed by the existing CT-QC pending queue and
  are approved/rejected by the existing CT-QC decision endpoint; `ct_qc_rejected`
  rework exits (`mapping`/`extracting`); `ct_qc_approved` proceeds only through
  the org Owner/Admin customer-review surface with the D37 charge at approval;
  Consultants/PE/customers have no CT-QC or Customer-Approval authority.
- **Deferred / not applicable:** D7 Consultant-origin provenance, D38 redesign,
  PE↔Consultant handoff, D39/D40, payment integration, subscription pricing,
  `consultant_billing`, Gate 3–6 behavior, PE workflow semantics, UI.

## 3. Files inspected

- `backend/domain/partners.py` — `ITEM_STATUS_FLOW` (intake/rework/approval exits).
- `backend/api/v3_operations.py` — `submit_internal_review`,
  `ct_qc_queue`/`GET /qc/ct-queue`, `ct_qc_decision_endpoint`
  (`POST /api/v3/ops/qc/items/{item_id}/decision`), staff auth wiring.
- `backend/api/operations_auth.py` — `StaffContext`, `require_staff`,
  `ensure_staff_permission`, `require_internal_staff`.
- `backend/data/manual_extraction.py` — `ct_qc_decision` (repo),
  `list_ct_qc_pending`, `customer_review`.
- `backend/api/v3_processing_workflow.py` — `consultant_submit_item` (P6-2B-2),
  `customer_review_item`.
- `backend/api/consultant_auth.py` — canonical P6-2A consultant chain.
- `backend/services/billing.py` — `get_entitlement` / `charge_processing`
  (PO-D7, D37 charge point).
- `backend/api/dependencies.py` — `ensure_org_access`,
  `ensure_processing_org_access`, `AuditContext`.
- `backend/tests/unit/api/fakes.py` — in-memory manual-extraction / staff /
  billing fakes.
- Existing tests: `test_v3_operations.py`, `test_v3_qc.py`,
  `test_processing_origin_qc.py`, `tests/unit/domain/test_v1_2_dual_origin_workflow.py`,
  `test_v3_processing_workflow.py`, P6-2B-1/2A/2A-R1/2B-2 suites, billing suites.

## 4. Files modified

| File | Change | Kind |
| ---- | ------ | ---- |
| `backend/api/v3_operations.py` | `ct_qc_decision_endpoint`: when the repository mutation returns `None` (item concurrently decided/advanced out of intake) → 409, raised BEFORE the audit record; no success audit for a decision that did not occur | implemented (production) |
| `backend/tests/unit/api/fakes.py` | in-memory `MemoryManualExtraction.ct_qc_decision` + `list_ct_qc_pending` mirroring production semantics (status gate `reviewed`/`pe_qc_approved`/`ct_qc`; `None` when no row matches) | implemented (test scaffolding) |
| `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py` | NEW focused suite — 25 tests (full matrix) | implemented (tests) |
| `docs/cline/CARBONTALLY_P6_2B_3_CARBONTALLY_QC_DECISION_IMPLEMENTATION_REPORT.md` | NEW — this report | implemented (report) |

No migration was added or required. No other production file changed.

## 5. Production changes

**Verified existing behavior (no change required):** the existing CT-QC machinery
already consumes Consultant-submitted `reviewed` items correctly:

- `list_ct_qc_pending` lists any `reviewed`/`pe_qc_approved` item without a
  quality score → consultant-submitted items appear in the existing CT-QC queue.
- `ct_qc_decision_endpoint` (internal staff + `can_qc`) accepts `reviewed` and
  routes to `ct_qc_approved`/`ct_qc_rejected`, stamping
  `quality_score`/`qc_by`/`qc_at`/`qc_notes` via
  `data.manual_extraction.ct_qc_decision` (`WHERE status IN
  ('reviewed','pe_qc_approved','ct_qc')`).
- Rejection rework and customer-boundary behaviour were already safe (see §8–§10).

**Implemented (one additive guard):** in `ct_qc_decision_endpoint`, when
`ct_qc_decision(...)` returns `None` (no row matched — the item was already
decided or concurrently advanced after the pre-check), the endpoint now raises
**409** instead of returning `{"item": None}` with a false success audit. This
hardens the duplicate/race case to zero-mutation denial and ensures a success
audit is only written when a state mutation actually occurred. It does not change
authorization, state validation, or the happy path.

No other production change was made (no new QC permission, no new state, no QC
redesign, no billing change).

## 6. Test changes

- `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py` (new, 25 tests) — the
  complete required test matrix (§ "REQUIRED TEST MATRIX"):
  - **Authorization:** internal `can_qc` approve (1/6) and reject (7); internal
    staff without `can_qc` → 403 zero mutation (2/17/19); Consultant → 403 (3); PE
    staff (entity-scoped) → 403 via `require_internal_staff` (4); customer member
    → 403 (5).
  - **State:** invalid source states (`consultant_reviewed`/`calculated`/`mapping`/
    `extracting`) → 409 zero mutation (8/18); unknown item → 404; duplicate
    decision → 409 with exactly one success audit (9); repository-level second
    decision returns `None` with no mutation (the guarded race); invalid quality
    score → 422 zero mutation (10).
  - **Customer boundary:** CT-QC approval leaves item at `ct_qc_approved`, never
    `approved`, and never charges (11); Consultant cannot convert to `approved`
    (11); PE cannot (12); org member cannot (13); org Owner/Admin CAN approve via
    the existing customer-review route with the D37 charge exactly at approval
    (24 + billing).
  - **Rework:** rejection lands in `ct_qc_rejected` whose only exits are
    `mapping`/`extracting` (14); a rejected item cannot be re-submitted without
    rework and cannot reach `reviewed`/`customer_review`/`approved` (15/25);
    rework claim back into `mapping` works via the existing start-item mechanism
    (14); a rejected item cannot be customer-approved (409 before any charge) (15);
    rejection audit preserves actor + before/after + correlation (16).
  - **Mutation ordering / side effects:** denied decision produces no workflow
    mutation, no CT-QC audit, no billing/subscription/order change (17/19/20);
    submission + CT-QC produce no charge and no notification/event side effect (19/20).
  - **Consultant path:** consultant-submitted `reviewed` item appears in the
    existing CT-QC intake queue (21); authorized CT-QC approves (22) and rejects
    (23) it; approved item proceeds only via the existing customer-review path
    (24); rejected item cannot bypass rework (25).
  - Existing internal path preserved: ops `submit-review` `reviewed` items remain
    QC-decidable.
- `backend/tests/unit/api/fakes.py`: additive in-memory `ct_qc_decision` and
  `list_ct_qc_pending` mirrors (no existing fake behaviour changed).
- No existing test was modified.

## 7. CT-QC authorization analysis

Verified by code trace + tests:

- `ct_qc_decision_endpoint` chain: `require_staff` (active staff profile) →
  `require_internal_staff` (`entity_id IS NULL`) → `ensure_staff_permission(
  "can_qc")` (role permissions from `staff_roles.permissions`) → quality-score
  validation → item load/state validation → repository mutation → audit.
- Consultants are never staff profiles (no route, permission, or indirect
  transition can perform `reviewed → ct_qc_approved` / `reviewed →
  ct_qc_rejected`); PE staff are rejected by `require_internal_staff` even with a
  role carrying `can_qc`; ordinary customers are rejected by `require_staff`.
- No new permission, role, or `consultant_qc` construct was introduced
  (repo-wide search: none).

## 8. State-transition analysis

- `reviewed → ct_qc_approved | ct_qc_rejected` is reachable ONLY through the
  internal `can_qc` decision endpoint (both outcomes validated server-side).
- `ct_qc_approved` exits (flow map): `customer_review`, `mapping`, `approved`,
  `rejected`. `approved` is reachable ONLY via `customer_review_item`
  (`require_org_admin`); there is no other endpoint that writes `approved`
  (verified by code search across `api/`). The latent `ct_qc_approved → approved`
  map entry is the canonical customer-approval transition, not a bypass: it is
  only actionable by an org Owner/Admin through the org-gated surface.
- `ct_qc_rejected` exits: `mapping`, `extracting` only (verified in flow map and
  by test) — a rejected item cannot skip rework.
- Duplicate decisions are rejected (409): either by the endpoint state pre-check
  (sequential) or by the new `None`-guard (concurrent).

## 9. Rework analysis

**Reused the existing rework mechanism; no new rework state.** A rejected
Consultant-submitted item sits in `ct_qc_rejected`, whose canonical exits are
`mapping`/`extracting`. An authorised processing actor claims `mapping` through
the existing `POST /api/v3/processing/items/{id}/start` (`stage=mapping`)
mechanism (tested). From rework the item must be re-processed
(`mapping → mapped → validated → calculated → consultant_reviewed →
consultant-submit → reviewed`) before it can re-enter CT-QC — it cannot reach
`reviewed`/Customer Review/`approved` directly from rejection (tested). QC
rejection rework hardening refinements beyond this are out of scope (deferred).

## 10. Customer Approval boundary

- `ct_qc_approved` is NOT `approved`. Only the existing org Owner/Admin
  customer-review surface (`customer_review_item`, `require_org_admin`) can
  produce `approved`, and that route performs the canonical D37 charge.
- Consultants, PE staff, and ordinary org members cannot convert `ct_qc_approved`
  → `approved` (403; tested). A rejected item cannot be customer-approved (409
  before any charge; tested).
- No Customer-Approval redesign; `require_org_admin` unchanged.

## 11. Billing isolation

- CT-QC decision performs **no** billing operation (code trace: no
  `charge_processing`, credit, order, payment, usage, or subscription call on the
  CT-QC path). Tests assert the credit ledger is unchanged (500 → 500) across
  submission and CT-QC approval/rejection, and that no order is created.
- The ONLY charge is at Customer Approval: the org-owner approval test consumes
  exactly 1 credit (500 → 499) via the existing `charge_processing` path.
- No existing CT-QC path violates the "no charge at CT-QC" rule → no STOP
  condition triggered.

## 12. Audit/notification analysis

- Preserved existing CT-QC audit events (`ct_qc:approved` / `ct_qc:rejected`)
  with: authenticated human actor (`qc_by` = staff `user_id`), action,
  item resource (`entity_id`), before/after (`status_from`/`status_to`),
  quality score, processing-origin/entity context where available, and request
  correlation id. No sensitive payload leakage.
- The new guard ensures a success audit is only written when the repository
  mutation actually occurred (no false `ct_qc:*` audit for a decision that did
  not happen).
- No notification framework is invoked by submission or CT-QC (tested); no D40
  vocabulary change was made.

## 13. RLS/data-access analysis

- No migration and no RLS change. `manual_extraction_items` has no
  `authenticated` UPDATE/INSERT policy — item-status writes (including the CT-QC
  decision and rework claims) remain API-only through service-role repositories
  under FastAPI authorization. Billing, consultant, and engagement tables are
  unchanged (previous read-only policy inspection still holds: no broad
  authenticated writes).
- The in-memory fake additions mirror the production repository surface and do
  not touch RLS or schema.

## 14. Test commands and exact results

| Command | Result |
| ------- | ------ |
| `pytest tests/unit/api/test_p6_2b_3_ct_qc_decision.py -q` | **EXIT 0** — 25 passed |
| Focused regression group (P6-2B-3, P6-2B-2, P6-2B-1, P6-2A, P6-2A-R1, P6-BILL-1, billing core, v3_operations, v3_qc, processing-origin/QC, v1_2 dual-origin domain, v3_processing_workflow, phase-1 core) | **EXIT 0** — 215 passed |

No existing test was modified; no failure was observed in any run.

## 15. Full unit-suite result

`pytest tests/unit -q` → **EXIT 0** — **1,563 collected, 0 failures/errors**
(1,538 prior + 25 new P6-2B-3 tests).

## 16. Database baseline comparison

Read-only SQL before and after (local investor demo DB): **identical** — no
persistent change was made.

| Baseline item | Value |
| ------------- | ----- |
| `organizations` | 975 |
| `consultant_firm_members` | 54 |
| `consultant_profiles` | 55 |
| `consultant_clients` | 917 |
| `manual_extraction_items` | 260 |
| `work_item_assignments` | 0 |
| `billing_plans` | 6 |
| `customer_subscriptions` | 0 |
| `billing_orders` | 0 |
| `billing_credit_ledger` | 0 |
| Six consultant processing flags true | 0 |
| Workflow-state counts (`reviewed`, `consultant_reviewed`, `ct_qc_*`) | 0 each |

No persistent test fixtures were created (the P6-2B-3 suite is fully in-memory),
so no cleanup was required.

## 17. Git status

- Branch `main`; **HEAD unchanged: `1639121` (`16391217103b98dcea520070c5a22c68f12fe607`)**.
- Files modified by this workstream: `backend/api/v3_operations.py` (the
  production guard) and `backend/tests/unit/api/fakes.py` (additive fake mirrors).
- Files added by this workstream: `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py`
  and this report.
- No migration file was added or modified.
- Pre-existing dirty/untracked working-tree files (earlier accepted sessions)
  were preserved untouched. No commit, push, or PR was created.

## 18. Out-of-scope / deferred items

- **Deferred (D7):** Consultant firm/origin provenance and origin-specific queue
  labelling — not implemented; the CT-QC path continues to receive `reviewed`
  items without a new origin-specific state. No production change was needed for
  this workstream (recorded as required by the brief).
- **Deferred:** CT-QC rejection/rework hardening refinements beyond the existing
  canonical rework loop (P6-2B-3+ / future); PE↔Consultant handoff; D39/D40;
  payment integration; subscription pricing; `consultant_billing`; Gate 3–6
  behavior; PE workflow semantics; UI; Customer-Approval redesign.
- **Not applicable:** no D38, billing, engagement, or provenance schema change
  was required.

## 19. Findings

- No blocking findings. The STOP-condition scan (§ "STOP CONDITIONS") found none:
  Consultants/PE cannot perform CT-QC; CT-QC cannot bypass Customer Review; CT-QC
  cannot directly cause Customer Approval; QC rejection cannot bypass required
  rework; unauthorized requests do not mutate state; CT-QC does not charge
  billing; RLS is unchanged/sufficient; no broad architectural redesign was
  required.
- **Verified existing behavior (no production change):** the existing CT-QC
  intake/decision/rework machinery already handled Consultant-submitted items;
  this workstream therefore added only the small duplicate/race guard plus the
  focused regression proof, per the brief's "do not modify production code merely
  to create work" instruction.
- Informational: the CT-QC decision endpoint retains the application-wide
  unconditional-update concurrency characteristic (a decision racing a concurrent
  state change is now rejected via the `None`-guard instead of returning a false
  success); no new locking was introduced.

## 20. Final verdict

`P6-2B-3 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

---

*End of implementation report. Bounded P6-2B-3 workstream: one additive
production guard + focused regression coverage; no migration; no commit/push/PR;
no QC/approval/billing redesign.*




