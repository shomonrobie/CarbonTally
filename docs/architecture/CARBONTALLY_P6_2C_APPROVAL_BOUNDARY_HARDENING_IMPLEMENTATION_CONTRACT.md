# CarbonTally P6-2C — Approval-Boundary Hardening & Workflow Finalisation — Implementation Contract

- **Contract ref:** `CARBONTALLY-P6-2C-IC-20260910-001`
- **Status:** **AUTHORITATIVE IMPLEMENTATION CONTRACT — READY FOR THE NEXT (IMPLEMENTATION) TASK**
- **Date:** 2026-09-10
- **Gate:** Phase 6 → **P6-2C** (NEXT defined gate)
- **Consumes (ratified PO decisions):**
  `PO-P6-2C-D1-20260910`, `PO-P6-2C-D2-20260910`, `PO-P6-2C-D3-20260910` —
  recorded in `docs/architecture/CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`
  (« P6-2C Ratified PO Decisions — 2026-09-10 »).
- **Authority chain:** Product Owner → `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`
  → `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` → this gate contract.
- **Derived from:** `docs/cline/prompt-history/CT-P6-2C-RA-20260910-001.md`
  (P6-2C readiness analysis, verdict *BLOCKED — authority/policy decision
  required* — **now unblocked** by the three ratified decisions).
- **This document is a specification. It implements nothing.**

---

## 1. Objective

Finalise the Phase-6 approval boundary and workflow-stage authorization so that:

1. the `calculated → approved` state-machine transition can only be exercised as
   an **automatic-processing-only** authorization (PO-P6-2C-D1);
2. a consultant can claim the generic `review` stage only with an **existing**
   capability — never on the strength of an active grant alone (PO-P6-2C-D2);
3. the workflow/stage authorization behaviour identified by the P6-2C readiness
   report is finalised **within** the authority of the three ratified decisions
   and the existing architecture (no new policy);
4. the approval boundary, CT-QC boundary, automatic path, billing, provenance,
   audit, RLS and existing tests are all preserved or strengthened — never
   weakened (PO-P6-2C-D3 keeps billing untouched);
5. focused D9 regression protection is added.

## 2. Authorized scope

**Authorized for the next (implementation) task:**

| # | Item | Basis |
|---|---|---|
| S1 | Express the `calculated → approved` authorization explicitly as automatic-only on the customer item-approval route | PO-P6-2C-D1 |
| S2 | Gate the consultant `review` stage claim on the **existing** capability `can_submit` (via the canonical resolver) | PO-P6-2C-D2 |
| S3 | Apply the same PO-D2 rule to the `source` stage-claim alias (same class of gap: `_STAGE_WORKING_STATUS["source"] == "extracting"` while `_STAGE_PERMISSION` has only `"extraction"`), using the **existing** capability `can_extract` | PO-P6-2C-D2 principle ("an active consultant grant by itself must not implicitly grant every workflow-stage capability") + §6C workflow finalisation |
| S4 | Confirm/regression-protect Operations and PE parity for the same stage claim (no functional expansion) | §6E |
| S5 | Focused P6-2C negative/security regression tests + implementation report | §6D |

**Note on S3:** if the PO intends PO-D2 to cover **only** the literal `review`
stage, S3 is a one-line removal. It is included because it is the same defect
class and is fixed by the same existing-capability rule, not by new policy.

## 3. Required behaviour (current → required)

| # | Area | Current behaviour (verified) | Required behaviour |
|---|---|---|---|
| B1 | `POST /api/v3/processing/items/{id}/customer-review`, source=`calculated`, target=`approved` | Ran: `require_org_admin` → PE-origin guard → `_require_transition` → `ensure_manual_ct_qc_prerequisite` → charge → write. Manual items are refused **403**; automatic items pass | **Unchanged outcome**, expressed **explicitly** as automatic-only: for source `calculated`, the item must be AUTOMATIC (via the existing `processing_mode.item_is_automatic`); non-automatic ⇒ **403**. No behavioural change to any currently-passing path |
| B2 | `POST /api/v3/processing/items/{id}/customer-review`, source=`ct_qc_approved`/`customer_review` | Allowed for org owner/admin (manual work that passed CT-QC) | **Unchanged** (manual post-CT-QC approval remains legitimate) |
| B3 | `POST /api/v3/processing/items/{id}/start {"stage":"review"}` (consultant capacity) | Gated only by `ensure_processing_org_access` (active grant); no capability; P6-2B-4 guard blocks manual, automatic passes | Consultant must hold **`can_submit`**; otherwise **403** before any mutation. Organisation-member and internal-staff behaviour unchanged |
| B4 | `POST /api/v3/processing/items/{id}/start {"stage":"source"}` (consultant capacity) | No capability gate (same class of gap) | Consultant must hold **`can_extract`**; otherwise **403**. Non-consultant capacities unchanged |
| B5 | Automatic approval path `POST /api/v3/processing/jobs/{job_id}/review` | `require_org_admin` → `stage=="review"` → `complete_review` + item stamp; no CT-QC; no charge | **Unchanged** |
| B6 | Ops `POST /api/v3/ops/items/{id}/start {"stage":"review"}` | `require_internal_staff` + `can_review` (for validation/review) → P6-2B-4 guard | **Unchanged** (already parity-gated); regression-protect |
| B7 | PE routes | entity status route rejects approval/validation states (403); entity start rejects validation/review (403) | **Unchanged** |
| B8 | Billing | single charge site (customer item approval); job-review does not charge | **Unchanged** (PO-P6-2C-D3) |

## 4. Security invariants

Must hold before and after implementation:

1. `identity → firm → active grant → resource → action → stage` — the canonical
   consultant resolver is the only consultant authorization path.
2. No new role, permission, capability or flag.
3. An active consultant grant alone grants **no** stage capability.
4. Consultants can never perform final Customer Approval.
5. PE, Operations and customer roles remain distinct; no role confusion.
6. No actor injection (actor is always `current_user.user_id`) and no
   organisation substitution (org derived from the item's batch server-side).
7. No IDOR (cross-organisation/cross-firm item id ⇒ 4xx, zero mutation).
8. No alternate-route approval (all approval writes enumerated and guarded).
9. CT-QC boundary intact (`can_qc` internal staff only).
10. Provenance intact (`processing_origin` immutable, `source_item_id`, snapshots).
11. Append-only audit intact; denied actions produce **no** success audit event.
12. Billing boundary intact (charge only at Customer Approval; unchanged).
13. Automatic-processing behaviour unchanged.
14. Manual-processing behaviour unchanged (canonical CT-QC path preserved).
15. P6-2B-4 protections unchanged (`reviewed → customer_review` remains removed;
    the CT-QC prerequisite guard remains).

## 5. Workflow invariants

- `ITEM_STATUS_FLOW` is **not** modified in P6-2C (PO-P6-2C-D1 keeps the
  `calculated → approved` entry).
- `reviewed` continues to have no `customer_review` exit.
- The canonical manual path
  `… → reviewed → ct_qc → ct_qc_approved → customer_review → approved` remains
  the only manual route to approval.
- Invalid transitions continue to return **409** with zero mutation.

## 6. Approval-boundary invariants

- Exactly two item-status write paths can reach `approved`: (a) the customer
  item-approval route (org owner/admin; manual requires CT-QC; automatic-only for
  `calculated`); (b) the automatic job-review route.
- All other surfaces (ops, entity/PE, QC decision, consultant routes) remain
  unable to set `approved`.
- `charge_processing` keeps its single call site; idempotency key
  `charge:item:{id}` unchanged.

## 7. Consultant authorization requirements

- The `review` stage claim resolves through
  `ensure_consultant_processing_authorized(permission="submit")` → `can_submit`.
- The `source` stage claim resolves through `permission="extract"` → `can_extract`.
- Organisation-member (`D10`) and internal-staff behaviour is unchanged.
- D38 conflict evaluation is unchanged (the resolver evaluates it when a
  batch/item is supplied).
- No consultant route may reach `approved` or the CT-QC decision.

## 8. Automatic-processing requirements

- The worker, job routes and the `calculated → approved` automatic approval path
  are **unchanged**.
- The automatic job-review route must remain fully functional (job `completed`,
  item stamped, audit recorded).
- Automatic items remain exempt from routine CT-QC (P6-2B-4 predicate).

## 9. Billing preservation requirements

- **No billing change** (PO-P6-2C-D3). No new charging; no change to
  idempotency, refunds, credit accounting or billing audit.
- Tests may assert the **existing** behaviour (one charge at Customer Approval;
  job-review unchanged) but must not alter it.
- The automatic job-review billing-policy question stays **DEFERRED**.

## 10. Audit/provenance preservation requirements

- Every guard executes **before** any mutation/charge; audit is recorded only
  after a successful mutation.
- Denied requests (403/409/422) produce **no** success audit event.
- `processing_origin`, `processing_entity_id` and `source_item_id` are unchanged.
- Existing audit action names for CT-QC, consultant review/submit and approvals
  are unchanged.

## 11. API/code areas that MAY change (precise targets)

| File | Function / route | Current | Required | Invariant | Test coverage |
|---|---|---|---|---|---|
| `backend/api/v3_processing_workflow.py` | `start_item` (`POST /api/v3/processing/items/{item_id}/start`) + `_STAGE_PERMISSION` | `_STAGE_PERMISSION` = {`extraction`, `mapping`, `validation`, `calculation`} | add `"review": "submit"` and `"source": "extract"` so the consultant capacity is checked for those stage claims | resolver-only authorization; capability check precedes mutation; org-member/internal paths unaffected | P6-2C negatives + existing suites |
| `backend/api/v3_processing_workflow.py` | `customer_review_item` (`POST /api/v3/processing/items/{item_id}/customer-review`) | `ensure_manual_ct_qc_prerequisite` implies automatic-only for source `calculated` | make the automatic-only authorization **explicit** for source `calculated` (reuse `processing_mode.item_is_automatic`); preserve every currently-passing path and status | guard before charge; no status/HTTP change for legitimate paths | P6-2C negatives + P6-2B-4 suite |
| `backend/tests/unit/api/test_p6_2c_approval_boundary.py` (new) | — | — | focused suite (§13/§15) | — | — |
| `docs/cline/CARBONTALLY_P6_2C_…IMPLEMENTATION_REPORT.md` (new) | — | — | implementation report | — | — |

*Optional and behaviour-preserving:* a named private helper may be added **inside**
`processing_mode.py` only if it does not change the existing predicate's
semantics; otherwise `processing_mode.py` is read-only.

## 12. API/code areas that MUST remain unchanged

`backend/domain/partners.py` (map kept — PO-D1), `backend/api/processing_mode.py`
predicate semantics (frozen), `backend/api/v3_automatic_processing.py`,
`backend/workers/automatic_processing.py`, `backend/services/automatic_processing.py`,
`backend/services/billing.py`, `backend/api/v3_pe.py`,
`backend/data/manual_extraction.py`, `backend/data/document_processing.py`,
`backend/api/dependencies.py`, `backend/api/consultant_auth.py` (no new keys — the
resolver already maps `submit`/`extract`), all `supabase/migrations/*` (no
schema/RLS change), all existing tests, the Master Roadmap and the Blueprint.

## 13. Tests that must be added

One focused suite: `backend/tests/unit/api/test_p6_2c_approval_boundary.py`,
covering the §15 matrix plus:

- explicit automatic-only assertion for `calculated → approved`;
- consultant `review` claim — `can_submit=True` ⇒ 200; `can_submit=False` ⇒ 403;
- consultant `source` claim — `can_extract=True` ⇒ 200; `False` ⇒ 403;
- ops/internal parity (`can_review`) regression;
- "`reviewed` can never reach `customer_review`" regression;
- zero-mutation / zero-charge / no-audit assertions on **every** denial.

## 14. Existing tests that must remain green (unmodified)

`test_p6_2b_4_ct_qc_prerequisite.py`, `test_p6_2b_3_ct_qc_decision.py`,
`test_p6_2b_2_consultant_submission.py`, `test_p6_2b_1_consultant_review.py`,
`test_p6_2a_consultant_processing_authorization.py`,
`test_p6_2a_r1_b1_automation_confirm_retry.py`,
`test_v3_processing_workflow.py`, `test_phase1_core_regressions.py`,
`test_v3_operations.py`, `test_v3_qc.py`, `test_processing_origin_qc.py`,
`test_v1_2_dual_origin_workflow.py`, `test_v3_automatic_processing_jobs.py`,
`test_v3_automatic_processing_payload.py`, `test_automatic_processing.py`,
`test_operations_auth.py`, `test_scope_aware_authorization.py`, `test_pe_auth.py`,
`test_billing_core.py`, `test_p6bill1_entitlement_and_consultant_commercial.py`,
`test_v3_consultants.py`, `test_p6_1b_membership_workspace_authorization.py`,
`test_p6_1c_engagement_confirmation.py`, plus the full `pytest tests/unit` suite
(baseline **1,576 collected, EXIT 0**).

## 15. Negative/security test matrix (required)

Expected semantics traced from the current contract (no invented status codes):

| # | Scenario | Expected |
|---|---|---|
| 1 | Consultant ⇒ `approved` | **403** (`require_org_admin`); zero mutation/charge |
| 2 | Processing Entity ⇒ `approved` | **403** (org access + `require_org_admin`) |
| 3 | Operations staff (non-admin internal) ⇒ `approved` | **403** (`require_org_admin`; only admin-role/global-admin staff pass by design) |
| 4 | Regular organisation member ⇒ `approved` | **403** |
| 5 | Viewer ⇒ `approved` | **403** |
| 6 | Unauthenticated ⇒ `approved` | **401** |
| 7 | Cross-organisation actor ⇒ `approved` | **403** (org isolation) |
| 8 | Consultant, active grant, **zero** capabilities ⇒ `review` claim | **403** |
| 9 | Consultant with `can_submit` ⇒ `review` claim | **200** (legitimate) |
| 10 | Manual item without CT-QC ⇒ customer-review/approval | **403** (P6-2B-4 guard) |
| 11 | `reviewed → customer_review` | **409** (no such transition) |
| 12 | Alternate endpoint attempting approval (ops/entity/QC) | **403/409** as today |
| 13 | Actor/ID injection (payload actor, foreign org) | rejected; actor taken from the session |
| 14 | IDOR / cross-firm resource access | **403/404**; zero mutation |
| 15 | Invalid state transition | **409**; zero mutation |
| 16 | Concurrent approval attempts | one wins; loser **409**; no double mutation |
| 17 | Duplicate charge behaviour | idempotent (`charge:item:{id}`) where applicable |
| 18 | Automatic approval path | still functional (job `completed`, item stamped) |
| 19 | P6-2B-4 CT-QC guard | intact for manual; automatic exempt |
| 20 | PE-origin guard | intact (PE work needs `ct_qc_approved` before customer approval) |
| 21 | RLS behaviour | unchanged (no authenticated item writes) |
| 22 | Audit on denied vs successful operations | denials ⇒ no success audit; success ⇒ audit |
| 23 | Provenance fields | unchanged |

## 16. Concurrency / idempotency expectations

- Guards run before mutation; concurrent approval attempts cannot both mutate;
  the loser receives **409**.
- The CT-QC decision `None → 409` race protection is unchanged.
- Charge idempotency key unchanged.

## 17. Acceptance criteria

1. All §15 rows behave as specified, proven by the new suite.
2. Consultant `review`/`source` claims require the specified existing capability.
3. `calculated → approved` is explicitly automatic-only; manual callers denied.
4. Automatic path, manual CT-QC path, PE guards, billing and RLS unchanged.
5. Full `pytest tests/unit` green (baseline 1,576, EXIT 0) with **no** existing
   test modified.
6. No schema/migration/RLS change; no new role or permission.
7. Implementation report produced; independent verification passes.

## 18. Stop conditions (implementation task)

STOP and report — do not improvise — if: a schema/migration/RLS change appears
necessary; a new role/permission appears necessary; the automatic path must be
redesigned; billing must change; the state map or the `processing_mode.py`
predicate must change; any existing test must be modified to pass; any
out-of-scope item is required.

## 19. Out of scope (explicitly prohibited)

P6-2D, P6-2E, P6-2F, Phase 7, Phase 8; new roles/permissions/capabilities;
billing/subscription/RLS/schema redesign; destructive migrations;
automatic-processing architecture redesign; evidence/auditor architecture;
provenance redesign; frontend/consultant-UI/customer-UI redesign; P6-2F E2E UI
work; unrelated refactoring or bug fixes; modifying existing tests to make them
pass; D4 PE↔Consultant handoff; D7 firm/origin provenance.

## 20. Expected migration / schema impact

**None.** No column, state value, constraint or RLS change is required: the
stage-gating changes are pure authorization logic and the approval-boundary item
is behaviour-preserving. If a migration appears necessary, **STOP and report**.

## 21. Expected frontend / UI impact

**None required.** `RoleRoute` and the consultant/customer pages are UX-only and
are not a security boundary. If a newly denied action is offered by the UI, hiding
it is optional cosmetic follow-up, not part of this gate.

## 22. Independent verification requirements

A separate, read-only agent must independently: reproduce every §15 row through
runtime tests (not code reading); confirm the automatic path, CT-QC guard, PE
guard, billing and RLS are unchanged; confirm no existing test was modified;
confirm the change set is limited to §11; and re-run `pytest tests/unit`.

## Deferred (recorded, not actioned)

| Item | Status |
|---|---|
| Automatic job-review billing policy (`/jobs/{id}/review` approves without charging) | **DEFERRED — PO decision required** (PO-P6-2C-D3) |
| D4 PE↔Consultant handoff | deferred (may be scoped out) |
| D6 entitlement timing / D7 firm+origin provenance | P6-2D |
| D8/D11 D39 conversation kind + D40 notification vocabulary | P6-2E |
| `/consultant` processing UI + E2E acceptance | P6-2F |
| P6-2B-4 / P6-1B / P6-1C on-disk verification artifacts | documentation item |

---

*End of contract. This document specifies; it does not implement. The next task
may be issued as: "Implement exactly the P6-2C contract identified by
`CARBONTALLY-P6-2C-IC-20260910-001`."*



