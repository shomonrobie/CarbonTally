# CarbonTally V3 — Authenticated Platform UX Blueprint

**Product UX Architecture · Information Architecture · Implementation Specification**

| | |
|---|---|
| Author | OpenHands (senior SaaS Product Architect + UX Architect) |
| Mode | READ-ONLY specification task — no application code, schema, RLS, API, migration, configuration, authentication or permission changes; no commits, no pushes |
| Repository baseline | `shomonrobie/CarbonTally` @ `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`) + docs-consolidation commit `9339a9b` |
| Decision authority | `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (authoritative; must not be contradicted) |
| Status labels | `VERIFIED` (confirmed in code) · `IMPLEMENTED` · `CURRENT UI` · `BACKEND-ONLY` · `BROKEN` · `MISSING` · `AUDIT FINDING` · `PROPOSED` · `PO DECISION REQUIRED` · `FUTURE` |
| Deliverable | This document — an implementation-ready blueprint for a later Cline frontend implementation task, after Product Owner approval |

**Evidence base consulted**

- `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
- `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md` (the prior authenticated-platform audit)
- `docs/audit/openhands/CARBONTALLY_V3_EXTRACTION_MAPPING_CALCULATION_CAPABILITY_AUDIT.md`
- `docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md`, `…_INDEPENDENT_REGULATORY_AND_DATA_RESIDENCY_AUDIT.md`, `…_INDEPENDENT_PRODUCT_PLATFORM_AUDIT_FLASH.md`
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`, `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`
- `docs/audit/cline/**` (platform finalization, phase reports, D-series records)
- Current implementation: `frontend/src/App.js`, `frontend/src/v3/**`, `backend/api/*.py`, `backend/auth.py`, `supabase/migrations/**`

A status label on a capability is **not** a Product Owner decision. Where the
PO has not decided, this document says `PO DECISION REQUIRED` and lists the
decision in §22.

---

## 1. Executive Summary

### 1.1 Current authenticated UX maturity

The authenticated V3 platform is **architecturally strong but UX-incomplete
and role-incoherent**. Strengths: a single V3 shell with real-data pages
(no fabricated numbers), a working upload→manual-extraction pipeline with
server-authoritative calculations, immutable evidence snapshots with a
navigable evidence record, an explicit active-client consultant context, and
an internal operations hub that re-uses real queue data. Weaknesses: the four
customer roles are not differentiated in the UI or the customer API surface;
the extraction workspace cannot display the source document for operators and
Processing Entity staff (broken viewer); several *existing* backend
capabilities have **no UI at all** (custom emission factors, customer
approval, factor catalogue, CSV/Excel mapping); and the customer-facing
processing pipeline exists only as an API.

### 1.2 Major structural problems

1. **Role blurring.** `Viewer`, `Member`, `Admin`, `Owner` share identical
   write capability across the customer API (`require_org_member` gates
   uploads, calculations, reports, exports, processing items, customer
   approval) and across RLS tenant policies (`is_org_member`). The UI shows
   the same navigation and controls to all four roles. `PO DECISION REQUIRED`
   on exact Viewer semantics; Admin/Owner are currently indistinguishable.
2. **Broken extraction document viewer.** Only the *internal* item-workspace
   endpoints sign document URLs; operator-queue and Processing-Entity
   extraction surfaces return raw storage paths that render as a blank
   iframe. The portal cannot currently display the very document it must
   extract from. (`VERIFIED` — `backend/api/v3_operations.py`; `frontend/src/v3/ops/ExtractionPanel.jsx`)
3. **Backend-without-UI capabilities.** Customer final approval
   (`/api/v3/processing/items/{id}/customer-review`) and Customer Custom
   Emission Factors (`/api/v3/customer-factors/*`) are complete server-side
   with zero frontend. Established PO capabilities are invisible.
4. **No customer processing depth.** The customer "Processing" page lists
   batches/items but offers no extraction/mapping/factor/evidence view, no
   review-approve flow, no status interpretation, and no item traceability.
5. **Multi-pane operations/entity workspaces are under-specified.** Review/QC
   render the source as raw JSON; entity clarification issues have no
   CarbonTally triage surface; ops tabs are not permission-filtered.

### 1.3 Strongest existing UX foundations

- **Real-data honesty** — every V3 page reads real APIs; there are no mocked
  dashboards in the authenticated area.
- **Active-client discipline** (ConsultantPage) — an explicit "you are
  working on X" banner and client switcher; multi-client confusion is
  structurally prevented.
- **Evidence record panel** (EmissionsPage / `EvidenceRecordPanel.jsx`) —
  SOURCE → EXTRACTION → MAPPING → FACTOR → CALCULATION → RESULT with
  completeness badge, technical expansion, and an audited access path.
- **Server-authoritative calculation** — clients never supply results;
  snapshots are immutable; factor provenance is captured.
- **Ops queues with real state** — operator/review/QC queues, assignment
  with operator-vs-entity routing, SLA settings, QC scoring.
- **Private documents by default** — D32 signed URLs; storage RLS is
  org-member-only; Processing Entities cannot download documents (`VERIFIED`).

### 1.4 Most important missing experiences

1. Customer **Review & Approve** flow (PO §12).
2. Customer **Custom Emission Factor** management (PO §6.2).
3. Customer **item-level processing + evidence** view (processing detail,
   traceability chain).
4. Working **document viewer** for operators and Processing Entities.
5. Processing Entity **mediated clarification** lifecycle with CarbonTally
   triage UI.
6. **Role-differentiated navigation and control gating** across all four
   customer roles and across ops staff roles.

### 1.5 Launch-blocking UX issues

- P0/P1 role model decisions (Viewer semantics; customer processing
  participation; consultant operating model) — without them the UI cannot be
  correctly role-gated.
- Broken extraction viewer (blocking the ratified operator/entity operating
  model).
- Customer approval and custom factors have no UI (established PO
  capabilities).
- Legacy `/privacy` route renders the PricingPage (routing bug).

### 1.6 Important but non-blocking improvements

Factor catalogue UI, report PDF download button, CSV/Excel mapping UI,
terminology pass, design-token consolidation, accessibility pass, legacy
cleanup, entity dashboard detail, consultant workspace depth.

### 1.7 What must NOT be changed

- One-person-one-role identity model.
- Processing Entity no-download boundary (storage RLS + signed URLs).
- Server-authoritative calculation and immutable evidence snapshots.
- Row-level traceability chain.
- Active-client consultant discipline.
- Existing DEFRA/SEAI/custom factor data and resolution precedence.
- Public marketing website (out of scope).

---

## 2. Product UX Principles

The following principles govern every authenticated screen. They are the
decision rules a Cline implementation must use when this blueprint is silent.

**P1 — Role-first UX.** Every screen, control and data element is presented
according to the authenticated context (Customer Owner/Admin/Member/Viewer,
Consultant, CarbonTally Staff, Processing Entity Staff). A user must never see
a control they cannot use, and never navigate to a page that 403s. Frontend
gating mirrors backend gating; the backend remains authoritative.

**P2 — Least privilege in the UI.** The UI exposes only what the authenticated
role may do. Hidden/disabled controls are a UI reflection, never a security
control. Security lives in RLS + API; the UI must not contradict it.

**P3 — Workflow-first design.** Every page is organised around a workflow
(Submit → Monitor → Review → Approve → Report) with a visible current state,
next action, and expected next state. No dead-end states.

**P4 — Evidence-first design.** Any displayed result is one click away from
its evidence chain (Source → Extraction → Mapping → Factor → Calculation →
Validation → QC → Approval → Result). Evidence is never a separate silo.

**P5 — Clear processing state.** Status vocabulary is shared, labelled, and
explained. Raw enum values never appear as user-facing text. A status badge
always implies a "what happens next" affordance.

**P6 — Progressive disclosure.** Simple by default, detail on demand.
Dashboards surface attention items; workspaces reveal technical depth behind
"Show details".

**P7 — Customer confidence.** Customers can always see what is happening to
their data, who is doing what (role-level), and what will happen next.
Processing is not a black box.

**P8 — Operational efficiency.** Operators/entities complete an item in one
continuous left-source/right-data workspace without leaving the screen.

**P9 — Traceability.** Every derived value can be walked back to its source.
Forward and backward navigation through the evidence chain where permissions
permit.

**P10 — Consistency.** One design system (tokens, components, status
semantics) across all five contexts. No per-context design forks.

**P11 — Accessibility.** WCAG 2.1 AA as the floor for the authenticated
platform: labelled controls, keyboard-complete workflows, focus management,
colour-independent status.

**P12 — No dead-end actions.** Every button performs its action or explains
why not. No "error" without recovery guidance. No 403 pages caused by UI
showing unauthorized controls.

**P13 — No accidental cross-organisation visibility.** Client-switching,
entity-switching, and org-scoped lists must always show an explicit context
header. Never trust a URL param alone in the UI flow (backend re-verifies).

**P14 — Preserve established capabilities.** CSV/Excel mapping, Custom
Emission Factors, DEFRA/SEAI factors, row-level traceability, and customer
approval are capabilities to surface and complete — never to remove.

---

## 3. Role & Capability Model

Status legend: `[V]` VERIFIED in code · `[I]` IMPLEMENTED · `[A]` AUDIT
FINDING · `[D]` PO DECISION REQUIRED · `[P]` PROPOSED (target).

Legend abbreviations: Org = Customer Organisation; CT = CarbonTally; PE =
Processing Entity; CA = CarbonTally Admin context (staff with management
permissions); Ops = CarbonTally Operator; Rev = CarbonTally Reviewer; QC =
CarbonTally QC staff.

| Capability | Owner | Admin | Member | Viewer | Consultant | Ops | Rev | QC | CA (staff mgmt) | PE Staff |
|---|---|---|---|---|---|---|---|---|---|---|
| View own org dashboard / data | `[V]` yes | `[V]` yes | `[V]` yes | `[V]` yes | `[V]` active-client grants | `[V]` assigned/all (`can_view_all`) | `[V]` queue | `[V]` queue | `[V]` all | `[V]` own entity |
| Upload documents | `[V]` yes | `[V]` yes | `[V]` yes | `[V]` yes *(A-1 viewer=writer)* | `[V]` flag `can_upload_documents` exists; no UI `[D]` | no | no | no | no | no |
| View documents list | `[V]` yes | `[V]` yes | `[V]` yes | `[V]` yes | `[V]` no doc-list UI `[D]` | `[V]` assigned items | `[V]` review items | `[V]` QC items | `[V]` all | `[V]` assigned items only |
| Process documents (extract/map) | `[A]` API-open; no UI `[D]` | same | same | same | no | `[V]` can_process | no | no | no | `[V]` can_process (own entity) |
| Calculation | `[V]` member-level | `[V]` | `[V]` | `[V]` | no | `[V]` | no | no | no | `[V]` (assigned) |
| Validation | `[A]` API-open; no UI `[D]` | same | same | same | no | `[V]` | `[V]` | `[V]` | no | `[A]` blocked by internal guard (PO §2.3 allows PE validation — reconcile) `[D]` |
| Review | no | no | no | no | no | no | `[V]` can_review | `[V]` | no | `[V]` own-entity review rows (PO §2.3) |
| QC | no | no | no | no | no | no | `[V]` via can_review | `[V]` qc | `[V]` | `[V]` own-entity QC (PO §2.3) |
| Customer final approval | `[A]` API-open; no UI `[D]` | same | same | same | no | no | no | no | no | no |
| Evidence view | `[V]` yes | `[V]` | `[V]` | `[V]` | `[V]` via client reports `[P]` deeper | `[V]` item-level | `[V]` | `[V]` | `[V]` | `[V]` own items |
| Reports | `[V]` generate | `[V]` | `[V]` | `[V]` | `[V]` read via client; `[D]` generate | no | no | no | `[V]` ops reporting | no |
| Issues | `[V]` create/view | `[V]` | `[V]` | `[V]` | `[V]` client issues | `[A]` no triage UI `[P]` | `[P]` | `[P]` | `[P]` | `[V]` clarify on own items |
| Messaging | `[V]` org↔consultant | `[V]` | `[V]` | `[V]` | `[V]` | no | no | no | no | no (mediated only) |
| Manage members | `[V]` admin | `[V]` admin | no | no | `[V]` can_manage_team (firm) | no | no | no | `[V]` staff mgmt | no |
| Manage organisation | `[V]` admin | `[V]` admin | no | no | no | no | no | no | no | no |
| Custom emission factors | `[V]` create/edit; `[V]` approve (admin) | `[V]` create/edit; `[V]` approve | `[V]` create/edit `[D]` | `[A]` via member gate `[D]` | `[V]` read via RLS; no UI `[D]` | no | no | no | `[P]` factor governance | no |
| Billing (customer) | `[V]` view/approve | `[V]` | `[V]` | `[V]` | no | no | no | no | `[V]` can_manage_billing | no |
| Processing entities | no | no | no | no | no | `[V]` read | `[V]` read | `[V]` read | `[V]` manage | `[V]` own |
| Staff management | no | no | no | no | no | no | no | no | `[V]` can_manage_staff | no |
| SLA / queue config | no | no | no | no | no | `[V]` read | `[V]` read | `[V]` read | `[V]` manage | no |
| Commercial (plans/credits/orders) | `[V]` customer billing only | `[V]` | `[V]` | `[V]` | no | no | no | no | `[V]` can_manage_billing | no |
| Platform configuration | no | no | no | no | no | no | no | no | `[P]` control plane | no |

**Notes on uncertain cells**

- **Viewer** (`[D]`): today the viewer is functionally a writer
  (`VERIFIED`). The PO decision is required: read-only, or editor-without-
  admin. The blueprint in §5 assumes both possibilities are designed; §22
  lists the decision.
- **Customer processing participation** (`[D]`): the customer processing
  item pipeline is API-open to all members. The decision: customers are
  submit/monitor/review-only (CarbonTally processes), or customers may
  self-service process. §22.
- **Consultant** (`[D]`): status/reporting user vs active processing user.
  PO §2.3 quality chain implies CarbonTally and PE do the processing;
  consultants advise. Blueprint defaults to status/reporting (+ messaging +
  evidence/report review) but flags the decision.
- **PE validation** (`[D]`): PO §2.3 says PE may perform
  extraction/mapping/validation/review/QC; the current internal ops guard
  denies PE `validate` on the internal item endpoint while the entity
  workspace exposes extraction only. Reconcile after PO confirmation.

---

## 4. Information Architecture

Five separate IAs. No shared mega-menu. Each context has: **primary
navigation** (workflows), **secondary navigation** (settings/account),
**contextual navigation** (within a workspace), and a persistent **context
header** showing WHO I am / WHICH organisation I am acting as.

### 4.A Customer Organisation IA

```
PRIMARY (workflow)              SECONDARY (settings)
  Dashboard   /home               Organisation      /organization
  Documents   /documents            ├ Profile
  Processing  /processing           ├ Members
  Emissions   /emissions            ├ Facilities
  Reports     /reports              ├ Suppliers
  Issues      /issues               ├ Security
                                    ├ Custom factors   (PROPOSED)
ACCOUNT / GLOBAL                    └ Billing          (PROPOSED move)
  Notifications  /notifications
  Messages       /messaging        CONTEXT HEADER
  Billing        /billing            "Acme Ltd · Workspace"  (+ role badge)
  Existing data  /existing-data      (moved out of primary nav → Settings)
```

Rationale against current: remove "Existing data" from primary nav
(`[A] N-1` — onboarding/administrative flow, not a daily workflow); keep
Billing primary only if it is a daily concern — otherwise move under
Organisation. Terminology: "Messages" retained for customer↔consultant;
"Issues" kept as-is.

### 4.B Consultant IA

```
PRIMARY                          CONTEXTUAL (inside active client)
  Portfolio    /consultant         Client overview
  Messages                        Documents        (PROPOSED read)
                                    Processing      (PROPOSED status+evidence)
  ACCOUNT                          Emissions
  Notifications                    Reports
                                    Issues
                                    Evidence        (PROPOSED)
ACTIVE-CLIENT CONTEXT HEADER:
  "Working on: Acme Ltd — every action applies to this client"
  [Switch client]
```

### 4.C CarbonTally Staff IA (operations control centre)

```
PRIMARY (permission-filtered tabs)
  Dashboard
  Data entry        (can_process)
  Review            (can_review)
  QC                (can_review)
  Issues            (PROPOSED — mediated clarification triage)
SECONDARY (can_manage_staff)
  Staff
  Roles
  Entities
  SLA
SECONDARY (can_manage_billing)
  Commercial
```

`[A] O-3`: tabs must be filtered by `getOpsMe().permissions`, never shown to
staff who cannot use them.

### 4.D Processing Entity IA

```
PRIMARY
  My work        (assigned items, queued by stage)
  Extraction     (workspace)
  Review         (own-entity review rows)
  QC             (own-entity QC rows)
  Clarifications (PROPOSED)
  Performance    (own entity only)
CONTEXT HEADER
  "Processing Entity: [name] — assigned work only"
```

### 4.E CarbonTally Admin / Control Plane IA (PROPOSED, future-ready)

```
  Operations   (work/review/QC/issues/SLA)
  People       (staff/roles/permissions)
  Processing   (entities/entity staff/assignment/policies)
  Data         (factor sets/versions/custom factors)
  AI           (providers/extraction config/transfer controls)
  Commercial   (customers/plans/subscriptions/credits/orders)
  Platform     (feature controls/retention/audit)
```

Each item is marked `PROPOSED` unless a backend surface already exists
(`[V]`: ops dashboard, staff, roles, entities, SLA, commercial).

---

## 5. Customer UX Blueprint

### 5.1 Dashboard

**Current:** `DashboardPage.jsx` — stat cards (org snapshot, emissions total,
documents, members), trend chart, recent activity, quick links. Real data.

**Target:** the dashboard answers *"What is happening with my emissions
data?"* in priority order:

1. **Attention required** (first, above the fold): items awaiting customer
   approval, failed uploads, unresolved issues, validation findings that need
   action. Each card links to the exact queue/filter.
2. **Processing status** (second): a stage overview of the current
   batch/pipeline (counts per stage: Source → Extracted → Mapped →
   Calculated → Validated → QC → Review → Approved) with a "View processing"
   affordance.
3. **Primary KPIs** (third): reporting-year emissions total (Scope 1/2/3
   split), documents processed, items awaiting action, reports ready.
4. **Recent activity + reports** (fourth): recent calculations, latest report
   status, recent issues.

Drill-down behavior: every card clicks through to a filtered list (e.g.
"5 documents failed" → `/documents?status=failed`). No dead stat cards.

Dependencies: frontend (reuse `/api/v3/reporting/customer-dashboard`,
`/api/v3/processing/status`). PO decision: none (dashboard composition).
Severity: P2.

### 5.2 Documents

**Current:** `DocumentsPage.jsx` — upload widget (PDF/image/CSV/Excel), list
with metadata + status, reverse evidence lookup ("Emissions from this
document"). No preview. `[A] O-2` upload shown to all members.

**Target:**

- **Upload** with drag-and-drop, type restrictions, size/limit feedback,
  multi-file, and a clear post-upload outcome ("uploaded → extraction item
  created → status: queued"). Role-gated (per Viewer decision).
- **Document list**: columns File · Type · Size · Pages · Status · Uploaded ·
  Evidence. Filters: type, status, date. Search by file name.
- **Document preview**: inline preview of PDF/image for org members via the
  existing org-gated signed URL (`/api/v3/documents/{id}/signed-url`,
  `[V]` org-member gate). Mark `PROPOSED` for CSV/Excel (tabular preview).
- **Metadata + processing state**: which batch/item(s) this document feeds,
  current stage, link to item trace (see §11).
- **Error states**: failed classification/extraction with reason and retry.

Dependencies: frontend; signed-URL endpoint already org-member-gated
(`[V]`). PO decision: viewer upload/edit (see §22). Severity: P1 (upload
result clarity), P2 (preview).

### 5.3 Processing

**Current:** `ProcessingPage.jsx` — batches list + item table with raw status
strings; "Add item" form accepts an arbitrary **File URL** string; "Create
batch" handler is dead code; no item detail; no extraction/mapping/factor
view. `[A] A-2/A-3/V-1/T-1/M-1`.

**Target:**

- **Batches**: create (org admin), assign, complete, cancel — with a real
  batch form (replaces dead code).
- **Items**: table with labelled status badges (see shared status vocabulary
  §12), stage, assigned processor (CarbonTally / PE), deadlines, linked
  issues.
- **Item detail** (read-only for customers): extraction data, mapped
  activity/facility/asset/supplier, factor selection + provenance, calculated
  result, validation/QC stamps, issues — the *item-level evidence chain*
  (§11). Customers should *see* the chain; they should not *operate* it
  unless PO decides otherwise (§22).
- **Add item** must accept a document reference (from the Documents list),
  not a freeform URL (`[A]` security/UX issue: arbitrary URL string).

Dependencies: frontend; backend item detail endpoints already exist
(`/api/v3/processing/items/{id}/workspace` is org-member-gated and signed
`[V]`). PO decision: customer processing participation (§22). Severity: P1.

### 5.4 Review & Approve (customer final approval)

**Current:** `/api/v3/processing/items/{id}/customer-review` exists
(`[V]`, `require_org_member`, reject requires reason, billing charge on
approve for subscribed orgs) but there is **no UI**. `[A] A-2`.

**Target** (`PO §12` — customer approval is a real flow):

- **Approval queue**: items in `customer_review` stage, grouped by batch,
  with "Items awaiting your approval" headline on the Dashboard.
- **Item review**: read-only item detail + evidence chain + signed source
  access (org member) so the customer can verify before approving.
- **Approve**: one-click with confirmation summary (items, quantities,
  factors, result, credits consumed if applicable). **Reject**: requires a
  reason (backend already enforces `[V]`); rejection routes the item back to
  `mapping` (backend `[V]`) and notifies CarbonTally.
- **Final status**: Approved/Rejected persisted, shown in item status and
  evidence.

Dependencies: frontend only (API complete). PO decision: who may approve
(admin-only vs any member) — §22. Severity: **P1 (launch-critical; a
ratified workflow has no UI).**

### 5.5 Emissions

**Current:** `EmissionsPage.jsx` — single-row manual calculation (quantity,
unit, date, activity, scope, facility/asset), factor auto-match display,
result with factor provenance text, calculation history, evidence record
panel (`EvidenceRecordPanel`).

**Target:**

- Keep the manual calculator (it is the customer's way to see
  server-authoritative results) but add: **filters** (date range, scope,
  facility, factor source), **drill-down** from any result to its evidence
  chain, and **factor provenance** presented as structured metadata
  (source/set, reporting year, country, unit, scope, ID) rather than a raw
  string.
- Bulk/CSV ingestion remains a capability to surface (PO §5.1) — see §10 CSV
  UX (PROPOSED).

Dependencies: frontend; `/api/v3/emissions/*` `[V]`. Severity: P2.

### 5.6 Evidence

**Current:** evidence record panel on Emissions + reverse lookup on
Documents. `[A] T-1`: not navigable as a chain from an item.

**Target** — one **universal evidence trail** component (see §11) reachable
from: an emission result, an item in Processing, a document, or a report
line. Directional navigation both ways where permissions permit.

Severity: P1 (traceability is a PO-locked differentiator).

### 5.7 Reports

**Current:** `ReportsPage.jsx` — generation modal (type/year), status
lifecycle, filters, versioning, JSON download. PDF endpoint exists
(`/api/v3/reports/{id}/pdf` `[V]`) but no UI button. `[A] R-1`.

**Target:** add **PDF/Excel/CSV download** buttons for completed reports;
**report detail** with preview of included data and its evidence links;
generation guidance (what each report type includes). Keep status vocabulary
labelled.

Dependencies: frontend (PDF/Excel endpoints `[V]`; CSV/Excel export
generation `[V]`). Severity: P2.

### 5.8 Issues

**Current:** `IssuesPage.jsx` — customer issues list/detail; create with
category/severity; entity-scoped issues excluded. Customers cannot reply
(`[A]` acknowledged limitation).

**Target:** add **conversation/reply** on an issue (customer ↔ CarbonTally),
status transitions with reasons, affected-item links, and a "resolved"
confirmation flow. Keep customer issues separated from entity clarification
issues (entity issues are mediated internally, §8.5).

Dependencies: backend issue reply/triage endpoints — `[D]` (reply may need a
backend addition; `/api/v3/issues/admin/open` exists for internal). Severity:
P2.

### 5.9 Custom Emission Factors

**Current:** complete backend (`/api/v3/customer-factors/*`: list/get/create/
update/approve(org admin)/deactivate; RLS org-member + consultant-read;
calculation integration with approved-customer-first precedence; snapshot
provenance `factor_source=CUSTOMER`) — **zero frontend**. `[A] F-3`.

**Target** (`PO §6.2` — must be surfaced, not removed):

- **Factor catalogue** (in Organisation or Emissions): list with status
  (DRAFT/ACTIVE/ARCHIVED), source, unit, scope, reporting year, usage count.
- **Create/Edit**: form with validation (value ≥ 0, unit required, scope,
  reporting year, source reference/notes).
- **Submit → Approve (org admin) → Activate**: status lifecycle with an
  approval step for draft factors.
- **Deactivate** (archive) with confirmation; deactivated factors are
  blocked from new calculations (backend `[V]`).
- **Provenance/usage**: show which calculations used this factor; link to
  the evidence trail.
- Consultants: read/use (backend RLS `[V]`); UI `[D]` per consultant model.

Dependencies: frontend only (API + RLS complete `[V]`). Severity: **P1**.

### 5.10 Organisation

**Current:** `AdminPage.jsx` tabs — Profile, Members, Facilities, Suppliers,
Security. `[A] O-2`: tab contents shown to all members; mutating controls
return 403 for non-admins.

**Target:**

- **Role-gate the whole section**: non-owners/admins see a read-only
  organisation view (or the section is hidden per Viewer decision).
- **Members**: email-invite flow (invitations backend `[V]`), role dropdown
  only for admin, "remove" with confirmation, owner can transfer ownership
  (`[D]` owner model).
- Add a **Custom factors** tab (see §5.9) and move **Billing** here if the
  PO prefers settings grouping.
- Facilities/Suppliers: keep, role-gated; add empty states.

Dependencies: frontend gating + reuse of existing admin endpoints `[V]`.
Severity: P1.

### 5.11 Billing

**Current:** `BillingPage.jsx` — plans/modes, credits, orders (assisted +
managed), order approval. Backend `[V]`; D37-0 protects billing writes.

**Target:** keep current scope; add order status vocabulary clarity and
credit consumption context when approving processing (align with §5.4).
Do **not** invent payment processing; mark anything beyond current
entitlement/credits/orders as `PROPOSED`/`FUTURE`.

Severity: P2.

---

## 6. Consultant UX Blueprint

**Current:** `ConsultantPage.jsx` — portfolio, client switcher with active-
client banner, client workspace (overview, processing status, reports,
issues, messaging, white-label). Backend `[V]` via `consultant_auth.py`
(active grants only, D15/D19). `[A] C-1`: workspace is status-only; no
documents/extraction/evidence depth.

**Target:**

1. **Consultant Dashboard** — portfolio health (clients, active grants,
   processing stages across clients, issues flagged, reports ready, approvals
   pending). Grouped by client.
2. **Client Switcher** — preserve the active-client discipline: persistent
   header "Working on: Acme Ltd", explicit switch control, and a guard when
   a client is suspended/ended (grants are active-only `[V]`).
3. **Client Workspace** — Client overview · Processing status (per stage) ·
   Documents (read-only `[P]`/`[D]`) · Emissions · Evidence (`[P]`) ·
   Reports · Issues · Messages. If PO decides consultants are
   **status/reporting** users (default), the workspace is read/advise; if
   **active processing** users, they get an org-scoped item workspace —
   **never** Processing-Entity-style controls.
4. **Multi-client safety** — every page in the workspace renders the active
   client context header; URL carries `clientId` but the UI also displays it;
   switching requires an explicit action; a "you are working on the wrong
   client" indicator is impossible because data is always rendered under the
   context header.

**Decision required (§22):** consultant operating model (status/reporting vs
active processing). Severity: P1 (decision), P2 (depth).

---

## 7. CarbonTally Internal Staff UX Blueprint

An operations control centre — not a customer dashboard.

### 7.1 Staff Dashboard

**Current:** `OpsDashboard.jsx` (`[V]` real data: pipeline, entities, staff,
review queue, issues, SLA). `[A] O-3`: tabs not permission-filtered.

**Target** (single ops dashboard, permission-filtered widgets):
work awaiting assignment · active processing · review queue · QC queue ·
customer approval pending (across orgs) · entity workload · SLA/aging ·
issues/exceptions · operational alerts. Each widget drills to a tab.

### 7.2 Data Entry / Processing workspace

**Target — the canonical split workspace:**

```
LEFT  Secure source-document viewer        RIGHT  Data panel
  (signed, view-only, no download for PE)    Extraction fields
  page navigation / zoom                      Mapped activity + factor
                                              Calculation
                                              Validation summary
                                              Save / Submit / Next
```

- **Fix the broken viewer first** (`[A] E-1`): the operator/entity surfaces
  must receive signed view-only URLs (server-scoped to assigned items),
  mirroring the internal `item_workspace` which already signs `[V]`.
- The user never leaves the workspace to compare source with extracted data.
- Validation findings appear inline with a "fix and re-validate" loop.

### 7.3 Review

**Target:** reviewer queue → open item workspace (signed source + data) →
record outcome (pass / findings) → next item. Assign/unassign
(`can_review`+`can_manage_staff` `[V]`). Reviewer history per item.

### 7.4 QC

**Target:** QC-specific panel: checklist (source↔extracted consistency, unit
sanity, factor match, calculation plausibility), quality score
(0–100 `[V]`), findings, notes, pass/fail, reviewer + QC history per item.
Reuse `/api/v3/ops/items/{id}/qc` `[V]`.

### 7.5 Issues (internal triage)

**Target:** an ops Issues tab listing org + entity issues with a **mediated
reply** action. This is the missing triage surface for PE clarification
(`[A] I-1`) and the customer-issue conversation endpoint (backend `[D]`).

### 7.6 Staff / Roles / Entities / SLA / Commercial

- **Staff** (`[V]` `/api/v3/ops/staff`): roster with role + entity
  assignment; entity assignment routes staff into the entity workspace
  (`[V]` D22).
- **Roles** (`[V]` `/staff-roles`): read-only catalogue of permissions;
  present as a matrix (not raw JSON).
- **Entities** (`[V]` `/api/v3/ops/entities`): entity list + status +
  assignment history; provision via admin surface.
- **SLA** (`[V]` `/sla/settings`): queue settings + aging dashboard.
- **Commercial** (`[V]` can_manage_billing): customers, subscriptions,
  credits, orders — internal, separate from customer Billing (§5.11).

Severity: P1 (viewer fix, tab filtering, issues triage); P2 (rest).

---

## 8. Processing Entity UX Blueprint

A focused work-management portal. The entity context header always shows the
entity name; data is **own-entity only** (`require_entity_scope` `[V]`).

### 8.1 Entity Dashboard

Assigned work (by stage) · in progress · review · clarification · completed ·
performance (own entity) · SLA within entity.

### 8.2 My Work

Queue of assigned items ordered by stage and priority with status labels and
SLA deadlines. Each row opens the extraction workspace.

### 8.3 Extraction Workspace (critical)

```
LEFT  Secure document viewer (CarbonTally-signed, view-only, NO download)
RIGHT Extraction / Mapping / Validation / Save / Submit / Clarify
```

- The source document is **viewable through CarbonTally only** — never
  downloaded (`PO §3.3`; enforced `[V]` at storage RLS + signed-URL gate +
  unsigned entity payloads; **must be kept**).
- Extraction, mapping, validation, review and QC are performed in-portal
  (PO §2.3). Save/draft, submit for internal review, request clarification.
- Fix the current broken viewer (E-1) by issuing view-only signed URLs
  scoped to assigned items.

### 8.4 Entity Review/QC

Entity-side review/QC of its own completed items (PO §2.3). No access to
CarbonTally internal queues, staff, other entities, or customer org surfaces
(`[V]` guards). Expose the entity review queue + QC action without any
internal operations chrome.

### 8.5 Clarification (mediated)

Flow: Entity staff → clarification request (issue, entity-scoped) →
CarbonTally staff triage (ops Issues tab, §7.5) → mediated response →
item continuation. The entity never communicates directly with the customer.

### 8.6 Performance

Metrics visible to the entity: own throughput, QC pass rate, SLA adherence,
open clarifications. **Never** expose customer names, other-entity data, or
CarbonTally-internal cross-entity comparisons (§22 item 5).

Severity: P1 (viewer fix + clarification triage), P2 (dashboard/performance).

---

## 9. CarbonTally Admin / Control Plane (PROPOSED, future-ready)

Not a new application — an expansion of the ops hub for users with
management permissions, each section gated by real permission flags.

| Section | Contents | Backend today |
|---|---|---|
| Operations | work/review/QC/issues/SLA dashboards | `[V]` (ops endpoints) |
| People | staff, roles, permissions matrix | `[V]` |
| Processing | entities, entity staff, assignment policies | `[V]` (entities) / `[P]` policies |
| Data | factor sets, factor versions, custom-factor governance | `[P]` (research only) |
| AI | providers, extraction config, transfer controls | `[P]` (PO §4.2 controlled) |
| Commercial | customers, plans, subscriptions, credits, orders | `[V]` (can_manage_billing) |
| Platform | feature controls, retention, audit logs | `[P]` |

Mark everything not currently backed by an endpoint as `PROPOSED`; do not
build UI on missing APIs.

Severity: P3 (except Commercial/People which are P2).

---

## 10. End-to-End Processing UX

Canonical map. "PE step" applies when a batch is assigned to a Processing
Entity; otherwise CarbonTally staff perform that stage.

| # | Step | Actor | UI surface | State (in/out) | Allowed actions | Failure path | Clarification path | Evidence generated | Event/notification |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Upload | Customer member | Documents upload | `pending` → `queued` | add files, cancel | upload error shown; retry | — | source file stored (private) | toast + notification |
| 2 | Classification + extraction item | system/CT | Processing list | `queued` → `extracting` | view item | classification failure → item flagged | — | source→item link | notification |
| 3 | Assignment | CT staff (`can_manage_staff`+`can_process`) | Data entry → Assign | `open` → `in_progress` (assigned CT or PE) | assign, reason, reassign | — | — | audit trail | — |
| 4 | Extraction | CT operator OR PE staff | split workspace | `extracting` → `extracted` | save draft, submit | validation block → route back | clarify (PE) → triage → continue | extracted_data + source refs | — |
| 5 | Mapping + factor | CT operator OR PE staff | split workspace | `extracted` → `mapped` | select factor, facility/asset/supplier | factor not found → message | clarify | mapped_data + factor_id | — |
| 6 | Calculation | system (server-authoritative) | workspace auto | `mapped` → `calculated` | (none — engine) | calculation error → item flagged | — | immutable snapshot + emissions_logs row | notification |
| 7 | Validation | CT staff / PE (own) | workspace | `calculated` → `validated` or back to `mapping` | re-validate | blocking findings → issues + rework | — | findings + issues | notification |
| 8 | PE review/QC (if PE) | PE staff | PE review/QC | → `reviewed`/`qc` | pass/fail, score | findings → rework | clarify | QC stamps | notification |
| 9 | CT review/QC | CT staff | Review/QC tabs | → `qc_approved` | pass/fail, score | findings → rework | — | review/QC stamps | notification |
| 10 | Customer review | Customer | **Review & Approve (§5.4)** | → `customer_review` | open item, approve/reject | — | — | approval/rejection record | notification |
| 11 | Customer approval | Customer (per §22) | Approve | `customer_review` → `approved` (or `rejected`) | approve/reject + reason | reject → routes to `mapping` (`[V]`) | — | approval stamp + billing charge (`[V]`) | notification |
| 12 | Evidence + result | system/customer | item trace / emissions | `approved` | view chain | — | — | full evidence record | report-ready event |
| 13 | Report | Customer (or auto `[D]`) | Reports | generated → ready | download PDF/Excel/CSV/JSON | generation failure | — | report version | notification |

**Gaps between backend workflow and UI workflow:**

- Steps 10–11 (customer review/approval) — backend `[V]`, UI missing.
- Step 4–5 document viewing — broken for operators/PE (`[A] E-1`).
- Steps 8 (PE review/QC) — API partial (`[V]` own rows), UI minimal.
- Step 13 report downloads — PDF/Excel not exposed (`[A] R-1`).
- Clarification loop — no triage UI (`[A] I-1`).

---

## 11. Traceability / Evidence UX

**Universal evidence trail component** (one component, used everywhere):

```
RESULT
  └─ Calculation (quantity × factor, date, methodology, snapshot id)
      ├─ Factor (source/set, provider, reporting year, country, unit, scope, id)
      │    └─ (custom) factor lifecycle: draft → approved → active
      ├─ Mapping (activity, facility, asset, supplier)
      │    └─ Extracted value (line item from source)
      │         └─ Source document (name, type, pages, private storage ref)
      ├─ Validation findings (severity, code, message)
      ├─ QC (score, by, at)
      └─ Approval history (customer, by, at, reason)
```

Properties:

- **Navigable both ways**: result → source, and source/document → items →
  calculations → results (Documents reverse lookup already `[V]`).
- **Permissions**: each link renders only if the viewer may see that object
  (org member / consultant grant / staff scope / entity own-items).
- **Timeline view**: a vertical stage timeline with timestamps and actors
  (role-level) for the item.
- **Source references**: `source_file`, `source_page` (D33.1) and the
  extracted line item are shown together.
- **Immutable evidence**: finalized snapshots are read-only (PO §7.3).

Dependencies: mostly frontend composition of existing endpoints
(`/api/v3/emissions/{id}/evidence` `[V]`, item workspace `[V]`, documents
`[V]`); item-level customer evidence view may need a small read endpoint
(`[D]` if we expose the full item workspace to customers read-only).

Severity: P1.

---

## 12. Design System

**Current problem** (`[A] D-1`): five V3 CSS files (`v3.css`, `admin.css`,
`ops.css`, `consultant.css`, `reports.css`) + the legacy 3,491-line
`App.css`, no design tokens, hard-coded hex colors, divergent status
vocabularies (`v3-status` vs `v3-ops-badge`).

**Target — one shared authenticated design system:**

- **Tokens** (`:root` variables): color (brand, semantic status, surface,
  text, border), spacing scale (4px base), radius, shadow, type scale,
  z-index. Adopted by all five contexts.
- **Typography**: one scale; headings + body + mono (for IDs/technical).
- **Colour/status semantics** (shared vocabulary, not color-only — always
  with text labels):
  - `queued` gray · `extracting/extracted/mapped/calculated` blue ·
    `validated` teal · `reviewing` indigo · `qc_approved` green ·
    `customer_review` amber · `approved` green · `rejected` red ·
    `failed/error` red · `clarification` violet.
- **Components**: card, table, form, button (primary/secondary/danger/
  ghost), badge, modal (focus-trapped), drawer, tabs, timeline, document
  viewer, evidence trail, uploader, empty state, loading skeleton, error
  banner, confirmation dialog. One implementation each, reused by all
  contexts.
- **Document viewer**: shared component with `sandbox` iframe, page
  controls, zoom, and a "view-only" indicator for PE contexts.
- **Evidence trail**: the §11 component.

Dependencies: frontend refactor; no backend. Severity: P2.

---

## 13. Accessibility

Minimum requirements (WCAG 2.1 AA) for the authenticated platform:

- Every form control has a visible label (`[A] A-4`: extraction line inputs
  are label-less today).
- Full keyboard navigation for every workflow; visible focus indicators.
- Modals/drawers: focus trap + Escape close + `aria-modal` (`[A] A-4`).
- Status is never conveyed by colour alone; badges carry text.
- Tables: real `<th>` scope, sortable with aria-sort, responsive behavior
  without horizontal-only scrolling for critical columns.
- Document viewer controls are keyboard accessible; "view-only" is
  announced.
- Validation/error messages are linked to fields (`aria-describedby`) and
  announced on change.
- Loading states are announced (aria-live polite); skeleton screens.

Severity: P2 (P1 for the extraction workspace which is the core workflow).

---

## 14. Responsive / Device UX

- **Desktop/laptop**: full split workspaces (extraction, review, evidence
  trail), multi-column dashboards.
- **Tablet**: stacked split workspace (source above, data below, toggleable),
  single-column dashboards.
- **Small screens**: 
  - Extraction workspace becomes **sequential** (view source → extract → map
    → validate) rather than side-by-side; never a poor zoomed copy.
  - Dashboards collapse to priority cards; tables switch to card lists for
    the most-used screens (documents, issues).
  - Processing approval remains usable: review summary → approve/reject.
- The full desktop extraction workspace is **not** reproduced 1:1 on mobile;
  it is a designed-for-small-screen sequence.

Severity: P3 (platform is desktop-heavy; mobile is a completeness item).

---

## 15. Notification / Feedback UX

Use existing mechanisms only (`/api/v3/notifications/*` `[V]`; in-app
banners/toasts; no invented email system):

| Event | Feedback |
|---|---|
| Upload accepted | toast + inline item status |
| Extraction started | inline status in Processing + notification |
| Extraction failed | error banner + notification + document flagged |
| Processing complete (item) | notification; status badge |
| Review required | ops review queue; notification to reviewers |
| QC failed | item routed back; notification to processor |
| Clarification requested | ops Issues triage; notification to CarbonTally |
| Customer approval required | customer Dashboard attention card + notification |
| Report ready | notification; report status badge |
| Issue updated | notification; issue conversation |

Toasts: transient, non-blocking. Inline status: persistent on the object.
Notification centre: `/notifications` `[V]`. No new backend event system is
proposed.

Severity: P2.

---

## 16. Error / Empty / Loading States

Every major workspace defines: loading (skeleton), empty (icon + explanation
+ next action), error (recoverable, with retry), permission denied (explains
what is needed; not a generic 403 page caused by UI showing unauthorized
controls), unavailable (service/feature not enabled), processing (inline
progress), completed (success state + next action). No dead ends.

Example specifics:

- Documents empty: "Upload your first document" CTA.
- Approval queue empty: "No items awaiting your approval."
- Processing item 403 (member without permission): hidden entirely
  (frontend gating) rather than shown-then-denied.
- Factor catalogue empty: "No custom factors yet — create one."

Severity: P2.

---

## 17. Current UI → Target UX Gap Matrix

| Area | Current State | Target State | Gap | Severity | Backend Exists? | UI Work | Backend Work | PO Decision? |
|---|---|---|---|---|---|---|---|---|
| Customer dashboard | stat cards, quick links | attention-first + processing status | medium | P2 | yes | medium | no | no |
| Customer documents | upload+list, no preview | preview, role gate, upload outcome | medium | P1/P2 | yes (signed-url) | medium | no | viewer perms |
| Customer processing | list only, raw status, dead batch form | item detail, status vocab, evidence link | large | P1 | yes | large | no | customer processing role |
| Customer approval | none | Review & Approve flow | **critical** | P1 | yes | large | no | approver role |
| Customer emissions | manual calc + evidence | filters, drill-down, provenance display | small | P2 | yes | small | no | no |
| Customer evidence | per-result record only | universal navigable chain | medium | P1 | partial | medium | small (item read) | no |
| Customer reports | JSON download | PDF/Excel/CSV + detail | small | P2 | yes (pdf) | small | no | no |
| Customer issues | create/view, no reply | conversation + resolution | medium | P2 | partial | medium | reply endpoint | no |
| Customer custom factors | none | catalogue + lifecycle UI | **critical** | P1 | yes | large | no | editor/approver |
| Customer organisation | admin tabs to all roles | role-gated admin | medium | P1 | yes | medium | no | no |
| Customer billing | plans/credits/orders | keep + status clarity | small | P2 | yes | small | no | no |
| Consultant dashboard | portfolio | health + per-client status | small | P2 | yes | small | no | model |
| Consultant client workspace | status-only | read depth (docs/evidence) | medium | P2 | partial | medium | small | model |
| Staff dashboard | real-data widgets | permission-filtered widgets | small | P1 | yes | small | no | no |
| Staff processing | workspace, broken viewer | working split workspace | **critical** | P1 | partial (signing) | medium | small (view-only URLs) | no |
| Staff review | JSON source view | rendered source + outcomes | medium | P2 | yes | medium | no | no |
| Staff QC | score+notes | checklist + history | small | P2 | yes | small | no | no |
| Staff issues | none | triage + mediated replies | large | P1 | partial | medium | reply/triage | no |
| Staff entities | provision+assign | entity overview + status | small | P2 | yes | small | no | no |
| Staff SLA | settings+aging | dashboard integration | small | P2 | yes | small | no | no |
| PE dashboard | partial (extraction summary) | full own-entity overview | medium | P2 | yes | medium | no | metrics |
| PE work | queue exists | stage-ordered queue | small | P2 | yes | small | no | no |
| PE extraction | broken viewer, no validation | working portal extraction | **critical** | P1 | partial | medium | view-only URLs | no |
| PE review/QC | partial | own-entity review/QC UI | medium | P2 | partial | medium | small | no |
| PE clarification | issue create only | mediated triage lifecycle | large | P1 | partial | medium | triage endpoints | no |
| Admin/control plane | ops hub tabs | full control plane | large | P3 | partial | large | per section | yes (scope) |
| Navigation | mixed, "Existing data" primary | five role-specific IAs | medium | P2 | n/a | medium | no | no |
| Design system | 5 CSS + legacy App.css, no tokens | token-based shared system | large | P2 | n/a | large | no | no |
| Accessibility | gaps (labels, focus, color) | WCAG 2.1 AA | medium | P2 | n/a | medium | no | no |
| Legacy routes | `/dashboard/*` redirect, beta, `/privacy` bug | retire after V3 parity | medium | P2 | n/a | small | no | legacy policy |

---

## 18. Priority Roadmap

- **P0 (launch blocker — decisions/security):** Viewer permission decision;
  customer-processing role decision; consultant model decision. These gate
  correct role-gating. (A workflow/security blocker, not cosmetics.)
- **P1 (launch-critical):** extraction workspace viewer fix (operators +
  PE); customer Review & Approve UI; Custom Emission Factors UI; customer
  item-level processing/evidence view; ops tab permission filtering; PE
  clarification triage (ops Issues tab); role-gate Organisation section;
  `/privacy` route fix.
- **P2 (important completeness):** attention-first dashboard; document
  preview; report PDF/Excel/CSV buttons; issue conversations; consultant
  workspace depth; staff review rendered source; QC checklist; entity
  dashboard; SLA integration; design-token consolidation; accessibility
  pass; terminology/IA pass; legacy/beta cleanup; factor catalogue.
- **P3 (future):** CSV/Excel mapping UI; admin/control plane sections;
  AI-provider configuration; retention controls; mobile-first extraction;
  multi-org switching.

---

## 19. Implementation Dependencies

| Initiative | Frontend | Backend/API | RLS/Security | Database | Auth | Storage | Config | PO decision |
|---|---|---|---|---|---|---|---|---|
| Role-gated nav/controls | yes | no | no | no | no | no | no | **viewer + roles** |
| Customer approval UI | yes | no | no | no | no | no | no | approver role |
| Custom factors UI | yes | no | no | no | no | no | no | editor/approver |
| Item processing/evidence view | yes | small (customer item read) | verify scope | no | no | no | no | customer processing role |
| Extraction viewer fix | yes | small (view-only URLs) | yes (scope check) | no | no | yes (signed) | no | no |
| PE clarification triage | yes | yes (triage/reply) | yes (entity scope) | no | no | no | no | no |
| Issue conversations | yes | yes (reply) | yes | no | no | no | no | no |
| Report downloads | yes | no | no | no | no | no | no | no |
| Consultant workspace depth | yes | small | verify grants | no | no | no | no | **consultant model** |
| Design tokens | yes | no | no | no | no | no | no | no |
| Accessibility | yes | no | no | no | no | no | no | no |
| Admin control plane | yes | per section | per section | no | no | no | yes | scope |
| Legacy cleanup | yes | no | no | no | no | no | no | legacy policy |

**Guardrail:** no frontend feature may be built that conflicts with the
backend authorization model (e.g., a PE download button, a customer extract
control without a role decision, a consultant write control without a model
decision). Backend remains authoritative.

---

## 20. Recommended Implementation Sequence

Grounded in the repo evidence and dependencies (not the generic list):

1. **Decisions first** (§22) — Viewer, customer processing role, consultant
   model, approver role. No role-gated UI work before these.
2. **Backend hardening (small, non-UI)** — view-only signed URLs for
   assigned-item surfaces (unblocks the workspace); issue triage/reply
   endpoints; customer item-read endpoint if needed.
3. **Shared foundations** — design tokens + status vocabulary component +
   evidence-trail component (these underpin everything else).
4. **Extraction workspace fix** (operators + PE) — the core workflow must
   work before customer-facing depth.
5. **Customer processing + Review & Approve** (§5.3/§5.4) — the PO-mandated
   customer flow.
6. **Custom Emission Factors UI** (§5.9) — established capability surfaced.
7. **Evidence chain navigation** (§11) — customer item-level traceability.
8. **Role-gated IA + organisation admin** (§4/§5.10).
9. **Internal operations completeness** — ops tab filtering, review source,
   QC checklist, issues triage (§7).
10. **Processing Entity completeness** — dashboard, review/QC, performance
    (§8).
11. **Consultant depth** (§6) after model decision.
12. **Reports/CSV-Excel completeness** (§5.7, §10 CSV).
13. **Accessibility + responsive passes** (§13/§14).
14. **Legacy/beta cleanup** once V3 parity is confirmed.

---

## 21. CLINE IMPLEMENTATION HANDOFF

### A. What Cline should eventually implement

- The §5–§8 screens and §12 design-system foundations, exactly as specified,
  behind the role/IA decisions in §4.
- The §11 evidence-trail component and its integrations.
- The §10 end-to-end workflow wiring (states, actions, events).
- The §15–§16 feedback/state components.

### B. What Cline must NOT change

- Backend/API/RLS/schema/migrations/auth/permissions (beyond the explicitly
  listed small read/triage endpoints in §19).
- The one-person-one-role model; the PE no-download boundary; signed-URL
  storage model; server-authoritative calculation; immutable snapshots;
  factor data.
- The public marketing website.
- Any behavior pending a §22 decision.

### C. Backend dependencies

- View-only signed URL issuance for assigned-item surfaces (operator + PE).
- Customer item read (evidence) endpoint if required.
- Issue reply/triage endpoints (customer conversation + PE mediation).
- All other target UI relies on **existing** endpoints (`[V]` in §17).

### D. Product Owner decisions required before implementation

See §22 — Viewer, customer processing role, consultant model, approver role,
PE metrics, report automation, owner model.

### E. Recommended implementation phases

Phase 0: decisions + backend hardening. Phase 1: design tokens + status
vocabulary + extraction workspace fix. Phase 2: customer processing +
approval + evidence. Phase 3: custom factors + organisation role-gating.
Phase 4: internal ops completeness. Phase 5: PE completeness. Phase 6:
consultant. Phase 7: reports/CSV-Excel/accessibility. Phase 8: legacy cleanup.

### F. Acceptance criteria per phase

Each phase is accepted when: all flows reachable by the correct roles; no
unauthorized controls visible; no 403-on-click from UI; status vocabulary
labelled everywhere; evidence trail renders for every result; PE cannot
download; all new UI uses the shared design system; accessibility checklist
(§13) passes for the phase's screens.

### G. Tests that should accompany each phase

- Role-gating tests per context (what each role sees; 403s not triggered
  from UI).
- Workflow tests: upload→extract→map→calc→validate→review/QC→approve→report
  happy path + rejection/return + clarification loops.
- Evidence-chain navigation tests (forward/back).
- PE security tests: no signed URL for entity staff outside assigned items;
  no download controls.
- Design-system regression (shared tokens/components used; no new ad-hoc
  colors).
- Accessibility smoke (axe) per phase.

---

## 22. Product Owner Decisions Required

1. **Exact Viewer permissions.** Read-only, or editor-without-admin?
   (Today: viewer is functionally a writer — `VERIFIED`.)
2. **Customer processing participation.** May customers perform extraction/
   mapping/calculation themselves (self-service operator), or are they
   submit/monitor/review/approve only, with CarbonTally/PE performing
   processing? (Today: customer pipeline is API-open to all members with no
   UI.)
3. **Consultant operating model.** Status/reporting/advise users (default),
   or active processing users with an org-scoped item workspace?
4. **Owner vs Admin distinction.** Are they identical (current), or does
   Owner get exclusive rights (transfer ownership, remove admins, sole
   billing)?
5. **Processing Entity metrics.** Which performance/SLA metrics may an entity
   see about itself? (Never cross-entity or customer-identifying.)
6. **Customer approval permissions.** Which role(s) may approve/reject items
   (owner/admin only, or any member)? Today: any org member via API.
7. **Report generation model.** Manual only (current), scheduled, or
   automatic on approval?
8. **Multi-organisation consultant switching UX.** Keep active-client model
   (recommended); confirm whether a consultant may switch among several
   clients in one session (currently yes via client switcher) and whether
   org-member users may have multiple org memberships with switching.
9. **PE validation scope.** PO §2.3 allows PE validation/review/QC; current
   internal guard denies PE `validate`. Confirm the exact PE action set.
10. **Custom factor editors.** May Members create/edit custom factors, or
    Owner/Admin only? (Today backend is member-level; approve is admin.)
11. **Legacy/beta retirement scope.** Confirm which legacy routes/beta
    entry points to retire and when (PO §9).

---

## 23. Final Recommendation

**Recommended target architecture:** five coherent, role-first operating
experiences (Customer, Consultant, CarbonTally Staff, Processing Entity,
Admin control plane) built on one token-based design system, one shared
status vocabulary, and one universal evidence trail — all layered on the
existing backend authorization model without weakening the PE no-download
boundary or the one-person-one-role identity model.

**Top 10 UX priorities**

1. Resolve the §22 role decisions (Viewer, customer processing, consultant,
   approver).
2. Fix the extraction workspace document viewer (operators + PE).
3. Ship customer Review & Approve.
4. Ship Custom Emission Factors UI.
5. Build the customer item-level processing + evidence view.
6. Role-gate navigation and organisation admin.
7. Filter ops tabs by permission; add ops issues triage.
8. Build the universal evidence trail.
9. Surface report PDF/Excel/CSV downloads.
10. Consolidate the design system into tokens + shared components.

**Top 10 implementation risks**

1. Implementing role-gated UI before decisions → rework.
2. Weakening the PE no-download boundary while fixing the viewer (must
   remain view-only, signed, scoped).
3. Building customer processing UI that assumes a role not decided.
4. Making the evidence trail read endpoints too open (org/scope leaks).
5. Breaking server-authoritative calculation by "helpful" client-side
   features.
6. Design-system refactor regressing the working ops queues.
7. Issue-reply/triage endpoints weakening tenant/entity scoping.
8. Over-scoping the admin control plane beyond existing APIs.
9. Legacy cleanup breaking a V3 dependency.
10. Accessibility pass incomplete on the extraction workspace (core
    workflow).

**Product Owner decisions needed:** the §22 list (all 11 items).

**What should be done next:** Product Owner reviews §22 and the blueprint;
decisions are recorded in the Decision Register; then a Cline implementation
prompt is generated from §21 (Phase 0 → Phase 8).

---

*End of blueprint. Read-only documentation task — no application, schema,
RLS, API, migration, configuration, authentication or permission changes were
made.*
