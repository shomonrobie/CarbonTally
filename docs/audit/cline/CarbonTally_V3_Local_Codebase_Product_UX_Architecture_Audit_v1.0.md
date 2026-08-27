---
Document Type: Local Codebase Product / UX Architecture Audit
Project: CarbonTally
Architecture: CarbonTally V3 (Supabase + Render FastAPI + Lovable)
Version: 1.0
Status: FINAL
Audit Mode: READ-ONLY
Created: 2026-08-15
Author: Cline
Target: Lovable frontend build preparation
---

# CarbonTally V3 — Local Codebase Product / UX Architecture Audit

**Mode:** READ-ONLY. No files created, no files modified, no database/Supabase/migrations/API/frontend changes.

## SECTION 1 — Executive summary

The local repository contains **three deployable surfaces plus a rich database schema**, but they are not all wired together:

1. **`frontend/`** — the customer-facing React app (CRA 5, React 18, react-router-dom v7, MUI v9, Recharts, react-pdf, axios, `@supabase/supabase-js`). It is largely a single-file app (`App.js`, ~1,945 lines) plus a handful of page components and two contexts.
2. **`admin/`** — a separate internal staff/admin React app (CRA 5, React 18, react-router-dom v6, Tailwind, TanStack Query, react-hook-form, chart.js). It has a proper page/route structure.
3. **`backend/`** — FastAPI with **two independent application objects**:
   - `backend/main.py` → `main:app` — the **live/legacy monolith** that Render runs. It exposes the `routes/` tree and uses the Supabase **service-role** client directly.
   - `backend/main_v2.py` → `api/router.py` `create_app()` — a **v2.1 "engine" API** (`api/`, `engines/`, `domain/`, `data/`, `infra/`, `core/`) that is **NOT imported by `main.py`** and therefore not deployed.
4. **Database** — `CarbonTally_DB_Schema_V3M2.sql` + `supabase/migrations/` + `database/rc1|rc2/` define a schema **substantially ahead of the deployed API**: it includes `consultant_profiles`, `consultant_clients`, `consultant_firm_members`, `consultant_tasks`, `manual_extraction_batches`, `manual_extraction_items`, `processing_entities`, `customer_factors`, `factor_aliases`, `issues`, and RLS helper `is_org_consultant()`.

**Headline finding:** The **database is a V3 schema with multi-client consultant and external-processing-entity concepts, but the deployed backend (`main.py`) and both frontends implement only the original single-org customer + internal-staff model.** Consultant multi-client, external manual processing companies, and true split-screen source↔form workflows do **not** exist in the application layer.

## SECTION 2 — Current architecture

| Layer | Technology | Notes |
|---|---|---|
| Frontend (customer) | React 18 + CRA 5 + react-router-dom v7 + MUI v9 + Recharts + react-pdf + xlsx | `frontend/src/App.js` monolith + page components |
| Frontend (internal) | React 18 + CRA 5 + react-router-dom v6 + Tailwind + TanStack Query + chart.js | `admin/src/` with route/page structure |
| Backend (live) | FastAPI `backend/main.py` (`main:app`) | `routes/`, `routes/admin/`, `routes/organizations/`, `auth.py`, `database.py` |
| Backend (not wired) | FastAPI `backend/main_v2.py` (`api/router.py`) | `api/`, `engines/`, `domain/`, `data/`, `infra/`, `core/` |
| Auth | Supabase Auth (GoTrue) via `@supabase/supabase-js` (client) and `supabase-py` (backend) | JWT bearer, service-role on backend |
| Database | Supabase Postgres + RLS | Rich schema (V3M2), RLS tenant policies |
| Storage | Supabase Storage bucket `documents` | Backend-only (service role) |
| Realtime | Supabase Realtime | `frontend/src/lib/realtime/manager.js` + `RealtimeContext` (both apps) |
| Background processing | **None** (no Celery/RQ/worker; processing is synchronous in request handlers) | see §11 |
| PDF/OCR | `pdfplumber`, `pytesseract`, `pdf2image`, `reportlab` (OCR is Windows/lazy, not production-ready) | `pdf_engine.py`, `upload.py` repair endpoint |

## SECTION 3 — Authentication

| Capability | Status | Evidence |
|---|---|---|
| Email/password | IMPLEMENTED | `signUp` / `signInWithPassword` (`Login.js`, `BetaLogin.jsx`, `BetaSignup.jsx`); backend `get_current_user` verifies via `supabase.auth.get_user(token)` |
| Google OAuth | IMPLEMENTED | `signInWithOAuth({ provider: 'google' })` (`Login.js:168`) |
| Supabase Auth (session) | IMPLEMENTED | `@supabase/supabase-js` client; `AuthContext` (admin), session persisted by Supabase |
| Access-token handling | IMPLEMENTED | Bearer token → `auth.py` `get_current_user` |
| Refresh-token handling | IMPLEMENTED (implicitly) | handled by Supabase JS client; backend does not manage refresh |
| Password reset | IMPLEMENTED | `routes/users.py` `PasswordResetRequest/Confirm`; Supabase admin API |
| Magic link | IMPLEMENTED (frontend) | `MagicLink.jsx` → calls `/api/auth/magic`; backend endpoint not in `main.py` (stale) |
| MFA / TOTP | **NOT IMPLEMENTED** | no MFA references in code |
| Role detection | IMPLEMENTED | `auth.py`: staff (staff_profiles) vs org member (organization_members); roles table |
| Organization membership | IMPLEMENTED | `organization_members` |
| Consultant authentication | **NOT IMPLEMENTED** (schema only) | `consultant_profiles`/`consultant_firm_members` in SQL; no auth/route logic |
| Staff authentication | IMPLEMENTED | `staff_profiles`; admin app `isStaff` guard |

## SECTION 4 — Roles / personas

Implemented role model (`auth.py` + `staff_profiles` + `organization_members` + `roles`):

| Persona | DB | Backend | API access | UI | Permissions |
|---|---|---|---|---|---|
| Customer Owner | `organization_members.role='admin'` (no distinct owner) | PARTIAL (treated as org admin) | `require_org_admin` | PARTIAL | can_manage_members etc. via `DEFAULT_ORG_PERMISSIONS` |
| Customer Admin | `organization_members.role='admin'` | IMPLEMENTED | `require_org_admin` | PARTIAL | org CRUD |
| Customer Member/Editor | `organization_members.role='editor'` | IMPLEMENTED | `require_org_member` | PARTIAL | view/edit org data |
| Customer Viewer | `organization_members.role='viewer'` | IMPLEMENTED | `require_org_member` | PARTIAL | view |
| Consultant Owner/Admin | `consultant_profiles`, `consultant_firm_members` | **NOT CURRENTLY IMPLEMENTED** (schema + RLS only) | — | — | — |
| Consultant | `consultant_firm_members` | **NOT CURRENTLY IMPLEMENTED** | — | — | — |
| Consultant Analyst/Staff | (no explicit role) | **NOT CURRENTLY IMPLEMENTED** | — | — | — |
| CarbonTally Super Admin | `staff_profiles.role='admin'` | IMPLEMENTED | `require_admin` | IMPLEMENTED (admin app) | full |
| CarbonTally Operations Manager | (no distinct role; ≈ admin/staff) | **NOT EXPLICITLY IMPLEMENTED** | — | — | — |
| CarbonTally Data Entry Operator | `staff_profiles.role='data_extractor'` | PARTIAL | `require_role([...])` | PARTIAL (Reviews/ManualReviewQueue) | extraction |
| CarbonTally Reviewer | `staff_profiles.role='data_approver'` (≈) | PARTIAL | reviews endpoints | PARTIAL | approve |
| CarbonTally QC Operator | **NOT CURRENTLY IMPLEMENTED** (no QC role; only `accuracy_rate`/`quality_score` fields) | — | — | — | — |
| CarbonTally Support | **NOT CURRENTLY IMPLEMENTED** | — | — | — | — |
| Processing Company Owner/Admin | `processing_entities` (entity, not persona) | **NOT CURRENTLY IMPLEMENTED** in `main.py`; v2.1 `admin_entities` only | — | — | — |
| Processing Operator | `manual_extraction_items` (data model only) | **NOT CURRENTLY IMPLEMENTED** | — | — | — |
| Processing QC | `manual_extraction_items.quality_score` (field only) | **NOT CURRENTLY IMPLEMENTED** | — | — | — |

Roles are enforced by FastAPI dependency factories in `auth.py`: `require_admin`, `require_staff`, `require_role`, `require_permission`, `require_any/all_permissions`, `require_org_member`, `require_org_admin`, `require_auth`, plus `require_entity_member` (v2.1 layer only).

## SECTION 5 — Customer architecture

**Implemented:** single-organization customer model.

- `organizations` (management.py), `organization_members` (members.py), `facilities` + `assets` (assets.py), emissions data (data.py, emissions.py), analytics (analytics.py), dashboard (dashboard.py), files (files.py), team (team.py), metadata (metadata.py), exports (exports.py), bulk (bulk.py).
- Frontend: LandingPage, OnboardingWizard, CompanyNamePrompt, TeamManagement, AssetManager, BulkUpload, PDFIngestionPortal, UploadManager, ManualEntryStandalone, DocumentStatus, OrganizationMetadata, RecentProcessedData, CarbonReductionPlan, Glossary, BetaSignup/BetaLogin/MagicLink, chat widget.
- Customer verification (approve/reject extracted values) exists via `customer_documents.py` (`VerificationRequest`, verified_by/at, stats) and a **stale, unwired** `customer_verifications.py` module.

**Missing:** no owner/admin separation beyond the `role` string; no cross-org or multi-org customer view.

## SECTION 6 — Consultant / multi-client architecture

**Status: NOT implemented in the application layer — schema + RLS only.**

- **Schema (exists):** `consultant_profiles`, `consultant_clients` (consultant↔organization many-to-many), `consultant_firm_members` (firm team), `consultant_tasks`, `consultant_billing`; RLS function `is_org_consultant(org_id)` and tenant SELECT policies that union `is_org_member(...) OR is_org_consultant(...)` on virtually every org table.
- **Backend (absent):** no consultant routes in `main.py`; the only reference is a comment in `organizations/members.py` ("Future: multi for consultants", response `mode: "single"`).
- **Frontend (absent):** no client context, no client switcher, no consultant workspace.
- **Access enforcement:** RLS supports consultant read at the DB layer, but the deployed backend uses the **service role** (which bypasses RLS), so consultant access is not enforced anywhere in the live app.

## SECTION 7 — CarbonTally internal operations

**Implemented (admin app + `routes/admin/`):**

- Dashboard, Reviews, Users, Organizations, Batches, Analytics, Settings, DefraFactors, Customers, ManualReviewQueue, ExtractionErrorReview, BetaManagement, GlossaryManagement, StaffDashboard, StaffReviewQueue, LogViewer, AdminAssignment, WorkHub.
- Backend: staff, defra, extraction, reviews, assignments, permissions, workload (+ forecast), beta, audit, review_history, admin logs, bulk, email_templates, analytics, settings.

**Not implemented:** dedicated Operations Manager / Support roles; QC role.

## SECTION 8 — Manual data processing company support

**"External Manual Data Processing Company" is not currently implemented in the local codebase** as a product concept.

What does exist (adjacent, at the data layer):

- `processing_entities` table (V3M1/V3M2) — a generic "processing entity" with lifecycle statuses `active | remediation | suspended | terminated`, plus `entity_id` FKs on various tables and entity-scoped RLS.
- `manual_extraction_batches` + `manual_extraction_items` tables (currency, total_cost, total_documents, total_pages, quality_score, calculated_emissions_kg_co2e, page_count) — a batch/item data model for outsourced extraction.
- v2.1 `api/admin_entities.py` (processing-entity CRUD, `/api/v2/admin/entities`) — **not** wired into `main.py`.
- No operator/QC UI, no assignment, no billing flow, no vendor management in either frontend.

## SECTION 9 — Data-entry workflow

The internal staff "review/extraction" workflow exists, but it is **not** a source-document↔form split-screen:

- Backend: `routes/admin/reviews.py` (queue, assign, complete, escalate, SLA monitor), `assignments.py` (available/staff/batch assign), `workload.py` (workload, queue settings), `extraction.py` (extraction approval). Queue table: `manual_review_queue` (status pending/assigned/in_progress/completed/rejected, priority, assigned_to, sla_deadline, auto/manual extraction result JSON).
- Frontend (admin): Reviews, ManualReviewQueue, StaffReviewQueue, WorkHub.
- Customer manual entry: `ManualEntryStandalone.jsx` — a **table/CSV** entry UI, not document-linked.

| Sub-capability | Status |
|---|---|
| Existing viewer | PARTIAL (PDF is a public URL; `react-pdf` declared but no dedicated viewer) |
| Extraction form | PARTIAL (JSON result forms) |
| Assignment | IMPLEMENTED |
| Save/submit | IMPLEMENTED |
| Next-item workflow | PARTIAL (queue, no explicit "next") |
| Page navigation / zoom | NOT IMPLEMENTED |
| OCR in-form | NOT IMPLEMENTED (OCR only in `repair-pdf` backend endpoint) |
| Bounding boxes / source coordinates | **NOT IMPLEMENTED** (no such data model) |

## SECTION 10 — Customer verification workflow

**Partial.**

- Backend: `customer_documents.py` verification endpoints (`/stats/{org_id}`, `/pending/{org_id}`, verify/approve/reject with `VerificationRequest`, verified_by/verified_at, review_request). Also a **stale** `customer_verifications.py` route module (not imported by `routes/__init__.py`).
- Frontend: `DocumentStatus.jsx` (status display); no rich "source ↔ interpretation" split-screen.
- Missing: mapped values vs factor vs calculation display side-by-side, confidence/issues/comments UI, approval-with-correction flow.

## SECTION 11 — Review / QC workflow

**Review: implemented (internal).** Queue, assignment, completion, escalation, SLA monitoring, assignment history (`review_assignment_history`), reassignment, workload. Admin UI pages exist.

**QC: not implemented as a workflow.** There is no QC queue, QC checklist, QC error model, or QC role. Only `accuracy_rate` (staff_profiles) and `quality_score` (manual_extraction_items schema) fields exist.

True split-screen (source ↔ extracted/mapped/calculated + QC checklist) is **not technically possible** today because:
1. No extraction coordinates/bounding boxes exist.
2. No document viewer component in either frontend.
3. Mapping/calculation results are stored as JSON blobs (`auto_extraction_result`, `manual_extraction_result`, `metadata`), not a typed, queryable extraction-mapping-calculation chain.


## SECTION 12 — API capability map (deployed `main.py`)

| Capability | Endpoints | Method | Auth | Roles | Tables | Frontend |
|---|---|---|---|---|---|---|
| AUTHENTICATION | `/api/users/*` (reset, profile), auth via Supabase | GET/POST | Bearer | any | auth.users | Login/BetaLogin/MagicLink |
| HEALTH/SYSTEM | `/`, `/health`, admin `/system/health|performance|usage` | GET | —/admin | — | — |
| DOCUMENT UPLOAD | `/api/upload`, `/api/test-upload`, `/api/repair-pdf` | POST | Bearer | org member | organization_files, upload_batches | UploadManager, BulkUpload, PDFIngestionPortal |
| DOCUMENT PROCESSING | `/api/documents/*` (documents_main, document_activity) | GET/POST | Bearer | org member | organization_files, customer_documents | DocumentStatus |
| BATCH PROCESSING | `/api/batches/*` (upload.py), `/api/upload-batch` | GET/POST | Bearer | org member | upload_batches | BulkUpload |
| EXTRACTION | `/api/admin/extraction/*` (approval) | POST | admin | admin/staff | manual_review_queue | admin ExtractionErrorReview |
| MAPPING / FACTOR MATCHING | **legacy none in main.py**; v2.1 `/api/v2/factor-match` (not wired) | — | — | — | emission_factors | — |
| CALCULATION | `utils/emissions.py` + `process_emissions.py`; v2.1 `/api/v2/calculate` (not wired) | — | — | — | emissions_logs | ManualEntryStandalone (client-side DEFRA map) |
| VALIDATION | v2.1 `/api/v2/validate` (not wired) | — | — | — | — | — |
| REVIEW | `/api/admin/reviews/*` (queue/assign/complete/escalate/SLA) | GET/POST | admin | admin/staff | manual_review_queue | admin Reviews/ManualReviewQueue/StaffReviewQueue |
| QC | **none** | — | — | — | — | — |
| CUSTOMER VERIFICATION | `/api/customer-documents/*` (stats/pending/verify) | GET/POST | org member | org member | customer_documents | DocumentStatus |
| REPORTING | `/api/reports/*` + report_generator | GET/POST | org member | org | organizations, emissions | — |
| EXPORT | org `/exports/*`, admin audit/performance export | GET | org/staff | — | — | — |
| SUPPLIERS | **no supplier route in main.py** (schema has `suppliers`) | — | — | — | suppliers | — |
| FACILITIES/ASSETS | `/api/organizations/{org_id}/facilities|assets` | GET/POST/PUT/DELETE | org admin/member | org | facilities, assets | AssetManager |
| ORGANIZATIONS | `/api/organizations/*` (management) | CRUD | org admin | org | organizations | OnboardingWizard |
| MEMBERS | `/api/organizations/members/*` | CRUD | org admin | org | organization_members | TeamManagement |
| CONSULTANTS | **none in main.py** | — | — | — | consultant_* | — |
| CLIENTS | **none** | — | — | — | consultant_clients | — |
| MESSAGING | chat widget (frontend), `/api/notifications/*` (email); realtime messages | — | — | — | conversations, messages | ChatWidget |
| NOTIFICATIONS | `/api/notifications/*` (Resend email) | POST | org | — | — | RealtimeContext |
| ISSUES | v2.1 `/api/v3/issues` (not wired) | — | — | — | issues | — |
| PROCESSING QUEUES | reviews/assignments/workload (`manual_review_queue`) | GET/POST/PUT | admin | staff | manual_review_queue | admin |
| STAFF | `/api/admin/staff/*` (CRUD, performance, compare) | CRUD | admin | admin | staff_profiles | admin Users |
| SLA | reviews SLA monitor, workload queue settings | GET/PUT | admin | admin | queue_settings | admin Settings |
| PERFORMANCE | `/api/admin/staff/performance*`, analytics | GET | admin | admin | staff_workload | admin Analytics |
| ADMIN | permissions, beta, audit, review_history, logs, bulk, email_templates, settings, defra | CRUD | admin | admin | roles, audit_logs, etc. | admin pages |

The v2.1 engine endpoints (`/api/v2/factor-match|calculate|validate|report`, `/api/v3/customer-factors`, `/api/v3/issues`, `/api/v2/admin/{entities,aliases,imports,providers,audit}`) are **implemented in code but not reachable** because `main_v2.py` is a separate entrypoint.

## SECTION 13 — Database → API → Frontend trace

| Workflow | DB | FastAPI (live) | Frontend | Verdict |
|---|---|---|---|---|
| A. Upload | organization_files, upload_batches, storage | upload.py | UploadManager/BulkUpload | COMPLETE |
| B. Document processing | manual_review_queue, customer_documents | documents_main/document_activity | DocumentStatus | PARTIAL |
| C. Extraction | manual_review_queue JSON | extraction.py (approve) | admin | PARTIAL (no split-screen) |
| D. Mapping | emission_factors, factor_aliases | **v2.1 only (not wired)** | none | MISSING (live) |
| E. Factor matching | emission_factors + search_index | **v2.1 only** | none | MISSING (live) |
| F. Calculation | emissions_logs | utils/process_emissions | ManualEntryStandalone (client-side) | PARTIAL |
| G. Customer verification | customer_documents | customer_documents.py | DocumentStatus | PARTIAL |
| H. Reporting | organizations, emissions | reports.py + report_generator | none | PARTIAL (backend only) |
| I. Consultant/client | consultant_* (schema) | **none** | none | MISSING |
| J. Manual processing | manual_extraction_batches/items, processing_entities | **none (live)** | none | MISSING |
| K. QC | (accuracy_rate/quality_score fields) | **none** | none | MISSING |

## SECTION 14 — Split-screen capability

| Workflow | Technically supported now | Backend | Frontend | Data |
|---|---|---|---|---|
| 1. Data entry (source ↔ form) | NO | missing (no doc+form endpoint) | missing viewer+form | missing coords |
| 2. Customer verification (source ↔ result) | PARTIAL | partial (verify endpoints) | missing split UI | missing |
| 3. Reviewer (source ↔ extraction+mapping) | NO | partial (queue only) | missing | missing coords |
| 4. QC (source ↔ all + checklist) | NO | missing | missing | missing |

**Extraction coordinates / bounding boxes: DO NOT EXIST.** (Confirmed: no `bbox`/`coordinates`/`polygon`/`page_x`/`page_y` fields in any application schema or code — only Postgres geometry type catalogs inside `.tmp_pgdata` and a CSS class.)

## SECTION 15 — Missing functionality (major gaps)

1. Consultant multi-client workspace (UI + routes) — schema exists, app does not.
2. Client switching / client context.
3. External manual processing company (vendor + operator + QC) — schema partial, app absent.
4. True split-screen workflows (data entry / verification / review / QC).
5. Extraction bounding-box / coordinate model for source highlighting.
6. Typed mapping→calculation result model (currently JSON blobs).
7. QC workflow (queue, checklist, error taxonomy).
8. Dedicated Operations Manager / Support roles.
9. Suppliers API/UI (table exists).
10. Background/async processing (all synchronous).

## SECTION 16 — Security observations (report only)

1. `backend/.env` is **committed** and contains a real service-role secret; `SUPABASE_ANON_KEY` and `VITE_SUPABASE_ANON_KEY` are set to the **same service-role secret value**.
2. Backend uses the **service-role** Supabase client for every query (`database.py`, `auth.py`), which **bypasses RLS** — the rich RLS/consultant policies in the schema are not enforced by the live backend.
3. `frontend/src/supabaseClient.js` hardcodes the Supabase URL and anon key (publishable — acceptable, but should be env-driven).
4. Backend `.env` contains `REACT_APP_API_URL=http://localhost:8000` (dev assumption).
5. No MFA, no rate limiting wired into `main.py` (`middleware/rate_limit.py` exists but is not imported).

## SECTION 17 — Lovable readiness

**READY WITH CONDITIONS.**

- **Ready:** The live FastAPI OpenAPI spec (`main:app`) is complete and self-describing for the existing customer + staff surfaces; the schema is mature; auth and the core upload→review→verify→report loop are implementable.
- **Conditions/blockers for a full product build:**
  1. Consultant multi-client, processing-entity, QC, and supplier capabilities exist **only in the DB/v2.1 code**, not in the deployed API — Lovable cannot consume them from the live `/openapi.json`.
  2. No split-screen data model (bounding boxes) — source-highlighting UX cannot be built without backend/schema additions.
  3. Mapping/calculation results are unstructured JSON — weak contract for a Lovable UI.
  4. Backend `main.py` must start (the `staff.py` `Client` NameError and `workload.py` duplicate-module issues identified in the Render audit must be resolved) before Lovable can integrate against it.

## SECTION 18 — Recommended UI/UX architecture

(A proposed frontend-only information architecture for Lovable; not a redesign of the backend.)

- **Customer workspace:** upload → document status → verification (source ↔ extracted/mapped/calculated) → reports/exports → org/settings.
- **Consultant workspace:** firm dashboard → client list/switcher → per-client customer workspace (read/write per RLS).
- **CarbonTally admin workspace:** organizations/staff/factors/system (existing `admin/` app).
- **CarbonTally operations workspace:** review queue + assignment + workload (existing `admin/`).
- **Data entry / Review / QC workspaces:** a shared "split-screen" shell (left: document viewer with future coordinates; right: form) — new.
- **External processing company workspace:** batch/item queues + QC — new.

## SECTION 19 — Items that require backend changes

1. Expose consultant endpoints (multi-client) in the deployed app.
2. Expose processing-entity / manual-extraction batch+item endpoints.
3. Split-screen supporting endpoints (document page + field extraction with coordinates).
4. Typed extraction→mapping→calculation result contract.
5. QC workflow endpoints.
6. Wire `main_v2.py` engine endpoints (or port them into `main.py`).
7. Fix the Render blockers (staff.py `Client`, workload.py).

## SECTION 20 — Items solvable entirely in frontend

1. Customer verification approval/rejection UI (endpoints already exist).
2. Document status dashboards (data available).
3. Report viewing (report endpoints exist).
4. Org/assets/members/bulk management UI polish.
5. Realtime notifications UI (realtime manager already present).
6. Admin review queue/assignment UI (endpoints exist).
7. Workspace navigation/IA and empty states.

## SECTION 21 — Items that require schema changes

1. Extraction coordinates / bounding boxes (new columns or a new `extraction_spans` table) for source highlighting.
2. QC checklist / QC error taxonomy tables (if QC is not stored in existing JSON).
3. Consultant task/assignment detail beyond `consultant_tasks` (verify it meets workflow needs).
4. Supplier relationships if supplier UI becomes first-class.
5. (Verification) `manual_extraction_*` and `processing_entities` are already present — confirm column adequacy before adding UI.

## SECTION 22 — Recommended next steps

1. **Fix and redeploy the backend** (Render blockers from the prior audit) so Lovable has a live, stable `/openapi.json`.
2. **Decide the consultant & external-processing scope** — the schema is ready, but the API surface is not; a small backend increment is required before those workspaces can be built.
3. **Define the split-screen data contract** (bounding boxes / field spans) — this is the single biggest gap for the data-entry/review/QC UX.
4. **Port or expose the v2.1 engine endpoints** (factor-match / calculate / validate / customer-factors / issues) so the mapping/calculation/factor UX has a real API.
5. **Phase the Lovable build**: (P1) customer upload→verify→report; (P2) internal review/QC ops; (P3) consultant multi-client; (P4) external processing company.
6. **Remediate security** (rotate the exposed service-role key, remove `.env` from VCS, keep the backend on service role deliberately but document it).

---

**Bottom line:** The local V3 codebase implements a **single-organization customer + internal CarbonTally staff** product end-to-end. The **database** is already a V3 schema with consultant multi-client and external-processing-entity tables + RLS, but those capabilities are **not** in the deployed FastAPI (`main.py`), the v2.1 engine API is **not wired**, and **no split-screen/coordinate model exists**. Lovable can build the customer and staff workspaces now (with conditions); consultant, external-processing, and split-screen source-highlighting UX require backend/schema work first. Nothing was modified during this audit.

















