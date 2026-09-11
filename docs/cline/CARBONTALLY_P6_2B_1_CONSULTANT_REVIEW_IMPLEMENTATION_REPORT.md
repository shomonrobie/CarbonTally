# CarbonTally P6-2B-1 — Consultant Review State & Authorization (implementation report)

- **Date:** 2026-09-06
- **Status:** `P6-2B-1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`
- **Authorities:** Accepted P6-2B architecture
  (`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`),
  PO decision P6-2B-D1 (self-review), frozen six-flag model (D1), frozen P6-2A.

## 1. Verdict

`P6-2B-1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

## 2. Implemented Scope

Only P6-2B-1: Consultant Review state, authorization, transitions, rework
(to `mapping`), audit, and focused tests. **NOT implemented:** submission to
CarbonTally QC, `can_submit` behaviour, CT-QC changes, billing/entitlement,
provenance redesign, D38 changes, PE↔Consultant handoff, D39/D40, UI, customer
approval changes. No migration was required (status vocabulary is free-varchar;
the change is additive code/domain vocabulary only).

## 3. Files Changed

- `backend/domain/partners.py` — additive `consultant_reviewed` status;
  `WORKFLOW_STAGE_STATUSES["review"]` includes it; `ITEM_STATUS_FLOW`:
  `calculated → consultant_reviewed`; `consultant_reviewed → (mapping,
  calculated)`.
- `backend/api/consultant_auth.py` — `ensure_consultant_processing_authorized`
  `permission` now Optional (None = capability-free path used by Review; flags
  still enforced whenever a permission is supplied — P6-2A unchanged); new
  canonical `ensure_consultant_review_authorized` (consultant-capacity gate
  reusing the canonical resolver with `permission=None`).
- `backend/api/v3_processing_workflow.py` — new
  `POST /api/v3/processing/items/{item_id}/consultant-review` (+ payload +
  audit helper).
- `backend/tests/unit/api/test_p6_2b_1_consultant_review.py` — new (16 tests).
- This report.

## 4. Workflow-State Representation

One additive item status `consultant_reviewed` (distinct from internal
`reviewed`, PE review/QC, `ct_qc_*`, `customer_review`, `approved`). Entry
requires item status `calculated`. Review pass → `consultant_reviewed`; Review
fail → `mapping` (existing rework state). No migration (status column is
free-varchar; no CHECK constraint on the status vocabulary).

## 5. Authorization Chain

```text
identity (require_auth)
→ consultant capacity only (org members / internal staff / PE staff DENY)
→ ensure_consultant_review_authorized:
    → canonical resolver (permission=None):
        active membership → active engagement (server-derived org from the
        loaded batch/item) → resource-scope + cross-org guards → D38 conflict
        (open item assignment / batch default → DENY)
→ workflow-state eligibility (status must be 'calculated')
→ decision
→ mutation + audit
```

No seventh permission flag; `can_submit` is NOT required and is not granted.

## 6. Self-Review Behavior

Ratified P6-2B-D1 honored: no "different human" rule; the processing
consultant may review their own item (test proves success with the same
member; readiness control only — independent assurance remains CarbonTally QC).

## 7. D38 Enforcement

Reused canonical resolver D38 checks before mutation: open internal-staff item
assignment, open PE item assignment, batch-default internal (`assigned_to`) and
batch-default PE (`entity_id`) all DENY. No D38 change; consultants remain
non-assignees; no handoff introduced.

## 8. Membership / Engagement Enforcement

Per-request: inactive membership DENY; `pending`/`rejected`/`suspended`/
`ended`/`inactive` engagements DENY; only `active` engagement passes.
Cross-firm and cross-client denied; unknown item 404; unauthenticated 401.

## 9. Workflow Transition Behavior

Review allowed only from `calculated`; any other state (including
`consultant_reviewed`, `extracting`, `mapped`, `validated`, QC, customer
states) → 409. Repeat review of an already-reviewed item → 409 (explicit
status eligibility). Rejection requires a `rejection_reason` (422 without).

## 10. Rework Behavior

Review fail routes the item to the existing `mapping` state (established rework
target). No new rework engine. QC/customer rejection behaviour untouched.

## 11. Audit Behavior

Best-effort append-only audit via existing `repos.audit.record`:
`consultant.review:passed` / `consultant.review:rework` with authenticated human
actor, entity (item), status_from/status_to, correlation (item id), notes and
reason. No Gate 4–6 change; firm provenance deferred (P6-2D).

## 12. QC / Customer Approval Boundary

Consultant Review grants no QC authority and no approval authority. Negative
tests: consultant CT-QC decision → 403; consultant customer-review (approval) →
403. Existing CT-QC and customer endpoints unmodified.

## 13. Migration Details

None. Additive domain vocabulary only; no schema/data change.

## 14. Test Results

`pytest tests/unit/api/test_p6_2b_1_consultant_review.py -q` → **EXIT 0**
(16 tests): positives (pass, self-review, rework→mapping, reason-required 422),
capability separation (no `can_submit` needed, flag stays false), capacity
(org member 403), membership/engagement denials (inactive member, five
engagement states), scope (cross-firm, cross-client, unknown item 404, 401),
D38 (open internal/PE item + batch defaults → 403), workflow (invalid states
409, re-review 409), QC/approval boundaries (403), zero-mutation assertions.

## 15. Regression Results

16-suite regression batch (P6-2B-1, P6-2A, P6-2A-R1, processing workflow,
phase regressions, ops, processing-origin/QC, consultants, P6-1B/1C, D38
effective assignment, scope-aware auth, PE auth, D19 lifecycle + domain
transition suites) → **REG_EXIT 0**.
Full unit suite `pytest tests/unit -q` → **FULL_EXIT 0** (100%, no failures).

## 16. Database Before/After Baseline

No migration and no data change. Baseline (before == after, read-only):
`consultant_firm_members=54` (any of the six processing flags true = 0),
`consultant_profiles=55`, `consultant_clients=917`, `organizations=975`,
`manual_extraction_items=260`, `work_item_assignments=0`, `billing_plans=6`,
`customer_subscriptions=0`, `billing_orders=0`, credit ledger = 0. No fixtures.

## 17. Scope-Containment Verification

No P6-2B-2 (submit/CT-QC), no `can_submit` behaviour, no billing, no
entitlement, no provenance schema, no D38 change, no PE↔Consultant handoff, no
D39/D40, no UI, no customer-approval change, no new permission flag.

## 18. Git State

Branch `main`; HEAD `1639121` (unchanged). Modified:
`backend/domain/partners.py`, `backend/api/consultant_auth.py`,
`backend/api/v3_processing_workflow.py`. New: test suite and this report.
Pre-existing dirty working-tree files (consultant/processing/automatic files
from earlier sessions) preserved untouched. No commit, push, or PR.

## 19. Deferred P6-2B-2 Items

Consultant submission to CarbonTally QC (`can_submit` action), CT-QC queue
entry for consultant-origin items, entitlement availability check (D6), origin
value `CONSULTANT`, firm provenance (D7). All deferred by design.

## 20. Known Limitations

- Review is a single action from `calculated` (entry working-state not
  separately represented — mirrors the ops `submit-review` pattern).
- Rework target is `mapping`; resumption depends on re-authorization (no
  assignment semantics change).
- Firm/origin provenance fields are not added (deferred to P6-2D).
- No batch-level orchestration (item-level only, consistent with D38).

## 21. Recommendation for Independent Verification

Subject the change to an independent P6-2B-1 verification gate before any
P6-2B-2 work begins.

---

*End of report.*

