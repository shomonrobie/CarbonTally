# CarbonTally P6-2B-2 — Consultant Submission → CarbonTally QC — Independent Verification Report

- **Date:** 2026-09-06
- **Workstream:** P6-2B-2 (Consultant Review → Consultant Submission → CarbonTally QC intake)
- **Gate:** Independent verification (read-only). No fixes implemented; P6-2B-3 and later workstreams not started.
- **Git baseline:** branch `main`, HEAD `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`) — unchanged by this gate.
- **Authorities:** Accepted P6-2B architecture; P6-2A / P6-2A-R1 (closed); P6-2B-1 (accepted, independently verified); frozen decisions D1–D3, D5–D7, D9.

---

## 1. Final verdict

`P6-2B-2 VERIFICATION PASSED — READY FOR PO ACCEPTANCE`

No blocking finding was identified. Every P6-2B-2 acceptance condition (§29 of the
gate brief) is satisfied on the inspected runtime code, tests, database baseline,
RLS state, and Git state. The critical target-state decision
(`consultant_reviewed → reviewed`, where `reviewed` is the existing CarbonTally
QC intake state) was independently code-traced and found safe. Only informational
observations are recorded (§27). No defect was repaired and no out-of-scope work
was performed.

## 2. Verification scope

Verified independently (source inspection + read-only SQL/RLS inspection + running
existing tests; the implementation report was read but NOT relied on as proof):

1. The critical `reviewed` target-state assessment (meaning, producers, consumers,
   awaiting-vs-completed semantics, QC/approval bypass potential).
2. Runtime code-path trace of `POST /api/v3/processing/items/{item_id}/consultant-submit`.
3. Authorization chain and canonical P6-2A resolver reuse.
4. `can_submit` exclusivity; no auto-grant.
5. Membership/engagement lifecycle (request-time).
6. Server-derived resource scope and forged-input resistance.
7. D38 effective-assignment enforcement (no migration, no handoff).
8. Workflow-state eligibility (cannot skip Review; duplicate-submission safety).
9. Authorization-before-mutation ordering.
10. Zero-mutation denial classes.
11. D6 entitlement availability (read-only, server-authoritative, fail-closed).
12. Billing isolation (no charge/credit/order/payment/subscription mutation).
13. Audit behaviour.
14. QC authority boundary.
15. Customer Review/Approval boundary.
16. Existing Internal/PE/QC workflow preservation.
17. RLS security.
18. Concurrency characteristics.
19. Tests (dedicated + regressions + full unit).
20. Database baseline, migration/schema state, scope containment, Git state.

## 3. Critical `reviewed` target-state assessment

Independent code trace answers (question numbers from the gate brief §4):

| # | Question | Independent finding |
|---| -------- | ------------------- |
| 1 | What does `reviewed` mean? | In the canonical V1.2 workflow `reviewed` is the **internal review-completion hand-off state that feeds the late CarbonTally QC gate** (internal path `… → calculated → reviewed → ct_qc_approved/ct_qc_rejected → customer_review → approved`). It is distinct from PE statuses (`pe_reviewed`, `pe_qc_approved`), CT-QC outcomes (`ct_qc_approved/rejected`), `customer_review`, and `approved`. |
| 2 | Which endpoints create `reviewed`? | Exactly two: (a) ops `POST /api/v3/ops/items/{item_id}/submit-review` (`submit_internal_review`, internal `can_review`; `calculated → reviewed`, PE-origin denied); (b) the new `POST /api/v3/processing/items/{item_id}/consultant-submit` (`consultant_reviewed → reviewed`). No other code writes status `reviewed`. |
| 3 | Which endpoints consume `reviewed`? | The CarbonTally QC surfaces: `GET /api/v3/ops/qc/ct-queue` (`list_ct_qc_pending`) and `POST /api/v3/ops/qc/items/{item_id}/decision` (`ct_qc_decision_endpoint` → `data.manual_extraction.ct_qc_decision`, `WHERE status IN ('reviewed','pe_qc_approved','ct_qc')`). |
| 4 | Does the CT-QC pending queue include `reviewed`? | **Yes** — `list_ct_qc_pending` selects `status IN ('reviewed','pe_qc_approved') AND quality_score IS NULL`. A submitted item therefore appears in the existing CT-QC queue without any QC change. |
| 5 | Does CT-QC decision accept `reviewed`? | **Yes** — the decision endpoint and repository method accept `reviewed` (also `pe_qc_approved`, `ct_qc`) and produce `ct_qc_approved`/`ct_qc_rejected`. |
| 6 | Does `reviewed` mean "awaiting QC" rather than "QC completed"? | **Awaiting QC.** `reviewed` items have `quality_score IS NULL` and appear in the pending queue; the QC decision stamps `quality_score`/`qc_by`/`qc_at` and produces the `ct_qc_*` outcome. It is not a QC-completed state and not a customer-facing state. |
| 7 | Does entering `reviewed` grant QC authority? | **No.** Status is data; authority is the server-side staff context. Every QC surface requires `require_staff` → `require_internal_staff` + `ensure_staff_permission("can_qc")`. A Consultant remains non-staff (403) before and after submission (tested). |
| 8 | Can a Consultant exploit `reviewed` to bypass CT-QC? | **No.** A Consultant has no route that acts on a `reviewed` item: the consultant-review route requires `calculated`; the consultant-submit route requires `consultant_reviewed`; ops/QC/customer routes require staff/org-admin. After submission the Consultant cannot move the item further. |
| 9 | Can a Consultant directly reach Customer Review from `reviewed`? | **No.** No endpoint performs a `→ customer_review` transition (repo-wide search: no `set_item_status(…,'customer_review')` and no `_require_transition(…,'customer_review')` call exists), and the customer-review route requires org Owner/Admin (`require_org_admin`), which a Consultant is not. |
| 10 | Can a Consultant directly reach `approved` from `reviewed`? | **No.** `ITEM_STATUS_FLOW["reviewed"]` does not contain `approved`, and the only approval route (`customer_review_item`, `require_org_admin`) cannot transition `reviewed → approved` (its transition targets are `approved`/`rejected`). |
| 11 | Does using `reviewed` alter existing Internal/PE semantics? | **No adverse change.** Internal producers/consumers of `reviewed` are unchanged (`submit_internal_review`, CT-QC queue/decision untouched); the PE path never uses `reviewed` (PE items enter CT-QC via `pe_qc_approved`); the PE-origin customer-approval guard is unchanged. The only shared-state nuance: consultant-submitted items are indistinguishable from internally-reviewed items in the queue (origin provenance deferred to D7 — expected, not a defect; see F-3). |

**Conclusion:** `reviewed` is a safe, genuine CT-QC intake state for this purpose.
The implementation did not invent a parallel state, did not duplicate the QC state
machine, and created no path from submission to Customer Review/Approval without
the internal CT-QC decision.

## 4. Runtime code-path trace

Actual call sequence in the working tree (read from `backend/api/v3_processing_workflow.py` → `consultant_submit_item`):

1. `Depends(require_auth())` — authenticated identity (401 when unauthenticated).
2. `repos.manual_extraction.get_item(item_id)` → 404 if missing.
3. `repos.manual_extraction.get_batch(item.batch_id)` → 404 if missing (no body/query resource input; organization not yet consulted).
4. `ensure_consultant_submission_authorized(current_user, repos, batch=batch, item=item)`:
   - consultant-capacity gate: internal staff / PE staff / org members → 403;
   - `ensure_consultant_processing_authorized(... permission="submit")` (canonical P6-2A resolver): `_resolve_context` (ACTIVE membership only) → server-derived authoritative org (`batch.organization_id`) → active client grant (`consultant_clients.status='active'` for the firm on that org) → `can_submit` capability (`ensure_consultant_permission`, no other capability maps to `submit`) → D38 conflict (open item assignment OR batch carrier `entity_id`/`assigned_to`) → 403 on any failure.
5. Workflow-state gate: `item.status == "consultant_reviewed"` required → else 409.
6. `_require_transition(item, "reviewed")` — canonical `ITEM_STATUS_FLOW` check → 409 if the flow denies.
7. `BillingService(repos).ensure_processing_entitlement(batch.organization_id)` — read-only D6 availability; `EntitlementUnavailableError` → 403 HTTPException. No charge/mutation.
8. `repos.manual_extraction.set_item_status(item_id, "reviewed")` — the ONLY workflow mutation, reached only after steps 1–7.
9. `_audit_consultant_submit(...)` — append-only audit (`consultant.submit:submitted`) after the successful transition.
10. Return `{"item": updated}`.

No notification is sent. The request body is never parsed (route has no body model), so no client-supplied organization/consultant/firm/price/entitlement/state is ever read.

## 5. Authorization chain

The implemented runtime chain is the required chain:

**authenticated identity → active Consultant membership → active engagement →
`can_submit` → server-derived client/resource scope → valid workflow state
(`consultant_reviewed`) → D38 conflict check → non-charging entitlement
availability → submission mutation → successful audit.**

Check ordering within the endpoint is: capability/scope/D38 (inside the canonical
resolver) run before the state gate, which runs before the entitlement check, all
before mutation. No unauthorized or commercially ineligible request can reach the
mutation: every axis raises before `set_item_status`. The ordering (D38 inside the
resolver preceding the explicit state gate) is the same structural pattern as the
accepted P6-2B-1 review route and preserves the security invariant.

## 6. Canonical resolver reuse

Submission reuses the established P6-2A foundation. `ensure_consultant_submission_authorized`
(`backend/api/consultant_auth.py`) adds ONLY the consultant-capacity gate and then
delegates to `ensure_consultant_processing_authorized` with `permission="submit"`
— the identical canonical chain P6-2A uses for extract/map/validate/calculate and
P6-2B-1 uses for Review. Membership, engagement, client scope, capability, and D38
are all enforced through that single resolver. No independent/second Consultant
authorization model was introduced (repo-wide call-site search: the wrapper is
invoked only by the submit endpoint).

## 7. `can_submit` verification

- `permission="submit"` maps through `CONSULTANT_PERMISSIONS` to the real
  `consultant_firm_members.can_submit` column. Exactly six capability columns exist
  (P6-2A migration); there is no seventh `can_review`.
- Allow (tested): active member + active engagement + `can_submit=true` +
  `consultant_reviewed` + no D38 conflict + active entitlement → 200 into `reviewed`.
- Deny (tested): `can_submit=false` → 403, zero mutation.
- Non-substitution (tested per flag): `can_extract`, `can_map`, `can_validate`,
  `can_calculate`, `can_confirm_automation` each set as the only capability with
  `can_submit=false` → 403.
- No automatic capability granting: the submission action performs no membership/
  flag mutation (code trace + test asserts the member's flags are unchanged after a
  successful submission); live DB shows 0 members with any processing flag true.

## 8. Membership/engagement verification

Both evaluated at request time (no caching): membership via `_resolve_context`
(active rows only; single distinct active firm) and engagement via
`consultants.get_client_by_org(firm, org)` with `status == 'active'` required.
Dedicated-test evidence:

| Condition | Expected | Verified |
| --------- | -------- | -------- |
| Active membership + active engagement | ALLOW | positive tests (200) |
| Inactive membership | DENY | 403 |
| Pending engagement | DENY | 403 |
| Rejected engagement | DENY | 403 |
| Suspended engagement | DENY | 403 |
| Ended engagement | DENY | 403 |
| Inactive engagement | DENY | 403 |

## 9. Resource-scope verification

The organization is resolved server-side as `item → item.batch_id →
batch.organization_id`. The route defines no body model, so a forged
`organization_id`, consultant ID, firm ID, or price in the request body is never
parsed. Dedicated tests: cross-firm → 403; cross-client (item in an org without an
active grant) → 403; forged body org on an unauthorized org → 403; forged body
org/consultant/firm/price on an authorized org → submission still governed by the
server-derived org (200, item in the correct org flow); unresolved item→batch → 404.

## 10. D38 verification

The canonical resolver's D38 checks run before mutation for every submission:
open item-level `work_item_assignments` row (internal `assigned_to` or PE
`processing_entity_id`) → 403; otherwise batch default carrier (`assigned_to`
internal / `entity_id` PE) → 403; no effective assignment → proceeds (positive
tests). No `consultant` assignee kind exists (`assignee_kind` CHECK remains
`internal_staff`/`processing_entity`); no D38 migration; no assignment records are
mutated by submission; no handoff mechanism exists. Dedicated-test matrix: item
internal/PE → 403; batch-default internal/PE → 403; unassigned → allowed.

## 11. Workflow-state verification

Server-side only: submission requires `item.status == "consultant_reviewed"`
(409 otherwise) and `_require_transition(item, "reviewed")` re-checks the
canonical flow. Dedicated tests deny `extracting`, `mapping`, `validating`,
`calculated`, and an already-submitted (`reviewed`) item (409), and prove a
Consultant cannot skip P6-2B-1 Review (`calculated` → 409). Repeated submission of
an already-submitted item is rejected (409) — no invalid duplicate transition; no
separate idempotency contract exists in the canonical workflow for this state, so
denial is the correct behaviour.

## 12. Authorization-before-mutation

Control-flow inspection of `consultant_submit_item` confirms the mutation
(`set_item_status`) is the 8th step and is preceded by: identity (1), item/batch
load (2–3), full consultant authorization incl. D38 (4), workflow-state gate (5),
canonical transition check (6), and the entitlement availability check (7). The
audit (9) follows the mutation. There is no code path in which any of these
checks can be bypassed to reach the mutation, and the entitlement check runs
before any state change.

## 13. Zero-mutation denial

Denials raise HTTPException before `set_item_status` and before the audit helper,
so no business mutation occurs. The dedicated suite asserts status preservation
and/or absence of the submission audit for every important denial class:
`can_submit=false` (403); each non-substituting capability (403); inactive
membership (403); all five non-active engagement states (403, status unchanged, no
audit); cross-firm/cross-client and forged-input (403); item-level and
batch-default D38 conflicts (403, status unchanged, no audit); invalid workflow
states (409, status unchanged, no audit); already-submitted (409); and entitlement
denial (403, status unchanged, ledger/subscriptions/orders unchanged, no audit).
No denial path records a successful-submission audit, mutates billing, or sends a
notification.

## 14. Entitlement availability verification

`BillingService.ensure_processing_entitlement(org)` is:

- **read-only** — it calls `get_entitlement(org)` (reads organization, active
  subscription, plan/config, ledger balance, usage) plus the same
  `billing_subscriptions.get_active_for_org(org)` lookup that `charge_processing`
  gates on; it performs no writes (verified by code inspection; no mutation calls
  are present in its body);
- **server-authoritative** — inputs are the server-resolved org id; no client
  claim/price/entitlement is accepted;
- **fail-closed** — raises `EntitlementUnavailableError` (403) when no ACTIVE
  subscription exists (org missing likewise fails closed via `get_entitlement`);
- **client-organization scoped** — the org is `batch.organization_id`
  (item → batch), i.e. the organisation owning the work; a consultant subscription
  cannot substitute (the check never queries consultant billing);
- **non-charging** — no `charge_processing`, `consume_credits`, `grant_credits`,
  order/payment/usage/ledger/subscription mutation.

**Definition of "available":** the organisation holds an ACTIVE processing
entitlement (an active `customer_subscriptions` row). This matches the first gate
of the Customer-Approval charge path (`charge_processing` → PO-D7 denies without
an active subscription), so the two checks do not contradict the canonical
commercial model. They differ only in purpose: submission checks entitlement
presence (non-charging); Customer Approval performs the actual charge and at that
point also enforces STANDARD allowance / CREDIT balance sufficiency. Submission is
therefore never allowed for a client with no processing entitlement (blocking
condition checked — not present), and nothing is ever charged or consumed by
submission (blocking condition checked — not present). The remaining-granularity
nuance (an entitled org with zero remaining credits may still submit; the charge
gate then applies at approval) is recorded as informational F-4.

## 15. Billing isolation

Submission invokes only the read-only `ensure_processing_entitlement`; it never
calls `charge_processing`, credit operations, order/payment/usage/subscription
methods. Dedicated tests assert on the success path: credit-ledger balance stays 0;
no subscription is created; no order is created. Denial paths assert the same plus
no state change. The canonical charge point remains Customer Approval
(`customer_review_item` → `BillingService.charge_processing`); no second charge
was introduced anywhere (code search confirms the only new billing surface is the
read-only availability method).

## 16. Audit verification

Successful submission records one append-only `audit_trail` entry via the
canonical `repos.audit.record`/`AuditEntry`:

- event name: `consultant.submit:submitted` (existing `consultant.*`/`*:submitted`
  namespaces);
- actor: authenticated human `current_user.user_id`;
- resource: `entity_type="manual_extraction_item"`, `entity_id=item_id`;
- organization: not a dedicated column, but the org is server-derived from the
  item's batch (consistent with the existing audit contract; no org column exists
  on `audit_trail` for other item actions either);
- previous state / new state: `status_from="consultant_reviewed"`,
  `status_to="reviewed"` in `changed_fields` plus `before`/`after`;
- correlation identifier: `correlation_id=item_id` (the existing fallback pattern).

Audit is written only after a successful state transition (best-effort wrapper,
consistent with P6-2B-1/ops conventions). Denied requests produce no submission
audit. No future D7 firm/origin provenance field is fabricated or claimed.

## 17. QC boundary

Submission grants no QC authority:

- Status `reviewed` alone confers nothing; all QC surfaces require internal staff
  context (`require_staff` → `require_internal_staff` + `can_qc`).
- The CT-QC decision endpoint was not modified by P6-2B-2 (the four-file delta
  contains no QC file). Consultants calling
  `POST /api/v3/ops/qc/items/{item_id}/decision` receive 403 both before and after
  a successful submission (dedicated tests).
- A Consultant cannot supply QC parameters, outcomes, or forged state: the
  consultant-submit route consumes no QC inputs and the QC route is staff-gated.
- No new QC permission exists (six-flag model unchanged; `can_qc` is a staff
  permission on the staff side, never a consultant capability).

## 18. Customer Review / Approval boundary

- The submission route's only possible outcome is status `reviewed` (dedicated
  test asserts the result is `reviewed`, never `customer_review`/`approved`/
  `ct_qc`/`ct_qc_approved`).
- After submission, the canonical path continues only through the internal CT-QC
  decision (`reviewed` → `ct_qc_approved`/`ct_qc_rejected`) before any customer
  surface, and the customer-review route (`require_org_admin`) remains the sole
  approval authority. Consultants receive 403 on it (dedicated test).
- No latent approval-bypass entry was newly made reachable by P6-2B-2 (see §3,
  rows 8–10). No latent transition entries elsewhere were repaired (out of scope).

## 19. Existing workflow preservation

- **Internal:** `submit_internal_review` (`calculated → reviewed`, internal
  `can_review`) is unchanged; CT-QC queue/decision unchanged; internal items
  proceed exactly as before. Informational nuance (F-2): because the state-machine
  exit `consultant_reviewed → reviewed` is shared, an internal `can_review` staff
  caller may now also route a `consultant_reviewed` item to `reviewed` through the
  existing ops `submit-review` route (previously 409). This is an internal-staff
  action only — it grants Consultants nothing, does not bypass any Consultant
  security boundary, and is consistent with internal staff authority over
  organisational work (D22: internal staff may act on batches; PE-origin remains
  denied by `submit_internal_review`). Non-blocking.
- **PE:** untouched — PE work continues through `pe_reviewed`/`pe_qc_approved` →
  CT-QC; the PE-origin customer-approval guard is unchanged.
- **Customer:** approval surface unchanged (org Owner/Admin; D37 charge at
  approval). Customer review queue does not list `reviewed`/`consultant_reviewed`
  items.
- **QC decision flow:** unchanged; the added consultant-submitted items simply
  join the `reviewed` intake that the existing CT-QC authority already consumes.

## 20. RLS verification

Read-only `pg_policies` inspection (same 13 policies as the accepted baseline; no
migration was added by P6-2B-2):

- `manual_extraction_items`: no UPDATE/INSERT policy for `authenticated` — item
  status writes are API-only (the consultant-submit route runs under the
  service-role repository with full application-level authorization, verified in
  §4–§13). No broad authenticated write exists.
- `manual_extraction_batches`: tenant UPDATE gated by `is_org_member`; consultants
  cannot mutate batches via PostgREST.
- Billing tables (`customer_subscriptions`, `billing_orders`,
  `billing_credit_ledger`, etc.): no authenticated write policies among the
  inspected set (subscription/order/ledger writes remain API/admin-only).
- Consultant tables: `consultant_firm_members` UPDATE is self-only; client rows are
  select/delete-gated by firm/tenant helpers.
- No direct PostgREST path bypasses the API authorization for submission.

## 21. Concurrency assessment

The submission action uses the same unconditional `UPDATE ... WHERE id = $1`
(`set_item_status`) as every other item transition in the application, with the
state gate evaluated on the loaded snapshot (no row lock, no
`WHERE status='consultant_reviewed'` predicate). Analysis of the gate's races:

- **Race A (two Consultants submit):** both may read `consultant_reviewed`; the
  final state is `reviewed` (both set the same target) or, in a concurrent-rework
  interleaving, one of the other legitimate exits (`mapping`/`calculated`). No
  invalid state results; a duplicate audit entry is the only plausible side effect.
- **Race B (state changes after authorization):** last-writer-wins with valid
  targets only (the flow restricts exits), consistent with the rest of the
  workflow.
- **Races C/D/E (D38 assignment appears / engagement ends / entitlement lapses
  between authorization and commit):** the same TOCTOU window shared by every
  existing item transition; the checks are re-run per request and no write-side
  re-verification exists anywhere in the application.

This is the established application-wide transition characteristic, not a new race
class introduced by P6-2B-2, and per the gate brief no locking was added. Recorded
as informational (F-1).

## 22. Test results

All runs executed against the existing tests without modification.

| Suite | Result |
| ----- | ------ |
| P6-2B-2 dedicated `tests/unit/api/test_p6_2b_2_consultant_submission.py` | **EXIT 0** — 29 passed |
| Focused group (P6-2B-2 + P6-2B-1 + P6-2A + P6-2A-R1 + P6-BILL-1 + billing core) | **EXIT 0** — 117 passed |
| Broad 22-suite regression batch (P6-1B, P6-1C, D38 effective assignment, operations auth, scope-aware auth, PE auth, v3 QC, processing-origin/QC, processing workflow, D19 lifecycle, phase-1 core regressions, automatic-processing jobs/payload/services, automatic extraction, Gate-4 provenance, audit immutability, consultant branding, P6-2A/2A-R1/2B-1/2B-2) | **EXIT 0** — 294 passed |
| Full unit suite `pytest tests/unit -q` | **EXIT 0** — 1,538 collected, 0 failures/errors |

The dedicated suite covers: positive submission into the existing CT-QC intake
state with audit; target-state structural assertion; no-charge/no-billing-mutation
and no auto-grant; `can_submit=false` and each of the other five capabilities →
403; inactive membership → 403; all five non-active engagement states → 403;
cross-firm/cross-client and forged-body-org denials (incl. the no-redirect proof);
unresolved item→batch → 404; D38 item-level (internal/PE) and batch-default
(internal/PE) → 403; unassigned allowed; invalid states (extracting/mapping/
validating/calculated/reviewed) → 409; cannot-skip-Review; duplicate submission →
409; no/cancelled entitlement → 403 with zero workflow+billing mutation; credit
ledger unchanged on success; consultant QC-decision → 403 before and after
submission; submission cannot reach `customer_review`/`approved`; consultant
customer-approval → 403; authorization/entitlement-precede-mutation; audit only
after successful transition (exactly one event with actor and
`status_from`/`status_to`); no submission audit on any denial class.

## 23. Database baseline

Read-only SQL (local investor demo DB, 127.0.0.1:54426) taken independently at
this gate:

| Baseline item | Expected | Verified |
| ------------- | -------- | -------- |
| `organizations` | 975 | 975 |
| `consultant_firm_members` | 54 | 54 |
| `consultant_profiles` | 55 | 55 |
| `consultant_clients` | 917 | 917 |
| `manual_extraction_items` | 260 | 260 (status sum = 260) |
| `work_item_assignments` | 0 | 0 |
| `billing_plans` | 6 | 6 |
| `customer_subscriptions` | 0 | 0 |
| `billing_orders` | 0 | 0 |
| `billing_credit_ledger` | 0 | 0 |
| Members with any of the six processing flags true | 0 | 0 |
| Items in `consultant_reviewed` / `reviewed` | 0 / 0 | 0 / 0 (status counts show neither state present) |

Item status distribution: `pending 160, approved 30, extracted 28, calculated 14,
mapped 12, validated 10, rejected 3, extracting 2, qc_approved 1`. No unintended
production/test data remains — the dedicated suite is entirely in-memory, so no
fixture cleanup was required.

## 24. Migration/schema verification

- No migration was added by P6-2B-2 (migration directory ends at
  `20260906100000_p6_2a_consultant_processing_permissions.sql`; repo-wide search
  finds no P6-2B/`consultant_reviewed`/`consultant-submit` markers in
  `supabase/migrations/`).
- Schema is unchanged. The item status column is free-varchar with no CHECK
  constraint on the status vocabulary, so both `consultant_reviewed` (P6-2B-1) and
  the reused `reviewed` target remain supported by the existing schema.
- No unrelated schema (D38, billing, engagement, provenance) was altered.

## 25. Scope-containment audit

Independently confirmed NOT implemented by P6-2B-2 (delta = 4 source files +
2 new files; the new mutation route is a single `consultant-submit` endpoint):

- CT-QC decision implementation / Consultant QC authority / new QC permission —
  absent (QC endpoints and staff `can_qc` unchanged);
- billing charge or credit consumption at submission — absent (the only billing
  addition is a read-only availability method; charge remains at Customer
  Approval);
- new payment integration — absent;
- Consultant firm provenance / processing-origin schema — absent (deferred to
  D7/P6-2D; nothing falsely claims origin provenance);
- D38 changes / PE↔Consultant handoff — absent (no migration, no assignee kind,
  no assignment mutation);
- D39 / D40 — absent (no notification/conversation/event work);
- Customer Approval redesign — absent (`require_org_admin` + charge point
  unchanged);
- UI — absent (no frontend change).

## 26. Git state

- Branch: `main`; **HEAD unchanged: `1639121` (`16391217103b98dcea520070c5a22c68f12fe607`)**.
- P6-2B-2 files changed (`git status --porcelain`): `backend/domain/partners.py`,
  `backend/api/consultant_auth.py`, `backend/api/v3_processing_workflow.py`,
  `backend/services/billing.py` (each also carries pre-existing accepted
  working-tree changes from earlier sessions; the P6-2B-2 delta is the additive
  portion identified in §25 and the implementation report).
- P6-2B-2 files added: `backend/tests/unit/api/test_p6_2b_2_consultant_submission.py`,
  `docs/cline/CARBONTALLY_P6_2B_2_CONSULTANT_SUBMISSION_IMPLEMENTATION_REPORT.md`,
  and this verification report.
- No migration file was added or modified.
- Pre-existing dirty working-tree files (earlier accepted sessions) were preserved
  untouched. This gate performed **no commit, push, PR, or working-tree cleanup**.

## 27. Findings

### Blocking findings

None.

### Informational observations (non-blocking; no action taken)

- **F-1 — Shared TOCTOU / no write-side re-check (Races A–E).** Submission uses
  the application-wide unconditional `UPDATE ... WHERE id = $1` status transition
  with the state gate evaluated on the loaded snapshot. Race interleavings can
  only yield legitimate `consultant_reviewed` exits (`reviewed`, or rework
  `mapping`/`calculated`); D38/engagement/entitlement are not re-checked at write
  time. This is the established mechanism shared by all item transitions (also
  noted in the accepted P6-2B-1 gate) — not a new P6-2B-2 vulnerability.
- **F-2 — Shared flow exit usable by internal ops `submit-review`.** Because the
  state-machine exit `consultant_reviewed → reviewed` is global, an internal
  `can_review` staff member can now route a `consultant_reviewed` item to
  `reviewed` via the existing ops `submit-internal-review` route (previously 409).
  This is internal-staff-only, grants Consultants nothing, does not weaken any
  Consultant/QC/customer boundary (the item still needs the internal CT-QC
  decision), and matches internal staff authority over organisational work. It is
  documented here rather than changed (transition-granularity controls would be a
  larger architectural change outside this gate).
- **F-3 — Origin indistinguishability at CT-QC intake (deferred D7).** A
  consultant-submitted item enters the shared `reviewed` intake with no CONSULTANT
  origin marker, so the CT-QC queue cannot currently distinguish it from
  internally-reviewed work. This is the ratified provenance deferral (D7/P6-2D);
  the submission does not fabricate any origin claim. Expected, non-blocking.
- **F-4 — Entitlement granularity.** The D6 availability gate checks ACTIVE
  processing entitlement (subscription) presence only; STANDARD allowance / CREDIT
  balance sufficiency is enforced at the Customer-Approval charge
  (`charge_processing`), unchanged. The checks do not contradict the canonical
  commercial model (PO-D7); an entitled org with insufficient remaining credits can
  submit but cannot complete approval without payment, which is the existing
  charge-time behaviour. Non-blocking.

## 28. Recommendation to PO

Approve P6-2B-2 as verified. Independent evidence demonstrates: the existing
`reviewed` state is a safe and genuine CarbonTally QC intake state (no bypass to
Customer Review/Approval, no QC-authority grant, no Internal/PE semantic change);
submission requires `consultant_reviewed`, `can_submit=true`, active membership,
active engagement, server-derived scope, D38 clear, and an active client
processing entitlement; the check chain runs entirely before mutation; denials
are zero-mutation; submission never charges or consumes; the audit event is
correct and success-only; RLS/schema/database are unchanged and controlled; and
all dedicated, regression, and full-unit tests pass with no out-of-scope
implementation. P6-2B-3 and the D7 provenance workstream may proceed against this
verified foundation.

---

*End of independent verification report. Read-only gate: no code, migration, RLS,
schema, test, or data change was made; no commit, push, or PR was created.*







