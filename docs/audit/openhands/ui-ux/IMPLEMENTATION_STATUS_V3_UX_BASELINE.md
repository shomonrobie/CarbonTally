# CarbonTally V3 — UX BASELINE IMPLEMENTATION STATUS

| | |
|---|---|
| Document type | Implementation status record (TARGET / CURRENT / REASON / REMAINING GAP) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | TRACKING DOCUMENT — the frozen UX specification (`docs/audit/openhands/ui-ux/`) remains the target authority; this record reconciles implementation against it (spec §18) |
| Date | 2026-08-27 |

This document is not a rewrite of the frozen UX specification. It records, for
each major capability, the TARGET (frozen), the CURRENT implementation state
(after this baseline), the REASON for any temporary difference, and the
REMAINING GAP. Implementation-status labels follow the canonical vocabulary
(IMPLEMENTED · PARTIALLY IMPLEMENTED · BACKEND READY / UI MISSING · UI READY /
BACKEND MISSING · DESIGN ONLY · PLANNED · BLOCKED · REQUIRES ENGINEERING
DECISION).

---

## 1. Phase 1 — UX foundation

| Capability | TARGET | CURRENT | Status |
|---|---|---|---|
| D21 unified design tokens | One `ct-*` token vocabulary; consolidate dual-green (#2f855a / #2d6a4f) | `frontend/src/v3/tokens.css` defines the `ct-*` layer; `v3.css` aliases it; `App.css` `--primary` unified on `#2f855a` | IMPLEMENTED |
| Typography / spacing / radii / shadows | Codified from existing v3.css evidence | `tokens.css` (`--ct-type-*`, `--ct-space-*`, `--ct-radius-*`, `--ct-shadow-*`) | IMPLEMENTED |
| UI primitives | Buttons, forms, tables, cards, badges, status indicators, alerts, dialogs, drawers, tabs, states | `frontend/src/v3/components/ui/*` (Button, FormControls, DataTable, Card, Badge, StatusBadge, statusConfig, Alert, Dialog/ConfirmationDialog, Drawer, Tabs, StateViews, Icon, hooks) | IMPLEMENTED |
| Status system (D21.4) | label + icon + colour, never colour alone | `statusConfig.js` maps the authoritative backend vocabulary (ITEM/BATCH/ISSUE/REPORT/ENTITY statuses) | IMPLEMENTED |
| App shell (D18) | Top workflow navigation, role-aware, org context, tablet tray | `V3Layout.jsx`: customer nav Home/Documents/Processing/Review/Emissions/Reports/Issues/Billing/Organisation/Messaging/Existing data; staff/consultant/notifications; hamburger + left drawer on ≤900px | IMPLEMENTED |
| Workbench shell (D19) | Top workflow nav + split panes + 40/60·50/50·60/40 + secure viewer + confidence + autosave + lock; no left sidebar | `frontend/src/v3/components/workbench/*`: WorkbenchShell, WorkflowNav, SplitPane, SecureDocumentViewer, ConfidenceBadge, AutosaveIndicator; `WorkItemWorkspace` retrofitted onto it | IMPLEMENTED |
| Responsive (D20) | Desktop-first; tablet tray; mobile monitor | `useMediaQuery`/`useIsTablet`/`useIsMobile` hooks; workbench tray flow ≤900px; nav drawer ≤900px | IMPLEMENTED |
| Accessibility | WCAG 2.2 AA targets; focus-visible; semantic landmarks; live regions | focus-visible ring token, aria-live states, focus-trapped dialogs/drawers, `role="alert"` errors, scoped table headers, reduced-motion support | PARTIALLY IMPLEMENTED (full audit outstanding) |

## 2. Phase 2 — Customer + Consultant

| Capability | TARGET | CURRENT | Status |
|---|---|---|---|
| Customer Review & Approve UI (G-P0-2, D2/D5) | Evidence-first review; distinct approver gate; Approve/Reject with reason; audit | `/review` (queue) + `/review/:itemId` (D19 workbench, evidence panel, Approve/Reject with reason). Backend `customer-review` now requires org OWNER/ADMIN (`require_org_admin`, D5) | IMPLEMENTED |
| Custom Factors UI (G-P0-3, D9) | Org-scoped lifecycle surface: draft/create/approve/deactivate, precedence note | `/organization` → Custom Factors tab (create draft, edit draft, approve admin-only no-self-approval, deactivate) over the existing `/api/v3/customer-factors` | IMPLEMENTED |
| Master data — Facilities/Assets/Suppliers (D17) | First-class, org-scoped, never blocks processing | Existing tables/APIs/tabs (pre-existing) | IMPLEMENTED (pre-existing) |
| Master data — Locations (D17/N2) | First-class Locations concept; physical representation is an engineering decision | **Engineering decision:** reuse the `facilities` entity (it already carries full address fields + `type` discriminator) — NO separate `locations` table. `/organization` → Locations tab presents the facility-as-location hierarchy with type filtering | IMPLEMENTED (reuse per N2) |
| Master data — Vehicles (D17/G-P1-2) | Org-scoped fleet master data | New `vehicles` table + RLS (migration `20260825000000_v3m7_vehicles.sql`), `/api/v3/vehicles` API, `/organization` → Vehicles tab | IMPLEMENTED |
| Messaging (N1) | Customer-org internal; consultant internal + active-client; scoped support; NO direct Customer↔PE chat | Server-enforced via `_authorize_org_actor` (org member matching own org OR active-grant consultant; PE denied 403) + conversation RLS (d27 migration). Customer `/messaging` + consultant client messaging surfaces pre-existing | PARTIALLY IMPLEMENTED — N1 boundary enforced; staff/PE-manager messaging surfaces not yet exposed in UI |
| Retention (N3) | Configurable retention policy; Settings/Admin surface; server-side enforcement; no invented values | `system_settings` retention columns; `/api/v3/settings/retention` (staff admin GET/PUT); ops → Settings tab renders configured values / "Not configured" | IMPLEMENTED (configuration surface) — server-side enforcement jobs remain a separate engineering concern |

## 3. Phase 3 — PE + Staff + Admin

| Capability | TARGET | CURRENT | Status |
|---|---|---|---|
| PE workspace | Assigned-work extraction/mapping/calculation, mediated clarification, no-download | Pre-existing `EntityExtractionWorkspace` (D22); no-download boundary preserved (signed URLs, view-only); PE denied from customer/consultant/messaging surfaces | IMPLEMENTED (pre-existing) |
| Staff operations | Queue/review/QC/staff/roles/entities/SLA/commercial + retention settings | Pre-existing ops tabs + new Settings (retention) tab | IMPLEMENTED (with N3 addition) |
| Admin control plane | Dense enterprise admin console: users/roles/orgs/PEs/consultants/billing/factors/system settings/audit | Pre-existing Commercial/SLA/Entities/SLA staff-admin tabs; `/api/v3/admin/audit*` endpoints exist; consolidated admin console + audit console remain target | PARTIALLY IMPLEMENTED |

## 4. Security invariants

| Invariant | Verification |
|---|---|
| RLS org isolation | Unchanged; all new surfaces (vehicles, retention) use deny-by-default RLS / staff-admin-only API |
| D5 approver authority | `customer-review` now org-owner/admin only (`require_org_admin`); unit-tested |
| PE no-download | Preserved (signed URLs; `SecureDocumentViewer` renders no download affordance for PE); server boundary unchanged |
| Server-authoritative calculation | Unchanged; review UI never computes |
| UI is not the security boundary | All new UI actions post to server endpoints; frontend role flags are display-only |
| Messaging (N1) | PE denied messaging; org-scoped actor authorization + RLS |



## 5. Phase 3 — completed this session

| Capability | TARGET | CURRENT | Status |
|---|---|---|---|
| PE workspace (D19) | PE workbench with top workflow nav, presets, secure viewer, no-download | `ExtractionPanel` (used by PE + staff) now renders inside the D19 `WorkbenchShell` with PE stage set, pane presets, autosave indicator and secure view-only source (`allowDownload=false`) | IMPLEMENTED |
| Staff workbench | Same D19 contract for internal operators | `ExtractionPanel mode="staff"` uses the staff stage set (Extract→Map→Validate→Review→QC→Evidence); `WorkItemWorkspace` already on the shell | IMPLEMENTED |
| Ops issues-triage UX (G-P0-4) | First-class triage queue: assign/prioritise/escalate/resolve | New `IssuesTriageTab` over `/api/v3/issues/admin/open` + `PUT /api/v3/issues/{id}` with domain-transition validation; status/priority/reopen/resolve actions | IMPLEMENTED |
| Admin audit console | Read-side audit with filters + pagination | New `AuditConsoleTab` over `/api/v3/ops/reporting/audit` (staff admin, can_manage_staff) | IMPLEMENTED |
| Staff messaging (N1) | CarbonTally Support/Authorised Admin may message authorised customers/consultants | Backend `_authorize_org_actor` now allows INTERNAL staff with `can_manage_staff` (participant role `staff`); new `OpsMessagingTab`; general employees and PE staff still denied (unit-tested) | IMPLEMENTED |
| Universal evidence trail (G-P0-5) | Evidence chain visible on every number | New `EvidenceTrail` component (D33 record or explicit steps; never implies independent certification); wired into Report detail | IMPLEMENTED |
| Search (G-P1-1) | Nav search box, org-scoped results | New `/api/v3/search` backend (documents/items/issues/suppliers/facilities/vehicles/reports, org-scoped) + `SearchBox` in the V3 nav | IMPLEMENTED |
| Organisation Activity (R2) | Org-scoped member activity | New `ActivityTab` over `/api/v3/reporting/member-activity` (uploads, batches, issues, emissions rows per member) | IMPLEMENTED |
| Retention enforcement (N3) | Server-side enforcement of configured policy | New `services/retention.py` + `tools/enforce_retention.py` CLI (dry-run by default). Only configured durations are enforced; audit/evidence tables explicitly excluded (security invariant); documents soft-expire via `deleted_at` | IMPLEMENTED (scheduler invocation is deployment) |
| Vehicles migration application | Apply + verify migration | `20260825000000_v3m7_vehicles.sql` applied to the local app DB and verified (table, 4 org-scoped policies, RLS enabled, `is_org_member`/`is_org_consultant` helpers present) | VERIFIED |

## 6. Phase 4 — reconciliation summary

Reconciled against `MASTER_SCREEN_INVENTORY.md`, `MASTER_WORKFLOW_MAP.md`,
`MASTER_UI_UX_ASCII_DESIGNS.md`, `UI_UX_IMPLEMENTATION_MATRIX.md`,
`CARBONTALLY_V3_DESIGN_SYSTEM.md`, the Decision Register and the AI Assistant
architecture:

- **Screens**: every previously "BACKEND READY / UI MISSING" or "UI MISSING"
  P0 row now has an implementation: Customer Review & Approve (G-P0-2), Custom
  Factors (G-P0-3), extraction workbench (G-P0-1 partial → D19 shell), Issues
  triage (G-P0-4), evidence trail (G-P0-5), Vehicles + Locations (D17),
  retention settings + enforcement (N3), search (G-P1-1), admin audit console.
- **Workflows**: the canonical pipeline upload→…→customer approval→reporting
  is now UI-complete end-to-end. Approve is still a distinct, server-gated
  gate (never "calculated"="approved").
- **Design system (D21)**: all new surfaces consume the `ct-*` tokens and the
  shared primitives; no competing visual language.
- **AI Assistant**: no new assistant capability was added; the public /
  role-scoped / normal-workflow layering and the "no direct DB access / no
  permission escalation" rules are preserved (the authenticated assistant
  remains a documented future programme item).
- **201-screen inventory**: shared components (ui/, workbench/, EvidenceTrail,
  SearchBox, StateViews) satisfy multiple inventory rows; no screen was built
  to "look functional" without a backend.

## 7. Known remaining gaps

- **App.test.js** fails in jest (`react-router/dom` resolution) — pre-existing committed-baseline issue, not introduced by this work.
- **Full CI build** (`CI=true npm run build`) fails on ~30 pre-existing unused-import warnings in `App.js`/legacy components — not introduced by this work; `npm run build` succeeds.
- **PE internal messaging** (PE-manager ↔ PE users) is not implemented: the conversation model is org-scoped and PE staff are structurally denied messaging. Implementing entity-scoped conversations is a data-model change beyond the existing architecture — documented, not fabricated.
- **Authenticated AI assistant** remains a programme decision (provider + tool-call architecture) — no credentials were invented.
- **Retention enforcement scheduling** (cron/scheduler wiring) is a deployment step; the enforcement command is ready (`python -m tools.enforce_retention [--apply]`).
- Integration/RLS suites require the dedicated `carbontally_test` DB; the vehicles migration has been applied and verified against the local app DB.

## 8. Tests

- Frontend: `frontend/src/v3/__tests__/` — **109 tests pass** (6 suites, incl. new `evidence-trail`).
- Backend: full `tests/unit` suite **passes** (exit 0; ~1108 tests incl. new `test_v3_search`, `test_retention`, N1 messaging gate tests in `test_v3_messaging`, D5 tests in `test_scope_aware_authorization`).
- Vehicles migration: applied + verified against the local app database.

*End of implementation status record.*

