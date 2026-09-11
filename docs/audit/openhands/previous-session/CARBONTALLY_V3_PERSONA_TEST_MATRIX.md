# CarbonTally V3 — Persona Test Matrix

**Date:** 2026-08-28 · **Baseline:** `c36c848` (main) · **Environment:** local/dev (`localhost:3000/8050`, Supabase demo auth, Postgres 54426)

Statuses: ✅ = VERIFIED WORKING · ⚠️ = PARTIALLY WORKING · ❌ = BROKEN · ➖ = NOT IMPLEMENTED · ❓ = NOT TESTABLE · ⏸ = PO DECISION REQUIRED / ENVIRONMENT BLOCKED

Finding IDs refer to the Master Acceptance Audit and the Cline Backlog (CL-xx).

| Persona | Workflow | Expected | Actual | Status | Finding ID |
|---|---|---|---|---|---|
| **Customer Owner** | Login + workspace routing | Lands on customer shell | `/` V3 customer shell | ✅ | AUTH-1 |
| | Org profile edit + persistence | Saves and persists after reload | PUT `/organizations/{id}/profile` 200; GET reflects change after reload | ✅ | CUS-8 |
| | Facility create (with postcode) | 201 | 201 | ✅ | MD-1a |
| | Facility create (no postcode) | 201 (optional field) | 500 DB CHECK violation | ❌ | MD-1 / CL-08 |
| | Facility list / detail | Readable | 200 | ✅ | MD-4 |
| | Locations (N2) | Locations view lists facilities | Locations tab shows facilities with N2 explanation | ✅ | MD-3 |
| | Asset create (with type) | 201, type persists | 201; type column persists | ✅ | MD-4 |
| | Asset type display | Shows type | Existing seeded assets show "—" (null type); form has Type field | ⚠️ | MD-4 |
| | Vehicle create | 201 | 500 `relation "public.vehicles" does not exist` | ❌ | MD-2 / CL-04 |
| | Supplier create/edit | 201/200 | 201 create, 200 update + UI dialog | ✅ | MD-5 |
| | Members list / role change | Manage members | List 200; role change round-trip verified | ✅ | CUS-9 |
| | Invite member | 201 | 201; list 200 | ✅ | CUS-9 |
| | Document upload | 201 | 201 + storage object | ✅ | DOC-1 |
| | Documents page (emissions outcome) | Business-workflow view | File-browser orientation + per-doc "Emissions from this document" | ⚠️ | UX-8 / CL-11 |
| | Emissions calculation | Real persisted result | 11735.015649 kg CO₂e persisted from backend calc | ✅ | CAL-1 |
| | Calculation history factor label | Factor shown | FACTOR column "—" | ⚠️ | UX-6 / CL-19 |
| | Review & approve | Loads review queue | `/review` Network error; API 500 ambiguous `id` | ❌ | PRC-1 / CL-02 |
| | Reports list/export | Real reports | 2024 Ready v1 + download; exports; 2023 honest failure | ✅ | RPT-1 |
| | Issues create | 201 | 201 (defect/exception/escalation) | ✅ | CUS-5 |
| | Issue status transition | Works from UI | `POST /issues/{id}/status` 404 (path mismatch) | ⚠️ | API-6 / CL-21 |
| | Billing page | Plan/credits/estimates | Full surface renders (CREDIT, no subscription, forms) | ✅ | CUS-6 |
| | Existing-data (D35) | Candidate search | Renders with honest "candidates only" copy | ✅ | CUS-7 |
| | Messaging send/reply | 201/201 | Verified owner send + reply | ✅ | MSG-2 |
| | Messaging create conversation | 201 | 500 ON CONFLICT; orphan thread | ❌ | MSG-1 / CL-03 |
| | Cross-org access (owner B→A) | Denied | 403 read + 403 upload | ✅ | SEC |
| | Search in-org | Results | 200 | ✅ | DOC-2 |
| | Search cross-org | Denied | 403 | ✅ | DOC-2 |
| **Customer Admin** | Org admin surface | Same as owner (except owner-only?) | `/organization` renders; member mgmt works | ✅ | CUS-8/9 |
| | Staff ops access | Denied | `/ops/me` 403 | ✅ | AUTH-3 |
| | Approve other admin's factor | 200 active | Verified admin→owner factor approval | ✅ | FAC-1 |
| | Self-approve own factor | Denied | 403 | ✅ | FAC-1 |
| **Customer Member** | Login | Member shell | Works | ✅ | AUTH-1 |
| | Upload/calculate | Allowed | API permits (upload 201; calc works) | ✅ | — |
| | Master-data admin | Denied | Facility/batch create 403 | ✅ | SEC |
| | Role change handling | — | Round-tripped member→viewer→member by owner | ✅ | CUS-9 |
| **Customer Viewer** | Read facilities/docs | Readable | 200 | ✅ | SEC |
| | Upload documents | **Denied** | **201 allowed** (viewer_up.pdf) | ❌ | SEC-1 / CL-01 |
| | Create batch/facility | Denied | 403 | ✅ | SEC |
| | Approve processed item | Denied | 403 | ✅ | SEC |
| | Edit org profile | Denied | 403 | ✅ | SEC |
| **Consultant** | Login + workspace | `/consultant` | Renders dashboard, 2 clients | ✅ | CON-5 |
| | Client list + switching | Active-client isolation | Switch A→B re-scopes all metrics (different totals/items/reports) | ✅ | CON-5 |
| | Client workspace | Scoped summary | Scoped CO2E/rows/issues/reports + "working on X" banner | ✅ | CON-5 |
| | Firm branding / White-label | Settings tabs | Tabs render | ✅ | CON-4 |
| | **Create customer** | Add client/new customer | No UI; API requires existing org id | ❌ | CON-1 / CL-05 |
| | **Upload documents** | Upload into client | No UI; API 403 | ❌ | CON-2 / CL-06 |
| | **Process / map / extract** | Drive client processing | No UI; API 403 | ❌ | CON-3 / CL-07 |
| | Client messages | Realtime messaging | Thread renders; send/reply works | ✅ | CON-6 |
| | Create conversation | 201 | 500 (same MSG-1) | ❌ | MSG-1 |
| | Cross-client access | Denied | Active-client scope holds (verified) | ✅ | CON-5 |
| **PE Staff (entity-staff)** | Login + PE workspace | `/ops` PE surface | Renders; `/ops/me` 200 (entity, operator, max 4) | ✅ | PE-1 |
| | Queue zero-state | "No work assigned" | Verified when unassigned | ✅ | PE-2 |
| | Assigned extraction | Extract item → status transitions | Batch 76222222 assigned; item → `extracted` | ✅ | PE-3 |
| | Document download | Denied | file_url empty; no download path | ✅ | PE-5 |
| | Unassigned/cross-org work | Denied | Org queue 403; org docs 403 | ✅ | PE-4 |
| | Customer messaging | Denied | 403 | ✅ | PE-6 / MSG-4 |
| **Operator** | Ops workspace | `/ops` Data entry | Renders with operator queue | ✅ | OPS-1 |
| | Process assigned items | Works | Verified through extraction flow | ✅ | PE-3/OPS-1 |
| **Reviewer** | Ops workspace | `/ops` review gate | Renders (reviewer persona) | ✅ | OPS-2 |
| | Operator queue | Denied | 403 `can_process` | ✅ | OPS-2 |
| | Validate item | 200 | Item → `validated` | ✅ | OPS-2 |
| | Calculate item | Denied | 403 (no can_process) | ✅ | OPS-2 |
| | Review queue list | 200 | Verified | ✅ | t43 |
| **QC** | Ops workspace | `/ops` QC gate | Renders QC queue + reporting | ✅ | OPS-3 |
| | QC validate | 200 | Verified | ✅ | OPS-3 |
| | QC errors/quality model | Honest state | "qc_errors not supported by current data model" | ✅ | OPS-3 |
| **Staff Admin** | Control plane | All tabs | Dashboard/Data entry/Review/QC/Staff/Roles/Entities/SLA/Issues/Messaging/Audit/Settings/Commercial | ✅ | OPS-4 |
| | Staff roster + create form | Manage staff | Roster (11) + create form render | ✅ | SA-1 |
| | Retention (N3) | Configurable, server-enforced | UI with honest "Not configured"; save/enforcement untested | ⚠️ | RET-1 / CL-15 |
| | Commercial versioned config | Versioned rules | Renders versioned rules + plans + Publish v2 | ✅ | SA-2 |
| | Staff role select | 4 roles | Includes stray `t_ba_34e3cb` | ⚠️ | UX-7 / CL-17 |
| | Assign batch to PE | 200 | Verified (Entity Beta) | ✅ | PE-3 |
| **System Admin** | Distinct control plane | Exists | **No distinct role** — staff `admin` is the control plane | ⏸ | AUTH-2 / PO-5 |
| **Cross-cutting** | Realtime messaging (N1) | Realtime + persistence | Send/reply/read/mark-read + realtime setup; creation broken | ⚠️ | MSG-1..4 |
| | Custom-factor lifecycle | draft→active | draft→(403 self)→active by other admin; solo-org deadlock | ⚠️ | FAC-1 / PO-1 |
| | Fuel-type reference | 200 | 500 PGRST205 | ❌ | CAL-3 / CL-09 |
| | Notifications | Bell + unread | Console error; RLS 0 policies; backend API 200 unused | ❌ | PERF-1 / CL-10 |
| | Mobile 390px customer shell | No overflow | No horizontal overflow; nav collapses | ✅ | D20 |
| | D19 workbench layout | Top nav + presets | Stage tabs + fixed split; no presets/keyboard divider | ⚠️ | D19-2 / CL-12 |
| | D21 consistency | Unified | V3 system + legacy leaks | ⚠️ | D21-2 / CL-13 |
| | Reports from real data | Not demo strings | 2024 report from emissions_logs; 2023 honest failure | ✅ | RPT-1 |

---

## Investor-scale continuation additions (2026-08-28, second session)

Rows verified in the continuation session against the new self-service org `OHD Audit Org Ltd` (see `CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md`). Statuses: ✅ = VERIFIED WORKING, ❌ = BROKEN, ⚠️ = PARTIALLY WORKING.

| Persona | Workflow | Expected | Actual | Status | Finding ID |
|---|---|---|---|---|---|
| **New user (Customer Owner)** | Signup → onboarding → org create (D35) | Landing on `/onboarding`, org created, workspace `/home` | Verified end-to-end on a brand-new email/org | ✅ | ISC-V1 |
| **Customer Owner** | Upload → batch → item → extract → map → validate → calculate | Full pipeline to a persisted, server-authoritative emissions result | All transitions returned expected statuses; `emissions_logs` 2661.55 kg CO₂e + content-hashed snapshot | ✅ | ISC-V1 |
| **Customer Owner** | Customer review → approve | Item → `approved` | Verified (status `approved`) | ✅ | ISC-V1 |
| **Customer Owner** | Dashboard emissions totals | Real totals from DB | `EMISSIONS ROWS 1`, `TOTAL TCO₂E 2.66`, trend populated | ✅ | ISC-V1 |
| **Customer Owner** | Documents page emissions outcome | Document shows its emissions | "Emissions from this document —" (empty) | ❌ | ISC-1 / CL-25 |
| **Customer Owner** | Evidence view of a calculation | Snapshot factor/rate/hash | "View evidence" renders snapshot (activity, multiplier, content hash) | ✅ | ISC-V1 |
| **Customer Owner** | Report generation + PDF | Real data report | Annual 2026 report totals 2661.55 kg from `emissions_logs`; 6-page PDF | ✅ | ISC-V2 |
| **Customer Owner** | Validation-issue lifecycle | Issues close when resolved | 2 blocking issues stay `open` on an `approved` item; dashboard "Open issues: 2" | ❌ | ISC-2 / CL-26 |
| **Customer Owner** | Emissions history detail | Activity + factor shown | ACTIVITY and FACTOR render "—" (payload lacks `activity`, factor name) | ⚠️ | ISC-3 / CL-27 |
| **Customer Owner** | Facility create + asset create | 201/201 | Facility 201; asset with facility 201; asset without facility → 500 (should be 422) | ⚠️ | ISC-4 / CL-28 |
| **Customer Owner** | Asset list shows facility | Facility name | Raw UUID shown | ⚠️ | ISC-4 / CL-28 |
| **Customer Owner** | Locations tab (N2) | New facility Active | Shows `Inactive` despite `is_active:true` | ⚠️ | ISC-7 / CL-30 |
| **Customer Owner + Admin** | Custom factor draft→approve | No self-approval; other admin approves | 403 self; admin2 (added via members API) → `active` | ✅ | ISC-5 |
| **PE Staff** | Claim assigned work | Queue returns item | `next-item?stage=extraction` returns assigned `FuelCard_01_Statement.pdf` | ✅ | ISC-V4 |
| **PE Staff** | PE no-download boundary | signed-url denied | 403 for OHD and Granite files | ✅ | ISC-V3 |
| **PE Staff** | Customer ↔ PE messaging | Blocked | 403 "Messaging requires an active membership…" | ✅ | ISC-V3 |
| **Customer Owner** | Cross-org document read/list | 403 | 403 for Granite document and document list | ✅ | ISC-V3 |
| **Customer Viewer** | Facility create (denied) | 403 | 403 | ✅ | ISC-V3 |
| **Customer Owner** | Cross-org conversation message | 403 | 403 | ✅ | ISC-V3 |
| **All users** | Notifications bell | Count loads | Hook calls removed `/api/notifications` → 404; console error on every page | ❌ | ISC-6 / CL-29 |

## Investor-scale continuation additions (2026-08-28, third session — API battery ISC-8..16)

| Persona | Workflow | Expected | Actual | Status | Finding ID |
| ------- | -------- | -------- | ------ | ------ | ---------- |
| **Customer Owner** (owner.demo0001, Quayside) | Custom-factor create — colliding family (Diesel/2025/GB/litres/Scope-1) | Clean 409 | Raw 500 duplicate key `idx_customer_factors_family_version` (org already has active "Customer Diesel factor v1") | ❌ | ISC-8 / CL-31 |
| **Customer Owner** | Mapping a spend-based item ("Purchased goods"/GBP) | Factor candidates / fallback picker | `mapping-options` returns `factors: []`; map → 422 "an emission factor must be selected" — pipeline dead-ends at mapping | ❌ | ISC-9 / CL-32 |
| **Customer Owner** | Customer-review queue (PRC-1) | Queue renders | 500 `column reference "id" is ambiguous` (re-confirmed on dataset) | ❌ | PRC-1 / CL-02 |
| **Customer Owner** | Conversation create (MSG-1) | New thread | 500 "no unique or exclusion constraint matching the ON CONFLICT"; orphan conversation with 0 participants left behind | ❌ | MSG-1 / CL-03 |
| **Customer Owner** | Send message in own existing conversation | 201 persisted | 201, row persisted (test message) | ✅ | ISC-V2 |
| **Customer Owner** | Billing profile | CREDIT mode, credits | 200, credits 0, no subscription (seeded orgs unconsumed) | ✅ | — |
| **Customer Admin** | Approve member-created factor draft | 200 active | 200, status active (viewer 403, member 403 self/non-admin) | ✅ | ISC-13 |
| **Customer Viewer** | Factor approve (denied) | 403 | 403 | ✅ | ISC-13 |
| **Customer Member** | Factor create (allowed by D-cf-3) | 201 | 201 draft; admin approval flips active | ✅ | ISC-13 |
| **Client Owner 1.1** (consultant 1) | Own-org resolve + docs | 200 | 200 (Quayside Distribution); same-consultant client 1.2 org docs → 403 | ✅ | ISC-12 |
| **Consultant 1** (14 clients) | Portfolio list/dashboard/client context | Works | 200; 12 active/2 onboarding; context full payload | ✅ | ISC-11 |
| **Consultant 1** | Access consultant 2's client | Denied | 403 | ✅ | ISC-11 |
| **PE Manager/Staff** (Alpha) | /ops/me + entity dashboard | Works | 200; unassigned next-item claim → 403 "can_process"; PE→customer docs/messaging → 403; **no assigned batches in dataset** | ✅(boundaries) | ISC-14 |
| **System Admin** | Audit trail + billing config | Superset of staff-admin | `/api/v2/admin/audit` → 403 "Admin privileges required" (staff-admin 200); perms lack `can_manage_billing` | ❌ | ISC-10 / CL-33 |
| **Staff Admin** | v2 audit trail | 200 | 200 (entries present) | ✅ | — |
| **Internal Operator** | Operator queue | Queued work | 200, queued 53 | ✅ | — |
| **Reviewer** | Calculate (denied) | 403 | 403 | ✅ | — |
| **All personas** | fuel-types reference (CAL-3) | 200 | 500 (re-confirmed) | ❌ | CAL-3 / CL-09 |
| **All orgs** | Document→emissions reverse lookup (ISC-1) | Emissions shown | 25/27 snapshots `source_item_id` NULL → `emissions: []` (breadth confirmed on dataset) | ❌ | ISC-1/16 / CL-25 |

## Not tested / not testable this session

| Item | Reason | Finding |
|---|---|---|
| Commercial "Publish v2" round-trip | Avoided mutating shared config; endpoints exist | SA-4 |
| Retention save + enforcement | Same; PO-2 gates durations | RET-1/CL-15 |
| Report detail view (inside) | Nav click intercepted in automation; generation verified | RPT-3 |
| Live realtime push timing | Channel-setup + persisted reads verified; push timing not instrumented | MSG-2 |
| Ops workbench on mobile | Not exercised in this session | D19-4 |
| Custom-factor precedence in a live calculation | Factor resolution code verified; custom-override calc not run | FAC-3 |
| Finalised-evidence immutability | No finalisation path exercised | EVD-3 / CL-16 |
| Customer "Review & approve" page UI capture | PRC-1 500 proven at API; UI capture outstanding (defect already established) | PRC-1 / CL-02 |

*Companion deliverables: Master Acceptance Audit (`CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md`), Investor-Scale continuation audit (`CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md`), Cline Implementation Backlog, Security Acceptance Findings.*
