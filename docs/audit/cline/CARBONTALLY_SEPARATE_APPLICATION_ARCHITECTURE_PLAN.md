# CarbonTally — Separate PE Application + CarbonTally Application: UI/UX & Access-Point Separation Plan

> **Type:** Read-only implementation planning (no code changes) — input for a later approved build.
> **Date:** 2026-09-01
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Modes honoured:** analysis only. No application/database/migration/RLS/package/config changes;
> no commits/pushes. Only this plan file is created.
> **Sources:** live-verified evidence from the functional/UX audit (persona API probes + real
> Chromium sessions), the architecture forensic report, and the Final Product Decision Register
> (D01–D53, F-1…F-32, CL-66 D-P2-02/03/04, N1, D22, WS6/SEC-0003).

---

# 1. Executive Summary

CarbonTally's **backend PE boundary is sound and verified** — no security defect was found in this
review (per the task's STOP clause, none is triggered):

- PE staff authenticate as normal Supabase users and resolve to an entity via
  `staff_profiles.entity_id`.
- Entity isolation is enforced at **three layers**: RLS (`is_entity_member` + 7 entity-scoped
  SELECT policies), API (`require_staff` + `require_entity_scope`), and auth (`require_admin`
  hard-blocks `is_entity_staff` — the previously-recorded "name-string admin over-grant" latent
  risk is already closed in `backend/auth.py`).
- Verified 403 denials: PE→customer-org list, PE→another entity's dashboard, PE→org messaging.

The **product/UI separation does not yet exist**: PE functionality lives inside the CarbonTally
`/ops` surface (`OperationsPage` branch + `v3/ops/*` components) under the shared `V3Layout`,
and there is a stray `/pe/items/:entityId/:itemId` route that still uses the customer/staff shell.
The PE user effectively receives the **CarbonTally internal-ops application**, which is exactly
what the non-negotiable product architecture forbids as the *final* state.

This plan defines the target where **six explicit application surfaces** exist — Public, Customer,
Consultant, **PE**, Staff/Operations, Admin — sharing one backend, one auth system, one V3 API and
one D21 UI foundation, but with **dedicated shells, route namespaces, navigation and role-aware
page sets**, such that the PE application can later move to a separate deployment/domain/IP
without redesigning the core processing domain.

**Headline recommendations**

1. Create a dedicated **PE application** at route namespace `/pe` (e.g. `/pe/login`,
   `/pe/dashboard`, `/pe/work/:itemId`) with its own `PEShell` (navigation = Dashboard, Assigned
   Work, Document Viewer, Extraction/Map/Validate/QC, Work Status, Messaging with CarbonTally,
   Team, PE Settings) — reusing the D21 primitives and the D19 `WorkbenchShell`/`ExtractionPanel`.
2. Keep **Staff/Operations** at `/ops` (canonical per D-P2-02), stripping the PE branch out of
   `OperationsPage`.

---

# 2. Current Application Inventory

| Application | Exists today? | Entry | Shell | Role source | Notes |
|---|---|---|---|---|---|
| Public website | ✅ | `/`, `/pricing`, `/privacy`, `/data-security`, … | public pages in `frontend/src` | unauthenticated | `App.js` public routes |
| Customer | ✅ | `/home`, `/documents`, `/processing`, `/review`, `/emissions`, `/reports`, `/billing`, `/organization`, `/messaging`, `/existing-data`, `/issues`, `/notifications` | `V3Layout` (customer links) | `requireOrg` (`RoleRoute`) + `/api/v3/me/context` | flat route namespace under `/` |
| Consultant | ✅ | `/consultant`, `/consultant/items/:clientId/:itemId` | `V3Layout` (consultant links) | `requireConsultant` | `ConsultantPage` tabs |
| **PE** | ⚠️ **not separate** | `/ops` (entity branch), `/pe/items/:entityId/:itemId` | `V3Layout` (staff links) | `requireStaff` + `me.profile.entity_id` | lives inside `v3/ops/*`; stray `/pe` item route still uses the shared shell |
| Staff/Operations | ✅ | `/ops`, `/ops/items/:id`, `/ops/review/:id`, `/ops/qc/:id` | `V3Layout` (staff links) | `requireStaff` | `OperationsPage` tabs; canonical staff app (D-P2-02) |
| Admin | ⚠️ split | legacy `admin/` CRA (`/admin/*`, port 3001, not running locally) + modern admin tabs inside `/ops` | `admin/src/components/layout/*` + `V3Layout` | legacy `AuthContext` / `require_admin` | quarantined per CL-66; final surface pending PO decision |

**Frontend structure (evidence):** single CRA `frontend/` (React Router v7) + separate CRA
`admin/`. No PE-specific app exists. Shared shell `V3Layout.jsx` renders role-appropriate nav from
`/api/v3/me/context` (`actor_type`: customer / staff / entity_staff / consultant).
`OperationsPage.jsx` branches: `me.profile.entity_id` → `PEManagerDashboard` or
`EntityExtractionWorkspace`; else internal staff tabs.

**Target mapping:**


---

# 3. Current PE Backend Boundary (verified)

**Entity model.** `processing_entities` (dedicated table, ADR-V3-001 Option B); staff identity via
`staff_profiles.entity_id` (`NULL` = CarbonTally internal, positive convention). Lifecycle
`active | remediation | suspended | terminated`; only `active` grants access. Work assignment via
`manual_extraction_batches.entity_id` (D22); batch has exactly ONE processing party (`assigned_to`
internal operator XOR `entity_id`).

**Authorization chain (verified in code).**
- `backend/auth.py`: `get_current_user` resolves `staff_profiles.entity_id` → `is_entity_staff`;
  **`require_admin()` hard-blocks `is_entity_staff`** (403 "Processing Entity staff cannot hold
  internal admin authority") — the D20 scope-first fix is implemented; the latent admin over-grant
  risk recorded in the Actor-Model §35.5 / reconciliation §27 is **closed**.
- `backend/api/operations_auth.py`: `require_staff` (active profile) → `require_internal_staff`
  (CarbonTally internal only) → `require_entity_scope(context, entity_id)` (entity staff may touch
  only their own entity); `ensure_batch_operator_access` (internal operators only on their/open
  batches; entity staff only on their entity's batches).
- Entity API surface: `/api/v3/ops/entities/{entity_id}/dashboard | extraction/batches |
  extraction/batches/{id} | extraction/items/{id} | extraction/next-item | extraction/items/{id}/
  start|extract|map|calculate|status|clarify`.
- RLS: 7 entity-scoped SELECT policies (`processing_entities`, `staff_profiles`,
  `manual_review_queue`, `manual_extraction_batches`, `manual_extraction_items`, `upload_batches`,
  `issues`); entity writes are service-role/application only.

---

# 4. Current PE UI Boundary

| Component | Location | Role | Current shell |
|---|---|---|---|
| PE landing branch | `v3/ops/OperationsPage.jsx` (`me.profile.entity_id`) | entity staff/manager | `V3Layout` (staff links!) |
| PE Manager dashboard | `v3/ops/PEManagerDashboard.jsx` | `role_name === 'pe_manager'` | inside `/ops` |
| PE work surface | `v3/ops/EntityExtractionWorkspace.jsx` | entity staff | inside `/ops` |
| PE item page | `v3/ops/PEEntityItemPage.jsx` | entity staff | `/pe/items/:entityId/:itemId` under `V3Layout` |
| Shared extraction panel | `v3/ops/ExtractionPanel.jsx` (D23) | PE + internal staff | shared |
| Document viewer | `v3/components/workbench/SecureDocumentViewer.jsx` | shared | `allowDownload=false` for PE |

**Problems:** (1) PE users see the CarbonTally staff shell/nav; (2) `/pe/items/:entityId/:itemId`
reaches `V3Layout` which is customer/staff-oriented; (3) no PE-specific navigation or module
separation; (4) PE Manager vs PE Staff is the only PE-side role differentiation today
(`pe_manager` role_name) — there is no PE Owner/Admin concept in the UI.

| Actor | Current | Target |
|---|---|---|
| Customer | flat routes + V3Layout | **Customer Application** (dedicated shell; optional `/app` prefix) |
| Consultant | `/consultant` + V3Layout | **Consultant Application** |
| PE | `/ops` entity branch + V3Layout | **PE Application** (`/pe` namespace + PEShell) |
| Staff | `/ops` + V3Layout | **Operations Application** (`/ops`) |
| Admin | split (legacy CRA + /ops tabs) | **Admin Application** (`/admin`, pending PO decision) |

3. Keep **Admin** decisions pending the Product Owner's `/admin`-vs-`/ops` ruling (decision
   register §39); design the Admin surface as a separate shell regardless, so the final choice is
   a page-set/nav decision, not an architecture rework.
4. Migrate the existing PE components (`EntityExtractionWorkspace`, `PEManagerDashboard`,
   `PEEntityItemPage`, and the shared `ExtractionPanel`) **without deleting** the `/ops` branch
   until the `/pe` surface is verified (non-destructive, incremental).
5. Fix the **document viewer** as a pre-requisite: the signed-URL download-scope defect must be
   corrected (render-scope signed URL) before any PE preview milestone — without ever exposing
   unrestricted original-document URLs.
6. Keep PE role model as **PE Owner/Admin, PE Manager, PE Staff** at the application level,
   mapped onto the existing entity + staff-permission surface (no new permission engine; a
   dedicated `PE_ROLES` vocabulary to be ratified).

# 5. Current Customer UI Boundary

`V3Layout` customer shell + flat routes `/home`, `/documents`, `/processing`,
`/processing/:itemId` (ProcessingItemWorkspace on WorkbenchShell), `/review`, `/review/:itemId`,
`/emissions`, `/reports`, `/reports/:id`, `/issues`, `/billing`, `/organization`,
`/messaging`, `/existing-data`, `/notifications`. Route guard `RoleRoute requireOrg` (fail-closed
via `/api/v3/me/context`). All API through `/api/v3/*` org-scoped, `require_org_member` /
`require_org_admin` backend guards. **No PE access from customer surface** (verified: a PE user
redirected from `/home` by RoleRoute; backend denies anyway).

---

# 6. Current Consultant UI Boundary

`/consultant` (ConsultantPage hub: dashboard, client switcher, client workspace, white-label,
team, client messaging, new-customer view) + `/consultant/items/:clientId/:itemId`
(ConsultantItemPage). Guard `requireConsultant`. Client-scoped authorization re-verified per
request (`/api/v3/consultants/clients/{id}/*`). Consultant clients do **not** log in (D31).

---

# 7. Current Staff/Operations UI Boundary


---

# 8. Current Admin UI Boundary

Two surfaces: (a) legacy `admin/` CRA (`/admin/*`, separate AuthContext, direct Supabase reads —
**bypasses FastAPI**; quarantined per CL-66; **not running** in the local environment because port
3001 is occupied); (b) modern staff-admin tabs inside `/ops` (`CommercialTab`, `QcQueue`,
`IssuesTriageTab`, `AuditConsoleTab`, `SettingsTab`, `StaffRoster`, `StaffRolesTab`, `SlaTab`,
`ProcessingEntitiesTab`) gated by `require_admin` (`admin`/`system_admin`) and
`can_manage_staff`/`can_manage_billing`. The `/admin` vs `/ops` final ruling is PO-pending
(decision register §39).

---

# 9. Current vs Target Architecture

| Aspect | Current | Target |
|---|---|---|
| PE surface | inside `/ops` + stray `/pe` item route under staff shell | **Dedicated PE Application** `/pe` with `PEShell` |
| Customer surface | flat routes under `/` + V3Layout | Customer Application shell (routes optionally under `/app`) |
| Consultant surface | `/consultant` + V3Layout | Consultant Application shell |
| Staff surface | `/ops` + V3Layout | Operations Application `/ops` (unchanged canonical) |
| Admin surface | split legacy CRA + /ops tabs | Admin Application `/admin` (after PO ruling) |
| Shell | one `V3Layout` for all authenticated roles | per-application shells sharing primitives |
| Navigation | role-filtered single nav | role-and-application specific navigation |
| Backend | one FastAPI + one V3 API | unchanged (shared) |
| Auth | Supabase + `/api/v3/me/context` | unchanged (shared) |
| UI foundation | D21 primitives | unchanged (shared) |


**Verified denials (live probes):** PE→`/api/v3/ops/organizations` **403**; PE→
`/api/v3/ops/entities/999/dashboard` (foreign entity) **403**; PE→org-scoped messaging **403**.

**Document access.** Documents are served via short-lived signed URLs
(`services/storage.py:storage_signed_url`), authorized before issuance. The PE no-download
boundary is server-side; the current **document-preview defect** is a *browser/render* issue
(signed-URL `scope=download` triggers a download; iframe renders blank) — it does **not** weaken
the no-download boundary. It is a P1 UI defect to fix as a pre-requisite (§21).

**Security verdict: no defect found.** The backend PE boundary is intact at RLS, API and auth
layers. No STOP is triggered. The only hardening note: the PE staff-role vocabulary
(`staff_roles.name`) is currently shared with CarbonTally staff roles — a PE-side role naming
separation is a product decision (§26/§39), not a security defect today because `require_admin`
and `require_entity_scope` gate entity staff independently of role name.

---

# 10. Target Application Boundary Diagram

```
                        ┌──────────────────────────────────────────────┐
                        │          SUPABASE AUTH (shared)              │
                        │   one identity · /api/v3/me/context          │
                        └──────────────┬───────────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │   CARBONTALLY FASTAPI V3 API (shared)    │
                    │   require_org_member · require_staff     │
                    │   require_entity_scope · require_admin   │
                    │   domain/engines/repositories (shared)   │

---

# 11. PE Application Architecture

**Route namespace:** `/pe` (behind a `PEShell` + `RoleRoute requirePE`).

```
/pe                          → PE Landing → dashboard (role-aware)
/pe/dashboard                → PE Dashboard (own entity: batches, items, status, SLA)
/pe/work                     → Assigned Work list (own entity only)
/pe/work/:itemId             → Processing Workspace (WorkbenchShell + ExtractionPanel)
/pe/work/:itemId/evidence    → item evidence/status
/pe/messages                 → Messaging with CarbonTally (entity-scoped; pending PO decision)
/pe/team                     → PE Team management (Owner/Admin/Manager)
/pe/settings                 → PE settings (Owner/Admin)
```

**Shell:** `PEShell` (new, modeled on `V3Layout` but PE-only nav + "Processing Entity" identity
badge; reuses `Drawer`, `SearchBox` if org-scoped search is excluded for PE, `Icon`, D21 tokens).
The PE logo/title is CarbonTally-branded but with an explicit "Processing Entity workspace"
identity; future white-label may alter branding.

**Modules exposed (role-aware):**
- Dashboard, Assigned Work, Workspace (document viewer, extraction, mapping, validation,
  review/QC, status) — all roles.
- Messaging with CarbonTally — all roles (after PO decision on entity-scoped threads; until then
  hidden with a clear "mediated clarification only" note).
- Team management — PE Owner/Admin/Manager (PE-side roles).
- PE Settings — PE Owner/Admin.
- **Never exposed:** customer modules, consultant modules, CarbonTally staff/admin modules.

**PE-side roles (to be ratified):** PE Owner/Admin · PE Manager · PE Staff. Current mapping:
`staff_profiles.entity_id` + `staff_roles.name` (`pe_manager` vs other). Proposed: a PE-side role
vocabulary (`PE_ROLES = owner | admin | manager | staff`) stored on the entity profile and
resolved server-side into entity-scoped capabilities, without reusing CarbonTally internal role
names for authority (guards stay `require_entity_scope` + entity-role checks).

**Component reuse:** `ExtractionPanel`, `WorkbenchShell`, `SecureDocumentViewer`,
`v3/components/ui/*`, `DataTable`, `StateViews`, `StatusBadge` — no new component system.

---

# 12. Staff/Operations Architecture

`/ops` remains the canonical Operations application (D-P2-02). **Change:** remove the
`me.profile.entity_id` branch from `OperationsPage` (PE users land on `/pe` instead); keep the
internal staff tabs and dedicated workspaces unchanged. The shared `ExtractionPanel` and

---

# 13. Admin Architecture

Pending PO ruling (§39): the plan designs Admin as a **separate AdminApp** at `/admin` (V3-API
backed, D21 primitives, `AdminShell`) so that whichever ruling lands, the separation is already
structural. The current modern admin capabilities (Commercial, QC, Issues, Audit, Settings,
Staff/Roles, Entities, SLA) move to the AdminApp page set; the quarantined legacy `admin/` CRA is
not extended and is retired after dependency inventory. **No Admin redesign during this task** —
only surface separation.

---

# 14. Customer Architecture

CustomerApp shell (`CustomerShell` = today's `V3Layout` customer branch, optionally mounted under
`/app`). Routes/nav unchanged in behaviour. PE and staff routes are outside this shell; a PE user
reaching `/app` is redirected by `RoleRoute requireOrg` and denied by backend.

---

# 15. Consultant Architecture

ConsultantApp shell (today's consultant branch of `V3Layout` + `ConsultantPage`) at `/consultant`.
Client-scoped authorization unchanged. No PE/customer modules exposed.

                    └────────────┬─────────────┬───────────────┘
                                 │             │
        ┌────────────────────────┼─────────────┼────────────────────────┐
        ▼                        ▼             ▼                        ▼
   PUBLIC                  CUSTOMER      CONSULTANT             PROCESSING ENTITY
   website                 /app          /consultant            /pe
   (marketing)             CustomerApp   ConsultantApp          PEApp (PEShell)
                                                 │                  │
                              ┌───────────────────┴───────────────────┐
                              ▼                                       ▼
                        STAFF / OPERATIONS                    ADMIN (pending PO)
                        /ops  OpsApp                           /admin  AdminApp
                        (canonical D-P2-02)                    (control plane)
```

Rules: each application is a **route namespace + dedicated shell + role-aware navigation**; all
call the same V3 API; the backend is the only authorization authority; a PE user navigating to
`/app` or `/ops` receives **no extra data** (frontend guards redirect; backend denies).

`/ops` (OperationsPage permission-aware tabs: Dashboard, Data entry, Review, QC, Staff, Roles,
Entities, SLA, Messaging, Audit, Settings, Commercial, Issues) + dedicated workspaces
`/ops/items/:id`, `/ops/review/:id`, `/ops/qc/:id`. Guard `requireStaff` +
`require_internal_staff` for internal pipeline. Canonical staff app per D-P2-02.

---

# 16. Authentication Architecture

- **Shared Supabase Auth** for all applications; **no separate user databases**.
- Login: per-application entry points (`/login`, `/pe/login`, `/admin/login` concept) but all use
  the same `supabase.auth` password grant / Google OAuth; post-login routing via the single
  authoritative `GET /api/v3/me/context` (returns `actor_type` + `destination`) — a PE user always
  lands on `/pe`, staff on `/ops`, customer on `/app`/`/home`, consultant on `/consultant`,
  admin on `/admin`.
- Session/token: existing bearer token propagation (`v3Fetch`/`apiClient`); localStorage
  fallback unchanged.
- Cross-application navigation: a user who types another application's URL is redirected by the
  role guard to their own application (frontend) **and** denied by backend guards — a PE user
  gains no privilege by URL (verified backend behaviour).
- Logout: per-application sign-out, clearing the shared Supabase session.
- PE application must **not** include customer/consultant/staff/admin route definitions in its
  nav; routes are still guarded (defence-in-depth; UI is never the security boundary).

---

# 17. Authorization Architecture

Authorization stays **100% server-side** and unchanged in principle:

| Application | Primary guard | Entity/boundary | Admin/ops guard |
|---|---|---|---|
| Customer | `require_org_member` / `require_org_admin` | org | — |
| Consultant | firm guard + `ensure_consultant_org_access` | client grants | — |
| PE | `require_staff` + `require_entity_scope` | entity | `require_admin` hard-blocks `is_entity_staff` |
| Staff | `require_staff` + `require_internal_staff` + permissions | system | `require_admin` |
| Admin | `require_admin` | system | `ADMIN_ROLE_NAMES` |

No new authorization engine. PE role additions (Owner/Admin/Manager/Staff) are resolved

---

# 18. API Architecture

- **Reuse the existing V3 API.** PE app → `/api/v3/ops/entities/*` (entity-scoped);
  optionally introduce a thin `/api/v3/pe/*` alias later for contract cleanliness — **same
  domain/service/engine/repository layer**. No duplicated business logic.
- Staff app → `/api/v3/ops/*`; customer → `/api/v3/*` org-scoped; consultant →
  `/api/v3/consultants/*`; admin → `/api/v3/ops/*` (admin-gated) + `/api/v3/commercial/*` +
  `/api/v3/qc/*`.
- New PE context endpoint (recommended): `GET /api/v3/pe/me` returning entity profile + entity
  role + capabilities, mirroring `/api/v3/ops/me` — so the PE shell never calls ops-dashboard
  aggregates it must not see.

---

# 19. Database Boundary

No schema changes required for surface separation. The entity model (`processing_entities`,
`staff_profiles.entity_id`, `manual_extraction_batches.entity_id`) is already correct and is the
shared tenant boundary. A future PE-side role vocabulary could add a column (e.g.
`staff_profiles.entity_role`) — **deferred**; current `staff_roles.name` (`pe_manager`) suffices
for the first PE Manager/Staff split.

---

# 20. RLS Boundary

Existing RLS is preserved exactly (org/consultant/entity axes; entity deny-by-default + 7 entity
SELECT policies). No RLS changes for separation. If entity-scoped messaging is approved later, new
entity conversation policies would be **additive** (N1-compliant), never touching org-scoped
messaging RLS.

`WorkbenchShell` continue to serve internal operator/reviewer/QC workspaces. PE management
(Entities tab, batch assignment) stays in Operations (CarbonTally controls assignment — D24).

---

# 21. Document Access Architecture

- Preserve: private bucket + short-lived signed URLs + authorize-before-issue + PE no-download.
- **Pre-requisite fix (P1):** `services/storage.py:storage_signed_url` must request a
  **render-scope** signed URL (JWT scope ≠ `download`) so the browser renders inline; align
  `SecureDocumentViewer` iframe sandbox (or render via `react-pdf`, already a dependency). This
  fixes preview for PE **and** customer/staff workspaces without exposing unrestricted URLs.
- **Three document classes for the PE application:**
  1. *Original customer document* — never exposed to PE beyond the required view of assigned work;
  2. *PE-visible document* — the signed, view-only render of the assigned source item (the only
     class PE sees today);
  3. *Future sanitized/redacted derivative* — for the later privacy layer (§33); not built now.
- No PE user may ever receive an unsigned or bucket-root URL; signed URLs remain the sole access
  path and are re-authorized at issue time.

---

# 22. Shared UI Design System

Applications share the **D21 foundation**: `v3/components/ui/*` (Button, FormControls, Dialog,
Drawer, Tabs, Badge/Card, StateViews, StatusBadge, Icon, DataTable) + `tokens.css` + `ui.css` +
`v3.css` conventions. `PEShell`/`AdminShell` reuse these; only navigation/identity differ. **No
shadcn/ui unless explicitly approved**; **no third component system** for PE. Standardization
targets (already partially converged): buttons (ui/Button over `v3-btn`), forms
(FormControls over raw inputs), tabs (adopt `ui/Tabs.jsx`, currently 0 consumers), loading/empty/
error (StateViews), cards (adopt `ui/Card`/`StatCard`, currently 0 consumers — pages hand-roll).

---

# 23. DataTable Architecture

`DataTable` remains the canonical table foundation for all applications (13 consumers today).
Gaps to close before universal adoption in the PE app: bulk-selection/row-actions props and a
shared filter toolbar (P2/P3 engineering). PE tables (Assigned Work, Team) use `DataTable` with
server `limit/offset/total` — never `v3-ops-table` or raw tables in new PE pages.

---

# 24. Pagination/Search/Sort/Filter

- Uniform server-side `limit/offset/total` + org/entity-scoped search (today org-only;
  **entity-scoped search** is a future addition for the PE app — search must be scoped to the
  entity, never global).
- Sorting: client (`sortValue`) and server (`onSortChange`) as today; PE lists default to server
  sorting on `created_at`/status.

---

# 25. Responsive UI Architecture

Reusable rules (not per-page patches), mandated for every new PE page and applied as a shared
foundation fix:

1. **Reconcile the duplicate `.v3-form-grid` definitions** (`v3.css:202` minmax 220px vs
   `admin.css:61` minmax 280px) into one shared rule.
2. **Add `min-width: 0` and `overflow-wrap: anywhere`** to grid/flex children in shared form
   layouts so no container can squeeze text into one-character lines at 100% zoom.
3. Wrap any raw table in a horizontal-scroll container (or migrate to DataTable).
4. Test widths: 1920 / 1440 / 1280 / 1024 / 768 / 390 (the PE workspace uses the D19 tray flow
   below ~900px via `WorkbenchShell`).
5. Do not rely on browser zoom below 100%.

(These were identified in the functional audit; the org-profile overflow reported at 100% zoom was
not reproduced in headless Chromium at tested widths but the duplicate CSS rules are a verified
risk factor.)

server-side as entity-scoped capabilities; the UI merely renders/redirects.

---

# 26. PE Role Navigation Matrix

| Module | PE Owner/Admin | PE Manager | PE Staff |
|---|---|---|---|
| Dashboard (own entity) | ✅ | ✅ | ✅ |
| Assigned Work list | ✅ | ✅ | ✅ |
| Processing workspace (viewer/extract/map/validate/QC) | ✅ | ✅ | ✅ |
| Work status/evidence | ✅ | ✅ | ✅ |
| Messaging with CarbonTally | ✅ | ✅ | ✅ (after PO decision; else hidden) |
| Team management | ✅ | ✅ | — |
| PE Settings | ✅ | — | — |
| Customer modules | ❌ | ❌ | ❌ |
| Consultant modules | ❌ | ❌ | ❌ |
| CarbonTally staff/ops modules | ❌ | ❌ | ❌ |
| Admin modules | ❌ | ❌ | ❌ |
| Cross-entity work | ❌ | ❌ | ❌ |

# 27. Staff Role Navigation Matrix (unchanged)

| Module | operator | reviewer | qc_specialist | admin | system_admin |
|---|---|---|---|---|---|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Data entry queue + workspace | ✅ | — | ✅ | ✅ | ✅ |
| Review queue | — | ✅ | ✅ | ✅ | ✅ |
| QC | — | — | ✅ (internal) | ✅ | ✅ |
| Staff/Roles/Entities/SLA/Settings/Audit/Commercial | — | — | — | ✅ | ✅ |
| PE entity management (assignment) | ✅ (assign w/ can_manage_staff) | — | — | ✅ | ✅ |

# 28. Admin Role Navigation Matrix (target AdminApp)

| Module | admin | system_admin |
|---|---|---|
| Organisations/Users/Staff/PEs/Consultants | ✅ | ✅ |
| Factors/Defra | ✅ | ✅ |
| Reviews/Manual processing/QC | ✅ | ✅ |
| Billing/commercial/config | ✅ | ✅ (superset incl. can_manage_billing) |
| Settings/retention | ✅ | ✅ |
| Audit/logs | ✅ | ✅ |

# 29. Customer Role Navigation Matrix (unchanged)

| Module | owner | admin | member | viewer |
|---|---|---|---|---|
| Home/Documents/Processing/Emissions/Reports/Issues/Billing | ✅ | ✅ | ✅ | ✅ (read-only) |
| Review & approve | ✅ | ✅ | — | — |
| Organisation mgmt (members/master data) | ✅ | ✅ | — | — |
| Custom factors (approve) | ✅ (self-approve allowed) | ✅ | propose only | — |
| PE application | ❌ | ❌ | ❌ | ❌ |

# 30. Consultant Role Navigation Matrix (unchanged)

| Module | owner | manager | consultant | viewer |
|---|---|---|---|---|
| Dashboard/clients/workspace/reports/evidence | ✅ | ✅ | grant-gated | grant-gated read |
| Revoke relationship | ✅ | ✅ | ✅ | ❌ |
| Team management | ✅ | ✅ | — | — |
| White-label/branding | ✅ | — | — | — |
| Customer/PE/Admin apps | ❌ | ❌ | ❌ | ❌ |

---

# 31. Current `/ops` Migration Plan (non-destructive, incremental)

1. **Fix P1 prerequisites** (document viewer render-scope; unit-normalisation; methodology
   server-side) — independent of separation.
2. **Add `/pe` namespace + `PEShell` + `RoleRoute requirePE`**; create

---

# 32. Future Separate PE Deployment Plan

The PE app must be deployable independently **without redesigning the core domain**. Coupling
analysis:

- **Frontend coupling today:** PE components live inside `frontend/src/v3/ops` and are imported by
  `App.js`/`OperationsPage`. For a separate deployment, isolate them in `frontend/src/pe` (or a
  `pe/` package) with no imports from customer/ops pages (only shared `v3/components/*`). A
  separate build entry (CRA multi-app or a second Vite/CRA app consuming the shared component
  package) then becomes possible.
- **Backend coupling:** low — the PE API is already a stable contract
  (`/api/v3/ops/entities/*`); a future `pe.carbontally.co.uk` frontend can call the same API
  (CORS + bearer auth). No backend change needed; optionally add `/api/v3/pe/*` aliases.
- **Auth coupling:** shared Supabase; a separate deployment still authenticates against the same
  project (no separate user DB).
- **Identified blocker to avoid:** never let the PE app import `App.js` route tables or customer/
  ops pages; keep PE pages self-contained; keep the shared-primitives package boundary explicit.
- Phases: (1) same repo, `/pe` namespace; (2) independent build entry; (3) `pe.carbontally.co.uk`
  deployment; (4) optional external PE platform consuming the PE API. Each phase is a deployment
  concern, not a domain redesign.

---

# 33. Future PE Privacy/Masking Architecture

Not implemented now (no security defect requires it). Design intent so the PE app can later
present:

- Customer → `CT-CLIENT-004821` · Document → `CT-DOC-771923` · Supplier → `SUPPLIER-019`
- Pseudonymous aliases, sanitized/redacted document derivatives, minimum-necessary PE-visible
  metadata; the internal identity mapping remains **inside CarbonTally**; aliases are
  server-generated and irreversible from the PE frontend/API.
- Design points for today: keep PE-visible payloads minimal; the entity workspace should not
  enumerate customer org names where the API can omit them; future alias mapping lives in a
  server-side module (no frontend key material).

---

# 34. Security Threat Model (PE application separation)

| Threat | Control (current/planned) |
|---|---|
| PE enumerates customer organisations | Existing: `require_internal_staff` denies entity staff org lists (403 verified). PE app never renders customer lists. |
| PE accesses another entity's work | Existing: `require_entity_scope` + RLS entity policies (403 verified). |
| PE staff reach admin authority | Existing: `require_admin` hard-blocks `is_entity_staff` (verified). |
| PE staff reach staff/ops pipeline | Existing: `require_internal_staff` for the manual-extraction pipeline and ops-wide surfaces (403 verified). |
| PE downloads source documents | Existing: private bucket + signed URLs + `allowDownload=false`. Planned: render-scope signed URL (no download scope). |
| URL hopping across applications | Frontend role guards redirect; backend denies. No privilege by URL (verified). |
| PE messaging customers/consultants | Existing: PE denied org messaging 403; N1 boundary. |
| Future: alias reversal | Server-side alias mapping only; no frontend/API reversal (design §33). |
| Role-name confusion (PE role vs internal role) | Current: entity guards independent of role name. Planned: separate PE-side role vocabulary (PO decision §39). |

---


---

# 35. Acceptance Tests

**PE**
1. PE staff logs in → lands on `/pe` (not `/ops`, not `/app`).
2. PE dashboard renders own entity only (name/staff/batches of its entity).
3. PE sees only authorized modules (no customer/consultant/staff/admin nav).
4. PE Assigned Work shows only its entity's batches/items.
5. PE workspace: document viewer renders inline (render-scope URL); no download control.
6. PE `/pe/work/:itemId` extraction/map/validate/QC endpoints return 200 for own entity items.
7. PE→another PE: `/api/v3/ops/entities/{other}/dashboard` → 403; RLS returns no rows.
8. PE→customer app: `/app`/`/home` redirects to `/pe`; `/api/v3/organizations/*` → 403.
9. PE→staff: `/ops` redirects to `/pe`; ops internal endpoints → 403.
10. PE→admin: `/admin` redirects; `/api/v3/qc/*`, `/api/v3/commercial/*` → 403.
11. PE cannot enumerate customer organisations (no endpoint returns org lists; 403 verified).
12. PE cannot bypass API authorization by direct requests (all writes entity-scoped).

**Staff**
13. Internal staff logs in → `/ops`; performs authorized operational work (assign, queue,
    extract, validate, review, QC).
14. Internal staff can assign PE work (`assign_batch` entity_id); sees Entities tab.

**Admin**
15. Admin logs in → admin surface; separate from staff and PE; `/admin` page set only.

**Customer**
16. Customer logs in → customer app; cannot reach PE functionality; no PE nav.

**Consultant**
17. Consultant logs in → `/consultant`; client-scoped authorization retained (A/B allowed, C denied).

**Responsive**
18. PE pages pass overflow checks at 1920/1440/1280/1024/768/390 (no horizontal scroll; no
    one-character text at 100% zoom).

   `v3/pe/*` pages by **moving** (git mv, preserving history) the PE components
   (`EntityExtractionWorkspace`, `PEManagerDashboard`, `PEEntityItemPage`) and sharing
   `ExtractionPanel`/`WorkbenchShell`/`SecureDocumentViewer`.
3. **Redirect** the `/ops` entity branch: PE users landing on `/ops` get redirected to `/pe`
   (temporary bridge kept until verified).
4. **Keep the `/ops` PE branch** running behind the bridge (do not delete) until acceptance tests
   pass and the bridge is confirmed for N days.
5. **Remove the bridge + `/ops` PE branch** only after verification (still non-destructive to
   data; the entity API endpoints remain unchanged and continue to serve both internal assignment
   and the PE app).
6. No database, RLS, migration or API-authorization changes are required for the migration.


---

# 36. Implementation Phases

**Phase P0 — pre-requisites (smallest safe fixes).**
P0.1 Fix signed-URL render scope (`storage_signed_url`) + SecureDocumentViewer sandbox/viewer.
P0.2 Unit-normalisation at the calculation-engine boundary; server-side methodology derivation.
P0.3 Responsive foundation: reconcile duplicate `.v3-form-grid`; `min-width:0` +
`overflow-wrap:anywhere`; table scroll wrappers.

**Phase P1 — PE application surface (same repo).**
P1.1 Add `RoleRoute requirePE` + `/api/v3/pe/me` context; `PEShell`; `/pe` route namespace.
P1.2 Move PE components to `v3/pe/*` (git mv; shared workbench/extraction/viewer reused).
P1.3 Redirect `/ops` entity branch → `/pe`; keep the old branch as bridge.
P1.4 PE Team/Settings surfaces (PE-side roles) behind entity-role checks.
P1.5 Acceptance tests §35 PE block + responsive block.

**Phase P2 — Operations/Admin separation.**
P2.1 Remove the PE branch from `OperationsPage` (after bridge verified).
P2.2 AdminApp shell + page set on the V3 API (after PO ruling on `/admin` vs `/ops`).
P2.3 Retire the quarantined legacy `admin/` CRA after dependency inventory.

**Phase P3 — PE side roles & messaging (subject to PO decisions).**
P3.1 PE role vocabulary (`owner|admin|manager|staff`) server-side.
P3.2 Entity-scoped PE↔CarbonTally messaging (if approved).

**Phase P4 — deployment + privacy (future).**
P4.1 Independent PE build entry; P4.2 `pe.carbontally.co.uk`; P4.3 external PE platform.
P4.4 Pseudonymous alias / redacted-derivative layer.

---

# 37. Risks

| Risk | Mitigation |
|---|---|
| Breaking PE users during migration | Non-destructive bridge; no data/API change; acceptance tests before removal |
| Duplicate logic across apps | Shared V3 API + D21 primitives; no per-app business logic |
| `/admin` ambiguity | Separation is structural regardless of ruling; page-set decision only |
| Document viewer remains broken | P0.1 gate before PE preview milestone |
| Entity-scoped search/nav accidentally global | PE app never calls org-wide aggregates; entity-scoped queries only |
| Layout regression at 100% zoom | P0.3 shared foundation + acceptance widths |
| PE-side role model conflicts with internal `staff_roles` | Separate PE role vocabulary (PO decision); guards stay entity-scoped |

---

# 38. Decisions Already Made (relevant to this plan)

- PE = third-party processor, NOT a customer; separate boundary; work-assignment based
  (D23/D24; F-3/F-4).
- PE strictly non-customer-facing; no direct customer↔PE communication; mediated (D25; F-4).
- PE no-download of source documents (D07; F-5).
- Quality chain PE QC → CT QC → Customer final approval (D05/D20; F-6).
- CarbonTally controls assignment (D24).
- `/ops` is the canonical Staff/Operations application (D-P2-02; F-24).
- Admin control-plane surface ruling pending (decision register §39) — NOT yet made.
- Entity-scoped PE messaging implementation NOT yet approved (N1 boundary approved) — NOT yet made.
- V3 canonical; D21 UI foundation; no shadcn assumption (F-17/F-25).
- Four access axes never interchangeable (D22; F-2).
- One account, one role (D03; F-2).

# 39. Decisions Requiring PO Approval

1. **Dedicated `/pe` route namespace + `PEShell` as the PE application** (the core of this plan).
2. **PE-side role vocabulary** (`owner|admin|manager|staff`) and its storage mapping.
3. **Admin final surface**: dedicated `/admin` AdminApp vs `/ops` (decision register §39 #1).
4. **Entity-scoped PE ↔ CarbonTally operational messaging** (decision register §39 #2).
5. **Optional `/app` prefix** for the Customer application (vs keeping current flat routes).
6. **Optional `/api/v3/pe/*` alias** for the PE API contract (vs reusing `/api/v3/ops/entities/*`).
7. **Masking/privacy layer scope** for a later phase (not this task).

# 40. FINAL RECOMMENDATION

1. **Approve the `/pe` dedicated PE application** as the target surface, with `PEShell`, the
   `v3/pe/*` page set, `RoleRoute requirePE`, and `/api/v3/pe/me` context — reusing the existing
   V3 API, auth, RLS and D21 primitives, and the D19 workbench/extraction components.
2. **Treat P0.1 (document viewer render-scope fix) as the immediate pre-requisite**, since PE
   preview is unusable today and is required by every PE workflow.
3. **Execute the migration non-destructively** (Phase P1): new `/pe` surface, `/ops`→`/pe`
   redirect bridge, old branch retained until acceptance passes.
4. **Decide the Admin surface** (§39 #3) before Phase P2.2; keep the separation structural
   regardless of the ruling.
5. **Do not redesign the PE backend boundary** — it is verified sound (RLS + API + auth layers;
   `require_admin` already hard-blocks entity staff); only additive PE-role and (optionally)
   messaging work is proposed, gated on PO approval.
6. **Keep all applications on the shared V3 API and D21 UI foundation**; a future separate PE
   deployment (domain/IP/external platform) is then a deployment step, not a redesign.

---

## Safety confirmation

Read-only plan. No application files, database, migrations, RLS, packages, configuration, tests,
Docker or infrastructure modified; no documents deleted/moved/renamed; no commits/pushes. Only this
plan file was created.
