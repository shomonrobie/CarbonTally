# CarbonTally P6-2B-3 — CarbonTally QC Decision Boundary — Independent Verification Report

- **Date:** 2026-09-06
- **Gate:** Independent verification (READ-ONLY). No code, test, migration, RLS,
  or data was modified by this gate; nothing committed/pushed.
- **Git baseline:** branch `main`, HEAD `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`).
- **Authorities:** Gate 3–6, P6-0/BILL-0/BILL-1, P6-1B/1C, P6-2A, P6-2B-1,
  P6-2B-2 closed/accepted; frozen P6-2B decisions D1–D3, D5–D7, D9.

## 1. Verification objective

Independently prove that the CarbonTally QC decision boundary is correct for
Consultant-submitted items (`consultant_reviewed → reviewed → CT-QC →
Customer Review → Customer Approval`), including: authorized-CT-QC-only
decisions; `reviewed` semantics; no CT-QC bypass to Customer Review/Approval;
correct rejection/rework; zero charge at CT-QC; correct audit; RLS integrity;
no hidden scope expansion; and persistent-baseline preservation.

## 2. Implementation report reviewed

`docs/cline/CARBONTALLY_P6_2B_3_CARBONTALLY_QC_DECISION_IMPLEMENTATION_REPORT.md`
(verdict `IMPLEMENTED`). Per the gate rules it was read for context only; every
claim below was independently re-verified by source trace, runtime probe, and
test execution.

## 3. Files inspected

- `backend/api/v3_operations.py` — `ct_qc_queue`, `ct_qc_decision_endpoint`
  (incl. the new repository-`None` guard), `submit_internal_review`,
  `_get_item_and_batch`.
- `backend/api/operations_auth.py` — `require_staff`, `require_internal_staff`,
  `ensure_staff_permission`, `StaffContext`.
- `backend/data/manual_extraction.py` — `ct_qc_decision`, `list_ct_qc_pending`.
- `backend/domain/partners.py` — `ITEM_STATUS_FLOW`, `WORKFLOW_STAGES`,
  `WORKFLOW_STAGE_STATUSES`.
- `backend/api/v3_processing_workflow.py` — `consultant_review_item` (P6-2B-1),
  `consultant_submit_item` (P6-2B-2), `customer_review_item`, `start_item`
  (generic stage-claim), `_get_checked_item`, `_STAGE_WORKING_STATUS`,
  `_STAGE_PERMISSION`.
- `backend/api/consultant_auth.py` — P6-2A canonical resolver.
- `backend/services/billing.py` — `charge_processing`/`get_entitlement`.
- `backend/api/dependencies.py` — org-access helpers, `AuditContext`.
- New tests `test_p6_2b_3_ct_qc_decision.py`, in-memory fakes, and the P6-2B-2/1,
  P6-2A/R1, billing, ops, QC, PE, workflow test suites.

## 4. CT-QC authorization

**Verified correct.** `ct_qc_decision_endpoint` enforces, in order:
`require_staff` (active staff profile) → `require_internal_staff`
(`entity_id IS NULL`) → `ensure_staff_permission("can_qc")` → quality-score
validation → item load (404) → intake-state check (409) → repository mutation →
audit. PE staff are denied by `require_internal_staff` even with a role that
carries `can_qc` (tested). No new QC permission/role was introduced. The P6-2B-3
implementation added no authorization widening.

## 5. Consultant boundary

**Verified correct in isolation:** Consultants are not staff profiles and cannot
call the CT-QC decision endpoint (403; tested both before and after submission).
Consultant submission (`consultant_reviewed → reviewed`) grants no QC authority
and no `can_qc`; there is no `consultant_qc` construct (repo-wide search: none).

## 6. `reviewed` semantics

**Partially verified — one critical FAILURE (see §20).** `reviewed` is the
existing awaiting-CT-QC intake: `list_ct_qc_pending` lists
`reviewed`/`pe_qc_approved` items with `quality_score IS NULL`, and the CT-QC
decision endpoint accepts `reviewed` and produces `ct_qc_approved` /
`ct_qc_rejected`. It is therefore "awaiting QC", not QC-completed — that part is
confirmed.

**However, question 8 ("`reviewed` cannot bypass CT-QC and reach Customer
Review/Approval") FAILS.** `ITEM_STATUS_FLOW["reviewed"]` still contains the exit
`customer_review`, and the generic stage-claim endpoint
`POST /api/v3/processing/items/{id}/start` (`_STAGE_WORKING_STATUS["review"] =
"customer_review"`) performs that transition for any actor with organisation
access (org members; Consultants with an active grant), because the `review`
stage carries no `_STAGE_PERMISSION` entry and therefore skips the consultant
capability/D38 gate. Runtime probe (see §19/§20) confirmed this is reachable
end-to-end by the submitting Consultant.

## 7. CT-QC approval

**Verified correct (as an operation):** internal `can_qc` staff can approve a
Consultant-submitted `reviewed` item → `ct_qc_approved`, stamping quality data
and auditing `ct_qc:approved`; the item is NOT `approved` and no credit is
charged at CT-QC. **But** the bypass in §6 means CT-QC approval is not actually
*required* for a Consultant-submitted item to reach the customer surface, which
defeats the purpose of this workstream's boundary.

## 8. CT-QC rejection / rework

**Verified correct.** `ct_qc_decision_endpoint(approved=False)` moves a
`reviewed` item to `ct_qc_rejected` (audited `ct_qc:rejected`). The only flow
exits from `ct_qc_rejected` are `mapping`/`extracting`; a rejected item cannot be
re-submitted directly (`consultant-submit` → 409) and cannot reach
`customer_review`/`approved` (409 before any charge). Rework back into `mapping`
works through the existing `start {"stage":"mapping"}` claim (tested). No
Consultant-specific rework state exists.

## 9. Customer Review / Approval boundary

**Partially verified — one critical FAILURE.** The approval *route* is correctly
restricted: `customer_review_item` requires `require_org_admin`; Consultants, PE
staff, and ordinary members receive 403 on a `ct_qc_approved` item; only the org
Owner/Admin can produce `approved`, and the D37 charge fires at that point
(tested: ledger 500 → 499). **However**, because a Consultant can move a
`reviewed` (awaiting-CT-QC) item to `customer_review` via the stage-claim
endpoint (§6/§20), the org Owner/Admin can then approve it — producing `approved`
**with no CT-QC decision ever having occurred**. That is a reachable CT-QC
bypass for Consultant-submitted work and contradicts the frozen
D5/P6-2B-2/P6-2B-3 flow (`Consultant Submit → CT-QC → Customer Review →
Customer Approval`).

## 10. Billing isolation

**Verified correct.** The CT-QC decision path performs no billing operation
(code trace; tests assert ledger 500 → 500 across submission and CT-QC
approval/rejection, no order created). The only charge is at Customer Approval
(org-owner approval consumes exactly 1 credit). No existing CT-QC path charges.

## 11. Concurrency guard

**Verified correct.** The P6-2B-3 change to `ct_qc_decision_endpoint` is
present: when the repository `ct_qc_decision` returns `None` (item concurrently
decided/advanced out of intake — the repository UPDATE is guarded by
`WHERE status IN ('reviewed','pe_qc_approved','ct_qc')`), the endpoint raises
**409 before recording any audit** instead of returning `{"item": None}` with a
false success audit. Sequential duplicate decisions are rejected by the pre-check
(409, exactly one success audit); the repository-level double-decision returns
`None` with no mutation (tested). Audit now occurs only after an actual state
mutation on this endpoint.

## 12. Zero-mutation denial

**Verified correct for the tested classes.** Unauthorized attempts
(staff-without-`can_qc`, Consultant, PE, customer member) → 403 with item state,
ledger, subscriptions and orders unchanged and no `ct_qc:*` audit; invalid source
states → 409 unchanged; invalid quality score → 422 unchanged; duplicate decision
→ 409 unchanged. No notification side effects.

## 13. Audit

**Verified correct on the CT-QC decision path:** `ct_qc:approved` /
`ct_qc:rejected` entries carry the authenticated human actor (`qc_by`), item
entity, before/after states, quality score, and request correlation id, and are
written only after a successful mutation (the new `None`-guard enforces this on
races). Consultant submission audit (`consultant.submit:submitted`) is separate
and correct. **Independently notable:** in the bypass reproduction the full audit
trail contained `consultant.submit:submitted` but **no `ct_qc:*` event** — i.e.,
the item reached `approved` without any CT-QC audit, corroborating the bypass.

## 14. Notifications

**Verified:** no notification framework is invoked by consultant submission or
CT-QC decision; no D40 change exists. No notification side effect was observed in
any test or probe.

## 15. RLS

**Verified unchanged and sufficient.** No migration and no RLS policy change
(read-only `pg_policies` inspection: the same 13 policies as the accepted
baseline). `manual_extraction_items` has no `authenticated` UPDATE/INSERT policy —
item-status writes (CT-QC decision, stage claims, approval) flow only through
API/service-role repositories under application authorization. The verified
bypass is an application-authorization gap, not an RLS gap.

## 16. Regression tests

All executed against existing tests; none modified.

| Suite | Result |
| ----- | ------ |
| Dedicated `test_p6_2b_3_ct_qc_decision.py` | **EXIT 0** — 25 passed |
| 16-suite regression group (P6-2B-3, P6-2B-2, P6-2B-1, P6-2A, P6-2A-R1, P6-BILL-1, billing core, v3_operations, v3_qc, processing-origin/QC, v1_2 dual-origin domain, v3_processing_workflow, phase-1 core, operations auth, scope-aware auth, PE auth) | **EXIT 0** — 256 passed |

## 17. Database baseline

Read-only SQL at this gate — identical to the accepted baseline, no verification
fixtures remain:

`organizations 975 · consultant_firm_members 54 · consultant_profiles 55 ·
consultant_clients 917 · manual_extraction_items 260 · work_item_assignments 0 ·
billing_plans 6 · customer_subscriptions 0 · billing_orders 0 ·
billing_credit_ledger 0 · six consultant processing flags true 0 · workflow-state
counts: no `reviewed`/`consultant_reviewed`/`ct_qc_*` items` (status distribution
`pending 160, approved 30, extracted 28, calculated 14, mapped 12, validated 10,
rejected 3, extracting 2, qc_approved 1`).

## 18. Git status

- Branch `main`; **HEAD `1639121` unchanged** (`16391217103b98dcea520070c5a22c68f12fe607`).
- P6-2B-3 working-tree delta (verified): modified `backend/api/v3_operations.py`
  (the `None`-guard) and `backend/tests/unit/api/fakes.py` (additive in-memory
  CT-QC mirrors); added `backend/tests/unit/api/test_p6_2b_3_ct_qc_decision.py`
  and the implementation report (+ this report). No migration was added
  (migration directory still ends at `20260906100000_p6_2a_...`).
- Pre-existing dirty/untracked files from earlier accepted sessions remain
  untouched (porcelain counts unchanged apart from this gate's report file).
- No commit, push, PR, or working-tree cleanup was performed.

## 19. Findings

### Findings verified as facts (independent evidence)

- **F-1 (verified):** CT-QC decision authority is internal `can_qc` only; PE,
  Consultant, and customer denials are enforced server-side with zero mutation.
- **F-2 (verified):** `reviewed` is the awaiting-CT-QC intake state (pending
  queue + decision intake), not QC-completed.
- **F-3 (verified):** CT-QC approval/rejection, rework exits
  (`mapping`/`extracting`), org-owner-only Customer Approval with the D37 charge
  at approval, audit-after-mutation (incl. the new `None`-guard), billing
  isolation, RLS stability, and the unchanged database baseline all behave as
  documented.
- **F-4 (blocking — see §20):** `reviewed → customer_review` remains reachable
  through the generic stage-claim endpoint, enabling a Consultant-submitted item
  to reach Customer Approval with no CT-QC decision.

### Runtime reproduction (read-only probe, in-memory world mirroring the API composition root)

```
1. Consultant submits `consultant_reviewed` item → 200, status `reviewed`.
2. SAME consultant POST /api/v3/processing/items/{id}/start {"stage":"review"}
   → 200, status becomes `customer_review`.
3. Org Owner POST /api/v3/processing/items/{id}/customer-review {approved:true}
   → 200, status becomes `approved`.
4. Item audit trail: ["consultant.submit:submitted"] — NO `ct_qc:*` event.
```

Root cause: `_STAGE_WORKING_STATUS["review"] = "customer_review"` and
`ITEM_STATUS_FLOW["reviewed"]` retains the exit `customer_review`; the generic
`start` claim applies `_require_transition(item, "customer_review")` without any
CT-QC-pass or origin gate, and the `review` stage has no `_STAGE_PERMISSION`
entry, so the consultant capability/D38 gate is skipped for this claim. The same
claim surface is available to ordinary org members on `reviewed` items
(pre-existing class); for Consultant-submitted work it is a reachable,
Consultant-drivable bypass of the CarbonTally QC gate that P6-2B-2/P6-2B-3 are
chartered to enforce. (It also means the earlier P6-2B-2 verification statement
that "no endpoint performs `reviewed → customer_review`" was incorrect: the
generic stage-claim endpoint performs it.)

## 20. Blocking findings

- **BLOCKER-B1 — Consultant-submitted work can bypass CarbonTally QC and reach
  Customer Approval.** A `reviewed` (awaiting-CT-QC) item can be moved to
  `customer_review` by the submitting Consultant (or any org member) via
  `POST /api/v3/processing/items/{id}/start {"stage":"review"}`, after which the
  org Owner/Admin can approve it — with **no `ct_qc:approved` decision and no
  CT-QC audit**. This contradicts the frozen flow
  (`Consultant Submit → CT-QC → Customer Review → Customer Approval`), the
  P6-2B-3 verification question 8 (`reviewed` cannot bypass CT-QC and reach
  Customer Review/Approval), and the workstream's objective that the CT-QC
  decision boundary be enforced for Consultant-submitted items. It is a genuine
  security/workflow-control gap in the current state of the consultant path.

Remediation (NOT performed — read-only gate; requires a bounded hardening
workstream): prevent the `reviewed → customer_review` claim for items that have
not passed CT-QC — e.g., remove the `customer_review` exit from
`ITEM_STATUS_FLOW["reviewed"]` or gate the `review`-stage claim on a CT-QC pass /
origin rule — and re-verify that no actor can place awaiting-CT-QC work on the
customer surface without an internal `can_qc` decision. No P6-2B-3 code defect
was found in the additive `None`-guard itself; the blocker is in the boundary
state this workstream was required to make correct.

## 21. Scope assessment

- The P6-2B-3 implementation delta itself is minimal and in-scope (one additive
  guard + test scaffolding); no hidden scope expansion was found (no QC redesign,
  no `consultant_qc`, no `can_qc` grant, no billing change, no D38/handoff/
  provenance/D39/D40/UI work, no migration).
- The blocker is NOT introduced by the P6-2B-3 guard; it arises from the
  interaction of the pre-existing stage-claim mechanism and flow-map exit with
  P6-2B-2's `reviewed` intake. Nevertheless, per the gate's binary rule
  (every required condition must pass; do not provide a conditional pass), the
  failure of verification question 8 and of the workstream's core boundary means
  the gate FAILS.

## 22. Final verdict

`P6-2B-3 VERIFICATION FAILED — BLOCKING FINDINGS`

---

*End of independent verification report. Read-only gate: no code, test, migration,
RLS, or data change was made; no commit, push, or PR was created. Blocker
documented for a bounded remediation workstream and re-verification.*


