# CarbonTally V3 — UI/UX IMPLEMENTATION MATRIX

| | |
|---|---|
| Document type | Implementation gap matrix (authoritative) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE (UX phase) — do not claim implementation without evidence |
| Date | 2026-08-24 |
| Priority scale | P0 = release-blocking UX gap · P1 = serious · P2 = should fix · P3 = nice to have |

For every row: Target UX (frozen D1–D21) · Current implementation · Database /
API / Frontend support · Engineering dependencies · Acceptance criteria ·
PO decision dependency. Implementation status is evidence-based from
`frontend/src/**`, `backend/api/**`, `supabase/migrations/**` and live probes.

---

## 1. P0 gaps

| # | Screen / workflow | Role | Target UX | Current implementation | DB | API | FE | Backend dep | DB dep | RLS dep | Priority | Acceptance criteria | PO dep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-P0-1 | **Extraction / secure document viewer (workbench)** | S, E | D19 split-screen + top workflow nav; secure view-only source; pane presets 40/60·50/50·60/40; zoom/page nav; confidence; source↔field links; autosave; lock states | Split panes exist (`ExtractionPanel.jsx`, `WorkItemWorkspace.jsx`, `EntityExtractionWorkspace.jsx`); iframe viewer with `sandbox="allow-same-origin"`; signed URLs (D32). No explicit top workflow nav wizard, no pane presets, no confidence badges, no lock states | SUPPORTED (files, signed URLs, private bucket) | SUPPORTED (`mapping-options`, `start/extract/map/calculate`) | PARTIAL (panes yes; wizard/presets/confidence no) | Medium (workbench component) | None | Maintain PE no-download (signed URLs; sandboxed viewer; no download control for entity staff) | **P0** | Workbench renders top workflow nav + source/data panes with 3 presets; source is view-only (no download for PE); confidence shown per field; autosave indicator; keyboard-navigable; ARIA roles | D19 |
| G-P0-2 | **Customer Review & Approve UI** | O/A (approve); M/V (review) | D2/D5 distinct review vs approval; evidence-first; Approve/Reject with reason; audit | Backend `customer-review` route + `ITEM_STATUSES.customer_review→approved/rejected`; `customer_verifications` surface; **no dedicated customer approve UI** in v3 customer workspace | SUPPORTED | SUPPORTED (customer-review; verifications) | **MISSING** (no review/approve screen) | Medium (review/approve page + routing) | None | Org-scoped; approver authority per D5; audit reason | **P0** | Customer sees review-ready items with evidence chain; Approve/Reject posts reason; state changes to approved/rejected; audit record written | D2/D5 |
| G-P0-3 | **Custom Factors UI** | O/A approve; M propose | D9 factor lifecycle surface under Organisation → Custom Factors | `customer_factors` table + API (list/create/approve/deactivate) + RLS; **no V3 UI tab** | SUPPORTED (V3M-3) | SUPPORTED | **MISSING** | Medium (tab + form) | None | Org-scoped `is_org_member`; approval by org Admin/Owner only; no self-approval | **P0** | Tab exists; create draft; approve/deactivate; precedence note; snapshot provenance visible | D9 |
| G-P0-4 | **Operations issues triage** | S, E, O/A/M/V | First-class issues (ADR-V3-009) with triage queue, status, escalation, resolution | Issues API + customer/ops/entity surfaces implemented; ops triage (assign/prioritise/escalate UI) needs polish | SUPPORTED | SUPPORTED | PARTIAL | Small-medium | None | Issue org/entity scope | **P0** | Ops sees open issues with priority/status/SLA; can assign/escalate/resolve; entity issues mediated | D6/D18 |
| G-P0-5 | **Universal evidence trail UI** | all | D33 evidence chain visible on every number; Complete/Partial/Unavailable | Evidence records on reports/emissions (`EvidenceRecordPanel.jsx`, report detail); universal evidence panel in workbench target | SUPPORTED (D33) | SUPPORTED | PARTIAL | Medium | None | Org/entity scoped evidence access | **P0** | Every calculated result shows a traceable evidence chain with stable IDs; unavailable is honest | D33/D7 |
| G-P0-6 | **Approver-role implementation** | O/A | D5 approver is a distinct responsibility | `customer_verifications` + `customer-review` route; no explicit approver-role gating UI | SUPPORTED | SUPPORTED | PARTIAL | Small | None | Org admin/owner only approve | **P0** | Approve action visible only to authorised roles; audit records approver identity | D5 |
| G-P0-7 | **Workflow-consistency fixes** | all | D18 nav labels; D21.4 status vocabulary; copy alignment | Nav labels "Dashboard"/"Messages"; statuses partially styled in v3.css | n/a | n/a | PARTIAL | Small (labels/status map) | None | n/a | **P0** | Labels match D18; status system documented and applied consistently | D18/D21.4 |
| G-P0-8 | **Responsive workbench** | S, E | D20 adaptive trays on tablet/mobile; never shrink split | CSS collapses grid ≤900px to single column (functional but not tray-based) | n/a | n/a | PARTIAL | Medium | None | n/a | **P0** | Workbench becomes tray-based under 768px; actions pinned; accessible | D20 |
| G-P0-9 | **Design-system token consolidation** | all | D21 one visual system; single token source | `v3.css` (#2f855a primary) vs `App.css` (#2d6a4f primary) inconsistent; per-area css files | n/a | n/a | PARTIAL | Small-medium (tokens) | None | n/a | **P0** | One token set defined in the design system; both surfaces migrate; visual QA passes | D21 |

## 2. P1 gaps

| # | Screen / workflow | Role | Target UX | Current implementation | DB | API | FE | Backend dep | DB dep | RLS dep | Priority | Acceptance criteria | PO dep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-P1-1 | **Messaging / mediated clarification** | O/A/M/V, S, E | Customer messaging functional (N1-A/B); entity clarification mediated (CarbonTally-only channel, N1-E) | Conversations/messages surface exists; chat non-functional end-to-end (`conversation_participants` deny-by-default, 0 policies); entity clarify via issues | PARTIAL | PARTIAL | PARTIAL | Medium (conversation RLS + wiring) | None | **Yes** (implement N1-F: conversation RLS/API — minimum change, N1-G) | **P1** | Customer-to-customer/support/consultant(active-client) chat works within N1 boundaries; no direct Customer↔PE chat; entity clarification only via mediated issue flow | D6/D18 + N1 |
| G-P1-2 | **Vehicles master data** | O/A | D17 Vehicles as first-class org master data | **No table, no API, no UI** | **MISSING** | **MISSING** | **MISSING** | Medium | Medium (table+RLS) | Org-scoped | **P1** | Vehicles CRUD + archive + related evidence/activity under Organisation → Vehicles | D17 |
| G-P1-3 | **Locations as distinct master data** | O/A | D17 Locations → Facilities (first-class concept; no separate physical table required per N2) | `facilities` serves as "facilities/locations"; no separate Locations entity/UI | PARTIAL (facilities covers) | PARTIAL | PARTIAL | Medium (engineering decision per N2: separate entity vs facilities reuse) | None (if reuse) | Org-scoped | **P1** | Locations surface present; hierarchy documented; no forced configuration; no new table unless schema inspection justifies it | D17 + N2 (engineering) |
| G-P1-4 | **Organisation Activity & Settings surfaces** | O/A/M/V | D18 Organisation → Activity, Settings | Activity feed legacy component; Settings target (incl. retention D15) | PARTIAL | PARTIAL | **MISSING** | Medium | None | Org-scoped | **P1** | Activity tab shows org-scoped event log; Settings tab shows profile, notifications, retention status | D15/D18 |
| G-P1-5 | **Data retention UX** | O/A, ADM | N3 configurable retention (Settings/Admin control plane); D15 visibility; export-before-delete | Storage metering (D37) + private storage (D32); no retention UI/policy | PARTIAL | PARTIAL | **MISSING** | Medium | None (config values = business/engineering config; no durations invented) | Org-scoped (+admin) | **P1** | Settings/Admin shows configurable retention surface; export-before-delete flow; server-side enforcement; no data deletion at limits; audit/evidence not weakened | D15 + N3 |
| G-P1-6 | **Admin control-plane console** | ADM | Option A dense admin: organisations/users/roles/entities/consultants/billing/factors/audit/security/logs/monitoring | Ops tabs (Commercial/Entities/SLA/Staff/Roles) + admin APIs exist; no unified admin console | SUPPORTED | SUPPORTED | PARTIAL | Medium | None | Admin-scoped | **P1** | Admin console covers the P0 admin surfaces with dense tables + audit/logs views | D4/D18 |
| G-P1-7 | **Audit / log UX** | S, ADM | Who/What/When/Previous/New/Reason visible for state-changing actions | `audit_trail`, `domain_events`, review history exist; no consolidated audit UI | SUPPORTED | SUPPORTED | **MISSING** | Medium | None | Admin/staff scoped | **P1** | Audit view for approvals/rejections/QC/assignments/factor changes/billing with before/after + reason | D21/D33 |
| G-P1-8 | **Global/workspace search** | all | Search across documents/emissions/activity within scope | `infra/search_index.py` exists; no search UI | PARTIAL | PARTIAL | **MISSING** | Medium | None | Scope-aware | **P1** | Search box in nav; results scoped to org/client/entity | D18 |

## 3. P2 gaps

| # | Screen / workflow | Role | Target UX | Current implementation | Priority | Acceptance criteria |
|---|---|---|---|---|---|---|
| G-P2-1 | Report branding rendering (full white-label) | C | Rendered logo-in-report, per-consultant outbound email, custom domains, client portal | Foundation implemented; full rendering future | P2 | Branded report output + sender domain verified |
| G-P2-2 | Notification preferences | all | In-app + email notification settings | NotificationSettings component exists; V3 integration target | P2 | Per-user preference surface in V3 |
| G-P2-3 | Entity SLA / capacity automation | S | Per-entity SLA/KPI/capacity | SLA settings exist (org); entity-level automation target | P2 | Entity SLA config + KPI dashboard |
| G-P2-4 | Consultant firm roles coverage | C | manager/consultant/viewer surfaces verified | Demo only has firm owner; roles in API | P2 | Demo coverage + UI verification for firm roles |
| G-P2-5 | Raw UUIDs in consultant UI | C | Show client name, UUID in tooltip | D28 F10 | P2 | No raw UUID in visible copy |
| G-P2-6 | Multi-org membership UX | customer | Explicit org context per user with multiple memberships | Single-org resolution today; multi-org membership rows possible but no switch UI | P2 | Org context explicit; switching where supported |

## 4. P3 gaps

| # | Screen / workflow | Target | Priority | Acceptance criteria |
|---|---|---|---|---|
| G-P3-1 | Global onboarding polish (guided first steps, sample data) | Guided "first run" after org creation | P3 | First-run checklist |
| G-P3-2 | PDF/HTML report export | Structured outputs only today | P3 | PDF export behind a decision |
| G-P3-3 | Break-glass access UX | Admin escalation with audit | P3 | Documented break-glass flow |

## 5. Evidence-based status notes

- **D17 master-data coverage**: Facilities, Assets and Suppliers are
  IMPLEMENTED (tables, org-scoped APIs, admin tabs) — no gap rows are needed
  for them. The D17 gaps are **Vehicles** (G-P1-2, no table/API/UI) and
  **Locations as a distinct entity** (G-P1-3, `facilities` doubles as
  "facilities/locations"). **N2 resolved the product direction**: Locations
  remains a first-class concept; whether to add a dedicated `locations`
  table or reuse Facilities is an engineering decision (G-P1-3). Master data
  remains secondary to workflow navigation (D18) and never blocks processing
  (D17).
- **D37 billing**: subscriptions/entitlements/ledger/orders implemented;
  **no payment-provider integration** (provider-neutral) — do not claim one.
- **D35 onboarding**: self-service signup + org creation + discovery
  implemented and verified.
- **D22 entity assignment**: batch-level entity assignment + entity extraction
  workspace implemented and verified (transient fixture cleaned up; no
  permanent entity staff demo identity).
- **Vehicles and distinct Locations**: end-to-end absent — the only master-data
  entities without implementation evidence. **N2** resolved the Locations
  product direction (engineering decides dedicated table vs Facilities
  reuse); Vehicles remains an engineering gap (G-P1-2).
- **Chat**: customer messaging surface exists but end-to-end chat is
  non-functional under current RLS (`conversation_participants`
  deny-by-default). **N1** defines the messaging access model; the remaining
  work is engineering implementation of the conversation RLS/API (N1-F),
  classified REQUIRES ENGINEERING DECISION (P1).

*End of implementation matrix. Every claim is evidence-based.*
