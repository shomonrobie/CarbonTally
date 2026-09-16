# CARBONTALLY — AUDIT FINDING VERIFICATION REPORT

- **Verification date:** 2026-08-31
- **Checkpoint under audit:** `16391217103b98dcea520070c5a22c68f12fe607` (HEAD confirmed: `1639121`)
- **Source:** Independent Audit Swarm run `20260831T173912_16391217` (18 findings)
- **Task:** Independent verification of each finding against the actual codebase. **Read-only. No application code, schema, RLS, routes, or configuration was modified. Nothing committed.**
- **Method:** Source inspection of `backend/`, `frontend/`, `supabase/migrations/`, `v3_schema.sql`, plus cross-reference against the audit's own evidence (`independent_audit/reports/evidence/*.json`).

---

## Executive Summary

| Classification | Count | Findings |
|---|---|---|
| VERIFIED TRUE | 10 | ARCH-0001, ARCH-0002, DB-0001, API-0001, API-0002, ARCH-0003, SEC-0001, SEC-0003, FE-0003, UX-0001 |
| PARTIALLY TRUE | 5 | API-0003, ARCH-0004, DB-0002, DB-0003, UX-0002 |
| FALSE / AUDIT MISINTERPRETATION | 2 | FE-0002, FE-0004 |
| NOT VERIFIED | 0 | — |
| PO_DECISION REQUIRED | 1 | SEC-0003 (also VERIFIED TRUE as a technical fact) |
| FURTHER INVESTIGATION | 1 | DB-0003 / SEC-0002 (execution-path analysis) |
| Duplicates | 1 | SEC-0002 = same underlying issue as DB-0003 |

**Key cross-cutting findings from verification:**

1. Several "CONFIRMED" findings are technically true but their **impact is overstated** because the audit did not consider compensating controls (e.g., DB-0001: the V3 forensic `audit_trail` is deny-by-default and has *no* RLS policies; SEC-0001: no frontend path queries `calculation_snapshots` directly; UX-0002: production `vercel.json` routes `/admin` to the dedicated admin app).
2. Two findings (FE-0002, FE-0004) are demonstrably **false** — the audit's evidence collector produced an unreliable "unreferenced files" list (it also flagged `public/FaqPage.jsx`, `ContactPage`, `DataSecurity.jsx`, `emailService.js` — all of which are referenced).
3. The API-0003 "600 vs 247 route" comparison is an **apples-to-oranges comparison** (full legacy-app OpenAPI vs modular v3 route count with relative paths).
4. No finding was verified as an **actively exploitable cross-tenant security vulnerability** in the current implementation. The P1 classification is retained only for DB-0001 (legacy audit surface mutability) and re-graded for ARCH-0001/ARCH-0002.

---

## FINDING-BY-FINDING VERIFICATION

### ARCH-0001 — Duplicate SLA settings and Review Queue API routes between v3_review and v3_operations

**Audit classification:** CONFIRMED / P1 / HIGH
**Cline verification classification:** VERIFIED TRUE (technical duplication) — severity re-graded P1 → **P2**

**Evidence inspected:**
- `backend/api/v3_review.py` — `router = APIRouter(prefix="/api/v3/admin")`; routes: `GET/PUT /api/v3/admin/sla/settings` (lines 95–116), `POST /api/v3/admin/review-queue/{review_id}/assign` (line 65), `POST /api/v3/admin/review-queue/{review_id}/complete` (line 80), `GET /review-queue`, `GET /review-queue/{review_id}`.
- `backend/api/v3_operations.py` — `router = APIRouter(prefix="/api/v3/ops")`; routes: `GET/PUT /api/v3/ops/sla/settings` (lines 1794, 1811), `POST /api/v3/ops/review/{review_id}/assign` (line 1723), `POST /api/v3/ops/review/{review_id}/complete` (line 1752).
- `backend/api/router.py` lines 188, 203 — **both routers are mounted** in the v2.1 router.
- `frontend/src/v3/api.js` lines 685, 696, 861–865 — frontend consumes **only the `/api/v3/ops/...` surface**.

**Audit claim:** Both modules "define duplicate and overlapping routes such as GET/PUT /sla/settings and POST /review-queue/{review_id}/assign vs POST /review/{review_id}/assign".

**Verification result:** Confirmed. **Nuances the audit omitted:**
- The duplicates are **not URL collisions** — they live under different prefixes (`/api/v3/admin/*` vs `/api/v3/ops/*`).
- The handlers are **not identical**: `v3_operations` enforces staff permissions (`can_review`, `can_manage_staff`), Processing-Entity scoping, and a bounded SLA write (`sla_hours` only); `v3_review` enforces only `require_admin()` and allows writes to all queue-settings fields.
- The frontend has **one consumer** (the `/api/v3/ops/*` surface); `v3_review.py` is a "V3 legacy-capability reimplementation" with **no frontend consumer**.

**Impact:** Maintainability/divergence risk (the two surfaces *already* differ in authorization strictness and write surface); not an active authorization conflict.

**Existing controls:** The more restrictive surface is the one consumed by the UI; both route sets funnel into the same repositories.

**Recommended eventual action (NOT YET APPROVED):** Designate one canonical surface (evidence points to `/api/v3/ops/*`), deprecate the other after confirming no external/legacy API clients rely on it. Risk: any client using `/api/v3/admin/*` would break; requires API-contract review first.

**Confidence:** HIGH

---

### ARCH-0002 — Dual extraction and processing workflow routes across v3_operations and v3_processing_workflow

**Audit classification:** CONFIRMED / P1 / HIGH
**Cline verification classification:** VERIFIED TRUE (route duplication) — severity re-graded P1 → **P2**

**Evidence inspected:**
- `backend/api/v3_operations.py` (`prefix="/api/v3/ops"`): `POST /items/{item_id}/start` (1372), `/extract` (1401), `/map` (1420), `/validate` (1444), `/calculate` (1481), `/qc` (1574); entity-scoped twins `POST /entities/{entity_id}/extraction/items/{item_id}/...` (882–950).
- `backend/api/v3_processing_workflow.py` (`prefix="/api/v3/processing"`): `POST /items/{item_id}/start` (319), `/extract` (344), `/map` (359), `/validate` (387), `/calculate` (437).
- Both mounted in `backend/api/router.py` (lines 194, 203).
- `frontend/src/v3/api.js` — **both surfaces are consumed**: `/api/v3/processing/items/{id}/...` (lines 1292–1306, customer/consultant workspace) and `/api/v3/ops/items/{id}/...` (lines 642–669, ops workspace).

**Audit claim:** Both modules "expose duplicate item lifecycle endpoints (POST /items/{item_id}/start, /extract, /map, /validate, /calculate)".

**Verification result:** Confirmed. **Business-logic differences are significant:**
- `v3_operations`: `require_staff` + `can_process`/`can_review` permission checks, operator-batch gating, entity scoping.
- `v3_processing_workflow`: `require_auth()` + org-membership item check — a customer/consultant-facing surface.
- Both reuse the same repositories (`manual_extraction`) and validation engine; the **authorization model differs** (internal staff+entity vs org member).

**Impact:** Genuine dual maintenance and divergent authorization semantics for the same logical verbs. The `/api/v3/processing/*` surface is *org-scoped*, `/api/v3/ops/*` is *entity-scoped* — these may be intentional two-actor surfaces, but the near-identical path shape is a maintenance hazard.

**Recommended eventual action (NOT YET APPROVED):** Decide whether the two actor surfaces are product-required. If yes, differentiate paths semantically and document the authorization contract; if no, consolidate onto one router. Requires PO/architecture sign-off.

**Confidence:** HIGH



### DB-0001 — Audit and activity logs permit UPDATE and DELETE operations by regular authenticated organization members

**Audit classification:** CONFIRMED / P1 / HIGH
**Cline verification classification:** VERIFIED TRUE — severity **P1 retained** (with compensating-control nuance)

**Evidence inspected:**
- `v3_schema.sql` lines 4941–4953: `audit_logs_tenant_delete`, `audit_logs_tenant_update`, etc. — `FOR ... TO "authenticated"` with `USING is_org_member(organization_id)`.
- `independent_audit/reports/evidence/db_rls.json` (live DB): identical policy shapes on `activity_logs`, `activity_feed`, `document_activity_log`.
- `supabase/migrations/00000000000000_init_schema.sql` lines 1647–1727: table definitions.
- `backend/data/audit.py`: the V3 backend writes its audit records to **`public.audit_trail`** (lines 138, 247, 283) via the service-role pool.

**Audit claim:** "RLS policies 'audit_logs_tenant_update' and 'audit_logs_tenant_delete' (and corresponding policies on 'activity_logs') allow any authenticated user who passes is_org_member(organization_id) to update and delete audit log rows."

**Verification result:** **Confirmed exactly as stated.** Any `authenticated` org member can `UPDATE`/`DELETE` their org's rows in `audit_logs`, `activity_logs`, `activity_feed`, and `document_activity_log` directly through Supabase (the frontend ships a user-scoped Supabase client, so this is a real reachable path).

**Compensating controls the audit did not consider:**
- `audit_trail`, `processing_audit_trail`, `review_audit_trail` have **no RLS policies at all** (verified absent from the 60 policy-bearing tables in `db_rls.json`) → deny-by-default → the **V3 forensic audit trail is immutable** to authenticated users.
- The operational audit trail is written through the backend service-role path (RLS bypassed by design); an admin delete path exists (`data/audit.py:309`) and is service-role gated.
- The mutable tables are the **legacy org-scoped** log surface; `activity_feed` UPDATE has a plausible legitimate use (mark-as-read).

**Impact:** Real integrity risk on the legacy audit/activity surface. Does **not** extend to the V3 `audit_trail`.

**Recommended eventual action (NOT YET APPROVED):** Drop the UPDATE/DELETE policies on `audit_logs`, `activity_logs`, `document_activity_log` (audit `activity_feed` DELETE; keep a bounded UPDATE for read-flagging if needed), or migrate consumers to the immutable `audit_trail`. Confirm no legacy workflow legitimately mutates these tables; re-verify the service-role path is unaffected.

**Confidence:** HIGH

---

### API-0001 — HTTP 403 Forbidden returned instead of 401 Unauthorized for missing authentication credentials

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** VERIFIED TRUE — severity **P2 retained**

**Evidence inspected:**
- `backend/auth.py` line 129: `security = HTTPBearer()` — default `auto_error=True`.
- `backend/auth.py` lines 175–210: `get_current_user` raises `HTTP_401_UNAUTHORIZED` for invalid tokens.
- `backend/api/router.py` `http_exception_handler`: adds `WWW-Authenticate: Bearer` **only** for 401.
- `independent_audit/reports/evidence/api_probes.json`: unauthenticated `POST /api/v3/organizations` → `403 {"error":{"code":403,"message":"Not authenticated"}}`; `GET /api/v2/admin/audit` → 403 same body (Starlette `HTTPBearer` auto-error for a **missing** header, raised before `get_current_user`).

**Audit claim:** Unauthenticated requests return 403 "Not authenticated" instead of 401.

**Verification result:** Confirmed. **Missing** header → 403 "Not authenticated" (no `WWW-Authenticate`); **invalid** token → 401 with `WWW-Authenticate: Bearer`. Status semantics are inconsistent between the two cases. The audited probes hit the legacy `main.py` app envelope, but the same `HTTPBearer` dependency governs the v2.1 router app.

**Impact:** API-contract/standards issue; clients cannot cleanly distinguish "not authenticated" from "authenticated but forbidden". Not a security boundary failure (the request is rejected either way).

**Recommended eventual action (NOT YET APPROVED):** `HTTPBearer(auto_error=False)` and raise explicit `401` with `WWW-Authenticate: Bearer` when credentials are absent. Compatibility risk: any client relying on 403-for-unauth (including legacy frontend paths) must be checked first.

**Confidence:** HIGH

### API-0002 — Missing root GET endpoint on `/api/v3/organizations` causes 405 Method Not Allowed

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** VERIFIED TRUE (technical claim) — severity re-graded P2 → **P3 / INFO** (no consumer; likely intentional)

**Evidence inspected:**
- `backend/api/v3_organizations.py` — `router = APIRouter(prefix="/api/v3/organizations")`; routes include `POST ""` (103), `GET /{org_id}` (398), `GET/PUT /{org_id}/profile|metadata`, `GET/POST /{org_id}/members`, `GET/POST /{org_id}/facilities`, `GET/POST /{org_id}/assets`. **No root `GET ""` handler.**
- `independent_audit/reports/evidence/api_probes.json`: `GET /api/v3/organizations` → **405** `{"detail":"Method Not Allowed"}` (the path exists for POST, so FastAPI returns 405 rather than 404).
- `frontend/src/v3/api.js`: organisation enumeration is done via `GET /api/v3/ops/organizations` (line 506) and `/api/v3/me/context`; all `/api/v3/organizations/*` calls are parameterized. **No consumer calls the root GET.**

**Audit claim:** "GET /api/v3/organizations returns HTTP 405 Method Not Allowed because v3_organizations.py only implements POST / (create) and parameterized GET /{org_id} routes without a root GET collection handler."

**Verification result:** Confirmed exactly. The endpoint is intentionally absent: collection listing lives on the ops surface (`/api/v3/ops/organizations`), and the V3 frontend does not require it.

**Impact:** Negligible in the current product — no UI or documented client depends on root GET collection enumeration.

**Existing controls:** `/api/v3/ops/organizations` provides collection listing; `/api/v3/me/context` resolves the actor's organisations.

**Recommended eventual action (NOT YET APPROVED):** If a public organisation-collection endpoint is desired, add `GET /api/v3/organizations` (org-scoped listing) or explicitly document that enumeration lives at `/api/v3/ops/organizations`. Low priority.

**Confidence:** HIGH

---

### API-0003 — Substantial contract divergence between OpenAPI specification and implemented v3 source routes

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** PARTIALLY TRUE — severity re-graded P2 → **P3**

**Evidence inspected:**
- `backend/main.py` (legacy app, title "CarbonTally API v3.0.0", root `/` reports `routes_count: 621`) — mounts the legacy `routes/*` routers **and** the V3 router alongside ("Mounted alongside the legacy surface during the transition").
- `backend/main_v2.py` / `backend/api/router.py` `create_app()` — the v2.1-only app with `openapi_url="/api/v2/openapi.json"`, `docs_url="/api/v2/docs"`.
- `independent_audit/reports/evidence/api_probes.json`: `/openapi.json` returns the **legacy** app document (paths include `/api/waitlist/`, legacy admin, etc.).
- `independent_audit/reports/evidence/api_contract_diff.json`: `source_route_count: 247` (modular `api/*.py` routes, relative paths) vs `openapi_path_count: 600`; the "declared_but_not_in_openapi" list is composed of **router-relative paths** (e.g. `DELETE /assets/{asset_id}`, `GET /me/context`) compared without their `/api/v3/...` prefixes.

**Audit claim:** "The OpenAPI document contains 600 paths with legacy unversioned v1/v2 paths ... while the core application source registers 247 modular routes across v3_*.py files, resulting in extensive mismatch."

**Verification result:** The **600 vs 247 comparison is not apples-to-apples**: 600 is the *legacy app's* full path count (legacy + v3 mounted), 247 is a *subset* (modular v3 files, relative paths). FastAPI auto-generates `/openapi.json` from the routers actually mounted in the running app, so the document *does* reflect the implemented routes of the app it was fetched from. The "declared_but_not_in_openapi" entries are largely a prefix-matching artifact (the same paths appear under their full `/api/v3/...` prefix in the OpenAPI). What is genuinely true: the served OpenAPI **intentionally documents both legacy and V3 surfaces** during the documented transition, and a second, v2.1-only OpenAPI exists at `/api/v2/openapi.json` — so integrators have two contracts to reconcile.

**Impact:** Documentation complexity and integration friction for external API consumers; not an inaccuracy that causes runtime failures.

**Recommended eventual action (NOT YET APPROVED):** Publish the v2.1 app's OpenAPI (`/api/v2/openapi.json`) as the canonical contract, and either scope the legacy app's `/openapi.json` or document the coexistence explicitly. Requires a decision on the legacy-to-V3 transition plan.

**Confidence:** HIGH



### ARCH-0003 — Legacy and V3 frontend component coexistence with fragmented API calling patterns

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** VERIFIED TRUE — severity **P2 retained** (technical-debt)

**Evidence inspected:**
- `frontend/src/App.js` imports and renders legacy components alongside V3: `PDFIngestionPortal` (line 1780), `UploadManager`/`BulkUpload` (1811–1826), `TeamManagement` (1839), `AssetManager` (1843), `ManualEntryStandalone` (1852), inside the legacy dashboard area.
- `frontend/src/v3/api.js` is the centralized V3 client (`v3Fetch` with auth header handling).
- `frontend/src/AssetManager.js`, `PDFIngestionPortal.jsx`, `BulkUpload.jsx`, `TeamManagement.js`, `UploadManager.js`, `components/PDFRepairTool.js`, `components/ActivityFeed.jsx`, `components/DashboardSummary.jsx`, `components/DocumentStatus.jsx`, `components/ManualEntryStandalone.jsx`, `components/StaffPresence.jsx` — all contain direct `fetch(...)`/`axios`/local `API_URL` usage (verified by grep; `v3/api.js` line 94 still contains a legacy `${API_URL}/api/organizations/...` call).

**Audit claim:** "Legacy standalone components (AssetManager.js, PDFIngestionPortal.jsx, BulkUpload.jsx, TeamManagement.js, UploadManager.js) execute direct fetch/axios calls with localized API_URL definitions alongside the V3 centralized api client."

**Verification result:** Confirmed. Legacy components are still reachable (rendered in the App.js legacy dashboard surface), use direct `fetch`/`axios` with local `API_URL` constants, while V3 pages funnel through `v3/api.js`. This is the documented transitional state (backend `main.py`: "Mounted alongside the legacy surface during the transition"; the same pattern on the frontend).

**Impact:** Real technical debt: inconsistent header/auth/error handling across legacy vs V3 networking, and duplicated API base-URL definitions.

**Existing controls:** The V3 authenticated surfaces (the product's primary operational UI) all use `v3/api.js`; the legacy components are confined to the legacy dashboard/power-user area.

**Recommended eventual action (NOT YET APPROVED):** Migrate remaining legacy views to the V3 architecture and funnel all HTTP through `v3/api.js` as part of the transition plan. Not an urgent defect.

**Confidence:** HIGH

---

### ARCH-0004 — Database schema redundancy across audit and activity tracking tables

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** PARTIALLY TRUE — severity re-graded P2 → **P3**

**Evidence inspected:**
- `supabase/migrations/00000000000000_init_schema.sql`: `processing_audit_trail` (914), `audit_logs` (1647), `audit_trail` (1669), `activity_logs` (1687), `activity_feed` (1704), `document_activity_log` (1716), `review_audit_trail` (1870); plus `processing_logs` (1731), `reassignment_history` (930), `review_assignment_history`.
- `backend/data/audit.py`: the V3 API audit repository reads/writes **`audit_trail`**.
- `independent_audit/reports/evidence/db_rls.json`: only 4 of these tables carry tenant policies (`audit_logs`, `activity_logs`, `activity_feed`, `document_activity_log`); the workflow trails have none.

**Audit claim:** "The database contains multiple fragmented audit tables (audit_logs, audit_trail, processing_audit_trail, review_audit_trail) and over eight distinct activity log tables."

**Verification result:** The **count of tables is accurate** (≈10 audit/activity/history tables). The **"redundancy" conclusion is not established**: the tables have distinct schemas and purposes — org-scoped legacy action logs (`audit_logs`, `activity_logs`, `activity_feed`, `document_activity_log`), a generic record-level V3 audit trail (`audit_trail`, written by the backend service role), and workflow-specific trails (`processing_audit_trail`, `review_audit_trail`). Consolidation is an opinion, not a demonstrated defect; a single `audit_events` table would change retention and RLS semantics for each domain.

**Impact:** Maintainability/storage complexity; no functional or security impact demonstrated.

**Recommended eventual action (NOT YET APPROVED):** If consolidation is ever pursued, it must be a deliberate migration with per-domain retention mapping and RLS redesign — not a merge of equal tables. Low priority; requires architecture review.

**Confidence:** HIGH

### DB-0002 — Nullable organization_id column on tenant-scoped tables creates isolation and orphan risks

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** PARTIALLY TRUE — severity re-graded P2 → **P3**

**Evidence inspected:**
- `independent_audit/reports/evidence/db_schema.json` (live DB): `assets.organization_id` `is_nullable: "YES"`; `activity_feed.organization_id` `is_nullable: "YES"`; `audit_logs.organization_id` `is_nullable: "YES"`; by contrast `calculation_snapshots.organization_id` is `"NO"`.
- `supabase/migrations/00000000000000_init_schema.sql` lines 1704–1712 (`activity_feed`), assets table definition — columns declared nullable.
- `backend/api/v3_organizations.py` `POST /{org_id}/assets` — the V3 insertion path derives `organization_id` from the URL path parameter (always set).
- `independent_audit/reports/evidence/db_integrity.json` — orphan checks for `assets.organization_id → organizations.id` report `orphans_found: false` (no dangling FK rows; NULL rows are not captured by that check).

**Audit claim:** "columns assets.organization_id and activity_feed.organization_id have is_nullable set to 'YES'" and "records inserted without an organization_id will fail is_org_member(organization_id), leading to inaccessible orphaned records."

**Verification result:** The **nullability facts are confirmed** (and extend further than the audit stated — `audit_logs.organization_id` is also nullable). The **orphan-risk impact is plausible but not demonstrated**: no NULL/orphan rows were found by the integrity collector, and modern V3 insertion paths always set the org id (path-derived). NULL is arguably meaningful for legacy/system-global events in `activity_feed`/`audit_logs`.

**Impact:** Latent data-integrity risk only if a future insert path omits the org id; no current cross-tenant leak or orphan population demonstrated.

**Recommended eventual action (NOT YET APPROVED):** Enforce NOT NULL on `assets.organization_id` (all asset records are tenant-scoped by design), and decide per-table whether NULL has semantic meaning (e.g. system events in `activity_feed`/`audit_logs`) before changing. Requires schema-change approval and a NULL-data audit.

**Confidence:** HIGH

---

### DB-0003 — Row Level Security forced flag is disabled across all database tables

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** PARTIALLY TRUE (configuration fact) — no exploitable path demonstrated; severity P2 → **P3 / further investigation**

**Evidence inspected:**
- `independent_audit/reports/evidence/db_rls.json` (live DB): every audited table has `rls_enabled: "t"`, `rls_forced: "f"` (84 tables).
- No `ALTER TABLE ... FORCE ROW LEVEL SECURITY` anywhere in `supabase/migrations/*.sql` or `v3_schema.sql`.
- `backend/infra/supabase.py`: the backend repository layer connects via the **service-role database role (the `postgres` superuser)**, which "bypasses RLS like the service-role client" — a documented, deliberate design.
- `backend/api/dependencies.py` + `backend/auth.py`: every repository call behind a FastAPI route is preceded by explicit application-level authorization (`require_auth`/`require_org_member`/`require_staff`/`require_admin`/`ensure_org_access`).

**Audit claim:** "All tables in db_schema and db_rls show rls_forced: 'f' despite having rls_enabled: 't'" and "any query running under the table owner role or via SECURITY DEFINER functions without explicit user context bypasses RLS policies unintentionally."

**Verification result:** The configuration observation is **true**. The **security conclusion is not demonstrated**: RLS applies to the `authenticated`/`anon` roles used by the Supabase JS client (frontend direct access); those roles are not the table owner, so RLS is enforced for them regardless of FORCE. FORCE RLS only changes behaviour for **table-owner** connections — and the only owner-role path is the backend service-role pool, which is (a) a deliberate design choice documented in `infra/supabase.py`, and (b) protected by the FastAPI authorization layer. No SECURITY DEFINER function was identified that executes without its own authorisation (the RLS helper functions `is_org_member`/`is_org_consultant` are SECURITY DEFINER but only gate RLS policy evaluation; they do not expose owner-privileged queries).

**Impact:** Without a demonstrated owner-role execution path that skips application authorization, this is defense-in-depth hardening, not a current vulnerability.

**Recommended eventual action (NOT YET APPROVED):** As defense-in-depth, evaluate `ALTER TABLE ... FORCE ROW LEVEL SECURITY` on tenant tables — but ONLY after confirming the backend service-role path cannot be affected (FORCE does not alter service-role/owner bypass for the *owner* role unless the owner role is also the connection role; in Supabase the service role *is* effectively the owner, so FORCE could break the backend's documented RLS-bypass repository layer). This requires a security architecture decision, not a mechanical migration.

**Confidence:** MEDIUM


### FE-0002 — Navigation Mismatch to Unregistered Route /dashboard in BetaLogin

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** FALSE / AUDIT MISINTERPRETATION — severity P2 → **cosmetic (drop or P3)**

**Evidence inspected:**
- `frontend/src/BetaLogin.jsx` lines 28, 85, 148: `navigate('/dashboard');`
- `frontend/src/App.js` line 2020: `<Route path="/dashboard/*" element={<Navigate to="/home" replace />} />`
- `frontend/src/App.js` line 2217: `<Route path="*" element={<Navigate to="/" replace />} />`

**Audit claim:** "BetaLogin.jsx initiates navigation to exact route '/dashboard', whereas the route table only defines wildcard route '/dashboard/*' and '/home' ... may fail route exact matching."

**Verification result:** **Not broken.** React Router v6/v7 splat matching (`path="/dashboard/*"`) matches `/dashboard` with an empty splat, so the navigation is handled and **redirects to `/home`** — the intended customer dashboard. The audit's own wording ("may fail") is speculative and the browser evidence does not demonstrate a failure. The only real observation is that `BetaLogin` navigates to a redirect route rather than `/home` directly — a cosmetic redundancy.

**Impact:** None demonstrated. Users land on `/home`.

**Recommended eventual action (NOT YET APPROVED):** Optionally point `navigate('/home')` directly to remove the redundant redirect hop. Not required.

**Confidence:** HIGH

---

### SEC-0001 — Calculation Snapshots RLS Policy Excludes Consultants from Direct Read Access

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** VERIFIED TRUE (policy-inconsistency fact) — impact limited; severity re-graded P2 → **P3**

**Evidence inspected:**
- `supabase/migrations/20260807070000_add_new_table_rls.sql` lines 70–74: `calc_snapshots_select_own ... FOR SELECT TO authenticated USING (public.is_org_member(organization_id))`.
- `independent_audit/reports/evidence/db_rls.json`: same policy in the live DB.
- Sibling tables **do** include the consultant predicate: `emissions_logs`, `assets`, `facilities`, `customer_factors` SELECT policies all use `(is_org_member(organization_id) OR is_org_consultant(organization_id))`.
- `supabase/migrations/20260803000000_rc2_rls.sql` lines 85–106: `is_org_consultant(p_org)` — SECURITY DEFINER function resolving ACTIVE consultant-firm membership via `consultant_firm_members.client_access` or a live `consultant_clients` link.
- `frontend/src/v3/*`: **no direct Supabase query against `calculation_snapshots`** (verified: no `from('calculation_snapshots')` anywhere); all snapshot data flows through the backend API (`/api/v3/...`), which uses the service-role pool.

**Audit claim:** "The calc_snapshots_select_own policy on calculation_snapshots checks only is_org_member(organization_id), denying read access to authorized consultants."

**Verification result:** Confirmed as a **policy inconsistency** with sibling tables. **Impact assessment differs**: consultants already access calculation data through the backend API layer (service-role), so no product workflow is currently blocked; the RLS restriction only affects hypothetical *direct* Supabase REST reads by a consultant — which fail **closed** (conservative), not open. There is no security impact from denying; at most a functional/consistency gap.

**Existing controls:** Backend API layer (`v3/api.js` + FastAPI) is the actual data-access path for consultants; RLS direct-table access is not used by the UI.

**Recommended eventual action (NOT YET APPROVED):** For policy consistency, extend `calc_snapshots_select_own` to `(is_org_member(organization_id) OR is_org_consultant(organization_id))` — but confirm whether consultants should have *direct* table reads at all (the safer posture is to keep direct access restricted and route consultants through the API). Requires an RLS/security decision.

**Confidence:** HIGH


### SEC-0002 — Row Level Security Enabled Without Table-Level FORCE Option

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** **DUPLICATE of DB-0003** — same underlying issue; not double-counted. PARTIALLY TRUE (see DB-0003 analysis).

**Verification result:** SEC-0002 and DB-0003 are the same technical claim (all RLS-enabled tables have `rls_forced = 'f'`). Cross-checked against the same evidence (`db_rls.json`). The two findings should be merged in any future remediation tracking. See the DB-0003 section for the full analysis — the configuration fact is true; an exploitable owner-role bypass path is not demonstrated; the backend service-role design and FastAPI authorization layer are the relevant compensating controls.

**Confidence:** MEDIUM

---

### SEC-0003 — Permissive Delete Policy on consultant_clients Allows Unilateral Deletion by Client Organization Members

**Audit classification:** PO_DECISION / P2 / HIGH
**Cline verification classification:** VERIFIED TRUE (policies exist exactly as claimed) **and PO_DECISION REQUIRED** — severity **P2 retained as a product decision**

**Evidence inspected:**
- `v3_schema.sql` line 4998: `CREATE POLICY "consultant_clients_tenant_delete" ON "public"."consultant_clients" FOR DELETE TO "authenticated" USING (is_org_member(organization_id))`.
- `supabase/migrations/20260803000000_rc2_rls.sql` lines 369–370 and `20260822000000_p9_rls_recursion_fix.sql` lines 103–104: `cc_delete_own_firm` (requires `is_consultant_firm_manager(consultant_id)`).
- `independent_audit/reports/evidence/db_rls.json`: both DELETE policies confirmed live.

**Audit claim:** "consultant_clients has two permissive DELETE policies: cc_delete_own_firm (requiring is_consultant_firm_manager) and consultant_clients_tenant_delete (requiring only is_org_member). Any member of the client organization can delete the consultant linkage."

**Verification result:** Confirmed exactly. Any `authenticated` member of the client organisation (Owner, Admin, **Member**, Viewer — the predicate is org membership, not a role) can `DELETE` the `consultant_clients` row linking their org to a consultant firm. The consultant side requires firm-manager authority; the client side has **no role restriction**.

**Product context:** AGENTS.md §11 defines the consultant–client relationship lifecycle (a client may leave a consultant; data is preserved and consultant access revoked) but does **not** ratify which client roles may initiate termination. §9 distinguishes Customer Owner/Admin/Member/Viewer capabilities. There is therefore a genuine, unanswered product question.

**Impact:** If the intended rule is "relationship termination is a customer-admin action", this is an authorization gap (Member/Viewer can sever the relationship). If the intended rule is "any client user may leave the consultant", it is correct. This is precisely why the audit classified it PO_DECISION.

**Recommended eventual action (PO DECISION REQUIRED, NOT YET APPROVED):** Ratify the role(s) allowed to terminate a consultant relationship. Options: (a) restrict `consultant_clients_tenant_delete` to customer Owners/Admins (e.g. via an org-role helper), or (b) confirm the current permissive behaviour. If restricted, verify the frontend "end relationship" lifecycle flow still works for the authorised roles and that the consultant-side `cc_delete_own_firm` path is unaffected.

**Confidence:** HIGH


### UX-0002 — Unmatched /admin route silently falls back to public marketing landing page

**Audit classification:** CONFIRMED / P2 / HIGH
**Cline verification classification:** PARTIALLY TRUE — severity re-graded P2 → **P3** (production routing mitigates)

**Evidence inspected:**
- `frontend/src/App.js`: no `/admin` route registered; the catch-all `<Route path="*" element={<Navigate to="/" replace />} />` (line 2217) sends `/admin` → `/` → `LandingPage` in the main app / local dev server.
- `vercel.json` (production): rewrites `/admin` and `/admin/(.*)` → `/admin/index.html` (the **separate admin CRA application** in `admin/`).
- `admin/` is a standalone CRA app (`admin/src/App.js`, `admin/src/pages/staff/StaffDashboard.js`, own package.json with react-table/react-select/react-hook-form).

**Audit claim:** "Navigating to /admin renders the public pre-launch landing page ... without indicating the route was invalid or restricted" (reproduction was on `localhost:3000`).

**Verification result:** Partially correct. In the **local dev server / main frontend app**, `/admin` matches the wildcard and lands on the marketing page. In **production**, `vercel.json` explicitly routes `/admin` to the dedicated admin console — the intended administrative surface exists and is served at `/admin`. The audit's browser evidence was captured against the dev topology and did not account for the production rewrites.

**Impact:** Developer/operator confusion in the dev environment; the intended admin console is reachable in production. Not a security issue (the admin app has its own auth).

**Recommended eventual action (NOT YET APPROVED):** Optionally add an explicit `/admin` route in the main app that renders a clear "Admin console is a separate application — sign in at the admin portal" notice (or redirects per environment), instead of silently falling to the landing page. Purely UX polish.

**Confidence:** HIGH

---

### FE-0003 — Dead UI / Unreferenced Legacy Component StaffDashboard.jsx

**Audit classification:** CONFIRMED / P3 / HIGH
**Cline verification classification:** VERIFIED TRUE — severity **P3 retained**

**Evidence inspected:**
- `frontend/src/StaffDashboard.jsx` — contains a **locally-defined** `ManualExtractionForm` component (line 140) inside the same file.
- Repo-wide reference search: `StaffDashboard` matched only `frontend/src/StaffDashboard.jsx` (self) and **`admin/src/pages/staff/StaffDashboard.js` + `admin/src/App.js`** — a *different* file in the separate admin app (which is referenced by the admin router).
- No import/route/test reference to `frontend/src/StaffDashboard.jsx` exists in the frontend.

**Audit claim:** "StaffDashboard.jsx and ManualExtractionForm are unreferenced across the application while v3/ops components handle operations workflows."

**Verification result:** Confirmed for `frontend/src/StaffDashboard.jsx`. Note the audit's phrasing slightly misleads: `ManualExtractionForm` is **not a separate unreferenced file** — it is a local component defined *within* `StaffDashboard.jsx`, so both die together. The separate `admin/src/pages/staff/StaffDashboard.js` is a different, live component and must not be confused with this finding.

**Impact:** Dead code / maintenance clutter only (P3 appropriate).

**Recommended eventual action (NOT YET APPROVED):** Remove `frontend/src/StaffDashboard.jsx` (and its local `ManualExtractionForm`) once confirmed unreferenced; do **not** touch `admin/src/pages/staff/StaffDashboard.js`.

**Confidence:** HIGH

---

### FE-0004 — Unreferenced Legacy Contexts and Hooks (RealtimeContext, useNotifications, useManualEntry)

**Audit classification:** CONFIRMED / P3 / MEDIUM
**Cline verification classification:** FALSE / AUDIT MISINTERPRETATION (collector artifact) — severity **drop (not a real finding)**

**Evidence inspected:**
- `frontend/src/App.js` line 80: `import { RealtimeProviderWrapper, useRealtime, useNotifications, useMessageCount } from './context/RealtimeContext';` and line 1649: `const { user: realtimeUser } = useRealtime();`
- `frontend/src/App.js`: imports and uses `ReferenceDataContext` (`ReferenceDataProvider`).
- `frontend/src/hooks/useDocumentLogging.js` — referenced by `frontend/src/UploadManager.js`.
- `frontend/src/hooks/useManualEntry.js` — referenced by `frontend/src/components/ManualEntry.jsx` (import + use at line 23).
- `frontend/src/hooks/useNotifications.js` — referenced by `App.js`, `context/RealtimeContext.jsx`.
- `independent_audit/reports/evidence/frontend_dead_ui.json` — the collector's "unreferenced_file_candidates" list also contains clearly-referenced files: `DataSecurity.jsx`, `public/FaqPage.jsx`, `public/ContactPage.jsx`, `public/PlatformPage.jsx`, `services/emailService.js`, `v3/NotificationsPage.jsx`, etc. → the heuristic is unreliable.

**Audit claim:** "RealtimeContext.jsx, ReferenceDataContext.jsx, useNotifications.js, and useDocumentLogging.js appear in the unreferenced file list."

**Verification result:** **Every named file is referenced and active** in the legacy application surface. The finding rests on the collector's flawed "unreferenced" heuristic, which is contradicted by direct reference checks. (The audit's reproduction note "check usage in active v3 components" subtly narrows the claim to the V3 surface — trivially true and not the finding's headline.)

**Impact:** None. No dead-code claim survives verification.

**Recommended eventual action:** None. Do not act on FE-0004. If legacy-context consolidation is ever desired (realtime/notifications on the V3 surface), that is a separate, deliberate piece of work — not justified by this finding.

**Confidence:** HIGH


### UX-0001 — DataSecurity component links to non-existent route /privacy-policy instead of /privacy

**Audit classification:** CONFIRMED / P3 / HIGH
**Cline verification classification:** VERIFIED TRUE — severity **P3 retained**

**Evidence inspected:**
- `frontend/src/DataSecurity.jsx` line 441: `<Link to="/privacy-policy" className="btn-outline">` (also links `/contact` at line 438).
- `frontend/src/App.js`: only `<Route path="/privacy" element={<PrivacyPolicy />} />` (line 1997) is registered; there is **no `/privacy-policy` route or alias**.
- `frontend/src/App.js` line 2217: catch-all `<Route path="*" element={<Navigate to="/" replace />} />` → any click on `/privacy-policy` redirects to `/` (the public landing page), not the privacy policy.

**Audit claim:** "DataSecurity.jsx contains a navigation link to '/privacy-policy' which is not defined in frontend routes (where only '/privacy' is registered)."

**Verification result:** Confirmed exactly. Users clicking the "Privacy Policy" button from the DataSecurity view are redirected to the marketing landing page instead of the privacy terms. Minor, real UX defect. (The audit's merged FE-0001 duplication was correctly handled.)

**Impact:** Broken navigation link on a secondary informational page; no functional or security impact.

**Recommended eventual action (NOT YET APPROVED):** Change the link target to `/privacy` (or register `/privacy-policy` as an alias route). Trivial, low-risk fix.

**Confidence:** HIGH



## FINAL SUMMARY

### Verification counts (18 findings)

1. **VERIFIED TRUE: 10** — ARCH-0001, ARCH-0002, DB-0001, API-0001, API-0002, ARCH-0003, SEC-0001, SEC-0003, FE-0003, UX-0001
2. **PARTIALLY TRUE: 5** — API-0003, ARCH-0004, DB-0002, DB-0003, UX-0002
3. **NOT VERIFIED: 0**
4. **FALSE / AUDIT MISINTERPRETATION: 2** — FE-0002, FE-0004
5. **EXPECTED / INTENTIONAL: 0** as a primary classification (several verified findings are intentionally transitional, e.g. ARCH-0003 legacy coexistence, API-0002 absent endpoint)
6. **PO DECISIONS REQUIRED: 1** — SEC-0003 (also counted in VERIFIED TRUE as a technical fact)
7. **FURTHER INVESTIGATION REQUIRED: 1** — DB-0003 / SEC-0002 (owner-role execution-path analysis before any FORCE RLS decision)

### Duplicate findings
- **SEC-0002 ≡ DB-0003** — identical underlying claim (RLS enabled, FORCE off). Must not be double-counted in remediation. The audit produced both because two investigators (security_agent, db_agent) independently reported the same condition.

### Severity re-gradings (all opinion, for eventual triage)
- **P1 → P2:** ARCH-0001, ARCH-0002 (duplication is real; not an active authorization conflict; consumers use one surface)
- **P1 retained:** DB-0001 (legacy audit mutability)
- **P2 → P3:** API-0002, API-0003, ARCH-0004, DB-0002, DB-0003, SEC-0001, UX-0002
- **P2 → drop:** FE-0002 (false), FE-0004 (false)
- **Retained as-is:** API-0001 (P2), ARCH-0003 (P2), SEC-0003 (P2 + PO), FE-0003 (P3), UX-0001 (P3)

---

## PROPOSED REMEDIATION ORDER

Ranked only for findings sufficiently verified to justify eventual remediation. **None of this is approved; nothing was implemented.**

### A. Security / data integrity
1. **DB-0001** (P1) — Remove/replace UPDATE & DELETE RLS policies on `audit_logs`, `activity_logs`, `document_activity_log` (and review `activity_feed` DELETE; keep a bounded UPDATE for read-flagging), or migrate consumers to the immutable `audit_trail`. Verify no legacy workflow mutates these tables and that the service-role backend path is unaffected.
2. **SEC-0003** (P2, PO DECISION) — Ratify which client-organisation roles may terminate a consultant relationship; if restricted to Owner/Admin, tighten `consultant_clients_tenant_delete` accordingly.
3. **DB-0003 / SEC-0002** (P2→P3) — Security-architecture review of FORCE RLS as defense-in-depth. Only after demonstrating (or eliminating) any owner-role execution path that skips application authorization. Beware interaction with the documented service-role repository layer.
4. **SEC-0001** (P2→P3) — Policy-consistency decision for `calculation_snapshots` SELECT (either add `is_org_consultant` for consistency or deliberately keep consultant access API-only and document why).

### B. Core architecture
5. **ARCH-0001** (P1→P2) — Designate the canonical SLA/review surface (`/api/v3/ops/*` by evidence), deprecate the `/api/v3/admin/*` twins after API-contract check.
6. **ARCH-0002** (P1→P2) — Decide whether the customer/org-scoped (`/api/v3/processing/*`) and ops/entity-scoped (`/api/v3/ops/*`) workflow surfaces are both product-required; if so differentiate and document, if not consolidate.

### C. API correctness
7. **API-0001** (P2) — Return 401 + `WWW-Authenticate: Bearer` for missing credentials (`HTTPBearer(auto_error=False)`); verify no client depends on 403-for-unauth.
8. **API-0003** (P2→P3) — Publish the v2.1 OpenAPI (`/api/v2/openapi.json`) as canonical; document the legacy coexistence explicitly.
9. **API-0002** (P2→P3) — Either add `GET /api/v3/organizations` or document that enumeration lives at `/api/v3/ops/organizations`.

### D. UX / frontend
10. **UX-0001** (P3) — Fix `DataSecurity.jsx` link `/privacy-policy` → `/privacy` (or alias route).
11. **UX-0002** (P2→P3) — Add an explicit `/admin` route in the main app with a clear notice (dev/edge case only; production already serves the admin app via `vercel.json`).

### E. Technical cleanup
12. **ARCH-0003** (P2) — Continue the documented legacy→V3 migration; funnel all HTTP through `v3/api.js`.
13. **ARCH-0004** (P2→P3) — Optional audit-table consolidation; only as a deliberate per-domain migration with retention mapping (not currently justified).
14. **DB-0002** (P2→P3) — Enforce NOT NULL on `assets.organization_id`; audit NULLs in `activity_feed`/`audit_logs` before deciding per-table.
15. **FE-0003** (P3) — Remove dead `frontend/src/StaffDashboard.jsx` (keep `admin/src/pages/staff/StaffDashboard.js`).
16. **FE-0002** (drop) — Optional: navigate directly to `/home` in `BetaLogin.jsx`.

### F. PO decisions
17. **SEC-0003** — Who may terminate a consultant–client relationship (see A.2).
18. (Optional) **ARCH-0002** — Are the customer and ops workflow surfaces both product-required?

### NOT to be actioned (false findings)
- **FE-0004** — RealtimeContext/ReferenceDataContext/useNotifications/useManualEntry/useDocumentLogging are all referenced and live. No action.
- **FE-0002** — navigation works via the `/dashboard/*` redirect. No action required.

---

## FINAL SAFETY CHECK

- **git diff:** only untracked/new deliverable file `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` was created; no tracked application file was modified by this verification.
- **git status:** all working-tree entries are pre-existing (untracked audit/QA/skill directories and prior modifications) — none created or altered by this session. HEAD remains `1639121` (the audited checkpoint).
- **No CarbonTally application files modified** (frontend, backend, schema, migrations, RLS, routes, auth, business logic, configuration).
- **No database migrations executed, no RLS policies changed.**
- **No API/frontend code changed.**
- **No commits or pushes made.**
- Scratch output was written only under `/tmp`.
