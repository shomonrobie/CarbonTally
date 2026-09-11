# CarbonTally P6-2B — Consultant Review, Submission & QC Workflow Architecture

- **Date:** 2026-09-06
- **Status:** Read-only architecture gate. No code/schema/migration/RLS/API/
  test/workflow/billing/provenance/D38/D39/D40/UI/data change; no fixtures;
  nothing committed or pushed.
- **Scope:** Readiness for *Consultant Processing → Consultant Review →
  Submit to CarbonTally QC → CarbonTally QC → Customer Review → Customer
  Approval*, reusing Internal/PE/Customer paths; P6-2A is closed, not reopened.

## 1. Executive Summary

CarbonTally already contains the substrate this workstream needs: one
item-level state machine (`backend/domain/partners.py` `ITEM_STATUS_FLOW`),
dual-origin internal/PE paths with a CarbonTally-only QC gate, an org-scoped
shared processing surface, item-granular D38 assignment, customer-only
approval, and Gate 4–6 provenance. What does **not** exist is any Consultant
Review/Submit stage: no `consultant_review` state, no `consultant → ct_qc`
submission action, no consultant processing-origin value. P6-2A already
provides the reusable server-authoritative resolver
(`ensure_consultant_processing_authorized`) and the reserved `can_submit`
flag.

**No security blocker was found.** `approved` is reachable only via the
org-admin-gated `customer_review_item`; CT-QC outcomes only via internal
`can_qc` staff endpoints; entity/PE status mutation is guarded against
customer/QC-gated statuses; Consultants have no route writing `ct_qc_*` or
`approved`.

Verdict: **`P6-2B ARCHITECTURE READY — IMPLEMENTATION WORKSTREAM CAN BE
DEFINED`** — two items for early P6-2B design (§21), none blocking.

## 2. Authority Hierarchy

1. `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (§5, §9, §13, §31.3,
   §32).
2. Ratified P6-2 decisions D1–D11; P6-0 / P6-BILL-0 / P6-BILL-1 / P6-1B /
   P6-1C / P6-2A (accepted).
3. Gate 3 (D38), Gate 4/5/6, D35/D37/D39/D40, V1.2 dual-origin + CT-QC
   amendments (CT-QC-001..005).

## 3. Previously Ratified Decisions (binding)

- **D1:** six additive deny-by-default capabilities; `can_submit` reserved and
  NOT implemented by this gate.
- **D2:** active membership + active engagement only; non-active engagement
  states grant nothing; legacy/Case A/Case B uniform.
- **D3:** Consultants are not D38 assignees; open effective assignment
  (internal/PE) blocks Consultant work absent an Ops-controlled handoff.
- **D4:** PE↔Consultant handoff Ops-owned; representation deferred.
- **D5:** path = Consultant Processing → Consultant Review → CarbonTally QC →
  Customer Review → Customer Approval. Consultant may process/review/submit;
  must NOT perform CarbonTally QC or Customer Approval.
- **D6:** client org owns entitlement; consultant subscription never
  substitutes; actual charge at Customer Approval; non-charging availability
  check at Consultant submission ratified-desirable.
- **D7:** provenance distinguishes actor, consultant firm, client org,
  processing origin, machine vs human.
- **D8/D11:** reuse D39 org conversations; D40 event vocabulary.
- **D9:** Customer Approval is customer owner/admin only.
- **D10:** preserve ordinary org-member behaviour.

## 4. Current Workflow Architecture (verified)

Item-level pipeline on `manual_extraction_items` +
`manual_extraction_batches`; state machine `domain/partners.py`
(`ITEM_STATUSES`, `ITEM_STATUS_FLOW`, `WORKFLOW_STAGES`,
`WORKFLOW_STAGE_STATUSES`, `can_transition_item_status`).

- **Org-shared** `/api/v3/processing/*` (`v3_processing_workflow.py`):
  batch start/complete/cancel; item `start` (stage claim), `extract`, `map`,
  `validate`, `calculate`, `customer-review`, workspaces/queues/issues.
  `ensure_processing_org_access` admits internal staff (any-org), org members
  (own org), active-grant Consultants; P6-2A capability-gates consultant stage
  actions (extract/map/validate/calculate + matching stage claims). Approval
  gated `require_org_admin`.
- **Operations** `/api/v3/ops/*` (`v3_operations.py`): `submit-review`
  (staff `can_review`, internal-only; `calculated → reviewed`; PE origin
  rejected), `/qc/ct-queue` + `/qc/items/{id}/decision` (staff `can_qc`;
  `reviewed|pe_qc_approved|ct_qc → ct_qc_approved|ct_qc_rejected`), entity
  extraction status route (rejects customer/QC-gated statuses), D38
  `work/claim|assign|reassign|recover|release|complete`.
- **PE** `/api/v3/pe/*` (`v3_pe.py`): assigned work start/extract/map/
  validate/calculate, pe-review, pe-qc, clarify, work claim/release/complete.
- **CarbonTally QC** `/api/v3/qc/*` (`v3_qc.py`) + ops CT-QC surfaces:
  internal staff `can_qc` only.
- **Automatic** `/api/v3/processing/jobs/*` (`v3_automatic_processing.py`):
  durable job lifecycle; consultant confirm/retry gated on
  `can_confirm_automation` (P6-2A-R1); job `review` org-admin/internal.
- **D38** `work_item_assignments` + `services/work_items.py`:
  `assignee_kind ∈ {internal_staff, processing_entity}`; effective = open item
  row else batch default (`entity_id`/`assigned_to`).
- **Entitlement/charge** `services/billing.py`: only `charge_processing` call
  site is `customer_review_item` at approval (`batch.organization_id`).

## 5. Current State Machine (per-actor, item-level)

Verified against `domain/partners.py` `ITEM_STATUS_FLOW` and the route bodies.

| Current | Who can enter (endpoint) | Who can act | Auth | Next | Audit examples |
| --- | --- | --- | --- | --- | --- |
| pending | batch/item creation | org surface start/extract; ops; PE claim | org/consultant/staff/PE | extracting, extracted | `work_item:*` |
| extracting/extracted | stage claim + extract | org member, consultant `can_extract`, ops, PE(assigned) | per-surface | extracted, mapping | extraction stamps + audit |
| mapping/mapped | map | consultant `can_map`, ops, PE | | validating/validated; mapping (rework) | map audit |
| validating/validated | validate | consultant `can_validate`, ops | | calculating/calculated; mapping (blocking issues) | validation issues |
| calculating/calculated | claim + calculate | consultant `can_calculate`, ops, PE | | customer_review/approved/rejected/mapping; reviewed; pe_review | snapshot + audit |
| reviewed | ops `submit-review` (staff `can_review`, internal only) | ops; then CT-QC decision | staff | ct_qc, ct_qc_approved, mapping/calculated | `review:submitted` |
| pe_review*/pe_qc* | PE routes | PE (assigned) | PE | pe_qc_approved → ct_qc | PE audits |
| ct_qc / ct_qc_approved / ct_qc_rejected | ops `/qc/items/{id}/decision` from reviewed/pe_qc_approved/ct_qc | CarbonTally QC staff only | staff `can_qc` | customer_review/approved/rejected/mapping | `ct_qc:approved/rejected` |
| customer_review | org-surface start-review claim (any org-authorized incl. member/consultant) | customer owner/admin approve/reject | org admin | approved/rejected/calculated | approve/reject audit |
| approved | customer review approval only (PE-origin requires prior ct_qc_approved) | customer owner/admin | org admin | customer_review | approval audit |
| rejected | customer review rejection | customer owner/admin | org admin | mapping/extracting | rejection audit |
| qc_approved/qc_rejected | legacy early-QC markers | historical | — | mapping/extracted | — |

Verified boundaries: PE-origin approval blocked until `ct_qc_approved`
(`customer_review_item` guard); entity/PE status route rejects
customer/QC-gated statuses; no code path writes `approved` or `ct_qc_*`
outside those staff/customer endpoints.

## 6. Consultant Review Assessment

1. Does a Consultant Review state exist? **No.** No `consultant_review`
   status in `ITEM_STATUSES`; nothing routes to a consultant review stage.
2. Batch or item? **Neither exists.** A future stage must be item-level to
   align with D38 and the item state machine.
3. What resource becomes reviewable? **Item** (`manual_extraction_items`),
   consistent with `submit-review`/CT-QC being item-level today.
4. Who can enter? No entry today. Future: consultant member with capability +
   active engagement on the item's org, from `calculated` (or after
   consultant-origin processing). *("Consultant-origin processing" here means
   processing performed **by a consultant actor** — it is not a `processing_origin`
   value; see the clarification note in §22.)*
5. Who can act? N/A today. Future per D5: Consultant Review by an authorized
   consultant member.
6. May the processing consultant review own work? **Policy to decide**
   (recommend: yes per D5 wording "may review their own applicable work";
   segregation is provided later by independent CT QC). Open item (§21).
7. Same-firm other member? Recommend yes if active member + capability +
   engagement; open design detail.
8. Another firm? **No** — engagement/firm scope denies (resolver reuse).
9. Customer access before Customer Review? Today no such state; customers only
   read their own review queue; design keeps customers out of consultant
   review.
10. Can CarbonTally staff intervene? Today ops can always act on org items
    (internal staff any-org bypass) — preserved.
11. PE access? **No** — PE staff denied on org surface; assigned-PE items are
    blocked to consultants (D3).
12. Review failures? None today (no state). Future: `consultant_review_rejected`
    or route to `mapping`/`extracting` rework.
13. Rework return? Via the existing `mapping`/`extracting` rework transitions.
14. Audit event? Future `consultant.review:*` on `audit_trail`
    (human actor). 
15. Human attribution? Existing `current_user.user_id` stamps + audit actor
    (Gate 4); item `reviewed_by`-style column if added at implementation.

## 7. Consultant Submission to CarbonTally QC (D5) — Architecture

- **Resource submitted:** item (not batch) — mirrors ops `submit-review` and
  CT-QC decision granularity. Batch submit would require a consistency rule
  (§12) and is not required by any ratified decision.
- **State model (proposed, additive):** `calculated → consultant_review →
  consultant_reviewed → ct_qc → ct_qc_approved → customer_review →
  approved`. Additive item statuses only; rework returns via existing
  `mapping`/`extracting`.
- **`can_submit`:** required for the submission action; still deny-by-default
  and not wired today (reserved by D1). Submission action must be a distinct
  endpoint (consultant-route or shared-surface action gated by
  `ensure_consultant_processing_authorized` with `permission="submit"`).
- **Who may submit:** any active member of the engaged firm holding
  `can_submit`, acting on an item of the engaged client org (design decision:
  processor-only vs any authorized member — recommend any authorized member,
  per the member-capability model; D38 must be clear).
- **D38:** open item assignment or batch default → submit DENIED (D3); no
  handoff representation exists, so an item released from PE/staff ownership by
  Ops (future handoff) is the only way D38-held work becomes submittable.
- **Lifecycle races:** if membership becomes inactive or engagement suspended/
  ended, the resolver denies on next request (CT-CONS-REV-003). No stored
  "submitted" authority persists past the request.
- **Entitlement:** submission must perform a **non-charging** availability
  check (D6) against the client org's entitlement/credits; it must NOT call
  `charge_processing` (which remains at approval). If entitlement is
  unavailable → submission DENIED with an explanatory 403/409 (design detail);
  does not block today's manual actions.
- **Irreversibility:** submission should be reversible only via Ops/QC
  (e.g., CT-QC reject or ops return to mapping). No consultant withdraw of a
  submitted item without an explicit design (recommend: no self-withdraw after
  submit; Ops-controlled).
- **Audit/provenance:** `consultant.submit:item` audit (actor = consultant
  user, correlation item/batch); origin/firm attribution deferred (P6-2D) but
  the audit payload can carry `consultant_id` additively.
- **No QC bypass:** CT-QC decision endpoints remain internal `can_qc` only.

## 8. CarbonTally QC Boundary

- Entry: items at `reviewed` (internal path) or `pe_qc_approved` (PE path) via
  ops `/qc/items/{id}/decision` (`v3_operations.py`) and the `/api/v3/qc/*`
  surface (`require_admin`/`can_qc`). QC outcome (`ct_qc_approved`/
  `ct_qc_rejected`) written only by those internal endpoints and repo
  `ct_qc_decision`.
- Consultants: cannot trigger or mutate QC outcomes (no consultant route calls
  `ct_qc_decision`/`qc_review`; no `can_qc` flag exists for consultants).
- PE/customers: no path mutates CT-QC outcome.
- **Conclusion:** CT-QC boundary is sound today; P6-2B submission must land
  items at a state the internal QC queue accepts (i.e., feed the existing
  `ct_qc` gate after consultant review rather than duplicating a QC engine).

## 9. Customer Review Boundary

- Customer review/approval surface = `POST /api/v3/processing/items/{id}/customer-review`
  (`require_org_admin`) + `/customer-review` queue (org members read).
- PE-origin guard: approval requires `ct_qc_approved` already reached.
- Consultants have no customer-review authority (org-admin only); org members
  read their org queue only.
- Conclusion: customer review/approval boundaries are intact and must remain
  unchanged; P6-2B only adds a prior consultant stage that routes into the
  existing CT-QC gate.

## 10. Customer Approval Security Audit

Every writer of `approved` searched: only `customer_review_item` issues
`approved`/`rejected` (through `repos.manual_extraction.customer_review`),
gated `require_org_admin`; the transition map also allows
`calculated → approved` and `ct_qc_approved → approved` but no other endpoint
issues those transitions. PE/entity staff status route explicitly rejects
customer-gated statuses. Consultants cannot become org admins. Forged item ids
→ 404; cross-org → 403 (org access). Service-role operations (repo/worker) are
not reachable by Consultant API surface.
**Finding: no unauthorized approval path found.** The latent
`calculated → approved` map entry is flagged for P6-2C/D9 hardening, not a
current exploitable path.

## 11. D38 Interaction at Review / Submit / Rework

- Review and submit actions must apply the same P6-2A rule: open item
  assignment or batch default → DENY; unassigned (or Ops-handoff-released)
  work → allowed under capability/engagement.
- Rework after CT-QC rejection returns to `mapping`/`extracting`; resumption by
  the original consultant is allowed only if still authorized and the item has
  no open D38 assignment. If Ops assigns the reworked item, D38 blocks the
  consultant again (handoff required). No self-reassign exists.
- A race where a D38 assignment appears between open and submit must be closed
  by re-checking D38 at submit time (authorization before mutation).

## 12. Batch vs Item Granularity

- Current workflow is item-granular at the state-machine and D38 levels;
  batches carry status and an assignment default but no batch-wide review/QC
  gate. Ops submit-review and CT-QC decision are item-level; the existing
  customer review queue lists items.
- **Conclusion:** Consultant Review and Submit must be item-level. Batch-level
  submit is not evidenced by any existing mechanism and would require a new
  consistency rule (all items complete, none blocked). Partial batches are
  already possible (mixed item statuses) — keep that. CT-QC remains
  item-level; QC rejection returns individual items to rework without
  un-submitting the batch.

## 13. Rework Architecture

- Existing loops: blocking validation → `mapping` (issues recorded and
  resolved on clean runs); customer/QC rejection → `mapping`/`extracting`;
  machine extraction retry is distinct (automatic job `retry`/`confirm`,
  Gate 6); PE review/QC rejection loops within PE path.
- Who receives work after rejection: no assignment change occurs on rejection
  (rework returns to a state; availability to actors is re-derived by
  authorization + D38 on next request). Customer rejection reason is recorded
  (`rejection_reason`/notes); QC rejection records quality notes.
- **Proposed consultant rework model:** consultant review/submission failure or
  CT-QC `ct_qc_rejected` returns the item to `mapping`/`extracting` where the
  original consultant (still authorized, no open D38 assignment) or another
  authorized member resumes; audit events capture each loop with the human
  actor. Customer rejection remains distinct and customer-attributed; QC
  rejection is internal-attributed. No new mechanism required beyond existing
  transitions + a `consultant_review_rejected` (or route-to-mapping) mapping.

## 14. Authorization Architecture

Server-authoritative chain for each consultant review/submit action (each step
separate; none collapsed):

```text
identity → active consultant membership → active engagement (server-derived
org) → capability (review: can_review-equivalent action — see §21 decision;
submit: can_submit) → resource scope (item→batch→org) → workflow-state
eligibility (state machine) → D38 conflict (open assignment/batch default) →
commercial entitlement availability (non-charging) → action → mutation+audit
```

Reuse `ensure_consultant_processing_authorized` (extend `CONSULTANT_PERMISSIONS`
only if a review capability is added) — no parallel resolver. Enforce at API
(action), domain (transition map), DB/RLS (resource isolation), frontend
(presentation only).

## 15. Entitlement / Billing Architecture

1. Entitlement resolver: org subscription/credits resolved in
   `services/billing.py` at charge time (`charge_processing`,
   `batch.organization_id`).
2. Charge point: **customer approval only** (single call site in
   `customer_review_item`); pre-commercial orgs uncharged.
3. Consultant submission performs **no charge today** (no submission exists).
4. Consultant processing today is possible without an entitlement check
   (charges only at approval) — unchanged.
5. Non-charging availability check at submission: safe location is the new
   submit action/service before the state mutation, reading the client org's
   current entitlement (a read-only billing query — implement in P6-2D; a
   stub returning "available" would preserve D6 behaviour until then, or the
   check is added together with the submit action if PO prefers; design
   detail).
6. If unavailable at submission → deny submission (D6), no charge.
7. Approval remains the only actual charge; consultant subscription never
   substitutes (verified: no billing path keys on consultant identity).

## 16. Provenance Architecture

Gate 4–6 mechanisms reused: audit trail with authenticated actor,
item human stamps, write-once machine provenance, human-after-automation
attribution, calculation snapshots (`performed_by`/`source_item_id`),
immutable `processing_origin` set from batch carrier at claim/extract
(internal/PE only today).
P6-2B actions to record: consultant processing (already human-attributed),
Consultant Review, Consultant submit, CT-QC outcome, rework, customer
review/decision. Required attribution fields: actor user id, consultant firm
(additive `consultant_id` on audit payload — P6-2D), client org, processing
origin, action, status_from/status_to, resource, correlation id, reason/notes,
machine-vs-human. No provenance schema change in this gate.

## 17. RLS / API / Domain Enforcement Model

- **DB/RLS:** keep resource isolation (`is_org_consultant`-style scoping,
  deny-by-default); no new table; additive status vocabulary only. A future
  `consultant_review` state remains a column value — no RLS widening.
- **API:** every consultant review/submit action re-runs the canonical resolver
  (membership → engagement → capability → scope → D38) before mutation;
  entitlement availability check (non-charging) at submit.
- **Domain/service:** transitions enforced centrally by
  `can_transition_item_status` (extend `ITEM_STATUS_FLOW` additively); a shared
  processing service (mirroring `services/work_items.py`) should own the submit
  action so item-stage and automatic surfaces cannot drift.
- **Frontend:** presentation only; never an authority source.

## 18. Concurrency / Race Analysis

- Race A (assignment appears after open, before submit): re-check D38 in the
  same request as the submit mutation (authorization before mutation).
- Race B (engagement suspended right after submit): authority is per-request;
  recorded submission stays valid state; downstream QC/customer actions
  re-evaluate their own authorities.
- Race C (another process changes state): transition guard +
  row-conditional update (`UPDATE … WHERE id=$1 AND status=$2`) prevents stale
  transitions.
- Race D (entitlement changes before approval): charge at approval re-checks
  entitlement (existing fail-closed `charge_processing`).
- Race E (two firm members submit the same item): transition guard makes the
  second submit a 409; idempotent audit.
- Race F (QC rejects while consultant reworks): both go through the same
  transition guard; single-writer item status prevents conflicting outcomes.

## 19. Security Invariants

- **CT-CONS-REV-001** — Consultant Review only for active-engagement orgs.
- **CT-CONS-REV-002** — Consultant Review grants no CT-QC authority.
- **CT-CONS-REV-003** — inactive membership/engagement removes consultant
  workflow authority immediately (per-request re-check).
- **CT-CONS-SUB-001** — only active member of engaged firm with
  `can_submit=true` may submit.
- **CT-CONS-SUB-002** — submission never consumes/charges credits.
- **CT-CONS-SUB-003** — server-derived client/resource scope required.
- **CT-CONS-SUB-004** — open effective D38 assignment blocks submission unless
  a future Ops-controlled handoff releases it.
- **CT-CONS-SUB-005** — submission requires workflow-state eligibility
  (Consultant Review completion) — no bypass of the stage chain.
- **CT-CONS-QC-001** — Consultants never perform CarbonTally QC.
- **CT-CONS-APP-001** — Consultants never perform Customer Approval.

## 20. Existing-vs-Required Matrix

| Requirement | Existing | Partial | Missing | Risk | Future workstream |
| --- | --- | --- | --- | --- | --- |
| Consultant processing gates (P6-2A) | Yes (accepted) | — | — | — | closed |
| Consultant auto confirm/retry gate | Yes (R1) | — | — | — | closed |
| Consultant Review state/action | — | — | Missing | Low (absent, no bypass) | P6-2B impl |
| `can_submit` behaviour | flag exists | — | Missing | none (reserved) | P6-2B impl |
| Submit to CT-QC action | — | — | Missing | none | P6-2B impl |
| Entitlement availability at submit | — | charge at approval only | Missing | none (D6) | P6-2D |
| Consultant origin value | — | internal/PE only | Missing | none (submit feeds existing CT-QC gate) | P6-2B/P6-2D |
| Firm provenance | — | — | Missing | none | P6-2D |
| CT-QC boundary | Yes | — | — | — | preserved |
| Customer review/approval boundary | Yes | — | — | latent `calculated→approved` map entry (no endpoint) | P6-2C/D9 |
| D39/D40 consultant vocab | conversations exist | kinds/events | Missing | none | P6-2E |
| PE↔Consultant handoff | — | — | Missing (by design) | none (D38 deny default) | dedicated handoff |

## 21. Open PO / Design Items (do not block readiness)

- **P6-2B-P1 (policy, recommended):** may the item's *processing* consultant
  also perform Consultant Review on it, or must a different engaged firm
  member review (segregation)? Evidence: D5 says a consultant "may review
  their own applicable work"; CT QC is the independent gate. Recommended:
  allow self-review; segregation is provided by CT QC. Consequence: review
  needs member+engagement+state only. Does not block definition.
- **P6-2B-P2 (design):** how is Consultant Review capability represented given
  D1's closed six-flag set? Recommended: no new flag; the review action is
  gated by the same authorization surface (membership/engagement/state) and
  `can_submit` gates only the submit action. Consequence: no migration.
- **P6-2B-P3 (design):** consultant processing-origin representation
  (`CONSULTANT` value vs reuse `CARBONTALLY_INTERNAL`). Recommendation from
  the earlier P6-2 analysis: a distinct `CONSULTANT` origin; additive, affects
  only queues/labels/guard parity.
  - **Clarification (10 September 2026) — this recommendation is superseded.**
    The proposed `CONSULTANT` **`processing_origin` value is withdrawn** by the
    Product Owner (`PO-P6-2D-D7b-R-20260910`, recorded in
    `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`). `processing_origin` retains its
    established meaning: the **manual-processing capacity/control path**
    (CarbonTally internal vs Processing Entity). It is **not** actor identity,
    **not** processing mode and **not** a consultant vocabulary. A consultant is an
    **actor**; automatic vs manual processing remains an **independent dimension**.
    Only the **queue/label visibility and CT-QC guard-parity** aspects of this item
    remain relevant. Authoritative current definitions:
    `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §9 (*Processing model —
    dimensional clarification*), `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md`
    §4, and `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`.

## 22. Proposed Future Implementation Workstreams

- **P6-2B-1 — Consultant Review + Submit:** additive statuses
  (`consultant_review`, `consultant_reviewed`, optional
  `consultant_review_rejected`), submit action feeding the existing `ct_qc`
  gate, canonical-resolver reuse with `can_submit`, D38 deny, non-charging
  entitlement availability (stub-or-check), audit. Stop: state-machine +
  security negatives green.
- **P6-2B-2 — Origin + CT-QC guard parity:** consultant origin value and queue
  labelling; customer-review guard parity. Stop: guard negatives.
  - **Clarification (10 September 2026):** "consultant origin value" in this bullet
    is **withdrawn** — no `CONSULTANT` value is added to `processing_origin`
    (`PO-P6-2D-D7b-R-20260910`). What this workstream delivered and what remains
    applicable is **queue/label visibility** for consultant-processed work plus
    **customer-review guard parity**. `processing_origin` keeps its established
    meaning (manual-processing capacity/control path: CarbonTally internal vs
    Processing Entity); a consultant is an **actor**, and automatic vs manual
    processing is an **independent dimension**. **No P6-2B routing, QC or
    state-machine semantics are changed by this clarification.** Authoritative
    definitions: `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §9,
    `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4,
    `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`.
- **P6-2B-3 — Rework/resume hardening** for the QC-reject loop if required.
- **P6-2C — approval-boundary hardening** (latent `calculated→approved` map)
  + workflow finalisation.
- **P6-2D — entitlement availability + firm provenance.**
- **P6-2E — D39/D40 vocabulary.**
- **P6-2F — `/consultant` UI + E2E acceptance.**

## 23. Regression Requirements (post-implementation)

P6-2A, P6-2A-R1, v3_processing_workflow, automatic jobs/payload, ops, PE, D38
effective assignment, processing-origin/QC, customer review/approval, Gate
4/5/6 provenance suites, scope-aware authorization, P6-1B/1C, consultants —
plus new negatives: consultant cannot enter CT-QC or approve; cannot submit
without `can_submit`; cannot submit a D38-held item; internal/PE/customer
paths unchanged. Full `pytest tests/unit -q`.

## 24. Final Readiness Verdict

`P6-2B ARCHITECTURE READY — IMPLEMENTATION WORKSTREAM CAN BE DEFINED`

No security blocker exists; existing CT-QC and Customer Approval boundaries are
intact and verifiable; Consultant Review/Submit can be built additively on the
existing item state machine and D38 rules without changing Internal/PE/Customer
paths. Items P1–P3 (§21) should be settled at the start of the P6-2B
implementation workstream. No implementation begins until the PO accepts this
architecture.

---

*End of architecture gate. Read-only — no code, schema, migration, RLS, API,
test, workflow, billing, provenance, D38/D39/D40, UI or data was changed; no
fixtures; nothing committed or pushed.*






