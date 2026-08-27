# CarbonTally V3 — MASTER UX DECISION RECONCILIATION REPORT

| | |
|---|---|
| Document type | Final reconciliation report (authoritative) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | COMPLETE — D1–D21 APPROVED / FROZEN; target UX reconciled with implementation |
| Date | 2026-08-24 |
| Author | CarbonTally V3 Product Documentation, Product UX Reconciliation and Design-System Specification Agent (OpenHands) |
| Mode | **DOCUMENTATION-ONLY.** No application code, backend, Supabase, database, schema, migration, RLS, API, authentication, configuration, deployment, package files or tests were modified. |

## 1. Executive summary

CarbonTally V3's product decisions **D1–D21** are recorded as **APPROVED /
FROZEN** in `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`.
**N1–N3** (messaging access, Locations physical representation, configurable
retention) were approved afterwards and supplement D1–D21 (register §24–§26;
see §33).
This report reconciles those decisions with the current implementation
(frontend, backend/API, database/RLS) and the live platform, and produces a
single coherent target-UX specification for the next engineering phase.

**Selected architecture:** Option B (workflow-first) as the platform + Option
C (modern/guided) for customer/onboarding/evidence surfaces + Option A
(enterprise/control-plane) for CarbonTally Admin (D18/D21).

**Key findings:**

- The current V3 implementation is already substantially workflow-first and
  aligned with D1–D21 (role-aware top navigation, split-screen workbench
  precedent, entity assignment, self-service onboarding, provider-neutral
  billing, evidence records).
- The main gaps are UX-completion gaps rather than architectural conflicts:
  a dedicated Customer Review & Approve UI, a Custom Factors UI, an explicit
  top-workflow-nav workbench with pane presets and confidence indicators, a
  unified design-system token layer, Vehicles (and distinct Locations)
  master data, a consolidated audit/admin console, and responsive tray-based
  workbench behaviour.
- Two implementation states are documented honestly: the **committed
  baseline** (the repository) and the **live application** (which runs
  additional uncommitted public-site changes). Neither is treated as
  automatically authoritative over the frozen product decisions.

## 2. Source-of-truth hierarchy

1. Product Owner Decision Register (D1–D21) — `docs/ChatGPT/...`.
2. Explicit Product Owner decisions in the current task.
3. Approved Master UX Recommendation / reconciliation (`MASTER_UX_RECOMMENDATION.md`).
4. Approved UX/design documents (`docs/audit/openhands/ui-ux/`).
5. Current application / database / API implementation.
6. Earlier audits and historical reports.
7. Older / superseded documents.

Conflicts were reconciled by applying the higher-authority source and
recording the reconciliation (never silently deleting historical evidence).

## 3. D1–D21 status

All **D1–D21 = APPROVED / FROZEN**. No decision remains marked unresolved; no
decision was re-opened; no duplicate decision numbers were created. See the
decision register §2 for the summary table.

**N1–N3 supplement D1–D21** (approved after the reconciliation; decision
register §24–§26): N1 Messaging Access and Communication Boundaries
(APPROVED / FROZEN), N2 Location Physical Data-Model Representation (PO
DIRECTION RESOLVED; ENGINEERING DECISION), N3 Configurable Data Retention
(APPROVED PRODUCT MODEL; IMPLEMENTATION DETAIL REMAINS). They do not alter,
reopen or renumber any D1–D21 decision.

## 4. Current target architecture

- Platform: workflow-first (Option B).
- Customer / onboarding / evidence: modern/guided (Option C).
- CarbonTally Admin: enterprise/control-plane (Option A).
- Processing workbench: split-screen + top workflow navigation (D19).
- Visual system: one unified design system (D21) built on the existing
  CarbonTally `v3.css`/`App.css` identity.
- Billing: provider-neutral (D11); indicative GBP pre-launch pricing (D12).

## 5. Customer UX

- Navigation: Home, Documents, Processing, Emissions, Reports, Issues,
  Billing, Organisation (D18). Current labels: Dashboard(=Home),
  Emissions, Documents, Processing, Issues, Reports, Messages, Existing data,
  Billing, Organization.
- Prioritised: attention dashboard, processing status, review, approval,
  issues, evidence, reports, emissions, notifications.
- Gaps: dedicated Review & Approve UI (P0-2); Custom Factors tab (P0-3);
  "Home" label (P0-7); Organisation Activity/Settings (P1-4).

## 6. Consultant UX

- Active-client model with explicit context (D3/D8); firm + client management;
  white-label foundation (D14/D21).
- Prioritised: active client, client switching, client status, workflow,
  issues, reports, evidence.
- Gaps: full white-label rendering (P2-1), firm-role demo coverage (P2-4),
  raw UUID copy (P2-5).

## 7. Processing Entity UX

- Entity-scoped work surface: assigned batches/items only; extraction/mapping/
  calculation; mediated clarification; **no customer/consultant access; no
  download of source** (D6/D18/D22).
- Current: D22/D24 implemented and verified (transient fixture); entity staff
  land on `EntityExtractionWorkspace`.
- Gaps: full mediated messaging threads (P1-1), entity SLA/capacity
  automation (P2-3), permanent entity-staff demo identity (note).

## 8. CarbonTally Staff UX

- Ops hub tabs: Dashboard, Data entry, Review, QC, Staff, Roles, Entities,
  SLA, Commercial.
- Prioritised: operational queue, assignments, extraction, review, QC, PE
  coordination, issues, escalation, evidence.
- Gaps: ops issues triage polish (P0-4), audit/log UX (P1-7), global search
  (P1-8).

## 9. CarbonTally Admin UX

- Dense control-plane (Option A) for platform administration; org admin stays
  in the customer surface (D4).
- Prioritised: organisations, users, roles, Processing Entities, consultants,
  billing, subscriptions, pricing, factor governance, system configuration,
  audit, security, logs, operational monitoring.
- Current: Commercial/Entities/SLA/Staff/Roles tabs implement much of this;
  a unified admin console is a P1 gap (P1-6).

## 10. Master-data UX

- Conceptual: Organisation → Locations → Facilities → {Assets, Vehicles};
  Suppliers org-scoped (D17).
- Implemented: Facilities, Assets, Suppliers (tables + APIs + admin tabs).
- **Gaps:** Vehicles end-to-end missing (P1-2); Locations as a distinct
  entity missing (facilities doubles as locations) (P1-3).
- Master data remains secondary to workflow navigation (D18); no forced
  configuration before processing.

## 11. Navigation architecture

- Workflow-first top navigation rail (D18), role-aware
  (`V3Layout.jsx` resolves org/staff/consultant).
- No left-side sidebar inside workbenches (D19).
- Ops uses tab-based hub; admin uses denser control-plane patterns.
- Target label fixes: "Dashboard"→"Home", "Messages"→"Messaging"; add
  Organisation secondary entries (Locations, Facilities, Assets, Vehicles,
  Suppliers, Members, Custom Factors, Activity, Settings).

## 12. Split-screen workbench

- Mandatory for source+structured-data workflows (D19).
- Current precedent: `ExtractionPanel.jsx`, `WorkItemWorkspace.jsx`,
  `EntityExtractionWorkspace.jsx` (source pane + data pane).
- Target: explicit top workflow navigation (Queue → Extract → Map → Validate →
  Review → QC → Evidence), pane presets 40/60 · 50/50 · 60/40, confidence
  indicators, source↔field links, autosave, lock states,
  approval/rejection states, immutable calculation/evidence boundaries,
  keyboard operation, accessibility (P0-1).

## 13. Top workflow navigation

- The workbench MUST use top workflow navigation and must NOT consume
  horizontal space with a permanent left-side application sidebar (D19).
- This is a core difference from ERP-style module layouts and from the
  historical "sidebar workbench" anti-pattern (see §31–§32 for stale-phrase
  reconciliation).

## 14. Responsive / mobile strategy

- Desktop primary for extraction/mapping/validation/QC/structured entry (D20).
- Tablet: adaptive workbench layouts and trays.
- Mobile: monitoring, notifications, status, lightweight review, evidence
  inspection, approval/rejection, comments, clarification, lightweight actions.
- Do NOT shrink the desktop workbench onto a phone (tray-based instead).
- Gap: P0-8 (responsive workbench).

## 15. Design-system findings

- A shared V3 visual system exists (`v3.css`) plus page-level stylesheets.
- **Inconsistent:** two green primaries (`#2f855a` v3 vs `#2d6a4f` App.css);
  several blue accents; differing borders/text greys.
- **Missing:** token set, icon set, status system vocabulary, confirmation
  patterns, adaptive responsive behaviour.
- Target: `CARBONTALLY_V3_DESIGN_SYSTEM.md` (extends the existing identity;
  P0-9 consolidation).

## 16. Colour system

- Existing semantic tokens documented in the design system §2 (success,
  warning, error, info, pending, evidence complete/partial/unavailable,
  nav, focus, disabled).
- Target palette defined; status never by colour alone (D21.1).

## 17. Typography

- System font stack; monospace for formulas/IDs; heading hierarchy
  (26/24/18/16/15/14/12px); table, label, metadata, helper, error
  conventions documented (design system §3).

## 18. Iconography

- Current: ad hoc emoji glyphs; no icon library.
- Target: one semantic icon set with a mapping for Home, Documents,
  Processing, Emissions, Reports, Issues, Billing, Organisation, Locations,
  Facilities, Assets, Vehicles, Suppliers, Members, Custom Factors, Evidence,
  Validation, Review, Approval, Rejection, Settings, Logs, Audit,
  Notifications (design system §4).

## 19. Status system

- Vocabulary reconciled with the backend state model (ITEM/BATCH/REPORT/
  ISSUE/ENTITY statuses) and mapped to text + icon + colour (D21.4,
  design system §5).

## 20. Components

- Cards, panels, drawers, modals, alerts, notifications, status indicators,
  loading/empty/error states, confirmation patterns, data visualisation
  conventions documented (design system §11).

## 21. Accessibility

- Target WCAG 2.2 AA; keyboard navigation, visible focus, contrast, semantic
  HTML, screen readers, accessible forms, error announcements, icon-only
  controls, modal focus management, tables, status communication without
  colour alone (design system §10).

## 22. Notification architecture

- In-app notifications implemented (per-user, V3 notifications page).
- Action-required vs informational classification target; landing target
  defined (ASCII H1).
- Email notifications: foundation exists; delivery is external config.
- Gap: notification preferences integration (P2-2).

## 23. Auditability

- Who/What/When/Previous/New/Reason visible for important state changes:
  approval, rejection, correction, QC, factor changes, assignment, document
  actions, billing/admin changes.
- Backing: `audit_trail`, `domain_events`, `review_assignment_history`,
  `customer_review_log`, `calculation_snapshots`.
- Gap: consolidated audit UI (P1-7).

## 24. System settings / logging

- Customer settings vs platform administration clearly distinguished (D4).
- Target UX: Organisation settings (profile, members, retention, activity)
  for customers; admin control-plane (system configuration, billing config,
  factor governance, PE configuration, audit logs, security events,
  operational logs, workflow/job history, failed jobs, health/configuration)
  for CarbonTally Admin.
- Gaps: Organisation Settings/Activity (P1-4), admin console (P1-6),
  audit/logs UX (P1-7).

## 25. AI Assistant UX

- AI may assist navigation, explanation, contextual help, extraction
  suggestions, document assistance, workflow guidance (D16).
- AI MUST NOT be authoritative for calculations, factor selection, evidence,
  approval, security, org access, compliance certification.
- The full AI Assistant architecture is an authoritative member of this
  package: `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (public prototype +
  authenticated tiered model; PUBLIC ASSISTANT / AUTHENTICATED
  ROLE-SCOPED ASSISTANT / NORMAL CARBONTALLY WORKFLOWS distinction).
- Current: AI-assisted extraction engine exists (`engines/ai_extraction.py`)
  as a suggestion engine with confidence; no production assistant UI surface
  exists (public prototype lives in the OHD `website_candidate` export).
- Target: assistant surfaces are clearly labelled as guidance; authoritative
  values always show human/server review (see ASCII designs). The assistant
  is a front-end over existing authorization — never an alternative
  permission or workflow engine.

## 26. Database ↔ UX reconciliation

| Domain | Target UX | Current DB | Current API/backend | Current FE | Gap | Engineering dependency |
|---|---|---|---|---|---|---|
| Organisation | tenant + workspace | `organizations`, `organization_metadata`, `organization_members` | org routes | V3 customer/admin | minor (nav labels) | none |
| Locations | master data | no separate table (facilities doubles) | none specific | none | **P1-3** | engineering decision per N2 + DB/API/FE |
| Facilities | master data | `facilities` | `/organizations/{id}/facilities` | admin tab | none | — |
| Assets | master data | `assets` | assets routes | admin tab | none | — |
| Vehicles | master data | **none** | **none** | **none** | **P1-2** | table+RLS+API+FE |
| Suppliers | master data | `suppliers` | `/v3/suppliers` | admin tab | none | — |
| Members | org roles | `organization_members` | members routes | admin tab | none | — |
| Consultants | firm + clients | consultant tables | consultant routes | consultant workspace | full white-label P2-1 | FE/email/domains |
| Processing Entities | entity model | `processing_entities`, `staff_profiles.entity_id` | entity routes + workspace | entity workspace | controlled clarification (N1-E), no direct Customer↔PE chat | conversation RLS implementation (N1-F) |
| Staff | staff roles/permissions | `staff_roles`, `staff_profiles` | ops routes | ops hub | audit/log UX P1-7 | FE |
| Admin | control plane | admin tables | admin APIs | ops tabs | unified console P1-6 | FE |
| Documents | private storage | `organization_files` (D32) | documents routes | documents page | — | — |
| Extraction | workbench | `manual_extraction_batches/items` | processing-workflow routes | workbench | top nav/presets P0-1 | FE |
| Mapping | workbench | items + `factor_aliases` | mapping-options | workbench | — | — |
| Validation | workbench | items | validate route | workbench | — | — |
| PE QC | entity QC | items `qc_*` | entity workspace | entity workspace | — | — |
| CarbonTally QC | internal QC | items `qc_*` | qc routes | QC queue | — | — |
| Customer review | evidence-first review | `customer_verifications` | customer-review route | **missing** | **P0-2** | FE |
| Customer approval | approver role | verifications | customer-review route | **missing** | **P0-6** | FE |
| Calculations | server-authoritative | `calculation_snapshots` (O1) | calculate route | emissions | — | — |
| Evidence | universal trail | D33 evidence records | evidence endpoints | partial | **P0-5** | FE |
| Emissions | scoped + trend | `emissions_logs` | emissions routes | emissions page | — | — |
| Reports | branded outputs | `report_versions` | reports routes | reports pages | full branding P2-1 | FE/email |
| Issues | first-class | `issues` | issues routes | customer/ops/entity | ops triage P0-4 | FE |
| Messaging | mediated (N1) | conversations/messages | messaging routes | messaging page | **P1-1** (RLS) | implement N1-F (RLS/API enforcement) + FE |
| Billing | provider-neutral | billing tables (D37) | billing routes | billing page | live provider: none by design | external |
| Custom Factors | org-scoped lifecycle | `customer_factors` (V3M-3) | factor routes | **missing** | **P0-3** | FE |
| AI | suggestion only | ai_content_history | AI extraction engine | none | assistant surfaces target | FE |
| Audit Logs | consolidated | audit tables | audit routes | **missing** | **P1-7** | FE |
| System Logs | ops visibility | processing_logs etc. | ops/admin | partial | P1-6/P1-7 | FE |

## 27. Security / RLS reconciliation

- Three RLS axes preserved: org (`is_org_member`), consultant
  (`is_org_consultant` with ACTIVE grant — D15 implemented), entity
  (`is_entity_member`, active entity only).
- **PE boundary verified**: entity staff cannot reach customer org data,
  users, consultants, documents beyond assigned work, contact info, messaging,
  reports, billing; notifications are per-user; entity extraction is
  assignment-scoped (D22); mediated clarification via entity-scoped issues.
- **Latent risk recorded** (historical, from the access-model doc §35.5):
  name-string `require_admin`/`is_admin` authorization could over-grant an
  entity-staff profile carrying an `admin` role — no entity staff exist in
  production, but this is a REQUIRES ENGINEERING DECISION security-hardening
  item before entity provisioning at scale.
- **Chat RLS gap**: `conversation_participants` has zero RLS policies
  (deny-by-default) — chat is non-functional end-to-end. **N1 now defines
  the approved messaging access model** (who may converse with whom). The
  remaining work is **engineering implementation** of N1-F (conversation
  RLS/API enforcement), classified REQUIRES ENGINEERING DECISION (P1-1),
  not a product decision. The UI must never be treated as the security
  boundary; the assistant inherits the same permissions (N1-F).
- No RLS was modified.

## 28. Role × workflow matrix

Classification: Allowed / Not Allowed / Conditional / Delegated / Read-only /
Not Applicable.

| Workflow | Owner | Admin | Member | Viewer | Consultant | PE staff | Staff | CarbonTally Admin |
|---|---|---|---|---|---|---|---|---|
| Signup/onboarding | A | A | A | A | A | NA | NA | NA |
| Organisation setup | A | A | Not | Not | NA | NA | NA | NA |
| Members/invite | A | A | Not | Not | NA | NA | NA | A |
| Consultant client mgmt | NA | NA | NA | NA | Conditional (can_manage_clients) | NA | NA | A |
| Document upload | A | A | A | A | Conditional (can_upload_documents) | Not | Not (ops) | NA |
| Classification | A | A | A | A | Conditional | NA | A (engine/staff) | NA |
| Extraction | Not | Not (create extraction) | Not | Not | Conditional | Delegated (assigned) | A (can_process) | NA |
| Mapping | NA | NA | NA | NA | NA | A (assigned) | A | NA |
| Validation | NA | NA | NA | NA | NA | Conditional | A (can_review) | NA |
| PE processing | NA | NA | NA | NA | NA | A (assigned) | Assigns | NA |
| PE QC | NA | NA | NA | NA | NA | Conditional (own entity) | A | NA |
| CarbonTally QC | NA | NA | NA | NA | NA | Not | A (can_review); admin surface | A |
| Clarification | A | A | A | A | Conditional | Delegated (mediated) | A | NA |
| Correction/rework | NA | NA | NA | NA | NA | Conditional | A | NA |
| Customer review | A | A | A | A (read) | NA | Not | NA | NA |
| Customer approval | A | A | Not | Not | NA | Not | NA | NA |
| Calculation | A (trigger) | A | A | A | Conditional | A (assigned) | A | NA |
| Evidence | R/O | R/O | R/O | R/O | Conditional | Conditional (assigned) | A | R/O |
| Reporting | A | A | A | A | Conditional (can_generate_reports) | Not | Not | A |
| Issues | A | A | A | A | Conditional | Conditional (own entity) | A | A |
| Messaging | A | A | A | A | Conditional | Not (mediated only) | A | A |
| Billing | R/O | R/O | Not | Not | NA | Not | Not | A |
| Custom factors | A (approve) | A (approve) | A (propose) | Not | Conditional (grant) | Not | A (manage drafts) | A |
| Master data | A | A | Not | Not | Conditional | Not | Not | A |
| AI assistance | A | A | A | A | A | A (guidance) | A | A |
| Audit/log review | R/O | R/O | Not | Not | NA | Not | A | A |
| Administration | NA | NA | NA | NA | NA | NA | A (per permission) | A |

This matrix reflects the approved access model (D1–D8) and the current
implementation guards; no new permissions were invented.

## 29. P0 gaps

P0 = release-blocking UX gaps (details + acceptance criteria in
`UI_UX_IMPLEMENTATION_MATRIX.md` §1):

1. G-P0-1 Secure extraction/document viewer workbench (top workflow nav +
   split panes + presets + confidence + source↔field links + autosave/locks).
2. G-P0-2 Customer Review & Approve UI.
3. G-P0-3 Custom Factors UI.
4. G-P0-4 Operations issues triage.
5. G-P0-5 Universal evidence trail UI.
6. G-P0-6 Approver-role implementation.
7. G-P0-7 Workflow-consistency fixes (nav labels, status vocabulary).
8. G-P0-8 Responsive workbench.
9. G-P0-9 Design-system token consolidation.

P0 review (per task): extraction viewer exists as split panes but lacks the
full workbench contract; Customer Review & Approve UI is missing (backend
ready); Custom Factors UI missing (backend ready); issues triage partially
implemented; evidence trail partially implemented; approver role partially
implemented; workflow consistency needs label/status fixes; responsive
workbench needs tray behaviour; design-system tokens need consolidation.

## 30. P1/P2 gaps

See `UI_UX_IMPLEMENTATION_MATRIX.md` §2 (P1: messaging/mediated
clarification, Vehicles, Locations, Activity/Settings, retention, admin
console, audit/log UX, search) and §3 (P2: full white-label rendering,
notification preferences, entity SLA/capacity, consultant firm roles, UUID
copy, multi-org UX).

The product direction for the messaging, Locations and retention P1 items is
resolved (N1–N3; decision register §24–§26); the remaining work in each row
is engineering implementation with the dependencies recorded in the matrix.

## 31. Historical conflicts preserved

- Three UX options preserved as historical documents
  (`UI_UX_OPTION_A/B/C_*.md`); the composition B+C+A is marked as the current
  target.
- ADR register statuses (PROVISIONALLY DECIDED → DECIDED) preserved as
  historical evidence.
- The pre-D22 "entity assignment gap" analysis preserved in the access-model
  document (now resolved/implemented).
- The committed baseline `PricingPage.jsx` (USD, proposed) preserved in git
  history; the GBP indicative direction supersedes it.
- D34 "NOT READY — beta-gated signup" finding preserved; D35 implemented
  self-service onboarding and is recorded as the current state.

## 32. Stale conflicts reconciled

| Stale phrase / status | Classification | Resolution |
|---|---|---|
| "PO DECISION REQUIRED / Decision Required / TBD" | STALE WORDING | No D1–D21 item requires a decision; all are APPROVED / FROZEN. The previously open N1/N2/N3 items are resolved (see §33); no PO product decision remains unresolved. |
| "N1/N2/N3 PO DECISION REQUIRED" · "messaging RLS decision pending" · "Locations as distinct entity requires PO decision" · "retention policy requires PO decision" · "three remaining PO decisions" | STALE WORDING | N1 (messaging access) APPROVED / FROZEN; N2 (Locations physical representation) PO DIRECTION RESOLVED — engineering decision; N3 (configurable retention) APPROVED PRODUCT MODEL — implementation detail remains. Recorded in the decision register §24–§26. |
| "Option A/B/C unresolved" | STALE WORDING | Composed as B+C+A (current target); options preserved as historical. |
| "sidebar workbench / left navigation inside workbench" | STALE WORDING (anti-pattern) | D19 mandates top workflow navigation; no left sidebar inside workbenches. |
| "facilities missing / assets missing / suppliers missing" | IMPLEMENTATION GAP (resolved) | Facilities/Assets/Suppliers implemented. **Vehicles** missing; **Locations** as distinct entity missing. |
| "customer approval unresolved" | STALE WORDING | D2/D5 approved/frozen; backend ready; UI is P0-2. |
| "AI provider unresolved" | STALE WORDING | D16 approved/frozen: AI is assist-only, never authoritative. |
| "waitlist / beta access" | HISTORICAL | Committed baseline LandingPage still has a beta modal; D13 + live site use "Request launch information"; `/signup` is self-service (D35). |

## 33. Decision resolution status (N1–N3) and remaining engineering decisions

The three items previously flagged as NEW PO DECISION REQUIRED have been
reviewed and approved by the Product Owner. They are recorded in the decision
register §24–§26 and supplement (never replace) D1–D21:

| # | Decision | Status | Product/UX consequence | Remaining engineering work |
|---|---|---|---|---|
| N1 | **Messaging Access and Communication Boundaries** | **APPROVED / FROZEN** | Customer-org internal; consultant internal + active-client customers; Customer Support/Admin scoped support threads; PE Manager↔PE users + CarbonTally operational; **no direct Customer↔PE chat** — clarification via the controlled processing/clarification workflow. UI is not the security boundary. | Implement N1-F: conversation RLS/API enforcement (minimum change to existing schema — N1-G). See implementation matrix G-P1-1. |
| N2 | **Location Physical Data-Model Representation** | **PO DIRECTION RESOLVED; ENGINEERING DECISION** | Locations remains a first-class D17 product concept; no separate physical `locations` table is required. | Engineering inspects the existing schema and decides: dedicated Locations table/entity OR Facilities reuse, satisfying D17 UX. See implementation matrix G-P1-3. |
| N3 | **Configurable Data Retention** | **APPROVED PRODUCT MODEL; IMPLEMENTATION DETAIL REMAINS** | Retention is configurable via the appropriate Settings/Admin control plane; no invented durations; server-side enforcement. | Settings/Admin retention UI + server-side enforcement (G-P1-4/G-P1-5); default values (where not already specified) are business/engineering configuration. |

**Remaining open items are engineering implementation decisions**, not PO
product decisions — none block Cline implementation of the UX baseline:

1. Conversation RLS/API design and the minimal schema changes to enable N1
   (inspect `conversations`/`messages`/`conversation_participants` first).
2. N2 data-model choice (dedicated Locations table vs Facilities reuse) after
   schema inspection.
3. N3 configuration surface and server-side enforcement mechanics; retention
   default values (business/engineering configuration).
4. Entity-staff `admin`-role hardening noted in §27 (before entity
   provisioning at scale).
5. Vehicles master data end-to-end (G-P1-2): table + RLS + API + FE.

**AI assistant programme decisions** remain recorded separately in
`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §13 (provider choice for
Phase 2, answer style, FAQ source of truth, branding, chat-log retention,
feedback surfacing, PE document boundary reconfirmation, entry points).

## 34. Cline implementation handoff

1. **Start from the frozen decisions + N1–N3** (`docs/ChatGPT/...DECISION_REGISTER_v1.md`, §3–§23 for D1–D21 and §24–§26 for N1–N3).
2. **Read the reference index and master index** for the doc map.
3. **Target UX narrative:** this report + `MASTER_UX_RECOMMENDATION.md`.
4. **Workflows:** `MASTER_WORKFLOW_MAP.md` (align with
   `backend/domain/partners.py` statuses).
5. **Screens:** `MASTER_SCREEN_INVENTORY.md`.
6. **Interactions:** `MASTER_UI_UX_ASCII_DESIGNS.md`.
7. **Visual:** `CARBONTALLY_V3_DESIGN_SYSTEM.md` — extend the existing
   CarbonTally identity; consolidate tokens first (P0-9).
8. **Gaps:** `UI_UX_IMPLEMENTATION_MATRIX.md` — implement P0 → P1 → P2; every
   row has acceptance criteria and engineering dependencies.
9. **Traceability:** use the Decision → Screen → Workflow → Engineering chain
   (see §35 example).
10. **Status discipline:** use the implementation-status labels; never claim a
    target feature as implemented without current evidence.

## 35. Decision → screen → workflow → engineering traceability (examples)

**Example 1 — D19 → PE → Extraction Workbench → Extraction workflow → Top
workflow nav + split panes → OCR/extraction APIs → Secure scoped document
access → Human review + source linking + autosave → Frontend/API/security
tests.**

**Example 2 — D5 → Customer Approver → Review & Approve screen → Customer
approval workflow → Evidence-first Approve/Reject with reason → customer-review
API + audit → Org-admin/owner authorisation → Approver identity + audit
record → Frontend/API/security tests.**

**Example 3 — D9 → Org Admin → Custom Factors tab → Factor lifecycle
workflow → Draft/approve/deactivate UI → factor CRUD + snapshot provenance →
Org RLS + no-self-approval → Precedence respected + traceability → Frontend/
API tests.**

## 36. Verification

- D1–D21 recorded as APPROVED / FROZEN — yes (§3; decision register).
- Source-of-truth hierarchy documented — yes (§2).
- Database inspected read-only — yes (migrations, tables, RLS).
- API/backend inspected read-only — yes (routes, guards, statuses).
- Frontend inspected read-only — yes (v3, tokens, workbench, nav).
- RLS/security inspected read-only — yes (§27).
- Customer/Consultant/PE/Staff/Admin UX coherent — yes (§5–§9).
- Locations/Facilities/Assets/Vehicles/Suppliers represented — yes
  (Facilities/Assets/Suppliers implemented; Locations/Vehicles gapped).
- Master data org-scoped; not dominating navigation — yes.
- Workflow-first navigation consistent — yes (with label fixes).
- Split-screen workbench mandatory where appropriate — yes; top workflow nav
  explicit — yes; 40/60·50/50·60/40 documented — yes.
- PE no-download boundary preserved — yes.
- Customer review/approval represented — yes (target + backend).
- Evidence traceability represented — yes (D33).
- Server-authoritative calculation preserved — yes.
- AI governance preserved — yes (D16).
- Mobile strategy documented — yes.
- Unified D21 design system documented — yes; `ct-*` tokens inspected (no
  literal `ct-` prefixed CSS variables exist; the V3 token vocabulary is
  `v3-*`/`--v3-*` and App.css `:root` tokens — documented in the design
  system).
- Colours/typography/iconography/status/buttons/forms/tables/accessibility/
  notifications/auditability/settings/logs documented — yes.
- Role × workflow coverage completed — yes (§28).
- Entity lifecycle UX completed — yes (D17 + matrix).
- Three historical UX options preserved — yes.
- B+C+A architecture marked as selected — yes.
- Target vs current implementation separated — yes (labels throughout).
- P0/P1/P2 gaps identified — yes (matrix).
- Cline handoff actionable — yes (§34).
- No unsupported product claims introduced — yes (evidence-based labels;
  no assurance/certification/guaranteed-compliance claims).
- No application code changed — yes (see §37).
- No schema/RLS/API/configuration changed — yes.
- Application remains running — verified (frontend :3000, backend :8050
  healthy).
- Final reconciliation report exists — yes (this document).
- Manifest updated — yes (SHA-256 manifest).

## 37. Explicit no-code-change statement

This task modified **ONLY approved documentation** under `docs/`. Explicitly
verified **zero changes** to:

- frontend application code (`frontend/src/**`)
- backend (`backend/**`)
- Supabase / database / migrations / RLS / functions / triggers / seed data
- API implementation / authentication / configuration / deployment
- package files (`package.json`, `requirements.txt`, lock files)
- tests

Working-tree changes to application code that exist in the original workspace
(pre-existing uncommitted public-site work) were **not** touched. The running
application was **not** stopped, restarted or reconfigured.

*End of final reconciliation report. Documentation-only — no implementation performed.*
