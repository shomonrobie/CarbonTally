# CarbonTally V3 — MASTER SCREEN INVENTORY

| | |
|---|---|
| Document type | Screen inventory (authoritative) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE (UX phase) — implementation status per screen |
| Date | 2026-08-24 |

Implementation-status labels: IMPLEMENTED · PARTIALLY IMPLEMENTED · BACKEND
READY / UI MISSING · UI READY / BACKEND MISSING · DESIGN ONLY · PLANNED ·
BLOCKED · REQUIRES ENGINEERING DECISION.

Legend — roles: **O** = org owner · **A** = org admin · **M** = org member ·
**V** = org viewer · **C** = consultant · **S** = staff (internal) ·
**E** = Processing Entity staff · **ADM** = CarbonTally admin.

---

## 1. Public website

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Landing | `/` | Public | IMPLEMENTED | Pre-launch badge, "Request launch information", indicative GBP pricing, evidence demo, service ecosystem. Live app ahead of committed baseline. |
| Platform overview | `/platform` | Public | LIVE ONLY (uncommitted) | Not in committed baseline (`frontend/src/public/PlatformPage.jsx` exists only in the running workspace). |
| Services | `/services` | Public | LIVE ONLY (uncommitted) | — |
| Processing services | `/processing-services` | Public | LIVE ONLY (uncommitted) | — |
| Consultants | `/consultants` | Public | LIVE ONLY (uncommitted) | — |
| Pricing | `/pricing` | Public | LIVE ONLY (uncommitted; committed App.js maps `/privacy`→PricingPage bug) | GBP indicative plans + credit model. |
| About | `/about` | Public | IMPLEMENTED | — |
| Contact | `/contact` | Public | LIVE ONLY (uncommitted) | "Request launch information". |
| Glossary | `/glossary` | Public | IMPLEMENTED | `Glossary.jsx` (static data). |
| Privacy / Cookies / Terms | `/privacy` `/cookies` `/terms` | Public | IMPLEMENTED | — |
| Sign in | `/login` | Public | IMPLEMENTED | Email+password + Google. Post-login redirect target: V3 `/home` (D28 F5 fixed). |
| Self-service signup | `/signup` | Public | IMPLEMENTED (D35) | No beta gate. |
| Beta signup (optional) | `/beta/signup` | Public (admin cohort) | IMPLEMENTED | Controlled-cohort path. |

## 2. Auth / onboarding

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Auth callback | `/auth/callback` | All | IMPLEMENTED | Supabase magic/SSO callback. |
| Magic link | `/auth/magic` | Public | IMPLEMENTED | — |
| Onboarding | `/onboarding` | New customer | IMPLEMENTED (D35) | Self-service: create/adopt org, existing-data discovery, choice of proceed. Relationship-less users land here (no dead end, D10). |

## 3. Customer workspace (org roles)

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Customer dashboard | `/home` | O/A/M/V | IMPLEMENTED | Stat cards (reports, documents, members, emissions), emissions trend chart, member activity. "What needs my attention" is target polish. |
| Emissions | `/emissions` | O/A/M/V | IMPLEMENTED | Scope breakdown, calculations, exports. |
| Documents | `/documents` | O/A/M/V | IMPLEMENTED | List 11 demo docs; upload; private storage (D32). |
| Processing | `/processing` | O/A/M/V | IMPLEMENTED | Batches + items over `/api/v3/manual-extraction`. |
| Existing data discovery | `/existing-data` | O/A/M/V | IMPLEMENTED (D27/D19) | Lookup → request → verify → USE ALL/PARTIAL/DISCARD. |
| Issues | `/issues` | O/A/M/V | IMPLEMENTED | Customer-facing issues (entity issues excluded). |
| Messaging | `/messaging` | O/A/M/V | IMPLEMENTED (surface) | Conversations UI; direct chat non-functional end-to-end (`conversation_participants` deny-by-default) — **N1 approved** defines the access model; engineering implements N1-F (RLS/API). |
| Notifications | `/notifications` | O/A/M/V | IMPLEMENTED | Per-user; empty state (D28 F8 fixed to one variant). |
| Reports | `/reports` | O/A/M/V | IMPLEMENTED | Report list, statuses, branding context. |
| Report detail | `/reports/:id` | O/A/M/V | IMPLEMENTED | Content + versions + evidence. |
| Billing | `/billing` | O/A/M/V | IMPLEMENTED (D37) | Plan, mode, credits, orders; no live payment provider. |
| Organisation (admin) | `/organization` | O/A (mutations); M/V read | IMPLEMENTED | Tabs: Profile, Members, Suppliers, Facilities & Assets, Security. |
| Organisation — Members | `/organization` (tab) | O/A manage; M/V view | IMPLEMENTED | Invitations + roles. |
| Organisation — Facilities & Assets | `/organization` (tab) | O/A manage; M/V view | IMPLEMENTED | Facilities (3 demo), assets (4 demo). |
| Organisation — Suppliers | `/organization` (tab) | O/A manage; M/V view | IMPLEMENTED | Suppliers (3 demo). |
| Organisation — Custom Factors | target `/organization` (tab) | O/A approve; M propose | **BACKEND READY / UI MISSING** | `customer_factors` API + RLS; no V3 UI tab. |
| Organisation — Vehicles | target | O/A manage | **DESIGN ONLY** | No table, no API, no UI (gap G-P1-2). |
| Organisation — Locations | target | O/A manage | **DESIGN ONLY** | `facilities` doubles as facilities/locations today; **N2**: dedicated Locations table OR Facilities reuse is an engineering decision. |
| Organisation — Activity | target | O/A/M/V | **DESIGN ONLY** | Activity feed exists as legacy component; V3 surface target. |
| Organisation — Settings | target | O/A | **DESIGN ONLY** | Retention/settings target (D15); **N3**: configurable retention surface (no invented durations). |

## 4. Consultant workspace

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Consultant dashboard | `/consultant` (view=dashboard) | C | IMPLEMENTED | Firm stats, clients by status, pending reviews, open issues, ready reports. |
| Client workspace | `/consultant` (view=workspace) | C (grant-gated) | IMPLEMENTED | Active client context, dashboard/reports/processing/issues/documents. |
| Client messaging | `/consultant` (view=messaging) | C | IMPLEMENTED (surface) | Same chat limitation as customer messaging; **N1-B**: consultant messages scoped to active-client relationship (no cross-client). |
| Branding | `/consultant` (view=branding) | C (owner/manager) | IMPLEMENTED (D21) | Brand name/context; server-authoritative. |
| White-label | `/consultant` (view=whitelabel) | C | IMPLEMENTED (foundation) | `white_label_enabled`; full rendering future. |

## 5. Internal operations (CarbonTally staff)

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Ops dashboard | `/ops` (tab) | S (can_view_all) | IMPLEMENTED | Scope, organisations, entities, staff, pipeline, review queue. |
| Data entry queue | `/ops` (tab) | S (can_process) | IMPLEMENTED | Operator queue (`/queues/operator`), batches + items. |
| Review queue | `/ops` (tab) | S (can_review) | IMPLEMENTED | Review items (3 demo). |
| QC queue | `/ops` (tab) | S (can_review) | IMPLEMENTED | QC items (1 demo). |
| Staff roster | `/ops` (tab) | S (can_view_all/manage_staff) | IMPLEMENTED | Staff profiles CRUD. |
| Roles | `/ops` (tab) | S (can_manage_roles) | IMPLEMENTED | Staff roles catalog. |
| Entities | `/ops` (tab) | S (can_manage_staff) | IMPLEMENTED (D22/D24) | Processing Entities list/create; batch assign control. |
| SLA | `/ops` (tab) | S (can_manage_staff) | IMPLEMENTED | SLA settings. |
| Commercial | `/ops` (tab) | S (can_manage_billing) | IMPLEMENTED (D37) | Plans, modes, price book, credit ledger, orders. |
| Work item workspace | `/ops` (in queue) | S (per permission) | IMPLEMENTED | Split-screen source+data; role-layered actions. |
| Extraction panel | `/ops` (in queue) | S operator | IMPLEMENTED (D23) | Doc viewer + multi-line extraction + mapping. |

## 6. Processing Entity workspace

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Entity extraction workspace | `/ops` (renders for entity staff) | E | IMPLEMENTED (D22/D24) | Entity-scoped batches/items, extraction/mapping/calculation, mediated clarification. |
| Entity dashboard | `/ops/entities/{id}/dashboard` | E (own) / ADM | IMPLEMENTED | — |

## 7. CarbonTally admin / control plane

| Screen | Route | Roles | Status | Notes |
|---|---|---|---|---|
| Admin audit | target | ADM | PARTIALLY IMPLEMENTED | Audit endpoints exist; consolidated admin audit console target. |
| Platform admin console | target | ADM | **DESIGN ONLY** | Option A control-plane target (D18). |

## 8. Notable UX issues (live/documented)

| # | Route | Issue | Classification |
|---|---|---|---|
| U1 | `/login` | Legacy post-login redirect (D28 F5) — fixed per D29 in baseline; verify live | DOCUMENTATION MATCHES / VERIFIED |
| U2 | `/messaging` | Chat non-functional end-to-end (`conversation_participants` deny-by-default, 0 policies) | IMPLEMENTATION GAP vs D18/N1 → engineering implements N1-F (conversation RLS/API); N1 access model approved |
| U3 | `/pricing` (committed) | `/privacy` route duplicated to PricingPage (bug in committed baseline); `/pricing` missing | IMPLEMENTATION AHEAD OF DOCUMENTATION (live) / committed baseline behind |
| U4 | `/consultant` client list | Raw org UUID shown (D28 F10) | DOCUMENTATION AHEAD OF IMPLEMENTATION (fix target) |
| U5 | Workbench | No explicit top workflow nav bar; no pane presets; confidence indicators not yet surfaced | DOCUMENTATION AHEAD OF IMPLEMENTATION (D19 target) |
| U6 | Master data | Vehicles + distinct Locations missing end-to-end | IMPLEMENTATION GAP (D17); N2 resolved the Locations product direction — engineering decides dedicated table vs Facilities reuse |
| U7 | Design tokens | Two green primaries across `v3.css`/`App.css` | UX INCONSISTENCY (D21) |
| U8 | Custom factors | Backend ready; no UI | IMPLEMENTATION GAP (D9) |

*End of screen inventory. Documentation-only.*
