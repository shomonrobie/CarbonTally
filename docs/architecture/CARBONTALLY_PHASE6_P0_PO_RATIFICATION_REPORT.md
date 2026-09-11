# CarbonTally Phase 6 — P6-0 — PO Policy Ratification Report

- **Date:** 4 September 2026
- **Task type:** Policy ratification review only (read-only). No code, schema,
  migration, RLS, API, UI, workflow, D38/D39/D40, consultant tables,
  permissions, invitations or billing was modified; no fixtures created; no
  data mutated; nothing committed or pushed.
- **Reviewed against:** CarbonTally Final Architecture Blueprint v1.2
  (ARCHITECTURE FREEZE), the Phase 6 readiness report
  (`CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md`), the current
  consultant implementation, live schema, RLS, authorization helpers, D38/D39/
  D40 and Gate 4/5/6 mechanisms.

---

## 1. D-1 — Consultant invitation & provisioning — compatibility assessment

**Compatible — APPROVED.** No contradiction with the frozen architecture.

- Existing foundations match the ratified model: `user_invitations`
  (email/role/org/token/status/expiry), `consultant_firm_members` invite/join
  stamps (`invited_by`, `invited_at`, `joined_at`, `is_active`), and the
  RLS/authorization chain already requires an **active firm membership** before
  any consultant capability resolves (`require_consultant`).
- The open self-service points that D-1 closes are `POST /consultant/me`
  (any authenticated user may create a profile) and `POST /me/team`
  (a `can_manage_team` member may add an arbitrary existing `user_id` with no
  invitation token). Replacing these with an invitation-based flow is additive
  API/schema work, not an architecture change.
- Important existing safety property (preserved): a profile alone grants no
  client access — org access still requires the active `consultant_clients`
  grant plus permission flags. Invitation gating therefore bounds membership
  creation without changing the trust chain.
- Implementation dependency: `add_firm_member` currently records the role only
  (the four `can_*` columns default to FALSE and are never set by any endpoint),
  and there is no permission-administration endpoint. D-1's "the inviter must be
  authorized to grant the selected permissions" therefore requires a new
  authorized permission-grant surface (firm admin with `can_manage_team`; CT
  override) plus a no-self-elevation guard.

## 2. D-2 / D-2b — Work-access model — compatibility assessment

**Compatible — APPROVED (Model C + PE-assigned-item block).**

- Model C matches the existing authorization chain exactly:
  identity → firm → **active client grant** → resource → action, where
  `ensure_consultant_org_access` / `_authorized_client_org` already enforce the
  active grant per organisation and RLS mirrors it (`is_org_consultant`).
- Resource-scoped reads the consultant already has (client documents, items,
  batches, reports, evidence, issues) all go through grant-authorized endpoints.
- D-2b (no PE-assigned items) is implementable without touching D38: the
  effective-assignment resolution already exists (item → batch default →
  unassigned; `assignee_kind` = internal_staff | processing_entity). Consultant
  processing endpoints simply consult the same effective-assignment view and
  deny when a PE assignment is effective. D38 remains authoritative; no new
  assignee kind is required for the D-2b block.

## 3. D-3 — Consultant processing capability matrix — compatibility assessment

**Compatible — APPROVED with the matrix.**

- Verified: `consultant_firm_members` currently carries only
  `can_manage_clients` / `can_upload_documents` / `can_generate_reports` /
  `can_manage_team`. The D-3 flags (`can_extract`, `can_map`, `can_validate`,
  `can_calculate`, `can_review`, `can_submit`) **do not exist yet** on the
  consultant surface (the `can_extract`/`can_review` found in code are the
  *internal staff* vocabulary in `domain/staff.py`/ops routers). D-3 is an
  additive extension of the existing flag model — an implementation detail
  (boolean columns or role-defaults via the existing `role_id`/`permissions`
  JSON), not an architecture change.
- Calculation uses the existing deterministic engine (no consultant engine);
  AI stays non-authoritative under Gate 5; consultant actions are human
  provenance (Gate 4/6). All consistent with the frozen mechanisms.

## 4. D-4 — Customer approval boundary — compatibility assessment

**Compatible — APPROVED.**

- The final customer approval on automatic jobs already requires
  `require_org_admin` (org owner/admin). A consultant is not an
  `organization_members` row and cannot satisfy that dependency, so the
  boundary is enforced by the existing code today. D-4 adds the consultant-side
  "submit for customer review" capability and keeps approval exclusively
  customer-authority; both are additive and consistent.

## 5. D-5 — PE ↔ Consultant hand-off — compatibility assessment

**Compatible — APPROVED with the hand-off rules.**

- PE/Consultant are separate trust domains in the implementation (separate
  tables, separate `require_*` dependencies, separate routers). The D38
  assignment service and ledger already centralise assignment/reassignment in
  Operations; Rule 5 (consultant requests → Operations assigns → D38 records)
  reuses that service. Rules 2–4 and 6–8 are workflow/provenance rules that the
  existing provenance and D39 infrastructure can represent; no new trust
  surface is required.

## 6. D-6 — Consultant conversations — compatibility assessment

**Compatible — APPROVED (reuse D39).**

- `domain/messaging.py` already documents and the RLS storey enforces: org
  members participate; consultants participate only through an active
  `consultant_clients` grant for that org; PE staff never participate in
  org/customer conversations. `conversations.conversation_kind`,
  `processing_entity_id` and participant metadata already exist. The four
  recommended consultant categories (org/client, work-item/issue, Operations
  coordination, controlled PE coordination) map onto the existing
  conversations model — no new messaging system and no unrestricted
  Consultant↔PE channel.

## 7. D-6b — Consultant notifications — compatibility assessment

**Compatible — APPROVED (reuse D40).**

- `notifications` supports `recipient_type='user'`/`recipient_id`, `event_key`
  idempotency, `actor_domain`, unread/read, and authorization-on-open. Targets
  are per-user; a producer that checks the active grant at send time satisfies
  "revocation stops future notifications" and the no-leakage rule. Event
  vocabulary for consultants is additive (free-form `notification_type`), no
  schema redesign.

## 8. D-7 — Billing / credit ownership — compatibility assessment

**Compatible — APPROVED (client organisation owns entitlement).**

- All consultant-performed work is organisation-scoped today: consultant uploads
  call `create_document_and_enqueue(organization_id=client_org, ...)`, and jobs,
  items, batches, snapshots and emissions logs all key on the client
  organisation id. Client-owned entitlement/consumption is therefore the
  natural and existing scope — no consultant plan or per-consultant credit
  transfer is needed for client work.
- Implementation dependency/guard: confirm during P6-3 that any billing/credit
  metering hooks consume the **organisation** context (not the actor's own
  plan). If an integration gap is found (e.g. metering keyed to the uploader's
  subscription), it must be documented before implementation per D-7.
- `consultant_billing`/`consultant_clients.billing_plan` remain firm/client
  commercial display data and are not authorization inputs.


## 9. Consolidated policy matrix

The ratified matrix in the policy brief (§11) is technically compatible with
the current implementation. Notes:

- "✓" rows that already exist today: view client work/documents, upload
  documents (→ automatic pipeline), reports/evidence/issues (grant-scoped).
- Rows requiring new consultant capability flags (D-3): extract, map, validate,
  calculate, review, submit — none exist on the consultant surface yet.
- Rows that must remain denied: final customer approval, PE assignment/
  reassignment/release, PE QC, CarbonTally QC, org/billing/user administration,
  cross-client access, arbitrary work claiming.
- Critical interpretation is preserved: every operation stays gated by
  identity + org/client scope + resource + action permission + workflow state +
  assignment/security policy (this is the existing authorization-chain
  discipline, not a new concept).

## 10. Security invariant assessment (C-SEC-001 … C-SEC-012)

| Invariant | Existing control | Assessment |
|---|---|---|
| C-SEC-001 no client access without active grant | `ensure_consultant_org_access` + `is_org_consultant` RLS | Already enforced |
| C-SEC-002 no cross-client IDOR | `_checked_client`/`_authorized_client_org` (firm ownership + active status) | Already enforced; keep for all new routes |
| C-SEC-003 no PE-assigned item operation | Effective-assignment view (D38) exists; consultant check to be added | Implementation (P6-2) |
| C-SEC-004 no PE assign/reassign/release by consultant | D38 assignment service is Operations-scoped | Already enforced; consultants have no D38 route |
| C-SEC-005 no final customer approval by consultant | `require_org_admin` on approval; consultant has no org membership | Already enforced |
| C-SEC-006 no CT QC by consultant | CT QC uses `require_staff`; consultant context ≠ staff | Already enforced |
| C-SEC-007 no unrelated conversations | Participation + org/consultant RLS storey | Already enforced (D39) |
| C-SEC-008 notifications authorization-scoped | Per-recipient rows; producers must check active grant | Implementation discipline (P6-5) |
| C-SEC-009 actor from authenticated identity | All actor fields from `current_user`/context | Already enforced |
| C-SEC-010 Gate-5/6 provenance immutable | Write-once automation columns/trigger; G6-A preserved output; G6-D markers | Already enforced; applies to consultant edits via shared paths |
| C-SEC-011 no D38 bypass | D38 service + conflict rule | Implementation (P6-2/D-2b) |
| C-SEC-012 revocation immediately blocks access | Active-grant + `is_active` member checked per request | Already enforced |

## 11. Architecture contradictions, if any

**None found.** Every ratified decision D-1…D-7 fits Blueprint v1.2 and the
current implementation without weakening a frozen trust boundary. Two
near-misses recorded as implementation guards (not contradictions):

1. `add_client` (firm admin linking a pre-existing organisation) is gated only
   by `can_manage_clients`, not by customer-side/CT confirmation. This is
   consistent with the consultant-owned-customer model (PO Decision 3 / CON-1)
   but must be surfaced in audit and remain severable (D19 lifecycle). No
   policy change required.
2. Open `POST /me` and `POST /me/team` self-provisioning — the exact behaviour
   D-1 closes. Confirmed as the intended change, not a frozen behaviour.


## 12. Implementation dependencies

- Authorized permission-grant surface (firm admin `can_manage_team` / CT
  override) + no-self-elevation guard (D-1/D-3).
- Invitation record/flow for consultant firm membership (accept/expiry/
  re-invite/revoke); additive, reusing `user_invitations` patterns.
- D-3 capability flags (columns or role→permission defaults) on the consultant
  surface.
- Model-C resource/stage guards incl. the D-2b effective-PE-assignment check
  in consultant processing routes.
- Consultant processing routes reusing shared engines/repositories with
  Gate-4/6 actor + audit semantics and G6-D confirm/resume handling.
- Submit-for-review capability and audit separation from customer approval.
- D39 conversation participation wiring for consultants (participants derived
  from active grant) and D40 consultant event producers (active-grant check at
  send time).
- Billing/credit metering verified as organisation-scoped during P6-3.

## 13. Unresolved decisions, if any

No material (architecture/trust/ownership/authorization/commercial) decision
remains. Minor, non-architectural clarifications to resolve during
implementation:

1. 7-day invitation expiry — fixed constant vs configurable setting.
2. Which CT role may provision/revoke firm invitations and engagements
   (Operations staff vs Staff Admin) and whether provisioning reuses the
   consultant endpoints or an internal surface.
3. Whether linking a **pre-existing** organisation as a new client requires
   customer-side or CT confirmation (recommended guard: log + severable grant;
   no hard confirmation required for consultant-created customers).
4. D-3 flags implemented as boolean columns vs role→permission defaults
   (`permissions` JSON / `role_id`).
5. Exact D-6b consultant `notification_type` event vocabulary.

None of these change the authorization/ownership model; each is resolved inside
the P6-1…P6-6 workstreams.

## 14. Recommended implementation sequence

1. **P6-1 Provisioning/invitation (D-1)** — gate profile/member creation behind
   invitations; permission-grant surface; 7-day expiry; no self-elevation.
2. **P6-2 Authorization contract (D-2/D-2b/D-3)** — Model C scope guards,
   D-3 capability flags + checks, PE-assigned-item block, provenance actor
   model for consultant actions.
3. **P6-3 Processing actions** — extract/map/validate/calculate via shared
   engines; confirm/resume with G6-D safeguards; org-scoped billing/credit
   verification.
4. **P6-4 Submit/review boundary (D-4)** — consultant submit/recommend; final
   approval stays org owner/admin.
5. **P6-5 Conversations + notifications (D-6/D-6b)** — D39/D40 reuse.
6. **P6-6 UI + E2E/security acceptance** — `/consultant` processing views
   (D19/D21) and the full C-SEC negative matrix.

---

## Final verdict

**PHASE 6 POLICY RATIFIED — IMPLEMENTATION READY**

All ratified decisions D-1…D-7 are technically compatible with the frozen
architecture and current implementation; no material architecture, trust,
ownership, authorization, approval, PE-boundary or commercial decision remains
open (only minor, non-architectural implementation clarifications listed in
§13). STOPPED — no implementation performed; the PO will authorise P6-1,
P6-2, P6-3… individually.

