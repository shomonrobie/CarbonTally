# CarbonTally V3 — Authenticated Platform UI/UX & Product Workflow Audit

| | |
|---|---|
| Audit type | Independent, READ-ONLY UI/UX + Product Workflow audit |
| Repository | https://github.com/shomonrobie/CarbonTally |
| Baseline | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (== `origin/main` at audit time) |
| Date | 2026-08-24 |
| Mode | Read-only. No source, database, RLS, API, migration, configuration or Git changes were made. HARD STOP after this report. |
| Scope | The **authenticated** platform only (the V3 customer workspace, consultant workspace, internal operations and Processing Entity surfaces). The public marketing website is out of scope except where it links into the authenticated area. |
| Evidence base | Actual database schema + RLS migrations (`supabase/migrations/*.sql`), backend implementation (`backend/**`), API routes (`backend/api/*.py`, `backend/routes/**`, `backend/main.py`), frontend routes (`frontend/src/App.js`), frontend components (`frontend/src/v3/**`), and architecture/decision documentation (`docs/architecture/**`, `docs/audit/**`). |

---

## 0. Scope note, sources and caveats

**Referenced documents that do not exist at this baseline.** The task brief
references `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
and `docs/audit/openhands/`. **Neither exists in the repository at commit
`d4dcca1`.** No `docs/ChatGPT/` directory exists anywhere in the tree. The
authoritative product/architecture decision evidence actually present in the
repository and used for this audit is:

- `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md` (ADR-V3-001…016, D-series records)
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (authoritative actor/workspace/access analysis, §§30–50)
- `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md`
- `docs/architecture/'CarbonTally Staff Roles & Organizational Structure.md'`
- `docs/architecture/ARCHITECTURE_DECISIONS.md`
- `docs/audit/CarbonTally_V3_Processing_Entity_Architecture_Decision_Analysis.md`
- `docs/audit/CarbonTally_V3_Processing_Entity_Open_Questions_Classification.md`
- `docs/audit/CarbonTally_V3_Queue_Architecture_Audit.md`
- `docs/audit/CarbonTally_V3_Customer_Factors_Impact_Analysis.md`
- `docs/audit/cline/CARBONTALLY_V3_D32…D37_*.md` (per-day implementation records)

Where a brief instruction conflicts with the actual repository, the repository
code is treated as the source of truth (per the Actor Workspace Access Model's
own authority hierarchy). No Product Owner decision was overridden; the
decisions listed in the brief (one-account-one-role, no entity document
download, portal-based processing, Owner/Admin/Member/Viewer, consultant
cross-org access, existing customer factors, existing DEFRA/SEAI factors,
row-level traceability, customer final approval, entity self-validation,
CarbonTally final review) are all consistent with the repository evidence and
are preserved.

**Terminology in this report.** The platform code mixes "organisation" and
"organization"; the DB schema and RLS use `organization_*`. This report uses
"organisation" in prose (the canonical glossary term) and the exact code
spellings when naming tables/columns/routes.

---

## 1. Executive Summary

CarbonTally V3 ships a coherent, data-driven authenticated platform. The
backend is unusually well-grounded: RLS is deny-by-default, tenant and
Processing-Entity boundaries are enforced at the database layer, and the V3
frontend deliberately shows only real backend data (no fabricated numbers).
The architecture documentation (Actor Workspace Access Model, ADR register,
D-series records) is exceptionally precise about what is and is not enforced.

However, the audit found **two P0-adjacent workflow/authorization
discrepancies, one P0 security-enforcement verification (positive), and a
large set of P1/P2 role-fidelity and UX gaps**:

1. **Processing Entity document download is genuinely blocked — verified.**
   Storage objects RLS is org-member-only (`d32_documents_*`), the only
   signed-URL endpoint is org-member-gated, and the entity extraction API
   returns **unsigned** storage paths. Product Owner decision "external
   Processing Entities must not download customer documents" is **enforced by
   the current code** at the RLS + API layers. No `SECURITY/ARCHITECTURE GAP`
   exists on this decision. **However**, the enforcement is so blunt that the
   portal document viewer is broken for entity staff *and* internal operators
   (see finding E-1), which means Processing Entities **cannot currently
   perform extraction through the CarbonTally portal** — the portal cannot
   display the very document they must extract from. This contradicts Product
   Owner decision "Processing Entities perform extraction/mapping/validation
   through the CarbonTally portal" and must be resolved as a P1 workflow
   defect.

2. **The `viewer` role is functionally a writer.** RLS tenant policies and the
   V3 customer APIs gate writes by `is_org_member()` / `require_org_member()`
   — i.e. **owner, admin, member and viewer all receive identical write
   capability** for uploads, calculations, report generation, exports, and the
   customer-side processing pipeline (including customer approval). The four
   org roles only diverge at the organisation-administration layer
   (`require_org_admin`: members, facilities, suppliers, profile, invitations)
   and at `organization_members` RLS. A role named `viewer` that can upload,
   calculate, export and approve is a role-model/authorization discrepancy the
   UI also fails to communicate.

3. **The customer-side processing pipeline (`/api/v3/processing/items/*`) is
   open to every org member and has no UI at all.** Any member — including a
   viewer — can start/extract/map/validate/calculate/approve items through the
   API, bypassing CarbonTally's internal operator pipeline. None of those
   operations is surfaced in the customer frontend, and the "customer final
   approval" workflow (Product Owner decision) exists **only as an API** — no
   screen lets a customer approve or reject a processed item.

4. **Custom Emission Factors are backend-only.** `customer_factors` (table,
   RLS, ~7 API routes, approval/deactivation, calculation integration) is
   complete server-side, but there is **zero frontend**: no list, create,
   edit, approve or usage screen, and no entry in the V3 navigation. A
   capability that the Product Owner says already exists is invisible to every
   role.

5. **Legacy and dead surfaces remain in the build.** The legacy customer
   dashboard (`/dashboard/*`) is redirected to `/home` but its ~1,600-line
   `Dashboard` component and its components (UploadManager, TeamManagement,
   AssetManager, ManualEntryStandalone, ChatWidget, BulkUpload, …) are still
   imported and bundled; `App copy.js`, `App copy.css`, `App_.js`, `main
   copy.py` and several `* copy.*` files remain in the tree; the marketing
   landing page still advertises "Limited Beta Access"; `/beta/signup` and
   `/beta-login` remain. A `/privacy` route is shadowed by a second
   `/privacy` route that renders the **PricingPage** (routing bug).

6. **Design system is split across five V3 CSS files plus the 3,491-line
   legacy `App.css`**, with hard-coded colors repeated and no design tokens.
   The authenticated experience is visually consistent at the macro level
   (V3 shell), but component vocabulary, status colours, form patterns and
   spacing diverge between `v3.css`, `admin.css`, `ops.css`, `consultant.css`
   and `reports.css`.

7. **Legacy name-string authorization guards remain mounted** (`require_role(["admin","staff"])`
   in `routes/customer_documents.py`, `routes/notifications.py`, `routes/logs.py`,
   `routes/documents_main.py`, `routes/glossary.py`, …). The D20
   scope-first fixes make Processing-Entity staff structurally unable to pass
   them and scope `is_admin` to internal staff, so the risk is **latent**, not
   exploitable today. It remains a hardening item (role names are not the
   permission model; `staff_roles.permissions` is).

**Overall verdict.** The V3 platform is architecturally sound and its UI is
honest (real data everywhere). It is not yet a *role-coherent* product: the
role model is enforced at the organisation-administration boundary only, the
Processing Entity document-viewing workflow is broken end-to-end, and several
"existing" capabilities (custom factors, customer approval, factor catalogue)
have no user-facing surface. The recommended sequencing is in §24.

---

## 2. Current Platform Architecture

### 2.1 Stack

| Layer | Technology / layout |
|---|---|
| Frontend | React (CRA) single page, `frontend/src/App.js` routes. V3 surface in `frontend/src/v3/**`; legacy dashboard components still in the bundle. |
| Backend | Python FastAPI, single composition root `backend/main.py` mounting the legacy `routes/**` routers **and** the V3 `api/router.py` router (all under `/api`). |
| Database | PostgreSQL (Supabase). Schema migrations under `supabase/migrations/` (31 files). RLS deny-by-default; org, consultant, entity and staff access axes. |
| Storage | Supabase Storage bucket `documents`, **private** since D32; only short-lived signed URLs are issued server-side. |
| Auth | Supabase Auth (JWT). `backend/auth.py` resolves the caller into an `AuthUser` (staff profile / org membership / role + permissions). |

### 2.2 Route map (authenticated areas)

Frontend routes (`frontend/src/App.js`) and their guards:

| Route | Screen | Guard (frontend) | Backend area |
|---|---|---|---|
| `/home` | V3 customer Dashboard | `RoleRoute requireOrg` | `/api/v3/reporting/*`, `/api/v3/organizations/*` |
| `/emissions` | Emissions & calculations + evidence | `requireOrg` | `/api/v3/emissions/*` |
| `/documents` | Documents + uploads + reverse lookup | `requireOrg` | `/api/v3/uploads`, `/api/v3/documents/*` |
| `/processing` | Processing batches/items (customer) | `requireOrg` | `/api/v3/manual-extraction/*` |
| `/existing-data` | D19/D35 data discovery/adoption | `requireOrg` | `/api/v3/discovery/*` |
| `/issues` | Customer issues | `requireOrg` | `/api/v3/issues/*` |
| `/messaging` | Customer↔consultant messages | `requireOrg` | `/api/v3/messaging/*` |
| `/reports`, `/reports/:id` | Reports + detail | `requireOrg` | `/api/v3/reports/*` |
| `/billing` | Billing / plans / credits / orders | `requireOrg` | `/api/v3/billing/*` |
| `/organization` | Org administration (profile/members/suppliers/facilities/security) | `requireOrg` | `/api/v3/organizations/*` |
| `/consultant` | Consultant multi-client hub | `RoleRoute requireConsultant` | `/api/v3/consultants/*`, `/api/v3/whitelabel/*` |
| `/ops` | Internal Operations hub (renders the Entity workspace for entity staff) | `RoleRoute requireStaff` | `/api/v3/ops/*`, `/api/v3/qc/*`, `/api/v3/review/*` |
| `/notifications` | Per-user notifications | auth | `/api/v3/notifications/*` |
| `/dashboard/*` | Legacy dashboard → **redirected to `/home`** | — | — |
| `/beta/signup`, `/beta-login`, `/signup`, `/onboarding` | Signup / onboarding | public / auth | Supabase Auth + `/api/v3/organizations` |

### 2.3 Key architectural properties relevant to this audit

- **One account, one primary organisation.** `get_current_user` resolves the
  org via `.maybe_single()`; the V3 shell resolves the primary org through
  `resolveV3Organization()` (`/api/organizations/members/user/{id}`).
  Multiple membership rows are possible in the schema, but no org-switcher
  exists in the UI (documented "NOT IMPLEMENTED as a surface").
- **Staff authorization chain** (`operations_auth.py`): active `staff_profiles`
  → `staff_roles.permissions` (jsonb) → scope (`entity_id IS NULL` = internal;
  populated = Processing Entity staff). Every `/api/v3/ops/*` endpoint
  re-authorizes the entity/batch/item it touches.
- **Consultant chain** (`consultant_auth.py`): active consultant profile →
  active firm membership → **active** client grant (`consultant_clients.status='active'`,
  D15/D19). No global consultant access.
- **Processing Entity chain** (`operations_auth.py`): `require_entity_scope`
  (own entity only), `ensure_entity_batch_access`, `_entity_workspace_guard`
  (own entity + `can_process` + entity `status='active'`), plus entity RLS
  storeys.
- **Documents are private** (D32): `storage.objects` RLS org-member-only;
  signed URLs issued only by org-member-gated endpoints or by the signed
  internal workspace; entity extraction endpoints return **unsigned** paths.
- **Billing writes are server-only** (D37-0): table-level `REVOKE
  INSERT/UPDATE/DELETE … FROM authenticated` on `organizations`,
  `usage_tracking`, `customer_subscriptions`, `consultant_billing`.

---

## 3. Role Model (as implemented)

Source of truth: schema CHECK constraints + `auth.py`/`operations_auth.py`/
`consultant_auth.py` + RLS migrations.

| Actor | Representation | Write authority today (V3) | Notes |
|---|---|---|---|
| Org **owner** | `organization_members.role='owner'` | org admin authority + all member writes | `require_org_admin` includes owner; no owner-only API distinction found beyond membership semantics |
| Org **admin** | `organization_members.role='admin'` | org admin authority + all member writes | `require_org_admin` includes admin |
| Org **member** | `organization_members.role='member'` | all org member writes | uploads, calculations, reports, exports, processing items, issues, messaging |
| Org **viewer** | `organization_members.role='viewer'` | **identical member write authority** | no read-only enforcement in V3 customer APIs or RLS tenant policies |
| **Consultant** (firm owner/manager/consultant/viewer) | `consultant_firm_members` + `consultant_clients` | read client org data via active grants; manage clients/team via `can_manage_*` flags | no org membership |
| **Operator** | `staff_profiles` + `staff_roles` `can_process` | extract/map/calculate on assigned/internal batches | internal staff only |
| **Reviewer** | `staff_roles` `can_review` | validate, review queue actions | internal staff; entity staff limited to own-entity review rows |
| **QC** | `staff_roles` `can_process`+`can_review` (named `qc_specialist`) | QC pass/fail via `/api/v3/ops/items/{id}/qc` and `/api/v3/qc/*` | |
| **Staff Admin** | `staff_roles.name='admin'` (internal) | staff CRUD, entity CRUD, SLA, commercial, ops-wide dashboards | `is_admin` is internal-staff-scoped (D20) |
| **Processing Entity staff** | `staff_profiles.entity_id IS NOT NULL` | only own-entity extraction workspace, own-entity review/issues | cannot access org surfaces; cannot obtain signed document URLs |

### 3.1 Role model discrepancies (summary)

1. **`viewer` is not read-only** (see finding A-1).
2. **Owner vs Admin are indistinguishable** in the current codebase — both are
   "org admin". No owner-only capabilities exist (e.g. transfer of ownership,
   owner-only approval, owner-only billing). This is fine operationally but
   should be stated; the UI calls the tab "Organization administration".
3. **Customer processing pipeline has no role gate** (see finding A-2).
4. **Consultant sub-roles** (owner/manager/consultant/viewer in the firm) map
   to `can_manage_clients` / `can_manage_team` / `can_upload_documents` /
   `can_generate_reports` flags; the V3 consultant UI only uses
   `can_manage_clients` today.

---

## 4. Customer Organisation UX (Owner / Admin / Member / Viewer)

### 4.1 What exists

V3 customer screens: Dashboard (`/home`), Emissions (`/emissions`), Documents
(`/documents`), Processing (`/processing`), Existing data (`/existing-data`),
Issues (`/issues`), Messages (`/messaging`), Reports (`/reports`), Billing
(`/billing`), Organization (`/organization`), Notifications.

All are `RoleRoute requireOrg`-gated: **any** org member (owner, admin, member,
viewer) can navigate to all of them. There is no per-role navigation
differentiation in the V3 shell.

### 4.2 Owner vs Admin

**What the code does:** `require_org_admin()` accepts `owner` and `admin`
identically. The owner role is stored in `organization_members.role` and
`AuthUser.role='org_owner'`, but no V3 endpoint distinguishes owner from
admin. The "Security" tab (MFA/TOTP) is per-user. There is no ownership
transfer UI, no "leave organisation", no billing-management distinction, and
no owner-only approval step.

**UI/UX finding O-1 — Owner has no distinct experience.**
- FINDING: The Owner role has no owner-only capabilities or UI.
- EVIDENCE: `require_org_admin` (backend/auth.py) treats `owner` and `admin`
  identically; no owner-specific routes in `backend/api/*`; MembersTab offers
  the same role dropdown to all four roles.
- CURRENT UI: A single "Organization administration" hub for everyone.
- BACKEND/API/RLS EVIDENCE: `om_update_admin`/`om_insert_admin` policies use
  `role IN ('owner','admin')`; V3 member routes use `require_org_admin`.
- PRODUCT IMPACT: No way to transfer ownership, no separation of "the person
  accountable" from "people who can administer".
- UX IMPACT: Low today, but ownership semantics are invisible.
- SECURITY IMPACT: none (owner and admin have identical privileges).
- RECOMMENDATION: Decide whether owner is a distinct privilege tier. Minimum:
  owner-only "transfer ownership" and owner can remove admins; document the
  tier in the Role matrix.
- PRIORITY: P2.

### 4.3 Admin vs Member

**What the code does:** Admin (and owner) can manage members, invitations,
profile/metadata, facilities, assets, suppliers, and approve customer factors
(backend). Members can upload, calculate, export, generate reports, and
operate the processing pipeline.

**UI/UX finding O-2 — Administration controls are rendered for non-admins.**
- FINDING: The `/organization` route is `requireOrg`, and `MembersTab`
  renders the role `<select>`, "Remove", "Add member" (raw user-id input) and
  invitation controls for **every** member including viewers. Non-admins only
  discover they cannot act when the API returns 403 (surfaced as a generic
  error banner).
- EVIDENCE: `frontend/src/App.js` route `/organization` (requireOrg only);
  `frontend/src/v3/admin/MembersTab.jsx` renders role dropdown + Remove + Add
  member without any `role` gate; `backend/api/v3_organizations.py`
  `add_member`/`update_member`/`remove_member` are `require_org_admin()`.
  Related: `list_members` is `require_org_member` only, so any member/viewer
  can read the full roster (member emails, user ids, roles) via the API even
  though RLS (`om_select_self_or_admin`) would only allow self/admin rows —
  the service-role API surface is broader than the direct-RLS surface.
- CURRENT UI: A viewer opening "Organization → Members" sees every
  management control and gets 403s when clicking.
- BACKEND/API/RLS EVIDENCE: `require_org_admin()` on the mutating endpoints;
  RLS `om_insert_admin`/`om_update_admin` admin-gated.
- PRODUCT IMPACT: Role-coherence failure; members cannot tell what they may do
  and receive confusing error states.
- UX IMPACT: Medium — controls should be disabled/hidden for member/viewer.
- SECURITY IMPACT: None (API enforces) — a UI-only issue, explicitly not an
  authorization gap.
- RECOMMENDATION: Pass the caller's org role into the page (it is already
  returned by `resolveV3Organization` / `/api/organizations/members/user/{id}`)
  and gate tabs and controls by `owner|admin`. Also replace the raw "user id"
  add-member input with an email invite flow (invitations already exist).
- PRIORITY: P1.

### 4.4 Member vs Viewer

**What the code does:** identical. Both can upload documents, calculate
emissions, generate reports, export, operate processing items, open issues
and approve items.

**UI/UX finding A-1 — `viewer` is functionally a writer.**
- FINDING: The Viewer role cannot be described as read-only anywhere in the
  implementation. RLS tenant INSERT/UPDATE/DELETE policies and the V3 customer
  API both key on "active org member", not on role.
- EVIDENCE: `supabase/migrations/20260803000000_rc2_rls.sql` §3 tenant policy
  loop: INSERT `WITH CHECK (is_org_member(organization_id))`, UPDATE/DELETE
  `USING (is_org_member(...))` — no role predicate. `require_org_member()` is
  the only gate on `/api/v3/uploads`, `/api/v3/emissions/calculate`,
  `/api/v3/reports` (POST generate), `/api/v3/exports/*`,
  `/api/v3/processing/items/*` (including `/customer-review`).
- CURRENT UI: A viewer sees "Upload document", "Record / calculate emissions",
  "Generate a report", "Export emissions CSV", "Report an issue".
- BACKEND/API/RLS EVIDENCE: as above.
- PRODUCT IMPACT: If Viewer is intended to be read-only, the whole org write
  surface must be role-gated. If Viewer is intended to be a "working but
  non-admin" role, it must be renamed or documented.
- UX IMPACT: High — the role name promises read-only; the product grants
  write.
- SECURITY IMPACT: Medium — no cross-org leak, but a stated read-only role
  with write authority is an authorization-model discrepancy (a compliance
  risk for "who could edit emissions data").
- RECOMMENDATION: Decide the Viewer contract; then gate writes either at the
  API (`require_org_member` → `require_org_editor` for mutating endpoints) or
  by declaring viewer = editor-without-admin. Add role-based nav/controls.
- PRIORITY: P1 (P0 if Viewer is contractually read-only).

### 4.5 Customer capabilities missing from the UI

| Capability (backend has it) | Customer UI | Status |
|---|---|---|
| Item workspace (`/api/v3/processing/items/{id}/workspace`) | not rendered anywhere in `/processing` | Missing (F-1) |
| Customer approval/rejection (`/customer-review`) | no screen | Missing (A-2) |
| Custom emission factors (list/create/edit/approve) | none | Missing (F-3) |
| Factor catalogue (DEFRA/SEAI browse) | none | Missing (F-4) |
| Document preview (`/documents/{id}/signed-url`) | only "Emissions from this document" | Missing viewer |
| Report PDF download (`/reports/{id}/pdf`) | only JSON download | Missing |

### 4.6 Customer screens audit highlights

| Screen | Strengths | Issues |
|---|---|---|
| Dashboard | real stats, empty states, trend chart | "Documents"/"Members"/"Emissions rows" are count cards with no drill-through intent labels; per-member activity table is admin-ish data shown to all members |
| Documents | upload + reverse evidence lookup | no document preview; "Data type" select is freeform; no role gate on upload |
| Processing | lists batches/items | "Add item" form accepts an arbitrary **File URL** string and is shown to all members; "Create batch" state/handler is dead code (never rendered); no extraction/mapping/factor/evidence view; no approval |
| Emissions | authoritative calculate + evidence record panel | manual single-row calculator only; no bulk/CSV; factor provenance shown as raw `factor_source` |
| Issues | create + filter + detail | customers cannot reply to or comment on issues (acknowledged in code comment) |
| Reports | filters, status badges, generation modal, JSON download | PDF download endpoint unused; no report *content* review before download (detail page is separate) |
| Billing | plan/mode/credits/orders/assisted/managed | rich; sits under `/billing` for all members incl. viewer |
| Organization | tabs for profile/members/suppliers/facilities/security | role-gating issue O-2; no "Custom factors" tab despite backend |

---

## 5. Consultant UX

**What exists** (`frontend/src/v3/consultant/ConsultantPage.jsx`): consultant
dashboard (client count, portfolio health), explicit **active-client
switcher** with a persistent banner ("You are working on: X — every action
here applies to this client only"), client workspace (processing status,
reports, issues, emissions), firm branding, white-label configuration and
client messaging. Client lifecycle actions (suspend/end/reactivate/deactivate)
are gated on `can_manage_clients` in the UI **and** the backend.

**What the code enforces** (`consultant_auth.py`): active profile → active
firm membership → **active** `consultant_clients` grant; every client-id is
re-authorized server-side. D15/D19 active-grant lifecycle is real.

**Coherence with Customer Organisation experience:**
- Consultants see processing *status* and *reports* per client, but no
  extraction workspace, no mapping, no item-level evidence and no custom
  factors UI (though RLS permits consultants to read `customer_factors`
  via `is_org_consultant`, no UI consumes it).
- The consultant client workspace is **read/status-oriented**; there is no
  consultant "do work on this client's items" surface. If consultants are
  expected to perform extraction/review for clients (business decision R3
  permits factor access), this is missing.

**UI/UX findings C-1:**
- FINDING: Consultant view of clients is mostly aggregate status; the
  per-client workspace does not surface documents, extraction items or
  evidence, and cannot open the client organisation's Processing page.
- EVIDENCE: `ConsultantPage.jsx` `ClientWorkspace` calls
  `getClientReports/getClientDashboard/getClientProcessingStatus/getClientIssues`
  only; no document/extraction/evidence endpoints are called.
- CURRENT UI: Cards + stage table + report table.
- BACKEND/API/RLS EVIDENCE: `v3_consultants.py` exposes reporting/status
  aggregates; no client-side processing workspace endpoints.
- PRODUCT IMPACT: Consultants cannot perform or verify client work in-product.
- UX IMPACT: Medium.
- RECOMMENDATION: Decide the consultant operating model: if consultants are
  to perform/verify processing, expose the item workspace (org-scoped) under
  the active client. Otherwise, explicitly document consultants as
  status/report-only.
- PRIORITY: P2.

---

## 6. CarbonTally Internal Operations UX

### 6.1 The hub

`/ops` (`OperationsPage.jsx`) is gated by `RoleRoute requireStaff`. Internal
staff see BASE_TABS: **Dashboard, Data entry, Review, QC, Staff, Roles** and,
when `can_manage_staff`, **Entities, SLA**; when `can_manage_billing`,
**Commercial**. Processing-Entity staff bypass the hub entirely and land on
`EntityExtractionWorkspace`.

**UI/UX finding O-3 — Ops tabs are not permission-filtered.**
- FINDING: BASE_TABS are shown to every internal staff role. An operator
  (`can_process` only) sees Review, QC, Staff and Roles tabs whose endpoints
  will 403 (review/QC need `can_review`; staff/roles need `can_manage_staff`),
  producing error banners instead of hidden tabs.
- EVIDENCE: `OperationsPage.jsx` computes `TABS` from `canManageStaff` only;
  `ReviewQueue.jsx` calls `/api/v3/ops/queues/review` (needs `can_review`);
  `StaffRoster.jsx` calls `/api/v3/ops/staff` (needs `can_manage_staff`).
- CURRENT UI: Permissions appear broken when tabs 403.
- BACKEND/API/RLS EVIDENCE: `ensure_staff_permission(context, "can_review")`
  etc. in `v3_operations.py`.
- RECOMMENDATION: Filter tabs by the real permission set returned by
  `getOpsMe()` (`permissions` object).
- PRIORITY: P1.

### 6.2 Operator

- Queue: `/api/v3/ops/queues/operator` (internal only, `can_process`).
- Workspace: `OperatorQueue.jsx` + `ExtractionPanel` (document viewer,
  multi-line extraction, factor picker, save/draft/calculate).
- **Critical defect:** the document viewer is broken (finding E-1) because
  `OperatorQueue` loads items via `/api/v3/ops/batches/{batch_id}/items`
  (unsigned `file_url`), not via the signing workspace endpoint.
- Assign control gated by `can_manage_staff && can_process` (correct), with
  operator-vs-entity radio, reason field, and audit trail — good.

### 6.3 Reviewer / QC

- `ReviewQueue.jsx` and `QcQueue.jsx` use `WorkItemWorkspace` →
  `/api/v3/ops/items/{item_id}/workspace` (**signed** source URL), and render
  the source as **raw JSON** (`JSON.stringify(workspace.source)`) — a
  functional but low-fidelity viewer.
- QC pass/fail with quality score + notes; QC reporting incl. processor
  performance (internal vs entity) — good.

**UI/UX finding O-4 — Review/QC "document viewer" is a JSON dump.**
- FINDING: `WorkItemWorkspace` shows `<pre>{JSON.stringify(workspace.source)}</pre>`
  rather than rendering the document.
- EVIDENCE: `frontend/src/v3/ops/WorkItemWorkspace.jsx`.
- RECOMMENDATION: reuse `ExtractionPanel`'s iframe viewer (with the signing
  fix, finding E-1) for review/QC too.
- PRIORITY: P2.

### 6.4 Staff Admin

- Staff roster (create/update profile incl. entity assignment), staff roles
  catalogue, Processing Entities provisioning, SLA settings, Commercial tab
  (subscriptions/orders/credits/storage). Backend-enforced
  (`can_manage_staff`, `can_manage_billing`).
- **Missing:** no dedicated issues triage surface for entity clarification
  issues (finding I-1).

---

## 7. External Processing Entity UX

### 7.1 What the PO decision requires (preserved)

External/manual Processing Entities must **not** download customer documents;
they perform extraction, mapping and validation **through the CarbonTally
portal**; CarbonTally mediates all communication; entity staff are scoped to
assigned work only.

### 7.2 What the code does

**Assignment** — `manual_extraction_batches.entity_id` (D22); exactly one
processing party (entity XOR internal operator); assignment audited in
`audit_trail`. Internal staff with `can_manage_staff`+`can_process` assign via
the Data entry queue.

**Access boundary** — `require_entity_scope` (own entity only) +
`_entity_workspace_guard` (own entity + `can_process` + entity `active`) +
`ensure_entity_batch_access` (batch must be assigned to that entity) on every
`/api/v3/ops/entities/{id}/extraction/*` route. RLS entity storeys on
`manual_extraction_batches/items` (`*_entity_select`) and on
`manual_review_queue`, `issues`, `staff_profiles`, `processing_entities`,
`upload_batches`. Entity staff are not org members and cannot pass any
`require_org_member()` gate.

**Document download controls — verified enforcement.**

| Layer | Mechanism | Entity staff result |
|---|---|---|
| Storage RLS | `storage.objects` policies `d32_documents_select/insert/update/delete_org_member` (path `uploads/<org_id>/…` + org membership) | SELECT denied |
| API signed URLs | `/api/v3/documents/{id}/signed-url` = `require_org_member()` + `ensure_org_access` | 403 |
| Entity extraction API | returns **raw** (unsigned) `file_url` storage paths; never calls `storage_signed_url` | no usable URL issued |
| Internal workspace API | `/api/v3/ops/items/{item_id}/workspace` signs via `signed_item` **but** rejects entity staff (`_get_item_and_batch` → 403 "Processing-entity staff cannot use the internal extraction pipeline") | 403 |
| Direct browser storage client | anon key + RLS (org member only) | no rows |

**VERDICT: The Product Owner decision "External/manual Processing Entities
must not download Customer documents" IS enforced by the current code. No
security/architecture gap exists on this specific decision.** The raw storage
path (`uploads/<org-uuid>/…`) is exposed to entity staff in item payloads; it
is not usable to fetch the object (private bucket, RLS), but it does reveal
the organisation UUID and storage layout — a minor information-disclosure note
(S-2).

### 7.3 The portal workflow is currently broken for entities

**Finding E-1 — The Processing-Entity (and internal-operator) document viewer
is broken, so extraction through the portal is impossible today.**
- FINDING: `ExtractionPanel` renders `<iframe src={item.file_url}>`. Entity
  workspace endpoints (`entity_extraction_item_workspace`,
  `entity_extraction_batch_items`, `entity_extraction_next_item`) return raw
  `file_url` = storage path (`uploads/<org>/…`), not a signed URL. The same
  applies to the internal operator surface (`/api/v3/ops/batches/{batch_id}/items`).
  Only `/api/v3/ops/items/{id}/workspace` (Review/QC) signs.
- EVIDENCE: `backend/api/v3_operations.py` (entity endpoints return
  `{"item": item}` raw; `ops_batch_items` returns raw `list_items`);
  `backend/data/manual_extraction.py` `list_items` maps `file_url` raw;
  `frontend/src/v3/ops/ExtractionPanel.jsx` `<iframe src={item.file_url}>`;
  `frontend/src/v3/ops/OperatorQueue.jsx`/`EntityExtractionWorkspace.jsx` feed
  raw items to the panel.
- CURRENT UI: A blank/broken iframe titled by file name in the extraction
  workspace; operators and entity staff cannot see the source document.
- BACKEND/API/RLS EVIDENCE: only `services/storage.signed_item` signs, and it
  is called only in `item_workspace` (both ops-internal and
  processing-workflow) and `v3_documents` upload metadata.
- PRODUCT IMPACT: Contradicts PO decision "Processing Entities perform
  extraction/mapping/validation through the CarbonTally portal" — the portal
  cannot display the document to extract from. Also breaks internal operators.
- UX IMPACT: Critical for the core workflow.
- SECURITY IMPACT: None (the break is caused by *over-restriction*, not a
  leak).
- RECOMMENDATION: Issue a **view-only** signed URL to entity staff scoped to
  assigned items (server-side check: item's batch `entity_id` == caller
  `entity_id`; 60s expiry). Rendering a signed URL in a `sandbox` iframe is
  the standard pattern. If PO wants stronger guarantees (no download at all),
  consider an image/page rasterization proxy; but note that a browser view
  always permits screenshots — the PO decision should be interpreted as "no
  direct download/export", not "no view". Until then the entity workflow
  cannot operate end-to-end.
- PRIORITY: **P1** (blocking the ratified entity operating model).

**Finding I-1 — Mediated clarification has no triage UI.**
- FINDING: Entity staff can open a clarification issue
  (`/entities/{id}/extraction/items/{item_id}/clarify`), but no ops tab lists
  entity issues for CarbonTally staff to triage, and the customer Issues page
  deliberately excludes entity-scoped issues.
- EVIDENCE: `v3_operations.py` `entity_extraction_clarify` creates an
  entity-scoped issue; `OperationsPage.jsx` BASE_TABS has no Issues tab;
  `IssuesPage.jsx` reads `/api/v3/issues` which excludes `entity_id` rows;
  `issues.py` `/admin/open` endpoint exists but no UI calls it.
- RECOMMENDATION: Add an ops "Issues" tab (internal staff) listing
  org+entity issues with a mediated reply action. PRIORITY: P1 (the
  clarification boundary exists in code but is dead-end for users).

**Finding I-2 — Entity dashboard is not reachable from the entity UI.**
- FINDING: `getEntityDashboard` is fetched but only the extraction summary is
  shown; review-queue and issues blocks of the dashboard response are not
  rendered in `EntityExtractionWorkspace`.
- EVIDENCE: `EntityExtractionWorkspace.jsx` uses only `dashboard.extraction`
  and performance; `entity_dashboard` returns review_queue/issues too.
- PRIORITY: P3.

---

## 8. End-to-End Processing Work UX

Traced lifecycle vs UI/API coverage:

| Step | Who performs (code) | API | UI | Notes |
|---|---|---|---|---|
| Upload source doc | org member | `POST /api/v3/uploads` | Documents | auto-enqueues extraction item (D23) |
| Batch lifecycle | org admin | `POST /api/v3/manual-extraction/batches`, `/api/v3/processing/batches/{id}/start\|complete\|cancel` | Processing (no batch-create UI) | "Create batch" handler dead in UI |
| Assign work | internal staff (`can_manage_staff`+`can_process`) | `POST /api/v3/ops/batches/{id}/assign` | Data entry → Assign | operator XOR entity, audited |
| Extract / map / calculate | internal operator **or entity staff** | `/api/v3/ops/items/*` + `/api/v3/ops/entities/{id}/extraction/items/*` | Data entry / Entity workspace | **document viewer broken (E-1)** |
| Validation | internal (ops `/validate`) | `/api/v3/ops/items/{id}/validate` | Review tab | findings → issues |
| Review | internal reviewer / entity staff (own rows) | `/api/v3/ops/queues/review`, `/review/{id}/complete` | Review tab | WorkItemWorkspace JSON view |
| QC | internal (`can_review`) | `/api/v3/ops/items/{id}/qc`, `/api/v3/qc/*` | QC tab | quality score + notes |
| Customer review/approval | any org member (API) | `POST /api/v3/processing/items/{id}/customer-review` | **no UI** | A-2 |
| Evidence | org member | `GET /api/v3/emissions/{log_id}/evidence` | Emissions → Evidence | good record panel |
| Reports | org member | `POST /api/v3/reports` | Reports | JSON only |

**Finding A-2 — Customer final approval exists only as an API.**
- FINDING: PO decision #10 ("Customer final approval is part of the
  workflow") is implemented server-side but has no customer screen; and the
  endpoint that does it is open to all org members, not just owners/admins.
- EVIDENCE: `backend/api/v3_processing_workflow.py` `customer_review_item`
  (`require_org_member`); `grep -rn "customer-review" frontend/src` → no
  frontend usage; `ProcessingPage.jsx` renders no approval UI.
- RECOMMENDATION: Build a customer "Review & approve" screen (list items in
  `customer_review` stage → approve/reject with reason) gated to
  Owner/Admin, and re-gate the API to `require_org_admin`.
- PRIORITY: **P1** (ratified workflow invisible).

**Finding A-3 — Customer members can operate the extraction pipeline.**
- FINDING: `/api/v3/processing/items/*` (start/extract/map/validate/calculate/
  customer-review) is `require_org_member` — any customer role can act as an
  operator or reviewer on their own org's items, bypassing the CarbonTally
  internal control chain that `operations_auth` carefully builds.
- EVIDENCE: `v3_processing_workflow.py` uses `require_org_member` for
  `start_item`, `extract_item`, `map_item`, `validate_item`, `calculate_item`,
  `customer_review_item`.
- IMPACT: role-model incoherence; if the intended model is "customers consume
  CarbonTally processing, they do not operate it", these endpoints should be
  internal-only or gated to a deliberate "self-service operator" role.
- RECOMMENDATION: Re-scope: either (a) gate to `require_org_admin` and expose
  only `customer-review` + status read to customers; or (b) explicitly design
  a "self-service extraction" mode with its own permissions. Align the UI
  accordingly.
- PRIORITY: **P1** (authorization-model decision) — **P0** if customer
  self-service extraction is not intended.

---

## 9. Document Processing UX

- Upload supports PDF/IMAGE/SPREADSHEET (`_classify` in `v3_documents.py`);
  PDF page count computed; each upload auto-creates an extraction item (D23).
- **UI does not separate the document-processing layers** the way the backend
  does. The customer Processing page shows batches + item rows (file name /
  status / type) but never the extraction data, mapping, factor, calculation
  or evidence for an item; the only evidence access is from the Emissions
  page (per emission row) and the Documents page (reverse lookup).
- Traceability chain "source → extracted record → mapped activity → factor →
  calculation → validation → evidence → result" is **not rendered as a chain
  anywhere in the customer UI**; it exists atomically (evidence record) and
  in reverse (document → emissions). Finding T-1 (§14).

---

## 10. CSV/Excel Mapping UX

- **There is no live CSV/Excel mapping workflow in the authenticated V3
  platform.** CSV/Excel uploads are classified as SPREADSHEET documents and
  become manual-extraction items like any other file; extraction is manual,
  line-by-line, in `ExtractionPanel` (no column-header mapping, no unit
  normalization helper, no template matching).
- The rich CSV mapping UX that once existed lives in the **legacy** dashboard
  components (`BulkUpload.jsx`, `UploadManager.js`, `ManualEntryStandalone`),
  which are unreachable because `/dashboard/*` redirects to `/home`.
- **Finding M-1 — CSV/Excel mapping capability is either dead or manual-only.**
  - EVIDENCE: `frontend/src/BulkUpload.jsx`/`UploadManager.js` not routed
    (only inside legacy `Dashboard` in `App.js`, shadowed by the
    `/dashboard/*` redirect); `ExtractionPanel` has no CSV parsing.
  - RECOMMENDATION: Decide whether spreadsheet ingestion is a product
    capability. If yes, build a V3 "spreadsheet mapping" screen (upload →
    preview rows → column mapping → unit normalization → line items →
    mapping → calculate). If no, remove the dead components.
  - PRIORITY: P2 (capability), P3 (cleanup).

---

## 11. Emission Factor UX

- Factors are surfaced in exactly two places: the **factor picker** in the
  extraction/mapping `ExtractionPanel` (label
  `{activity_type} · {unit} · {factor_source} {reporting_year}`) and the
  **auto-match result** in `EmissionsPage` (shows `factor_source`/`factor_id`
  as raw text). DEFRA vs SEAI/country/unit/scope are not browsable; there is
  no factor catalogue screen anywhere (customer, consultant, or ops).
- **Finding F-4 — No factor catalogue / provenance browsing UI.**
  - The backend has factor search (`find_by_activity`, `emission_factors`
    authenticated-read RLS) and snapshot provenance, but no UI to explore
    factors, compare providers, or verify the factor behind a result beyond a
    raw `factor_source` string.
  - RECOMMENDATION: Add a read-only "Emission factors" screen (searchable,
    provider filter DEFRA/SEAI/custom, country/year/unit/scope columns,
    "used in N calculations" link to snapshots) for customers/consultants; a
    richer admin version for internal staff.
  - PRIORITY: P2.

---

## 12. Custom Emission Factor UX

**Finding F-3 — Customer Custom Emission Factors are invisible in the UI.**
- FINDING: Full backend exists (table `customer_factors`, RLS org-member +
  consultant-select, `customer_factors.py` API: list/get/create/update/approve
  (org admin)/deactivate; calculation integration with approved-customer-first
  precedence; snapshot provenance `factor_source='CUSTOMER'`). **Zero
  frontend**: no API client functions in `frontend/src/v3/api.js`, no page, no
  nav item.
- EVIDENCE: `grep -rn "customer-factors" frontend/src` → no matches;
  `backend/api/customer_factors.py` routes present; ADR-V3-002 "Frontend:
  customer-factor management UI (later phase)".
- PRODUCT IMPACT: PO decision #6 says custom factors already exist — they
  exist as data/API but are unusable by customers; the DRAFT→ACTIVE→ARCHIVED
  lifecycle, org-admin approval and usage in calculations cannot be exercised.
- RECOMMENDATION: Build a customer "Emission factors" tab (in `/organization`
  or `/emissions`): list (DRAFT/ACTIVE/ARCHIVED), create/edit with validation
  (value ≥ 0, unit, scope, reporting year, source reference), admin approve,
  usage/traceability links. Ensure the factor picker in extraction shows
  approved custom factors (backend precedence already does).
- PRIORITY: **P1** (existing capability unusable).

---

## 13. Validation / Review / QC UX

- **Internal**: Review and QC tabs work off real queues; validation findings
  become issues; QC has pass/fail + quality score + notes; reporting (aging,
  SLA, processor performance) is strong.
- **Customer**: none of this is visible. Customers see item status strings
  (e.g. `validated`, `qc_approved`) in the Processing table with no meaning,
  no definition, and no path to act.
- **Finding V-1 — Validation/QC status vocabulary is raw for customers.**
  - The Processing page prints raw status values; there is no legend,
  localized label, or "what happens next" guidance. Combined with A-2 (no
  approval UI), customers cannot act on or interpret their processing status.
  - RECOMMENDATION: status badge component with labels + step indicator
  (Source → Extracted → Mapped → Calculated → Validated → QC → Customer
  review → Approved), per item; add the customer-review action screen.
  - PRIORITY: P1.

---

## 14. Evidence / Traceability UX

- **Good**: `EvidenceRecordPanel.jsx` renders the D33.1 evidence record
  (SOURCE DOCUMENT / ORIGINAL EXTRACTED DATA / CARBONTALLY MAPPING / EMISSION
  FACTOR / CALCULATION / EMISSION RESULT) with completeness badge and
  technical-details expansion; reverse lookup (document → emissions) exists;
  evidence access is audited; exports add `evidence_status`.
- **Finding T-1 — The chain is not navigable as a chain.**
  - The customer can open evidence for a single emission row and can reverse
    lookup from a document, but there is no forward trace from a source
    document → its extraction items → calculations → results, and no
    item-level evidence (a processed item's `extracted_data`/`mapped_data`/
    factor/calculation/QC stamps are not shown anywhere to the customer).
  - `WorkItemWorkspace` (ops) renders source+data as JSON.
  - RECOMMENDATION: add an "item detail / trace" panel to the customer
    Processing page (read-only) exposing the item's extraction/mapping/factor/
    calculation/QC stamps, and make document → items → emissions navigable.
  - PRIORITY: P1 (traceability is a stated product differentiator).

---

## 15. Reports / Exports UX

- Report generation (types, year), status lifecycle, filters, versioning,
  JSON download. Exports CSV/JSON for emissions and documents.
- **Finding R-1 — PDF download exists in the API but not the UI.**
  - `GET /api/v3/reports/{report_id}/pdf` exists; `api.js` has
    `downloadReportPdf`; `ReportsPage.jsx` only calls JSON `downloadReport`.
  - RECOMMENDATION: add a PDF download button for completed reports.
  - PRIORITY: P2.
- Export permission is member-level (any member incl. viewer) — consistent
  with A-1.

---

## 16. Navigation / Information Architecture

- V3 shell nav (V3Layout) is role-aware at the **area** level (org vs
  consultant vs ops vs notifications), but not at the **capability** level
  within an area (see O-2, O-3, A-1).
- **Finding N-1 — "Existing data" is a permanent primary nav item for all
  members.** The D19/D35 discovery/adoption flow is an onboarding/administrative
  flow but sits in the main nav between "Messages" and "Billing" for every
  org member, including viewers.
  - RECOMMENDATION: move to `/organization` as a tab or show only during
    onboarding. PRIORITY: P2.
- **Finding N-2 — Navigation labels are inconsistent.**
  - Nav: "Operations" (V3Layout) vs page title "Internal Operations";
    "Processing" (customer) vs "Data entry" (ops) for the same extraction
    concept; "Messages" vs "Client messages"; report status labels differ
    between pages ("Queued" on Reports, raw `pending` on dashboard cards).
  - RECOMMENDATION: adopt the glossary terms end-to-end. PRIORITY: P2.
- No org-switcher (schema permits multi-membership, UI resolves a single
  primary org) — documented as NOT IMPLEMENTED; product should decide if
  multi-org switching is in scope. PRIORITY: P3/decision.

---

## 17. Design System Consistency

- Shared shell (`v3.css`: nav, cards, forms, tables, badges, status dots,
  modals) with five page-level stylesheets (`admin.css`, `ops.css`,
  `consultant.css`, `reports.css`). Classes are reused, but:
  - **No CSS design tokens** (`:root` variables); colors hard-coded
    (e.g. `#2f855a`, `#1a202c`, `#718096`) and repeated across all five files;
    status colors differ between `v3-status` (customer) and `v3-ops-badge`
    (ops) vocabularies.
  - Tables/forms/modal markup duplicated per area; button variants
    (`v3-btn`, `v3-btn-primary`, `v3-btn-danger`, `.primary`, `.danger`)
    mixed.
  - Legacy `App.css` (3,491 lines) still loaded by `index.js` and still
    contains the marketing/legacy dashboard styles — two full visual systems
    ship in one bundle.
- **Finding D-1 — Duplicated/conflicting design systems (legacy + five V3
  files, no tokens).**
  - RECOMMENDATION: consolidate V3 styles into the shared system with tokens;
  remove legacy App.css rules for dead dashboard components; align status
  badge semantics across customer/ops.
  - PRIORITY: P2.

---

## 18. Responsive / Accessibility Review

- Responsive: grid media queries exist (`v3-grid-2` collapses <900px; stat
  grids auto-fit); nav wraps; mobile menu exists only in legacy dashboard
  (dead). Entity/ops tables are not responsive (wide tables on mobile).
- Accessibility:
  - Buttons generally have visible labels; a few `aria-label`s exist.
  - The **legacy inline-style NotificationBell** (in `App.js`) and parts of
    the legacy dashboard rely on inline styles and emoji-only affordances.
  - `ExtractionPanel` line-table uses `<input>`s without labels (placeholder
    only); factor `<select>` has no label.
  - Modal backdrops do not trap focus; no Escape handling in custom modals.
  - Status conveyed by color alone in several badges (e.g. `v3-status` dot)
    without text duplication.
- **Finding A-4 — Accessibility gaps in V3 forms/modals and status badges.**
  - RECOMMENDATION: label form controls, add focus trap/ESC to modals, ensure
    status is not color-only, run axe on the five page families.
  - PRIORITY: P2.

---

## 19. Legacy / Beta UI

Product Owner decision: legacy application/document routes should be removed/
deprecated. Identified (report only — not removed):

| Legacy / dead item | Location | Status |
|---|---|---|
| `/dashboard/*` legacy customer dashboard | `frontend/src/App.js` (Dashboard component ~1,600 lines) | Shadowed by `/dashboard/*` → `/home` redirect; still bundled; still imports UploadManager, TeamManagement, AssetManager, OrganizationMetadata, BulkUpload, ManualEntryStandalone, ChatWidget, etc. |
| Duplicate `/privacy` route | `App.js` — second `/privacy` renders **PricingPage** | Routing bug: `/privacy` shows Pricing |
| `/beta/signup`, `/beta-login`, `BetaLogin.jsx`, `BetaSignup.jsx` | `App.js`, `frontend/src` | Legacy controlled-cohort path; primary is now `/signup` |
| Marketing "Limited Beta Access" banner | `LandingPage.jsx` (isBetaMode, beta-banner, "Join our beta program") | Inconsistent with self-service GA signup |
| Dead copies | `App copy.js`, `App copy.css`, `App_.js`, `LandingPage copy.jsx`, `FileUploadHero copy.jsx`, `CarbonTallyDemo copy.jsx`, `backend/main copy.py`, `backend/main copy 2.py`, `backend/glossary copy.py` | Not served/imported; cleanup candidates |
| Legacy admin routers | `backend/routes/admin/*` (staff, defra, extraction, reviews, assignments, workload, permissions, beta, audit, review_history, admin_bulk, email_templates, admin_analytics, settings) + `backend/routes/…` | Mounted in `main.py` alongside V3; many are name-string-guarded (see S-1) |
| Dormant queue families | `processing_queue`, `processing_assignments`, `reassignment_history` (ADR-V3-016 DEFERRED) | Untouched; documented |

**Finding L-1 — Legacy dashboard and beta entry points remain in the shipped
bundle and marketing site.**
- RECOMMENDATION: after the V3 surface covers the legacy functions, remove the
  legacy Dashboard component, its components, dead copy files, the `/privacy`
  duplicate and the beta banner, and retire the `/beta/*` routes. Controlled
  cleanup (do not remove before V3 parity).
- PRIORITY: P2 (P1 for the `/privacy` routing bug).

---

## 20. Security-Relevant UI Findings

Security findings are distinguished from UI-only findings. For each: layer.

**S-1 (latent) — Legacy name-string authorization remains mounted.**
- FINDING: `require_role(["admin","staff"])` and `require_role(["admin"])`
  guards on mounted legacy routes authorize by `staff_roles.name`, not by
  permission/scope.
- EVIDENCE: `backend/routes/customer_documents.py:1009`,
  `routes/notifications.py:257,341,441,537`, `routes/logs.py:90,204,281,313`,
  `routes/documents_main.py:603`, `routes/glossary.py:310,400,496,560`,
  `routes/organizations/management.py:189…436`; `auth.py require_role` (D20
  rejects entity staff).
- Layer: API (backend). RLS: n/a (service-role reads).
- MITIGATION IN PLACE: D20 — `require_role`/`require_admin`/`is_admin` reject
  Processing-Entity staff regardless of role name; `is_admin` is scoped to
  internal staff. Today only an internal `admin`-named profile passes.
- RISK: if a future profile is mis-provisioned, role names alone remain the
  gate. Harden by requiring `staff_roles.permissions` + internal scope on the
  legacy admin routes, or un-mount them (V3 has equivalents).
- PRIORITY: P1 (hardening; latent today).

**S-2 — Entity work payloads expose organisation UUIDs and storage paths.**
- FINDING: entity staff receive `organization_id` and `file_url`
  (`uploads/<org-uuid>/…`) in assigned-work payloads.
- Layer: API payload. Storage: RLS denies object reads; path not usable.
- IMPACT: information disclosure (low): reveals org UUID and bucket layout,
  not names/contacts. Acceptable work-data scope per §35.3, but the raw path
  should not be returned if not needed — return only file metadata + a
  view-only signed URL (see E-1).
- PRIORITY: P2.

**S-3 (positive verification) — No direct customer write to billing state.**
- D37-0 table-level revokes + dropped policies verified
  (`20260824020000_d37_0…sql`). UI has no billing editing beyond order
  approval. Layer: DB + API. PRIORITY: none (resolved).

**S-4 (positive verification) — Processing-Entity document download is
blocked at three layers** (storage RLS, signed-URL API gate, unsigned entity
payloads). See §7.2. No gap.

**S-5 — `viewer` write authority (see A-1)** — authorization-model finding;
enforcement location: API (`require_org_member`) and RLS tenant policies.
Frontend hides nothing.

**S-6 — `require_org_access` any-staff bypass is dead code but remains.**
- `auth.py` `require_org_access` lets any internal staff pass for any org;
  the Actor Workspace Access Model §35.3 confirms no mounted endpoint uses it.
  Keep it dead or remove it (G2 risk). PRIORITY: P1 (latent).

---

## 21. Role Capability Matrix

Legend: VIEW / CREATE / EDIT / APPROVE / ASSIGN / QC / EXPORT / NONE. Where
the code is ambiguous, **VERIFY** (no guessing).

| Capability | Org Owner | Org Admin | Org Member | Org Viewer | Consultant | CT Operator | Reviewer | QC | Staff Admin | PE Staff |
|---|---|---|---|---|---|---|---|---|---|---|
| View own org/client data | VIEW | VIEW | VIEW | VIEW | VIEW (active grants) | VIEW (assigned) | VIEW (queue) | VIEW | VIEW (all) | VIEW (own entity) |
| Upload documents | CREATE | CREATE | CREATE | **CREATE** (A-1) | **VERIFY** (flag exists; no UI) | NONE | NONE | NONE | NONE | NONE |
| Calculate emissions (manual/items) | CREATE | CREATE | CREATE | **CREATE** (A-1) | NONE | CREATE (assigned items) | EDIT | EDIT | NONE | CREATE (assigned items) |
| Edit org profile/metadata | EDIT | EDIT | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE |
| Manage members/invitations | EDIT | EDIT | NONE | NONE | NONE (firm team only via flag) | NONE | NONE | NONE | EDIT (staff) | NONE |
| Manage facilities/assets/suppliers | EDIT | EDIT | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE |
| Custom factor create/edit | CREATE | CREATE | CREATE | **CREATE** (A-1) | **VERIFY** (RLS read only; write via RLS is_org_member only — consultant no) | NONE | NONE | NONE | NONE | NONE |
| Custom factor approve | APPROVE | APPROVE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE |
| Customer item approval (final) | APPROVE | APPROVE | **APPROVE** (A-2/A-3) | **APPROVE** (A-2/A-3) | NONE | NONE | NONE | NONE | NONE | NONE |
| Assign work (batch/entity) | NONE | NONE | NONE | NONE | NONE (client status only) | NONE (receive only) | NONE | NONE | ASSIGN (`can_manage_staff`+`can_process`) | NONE |
| Validate processing items | NONE | NONE | **VERIFY** (API open, no UI) | **VERIFY** | NONE | VERIFY | EDIT | EDIT | NONE | **VERIFY** (extraction only; validation gated 403) |
| QC pass/fail | NONE | NONE | NONE | NONE | NONE | NONE | NONE | QC | QC | NONE |
| Export emissions/documents | EXPORT | EXPORT | EXPORT | **EXPORT** (A-1) | **VERIFY** (no UI) | NONE | NONE | NONE | NONE | NONE |
| Generate reports | CREATE | CREATE | CREATE | **CREATE** (A-1) | VERIFY (read only in UI) | NONE | NONE | NONE | NONE | NONE |
| Download customer documents | VIEW | VIEW | VIEW | VIEW | VERIFY | NONE | NONE | NONE | NONE | **NONE (enforced)** |
| Download source doc (assigned work view) | NONE | NONE | NONE | NONE | NONE | **VERIFY (broken E-1)** | VERIFY (JSON) | VERIFY (JSON) | NONE | **VERIFY (broken E-1)** |
| Mediated clarification | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | CREATE (own items) |
| Manage processing entities/SLA | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | EDIT (`can_manage_staff`) | NONE |
| Manage billing/commercial | NONE | NONE | NONE | NONE | NONE | NONE | NONE | NONE | EDIT (`can_manage_billing`) | NONE |

---

## 22. UI/UX Gap Matrix

| # | Gap | Roles affected | Layer | Severity |
|---|---|---|---|---|
| E-1 | Extraction document viewer broken (unsigned file_url) | Operator, PE staff | Frontend+API | P1 (workflow-blocking) |
| A-1 | Viewer = full writer authority | Viewer | API+RLS+UI | P1/P0 (if read-only intended) |
| A-2 | Customer final approval: API only, no UI | Owner/Admin | Frontend | P1 |
| A-3 | Customer processing pipeline member-open | all org roles | API | P1/P0 (if not intended) |
| F-3 | Custom Emission Factors: backend only, no UI | all | Frontend | P1 |
| O-2 | Admin controls visible to member/viewer | Member/Viewer | Frontend | P1 |
| O-3 | Ops tabs not permission-filtered | Operator/Reviewer/QC | Frontend | P1 |
| I-1 | Entity clarification issues have no triage UI | Internal staff | Frontend | P1 |
| V-1 | Raw processing status vocabulary for customers | Customer | Frontend | P1 |
| T-1 | Traceability chain not navigable item-level | Customer/Consultant | Frontend | P1 |
| F-4 | No factor catalogue/provenance UI | all | Frontend | P2 |
| M-1 | CSV/Excel mapping dead or manual-only | Customer | Frontend | P2 |
| R-1 | Report PDF not exposed in UI | Customer | Frontend | P2 |
| N-1 | "Existing data" in primary nav | all | Frontend | P2 |
| N-2 | Terminology inconsistencies (nav/labels) | all | Frontend | P2 |
| D-1 | Design systems duplicated; no tokens | all | CSS | P2 |
| A-4 | Accessibility gaps (labels, focus, color-only) | all | Frontend | P2 |
| L-1 | Legacy dashboard/beta/dead files remain; `/privacy` bug | all | Bundle | P2 (privacy bug P1) |
| S-1 | Legacy name-string guards (latent) | Internal staff | API | P1 (hardening) |
| S-2 | Entity payload exposes org UUID + storage path | PE staff | API | P2 |
| S-6 | `require_org_access` any-staff bypass (dead code) | Internal staff | API | P1 (latent) |
| C-1 | Consultant client workspace is status-only | Consultant | Frontend | P2 |
| O-1 | Owner has no distinct experience | Owner | Frontend+API | P2 |
| I-2 | Entity dashboard blocks not rendered | PE staff | Frontend | P3 |

---

## 23. Recommended Improvements

Prioritized, mapped to the findings:

1. **P0/P1 — Resolve the role-write model (A-1, A-2, A-3).** Decide Viewer and
   customer-processing contracts; re-gate APIs and RLS accordingly; make the
   UI reflect the decision (hide/disable, never just 403).
2. **P1 — Fix the extraction document viewer (E-1).** Sign assigned-work item
   URLs server-side under strict scope checks for operators and entity staff
   (view-only, short-lived); keep the no-download posture for org documents.
3. **P1 — Build the customer "Review & approve" screen (A-2) and item trace
   (T-1/V-1)** with a processing step indicator.
4. **P1 — Build the Custom Emission Factors UI (F-3)** (list/create/edit/
   approve/usage), reusing the existing API and RLS.
5. **P1 — Filter ops tabs by permission (O-3); add an ops Issues tab (I-1).**
6. **P1 — Role-gate customer admin surfaces (O-2); fix `/privacy` route; harden
   legacy name-string guards (S-1) or un-mount legacy routers.**
7. **P2 — Factor catalogue (F-4); CSV/Excel mapping (M-1) or removal; report
   PDF (R-1); terminology pass (N-2); IA cleanup (N-1); design-token
   consolidation (D-1); accessibility pass (A-4); legacy cleanup (L-1).**
8. **P2/P3 — Consultant operating model (C-1); owner tier (O-1); entity
   dashboard blocks (I-2); multi-org switching decision.**

---

## 24. Priority Roadmap

| Phase | Items |
|---|---|
| **Before launch (P0/P1)** | Role-write model decision + API/RLS re-gate (A-1/A-3) · extraction viewer fix (E-1) · customer approval UI + admin-only gate (A-2) · Custom Factor UI (F-3) · ops tab filtering (O-3) · ops Issues triage (I-1) · customer processing status interpretation (V-1/T-1) · `/privacy` bug · org-admin control gating (O-2) |
| **Launch hardening (P1)** | Legacy name-string guard remediation or un-mount (S-1) · `require_org_access` dead-code removal (S-6) · evidence chain navigation (T-1) |
| **Important product (P2)** | Factor catalogue (F-4) · report PDF (R-1) · CSV/Excel mapping (M-1) · terminology/IA (N-1/N-2) · design tokens + CSS consolidation (D-1) · accessibility (A-4) · legacy/beta cleanup incl. marketing beta banner (L-1) · consultant workspace depth (C-1) · entity payload hygiene (S-2) |
| **Future (P3)** | Owner-tier differentiation (O-1) · entity dashboard blocks (I-2) · multi-org switching decision · spreadsheet column mapping · custom factor version diffing |

---

## Appendix A — Positive verifications (no action required)

1. **Processing-Entity document download is blocked** (storage RLS + API gate +
   unsigned payloads) — PO decision enforced. ✔
2. **Tenant/entity/consultant RLS boundaries** are deny-by-default and
   consistent with the documented access model. ✔
3. **D37-0 billing write revocation** closes the direct-PostgREST billing
   path. ✔
4. **D15/D19 active client grant enforcement** is real (RLS + API). ✔
5. **Calculation is server-authoritative** — the client never supplies
   results; snapshots are immutable; evidence provenance preserved. ✔
6. **D32 private bucket + signed URLs only** — no predictable public document
   URLs. ✔
7. **Entity workspace scope re-checks** on every route
   (`require_entity_scope` + `ensure_entity_batch_access` + `_entity_workspace_guard`). ✔
8. **D35 self-service onboarding** binds discovery requests to `created_by`
   and reuses the real owner role model. ✔

## Appendix B — Evidence file map

| Claim | Primary evidence |
|---|---|
| Route map | `frontend/src/App.js` |
| Nav role-awareness | `frontend/src/v3/components/V3Layout.jsx`, `RoleRoute.jsx` |
| Staff auth chain | `backend/api/operations_auth.py`, `backend/auth.py` |
| Consultant chain | `backend/api/consultant_auth.py` |
| Entity workspace + guards | `backend/api/v3_operations.py` (lines ~551–1010, 1047–1120, 1382–1396) |
| Unsigned file_url in entity/operator lists | `backend/api/v3_operations.py` `ops_batch_items`, `entity_extraction_*`; `backend/data/manual_extraction.py` `list_items` |
| Signing only in item_workspace | `backend/api/v3_operations.py` item_workspace; `services/storage.py` |
| Broken iframe | `frontend/src/v3/ops/ExtractionPanel.jsx` |
| Storage RLS | `supabase/migrations/20260823000000_d32_private_documents_storage.sql` |
| Entity RLS | `20260810050000_v3m6_entity_rls.sql`, `20260821020000_d22_processing_work_assignment.sql`, `20260822000000_p9_rls_recursion_fix.sql` |
| Tenant RLS (member=writer) | `20260803000000_rc2_rls.sql` §3 |
| Billing revoke | `20260824020000_d37_0_…sql` |
| Customer factors backend | `backend/api/customer_factors.py`; `20260810020000_v3m3_customer_factors.sql` |
| No customer factor frontend | `grep -rn "customer-factors" frontend/src` (empty) |
| Customer approval API no UI | `backend/api/v3_processing_workflow.py`; `grep -rn "customer-review" frontend/src` (empty) |
| Member-open processing | `v3_processing_workflow.py` `require_org_member` on item endpoints |
| Legacy name-string guards | `backend/routes/*.py` `require_role(["admin",…])` |
| Legacy dashboard dead | `frontend/src/App.js` `/dashboard/*` redirect; Dashboard component still imported |
| `/privacy` duplicate | `frontend/src/App.js` (two `/privacy` routes) |
| Design system | `frontend/src/v3/*.css` (5 files), `frontend/src/App.css` (3491 lines) |
| Actor/access authority | `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §§3–38 |
| PO decisions | `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`; D-series records in the Actor Workspace Access Model §§37–50 |

---

*End of audit. Read-only — no files outside this report were created or
modified during the audit.*
