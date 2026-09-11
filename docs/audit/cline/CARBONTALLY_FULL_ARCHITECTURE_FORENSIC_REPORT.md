# CarbonTally — Full Product Architecture & UI/UX Forensic Report

> **Type:** First-pass architecture discovery / forensic evidence collection
> **Purpose:** Input for a later architecture decision. No implementation was performed.
> **Date:** 2026-09-01
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Repository:** `/home/shomonrobie/carbon_tally`
> **Mode:** Read-only investigation; report written only after explicit Act-mode approval.
> **Classification vocabulary:** VERIFIED DEFECT · ARCHITECTURE GAP · TECHNICAL DEBT · USABILITY · ACCESSIBILITY · PERFORMANCE · INTENTIONAL · FUTURE RECOMMENDATION · PO DECISION REQUIRED

---

# 1. Executive summary

CarbonTally is a **dual-surface platform**: a FastAPI backend (one app factory serving both a legacy
`/api/*` route surface and the canonical V3 `/api/v2/*` + `/api/v3/*` surface), a single main React
frontend (`frontend/`) that hosts the public website and all authenticated workspaces, and a
**separate legacy admin React app** (`admin/`) that talks to Supabase **directly**, bypassing FastAPI.

The V3 core is architecturally **coherent and layered**:

```
API routers (backend/api/*) → Composition root (api/dependencies.py)
  → Data repositories (backend/data/*, 36 repos over service-role asyncpg pool)
  → Domain modules (backend/domain/*) + Engines (backend/engines/*)
  → Supabase Postgres (supabase/migrations/, RLS + SECURITY DEFINER helper functions)
```

Business logic lives server-side (engines + domain), authorization is server-side
(`backend/auth.py` + `backend/api/operations_auth.py`), and the frontend is a thin consumer with a
role-aware shell (`V3Layout` + `RoleRoute` resolved from the single authoritative
`GET /api/v3/me/context` endpoint). The D19 workbench is a genuine reusable component family.

The main architectural weaknesses are **convergence debt**, not design incoherence:

1. **Three competing UI component ecosystems** (V3 hand-rolled `ui/` primitives; parallel
   `v3.css`/`ops.css` utility-class systems; the separate `admin/` app stack).
2. **Three table rendering approaches** (canonical `DataTable`; hand-rolled `v3-ops-table` with
   duplicated pagination markup; raw `<table>` in 22 files).
3. **A separate admin control-plane app that bypasses the FastAPI business layer** and reads
   Supabase directly (`admin/src/services/reviewService.js`), duplicating API + authorization
   responsibilities and diverging from the ratified admin-separation architecture.
4. **A large legacy surface** (~405 legacy endpoints, ~23 legacy root components) still mounted and
   partially routed; V3 (290 endpoints) is canonical but not yet the sole surface.
5. **Dead/parallel endpoint families** (e.g. `v3_review.py` `/api/v3/admin/review-queue` has zero
   frontend consumers; QC admin helpers exported but unused).
6. **A single 1,473-line flat frontend service module** (`frontend/src/v3/api.js`, ~239 exports)
   that works but is approaching maintainability limits.

The database domain model is broad (104+ tables), tenant-scoped, RLS-guarded and mostly coherent.
Audit/activity proliferation and JSONB-heavy legacy columns are acknowledged technical debt.
---

# 2. Current architecture diagram

```
PUBLIC WEBSITE  (frontend/src — LandingPage, public/*, Pricing, Glossary, Assistant)
      │  public routes
      ▼
MAIN REACT APP  (frontend/src/App.js — React Router)
      │  ProtectedRoute → RoleRoute → V3Layout
      │  /home /documents /processing /review /emissions /reports /issues
      │  /billing /organization /messaging /existing-data          (customer)
      │  /consultant /consultant/items/:clientId/:itemId           (consultant)
      │  /ops /ops/items|review|qc/:id /pe/items/:entityId/:itemId (staff / PE)
      │
      ├── V3 API CLIENT   frontend/src/v3/api.js   (v3Fetch, ~239 fns)
      ├── LEGACY CLIENT   frontend/src/services/apiClient.js (AssetManager, TeamManagement)
      └── SUPABASE CLIENT frontend/src/supabaseClient.js (auth session, Realtime, RLS reads)

LEGACY ADMIN APP  (admin/ — separate CRA, /admin/*, port 3001)
      └── SUPABASE DIRECT  admin/src/services/reviewService.js  ← bypasses FastAPI (gap)

FASTAPI  (backend/main.py — one app: legacy routes + V3 router; main_v2.py = V3-only)
      │
      ├── LEGACY ROUTES      backend/routes/**        (~405 endpoints, /api/*)
      ├── V3 ROUTERS         backend/api/*            (290 endpoints: /api/v2/*, /api/v3/*)
      │     └── dependencies.py  (composition root — RepositoryBundle)
      │           ├── DATA REPOS  backend/data/*  (36, service-role asyncpg pool)
      │           ├── DOMAIN      backend/domain/* (25)
      │           └── ENGINES     backend/engines/* (12: calculation, extraction,
      │                              factor_matching, processing_workflow, validation…)
      ├── AUTH / RBAC         backend/auth.py + backend/api/operations_auth.py
      └── WORKER              backend/workers/automatic_processing.py (durable claim loop)

SUPABASE POSTGRES  (supabase/migrations/ — 41 migrations, RC2 base + V3 additive)
      ├── RLS policies + SECURITY DEFINER helpers (is_org_member, is_org_consultant,
      │   is_org_admin_or_owner, is_entity_member, is_org_active)
      ├── 104+ base tables (organizations, users, staff, consultants, PEs, documents,
      │   extraction, factors, emissions, snapshots, reports, billing, audit, messaging…)
      └── Storage (private documents, signed URLs) + Realtime (messages, presence)
```

---

# 3. Database architecture

Source: `supabase/migrations/` (41 files) and `v3_schema.sql` (6,331-line dump; note it predates
`v3m7` vehicles and `d21` white-label tables, so those are read from migrations).

## 3.1 Domain map

| Domain | Key tables | Ownership / tenant boundary | Lifecycle states |
|---|---|---|---|
| **Organizations** | `organizations`, `organization_members`, `organization_metadata`, `organization_files`, `user_invitations`, `pending_invites` | `organizations.id` is the tenant root; members via `organization_members` (role CHECK owner/admin/member/viewer) | `is_active` / `archived_at` (C2); member `is_active` |
| **Users / identity** | `users` (auth.users mirror), `login_history`, `password_reset_tokens` | `users.id` = `auth.uid()` convention | `is_active`, `is_anonymised` |
| **Staff RBAC** | `staff_profiles`, `staff_roles` (JSONB `permissions`), `roles` (customer-org role reference) | `staff_profiles.user_id`; `entity_id` NULL = CarbonTally internal (positive convention) vs PE staff | `is_active`; role `is_active` |
| **Consultants** | `consultant_profiles`, `consultant_firm_members` (`client_access` GIN array), `consultant_clients`, `consultant_tasks`, `consultant_billing` | Firm = `consultant_profiles.id`; client org links via `consultant_clients.organization_id`; `consultant_firm_members.client_access` array grants member-level org access | client suspend/end/reactivate |
| **Processing Entities (PE)** | `processing_entities`, `staff_profiles.entity_id`, `manual_extraction_batches.entity_id`, `manual_review_queue.entity_id`, `issues.entity_id` | Entity-scoped; deny-by-default RLS; entity SELECT only via `is_entity_member` | `active`/`remediation`/`suspended`/`terminated` |
| **Documents** | `customer_documents`, `document_types`, `file_attachments`, `organization_files` | `organization_id` | uploaded→pending→processing→processed→manual_review→verified→approved/rejected/failed |
| **Processing / queue** | `document_processing_queue` (durable job store), `processing_queue`, `processing_steps`, `upload_batches`, `import_batches`, `queue_settings` | `organization_id` | v3m9 `stage` + RC2 `status` (pending/processing/ai_extracted/manual_review/manual_extraction/qc/customer_review/approved/rejected/completed/failed); `attempt_count`/`max_attempts`/`locked_at`/`lock_token` |
| **Manual extraction** | `manual_extraction_batches`, `manual_extraction_items`, `manual_review_queue` (work items) | `organization_id` + optional `entity_id` (PE allocation) | batch/item status; `qc_*`; customer approval fields |
| **Emissions factors** | `emission_factors`, `customer_factors`, `factor_aliases`, `units`, `import_batches` | factors are global reference (country GB/IE); `customer_factors` are org-scoped | customer factor: draft→active→inactive/archived, monotonic `version` |
| **Emissions / calculations** | `emissions_logs`, `calculation_snapshots` | `organization_id` | snapshots immutable/append-only; `factor_kind` = emission_factor XOR customer_factor (CHECK); `content_hash`, `request_id` |
| **Reports** | `report_versions`, `report_generation_queue`, `report_templates`, `report_comments`, `export_history` | `organization_id` | generation queue lifecycle |
| **Billing / commercial** | `customer_subscriptions`, `consultant_billing` + D37 commercial tables (`subscriptions`, `plans`, `orders`, `credit_ledger`, `payments`, `storage_usage`, `usage_tracking`, `idempotency`) | `organization_id` / consultant | subscription: trialing/active/past_due/paused/cancelled/expired/incomplete/… |
| **Audit / activity** | `audit_logs`, `activity_logs`, `audit_trail`, `domain_events`, `staff_activity_log`, `user_activity_log`, `document_activity_log`, `processing_audit_trail`, `review_audit_trail`, `conversation_activity_log`, `message_activity_log`, `verification_activity_log` | separate by design (PO intent) | append-only; immutability migration `20260831020000_audit_activity_immutability.sql` |
| **Messaging** | `conversations`, `conversation_participants` (unique migration v3m8), `messages`, `typing_status`, `user_presence` | org-member / consultant-grant / staff-admin RLS; PE denied | conversation lifecycle; read receipts |
| **Notifications** | `notifications`, `notification_delivery`, `notification_templates` | `recipient_id` | `is_read` partial index |
| **Issues / ops** | `issues` (first-class, ADR-V3-009), `qc_checks/qc_errors/qc_checklists`, `sla_definitions/sla_compliance`, `processing_assignments`, `reassignment_history` | optional org + entity + work_item context | open→in_progress→on_hold/escalated→resolved→closed |
| **Master data** | `assets`, `facilities`, `suppliers`, `supplier_categories`, `vehicles` (v3m7), `product_categories` | `organization_id` | org-scoped CRUD |


## 3.2 RLS / security boundary

- RLS enabled on tenant tables; policies delegate to **SECURITY DEFINER helper functions**
  (`v3_schema.sql:130-209`): `is_org_member`, `is_org_admin_or_owner`, `is_org_consultant`,
  `is_org_active`, `is_entity_member` (all with pinned `search_path`).
- Consultant access grants via `is_org_consultant` (firm membership + `client_access` array OR
  `consultant_clients` row).
- Entity boundary: `processing_entities` is deny-by-default; entity SELECT policies exist only on
  `manual_extraction_batches`/`manual_extraction_items` (D22); entity writes are service-role only.
- **FORCE RLS is deferred** (intentional — separate security investigation).
- `backend/infra/supabase.py` uses the **service-role** client + asyncpg pool (RLS-bypassing) with
  explicit application-level authorization on top.

## 3.3 Indexes

Targeted operational indexes exist and cover the hot paths: `dpq_claim_idx` (status/created partial),
`dpq_org_created_idx`, `dpq_lock_token_idx`, `dpq_snapshot_idx`, `emissions_logs_org_start_date_idx`,
`notifications_unread_recipient_idx`, `consultant_firm_members_client_access_gin`,
`organizations_name_trgm_idx`, and the `v3m11_operational_indexes` batch.

## 3.4 Observations

- **Coherent tenant model** (org → members → org-scoped data) — VERIFIED.
- Table count ~104+ with several very wide legacy tables (`organizations` ≈ 70 columns,
  `organization_metadata` ≈ 30 columns) — TECHNICAL DEBT (wide-column drift, not blocking).
- 8+ audit/activity tables with overlapping purpose — INTENTIONAL (PO: audit/activity remain separate).
- `customer_documents` carries `extracted_data`/`mapped_data`/`calculated_emissions_kg_co2e` JSONB
  alongside the newer `document_processing_queue` durable job columns — duplication risk
  (document state held in two places) — ARCHITECTURE GAP.


---

# 4. FastAPI / business architecture

## 4.1 Entry points

- `backend/main.py` — **single composition root**: imports all legacy `routes/**`, then mounts the
  V3 router (`main.py:211-261`, `app.include_router(api_router)`), with a defensive try/except so a
  V3 import failure degrades to legacy-only. Also defines legacy `ProtectedRoute`-style auth usage.
- `backend/main_v2.py` — V3-only uvicorn entry (`app = create_app()` from `api.router`).

## 4.2 V3 layered structure

| Layer | Location | Count | Responsibility |
|---|---|---|---|
| Routers | `backend/api/*.py` | 43 modules | Thin HTTP boundary, `Depends` auth, no business logic |
| Composition root | `backend/api/dependencies.py` | 1 | Per-request `RepositoryBundle` + engine instances; re-exports auth guards |
| Authorization | `backend/auth.py` + `backend/api/operations_auth.py` | 2 | JWT/Bearer (`get_current_user`), RBAC guards, `StaffContext` for ops |
| Repositories | `backend/data/*.py` | 36 | Service-role asyncpg SQL; explicit column lists, transactions, natural-key upserts |
| Domain | `backend/domain/*.py` | 25 | Business rules, state machines, evidence/provenance semantics |
| Engines | `backend/engines/*.py` | 12 | Calculation (525 L), extraction (317 L), factor_matching (330 L), matching_stages (361 L), processing_workflow (313 L), validation (1,159 L), workflow (850 L), report_generation (853 L), ai_extraction, pdf_render, benchmarking |
| Services | `backend/services/*.py` | 8 | automatic_extraction, automatic_processing, billing, email_service, extraction_suggestions, retention, storage, v3_email |
| Infra | `backend/infra/*.py` | 6 | supabase (client+pool), event_bus, audit_logger, llm_client, search_index, config |
| Worker | `backend/workers/automatic_processing.py` | 1 | Durable claim/process loop (`FOR UPDATE SKIP LOCKED`, stale-lock recovery, idempotency) |

## 4.3 Where business logic actually lives

Canonical V3 logic: **engines + domain**, called by routers through the composition root. Examples:

- Calculation: `engines/calculation.py` (persists immutable `calculation_snapshots`, dedup by
  request id, preserves `factor_id`/`customer_factor_id`/`factor_kind` provenance).
- Factor matching: `engines/factor_matching.py` + `matching_stages.py` (customer-factor precedence,
  unit normalization via `core/units.py`).
- Durable pipeline: `domain/automatic_processing.py` + `services/automatic_processing.py` +
  `workers/automatic_processing.py` (stage machine on `document_processing_queue`).
- Validation: `engines/validation.py` (1,159 L — largest engine).
- Ops authorization: `api/operations_auth.py` — the docstring documents the exact chain:
  authenticated user → active `staff_profiles` → `staff_roles.permissions` JSONB → scope
  (`entity_id` NULL = internal vs PE). Every `/api/v3/ops/*` endpoint passes `require_staff()` and
  re-authorizes each item/batch/entity (`require_internal_staff` / `require_entity_scope`).

## 4.4 Legacy vs V3 logic

- Legacy routes (`routes/*`, `routes/admin/*`, `routes/organizations/*`) contain their own
  business logic (e.g. `backend/process_emissions.py`, `backend/report_generator.py`,
  `backend/pdf_engine.py` at repo root are legacy standalone modules).
- Root-level legacy modules (`backend/database.py`, `backend/config.py`, `backend/auth.py` used by
  both). `auth.py` is shared and reused by V3 (`api/dependencies.py` re-exports it) — not duplicated.
- `admin/` frontend app performs its own business reads directly against Supabase (see §11) —
  the only surface that bypasses FastAPI.

## 4.5 Observations

- **Layering is clean and canonical for V3** — VERIFIED. Repositories are the only DB access path
  for V3; engines are stateless and instantiated per request (`dependencies.py` docstring).
- Duplication exists between legacy `routes/**` logic and V3 engines for overlapping domains
  (documents/emissions/reports) — TECHNICAL DEBT (transitional, INTENTIONAL per PO: legacy remains).
- `admin/` app direct-Supabase access is a genuine separation violation — ARCHITECTURE GAP.


---

# 5. API architecture

## 5.1 Scale

- **V3 API:** 290 endpoints across 43 modules (`backend/api/*.py`).
- **Legacy API:** 405 endpoints across `routes/**` (50 modules).
- Both served by the same FastAPI app in `main.py`; `main_v2.py` serves V3 only.

## 5.2 Representative endpoint families (V3)

| Domain | Router (prefix) | Endpoint count | Representative endpoints | Auth |
|---|---|---|---|---|
| Organizations | `v3_organizations.py` (`/api/v3/organizations`) | 25 | POST `""`; GET/PUT `/{org_id}/profile`; members CRUD; facilities/assets CRUD; invitations | `require_org_member` / `require_org_admin` |
| Consultants | `v3_consultants.py` (`/api/v3/consultants`) | 31 | `/me`, `/me/clients`, `/clients/{id}/suspend\|end\|reactivate`, `/me/dashboard`, `/me/team`, `/clients/{id}/documents`, `/clients/{id}/processing/items`, `/clients/{id}/evidence`, `/clients/{id}/reports` | firm-membership guard; per-client re-authorization |
| Operations | `v3_operations.py` (`/api/v3/ops`) | 39 | `/me`, `/dashboard`, `/organizations`, `/staff`, `/entities/{id}/dashboard`, `/entities/{id}/extraction/*`, `/items/{id}/workspace`, `/items/{id}/start\|extract\|map\|validate\|calculate\|qc`, `/queues/operator\|review\|qc`, `/sla/settings` | `require_staff` + `require_internal_staff` / `require_entity_scope` |
| Processing workflow (customer) | `v3_processing_workflow.py` (`/api/v3/processing`) | 18 | `/dashboard`, `/queue`, `/items/{id}/start\|extract\|map\|validate\|calculate\|customer-review`, `/items/{id}/workspace`, `/next-item` | `require_org_member` |
| Automatic processing | `v3_automatic_processing.py` (`/api/v3/processing`) | 6 | `/jobs`, `/jobs/{id}/confirm\|retry\|review`, `/documents/{file_id}/enqueue` | org-scoped |
| Documents | `v3_documents.py` (`/api/v3`) | 9 | `/documents`, `/uploads`, `/batches/*` | `require_org_member` |
| Emissions | `v3_emissions.py` (`/api/v3/emissions`) | 9 | `/dashboard`, `/calculations`, `/calculations/{id}/verify`, `/factors`, `/calculate` | org-scoped |
| Reports | `v3_reports.py` (`/api/v3/reports`) | 8 | `/types`, `/generate`, versions, content | org-scoped |
| Manual extraction | `v3_manual_extraction.py` (`/api/v3/manual-extraction`) | 6 | `/batches`, `/batches/{id}/items`, PUT `/items/{id}` | internal staff |
| QC | `v3_qc.py` (`/api/v3/qc`) | 3 | `/queue`, `/stats`, `/items/{id}/review` | `require_admin` |
| Messaging | `v3_messaging.py` (`/api/v3/messaging`) | 5 | conversations CRUD + messages + read | org/consultant/staff per relationship |
| Notifications | `v3_notifications.py` (`/api/v3/notifications`) | 3 | list, mark read, read-all | recipient-scoped |
| Review (admin family) | `v3_review.py` (`/api/v3/admin`) | 6 | `/review-queue`, assign, complete, sla | **zero frontend consumers** (§5.5) |
| Billing / commercial | `v3_billing.py`, `v3_commercial.py` | 34 | `/me`, credits, orders, payments, subscriptions, plans, storage | org / admin billing permission |
| Search | `v3_search.py` (`/api/v3/search`) | 1 | org-scoped keyword search | `require_org_member` |
| Context | `v3_context.py` (`/api/v3`) | 1 | `/me/context` — single authoritative actor/workspace resolver | bearer |
| Reporting | `v3_reporting.py` | 11 | customer dashboard, consultant portfolio, ops platform/aging/review/qc/audit | role-scoped |

## 5.3 Contract consistency

- **Error envelope:** uniform `ErrorResponse{error:{code,message,details}, request_id}` for
  CarbonTallyError / HTTPException / 422 / 500 (`api/router.py` exception handlers). VERIFIED.
- **Pagination:** V3 consistently uses `limit` + `offset` (+ `total` in responses) across ops
  queues, consultant lists, organizations, reports and workflow queues. VERIFIED.
- **Auth:** every V3 router uses `Depends` guards from `auth.py`/`operations_auth.py`; no
  frontend-only authorization.

## 5.4 Legacy / V3 overlap (INTENTIONAL, transitional)

- `/api/organizations/**` (legacy) vs `/api/v3/organizations/**`.
- `/api/reports` + `/api/admin/reviews` vs `/api/v3/reports` + `/api/v3/ops/queues/review`.
- `/api/emissions` vs `/api/v3/emissions`; `/api/customer/dashboard` vs `/api/v3/reporting/*`.

## 5.5 Duplicate / dead endpoint evidence

- `v3_review.py` (`/api/v3/admin/review-queue`) — the current frontend exclusively calls
  `/api/v3/ops/queues/review` (`frontend/src/v3/api.js` `getReviewQueue`); **no file in
  `frontend/src` references `/api/v3/admin`**. → VERIFIED DEFECT (dead endpoint family).
- QC helpers `getQcQueueAdmin`/`getQcStats`/`qcReviewItemAdmin` are exported from `api.js` but used
  by **no page component** (grep across `frontend/src/v3`). → VERIFIED DEFECT (dead client surface).
- Two review queue families exist (`/api/v3/ops/queues/review` and `/api/v3/admin/review-queue`) and
  two QC families (`/api/v3/ops/queues/qc` and `/api/v3/qc/queue`). → ARCHITECTURE GAP.


---

# 6. User / role architecture

Roles resolve server-side via `GET /api/v3/me/context` (returns `actor_type` + `destination` +
`organization`); the frontend `RoleRoute` + `V3Layout` consume it and are explicitly
navigation-only (fail-closed on error).

| Actor | Identity source | Access boundary | Dashboard / shell | Primary workflows | API used | Key UI |
|---|---|---|---|---|---|---|
| **CarbonTally Admin** | `staff_profiles` + `staff_roles.permissions` (`role_name` in `admin`/`system_admin`) | Global admin: `require_admin`, `ADMIN_ROLE_NAMES=("admin","system_admin")`; QC/issue surfaces | Separate **legacy `admin/` app** (`/admin/*`) for the legacy control plane; V3 `/ops` Commercial/QC/Issues tabs for staff admin | Reviews, QC, issues triage, commercial/billing config, settings, audit console | legacy `/api/admin/*` + V3 `/api/v3/ops/*`, `/api/v3/qc/*`, `/api/v3/commercial/*` | `admin/src/pages/admin/*`; `v3/ops/{CommercialTab,QcQueue,IssuesTriageTab,AuditConsoleTab,SettingsTab}` |
| **CarbonTally Staff (internal)** | `staff_profiles` with `entity_id IS NULL` | Ops-wide via `require_internal_staff`; permission keys `can_view_all`/`can_process`/`can_review`/`can_manage_staff`/`can_manage_billing` | `/ops` (`OperationsPage` tabs) | Operator queue→extract→map→calculate; review; SLA; staff/roles/entities; messaging | `/api/v3/ops/*` | `OperatorQueue`, `ReviewQueue`, `StaffRoster`, `WorkItemWorkspace` |
| **Customer** | `organization_members` (owner/admin/member/viewer) | Org-scoped `require_org_member`; owner/admin-only gates (approve, self-approve factors — PO decision §16) | `/home` `V3Layout` customer nav (11 links) | Upload→processing→review/approve→emissions→reports→billing | `/api/v3/processing/*`, `/api/v3/reports`, `/api/v3/billing`, `/api/v3/organizations/*` | `DashboardPage`, `ProcessingPage`, `ProcessingItemWorkspace` (WorkbenchShell), `ReviewPage` |
| **Individual Organization** | Same as customer; `organization_members` role governs | Org-scoped; member/viewer vs owner/admin | Same customer shell; `/organization` admin tabs | Profile, members, facilities, assets, suppliers, vehicles, custom factors, activity, security | `/api/v3/organizations/*` | `v3/admin/*` tabs (org settings, not a control plane) |
| **Consultant** | `consultant_firm_members` (owner/admin/manager/member/viewer) + `client_access` array | Firm membership + per-client re-authorization (`is_org_consultant` in RLS) | `/consultant` (`ConsultantPage`) | Portfolio dashboard, client switcher, client docs upload, processing items, evidence, reports, team, white-label, messaging, new customer creation | `/api/v3/consultants/*` (31 endpoints) | `ConsultantPage` tabs: Dashboard/WhiteLabel/Team/Messaging/NewCustomer |
| **Consultant Client** | org row linked via `consultant_clients` (no direct login unless converted) | Access only via authorised consultant; revocation (Owner/Admin/Manager) preserves data (PO intent) | n/a (no login) | n/a | n/a (consultant operates on their behalf via `/api/v3/consultants/clients/{id}/*`) | n/a |
| **Processing Entity (PE)** | `staff_profiles` with `entity_id` populated | Entity-scoped only (`is_entity_member` RLS; `require_entity_scope` API); **no** broad customer access; no manual-extraction pipeline access | `/ops` → PE Manager dashboard (`view=dashboard`) or `EntityExtractionWorkspace` (`view=work`) | Entity extraction batches, item work, PE dashboard, entity issues | `/api/v3/ops/entities/{entity_id}/extraction/*`, `/api/v3/ops/entities/{entity_id}/dashboard` | `PEManagerDashboard`, `EntityExtractionWorkspace`, `PEEntityItemPage` |

## 6.1 Observations

- Role boundaries are enforced server-side and in RLS; UI role detection is UX-only. VERIFIED.
- The **admin control plane is split**: the modern `/ops` commercial/QC/audit surfaces live in the
  main app, while the legacy `admin/` app (Users, Organizations, Reviews, Analytics, Settings,
  DefraFactors, ManualReviewQueue, WorkHub) remains a **separate surface with direct Supabase
  access** — ARCHITECTURE GAP (see §17).
- PE boundary preserved per the approved source-document model (no customer download in PE
  workspace; server-side signed URLs). VERIFIED (SecureDocumentViewer + ops auth docstring).


---

# 7. Customer data workflow

```
CUSTOMER (owner/admin/member)
  ↓ UI: /home DashboardPage → DocumentsPage / ProcessingPage
  ↓ UI ACTION: upload file (v3UploadDocument / legacy UploadManager)
  ↓ FRONTEND SERVICE: frontend/src/v3/api.js v3UploadDocument / enqueueDocumentForProcessing
  ↓ API: POST /api/v3/uploads → POST /api/v3/processing/documents/{file_id}/enqueue
  ↓ FASTAPI: v3_documents.py → v3_automatic_processing.py → services/automatic_processing.py
  ↓ WORKER: workers/automatic_processing.py (claim → extract → map → validate → calculate)
  ↓ DATABASE: customer_documents + document_processing_queue (durable job, stage + status)
  ↓ RESULT: calculation_snapshots (immutable) + emissions_logs + evidence
  ↓ NEXT STATE: awaiting customer review → customer_review
  ↓ CUSTOMER REVIEW: /review (ReviewPage → ReviewDetailPage), submitCustomerReview
  ↓ API: POST /api/v3/processing/items/{id}/customer-review
  ↓ APPROVAL GATE: owner/admin approve/reject (ApproverRoles = ['owner','admin'])
  ↓ RESULT: approved/rejected → emissions dashboard + reports
  ↓ REPORTING: /reports (ReportsPage → ReportDetailPage), generateReport → report_generation_queue
```

Supporting pages: `/processing/:itemId` → `ProcessingItemWorkspace` (WorkbenchShell with customer
stage list extract→map→validate→calculate→review→approve→evidence), `/emissions`
(`EmissionsPage` DataTable), `/existing-data` (Discovery), `/issues`, `/billing`, `/organization`.

**Gaps / observations:**
- State machine is server-side and durable (v3m9); UI renders `stage` from the API — VERIFIED.
- `ProcessingItemWorkspace` imports only `/api/v3/processing/*` (never ops) — INTENTIONAL separation
  (customer vs internal operations), confirmed in file header comment.
- Approval is owner/admin-only client-side AND the backend re-authorizes — VERIFIED.
- Mixed upload paths remain (V3 `v3UploadDocument` and legacy `UploadManager`/`BulkUpload`
  embedded in the legacy Dashboard function in App.js) — TECHNICAL DEBT.

---

# 8. Consultant workflow

```
CONSULTANT
  ↓ UI: /consultant (ConsultantPage, role-route requireConsultant)
  ↓ API: GET /api/v3/consultants/me + /me/dashboard + /me/clients (listConsultantClients)
  ↓ UI ACTION: select active client (client switcher — explicit active-client context)
  ↓ API: GET /api/v3/consultants/clients/{client_id}/context + /dashboard + /documents + /reports
  ↓ UI: upload consultant document (uploadConsultantDocument)
  ↓ API: POST /api/v3/consultants/clients/{client_id}/documents
  ↓ PROCESSING: GET /clients/{client_id}/processing/items + /processing/status
  ↓ UI: ConsultantItemPage (per-client processing items) — calculation snapshots API-only (PO intent)
  ↓ REVIEW/EVIDENCE: GET /clients/{client_id}/evidence + /issues
  ↓ REPORTING: GET /clients/{client_id}/reports (ClientMessagingTab, WhiteLabelTab, ConsultantTeamTab)
  ↓ RESULT: per-client portfolio reports; revocation via /suspend /end /reactivate
  (Owner/Admin/Manager only; revocation preserves client data — PO intent)
```

**Gaps / observations:**
- Active-client context is explicit in UI and every request is re-authorized server-side — VERIFIED.
- `ConsultantPage` is a large 1,092-line hub (multiple tab views in one file) — TECHNICAL DEBT
  (component size).
- Consultant processing reuses the V3 processing API surface rather than ops — INTENTIONAL.

---

# 9. Processing Entity (PE) workflow

```
CARBONTALLY (assigns work)
  ↓ API: POST /api/v3/ops/batches/{batch_id}/assign (assigned_to XOR entity_id — D22)
  ↓ DATABASE: manual_extraction_batches.entity_id = <PE>
  ↓ PE STAFF / PE MANAGER
  ↓ UI: /ops (OperationsPage) → role_name pe_manager ? PEManagerDashboard : EntityExtractionWorkspace
  ↓ API: GET /api/v3/ops/entities/{entity_id}/dashboard | /extraction/batches | /next-item
  ↓ DOCUMENT ACCESS: SecureDocumentViewer with backend-signed, role-scoped URL; no download for PE
  ↓ UI ACTION: start → extract → map → calculate (item-level)
  ↓ API: POST /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/start|extract|map|calculate
  ↓ RESULT: item status transitions persisted; evidence recorded
---

# 10. Internal Operations workflow

```
CARBONTALLY STAFF (internal, entity_id IS NULL)
  ↓ UI: /ops (OperationsPage — permission-aware tabs)
  ↓ QUEUE: OperatorQueue (/api/v3/ops/queues/operator) → ReviewQueue (/queues/review) → QcQueue (/queues/qc)
  ↓ UI ACTION: open batch → open item → dedicated route /ops/items/:itemId (CL-59, never inline)
  ↓ UI: WorkItemWorkspace (WorkbenchShell) + ExtractionPanel
  ↓ API: POST /api/v3/ops/items/{id}/start|extract|map|validate|calculate|qc
  ↓ FASTAPI: v3_operations.py → operations_auth (require_staff + scope) → engines (validation/calculation)
  ↓ DATABASE: manual_review_queue + manual_extraction_items + issues + processing logs
  ↓ REVIEW: ReviewItemPage assign/complete (/api/v3/ops/review/{id}/assign|complete)
  ↓ QC: QcItemPage (/api/v3/qc/* for admin; /api/v3/ops/items/{id}/qc otherwise)
  ↓ EVIDENCE: EvidenceTrail + audit console
  ↓ ADMIN: staff/roles/entities/SLA/settings/messaging/audit/commercial tabs
  ↓ RESULT: completed work → customer review → approval → emissions/reporting
```

**Gaps / observations:**
- Queue→workspace is a dedicated routed workspace per queue (CL-59) — matches the ratified UX
  principle (queue → open workspace → focused page → back to queue). VERIFIED.
- Ops pages use the hand-rolled `v3-ops-table` instead of the shared `DataTable` for the queues
  (see §13) — ARCHITECTURE GAP / TECHNICAL DEBT.
- QA/QC split: `/api/v3/qc/queue` (admin) exists alongside `/api/v3/ops/queues/qc`; the QC tab is
  gated to global admins — INTENTIONAL role separation.

---

# 11. Admin / staff workflow

```
CARBONTALLY ADMIN / SYSTEM ADMIN
  ↓ LEGACY CONTROL PLANE (separate admin/ app — /admin/login → /admin/*):
  ↓   Dashboard, Users, Organizations, Customers, Batches, Analytics, Settings,
  ↓   DefraFactors, Reviews, ManualReviewQueue, ExtractionErrorReview, BetaManagement,
  ↓   GlossaryManagement, WorkHub, StaffOnlinePresence, LogViewer, Assignments
  ↓   DATA ACCESS: admin/src/services/reviewService.js → supabase.from(...) DIRECT (bypasses FastAPI)
  ↓   STACK: react-table, react-hook-form, react-select, tailwindcss, chart.js, react-toastify
  ↓ MODERN STAFF ADMIN (in main app /ops):
  ↓   CommercialTab (/api/v3/commercial/*), QcQueue (/api/v3/qc/*), IssuesTriageTab,
  ↓   AuditConsoleTab (/api/v3/ops/reporting/audit), SettingsTab, StaffRoster/StaffRolesTab
  ↓ ORG-SETTINGS (customer "admin" — not a control plane):
  ↓   /organization → v3/admin/AdminPage tabs: Profile, Members, Suppliers, Facilities,
  ↓   Locations, Vehicles, CustomFactors, Activity, Security
```

**Gaps / observations:**
- The legacy `admin/` app is a **third component ecosystem** and the **only surface that reads
  Supabase directly without FastAPI authorization** — ARCHITECTURE GAP (high priority). Evidence:
  `admin/src/services/reviewService.js` `fetchStaffMembers()`/`assignReviewToStaff()` call
  `supabase.from('staff_profiles')`/`supabase.from('manual_review_queue')` directly.
- The staff-dashboard route (`/staff-dashboard`) exists only in `admin/`, not in the main app.
- `v3/admin/*` is org-level settings (tabs over `/api/v3/organizations`), correctly distinct from
  the control plane — INTENTIONAL separation, but naming (`AdminPage`) is confusing.

  ↓ NEXT: review/QA by CarbonTally (ReviewQueue / QcQueue); clarification via entity-scoped issues
  ↓ COMPLETION: entity work complete → internal review/QC → customer approval → reporting
```

**Gaps / observations:**
- PE isolation is enforced both in RLS (`is_entity_member` + entity SELECT policies) and API
  (`require_entity_scope`) — VERIFIED.
- PE staff structurally cannot reach the manual-extraction pipeline (no entity column on those
  tables) — VERIFIED (documented in operations_auth.py).
- `PEEntityItemPage` and `EntityExtractionWorkspace` reuse `ExtractionPanel` (D23) — coherent.
- PE work UI is separate from internal ops queues — INTENTIONAL (PE application separation).

---

# 12. UI component architecture

## 12.1 Answers to the component questions

1. **Is shadcn/ui installed?** **No.** No `components.json`, no `tailwind.config.js`, no
   `postcss.config.js`, no shadcn/@radix dependencies in `frontend/package.json` (verified by file
   listing + package.json inspection).
2. **Is it used?** N/A (not installed).
3. **What is the canonical component system?** The **hand-rolled D21 primitive set** in
   `frontend/src/v3/components/ui/` (12 files, plain CSS `ui.css` + `react-icons/fi`), built on
   design tokens in `frontend/src/v3/tokens.css`. Barrel export in `ui/index.js`.
4. **Competing component systems?** Yes — three:
   - **D21 primitives** (`v3/components/ui/*`) — canonical for V3 pages.
   - **Parallel utility-class system** in `v3.css` (`v3-btn`, `v3-card`, `v3-form`, `v3-input`,
     `v3-modal`, `v3-loading`, `v3-error`, `v3-empty`) + `ops.css` (`v3-ops-table`, `v3-ops-tabs`,
     `v3-ops-badge`, `v3-ops-card`) — used directly by consultant/ops pages and even by DataTable's
     own pagination buttons (`v3-btn v3-btn-sm` in DataTable.jsx:181).
   - **Legacy admin app stack** (`admin/`): react-table, react-hook-form, react-select,
     tailwindcss, chart.js, react-toastify — a fully independent system.
   - (MUI `@mui/material` is present but only in 2 public demo components: `CarbonTallyDemo.jsx`,
     `FileUploadHero.jsx` — not a live system.)
5. **Components duplicated?** Yes — see §12.3 / §13.
6. **Shared components reused?** The `ui/` primitives are genuinely reused (~16 consumers across
   customer/ops/consultant/admin/reports/workbench), but several pages define local
   `LoadingBlock`/`ErrorBlock` helpers (e.g. `ConsultantPage.jsx:60-66`) instead of importing
   `StateViews` — duplication of primitive behaviour.

## 12.2 Representative primitive audit

| Primitive | File | Evidence |
|---|---|---|
| Button | `v3/components/ui/Button.jsx` | D21 button; `v3-btn` utility class used 152× across JSX |
| Input / Select / TextArea | `ui/FormControls.jsx` (`TextInput`, `SelectInput`, `TextArea`, `CheckboxField`, `Field`) | consumed via `ui/index.js` |
| Dialog / Modal | `ui/Dialog.jsx` (`Dialog`, `ConfirmationDialog`) | used in ops/customer/admin |
| Drawer | `ui/Drawer.jsx` | V3Layout mobile tray (D20) |
| Tabs | `ui/Tabs.jsx` | present, though ops/admin hubs roll their own tab bars (`v3-ops-tabs`) |
| Table | `ui/DataTable.jsx` | canonical (see §13) |
| Pagination | DataTable built-in (`ct-table-pagination`) **and** duplicated hand-rolled bars (ReviewQueue) |
| Search | `v3/components/SearchBox.jsx` (nav org-scoped search) | wired to `/api/v3/search` |
---

# 13. DataTable architecture

**Verdict: B — several compatible systems, converging on one canonical table.**

## 13.1 The canonical table

`frontend/src/v3/components/ui/DataTable.jsx` (211 lines):
- Server pagination contract: `total` / `limit` / `offset` + `onPage` (CL-58); renders
  Prev/Next + page-size select + "x–y of z" count.
- Client pagination mode (`clientPaginate`, BL-2) for bounded, fully-loaded per-org lists; sorting
  applies before slicing so page+sort stay coherent.
- Sorting: client (`sortValue`) and server-controlled (`onSortChange`/`sortKey`/`sortDir`, BL-4).
- Accessibility: `<caption>`, `scope="col"`/`scope="row"`, `aria-sort`, sort-button semantics.
- Consumers (14, excluding tests): admin tabs (Activity, CustomFactors, Facilities, Locations,
  Suppliers, Vehicles), customer (Documents, Emissions, Processing, Review), ops
  (AuditConsole, IssuesTriage), reports (ReportsPage).

## 13.2 The parallel table

`v3-ops-table` (ops.css) — hand-rolled `<table className="v3-ops-table">` used by **11 files**:
OperatorQueue, ReviewQueue, QcQueue, OpsDashboard, PEManagerDashboard, ProcessingEntitiesTab,
EntityExtractionWorkspace, SlaTab, StaffRoster, StaffRolesTab, ConsultantTeamTab.
`ReviewQueue.jsx:80-115` duplicates DataTable's pagination bar markup (count, Prev/Next,
page-size select) by hand with `v3-btn v3-btn-sm` — the same classes DataTable itself uses.

## 13.3 Raw tables

22 V3 files contain raw `<table>` markup (admin Members/Security, consultant page/WhiteLabel,
customer Dashboard/Billing/Issues/ExistingData, ops Commercial/Dashboard, etc.).

## 13.4 Assessment

- One canonical reusable system exists (A-quality component), but adoption is partial (14 of ~29
  table-bearing V3 files). Ops queues — the highest-volume operational tables — use the parallel
  `v3-ops-table`, duplicating pagination logic and drifting from the shared contract.
- Classification: **TECHNICAL DEBT / ARCHITECTURE GAP** (convergence issue, not a defect in
  DataTable itself). Not a blocker; queue tables are paginated and bounded.
- Admin app tables are a separate system entirely (react-table) — part of the §17 admin gap.

| Loading / Empty / Error | `ui/StateViews.jsx` (`LoadingState`, `ErrorState`, `EmptyState`, `PermissionState`) | reused, but pages also define local equivalents |
| Toast | `react-hot-toast` (app-level, `App.js`) | single global toast lib |
| Status badge | `ui/StatusBadge.jsx` + `ui/statusConfig.js` | canonical status mapping |

## 12.3 Quantitative

- 12 V3 UI primitive files; 6 workbench files; 6 V3 root components (`RoleRoute`, `V3Layout`,
  `SearchBox`, `StateViews`, `EvidenceTrail`, `EvidenceRecordPanel`).
- 3 competing component systems; 2 additional legacy styling layers (`src/css/*`, per-component
  CSS files).
- 152 total JSX files in `frontend/src`; 67 V3 page/component files.
- 23 legacy root components still present (UploadManager, BulkUpload, PDFIngestionPortal,
  ManualEntryStandalone, LandingPage, …) — partially routed, partially dead (e.g. unrouted
  `Dashboard` function at `App.js:498`).

---

# 14. Pagination / search / sorting / filtering

## 14.1 The traced path (representative)

```
Ops ReviewQueue: UI table → frontend/src/v3/api.js getReviewQueue({limit,offset})
  → GET /api/v3/ops/queues/review?limit=25&offset=0 (v3_operations.py:1834-1930)
  → repositories (review_queue.py) → SQL LIMIT/OFFSET + COUNT → {items, total}
  → ReviewQueue renders hand-rolled pagination (offset-based) → next load(limit, offset+limit)
```

## 14.2 Findings

- **Server-side pagination is the V3 standard**: `limit` + `offset` + `total` across ops queues,
  consultant lists, organizations, reports, processing workflow and search. Consistent contract —
  VERIFIED.
- **Page-size bounds exist**: e.g. search `limit` capped (ge=1, le=50); queues default 25 with
  options 10/25/50/100. VERIFIED.
- **DB support exists**: dedicated indexes (`dpq_org_created_idx`, `emissions_logs_org_start_date_idx`,
  `notifications_unread_recipient_idx`, v3m11 batch). VERIFIED.
- **Search** is server-side and org-scoped (`/api/v3/search`, `SearchBox` in V3Layout); the
  frontend never holds a full search corpus. VERIFIED.
- **Client-side processing** is used only for bounded per-org lists via `DataTable clientPaginate`
  (BL-2), with honest row counts (no fake totals). VERIFIED.
- **Two pagination implementations coexist** (DataTable built-in vs hand-rolled in ReviewQueue/
  QcQueue/OperatorQueue) but share the same offset contract — TECHNICAL DEBT (no contract
  divergence, only markup duplication).
- **N+1 patterns:** not demonstrated in the traced V3 paths (repositories use explicit joins/
  grouped aggregation per `infra/supabase.py` design). Legacy routes not exhaustively audited —
  FUTURE RECOMMENDATION (out of first-pass scope).
- **Unbounded queries:** none found in the V3 paths traced. Legacy lists (e.g. `routes/admin/*`)
  were not exhaustively audited — UNVERIFIED, FUTURE RECOMMENDATION.


---

# 15. D19 Workbench

**Verdict: coherent and reusable.**

| Component | File | Role |
|---|---|---|
| `WorkbenchShell` | `v3/components/workbench/WorkbenchShell.jsx` | Top workflow nav + pane presets (40/60, 50/50, 60/40) + secure source pane + status/lock/autosave indicators + actions + tray flow on mobile (D20) |
| `WorkflowNav` | `WorkbenchShell`/`WorkflowNav.jsx` | Horizontal stepper; `DEFAULT_STAGES` = Queue → Extract → Map → Validate → Review → QC → Evidence; complete/current/upcoming states; `aria-current` |
| `SplitPane` | `SplitPane.jsx` | Preset split with labels |
| `SecureDocumentViewer` | `SecureDocumentViewer.jsx` | Role-scoped, signed-URL viewer; download affordance controlled by `allowDownload` (PE no-download boundary server-side) |
| `AutosaveIndicator` | `AutosaveIndicator.jsx` | Save state surface |
| `ConfidenceBadge` | `ConfidenceBadge.jsx` | Extraction-confidence presentation |

**Consumers:**
- `v3/customer/ProcessingItemWorkspace.jsx` — customer stage list
  (extract→map→validate→calculate→review→approve→evidence) — **reuses the shell with a
  role-specific stage set.**
- `v3/ops/WorkItemWorkspace.jsx` — internal operator/reviewer workspace.
- `v3/ops/ExtractionPanel.jsx` — document viewer + multi-line extraction + factor picker (D23),
  used by both ops and PE workspaces.
- `v3/customer/ReviewDetailPage.jsx` — review/approval presentation.

**Assessment:** The workbench is the strongest example of cross-role reuse in the codebase:
customer, internal ops, and PE all compose `WorkbenchShell`/`WorkflowNav`/`ExtractionPanel` with
stage lists and authorization scopes that differ per role — exactly the D19 intent. VERIFIED.
No inconsistency found beyond queue components using `v3-ops-table` instead of `DataTable` for
their list views (covered in §13).


---

# 16. Cross-role UX consistency

## 16.1 Consistent (verified)

- **Shell:** single `V3Layout` for customer/consultant/staff/PE surfaces (top nav, brand, org
  context, search box, mobile drawer). Staff/consultant badges; sign-out.
- **Route guarding:** single `RoleRoute` fail-closed pattern everywhere.
- **State/error vocabulary:** `StateViews` (Loading/Error/Empty/Permission), friendly error copy
  in `v3Fetch`, no raw backend messages.
- **Status presentation:** `StatusBadge`/`statusConfig` + `v3-ops-badge` share the same status
  vocabulary across roles.
- **Workbench:** shared across customer/ops/PE.
- **Navigation principle (CL-59):** queues open into dedicated routed workspaces across ops,
  customer and consultant — consistent.
- **Business-first formatting:** e.g. `formatCo2` in ConsultantPage ("t CO₂e" / "kg CO₂e");
  reviewer display names instead of UUIDs in ReviewQueue (UH-7).

## 16.2 Inconsistent (significant, evidence-backed)

| Area | Evidence | Classification |
|---|---|---|
| Tables | Ops queues/roster/PE dashboards use `v3-ops-table`; customer/admin/reports use `DataTable`; admin app uses react-table | TECHNICAL DEBT / ARCHITECTURE GAP |
| Tab bars | Ops hub rolls its own `v3-ops-tabs`; admin hub rolls its own tab bar; `ui/Tabs.jsx` exists but is not the hub mechanism | TECHNICAL DEBT |
| Pagination markup | DataTable built-in vs hand-rolled bars (ReviewQueue:103-115) | TECHNICAL DEBT |
| Loading/Empty blocks | `StateViews` vs local `LoadingBlock`/`ErrorBlock` (ConsultantPage) | TECHNICAL DEBT |
| Admin surface split | Modern `/ops` admin tabs vs legacy `admin/` app (different stack + direct Supabase) | ARCHITECTURE GAP |
| Legacy embedded upload | Legacy `UploadManager`/`BulkUpload`/`PDFIngestionPortal` inside an unrouted legacy `Dashboard` function (App.js:498) vs V3 upload path | TECHNICAL DEBT / USABILITY (dead-path risk) |

## 16.3 Not flagged (intentional role differences)

- Customer approval gates (owner/admin), consultant client-switcher, PE manager dashboard vs work
  surface, staff-only queues — all deliberate role-specific surfaces per the ratified model.

---

# 17. Architecture gaps

| # | Gap | Evidence | Severity |
|---|---|---|---|
| G1 | **Legacy admin app bypasses FastAPI** — direct Supabase reads/writes (`supabase.from('staff_profiles')`, `manual_review_queue` updates + `review_audit_trail` inserts) with no application-level authorization layer, no V3 error envelope, third component stack | `admin/src/services/reviewService.js`, `admin/package.json`, `admin/src/App.js` | HIGH |
| G2 | **Dead/parallel review-queue API family** — `/api/v3/admin/review-queue*` (v3_review.py) has zero frontend consumers; ops review lives at `/api/v3/ops/queues/review` + `/api/v3/ops/review/*` | grep `/api/v3/admin` in `frontend/src` (empty); `v3_review.py` prefixes | MEDIUM |
| G3 | **Unused QC admin client surface** — `getQcQueueAdmin`/`getQcStats`/`qcReviewItemAdmin` exported in `v3/api.js`, no page consumer; parallel `/api/v3/qc/queue` vs `/api/v3/ops/queues/qc` | `frontend/src/v3/api.js:702-716`; page grep | LOW |
| G4 | **Table-system fragmentation** — canonical `DataTable` (14 consumers) vs hand-rolled `v3-ops-table` (11 files) vs raw tables (22 files) vs admin react-table | §13 | MEDIUM |
| G5 | **Document state duality** — `customer_documents.extracted_data/mapped_data/calculated_emissions_kg_co2e` JSONB alongside `document_processing_queue` durable job columns + `manual_extraction_items` | `v3_schema.sql:853-905, 1103-1167, 1799-1831` | MEDIUM (provenance risk) |
| G6 | **Single 1,473-line flat API client** — `v3/api.js` (~239 exports) mixes all domains; `services/` has only 4 files | `frontend/src/v3/api.js` | MEDIUM (maintainability) |
| G7 | **Legacy surface still mounted** — 405 legacy endpoints + 23 legacy root components; unrouted legacy `Dashboard` function (App.js:498) embeds upload/manual-entry paths | `backend/main.py:211-261`, `frontend/src/App.js` | LOW-MEDIUM (INTENTIONAL transitional, but dead-path risk) |
| G8 | **Audit/activity table proliferation** — 12+ audit-family tables with overlapping purpose | §3.1 | LOW (INTENTIONAL per PO) |

---

# 18. Technical debt

- **Component duplication:** local `LoadingBlock`/`ErrorBlock`/tab-bars/table-markup vs shared
  primitives (ConsultantPage, ops hubs).
- **Pagination markup duplication** between DataTable and queue components.
- **Wide legacy tables** (`organizations` ~70 cols, `organization_metadata` ~30 cols) and JSONB
  metadata sprawl on core tables.
- **Legacy business logic parallel to V3 engines** (`process_emissions.py`, `report_generator.py`,
  `pdf_engine.py`, legacy `routes/emissions.py` vs `v3_emissions.py`).
- **Large page components:** `ConsultantPage.jsx` 1,092 lines; `v3_operations.py` (39 endpoints in
  one module); `v3/api.js` 1,473 lines.
- **MUI dependency** retained solely for two public demo components.
- **Dead code:** unrouted legacy `Dashboard` in App.js; unused admin helpers in api.js.

---

# 19. Intentional differences (ratified / PO intent — not defects)

- V3 canonical; legacy remains temporarily for compatibility (dual-surface main.py).
- Customer/consultant processing (`/api/v3/processing/*`) separate from internal operations
  (`/api/v3/ops/*`); calculation snapshots are API-only for consultants.
- Audit/activity tables remain separate (immutability migration applies).
- FORCE RLS deferred to a separate security investigation.
- Consultant Owner/Admin/Manager may revoke consultant-client relationships; Member/Viewer cannot;
  revocation preserves client data.
- DataSecurity is a public page.
- PE application separation (entity-scoped workspace; no PE manual-extraction access).
- Customer Owner may self-approve custom factors (PO decision §16 of AGENTS.md).
- `system_admin` is a superset of `admin` (can_manage_billing added in v3m8 migration).

---

# 20. Future architecture recommendations

> These are input for a later architecture decision — **no implementation was performed.**

1. **Converge the admin control plane** onto the FastAPI V3 surface (or a dedicated `/admin`
   control-plane surface per the ratified separation), eliminating direct Supabase access from
   `admin/`. Decide whether to migrate `admin/` functionality into the main app or rebuild it on
   the V3 API + D21 primitives (PO DECISION REQUIRED — see §21).
2. **Standardize tables on `DataTable`** (or a single queue-table extension of it) across ops,
   consultant and admin tables; remove hand-rolled `v3-ops-table` pagination markup.
3. **Retire dead endpoint families** (`v3_review.py` review-queue family or its ops counterpart;
   unused QC admin helpers) once ownership is confirmed.
4. **Resolve document-state duality** (customer_documents JSONB vs document_processing_queue
   durable columns) so a single authoritative processing record exists.
5. **Split `v3/api.js` into domain service modules** (mirroring `backend/data/*` domains) while
   preserving the `v3Fetch` contract.
6. **Define a single table/pagination contract** across V3 (limit/offset/total is already uniform)
   and document it as the public contract for new endpoints.
7. **Add regression coverage for the identified dead/parallel endpoint families** and for
   cross-role table rendering (allow/deny + rendering parity).


---

# 21. PO decisions required

1. **Admin control-plane strategy:** migrate the legacy `admin/` app (Users/Organizations/Reviews/
   DefraFactors/WorkHub…) into the main React app on the V3 API + D21 primitives, rebuild it as a
   separate `/admin` surface on the V3 API, or keep it as-is with direct Supabase access (not
   recommended — bypasses FastAPI authorization). This is a PO decision, not an implementation
   choice.
2. **Dead endpoint retirement:** confirm which review-queue family (`/api/v3/admin/review-queue`
   vs `/api/v3/ops/queues/review`) and which QC family are canonical before removal.
3. **Document-state single source:** approve moving all processing state to
   `document_processing_queue` durable columns (retiring customer_documents JSONB mirrors) or
   formalize the current duality.
4. **Legacy surface cutover timeline:** explicit PO/plan decision on when legacy routes
   (`routes/**`) and legacy components can be removed.
5. **Table standard enforcement:** confirm the shared `DataTable` (+ queue extension) as the sole
   operational table component across all roles.

---

# 22. Overall architecture assessment

## Database
**Coherent.** Clear tenant root (`organizations`), consistent RLS helper functions, additive V3
migrations, first-class PE/consultant/issues/durable-processing domains, targeted indexes.
Wide legacy columns and JSONB sprawl are manageable debt. Confidence: high.

## Backend
**Appropriately separated for V3.** Routers are thin; repositories are the only DB path; engines
own business rules; authorization is centralized and server-side; a durable worker implements the
automatic pipeline. The legacy surface and the `admin/` app bypass this discipline. Confidence: high.

## API
**Contracts consistent within V3** (error envelope, limit/offset/total pagination, bearer auth).
Legacy/V3 overlap is intentional but two families are dead/duplicated. Confidence: high.

## Frontend
**Reusable component architecture exists and is used** (D21 primitives + DataTable + WorkbenchShell),
but three systems compete and adoption is partial. The single flat API client is a maintainability
concern. Confidence: high.

## Workflows
**End-to-end workflows are coherent and server-driven** across customer, consultant, PE and
internal ops; state machines persist in the DB and the UI reflects server state. The main
inconsistencies are presentational (tables) rather than functional. Confidence: high.

## Scalability
V3 queue/table architecture is paginated, indexed and bounded; search is server-side. Legacy
routes were not exhaustively audited (unbounded queries not proven). Overall: acceptable today,
with convergence required before the legacy surface grows further. Confidence: medium-high.

## Maintainability
Technical debt is concentrated in: the `admin/` app bypass, `v3-ops-table` duplication, the flat
`v3/api.js`, legacy parallel logic, and very large single-file components/modules. Confidence: high.

## AI-generated duplication
Evidence supports **independently generated screens composed around shared primitives**: the D21
`ui/` library + WorkbenchShell are clearly shared, but ops/consultant/admin pages each hand-roll
local helpers (loading blocks, tab bars, tables, pagination markup) rather than composing the
shared components, and the `admin/` app is a fully independent stack. This is consistent with
screen-by-screen generation converging onto a shared core over time. Confidence: medium.

## Final classification summary

| Class | Count | Key items |
|---|---|---|
| VERIFIED DEFECT | 3 | Dead review-queue API family; unused QC admin client; unrouted legacy Dashboard/dead-path |
| ARCHITECTURE GAP | 5 | Admin app bypass (G1); table fragmentation (G4); document-state duality (G5); dead families (G2/G3); admin surface split |
| TECHNICAL DEBT | 7 | component/tab/table duplication; wide tables; legacy parallel logic; flat api.js; large files; MUI-for-demos |
| INTENTIONAL | 9 | §19 list |
| FUTURE RECOMMENDATION | 7 | §20 list |
| PO DECISION REQUIRED | 5 | §21 list |

---

## Appendix A — Quantitative data

- V3 API endpoints: **290** (43 modules) · Legacy endpoints: **405** (50 modules)
- Supabase migrations: **41** · Base tables in `v3_schema.sql`: **104**
- Backend: **36 data repositories**, 25 domain modules, 12 engines, 8 services, 1 worker,
  43 API modules, 50 legacy route modules, **148 tests**
- Frontend: **152 JSX files** (67 V3), 12 V3 UI primitives, 6 workbench files, 6 V3 root
  components, 4 service files, 1 flat API client (~239 exports), **17 tests**
- DataTable consumers: **14** · `v3-ops-table` files: **11** · raw `<table>` files: **22**
- Competing component systems: **3** (D21 ui/ · v3.css/ops.css utilities · admin/ stack) + MUI
  (2 demo components only)
- Major API pagination patterns: **1** (limit/offset/total) in V3; **2** markup generations
- Admin app: separate CRA (port 3001, proxy 8000), routes `/admin/*` + `/staff-dashboard`,
  deps include react-table/react-hook-form/react-select/tailwindcss/chart.js

## Appendix B — Safety check

Confirmed before and after this investigation:

- ✅ No application files modified (only this report file created, as instructed)
- ✅ No database changes · no migration changes · no RLS changes
- ✅ No package changes · no configuration changes · no tests changed · no Docker changes
- ✅ No commits · no pushes
- ✅ All investigation commands were read-only
