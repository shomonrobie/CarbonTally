# CarbonTally V3 — MASTER UI/UX ASCII DESIGNS

| | |
|---|---|
| Document type | Interaction design (authoritative ASCII) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE (UX phase) — represents ACTUAL interaction design |
| Date | 2026-08-24 |

These ASCII designs specify interaction, not decoration. Every screen includes
WHO / GOAL / VISIBLE DATA / EDITABLE DATA / ACTIONS / NEXT STATE / ERROR
STATE / PERMISSION STATE / EMPTY STATE / LOADING STATE / RELATED WORKFLOW.

Design rules binding on every screen:

- Top navigation rail only (D18) — no left sidebar inside workbenches.
- Source+structured-data workflows use TOP WORKFLOW NAV + SPLIT-SCREEN (D19).
- Status never by colour alone — text + icon + colour (D21.4).
- PE no-download boundary preserved (D6/D19).

---

# A. PUBLIC

## A1. Public landing

```
┌──────────────────────────────────────────────────────────────────────┐
│ 🌱 CarbonTally            [Platform][Services][Processing][Consultants]│
│                            [Pricing][About][Contact]   [Sign in]      │
│  PRE-LAUNCH · commercial launch by arrangement         [Request launch│
│                                                         information →]│
├──────────────────────────────────────────────────────────────────────┤
│  Turn messy carbon data into traceable emissions.                    │
│  [Request launch information]  [Explore the platform]                │
│                                                                      │
│  Source → Extract → Map → Calculate → Validate   (interactive demo)  │
│  Evidence chain: Source → Extracted line → Factor → Calculation →    │
│                  Emission result  (Complete/Partial/Unavailable)     │
│  Indicative pricing: Starter £49 · Professional £149 · Business £399 ·│
│                      Enterprise Custom (GBP, no online checkout)     │
└──────────────────────────────────────────────────────────────────────┘
WHO: anonymous visitor
GOAL: understand CarbonTally; start acquisition
VISIBLE: product claims, demo, evidence chain, indicative pricing
EDITABLE: nothing
ACTIONS: Request launch information → /contact; Explore → /platform;
         Sign in → /login
NEXT STATE: contact/signup/login
ERROR STATE: none (static)
PERMISSION STATE: public
EMPTY STATE: n/a
LOADING STATE: n/a
RELATED WORKFLOW: public acquisition (D13)
```

## A2. Login

```
┌──────────────────────────────────────────────┐
│ 🌱 CarbonTally                               │
│ Email        [you@company.com        ]       │
│ Password     [••••••••              ]       │
│            [Sign In]                        │
│            [Continue with Google]           │
│  New to CarbonTally? [Create Account]       │
└──────────────────────────────────────────────┘
WHO: any actor
GOAL: authenticate
VISIBLE: form
EDITABLE: email, password
ACTIONS: Sign In → role-aware home (/home, /ops, /consultant)
NEXT STATE: authenticated workspace
ERROR STATE: "Invalid email or password." (already implemented)
PERMISSION STATE: n/a
EMPTY/LOADING: n/a
RELATED WORKFLOW: auth
```

---

# B. ONBOARDING

## B1. Self-service onboarding

```
┌──────────────────────────────────────────────────────────────┐
│ Welcome to CarbonTally      step 1 of 3                       │
│ 1. Create or join an organisation                             │
│    [Company name ________________]  [Companies House number]  │
│    [Create organisation]                                      │
│ 2. Existing data? (optional)                                  │
│    We can check whether you already have data here.           │
│    [Look up existing data]  →  request → verify → choose      │
│ 3. How would you like to proceed?                             │
│    ( ) Self-service   ( ) Assisted   ( ) Managed              │
│    [Finish]                                                  │
└──────────────────────────────────────────────────────────────┘
WHO: new authenticated user with no org/staff/consultant link (D10/D35)
GOAL: become an org owner; avoid dead ends
VISIBLE: guided steps
EDITABLE: company details, choice
ACTIONS: create org → owner; discovery → verify; finish → /home
NEXT STATE: customer dashboard
ERROR STATE: duplicate company → blocked with acknowledgment
PERMISSION STATE: relationship-less users only
EMPTY STATE: n/a
LOADING: bounded guard (D35)
RELATED WORKFLOW: onboarding (D10/D35)
```

---

# C. CUSTOMER

## C1. Customer dashboard (Home)

```
┌──────────────────────────────────────────────────────────────────────┐
│ CarbonTally [Home][Emissions][Documents][Processing][Issues][Reports]│
│ [Messages][Existing data][Billing][Organization]  Org: Demo Ltd  [⏻] │
├──────────────────────────────────────────────────────────────────────┤
│ What needs your attention?                                           │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│ │ Reports   │ │ Documents │ │ Members   │ │ Emissions │             │
│ │ 3         │ │ 11        │ │ 4         │ │ 4         │             │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘             │
│ Emissions trend (chart)          Member activity                     │
│ 2 items need your review → [Review now]  (attention-driven)         │
└──────────────────────────────────────────────────────────────────────┘
WHO: org owner/admin/member/viewer
GOAL: see state at a glance; find what needs attention
VISIBLE: stat cards, trend, activity, attention items
EDITABLE: nothing
ACTIONS: navigate; review attention items
NEXT STATE: target screen
ERROR STATE: ErrorState with Retry (D29)
PERMISSION STATE: viewer sees read-only
EMPTY STATE: "No reports yet — upload a document to begin."
LOADING STATE: LoadingState (bounded 25s)
RELATED WORKFLOW: all
```

## C2. Customer Processing

```
┌────────────────────────────────────────────────────────────┐
│ Processing                                                │
│ Batches                                    [New batch]    │
│ ┌────────────────────────────────────────────────────────┐│
│ │ Fleet Diesel Cards Q1   · open · 7 items · entity: —  ││
│ │ [Items ▾]  [Assign…] (admin only)                     ││
│ └────────────────────────────────────────────────────────┘│
│ Item  Status            Stage    Evidence  Actions        │
│ 001   calculated        calc     ✓         [View]         │
│ 002   customer_review   review   ✓         [Review]       │
│ 003   pending           source   —         [—]            │
└────────────────────────────────────────────────────────────┘
WHO: O/A/M/V
GOAL: monitor processing; act on review-ready items
VISIBLE: batches, items, statuses
EDITABLE: batch creation (admin), item metadata
ACTIONS: New batch (O/A), View item, Review
NEXT STATE: item review/approve workbench
ERROR/EMPTY/LOADING: standard states
RELATED WORKFLOW: upload→…→approval
```

## C3. Customer Review & Approve workbench (TOP WORKFLOW NAV + SPLIT-SCREEN)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Queue][Extract][Map][Validate][Review ●][QC][Evidence]   batch:…    │
│                          ← prev · item 2/5 · next →                  │
├───────────────────────────────┬──────────────────────────────────────┤
│ SOURCE DOCUMENT               │ REVIEW & APPROVAL                    │
│  INV-2026-0417 (PDF, view-    │  Status: customer_review             │
│  only, no download)           │  Extracted fields        Conf.       │
│  [Pg 1/3] [-][+][zoom]        │   supplier  Meridian Fuel   ✓ 0.98   │
│  ┌─────────────────────────┐  │   date      06 Mar 2026    ✓ 0.97   │
│  │                         │  │   qty       4,258.9 L      ✓ 0.95   │
│  │  (secure PDF render)    │  │  Mapped activity: Gas oil (red      │
│  │                         │  │    diesel) · DEFRA 2026 · 2.52       │
│  └─────────────────────────┘  │  Calculation: 4,258.9 × 2.52 =       │
│  Pane presets: [40/60][50/50] │    10,732.4 kg CO₂e (snapshot #)     │
│                [60/40]        │  Evidence chain: [Complete ✓]        │
│                               │  [View source link][View factor]     │
│                               │  Reason (if rejecting) [_____]       │
│                               │  [✗ Reject]        [✓ Approve]      │
└───────────────────────────────┴──────────────────────────────────────┘
WHO: O/A (approve); M/V (review only, no approve control)
GOAL: verify the result against the source; approve or reject with reason
VISIBLE: source doc (secure view-only), extracted/mapped/calculated data,
         confidence, evidence chain, snapshot
EDITABLE: rejection reason; (approval is a decision, not a data edit)
ACTIONS: Approve / Reject (with reason) → item status; next item
NEXT STATE: approved → evidence/reporting; rejected → rework loop
ERROR STATE: network → ErrorState + Retry; invalid transition → 409 message
PERMISSION STATE: viewer sees read-only; member review-only; owner/admin approve
EMPTY STATE: "Nothing awaiting your review."
LOADING STATE: bounded spinner
MOBILE: top workflow nav becomes horizontal scroll; panes become trays
         (Source ⇄ Review toggle), approve/reject pinned
ACCESSIBILITY: keyboard nav; focus order source→fields→actions; status also
               as text, not colour alone
RELATED WORKFLOW: D2/D5 review→approval; D19 workbench
```

## C4. Organisation — master data (Facilities & Assets / Suppliers)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Organisation                                  Org: Demo Ltd           │
│ [Profile][Members][Facilities & Assets][Suppliers] (+target tabs:     │
│  Locations · Vehicles · Custom Factors · Activity · Settings)         │
├──────────────────────────────────────────────────────────────────────┤
│ Facilities & Assets (D17, org-scoped)                                 │
│ ┌──────────────────────┐ ┌──────────────────────┐                     │
│ │ Facilities (3)       │ │ Assets (4)           │                     │
│ │ [New facility][…]    │ │ [New asset][…]       │                     │
│ │ Name · type · status │ │ Name · type · fac.   │                     │
│ │ ▸ Archive/deactivate │ │ ▸ Archive/deactivate │                     │
│ │   (restore where     │ │   (restore)          │                     │
│ │   supported)         │ │ ▸ Related docs/      │                     │
│ │ ▸ Related documents/ │ │   activity/emissions │                     │
│ │   activity/emissions │ │                      │                     │
│ └──────────────────────┘ └──────────────────────┘                     │
│ Suppliers (3): [New supplier] · list · status · related evidence      │
│ [Locations] [Vehicles] → target tabs (Vehicles gap P1-2;              │
│  Locations: N2 engineering decision — table or Facilities reuse)      │
└──────────────────────────────────────────────────────────────────────┘
WHO: org Owner/Admin (mutate); Member/Viewer (read-only)
GOAL: maintain organisation master data; see related activity/emissions
VISIBLE: facilities, assets, suppliers (and target: locations, vehicles)
EDITABLE: name/type/status fields (O/A)
ACTIONS: create, edit, archive/deactivate, restore, search/filter, view
         related documents/activity/emissions/evidence/reports
NEXT STATE: saved master-data record; related surfaces linkable
ERROR STATE: validation errors inline; duplicate name warning
PERMISSION STATE: O/A mutate; M/V read-only
EMPTY STATE: "No facilities yet. Add your first facility or skip for now."
LOADING STATE: bounded
RELATED WORKFLOW: D17 lifecycle; secondary to processing (D18)
```

## C5. Messaging (N1)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Messages (N1 access model — enforced by RLS/API, not the UI)         │
│                                                                      │
│ WHO CAN MESSAGE WHOM (target)                                        │
│  Customer org user    ⇄  own org users (org-scoped)                  │
│  Customer org user    ⇄  CarbonTally Customer Support / Admin        │
│                         (authorised support scope)                   │
│  Consultant user      ⇄  own firm users; CarbonTally Support/Admin;  │
│                         authorised customers WITHIN active client    │
│  Support/Admin        ⇄  customers + consultants (authorised scope)  │
│  PE Manager           ⇄  authorised PE users; CarbonTally personnel  │
│                         (operational workflow)                       │
│  Customer ⇄ PE        ✗  NO DIRECT MESSAGING — use the controlled    │
│                         processing/clarification workflow            │
│                                                                      │
│ Conversation list │ thread │ composer │ participants                 │
│ (scope-filtered)  │ (audit) │          │ (role-gated)                │
└──────────────────────────────────────────────────────────────────────┘
WHO: per N1 (org member, consultant, support/admin, PE manager)
GOAL: scoped communication; clarification via controlled workflow
VISIBLE: conversations the caller's identity/role/org/active-client/PE
         assignment permits (N1-F)
EDITABLE: compose/reply within permitted conversations
ACTIONS: start conversation (permitted pairings only), reply, view
         participants, (support/admin) scoped support threads
NEXT STATE: message persisted; audit logged; notifications per user
ERROR STATE: 403 on non-permitted pairing; no conversation options shown
PERMISSION STATE: UI never the boundary — RLS/API enforce N1-F
EMPTY STATE: "No conversations yet" (scope-appropriate)
LOADING STATE: bounded
RELATED WORKFLOW: D18 Messaging nav; N1; clarification workflow §4;
                  G-P1-1
```

---

# D. CONSULTANT

## D1. Consultant workspace

```
┌──────────────────────────────────────────────────────────────────────┐
│ CarbonTally [Home]…[Consultant ●][Operations][Notifications]         │
│   badge: Consultant · firm: Net Zero Advisory                        │
│  Active client: [Demo Ltd ▾ switch]  (always explicit — D3/D8)       │
├──────────────────────────────────────────────────────────────────────┤
│ [Dashboard][Client workspace][Branding][White-label][Messaging]      │
│ Clients: 1 active · Pending reviews · Open issues · Ready reports    │
│ ┌──────────────────────────┐ ┌──────────────────────────┐            │
│ │ Client workspace         │ │ Reports (brand context)  │            │
│ │ dashboard/processing/    │ │ [Download]               │            │
│ │ issues/documents         │ │                          │            │
│ └──────────────────────────┘ └──────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────┘
WHO: consultant firm member (grant-gated)
GOAL: manage multiple clients with explicit context
VISIBLE: active client banner, client data, reports
EDITABLE: per can_* flags (upload, generate reports, manage clients/team)
ACTIONS: switch client, open workspace, branding, messaging
NEXT STATE: selected surface
ERROR STATE: client revoked → 403 with message
PERMISSION STATE: grant must be ACTIVE (D15)
EMPTY STATE: "No clients yet."
RELATED WORKFLOW: D3/D8/D14/D21
```

---

# E. INTERNAL OPERATIONS (CarbonTally staff)

## E1. Ops hub

```
┌──────────────────────────────────────────────────────────────────────┐
│ Internal Operations  (staff badge)                                   │
│ [Dashboard][Data entry][Review][QC][Staff][Roles][Entities][SLA]     │
│ [Commercial]                                                         │
│  Queue: 5 pending · 3 review · 1 QC · 8 entities                    │
│  [Assign…]  [Reassign…]  (can_manage_staff)                          │
└──────────────────────────────────────────────────────────────────────┘
WHO: internal staff (entity_id NULL)
GOAL: run the operational pipeline
VISIBLE: queue aggregates, pipeline, staff, entities
EDITABLE: per permission
ACTIONS: tab navigation; assign; open workspace
NEXT STATE: workbench
ERROR/EMPTY/LOADING: standard
RELATED WORKFLOW: D18 ops prioritisation
```

## E2. Data-entry / extraction workbench (TOP WORKFLOW NAV + SPLIT-SCREEN)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Queue ●][Extract][Map][Validate][Review][QC][Evidence]   batch:…    │
│  ← prev · item 3/7 · next →  status: extracted                       │
├───────────────────────────────┬──────────────────────────────────────┤
│ SOURCE DOCUMENT               │ STRUCTURED DATA                      │
│  invoice.pdf (view-only)      │  Header:                            │
│  [Pg 1/2] [−][+][zoom][fit]   │   Supplier    [Meridian Fuel    ]    │
│  ┌─────────────────────────┐  │   Invoice #   [INV-2026-0417   ]    │
│  │  (secure PDF render,    │  │   Date        [06/03/2026      ]    │
│  │   sandboxed iframe,     │  │   Currency    [GBP             ]    │
│  │   no download button)   │  │  Line items (autosave ✓)           │
│  │                         │  │  Desc | Activity | Qty | Unit | Amt │
│  └─────────────────────────┘  │  [Red diesel | Natural gas|4258.9|L]│
│                               │  Factor: [Gas oil (red diesel) ▾]   │
│                               │  Confidence: 0.95 [edit]             │
│                               │  Source↔field links: [highlight]    │
│  Pane presets: [40/60][50/50] │  [Save draft][Save extraction]      │
│                [60/40]        │  [Map][Calculate]                    │
└───────────────────────────────┴──────────────────────────────────────┘
WHO: operator (can_process); reviewer/QC layer extra controls
GOAL: extract + map + calculate with source visible
VISIBLE: source doc, extracted data, factors, confidence
EDITABLE: all structured fields
ACTIONS: claim stage, save draft/extraction, map, calculate, next item
NEXT STATE: extracted→mapped→calculated
ERROR STATE: 422 (unit mismatch / no factor) with inline field errors
PERMISSION STATE: operator extract; reviewer validate; QC on extracted
EMPTY STATE: "No items assigned."
LOADING STATE: bounded
KEYBOARD: full keyboard entry (Tab through fields, Ctrl+S save)
ACCESSIBILITY: focus order; form labels; status text+icon
MOBILE: trays (Source ⇄ Data), not a squeezed split
RELATED WORKFLOW: D19/D20/D23; PE no-download preserved
```

## E3. Review / QC workbench

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Queue][Extract][Map][Validate][Review ●][QC][Evidence]              │
├───────────────────────────────┬──────────────────────────────────────┤
│ SOURCE DOCUMENT               │ REVIEW / QC                          │
│  (view-only)                  │  Validation A1–A9: 3 pass, 0 fail    │
│                               │  QC checklist: [x] headers [x] lines │
│                               │  [x] factor [x] calc [x] evidence    │
│                               │  Notes [________________]            │
│                               │  [✗ Reject]  [✓ QC Approve]         │
└───────────────────────────────┴──────────────────────────────────────┘
WHO: reviewer/QC (can_review); QC admin surface separately
GOAL: validate and QC the extraction before calculation/approval
ACTIONS: validate, QC approve/reject, comment
NEXT STATE: qc_approved / qc_rejected (rework)
RELATED WORKFLOW: D6 quality chain
```

---

# F. PROCESSING ENTITY

## F1. Entity extraction workspace

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Assigned work ●][Extract][Map][Calculate][Clarify]   Entity: A      │
│  (entity-scoped — only work assigned to this entity)                 │
├───────────────────────────────┬──────────────────────────────────────┤
│ SOURCE DOCUMENT               │ STRUCTURED DATA (same panel contract)│
│  (view-only, NO download)     │  Header + lines + factor picker      │
│                               │  [Save draft][Save extraction][Calc] │
│                               │  Clarification (mediated):           │
│                               │  [Ask CarbonTally…] → issue          │
└───────────────────────────────┴──────────────────────────────────────┘
WHO: entity staff (entity_id set)
GOAL: process only assigned work; never customer access
VISIBLE: assigned batches/items, source, data
EDITABLE: extraction fields
ACTIONS: claim, extract, map, calculate, clarify (mediated)
NEXT STATE: calculated → CarbonTally mediates handoff
ERROR STATE: cross-entity access denied (403); lifecycle non-active denied
PERMISSION STATE: entity-scoped; no customer/consultant/report/billing access
EMPTY STATE: "No work assigned to your entity."
RELATED WORKFLOW: D6/D19/D22
```

---

# G. CARBONTALLY ADMIN (control plane)

## G1. Admin commercial / control-plane

```
┌──────────────────────────────────────────────────────────────────────┐
│ Commercial (dense)                                                   │
│ [Plans][Modes][Price book][Credit ledger][Orders][Storage][Config]   │
│ Plan  Version  Price      Mode     Entitlements                     │
│ Starter 1      £49/mo     CREDIT   100 credits, 20 GB               │
│ …                                                                    │
│ Order # | Org | Type | Amount | Status | Action                      │
│ …                                                                    │
└──────────────────────────────────────────────────────────────────────┘
WHO: staff with can_manage_billing
GOAL: configure and monitor the commercial model
VISIBLE: plans, modes, price book, ledger, orders
EDITABLE: config (server-authoritative)
ACTIONS: activate/renew subscriptions, adjust ledger (audited)
NEXT STATE: persisted config
ERROR/EMPTY/LOADING: standard
RELATED WORKFLOW: D11/D12/D37
```

---

# H. CROSS-CUTTING STATES

## H1. Notifications

```
┌──────────────────────────────────────────┐
│ Notifications                            │
│ ● 2 action-required · 1 informational    │
│ [Action: item awaits your approval] → /processing  (lands on the item)
│ [Info: report ready] → /reports          │
│ EMPTY: "You are all caught up."          │
└──────────────────────────────────────────┘
WHO: all roles
GOAL: surface action-required and informational items
ACTIONS: select → navigate to the relevant item
NEXT STATE: target screen
```

## H2. Error / empty / loading / permission states

- **Error**: `ErrorState` with message + Retry (bounded 25s; D29).
- **Empty**: one clear variant per surface ("No reports yet — upload a
  document to begin.").
- **Loading**: `LoadingState` spinner; never infinite.
- **Permission**: denied controls hidden for viewers; denied routes show a
  clear 403 message; entity staff never see customer surfaces.

*End of ASCII designs. These are interaction specifications, not decoration.*
