# CarbonTally P6-2-PO — Consultant Processing Workflow — PO Decision Register

- **Date:** 2026-09-06
- **Status:** Read-only decision register. **No implementation.**
- **Source artifact:** `docs/architecture/CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md`
  (613 lines; architecture gate verdict **READY WITH PO DECISIONS**).
- **Purpose:** reproduce P6-2-D1…D11 exactly as documented (question, evidence,
  options, recommendation, consequences, dependencies) so the PO can ratify or
  modify each decision. No decision is presumed ratified by this table.
- **P6-2C amendment (10 September 2026):** the PO has **ratified** the three
  P6-2C blocking decisions. They are recorded in
  **`## P6-2C Ratified PO Decisions — 2026-09-10`** below as
  **PO-P6-2C-D1/D2/D3-20260910**. Those three entries **are** authoritative PO
  decisions; the D1–D11 rows above remain **register recommendations only**.
- **P6-2D amendment (10 September 2026):** the PO has **withdrawn** the proposed
  `CONSULTANT` `processing_origin` value (**D7b**). It is recorded in
  **`## P6-2D Ratified PO Decision — 2026-09-10`** below as
  **`PO-P6-2D-D7b-R-20260910`** (decision: **WITHDRAWN / REJECTED AS PROPOSED**).
  That entry is an authoritative PO decision; **no implementation** of it is
  required or permitted (see the entry's implementation status). The D7 row above
  carries a framing clarification (firm provenance, not `processing_origin`) and
  remains a **pending** PO decision.
- **Ground rules preserved from the source artifact:**
  - Consultant must never perform Customer Approval.
  - Client organisation owns processing entitlement.
  - Consultants are not automatically D38 assignees.
  - No new workflow state is proposed except where the source artifact
    explicitly recommends one (`consultant_review` is a **recommendation**, not
    a ratified state).
  - Existing permission terminology preserved: `can_manage_clients`,
    `can_upload_documents`, `can_generate_reports`, `can_manage_team`
    (consultant_firm_members); no new flags invented beyond the source
    artifact's candidate list under D1.

---

## P6-2-D1 — Consultant Processing Capability Flags

- **Question:** Which processing actions become real consultant capabilities,
  and which permission flags gate them (candidate flags named in the source
  artifact: `can_extract`, `can_map`, `can_validate`, `can_calculate`,
  `can_confirm_automation`, `can_submit`)?
- **Current implementation / evidence:** Only four relationship permission
  flags exist on `consultant_firm_members` (`can_manage_clients`,
  `can_upload_documents`, `can_generate_reports`, `can_manage_team`). The shared
  `/api/v3/processing/*` surface already admits active-grant consultants to
  extract/map/validate/calculate **without any processing flag** — inconsistent
  with the P6-1B permission model (Gap G2).
- **Documented options:**
  - (a) Add additive flag columns and gate every action.
  - (b) Gate actions on engagement + role only; no new flags.
  - (c) Hybrid — flags for destructive/submit actions only.
- **Recommended option:** (a) — additive flags gating every action, matching the
  P6-1B permission model.
- **Consequences:** schema columns, permission map (`CONSULTANT_PERMISSIONS`),
  negative tests.
- **Dependencies:** feeds P6-2A (consultant action authorization).

## P6-2-D2 — Consultant Processing Organization / Engagement Scope

- **Question:** Which organisation relationships may a consultant process —
  Case A (consultant-created customers), Case B (pre-existing organisations that
  accepted the engagement), and legacy rows; i.e., all active-grant orgs?
- **Current implementation / evidence:** P6-1C unified the active-grant
  boundary across all `relationship_origin` values
  (`legacy` / `consultant_created_customer` / `engagement_request`). Only
  `consultant_clients.status = 'active'` grants client access (D15). Pending,
  rejected, suspended, ended and inactive rows carry **no** access.
- **Documented options:** All active-grant orgs, re-checked per request
  (recommended); restrict to Case A only; or introduce origin-dependent
  processing scope.
- **Distinctions to preserve (from source artifact §7 and P6-1B):**
  - *Consultant commercial entitlement* — organisation-scoped commercial
    capability (`billing_plans.features.consultant`); not bound to a firm yet
    (D-C deferred). Never substitutes for client processing entitlement.
  - *Client processing authorization* — client organisation's own
    subscription/entitlement/credits.
  - *Active client engagement* — the `consultant_clients` active grant that
    authorizes the consultant to touch the client org at all.
- **Recommended option:** All active-grant orgs, per-request re-checked.
- **Consequences:** scope of every future consultant processing route.

## P6-2-D3 — D38 Interaction / Assignment Conflict

- **Question:** May an active-grant consultant process unassigned items? Items
  assigned to internal staff? Items assigned to a Processing Entity (and with
  what handoff)?
- **Current implementation / evidence:** No assignment check exists on the
  org/consultant processing surface — consultant action is gated only by org
  access. Internal-staff- or PE-assigned items can be operated by an
  active-grant consultant; unassigned items have no ownership rule for
  consultants (Gap G3; source artifact §6). Effective assignment = open D38
  item assignment else batch default; `assignee_kind` is strictly
  `('internal_staff','processing_entity')`. **Consultants are not automatically
  D38 assignees** — preserve that principle.
- **Documented options:** Engagement-scoped processing with a deny-rule vs
  D38-native assignment.
- **Recommended option:** Consultants act only on items **not** currently
  open-assigned to internal staff or a PE — i.e., deny any action on an item
  with an open D38 assignment unless an explicit Ops-controlled handoff exists —
  plus a new rule for unassigned items owned by the engaged org's workflow.
- **Consequences:** guard position in the processing service + tests.
- **Dependencies:** D4 (handoff) and D10 (org-member scope) interact; feeds the
  D38 conflict deny-rule in P6-2A.

## P6-2-D4 — PE ↔ Consultant Handoff (D5)

- **Question:** How is D5 (“Ops-controlled PE ↔ Consultant handoff”) realised?
  By adding consultant-visible handoff on the D38 ledger, by a separate explicit
  handoff state, or is PE↔Consultant handoff out of scope (Ops-routes
  reassignment only)?
- **Current implementation / evidence:** No representation exists — no handoff
  state, route, `assignee_kind` value, or audit event (Gap G4). Release/
  reassignment/recovery/audit/concurrency exist today **only** for
  Ops↔internal-staff and Ops↔PE via the D38 ledger (single-open partial unique
  index).
- **Documented recommendation (if handoff is in scope):** Ops-controlled release
  from PE + assignment to the consultant's org workflow, expressed as explicit
  audit plus a new **non-`assignee_kind` engagement-bound scope** — **not**
  `assignee_kind = 'consultant'` unless item-level queuing for consultants is
  separately ratified.
- **Open PO aspects (not resolved by the source artifact — preserve as PO
  decision):** who may initiate a handoff, who authorizes it, PE→Consultant and
  Consultant→PE direction rules, release/reassignment/recovery behaviour,
  auditability, and concurrency for any new representation; **whether a new
  schema/state representation is required is explicitly unresolved** and must be
  decided by the PO (source artifact §12 D4).
- **Consequences:** schema/route decisions (if in scope).

## P6-2-D5 — Consultant Review / Workflow Boundary / CarbonTally QC Submission

- **Question:** Is Consultant Review a distinct workflow state or a permission?
  What status sequence leads to CarbonTally-QC submission for consultant-origin
  work (including a `processing_origin` value)?
- **Current implementation / evidence:** No consultant stage exists. The CT-QC
  mandatory-before-approval guard keys only on
  `processing_origin = 'PROCESSING_ENTITY'`; consultant-origin work has no
  defined path and no guard (Gaps G1, G5). CarbonTally QC is CarbonTally-only
  (CT-QC-001…005).
- **Documented recommendation:** A distinct `consultant_review` status, an
  origin value `CONSULTANT` (or an explicit decision to reuse
  `CARBONTALLY_INTERNAL`), and a submit action that moves consultant-origin work
  into `ct_qc` before customer review. **This is a recommendation for PO
  ratification — the state is not added by this register.**
- **Note (10 September 2026):** the *origin-value* element of this recommendation
  (`origin CONSULTANT`) is **superseded / withdrawn** — the PO has withdrawn the
  proposed `CONSULTANT` `processing_origin` value in
  **`PO-P6-2D-D7b-R-20260910`** (see `## P6-2D Ratified PO Decision — 2026-09-10`).
  `processing_origin` remains the internal-vs-PE manual-processing capacity/control
  path and is neither actor identity nor processing mode. The remaining elements of
  this recommendation — the distinct consultant review state and the submit action
  into `ct_qc` — are **unaffected** and were implemented in P6-2B-1/P6-2B-2.
- **Workflow boundary (as documented):** Consultant processing stages
  (extraction → mapping → validation → calculation → consultant review) →
  CarbonTally QC (CarbonTally-only) → Customer Review → **Customer Approval
  (customer-only; hard invariant — Consultant must never perform Customer
  Approval).**
- **Consequences:** state-machine vocabulary + guard extension + queue labels.

## P6-2-D6 — Processing Entitlement Timing

Documented separately per the source artifact (§7, §12 D6):
1. **Entitlement ownership:** the **client organisation** owns processing
   entitlement (subscription/credits) — never the consultant firm or member.
2. **Entitlement authorization/check:** today enforced at customer approval via
   `BillingService.charge_processing(batch.organization_id, …, idempotency_key,
   actor)` (fail-closed for subscribed orgs).
3. **Actual credit consumption:** against the client organisation's credits/
   subscription (organisation-owned ledger/usage records).
4. **Billing/charging:** `charge_processing` is called at customer approval
   only (the single call site today); `organization_id` is read from the
   server-loaded batch — no substitution.
5. **Timing:** question is whether entitlement enforcement at customer approval
   is sufficient, or an earlier (non-charging or charging) check is required
   when consultant processing begins.
- **Recommended option:** Entitlement check at approval (client org) remains
  canonical; add a **non-charging** availability check at consultant submission
  only if capacity visibility is required. The source artifact does **not**
  silently decide that entitlement must be checked at every consultant action.
- **Alternatives:** earlier entitlement gating at consultant processing start.
- **Consequences:** billing call-site/check placement; ownership unchanged.

## P6-2-D7 — Consultant Firm Provenance

- **Question:** How is “which Consultant firm acted” recorded in provenance?
- **Current implementation / evidence:** Human actor (authenticated
  `user_id`) and client organisation are recorded; the acting **Consultant
  firm** is absent from item/snapshot/audit provenance (Gap G7). Gates 4–6
  structures otherwise support consultant actions as human-actor actions
  (human attribution, write-once machine provenance, human-after-automation
  attribution, immutable `processing_origin`, calculation snapshots with
  `performed_by`/`source_item_id`).
- **Distinctions to preserve (source artifact §8):**
  - *Actor identity* — authenticated consultant human (user_id).
  - *Actor's Consultant firm* — the `consultant_profiles`/firm containing the
    member (NOT currently recorded — the decision subject).
  - *Client organization* — server-loaded `batch.organization_id`.
  - *Processing origin* — the immutable origin concept (internal/PE today);
    consultant origin value is a separate D5 question.
  - Machine vs human provenance — automation is write-once (Gate 5); consultant
    confirm/edit is human-after-automation (Gate 6).
- **Documented options:** (a) record consultant firm at action time on the
  relevant provenance/audit payload (additive, no reinterpretation of existing
  columns — recommended); (b) derive via membership at read time (single-firm
  limitation, misattributes if the member changes firms); (c) extend the
  `processing_origin` vocabulary.
- **Consequences:** additive provenance field + additive migration (only if the
  PO ratifies option (a)). No new provenance schema is invented by this
  register.
- **P6-2D amendment (10 September 2026) — framing clarification:** D7 concerns
  **firm provenance for consultant processing actions** (and, where the
  architecture already places it under D7, the explicit recording of
  **processing-mode provenance**). It must **not** be represented through
  `processing_origin`: the origin column identifies the manual-processing
  **capacity/control path** (CarbonTally internal vs Processing Entity) and is
  neither actor identity nor processing mode. D7 option **(c)** ("extend the
  `processing_origin` vocabulary") is therefore **excluded** by the PO's
  withdrawal of D7b (`PO-P6-2D-D7b-R-20260910`). **Status: PENDING PO DECISION.**
  This clarification prescribes no schema and no column name.

## P6-2-D8 — D39 Conversation Kind

- **Existing D39 model:** conversations/messages/conversation_participants with
  `conversation_kind`, org id and `processing_entity_id` (PE operational
  messaging); org-scoped conversations; PE participation restricted to
  CarbonTally Operations (PE-MSG-001).
- **Consultant participation:** the messaging domain already admits consultants
  only through an active grant (source artifact §3.4 / prior readiness report);
  participant derivation should follow the same active-grant rule.
- **Client scope:** org-scoped conversations on the engaged client org.
- **Question:** Add a consultant conversation kind distinct from customer/ops/
  PE, or reuse customer-scoped conversations with firm participants?
- **Recommended option:** Reuse org conversations with participant derivation
  from active grants; add a consultant kind **only if** reporting/UI filtering
  requires it.
- **Exact proposed vocabulary:** the source artifact does **not** enumerate a
  fixed kind vocabulary (the domain kinds were not enumerated in the inspected
  module); if a kind is required, its exact string is a PO decision under D8.
- **Consequences:** messaging vocabulary; UI filters. D39 itself is not created
  or modified by this register.

## P6-2-D9 — Customer Approval Boundary

- **Question:** Confirm that final customer approval is exclusively customer
  owner/admin; that consultants only submit; and that no automatic transition
  (calculation, CT-QC approval, consultant submission) can reach `approved`.
- **Current implementation / evidence:** Only the org-admin-gated
  `customer_review_item` route writes `approved` (`require_org_admin`); no
  consultant route can write `approved` today. The item transition map has
  latent `calculated → approved` and `ct_qc_approved → approved` transitions
  (Gap G10).
- **Indirect-approval paths:** none found today — consultant submissions,
  calculation, CT-QC decisions and consultant review cannot reach `approved`.
- **Recommended option:** Ratify the invariant and add regression guards + tests
  preserving it through every P6-2 workstream.
- **Hard invariant (preserved):** **Consultant can never approve customer
  work.** Customer Review is a customer action; Customer Approval is
  customer-owned; CarbonTally QC remains CarbonTally-only.
- **Consequences:** negative tests in every P6-2A–F workstream.

## P6-2-D10 — Organization Member Manual Processing Scope

- **Question:** Keep ordinary customer-organisation members on the shared
  `/api/v3/processing/*` surface, or restrict stage actions to owners/admins and
  consultants?
- **Current implementation / evidence:** Today `ensure_processing_org_access`
  admits org members (own org), internal CarbonTally staff (any-org), and
  active-grant consultants; Processing Entity staff are denied on the org
  surface (Gap G9).
- **Actor distinctions (documented, not inferred):** organisation owner/admin —
  approve and administer; ordinary member — admitted to stage actions today
  (this decision); Consultant — active-grant processing (D1/D2); PE — assigned
  work only via `/pe`, never the org surface; internal CarbonTally staff —
  operational access via `/ops`/`/qc`.
- **Recommended option:** Preserve today's behaviour (org members admitted)
  unless the PO has a reason to restrict.
- **Consequences:** scope of D5/D9 changes.

## P6-2-D11 — D40 Notification Vocabulary

- **Existing D40 architecture:** notifications with recipient
  type/id, `event_key` dedupe (`create_idempotent`), `actor_domain`;
  recipient-scoped opening/authorization follows the existing notification
  authorization pattern (e.g. `work_item.assigned` events).
- **Question:** Which consultant processing events must exist and to whom?
- **Current implementation / evidence:** Event-key idempotent model exists;
  consultant processing lifecycle events are missing (Gap G8).
- **Recommended option:** Enumerate the consultant processing events during
  workstream P6-2E: engagement request accepted; submitted to CarbonTally QC;
  QC outcome; customer decision; rework required.
- **Recipients (documented in source artifact §9):** firm members (acting on
  the engagement), client org owner/admin, Ops QC assignee — recipient-scoped
  and idempotent.
- **Consequences:** event constants, recipient derivation, tests. D40 itself is
  not created or modified by this register.

## Decision Table

| ID | Decision | Recommended option | PO action required | Dependency |
| --- | --- | --- | --- | --- |
| D1 | Consultant processing capability flags | (a) additive `can_*` flags gating every action | RATIFY / MODIFY | P6-2A |
| D2 | Consultant processing org/engagement scope | all active-grant orgs, per-request re-checked | RATIFY / MODIFY | P6-2A |
| D3 | D38 interaction / assignment conflict | deny on any open D38 assignment (no explicit handoff); rule for unassigned items | RATIFY / MODIFY | D4, P6-2A |
| D4 | PE↔Consultant handoff (D5) | Ops-controlled release + non-`assignee_kind` engagement-bound scope (representation unresolved) | RATIFY / MODIFY / SCOPE | D3, P6-2A |
| D5 | Consultant review / submit / CT-QC / origin | distinct `consultant_review` + origin `CONSULTANT` (or reuse internal) + submit to `ct_qc` | RATIFY / MODIFY | P6-2B / P6-2C |
| D6 | Processing entitlement timing | approval-time check (client org) canonical; optional non-charging availability check at submission | RATIFY / MODIFY | P6-2D |
| D7 | Consultant firm provenance | record firm at action time (additive) | RATIFY / MODIFY | P6-2D |
| D8 | D39 conversation kind | reuse org conversations; kind only if reporting requires | RATIFY / MODIFY | P6-2E |
| D9 | Customer approval boundary | consultants submit only; approval customer owner/admin; regression guards | RATIFY / MODIFY | P6-2C & all |
| D10 | Org-member manual-processing scope | preserve today's behaviour (members admitted) | RATIFY / MODIFY | P6-2A |
| D11 | D40 notification vocabulary | events: request accepted, submitted to CT-QC, QC outcome, customer decision, rework | RATIFY / MODIFY | P6-2E |

This table is for PO review only; **no decision is ratified by this register**.

## Cross-Dependencies

- **D1 → consultant action authorization** (P6-2A).
- **D2 → resource/engagement authorization** — which orgs/engagements any
  consultant processing route may target (P6-2A).
- **D3 / D4 → D38 and PE interaction** — the conflict deny-rule and the PE↔
  Consultant handoff representation (P6-2A; D4 may be deferred if handoff is
  scoped out).
- **D5 → workflow implementation** — consultant review state/origin and the
  submit-to-`ct_qc` transition (P6-2B/C).
- **D6 → billing/entitlement enforcement** — charge/check placement (P6-2D).
- **D7 → provenance implementation** — additive firm dimension (P6-2D).
- **D8 → D39 integration** (P6-2E).
- **D9 → approval security** — hard invariant preserved across every workstream
  (P6-2C and all).
- **D10 → organization-member authorization** — scope of the org-side surface
  (P6-2A).
- **D11 → D40 integration** (P6-2E).

**Must be settled before P6-2A (Consultant Processing Authorization Contract):**
D1, D2, D3 (and D4 if PE↔Consultant handoff is in scope), D10.

**Can be deferred to later workstreams:** D5/D9 → P6-2C; D6/D7 → P6-2D;
D8/D11 → P6-2E; D9 regression guards apply across all P6-2A–F.

## P6-2C Ratified PO Decisions — 2026-09-10

> **Authority:** these three entries are **ratified Product Owner decisions**
> (authoritative product policy). They are recorded here — inside the established
> P6-2 PO Decision Register — to avoid creating a competing authority hierarchy.
> They do **not** ratify, modify or reinterpret the recommendation-only D1–D11
> rows above. The P6-2C implementation contract that consumes them is
> `docs/architecture/CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md`.

### PO-P6-2C-D1-20260910 — `calculated → approved` is automatic-processing-only

- **Decision Ref:** `PO-P6-2C-D1-20260910`
- **Decision date:** 2026-09-10
- **Decision status:** **RATIFIED**
- **PO selection:** **A**
- **Ratified policy:** keep the existing `calculated → approved` transition
  because the automatic-processing workflow requires it, but make its
  authorization **explicitly automatic-processing-only**. The transition must
  **not** become a general approval capability. Consultant, Processing Entity,
  Operations, regular organisation member, Viewer and other unauthorised
  actors/routes must not be able to exploit it as a manual approval shortcut.
  Manual processing retains the CT-QC / customer-approval boundary. The
  implementation must preserve the existing automatic-processing workflow while
  ensuring the state-machine transition itself does not grant approval authority
  to arbitrary callers.
- **Rationale:** the map entry is load-bearing for automatic approval; the
  approval *authority* must come from the authorized server-side route, not from
  the existence of the transition.
- **Scope implication:** P6-2C only; no new states, roles or permissions.
- **Implementation implication:** the customer item approval route must continue
  to refuse `calculated → approved` for non-automatic (manual) work, and this
  must be expressed explicitly and proved by negative tests; the automatic
  job-review route is the authorised automatic approval path.
- **Explicit non-decisions / deferred:** no change to the state map itself; no
  change to the automatic-processing architecture; no change to billing.

### PO-P6-2C-D2-20260910 — Consultant `review`-stage claiming requires an existing capability

- **Decision Ref:** `PO-P6-2C-D2-20260910`
- **Decision date:** 2026-09-10
- **Decision status:** **RATIFIED**
- **PO selection:** **A**
- **Ratified policy:** a consultant must possess an **existing appropriate
  capability** before being allowed to claim the generic `review` stage. **Do not
  create a new consultant-review capability** as part of P6-2C. If no existing
  capability is appropriate for a particular review-stage action, the consultant
  must **not** be permitted to claim that stage until a future PO decision
  explicitly defines such authority. **An active consultant grant by itself must
  not implicitly grant every workflow-stage capability.** The authorization model
  `identity → firm → grant → resource → action → stage` must be preserved.
- **Rationale:** the readiness analysis found `_STAGE_PERMISSION` has no `review`
  entry, so an active-grant consultant with **zero** capability flags can claim
  the `review` stage (P6-2A verification §18 B2); a grant alone must not imply a
  stage capability.
- **Scope implication:** P6-2C only; **no new flag**; the existing six-flag model
  is unchanged.
- **Implementation implication:** gate the consultant `review` stage claim on an
  **existing** capability through the canonical resolver
  (`ensure_consultant_processing_authorized(permission=…)`). The evidence-based
  mapping is **`submit` → `can_submit`** (the capability that already authorises
  consultant submission of reviewed work into the CT-QC pipeline, P6-2B-2). If
  the PO considers a different *existing* capability appropriate, only that
  single mapping changes; no new capability is created either way.
- **Explicit non-decisions / deferred:** no new capability; no change to D1–D11;
  no consultant privilege broadening.

### PO-P6-2C-D3-20260910 — Automatic job-review billing is unchanged and deferred

- **Decision Ref:** `PO-P6-2C-D3-20260910`
- **Decision date:** 2026-09-10
- **Decision status:** **RATIFIED**
- **PO selection:** **A**
- **Ratified policy:** do **not** modify billing behaviour as part of P6-2C. The
  existing automatic job-review billing behaviour remains unchanged. The
  billing-policy question for the automatic job-review approval path is
  explicitly **DEFERRED** and must not be silently resolved by implementation.
  Do not redesign billing, charging semantics, subscription/credit accounting,
  idempotency, refunds or billing audit behaviour unless a future explicit PO
  decision authorises such work.
- **Rationale:** the readiness analysis observed that
  `POST /api/v3/processing/jobs/{job_id}/review` stamps the item approved without
  charging (single charge site = the customer item-approval route). That is a
  pre-existing behaviour/policy question, not a P6-2C control defect.
- **Scope implication:** billing files are out of scope for P6-2C.
- **Implementation implication:** no billing code change; P6-2C tests may
  **assert** the existing (unchanged) billing behaviour but must not alter it.
- **Explicit non-decisions / deferred:** the automatic job-review billing-policy
  question remains **DEFERRED** (owner/phase unassigned; see the P6-2C contract
  §"Deferred").

## P6-2D Ratified PO Decision — 2026-09-10

> **Authority:** this entry is an **authoritative Product Owner decision** (product
> policy). It is recorded here — inside the established P6-2 PO Decision Register —
> in the same manner as the ratified P6-2C entries. It does **not** ratify, modify or
> reinterpret the recommendation-only D1–D11 rows above, and it does **not** assert
> any implementation.

### PO-P6-2D-D7b-R-20260910 — Consultant `processing_origin` value

- **Decision Ref:** `PO-P6-2D-D7b-R-20260910`
- **Decision date:** 2026-09-10
- **Decision status:** **RATIFIED (PROPOSAL WITHDRAWAL)**
- **PO selection:** **WITHDRAW / REJECT AS PROPOSED**
- **Ratified policy:** the proposed addition of a **`CONSULTANT`** value to
  `processing_origin` is **withdrawn**. `processing_origin` is **not** redefined as an
  actor-domain vocabulary; its CHECK constraint, its two-value vocabulary
  (`CARBONTALLY_INTERNAL`, `PROCESSING_ENTITY`), its write-once semantics and its
  origin→stage routing are unchanged. No consultant-specific `review` / `pe_review`
  routing is introduced on the basis of origin.
- **Reason:**
  - `processing_origin` already has an established architectural meaning — the
    **manual-processing capacity/control path** (CarbonTally internal vs Processing
    Entity);
  - it is **not** actor identity;
  - it is **not** processing mode;
  - adding `CONSULTANT` would conflate distinct domain concepts (actor / firm /
    processing mode / processing channel / workflow responsibility);
  - it would unnecessarily alter a CHECK-constrained, routing-driving vocabulary
    (schema, stage routing and queue semantics), for no requirement that the existing
    provenance model does not already answer.
- **Authoritative references:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §9
  (*Processing model — dimensional clarification*);
  `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4 (processing-origin model);
  `docs/cline/CARBONTALLY_P6_2_PROCESSING_MODEL_RECONCILIATION_REPORT.md`.
- **Implementation status:** **NOT IMPLEMENTED / NO CODE CHANGE REQUIRED FOR THIS
  DECISION.** This decision *removes* a proposal; it therefore requires no code,
  schema, migration, RLS, permission, billing, UI, workflow or test change. In
  particular it must **not** be reported as implemented.
- **Explicit non-decisions / deferred:** D7 (firm provenance, with the framing
  clarification above) remains a **pending** PO decision; the "no historical
  provenance backfill" direction (**D7c** as proposed in the Phase-6 remainder
  readiness analysis) also remains **pending** and is unchanged by this decision;
  D6 (entitlement timing) is unchanged. Nothing else in D1–D11 is ratified here.

---

## P6 Remainder Ratified PO Decisions — 2026-09-10

> **Authority:** these entries are **authoritative Product Owner decisions** (product
> policy), recorded in this register in the same manner as the ratified P6-2C and
> P6-2D entries. They ratify the *policy* for the remaining Phase-6 gates
> (**P6-2D / P6-2E / P6-2F**) and establish the baseline for the future implementation
> contract (`CARBONTALLY-PHASE6-REMAINDER-IC-20260910-001` — **not created yet**). They
> do **not** ratify, modify or reinterpret the recommendation-only D1–D11 rows above,
> and they assert **no implementation**.
>
> **Baseline document:** `docs/cline/CARBONTALLY_PHASE6_REMAINDER_PO_RATIFICATION_REPORT.md`.
> **Processing model of record:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §9
> (*Processing model — dimensional clarification*) and
> `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4 (origin model).

### Decision summary

| Ref | Subject | PO selection | Policy ratified | Implementation status |
|---|---|---|---|---|
| `PO-PHASE6-D6-R-20260910` | Entitlement timing | **A** | Non-charging submission preflight; canonical approval-time enforcement; entitlement owned by the client Organisation | PRE-EXISTING behaviour (matches policy); unchanged — no code change required |
| `PO-PHASE6-D7-R-20260910` | Firm + processing-mode provenance | **A** | Durable server-derived firm provenance for consultant actions; keep actor/mode/origin/firm distinct | **NOT IMPLEMENTED** — future contract defines exact representation |
| `PO-PHASE6-D7b-R-20260910` | Consultant `processing_origin` value | **WITHDRAW / REJECT AS PROPOSED** (previously ratified — see `## P6-2D Ratified PO Decision — 2026-09-10`) | No `CONSULTANT` origin value; no CHECK-constraint change; no vocabulary expansion; no consultant-origin routing/queue semantics | **NOT IMPLEMENTED / NO CODE CHANGE REQUIRED** |
| `PO-PHASE6-D7c-R-20260910` | Historical provenance backfill | **A** | **No historical backfill** of firm/mode provenance; no fabrication; prospective only | **NOT IMPLEMENTED** (and no backfill is authorised) |
| `PO-PHASE6-D8-20260910` | Consultant conversation model | **B** | Reuse the existing conversation model; no dedicated consultant kind unless later evidence requires it | PRE-EXISTING reuse model in place; **no new kind authorised** — no schema change |
| `PO-PHASE6-D11-20260910` | Consultant lifecycle notifications | **A** | Five lifecycle events; deterministic idempotent keys; server-side recipients; no cross-tenant leakage | **NOT IMPLEMENTED** — infrastructure exists; event constants/recipient matrix to be defined by the future contract |
| `PO-PHASE6-BILL-DEFER-20260910` | Automatic job-review billing | **A** | **Remain deferred** — no redesign, no new/removed charge, no resolution of the policy question | DEFERRED — no change |
| `PO-PHASE6-D4-20260910` | PE ↔ Consultant handoff | **A** | **Outside Phase 6** — no explicit handoff workflow, states, assignment or authorisation flows | OUT OF SCOPE — no change |
| `PO-PHASE6-F-ACC-20260910` | P6-2F final acceptance standard | **A** | Full Phase-6 UI/UX + E2E security acceptance; **independent verification mandatory**; no self-certification | Policy for a future gate — **NOT IMPLEMENTED** |
| `PO-PHASE6-F-ENV-20260910` | P6-2F E2E environment | **A** | Dedicated isolated E2E environment with synthetic/test data; no production data; resettable; production security not weakened for tests | Policy for a future gate — **NOT IMPLEMENTED** |
| `PO-PHASE6-CAMPAIGN-20260910` | Unified Phase-6 remainder campaign | **A** | One overall campaign with **hard internal checkpoints**; P6-2F in a **fresh session**; no checkpoint silently skipped | **NOT IMPLEMENTED** — campaign not started |


### PO-PHASE6-D6-R-20260910 — Entitlement timing

- **PO selection:** **A** — *non-charging submission preflight + canonical
  approval-time enforcement.*
- **Ratified policy:** (1) consultant submission performs a **non-charging** entitlement
  availability check; (2) submission **does not consume** entitlement; (3) final
  approval performs the **canonical authoritative** check; (4) approval remains the
  authoritative enforcement/consumption point; (5) entitlement remains owned by the
  **client Organisation**; (6) processing **actor** and processing **mode** do not
  transfer entitlement ownership.
- **Explicit non-decisions:** no entitlement redesign; no consultant-owned or
  actor-owned entitlement; **no charge at submission** merely because availability is
  checked.
- **Implementation status:** **PRE-EXISTING** — the existing codebase already performs a
  non-charging availability check at consultant submission and the canonical charge at
  customer approval. This record changes **no** code; the status is recorded for
  accuracy only, **not** as work performed under this ratification.

### PO-PHASE6-D7-R-20260910 — Firm provenance + relevant processing-mode provenance

- **PO selection:** **A** (the corrected D7).
- **Ratified policy:** preserve **durable firm provenance for consultant processing
  actions**, while preserving **processing-mode provenance separately** where the
  architecture requires it. The future implementation contract defines the exact
  representation after code/schema inspection.
- **Firm provenance requirements:** the relevant consultant **firm's identity** is
  captured **when the consultant action occurs**; it is derived **server-side** from the
  authorised consultant/grant relationship and is **never actor-supplied**; historical
  provenance remains **stable**, and later membership/grant changes must not rewrite
  historical firm provenance.
- **Concepts that must remain distinct:** individual **actor** · consultant **firm** ·
  **processing mode** · **processing origin** · **workflow state** · **entitlement**.
- **Processing-mode provenance:** where the existing D7 architecture requires it,
  preserve the **mode** associated with the action. **Do not** use `processing_origin`
  to represent mode; **do not** add Consultant to `processing_origin`.
- **Explicit non-decisions:** **no database field name is prescribed** by this record;
  D7 option (c) (extending the `processing_origin` vocabulary) remains **excluded**.
- **Implementation status:** **NOT IMPLEMENTED** — no schema, no column, no code.

### PO-PHASE6-D7c-R-20260910 — Historical backfill

- **PO selection:** **A** — **no historical provenance backfill.**
- **Ratified policy:** do not infer missing historical **firm** provenance; do not infer
  missing historical **mode** provenance; do not fabricate historical provenance;
  existing historical records remain unchanged where provenance was never captured; new
  provenance applies **prospectively** per the future implementation contract.
- **Scope:** applies to the firm/mode provenance introduced under D7.
- **Implementation status:** **NOT IMPLEMENTED** — and no backfill is authorised; **no
  migration and no historical record modification**.

### PO-PHASE6-D8-20260910 — Consultant conversation model

- **PO selection:** **B** — **reuse the existing conversation model.**
- **Ratified policy:** no dedicated consultant conversation kind is introduced unless
  later evidence demonstrates a concrete product/security requirement the existing model
  cannot satisfy; consultant participation continues through the existing
  authorisation/grant model; no unnecessary schema expansion; conversation authorisation
  must not be weakened.
- **Implementation status:** **PRE-EXISTING reuse model** already in place (consultants
  participate via the active grant). **No new kind is authorised**, so this decision
  requires **no schema change** unless a future PO decision reverses it.

### PO-PHASE6-D11-20260910 — Consultant lifecycle notifications

- **PO selection:** **A**.
- **Ratified policy:** lifecycle notifications for (1) consultant accepted;
  (2) submitted to QC; (3) QC outcome; (4) customer decision; (5) rework. Requirements:
  deterministic/idempotent **event keys**; use the **existing** idempotent notification
  infrastructure; **server-side** recipient derivation; recipients determined from the
  **actual workflow relationship**; notifications must not leak data across
  organisations, firms or unauthorised actors.
- **Explicit non-decisions:** the exact event constants/keys and the recipient matrix are
  **not** defined here — the future implementation contract must derive them from the
  existing architecture and code. No recipient identities are invented in this record.
- **Implementation status:** **NOT IMPLEMENTED** — only the idempotent notification
  infrastructure pre-exists; the consultant lifecycle events do not.

### PO-PHASE6-BILL-DEFER-20260910 — Automatic job-review billing

- **PO selection:** **A** — **remain deferred.**
- **Ratified policy:** during P6-2D/P6-2E/P6-2F: do not redesign automatic job-review
  billing; do not change current billing semantics; do not introduce a new charge; do not
  remove an existing charge; do not resolve the broader billing-policy question.
- **Status:** **DEFERRED** — remains a separate future PO billing-policy decision (this
  extends the deferral already recorded in `PO-P6-2C-D3-20260910`).

### PO-PHASE6-D4-20260910 — PE ↔ Consultant handoff

- **PO selection:** **A** — **D4 remains outside Phase 6.**
- **Ratified policy:** do not implement an explicit PE↔Consultant handoff workflow as part
  of P6-2D/E/F; do not introduce new state transitions, assignment semantics or
  authorisation flows for this purpose; existing workflows remain unchanged.
- **Status:** **OUT OF SCOPE** — no change.

### PO-PHASE6-F-ACC-20260910 — P6-2F final acceptance standard

- **PO selection:** **A** — **full Phase-6 acceptance is required.**
- **Ratified policy:** P6-2F is the final Phase-6 **UI/UX and E2E security acceptance
  gate**. Acceptance must cover, as applicable: Organisation, Consultant, Processing
  Entity and CarbonTally-Internal workflows; authentication; authorisation; organisation
  isolation; consultant grant boundaries; capability enforcement; CT-QC boundaries;
  processing-origin integrity; provenance; entitlement; billing invariants; notification
  behaviour; UI workflows; negative security scenarios; IDOR resistance; alternate-route
  resistance; actor-injection resistance; replay/idempotency; E2E browser workflows; and
  the full regression suite.
- **Hard rule:** P6-2F **cannot self-certify** final acceptance. **Mandatory independent
  verification is required**, and the final Phase-6 verdict must be based on **evidence**,
  not merely implementation completion.
- **Implementation status:** policy for a future gate — **NOT IMPLEMENTED**.

### PO-PHASE6-F-ENV-20260910 — P6-2F E2E environment / data safety

- **PO selection:** **A** — **dedicated isolated E2E environment with synthetic/test data.**
- **Ratified policy:** no production customer data; no destructive production operations;
  dedicated test identities; representative Organisation/Consultant/PE/Internal roles;
  realistic authentication and authorisation; RLS exercised where applicable;
  reproducible fixtures; safe test billing/ledger behaviour; resettable test data;
  security-negative tests may exercise denied operations; no real customer data mutation.
- **Hard rule:** the implementation **must not weaken production security** merely to make
  E2E tests pass.
- **Implementation status:** policy for a future gate — **NOT IMPLEMENTED**.

### PO-PHASE6-CAMPAIGN-20260910 — Unified Phase-6 remainder campaign

- **PO selection:** **A** — **one overall Phase-6 remainder campaign with mandatory hard
  internal checkpoints.**
- **Ratified policy:** the campaign is **not** one uninterrupted implementation session.
  Required structure:

```text
CP0  PO ratification
  ↓  P6-2D implementation → focused tests → regression → evidence report
  ↓  INDEPENDENT VERIFICATION           → STOP if failed
  ↓  P6-2E implementation → focused tests → regression → evidence report
  ↓  INDEPENDENT VERIFICATION           → STOP if failed
  ↓  P6-2F  (FRESH Cline session) → UI implementation → E2E/security acceptance
  ↓  full Phase-6 regression            → STOP if failed
  ↓  MANDATORY INDEPENDENT VERIFICATION
  ↓  FINAL PHASE-6 ACCEPTANCE
```

- **Hard rules:** P6-2F must be performed in a **fresh implementation session**; **no
  checkpoint may be silently skipped**; failure at any checkpoint **blocks progression**
  until resolved and independently verified.
- **Implementation status:** **NOT IMPLEMENTED** — the campaign has not started; this
  record is **CP0 only**.

### Explicit non-decisions / preserved boundaries

Not authorised by this PO package: adding `CONSULTANT` to `processing_origin`; redefining
`processing_origin`; redesigning automatic processing, manual processing or the
automatic→manual fallback; changing the **P6-2C** approval/review/source semantics;
billing redesign; PE↔Consultant handoff; **new roles or capabilities without a separate
PO decision**; RLS redesign; destructive migration; historical provenance
fabrication/backfill; demo-data redesign.

### P6-2C invariants remain frozen (do not reopen)

1. `calculated → approved` remains automatic-processing-only.
2. Consultant review claiming uses the existing canonical `can_submit` resolution.
3. Consultant source claiming uses the existing canonical `can_extract` resolution.
4. `_STAGE_PERMISSION` remains the single stage-gating mapping.
5. Approval remains organisation-admin controlled.
6. Billing remains after the applicable approval guard.
7. No new role/capability/permission is created by the P6 remainder unless separately authorised.
8. Billing semantics remain unchanged unless separately authorised.
9. Existing RLS/security boundaries remain unchanged.

## Final Recommendation

> **No Consultant Processing implementation should begin until P6-2-D1 through
> P6-2-D11 are explicitly ratified or modified by the PO.**

The next implementation workstream already recommended by the architecture
artifact is **P6-2A — Consultant Processing Authorization Contract** (additive
permission flags, action gating, org-scope rules, D38 conflict deny-rule, with
a full negative security matrix), gated on ratification of D1/D2/D3(/D4)/D10.
That workstream is **not** created by this register.

---

*End of register. Read-only task — no code, schema, migration, RLS, API, UI,
workflow, billing, provenance, D38/D39/D40, tests or seed/demo data was
changed; no fixtures created; nothing committed or pushed.*




