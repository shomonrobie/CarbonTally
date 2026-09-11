# CarbonTally P6-2B-1 — Consultant Review State & Authorization — Independent Verification Report

- **Date:** 2026-09-06
- **Workstream:** P6-2B-1 (Consultant Review state/representation + server-side authorization)
- **Gate:** Independent verification (read-only). No fixes implemented; P6-2B-2 not started.
- **Git baseline:** branch `main`, HEAD `16391217103b98dcea520070c5a22c68f12fe607` (`1639121`) — unchanged by this gate.
- **Authorities:** Accepted P6-2B architecture
  (`docs/architecture/CARBONTALLY_P6_2B_CONSULTANT_REVIEW_QC_WORKFLOW_ARCHITECTURE.md`),
  P6-2A / P6-2A-R1 (accepted), frozen six-flag model (D1), P6-2B-D1 (self-review).

---

## 1. Final verdict

`P6-2B-1 VERIFICATION PASSED — READY FOR PO ACCEPTANCE`

No blocking finding was identified. Every P6-2B-1 acceptance condition (§28 of the
gate brief) is satisfied on the inspected runtime code, tests, database baseline,
and Git state. Only informational observations are recorded (§26). No defect was
repaired and no out-of-scope work was performed.

## 2. Verification scope

Verified independently (source inspection + read-only SQL + existing tests; the
implementation report was read but NOT relied on as proof):

1. Consultant Review state/representation in the canonical workflow state machine.
2. Consultant Review server-side authorization chain (identity → membership →
   engagement → server-derived resource scope → D38 conflict → workflow state →
   mutation).
3. Valid transition into Consultant Review (`calculated → consultant_reviewed`).
4. Consultant Review action endpoint/service/domain support.
5. Minimal Review failure/rework behaviour (`→ mapping`, existing state-machine
   semantics).
6. Review audit/event recording through existing infrastructure.
7. Security + regression tests (dedicated, P6-2A, P6-2A-R1, broad regression
   batch, full unit suite).
8. RLS/schema unchanged; database baseline unchanged; Git state.

**Out of scope (verified absent, not required):** Consultant→CT-QC submission,
`can_submit` enforcement, CT-QC workflow changes, billing/entitlement, firm/origin
provenance redesign, D38 schema changes, PE↔Consultant handoff, D39/D40, Customer
Approval redesign, UI.

## 3. Implementation inspected

### Files carrying the P6-2B-1 delta (repo-wide `P6-2B-1`/`consultant_reviewed`/`consultant-review` marker search)

- `backend/domain/partners.py` — additive item status `consultant_reviewed`
  (lines 27–29); `WORKFLOW_STAGE_STATUSES["review"]` includes
  `consultant_reviewed` (line 48); `ITEM_STATUS_FLOW`:
  `calculated → consultant_reviewed` (lines 76–82) and
  `consultant_reviewed → (mapping, calculated)` (line 88).
- `backend/api/consultant_auth.py` — `ensure_consultant_processing_authorized`
  `permission` parameter now `Optional[str] = None` (capability check is skipped
  only when `None`, lines 221, 314 — P6-2A permission call-sites unchanged); new
  canonical `ensure_consultant_review_authorized` (lines 344–382) which applies a
  consultant-capacity gate (internal/entity staff and org members → 403) and then
  reuses the canonical P6-2A resolver with `permission=None`.
- `backend/api/v3_processing_workflow.py` — `ConsultantReviewPayload` (lines
  472–483); `_audit_consultant_review` (lines 486–522);
  `POST /api/v3/processing/items/{item_id}/consultant-review` →
  `consultant_review_item` (lines 525–585).
- `backend/tests/unit/api/test_p6_2b_1_consultant_review.py` — new, 16 tests.
- `docs/cline/CARBONTALLY_P6_2B_1_CONSULTANT_REVIEW_IMPLEMENTATION_REPORT.md` — the
  implementation report (not used as evidence).
- This verification report.

### Code-path trace (runtime call path)

```
POST /api/v3/processing/items/{item_id}/consultant-review
  require_auth()                       → identity (401 if unauthenticated)
  load item   (item.batch_id)          → 404 if missing
  load batch  (batch.organization_id)  → 404 if missing
  ensure_consultant_review_authorized(user, repos, batch=..., item=...)
      ├─ internal staff / PE staff / org member  → 403 (consultant capacity only)
      └─ ensure_consultant_processing_authorized(permission=None, batch, item)
            ├─ _resolve_context → ACTIVE membership only (else 403)
            ├─ authoritative_org := server-derived batch.organization_id
            ├─ engagement: firm must hold ACTIVE consultant_clients row on org
            │   (else 403)  [pending/rejected/suspended/ended/inactive → 403]
            ├─ capability: skipped (permission=None) — NO can_submit / no flag
            ├─ resource-scope guard (no caller-supplied org accepted here)
            └─ D38 conflict: open item assignment OR batch carrier
                (entity_id / assigned_to) → 403 (unassigned → pass)
  workflow-state eligibility: item.status must equal 'calculated' (else 409)
  _require_transition(item, target)     → 409 if the state machine denies
  failure-without-reason check          → 422 (before mutation)
  repos.manual_extraction.set_item_status(item_id, target)   ← mutation
  _audit_consultant_review(...)         ← audit (best-effort, append-only)
```

No request-body `organization_id`, consultant ID, firm ID, or frontend role is
accepted or trusted anywhere on this route; the resource organization is always
derived from the loaded batch.

## 4. Workflow-state verification

- A distinct `consultant_reviewed` status exists in the canonical `ITEM_STATUSES`
  vocabulary and the shared `ITEM_STATUS_FLOW` state machine. It does not reuse,
  and is unambiguous against, internal `review`/`reviewed`, PE review/QC
  (`pe_review*`, `pe_qc*`), CarbonTally QC (`ct_qc*`), Customer Review
  (`customer_review`), or `approved`.
- The review completion status appears in `WORKFLOW_STAGE_STATUSES["review"]`
  (alongside legacy `customer_review`), so stage grouping/dashboards remain
  canonical; no new workflow stage was invented.
- Transition integration is via `can_transition_item_status` /
  `_require_transition` used by the endpoint, not a UI-only check.
- Internal (`… → calculated → review → reviewed → ct_qc → ct_qc_approved →
  customer_review → approved`) and PE (`… → pe_review → … → ct_qc_approved →
  customer_review → approved`) canonical paths are untouched in `ITEM_STATUS_FLOW`.
- Data preservation: no migration, no data change, no existing status re-mapped;
  the status vocabulary column is free-varchar (no CHECK constraint on statuses),
  so the addition is pure domain vocabulary.

| State | Entry From | Exit To | Authorized Actors |
| ----- | ---------- | ------- | ----------------- |
| `consultant_reviewed` | `calculated` (endpoint requires exactly `calculated`; server-side 409 otherwise) | `mapping` (Review-fail rework) or `calculated` (ops rework reset); **no** path to `ct_qc_*`, `customer_review`, `approved`, or `reviewed` | **Entry:** an active Consultant firm member with an active engagement on the server-derived client org and no open D38 effective assignment (self-review allowed per P6-2B-D1). **Exits:** the existing shared-workflow rework actors (internal staff / organisation members claiming the `mapping` stage) — the canonical state machine; P6-2B-2 adds the submit action. |

## 5. Authorization-chain verification

The expected chain is implemented server-side and verified in code:

**authenticated identity → active Consultant membership → active engagement →
server-derived resource scope → D38 effective-assignment check → valid workflow
state → Review mutation.**

- **Not trusted:** request-body organization/Consultant/firm ID (none exist on the
  payload — only `passed`, `rejection_reason`, `consultant_notes`); frontend role;
  frontend permission state.
- `_resolve_context` resolves only ACTIVE `consultant_firm_members` rows and
  requires a single distinct active firm; zero or ambiguous memberships never
  resolve (deny, never guess).
- The authoritative org is `batch.organization_id`, reached through
  `item.batch_id` — i.e., derived from the server-loaded resource.
- The active client grant is checked per request against the authoritative org via
  `repos.consultants.get_client_by_org`.
- Workflow state is checked inside the endpoint after authorization and before any
  mutation.

## 6. Canonical resolver verification

P6-2B-1 **reuses** the established P6-2A foundation. `ensure_consultant_review_authorized`
calls `ensure_consultant_processing_authorized(... permission=None)` with the
server-loaded `batch`/`item`. All five axes of the canonical chain
(actor-class/membership/engagement/resource-scope/D38) are therefore enforced
through the same code path that P6-2A uses for extract/map/validate/calculate.
No parallel or second authorization implementation was introduced.

The only P6-2A surface change is the `permission` parameter becoming optional;
the capability check (`ensure_consultant_permission`) still runs whenever a
permission is supplied. All existing P6-2A call-sites pass a concrete permission
(`extract`, `map`, `validate`, `calculate`, and `confirm_automation` in the
automatic-processing confirm/retry paths), so P6-2A capability enforcement is
unchanged (verified by the passing P6-2A/P6-2A-R1 suites, §22).

## 7. Self-review verification

Ratified P6-2B-D1 is honored. There is no "different human" rule anywhere in the
route or resolver. The dedicated test seeds the processing consultant as
`extracted_by` on the item and proves the same member can review it successfully
(`test_consultant_self_review_allowed`, PASS). Self-review still passes through
the full authorization controls (membership, engagement, server scope, D38,
workflow state) — readiness control only; independent assurance remains CarbonTally
QC (not implemented in this gate).

## 8. Capability separation

- There is **no seventh `can_review` flag**. The P6-2A migration adds exactly six
  processing capability columns (`can_extract`, `can_map`, `can_validate`,
  `can_calculate`, `can_confirm_automation`, `can_submit`) — confirmed in
  `supabase/migrations/20260906100000_p6_2a_consultant_processing_permissions.sql`.
- `can_submit` is **not required** for Review: the positive test
  `test_consultant_review_pass_does_not_require_can_submit` asserts the member has
  `can_submit is False` and the Review returns 200.
- Review **does not set or activate** `can_submit` (repo-wide search: the flag is
  only read/constructed with a `False` default; no code path writes `true`).
- Review **does not invoke submission logic** and **does not enter CT-QC**: the
  only status targets are `consultant_reviewed` (pass) and `mapping` (rework).
  The working-tree state of the six-flag columns is verified §23 (0 members with
  any processing flag true).

## 9. Membership/engagement verification

Enforced at request time, per request (not cached), through `_resolve_context`
(active rows only) and the per-request `get_client_by_org` + `status == "active"`
check. Test evidence (dedicated suite, all DENY with status preserved):

| Condition | Expected | Verified |
| -------- | -------- | -------- |
| Active membership + active engagement | ALLOW | `test_consultant_review_pass_does_not_require_can_submit`, `test_consultant_self_review_allowed` |
| Inactive membership | DENY | `test_inactive_membership_denied` (403) |
| Pending engagement | DENY | `test_non_active_engagements_deny_review` (403) |
| Rejected engagement | DENY | same (403) |
| Suspended engagement | DENY | same (403) |
| Ended engagement | DENY | same (403) |
| Inactive engagement | DENY | same (403) |

## 10. Cross-scope verification

Server-authoritative isolation verified by test and code trace:

- Cross-firm / cross-client: `test_cross_firm_and_cross_client_denied` (403) — a
  firm without an active grant on the item's org cannot review it.
- Unknown item → 404 (`test_unknown_item_404`); unauthenticated → 401
  (`test_unauthenticated_denied`).
- Forged organization ID: **no such vector exists** — the route accepts no
  organization ID in the body/query; the org is always the loaded batch's org.
- Forged Consultant/firm ID: identity is derived from the authenticated token and
  membership rows only; the request cannot supply a profile/firm/member ID.

## 11. D38 verification

All four required cases verified in code and tests (dedicated suite):

| Case | Expected | Verified |
| ---- | -------- | -------- |
| Item assignment — internal-staff effective assignment | DENY | `test_open_internal_and_pe_assignment_deny_review` (403) |
| Item assignment — PE effective assignment | DENY | same (403) |
| Batch default — internal-staff (`assigned_to`) | DENY | `test_batch_default_assignment_denies_review` (403) |
| Batch default — PE (`entity_id`) | DENY | same (403) |
| Unassigned (no effective assignment) | ALLOW | positive tests (items/batches seeded without assignment) |

Additional confirmations:

- No `consultant` D38 assignee kind exists: `work_item_assignments.assignee_kind`
  CHECK constraint allows only `('internal_staff', 'processing_entity')`
  (`supabase/migrations/20260902030000_phase5_work_item_assignments.sql`).
- No D38 schema change and no new migration in this workstream (repo-wide search
  for P6-2B migrations: none; migration directory ends at the P6-1C/P6-2A files).
- No PE↔Consultant handoff mechanism was introduced; the D38 deny is fail-closed.

## 12. Workflow-state enforcement

Server-side only. The endpoint loads the item and requires
`item.status == "calculated"` before any mutation; every other status — including
`extracting`, `mapping`, `mapped`, `validating`, `validated`, `calculating`,
`ct_qc*`, `customer_review`, `approved` — returns 409. `_require_transition` then
re-checks the canonical `ITEM_STATUS_FLOW` for the chosen target. Test evidence:
`test_invalid_workflow_state_denied` (extracting/mapped/validated → 409) and
`test_already_reviewed_item_cannot_be_reviewed_again` (re-review from
`consultant_reviewed` → 409). No frontend-only state check exists.

## 13. Authorization-before-mutation

Control-flow inspection of `consultant_review_item`:

1. Load item/batch (read-only) — 404 paths.
2. `ensure_consultant_review_authorized(...)` — **authorization**.
3. `item.status != "calculated"` → 409 (state gate).
4. `_require_transition(item, target)` → 409 (state machine, read-only).
5. Missing `rejection_reason` on fail → 422 (read-only).
6. `set_item_status(item_id, target)` — **the only workflow-state mutation**,
   reached only after steps 2–5.
7. `_audit_consultant_review(...)` — audit insertion after a successful mutation
   only (best-effort; never breaks the review).

Authorization therefore precedes every persistent side effect (state mutation,
review result, audit, and there is no notification side effect on this route).

## 14. Zero-mutation denial

Denials raise HTTPException **before** `set_item_status` and before the audit
helper, so no business mutation occurs. Dedicated tests assert the item status is
unchanged after each important denial class:

- non-consultant org member → 403, status unchanged;
- inactive membership → 403 (no mutation reachable);
- pending/rejected/suspended/ended/inactive engagement → 403, status unchanged;
- cross-firm / cross-client → 403;
- D38 conflict (item and batch default) → 403, status unchanged;
- invalid workflow state → 409, status unchanged;
- re-review of a reviewed item → 409, status unchanged;
- missing rejection reason → 422, status unchanged;
- CT-QC and Customer-Approval attempts → 403.

No Review audit event is produced on any denial (audit is called only after a
successful mutation). `_actions(...)` assertions confirm audit entries appear only
for the pass/rework success paths.

## 15. Review/rework semantics

- **Review passed** (`passed=True`): the processed item is recorded as
  `consultant_reviewed` — a readiness/completeness representation distinct from
  CarbonTally QC and Customer Approval, explicitly leaving the item ready for the
  future P6-2B-2 `can_submit` action.
- **Review failed** (`passed=False`): the item is routed to the **existing**
  canonical rework state `mapping` (a transition already permitted from
  `calculated` in the pre-existing state machine). No new rejection status or new
  rework engine was introduced; CT-QC rejection/rework is not expected here and is
  absent. A `rejection_reason` is mandatory for a failed review (422 otherwise).

## 16. QC boundary

Consultants cannot create, approve, or reject any CarbonTally QC outcome:

- The CT-QC decision route
  (`POST /api/v3/ops/qc/items/{item_id}/decision`, `v3_operations.py`) requires
  `require_staff` → `require_internal_staff` + `ensure_staff_permission("can_qc")`.
- The new Review route never calls QC mutation logic and cannot reach a QC state
  (`consultant_reviewed`/`mapping` only).
- Negative test `test_consultant_cannot_reach_ct_qc` → 403.
- Existing CarbonTally QC authorization is unchanged (no edits to `v3_operations.py`
  in this delta; CT-QC queue/decision code untouched).

## 17. Customer Review / Approval boundary

- Customer approval remains org Owner/Admin only: the customer-review route uses
  `require_org_admin()`. Consultants are not org members/admins → denied.
- Negative test `test_consultant_cannot_reach_customer_approval` → 403.
- The new Review route can never transition an item to `customer_review` or
  `approved`: its targets are only `consultant_reviewed`/`mapping`, and the
  state machine grants no path from `consultant_reviewed` to `approved`.
- **No newly reachable approval bypass was introduced.** The previously identified
  latent `calculated → approved` map entry remains (reachable only by a customer
  org Owner/Admin through the org-gated customer-review surface — not by
  consultants) and is a later hardening item (P6-2C), not a P6-2B-1 regression.

## 18. Audit verification

`_audit_consultant_review` records through the existing append-only
`repos.audit.record` (`audit_trail` table) using the canonical `AuditEntry`:

- actor = authenticated human `current_user.user_id`;
- action = `consultant.review:passed` / `consultant.review:rework`;
- resource = `entity_type="manual_extraction_item"`, `entity_id=item_id`;
- before/after = `{"status": from}` / `{"status": to}`;
- `changed_fields` carries `status_from`, `status_to`, `consultant_notes`,
  `rejection_reason`;
- timestamp = `occurred_at` (UTC);
- correlation/request identifier = `correlation_id=item_id`.

No new firm/origin provenance fields were added (deferred to the approved
provenance workstream), which is within scope. Informational: the audit uses the
existing best-effort pattern (`try/except` — an audit failure never breaks the
review) and does not add a separate request-scoped correlation UUID or a
client-org column; both are consistent with the existing infrastructure contract.

## 19. RLS verification

- **No migration was added by P6-2B-1** (repo-wide search and migration-directory
  inspection: last files are the P6-1C and P6-2A migrations). The schema therefore
  remained unchanged.
- Read-only `pg_policies` inspection for `manual_extraction_items`,
  `manual_extraction_batches`, `consultant_clients`, `consultant_firm_members`,
  `consultant_profiles`, `work_item_assignments` shows **no broad authenticated
  write policy and no consultant-wide write**:
  - `manual_extraction_items`: no UPDATE/INSERT policy for `authenticated` at all
    (only entity-scoped SELECT) — item status writes are API-only;
  - `manual_extraction_batches`: tenant UPDATE is `is_org_member(...)` gated
    (consultants cannot mutate batches via PostgREST);
  - `consultant_firm_members`: UPDATE is self-only (`user_id = auth.uid()`);
  - `consultant_clients`: DELETE gated by revoker/admin functions; SELECT via
    firm/tenant helpers; no consultant UPDATE policy.
- No direct PostgREST mutation path exists that would bypass the API authorization
  verified in §5–§13 (the FastAPI route remains the item-status mutation boundary).

## 20. Concurrency assessment

`set_item_status` is a plain `UPDATE ... WHERE id = $1` with no
`WHERE status = <expected>` condition and no row lock — the same mechanism every
other item transition in the application uses. The endpoint therefore has the same
TOCTOU window as all existing transitions:

1. Two Consultants review simultaneously → both may read `calculated`; the final
   state is one of the two legitimate review outcomes (`consultant_reviewed` or
   `mapping`), both of which are valid from `calculated`. A duplicated audit entry
   is the only plausible side effect (benign).
2. State changes between authorization and commit → last-writer-wins, as across the
   rest of the workflow surface.
3. A D38 assignment appearing between authorization and commit, or an engagement
   ending in that window, is not re-checked at write time (same shared pattern).

Per the gate instructions no new locking was introduced. Because this is the
established application-wide transition mechanism — not a class of race newly
created by P6-2B-1 — this is recorded as an **informational observation**
(§26, F-1), not a blocking finding.

## 21. Non-Consultant regression

The new route and helper explicitly deny non-Consultant capacities:
`ensure_consultant_review_authorized` returns 403 for CarbonTally internal staff,
Processing Entity staff, and organisation members, so Consultant Review cannot
become a general processing-authorization mechanism. Existing behaviour for
internal staff, PE users and customer users is exercised by the passing regression
set (§22): operations auth, PE auth, scope-aware authorization, QC, processing
workflow, customer review/approval paths (phase-1 core regressions), automatic
processing, D38 effective-assignment and P6-1B/P6-1C suites. Full unit suite
passes.

## 22. Test results

All runs executed against the existing tests without modification.

| Suite | Command | Result |
| ----- | ------- | ------ |
| P6-2B-1 dedicated | `pytest tests/unit/api/test_p6_2b_1_consultant_review.py -q` | **EXIT 0** — 16 passed |
| P6-2A + P6-2A-R1 | `pytest tests/unit/api/test_p6_2a_consultant_processing_authorization.py tests/unit/api/test_p6_2a_r1_b1_automation_confirm_retry.py -q` | **EXIT 0** — 18 + 14 passed |
| Broad regression batch (18 suites: P6-1B, P6-1C, D38 effective assignment, operations auth, scope-aware auth, PE auth, v3 QC, processing-origin/QC, processing workflow, D19 lifecycle, phase-1 core regressions, automatic-processing jobs/payload/services, automatic extraction, Gate-4 remediation actor provenance, audit immutability, consultant branding) | `pytest -q …` (18 files) | **EXIT 0** — 217 passed |
| Full unit suite | `pytest tests/unit -q` | **EXIT 0** — ~1,509–1,510 collected, 0 failures/errors |

No test was modified, skipped, or deselected.

## 23. Database baseline

Read-only SQL against the local investor demo database (127.0.0.1:54426,
`carbon_ledger`). All expected baseline values confirmed **unchanged**:

| Baseline item | Expected | Verified |
| ------------- | -------- | -------- |
| `organizations` | 975 | 975 |
| `consultant_firm_members` | 54 | 54 |
| `consultant_profiles` | 55 | 55 |
| `consultant_clients` | 917 | 917 |
| `manual_extraction_items` | 260 | 260 (status distribution sum = 260) |
| `work_item_assignments` | 0 | 0 |
| `billing_plans` | 6 | 6 |
| `customer_subscriptions` | 0 | 0 |
| `billing_orders` | 0 | 0 |
| `billing_credit_ledger` | 0 | 0 |
| Members with any of the six processing flags true | 0 | 0 |
| Items in status `consultant_reviewed` | 0 (no data change) | 0 |

Item status distribution observed (no `consultant_reviewed`, no new
state-induced count change): `pending 160, approved 30, extracted 28,
calculated 14, mapped 12, validated 10, rejected 3, extracting 2, qc_approved 1`.

## 24. Scope-containment audit

Explicitly verified **not implemented** by this workstream (code + repo-wide
marker search + tests):

- Consultant submission / submit action — absent (no route; `consultant_reviewed`
  is a terminal representation until P6-2B-2);
- `can_submit` action enforcement — absent (`can_submit` not referenced by the
  route, not granted, not activated);
- CarbonTally QC workflow changes — absent (CT-QC route/queue code untouched);
- Billing / entitlement — absent (no billing code in the delta; D6 deferred);
- Consultant firm/origin provenance — absent (no schema change; provenance
  deferred to P6-2D);
- D38 schema change — absent (no migration; assignee-kind vocabulary unchanged);
- PE↔Consultant handoff — absent (fail-closed D38 deny preserved);
- D39 / D40 — absent;
- Customer Approval redesign — absent (approval remains org Owner/Admin);
- UI — absent (no frontend change in this delta);
- No seventh permission flag (`can_review`) — absent.

## 25. Git state

- Branch: `main`; **HEAD unchanged: `1639121` (`16391217103b98dcea520070c5a22c68f12fe607`)**.
- P6-2B-1 files changed (`git status --porcelain`):
  - modified: `backend/domain/partners.py`, `backend/api/consultant_auth.py`,
    `backend/api/v3_processing_workflow.py`;
  - new (untracked): `backend/tests/unit/api/test_p6_2b_1_consultant_review.py`,
    `docs/cline/CARBONTALLY_P6_2B_1_CONSULTANT_REVIEW_IMPLEMENTATION_REPORT.md`,
    and this verification report.
- No P6-2B-1 migration exists (and none is required — free-varchar status
  vocabulary; no CHECK constraint on item statuses).
- Pre-existing dirty working-tree files (from earlier accepted sessions — P6-2A/
  P6-2A-R1, V1.2, D20–D37, skills/agent-tooling moves, etc.; 284 modified, 152
  deleted, 206 untracked at gate start) remain untouched by this verification.
- This gate performed **no commit, push, PR, or working-tree cleanup**; it added
  only the single required report file.

## 26. Findings

### Blocking findings

None.

### Informational observations (non-blocking; no action taken)

- **F-1 — Shared transition TOCTOU (concurrency).** `set_item_status` performs an
  unconditional `UPDATE` by id (no old-status predicate, no row lock), so a Review
  racing another transition can pass the `calculated` gate on a stale read. End
  states remain legitimate (`consultant_reviewed`/`mapping`); the pattern is the
  application-wide transition mechanism and is not new to P6-2B-1. Locking was
  intentionally not introduced. Candidate future hardening: conditional
  `UPDATE … WHERE status = 'calculated'` (P6-2B-3+ territory).
- **F-2 — Stage-bucket representation nuance.** `consultant_reviewed` is grouped
  under `WORKFLOW_STAGE_STATUSES["review"]`, so consultant-reviewed items appear in
  the client org's own `review` stage queue/dashboard grouping. No mutation is
  possible on this state from those surfaces (the state machine limits exits to
  `mapping`/`calculated`, and the review route requires `calculated`); PE and
  internal dashboards are unaffected because D38 forbids consultant work on their
  batches. Representation choice, not a security/architecture defect.
- **F-3 — Audit correlation granularity.** Review audit uses the existing
  `repos.audit.record` contract with `correlation_id = item_id` and no separate
  client-org field or request-scoped UUID. This mirrors the existing fallback
  pattern and the scope explicitly defers provenance fields; flagged only for
  completeness.

## 27. Recommendation to PO

Approve P6-2B-1 as verified. The implementation satisfies the ratified P6-2B-1
scope: Consultant Review is correctly represented in the canonical workflow,
authorization is fully server-side and reuses the P6-2A canonical resolver,
self-review works as ratified, `can_submit` is neither required nor activated,
denials are zero-mutation, CT-QC and Customer Approval boundaries are preserved,
RLS/schema and the database baseline are unchanged, the full unit suite and all
targeted regression suites pass, and no out-of-scope implementation was
introduced. P6-2B-2 may now be defined against this verified foundation.

---

*End of independent verification report. Read-only gate: no code, migration, RLS,
schema, test, or data change was made; no commit, push, or PR was created.*





