# CarbonTally P6-2B-2 — Consultant Submission → CarbonTally QC (implementation report)

- **Date:** 2026-09-06
- **Status:** `P6-2B-2 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`
- **Authorities:** Accepted P6-2B architecture
  (`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`);
  P6-2A / P6-2A-R1 (closed); P6-2B-1 (accepted after independent verification);
  frozen PO decisions D1 (six capabilities), D2 (active engagement), D3 (D38),
  D5 (workflow), D6 (billing/entitlement), D7 (provenance deferred), D9
  (Customer Approval owner/admin only).
- This workstream is bounded to P6-2B-2 only. It was implemented on branch
  `main` at HEAD `1639121` (unchanged). No commit/push/PR.

## 1. Verdict

`P6-2B-2 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

## 2. Scope implemented

The single next transition of the approved Consultant path:

> `consultant_reviewed` → existing CarbonTally QC intake state (`reviewed`)

implemented as a server-side Consultant submission action:

1. authenticate the actor;
2. establish active Consultant membership;
3. establish active client engagement;
4. derive the organization/resource scope server-side (item → batch);
5. require `can_submit=true` (no other capability substitutes; no auto-grant);
6. enforce D38 effective-assignment conflict rules (reused canonical resolver);
7. verify workflow-state eligibility (`consultant_reviewed` only);
8. perform the non-charging entitlement availability check (D6, fail closed);
9. transition the item into the existing CarbonTally QC intake state;
10. record a submission audit/event (existing infrastructure).

NO billing charge occurs at submission. NO QC decision capability is granted.
Customer Approval remains owner/admin-only and unreachable from submission.

## 3. Existing workflow inspected

- `backend/domain/partners.py` — `ITEM_STATUS_FLOW`: `consultant_reviewed`
  (P6-2B-1) previously exited only to `mapping`/`calculated`; the internal
  CarbonTally path feeds CT-QC through `calculated → reviewed` (ops
  `submit_internal_review`) and the PE path through `pe_qc_approved`.
- Existing CarbonTally QC authority (`backend/api/v3_operations.py`):
  `POST /api/v3/ops/qc/items/{item_id}/decision` — internal staff with
  `can_qc`; accepts items with status `reviewed`/`pe_qc_approved`/`ct_qc` and
  produces `ct_qc_approved`/`ct_qc_rejected`. The CT-QC pending queue
  (`GET /api/v3/ops/qc/ct-queue` → `data/manual_extraction.list_ct_qc_pending`)
  lists items with status `reviewed`/`pe_qc_approved` and no quality score.
- `backend/api/consultant_auth.py` — canonical P6-2A resolver
  `ensure_consultant_processing_authorized(..., permission=...)` already enforces
  active membership, active engagement, the capability flag for `permission`,
  server-derived scope, and D38 conflict. P6-2B-1 added
  `ensure_consultant_review_authorized` (consultant-capacity gate +
  `permission=None`).
- Billing (`backend/services/billing.py`): canonical entitlement resolver
  `BillingService.get_entitlement(org)`; canonical charge
  `BillingService.charge_processing(org, job, idempotency_key)` (fires at
  Customer Approval, D37/PO-D7) DENIES with `EntitlementUnavailableError` (403)
  when the organisation has no active processing entitlement.
- `consultant_reviewed` items previously had no onward path into QC; submission
  was the missing link.

## 4. Submission endpoint/service

`POST /api/v3/processing/items/{item_id}/consultant-submit`
(`backend/api/v3_processing_workflow.py`, `consultant_submit_item`) — the route
name follows the existing surface conventions (`/items/{id}/consultant-review`
P6-2B-1, `/items/{id}/customer-review`, ops `/items/{id}/submit-review`). No
request body is consumed — the resource is the path `item_id`; nothing in the
request can supply an organisation, firm, consultant, entitlement, price, or
workflow state. The submission helper `_audit_consultant_submit` records the
append-only audit after a successful transition.

Control flow (authorization/eligibility complete BEFORE any mutation):

```
identity (require_auth; 401 if unauthenticated)
→ load item (404) → load batch via item.batch_id (404)
→ ensure_consultant_submission_authorized(permission="submit"):
     consultant-capacity gate (internal/entity staff, org members → 403)
     → canonical P6-2A resolver:
         active membership → active engagement (server-derived batch org) →
         can_submit capability → resource-scope guards → D38 conflict (403)
→ workflow-state gate: item.status must equal "consultant_reviewed" (else 409)
→ _require_transition(item, "reviewed") (canonical state machine; 409)
→ D6 non-charging entitlement availability (fail closed; 403) — NO charge
→ set_item_status(item_id, "reviewed")   ← the only workflow mutation
→ _audit_consultant_submit(...)          ← audit only after successful transition
```

## 5. Authorization chain

**identity → active Consultant membership → active engagement → `can_submit`
→ server-derived resource scope → valid workflow state → D38 conflict →
non-charging entitlement availability → submission mutation.**

`ensure_consultant_submission_authorized` (`backend/api/consultant_auth.py`) is
the only submission-specific wrapper and it adds ONLY the consultant-capacity
gate; everything else is delegated to the established P6-2A canonical resolver
`ensure_consultant_processing_authorized` with `permission="submit"` (same chain
P6-2A uses for extract/map/validate/calculate and P6-2B-1 uses for Review).
No parallel authorization system was introduced.

## 6. `can_submit` enforcement

- `permission="submit"` resolves through `CONSULTANT_PERMISSIONS` to the real
  `consultant_firm_members.can_submit` column (frozen six-flag model — no seventh
  flag, no `can_review`).
- Allow: active member + active engagement + `can_submit=true` → 200.
- Deny: `can_submit=false` → 403 even when every other condition holds.
- The other five capabilities (`can_extract`, `can_map`, `can_validate`,
  `can_calculate`, `can_confirm_automation`) do NOT substitute — each was tested
  individually as the only set flag with `can_submit=false` → 403.
- `can_submit` is never auto-granted or modified by the submission action (test
  asserts the member's flags are unchanged after a successful submission; DB
  baseline still shows 0 members with any processing flag true).

## 7. Membership/engagement enforcement

Both are evaluated at request time through the canonical resolver — inactive
membership never resolves (`_resolve_context` returns only ACTIVE
`consultant_firm_members` rows; single distinct active firm required) and only
`consultant_clients.status = 'active'` grants the engagement. Covered by tests:
inactive membership → 403; pending/rejected/suspended/ended/inactive engagement
→ 403; active engagement + active membership → allow.

## 8. Server-derived scope

The organisation is resolved as `item → item.batch_id → batch.organization_id`
server-side. The route has no body/query organisation parameter, so there is no
organisation to forge. Tests prove: a forged `organization_id` (and forged
`consultant_id`/`firm_id`/`price`) in the request body cannot authorize a
submission for an org the consultant does not serve (403), and cannot redirect a
legitimate submission away from the server-derived org (the item still enters
the batch's org flow). A broken item→batch relationship denies (404) rather than
submitting.

## 9. D38 enforcement

Reused the canonical resolver's D38 conflict checks verbatim (no duplication, no
assignment mutation, no handoff). Effective assignment is resolved as: open
item-level `work_item_assignments` row takes precedence (internal `assigned_to`
or PE `processing_entity_id`); otherwise the batch default carrier
(`assigned_to` internal / `entity_id` PE). Tests: item-level internal → 403,
item-level PE → 403, batch-default internal → 403, batch-default PE → 403,
unassigned → allowed. No `consultant` assignee kind exists and none was added
(`assignee_kind` CHECK constraint unchanged).

## 10. Workflow-state enforcement

Server-side gate only: submission requires `item.status == "consultant_reviewed"`
(409 otherwise), and `_require_transition(item, "reviewed")` re-checks the
canonical `ITEM_STATUS_FLOW`. Tests deny submission from `extracting`, `mapping`,
`validating`, `calculated`, and an already-submitted (`reviewed`) item; a
`calculated` item (Consultant processing complete but NOT reviewed) cannot skip
Review (409).

## 11. Target CT-QC state

The existing CarbonTally QC intake contract is: the CT-QC pending queue lists
`reviewed`/`pe_qc_approved` items and the CT-QC decision endpoint accepts
`reviewed`/`pe_qc_approved`/`ct_qc`. There is no separate "consultant submitted"
intake state. Per §10 of the gate brief, no duplicate `consultant_qc`-style state
was created: submission transitions the item into the existing state
**`reviewed`** (`_CT_QC_INTAKE_STATUS`), which is exactly the state that (a) makes
the work appear in the existing CT-QC pending queue and (b) makes it eligible for
the existing internal CarbonTally QC authority with **no QC endpoint change**.
The item then continues the canonical path `reviewed → ct_qc_approved /
ct_qc_rejected` (QC decision) → Customer Review → Customer Approval.

Consultant firm/origin distinction (a CONSULTANT origin value / queue labelling)
is intentionally NOT represented here and is documented for the later
D7/provenance workstream (P6-2D).

## 12. Entitlement availability check

Added one additive, READ-ONLY method to the existing server-authoritative
billing service (no billing redesign):

`BillingService.ensure_processing_entitlement(organization_id)` — calls the
canonical `get_entitlement(org)` and then re-checks the same active-subscription
source that `charge_processing` gates on; raises `EntitlementUnavailableError`
(403) when the organisation has no ACTIVE processing entitlement. It performs NO
charge, NO credit consumption, NO usage recording and NO
order/payment/ledger/subscription/plan mutation. This is exactly the D6
"non-charging availability check": an organisation that cannot commercially
proceed (PO-D7: no active entitlement → the eventual chargeable approval is
denied) is stopped at submission, fail-closed, before any workflow mutation.

Coverage: no entitlement → 403 with zero workflow/billing mutation and no
submission audit; cancelled subscription → 403; active subscription → allowed
with no charge.

## 13. Billing non-charge confirmation

- Submission invokes only `ensure_processing_entitlement` (read-only) — never
  `charge_processing`, `consume_credits`, `grant_credits`, order/payment/usage
  writes.
- Tests assert: successful submission leaves the credit ledger balance at 0 and
  creates no subscription and no order; entitlement denial likewise produces no
  ledger/order/subscription change.
- The canonical charge point remains **Customer Approval**
  (`customer_review_item` → `BillingService.charge_processing`); no second charge
  was added. Consultant Review, Consultant submission and CT-QC consume nothing.

## 14. Audit behavior

`_audit_consultant_submit` records through the existing append-only
`repos.audit.record` (`audit_trail`) with the canonical `AuditEntry`:

- action: `consultant.submit:submitted` (namespace consistent with
  `consultant.review:passed` and the ops `review:submitted` vocabulary);
- actor: authenticated human `current_user.user_id`;
- resource: `entity_type="manual_extraction_item"`, `entity_id=item_id`;
- before/after: `{"status": "consultant_reviewed"}` / `{"status": "reviewed"}`;
- `changed_fields`: `status_from`/`status_to`;
- timestamp + `correlation_id=item_id`.

Best-effort (audit failure never breaks the submission), matching the P6-2B-1 and
ops review patterns. Audit is written ONLY after a successful state transition;
every denial class produces no submission audit. No D7 firm/origin provenance
fields were added.

## 15. QC boundary

Submission is a declaration of readiness for CarbonTally QC — it grants no QC
authority:

- The CT-QC decision endpoint remains internal `require_staff` +
  `can_qc` only; it was NOT modified.
- Tests: a consultant calling
  `POST /api/v3/ops/qc/items/{item_id}/decision` → 403; and after a successful
  submission the same consultant still receives 403 on that endpoint (no
  `can_qc` is granted, and no staff capability can be acquired by a consultant).

## 16. Customer Approval boundary

- Submission cannot reach Customer Review/Approval: the only possible outcome is
  `reviewed` (test asserts the result is `reviewed`, never `customer_review`,
  `approved`, `ct_qc`, or `ct_qc_approved`).
- After submission the item still requires the CT-QC decision (internal `can_qc`)
  before `ct_qc_approved`, then the org Owner/Admin customer-review surface.
- The customer-review route was not modified (`require_org_admin` still governs);
  a consultant calling it → 403.

## 17. Concurrency considerations

The submission action uses the same mechanism as every other item transition in
the application (`set_item_status` is a plain `UPDATE ... WHERE id = $1` with the
state gate evaluated on the loaded snapshot — no row lock, no optimistic
`WHERE status = 'consultant_reviewed'` predicate). Implications, consistent with
the accepted P6-2B-1 mechanism (no new locking introduced):

- **Race A/B** (two simultaneous submissions / state advances between check and
  commit): both may read `consultant_reviewed`; the final state is one of the
  legitimate states reachable from `consultant_reviewed` (`reviewed`, or the ops
  rework `mapping`/`calculated` if a concurrent rework won). A duplicate audit
  entry is the only plausible benign side effect.
- **Race C/D/E** (D38 assignment appears / engagement ends / entitlement lapses
  between authorization and commit): the same TOCTOU window shared by the
  existing workflow transitions.

This is the established application-wide transition mechanism — not a new race
class introduced by P6-2B-2 — and is noted here for the independent gate rather
than "fixed" with new locking (per the gate brief).

## 18. Tests

New dedicated suite `backend/tests/unit/api/test_p6_2b_2_consultant_submission.py`
— **29 tests, EXIT 0** (in-memory world; no database access). Coverage map
(reference the gate brief list):

- Positive: submission success enters the existing CT-QC intake state (`reviewed`)
  and is audited; target state is the existing CT-QC intake status; no
  charge/billing mutation; no auto-grant of capabilities.
- Capability: `can_submit=false` → 403 (zero mutation); the other five
  capabilities individually cannot substitute; org member → 403.
- Membership: inactive membership → 403.
- Engagement: pending/rejected/suspended/ended/inactive → 403 (zero mutation, no
  audit).
- Scope: cross-firm → 403; cross-client → 403; forged body org cannot authorize;
  forged body org cannot redirect; unresolved item→batch → 404.
- D38: item-level internal and PE assignment → 403; batch-default internal and PE
  → 403; unassigned → allowed (positive path).
- Workflow: extracting/mapping/validating/calculated/reviewed → 409; cannot skip
  Review (calculated → 409); already-submitted item cannot resubmit (409).
- Billing/entitlement: no entitlement → 403 with zero workflow/billing mutation
  and no audit; cancelled entitlement → 403; credit ledger unchanged on success.
- QC boundary: consultant cannot perform CT-QC decision; submission does not
  grant CT-QC authority.
- Approval boundary: submission cannot produce customer_review/approved; consultant
  cannot perform customer approval.
- Ordering: authorization/entitlement precede mutation; successful audit only
  after successful transition (exactly one `consultant.submit:submitted` entry
  with actor + status_from/status_to); denied classes produce no submission audit.

## 19. Regression tests

All runs against existing tests; none modified.

| Suite | Result |
| ----- | ------ |
| P6-2B-2 dedicated (new) | **EXIT 0** — 29 passed |
| P6-2B-1 | **EXIT 0** — 16 passed |
| P6-2A | **EXIT 0** — 18 passed |
| P6-2A-R1 | **EXIT 0** — 14 passed |
| P6-BILL-1 + billing core | **EXIT 0** — 23 + 17 passed |
| Broad 22-suite regression batch (P6-1B, P6-1C, D38 effective assignment, operations auth, scope-aware auth, PE auth, v3 QC, processing-origin/QC, processing workflow, D19 lifecycle, phase-1 core regressions, automatic-processing jobs/payload/services, automatic extraction, Gate-4 provenance, audit immutability, consultant branding, P6-2A/2A-R1/2B-1/2B-2) | **EXIT 0** — 294 passed |
| Full unit suite `pytest tests/unit -q` | **EXIT 0** — 1,538 collected, 0 failures/errors | 

## 20. Database before/after

Read-only baseline checks before and after implementation (local investor demo
DB, 127.0.0.1:54426). Identical before/after — no data, assignment, billing, or
schema change was made:

| Baseline item | Before | After |
| ------------- | ------ | ----- |
| `organizations` | 975 | 975 |
| `consultant_firm_members` | 54 | 54 |
| `consultant_profiles` | 55 | 55 |
| `consultant_clients` | 917 | 917 |
| `manual_extraction_items` | 260 | 260 |
| `work_item_assignments` | 0 | 0 |
| `billing_plans` | 6 | 6 |
| `customer_subscriptions` | 0 | 0 |
| `billing_orders` | 0 | 0 |
| `billing_credit_ledger` | 0 | 0 |
| Members with any of the six processing flags true | 0 | 0 |
| Items in status `consultant_reviewed` / `reviewed` | 0 / 0 | 0 / 0 |

No disposable fixtures were written to the database (the new tests are fully
in-memory), so no cleanup was required.

## 21. Migration details, if any

**None.** The item status column is free-varchar with no CHECK constraint on the
status vocabulary, and submission reuses the existing `reviewed` state, so the
change is additive domain/API code only. No migration was added and none of the
D38 / billing / engagement / provenance schemas were touched.

## 22. Scope containment

This workstream implemented ONLY the Consultant submission transition. Explicitly
NOT included (verified absent from the delta):

- CarbonTally QC decision implementation / QC authorization changes / any
  consultant QC permission (`can_qc` is staff-only; QC endpoints unmodified);
- billing redesign / new payment integration / credit charging at submission
  (the only billing change is an additive read-only availability method);
- Consultant firm provenance / processing-origin schema (deferred to D7/P6-2D;
  documented in §11/§25);
- D38 changes (no migration, no assignee kind, no handoff);
- PE↔Consultant handoff;
- D39 / D40 (no notification/conversation/event-system work);
- Customer Approval redesign (approval remains org Owner/Admin; `require_org_admin`
  unchanged);
- UI (no frontend change);
- any change to P6-2A or P6-2B-1 semantics (capabilities and the Review action are
  untouched; `consultant_reviewed` remains the required Review outcome and the
  Review route is unmodified).

No migration was required, so no out-of-scope schema dependency exists.

## 23. Files changed

P6-2B-2 delta (working tree on `main` at HEAD `1639121`):

| File | Change |
| ---- | ------ |
| `backend/domain/partners.py` | `ITEM_STATUS_FLOW["consultant_reviewed"]` now exits to `mapping`/`calculated`/`reviewed` (additive submission exit); comment updated |
| `backend/api/consultant_auth.py` | new `ensure_consultant_submission_authorized` (consultant-capacity gate + canonical P6-2A resolver with `permission="submit"`) |
| `backend/api/v3_processing_workflow.py` | import of the new wrapper; `_CT_QC_INTAKE_STATUS = "reviewed"`; `_audit_consultant_submit`; `POST /api/v3/processing/items/{item_id}/consultant-submit` |
| `backend/services/billing.py` | additive read-only `BillingService.ensure_processing_entitlement` (D6 availability, no mutation) |
| `backend/tests/unit/api/test_p6_2b_2_consultant_submission.py` | NEW — 29 tests |
| `docs/cline/CARBONTALLY_P6_2B_2_CONSULTANT_SUBMISSION_IMPLEMENTATION_REPORT.md` | NEW — this report |

No migration file was added or modified.

## 24. Git state

- Branch: `main`; **HEAD unchanged: `1639121` (`16391217103b98dcea520070c5a22c68f12fe607`)**.
- Files newly created by this workstream: the P6-2B-2 test suite and this report.
- Files modified by this workstream: the four source files listed in §23 (each of
  these files also carries pre-existing accepted working-tree changes from earlier
  sessions; this workstream's delta is the additive portion described above).
- Pre-existing dirty working-tree files (earlier accepted sessions — P6-2A/2A-R1,
  P6-2B-1, V1.2, D20–D37, tooling/skills moves, etc.) were preserved untouched.
- No commit, push, or PR was created.

## 25. Known limitations / deferred items

- **Origin representation (D7/P6-2D):** a consultant-submitted item enters the
  shared `reviewed` intake with no CONSULTANT origin marker, so the CT-QC queue
  currently cannot visually distinguish consultant-submitted work from
  internally-reviewed work. This is the deliberate provenance deferral; the later
  provenance workstream adds the origin value + queue labelling. The workflow is
  functionally correct without it (the work is eligible for the existing internal
  CarbonTally QC authority).
- **QC rejection/rework path:** not implemented in this workstream. The existing
  state machine already routes `ct_qc_rejected → mapping/extracting`, from which a
  re-authorized consultant can rework to `calculated` → `consultant_reviewed` →
  re-submit; no state-machine change was needed. CT-QC rework hardening remains a
  later item (P6-2B-3) if the PO requires it.
- **Shared transition mechanism/TOCTOU:** submission uses the application-wide
  unconditional status update (see §17); no new locking was introduced per the
  brief.
- **Entitlement granularity:** the availability check mirrors the canonical
  charge-time gate (active processing entitlement present). Credit/allowance
  sufficiency for the eventual charge remains a Customer Approval (D37) concern
  and is deliberately not pre-judged at submission.
- P6-2B-3 and later workstreams (submission UI/E2E under P6-2F, entitlement
  availability surfacing under P6-2D, etc.) are NOT started.

## 26. Recommendation for independent verification

Subject the P6-2B-2 implementation to an independent verification gate before any
P6-2B-3 or later workstream begins. Suggested emphasis for the independent
verifier: (1) the target-state decision (`consultant_reviewed → reviewed` as the
existing CT-QC intake state) and its provenance-deferral implication; (2) the
non-charging entitlement availability semantics against PO-D7/D6; (3) the
canonical-resolver reuse and absence of any new QC/approval authority; and (4)
the concurrency/TOCTOU characteristics shared with the rest of the workflow.

---

*End of implementation report. Bounded P6-2B-2 workstream: no commit/push/PR; no
migration; no out-of-scope implementation.*






