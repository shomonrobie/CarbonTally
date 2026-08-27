# CarbonTally V3 — Product Owner Decision Register (v1)

> **REFERENCE COPY — AUTHORITATIVE SOURCE REMAINS IN `docs/ChatGPT/`**
>
> This is a copy included for review convenience only. The authoritative
> register is `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`.
> If the two differ, the `docs/ChatGPT/` source wins. No competing version is
> created by this package.

| | |
|---|---|
| Document type | Product Owner decision register (authoritative) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | **D1–D21 = APPROVED / FROZEN** |
| Date | 2026-08-24 |
| Authority | Product Owner (approved baseline); reconciled by the CarbonTally V3 Product Documentation & UX Reconciliation agent |
| Supersedes | Earlier product/UX decision drafts (older documents remain as historical evidence) |

## 1. Purpose and authority

This register is the single authoritative record of the approved CarbonTally V3
product decisions **D1–D21**. All decisions are **APPROVED / FROZEN**: they are
not to be re-opened, re-litigated or re-numbered.

The register records, for each decision: the decision, status, rationale,
UX consequence, implementation consequence, dependencies, and the historical
reference that preserves the supporting evidence.

Source-of-truth hierarchy (binding):

1. This Product Owner Decision Register (D1–D21).
2. Explicit Product Owner decisions in the current task.
3. `MASTER_UX_RECOMMENDATION.md` (approved reconciliation decisions).
4. Approved UX/design documents in `docs/audit/openhands/ui-ux/`.
5. Current application / database / API implementation.
6. Earlier audits and historical reports.
7. Older / superseded documents.

An older document never overrides a newer explicit Product Owner decision.
Where a conflict was found, the reconciliation is recorded explicitly in
`docs/audit/openhands/ui-ux/MASTER_UX_DECISION_RECONCILIATION_REPORT.md`.

## 2. D1–D21 status summary

| Decision | Title | Status |
|---|---|---|
| D1 | Viewer Permissions | **APPROVED / FROZEN** |
| D2 | Customer Processing Participation | **APPROVED / FROZEN** |
| D3 | Consultant Operating Model | **APPROVED / FROZEN** |
| D4 | Owner vs Admin Model | **APPROVED / FROZEN** |
| D5 | Customer Approver Role | **APPROVED / FROZEN** |
| D6 | Processing Entity Validation / Review / QC | **APPROVED / FROZEN** |
| D7 | Report Model | **APPROVED / FROZEN** |
| D8 | Multi-Organisation Consultant Context | **APPROVED / FROZEN** |
| D9 | Custom Emission Factors | **APPROVED / FROZEN** |
| D10 | Invitation Acceptance | **APPROVED / FROZEN** |
| D11 | Payment Provider | **APPROVED / FROZEN** |
| D12 | Public Pricing / Currency | **APPROVED / FROZEN** |
| D13 | Waitlist / Public Acquisition | **APPROVED / FROZEN** |
| D14 | Consultant Acquisition | **APPROVED / FROZEN** |
| D15 | Data Retention | **APPROVED / FROZEN** |
| D16 | AI Provider / AI Governance | **APPROVED / FROZEN** |
| D17 | Organisation Master Data | **APPROVED / FROZEN** |
| D18 | Workflow-First Authenticated Navigation | **APPROVED / FROZEN** |
| D19 | Split-Screen Processing Workbench | **APPROVED / FROZEN** |
| D20 | Responsive / Mobile Strategy | **APPROVED / FROZEN** |
| D21 | Unified CarbonTally Design System | **APPROVED / FROZEN** |

## 3. D1 — Viewer Permissions

- **Decision.** Record the approved viewer-permission model from the existing
  decision evidence. Customer org **viewers** are read-only members of the
  organisation tenant. They may view dashboard/org data, documents, processing
  state, emissions history, reports and evidence. They **cannot** mutate org
  master data, manage members, create extraction work, approve/reject, or
  access any other organisation. Consultant firm **viewers** are read-only firm
  members whose client access is grant-gated. No additional permission is
  invented.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §3
  (A4 org viewer, A12 consultant viewer), §13 (customer access matrix),
  §14 (consultant access matrix); `organization_members.role` CHECK
  (`owner|admin|member|viewer`).
- **UX consequence.** Customer viewer sees the same workflow-first navigation as
  other customer roles but with mutation controls hidden/disabled and an
  explicit read-only affordance.
- **Implementation consequence.** `require_org_member` read paths already permit
  viewer reads; admin/mutation guards already deny. No new permission surface.
- **Dependencies.** D18 (navigation), D21 (design system: read-only states).
- **Historical reference.** Actor/Workspace/Access Model §3, §13, §14, §16.

## 4. D2 — Customer Processing Participation

- **Decision.** Record the approved customer participation model. Distinguish
  clearly: customer **decision-making** (scope, factor approvals, approval of
  final results), customer **review** (inspect extracted/mapped/calculated data
  and evidence), customer **approval** (formal approve/reject on results),
  CarbonTally **operational processing** (internal staff pipeline), and
  Processing Entity **operational processing** (assigned work only).
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: five-layer approval separation in the V3
  architecture (worker submission ≠ entity approval ≠ CarbonTally validation ≠
  customer approval); `customer_verifications` as the customer-approval layer
  (ADR-V3-008); `ITEM_STATUSES` includes `customer_review`,
  `approved`, `rejected`; `v3_processing_workflow.py` `customer-review` route.
- **UX consequence.** The customer UI separates "review" (read + comment) from
  "approve/reject" (decision). Approve/reject is a distinct, guarded action,
  never collapsed into extraction/mapping/validation/QC.
- **Implementation consequence.** Customer review and approval are distinct
  API operations with distinct permissions and audit records.
- **Dependencies.** D5, D6, D18, D19.
- **Historical reference.** ADR-V3-008; Actor/Workspace/Access Model §16;
  `backend/domain/partners.py`.

## 5. D3 — Consultant Operating Model

- **Decision.** Record the approved consultant active-client model. A
  consultant works across approved client organisations one active client at a
  time; the active client is always explicit; organisation isolation and the
  one-account-one-role principle are preserved.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: consultant firm model
  (`consultant_profiles`, `consultant_firm_members`, `consultant_clients`);
  active client stored frontend-local (`localStorage('v3_consultant_active_client')`)
  and re-authorised server-side per request; D15 active-grant enforcement
  (RLS + API); D21 hybrid commercial model (consultant-led managed service).
- **UX consequence.** Consultant workspace always shows the active client
  context in a persistent banner; client switching is explicit; no ambiguous
  cross-organisation state is possible.
- **Implementation consequence.** Server re-authorizes the client id on every
  request (`_checked_client` + `ensure_consultant_org_access`).
- **Dependencies.** D8, D21 (design system: active-client banner).
- **Historical reference.** Actor/Workspace/Access Model §7–§8, §14, §34, §37.

## 6. D4 — Owner vs Admin Model

- **Decision.** Maintain a clear distinction between organisation **owner**,
  organisation **administrator**, CarbonTally **staff**, and CarbonTally
  **admin**. Organisation administration is never collapsed into platform
  administration, and vice versa.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: four independent role families in the access model
  (§10) — org roles (`owner|admin|member|viewer`), staff roles
  (`operator|reviewer|qc_specialist|admin`), consultant firm roles, and
  derived `AuthUser` roles. `require_org_admin` treats owner=admin for org
  mutations (P1-F4) but the concepts remain distinct surfaces.
- **UX consequence.** Customer "Organisation" surface is org-scoped
  (profile/members/facilities/assets/suppliers/security). CarbonTally
  admin surfaces live in the ops/admin estate. A customer owner is never a
  platform admin.
- **Implementation consequence.** Distinct guard families:
  `require_org_admin` vs `require_admin`/`require_staff`.
- **Dependencies.** D18, D21.
- **Historical reference.** Actor/Workspace/Access Model §10–§12, §15.

## 7. D5 — Customer Approver Role

- **Decision.** Customer approval is a distinct responsibility in the
  workflow. It is not merged with extraction, mapping, validation or QC unless
  the approved access model explicitly permits that action.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: `ITEM_STATUSES.customer_review → approved|rejected`;
  `customer_verifications` approval surface (ADR-V3-008); the five-layer
  approval separation requirement.
- **UX consequence.** The approval surface presents the evidence chain,
  calculation snapshot and change history before an Approve/Reject decision;
  the approver action is visually and semantically distinct from QC.
- **Implementation consequence.** Approval endpoints are separate from
  extraction/mapping/validation endpoints and write audit records.
- **Dependencies.** D2, D7, D21.
- **Historical reference.** ADR-V3-008; `backend/api/v3_processing_workflow.py`.

## 8. D6 — Processing Entity Validation / Review / QC

- **Decision.** Record the approved Processing Entity (PE) responsibility
  model. PEs perform assigned processing work (extraction, mapping, structured
  entry, per-assignment validation/review); CarbonTally retains the quality
  chain (CarbonTally QC, internal review) and the PE **no-download boundary**.
  PEs never gain customer/consultant access or customer-facing communication.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: ADR-V3-001 (dedicated `processing_entities`;
  `entity_id IS NULL` = internal); D18 boundary (non-customer-facing
  back-office processor, CarbonTally-mediated communication); D22 implemented
  batch-level entity assignment + entity extraction workspace; entity-scoped
  RLS.
- **UX consequence.** PE users get an entity-scoped work surface (assigned
  batches/items, extraction/mapping/calculation, mediated clarification via
  entity-scoped issues). They never see the customer workspace, org members,
  consultants, reports, billing, or general messaging.
- **Implementation consequence.** `require_entity_scope` +
  `ensure_entity_batch_access`; entity SELECT RLS storeys; no entity write
  policies; source documents remain view-only with no download for entity
  staff (signed URLs / sandboxed viewer).
- **Dependencies.** D2, D5, D19, D20.
- **Historical reference.** ADR-V3-001; Actor/Workspace/Access Model §6, §30–§33, §35.

## 9. D7 — Report Model

- **Decision.** CarbonTally provides reporting based on processed data,
  calculations and evidence. CarbonTally is **not** positioned as an
  unsupported independent assurance, audit or certification authority.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: D37/D36 reports; public site copy
  ("a carbon accounting and data-processing platform"); `REPORT_STATUSES`;
  report branding context (D21 white-label). No assurance/audit claims exist
  in the implementation.
- **UX consequence.** Reports present calculated, evidenced results with a
  clear provenance chain; UI copy avoids "certified", "assured", "audited",
  "guaranteed compliance" language.
- **Implementation consequence.** Report generation stays a data/evidence
  output surface; no certification engine is added.
- **Dependencies.** D16, D21, D33 evidence trail.
- **Historical reference.** `REPORT_STATUSES`; `docs/audit/cline/CARBONTALLY_V3_D30_REPORTING_COMPLETENESS_REPORT.md`.

## 10. D8 — Multi-Organisation Consultant Context

- **Decision.** Consultants may operate across approved client organisations
  according to the active-client model. Organisation context must always be
  explicit; cross-organisation ambiguity is never allowed.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: `consultant_clients` grants; active-client
  frontend-local context; server-side per-client re-authorization.
- **UX consequence.** Every consultant screen shows which client org is active;
  data shown is always scoped to that client.
- **Implementation consequence.** Same as D3 (server re-auth per request).
- **Dependencies.** D3, D21.
- **Historical reference.** Actor/Workspace/Access Model §7–§8.

## 11. D9 — Custom Emission Factors

- **Decision.** Record the approved custom-factor management permissions.
  Customer factors are org-scoped, managed through a dedicated surface, and
  follow deterministic precedence (**approved customer factor → CarbonTally
  factor → unresolved/manual review**). Selection is server-authoritative;
  traceability is preserved via `calculation_snapshots` provenance
  (`factor_source='CUSTOMER'`, snapshot FK Option O1).
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: ADR-V3-002 (D-cf-2 O1, D-cf-3 org Admin/Owner
  approval, D-cf-5 precedence, R3 consultant access via existing
  consultant-client RLS); `customer_factors` migration (V3M-3).
- **UX consequence.** Customer "Custom Factors" surface lists factors with
  lifecycle (DRAFT → ACTIVE → ARCHIVED), approval state, and usage evidence;
  staff cannot approve their own factors; factor values are never silently
  replaced.
- **Implementation consequence.** ~7 additive routes + matching/calculation
  extension + snapshot provenance.
- **Dependencies.** D21, D16.
- **Historical reference.** ADR-V3-002/014; `20260810020000_v3m3_customer_factors.sql`.

## 12. D10 — Invitation Acceptance

- **Decision.** Record the complete invitation lifecycle: invite → accept →
  membership activation; no invitation dead-end. A user with no
  org/staff/consultant relationship lands on onboarding, never an empty dead
  end.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: `pending_invites`, `user_invitations`,
  `organization_members`; D35 self-service onboarding redirect for
  relationship-less authenticated users (`V3Layout` → `/onboarding`);
  Members tab invitation management.
- **UX consequence.** Invitation emails/links resolve to a working acceptance
  surface; acceptance activates the membership; every authenticated state has
  a next action.
- **Implementation consequence.** Invitation acceptance routes exist and the
  "no relationship" state redirects to onboarding.
- **Dependencies.** D18, D21.
- **Historical reference.** D35; `V3Layout.jsx`; Members tab.

## 13. D11 — Payment Provider

- **Decision.** Record the approved billing/payment direction based on current
  evidence. Billing is **provider-neutral**; no payment-provider integration
  has been performed and none is claimed. D37 delivered subscriptions,
  entitlements, credit ledger, orders and provider-neutral payment records;
  provider adapters (PayPal / Wise / card) are a future addition behind the
  provider-adapter interface.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: D36 audit (hard-coded Stripe columns flagged;
  provider-neutrality required), D37-0/D37 (provider-neutral implementation,
  "No payment-provider integration was performed").
- **UX consequence.** The customer Billing page shows plan, mode, credits,
  orders and payment intent status — without implying a live payment
  provider.
- **Implementation consequence.** `billing_payment_records` is
  provider-neutral; adapters plug in later without touching the
  ledger/order/subscription model.
- **Dependencies.** D12, D21.
- **Historical reference.** D36, D37-0, D37 reports.

## 14. D12 — Public Pricing / Currency

- **Decision.** Public pricing and currency behaviour must be consistent
  across Pricing, FAQ, Services, and authenticated billing. No invented
  pricing claims. The approved public direction is **GBP (£) indicative
  pre-launch pricing** (Starter £49 / Professional £149 / Business £399 /
  Enterprise Custom) consistent with the D37 commercial model, presented as
  indicative pending final commercial terms.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: live pricing page and landing page pricing section
  (GBP, credit model, "indicative … subject to final commercial terms");
  D37 plan/credit architecture; the committed `PricingPage.jsx` baseline
  variant (USD, proposed) is superseded by the GBP indicative direction.
- **UX consequence.** All public pricing surfaces and the authenticated
  billing surface use the same currency and plan vocabulary.
- **Implementation consequence.** No live checkout; launch access by
  arrangement.
- **Dependencies.** D11, D13.
- **Historical reference.** Live `/pricing`; `docs/Pricing/*`.

## 15. D13 — Waitlist / Public Acquisition

- **Decision.** Do not retain fake or misleading waitlist behaviour. Public
  acquisition UX must correspond to actual product behaviour. The approved
  direction is **pre-launch acquisition by arrangement**: "Request launch
  information" (contact-led), self-service signup with immediate onboarding
  (D35), and an optional beta/invite path preserved as a controlled-cohort
  admin mechanism.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: D35 self-service signup replaces the beta-code gate
  on `/signup`; the committed baseline `LandingPage.jsx` still contains a beta
  waitlist modal (historical); the live site uses "Request launch information".
- **UX consequence.** No "join the waitlist" dead ends; acquisition CTAs lead
  to signup or contact.
- **Implementation consequence.** `/signup` → self-service onboarding;
  `/beta/signup` optional.
- **Dependencies.** D10, D14.
- **Historical reference.** D35; D34 (beta-gated status, superseded).

## 16. D14 — Consultant Acquisition

- **Decision.** Record the approved consultant acquisition/onboarding
  direction. Consultants are direct CarbonTally customers in a hybrid model
  (direct + consultant customers); consultant-led MANAGED SERVICE is the
  default; consultant clients do not automatically use CarbonTally; the
  white-label foundation (branding config, authorized brand context,
  report-branding context) is implemented.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: Actor/Workspace/Access Model §37 (D19/D21 records);
  D21 White-Label Foundation implemented; `consultant_profiles.white_label_enabled`.
- **UX consequence.** The consultant surface includes firm management,
  client management, white-label/branding, and client workspace views.
- **Implementation consequence.** White-label foundation is live; full
  white-label rendering (rendered reports, outbound email, custom domains,
  client portal) remains future.
- **Dependencies.** D3, D8, D21.
- **Historical reference.** Actor/Workspace/Access Model §37.

## 17. D15 — Data Retention

- **Decision.** Record the approved retention direction. Retention is a
  deliberate product policy, not invented. Implementation is **PARTIALLY
  IMPLEMENTED**: storage metering and the private-documents storage layer exist
  (D32), but a full retention/deletion policy (periods, export-before-delete,
  Storage deletion) is an identified engineering gap (ADR-V3 §7 deferred item).
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: D32 private documents storage; D37 storage
  metering; ADR register §7 (data retention DEFERRED — business/legal policy
  must not be invented).
- **UX consequence.** The target UX documents retention visibility in
  Organisation settings (data lifecycle, export-before-delete); the current
  implementation does not yet expose a retention UI.
- **Implementation consequence.** Engineering gap: retention policy
  implementation (schema/API/UI) pending a business/legal decision.
- **Dependencies.** D21.
- **Historical reference.** ADR-V3 §7; D32; D37.

## 18. D16 — AI Provider / AI Governance

- **Decision.** AI may assist navigation, explanations, document assistance,
  extraction suggestions, workflow guidance and contextual help. AI MUST NOT
  silently become authoritative for emissions calculations, factor selection,
  evidence, approval, security, organisation boundaries or compliance
  certification. Human review and server-authoritative business rules remain
  authoritative.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: `engines/ai_extraction.py` (AI-assisted field
  extraction, deterministic parsing + confidence validation); public site copy
  ("AI-assisted help" with human review); no AI assistant surface exists that
  claims authority.
- **UX consequence.** Any assistant/guidance surfaces label AI output as
  suggestion; calculations/factors/evidence/approvals always show
  authoritative human/server review.
- **Implementation consequence.** AI extraction stays a suggestion engine;
  matching/calculation/validation engines remain authoritative.
- **Dependencies.** D7, D9, D21.
- **Historical reference.** `engines/ai_extraction.py`; public site claims.

## 19. D17 — Organisation Master Data

- **Decision.** Facilities, Locations, Assets, Vehicles and Suppliers are
  first-class organisation-scoped master-data entities. Conceptual hierarchy:
  Organisation → Locations → Facilities → {Assets, Vehicles}; Suppliers
  org-scoped. This is a PRODUCT/UX relationship, not a mandated physical
  database structure. Users must NOT be forced to configure every entity
  before normal processing. Master data supports relationships to documents,
  activity, emissions, calculations, evidence and reports, with lifecycle
  Create → Configure → Use → Edit → Archive/Deactivate → Restore → View related
  activity/documents/emissions/evidence.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: current implementation has `facilities`
  (="Organization facilities/locations"), `assets`, `suppliers`; **no
  separate `locations` table and no `vehicles` table exist** (gap). Admin
  surface has Facilities & Assets and Suppliers tabs.
- **UX consequence.** Organisation → Facilities/Assets/Suppliers screens
  implement the lifecycle; Locations and Vehicles are represented as target
  master-data surfaces with an implementation gap for Vehicles (and Locations
  as a distinct entity).
- **Implementation consequence.** Master data must not dominate primary
  workflow navigation (see D18).
- **Dependencies.** D18, D21.
- **Historical reference.** Schema `facilities`/`assets`/`suppliers`;
  `v3/admin/*` tabs; D18 navigation.

## 20. D18 — Workflow-First Authenticated Navigation

- **Decision.** CarbonTally uses **workflow-first** authenticated navigation.
  Customer primary navigation: Home, Documents, Processing, Emissions, Reports,
  Issues, Billing, Organisation. Organisation secondary navigation: Overview,
  Locations, Facilities, Assets, Vehicles, Suppliers, Members, Custom Factors,
  Activity, Settings. The authenticated UX answers "What needs my attention?"
  rather than "Which database module do I want?". Operational roles prioritise
  Queue, Assignments, Work, Review, QC, Issues, Evidence. CarbonTally Admin may
  use a denser Enterprise/control-plane architecture.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: current V3 nav
  (Dashboard, Emissions, Documents, Processing, Issues, Reports, Messages,
  Existing data, Billing, Organization + Ops) is already workflow-first and
  matches this decision; ops surface is tab-based
  (Dashboard, Data entry, Review, QC, Staff, Roles, Entities, SLA, Commercial).
- **UX consequence.** Navigation is role-aware and workflow-first; the top
  navigation bar is a single horizontal rail (no left sidebar inside the
  workbench).
- **Implementation consequence.** Alignment work: rename "Dashboard"→"Home",
  "Messages"→"Messaging" copy, add "Custom Factors" under Organisation, add
  Vehicles/Locations/Activity/Settings secondary entries as target surfaces.
- **Dependencies.** D17, D19, D21.
- **Historical reference.** `V3Layout.jsx`; `OperationsPage.jsx`.

## 21. D19 — Split-Screen Processing Workbench

- **Decision.** Extraction, structured entry, mapping, validation, review, QC
  and approval workflows requiring simultaneous source + structured-data
  interaction MUST use a split-screen workbench. The workbench MUST use **TOP
  WORKFLOW NAVIGATION** (Queue → Extract → Map → Validate → Review → QC →
  Evidence) and must NOT consume horizontal space with a permanent left-side
  application navigation sidebar. Source document (PDF/image, secure
  view-only, page nav, zoom) on one pane; structured data (fields, confidence,
  validation, source↔field links, evidence, autosave, approve/reject/correct)
  on the other. Pane presets 40/60, 50/50, 60/40.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: current ops extraction panel (`ExtractionPanel.jsx`)
  already uses a side-by-side document viewer + extraction form with a top
  nav; `WorkItemWorkspace.jsx` uses a split-screen contract; the PE entity
  workspace reuses the same panel. Full top-workflow-nav wizard and pane
  presets are target enhancements.
- **UX consequence.** Workbench is the standard surface for source+structured
  work across internal staff, PE staff and (in review mode) customer review.
- **Implementation consequence.** Extend the existing split-screen contract
  with explicit top workflow nav, pane presets, confidence indicators,
  source↔field links, lock states, keyboard operation.
- **Dependencies.** D6, D20, D21.
- **Historical reference.** `ExtractionPanel.jsx`, `WorkItemWorkspace.jsx`,
  `EntityExtractionWorkspace.jsx`, `ops.css`.

## 22. D20 — Responsive / Mobile Strategy

- **Decision.** Desktop is primary for extraction, mapping, validation, QC and
  structured data entry. Tablet supports adaptive workbench layouts and trays.
  Mobile primarily supports monitoring, notifications, status, lightweight
  review, evidence inspection, approval/rejection, comments, clarification and
  lightweight actions. Do NOT simply shrink the desktop workbench onto a
  phone.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: current v3 CSS collapses grids at ≤900px; the
  workbench stack is a single column on mobile (target: replace with
  adaptive trays); D28 F6 (mobile capture limited).
- **UX consequence.** The workbench on mobile becomes a tray-based flow
  (source/fields switchable), not a squeezed split view.
- **Implementation consequence.** Responsive workbench behaviour is target
  work (see implementation matrix).
- **Dependencies.** D19, D21.
- **Historical reference.** `v3.css`, `ops.css` media queries; D28.

## 23. D21 — Unified CarbonTally Design System

- **Decision.** CarbonTally uses ONE unified visual design system across
  public website, customer, consultant, Processing Entity, CarbonTally Staff
  and CarbonTally Admin. Role-specific interfaces may differ in information
  density and workflow presentation but remain visually recognisable as one
  product. The design system defines colour, typography, iconography, spacing,
  layout, buttons, forms, tables, cards, panels, drawers, modals, alerts,
  notifications, status indicators, loading/empty/error states, confirmation
  patterns, accessibility, responsive behaviour and data-visualisation
  conventions. Sub-decisions D21.1–D21.9 (colour, typography, iconography,
  status system, buttons, forms, tables, responsive, accessibility) are
  specified in `CARBONTALLY_V3_DESIGN_SYSTEM.md`.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Evidence: existing `v3.css` (shared V3 visual system) and
  `App.css` root tokens exist; the design system must extend, not replace,
  the existing CarbonTally identity (see design-system findings).
- **UX consequence.** One recognisable product across all surfaces.
- **Implementation consequence.** Design tokens consolidated; component
  vocabulary shared (see `CARBONTALLY_V3_DESIGN_SYSTEM.md`).
- **Dependencies.** D21.1–D21.9 (sub-decisions).
- **Historical reference.** `v3.css`, `App.css`, `index.css`, `ops.css`,
  `admin.css`, `consultant.css`, `reports.css`.

## 24. N1 — Messaging Access and Communication Boundaries

- **Decision.** Approved communication model:
  - **A. Customer organisation.** Authorised customer internal users may
    message other authorised users within their own customer organisation,
    authorised CarbonTally Customer Support staff, and authorised CarbonTally
    Admin/support personnel where permitted. Messaging is
    organisation-scoped.
  - **B. Consultant organisation.** Authorised consultant internal users may
    message other authorised users within their consultant organisation,
    authorised CarbonTally Customer Support staff, authorised CarbonTally
    Admin/support personnel where permitted, and their authorised customer
    organisations/contacts **within their active-client relationship**.
    Consultant access to customers is limited to authorised active-client
    scope.
  - **C. CarbonTally Customer Support / authorised Admin.** Authorised
    CarbonTally Customer Support staff and authorised CarbonTally Admin users
    may message customers within authorised support scope and consultants
    within authorised support scope. General CarbonTally staff do NOT
    automatically receive messaging access. Messaging access is an explicit
    role/permission capability, not a property of being a CarbonTally
    employee.
  - **D. Processing Entity.** PE Managers may message authorised PE users
    within the permitted PE scope and CarbonTally personnel where the
    operational workflow permits. PE communication remains within the PE
    relationship/assignment and authorisation boundaries.
  - **E. Customer ↔ PE direct messaging.** Do NOT introduce unrestricted
    Customer ↔ Processing Entity direct messaging. Customer/PE communication
    that concerns processing clarification must use the controlled
    processing/clarification workflow. This preserves the existing Processing
    Entity security boundary.
  - **F. RLS/API enforcement.** The UI must NOT be treated as the security
    boundary. Conversation visibility and message access are enforced by
    authenticated identity, role, organisation scope, active-client scope
    where applicable, PE relationship/assignment where applicable,
    conversation membership, API authorization and Supabase RLS. The AI
    Assistant inherits these same permissions and must never create an
    alternate messaging or permission path.
  - **G. Implementation principle.** Before changing the messaging
    schema/RLS/API, engineering must inspect the existing implementation and
    determine the minimum required changes. Do not redesign the database
    merely because the UX requires messaging.
- **Status.** APPROVED / FROZEN.
- **Rationale.** Reconciles D6 (mediated entity communication) and D18
  (Messaging in navigation) with the current implementation, where
  `conversation_participants` has zero RLS policies (deny-by-default) so chat
  is non-functional end-to-end. The model defines who may converse with whom
  without creating an "everyone can message everyone" surface and without
  weakening the PE no-download/security boundary.
- **UX consequence.** Customer and consultant messaging pages are
  org-scoped / active-client-scoped; Customer Support and Admin have scoped
  support threads; PE uses the controlled clarification workflow (no direct
  Customer↔PE chat). The AI assistant inherits the same boundaries.
- **Implementation consequence.** Engineering must implement the
  conversation RLS/API enforcement (N1-F) as the minimum change; the
  existing `conversations`/`messages` schema is inspected before any change
  (N1-G). See implementation matrix G-P1-1.
- **Dependencies.** D6, D18, D21, D16 (assistant inheritance).
- **Historical reference.** Reconciliation report §33; implementation matrix
  G-P1-1; screen inventory Messaging rows.

## 25. N2 — Location Physical Data-Model Representation

- **Decision.** CarbonTally does NOT require a separate physical `locations`
  database table at this stage. The physical implementation may use a
  dedicated Locations table/entity OR the existing Facilities model/structure,
  provided the resulting product satisfies the frozen D17 UX and functional
  requirements. The engineering decision must consider existing database
  schema, relationships, RLS, API design, reporting, master-data integrity,
  future extensibility, migration complexity and existing application
  behaviour.
- **Status.** PO DIRECTION RESOLVED; ENGINEERING DECISION.
- **Rationale.** D17 remains frozen and establishes Locations as a first-class
  product concept (Organisation → Locations → Facilities → {Assets,
  Vehicles}; Suppliers org-scoped). Whether that concept needs a separate
  physical table is a data-model question, not a product question.
- **UX consequence.** The product model keeps Facilities + Locations + Assets
  + Vehicles + Suppliers as first-class concepts; the UX must not force
  configuration of every entity before normal processing (D17).
- **Implementation consequence.** Cline must inspect the existing schema
  before deciding. No new table should be created merely because the UX
  document contains the word "Locations". See implementation matrix G-P1-3.
- **Dependencies.** D17, D18, D21.
- **Historical reference.** Reconciliation report §33; implementation matrix
  G-P1-3; screen inventory Organisation — Locations.

## 26. N3 — Configurable Data Retention

- **Decision.** CarbonTally's retention model is CONFIGURABLE. Retention is
  not a permanently hard-coded product value. The system should support
  configurable retention policies through the appropriate Settings/Admin
  control plane. Potential retention domains (where supported by the existing
  architecture) include uploaded documents, extraction data, processing
  records, evidence, reports, messages, audit records and other applicable
  platform data. Do NOT invent retention durations: if previous CarbonTally
  decisions/documents already specify defaults, use those values; otherwise
  leave the actual configurable parameters to engineering/business
  configuration and clearly mark any missing values. The UX should provide an
  appropriate configuration surface without assuming a particular retention
  duration. Retention enforcement must be server-side; the UI alone is not a
  retention/security control.
- **Status.** APPROVED PRODUCT MODEL; IMPLEMENTATION DETAIL REMAINS.
- **Rationale.** Extends D15 (retention direction) into a configurable
  product model without inventing business/legal policy values.
- **UX consequence.** Retention configuration appears under the appropriate
  Admin/System Settings area as a configurable surface (no invented
  durations); audit/evidence requirements are not weakened.
- **Implementation consequence.** Settings/Admin retention UI + server-side
  enforcement remain engineering work (implementation matrix G-P1-4/G-P1-5);
  default values, where not already specified, are business/engineering
  configuration, clearly marked as such.
- **Dependencies.** D15, D21.
- **Historical reference.** ADR-V3 §7 (deferred retention); D32; D37;
  implementation matrix G-P1-5.

## 27. Reconciliation notes

- D1–D21 are recorded from the approved decision baseline and reconciled
  against the current implementation evidence (frontend `frontend/src/**`,
  `frontend/src/v3/**`; backend `backend/api/**`, `backend/domain/**`,
  `backend/engines/**`; database `supabase/migrations/**`; live platform).
- N1–N3 supplement D1–D21 (§24–§26) and were approved after the
  reconciliation; they do not alter, reopen or renumber any D1–D21 decision.
- Where the implementation already matches a decision, the decision is marked
  as implementation-aligned. Where it does not, the gap is recorded in
  `UI_UX_IMPLEMENTATION_MATRIX.md` with an engineering dependency — the frozen
  decision remains authoritative.
- Implementation-status vocabulary: IMPLEMENTED · PARTIALLY IMPLEMENTED ·
  BACKEND READY / UI MISSING · UI READY / BACKEND MISSING · DESIGN ONLY ·
  PLANNED · BLOCKED · REQUIRES ENGINEERING DECISION.

## 28. Decision-register maintenance

- No PO product decision remains unresolved for the UX baseline. N1–N3
  resolved the three items previously flagged as NEW PO DECISION REQUIRED
  (messaging access, Locations physical representation, retention
  configurability).
- Remaining open items are **engineering implementation decisions** (recorded
  in the reconciliation report §33) and the AI assistant programme decisions
  recorded in `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §13 (e.g.
  provider choice for Phase 2) — none block Cline implementation of the UX
  baseline.

*End of register. Documentation-only — no implementation performed.*
