# CarbonTally V3 — Persona Test Matrix

**Date:** 2026-08-28 · **Baseline:** `c36c848` · **Environment:** local/dev.
Statuses: ✅ VERIFIED WORKING · ⚠ PARTIALLY WORKING · ❌ BROKEN · ⛔ NOT IMPLEMENTED ·
❓ NOT TESTABLE · 🔒 ENV BLOCKED · 🧭 PO DECISION REQUIRED.

Test identities: existing local demo accounts (no new accounts created).

| Persona | Workflow | Expected | Actual | Status | Finding ID |
|---|---|---|---|---|---|
| Customer Owner (Org A) | Login + route to customer shell | `/` workspace | Works | ✅ | AUTH-1 |
| Customer Owner | Organisation profile edit + persistence | Save persists | PUT 200, persists after reload | ✅ | CUS-5 |
| Customer Owner | Members + invitations | Manage members/invites | Works; role round-trip verified | ✅ | CUS-5 |
| Customer Owner | Upload document | 201 + storage object | Works (owner/admin/member) | ✅ | DOC-1 |
| Customer Owner | Review & approve items | Queue lists calculated items; approve | **500 `id is ambiguous`**; UI "Network error" | ❌ | CUS-1/PRC-3 |
| Customer Owner | Create facility (with postcode) | 201 | Works | ✅ | MD-1 |
| Customer Owner | Create facility (no postcode) | Clear field error | **500 CHECK constraint** | ❌ | MD-1 |
| Customer Owner | Edit facility | Save changes | **No edit endpoint exists** | ⛔ | MD-6/CL-10 |
| Customer Owner | Vehicles CRUD | Manage vehicles | **500 `relation vehicles does not exist`** | ❌ | MD-2 |
| Customer Owner | Locations | Manage locations per N2 | Locations = facilities list (N2 resolution, honest) | ✅ | MD-3 |
| Customer Owner | Assets create/list | Manage assets | Create/list work; list shows raw facility UUID | ⚠ | MD-4/CL-19 |
| Customer Owner | Suppliers | Manage suppliers | List/create/update API; no edit UI | ⚠ | MD-5/CL-25 |
| Customer Owner | Custom factor create | Draft created | Works | ✅ | CF-2 |
| Customer Owner | Approve own custom factor | Defined path | **403 self-approval; no other approver in single-owner org** | 🧭 | CF-1 |
| Customer Owner | Org-wide search | Org-scoped results | **500 (missing vehicles table)**; cross-org 403 OK | ❌ | SRH-1 |
| Customer Owner | Emissions (manual calc) | Server-computed CO₂e | Works, persists to history | ✅ | CAL-1 |
| Customer Owner | Reports | Real data reports | Ready/Queued/Failed render; honest failures | ✅ | RPT-1 |
| Customer Owner | Report approval handoff | Approve report/items | **Blocked by review-queue 500** | ❌ | RPT-2 |
| Customer Owner | Messaging create conversation | Create + send | **500 for all personas** | ❌ | MSG-1 |
| Customer Owner | Notifications | Bell shows notifications | **"Error fetching notifications" every page** | ❌ | NOT-1 |
| Customer Admin (Org A) | Same as Owner minus owner-only | Admin ops | Owner/admin gates correct | ✅ | — |
| Customer Member (Org A) | Upload document | Allowed (member) | 201 | ✅ | DOC-1 |
| Customer Member | Approve item | Denied | 403 | ✅ | SEC-4 |
| Customer Member | Edit org profile / add member | Denied | 403 | ✅ | SEC-4 |
| Customer Viewer (Org A) | Read screens | Read-only UI | Data visible; edit affordances enabled (UX defect) | ⚠ | CUS-4 |
| Customer Viewer | Upload document | Denied | **201 ALLOWED (authorization bug)** | ❌ | SEC-1/CL-5 |
| Customer Viewer | Approve / edit / member mgmt | Denied | 403 | ✅ | SEC-4 |
| Customer Owner (Org B) | Cross-org access to Org A | Denied | 403 (docs, search, facilities) | ✅ | SEC-2 |
| Consultant | Login + consultant workspace | `/consultant` | Works | ✅ | AUTH-1 |
| Consultant | Client list + switch | Active-client switching | Verified; metric re-scope on switch | ✅ | CON-5 |
| Consultant | Default active client | Usable data | **403 dead-end until client switched** | ⚠ | CON-6 |
| Consultant | Create customer | Onboard new client | **No UI; API links existing orgs only** | ⛔ | CON-1 |
| Consultant | Upload documents | Upload for active client | **No UI; API 403 (not org member)** | ⛔ | CON-2 |
| Consultant | Process / extract / map | Drive processing | **No UI; API 403** | ⛔ | CON-3 |
| Consultant | Settings | Operational settings | Firm branding + white-label only | ⚠ | CON-4 |
| Consultant | Messaging with client | Send/receive (N1) | Creation **500**; existing threads render | ⚠ | MSG-1 |
| Consultant | Cross-client isolation | Client A ≠ Client B | Verified for visible data | ✅ | CON-5 |
| PE Manager (Entity A) | Login + PE workspace | PE surface | Works (zero-state) | ✅ | PE-1 |
| PE Manager | View entity assigned batches | See assigned work | **403 `can_process`; empty surfaces** | ❌ | PE-2/CL-13 |
| PE Staff (Entity A) | Assigned batch + extraction | Extract/map persist | Works (source viewer, lines, save) | ✅ | PE-3/PE-1 |
| PE Staff | Complete calculation (UI) | Calculated result | **409 stage gate / 422 unit mismatch** | ❌ | PRC-1/PRC-2 |
| PE Staff | Access unassigned/customer work | Denied | 403 (queue, docs, downloads) | ✅ | SEC-3 |
| PE Staff | Customer↔PE messaging | Denied | Denied (creation broken anyway) | ✅ | MSG-3 |
| Operator | Ops dashboard + data-entry queue | Queue + workbench | Works | ✅ | OPS-1 |
| Operator | Extract/map/validate via workbench | Persist | Works | ✅ | OPS-1 |
| Operator | Calculate via UI | Calculated | **409 (missing start('calculation'))** | ❌ | PRC-1/CL-2 |
| Operator | Staff roster / entities (can_view_all) | View | 200 | ⚠ | SA-5 |
| Reviewer | Review queue + validation | Validate → 200 | Works | ✅ | OPS-2 |
| Reviewer | Operator queue / calculate | Denied | 403 (`can_process`) | ✅ | OPS-2 |
| QC | QC queue + validation | Works | Works | ✅ | OPS-3 |
| QC | QC errors identification | — | Honest "not supported by data model" | ✅ | OPS-3 |
| Staff Admin | Control plane tabs | All render from real data | Works | ✅ | OPS-5 |
| Staff Admin | Retention (N3) read | Config (None = not configured) | 200, unset values honest | ✅ | RET-1 |
| Staff Admin | Commercial config read | Billing rules/plans | 200 | ✅ | SA-2 |
| System Admin | Ops read surfaces | Dashboard/staff/entities/queues | 200 | ✅ | OPS-6 |
| System Admin | Retention + commercial config | Admin access | **403 (role not mapped to admin)** | ❌ | OPS-6/CL-8 |
| All | Notifications bell | Real notifications | **Broken for every user** | ❌ | NOT-1 |
| All | Org-wide search | Results | **500 (vehicles table)** | ❌ | SRH-1 |
| All | `/api/reference/fuel-types` | Fuel types | **500 PGRST205** | ❌ | CAL-3 |
| All | D19 workbench top nav/presets | D19 chrome | Tab nav only; presets/keyboard absent | ⛔ | D19-2/CL-16 |
| All | Mobile workbench (390 px) | No overflow | Loads without horizontal overflow | ✅ | D21-3 |


---

# Phase 1 re-verification at `6148c86` (post-restoration audit, 2026-08-24)

Re-verified live during the post-restoration acceptance audit. Statuses: same legend.
Full evidence: `docs/audit/openhands/CARBONTALLY_V3_POST_RESTORATION_ACCEPTANCE_AUDIT.md`.

| Persona | Workflow | Status at `6148c86` | Note / Finding |
|---|---|---|---|
| Customer Owner | Review & approve queue | ✅ FIXED | queue 200; approve 200 persisted; member 403 (CL-1) |
| Customer Owner | Facility create (no postcode) | ✅ FIXED | 422 clean, not 500 (CL-9) |
| Customer Owner | Edit facility | ✅ FIXED | PUT 200 + Edit UI (CL-10/ISC-4) |
| Customer Owner | Vehicles | ✅ FIXED | UI table + API 200 (CL-4) |
| Customer Owner | Custom factor create | ⚠ PARTIAL | create 201; duplicate → **500**; version-bump impossible (CL-43) |
| Customer Owner | Approve own custom factor | ✅ FIXED | PO Decision 1 (owner self-approval 200) (CL-17) |
| Customer Owner | Approved factor precedence | ⚠ PARTIAL | server-side only; UI picker cannot select customer factor (CL-44) |
| Customer Owner | Calculate | ✅ FIXED | stage claim + calculate; snapshot persisted (CL-2) |
| Customer Owner | Report approval handoff | ✅ FIXED | review/approve no longer blocked (CL-1/RPT-2) |
| Customer Owner | Messaging | ✅ FIXED | create 201; send/recv 200 (CL-6) |
| Customer Owner | Notifications | ❌ NOT FIXED | console error every page (CL-45/ISC-6 partial) |
| Customer Viewer | Upload document | ❌ NOT FIXED | 201 ALLOWED (CL-42/SEC-1) |
| Consultant | Create customer | ✅ FIXED | 201 + active grant (CL-7/PO-D3) |
| Consultant | Cross-firm isolation | ✅ FIXED | 403 (re-verified) |
| PE Manager | Batches + workspace | ✅ FIXED | 200; doc 403 no-download (CL-13/PO-D4) |
| System Admin | Admin/Commercial/Audit/Retention | ✅ FIXED | all 200 (CL-8/ISC-10/PO-D2) |
| Operator | D19 workbench-first | ✅ FIXED | workbench primary at y≈200; queue below; responsive (CL-16/UH-1) |
| Reviewer | Review queue | ✅ FIXED | 2 real items; workspace 200 (UH-7) |
| Operator/All | Evidence chain | ✅ FIXED | 25/26 snapshots `source_item_id` (ISC-1) |
