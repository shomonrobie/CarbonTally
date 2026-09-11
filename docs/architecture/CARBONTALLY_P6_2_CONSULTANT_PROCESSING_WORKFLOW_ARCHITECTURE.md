# CarbonTally P6-2 — Consultant Processing Workflow Architecture & Capability Matrix

- **Date:** 2026-09-06
- **Status:** Read-only architecture / readiness assessment. No code, schema,
  migration, RLS, API, UI, test, workflow, billing, or D38/D39/D40 change was
  made. No fixtures were created and no data was mutated. Nothing was committed
  or pushed.
- **Architectural authorities (in order):**
  1. `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
  2. Ratified PO decisions: P6-0, P6-BILL-0, P6-BILL-1, P6-1B, P6-1C
     (including frozen amendments CT-CONSULT-001..004, CT-BILL-001..003,
     CT-QC-001..005, PE-ROLE-001, PE-MSG-001, D15, D19, D35, D37, D38, D39,
     D40)
  3. Existing implemented behaviour where it does not conflict with the above
  4. Existing tests as evidence of current behaviour

---

## 1. Executive Verdict

**`READY WITH PO DECISIONS`**

The consultant *relationship* architecture (identity → firm → active membership →
active client engagement → resource → action) is implemented, ratified and
security-tested (P6-1B, P6-1C). The client *processing* workflow surface that a
consultant may reach is also partly live today through the shared
`/api/v3/processing/*` surface (PO Decision 3 active-grant path). What is **not**
yet defined anywhere is the **consultant processing capability contract**: which
processing actions are consultant capabilities vs the four existing relationship
permission flags, which workflow stages a consultant may enter, how consultant
work interacts with D38 assignment and with Processing Entities (D5 handoff),
whose entitlement is consumed, and how consultant-processed work is submitted to
CarbonTally QC and then to customer approval. These require explicit PO
ratification (Section 12) before implementation.

**No implementation should begin until P6-2-D1…P6-2-D11 are ratified.**

---

## 2. Sources Inspected

**Architecture / policy documents**
- `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (§5 actors,
  §6 PE, §9 processing workflow, §10 automatic processing, §11 evidence/provenance,
  §13 authorization, §23 consultant/PE messaging, §31.3 CT-CONSULT/CT-BILL
  amendments, §32 authority rule, §33 undecided)
- `docs/architecture/CARBONTALLY_PHASE6_CONSULTANT_WORKFLOW_READINESS_REPORT.md`
  (4 Sep 2026 — prior Phase 6 readiness analysis and D-1…D-7 open decisions)
- `docs/architecture/CARBONTALLY_P6_1B_CONSULTANT_MEMBERSHIP_WORKSPACE_AUTHORIZATION.md`
- `docs/cline/CARBONTALLY_P6_1C_ENGAGEMENT_CONFIRMATION_REPORT.md`
- `docs/architecture/CARBONTALLY_P6_BILL_0_COMMERCIAL_ARCHITECTURE_RECONCILIATION.md`
- `docs/architecture/CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md`
- `docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md`
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`
- Phase 5 WS1–WS4 and WS4 Gate 3–6 implementation/acceptance reports (D38,
  D39, D40, Gate 4/5/6, processing-origin + CarbonTally QC)

**Code**
- `backend/api/consultant_auth.py` (context resolution, permission map,
  `ensure_consultant_org_access`)
- `backend/api/v3_consultants.py` (consultant routes incl. client workspace
  read surfaces and document upload)
- `backend/api/dependencies.py` (`ensure_org_access`, `ensure_processing_org_access`)
- `backend/api/v3_processing_workflow.py` (start/extract/map/validate/calculate/
  customer-review; `_get_checked_item`, `_require_transition`)
- `backend/api/v3_operations.py`, `backend/api/v3_pe.py`, `backend/api/v3_qc.py`,
  `backend/api/v3_review.py` (route inventories)
- `backend/services/work_items.py` + `supabase/migrations/20260902030000_phase5_work_item_assignments.sql`
  and `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` (D38)
- `backend/domain/partners.py` (item status vocabulary + state machine),
  `backend/domain/processing_origin.py`
- `backend/services/billing.py` (`charge_processing`, entitlement/credits/order
  logic)
- `backend/data/consultants.py`, `backend/data/manual_extraction.py`
- Live-schema read-only probes (policy/constraint/status/origin baselines)

**Tests (evidence of current behaviour)**
- P6-1C, P6-1B, v3_consultants, customer-admin, D19 lifecycle, P6-BILL-1,
  processing-origin/QC, Gate 4/5/6, D38/D39/D40, PE, customer-factor suites

---

## 3. Existing Architecture

### 3.1 Consultant identity / relationship (ratified, implemented)

- **Identity chain** (server-side, mirrored by RLS `is_org_consultant`):
  authenticated user → active `consultant_firm_members` row → single operating
  firm (`consultant_profiles`) → active `consultant_clients` grant for the
  target organisation (`ensure_consultant_org_access`, D15). Multiple distinct
  active firms are denied (P6-1B §11).
- **Permissions** are real columns on `consultant_firm_members`; evaluated by
  `ensure_consultant_permission`. The complete current map is only four flags:
  `manage_clients` (`can_manage_clients`), `manage_team` (`can_manage_team`),
  `upload_documents` (`can_upload_documents`), `generate_reports`
  (`can_generate_reports`). **There are no processing-action flags**
  (`can_extract/map/validate/calculate/review/submit`).
- **Engagement** (`consultant_clients`): P6-1C added additive states
  (`pending`, `rejected`), `relationship_origin`
  (`legacy` / `consultant_created_customer` / `engagement_request`) and decision
  provenance. Only `status='active'` grants client access. RLS now permits no
  authenticated INSERT/UPDATE on `consultant_clients`; all mutations are
  server-authoritative.
- **Client data/read surface** under `/api/v3/consultants`: client dashboard,
  reports list, documents list + upload (`can_upload_documents`, enqueues the
  durable automatic pipeline), **processing items (read)**, evidence (read),
  processing status (read), issues (read), client context. All client-data
  endpoints re-check the active grant per request.

### 3.2 Processing workflow (implemented)

- Canonical item table: `manual_extraction_items` with
  `manual_extraction_batches`; statuses and transition map in
  `domain/partners.py` (`pending → extracting → extracted → mapping → mapped →
  validating → validated → calculating → calculated → … review/QC/approval`
  with rework loops back to `mapping`/`extracting`).
- Dual-origin (V1.2): `CARBONTALLY_INTERNAL` path ends `reviewed → ct_qc →
  ct_qc_approved → customer_review → approved`; `PROCESSING_ENTITY` path inserts
  `pe_review → pe_qc → pe_qc_approved → ct_qc …`. CarbonTally QC
  (`ct_qc_approved`) is mandatory before customer approval for PE-origin work
  (guard in `customer_review_item`). Legacy `qc_approved/qc_rejected` markers
  are historical only.
- **Processing surfaces:**
  - `/api/v3/processing/*` (shared org-scoped workflow): start/extract/map/
    validate/calculate/customer-review + workspaces/queues. Gated by
    `ensure_processing_org_access` which admits (a) internal staff (any-org),
    (b) org members (own org), (c) **consultants with an ACTIVE grant** for the
    org (PO Decision 3), and denies PE staff. `customer-review` additionally
    requires `require_org_admin` (owner/admin only).
  - `/api/v3/operations/*` (internal Operations incl. item `work/claim|assign|
    reassign|recover|release|complete`, entity extraction routes, submit-review,
    CT-QC queue/decision).
  - `/api/v3/pe/*` (PE: own assigned work via effective assignment; start/
    extract/map/validate/calculate, pe-review, pe-qc, clarify, work claim/
    release/complete).
  - `/api/v3/qc/*` (CarbonTally QC surface).
- **Entitlement/charge** (P6-BILL-1): the only `charge_processing` call site is
  customer approval (`customer_review_item`), charged against
  `batch.organization_id` (the **client** organisation), fail-closed
  (idempotent key `charge:item:{id}`); organisations without an active
  subscription are not charged (pre-commercial).

### 3.3 Assignment (D38)

- `work_item_assignments` ledger over `manual_extraction_items`; `assignee_kind`
  CHECK is strictly `('internal_staff','processing_entity')`. Effective
  assignment = item open assignment, else batch default carrier
  (`manual_extraction_batches.entity_id` / `assigned_to`). Consultants are not
  an assignee kind and appear nowhere in D38.

### 3.4 Provenance (Gate 4–6), messaging (D39), notifications (D40)

- Item actor columns + audit trail (human attribution), automated-extraction
  write-once machine provenance (Gate 5), human-after-automation confirm/edit
  attribution (Gate 6), immutable `processing_origin`, calculation snapshots
  with `performed_by` + `source_item_id`.
- D39 conversations/messages/participants (org/entity scoped; PE ops messaging
  restricted); D40 notifications with recipient/event-key idempotency.

---

## 4. Consultant Capability Matrix

Legend — **Implemented** = exists today with an enforced server-side gate;
**Arch. recommendation** = recommended for P6-2 ratification (marked `R`);
**DECISION REQUIRED** = architecture is silent; `—` = not applicable.
Every row is resolved against `consultant_clients.status='active'` (D15) and,
where flag-gated, `consultant_firm_members.can_*`.

| Capability | Consultant allowed? | Required permission | Resource scope | Workflow stage | Preconditions | Authority boundary |
|---|---|---|---|---|---|---|
| View client (workspace/dashboard) | **Implemented** | none (active grant) | own-firm active-grant orgs | any | membership active; grant active | org access per request |
| View source documents | **Implemented** (list) + signed-view flow | none (active grant) | active-grant org docs | source | active grant | storage authz before signed URL |
| Upload documents (auto pipeline) | **Implemented** | `can_upload_documents` | active-grant org | source | active grant + flag | enqueues durable job |
| Extract data (manual data entry) | **Implemented (ungated by flag)** via `/processing/items/{id}/extract` | none today (`R`: `can_extract`) | active-grant org items | extraction | item in `extracted`-compatible state | `ensure_processing_org_access` only; **no D38/assignment check** |
| Edit extracted data | **Implemented** (same extract path / rework loop) | `R: can_extract` | same | extraction/mapping rework | state permits | above |
| Confirm/reject automation (G6) | **DECISION REQUIRED** | `R: can_confirm_automation` | active-grant org | post-auto-extraction | Gate 6 guard | confirm is a human action; rejected automation → manual state |
| Map activity | **Implemented (ungated)** via `/processing/items/{id}/map` | `R: can_map` | same | mapping | mapped-transition valid | above |
| Validate mapping | **Implemented (ungated)** via `/processing/items/{id}/validate` | `R: can_validate` | same | validation | validated-transition valid | issues/rework loop |
| Calculate | **Implemented (ungated)** via `/processing/items/{id}/calculate` | `R: can_calculate` | same | calculation | calculated-transition valid | engine computes; snapshot persisted |
| Review processing (consultant review) | **Not present** — no `consultant_review` stage | `R: can_review` or stage role | — | review | DECISION (distinct stage vs action) | cannot reach approval |
| Request rework | **Implemented** via reject-to-mapping paths on validate; customer reject is org-admin | same as action | same | validation/approval | state permits | rework routing server-side |
| Submit to CarbonTally QC | **Not present** for consultant origin | `R: can_submit` | active-grant org items | calculated/reviewed | DECISION (submission + CT QC gate) | Ops retains QC |
| CarbonTally QC | **No** | — | — | carbon_tally_qc | — | CT staff only (`/ops`, `/qc`) |
| Customer Review (read/verify surface) | **Not implemented** for consultant submit; customer review is customer action | `R: prepare/present` only | — | customer_review | DECISION | customers only |
| Customer Approval | **MUST NOT be Consultant-controlled** | — | — | approval | — | org owner/admin only (`require_org_admin`) |
| Manage client relationship | **Implemented** | `can_manage_clients` (+ Owner/Admin/Manager for revoke) | own firm rows | n/a | active membership | lifecycle policy (P6-1C origin-aware) |
| Assignment management (D38) | **No** | — | — | n/a | — | Ops only |
| PE/CT-QC/approval role cross-grant | **No** | — | — | — | — | role families never cross-grant |

Rows flagged **DECISION REQUIRED** are P6-2-D3/D4/D5/D9 in Section 12.

---

## 5. Workflow State / Transition Model

### 5.1 Current (implemented) canonical paths

```text
INTERNAL:    pending → extracting → extracted → mapping → mapped → validating →
             validated → calculating → calculated → reviewed → ct_qc →
             ct_qc_approved → customer_review → approved        (rework: → mapping/extracting)
PE:          … → calculated → pe_review → pe_reviewed → pe_qc → pe_qc_approved →
             ct_qc → ct_qc_approved → customer_review → approved
Customer:    approve/reject ONLY at customer_review (require_org_admin) —
             rejection returns item to mapping/extracting
```

Blueprint §9 lists only two origins (internal, PE). **Consultant-origin work has
no defined path** — the closest live equivalent today is an org member or
active-grant consultant driving the shared `/processing/*` stage actions
(extract/map/validate/calculate) on a batch whose `processing_origin` is
internal or PE, then a customer approving from `calculated`/`customer_review`.

### 5.2 Architectural recommendation (for ratification)

```text
Consultant-origin:  Extraction → Mapping → Validation → Calculation →
                    Consultant Review → CarbonTally QC → Customer Review →
                    Customer Approval
```

- Consultants may enter source→calculation for active-grant orgs (either as the
  human driving a consultant-uploaded auto pipeline, or manual entry).
- **Consultant Review** should be resolved by P6-2-D5: either a distinct
  workflow state (`consultant_review`/`consultant_review_approved`) or a pure
  permission acting before submission. A distinct state preserves the audit/
  provenance boundary and matches V1.2 stage philosophy.
- **CarbonTally QC remains CarbonTally-only** (CT-QC-001..005). Consultant-
  origin work must enter the CT-QC gate before customer review. A parallel of
  the PE-origin guard is needed (today the guard only inspects
  `processing_origin == 'PROCESSING_ENTITY'`).
- **Rework**: blocking validation and CT-QC/consultant rejection already route
  back to `mapping`/`extracting`; keep those loops.
- **Calculation reruns** must keep producing deterministic, idempotent,
  immutable snapshots and must not overwrite history (existing Gate 5/6 model).

### 5.3 Ambiguities requiring PO ratification

1. Whether consultant-origin work reuses `processing_origin` vocabulary
   (`CARBONTALLY_INTERNAL` vs a new `CONSULTANT`/`CONSULTANT_ASSISTED` origin) —
   CT-QC guard and queue labelling depend on it (P6-2-D5).
2. Whether the org-side `/processing/*` surface continues to admit org members
   (today it does), or whether customer manual entry is out of scope.
3. Whether QC-rejection returns consultant-origin work to the consultant or to
   Ops reassignment (assignment model dependency — P6-2-D4).

---

## 6. D38 Assignment Interaction

Current facts:
- `assignee_kind` is constrained to `('internal_staff','processing_entity')`.
- Effective assignment = open item assignment else batch default; PE visibility
  derived by the same rule (`work_item_effective_entity`). Claim/assign/reassign/
  recover/release/complete are Ops and PE surfaces only (`/ops/items/{id}/work/*`,
  `/pe/items/{id}/work/*`).
- **Consultants are absent from D38 entirely** — they are neither an assignee
  kind nor a caller of any assignment route.
- The org-scoped `/processing/*` surface does **not** consult
  `work_item_assignments` at all: `_get_checked_item` checks only org access
  (`ensure_processing_org_access`), never assignment or batch entity scope.

Answers to the P6-2 questions (current behaviour):

- **A. Consultant + unassigned work** — an active-grant consultant may act on any
  item of that org through `/processing/*`, including unassigned items
  (today: yes; policy: DECISION — recommend permitting only where Ops has not
  assigned the item/batch to a PE or staff queue).
- **B. Consultant + internal-staff assignment** — today: yes, technically
  possible on the `/processing/*` surface because assignment is not checked.
  This is an **enforcement gap** to close or explicitly ratify
  (recommendation: deny — internal-assigned work is Ops-owned).
- **C. Consultant + PE assignment** — today: yes via the same gap
  (org-scope check only). D5 **“Ops-controlled PE ↔ Consultant handoff”** is
  **not represented anywhere** — no handoff table, no route, no status, no
  `assignee_kind`, no audit event. If PE-assigned items must be
  consultant-visible at all, it must be through an explicit Ops-controlled
  handoff. **This is an architecture gap.**
- **D. Handoff / release / reassignment / recovery / audit / concurrency** —
  exists today **only for Ops↔PE and Ops↔internal-staff** via the D38 ledger
  (release/reassign/recover with `previous_*` history, single-open partial
  unique index for concurrency, `work_item:*` audit). No PE↔Consultant or
  Consultant↔PE analogue exists.

**Recommendation:** do **not** add `consultant` to `assignee_kind` unless a PO
decision (P6-2-D4) explicitly requires item-level assignment for consultant work.
Two coherent options are presented in P6-2-D4 (engagement-scoped processing vs
D38-native assignment).

---

## 7. Billing / Entitlement Model

Ratified principle (P6-BILL-0/1, D-7): **the client organisation owns processing
entitlement.** Current enforcement:
- The only consumption point is customer approval:
  `BillingService.charge_processing(batch.organization_id, …, idempotency_key,
  actor)` in `customer_review_item` (v3_processing_workflow) — fail-closed for
  subscribed orgs, no charge for pre-commercial orgs.
- `organization_id` is read from the server-loaded batch, never from the client
  payload → **no billing/entitlement substitution**.
- Entitlement/credits/subscription/usage are resolved against the client
  organisation (`billing_plans`, `billing_commercial_config`, subscriptions,
  `billing_credit_ledger`, `billing_usage`). Credit ledger rows are
  organisation-owned.

Consultant-specific answers:
- **Which organisation is charged / whose subscription and credits are checked:
  the client organisation.** Consultant membership or a hypothetical consultant
  commercial plan never substitutes for the client org's processing entitlement.
- **Consultant commercial entitlement vs client processing entitlement are
  separate axes** (blueprint §5.2, CT-CONSULT amendments; organisation↔firm
  commercial binding is still deferred — P6-1B §4 “D-C”). No consultant plan is
  bound to a firm today.
- **Can a consultant process a client with no active processing entitlement?**
  Today processing actions are not entitlement-gated (no charge until approval),
  so technically yes for pre-charge work. Only approval fails closed. This is
  architecturally sufficient **only if** the PO accepts entitlement enforcement
  at approval for consultant-assisted work too. Because consultant-performed
  processing is a paid advisory service distinct from the automated pipeline,
  decide whether earlier consumption/entitlement checks are needed
  (P6-2-D6). Keep the concepts separate:
  *authorization* (active grant) ≠ *consultant commercial entitlement* (firm
  plan, unbound) ≠ *client processing entitlement* (org subscription/credits)
  ≠ *credit balance* ≠ *payment*.

---

## 8. Provenance Model

Gate 4–6 structures already support consultant actions **as human actor actions**:
- Actor = authenticated `current_user.user_id` (never client-supplied); audit
  entries carry the actor and `actor_domain`; item columns record the human
  (`extracted_by`, `reviewed_by`, `qc_by`, `customer_reviewed_by` …).
- Organisation = server-loaded `batch.organization_id`.
- Automation = write-once machine extraction provenance (Gate 5) — a consultant
  cannot rewrite it.
- Human-after-automation = Gate 6 confirm/edit/retry attribution with
  immutable history; consultant edits of automated output must go through the
  same G6 guards.
- `processing_origin` is immutable and set once at claim/extract from the batch
  carrier.

**Gap (P6-2-D7):** the **consultant firm** is not recorded on item/snapshot
provenance columns. The chain “which Consultant firm employed the acting
member” is today derivable only by resolving the actor's active membership at
read time, which would misattribute if the member later changes firms. Options:
(a) record `consultant_id`/`firm_id` at action time on the audit/provenance
record; (b) derive via membership at read time with the documented single-firm
limitation; (c) extend `processing_origin` vocabulary. Recommend (a) for
auditable “who performed it, for which client, under which firm”.

Existing evidence chain (source → extracted value → mapped activity → factor →
calculation → immutable snapshot → review/QC → approval) is fully reusable for
consultant-origin work; the snapshot's `performed_by`/`source_item_id` model is
actor-agnostic.

---

## 9. D39 / D40 Integration

- **D39 Messaging:** reuse the existing conversations/messages/participants
  model with org-scoped conversations and RLS participation derived from the
  ACTIVE consultant grant (consultant participation is already admitted in the
  messaging domain; PE participation stays Ops-only per PE-MSG-001). No new
  messaging architecture.
- **D40 Notifications:** reuse recipient-scoped, event-key-idempotent
  notifications (existing pattern: `work_item.assigned`, review/QC events).
- **Required new event/conversation vocabulary (P6-2-D8/D11):**
  - a consultant conversation kind (if D-6 requires distinction) and participant
    derivation for firm members acting on the engagement;
  - notification events for consultant processing lifecycle: request pending /
    accepted (P6-1C), consultant processing started/submitted, CT-QC outcome,
    customer rejection/approval, rework required — each recipient-scoped
    (firm members, org owner/admin, Ops QC assignee) and idempotent.

---

## 10. Security / Authorization Matrix

Canonical mapping for every proposed consultant processing action:

```text
Identity → Consultant Firm (single, active) → Active Firm Membership →
Active Client Engagement (consultant_clients.status='active',
relationship_origin any, decision provenance intact) → Resource Scope
(org-scoped items/batches/docs of the engaged org) → Action Permission
(server-side: four can_* flags today; processing flags pending ratification) →
Workflow State (state machine permits transition) → Assignment/Ownership
Constraint (D38 internal_staff|processing_entity — today NOT enforced on the
org/consultant processing surface → GAP) → Processing Entitlement (client org
subscription/credits at approval)
```

Authority-source checks (current evidence):
- Frontend state, route paths and client-supplied org/client/item ids are never
  authority: every endpoint re-resolves via `require_consultant` +
  `ensure_consultant_org_access` (active grant) or `ensure_processing_org_access`
  (org member / active-grant consultant / internal staff); actors are taken from
  `AuthUser`, never payloads.
- IDOR / cross-client / cross-firm / inactive-member / pending-engagement /
  terminated-engagement denials are covered by P6-1B + P6-1C tests (22 + 27
  tests) and by client-boundary tests in v3_consultants.
- PE-assigned-work bypass: **possible today** on `/processing/*` for an
  active-grant consultant (no assignment check) — reported as an enforcement
  gap (Section 6, P6-2-D4).
- Customer-approval bypass: **not possible** — approval requires
  `require_org_admin`; a consultant is never an org admin; no consultant route
  can write `approved`. The transition map technically permits
  `calculated → approved`, but only `customer_review_item` (org-admin gated)
  issues that transition today. Preserve this under any P6-2 submit flow
  (P6-2-D9).
- Forged actor attribution: actor always from authenticated user.
- Client-organisation substitution / billing substitution: org id read from the
  server-loaded batch; `charge_processing` keys entitlement/credits to
  `batch.organization_id`.

---

## 11. Architecture Gaps

1. **G1 — No consultant workflow path in the blueprint.** Blueprint §5.2/§9
   define internal and PE origins only; consultant-origin processing
   (and its CT-QC/approval boundary) is undefined at the authority level.
2. **G2 — No consultant processing permission flags.** Only four relationship
   flags exist; the shared `/processing/*` surface already lets active-grant
   consultants extract/map/validate/calculate **without any processing flag** —
   inconsistent with the P6-1B permission model.
3. **G3 — D38 assignment not enforced on the org/consultant processing
   surface.** Consultant action is gated only by org access; internal-staff- or
   PE-assigned items can be operated by an active-grant consultant (batch/
   item-level), and conversely unassigned items have no ownership rule for
   consultants.
4. **G4 — No PE↔Consultant handoff (D5) representation.** No handoff state,
   route, `assignee_kind`, or audit event exists.
5. **G5 — No submit-to-CT-QC path and no consultant review state for
   consultant-origin work.** CT-QC guard inspects only `PROCESSING_ENTITY`
   origin; a consultant origin would bypass that guard if added naively.
6. **G6 — Entitlement enforcement only at customer approval.** Pre-approval
   consultant processing is not entitlement-gated; decide whether that is
   sufficient (D6). No firm-level commercial binding exists (D-C deferred).
7. **G7 — Consultant firm absent from provenance.** Acting member's firm is not
   recorded on item/snapshot/audit provenance.
8. **G8 — No consultant conversation kind or processing notification event
   vocabulary** for D39/D40.
9. **G9 — Org-side surface admits org members** (not just owners/admins and
   consultants) to extraction/mapping/calculation stage actions; scope of
   customer manual entry needs an explicit decision.
10. **G10 — Approver-authority surface.** Legacy transition map permits
    `calculated → approved` and `ct_qc_approved → approved`; only the
    org-admin-gated customer-review route issues approvals today, but the
    future consultant submit flow must not widen the set of routes that can
    reach `approved`.

---

## 12. PO Decisions Required

- **P6-2-D1 — Consultant processing capability set & flags.** Question: which
  processing actions become real consultant capabilities and their permission
  flags (`can_extract`, `can_map`, `can_validate`, `can_calculate`,
  `can_confirm_automation`, `can_submit`)? Evidence: only four relationship
  flags exist; `/processing/*` already admits active-grant consultants without
  flags (G2). Options: (a) add additive flag columns and gate every action;
  (b) gate actions on engagement + role only, no new flags; (c) hybrid
  (flags for destructive/submit actions). Recommended: (a) — matches P6-1B.
  Consequence: schema columns, permission map, negative tests.

- **P6-2-D2 — Which organisations may a consultant process.** Question: Case A
  (consultant-created customers), Case B (pre-existing orgs that accepted the
  engagement), and legacy rows — all active-grant orgs? Evidence: P6-1C unified
  the active-grant boundary across all `relationship_origin` values.
  Recommended: all active-grant orgs, per-request re-checked. Alternatives:
  restrict Case A only; or add origin-dependent processing scope. Consequence:
  scope of every future route.

- **P6-2-D3 — D38 interaction for consultant work.** Question: may an
  active-grant consultant process unassigned items? Items assigned to internal
  staff? Items assigned to a PE (with what handoff)? Evidence: no assignment
  check exists on the org surface (G3, Section 6). Recommended: consultants act
  only on items not currently open-assigned to internal staff/PE (i.e., deny on
  any open D38 assignment unless an explicit Ops-controlled handoff exists), and
  a new rule for unassigned items owned by the org's engaged workflow.
  Alternatives: engagement-scoped processing with a deny-rule vs D38-native
  assignment. Consequence: guard position in the processing service + tests.

- **P6-2-D4 — PE↔Consultant handoff representation (D5).** Question: is D5
  realised by adding consultant-visible handoff on the D38 ledger, by a
  separate explicit handoff state, or is PE↔Consultant handoff out of scope
  (Ops routes reassignment only)? Evidence: no representation exists (G4).
  Recommended (if in scope): Ops-controlled release from PE + assignment to the
  consultant's org workflow, expressed as explicit audit + a new
  (non-`assignee_kind`) engagement-bound scope, NOT `assignee_kind='consultant'`
  unless item-level queuing is ratified. Consequence: schema/route decisions.

- **P6-2-D5 — Consultant review & submit stage model.** Question: is
  Consultant Review a distinct state or a permission; and what status
  sequence leads to CT-QC submission for consultant-origin work (incl. a
  `processing_origin` value)? Evidence: no consultant stage exists; CT-QC guard
  keys on `PROCESSING_ENTITY` (G1, G5). Recommended: distinct
  `consultant_review` status + origin `CONSULTANT` (or explicit reuse of
  `CARBONTALLY_INTERNAL`) and a submit action that moves work into `ct_qc`.
  Consequence: state-machine vocabulary + guard extension + queue labels.

- **P6-2-D6 — Entitlement/charge timing for consultant-performed work.**
  Question: keep entitlement at customer approval only, or add an earlier
  entitlement check when consultant processing begins? Evidence: only approval
  charges today, org-owned (Section 7). Recommended: entitlement check at
  approval (client org) remains canonical; add a non-charging availability check
  at consultant submission only if capacity visibility is required. Consequence:
  billing call-site/check placement; no change to ownership.

- **P6-2-D7 — Provenance firm dimension.** Question: how is “which Consultant
  firm acted” recorded? Evidence: actor+org recorded; firm absent (G7).
  Recommended: record consultant firm at action time on the relevant
  provenance/audit payload (additive, no reinterpretation of existing
  columns). Alternatives: derive at read time; extend processing_origin.
  Consequence: additive provenance field + migration.

- **P6-2-D8 — Consultant conversation kind (D39).** Question: add a consultant
  conversation kind distinct from customer/ops/PE, or reuse customer-scoped
  conversations with firm participants? Evidence: messaging model exists with
  active-grant consultant participation; kinds not enumerated in the inspected
  domain module. Recommended: reuse org conversations with participant
  derivation from active grants; add kind only if reporting requires it.
  Consequence: messaging vocabulary; UI filters.

- **P6-2-D9 — Customer approval boundary hardening.** Question: confirm that
  final customer approval is exclusively customer owner/admin, that consultants
  only submit, and that no automatic transition (calculation, CT-QC approval,
  consultant submission) can reach `approved`. Evidence: only the org-admin
  customer-review route writes `approved`; transition map has latent
  `calculated→approved`. Recommended: ratify and add regression guards + tests
  preserving the invariant through P6-2 implementation. Consequence: negative
  tests in every P6-2A–F workstream.

- **P6-2-D10 — Org-member manual-processing scope (G9).** Question: keep org
  members on the shared `/processing/*` surface or restrict stage actions to
  owners/admins + consultants? Evidence: members admitted today. Recommended:
  preserve today's behaviour unless a PO reason exists to restrict.
  Consequence: scope of D6/D9 changes.

- **P6-2-D11 — Notification event vocabulary (D40).** Question: which
  consultant processing events must exist and to whom? Evidence: event-key
  idempotent model exists; consultant lifecycle events missing (G8).
  Recommended: enumerate events in P6-2E (request accepted, submitted to CT-QC,
  QC outcome, customer decision, rework). Consequence: event constants,
  recipient derivation, tests.

---

## 13. Recommended Implementation Sequence

Small, additive workstreams, each gated on ratification and with negative-test
acceptance. No workstream may add a consultant path to Customer Approval.

- **P6-2A — Authorization contract.** Ratified D1/D2/D3/D10: consultant
  processing permission flags (additive columns), action gating, org-scope
  rules, D38 conflict deny-rule on the org/consultant surface. Stop: negative
  matrix (assigned/PE-assigned/cross-org/cross-firm) green.
- **P6-2B — Consultant processing action surface.** Consultant-route processing
  actions (extract/map/validate/calculate/confirm) reusing the shared engines,
  provenance and G6 guards; consultant-origin `processing_origin` extension
  (D5). Stop: provenance + origin acceptance per scenario.
- **P6-2C — Consultant review + submit to CarbonTally QC** (D5/D9): consultant
  review state, submit action into `ct_qc`, CT-QC guard for consultant origin.
  Stop: submit/QC boundary negatives green; approval stays customer-only.
- **P6-2D — Entitlement & provenance finalisation** (D6/D7): entitlement check
  placement, consultant-firm provenance field.
- **P6-2E — D39/D40 consultant vocabulary** (D8/D11): conversation kind (if
  ratified) + notification events.
- **P6-2F — `/consultant` processing UI + E2E security acceptance** (D19/D21).
  Stop: full persona matrix incl. section-10 threats.

> **Documentation amendment (10 September 2026) — "consultant origin" terminology.**
> Wherever this document refers to *"consultant origin"*, *"consultant-origin work"*
> or a *"consultant-origin `processing_origin` extension"* (including §5.3 item 1 and
> the P6-2B bullet above), these phrases mean **provenance and queue/label context for
> work processed by a consultant** — they are **not** a proposal to add a value to the
> `processing_origin` column.
>
> `processing_origin` identifies the manual-processing **capacity/control path**
> (CarbonTally internal vs Processing Entity) and is not actor identity and not
> processing mode. The Product Owner has **withdrawn** the proposed `CONSULTANT`
> `processing_origin` value (see `CARBONTALLY_P6_2_PO_DECISION_REGISTER.md`, decision
> `PO-P6-2D-D7b-R-20260910`); the origin vocabulary, its CHECK constraint and its
> origin→stage routing are unchanged.
>
> Authoritative references: `CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md` §4
> (origin model) and `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §9
> (*Processing model — dimensional clarification*, incl. the actor/mode matrix).
> This note clarifies terminology only; it does not alter the consultant workflow
> design in this document.

---

## 14. Verification Plan (post-implementation)

- **Unit/API:** every new consultant processing route positive (active grant,
  flag) and negative (no grant, pending/rejected/ended engagement, inactive
  member, cross-firm, cross-org, internal-assigned, PE-assigned, PE user, Ops
  user, unauth); actor-forgery and org-substitution rejection; customer-approval
  denial for consultants; billing org-keyed charge checks.
- **Workflow:** state-machine acceptance for consultant path
  (extract→…→calculate→consultant review→ct_qc→ct_qc_approved→customer_review→
  approved) plus rework loops; CT-QC guard for consultant origin; idempotent
  calculation reruns; immutable snapshot/evidence assertions.
- **Provenance:** Gate 4/5/6 invariants on consultant actions (human actor,
  write-once automation, human-after-automation attribution, firm dimension).
- **Regression:** automatic processing, manual extraction, D38, D39, D40,
  Gate 3–6, P6-1B/P6-1C, PE, customer-approval suites.
- **DB baseline:** exact before/after counts for `consultant_clients`,
  `manual_extraction_items`, `work_item_assignments`, billing tables; fixtures
  cleaned; RLS unchanged unless a ratified decision requires an additive change.

---

*End of report. Read-only task — no code, schema, migration, RLS, API, UI,
workflow, billing, D38/D39/D40, seed/demo data or test was changed; no fixtures
created; nothing committed or pushed.*












