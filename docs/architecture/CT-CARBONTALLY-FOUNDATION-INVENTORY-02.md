# CT-CARBONTALLY-FOUNDATION-INVENTORY-02

## Phase 2 — Deep Surface Inventory: Routes, UI, Authorization, Commercial, Parity

| Field | Value |
|---|---|
| Task | CT-CARBONTALLY-FOUNDATION-INVENTORY-02 (Phase 2) |
| Mode | READ-ONLY INVENTORY |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Precondition | `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` present (72,782 bytes) — satisfied |
| Deliverable | this file (the only repository change) |
| Inventoried at | 2026-10-08 (local) |

### Classification key (applies to every statement below)

| Code | Meaning |
|---|---|
| A | Directly observed (command output captured this session) |
| B | Derived from source code |
| C | Derived from database schema/state |
| D | Derived from test results |
| E | Derived from runtime observation |
| F | Existing documentation / decision |
| G | Inference (explicitly labelled) |

### Provenance rule used throughout

`SOURCE STATE` (this git checkout) ≠ `RUNTIME STATE` (running processes) ≠
`DATABASE STATE` (two local databases) ≠ `TEST STATE` (Phase 1 baseline) ≠
`DOCUMENTED STATE` (repo docs). Where they disagree, the disagreement is
reported and **not** reconciled by choosing one.

---

# 1. EXECUTIVE SUMMARY

## 1.1 What Phase 2 established

| Dimension | Count | Class |
|---|---:|---|
| Backend HTTP operations actually registered by the FastAPI app (source) | **781** (775 under `/api/`) | A |
| Backend operations visible in the running instance's `/openapi.json` | **777** | E |
| Source-vs-runtime route difference | **0** (the 4 extra source entries are FastAPI's own `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect`, which never appear in an OpenAPI document) | A/E |
| Route *objects* in `app.routes` (naive enumeration) | **50** | A |
| Distinct endpoint modules serving routes | **97** | A |
| Distinct FastAPI dependency callables observed on routes | **34** | B |
| Auth/authorization guard families identified | **15** | B |
| Frontend `<Route>` entries declared in `frontend/src/App.js` | **75** (73 real + 2 redirects) | A |
| Distinct API paths reachable from the frontend | **330** literal paths in `frontend/src/v3/api.js` (+22 constructed) | A |
| Frontend mutation controls cross-referenced to backend routes | **171** mutating callables in `api.js`, bound from **91** files | A |
| Legacy/duplicate surface families still present | **6** (see §9) | A |
| Databases inspected (read-only) | **2** (135 and 154 public tables) | C |
| Migration ledger found in either database | **none** | A |

## 1.2 Headline observations (inventory-level, none is a verdict)

| ID | Observation | Class |
|---|---|---|
| I-01 | `app.routes` under-reports the surface: FastAPI 0.141 defers `include_router` into lazy `_IncludedRouter` wrappers, so the app reports **50** route objects while actually serving **781** operations. The repository already contains the correct helper (`backend/tests/unit/api/route_paths.py::effective_routes`); Phase 2 reused it. | A |
| I-02 | The **suppliers** write routes (`POST`/`PUT`/`DELETE /api/v3/suppliers…`) declare `require_org_admin` **without** `require_client_operation`, whereas facilities, assets and vehicles declare `require_org_admin` **plus** `require_client_operation("edit_master_data")`. The same master-data plane therefore reuses the client-access ceiling on three of four resources and not on the fourth. | B |
| I-03 | `frontend/src/v3/customer/ProcessingPage.jsx` renders an "Upload & process" control calling `v3UploadDocument`, but the page contains **no** `useClientAccess()` gate, while `UploadDocumentsPanel.jsx` gates on `can('upload_document')` and `FacilitiesTab.jsx` gates on `can('edit_master_data')`. The backend enforces the ceiling on the upload route via `api/upload_gate.py`. | B |
| I-04 | The customer-facing `/organization` route renders `frontend/src/v3/admin/AdminPage.jsx`; `/api/v3/admin/...` is a **different** surface (staff). The name "admin" in the frontend directory therefore does not denote an administrative plane. | B |
| I-05 | No route named `/admin` exists in the main frontend. The privileged internal surface is a **separate React application** (`admin/`, package `carbontally-admin`, port 3001) with its own `/admin/*` routes, and a **third** console exists inside the main app (`frontend/src/v3/ops/OperationsPage.jsx`, `/ops`). Two internal consoles plus one legacy app coexist. | B |
| I-06 | 17 operations declare **no** authentication dependency — 6 are FastAPI/main liveness, and 11 are business/legacy routes, including 3 mutations (`POST /api/waitlist/`, `POST /api/test-upload`, `POST /api/users/password-reset*`). Recorded, not judged. | A/B |
| I-07 | The most common guard is `require_org_member` (235 operations), ahead of `require_admin` (128) and `require_staff` (98 operations via `api.operations_auth`). 55 operations are `require_auth()`-only. | A |
| I-08 | Audit-dependency presence is **sparse**: only 35 of 781 operations declare an audit dependency (`get_audit_logger` / `get_audit_context`); other audit writes happen inside handler bodies and are invisible to the dependency graph. End-to-end audit coverage is **UNKNOWN**. | A/B |
| I-09 | Neither database contains a migration ledger table, so "migrations applied" cannot be established from the database; and the runtime database (154 tables) is **ahead** of the repository `.env` database (135 tables). | A/C |
| I-10 | Commercial/billing is provider-neutral: no checkout, webhook or payment-provider SDK reference exists anywhere in `backend/` — only plans, config, ledger, orders, payments, storage metering and idempotency keys. | B |
| I-11 | Master/reference data is **not** consistently controlled: `supplier_type`, `vehicle_type`, facility `type` and asset `type` are free-text inputs, while `fuel_type` is a select and `units` / `activity_categories` / `document_types` exist as tables. Neither database defines any enum type. | B/C |
| I-12 | Phase 1's `PO DECISION REQUIRED` items remain open; Phase 2 adds no new product decisions and takes none. | F |

## 1.3 What Phase 2 explicitly did NOT do

- No application code, schema, RLS policy, seed, migration or test file was modified.
- No fix, redesign, refactor or PO decision was made.
- No authorization outcome was judged correct or incorrect.
- No behavioural security test was executed (no authenticated business request was sent).
- No production endpoint was contacted; the `SUPABASE_LIVE_*` values in `backend/.env` were never dialled.
- No migration was applied; no database row was written, updated or deleted.

---

# 2. BACKEND ROUTE INVENTORY

## 2.1 Enumeration method (and why it matters)

| Step | Mechanism | Result |
|---|---|---|
| 1 | `git rev-parse HEAD` | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (A) |
| 2 | In-process import of the composition root (`backend/main.py:app`) + the repository's own flattener `backend/tests/unit/api/route_paths.py::effective_routes` | **781** effective operations (A) |
| 3 | Dependency-graph walk of each `APIRoute.dependant` | 34 distinct dependency callables; 766 operations carry a dependency chain (A/B) |
| 4 | `GET http://127.0.0.1:8070/openapi.json` (Demo Lab instance, read-only) | 777 operations (E) |
| 5 | `curl -m 4 http://127.0.0.1:8060/health` (the port named by `backend/.env`) | `http_code=000`, nothing listening → **NOT VERIFIED — runtime unavailable at the `.env` port** (A) |

Read-only artifacts (in `/tmp`, not in the repository):
`/tmp/p2_routes_effective.json`, `/tmp/p2_route_table.tsv`,
`/tmp/p2_appendix_routes.txt`.

The complete operation listing is **Appendix A**. Every count below is a
subset of that list.

## 2.2 Composition root and router families

`backend/main.py` (535 lines) includes **44** routers: 43 from
`backend/routes/*` (legacy / plane-A surface) plus one composition router
`backend/api/router.py`, which itself assembles ~60 `api/v3_*.py` / `api/*.py`
modules into the V3 surface.

| Layer | Router module(s) | Operations |
|---|---|---:|
| Legacy general | `routes/{waitlist,beta_access,upload,reports,legacy_reports,glossary,users,notifications,documents_main,document_activity,reference,drafts,emissions,feedback,drafts_enhanced,customer_documents}.py` | 118 |
| Legacy admin | `routes/admin/{staff,defra,extraction,reviews,assignments,permissions,workload,beta,audit,review_history,admin_logs,admin_bulk,email_templates,admin_analytics,settings}.py` | 105 |
| Legacy organisation | `routes/organizations/{management,members,assets,data,analytics,dashboard,files,team,metadata,exports,org_bulk}.py` | 79 |
| V3 (`/api/v3/*`) | `api/router.py` → `api/v3_*.py`, `api/customer_factors.py`, `api/issues.py` | 444 |
| V2 admin-plane helpers (mounted under `/api/v2/admin/*`) | `api/{admin_aliases,admin_audit,admin_entities,admin_imports,admin_providers}.py` | 15 |
| V2 engine endpoints | `api/business.py` (`/api/v2/{calculate,factor-match,validate,benchmark,generate-report}`) + `GET /api/v2/health` | 6 |
| Root | `main.py` (`/`, `/health`) | 2 |
| Framework | FastAPI `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` | 4 |

First-two-segment distribution of all 781 operations (A):
`/api/v3` 444, `/api/admin` 105, `/api/organizations` 79, `/api/reports` 23,
`/api/v2` 19, `/api/customer-documents` 16, `/api/documents` 11,
`/api/drafts` 11, `/api/glossary` 8, `/api/reference` 7, `/api/emissions` 7,
`/api/logs` 6, `/api/feedback` 6, `/api/users` 5, `/api/batches` 4,
`/api/notifications` 4, `/api/{waitlist,beta,bulk}` 2 each, then 19 single
legacy/root paths (including `/api/test-upload`, `/api/upload-csv`,
`/api/upload-pdf`, `/api/upload-batch`, `/api/repair-pdf`, `/api/upload`,
`/api/generate-enhanced-report`, `/api/generate-sustainability-report`,
`/api/{org_id}`, `/api/by-document-type`, `/api/{record_id}`, `/api/stats`,
`/api/by-asset`, `/api/verification-pending`).

Highest-operation V3 modules (A): `api.v3_operations` 53, `api.v3_consultants`
44, `api.v3_organizations` 29, `api.v3_reports` 27, `api.v3_commercial` 24,
`api.v3_processing_workflow` 20, `api.v3_pe` 20, `api.v3_disclosure` 15,
`api.v3_reporting` 15, `api.manual_processing_admin` 13, `api.v3_settings` 11,
`api.v3_billing` 10, `api.v3_documents` 10, `api.v3_emissions` 10,
`api.v3_messaging` 10, `api.v3_whitelabel` 9, `api.v3_backups` 9.

## 2.3 Declared authorization dependency per operation (source-level, B)

A route may declare several guards; the profile lists the strongest observed
combination.

| Declared guard combination | Operations | of which mutations |
|---|---:|---:|
| `require_org_member` + `get_current_user` | 235 | 94 |
| `require_admin` + `get_current_user` | 128 | 46 |
| `api.operations_auth.require_staff` (+ legacy `auth.require_staff`) | 84 | 37 |
| `api.consultant_auth.require_consultant` | 60 | 34 |
| `require_auth` only | 55 | 25 |
| `require_role([...])` | 47 | 28 |
| `get_current_user` only (no additional guard) | 40 | 20 |
| `require_org_admin` | 38 | 35 |
| `require_pe_capability` + `require_pe_member` | 19 | 12 |
| **no dependency chain at all** | 17 | 4 |
| `require_staff` + `require_manual_processing_admin` | 13 | 6 |
| `require_insight_user` | 11 | 5 |
| `require_client_operation` + `require_org_admin` | 9 | 9 |
| `require_backup_manager` | 9 | 3 |
| `require_org_member_or_internal_staff` | 8 | 4 |
| `require_client_portal_context` | 4 | 2 |
| single-occurrence combinations (`PE_MEMBER` only, `AUTH_ONLY`+`STAFF`, `USER_OPTIONAL`, `STAFF_LEGACY` only, `STAFF`+`AUTH_ONLY`) | 6 | 4 |

764 of 781 operations also declare `fastapi.security.http` (`HTTPBearer`)
because `get_current_user` depends on it — including the 12 operations that
carry the scheme but do **not** call `get_current_user`.

Global mutation/read split (A): **365 mutations** (`POST`/`PUT`/`PATCH`/
`DELETE`) and **416 reads** (`GET`).

## 2.4 Operations with no authentication dependency (complete list)

| Method | Path | Module | Inventory note (mechanism only) |
|---|---|---|---|
| GET | `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` | FastAPI | framework routes |
| GET | `/` | `main` | root banner |
| GET | `/health` | `main` | liveness (DB-aware) |
| GET | `/api/v2/health` | `api.router` | liveness, "never touches the database" (docstring) |
| POST | `/api/waitlist/` | `routes.waitlist` | public signup |
| POST | `/api/test-upload` | `routes.upload` | legacy test upload |
| GET | `/api/reports/report_status` | `routes.reports` | report-service status probe |
| GET | `/api/glossary/`, `/api/glossary/categories`, `/api/glossary/{term_id}` | `routes.glossary` | public glossary (also exposed by the public site) |
| POST | `/api/users/password-reset` | `routes.users` | self-service reset request |
| POST | `/api/users/password-reset/confirm` | `routes.users` | reset confirmation |
| GET | `/api/v3/settings/analytics` | `api.v3_settings` | analytics defaults |
| GET | `/api/v3/health/realtime` | `api.v3_health` | realtime health |

## 2.5 Selected route families (evidence for later discovery tracks)

**V3 organisation / master data** (`api.v3_organizations`, `api.v3_suppliers`,
`api.v3_vehicles`):

| Method | Path | Declared guards |
|---|---|---|
| GET | `/api/v3/organizations/{org_id}` | `require_org_member` |
| GET | `/api/v3/organizations/{org_id}/profile` / `metadata` / `members` / `roles` | `require_org_member` |
| PUT | `/api/v3/organizations/{org_id}/profile` / `metadata` | `require_org_admin` |
| POST | `/api/v3/organizations/{org_id}/members` | `require_org_admin` |
| PUT/DELETE | `/api/v3/organizations/members/{member_id}` | `require_org_admin` |
| POST/DELETE | `/api/v3/organizations/{org_id}/invitations[...]`, `/invitations/{id}` | `require_org_admin` |
| POST | `/api/v3/organizations/{org_id}/assets` · `PUT`/`DELETE /organizations/assets/{id}` | `require_org_admin` + `require_client_operation` |
| POST | `/api/v3/organizations/{org_id}/facilities` · `PUT`/`DELETE /organizations/facilities/{id}` | `require_org_admin` + `require_client_operation` |
| GET | `/api/v3/suppliers`, `/api/v3/suppliers/{id}` | `require_org_member` |
| POST/PUT/DELETE | `/api/v3/suppliers[...]` | `require_org_admin` (**no** ceiling dependency) |
| GET | `/api/v3/vehicles`, `/api/v3/vehicles/{id}` | `require_org_member` |
| POST/PUT/DELETE | `/api/v3/vehicles[...]` | `require_org_admin` + `require_client_operation` |

**V3 documents / uploads / batches** (`api.v3_documents`,
`api.v3_document_uploads`):

| Method | Path | Declared guards |
|---|---|---|
| GET | `/api/v3/documents`, `/api/v3/documents/{file_id}` | `require_org_member` |
| GET | `/api/v3/documents/{file_id}/emissions`, `/signed-url` | `require_org_member` |
| POST | `/api/v3/uploads` | `require_org_member` (ceiling enforced *inside* the handler via `api/upload_gate.py`) |
| POST | `/api/v3/uploads/{file_id}/ocr` | `require_org_member` |
| POST | `/api/v3/documents/upload-url` · `/{document_id}/upload-complete` · `/upload-abandon` | `require_org_member` |
| GET/POST | `/api/v3/batches`, `/api/v3/batches/{batch_id}`, `PATCH /api/v3/batches/{batch_id}` | `require_org_member` |
| POST | `/api/v3/consultants/clients/{client_id}/documents` (+`upload-url`, `upload-complete`, `upload-abandon`) | `require_consultant` |

**V3 processing / review / QC / PE** (`api.v3_operations` 53,
`api.v3_processing_workflow` 20, `api.v3_pe` 20, `api.v3_qc` 3):

- Operator plane under `/api/v3/ops/*` → `api.operations_auth.require_staff`
  (+ `ensure_entity_scope` / `ensure_batch_operator_access` inside handlers).
- QC + issue triage under `/api/v3/qc/*` and `/api/v3/issues/admin/*` →
  `require_admin` (the frontend comment in `OperationsPage.jsx` states the same).
- Processing Entity plane under `/api/v3/processing-entities/*` and
  `/api/v3/pe/*` → `require_pe_capability` + `require_pe_member` (19 operations).
- Automation surface `/api/v3/automatic-processing/*` (in
  `api.v3_automatic_processing`) and workflow transitions
  (`api.v3_processing_workflow`) → `require_staff`/`require_org_member`
  depending on the endpoint.

## 2.6 Audit instrumentation visible in the dependency graph

`get_audit_logger` (15) and `get_audit_context` (23) appear on 35 operations
(B). Additional auditing happens inside handler bodies via module-local helpers
(e.g. `api.v3_consultants._ct03_audit`, `_audit_engagement`,
`_audit_client_lifecycle`, `_audit_team_member_capability_change`,
`api.v3_commercial._audit`, `api/manual_processing_admin` grant auditing) and
is **not** visible to this method. End-to-end audit coverage: **UNKNOWN**.

## 2.7 Coverage matrix — backend routes

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Registered operations (method × path) | 781 | 781 (path, method, module, handler, dependency chain) | 0 for those five attributes | Handler bodies inspected only for the families in §4–§8 |
| Request/response schemas | 777 in the runtime OpenAPI document | 0 individually | 777 | out of Phase 2 scope |
| Operations with behavioural evidence (a request actually sent) | 0 | 0 | 781 | no authenticated request was issued (§11) |
| Operations with per-route test references | 781 | not counted individually | 781 | aggregate test state is Phase 1's (D) |
| RLS relevance per operation | 781 | not mapped per route | 781 | service-role client use is recorded in §4.10 |
| Duplicate `(method, path)` pairs | 0 | — | — | none detected |
| Operations returning raw `str(e)` in error detail | not counted | — | 781 | e.g. `routes/reference.py` handlers (`detail=f"Failed to get units: {str(e)}"`) — §46-relevant, recorded only |

---

# 3. FRONTEND SURFACE INVENTORY

## 3.1 Structure

| Item | Value | Class |
|---|---|---|
| Router | `react-router-dom` `BrowserRouter` in `frontend/src/App.js` (2,396 lines), single `<Routes>` block (lines 1987–2387) | B |
| Route entries | 75 (73 real routes + `/dashboard/*` and `*` redirects) | A |
| Route guards | `ProtectedRoute` (App.js:204), `RoleRoute` (`frontend/src/v3/components/RoleRoute.jsx`; props `requireOrg` / `requireConsultant` / `requireInternalStaff` / `requireEntityStaff`), `ClientOrgRoute` (App.js:1912) | B |
| Shells | `V3Layout` (customer/consultant/ops), `PEShell` (processing entity), `ClientOrgShell` (consultant operating a managed client) | B |
| Providers | `ReferenceDataProvider` → `RealtimeProviderWrapper` → `Routes`; `ClientAccessProvider` supplies the presentation ceiling view | B |
| Public assistant | `PublicAssistant` renders only when `isPublic` (App.js ~1900); comment states it is a deterministic local knowledge module with no AI provider and no network | B |
| v3 page tree | `frontend/src/v3/{customer,consultant,ops,pe,portal,admin,reports,insight,evidence,capabilities,messaging,components}` — file counts: `components` 32, `ops` 31, `customer` 14, `admin` 12, `consultant` 11, `insight` 9, `pe` 6, `reports` 4, `evidence` 3, `capabilities` 3, `portal` 2, `messaging` 1 | A |

## 3.2 Complete surface list (all 75 declared routes)

Actor column: `public` = no guard; `auth` = `ProtectedRoute` only;
`org` = `+ requireOrg`; `consultant` = `+ requireConsultant`;
`client-org` = `ClientOrgRoute`; `staff` = `+ requireInternalStaff`;
`entity` = `+ requireEntityStaff`.

| Route | Page/component | Actor | Inventory note (mechanism) |
|---|---|---|---|
| `/` | `LandingPage` | public | marketing surface |
| `/login` | `Login` | public | |
| `/privacy` `/data-security` `/cookies` `/terms` `/about` `/platform` `/services` `/processing-services` `/consultants` `/pricing` `/contact` `/faq` `/carbon-reduction-plan` | `PrivacyPolicy`, `DataSecurity`, `CookiePolicy`, `TermsPage`, `AboutUs`, `PlatformPage`, `ServicesPage`, `ProcessingServicesPage`, `ConsultantsPage`, `PricingPage`, `ContactPage`, `FaqPage`, `CarbonReductionPlan` | public | `/pricing` is static; no pricing API is called |
| `/auth/callback` | `AuthCallback` | public | OAuth / magic-link callback |
| `/signup` `/beta/signup` `/beta-login` `/auth/magic` `/accept-invitation` | `SelfServiceSignup`, `BetaSignup`, `BetaLogin`, `MagicLink`, `AcceptInvitation` | public | `AcceptInvitation` comment: backend enforces email binding, expiry, single-use |
| `/glossary` | `Glossary` | public | consumes `/api/glossary/*` (no-auth API) |
| `/onboarding` | `OnboardingPage` | auth | inside `ProtectedRoute`, no role prop |
| `/dashboard/*` | → `/home` | auth | redirect |
| `/home` | `DashboardPage` | org | |
| `/emissions` | `EmissionsPage` | org | |
| `/documents` | `DocumentsPage` → `UploadDocumentsPanel` | org | upload control gated by `useClientAccess().can('upload_document')` |
| `/processing` `/processing/:itemId` | `ProcessingPage`, `ProcessingItemPage` | org | **no** `useClientAccess` gate in either file |
| `/review` `/review/:itemId` | `ReviewPage`, `ReviewDetailPage` | org | `ReviewDetailPage` consumes `useClientAccess()` |
| `/existing-data` | `ExistingDataDiscoveryPage` | org | |
| `/messaging` | `MessagingPage` | org | Realtime messaging plane |
| `/insight` | `InsightPage` | org | |
| `/evidence/line-items/:lineItemId` | `SourceEvidenceViewer` | org | comment: a stored evidence id is a locator; the backend re-authorises every read |
| `/issues` | `IssuesPage` | org | |
| `/capabilities` | `CapabilitiesPage` | org | comment: makes no tenant-scoped request |
| `/capabilities/product` | `InvestorCapabilityPage` | auth | authenticated, deliberately not org-scoped |
| `/notifications` | `NotificationsPage` | auth | |
| `/reports` `/reports/:id` | `ReportsPage`, `ReportDetailPage` | org | |
| `/billing` | `BillingPage` | org | binds `/api/v3/billing/me*` |
| `/manual-processing` | `ManualProcessingPage` | org | |
| `/organization` | `AdminPage` (+10 tabs) | org | see §3.3 |

| `/consultant` | `ConsultantPage` | consultant | consultant operating plane |
| `/consultant/items/:clientId/:itemId` | `ConsultantItemPage` | consultant | |
| `/portal/:clientId/*` | `ClientPortal` | auth (**no** `ProtectedRoute` wrapper — B) | Plane C client portal; App.js comment: the server resolves relationship, access profile and firm entitlement |
| `/consultant/clients/:clientId` | `ClientOrgIndex` | client-org | |
| `/consultant/clients/:clientId/home` | `DashboardPage` | client-org | |
| `/consultant/clients/:clientId/documents` | `DocumentsPage` | client-org | |
| `/consultant/clients/:clientId/processing` `.../processing/:itemId` | `ProcessingPage`, `ProcessingItemPage` | client-org | |
| `/consultant/clients/:clientId/review` `.../review/:itemId` | `ReviewPage`, `ReviewDetailPage` | client-org | |
| `/consultant/clients/:clientId/manual-processing` | `ManualProcessingPage` | client-org | |
| `/consultant/clients/:clientId/emissions` | `EmissionsPage` | client-org | |
| `/consultant/clients/:clientId/reports` `.../reports/:id` | `ReportsPage`, `ReportDetailPage` | client-org | |
| `/consultant/clients/:clientId/issues` | `IssuesPage` | client-org | |
| `/consultant/clients/:clientId/messaging` | `MessagingPage` | client-org | |
| `/consultant/clients/:clientId/insight` | `InsightPage` | client-org | |
| `/consultant/clients/:clientId/existing-data` | `ExistingDataDiscoveryPage` | client-org | |
| `/consultant/clients/:clientId/capabilities` | `CapabilitiesPage` | client-org | |
| `/consultant/clients/:clientId/organization` | `AdminPage` | client-org | |
| `/consultant/clients/:clientId/evidence/line-items/:lineItemId` | `SourceEvidenceViewer` | client-org | |
| `/ops` | `OperationsPage` (tabbed console) | staff | |
| `/ops/items/:itemId` | `OperatorItemPage` | staff | |
| `/ops/review/:itemId` | `ReviewItemPage` | staff | |
| `/ops/qc/:itemId` | `QcItemPage` | staff | |
| `/ops/operational-health` | → `/ops?tab=operational-health` | staff | redirect for operator alerts |
| `/pe` | `PEDedicatedHome` in `PEShell` | entity | |
| `/pe/assignments` | `PeWorkItemsPage` | entity | |
| `/pe/messages` | `PeMessagingPage` | entity | |
| `/pe/items/:entityId/:itemId` | `PEEntityItemPage` | entity | |
| `*` | → `/` | public | catch-all |

Surface groups (A): **12** public marketing/legal, **5** public
auth/onboarding, **17** customer org surfaces, **17** consultant-managed-client
surfaces reusing the customer pages, **2** consultant-plane, **1** client-portal
family, **4** internal-ops, **4** processing-entity, **3** redirects/catch-all.

## 3.3 `/organization` tab inventory (`frontend/src/v3/admin/AdminPage.jsx`)

`TABS` (B): `profile` "Overview & Settings", `locations` "Locations",
`facilities` "Facilities & Assets", `vehicles` "Vehicles",
`suppliers` "Suppliers", `members` "Members & Invitations",
`factors` "Custom Factors", `activity` "Activity",
`audit` "Audit & evidence" (`adminOnly: true`), `security` "Security".

Recorded mechanisms:

- Tabs are filtered in the UI with `TABS.filter((tab) => !tab.adminOnly || isAdmin)`
  — presentation only; the source comment states the backend independently
  enforces it.
- Under a client prefix, the `members` tab is relabelled "Client Access" and
  `MembersTab` is swapped for `consultant/ClientAccessTab` (the same tab id, so
  `?tab=members` deep links still resolve).
- `?tab=` query values are honoured only when they match a known tab id.
- `listOrgRoles(org.id)` is called with `.catch(() => ({ roles: [] }))`, so a 403
  degrades to an empty role list rather than an error state (the source comment
  explains a consultant is not an org member and would receive 403).

## 3.4 Presentation-layer permission logic observed (complete)

| File | Mechanism | Class |
|---|---|---|
| `frontend/src/v3/clientAccess.jsx` | `ClientAccessContext` / `useClientAccess()`; default `UNRESTRICTED` with `can: () => true`; a provided view sets `can: (op) => value.capabilities[op] !== false` (fail-open in the UI; file comment: "PRESENTATION ONLY … the server is the security boundary") | B |
| `frontend/src/v3/customer/UploadDocumentsPanel.jsx` | `const canUpload = useClientAccess().can('upload_document')`; renders a restricted notice when `org && !canUpload` | B |
| `frontend/src/v3/customer/ReviewDetailPage.jsx` | `const clientAccess = useClientAccess()` | B |
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | `const clientAccess = useClientAccess()` | B |
| `frontend/src/v3/admin/FacilitiesTab.jsx` | `const canEditMasterData = useClientAccess().can('edit_master_data')` | B |
| `frontend/src/v3/admin/AdminPage.jsx` | `adminOnly` tab filter; `isAdmin` derived from membership role | B |
| `frontend/src/v3/ops/OperationsPage.jsx` | role-based tab visibility for QC / issues triage (comment: those APIs are gated by `require_admin()`) | B |
| `frontend/src/v3/components/RoleRoute.jsx` | actor/role gate for every `/ops`, `/pe`, `/consultant` and org route | B |

The scan also matched `/api/v3/pe/*` inside `RoleRoute.jsx`, which is a
documentation/URL template rather than a call site — recorded as a string-scan
false positive.

## 3.5 Coverage matrix — frontend surfaces

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Declared routes | 75 | 75 | 0 | route config read directly |
| Distinct page components reachable from the route table | ~55 | 55 (existence + import graph) | 0 | |
| Files with resolved API bindings | 91 | 91 | 0 | Appendix C |
| Tab-level sub-surfaces (`/organization` 10 tabs, `/ops` ~16 tabs) | ~60 | 26 tab files enumerated | ~34 | `OperationsPage` tab list not exhaustively mapped |
| Loading / empty / denied states | ~55 pages | 6 sampled | ~49 | no systematic state audit (§11) |
| Responsive behaviour | 75 | 0 | 75 | no browser viewport testing (§11) |
| Accessibility | 75 | 0 | 75 | no a11y tooling run (§11) |
| Legacy/duplicate frontend surfaces | §9 | §9 | — | |

---

# 4. AUTHENTICATION / AUTHORIZATION IMPLEMENTATION MAP

## 4.1 The resolution questions and the mechanism that answers each

| # | Question | Mechanism | Source | Approx. line |
|---|---|---|---|---|
| 1 | Authenticated identity | `get_current_user` | `backend/auth.py` | 182 |
| 2 | Staff / internal status | `staff_profiles` (+ `staff_roles.permissions`) resolved inside `get_current_user` → `AuthUser.is_internal_staff` | `backend/auth.py` | 252–285 |
| 3 | Organisation | `AuthUser.organization_id` from `organization_members` (`is_active = TRUE`) | `backend/auth.py` | 293–320 |
| 4 | Organisation membership | `AuthUser.is_org_member` + `require_org_member()` | `backend/auth.py` | 983 |
| 5 | Consultant firm | `_resolve_context` / `resolve_consultant_context` over `consultant_firm_members` → single active firm → `consultant_profiles` | `backend/api/consultant_auth.py` | 95, 140 |
| 6 | Consultant→client relationship | `resolve_managed_org_ids` (ACTIVE `consultant_clients` grants, capability-gated by `can_view_client`) | `backend/api/consultant_auth.py` | 155 |
| 7 | Relationship state | `resolve_relationship_state(status, retained_read_only)` (pure) | `backend/domain/relationship_access.py` | — |
| 8 | Client access profile | `resolve_client_ceiling` + `profile_allows(operation, profile, state)` | `backend/api/client_access_guard.py`, `backend/domain/relationship_access.py` | 76, 133 |
| 9 | Customer role | `AuthUser.role_name` / `role`, `require_role([...])`, `require_org_admin()` | `backend/auth.py` | 1279, 1116 |
| 10 | Staff capability | `StaffContext` + `ensure_staff_permission` / `require_internal_staff` / `require_entity_scope` | `backend/api/operations_auth.py` | 79–198 |
| 11 | Consultant capability | `ConsultantContext` + `ensure_consultant_permission` (`CONSULTANT_PERMISSIONS` flag map) | `backend/api/consultant_auth.py` | 151 |
| 12 | Commercial entitlement | `BillingService.get_entitlement`, `resolve_registration_mode`; consultant firm `resolve_entitlements(mode)` | `backend/services/billing.py`, `backend/domain/consultant_entitlement.py` | 60, 135 |
| 13 | RLS enforcement | Supabase RLS policies (`supabase/migrations/*`); some repositories use a service-role client (`database.get_supabase_client`) or the async pool (`api.dependencies.get_pool`) | migrations, `backend/database.py` | — |

## 4.2 Guard families and their instruments

| Guard | File:line | Question answered | Denial style |
|---|---|---|---|
| `get_current_user` | `auth.py:182` | identity (+ staff/org resolution) | 401 with `WWW-Authenticate: Bearer` |
| `get_current_user_optional` | `auth.py:1373` | identity, non-raising | returns `None` |
| `require_auth()` | `auth.py:760` | authenticated | 401; docstring: the parenthesised form is mandatory or the check is skipped |
| `require_admin()` | `auth.py:789` | staff/admin (`ADMIN_ROLE_NAMES = ("admin", "system_admin")`) | 403 |
| `require_staff()` | `auth.py:907` | legacy staff | 403 |
| `require_org_member()` | `auth.py:983` | membership + ACTIVE-grant consultant admission (`_admit_consultant_principal`) + suspended-org denial + exact-tenant (`enforce_org_path_scope`) | 401/403 |
| `require_org_member_or_internal_staff()` | `auth.py:1046` | membership OR internal staff | 403 |
| `require_org_admin()` | `auth.py:1116` | org admin authority (`_org_admin_authority`) | 403 |
| `require_org_access(organization_id)` | `auth.py:1196` | explicit org parameter | 403 |
| `require_entity_member(entity_id)` | `auth.py:1240` | PE membership | 403 |
| `require_role([...])` | `auth.py:1279` | named role list | 403 |
| `require_permission` / `_any` / `_all` | `auth.py:1310–1344` | role permission flags | 403 |
| `require_backup_manager()` | `auth.py:874` | admin + `can_manage_backups` | 403 |
| `resolve_staff_context` / `require_staff` | `api/operations_auth.py:66, 79` | staff profile, role permissions, entity scope | 401/403 |
| `require_consultant`, `ensure_consultant_permission`, `ensure_consultant_revocation_authority` | `api/consultant_auth.py:193, 209, 223` | firm membership, capabilities, revoker roles | 403 |
| `require_client_operation(operation)` | `api/client_access_guard.py:155` | client-access ceiling on the organisation plane | 403 (`CLIENT_OPERATION_DENIED_DETAIL`) |
| `require_client_portal_context` | `api/client_portal_auth.py` | Plane C client user | 403 generic |
| `require_pe_member` / `require_pe_capability` | `api/pe_auth.py` | PE membership + capability | 403 |
| `require_manual_processing_admin` | `api/manual_processing_admin.py` | MP governance | 403 |
| `require_insight_user` / `authorize_insight_scope` | `api/insight_authz.py:184, 206` | Insight persona scope (auditors and PE excluded) | 403 |
| `authorize_organization_upload` / `authorize_consultant_upload` | `api/upload_gate.py:198, 294` | upload admission: membership → tenant → viewer read-only (CL-42) → client ceiling; records `upload_denied` events (`_deny`) | 401/403/422 |

Used inside handlers rather than as a route dependency: `ensure_org_access`
(`api/dependencies.py:163`), `ensure_processing_org_access` (228),
`ensure_org_audit_access` (295), `ensure_batch_operator_access` (131),
`ensure_entity_batch_access` (173), `ensure_entity_review_scope` (198),
`resolve_accounting_context` (265), `ensure_record_owner_authorized` (395),
`resolve_authorized_supplier` (412).

## 4.3 Identity resolution detail (`get_current_user`, `auth.py:182–420`)

Recorded mechanisms (B):

1. `HTTPBearer(auto_error=False)`; `credentials is None` → 401 with
   `WWW-Authenticate: Bearer` (comment: WS3/API-0001 fixed a 403→401 issue).
2. Token verified with `supabase_client.auth.get_user(token)`; on failure it
   falls back to manual HS256 decode with `SUPABASE_JWT_SECRET` when that secret
   is configured, else 401.
3. `staff_profiles` looked up by `user_id`; if present `is_staff = True` and the
   role is resolved from `staff_roles` (`role_name`, `permissions`). The comment
   records that `staff_profiles` has no `role` column.
4. `organization_members` looked up by `user_id` with `is_active = TRUE` via
   `.maybe_single()` → at most one organisation per user in this resolver.
5. Console logging is used throughout; the authenticated email is printed
   ("User authenticated: <email>") — inventory note only.

## 4.4 Organisation guard composition (`require_org_member`)

Recorded decision order (B):

1. no user → 401.
2. `not is_org_member` → `_admit_consultant_principal(current_user, repos, request)`
   (CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01, PD-3/PD-7): an
   ACTIVE-grant consultant principal is admitted into the **same** guard family;
   every other non-member is denied with the historical 403.
3. `_caller_organization_inactive` → 403 `ORGANIZATION_SUSPENDED_DETAIL`
   (D-7 Decision B: organisation activation is independent of membership).
4. `enforce_org_path_scope(request, current_user)` — exact-tenant enforcement when
   the path names an organisation (`{organization_id}` / `{org_id}`); internal
   staff keep operational cross-organisation access; PE staff remain denied.

The docstring warns that `Depends(require_org_member)` (no parentheses) would
skip the check and inject the checker function; the same warning exists for
`require_auth` and `require_admin`. Phase 2 verified the dependency graph shows
`require_org_member.<locals>.org_member_checker` on 235 operations (the
**checker**, not the factory), so the parenthesised form is in use on all of them.

## 4.5 Client-access ceiling (organisation plane)

`api/client_access_guard.py` (B):

- Module docstring: before this module the ceiling was enforced only on the Plane
  C family `/api/v3/portal/{clientId}/*`, so an organisation member of a
  consultant-managed client could reach the direct-customer organisation plane.
- `resolve_client_ceiling` returns `None` (no ceiling) for: unauthenticated,
  internal staff, PE staff, non-members, and any caller whose own
  `organization_id` differs from the target organisation. It resolves the
  relationship from `ConsultantsRepository.get_relationship_for_org`, then
  `normalise_profile(relationship.client_access_profile)` and
  `resolve_relationship_state(status, retained_read_only)`.
- `enforce_client_operation(...)` fails closed with 403 for a client user whose
  profile/state does not admit the operation; every other caller is unaffected.
- `require_client_operation(operation)` is the dependency factory, used on 9
  operations (organisation assets/facilities, vehicles).
- `CLIENT_OPERATION_DENIED_DETAIL = "Your client access level does not permit this
  action"` — emitted without resource/organisation context (recorded; §13 Case F).

## 4.6 Consultant resolution

`api/consultant_auth.py` (B): `_resolve_context` requires ≥1 ACTIVE
`consultant_firm_members` row, exactly one distinct firm, and an active
`consultant_profiles` row; ambiguous (multi-firm) or inactive membership resolves
to `None` (deny rather than guess). `resolve_managed_org_ids` returns `()` unless
the firm member holds `can_view_client` — "the relationship row alone never
admits". `CONSULTANT_PERMISSIONS` maps verbs to columns:
`upload_documents→can_upload_documents`, `generate_reports→can_generate_reports`,
`manage_team→can_manage_team`, `extract/map/validate/calculate/confirm_automation/submit`
→ the matching `can_*` flag, plus `view_client→can_view_client`,
`approve→can_approve`. `CLIENT_STATUSES = (active, pending, rejected, suspended,
ended, inactive)`; only `active` grants access. Revocation requires role ∈
`CONSULTANT_REVOKER_ROLES` (Owner/Admin/Manager per the module comment).

## 4.7 Actor context returned to the frontend

`api/v3_context.py::me_context` (`GET /api/v3/me/context`, dependency:
`get_current_user`) returns a precedence-resolved workspace (B): internal staff →
`/ops`; entity staff → `/pe`; consultant → `/consultant`; organisation member →
`/home` (plus a presentation-only `client_access` capability map covering 10
operations); else `new_user` → `/onboarding`. Docstring: resolution errors raise
500 and can never be reported as "brand-new user". The `client_access` block is
labelled "PRESENTATION ONLY: enforcement is server-side".

## 4.8 Reuse vs divergence observed across routers

| Mechanism | Reuse pattern observed | Class |
|---|---|---|
| `require_org_member` | 235 operations across `api.v3_*`; per its docstring it also covers migrated legacy organisation handlers | B |
| Client-access ceiling | Present on facilities, assets and vehicles (9 dependency uses) and inside `upload_gate`; **absent** from the supplier write routes and from `/api/v3/organizations/{org_id}/members`, `/profile`, `/metadata`, `/invitations` (those are `require_org_admin` only) | B |
| `require_admin` | Legacy admin routes, QC, issue triage, manual-processing admin, backups | B |
| Legacy `auth.require_staff` vs `api.operations_auth.require_staff` | Two distinct staff authorities coexist; `auth.require_staff.<locals>.staff_checker` appears on 84 operations (usually alongside the operations variant), and one operation carries `STAFF_LEGACY` alone (`/api/admin/...`) | B |
| Suspended-organisation denial | Implemented in `require_org_member` only; operations guarded by `require_auth()` alone are unaffected | B |
| Viewer read-only rule | Implemented inside `upload_gate` (CL-42) for uploads; not expressed as a general-purpose guard | B |
| Audit dependency | 35 operations (`get_audit_logger` 15, `get_audit_context` 23); body-level helpers elsewhere | B |

## 4.9 RLS and the data-access layer

- RLS policies live in `supabase/migrations/*` (103 migration files). Phase 2 did
  **not** enumerate policy bodies (see §11).
- 45 operations depend on `database.get_supabase_client`; 15 on
  `api.dependencies.get_pool` (asyncpg → direct Postgres, i.e. past PostgREST-level
  RLS). Whether each such use is paired with application-level authorisation is
  **per-route UNKNOWN** here. For context, `data/contractual_instruments.py`
  documents one historical instance of the failure mode ("a client-supplied
  organisation id must never decide an accounting entitlement").
- Neither inspected database defines enum types, and neither contains a migration
  ledger table (so applied-migration state is not database-verifiable).

## 4.10 Coverage matrix — authorization mechanisms

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Guard factories exported by `auth.py` | 21 | 21 | 0 | names, signatures, key bodies |
| Route-dependency guard families | 15 | 15 | 0 | §2.3 |
| Handler-internal authorizers (`ensure_*`, `resolve_*`) | 12 | 12 (names + docstrings) | 0 | bodies sampled |
| RLS policies in migrations | 103 migration files | 0 policy bodies | all | deferred (§13) |
| Per-route behavioural ALLOW/DENY evidence | 781 | 0 | 781 | no requests issued (§11) |
| Entitlement resolver | 2 resolvers (`BillingService.get_entitlement`, `resolve_entitlements`) | 2 (signatures + docstrings) | rule tables not enumerated | §6 |

---

# 5. CONSULTANT / CLIENT ARCHITECTURE

## 5.1 Concepts and their implementation paths

| Concept | Backend implementation | Frontend implementation | Tables (present in both local DBs unless noted) |
|---|---|---|---|
| Consultant firm (profile) | `api/v3_consultants.py` (`GET /me`, `POST /me`), `api/consultant_auth.py::_resolve_context` | `frontend/src/v3/consultant/ConsultantPage.jsx` | `consultant_profiles` |
| Firm members | `GET/POST /me/team`, `POST /me/team/{id}/deactivate|reactivate`, `PATCH /me/team/{id}/capabilities` | `ConsultantTeamTab.jsx` | `consultant_firm_members` (4 rows in both) |
| Client relationships | `/me/clients`, `/me/customers`, `/me/engagements`, `GET/PUT/DELETE /clients/{client_id}`, `/suspend`, `/end`, `/reactivate` | `ConsultantPage`, `NewCustomerView.jsx`, `ConsultantClientContext.jsx` | `consultant_clients` (3 rows repo DB / 8 rows runtime DB) |
| Relationship status vocabulary | `CLIENT_STATUSES` — only `active` grants | status chips in client list | `consultant_clients.status` |
| Client access profiles | `POST /clients/{client_id}/access-profile`; policy in `domain/relationship_access.py`; enforcement in `api/client_access_guard.py` | `ClientAccessTab.jsx`, `clientAccess.jsx`, `AdminPage` "Client Access" tab | `consultant_clients.client_access_profile`, `retained_read_only` |
| Client invitations | `GET/POST /clients/{client_id}/invitations`, `POST …/revoke`; `GET /organizations/{org_id}/invitations`, `DELETE …/{id}`, `POST /organizations/invitations/accept`; composition in `services/client_invitations.py` | `AcceptInvitation.jsx`, `MembersTab.jsx`, `ClientAccessTab.jsx` | `user_invitations` |
| Client roles | `GET /organizations/{org_id}/roles`, `PATCH /clients/{client_id}/users/{member_id}` | `MembersTab.jsx` | `organization_members.role` |
| Termination / retained read-only | `POST /clients/{client_id}/end`, `DELETE /clients/{client_id}`; `resolve_relationship_state(status, retained_read_only)` | `ClientAccessTab.jsx` | `consultant_clients` |
| Commercial modes / mode changes | `POST /me/mode-change-requests`; `api/admin_consultant_commercial.py` (approve/reject); `domain/consultant_entitlement.py` | consultant + ops `CommercialTab.jsx` | runtime DB has `consultant_mode_change_requests`; absent in repo `.env` DB |
| Relationship requests (client-initiated) | `requestPortalRelationshipChange` path; `POST /organizations/{org_id}/consultant-engagements/{id}/accept|reject` | `ClientPortal.jsx` | runtime DB has `consultant_relationship_requests`; absent in repo `.env` DB |
| Consultant operating plane (Plane B) | `/api/v3/consultants/*` — 44 operations, `require_consultant` | `/consultant`, `/consultant/clients/:clientId/*` (reuses customer pages) | — |
| Client plane (Plane C) | `/api/v3/portal/{clientId}/*` — 4 operations, `require_client_portal_context` | `/portal/:clientId/*` (`ClientPortal.jsx`) | — |
| Direct-customer plane | `/api/v3/*` organisation routes | `/home`, `/organization`, … | — |
| Branding / white-label | `GET/PUT /me/branding`, `GET /me/branding/context`; `api/v3_whitelabel.py` custom domains (5 ops) + senders (4 ops) | `WhiteLabelTab.jsx` | `consultant_custom_domains`, `consultant_senders` |
| Consultant manual-processing coverage | `GET /me/manual-processing/coverage`; `api/v3_manual_processing_coverage.py`; `api/manual_processing_admin.py` (13 ops) | `ManualProcessingCoverageTab.jsx` (consultant + ops variants) | `consultant_mp_allocations` (runtime only) + `manual_processing_*` |
| Consultant lifecycle notifications | `services/consultant_lifecycle.py` — 5 events: accepted, submitted_to_qc, qc_outcome, customer_decision, rework | notification surfaces | — |

## 5.2 Client-access profile matrix (as implemented)

`domain/relationship_access.py` is a **pure** module (B). Its literals:

- Profiles: `OFF`, `READ_ONLY`, `COLLABORATIVE`, `MANAGED`.
- States: `ACTIVE`; `RETAINED_READ_ONLY` when status ∈ ended-set **and**
  `retained_read_only`; otherwise `OFF`.
- `CLIENT_FORBIDDEN_OPERATIONS = {map_factors, edit_mappings, recalculate}` —
  denied in every profile and state (PO-9), "including a client-Organisation
  Owner"; the docstring states server-side denial is mandatory (MUST-3).
- `KNOWN_OPERATIONS = {read_data, read_reports, read_evidence, comment,
  upload_document, edit_master_data, correct_submitted_data, approve_final}`;
  anything outside is denied (fail closed).
- Write ceiling per profile: `OFF` = ∅; `READ_ONLY` = {comment};
  `COLLABORATIVE` = {comment, upload_document, edit_master_data,
  correct_submitted_data, approve_final}; `MANAGED` = {comment}.
- `RETAINED_READ_ONLY` → read operations only.
- `has_client_login(profile)` → profile ≠ OFF; `state_has_client_plane(state)`
  → state ∈ {ACTIVE, RETAINED_READ_ONLY}.

The same module is consumed by `api/client_access_guard.py` (organisation plane)
and Plane C auth; its decisions are surfaced to the UI as
`/api/v3/me/context → client_access.capabilities` for the 10 operations in
`api/v3_context.py::_CLIENT_UI_OPERATIONS` (which includes `map_factors` and
`recalculate` — always false).

## 5.3 Invitations and branding

- `services/client_invitations.py` (210 lines) is the single composer of
  invitation emails for both planes: the brand is the **inviting** party's
  (consultant firm when it invited on the client's behalf, otherwise the
  CarbonTally fallback); the From address is the firm's own **verified** custom
  sender. Helpers: `invitation_accept_url`, `parse_invitation_expiry`,
  `describe_invitation`, `render_invitation_email`, `resolve_invitation_sender`,
  `send_invitation_email`.
- `api/v3_whitelabel.py` docstring: every endpoint is `require_consultant` +
  firm ownership; a client-supplied `consultant_id` is never trusted; "a domain
  NEVER grants authorization — the domain only selects which authorized brand is
  presented".

## 5.4 Migrations that define this architecture (source state)

| Migration (repository) | Subject |
|---|---|
| `20260821000000_d20_d15_active_consultant_grant.sql` | ACTIVE consultant grant (D20/D15) |
| `20260821010000_d21_white_label_branding.sql` | white-label branding (D21) |
| `20260831040000_consultant_revocation_roles.sql` | revocation roles |
| `20260906090000_p6_1c_consultant_engagement.sql` | engagement lifecycle |
| `20260906100000_p6_2a_consultant_processing_permissions.sql` | consultant processing permissions |
| `20260910120000_p6_2d_consultant_provenance.sql` | consultant provenance |
| `20260924000000_p8x_x2_operational_telemetry_retention.sql` | operational telemetry retention (X2) |
| `20261101000000_ct_mp_sub_003_consultant_coverage.sql` | consultant MP coverage |
| `20261102000000_ct_consultant_model_02_capability_admission.sql` | capability-gated admission |
| `20261103000000_ct_consultant_model_03_client_access_and_mode.sql` | client access + mode |
| `20261104000000_ct_consultant_client_identity_04.sql` | client identity / invitations |

## 5.5 SOURCE vs RUNTIME vs DATABASE disagreement (reported, not reconciled)

| Item | Source state | Repo `.env` DB (`ct_local_93d5cdd`) | Runtime DB (`carbontally_demo_local`) |
|---|---|---|---|
| Consultant tables (name match) | migrations above | `consultant_billing`, `consultant_clients`, `consultant_custom_domains`, `consultant_firm_members`, `consultant_profiles`, `consultant_senders`, `consultant_tasks` | the same **plus** `consultant_mode_change_requests`, `consultant_relationship_requests`, `consultant_mp_allocations` (+ `instrument_allocations`, `insight_concurrency_leases`) |
| Public tables | — | 135 | 154 |
| `consultant_clients` rows | — | 3 | 8 |
| `consultant_firm_members` rows | — | 4 | 4 |
| Organisations / members | — | 25 / 16 | 14 / 15 |
| `emission_factors` / `calculation_snapshots` | — | 0 / 0 | 7,049 / 34 |
| `customer_factors` | — | 5 | 0 |
| `audit_logs` | — | 0 | 0 |

Interpretation is deliberately **not** made here. The runtime database contains
objects with no corresponding migration in repository state at this HEAD; Phase 1
recorded the same "runtime database ahead of committed state" condition. A
migration-ledger reconciliation is a Phase 3 task (§13).

## 5.6 Coverage matrix — consultant/client architecture

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Consultant-plane operations | 44 | 44 (path + declared guard) | handler bodies largely unread | |
| Client-plane (Plane C) operations | 4 | 4 | bodies unread | |
| Client-access profiles / states | 4 profiles × 3 states | full matrix literals | — | pure module read in full |
| Consultant capability flags | 10 | 10 | — | `CONSULTANT_PERMISSIONS` |
| Lifecycle endpoints (suspend/end/reactivate/delete) | 4 | 4 | state-transition guards inside bodies | |
| Invitation paths | 6 (consultant 3 + org 3) | 6 | email delivery not exercised | |
| White-label endpoints | 9 | 9 (names + guards) | registrar/DNS integration unverified | |
| Mode-change / relationship-request flows | 2 families | endpoint-level only | request state machines unread; tables exist only in the runtime DB | |

---

# 6. COMMERCIAL ARCHITECTURE

## 6.1 Surfaces

| Plane | Router | Operations | Declared guard | Frontend |
|---|---|---:|---|---|
| CarbonTally internal commercial config | `api/v3_commercial.py` (`/api/v3/commercial/*`) | 24 | `api.operations_auth.require_staff` (+ module note: ACTIVE internal staff with `entity_id IS NULL` and `can_manage_billing`) | `frontend/src/v3/ops/CommercialTab.jsx` |
| Customer billing | `api/v3_billing.py` (`/api/v3/billing/*`) | 10 | `require_org_member` | `frontend/src/v3/customer/BillingPage.jsx` |
| Manual-processing governance | `api/manual_processing_admin.py` (`/api/v3/admin/manual-processing/*`) | 13 | `require_staff` + `require_manual_processing_admin` | `frontend/src/v3/ops/ManualProcessingTab.jsx`, `ManualProcessingCoverageTab.jsx` |
| Consultant commercial (mode decisions) | `api/admin_consultant_commercial.py` | counted within the consultant/staff families | staff/admin | ops `CommercialTab.jsx` |

## 6.2 Domain vocabulary (literals, B)

`domain/billing.py` (302 lines, pure, provider-neutral):

| Concept | Literal set |
|---|---|
| Registration mode | `REGISTRATION_MODES`; default `DEFAULT_REGISTRATION_MODE = "OPEN_REGISTRATION"` (the pre-existing D35 behaviour); CarbonTally Admin may publish `INVITATION_ONLY` |
| Credit ledger entry types | `grant`, `consume`, `adjustment`, `rollover`, `emergency_allowance`, `refund`, `reversal` |
| Credit ledger sources | `plan_included`, `purchase`, `promotional`, `adjustment`, `refund`, `emergency`, `rollover` |
| Subscription lifecycle | `pending`, `trial`, `active`, `past_due`, `suspended`, `cancelled`, `expired` |
| Order types | `automated`, `assisted`, `managed`, `storage`, `other` |
| Order statuses | `draft`, `estimated`, `awaiting_customer_approval`, `approved`, `queued`, `processing`, `awaiting_qc`, `completed`, `cancelled`, `rejected`, `failed`, `refunded` |
| Document complexity classes | `simple`, `standard`, `complex`, `exceptional` |
| Payment record statuses | `pending`, `confirmed`, `failed`, `refunded` |

Domain objects: `BillingPlan`, `CommercialConfig`, `CreditLedgerEntry`,
`Subscription`, `BillingOrder`, `StorageUsage`, `PaymentRecord`,
`IdempotencyKey`.

Configurable rule keys in `api/v3_commercial.py` (`CONFIG_KEYS`):
`default_billing_mode`, `credit_rules`, `structured_data_bands`, `storage`,
`assisted_pricing`, `credit_policy`, `standard_allowance`, `registration_mode`.
Module docstring: every material change is versioned (a new row; history is never
rewritten) and audited append-only, and "Provider-neutral: no payment-provider
code, no checkout, no webhooks."

## 6.3 Service layer (`services/billing.py`, 943 lines)

`BillingService` methods observed (B): `get_entitlement`,
`ensure_processing_entitlement`, `_standard_usage_this_period`, `grant_credits`,
`consume_credits`, `rollover`, `adjust_credits`, `reverse_credits`,
`refund_credits`, `activate_subscription`, `change_subscription_status`,
`create_order`, `estimate_assisted_order`, `approve_order`, `complete_order`,
`cancel_order`, `meter_storage`, `charge_processing`, `_required_units`,
`classify_document`, `record_payment_intent`, `consultant_capability`
(+ `_consultant_capability_from_plan`), `_claim_key` (idempotency), `_audit`,
`_entry`, `_subscription_out`, `_plan_out`.
Docstring: "Every mutation runs server-side, is organization-scoped, idempotent
and audited. The browser is never authoritative for commercial state. No
payment-provider integration."
Error types: `BillingError`, `InsufficientCreditsError`,
`EntitlementUnavailableError`, `OrderStateError`, `IdempotencyConflict`.

- `services/storage_metering.py` (137): `record_storage_usage`,
  `capacity_snapshot`, `capacity_integration_status`; docstring states storage
  beyond the included allowance is **metered, not refused**, and that
  `billing_plans.included_storage_bytes` is admin-configurable.
- `services/manual_processing_routing.py` (497) documents the authoritative
  chain: subscription entitlement → MP eligibility → admin MP enablement (FIN-06,
  most-specific-wins) → configured PE (`manual_processing_processors`) →
  automatic fallback routing → PE work item, with
  `effective = entitled AND enabled`.

## 6.4 Database shape (C)

| Table | Repo `.env` DB (`ct_local_93d5cdd`) | Runtime DB (`carbontally_demo_local`) |
|---|---|---|
| `billing_plans` | 8 rows | 27 rows |
| `billing_commercial_config` | present | present |
| `billing_credit_ledger` | present | present |
| `billing_orders` | present | present |
| `billing_payment_records` | present | present |
| `billing_storage_usage` | present | present |
| `billing_idempotency_keys` | present | present |
| `customer_subscriptions` | present | present |
| `consultant_billing` | present | present |
| `manual_processing_grants` | 0 rows | 1 row |

No table matching `plan_version*` was found in either database even though
`billing_plans` is described as a **versioned** catalogue. The versioning
mechanism (column vs row-per-version) was **not** inspected → recorded as
**UNKNOWN** in §11.

## 6.5 Explicitly not present

| Capability | Finding (both source and DB) |
|---|---|
| Payment-provider abstraction / SDK | no provider SDK or adapter module found in `backend/` |
| Checkout | none |
| Webhook handling | none |
| Invoicing | none; "invoice" occurs only as document-*extraction* vocabulary (`invoice_number`, `invoice_date`, `engines/invoice_extraction.py`, `services/extraction_suggestions.py`) |
| Trial logic | only the lifecycle literal `trial` in `domain/billing.py`; no trial-start code was located |
| Discount / add-on / proration / tax | not found in the files inspected |
| Public pricing API | `/pricing` is a static frontend route; the plan catalogue API is staff-only (`require_staff`) |

## 6.6 Coverage matrix — commercial architecture

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Commercial/billing operations | 34 | 34 (path + declared guard) | handler bodies partly read | |
| Domain literal sets | 8 | 8 | — | `domain/billing.py` read |
| Config keys | 8 | 8 | per-key enforcement paths | |
| `BillingService` methods | 24 | 24 (names + module docstring) | `charge_processing` / `classify_document` rule tables | |
| Billing tables | 10 name families | 10 (existence + row counts) | 0 columns inspected | |
| Provider integration | 0 | 0 | — | explicitly absent |
| Entitlement → UI mapping | `GET /api/v3/billing/me` | binding recorded | response body not exercised | |
| Customer self-service order flows | 3 (`assisted`, `managed`, `approve/cancel`) | endpoint-level | state machine bodies partly read | |

---

# 7. UI ↔ API PARITY INVENTORY

## 7.1 Method and artifacts

1. Every HTTP path literal in `frontend/src/v3/api.js` was extracted together
   with its nearest `method:` (330 of 352 exported callables carry a literal
   path; 22 build their path dynamically or delegate to another helper).
2. Every frontend file importing those callables was mapped to them
   (`/tmp/p2_appendix_page_bindings.txt`, 91 files, 360+ bindings).
3. Each extracted path was normalised (`${…}`/`{…}` → `{}`) and matched against
   the effective backend route table.

"Current backend authorization outcome" below is reported only where it is
determinable from source (the declared dependency chain) or from an existing
runtime observation; otherwise it is **UNKNOWN — not verified behaviourally**.

## 7.2 Aggregate parity statistics

| Metric | Value | Class |
|---|---:|---|
| Frontend files binding backend callables | 91 | A |
| Distinct backend paths called from the frontend | ~300 | A/B |
| Frontend callables with no literal path (require manual tracing) | 22 | A |
| Frontend mutation controls (POST/PUT/PATCH/DELETE callables) | 171 | A |
| Frontend mutation controls bound to a backend route | all matched by path shape after normalisation | A |
| Backend mutations with no frontend caller found | 194 (365 mutations − 171 frontend mutating callables) | B/G |
| Path-shape mismatches (UI path with no route at all) | 0 after normalisation; 3 apparent before normalisation, all explained by parameter naming or string templates | A |
| Route templates that differ only by parameter name (`{clientId}` vs `{client_id}`) | present (consultant family) | A |

The "apparent mismatches" found before normalisation (recorded for transparency,
**not** as defects): `/api/v3/consultants/clients/{clientId}/*` (UI uses
`clientId`, backend `client_id`), `/api/v3/commercial/entitlement/{id}` called
from `getAdminEntitlement` with a POST-shaped body (backend declares GET), and
`/api/v3/admin/backups/status` likewise. These are heuristics of the extractor,
not verified method mismatches — a per-call review is deferred (§13).

## 7.3 The nine known manual observations, located in source

| # | Observation | Surface + route | Backend route(s) | Implementation mechanism found | Class |
|---|---|---|---|---|---|
| 1 | Consultant operational gaps in managed Organisation surfaces | `/consultant/clients/:clientId/*` → `ClientOrgRoute` → customer pages | same organisation routes as a direct customer (`require_org_member` + consultant admission) | `App.js:1912 ClientOrgRoute` (ProtectedRoute → `RoleRoute requireConsultant` → `ClientOrgShell`); `AdminPage.jsx` swaps `MembersTab` → `ClientAccessTab`, and `listOrgRoles` fails soft to `{roles: []}` | B |
| 2 | Managed-client supplier mutation inconsistency | `/organization` → `SuppliersTab.jsx` | `POST/PUT/DELETE /api/v3/suppliers…` = `require_org_admin` (**no** `require_client_operation`) | `api/v3_suppliers.py` routes declare `require_org_admin()` only, whereas facilities/assets/vehicles declare `require_org_admin()` + `require_client_operation("edit_master_data")` | B |
| 3 | Managed-client vehicle mutation denial | `/organization` → `VehiclesTab.jsx` | `POST/PUT/DELETE /api/v3/vehicles…` = `require_org_admin` + `require_client_operation("edit_master_data")` | The ceiling applies to a client user of a consultant-managed organisation regardless of the caller's org role; `client_access_guard.enforce_client_operation` raises 403 unless the profile is COLLABORATIVE | B |
| 4 | Managed-client facility mutation issue | `/organization` → `FacilitiesTab.jsx` | `POST/PUT/DELETE /api/v3/organizations/{org_id}/facilities` and `/organizations/facilities/{id}` = `require_org_admin` + `require_client_operation("edit_master_data")` | Frontend hides edit affordances when `can('edit_master_data')` is false, but `LocationsTab`/list calls still issue `listFacilities` (`require_org_member`) | B |
| 5 | Documents page correctly denying client upload | `/documents` → `UploadDocumentsPanel.jsx` | `POST /api/v3/uploads` (+ `documents/upload-url`, `upload-complete`) = `require_org_member`, with `upload_gate.authorize_organization_upload` enforcing membership → tenant → viewer read-only → client ceiling | `const canUpload = useClientAccess().can('upload_document')` hides the control; the same ceiling is enforced server-side in `api/upload_gate.py:198` | B |
| 6 | Processing page exposes an upload control while backend returns 403 | `/processing` and `/consultant/clients/:clientId/processing` → `ProcessingPage.jsx` | `POST /api/v3/uploads` (via `v3UploadDocument`, api.js:1105–1115) | `ProcessingPage.jsx` has **no** `useClientAccess()` import while `UploadDocumentsPanel.jsx` and `FacilitiesTab.jsx` do; the button is `disabled={uploading \|\| !file}` only. This is a §7.4 Case A candidate (UI offers an operation the server's ceiling can deny) — recorded, not fixed | B |
| 7 | Supplier Type appears as free text | `/organization` → `SuppliersTab.jsx` | `POST/PUT /api/v3/suppliers` | `<input value={form.supplier_type}>` (line 126); no vocabulary source exists for supplier types (no `supplier_types` table; `supplier_categories` table exists but is not used by this tab) | B/C |
| 8 | Vehicle Type appears as free text | `/organization` → `VehiclesTab.jsx` | `POST/PUT /api/v3/vehicles` | `<TextInput label="Vehicle type" hint="e.g. car, van, HGV">` (line 183) — free text; `fuel_type` on the same form is a `<SelectInput>` | B |
| 9 | Generic contextual permission messaging | All guard denials surfaced through `v3/api.js` `friendlyError` | n/a | 403 → "You don't have permission to access this area." (api.js:33–35); 401 → "Please sign in again…"; 5xx → generic. The client-ceiling denial uses `CLIENT_OPERATION_DENIED_DETAIL` = "Your client access level does not permit this action". Neither message names the resource, organisation or required capability (a §7.4 Case F candidate) | B |

## 7.4 Parity cases found (the six categories requested)

### Case A — UI exposes an operation the backend denies

| UI surface | Control | API | Declared backend guard | Evidence |
|---|---|---|---|---|
| `/processing`, `/consultant/clients/:clientId/processing` (`ProcessingPage.jsx`) | "Upload & process" | `POST /api/v3/uploads` (`v3UploadDocument`) | `require_org_member` + in-handler `upload_gate` ceiling | `ProcessingPage.jsx:106–119, 316–331`; `api/upload_gate.py:198` |
| `/organization` → Suppliers tab | add/edit/remove supplier | `POST/PUT/DELETE /api/v3/suppliers…` | `require_org_admin` (no ceiling) | route table; `api/v3_suppliers.py` |
| `/organization` → Facilities tab | add/edit/remove facility | `POST/PUT/DELETE …/facilities…` | `require_org_admin` + ceiling | route table |
| `/organization` → Vehicles tab | add/edit/remove vehicle | `POST/PUT/DELETE /api/v3/vehicles…` | `require_org_admin` + ceiling | route table |

Recorded outcome: for a consultant-managed client user whose profile/state is
not COLLABORATIVE the ceiling denies (403) on uploads, facilities and vehicles;
behaviourally **UNKNOWN — not verified** in Phase 2. The supplier writes are the
one resource in this group without the ceiling.

### Case B — backend permits an operation but the UI provides no legitimate path

| API | Declared guard | Frontend caller found | Evidence |
|---|---|---|---|
| `POST /api/v2/{calculate,factor-match,validate,benchmark,generate-report}` | `get_current_user` only | none | `api/business.py`; not referenced by `v3/api.js` |
| `POST /api/{test-upload,upload-csv,upload-pdf,upload-batch,repair-pdf,upload}` | mixed (several `require_auth`; `test_upload` none) | none | legacy `routes/upload.py` |
| `GET /api/reference/{units,fuel-types,categories}` | `require_auth` | none | legacy reference router; the app uses its own `ReferenceDataProvider` |
| `/api/v2/admin/{aliases,audit,imports,providers}*` (15 ops) | `require_admin` | none in the main frontend | likely consumed by the separate `admin/` app (`admin/src/services/adminApi.js`) — not verified |

### Case C — UI hides an operation but the backend still exposes it

- `AdminPage` `adminOnly` tabs (`audit`) are hidden by a UI filter; the backend
  routes remain registered and independently guarded.
- QC / issues-triage tabs in `OperationsPage` are hidden by role while
  `/api/v3/qc/*` and `/api/v3/issues/admin/open` remain registered with
  `require_admin`.
- No route was found that is hidden by the UI **and** lacks a server-side guard —
  the hiding is always additional to a guard (B).

### Case D — UI and backend use different organisation/client identifiers

| UI source | Identifier | Backend expectation | Recorded note |
|---|---|---|---|
| `resolveV3Organization` / `resolveV3Membership` (api.js:123, 2199) | resolves the caller's org from `GET /api/organizations/members/user/{user.id}` (legacy router) | V3 handlers take `organization_id` as a parameter | dual-resolution path, recorded not judged |
| `/consultant/clients/:clientId/*` | `:clientId` in the URL | backend parameter name `{client_id}` | naming only; App.js comment states the URL id grants nothing |
| `ClientOrgShell` / `AdminPage` | `consultantClientId` drives labels and the `ClientAccessTab` | consultant routes are `require_consultant` + firm ownership | presentation |

### Case E — UI permission logic differs from backend authorization logic

| UI logic | Backend logic | Recorded divergence |
|---|---|---|
| `useClientAccess().can(op)` → `capabilities[op] !== false` (fail **open**) | `profile_allows(...)` (fail **closed**; unknown operation denies) | deliberate: the file comment states the backend denies regardless |
| `AdminPage` tab filter `!tab.adminOnly \|\| isAdmin` | audit routes guarded server-side | presentation filter only |
| `OperationsPage` role-based tabs | `require_admin` on QC / issue triage | presentation filter only |
| Client ceiling applied on facilities/assets/vehicles but **not** suppliers | same plane, same actor | **guard-set divergence** (I-02) |

### Case F — generic errors despite known resource/organisation context

| Message | Source | Context not conveyed |
|---|---|---|
| "You don't have permission to access this area." | `v3/api.js` `friendlyError` (403) | resource, organisation, required capability |
| "Your client access level does not permit this action" | `api/client_access_guard.py` | which operation was attempted |
| "Organization member access required", "Viewers are read-only and cannot upload documents" | `api/upload_gate.py` | organisation name (otherwise specific) |
| `detail=f"Failed to get units: {str(e)}"` and siblings | `routes/reference.py` | leaks a raw exception string (§46-relevant; recorded only) |

## 7.5 Selected parity table (master data, uploads, workflow, billing)

| UI surface | Control/action | API method/path | Route exists | Declared backend authorization | Evidence | Notes |
|---|---|---|---|---|---|---|
| Suppliers tab | create / update / remove | `POST /api/v3/suppliers`, `PUT/DELETE /api/v3/suppliers/{id}` | yes | `require_org_admin` | route table; `api/v3_suppliers.py` | **no** client ceiling |
| Suppliers tab | list | `GET /api/v3/suppliers` | yes | `require_org_member` | same | |
| Facilities tab | create / update / remove | `POST /api/v3/organizations/{org_id}/facilities`, `PUT/DELETE /api/v3/organizations/facilities/{id}` | yes | `require_org_admin` + `require_client_operation("edit_master_data")` | route table | ceiling present |
| Facilities tab (assets) | create / update / remove | `POST /api/v3/organizations/{org_id}/assets`, `PUT/DELETE /api/v3/organizations/assets/{id}` | yes | `require_org_admin` + ceiling | route table | ceiling present |
| Vehicles tab | create / update / remove | `POST /api/v3/vehicles`, `PUT/DELETE /api/v3/vehicles/{id}` | yes | `require_org_admin` + ceiling | route table | ceiling present |
| Locations tab | list (derived from facilities) | `GET /api/v3/organizations/{org_id}/facilities` | yes | `require_org_member` | `LocationsTab.jsx` | read-only tab |
| Members tab | add / update / remove member; invite / revoke invitation | `POST /api/v3/organizations/{org_id}/members`, `PUT/DELETE /api/v3/organizations/members/{id}`, `POST/DELETE /api/v3/organizations/{org_id}/invitations…` | yes | `require_org_admin` | route table | no ceiling |
| Custom Factors tab | create / update | `POST/PUT /api/v3/customer-factors…` | yes | `require_org_member` | route table | |
| Custom Factors tab | approve / deactivate | `POST /api/v3/customer-factors/{id}/approve`, `…/deactivate` | yes | `require_org_admin` | route table | consistent with AGENTS.md §16 (Owner may self-approve); recorded only |
| Documents page | single + batch upload | `POST /api/v3/uploads`; `POST /api/v3/documents/upload-url` → storage PUT → `POST /api/v3/documents/{id}/upload-complete`; `POST/PATCH /api/v3/batches` | yes | `require_org_member` + `upload_gate` ceiling | `UploadDocumentsPanel.jsx`, `api.js` | UI gates on `upload_document` |
| Processing page | upload document | `POST /api/v3/uploads` | yes | `require_org_member` + `upload_gate` ceiling | `ProcessingPage.jsx` | **UI has no gate** (Case A) |
| Processing page | confirm / retry job | `POST /api/v3/processing/jobs/{id}/{confirm,retry}` | yes | `/api/v3/processing/*` family registers `require_org_member` | `api.v3_processing` | |
| Review detail page | submit customer review | `POST /api/v3/processing/items/{item_id}/customer-review` | yes | `get_current_user` only at dependency level | route table | body-level item→org scoping not verified |
| Operator item page | extract / map / validate / calculate / start | `POST /api/v3/processing/items/{item_id}/{extract,map,validate,calculate,start}` | yes | `require_auth` only at dependency level | route table | body-level scoping not verified |
| Insight page | ask / answer / interactions | `/api/v3/insight/*` (11 ops) | yes | `require_insight_user` | route table | |
| Messaging page | create conversation / send message | `POST /api/v3/messaging/conversations`, `POST /api/v3/messaging/conversations/{id}/messages` | yes | `get_current_user` only at dependency level | route table | N1 boundary enforcement is body-level → UNKNOWN |
| PE pages | claim / complete work; entity messages | `/api/v3/pe/*` (20 ops) | yes | `require_pe_member` + `require_pe_capability` | route table | |
| Billing page | assisted / managed order; approve / cancel | `POST /api/v3/billing/orders/assisted`, `/billing/managed/orders`, `/billing/orders/{id}/{approve,cancel}` | yes | `require_org_member` | route table; `BillingPage.jsx` | client supplies `idempotency_key` |
| Client portal | annotation; relationship change request | `POST /api/v3/portal/{clientId}/{annotations,relationship-requests}` | yes | `require_client_portal_context` | `ClientPortal.jsx` | |
| Ops Commercial tab | plan / config / credit mutations | `/api/v3/commercial/*` (24 ops) | yes | `require_staff` (+ `can_manage_billing`) | route table | |
| Ops Manual-processing tab | grants / processors | `/api/v3/admin/manual-processing/*` (13 ops) | yes | `require_staff` + `require_manual_processing_admin` | route table | |
| Backups tab | create / verify / policy / download | `/api/v3/admin/backups/*` (9 ops) | yes | `require_admin` + `require_backup_manager` | route table | |

## 7.6 Coverage matrix — UI ↔ API parity

| Category | Discovered | Cross-referenced | Unknown | Notes |
|---|---:|---:|---:|---|
| Frontend files with API bindings | 91 | 91 | 0 | Appendix C |
| Frontend mutation controls | 171 | 171 bound to a route by path shape | behavioural outcome for all | §11 |
| Backend mutations | 365 | 171 traced from the main frontend | 194 | may be called by the separate `admin/` app, tests, workers, or be unreachable |
| Apparent path mismatches | 3 (pre-normalisation) | 3 explained | 0 | extractor heuristics only |
| Guard-set divergences on the same plane | 1 (suppliers vs facilities/assets/vehicles) | 1 | further divergences possible among the 194 untraced mutations | §13 |

---

# 8. MASTER / REFERENCE DATA INVENTORY

## 8.1 Concept inventory

| Concept | Source / table | API | UI field | Controlled or free-form | Maintenance path | Notes |
|---|---|---|---|---|---|---|
| Units | `units` table (0 rows in **both** DBs); backend also has a central alias map `core/units.py::UNIT_ALIASES` | `GET /api/reference/units` (`require_auth`) | `context/ReferenceDataContext.jsx` (`units`), `hooks/useManualEntry.js`, `components/ManualEntryStandalone.jsx` | table-driven but **empty** → effectively uncontrolled; aliases normalised centrally server-side (`l→litres`, `m3→cubic metres`) | no CRUD route found for `units` | alias docstring references the live `emission_factors` unit distribution |
| Fuel types | derived at read time from `emission_factors.activity_type` (keyword filter Diesel, Petrol, LPG, CNG, AdBlue, Fuel, Gasoline) | `GET /api/reference/fuel-types` (`require_auth`) | `ReferenceDataContext.fuelTypes`; `VehiclesTab` `<SelectInput label="Fuel type">` | semi-controlled (derived from the catalogue, not a vocabulary table) | via DEFRA factor CRUD | `emission_factors`: 0 rows repo `.env` DB / **7,049** runtime DB → empty list on the repo `.env` DB |
| Emission / conversion factors | `emission_factors` (+ `factor_aliases`, 0 rows) | `/api/admin/defra/factors*` (GET/POST/PUT/DELETE/bulk), `/api/admin/defra/{years,activities,validate}`, `GET /api/reports/defra-factors/{reporting_year}` | ops factor consoles; `ManualEntryStandalone.jsx` calls `/api/defra-factors/{year}` (**no such route**) | controlled catalogue | `routes/admin/defra.py` (9 ops, `require_admin`) | |
| Activity types | `emission_factors.activity_type`; `activity_categories` (0 rows both DBs) | `GET /api/reference/categories`, `GET /api/admin/defra/activities` | legacy manual-entry surfaces | mixed: catalogue-derived + empty category table | DEFRA factor CRUD | |
| Customer factors | `customer_factors` (5 rows repo DB / 0 runtime) | `GET/POST/PUT /api/v3/customer-factors`, `POST …/{id}/approve`, `…/deactivate` | `CustomFactorsTab.jsx` — `activity_type` free-text `TextInput` ("e.g. Natural gas, Diesel") | free-form within a controlled catalogue | org admin for approve/deactivate | factor precedence is a backend concern (AGENTS §15); not audited in Phase 2 |
| Supplier types | **no vocabulary used**; `supplier_categories` exists with 0 rows | `POST/PUT /api/v3/suppliers` (field `supplier_type`) | `SuppliersTab.jsx:126` plain `<input>` | **free-form** | none | recorded, not judged |
| Vehicle types | none | `POST/PUT /api/v3/vehicles` (field `vehicle_type`) | `VehiclesTab.jsx:183` `TextInput` hint "e.g. car, van, HGV" | **free-form** | none | `fuel_type` on the same form is a select |
| Facility types | `facilities.type` column (free string) | `POST/PUT …/facilities`, `GET …/facilities` | `FacilitiesTab.jsx:249/271` `<input placeholder="e.g. office, warehouse">` | **free-form** | none | `LocationsTab.jsx` derives its "Filter by type" options from the values present |
| Asset types | `assets.type` / `asset_type` | `POST/PUT …/assets` | `FacilitiesTab.jsx:292/313` `<input>` | **free-form** | none | table renders `r.type \|\| r.asset_type` |
| Document types | `document_types` + `document_type_categories` (0 rows both DBs) | no dedicated vocabulary route found | legacy `UploadManager.js` sends `data_type` | table-driven but empty | unknown | |
| Scope 1/2/3 activity vocabularies | **hardcoded in the frontend** — `App.js` ~150–164: `utility: ['Electricity','Natural Gas']`, `fuel: ['Diesel','Petrol','AdBlue']`, `scope3: ['Flight (Short Haul)','Flight (Long Haul)','Rail (National)','Hotel Stay','Mixed Waste','Recycled Waste']`; `components/CarbonTallyDemo.jsx: CATEGORY_OPTIONS` | legacy `/api/emissions` | legacy dashboard | **hardcoded literal arrays** | none | independent vocabulary source alongside the DB catalogue |
| Waste types / routes | no table found; "Mixed Waste"/"Recycled Waste" are hardcoded strings only | — | legacy dashboard | **hardcoded** | none | |
| Countries | no `countries` table in either DB; forms default `country: 'GB'` | — | supplier/facility/vehicle forms | free-form string | none | |
| Currencies | no `currencies` table found; `currency` appears in extraction fields and the billing domain | — | — | **UNKNOWN** | — | not inspected |
| Statuses | DB status columns (no enum types); frontend label map `frontend/src/v3/components/ui/statusConfig.js` (`extracting`, `mapping`, `validating`, `calculating`, `in_progress`, `qc_in_progress`, `generating`, …) | route-dependent | status chips/tables | presentation-controlled; **no DB enum constraint** | — | backend vocabularies are Python literals |
| Staff / org roles | `staff_roles` (3 rows both DBs); `GET /api/v3/organizations/{org_id}/roles` | `listStaffRoles` | `StaffRolesTab.jsx`, `MembersTab.jsx` | controlled (tables) | staff admin surfaces | |
| Vehicle capacity units | `VehiclesTab` `EMPTY` default `capacity_unit: 'tonnes'` | `POST/PUT /api/v3/vehicles` | select/input | literal default | none | |

## 8.2 Inconsistency observations (recorded, not judged)

1. **One concept, three representations**: fuel/activity vocabulary exists as the
   `emission_factors` catalogue, the (empty) `activity_categories` +
   `GET /api/reference/categories`, and hardcoded arrays in
   `App.js`/`CarbonTallyDemo.jsx`.
2. **Type fields are free text** for supplier, vehicle, facility and asset, while
   fuel is a select and roles are table-driven.
3. **Reference tables exist but are empty in both databases** (`units`,
   `supplier_categories`, `document_types`, `document_type_categories`,
   `activity_categories`, `factor_aliases` = 0 rows), so any UI relying on them
   renders an empty choice list on this environment.
4. **Two transports reach the UI**: `v3/api.js` functions vs raw `fetch` calls in
   `context/ReferenceDataContext.jsx`, `hooks/useManualEntry.js` and
   `components/ManualEntryStandalone.jsx` (see the §7.1 extraction limitation).
5. **Unit normalisation is centralised server-side** (`core/units.py`) — the one
   concept with a single shared implementation (AGENTS §23).

## 8.3 Coverage matrix — master / reference data

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Vocabulary concepts | 17 | 17 | currency handling | §8.1 |
| Table-backed vocabularies | 7 | 7 (existence + row counts) | columns | none populated |
| Hardcoded frontend vocabularies | ≥3 literal arrays | 3 | further arrays in `public/demos/*` | |
| Free-text type fields | 4 | 4 | — | §7.3 #7/#8 |
| Reference APIs | 4 families (`/api/reference/*` 3 ops, `/api/admin/defra/*` 9, `/api/reports/defra-factors/*` 1) | 4 (declared guards) | response shapes | |
| Central normalisation mechanisms | 1 (`core/units.py`) | 1 | full alias table not enumerated | |

## 8.4 Correction recorded against the first extraction pass

The first frontend scan (§7.1) matched only paths that **begin** a quoted or
template literal, so it missed paths embedded inside a template
(`${API_URL}/api/reference/fuel-types`) and every file that does not import
`v3/api.js`. A second pass captured **all** `/api/` tokens: **64 files** reference
the API, **63** of them outside `v3/api.js`, producing **101 distinct** paths.
Consequences for §7:

- Case B's row claiming "no caller found" for `/api/reference/{units,fuel-types,categories}`
  is **partly wrong**: `ReferenceDataContext.jsx`, `useManualEntry.js` and
  `ManualEntryStandalone.jsx` do call `/api/reference/fuel-types` and
  `/api/reference/units` (via raw `fetch`). `/api/reference/categories` still has
  no caller found.
- The corrected pass also identified **32 frontend paths with no matching backend
  route**, of which the clean legacy candidates (each one re-checked against the
  route table) are: `/api/activity-feed` (`components/ActivityFeed.jsx`),
  `/api/auth/magic` (`MagicLink.jsx`), `/api/settings` (`BulkUpload.jsx`),
  `/api/admin/documents/{id}/status` (`UploadManager.js`),
  `/api/defra-factors/{year}` (`ManualEntryStandalone.jsx`) and
  `/api/emissions/{id}/emissions` (`App.js`). Other entries of the 32 are
  parameterisation artifacts — `/api/reports/defra-factors/{year}` exists as
  `GET /api/reports/defra-factors/{reporting_year}`, `/api/documents/stats`
  exists only as `/api/documents/stats/{org_id}`, `/api/batches` only as
  `/api/batches/{batch_id}/*` + `/api/batches/stats`, and
  `/api/customer-documents` only in parameterised forms — plus bare prefixes
  (`/api/v{}`) and doc-comment file names (`/api/consultant_auth.py`). None of
  those is reported as a defect.

---

# 9. LEGACY / DUPLICATE SURFACE INVENTORY

Nothing was deleted, moved or refactored. "Reachable" means a render/registration
path was found in current source.

## 9.1 Backend

| Surface | Evidence | Reachable | Referenced by code | Referenced by tests | Status |
|---|---|---|---|---|---|
| `backend/routes/*` (43 routers, 302 operations) | registered by `main.py` via `app.include_router` | **yes** (registered) | yes | tests exist for several (not individually counted) | live legacy plane coexisting with V3 |
| `/api/v2/*` (19 ops incl. engine endpoints + 5 admin modules) | registered via `api/router.py` | **yes** | yes (`/api/v2/health`) | unknown | the "v2.1" surface mounted under `/api/v2` |
| `backend/main_v2.py` (18 lines, `api.router.create_app()`) | alternate entry point | **no** — the running process uses `uvicorn main:app` (observed cmdline) | docstring only | unknown | not used by the Demo Lab |
| `routes/legacy_reports.py` | comment: thin compatibility aliases for legacy report paths the live legacy UI still calls | **yes** | delegates to `routes/reports.py` | unknown | intentional shim |
| `routes/customer_documents.py` (16) vs `api/v3_documents.py` (10) | two document families | **yes** (both) | legacy `DocumentStatus.jsx` → `/api/customer-documents`; V3 UI → `/api/v3/documents` | unknown | duplicate capability on different planes |
| `routes/upload.py` (10: `/api/upload`, `-csv`, `-pdf`, `-batch`, `repair-pdf`, `test-upload`, batch status/progress/cancel/stats) vs `api/v3_documents.py` + `api/v3_document_uploads.py` | two upload families | **yes** (both) | legacy `UploadManager.js`; V3 `UploadDocumentsPanel.jsx` | unknown | duplicate upload implementations |
| `routes/organizations/*` (79) vs `api/v3_organizations.py` (29) | two organisation families | **yes** (both) | legacy `AssetManager.js`, `TeamManagement.js`, `OrganizationMetadata.jsx`; V3 `AdminPage` tabs | unknown | duplicate organisation administration |
| `routes/emissions.py` (15) / `api/v3_emissions.py` (10) / `POST /api/v2/calculate` | three emission entry points | **yes** (all registered) | legacy dashboard (`/api/emissions`), V3 pages, none for `/api/v2/*` | unknown | §13 |
| `routes/reports.py` (22) / `api/v3_reports.py` (27) / `api/v3_reporting.py` (15) | three report families | **yes** | legacy + V3 UIs | unknown | |
| `routes/reference.py` vs catalogue-driven V3 factor surfaces | see §8 | **yes** | `ReferenceDataContext.jsx`, manual entry | unknown | |
| `routes/glossary.py` (8 ops, no auth) | public glossary | **yes** | `Glossary.jsx` (public page) | unknown | matches the public-site glossary |
| `routes/{feedback,drafts,drafts_enhanced,logs,notifications,beta_access,waitlist}.py` | legacy support surfaces | **yes** | legacy hooks/services (`useNotifications`, `NotificationService`, `useDocumentLogging`, `useManualEntry`, `emailService`) | unknown | |
| Root/backend tooling: `list_endpoints.py`, `generate_api_docs.py`, `test_endpoints.py`, `quick_api_ref.py`, `create_admin_dashboard.py`, `export_postman.py`, `backend/verify_startup.py`, `backend/backup/` | scripts | **unknown** | not imported by the app | unknown | repository tooling, not a runtime surface |

## 9.2 Frontend

| Surface | Evidence | Reachable | Notes |
|---|---|---|---|
| Legacy `Dashboard` component (`App.js:519`, ~1,370 lines) rendering `UploadManager`, `BulkUpload`, `DocumentStatus`, `TeamManagement`, `AssetManager`, `OrganizationMetadata`, `ManualEntryStandalone`, `RecentProcessedData`, `PDFIngestionPortal`, `ChatWidget`, `NotificationBell`, `RealtimeStatus` | defined in `App.js` | **NO** — no `<Dashboard …>` render site exists anywhere in `frontend/src`; the router renders `v3/customer/DashboardPage` | dead-by-omission legacy UI; modules remain imported so they are still bundled |
| `DashboardLayout` (`App.js:245`) | defined | **NO** — no render site found | |
| `CompanyNamePrompt` | imported by `App.js` | **NO** — 0 `<CompanyNamePrompt` render sites | |
| Root-level legacy modules (`AssetManager.js`, `UploadManager.js`, `TeamManagement.js`, `DocumentStatus.jsx`, `OrganizationMetadata.jsx`, `BulkUpload.jsx`, `ManualEntryStandalone.jsx`, `RecentProcessedData.jsx`, `PDFIngestionPortal.jsx`, `components/{ActivityFeed,DashboardSummary,StaffPresence,CarbonTallyDemo}.jsx`, `components/chat/*`, `services/{NotificationService,apiClient,emailService}.js`, `hooks/{useNotifications,useDocumentLogging,useManualEntry}.js`) | present | only via the unreachable legacy `Dashboard`/`ChatWidget` tree, or not at all | several are still bundled because `App.js` imports them |
| `frontend/src/public/demos/*` (`demoData.js`, `ReportingDemo.jsx`, `ProcessingWorkbenchDemo.jsx`) | present | demo routes are not in the router | `public/assistant/*` **is** rendered (`PublicAssistant`, App.js:2389) |
| `frontend/src/v3/admin/*` | directory named `admin` serving the customer `/organization` surface | reachable | naming only; no administrative plane behind it |
| `frontend/src/css/*` and `v3/ops/{ops,v12}.css` | two ops stylesheets | reachable | styling duplication recorded, not judged |
| `carbon-tally-ui-demo/modules` (repo root) | present | unknown | demo/asset material |
| `frontend_backup_pre_v3_public_20260827/` | complete prior frontend copy (`App_.js`, `src/`, `package.json`, `vercel.json`) | **NO** (not built or served) | in-tree backup of the pre-V3 public frontend |
| `admin/` (package `carbontally-admin`, `cross-env PORT=3001 react-scripts start`, `serve.py`, `server.js`) | second React application; 20 routes under `/admin/*` plus `/staff-dashboard` | **NO in the main app**; the root `package.json` build script runs `cd admin && npm install && npm run build` and copies `admin/build/*` into `public/admin/` | legacy internal console |
| Root `package.json` build script | `… cd frontend … && cd ../admin … && mkdir -p public/admin && cp -r frontend/build/* public/ && cp -r admin/build/* public/admin/` | n/a | the deployed public bundle composes **two** applications |
| Root `src/` (Prisma/seed tooling: `commands/`, `providers/`, `seed.ts`, `prisma/`) | present | not a runtime surface | data tooling |
| `e2e/`, `tests/`, `qa_harness/`, `tools/` | present | not runtime surfaces | verification tooling |

## 9.3 Duplicate permission mechanisms (recorded, not judged)

| Mechanism A | Mechanism B | Where both appear |
|---|---|---|
| `auth.require_admin()` | `api/operations_auth.require_staff()` + `ensure_staff_permission` | legacy admin (105 ops) vs V3 ops/QC/commercial (98 ops) |
| `auth.require_staff()` | `api.operations_auth.require_staff()` | both names present on 84 operations |
| `auth.require_role([...])` | `require_org_admin()` / `require_org_member()` | 47 vs 38 / 235 operations |
| `api/client_access_guard.require_client_operation` | `api/upload_gate` internal ceiling | 9 route uses vs in-handler use |
| `MembersTab` (org roles) | `ClientAccessTab` (consultant client roles) | swapped deliberately by `AdminPage` under a client prefix |

## 9.4 Coverage matrix — legacy / duplicate surfaces

| Category | Discovered | Inspected | Unknown | Notes |
|---|---:|---:|---:|---|
| Legacy backend router families | 4 (general, admin, organisations, v2) | 4 | per-route test coverage | 302 legacy + 19 v2 operations |
| Duplicate capability families | ≥6 (upload, documents, organisations, emissions, reports, reference) | 6 | which family the investor demo actually exercises | §13 |
| Legacy frontend components | 12+ | 12 (import graph + render sites) | 0 | `Dashboard`, `DashboardLayout`, `CompanyNamePrompt` have no render site |
| Alternate entry points | 1 (`main_v2.py`) | 1 | — | not used by the running process |
| Whole legacy applications in-tree | 2 (`admin/`, `frontend_backup_pre_v3_public_20260827/`) | 2 | whether `admin/` is deployed to production | §11 |

---

# 10. COVERAGE MATRICES

Aggregate of the per-section matrices (§2.7, §3.5, §4.10, §5.6, §6.6, §7.6, §8.3,
§9.4).

| Area | Discovered | Inspected | Unknown | Method |
|---|---:|---:|---:|---|
| Backend routes (operations) | 781 | 781 for path/method/module/handler/guard | behavioural outcome for all 781 | in-process enumeration + dependency walk + runtime OpenAPI cross-check |
| Frontend surfaces (declared routes) | 75 | 75 | tab-level sub-surfaces (~34 of ~60) | route config read |
| Authorization mechanisms (guards) | 21 `auth.py` factories + 15 route guard families + 12 handler authorizers | 48 | RLS policy bodies; per-route runtime outcome | source read |
| UI mutation controls | 171 | 171 bound to a route by path shape | 171 behavioural outcomes | api.js + page import graph |
| Reference/master-data concepts | 17 | 17 | currency handling, vocabulary columns | source + DB |
| Legacy/duplicate surfaces | 4 backend families + 6 duplicate capability families + 2 whole apps + 12 frontend components | all of the above at file/route level | per-route test coverage; production deployment of `admin/` | source + `package.json` + import graph |
| Databases | 2 | schema name inventory + targeted row counts | columns, constraints, indexes, RLS policy bodies | read-only `psql` |
| Migrations | 103 files | filenames + the consultant/client/commercial subset | contents of the other ~90 | `ls` |
| Tests | 1,185 demo identities (manifest, F); 2,537 collected / 7 failing (Phase 1, D) | 0 re-run in Phase 2 | the entire API-unit/Jest/integration/e2e suites | Phase 1 baseline cited, not repeated |

## 10.1 Explicitly uninspected areas

1. RLS policy bodies and their table coverage (103 migration files).
2. Per-route handler bodies for the ~700 operations outside the families named in
   §4–§8 (org scoping inside handlers is therefore unverified).
3. Request/response schemas (777 operations in the runtime OpenAPI document).
4. Per-route test references and current test outcomes (Phase 1 data only).
5. Behavioural authorization: no authenticated request was issued, so no
   ALLOW/DENY outcome is asserted as verified.
6. Browser/UI behaviour: no page was loaded, no screenshot taken, no console
   error collected, no viewport or accessibility check performed.
7. Real-time messaging behaviour (Supabase Realtime) and N1 boundary enforcement.
8. Automatic-processing worker behaviour and job state machine execution.
9. Extraction/OCR capability presence in this environment (Phase 1 territory).
10. `.env`-configured runtime on port 8060 (nothing listening) — the only runtime
    observed is the Demo Lab instance on 8070.
11. Production: `https://carbontally-api.onrender.com` and
    `https://carbontally.co.uk` were **not** contacted (forbidden by §4).
12. Column-level detail of billing plans, consultant relationships and
    invitations.
13. `qa_harness/` execution.
14. The 194 backend mutations with no frontend caller (may be staff-only, worker
    internal, legacy, or unreachable).

---

# 11. KNOWN LIMITATIONS / UNVERIFIED AREAS

## 11.1 Method limitations

| ID | Limitation | Effect on confidence |
|---|---|---|
| L-01 | **Static analysis only.** No authenticated HTTP request was issued in Phase 2 (no writes to any environment, and no credentials were used). | Every "authorization outcome" is a statement about declared dependencies, not about runtime behaviour. |
| L-02 | The first frontend extraction pass missed template-embedded paths; a second pass corrected it (§8.4). | Parity counts are a floor; a third pass over dynamic URL construction could add call sites. |
| L-03 | Method inference from `api.js` uses the nearest `method:` literal within the same export block. | Individual method attributions may be wrong for the 22 dynamic callables; not used as a defect claim. |
| L-04 | Path-parameter **names** differ between UI and backend (`{clientId}` vs `{client_id}`). | Cross-references use normalised path shapes, not literal strings. |
| L-05 | Dependency-graph introspection reads FastAPI's `dependant` tree; guards applied *inside* handler bodies (`ensure_*`) are invisible there. | Guards counted as "absent" may still exist inside the handler (e.g. `/api/v3/uploads` has no ceiling *dependency* but does enforce it in the body). |
| L-06 | The running instance depends on the Demo Lab DB, while route introspection ran in this repo's checkout. | Route surface is comparable (0 drift); database state is **not** comparable between the two. |

## 11.2 Runtime availability

| Target | Status |
|---|---|
| `127.0.0.1:8060` (the port named by `backend/.env`) | **NOT VERIFIED — nothing listening** (`http_code=000`) |
| `127.0.0.1:8070` (Demo Lab instance, PID 1014820, cwd `…/ct_93d5cdd/backend`, `uvicorn main:app`) | reachable; `/health` returns `{"status":"healthy", … "routes":50}`; `/openapi.json` = 777 operations (read-only GETs only) |
| `127.0.0.1:3000` (frontend dev server, PID 1014827 `react-scripts start`) | listening (not exercised) |
| Production (Render/Vercel) | **not contacted** |

`backend/.env` states the file is the isolated local env for this checkout and
that `SUPABASE_URL` is deliberately unroutable; it was not modified.

## 11.3 Database state

| Item | Finding |
|---|---|
| Cluster | one PostgreSQL cluster on `127.0.0.1:54426` hosting **two** databases |
| Repo `.env` DB | `ct_local_93d5cdd` — 135 public tables; `emission_factors` 0 rows; `organizations` 25; `customer_factors` 5 |
| Runtime DB (PID env) | `carbontally_demo_local` — 154 public tables; `emission_factors` 7,049; `organizations` 14; `calculation_snapshots` 34; `manual_processing_grants` 1; `customer_factors` 0 |
| Migration ledger | **absent in both** — applied-migration state is not database-verifiable |
| Enum types | **none** in either database |
| Objects without a corresponding migration in this checkout | `consultant_mode_change_requests`, `consultant_relationship_requests`, `consultant_mp_allocations`, `instrument_allocations`, `insight_concurrency_leases` (runtime only) |
| `audit_logs` rows | 0 in both databases |
| Writes performed by Phase 2 | **none** (only `SELECT`/catalogue queries) |

## 11.4 Unverified areas (carried)

1. Whether the runtime database's extra objects were introduced by uncommitted
   migrations, manual DDL, or a different seed path.
2. Whether `admin/` (the second React app) is deployed to production and which
   backend paths it calls (only `admin/src/services/*` were listed).
3. Concurrency/migration state of Phase 1's 7 failing tests (not re-run).
4. The exact semantics of `/api/v3/processing/items/*` body-level org scoping.
5. Messaging conversation-scope enforcement (N1) for the four entity/customer
   messaging families.
6. Whether supplier writes intentionally omit the client-access ceiling.
7. Real-time behaviour of notifications and presence.
8. Storage signed-URL authorisation path (`/api/v3/documents/{file_id}/signed-url`).
9. Worker/queue behaviour for the durable automatic-processing pipeline.
10. Accessibility and responsive behaviour of every surface.

---

# 12. INTEGRITY VERIFICATION

## 12.1 Git state — initial capture (before inspection)

| Command | Result | Class |
|---|---|---|
| `git rev-parse HEAD` | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` | A |
| `git rev-parse --abbrev-ref HEAD` | `p8-release-reconciled` | A |
| `git status --porcelain` counts | `78 M`, `192 ??` | A |
| `git diff --stat` totals | `78 files changed, 7440 insertions(+), 928 deletions(-)` | A |
| `git diff --name-only` | 78 paths (backend `api/*`, `auth.py`, `data/*`, docs, tools, …) | A |
| Baseline file present | `docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` — 72,782 bytes | A |
| Phase 2 deliverable present at start | **no** (`ls` → "No such file or directory") | A |

## 12.2 Git state — final capture (after inspection and report writing)

| Command | Result | Class |
|---|---|---|
| `git rev-parse HEAD` | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` (unchanged) | A |
| `git rev-parse --abbrev-ref HEAD` | `p8-release-reconciled` (unchanged) | A |
| `git status --porcelain` counts | `78 M`, `193 ??` | A |
| `git diff --stat` totals | `78 files changed, 7440 insertions(+), 928 deletions(-)` — **identical to the initial capture** | A |
| `git diff --name-only` | 78 paths (unchanged) | A |
| `git diff --cached --name-only` | 0 paths (nothing staged) | A |
| New untracked file | `docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md` (this report) | A |

## 12.3 Delta analysis

| Expectation (§17) | Observed | Conclusion |
|---|---|---|
| No `git reset` / `clean` / `checkout` / `restore` / `stash` / `rebase` / `commit` / `amend` | none issued | satisfied |
| No formatter or write-producing lint run | none run | satisfied |
| Tracked working tree unchanged | `git diff --stat` totals byte-identical before/after; 78 modified paths before and after | satisfied |
| Untracked delta = exactly one new file | `192 ??` → `193 ??`; the only new path is this report | satisfied |
| No change to the Phase 1 baseline | file size still 72,782 bytes and untouched | satisfied |

**Conclusion: the only repository change produced by Phase 2 is the creation of
`docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md`.**

## 12.4 Production / database / migration safety

| Safety rule (§4, §19) | Action taken |
|---|---|
| No production access | no request was sent to `carbontally-api.onrender.com` or `carbontally.co.uk`; only `127.0.0.1:8060`, `127.0.0.1:8070`, `127.0.0.1:3000` were probed read-only |
| No database writes | only `SELECT` / catalogue queries through `psql -At -c` |
| No migrations | none created or applied |
| No seed changes | none |
| No RLS changes | none |
| No service restart/repair | none; the running API and frontend dev server were left untouched |
| No `.env` modification | none (values read only; credentials never printed) |
| No secrets printed | credentials masked as `<creds>` in every artifact |
| No destructive test setup | none — no authenticated request was issued at all |

---

# 13. RECOMMENDED NEXT DISCOVERY TRACKS

**No fixes are prescribed here.** Each track is an inventory-derived
*investigation* that this read-only phase could not complete. None of these
tracks was started, and none is authorised by Phase 2.

| Track | Question to settle | Seeds from Phase 2 | Suggested evidence class |
|---|---|---|---|
| D-1 Security / authorization behavioural verification | For each of the 15 guard families and the 9 client-ceiling routes: does the observed HTTP outcome match the declared dependency, for every actor type in §45? | §2.3, §4.2–§4.8, §7.4 (Case A/E) | authenticated negative testing (ALLOW **and** DENY), per AGENTS §45 |
| D-2 RLS policy enumeration | Which tables have RLS enabled, which policies exist, and which service-role/pool code paths bypass them? | §4.9 (103 migrations; 45 `get_supabase_client` + 15 `get_pool` operations) | migration + catalog inspection, then negative DB tests |
| D-3 Migration ledger / runtime drift | Which runtime-database objects have no committed migration, and what is the true applied order? | §5.5, §11.3 | DB catalogue diff vs `supabase/migrations` |
| D-4 Master-data consistency | Should supplier/vehicle/facility/asset `type` be controlled vocabularies, and what is the canonical vocabulary source (catalogue vs table vs hardcoded arrays)? | §8.1, §8.2 | source + DB + PO decision |
| D-5 Client-ceiling coverage | Which organisation-plane writes should carry `require_client_operation`, given that suppliers does not while facilities/assets/vehicles do? | §7.3 #2/#3/#4, §7.4 Case A | source audit + behavioural test |
| D-6 Legacy surface consolidation plan | Which of the 302 legacy + 19 v2 operations are still exercised by any client, and which are dead? | §9.1, §9.2, §8.4 | endpoint telemetry / access logs + test coverage |
| D-7 Handler-level scoping review | For the ~700 operations whose guards are `require_auth`-only at the dependency level (`/api/v3/processing/items/*`, messaging, customer-review), is scope enforced inside the handler? | §2.3, §7.5 | source read + behavioural test |
| D-8 Commercial completeness | Which commercial capabilities are intentionally absent (checkout, provider, invoicing, trial, tax) versus planned, and where is `billing_plans` versioned? | §6.4, §6.5 | PO decision + schema inspection |
| D-9 UI state audit | Loading / empty / denied / error state for each of the 55 page components, plus responsive and accessibility behaviour at the §49 viewports | §3.5, §10.1 | browser automation + a11y tooling |
| D-10 Two-console consolidation | Should the internal console be `admin/` (separate app), `frontend/src/v3/ops` (`/ops`), or both, and is `admin/` in the deployed bundle? | §9.2 | deployment/config inspection + PO decision |
| D-11 Automatic-processing observance | Do the durable job states, retries and manual-review gates behave as the DB/state machine claims? | §6.3 (routing chain), §11.4 | worker/job-state inspection |
| D-12 Test-baseline re-establishment | Are Phase 1's 7 failures still current, and what do the un-run API-unit/Jest/integration/e2e suites report? | §10, §11.4 | test execution (requires a separate authorised task) |

## 13.1 Boundary of this report

This document is an **inventory**. It contains no recommendation to change code,
schema, RLS, seeds, tests or configuration, and it reopens no Product Owner
decision. Every statement is classified (A–G) and every unverifiable area is
marked UNKNOWN / NOT VERIFIED rather than filled in.

---

# APPENDIX A — COMPLETE REGISTERED ROUTE LISTING (781 operations)

Machine-generated from the in-process enumeration of this checkout
(`/tmp/p2_routes_effective.json` → `/tmp/p2_route_table.tsv` → this listing).
Columns: `METHODS  PATH  DECLARED-GUARD-CODES  M|R` where the guard codes are the
abbreviations defined in §2.3 and `M` = mutation (`POST`/`PUT`/`PATCH`/`DELETE`),
`R` = read (`GET`). Guard codes are derived from the FastAPI dependency graph and
do not include guards applied inside handler bodies.

```text
GET          /                                                                              NONE                               R
GET          /api/admin/analytics/system/health                                             ADMIN+USER                         R
GET          /api/admin/analytics/system/performance                                        ADMIN+USER                         R
GET          /api/admin/analytics/system/usage                                              ADMIN+USER                         R
GET          /api/admin/assignments/assignment-stats                                        ROLE+USER                          R
GET          /api/admin/assignments/available                                               ROLE+USER                          R
POST         /api/admin/assignments/batch/{batch_id}/assign                                 ROLE+USER                          M
GET          /api/admin/assignments/staff                                                   ROLE+USER                          R
GET          /api/admin/audit/activity                                                      ADMIN+USER                         R
GET          /api/admin/audit/activity/export                                               ADMIN+USER                         R
GET          /api/admin/audit/activity/search                                               ADMIN+USER                         R
GET          /api/admin/audit/activity/{log_id}                                             ADMIN+USER                         R
GET          /api/admin/beta/codes                                                          ADMIN+USER                         R
POST         /api/admin/beta/codes                                                          ADMIN+USER                         M
GET          /api/admin/beta/codes/validate/{code}                                          USER_OPTIONAL+USER                 R
DELETE       /api/admin/beta/codes/{code_id}                                                ADMIN+USER                         M
PUT          /api/admin/beta/codes/{code_id}/status                                         ADMIN+USER                         M
GET          /api/admin/beta/users                                                          ADMIN+USER                         R
POST         /api/admin/beta/users                                                          ADMIN+USER                         M
GET          /api/admin/beta/users/stats                                                    ADMIN+USER                         R
DELETE       /api/admin/beta/users/{user_id}                                                ADMIN+USER                         M
PUT          /api/admin/beta/users/{user_id}/access                                         ADMIN+USER                         M
DELETE       /api/admin/bulk/documents/bulk                                                 ADMIN+USER                         M
POST         /api/admin/bulk/documents/status                                               ADMIN+USER                         M
POST         /api/admin/bulk/organizations/status                                           ADMIN+USER                         M
GET          /api/admin/defra/activities                                                    ADMIN+USER                         R
GET          /api/admin/defra/factors                                                       ADMIN+USER                         R
POST         /api/admin/defra/factors                                                       ADMIN+USER                         M
POST         /api/admin/defra/factors/bulk                                                  ADMIN+USER                         M
DELETE       /api/admin/defra/factors/{factor_id}                                           ADMIN+USER                         M
GET          /api/admin/defra/factors/{factor_id}                                           ADMIN+USER                         R
PUT          /api/admin/defra/factors/{factor_id}                                           ADMIN+USER                         M
GET          /api/admin/defra/validate                                                      ADMIN+USER                         R
GET          /api/admin/defra/years                                                         ADMIN+USER                         R
GET          /api/admin/email/templates                                                     ADMIN+USER                         R
POST         /api/admin/email/templates                                                     ADMIN+USER                         M
POST         /api/admin/email/templates/reset-defaults                                      ADMIN+USER                         M
GET          /api/admin/email/templates/types                                               ADMIN+USER                         R
DELETE       /api/admin/email/templates/{template_id}                                       ADMIN+USER                         M
GET          /api/admin/email/templates/{template_id}                                       ADMIN+USER                         R
PUT          /api/admin/email/templates/{template_id}                                       ADMIN+USER                         M
POST         /api/admin/email/templates/{template_id}/preview                               ADMIN+USER                         M
POST         /api/admin/extraction/approve                                                  ROLE+USER                          M
POST         /api/admin/extraction/batch/approve                                            ROLE+USER                          M
POST         /api/admin/extraction/manual-review-note                                       ROLE+USER                          M
GET          /api/admin/extraction/reviews/pending                                          ROLE+USER                          R
GET          /api/admin/logs/email                                                          ADMIN+USER                         R
GET          /api/admin/logs/email/email/{email_address}                                    ADMIN+USER                         R
GET          /api/admin/logs/email/stats                                                    ADMIN+USER                         R
GET          /api/admin/logs/email/{log_id}                                                 ADMIN+USER                         R
GET          /api/admin/logs/processing                                                     ADMIN+USER                         R
GET          /api/admin/logs/processing/file/{file_id}                                      ADMIN+USER                         R
GET          /api/admin/logs/processing/stats                                               ADMIN+USER                         R
GET          /api/admin/logs/processing/{log_id}                                            ADMIN+USER                         R
GET          /api/admin/permissions/permissions/list                                        ROLE+USER                          R
GET          /api/admin/permissions/roles                                                   ROLE+USER                          R
POST         /api/admin/permissions/roles                                                   ROLE+USER                          M
DELETE       /api/admin/permissions/roles/{role_id}                                         ROLE+USER                          M
GET          /api/admin/permissions/roles/{role_id}                                         ROLE+USER                          R
PUT          /api/admin/permissions/roles/{role_id}                                         ROLE+USER                          M
POST         /api/admin/permissions/setup-defaults                                          ROLE+USER                          M
POST         /api/admin/queue/reassign                                                      ADMIN+USER                         M
GET          /api/admin/queue/settings                                                      ADMIN+USER                         R
PUT          /api/admin/queue/settings                                                      ADMIN+USER                         M
GET          /api/admin/queue/stats                                                         ADMIN+USER                         R
GET          /api/admin/reviews/history                                                     ADMIN+USER                         R
GET          /api/admin/reviews/history/audit                                               ADMIN+USER                         R
GET          /api/admin/reviews/history/audit/export                                        ADMIN+USER                         R
GET          /api/admin/reviews/history/staff/{staff_id}                                    ADMIN+USER                         R
GET          /api/admin/reviews/my-queue                                                    ROLE+USER                          R
POST         /api/admin/reviews/my-queue/{review_id}/start                                  ROLE+USER                          M
GET          /api/admin/reviews/queue                                                       ROLE+USER                          R
POST         /api/admin/reviews/queue/escalate                                              ADMIN+USER                         M
GET          /api/admin/reviews/queue/priority                                              ADMIN+USER                         R
POST         /api/admin/reviews/queue/reorder                                               ADMIN+USER                         M
GET          /api/admin/reviews/queue/sla-monitor                                           ADMIN+USER                         R
GET          /api/admin/reviews/queue/stats/detailed                                        ADMIN+USER                         R
GET          /api/admin/reviews/{review_id}                                                 ROLE+USER                          R
POST         /api/admin/reviews/{review_id}/assign                                          ROLE+USER                          M
POST         /api/admin/reviews/{review_id}/complete                                        ROLE+USER                          M
GET          /api/admin/reviews/{review_id}/history                                         ADMIN+USER                         R
POST         /api/admin/reviews/{review_id}/reject                                          ROLE+USER                          M
POST         /api/admin/settings/reset                                                      ADMIN+USER                         M
GET          /api/admin/settings/settings-history                                           ADMIN+USER                         R
POST         /api/admin/settings/validate                                                   ADMIN+USER                         M
GET          /api/admin/staff                                                               ROLE+USER                          R
POST         /api/admin/staff/                                                              ROLE+USER                          M
GET          /api/admin/staff/activity                                                      ADMIN+USER                         R
GET          /api/admin/staff/me                                                            STAFF_LEGACY+USER                  R
GET          /api/admin/staff/performance                                                   ADMIN+USER                         R
GET          /api/admin/staff/performance/compare                                           ADMIN+USER                         R
GET          /api/admin/staff/performance/dashboard                                         ADMIN+USER                         R
GET          /api/admin/staff/performance/export                                            ADMIN+USER                         R
GET          /api/admin/staff/workload                                                      ADMIN+USER                         R
GET          /api/admin/staff/workload/{staff_id}                                           ADMIN+USER                         R
DELETE       /api/admin/staff/{staff_id}                                                    ROLE+USER                          M
GET          /api/admin/staff/{staff_id}                                                    ROLE+USER                          R
PUT          /api/admin/staff/{staff_id}                                                    ROLE+USER                          M
GET          /api/admin/staff/{staff_id}/activity-log                                       ADMIN+USER                         R
GET          /api/admin/staff/{staff_id}/performance-history                                ADMIN+USER                         R
POST         /api/admin/staff/{staff_id}/reset-password                                     ADMIN+USER                         M
PUT          /api/admin/staff/{staff_id}/role                                               ROLE+USER                          M
GET          /api/admin/workload/forecast                                                   ADMIN+USER                         R
GET          /api/admin/workload/forecast/export                                            ADMIN+USER                         R
GET          /api/admin/workload/forecast/scenarios                                         ADMIN+USER                         R
GET          /api/admin/workload/forecast/summary                                           ADMIN+USER                         R
GET          /api/batches/stats                                                             AUTH_ONLY+USER                     R
POST         /api/batches/{batch_id}/cancel                                                 AUTH_ONLY+USER                     M
GET          /api/batches/{batch_id}/progress                                               AUTH_ONLY+USER                     R
GET          /api/batches/{batch_id}/status                                                 AUTH_ONLY+USER                     R
GET          /api/beta/me                                                                   AUTH_ONLY+USER                     R
POST         /api/beta/redeem                                                               AUTH_ONLY+USER                     M
POST         /api/bulk/approve                                                              ORG_MEMBER+USER                    M
POST         /api/bulk/reject                                                               ORG_MEMBER+USER                    M
GET          /api/by-asset                                                                  ORG_MEMBER+USER                    R
GET          /api/by-document-type                                                          ORG_MEMBER+USER                    R
GET          /api/customer-documents/assets/{asset_id}                                      ORG_MEMBER+USER                    R
GET          /api/customer-documents/documents/{org_id}                                     ORG_MEMBER+USER                    R
GET          /api/customer-documents/pending/{org_id}                                       ORG_MEMBER+USER                    R
POST         /api/customer-documents/staff/organize/{document_id}                           ROLE+USER                          M
GET          /api/customer-documents/stats/detailed                                         ORG_MEMBER+USER                    R
GET          /api/customer-documents/stats/{org_id}                                         ORG_MEMBER+USER                    R
GET          /api/customer-documents/{document_id}                                          ORG_MEMBER+USER                    R
GET          /api/customer-documents/{document_id}/download                                 ORG_MEMBER+USER                    R
GET          /api/customer-documents/{document_id}/extraction                               ORG_MEMBER+USER                    R
GET          /api/customer-documents/{document_id}/history                                  ORG_MEMBER+USER                    R
GET          /api/customer-documents/{document_id}/notes                                    ORG_MEMBER+USER                    R
POST         /api/customer-documents/{document_id}/notes                                    ORG_MEMBER+USER                    M
POST         /api/customer-documents/{document_id}/request-review                           ORG_MEMBER+USER                    M
POST         /api/customer-documents/{document_id}/verify                                   ORG_MEMBER+USER                    M
GET          /api/customer-documents/{document_id}/versions                                 ORG_MEMBER+USER                    R
POST         /api/customer-documents/{document_id}/versions                                 ORG_MEMBER+USER                    M
GET          /api/documents/admin/reviews/customer                                          ADMIN+USER                         R
GET          /api/documents/organizations/{org_id}/documents/activity                       ORG_MEMBER+USER                    R
GET          /api/documents/stats/{org_id}                                                  ORG_MEMBER+USER                    R
GET          /api/documents/{file_id}/activity                                              ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER R
GET          /api/documents/{file_id}/activity/export                                       ADMIN+USER                         R
POST         /api/documents/{file_id}/review/response                                       ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER M
GET          /api/documents/{file_id}/reviews                                               ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER R
GET          /api/documents/{org_id}                                                        ORG_MEMBER+USER                    R
POST         /api/documents/{org_id}/admin/{file_id}/status                                 ROLE+USER                          M
POST         /api/documents/{org_id}/{file_id}/review                                       ORG_MEMBER+USER                    M
GET          /api/documents/{org_id}/{file_id}/status                                       ORG_MEMBER+USER                    R
GET          /api/drafts/                                                                   ORG_MEMBER+USER                    R
POST         /api/drafts/save                                                               ORG_MEMBER+USER                    M
DELETE       /api/drafts/{draft_id}                                                         ORG_MEMBER+USER                    M
GET          /api/drafts/{draft_id}                                                         ORG_MEMBER+USER                    R
GET          /api/drafts/{draft_id}/progress                                                AUTH_ONLY+USER                     R
POST         /api/drafts/{draft_id}/publish                                                 AUTH_ONLY+USER                     M
GET          /api/drafts/{draft_id}/sections                                                AUTH_ONLY+USER                     R
DELETE       /api/drafts/{draft_id}/sections/{section_id}                                   AUTH_ONLY+USER                     M
POST         /api/drafts/{draft_id}/sections/{section_id}                                   AUTH_ONLY+USER                     M
POST         /api/drafts/{draft_id}/submit                                                  ORG_MEMBER+USER                    M
POST         /api/drafts/{draft_id}/validate                                                AUTH_ONLY+USER                     M
POST         /api/emissions                                                                 ORG_MEMBER+USER                    M
POST         /api/emissions/bulk                                                            ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER M
GET          /api/emissions/export                                                          ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER R
GET          /api/emissions/stats                                                           ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER R
POST         /api/emissions/verify                                                          ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER M
DELETE       /api/emissions/{record_id}                                                     ORG_MEMBER+USER                    M
PUT          /api/emissions/{record_id}                                                     ORG_MEMBER_OR_STAFF+ORG_MEMBER+USER M
GET          /api/feedback                                                                  AUTH_ONLY+USER                     R
POST         /api/feedback                                                                  AUTH_ONLY+USER                     M
GET          /api/feedback/admin/feedback/pending                                           ADMIN+USER                         R
GET          /api/feedback/admin/feedback/stats                                             ADMIN+USER                         R
GET          /api/feedback/{feedback_id}                                                    AUTH_ONLY+USER                     R
PUT          /api/feedback/{feedback_id}                                                    ADMIN+USER                         M
POST         /api/generate-enhanced-report                                                  ORG_MEMBER+USER                    M
POST         /api/generate-sustainability-report                                            ORG_MEMBER+USER                    M
GET          /api/glossary/                                                                 NONE                               R
POST         /api/glossary/                                                                 ROLE+USER                          M
GET          /api/glossary/categories                                                       NONE                               R
GET          /api/glossary/search                                                           AUTH_ONLY+USER                     R
DELETE       /api/glossary/{term_id}                                                        ROLE+USER                          M
GET          /api/glossary/{term_id}                                                        NONE                               R
PUT          /api/glossary/{term_id}                                                        ROLE+USER                          M
POST         /api/glossary/{term_id}/restore                                                ROLE+USER                          M
GET          /api/logs/                                                                     ROLE+USER                          R
POST         /api/logs/                                                                     ORG_MEMBER+USER                    M
GET          /api/logs/analytics/errors                                                     ROLE+USER                          R
GET          /api/logs/analytics/stats                                                      ROLE+USER                          R
GET          /api/logs/analytics/users                                                      ROLE+USER                          R
GET          /api/logs/documents/{file_id}                                                  ORG_MEMBER+USER                    R
POST         /api/notifications/batch/completion                                            ROLE+USER                          M
POST         /api/notifications/customer/manual-extraction                                  ROLE+USER                          M
POST         /api/notifications/staff                                                       ROLE+USER                          M
GET          /api/notifications/templates                                                   ROLE+USER                          R
POST         /api/organizations/                                                            ROLE+USER                          M
GET          /api/organizations/analytics/asset-performance                                 ORG_MEMBER+USER                    R
GET          /api/organizations/analytics/emissions-trend                                   ORG_MEMBER+USER                    R
GET          /api/organizations/analytics/scope-comparison                                  ORG_MEMBER+USER                    R
GET          /api/organizations/analytics/summary                                           ORG_MEMBER+USER                    R
GET          /api/organizations/data/organizations/{org_id}/assets                          ORG_MEMBER+USER                    R
GET          /api/organizations/data/{org_id}/defra-factors                                 ORG_MEMBER+USER                    R
GET          /api/organizations/data/{org_id}/emissions-data                                ORG_MEMBER+USER                    R
GET          /api/organizations/data/{org_id}/emissions/export-csv                          ORG_MEMBER+USER                    R
GET          /api/organizations/files/                                                      ORG_MEMBER+USER                    R
POST         /api/organizations/files/api/organizations/{org_id}/files/upload               ORG_MEMBER+USER                    M
POST         /api/organizations/files/bulk-upload                                           ORG_MEMBER+USER                    M
GET          /api/organizations/files/organizations/{org_id}/files/stats                    ORG_MEMBER+USER                    R
DELETE       /api/organizations/files/{file_id}                                             ORG_MEMBER+USER                    M
GET          /api/organizations/files/{file_id}/download                                    ORG_MEMBER+USER                    R
GET          /api/organizations/files/{file_id}/url                                         ORG_MEMBER+USER                    R
GET          /api/organizations/files/{org_id}/files/archived                               ORG_ADMIN+USER                     R
POST         /api/organizations/files/{org_id}/files/{file_id}/archive                      ORG_ADMIN+USER                     M
GET          /api/organizations/files/{org_id}/files/{file_id}/comments                     ORG_MEMBER+USER                    R
POST         /api/organizations/files/{org_id}/files/{file_id}/comments                     ORG_MEMBER+USER                    M
DELETE       /api/organizations/files/{org_id}/files/{file_id}/comments/{comment_id}        ORG_MEMBER+USER                    M
PUT          /api/organizations/files/{org_id}/files/{file_id}/comments/{comment_id}        ORG_MEMBER+USER                    M
DELETE       /api/organizations/files/{org_id}/files/{file_id}/permanent                    ORG_ADMIN+USER                     M
POST         /api/organizations/files/{org_id}/files/{file_id}/restore                      ORG_ADMIN+USER                     M
GET          /api/organizations/files/{org_id}/files/{file_id}/versions                     ORG_MEMBER+USER                    R
POST         /api/organizations/files/{org_id}/files/{file_id}/versions                     ORG_MEMBER+USER                    M
GET          /api/organizations/files/{org_id}/files/{file_id}/versions/{version_id}        ORG_MEMBER+USER                    R
GET          /api/organizations/members/                                                    ORG_MEMBER+USER                    R
POST         /api/organizations/members/invite                                              ORG_MEMBER+USER                    M
GET          /api/organizations/members/user/{user_id}                                      AUTH_ONLY+USER                     R
DELETE       /api/organizations/members/{member_id}                                         ORG_MEMBER+USER                    M
PUT          /api/organizations/members/{member_id}                                         ORG_MEMBER+USER                    M
POST         /api/organizations/members/{member_id}/resend-invite                           ORG_MEMBER+USER                    M
POST         /api/organizations/members/{org_id}/members/bulk/remove                        ORG_ADMIN+USER                     M
POST         /api/organizations/members/{org_id}/members/bulk/update                        ORG_ADMIN+USER                     M
GET          /api/organizations/members/{org_id}/members/roles                              ORG_MEMBER+USER                    R
GET          /api/organizations/members/{org_id}/members/stats                              ORG_MEMBER+USER                    R
POST         /api/organizations/team/{org_id}/invite                                        ORG_MEMBER+USER                    M
GET          /api/organizations/team/{org_id}/members                                       ORG_MEMBER+USER                    R
DELETE       /api/organizations/team/{org_id}/members/{member_id}                           ORG_MEMBER+USER                    M
PATCH        /api/organizations/team/{org_id}/members/{member_id}                           ORG_MEMBER+USER                    M
DELETE       /api/organizations/{org_id}                                                    ROLE+USER                          M
GET          /api/organizations/{org_id}                                                    ROLE+USER                          R
PUT          /api/organizations/{org_id}                                                    ROLE+USER                          M
GET          /api/organizations/{org_id}/assets                                             ORG_MEMBER+USER                    R
POST         /api/organizations/{org_id}/assets                                             ORG_ADMIN+USER                     M
POST         /api/organizations/{org_id}/assets/bulk/create                                 ORG_ADMIN+USER                     M
GET          /api/organizations/{org_id}/assets/stats                                       ORG_MEMBER+USER                    R
DELETE       /api/organizations/{org_id}/assets/{asset_id}                                  ORG_ADMIN+USER                     M
PUT          /api/organizations/{org_id}/assets/{asset_id}                                  ORG_ADMIN+USER                     M
GET          /api/organizations/{org_id}/dashboard-summary                                  ORG_MEMBER+USER                    R
GET          /api/organizations/{org_id}/exports                                            ORG_MEMBER+USER                    R
POST         /api/organizations/{org_id}/exports/exports/emissions                          ORG_MEMBER+USER                    M
DELETE       /api/organizations/{org_id}/exports/{export_id}                                ORG_ADMIN+USER                     M
GET          /api/organizations/{org_id}/exports/{export_id}/download                       ORG_MEMBER+USER                    R
GET          /api/organizations/{org_id}/facilities                                         ORG_MEMBER+USER                    R
POST         /api/organizations/{org_id}/facilities                                         ORG_ADMIN+USER                     M
GET          /api/organizations/{org_id}/facilities/stats                                   ORG_MEMBER+USER                    R
DELETE       /api/organizations/{org_id}/facilities/{facility_id}                           ORG_ADMIN+USER                     M
PATCH        /api/organizations/{org_id}/facilities/{facility_id}                           ORG_ADMIN+USER                     M
PUT          /api/organizations/{org_id}/facilities/{facility_id}                           ORG_ADMIN+USER                     M
POST         /api/organizations/{org_id}/members/bulk/invite                                ORG_ADMIN+USER                     M
GET          /api/organizations/{org_id}/metadata/all                                       ORG_MEMBER+USER                    R
GET          /api/organizations/{org_id}/metadata/contacts                                  ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/contacts                                  ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/metadata/custom-metrics                            ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/custom-metrics                            ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/metadata/employees                                 ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/employees                                 ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/metadata/financials                                ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/financials                                ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/metadata/industry                                  ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/industry                                  ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/metadata/required-fields                           ORG_MEMBER+USER                    R
GET          /api/organizations/{org_id}/metadata/sustainability                            ORG_MEMBER+USER                    R
PUT          /api/organizations/{org_id}/metadata/sustainability                            ORG_MEMBER+USER                    M
POST         /api/organizations/{org_id}/metadata/validate                                  ORG_MEMBER+USER                    M
GET          /api/organizations/{org_id}/organization-activity                              ORG_MEMBER+USER                    R
GET          /api/organizations/{org_id}/stats                                              ROLE+USER                          R
GET          /api/reference/asset-types                                                     AUTH_ONLY+USER                     R
GET          /api/reference/assets                                                          AUTH_ONLY+USER                     R
GET          /api/reference/categories                                                      AUTH_ONLY+USER                     R
GET          /api/reference/facilities                                                      AUTH_ONLY+USER                     R
GET          /api/reference/facility-types                                                  AUTH_ONLY+USER                     R
GET          /api/reference/fuel-types                                                      AUTH_ONLY+USER                     R
GET          /api/reference/units                                                           AUTH_ONLY+USER                     R
POST         /api/repair-pdf                                                                ORG_MEMBER+USER                    M
POST         /api/reports/admin/import-defra-factors                                        ADMIN+USER                         M
GET          /api/reports/admin/organization-comparison                                     ADMIN+USER                         R
GET          /api/reports/admin/staff-performance                                           ADMIN+USER                         R
GET          /api/reports/customer/summary                                                  ORG_MEMBER+USER                    R
GET          /api/reports/defra-factors/{reporting_year}                                    ORG_MEMBER+USER                    R
GET          /api/reports/defra-mapping                                                     ORG_MEMBER+USER                    R
GET          /api/reports/emissions/trend                                                   ORG_MEMBER+USER                    R
POST         /api/reports/generate                                                          ORG_MEMBER+USER                    M
POST         /api/reports/generate-enhanced-report                                          ORG_MEMBER+USER                    M
GET          /api/reports/metrics                                                           ORG_MEMBER+USER                    R
GET          /api/reports/report_status                                                     NONE                               R
GET          /api/reports/schedule                                                          ORG_MEMBER+USER                    R
POST         /api/reports/schedule                                                          ORG_MEMBER+USER                    M
GET          /api/reports/schedule/frequencies                                              ORG_MEMBER+USER                    R
DELETE       /api/reports/schedule/{schedule_id}                                            ORG_MEMBER+USER                    M
GET          /api/reports/shared                                                            ORG_MEMBER+USER                    R
GET          /api/reports/templates                                                         ORG_MEMBER+USER                    R
POST         /api/reports/templates                                                         ORG_MEMBER+USER                    M
GET          /api/reports/templates/categories                                              ORG_MEMBER+USER                    R
DELETE       /api/reports/templates/{template_id}                                           ORG_MEMBER+USER                    M
PUT          /api/reports/templates/{template_id}                                           ORG_MEMBER+USER                    M
GET          /api/reports/types                                                             ORG_MEMBER+USER                    R
POST         /api/reports/{report_id}/share                                                 ORG_MEMBER+USER                    M
GET          /api/stats/summary                                                             ORG_MEMBER+USER                    R
POST         /api/test-upload                                                               NONE                               M
POST         /api/upload                                                                    ORG_MEMBER+USER                    M
POST         /api/upload-batch                                                              ORG_MEMBER+USER                    M
POST         /api/upload-csv                                                                ORG_MEMBER+USER                    M
POST         /api/upload-pdf                                                                ORG_MEMBER+USER                    M
POST         /api/users/change-password                                                     USER                               M
POST         /api/users/password-reset                                                      NONE                               M
POST         /api/users/password-reset/confirm                                              NONE                               M
GET          /api/users/profile                                                             USER                               R
PUT          /api/users/profile                                                             USER                               M
GET          /api/v2/admin/aliases                                                          ADMIN+USER                         R
POST         /api/v2/admin/aliases                                                          ADMIN+USER                         M
DELETE       /api/v2/admin/aliases/{alias_id}                                               ADMIN+USER                         M
PUT          /api/v2/admin/aliases/{alias_id}                                               ADMIN+USER                         M
GET          /api/v2/admin/audit                                                            ADMIN+USER                         R
GET          /api/v2/admin/audit/correlation/{correlation_id}                               ADMIN+USER                         R
GET          /api/v2/admin/audit/export                                                     ADMIN+USER                         R
GET          /api/v2/admin/audit/{entry_id}                                                 ADMIN+USER                         R
GET          /api/v2/admin/imports                                                          ADMIN+USER                         R
GET          /api/v2/admin/imports/active                                                   ADMIN+USER                         R
GET          /api/v2/admin/imports/{batch_id}                                               ADMIN+USER                         R
GET          /api/v2/admin/providers                                                        ADMIN+USER                         R
GET          /api/v2/admin/providers/{key}                                                  ADMIN+USER                         R
POST         /api/v2/benchmark                                                              USER                               M
POST         /api/v2/calculate                                                              USER                               M
POST         /api/v2/factor-match                                                           USER                               M
POST         /api/v2/generate-report                                                        USER                               M
GET          /api/v2/health                                                                 NONE                               R
POST         /api/v2/validate                                                               USER                               M
POST         /api/v3/accounting/acting-for                                                  USER                               M
POST         /api/v3/accounting/acting-for/attribute                                        USER                               M
GET          /api/v3/accounting/acting-for/attribution                                      USER                               R
GET          /api/v3/accounting/context                                                     USER                               R
POST         /api/v3/accounting/dimensions/resolve                                          USER                               M
GET          /api/v3/accounting/dimensions/snapshot/{snapshot_id}                           USER                               R
GET          /api/v3/accounting/organizations                                               USER                               R
GET          /api/v3/accounting/scope3/categories                                           USER                               R
POST         /api/v3/activity-clarifications/clarifications                                 USER                               M
POST         /api/v3/activity-clarifications/decline                                        USER                               M
GET          /api/v3/activity-clarifications/effective                                      USER                               R
GET          /api/v3/activity-clarifications/history                                        USER                               R
GET          /api/v3/activity-clarifications/options                                        USER                               R
GET          /api/v3/admin/backups                                                          BACKUP_MGR+USER                    R
POST         /api/v3/admin/backups                                                          BACKUP_MGR+USER                    M
GET          /api/v3/admin/backups/policy                                                   BACKUP_MGR+USER                    R
PUT          /api/v3/admin/backups/policy                                                   BACKUP_MGR+USER                    M
GET          /api/v3/admin/backups/status                                                   BACKUP_MGR+USER                    R
GET          /api/v3/admin/backups/{job_id}                                                 BACKUP_MGR+USER                    R
GET          /api/v3/admin/backups/{job_id}/download                                        BACKUP_MGR+USER                    R
GET          /api/v3/admin/backups/{job_id}/pair                                            BACKUP_MGR+USER                    R
POST         /api/v3/admin/backups/{job_id}/verify                                          BACKUP_MGR+USER                    M
GET          /api/v3/admin/consultants/mode-change-requests                                 ADMIN+USER                         R
POST         /api/v3/admin/consultants/mode-change-requests/{request_id}/decision           ADMIN+USER                         M
GET          /api/v3/admin/entities                                                         ADMIN+USER                         R
POST         /api/v3/admin/entities                                                         ADMIN+USER                         M
GET          /api/v3/admin/entities/{entity_id}                                             ADMIN+USER                         R
PUT          /api/v3/admin/entities/{entity_id}                                             ADMIN+USER                         M
GET          /api/v3/admin/manual-processing/clients/{organization_id}                      STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
POST         /api/v3/admin/manual-processing/coverage/allocations                           STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
DELETE       /api/v3/admin/manual-processing/coverage/allocations/{allocation_id}           STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
GET          /api/v3/admin/manual-processing/coverage/{consultant_id}                       STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
GET          /api/v3/admin/manual-processing/effective/{organization_id}                    STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
GET          /api/v3/admin/manual-processing/grants                                         STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
PUT          /api/v3/admin/manual-processing/grants                                         STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
DELETE       /api/v3/admin/manual-processing/grants/{scope_type}/{scope_id}                 STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
GET          /api/v3/admin/manual-processing/organizations                                  STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
GET          /api/v3/admin/manual-processing/processors                                     STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
PUT          /api/v3/admin/manual-processing/processors                                     STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
DELETE       /api/v3/admin/manual-processing/processors/{scope_type}/{scope_id}             STAFF+MP_ADMIN+STAFF_LEGACY+USER   M
GET          /api/v3/admin/manual-processing/state                                          STAFF+MP_ADMIN+STAFF_LEGACY+USER   R
GET          /api/v3/admin/review-queue                                                     ADMIN+USER                         R
GET          /api/v3/admin/review-queue/{review_id}                                         ADMIN+USER                         R
POST         /api/v3/admin/review-queue/{review_id}/assign                                  ADMIN+USER                         M
POST         /api/v3/admin/review-queue/{review_id}/complete                                ADMIN+USER                         M
GET          /api/v3/admin/sla/settings                                                     ADMIN+USER                         R
PUT          /api/v3/admin/sla/settings                                                     ADMIN+USER                         M
GET          /api/v3/batches                                                                ORG_MEMBER+USER                    R
POST         /api/v3/batches                                                                ORG_MEMBER+USER                    M
GET          /api/v3/batches/{batch_id}                                                     ORG_MEMBER+USER                    R
PATCH        /api/v3/batches/{batch_id}                                                     ORG_MEMBER+USER                    M
POST         /api/v3/billing/managed/orders                                                 ORG_MEMBER+USER                    M
GET          /api/v3/billing/me                                                             ORG_MEMBER+USER                    R
GET          /api/v3/billing/me/credits                                                     ORG_MEMBER+USER                    R
GET          /api/v3/billing/me/orders                                                      ORG_MEMBER+USER                    R
GET          /api/v3/billing/me/orders/{order_id}                                           ORG_MEMBER+USER                    R
GET          /api/v3/billing/me/payments                                                    ORG_MEMBER+USER                    R
POST         /api/v3/billing/me/storage/refresh                                             ORG_MEMBER+USER                    M
POST         /api/v3/billing/orders/assisted                                                ORG_MEMBER+USER                    M
POST         /api/v3/billing/orders/{order_id}/approve                                      ORG_MEMBER+USER                    M
POST         /api/v3/billing/orders/{order_id}/cancel                                       ORG_MEMBER+USER                    M
GET          /api/v3/capabilities                                                           USER                               R
GET          /api/v3/commercial/config                                                      STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/config/{config_key}                                         STAFF+STAFF_LEGACY+USER            R
PUT          /api/v3/commercial/config/{config_key}                                         STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/credits/adjust                                              STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/credits/grant                                               STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/credits/refund                                              STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/credits/reverse                                             STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/credits/rollover                                            STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/commercial/entitlement/{organization_id}                               STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/ledger                                                      STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/orders                                                      STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/orders/{order_id}                                           STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/commercial/orders/{order_id}/complete                                  STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/commercial/organizations                                               STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/overview                                                    STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/payments                                                    STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/plans                                                       STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/commercial/plans                                                       STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/commercial/plans/{plan_code}                                           STAFF+STAFF_LEGACY+USER            R
PUT          /api/v3/commercial/plans/{plan_code}                                           STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/commercial/storage                                                     STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/commercial/subscriptions                                               STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/commercial/subscriptions                                               STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/commercial/subscriptions/{subscription_id}/status                      STAFF+STAFF_LEGACY+USER            M
DELETE       /api/v3/consultants/clients/{client_id}                                        CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}                                        CONSULTANT+USER                    R
PUT          /api/v3/consultants/clients/{client_id}                                        CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/access-profile                         CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}/context                                CONSULTANT+USER                    R
GET          /api/v3/consultants/clients/{client_id}/dashboard                              CONSULTANT+USER                    R
GET          /api/v3/consultants/clients/{client_id}/documents                              CONSULTANT+USER                    R
POST         /api/v3/consultants/clients/{client_id}/documents                              CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/documents/upload-url                   CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/documents/{document_id}/upload-abandon CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/documents/{document_id}/upload-complete CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/end                                    CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}/evidence                               CONSULTANT+USER                    R
GET          /api/v3/consultants/clients/{client_id}/invitations                            CONSULTANT+USER                    R
POST         /api/v3/consultants/clients/{client_id}/invitations                            CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/invitations/{invitation_id}/revoke     CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}/issues                                 CONSULTANT+USER                    R
GET          /api/v3/consultants/clients/{client_id}/processing/items                       CONSULTANT+USER                    R
GET          /api/v3/consultants/clients/{client_id}/processing/status                      CONSULTANT+USER                    R
POST         /api/v3/consultants/clients/{client_id}/reactivate                             CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}/reports                                CONSULTANT+USER                    R
POST         /api/v3/consultants/clients/{client_id}/retention                              CONSULTANT+USER                    M
POST         /api/v3/consultants/clients/{client_id}/suspend                                CONSULTANT+USER                    M
GET          /api/v3/consultants/clients/{client_id}/users                                  CONSULTANT+USER                    R
PATCH        /api/v3/consultants/clients/{client_id}/users/{member_id}                      CONSULTANT+USER                    M
GET          /api/v3/consultants/me                                                         CONSULTANT+USER                    R
POST         /api/v3/consultants/me                                                         USER                               M
GET          /api/v3/consultants/me/branding                                                CONSULTANT+USER                    R
PUT          /api/v3/consultants/me/branding                                                CONSULTANT+USER                    M
GET          /api/v3/consultants/me/branding/context                                        CONSULTANT+USER                    R
GET          /api/v3/consultants/me/clients                                                 CONSULTANT+USER                    R
POST         /api/v3/consultants/me/clients                                                 CONSULTANT+USER                    M
GET          /api/v3/consultants/me/custom-domains                                          CONSULTANT+USER                    R
POST         /api/v3/consultants/me/custom-domains                                          CONSULTANT+USER                    M
POST         /api/v3/consultants/me/custom-domains/{domain_id}/activate                     CONSULTANT+USER                    M
POST         /api/v3/consultants/me/custom-domains/{domain_id}/remove                       CONSULTANT+USER                    M
POST         /api/v3/consultants/me/custom-domains/{domain_id}/verify                       CONSULTANT+USER                    M
POST         /api/v3/consultants/me/customers                                               CONSULTANT+USER                    M
GET          /api/v3/consultants/me/dashboard                                               CONSULTANT+USER                    R
GET          /api/v3/consultants/me/engagements                                             CONSULTANT+USER                    R
POST         /api/v3/consultants/me/manual-processing/allocations                           CONSULTANT+USER                    M
DELETE       /api/v3/consultants/me/manual-processing/allocations/{allocation_id}           CONSULTANT+USER                    M
GET          /api/v3/consultants/me/manual-processing/coverage                              CONSULTANT+USER                    R
GET          /api/v3/consultants/me/mode-change-requests                                    CONSULTANT+USER                    R
POST         /api/v3/consultants/me/mode-change-requests                                    CONSULTANT+USER                    M
GET          /api/v3/consultants/me/relationship-requests                                   CONSULTANT+USER                    R
POST         /api/v3/consultants/me/relationship-requests/{request_id}/decision             CONSULTANT+USER                    M
GET          /api/v3/consultants/me/senders                                                 CONSULTANT+USER                    R
POST         /api/v3/consultants/me/senders                                                 CONSULTANT+USER                    M
POST         /api/v3/consultants/me/senders/{sender_id}/remove                              CONSULTANT+USER                    M
POST         /api/v3/consultants/me/senders/{sender_id}/verify                              CONSULTANT+USER                    M
GET          /api/v3/consultants/me/tasks                                                   CONSULTANT+USER                    R
POST         /api/v3/consultants/me/tasks                                                   CONSULTANT+USER                    M
GET          /api/v3/consultants/me/team                                                    CONSULTANT+USER                    R
POST         /api/v3/consultants/me/team                                                    CONSULTANT+USER                    M
PATCH        /api/v3/consultants/me/team/{member_id}/capabilities                           CONSULTANT+USER                    M
POST         /api/v3/consultants/me/team/{member_id}/deactivate                             CONSULTANT+USER                    M
POST         /api/v3/consultants/me/team/{member_id}/reactivate                             CONSULTANT+USER                    M
PUT          /api/v3/consultants/tasks/{task_id}/status                                     CONSULTANT+USER                    M
GET          /api/v3/customer-factors                                                       ORG_MEMBER+USER                    R
POST         /api/v3/customer-factors                                                       ORG_MEMBER+USER                    M
GET          /api/v3/customer-factors/{factor_id}                                           ORG_MEMBER+USER                    R
PUT          /api/v3/customer-factors/{factor_id}                                           ORG_MEMBER+USER                    M
POST         /api/v3/customer-factors/{factor_id}/approve                                   ORG_ADMIN+USER                     M
POST         /api/v3/customer-factors/{factor_id}/deactivate                                ORG_ADMIN+USER                     M
POST         /api/v3/discovery/lookup                                                       AUTH_ONLY+USER                     M
GET          /api/v3/discovery/requests                                                     ORG_MEMBER+USER                    R
POST         /api/v3/discovery/requests                                                     AUTH_ONLY+USER                     M
GET          /api/v3/discovery/requests/{request_id}                                        AUTH_ONLY+USER                     R
POST         /api/v3/discovery/requests/{request_id}/choice                                 AUTH_ONLY+USER                     M
POST         /api/v3/discovery/requests/{request_id}/staff-verify                           ADMIN+USER                         M
POST         /api/v3/discovery/requests/{request_id}/verify                                 AUTH_ONLY+USER                     M
GET          /api/v3/documents                                                              ORG_MEMBER+USER                    R
POST         /api/v3/documents/upload-url                                                   ORG_MEMBER+USER                    M
POST         /api/v3/documents/{document_id}/upload-abandon                                 ORG_MEMBER+USER                    M
POST         /api/v3/documents/{document_id}/upload-complete                                ORG_MEMBER+USER                    M
GET          /api/v3/documents/{file_id}                                                    ORG_MEMBER+USER                    R
GET          /api/v3/documents/{file_id}/emissions                                          ORG_MEMBER+USER                    R
GET          /api/v3/documents/{file_id}/signed-url                                         ORG_MEMBER+USER                    R
POST         /api/v3/emissions/calculate                                                    ORG_MEMBER+USER                    M
GET          /api/v3/emissions/calculations                                                 ORG_MEMBER+USER                    R
GET          /api/v3/emissions/calculations/{snapshot_id}                                   ORG_MEMBER+USER                    R
POST         /api/v3/emissions/calculations/{snapshot_id}/invalidate                        STAFF+STAFF_LEGACY+AUTH_ONLY+USER  M
POST         /api/v3/emissions/calculations/{snapshot_id}/verify                            ORG_MEMBER+USER                    M
GET          /api/v3/emissions/dashboard                                                    ORG_MEMBER+USER                    R
GET          /api/v3/emissions/factors                                                      ORG_MEMBER+USER                    R
GET          /api/v3/emissions/factors/{factor_id}                                          ORG_MEMBER+USER                    R
GET          /api/v3/emissions/scope-breakdown                                              ORG_MEMBER+USER                    R
GET          /api/v3/emissions/{log_id}/evidence                                            ORG_MEMBER+USER                    R
GET          /api/v3/evidence/line-items/{line_item_id}                                     ORG_MEMBER+USER                    R
GET          /api/v3/exports/audit-package.json                                             USER                               R
GET          /api/v3/exports/documents.csv                                                  ORG_MEMBER+USER                    R
GET          /api/v3/exports/emissions.csv                                                  ORG_MEMBER+USER                    R
GET          /api/v3/exports/emissions.json                                                 ORG_MEMBER+USER                    R
GET          /api/v3/health/realtime                                                        NONE                               R
GET          /api/v3/insight/conversations                                                  INSIGHT+USER                       R
POST         /api/v3/insight/conversations                                                  INSIGHT+USER                       M
GET          /api/v3/insight/conversations/{conversation_id}                                INSIGHT+USER                       R
GET          /api/v3/insight/conversations/{conversation_id}/messages                       INSIGHT+USER                       R
POST         /api/v3/insight/conversations/{conversation_id}/messages                       INSIGHT+USER                       M
GET          /api/v3/insight/interactions                                                   INSIGHT+USER                       R
POST         /api/v3/insight/interactions                                                   INSIGHT+USER                       M
GET          /api/v3/insight/interactions/{interaction_id}                                  INSIGHT+USER                       R
GET          /api/v3/insight/tools                                                          INSIGHT+USER                       R
POST         /api/v3/insight/tools/intent                                                   INSIGHT+USER                       M
POST         /api/v3/insight/tools/invoke                                                   INSIGHT+USER                       M
GET          /api/v3/issues                                                                 ORG_MEMBER+USER                    R
POST         /api/v3/issues                                                                 ORG_MEMBER+USER                    M
GET          /api/v3/issues/admin/entity/{entity_id}                                        USER                               R
GET          /api/v3/issues/admin/open                                                      ADMIN+USER                         R
GET          /api/v3/issues/{issue_id}                                                      ORG_MEMBER+USER                    R
PUT          /api/v3/issues/{issue_id}                                                      ORG_MEMBER+USER                    M
GET          /api/v3/manual-extraction/batches                                              ORG_MEMBER+USER                    R
POST         /api/v3/manual-extraction/batches                                              ORG_ADMIN+USER                     M
GET          /api/v3/manual-extraction/batches/{batch_id}                                   ORG_MEMBER+USER                    R
GET          /api/v3/manual-extraction/batches/{batch_id}/items                             ORG_MEMBER+USER                    R
POST         /api/v3/manual-extraction/batches/{batch_id}/items                             ORG_ADMIN+USER                     M
PUT          /api/v3/manual-extraction/items/{item_id}                                      ORG_MEMBER+USER                    M
GET          /api/v3/me/context                                                             USER                               R
GET          /api/v3/messaging/conversations                                                USER                               R
POST         /api/v3/messaging/conversations                                                USER                               M
GET          /api/v3/messaging/conversations/{conversation_id}/messages                     USER                               R
POST         /api/v3/messaging/conversations/{conversation_id}/messages                     USER                               M
POST         /api/v3/messaging/conversations/{conversation_id}/read                         USER                               M
GET          /api/v3/messaging/entity-conversations                                         USER                               R
POST         /api/v3/messaging/entity-conversations                                         USER                               M
GET          /api/v3/messaging/entity-conversations/{conversation_id}/messages              USER                               R
POST         /api/v3/messaging/entity-conversations/{conversation_id}/messages              USER                               M
POST         /api/v3/messaging/entity-conversations/{conversation_id}/read                  USER                               M
GET          /api/v3/notifications                                                          AUTH_ONLY+USER                     R
POST         /api/v3/notifications/read-all                                                 AUTH_ONLY+USER                     M
POST         /api/v3/notifications/{notification_id}/read                                   AUTH_ONLY+USER                     M
GET          /api/v3/ops/api-runtime-metrics                                                STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/batches/{batch_id}/assign                                          STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/batches/{batch_id}/items                                           STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/dashboard                                                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities                                                           STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/audit-activity                                STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/dashboard                                     STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/extraction/batches                            STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/extraction/batches/{batch_id}                 STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/extraction/batches/{batch_id}/items           STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}                    STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/calculate          STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/clarify            STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/extract            STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/map                STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/mapping-options    STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/start              STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/status             STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/entities/{entity_id}/extraction/next-item                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/entities/{entity_id}/performance                                   STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/items/{item_id}/calculate                                          STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/extract                                            STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/map                                                STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/items/{item_id}/mapping-options                                    STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/items/{item_id}/qc                                                 STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/start                                              STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/submit-review                                      STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/validate                                           STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/items/{item_id}/work                                               STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/items/{item_id}/work/assign                                        STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/work/claim                                         STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/work/complete                                      STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/work/reassign                                      STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/work/recover                                       STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/items/{item_id}/work/release                                       STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/items/{item_id}/workspace                                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/me                                                                 STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/next-item                                                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/operational-health/queue                                           STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/operational-health/worker                                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/operational-intelligence                                           STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/organizations                                                      STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/qc/ct-queue                                                        STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/qc/items/{item_id}/decision                                        STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/queues/operator                                                    STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/queues/qc                                                          STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/queues/review                                                      STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/reporting/aging                                                    STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/reporting/audit                                                    STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/reporting/platform                                                 STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/reporting/qc                                                       STAFF+STAFF_LEGACY+USER            R
GET          /api/v3/ops/reporting/review                                                   STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/review/{review_id}/assign                                          STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/ops/review/{review_id}/complete                                        STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/sla/settings                                                       STAFF+STAFF_LEGACY+USER            R
PUT          /api/v3/ops/sla/settings                                                       STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/staff                                                              STAFF+STAFF_LEGACY+USER            R
POST         /api/v3/ops/staff                                                              STAFF+STAFF_LEGACY+USER            M
GET          /api/v3/ops/staff-roles                                                        STAFF+STAFF_LEGACY+USER            R
PUT          /api/v3/ops/staff/{profile_id}                                                 STAFF+STAFF_LEGACY+USER            M
POST         /api/v3/organizations                                                          AUTH_ONLY+USER                     M
DELETE       /api/v3/organizations/assets/{asset_id}                                        CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/organizations/assets/{asset_id}                                        ORG_MEMBER+USER                    R
PUT          /api/v3/organizations/assets/{asset_id}                                        CLIENT_OP_GUARD+ORG_ADMIN+USER     M
DELETE       /api/v3/organizations/facilities/{facility_id}                                 CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/organizations/facilities/{facility_id}                                 ORG_MEMBER+USER                    R
PUT          /api/v3/organizations/facilities/{facility_id}                                 CLIENT_OP_GUARD+ORG_ADMIN+USER     M
POST         /api/v3/organizations/invitations/accept                                       AUTH_ONLY+USER                     M
DELETE       /api/v3/organizations/invitations/{invitation_id}                              ORG_ADMIN+USER                     M
DELETE       /api/v3/organizations/members/{member_id}                                      ORG_ADMIN+USER                     M
GET          /api/v3/organizations/members/{member_id}                                      ORG_MEMBER+USER                    R
PUT          /api/v3/organizations/members/{member_id}                                      ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}                                                 ORG_MEMBER+USER                    R
GET          /api/v3/organizations/{org_id}/assets                                          ORG_MEMBER+USER                    R
POST         /api/v3/organizations/{org_id}/assets                                          CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/organizations/{org_id}/consultant-engagements                          ORG_ADMIN+USER                     R
POST         /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept   ORG_ADMIN+USER                     M
POST         /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/reject   ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}/facilities                                      ORG_MEMBER+USER                    R
POST         /api/v3/organizations/{org_id}/facilities                                      CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/organizations/{org_id}/invitations                                     ORG_ADMIN+USER                     R
POST         /api/v3/organizations/{org_id}/invitations                                     ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}/members                                         ORG_MEMBER+USER                    R
POST         /api/v3/organizations/{org_id}/members                                         ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}/metadata                                        ORG_MEMBER+USER                    R
PUT          /api/v3/organizations/{org_id}/metadata                                        ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}/profile                                         ORG_MEMBER+USER                    R
PUT          /api/v3/organizations/{org_id}/profile                                         ORG_ADMIN+USER                     M
GET          /api/v3/organizations/{org_id}/roles                                           ORG_MEMBER+USER                    R
GET          /api/v3/organizations/{organization_id}/applicability                          ORG_MEMBER+USER                    R
POST         /api/v3/organizations/{organization_id}/applicability                          ORG_MEMBER+USER                    M
GET          /api/v3/organizations/{organization_id}/manual-processing                      ORG_MEMBER+USER                    R
GET          /api/v3/pe/batches/{batch_id}/items                                            PE_CAP+PE_MEMBER+USER              R
GET          /api/v3/pe/issues                                                              PE_CAP+PE_MEMBER+USER              R
GET          /api/v3/pe/issues/{issue_id}                                                   PE_CAP+PE_MEMBER+USER              R
POST         /api/v3/pe/items/{item_id}/calculate                                           PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/clarify                                             PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/extract                                             PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/map                                                 PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/pe-qc                                               PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/pe-review                                           PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/start                                               PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/status                                              PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/validate                                            PE_CAP+PE_MEMBER+USER              M
GET          /api/v3/pe/items/{item_id}/work                                                PE_CAP+PE_MEMBER+USER              R
POST         /api/v3/pe/items/{item_id}/work/claim                                          PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/work/complete                                       PE_CAP+PE_MEMBER+USER              M
POST         /api/v3/pe/items/{item_id}/work/release                                        PE_CAP+PE_MEMBER+USER              M
GET          /api/v3/pe/items/{item_id}/workspace                                           PE_CAP+PE_MEMBER+USER              R
GET          /api/v3/pe/me                                                                  PE_MEMBER+USER                     R
GET          /api/v3/pe/team                                                                PE_CAP+PE_MEMBER+USER              R
GET          /api/v3/pe/work                                                                PE_CAP+PE_MEMBER+USER              R
POST         /api/v3/portal/{client_id}/annotations                                         CLIENT_PORTAL+USER                 M
GET          /api/v3/portal/{client_id}/context                                             CLIENT_PORTAL+USER                 R
GET          /api/v3/portal/{client_id}/organization                                        CLIENT_PORTAL+USER                 R
POST         /api/v3/portal/{client_id}/relationship-requests                               CLIENT_PORTAL+USER                 M
GET          /api/v3/processing-entities                                                    ADMIN+USER                         R
POST         /api/v3/processing-entities                                                    ADMIN+USER                         M
GET          /api/v3/processing-entities/{entity_id}                                        ADMIN+USER                         R
PUT          /api/v3/processing-entities/{entity_id}                                        ADMIN+USER                         M
POST         /api/v3/processing/batches/{batch_id}/cancel                                   ORG_ADMIN+USER                     M
POST         /api/v3/processing/batches/{batch_id}/complete                                 ORG_ADMIN+USER                     M
GET          /api/v3/processing/batches/{batch_id}/progress                                 AUTH_ONLY+USER                     R
POST         /api/v3/processing/batches/{batch_id}/start                                    ORG_ADMIN+USER                     M
GET          /api/v3/processing/customer-review                                             AUTH_ONLY+USER                     R
GET          /api/v3/processing/dashboard                                                   AUTH_ONLY+USER                     R
POST         /api/v3/processing/documents/{file_id}/enqueue                                 AUTH_ONLY+USER                     M
GET          /api/v3/processing/issues                                                      AUTH_ONLY+USER                     R
POST         /api/v3/processing/items/{item_id}/calculate                                   AUTH_ONLY+USER                     M
POST         /api/v3/processing/items/{item_id}/consultant-review                           AUTH_ONLY+USER                     M
POST         /api/v3/processing/items/{item_id}/consultant-submit                           AUTH_ONLY+USER                     M
POST         /api/v3/processing/items/{item_id}/customer-review                             USER                               M
POST         /api/v3/processing/items/{item_id}/extract                                     AUTH_ONLY+USER                     M
POST         /api/v3/processing/items/{item_id}/map                                         AUTH_ONLY+USER                     M
GET          /api/v3/processing/items/{item_id}/mapping-options                             AUTH_ONLY+USER                     R
POST         /api/v3/processing/items/{item_id}/start                                       AUTH_ONLY+USER                     M
POST         /api/v3/processing/items/{item_id}/validate                                    AUTH_ONLY+USER                     M
GET          /api/v3/processing/items/{item_id}/workspace                                   AUTH_ONLY+USER                     R
GET          /api/v3/processing/jobs                                                        AUTH_ONLY+USER                     R
GET          /api/v3/processing/jobs/{job_id}                                               AUTH_ONLY+USER                     R
POST         /api/v3/processing/jobs/{job_id}/confirm                                       AUTH_ONLY+USER                     M
POST         /api/v3/processing/jobs/{job_id}/retry                                         AUTH_ONLY+USER                     M
POST         /api/v3/processing/jobs/{job_id}/review                                        ORG_ADMIN+USER                     M
GET          /api/v3/processing/next-item                                                   AUTH_ONLY+USER                     R
GET          /api/v3/processing/queue                                                       AUTH_ONLY+USER                     R
GET          /api/v3/processing/status                                                      AUTH_ONLY+USER                     R
POST         /api/v3/qc/items/{item_id}/review                                              ADMIN+USER                         M
GET          /api/v3/qc/queue                                                               ADMIN+USER                         R
GET          /api/v3/qc/stats                                                               ADMIN+USER                         R
GET          /api/v3/reporting/audit-activity                                               USER                               R
GET          /api/v3/reporting/audit-readiness                                              USER                               R
GET          /api/v3/reporting/consultant-client/{client_id}                                CONSULTANT+USER                    R
GET          /api/v3/reporting/consultant-client/{client_id}/audit-activity                 USER                               R
GET          /api/v3/reporting/consultant-portfolio                                         CONSULTANT+USER                    R
GET          /api/v3/reporting/customer-dashboard                                           ORG_MEMBER+USER                    R
GET          /api/v3/reporting/emissions-trend                                              ORG_MEMBER+USER                    R
GET          /api/v3/reporting/member-activity                                              ORG_MEMBER+USER                    R
GET          /api/v3/reports                                                                ORG_MEMBER+USER                    R
POST         /api/v3/reports                                                                ORG_MEMBER+USER                    M
GET          /api/v3/reports/schedules                                                      ORG_MEMBER+USER                    R
POST         /api/v3/reports/schedules                                                      ORG_MEMBER+USER                    M
GET          /api/v3/reports/schedules/frequencies                                          ORG_MEMBER+USER                    R
DELETE       /api/v3/reports/schedules/{schedule_id}                                        ORG_MEMBER+USER                    M
GET          /api/v3/reports/schedules/{schedule_id}                                        ORG_MEMBER+USER                    R
POST         /api/v3/reports/schedules/{schedule_id}/pause                                  ORG_MEMBER+USER                    M
POST         /api/v3/reports/schedules/{schedule_id}/resume                                 ORG_MEMBER+USER                    M
GET          /api/v3/reports/schedules/{schedule_id}/runs                                   ORG_MEMBER+USER                    R
GET          /api/v3/reports/shares/received                                                ORG_MEMBER+USER                    R
GET          /api/v3/reports/shares/{share_id}/access-history                               ORG_MEMBER+USER                    R
POST         /api/v3/reports/shares/{share_id}/revoke                                       ORG_MEMBER+USER                    M
GET          /api/v3/reports/types                                                          ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}                                                    ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/approve                                            ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/content                                            ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}/disclosure                                         ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}/disclosure/narrative                               ORG_MEMBER+USER                    R
PUT          /api/v3/reports/{report_id}/disclosure/narrative/{requirement_version_id}      ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/disclosure/project                                 ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/disclosure/{value_id}/lines                        ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}/download                                           ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}/finalisation-check                                 ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/finalise                                           ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/frozen-artefact                                    ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/frozen-artefact/signed-url                         ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/intensity                                          ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/intensity                                          ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/pdf                                                ORG_MEMBER+USER                    R
GET          /api/v3/reports/{report_id}/shares                                             ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/shares                                             ORG_MEMBER+USER                    M
GET          /api/v3/reports/{report_id}/versions                                           ORG_MEMBER+USER                    R
POST         /api/v3/reports/{report_id}/versions                                           ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/versions/{version_number}/approve                  ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/versions/{version_number}/finalize                 ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/versions/{version_number}/reject                   ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/versions/{version_number}/request-changes          ORG_MEMBER+USER                    M
POST         /api/v3/reports/{report_id}/versions/{version_number}/submit                   ORG_MEMBER+USER                    M
POST         /api/v3/scope2/calculate                                                       ORG_MEMBER+USER                    M
POST         /api/v3/scope3/calculate                                                       ORG_MEMBER+USER                    M
GET          /api/v3/search                                                                 ORG_MEMBER+USER                    R
GET          /api/v3/settings/analytics                                                     NONE                               R
PUT          /api/v3/settings/analytics                                                     ADMIN+USER                         M
GET          /api/v3/settings/email-provider                                                ADMIN+USER                         R
PUT          /api/v3/settings/email-provider                                                ADMIN+USER                         M
POST         /api/v3/settings/email-provider/validate                                       ADMIN+USER                         M
GET          /api/v3/settings/notification-sender                                           ADMIN+USER                         R
PUT          /api/v3/settings/notification-sender                                           ADMIN+USER                         M
GET          /api/v3/settings/retention                                                     ADMIN+USER                         R
PUT          /api/v3/settings/retention                                                     ADMIN+USER                         M
GET          /api/v3/settings/upload-policy                                                 ADMIN+USER                         R
PUT          /api/v3/settings/upload-policy                                                 ADMIN+USER                         M
GET          /api/v3/suppliers                                                              ORG_MEMBER+USER                    R
POST         /api/v3/suppliers                                                              ORG_ADMIN+USER                     M
DELETE       /api/v3/suppliers/{supplier_id}                                                ORG_ADMIN+USER                     M
GET          /api/v3/suppliers/{supplier_id}                                                ORG_MEMBER+USER                    R
PUT          /api/v3/suppliers/{supplier_id}                                                ORG_ADMIN+USER                     M
POST         /api/v3/uploads                                                                ORG_MEMBER+USER                    M
POST         /api/v3/uploads/{file_id}/ocr                                                  ORG_MEMBER+USER                    M
GET          /api/v3/vehicles                                                               ORG_MEMBER+USER                    R
POST         /api/v3/vehicles                                                               CLIENT_OP_GUARD+ORG_ADMIN+USER     M
DELETE       /api/v3/vehicles/{vehicle_id}                                                  CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/vehicles/{vehicle_id}                                                  ORG_MEMBER+USER                    R
PUT          /api/v3/vehicles/{vehicle_id}                                                  CLIENT_OP_GUARD+ORG_ADMIN+USER     M
GET          /api/v3/verifications/pending                                                  ORG_MEMBER+USER                    R
POST         /api/v3/verifications/{document_id}/approve                                    ORG_MEMBER+USER                    M
POST         /api/v3/verifications/{document_id}/correct                                    ORG_MEMBER+USER                    M
POST         /api/v3/verifications/{document_id}/reject                                     ORG_MEMBER+USER                    M
GET          /api/verification-pending                                                      ORG_MEMBER+USER                    R
GET          /api/waitlist/                                                                 ADMIN+USER                         R
POST         /api/waitlist/                                                                 NONE                               M
GET          /api/{org_id}/emissions                                                        ORG_MEMBER+USER                    R
GET          /api/{record_id}/verification-history                                          ORG_MEMBER+USER                    R
GET          /docs                                                                          NONE                               R
GET          /docs/oauth2-redirect                                                          NONE                               R
GET          /health                                                                        NONE                               R
GET          /openapi.json                                                                  NONE                               R
GET          /redoc                                                                         NONE                               R
```

---

# APPENDIX B — FRONTEND API CLIENT INVENTORY (`frontend/src/v3/api.js`)

352 exported callables; 330 carry a literal path; 22 construct their path
dynamically (listed as `(no literal path)`). Method is the nearest `method:`
literal inside the same export block (§11.1 L-03).

```text
GET     (no literal path)                                                      <= REPORT_LIFECYCLE_ACTION_CALLS
POST    /api/v3/organizations/invitations/accept                               <= acceptInvitation
POST    /api/v3/consultants/me/custom-domains/${domainId}/activate             <= activateCustomDomain
POST    /api/v3/commercial/subscriptions                                       <= activateSubscription
POST    /api/v3/consultants/me/team                                            <= addConsultantTeamMember
POST    /api/v3/organizations/${organizationId}/members                        <= addMember
POST    /api/v3/commercial/credits/adjust                                      <= adminAdjustCredits
POST    /api/v3/commercial/credits/grant                                       <= adminGrantCredits
POST    /api/v3/commercial/credits/refund                                      <= adminRefundCredits
POST    /api/v3/commercial/credits/reverse                                     <= adminReverseCredits
POST    /api/v3/commercial/credits/rollover                                    <= adminRolloverCredits
POST    /api/v3/admin/manual-processing/coverage/allocations                   <= allocateAdminManualProcessingClient
POST    /api/v3/consultants/me/manual-processing/allocations                   <= allocateConsultantManualProcessingClient
POST    /api/v3/billing/orders/${encodeURIComponent(orderId)}/approve          <= approveBillingOrder
POST    /api/v3/customer-factors/${encodeURIComponent(factorId)}/approve       <= approveCustomerFactor
POST    /api/v3/reports/${reportId}/versions/${versionNumber}/approve          <= approveReportVersion
POST    /api/v3/ops/batches/${batchId}/assign                                  <= assignBatch
POST    /api/v3/ops/review/${reviewId}/assign                                  <= assignReview
GET     (no literal path)                                                      <= auditPackageUrl
POST    /api/v3/ops/items/${itemId}/calculate                                  <= calculateItem
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/calculate       <= calculateProcessingItem
POST    /api/v3/billing/orders/${encodeURIComponent(orderId)}/cancel           <= cancelBillingOrder
POST    /api/v3/commercial/subscriptions/${encodeURIComponent(subscriptionId)}/status <= changeSubscriptionStatus
POST    /api/v3/discovery/requests/${requestId}/choice                         <= chooseDiscoveryAdoption
POST    /api/v3/discovery/requests/${requestId}/choice                         <= chooseOnboardingAdoption
POST    /api/v3/commercial/orders/${encodeURIComponent(orderId)}/complete      <= completeAdminOrder
POST    /api/v3/ops/review/${reviewId}/complete                                <= completeReview
POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/confirm           <= confirmProcessingJob
POST    /api/v3/processing/items/${itemId}/consultant-review                   <= consultantReviewItem
POST    /api/v3/processing/items/${itemId}/consultant-submit                   <= consultantSubmitItem
POST    /api/v3/organizations/${organizationId}/assets                         <= createAsset
POST    /api/v3/billing/orders/assisted                                        <= createAssistedEstimate
POST    /api/v3/admin/backups                                                  <= createBackup
POST    /api/v3/consultants/clients/${clientId}/invitations                    <= createClientInvitation
POST    /api/v3/commercial/plans                                               <= createCommercialPlan
POST    /api/v3/consultants/me/customers                                       <= createConsultantCustomer
POST    /api/v3/consultants/me/tasks                                           <= createConsultantTask
POST    /api/v3/consultants/me/custom-domains                                  <= createCustomDomain
POST    /api/v3/consultants/me/senders                                         <= createCustomSender
POST    /api/v3/customer-factors                                               <= createCustomerFactor
POST    /api/v3/issues                                                         <= createCustomerIssue
POST    /api/v3/discovery/requests                                             <= createDiscoveryRequest
POST    /api/v3/messaging/entity-conversations                                 <= createEntityConversation
POST    /api/v3/organizations/${organizationId}/facilities                     <= createFacility
POST    /api/v3/insight/conversations                                          <= createInsightConversation
POST    /api/v3/organizations/${organizationId}/invitations                    <= createInvitation
POST    /api/v3/billing/managed/orders                                         <= createManagedOrder
POST    /api/v3/messaging/conversations                                        <= createMessagingConversation
POST    /api/v3/discovery/requests                                             <= createOnboardingDiscoveryRequest
POST    /api/v3/ops/staff                                                      <= createOpsStaff
POST    /api/v3/organizations                                                  <= createOrganization
POST    /api/v3/processing-entities                                            <= createProcessingEntity
POST    /api/v3/suppliers                                                      <= createSupplier
POST    /api/v3/vehicles                                                       <= createVehicle
POST    /api/v3/ops/qc/items/${itemId}/decision                                <= ctQcDecision
DELETE  /api/v3/consultants/clients/${clientId}                                <= deactivateConsultantClient
POST    /api/v3/consultants/me/team/${memberId}/deactivate                     <= deactivateConsultantTeamMember
POST    /api/v3/customer-factors/${encodeURIComponent(factorId)}/deactivate    <= deactivateCustomerFactor
DELETE  /api/v3/admin/manual-processing/grants/${encodeURIComponent(scopeType)}/${encodeURIComponent(scopeId)} <= deleteManualProcessingGrant
DELETE  /api/v3/admin/manual-processing/processors/${encodeURIComponent(scopeType)}/${encodeURIComponent(scopeId)} <= deleteManualProcessingProcessor
POST    /api/v3/discovery/lookup                                               <= discoveryLookup
GET     (no literal path)                                                      <= downloadBackupArtifact
GET     (no literal path)                                                      <= downloadExport
GET     (no literal path)                                                      <= downloadReport
GET     (no literal path)                                                      <= downloadReportPdf
POST    /api/v3/consultants/clients/${clientId}/end                            <= endConsultantClient
POST    /api/v3/processing/documents/${encodeURIComponent(fileId)}/enqueue     <= enqueueDocumentForProcessing
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/calculate  <= entityCalculateItem
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/clarify    <= entityClarifyItem
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/extract    <= entityExtractItem
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/map        <= entityMapItem
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/status     <= entitySetItemStatus
POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/start      <= entityStartItem
POST    /api/v3/pe/items/${itemId}/validate                                    <= entityValidateItem
GET     (no literal path)                                                      <= exportDocumentsUrl
GET     (no literal path)                                                      <= exportEmissionsUrl
POST    /api/v3/ops/items/${itemId}/extract                                    <= extractItem
POST    /api/v3/reports/${reportId}/versions/${versionNumber}/finalize         <= finalizeReportVersion
POST    /api/v3/reports                                                        <= generateReport
GET     (no literal path)                                                      <= getActiveConsultantClientId
GET     /api/v3/commercial/entitlement/${encodeURIComponent(organizationId)}   <= getAdminEntitlement
GET     /api/v3/admin/manual-processing/clients/${encodeURIComponent(organizationId)} <= getAdminManualProcessingClientState
GET     /api/v3/admin/manual-processing/coverage/${encodeURIComponent(consultantId)} <= getAdminManualProcessingCoverage
GET     /api/v3/settings/analytics                                             <= getAnalyticsSettings
GET     /api/v3/organizations/assets/${assetId}                                <= getAsset
GET     /api/v3/reporting/audit-activity?${query.toString()}                   <= getAuditActivity
GET     /api/v3/reporting/audit-readiness?organization_id=${encodeURIComponent(organizationId)} <= getAuditReadiness
GET     /api/v3/admin/backups/${encodeURIComponent(jobId)}                     <= getBackup
GET     /api/v3/admin/backups/${encodeURIComponent(jobId)}/pair                <= getBackupPair
GET     /api/v3/admin/backups/policy                                           <= getBackupPolicy
GET     /api/v3/admin/backups/status                                           <= getBackupStatus
GET     /api/v3/capabilities                                                   <= getCapabilityCatalogue
GET     /api/v3/consultants/clients/${clientId}/dashboard?${query.toString()}  <= getClientDashboard
GET     /api/v3/consultants/clients/${clientId}/documents                      <= getClientDocuments
GET     /api/v3/consultants/clients/${clientId}/evidence?limit=${limit}&offset=${offset} <= getClientEvidence
GET     /api/v3/consultants/clients/${clientId}/issues                         <= getClientIssues
GET     /api/v3/consultants/clients/${clientId}/processing/items${query}       <= getClientProcessingItems
GET     /api/v3/consultants/clients/${clientId}/processing/status              <= getClientProcessingStatus
GET     /api/v3/consultants/clients/${clientId}/reports                        <= getClientReports
GET     /api/v3/consultants/clients/${clientId}/context                        <= getClientWorkspaceContext
GET     /api/v3/commercial/config/${encodeURIComponent(configKey)}             <= getCommercialConfig
GET     /api/v3/commercial/overview                                            <= getCommercialOverview
GET     /api/v3/commercial/plans/${encodeURIComponent(planCode)}               <= getCommercialPlan
GET     /api/v3/consultants/me/branding                                        <= getConsultantBranding
GET     /api/v3/consultants/me/branding/context                                <= getConsultantBrandingContext
GET     /api/v3/consultants/clients/${clientId}                                <= getConsultantClient
GET     /api/v3/reporting/consultant-client/${encodeURIComponent(clientId)}/audit-activity <= getConsultantClientAuditActivity
GET     /api/v3/reporting/consultant-client/${clientId}                        <= getConsultantClientDetail
GET     /api/v3/consultants/me/dashboard                                       <= getConsultantDashboard
GET     /api/v3/processing/items/${itemId}/workspace                           <= getConsultantItemWorkspace
GET     /api/v3/consultants/me/manual-processing/coverage                      <= getConsultantManualProcessingCoverage
GET     /api/v3/reporting/consultant-portfolio                                 <= getConsultantPortfolio
GET     /api/v3/consultants/me                                                 <= getConsultantProfile
GET     /api/v3/consultants/me/tasks${query}                                   <= getConsultantTasks
GET     /api/v3/consultants/me/team                                            <= getConsultantTeam
GET     /api/v3/commercial/ledger?organization_id=${encodeURIComponent(organizationId)} <= getCreditLedger
GET     /api/v3/ops/qc/ct-queue                                                <= getCtQcQueue
GET     /api/v3/reporting/customer-dashboard?${query.toString()}               <= getCustomerDashboardReport
GET     /api/v3/customer-factors/${encodeURIComponent(factorId)}               <= getCustomerFactor
GET     /api/v3/issues/${issueId}                                              <= getCustomerIssue
GET     /api/v3/processing/customer-review?organization_id=${encodeURIComponent(organizationId)} <= getCustomerReviewQueue
GET     /api/v3/discovery/requests/${requestId}?organization_id=${encodeURIComponent(organizationId)} <= getDiscoveryRequest
GET     /api/v3/documents/${fileId}/emissions                                  <= getDocumentEmissions
GET     /api/v3/settings/email-provider                                        <= getEmailProviderSettings
GET     /api/v3/emissions/${logId}/evidence                                    <= getEmissionEvidence
GET     /api/v3/reporting/emissions-trend?organization_id=${organizationId}&months=${months} <= getEmissionsTrend
GET     /api/v3/ops/entities/${entityId}/dashboard                             <= getEntityDashboard
GET     /api/v3/ops/entities/${entityId}/extraction/batches/${batchId}         <= getEntityExtractionBatch
GET     /api/v3/ops/entities/${entityId}/extraction/batches/${batchId}/items   <= getEntityExtractionBatchItems
GET     /api/v3/ops/entities/${entityId}/extraction/batches${query}            <= getEntityExtractionBatches
GET     /api/v3/ops/entities/${entityId}/extraction/items/${itemId}            <= getEntityExtractionItem
GET     /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/mapping-options${qs ?  <= getEntityMappingOptions
GET     /api/v3/ops/entities/${entityId}/extraction/next-item?${query}         <= getEntityNextItem
GET     /api/v3/ops/entities/${entityId}/performance                           <= getEntityPerformance
GET     /api/v3/evidence/line-items/${encodeURIComponent(lineItemId)}          <= getEvidenceLine
GET     /api/v3/organizations/facilities/${facilityId}                         <= getFacility
GET     /api/v3/insight/interactions/${encodeURIComponent(interactionId)}?     <= getInsightInteraction
GET     /api/v3/ops/items/${itemId}/workspace                                  <= getItemWorkspace
GET     /api/v3/admin/manual-processing/grants${qs}                            <= getManualProcessingGrants
GET     /api/v3/admin/manual-processing/processors${qs}                        <= getManualProcessingProcessors
GET     /api/v3/admin/manual-processing/state?scope_type=${encodeURIComponent(scopeType)}&scope_id=${encodeURIComponent(scopeId)} <= getManualProcessingState
GET     /api/v3/ops/items/${itemId}/mapping-options${qs ?                      <= getMappingOptions
GET     /api/v3/me/context                                                     <= getMeContext
GET     /api/v3/organizations/members/${memberId}                              <= getMember
GET     /api/v3/reporting/member-activity?organization_id=${organizationId}    <= getMemberActivity
GET     /api/v3/billing/me                                                     <= getMyBilling
GET     /api/v3/billing/me/credits                                             <= getMyCreditHistory
GET     /api/v3/organizations/${encodeURIComponent(organizationId)}/manual-processing <= getMyManualProcessing
GET     /api/v3/billing/me/orders/${encodeURIComponent(orderId)}               <= getMyOrder
GET     /api/v3/ops/next-item?stage=${encodeURIComponent(stage)}               <= getNextItem
GET     /api/v3/settings/notification-sender                                   <= getNotificationSenderSettings
GET     /api/v3/discovery/requests/${requestId}                                <= getOnboardingDiscoveryRequest
GET     /api/v3/ops/operational-health/queue                                   <= getOperationalHealthQueue
GET     /api/v3/ops/operational-health/worker                                  <= getOperationalHealthWorker
GET     /api/v3/ops/operational-intelligence                                   <= getOperationalIntelligence
GET     /api/v3/ops/queues/operator?${query.toString()}                        <= getOperatorQueue
GET     /api/v3/ops/reporting/audit${query.toString() ?                        <= getOpsAudit
GET     /api/v3/ops/batches/${batchId}/items                                   <= getOpsBatchItems
GET     /api/v3/ops/dashboard                                                  <= getOpsDashboard
GET     /api/v3/ops/me                                                         <= getOpsMe
GET     /api/v3/ops/organizations${qs ?                                        <= getOpsOrganizations
GET     /api/v3/ops/reporting/platform                                         <= getOpsPlatformReporting
GET     /api/v3/ops/reporting/qc                                               <= getOpsQcReporting
GET     /api/v3/ops/reporting/aging                                            <= getOpsQueueAging
GET     /api/v3/ops/reporting/review                                           <= getOpsReviewReporting
GET     /api/v3/organizations/${organizationId}/metadata                       <= getOrganizationMetadata
GET     /api/v3/organizations/${organizationId}/profile                        <= getOrganizationProfile
GET     /api/v3/pe/batches/${batchId}/items                                    <= getPeBatchItems
GET     /api/v3/pe/me                                                          <= getPeMe
GET     /api/v3/pe/work${status ?                                              <= getPeWork
GET     /api/v3/portal/${clientId}/context                                     <= getPortalContext
GET     /api/v3/portal/${clientId}/organization                                <= getPortalOrganization
GET     /api/v3/processing/issues?${query.toString()}                          <= getProcessingIssues
GET     /api/v3/processing/items/${encodeURIComponent(itemId)}/workspace       <= getProcessingItemWorkspace
GET     /api/v3/processing/jobs/${encodeURIComponent(jobId)}                   <= getProcessingJob
GET     /api/v3/processing/jobs?${query.toString()}                            <= getProcessingJobs
GET     /api/v3/processing/items/${encodeURIComponent(itemId)}/mapping-options <= getProcessingMappingOptions
GET     /api/v3/processing/next-item?organization_id=${encodeURIComponent(organizationId)}&stage=${encodeURIComponent(stage)} <= getProcessingNextItem
GET     /api/v3/processing/queue?organization_id=${encodeURIComponent(organizationId)}&stage=${encodeURIComponent(stage)}&limit=${limit} <= getProcessingQueue
GET     /api/v3/processing/status?organization_id=${encodeURIComponent(organizationId)} <= getProcessingStatus
GET     /api/v3/ops/queues/qc?limit=${limit}&offset=${offset}                  <= getQcQueue
GET     /api/v3/qc/queue                                                       <= getQcQueueAdmin
GET     /api/v3/qc/stats                                                       <= getQcStats
GET     /api/v3/reports/${reportId}                                            <= getReport
GET     /api/v3/reports/${reportId}/content                                    <= getReportContent
GET     /api/v3/reports/types                                                  <= getReportTypes
GET     /api/v3/reports/${reportId}/versions                                   <= getReportVersions
GET     /api/v3/settings/retention                                             <= getRetentionSettings
GET     /api/v3/ops/queues/review?${query.toString()}                          <= getReviewQueue
GET     /api/v3/ops/sla/settings                                               <= getSlaSettings
GET     /api/v3/suppliers/${supplierId}                                        <= getSupplier
GET     /api/v3/settings/upload-policy                                         <= getUploadPolicySettings
GET     (no literal path)                                                      <= getV3Token
GET     (no literal path)                                                      <= goToWorkspace
POST    /api/v3/insight/tools/invoke                                           <= invokeInsightTool
GET     /api/v3/commercial/orders${status ?                                    <= listAdminOrders
GET     /api/v3/commercial/payments                                            <= listAdminPayments
GET     /api/v3/commercial/storage                                             <= listAdminStorage
GET     /api/v3/organizations/${organizationId}/assets                         <= listAssets
GET     /api/v3/admin/backups?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)} <= listBackups
GET     /api/v3/consultants/clients/${clientId}/invitations                    <= listClientInvitations
GET     /api/v3/consultants/clients/${clientId}/users                          <= listClientUsers
GET     /api/v3/commercial/organizations${
      billingMode ?                 <= listCommercialOrganizations
GET     /api/v3/commercial/plans                                               <= listCommercialPlans
GET     /api/v3/consultants/me/clients                                         <= listConsultantClients
GET     /api/v3/consultants/me/custom-domains                                  <= listCustomDomains
GET     /api/v3/consultants/me/senders                                         <= listCustomSenders
GET     /api/v3/customer-factors?organization_id=${encodeURIComponent(organizationId)} <= listCustomerFactors
GET     /api/v3/issues?${query.toString()}                                     <= listCustomerIssues
GET     /api/v3/discovery/requests?organization_id=${encodeURIComponent(organizationId)} <= listDiscoveryRequests
GET     /api/v3/messaging/entity-conversations${qs}                            <= listEntityConversations
GET     /api/v3/issues/admin/entity/${encodeURIComponent(entityId)}            <= listEntityIssues
GET     /api/v3/messaging/entity-conversations/${conversationId}/messages      <= listEntityMessages
GET     /api/v3/organizations/${organizationId}/facilities                     <= listFacilities
GET     /api/v3/insight/conversations?${insightQuery({ organization_id: organizationId, limit, offset })} <= listInsightConversations
GET     /api/v3/insight/interactions?${insightQuery({
    organization_id: organizationId,
    conversation_id: conversationId,
    limit,
    offset,
  })} <= listInsightInteractions
GET     /api/v3/insight/conversations/${encodeURIComponent(conversationId)}/messages? <= listInsightMessages
GET     /api/v3/organizations/${organizationId}/invitations                    <= listInvitations
GET     /api/v3/organizations/${organizationId}/members                        <= listMembers
GET     /api/v3/messaging/conversations?organization_id=${encodeURIComponent(organizationId)} <= listMessagingConversations
GET     /api/v3/messaging/conversations/${conversationId}/messages             <= listMessagingMessages
GET     /api/v3/billing/me/orders                                              <= listMyOrders
GET     /api/v3/billing/me/payments                                            <= listMyPayments
GET     /api/v3/notifications${qs ?                                            <= listNotifications
GET     /api/v3/issues/admin/open${query}                                      <= listOpsOpenIssues
GET     /api/v3/ops/staff?limit=${limit}&offset=${offset}                      <= listOpsStaff
GET     /api/v3/organizations/${organizationId}/roles                          <= listOrgRoles
GET     /api/v3/ops/entities?${query.toString()}                               <= listProcessingEntities
GET     /api/v3/reports?${query.toString()}                                    <= listReports
GET     /api/v3/ops/staff                                                      <= listStaff
GET     /api/v3/ops/staff-roles                                                <= listStaffRoles
GET     /api/v3/commercial/subscriptions                                       <= listSubscriptions
GET     /api/v3/suppliers?${query.toString()}                                  <= listSuppliers
GET     /api/v3/vehicles?organization_id=${encodeURIComponent(organizationId)} <= listVehicles
POST    /api/v3/ops/items/${itemId}/map                                        <= mapItem
POST    /api/v3/notifications/read-all                                         <= markAllNotificationsRead
POST    /api/v3/messaging/entity-conversations/${conversationId}/read          <= markEntityConversationRead
POST    /api/v3/messaging/conversations/${conversationId}/read                 <= markMessagingConversationRead
POST    /api/v3/notifications/${notificationId}/read                           <= markNotificationRead
POST    /api/v3/discovery/lookup                                               <= onboardingDiscoveryLookup
POST    /api/v3/ops/items/${itemId}/work/assign                                <= opsWorkAssign
POST    /api/v3/ops/items/${itemId}/work/assign                                <= opsWorkAssignTarget
POST    /api/v3/ops/items/${itemId}/work/claim                                 <= opsWorkClaim
POST    /api/v3/ops/items/${itemId}/work/complete                              <= opsWorkComplete
GET     /api/v3/ops/items/${itemId}/work                                       <= opsWorkInfo
POST    /api/v3/ops/items/${itemId}/work/reassign                              <= opsWorkReassignTarget
POST    /api/v3/ops/items/${itemId}/work/release                               <= opsWorkRelease
POST    /api/v3/pe/items/${itemId}/pe-qc                                       <= peQcDecision
POST    /api/v3/pe/items/${itemId}/pe-review                                   <= peReviewDecision
POST    /api/v3/pe/items/${itemId}/work/claim                                  <= peWorkClaim
POST    /api/v3/pe/items/${itemId}/work/complete                               <= peWorkComplete
GET     /api/v3/pe/items/${itemId}/work                                        <= peWorkInfo
POST    /api/v3/pe/items/${itemId}/work/release                                <= peWorkRelease
POST    /api/v3/portal/${clientId}/annotations                                 <= postPortalAnnotation
GET     (no literal path)                                                      <= putBytesToSignedUrl
POST    /api/v3/ops/items/${itemId}/qc                                         <= qcReviewItem
POST    /api/v3/qc/items/${itemId}/review                                      <= qcReviewItemAdmin
POST    /api/v3/consultants/clients/${clientId}/reactivate                     <= reactivateConsultantClient
POST    /api/v3/consultants/me/team/${memberId}/reactivate                     <= reactivateConsultantTeamMember
GET     (no literal path)                                                      <= recordAbandonedUpload
POST    /api/v3/billing/me/storage/refresh                                     <= refreshMyStorage
POST    /api/v3/reports/${reportId}/versions/${versionNumber}/reject           <= rejectReportVersion
DELETE  /api/v3/admin/manual-processing/coverage/allocations/${encodeURIComponent(allocationId)} <= releaseAdminManualProcessingAllocation
DELETE  /api/v3/consultants/me/manual-processing/allocations/${encodeURIComponent(allocationId)} <= releaseConsultantManualProcessingAllocation
DELETE  /api/v3/organizations/assets/${assetId}                                <= removeAsset
POST    /api/v3/consultants/me/custom-domains/${domainId}/remove               <= removeCustomDomain
POST    /api/v3/consultants/me/senders/${senderId}/remove                      <= removeCustomSender
DELETE  /api/v3/organizations/facilities/${facilityId}                         <= removeFacility
DELETE  /api/v3/organizations/members/${memberId}                              <= removeMember
DELETE  /api/v3/suppliers/${supplierId}                                        <= removeSupplier
DELETE  /api/v3/vehicles/${encodeURIComponent(vehicleId)}                      <= removeVehicle
POST    /api/v3/reports/${reportId}/versions/${versionNumber}/request-changes  <= requestChangesReportVersion
POST    /api/v3/consultants/me/mode-change-requests                            <= requestConsultantModeChange
POST    /api/v3/portal/${clientId}/relationship-requests                       <= requestPortalRelationshipChange
GET     (no literal path)                                                      <= resolvePostLoginPath
GET     (no literal path)                                                      <= resolveV3Membership
GET     (no literal path)                                                      <= resolveV3Organization
POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/retry             <= retryProcessingJob
POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/review            <= reviewProcessingJob
POST    /api/v3/consultants/clients/${clientId}/invitations/${invitationId}/revoke <= revokeClientInvitation
DELETE  /api/v3/organizations/invitations/${invitationId}                      <= revokeInvitation
POST    /api/v3/insight/interactions                                           <= runInsightInteraction
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/extract         <= saveProcessingExtraction
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/map             <= saveProcessingMapping
GET     /api/v3/admin/manual-processing/organizations?${params.toString()}     <= searchAdminManualProcessingOrganizations
GET     /api/v3/search?organization_id=${encodeURIComponent(organizationId)}&q=${encodeURIComponent(q)}&limit=${limit} <= searchOrg
POST    /api/v3/messaging/entity-conversations/${conversationId}/messages      <= sendEntityMessage
POST    /api/v3/messaging/conversations/${conversationId}/messages             <= sendMessagingMessage
GET     (no literal path)                                                      <= setActiveConsultantClientId
POST    /api/v3/consultants/clients/${clientId}/access-profile                 <= setConsultantClientAccessProfile
POST    /api/v3/consultants/clients/${clientId}/retention                      <= setConsultantClientRetention
PUT     /api/v3/admin/manual-processing/grants                                 <= setManualProcessingGrant
PUT     /api/v3/admin/manual-processing/processors                             <= setManualProcessingProcessor
POST    /api/v3/ops/items/${itemId}/start                                      <= startItem
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/start           <= startProcessingItem
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/customer-review <= submitCustomerReview
POST    /api/v3/ops/items/${itemId}/submit-review                              <= submitInternalReview
POST    /api/v3/reports/${reportId}/versions/${versionNumber}/submit           <= submitReportVersion
POST    /api/v3/consultants/clients/${clientId}/suspend                        <= suspendConsultantClient
PUT     /api/v3/settings/analytics                                             <= updateAnalyticsSettings
PUT     /api/v3/organizations/assets/${assetId}                                <= updateAsset
PUT     /api/v3/admin/backups/policy                                           <= updateBackupPolicy
PATCH   /api/v3/consultants/clients/${clientId}/users/${memberId}              <= updateClientUser
PUT     /api/v3/commercial/config/${encodeURIComponent(configKey)}             <= updateCommercialConfig
PUT     /api/v3/commercial/plans/${encodeURIComponent(planCode)}               <= updateCommercialPlan
PUT     /api/v3/consultants/me/branding                                        <= updateConsultantBranding
PUT     /api/v3/consultants/clients/${clientId}                                <= updateConsultantClientStatus
PUT     /api/v3/consultants/tasks/${taskId}/status                             <= updateConsultantTaskStatus
PATCH   /api/v3/consultants/me/team/${memberId}/capabilities                   <= updateConsultantTeamMemberCapabilities
PUT     /api/v3/customer-factors/${encodeURIComponent(factorId)}               <= updateCustomerFactor
PUT     /api/v3/settings/email-provider                                        <= updateEmailProviderSettings
PUT     /api/v3/organizations/facilities/${facilityId}                         <= updateFacility
PUT     /api/v3/issues/${encodeURIComponent(issueId)}                          <= updateIssue
PUT     /api/v3/organizations/members/${memberId}                              <= updateMember
PUT     /api/v3/settings/notification-sender                                   <= updateNotificationSenderSettings
PUT     /api/v3/ops/staff/${profileId}                                         <= updateOpsStaff
PUT     /api/v3/organizations/${organizationId}/metadata                       <= updateOrganizationMetadata
PUT     /api/v3/organizations/${organizationId}/profile                        <= updateOrganizationProfile
PUT     /api/v3/settings/retention                                             <= updateRetentionSettings
PUT     /api/v3/ops/sla/settings                                               <= updateSlaSettings
PUT     /api/v3/suppliers/${supplierId}                                        <= updateSupplier
PUT     /api/v3/settings/upload-policy                                         <= updateUploadPolicySettings
PUT     /api/v3/vehicles/${encodeURIComponent(vehicleId)}                      <= updateVehicle
GET     (no literal path)                                                      <= uploadConsultantDocument
POST    /api/v3/consultants/clients/${encodeURIComponent(clientId)}/documents/ <= v3AbandonConsultantDirectUpload
POST    /api/v3/documents/${encodeURIComponent(documentId)}/upload-abandon     <= v3AbandonDirectUpload
POST    /api/v3/emissions/calculate                                            <= v3CalculateEmissions
POST    /api/v3/consultants/clients/${encodeURIComponent(clientId)}/documents/ <= v3CompleteConsultantDirectUpload
POST    /api/v3/documents/${encodeURIComponent(documentId)}/upload-complete    <= v3CompleteDirectUpload
POST    /api/v3/manual-extraction/batches?organization_id=${encodeURIComponent(organizationId)} <= v3CreateExtractionBatch
POST    /api/v3/manual-extraction/batches/${encodeURIComponent(batchId)}/items <= v3CreateExtractionItem
POST    /api/v3/batches?organization_id=${encodeURIComponent(organizationId)}  <= v3CreateUploadBatch
GET     (no literal path)                                                      <= v3Fetch
GET     /api/v3/documents?${query.toString()}                                  <= v3ListDocuments
GET     /api/v3/exports/emissions.json?${query.toString()}                     <= v3ListEmissions
GET     /api/v3/manual-extraction/batches?organization_id=${encodeURIComponent(organizationId)} <= v3ListExtractionBatches
GET     /api/v3/manual-extraction/batches/${encodeURIComponent(batchId)}/items <= v3ListExtractionItems
GET     /api/v3/batches?organization_id=${encodeURIComponent(organizationId)}  <= v3ListUploadBatches
POST    /api/v3/consultants/clients/${encodeURIComponent(clientId)}/documents/upload-url <= v3StartConsultantDirectUpload
POST    /api/v3/documents/upload-url                                           <= v3StartDirectUpload
PATCH   /api/v3/batches/${encodeURIComponent(batchId)}                         <= v3UpdateUploadBatchProgress
GET     (no literal path)                                                      <= v3UploadConsultantDocumentDirect
POST    (no literal path)                                                      <= v3UploadDocument
GET     (no literal path)                                                      <= v3UploadDocumentDirect
POST    /api/v3/settings/email-provider/validate                               <= validateEmailProviderSettings
POST    /api/v3/ops/items/${itemId}/validate                                   <= validateItem
POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/validate        <= validateProcessingItem
POST    /api/v3/admin/backups/${encodeURIComponent(jobId)}/verify              <= verifyBackup
POST    /api/v3/consultants/me/custom-domains/${domainId}/verify               <= verifyCustomDomain
POST    /api/v3/consultants/me/senders/${senderId}/verify                      <= verifyCustomSender
POST    /api/v3/discovery/requests/${requestId}/verify                         <= verifyDiscoveryRequest
POST    /api/v3/discovery/requests/${requestId}/verify                         <= verifyOnboardingDiscoveryRequest
```

---

# APPENDIX C — UI SURFACE → API BINDINGS

91 frontend files that import callables from `v3/api.js`, with the resolved
method/path and the backend guard codes for each binding. Files that call the API
without importing `v3/api.js` (raw `fetch`, e.g. `context/ReferenceDataContext.jsx`,
`hooks/useManualEntry.js`, `components/ManualEntryStandalone.jsx`) are covered by
§8.4 instead.

```text
### AcceptInvitation.jsx  (bindings=2, mutations=1)
    POST    /api/v3/organizations/invitations/accept                         <= acceptInvitation
    GET     (n/a)                                                            <= goToWorkspace

### AuthCallback.js  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= goToWorkspace

### BetaSignup.jsx  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= goToWorkspace

### Login.js  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= goToWorkspace

### MagicLink.jsx  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= goToWorkspace

### OnboardingPage.jsx  (bindings=6, mutations=5)
    POST    /api/v3/discovery/requests/${requestId}/choice                   <= chooseOnboardingAdoption
    POST    /api/v3/discovery/requests                                       <= createOnboardingDiscoveryRequest
    POST    /api/v3/organizations                                            <= createOrganization
    GET     /api/v3/me/context                                               <= getMeContext
    POST    /api/v3/discovery/lookup                                         <= onboardingDiscoveryLookup
    POST    /api/v3/discovery/requests/${requestId}/verify                   <= verifyOnboardingDiscoveryRequest

### SelfServiceSignup.jsx  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= goToWorkspace

### components/chat/ChatList.jsx  (bindings=1, mutations=0)
    GET     /api/v3/organizations/${organizationId}/members                  <= listMembers

### components/chat/ChatWidget.jsx  (bindings=1, mutations=1)
    POST    /api/v3/messaging/conversations                                  <= createMessagingConversation

### components/chat/ChatWindow.jsx  (bindings=2, mutations=1)
    GET     /api/v3/organizations/${organizationId}/members                  <= listMembers
    POST    /api/v3/messaging/conversations/${conversationId}/messages       <= sendMessagingMessage

### context/RealtimeContext.jsx  (bindings=3, mutations=2)
    GET     /api/v3/notifications${qs ?                                      <= listNotifications
    POST    /api/v3/notifications/read-all                                   <= markAllNotificationsRead
    POST    /api/v3/notifications/${notificationId}/read                     <= markNotificationRead

### v3/NotificationsPage.jsx  (bindings=3, mutations=2)
    GET     /api/v3/notifications${qs ?                                      <= listNotifications
    POST    /api/v3/notifications/read-all                                   <= markAllNotificationsRead
    POST    /api/v3/notifications/${notificationId}/read                     <= markNotificationRead

### v3/admin/ActivityTab.jsx  (bindings=1, mutations=0)
    GET     /api/v3/reporting/member-activity?organization_id=${organizationId} <= getMemberActivity

### v3/admin/AdminPage.jsx  (bindings=3, mutations=0)
    GET     /api/v3/organizations/${organizationId}/roles                    <= listOrgRoles
    GET     (n/a)                                                            <= resolveV3Membership
    GET     (n/a)                                                            <= resolveV3Organization

### v3/admin/AuditTab.jsx  (bindings=4, mutations=0)
    GET     (n/a)                                                            <= auditPackageUrl
    GET     (n/a)                                                            <= downloadExport
    GET     /api/v3/reporting/audit-activity?${query.toString()}             <= getAuditActivity
    GET     /api/v3/reporting/audit-readiness?organization_id=${encodeURIComponent(organizationId)} <= getAuditReadiness

### v3/admin/CustomFactorsTab.jsx  (bindings=5, mutations=4)
    POST    /api/v3/customer-factors/${encodeURIComponent(factorId)}/approve <= approveCustomerFactor
    POST    /api/v3/customer-factors                                         <= createCustomerFactor
    POST    /api/v3/customer-factors/${encodeURIComponent(factorId)}/deactivate <= deactivateCustomerFactor
    GET     /api/v3/customer-factors?organization_id=${encodeURIComponent(organizationId)} <= listCustomerFactors
    PUT     /api/v3/customer-factors/${encodeURIComponent(factorId)}         <= updateCustomerFactor

### v3/admin/FacilitiesTab.jsx  (bindings=8, mutations=6)
    POST    /api/v3/organizations/${organizationId}/assets                   <= createAsset
    POST    /api/v3/organizations/${organizationId}/facilities               <= createFacility
    GET     /api/v3/organizations/${organizationId}/assets                   <= listAssets
    GET     /api/v3/organizations/${organizationId}/facilities               <= listFacilities
    DELETE  /api/v3/organizations/assets/${assetId}                          <= removeAsset
    DELETE  /api/v3/organizations/facilities/${facilityId}                   <= removeFacility
    PUT     /api/v3/organizations/assets/${assetId}                          <= updateAsset
    PUT     /api/v3/organizations/facilities/${facilityId}                   <= updateFacility

### v3/admin/LocationsTab.jsx  (bindings=1, mutations=0)
    GET     /api/v3/organizations/${organizationId}/facilities               <= listFacilities

### v3/admin/MembersTab.jsx  (bindings=7, mutations=5)
    POST    /api/v3/organizations/${organizationId}/members                  <= addMember
    POST    /api/v3/organizations/${organizationId}/invitations              <= createInvitation
    GET     /api/v3/organizations/${organizationId}/invitations              <= listInvitations
    GET     /api/v3/organizations/${organizationId}/members                  <= listMembers
    DELETE  /api/v3/organizations/members/${memberId}                        <= removeMember
    DELETE  /api/v3/organizations/invitations/${invitationId}                <= revokeInvitation
    PUT     /api/v3/organizations/members/${memberId}                        <= updateMember

### v3/admin/ProfileTab.jsx  (bindings=4, mutations=2)
    GET     /api/v3/organizations/${organizationId}/metadata                 <= getOrganizationMetadata
    GET     /api/v3/organizations/${organizationId}/profile                  <= getOrganizationProfile
    PUT     /api/v3/organizations/${organizationId}/metadata                 <= updateOrganizationMetadata
    PUT     /api/v3/organizations/${organizationId}/profile                  <= updateOrganizationProfile

### v3/admin/SuppliersTab.jsx  (bindings=3, mutations=2)
    POST    /api/v3/suppliers                                                <= createSupplier
    GET     /api/v3/suppliers?${query.toString()}                            <= listSuppliers
    DELETE  /api/v3/suppliers/${supplierId}                                  <= removeSupplier

### v3/admin/VehiclesTab.jsx  (bindings=4, mutations=3)
    POST    /api/v3/vehicles                                                 <= createVehicle
    GET     /api/v3/vehicles?organization_id=${encodeURIComponent(organizationId)} <= listVehicles
    DELETE  /api/v3/vehicles/${encodeURIComponent(vehicleId)}                <= removeVehicle
    PUT     /api/v3/vehicles/${encodeURIComponent(vehicleId)}                <= updateVehicle

### v3/capabilities/CapabilitiesPage.jsx  (bindings=1, mutations=0)
    GET     /api/v3/capabilities                                             <= getCapabilityCatalogue

### v3/capabilities/InvestorCapabilityPage.jsx  (bindings=1, mutations=0)
    GET     /api/v3/capabilities                                             <= getCapabilityCatalogue

### v3/components/RoleRoute.jsx  (bindings=1, mutations=0)
    GET     /api/v3/me/context                                               <= getMeContext

### v3/components/SearchBox.jsx  (bindings=1, mutations=0)
    GET     /api/v3/search?organization_id=${encodeURIComponent(organizationId)}&q=${encodeURIComponent(q)}&limit=${limit} <= searchOrg

### v3/components/V3Layout.jsx  (bindings=2, mutations=0)
    GET     /api/v3/consultants/clients/${clientId}/context                  <= getClientWorkspaceContext
    GET     /api/v3/me/context                                               <= getMeContext

### v3/consultant/ClientAccessTab.jsx  (bindings=5, mutations=3)
    POST    /api/v3/consultants/clients/${clientId}/invitations              <= createClientInvitation
    GET     /api/v3/consultants/clients/${clientId}/invitations              <= listClientInvitations
    GET     /api/v3/consultants/clients/${clientId}/users                    <= listClientUsers
    POST    /api/v3/consultants/clients/${clientId}/invitations/${invitationId}/revoke <= revokeClientInvitation
    PATCH   /api/v3/consultants/clients/${clientId}/users/${memberId}        <= updateClientUser

### v3/consultant/ClientMessagingTab.jsx  (bindings=4, mutations=2)
    POST    /api/v3/messaging/conversations                                  <= createMessagingConversation
    GET     /api/v3/messaging/conversations?organization_id=${encodeURIComponent(organizationId)} <= listMessagingConversations
    GET     /api/v3/messaging/conversations/${conversationId}/messages       <= listMessagingMessages
    POST    /api/v3/messaging/conversations/${conversationId}/messages       <= sendMessagingMessage

### v3/consultant/ClientOrgShell.jsx  (bindings=4, mutations=0)
    GET     /api/v3/consultants/clients/${clientId}/context                  <= getClientWorkspaceContext
    GET     /api/v3/consultants/me                                           <= getConsultantProfile
    GET     /api/v3/consultants/me/clients                                   <= listConsultantClients
    GET     (n/a)                                                            <= setActiveConsultantClientId

### v3/consultant/ConsultantItemPage.jsx  (bindings=9, mutations=6)
    POST    /api/v3/ops/items/${itemId}/calculate                            <= calculateItem
    POST    /api/v3/processing/items/${itemId}/consultant-review             <= consultantReviewItem
    POST    /api/v3/processing/items/${itemId}/consultant-submit             <= consultantSubmitItem
    POST    /api/v3/ops/items/${itemId}/extract                              <= extractItem
    GET     /api/v3/consultants/clients/${clientId}/processing/items${query} <= getClientProcessingItems
    GET     /api/v3/processing/items/${itemId}/workspace                     <= getConsultantItemWorkspace
    GET     /api/v3/ops/items/${itemId}/mapping-options${qs ?                <= getMappingOptions
    POST    /api/v3/ops/items/${itemId}/map                                  <= mapItem
    POST    /api/v3/ops/items/${itemId}/start                                <= startItem

### v3/consultant/ConsultantPage.jsx  (bindings=12, mutations=5)
    POST    /api/v3/consultants/clients/${clientId}/end                      <= endConsultantClient
    GET     /api/v3/consultants/me/branding                                  <= getConsultantBranding
    GET     /api/v3/consultants/me/branding/context                          <= getConsultantBrandingContext
    GET     /api/v3/reporting/consultant-client/${clientId}                  <= getConsultantClientDetail
    GET     /api/v3/consultants/me/dashboard                                 <= getConsultantDashboard
    GET     /api/v3/reporting/consultant-portfolio                           <= getConsultantPortfolio
    GET     /api/v3/consultants/me                                           <= getConsultantProfile
    GET     /api/v3/consultants/me/clients                                   <= listConsultantClients
    POST    /api/v3/consultants/clients/${clientId}/reactivate               <= reactivateConsultantClient
    POST    /api/v3/consultants/clients/${clientId}/suspend                  <= suspendConsultantClient
    PUT     /api/v3/consultants/me/branding                                  <= updateConsultantBranding
    PUT     /api/v3/consultants/clients/${clientId}                          <= updateConsultantClientStatus

### v3/consultant/ConsultantTeamTab.jsx  (bindings=9, mutations=6)
    POST    /api/v3/consultants/me/team                                      <= addConsultantTeamMember
    POST    /api/v3/consultants/me/tasks                                     <= createConsultantTask
    POST    /api/v3/consultants/me/team/${memberId}/deactivate               <= deactivateConsultantTeamMember
    GET     /api/v3/consultants/me/tasks${query}                             <= getConsultantTasks
    GET     /api/v3/consultants/me/team                                      <= getConsultantTeam
    GET     /api/v3/consultants/me/clients                                   <= listConsultantClients
    POST    /api/v3/consultants/me/team/${memberId}/reactivate               <= reactivateConsultantTeamMember
    PUT     /api/v3/consultants/tasks/${taskId}/status                       <= updateConsultantTaskStatus
    PATCH   /api/v3/consultants/me/team/${memberId}/capabilities             <= updateConsultantTeamMemberCapabilities

### v3/consultant/ManualProcessingCoverageTab.jsx  (bindings=3, mutations=2)
    POST    /api/v3/consultants/me/manual-processing/allocations             <= allocateConsultantManualProcessingClient
    GET     /api/v3/consultants/me/manual-processing/coverage                <= getConsultantManualProcessingCoverage
    DELETE  /api/v3/consultants/me/manual-processing/allocations/${encodeURIComponent(allocationId)} <= releaseConsultantManualProcessingAllocation

### v3/consultant/NewCustomerView.jsx  (bindings=1, mutations=1)
    POST    /api/v3/consultants/me/customers                                 <= createConsultantCustomer

### v3/consultant/WhiteLabelTab.jsx  (bindings=9, mutations=7)
    POST    /api/v3/consultants/me/custom-domains/${domainId}/activate       <= activateCustomDomain
    POST    /api/v3/consultants/me/custom-domains                            <= createCustomDomain
    POST    /api/v3/consultants/me/senders                                   <= createCustomSender
    GET     /api/v3/consultants/me/custom-domains                            <= listCustomDomains
    GET     /api/v3/consultants/me/senders                                   <= listCustomSenders
    POST    /api/v3/consultants/me/custom-domains/${domainId}/remove         <= removeCustomDomain
    POST    /api/v3/consultants/me/senders/${senderId}/remove                <= removeCustomSender
    POST    /api/v3/consultants/me/custom-domains/${domainId}/verify         <= verifyCustomDomain
    POST    /api/v3/consultants/me/senders/${senderId}/verify                <= verifyCustomSender

### v3/customer/BillingPage.jsx  (bindings=9, mutations=5)
    POST    /api/v3/billing/orders/${encodeURIComponent(orderId)}/approve    <= approveBillingOrder
    POST    /api/v3/billing/orders/${encodeURIComponent(orderId)}/cancel     <= cancelBillingOrder
    POST    /api/v3/billing/orders/assisted                                  <= createAssistedEstimate
    POST    /api/v3/billing/managed/orders                                   <= createManagedOrder
    GET     /api/v3/billing/me                                               <= getMyBilling
    GET     /api/v3/billing/me/credits                                       <= getMyCreditHistory
    GET     /api/v3/billing/me/orders                                        <= listMyOrders
    GET     /api/v3/billing/me/payments                                      <= listMyPayments
    POST    /api/v3/billing/me/storage/refresh                               <= refreshMyStorage

### v3/customer/DashboardPage.jsx  (bindings=8, mutations=0)
    GET     /api/v3/reporting/customer-dashboard?${query.toString()}         <= getCustomerDashboardReport
    GET     /api/v3/reporting/emissions-trend?organization_id=${organizationId}&months=${months} <= getEmissionsTrend
    GET     /api/v3/reporting/member-activity?organization_id=${organizationId} <= getMemberActivity
    GET     /api/v3/organizations/${organizationId}/members                  <= listMembers
    GET     /api/v3/reports?${query.toString()}                              <= listReports
    GET     (n/a)                                                            <= resolveV3Organization
    GET     /api/v3/documents?${query.toString()}                            <= v3ListDocuments
    GET     /api/v3/exports/emissions.json?${query.toString()}               <= v3ListEmissions

### v3/customer/DocumentsPage.jsx  (bindings=4, mutations=0)
    GET     /api/v3/documents/${fileId}/emissions                            <= getDocumentEmissions
    GET     (n/a)                                                            <= resolveV3Organization
    GET     /api/v3/documents?${query.toString()}                            <= v3ListDocuments
    GET     /api/v3/batches?organization_id=${encodeURIComponent(organizationId)} <= v3ListUploadBatches

### v3/customer/EmissionsPage.jsx  (bindings=4, mutations=1)
    GET     /api/v3/emissions/${logId}/evidence                              <= getEmissionEvidence
    GET     (n/a)                                                            <= resolveV3Organization
    POST    /api/v3/emissions/calculate                                      <= v3CalculateEmissions
    GET     /api/v3/exports/emissions.json?${query.toString()}               <= v3ListEmissions

### v3/customer/ExistingDataDiscoveryPage.jsx  (bindings=7, mutations=4)
    POST    /api/v3/discovery/requests/${requestId}/choice                   <= chooseDiscoveryAdoption
    POST    /api/v3/discovery/requests                                       <= createDiscoveryRequest
    POST    /api/v3/discovery/lookup                                         <= discoveryLookup
    GET     /api/v3/discovery/requests/${requestId}?organization_id=${encodeURIComponent(organizationId)} <= getDiscoveryRequest
    GET     /api/v3/discovery/requests?organization_id=${encodeURIComponent(organizationId)} <= listDiscoveryRequests
    GET     (n/a)                                                            <= resolveV3Organization
    POST    /api/v3/discovery/requests/${requestId}/verify                   <= verifyDiscoveryRequest

### v3/customer/IssuesPage.jsx  (bindings=4, mutations=1)
    POST    /api/v3/issues                                                   <= createCustomerIssue
    GET     /api/v3/issues/${issueId}                                        <= getCustomerIssue
    GET     /api/v3/issues?${query.toString()}                               <= listCustomerIssues
    GET     (n/a)                                                            <= resolveV3Organization

### v3/customer/ManualProcessingPage.jsx  (bindings=2, mutations=0)
    GET     /api/v3/organizations/${encodeURIComponent(organizationId)}/manual-processing <= getMyManualProcessing
    GET     (n/a)                                                            <= resolveV3Organization

### v3/customer/MessagingPage.jsx  (bindings=5, mutations=2)
    POST    /api/v3/messaging/conversations                                  <= createMessagingConversation
    GET     /api/v3/messaging/conversations?organization_id=${encodeURIComponent(organizationId)} <= listMessagingConversations
    GET     /api/v3/messaging/conversations/${conversationId}/messages       <= listMessagingMessages
    GET     (n/a)                                                            <= resolveV3Organization
    POST    /api/v3/messaging/conversations/${conversationId}/messages       <= sendMessagingMessage

### v3/customer/ProcessingItemWorkspace.jsx  (bindings=14, mutations=9)
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/calculate <= calculateProcessingItem
    POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/confirm     <= confirmProcessingJob
    GET     /api/v3/documents/${fileId}/emissions                            <= getDocumentEmissions
    GET     /api/v3/processing/items/${encodeURIComponent(itemId)}/workspace <= getProcessingItemWorkspace
    GET     /api/v3/processing/jobs?${query.toString()}                      <= getProcessingJobs
    GET     /api/v3/processing/items/${encodeURIComponent(itemId)}/mapping-options <= getProcessingMappingOptions
    GET     (n/a)                                                            <= resolveV3Membership
    POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/retry       <= retryProcessingJob
    POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/review      <= reviewProcessingJob
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/extract   <= saveProcessingExtraction
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/map       <= saveProcessingMapping
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/start     <= startProcessingItem
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/customer-review <= submitCustomerReview
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/validate  <= validateProcessingItem

### v3/customer/ProcessingPage.jsx  (bindings=8, mutations=3)
    POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/confirm     <= confirmProcessingJob
    GET     /api/v3/processing/jobs?${query.toString()}                      <= getProcessingJobs
    GET     /api/v3/processing/status?organization_id=${encodeURIComponent(organizationId)} <= getProcessingStatus
    GET     (n/a)                                                            <= resolveV3Organization
    POST    /api/v3/processing/jobs/${encodeURIComponent(jobId)}/retry       <= retryProcessingJob
    GET     /api/v3/manual-extraction/batches?organization_id=${encodeURIComponent(organizationId)} <= v3ListExtractionBatches
    GET     /api/v3/manual-extraction/batches/${encodeURIComponent(batchId)}/items <= v3ListExtractionItems
    POST    (n/a)                                                            <= v3UploadDocument

### v3/customer/ReviewDetailPage.jsx  (bindings=3, mutations=1)
    GET     /api/v3/processing/items/${encodeURIComponent(itemId)}/workspace <= getProcessingItemWorkspace
    GET     (n/a)                                                            <= resolveV3Membership
    POST    /api/v3/processing/items/${encodeURIComponent(itemId)}/customer-review <= submitCustomerReview

### v3/customer/ReviewPage.jsx  (bindings=2, mutations=0)
    GET     /api/v3/processing/customer-review?organization_id=${encodeURIComponent(organizationId)} <= getCustomerReviewQueue
    GET     (n/a)                                                            <= resolveV3Membership

### v3/customer/UploadDocumentsPanel.jsx  (bindings=3, mutations=2)
    POST    /api/v3/batches?organization_id=${encodeURIComponent(organizationId)} <= v3CreateUploadBatch
    PATCH   /api/v3/batches/${encodeURIComponent(batchId)}                   <= v3UpdateUploadBatchProgress
    GET     (n/a)                                                            <= v3UploadDocumentDirect

### v3/evidence/SourceEvidenceViewer.jsx  (bindings=1, mutations=0)
    GET     /api/v3/evidence/line-items/${encodeURIComponent(lineItemId)}    <= getEvidenceLine

### v3/insight/InsightComparison.jsx  (bindings=1, mutations=1)
    POST    /api/v3/insight/tools/invoke                                     <= invokeInsightTool

### v3/insight/InsightInteraction.jsx  (bindings=1, mutations=0)
    GET     /api/v3/insight/interactions/${encodeURIComponent(interactionId)}? <= getInsightInteraction

### v3/insight/InsightPage.jsx  (bindings=6, mutations=2)
    POST    /api/v3/insight/conversations                                    <= createInsightConversation
    GET     /api/v3/insight/conversations?${insightQuery({ organization_id: organizationId, limit, offset })} <= listInsightConversations
    GET     /api/v3/insight/interactions?${insightQuery({
    organization_id: organizationId,
    conversation_id: conversationId,
    limit,
    offset,
  })} <= listInsightInteractions
    GET     /api/v3/insight/conversations/${encodeURIComponent(conversationId)}/messages? <= listInsightMessages
    GET     (n/a)                                                            <= resolveV3Organization
    POST    /api/v3/insight/interactions                                     <= runInsightInteraction

### v3/insight/InsightReferences.jsx  (bindings=1, mutations=1)
    POST    /api/v3/insight/tools/invoke                                     <= invokeInsightTool

### v3/ops/AuditConsoleTab.jsx  (bindings=1, mutations=0)
    GET     /api/v3/ops/reporting/audit${query.toString() ?                  <= getOpsAudit

### v3/ops/BackupsTab.jsx  (bindings=8, mutations=3)
    POST    /api/v3/admin/backups                                            <= createBackup
    GET     (n/a)                                                            <= downloadBackupArtifact
    GET     /api/v3/admin/backups/${encodeURIComponent(jobId)}/pair          <= getBackupPair
    GET     /api/v3/admin/backups/policy                                     <= getBackupPolicy
    GET     /api/v3/admin/backups/status                                     <= getBackupStatus
    GET     /api/v3/admin/backups?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)} <= listBackups
    PUT     /api/v3/admin/backups/policy                                     <= updateBackupPolicy
    POST    /api/v3/admin/backups/${encodeURIComponent(jobId)}/verify        <= verifyBackup

### v3/ops/CommercialTab.jsx  (bindings=18, mutations=11)
    POST    /api/v3/commercial/subscriptions                                 <= activateSubscription
    POST    /api/v3/commercial/credits/adjust                                <= adminAdjustCredits
    POST    /api/v3/commercial/credits/grant                                 <= adminGrantCredits
    POST    /api/v3/commercial/credits/refund                                <= adminRefundCredits
    POST    /api/v3/commercial/credits/reverse                               <= adminReverseCredits
    POST    /api/v3/commercial/credits/rollover                              <= adminRolloverCredits
    POST    /api/v3/commercial/subscriptions/${encodeURIComponent(subscriptionId)}/status <= changeSubscriptionStatus
    POST    /api/v3/commercial/orders/${encodeURIComponent(orderId)}/complete <= completeAdminOrder
    POST    /api/v3/commercial/plans                                         <= createCommercialPlan
    GET     /api/v3/commercial/overview                                      <= getCommercialOverview
    GET     /api/v3/commercial/plans/${encodeURIComponent(planCode)}         <= getCommercialPlan
    GET     /api/v3/commercial/ledger?organization_id=${encodeURIComponent(organizationId)} <= getCreditLedger
    GET     /api/v3/commercial/orders${status ?                              <= listAdminOrders
    GET     /api/v3/commercial/storage                                       <= listAdminStorage
    GET     /api/v3/commercial/organizations${
      billingMode ?           <= listCommercialOrganizations
    GET     /api/v3/commercial/subscriptions                                 <= listSubscriptions
    PUT     /api/v3/commercial/config/${encodeURIComponent(configKey)}       <= updateCommercialConfig
    PUT     /api/v3/commercial/plans/${encodeURIComponent(planCode)}         <= updateCommercialPlan

### v3/ops/CtQcTab.jsx  (bindings=2, mutations=1)
    POST    /api/v3/ops/qc/items/${itemId}/decision                          <= ctQcDecision
    GET     /api/v3/ops/qc/ct-queue                                          <= getCtQcQueue

### v3/ops/EntityExtractionWorkspace.jsx  (bindings=4, mutations=0)
    GET     /api/v3/ops/entities/${entityId}/dashboard                       <= getEntityDashboard
    GET     /api/v3/ops/entities/${entityId}/extraction/batches/${batchId}/items <= getEntityExtractionBatchItems
    GET     /api/v3/ops/entities/${entityId}/extraction/batches${query}      <= getEntityExtractionBatches
    GET     /api/v3/ops/entities/${entityId}/performance                     <= getEntityPerformance

### v3/ops/IssuesTriageTab.jsx  (bindings=2, mutations=1)
    GET     /api/v3/issues/admin/open${query}                                <= listOpsOpenIssues
    PUT     /api/v3/issues/${encodeURIComponent(issueId)}                    <= updateIssue

### v3/ops/ManualProcessingCoverageTab.jsx  (bindings=5, mutations=2)
    POST    /api/v3/admin/manual-processing/coverage/allocations             <= allocateAdminManualProcessingClient
    GET     /api/v3/admin/manual-processing/clients/${encodeURIComponent(organizationId)} <= getAdminManualProcessingClientState
    GET     /api/v3/admin/manual-processing/coverage/${encodeURIComponent(consultantId)} <= getAdminManualProcessingCoverage
    DELETE  /api/v3/admin/manual-processing/coverage/allocations/${encodeURIComponent(allocationId)} <= releaseAdminManualProcessingAllocation
    GET     /api/v3/admin/manual-processing/organizations?${params.toString()} <= searchAdminManualProcessingOrganizations

### v3/ops/ManualProcessingTab.jsx  (bindings=5, mutations=3)
    DELETE  /api/v3/admin/manual-processing/processors/${encodeURIComponent(scopeType)}/${encodeURIComponent(scopeId)} <= deleteManualProcessingProcessor
    GET     /api/v3/admin/manual-processing/state?scope_type=${encodeURIComponent(scopeType)}&scope_id=${encodeURIComponent(scopeId)} <= getManualProcessingState
    GET     /api/v3/ops/entities?${query.toString()}                         <= listProcessingEntities
    PUT     /api/v3/admin/manual-processing/grants                           <= setManualProcessingGrant
    PUT     /api/v3/admin/manual-processing/processors                       <= setManualProcessingProcessor

### v3/ops/OperationalHealthTab.jsx  (bindings=3, mutations=0)
    GET     /api/v3/ops/operational-health/queue                             <= getOperationalHealthQueue
    GET     /api/v3/ops/operational-health/worker                            <= getOperationalHealthWorker
    GET     /api/v3/ops/operational-intelligence                             <= getOperationalIntelligence

### v3/ops/OperationsPage.jsx  (bindings=1, mutations=0)
    GET     /api/v3/ops/me                                                   <= getOpsMe

### v3/ops/OperatorItemPage.jsx  (bindings=7, mutations=4)
    POST    /api/v3/ops/items/${itemId}/calculate                            <= calculateItem
    POST    /api/v3/ops/items/${itemId}/extract                              <= extractItem
    GET     /api/v3/ops/items/${itemId}/workspace                            <= getItemWorkspace
    GET     /api/v3/ops/items/${itemId}/mapping-options${qs ?                <= getMappingOptions
    GET     /api/v3/ops/batches/${batchId}/items                             <= getOpsBatchItems
    POST    /api/v3/ops/items/${itemId}/map                                  <= mapItem
    POST    /api/v3/ops/items/${itemId}/start                                <= startItem

### v3/ops/OperatorQueue.jsx  (bindings=11, mutations=5)
    POST    /api/v3/ops/batches/${batchId}/assign                            <= assignBatch
    POST    /api/v3/ops/items/${itemId}/calculate                            <= calculateItem
    POST    /api/v3/ops/items/${itemId}/extract                              <= extractItem
    GET     /api/v3/ops/items/${itemId}/mapping-options${qs ?                <= getMappingOptions
    GET     /api/v3/ops/queues/operator?${query.toString()}                  <= getOperatorQueue
    GET     /api/v3/ops/batches/${batchId}/items                             <= getOpsBatchItems
    GET     /api/v3/ops/me                                                   <= getOpsMe
    GET     /api/v3/ops/staff?limit=${limit}&offset=${offset}                <= listOpsStaff
    GET     /api/v3/ops/entities?${query.toString()}                         <= listProcessingEntities
    POST    /api/v3/ops/items/${itemId}/map                                  <= mapItem
    POST    /api/v3/ops/items/${itemId}/start                                <= startItem

### v3/ops/OpsAssignmentsTab.jsx  (bindings=11, mutations=5)
    GET     /api/v3/ops/entities/${entityId}/extraction/batches${query}      <= getEntityExtractionBatches
    GET     /api/v3/ops/queues/operator?${query.toString()}                  <= getOperatorQueue
    GET     /api/v3/ops/batches/${batchId}/items                             <= getOpsBatchItems
    GET     /api/v3/ops/staff?limit=${limit}&offset=${offset}                <= listOpsStaff
    GET     /api/v3/ops/entities?${query.toString()}                         <= listProcessingEntities
    POST    /api/v3/ops/items/${itemId}/work/assign                          <= opsWorkAssignTarget
    POST    /api/v3/ops/items/${itemId}/work/claim                           <= opsWorkClaim
    POST    /api/v3/ops/items/${itemId}/work/complete                        <= opsWorkComplete
    GET     /api/v3/ops/items/${itemId}/work                                 <= opsWorkInfo
    POST    /api/v3/ops/items/${itemId}/work/reassign                        <= opsWorkReassignTarget
    POST    /api/v3/ops/items/${itemId}/work/release                         <= opsWorkRelease

### v3/ops/OpsDashboard.jsx  (bindings=4, mutations=0)
    GET     /api/v3/ops/reporting/audit${query.toString() ?                  <= getOpsAudit
    GET     /api/v3/ops/dashboard                                            <= getOpsDashboard
    GET     /api/v3/ops/reporting/platform                                   <= getOpsPlatformReporting
    GET     /api/v3/ops/reporting/aging                                      <= getOpsQueueAging

### v3/ops/OpsMessagingTab.jsx  (bindings=5, mutations=2)
    POST    /api/v3/messaging/conversations                                  <= createMessagingConversation
    GET     /api/v3/ops/organizations${qs ?                                  <= getOpsOrganizations
    GET     /api/v3/messaging/conversations?organization_id=${encodeURIComponent(organizationId)} <= listMessagingConversations
    GET     /api/v3/messaging/conversations/${conversationId}/messages       <= listMessagingMessages
    POST    /api/v3/messaging/conversations/${conversationId}/messages       <= sendMessagingMessage

### v3/ops/OpsPeMessagingTab.jsx  (bindings=3, mutations=1)
    GET     /api/v3/messaging/entity-conversations${qs}                      <= listEntityConversations
    GET     /api/v3/messaging/entity-conversations/${conversationId}/messages <= listEntityMessages
    POST    /api/v3/messaging/entity-conversations/${conversationId}/messages <= sendEntityMessage

### v3/ops/PEEntityItemPage.jsx  (bindings=11, mutations=6)
    POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/calculate <= entityCalculateItem
    POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/clarify <= entityClarifyItem
    POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/extract <= entityExtractItem
    POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/map  <= entityMapItem
    POST    /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/start <= entityStartItem
    POST    /api/v3/pe/items/${itemId}/validate                              <= entityValidateItem
    GET     /api/v3/ops/entities/${entityId}/extraction/batches/${batchId}/items <= getEntityExtractionBatchItems
    GET     /api/v3/ops/entities/${entityId}/extraction/batches${query}      <= getEntityExtractionBatches
    GET     /api/v3/ops/entities/${entityId}/extraction/items/${itemId}      <= getEntityExtractionItem
    GET     /api/v3/ops/entities/${entityId}/extraction/items/${itemId}/mapping-options${qs ?  <= getEntityMappingOptions
    GET     /api/v3/pe/me                                                    <= getPeMe

### v3/ops/PEManagerDashboard.jsx  (bindings=3, mutations=0)
    GET     /api/v3/ops/entities/${entityId}/dashboard                       <= getEntityDashboard
    GET     /api/v3/ops/entities/${entityId}/extraction/batches${query}      <= getEntityExtractionBatches
    GET     /api/v3/ops/entities/${entityId}/performance                     <= getEntityPerformance

### v3/ops/ProcessingEntitiesTab.jsx  (bindings=2, mutations=1)
    POST    /api/v3/processing-entities                                      <= createProcessingEntity
    GET     /api/v3/ops/entities?${query.toString()}                         <= listProcessingEntities

### v3/ops/QcItemPage.jsx  (bindings=1, mutations=1)
    POST    /api/v3/ops/items/${itemId}/qc                                   <= qcReviewItem

### v3/ops/QcQueue.jsx  (bindings=2, mutations=0)
    GET     /api/v3/ops/reporting/qc                                         <= getOpsQcReporting
    GET     /api/v3/ops/queues/qc?limit=${limit}&offset=${offset}            <= getQcQueue

### v3/ops/ReviewItemPage.jsx  (bindings=4, mutations=4)
    POST    /api/v3/ops/review/${reviewId}/assign                            <= assignReview
    POST    /api/v3/ops/review/${reviewId}/complete                          <= completeReview
    POST    /api/v3/ops/items/${itemId}/submit-review                        <= submitInternalReview
    POST    /api/v3/ops/items/${itemId}/validate                             <= validateItem

### v3/ops/ReviewQueue.jsx  (bindings=2, mutations=0)
    GET     /api/v3/ops/reporting/review                                     <= getOpsReviewReporting
    GET     /api/v3/ops/queues/review?${query.toString()}                    <= getReviewQueue

### v3/ops/SettingsTab.jsx  (bindings=11, mutations=6)
    GET     /api/v3/settings/analytics                                       <= getAnalyticsSettings
    GET     /api/v3/settings/email-provider                                  <= getEmailProviderSettings
    GET     /api/v3/settings/notification-sender                             <= getNotificationSenderSettings
    GET     /api/v3/settings/retention                                       <= getRetentionSettings
    GET     /api/v3/settings/upload-policy                                   <= getUploadPolicySettings
    PUT     /api/v3/settings/analytics                                       <= updateAnalyticsSettings
    PUT     /api/v3/settings/email-provider                                  <= updateEmailProviderSettings
    PUT     /api/v3/settings/notification-sender                             <= updateNotificationSenderSettings
    PUT     /api/v3/settings/retention                                       <= updateRetentionSettings
    PUT     /api/v3/settings/upload-policy                                   <= updateUploadPolicySettings
    POST    /api/v3/settings/email-provider/validate                         <= validateEmailProviderSettings

### v3/ops/SlaTab.jsx  (bindings=2, mutations=1)
    GET     /api/v3/ops/sla/settings                                         <= getSlaSettings
    PUT     /api/v3/ops/sla/settings                                         <= updateSlaSettings

### v3/ops/StaffRolesTab.jsx  (bindings=1, mutations=0)
    GET     /api/v3/ops/staff-roles                                          <= listStaffRoles

### v3/ops/StaffRoster.jsx  (bindings=5, mutations=2)
    POST    /api/v3/ops/staff                                                <= createOpsStaff
    GET     /api/v3/ops/staff?limit=${limit}&offset=${offset}                <= listOpsStaff
    GET     /api/v3/ops/entities?${query.toString()}                         <= listProcessingEntities
    GET     /api/v3/ops/staff-roles                                          <= listStaffRoles
    PUT     /api/v3/ops/staff/${profileId}                                   <= updateOpsStaff

### v3/ops/WorkItemWorkspace.jsx  (bindings=1, mutations=0)
    GET     /api/v3/ops/items/${itemId}/workspace                            <= getItemWorkspace

### v3/pe/PEDedicatedHome.jsx  (bindings=5, mutations=2)
    GET     /api/v3/pe/batches/${batchId}/items                              <= getPeBatchItems
    GET     /api/v3/pe/me                                                    <= getPeMe
    GET     /api/v3/pe/work${status ?                                        <= getPeWork
    POST    /api/v3/pe/items/${itemId}/pe-qc                                 <= peQcDecision
    POST    /api/v3/pe/items/${itemId}/pe-review                             <= peReviewDecision

### v3/pe/PEShell.jsx  (bindings=1, mutations=0)
    GET     /api/v3/pe/me                                                    <= getPeMe

### v3/pe/PeMessagingPage.jsx  (bindings=5, mutations=3)
    POST    /api/v3/messaging/entity-conversations                           <= createEntityConversation
    GET     /api/v3/messaging/entity-conversations${qs}                      <= listEntityConversations
    GET     /api/v3/messaging/entity-conversations/${conversationId}/messages <= listEntityMessages
    POST    /api/v3/messaging/entity-conversations/${conversationId}/read    <= markEntityConversationRead
    POST    /api/v3/messaging/entity-conversations/${conversationId}/messages <= sendEntityMessage

### v3/pe/PeNotificationsBell.jsx  (bindings=3, mutations=2)
    GET     /api/v3/notifications${qs ?                                      <= listNotifications
    POST    /api/v3/notifications/read-all                                   <= markAllNotificationsRead
    POST    /api/v3/notifications/${notificationId}/read                     <= markNotificationRead

### v3/pe/PeWorkItemsPage.jsx  (bindings=7, mutations=3)
    GET     /api/v3/pe/batches/${batchId}/items                              <= getPeBatchItems
    GET     /api/v3/pe/me                                                    <= getPeMe
    GET     /api/v3/pe/work${status ?                                        <= getPeWork
    POST    /api/v3/pe/items/${itemId}/work/claim                            <= peWorkClaim
    POST    /api/v3/pe/items/${itemId}/work/complete                         <= peWorkComplete
    GET     /api/v3/pe/items/${itemId}/work                                  <= peWorkInfo
    POST    /api/v3/pe/items/${itemId}/work/release                          <= peWorkRelease

### v3/portal/ClientPortal.jsx  (bindings=4, mutations=2)
    GET     /api/v3/portal/${clientId}/context                               <= getPortalContext
    GET     /api/v3/portal/${clientId}/organization                          <= getPortalOrganization
    POST    /api/v3/portal/${clientId}/annotations                           <= postPortalAnnotation
    POST    /api/v3/portal/${clientId}/relationship-requests                 <= requestPortalRelationshipChange

### v3/reports/ReportDetailPage.jsx  (bindings=7, mutations=0)
    GET     (n/a)                                                            <= downloadExport
    GET     (n/a)                                                            <= downloadReport
    GET     (n/a)                                                            <= exportEmissionsUrl
    GET     /api/v3/reports/${reportId}                                      <= getReport
    GET     /api/v3/reports/${reportId}/content                              <= getReportContent
    GET     /api/v3/reports/${reportId}/versions                             <= getReportVersions
    GET     (n/a)                                                            <= resolveV3Organization

### v3/reports/ReportLifecyclePanel.jsx  (bindings=1, mutations=0)
    GET     (n/a)                                                            <= REPORT_LIFECYCLE_ACTION_CALLS

### v3/reports/ReportsPage.jsx  (bindings=8, mutations=1)
    GET     (n/a)                                                            <= downloadExport
    GET     (n/a)                                                            <= downloadReport
    GET     (n/a)                                                            <= exportDocumentsUrl
    GET     (n/a)                                                            <= exportEmissionsUrl
    POST    /api/v3/reports                                                  <= generateReport
    GET     /api/v3/reports/types                                            <= getReportTypes
    GET     /api/v3/reports?${query.toString()}                              <= listReports
    GET     (n/a)                                                            <= resolveV3Organization
```

---

# APPENDIX D — REPRODUCIBILITY, EVIDENCE INDEX, SAFETY CONFIRMATION

## D.1 How to reproduce Phase 2 (all commands read-only)

```bash
# 0. Environment truth
cd /home/shomonrobie/ct_93d5cdd
git rev-parse HEAD && git rev-parse --abbrev-ref HEAD
git status --porcelain | awk '{print $1}' | sort | uniq -c
git diff --stat | tail -2
sed -E 's/=.*/=<redacted>/' backend/.env | head -30      # keys only
ss -ltn                                                   # listening ports

# 1. Registered backend routes (in-process; uses the repo's own flattener)
backend/.venv/bin/python /tmp/p2_dump_routes2.py          # -> /tmp/p2_routes_effective.json
python3 /tmp/p2_analyze_routes.py                         # -> /tmp/p2_route_table.tsv + profile

# 2. Runtime cross-check (local Demo Lab only; production forbidden)
curl -s -m 6  http://127.0.0.1:8070/health
curl -s -m 30 http://127.0.0.1:8070/openapi.json -o /tmp/p2_runtime_openapi.json
curl -s -o /dev/null -m 4 -w '%{http_code}\n' http://127.0.0.1:8060/health   # the .env port

# 3. Frontend surface + parity
python3 /tmp/p2_build_appendices.py                       # appendices A–C inputs
python3 /tmp/p2_fe_api_map.py                             # first pass (api.js only)
python3 /tmp/p2_page_api_map.py                           # page -> api.js bindings
python3 /tmp/p2_api_scan2.py                              # second pass (all /api/ tokens)
python3 /tmp/p2_dead_paths.py                             # paths with no backend route

# 4. Database inventory (read-only)
python3 /tmp/p2_db_probe.py                               # schema + row counts, both DBs

# 5. Integrity
git status --porcelain ; git diff --stat ; git diff --cached --name-only
```

Notes: the helper scripts were written to `/tmp` (never into the repository).
`/tmp/p2_dump_routes2.py` imports the FastAPI composition root in-process and
starts **no** server. The `.env` port probe returned `000` (unavailable); the
Demo Lab instance on `8070` is a different configuration whose database is
`carbontally_demo_local` (§11.2).

## D.2 Evidence-file index (`/tmp`, outside the repository)

| File | Content |
|---|---|
| `p2_git_initial.txt` / `p2_git_final.txt` | Git state before/after |
| `p2_backend_tree.txt`, `p2_routers.txt`, `p2_includes.txt`, `p2_api_router.txt` | composition root, router includes, api router head |
| `p2_routes_dump.txt`, `p2_routes_dump2.txt`, `p2_routes_effective.json`, `p2_route_table.tsv` | route enumeration (50 objects → 781 operations) |
| `p2_route_analysis.txt`, `p2_routes_consult_commercial.txt`, `p2_tabs_routes.txt`, `p2_processing_routes.txt` | guard profiles and family slices |
| `p2_runtime_probe.txt`, `p2_runtime_openapi.json`, `p2_proc.txt`, `p2_env.txt` | runtime observation and process facts |
| `p2_appjs.txt`, `p2_app_imports.txt`, `p2_app_fns.txt`, `p2_guards.txt`, `p2_roleroute.txt` | frontend route config and guard usage |
| `p2_v3_files.txt`, `p2_v3_lists.txt`, `p2_frontend.txt`, `p2_admin_ui.txt`, `p2_admin_app.txt` | frontend surface tree (incl. the separate `admin/` app) |
| `p2_fe_api_summary.txt`, `p2_fe_api_map.txt`, `p2_page_api_summary.txt`, `p2_page_api_map.txt`, `p2_api_scan2.txt`, `p2_dead_paths.txt` | UI → API extractions (both passes) |
| `p2_auth_defs.txt`, `p2_auth_defs2.txt`, `p2_consultant_auth.txt`, `p2_ceiling.txt`, `p2_upload_gate.txt`, `p2_guards.txt` | authorization mechanism evidence |
| `p2_context_rel.txt`, `p2_profile_matrix.txt`, `p2_lifecycle.txt`, `p2_uploads.txt` | actor context, client-access matrix, invitations, upload gating |
| `p2_commercial_files.txt`, `p2_commercial_defs.txt`, `p2_billing_detail.txt`, `p2_billing_routes.txt` | commercial architecture evidence |
| `p2_reference.txt`, `p2_refdata.txt`, `p2_vocab_counts.txt`, `p2_vocab_counts_runtime.txt`, `p2_units_ref.txt` | master/reference data evidence |
| `p2_db_probe_out.txt`, `p2_db_target.txt` | database schema/state evidence |
| `p2_legacy.txt`, `p2_legacy_imports.txt`, `p2_legacy_render.txt`, `p2_dashboard_usage.txt`, `p2_legacy_paths_check.txt`, `p2_mig_names.txt`, `p2_mig2.txt` | legacy/duplicate surface evidence |
| `p2_appendix_routes.txt`, `p2_appendix_api_js.txt`, `p2_appendix_page_bindings.txt`, `p2_appendix_fe_routes.txt` | appendix inputs |
| `p2_appendices_summary.txt`, `p2_append_out.txt`, `p2_verify_report.txt` | aggregate counts and this report's own verification |

## D.3 Safety confirmation

| Rule | Confirmation |
|---|---|
| Application code modified | **no** |
| Database schema modified | **no** |
| RLS modified | **no** |
| Migrations created or applied | **no** |
| Seed/demo data modified | **no** |
| Test files modified | **no** |
| `.env` modified | **no** |
| Services started, stopped or repaired | **no** |
| Production contacted | **no** |
| Secrets, tokens or signed URLs printed | **no** (credentials masked as `<creds>`; the report contains no secret values) |
| Git history changed (reset/clean/checkout/restore/stash/rebase/commit/amend) | **no** |
| Files created in the repository | exactly one: `docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md` |
| Phase 1 baseline edited | **no** (still 72,782 bytes) |

## D.4 Verdict

INVENTORY COMPLETE — READ-ONLY

Scope caveats that accompany this verdict (they do not change it): the inventory
is a **static, source-and-catalogue-level** inventory. Behavioural authorization,
RLS policy contents, per-route schema verification, browser/UI state auditing,
accessibility and responsive testing, and the current test baseline were **not**
performed and are recorded as UNKNOWN / NOT VERIFIED in §10.1, §11.3 and §11.4.

*End of CT-CARBONTALLY-FOUNDATION-INVENTORY-02.*
