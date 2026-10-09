# CT-FEATURE-01 — CarbonTally Complete Feature & Functionality Catalogue

**Task ID:** `CT-FEATURE-01-20260927-CARBONTALLY-COMPLETE-FEATURE-AND-FUNCTIONALITY-CATALOGUE-FROM-SCHEMA-CODE-AND-HISTORICAL-EVIDENCE`
**Type:** READ-ONLY forensic product/architecture discovery — **no implementation, no migration, no seed, no deployment, no push**
**Date:** 2026-09-27
**Canonical tree:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`)
**Historical tree:** `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (branch `main`)
**Companion documents:** configuration catalogue, functionality traceability, feature gap analysis, discovery report (`docs/architecture/CT-PO-CARBONTALLY-*‑20260927.md`)

---

## 0. Reading rules

1. **One row = one feature.** A feature is a product capability a named actor can
   use, configure, or that the platform performs on their behalf. Migration files,
   React components and endpoints are **not** features by themselves.
2. **Sub-capabilities are listed inside the feature**, not split into separate IDs,
   unless the sub-capability has its own actor, its own data object and its own
   lifecycle (the split rule is stated per domain where it was applied).
3. **The truth ladder is preserved.** A feature is never upgraded because a lower
   rung exists:

```
DOCUMENTED ≠ SCHEMA EXISTS ≠ CODE EXISTS ≠ API EXISTS ≠ UI EXISTS ≠ ROUTE WIRED
≠ PERSISTED ≠ TESTED ≠ E2E VERIFIED ≠ INDEPENDENTLY VERIFIED
≠ PRODUCTION AVAILABLE ≠ PRODUCTION VERIFIED
```

4. **`Truth` is one controlled value** per feature (§0.2). Additional columns
   carry the evidence path so the value can be re-tested by another agent.
5. **Deployment state is per environment, not per product.** A feature can be
   `IMPLEMENTED_AND_WIRED` in the release tree and simultaneously **unapplied**
   in every database on this host. The `Deploy` column states where the *data
   model* of the feature was actually found on 2026-09-27 (see §1.4).
6. **No product decision is made here.** Where evidence cannot settle a question
   the row says `UNKNOWN` and the item appears in the gap analysis as
   `PO_DECISION_REQUIRED`. Nothing is recommended, merged, deleted or promoted.

### 0.1 Truth statuses (controlled vocabulary)

`IMPLEMENTED_AND_WIRED` · `IMPLEMENTED_BACKEND_ONLY` · `IMPLEMENTED_FRONTEND_ONLY` ·
`SCHEMA_ONLY` · `API_ONLY` · `DOCUMENTED_ONLY` · `PARTIALLY_IMPLEMENTED` ·
`SUPERSEDED` · `HISTORICAL_ONLY` · `EXPERIMENTAL` · `UNVERIFIED` · `UNKNOWN`

### 0.2 Evidence token legend (used in the `Evidence` column)

| Token | Meaning | Verified how (2026-09-27) |
|---|---|---|
| `DB:<obj>` | database object found in a live local database | read-only `information_schema` / `pg_policies` query |
| `MIG:<file>` | declared by a repository migration | file read; **not** an applied-state claim |
| `BE:<module>` | backend Python module | file listing / targeted grep |
| `API:<prefix or file>(n)` | registered router + endpoint count | `backend/api/*.py`, `backend/routes/**`, `backend/main.py`, `backend/api/router.py` |
| `UI:<file>` | frontend component / route | `frontend/src/**` |
| `AD:<file>` | admin CRA component / route | `admin/src/**` |
| `T:<file>` | test artefact | `backend/tests/**`, `frontend/src/**/__tests__/**`, `admin/src/**`, `qa_harness/**`, `e2e/**` |
| `DOC:<doc>` | project document | `docs/**` in both trees |
| `PROD:<state>` | production evidence state | `PV` proven public, `NOT-DEPLOYED`, `UNKNOWN`, `N/A` (see §1.4) |

### 0.3 Scope disclaimer

The catalogue is complete **as discovery**, not as acceptance. Nothing here is
`INDEPENDENTLY VERIFIED` unless the row names a non-implementer verification
record; nothing is `PRODUCTION VERIFIED` unless the row names direct live
evidence. Production was never contacted by this task.

---

## 1. Summary

| Dimension | Value (2026-09-27) |
|---|---|
| Features catalogued | **354** (`FTR-001` … `FTR-354`) |
| Functional domains | **54** (the 50 of the task taxonomy + 4 evidence-required additions: 51 Design System & UX, 52 Public Website, 53 Deployment & Platform Tooling, 54 Historical/Superseded/Experimental) |
| Configuration options | see `CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` §7 (counting rules there) |
| API surfaces mapped | **59 V3 API modules (370 endpoints)** + legacy routers (**401 endpoints**) + app-level router contract |
| Roles evidenced | 4 customer roles · 6 internal staff roles · PE manager + PE staff · consultant roles/permission flags |
| Admin capabilities | domain 45 (7 features) + domain 01 (20 features) |
| Organization capabilities | domain 04 (11) + domain 05 (5) + domain 06 (7) |
| Consultant capabilities | domains 07 (10) + 08 (5) + 09 (3) |
| Audit capabilities | domain 33 (9) |
| Reporting capabilities | domains 34 (12) + 35 (3) + 36 (8) |
| Historical capabilities | domain 54 (6) + `HISTORICAL_ONLY` entries flagged throughout |
| Schema requirements derived | yes — §4 (input to CT-SCHEMA-01) |

### 1.1 The single most important discovery

The repository contains a complete Phase-8 / P16 / P17 feature surface (V3 API,
React application, admin console, tests, 417 architecture documents), and the
**databases on this host contain materially less than that surface**:

| Database (local Supabase cluster `carbon_ledger`) | public tables | migration ledger | highest applied migration | disclosure schema | Insight schema | P17 schema |
|---|---|---|---|---|---|---|
| `postgres` (flagship: 975 orgs / 7,049 factors / 1,125 members) | 116 | 46 rows | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | absent | absent | absent |
| `ct_local_93d5cdd` (25-org READINESS-02 DB) | 135 | no ledger table | n/a | present | absent | absent |
| `carbontally_qa_phase8` | 133 | 0 rows | n/a | present | absent | absent |
| `carbontally_test` | 117 | no ledger table | n/a | absent | present | absent |
| `ct_p17k_20260926` (disposable P17 clone) | 145 | n/a | n/a | present | present | **present** (P17-A columns, P17-C/D/H tables, 55 `disclosure_requirement_versions` rows) |
| production | never contacted | never contacted | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** |

Consequence for reading this catalogue: **"code exists" is true far more often
than "the product can run it"**. Every Phase-8, P16 and P17 feature below is
`IMPLEMENTED_AND_WIRED` (or `PARTIALLY_IMPLEMENTED`) in the release tree, and
**not** deployable from any non-disposable database on this host.

### 1.2 Second discovery — the `accounting_dimensions` table does not exist

P17 documentation speaks of "accounting dimensions". **No table of that name
exists in any database on this host**, and the P17-A migration
(`20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`) creates
**no table at all**: it adds ten dimension columns to `calculation_snapshots`
and `emissions_logs`, four to `emission_factors`, two to `customer_factors`, two
to `organizations`, plus constraints and indexes. Verified read-only in
`ct_p17k_20260926` (columns present) and absent in the four other DBs tested.
This is **documentation-vs-schema naming drift**, not a schema gap (§5.3).

### 1.3 Third discovery — production is documentary, not verified

The only production facts in evidence are documentary: the public site
`https://carbontally.co.uk`, the API host `https://carbontally-api.onrender.com`
(`/health`, `/openapi.json`), and the verified-`UNKNOWN` production deployment
state recorded in
`docs/verification/CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md` §2–§4.
**No production capability in this catalogue is `PRODUCTION VERIFIED`.**

### 1.4 Deployment vocabulary used in the `Deploy` column

`flagship:NO` absent from `postgres` · `flagship:PRE_P6` present up to the
WS4-Gate-3 ledger row · `local135:YES` in `ct_local_93d5cdd` · `qa133:YES` in
`carbontally_qa_phase8` · `test117:YES` in `carbontally_test` · `p17clone:YES`
only in disposable clone(s) · `PROD:UNKNOWN` production never contacted ·
`n/a` no database object implied.

---

## 2. Method and sources actually inspected

**Repositories** (read-only): `/home/shomonrobie/ct_93d5cdd` (89 migrations;
5,917 backend Python files; 308 `frontend/src` files; 47,873 `admin` files incl.
`node_modules`; 1,081 docs) and `/home/shomonrobie/carbon_tally` (68 migrations;
6,214 backend Python files; 275 `frontend/src` files; historical-only trees —
`tools/`, `agent_swarm/`, `saas-assurance/`, `independent_audit/`,
`website_candidate/`, `carbon-tally-ui-demo/`, `prisma/`, `demodatagen/`).

**Code surfaces enumerated**: `backend/main.py` (legacy mounts L212–259 +
`api_router` L265); `backend/api/router.py`; `backend/api/*.py` (59 modules,
370 endpoints); `backend/routes/**` (401 endpoints incl. `admin/` 16 files,
`organizations/` 11 files); `backend/domain/**` (57 modules);
`backend/engines/**` (16); `backend/services/**` (28); `backend/data/**` (54
repositories); `backend/workers/automatic_processing.py`; `backend/tools/**`;
`frontend/src/App.js` (52 routes); `frontend/src/v3/**` (124 `.jsx`; `api.js`
exports 292 API functions); `admin/src/App.js` (21 routes); `admin/src/pages/**`;
all 89 `supabase/migrations/*.sql`.

**Database evidence** (read-only; no writes, no DDL): the local Supabase cluster
container, its 78 non-template logical databases, per-DB table inventories,
column inventories, policy counts, migration ledgers, `system_settings` rows,
role vocabularies, and a 75-object existence probe in `postgres`,
`ct_local_93d5cdd`, `carbontally_qa_phase8`, `carbontally_test`,
`ct_p17k_20260926`, `carbontally_demo_local`.

**Documents read or sampled**: `docs/architecture` (417) incl. the P17-A…P17-M
series, Phase-8 B/I/X series, `CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`,
`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`, `CARBONTALLY_V3_*`;
`docs/cline` (269); `docs/audit` (197);
`docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md` (1,404 lines, 447 requirement
rows); `docs/verification` (12); `docs/implementation` (21);
`docs/operations` (6); `docs/demo-investor` (7 `DR-00x`); `docs/ohd` (6);
`AGENTS.md` (both trees); the 152-row capability census; the capability/release
ledger; the P17-K/P17-L/P17-M capability documents; the database census.

**Reconciliation baselines for §3**: census `CAP-001`…`CAP-152`; OHD feature
audit's 447 requirement rows; P17-K governed catalogue (18 rows / 7 governed
values); P17-L Scope-3 rows; the 146 distinct table names declared across the
migrations.

---

## 3. Domain index

| # | Domain | Features | IDs |
|---|---|---|---|
| 01 | Platform Administration | 20 | FTR-001…020 |
| 02 | Authentication | 9 | FTR-021…029 |
| 03 | Authorization | 7 | FTR-030…036 |
| 04 | Organizations | 11 | FTR-037…047 |
| 05 | Users | 5 | FTR-048…052 |
| 06 | Roles & Permissions | 7 | FTR-053…059 |
| 07 | Consultant Management | 10 | FTR-060…069 |
| 08 | Consultant Clients | 5 | FTR-070…074 |
| 09 | Acting-For / Delegation | 3 | FTR-075…077 |
| 10 | Principal / Reporting Entities (PE) | 5 | FTR-078…082 |
| 11 | Facilities & Locations | 3 | FTR-083…085 |
| 12 | Assets & Vehicles | 3 | FTR-086…088 |
| 13 | Suppliers | 3 | FTR-089…091 |
| 14 | Documents | 10 | FTR-092…101 |
| 15 | Extraction | 10 | FTR-102…111 |
| 16 | Mapping & Unit Normalisation | 6 | FTR-112…117 |
| 17 | Manual Review & QC | 8 | FTR-118…125 |
| 18 | Evidence | 5 | FTR-126…130 |
| 19 | Data Quality & Validation | 5 | FTR-131…135 |
| 20 | Emission Factors | 8 | FTR-136…143 |
| 21 | Factor Governance | 4 | FTR-144…147 |
| 22 | Scope 1 | 3 | FTR-148…150 |
| 23 | Scope 2 Location-Based | 3 | FTR-151…153 |
| 24 | Scope 2 Market-Based | 3 | FTR-154…156 |
| 25 | Contractual Instruments | 4 | FTR-157…160 |
| 26 | Allocations | 3 | FTR-161…163 |
| 27 | Scope 3 | 6 | FTR-164…169 |
| 28 | Accounting Dimensions | 5 | FTR-170…174 |
| 29 | Estimation & Assumptions | 4 | FTR-175…178 |
| 30 | Calculations | 9 | FTR-179…187 |
| 31 | Workflow & Processing Jobs | 9 | FTR-188…196 |
| 32 | Approvals | 5 | FTR-197…201 |
| 33 | Audit & Auditability | 9 | FTR-202…210 |
| 34 | Reporting | 12 | FTR-211…222 |
| 35 | Report Versions & Frozen Artefacts | 3 | FTR-223…225 |
| 36 | Disclosures | 8 | FTR-226…233 |
| 37 | Insight | 9 | FTR-234…242 |
| 38 | Dashboards & Analytics | 6 | FTR-243…248 |
| 39 | Notifications | 6 | FTR-249…254 |
| 40 | Messaging | 8 | FTR-255…262 |
| 41 | Storage | 4 | FTR-263…266 |
| 42 | Integrations | 6 | FTR-267…272 |
| 43 | API Platform | 8 | FTR-273…280 |
| 44 | Operations | 9 | FTR-281…289 |
| 45 | Admin Console | 7 | FTR-290…296 |
| 46 | Security, Identity & Access Control | 11 | FTR-297…307 |
| 47 | Investor Demo & Synthetic Data | 6 | FTR-308…313 |
| 48 | QA & Independent Verification | 9 | FTR-314…322 |
| 49 | Billing, Subscription & Commercial | 7 | FTR-323…329 |
| 50 | Product Capability Model | 6 | FTR-330…335 |
| 51 | Design System & UI Shell | 5 | FTR-336…340 |
| 52 | Public Website & Visitor Surface | 5 | FTR-341…345 |
| 53 | Deployment, Build & Operational Tooling | 5 | FTR-346…350 |
| 54 | Historical, Legacy & Unreconciled Artefacts | 4 | FTR-351…354 |

---

## 4. Feature catalogue

### Domain 01 — Platform Administration (FTR-001…020)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-001 | Admin control plane — legacy admin CRA (19 screens + staff dashboard) | CT staff admin | IMPLEMENTED_AND_WIRED — DEPRECATED (PO D-P2-02) | AD:App.js 21 routes (`/admin/login`,`/admin`,`/admin/reviews`,`/admin/users`,`/admin/organizations`,`/admin/batches`,`/admin/analytics`,`/admin/settings`,`/admin/defra`,`/admin/customers`,`/admin/manual-review-queue`,`/admin/errors`,`/admin/beta-management`,`/admin/glossary-management`,`/staff-dashboard`,`/admin/reviews-queue`,`/admin/log-viewer`,`/admin/assignments`,`/admin/work-hub`) · API:legacy `/api/admin/*` · DOC:CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md §1–§2,§6 · Deploy:served by `vercel.json` rewrite |
| FTR-002 | V3 internal operations console (`/ops`) — canonical staff application | CT internal staff | IMPLEMENTED_AND_WIRED | API:`/api/v3/ops` (`v3_operations.py`, 53 endpoints) · UI:`frontend/src/v3/ops/OperationsPage.jsx`(+17 tabs) · DOC:ADMIN_CONTROL_PLANE §2 |
| FTR-003 | Ops dashboard | CT operator / reviewer / QC | IMPLEMENTED_AND_WIRED | UI:`ops/OpsDashboard.jsx` · API:`/api/v3/ops/*` · DOC:CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md |
| FTR-004 | Admin work hub + live queue statistics | CT operator / staff admin | IMPLEMENTED_AND_WIRED | AD:`pages/admin/WorkHub.jsx`,`LiveQueueStats.jsx` · API:legacy admin dashboard/workload routers · Deploy:admin CRA |
| FTR-005 | Staff online presence monitoring | CT staff admin | IMPLEMENTED_AND_WIRED | AD:`StaffOnlinePresence.jsx` · UI:`components/StaffPresence.jsx` · DB:`user_presence`,`staff_activity_log` · Deploy:flagship:PRE_P6 |
| FTR-006 | Staff roster and role administration | CT staff admin / system admin | IMPLEMENTED_AND_WIRED | UI:`ops/StaffRoster.jsx`,`ops/StaffRolesTab.jsx` · DB:`staff_profiles`,`staff_roles` (jsonb `permissions`) · API:`/api/v3/ops` · MIG:`20260828010000_v3m8_system_admin_role_model.sql` |
| FTR-007 | Staff workload and performance reporting | CT staff admin | IMPLEMENTED_AND_WIRED | DB:`staff_workload`,`staff_performance`,`staff_daily_performance`,`team_performance` · BE:`utils/staff_workload.py` · API:legacy `/api/admin/workload` · UI:`ops/OpsAssignmentsTab.jsx` |
| FTR-008 | Platform settings administration (`system_settings`) | CT staff admin | IMPLEMENTED_AND_WIRED | DB:`system_settings` (63 columns; rows `analytics_ga4`, `platform_retention` read live) · API:`/api/v3/settings` (4) + legacy `/api/admin/settings` · AD:`pages/admin/Settings.js` · UI:`ops/SettingsTab.jsx` |
| FTR-009 | Configurable retention policy administration (N3) | CT staff admin | PARTIALLY_IMPLEMENTED — destructive enforcement deferred (PO D-P2-04) | DB:`system_settings.platform_retention` (data 365 / backup 365 / document 365 / audit_log 1) · BE:`services/retention.py`, `tools/enforce_retention.py` · API:`/api/v3/settings/retention` |
| FTR-010 | Admin analytics configuration (GA4) | CT staff admin | IMPLEMENTED_AND_WIRED | DB:`system_settings.analytics_ga4` = `{enabled,ga4_measurement_id}` (read live) · AD:`pages/admin/Analytics.js` · UI:`components/AnalyticsBootstrap.jsx` · T:`AnalyticsBootstrap.test.jsx` · DOC:CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md |
| FTR-011 | Admin bulk operations (organisations, users, bulk queue actions) | CT staff admin | IMPLEMENTED_AND_WIRED | API:legacy `/api/admin/bulk`+`org_bulk` routers · BE:`backend/routes/organizations/bulk.py` · UI:`ops/OpsAssignmentsTab.jsx` |
| FTR-012 | Admin import management (`import_batches`) | CT operator | IMPLEMENTED_AND_WIRED | API:`/api/v2/admin/imports`(3) · DB:`import_batches`,`upload_batches` · BE:`data/imports.py` |
| FTR-013 | Factor-provider administration (provider registry/ownership) | CT staff admin | IMPLEMENTED_AND_WIRED | API:`/api/v2/admin/providers`(2) · BE:`domain/provider.py`,`data/emission_factors.py` · MIG:`20260926000000_p8_d4_emission_factors_internal_containment.sql` |
| FTR-014 | Admin glossary management | CT staff admin | IMPLEMENTED_AND_WIRED | AD:`pages/admin/GlossaryManagement.js` · API:legacy `/api/glossary`(8) · DB:`glossary` · Deploy:flagship:PRE_P6 |
| FTR-015 | Admin DEFRA factor management | CT operator | IMPLEMENTED_AND_WIRED | AD:`pages/admin/DefraFactors.js`,`DefraFactorModal.js`,`ImportDefraModal.js` · API:legacy `/api/admin/defra`(9) · DB:`emission_factors` (7,049 rows read live) · Deploy:flagship:PRE_P6 |
| FTR-016 | Admin document-type catalogue management | CT staff admin | IMPLEMENTED_AND_WIRED | API:legacy `/api/admin/document-types`(14) · DB:`document_types`,`document_type_categories` · Deploy:flagship:PRE_P6 |
| FTR-017 | Admin email-template management | CT staff admin | IMPLEMENTED_AND_WIRED | API:legacy `/api/admin/email-templates`(8) · DB:`email_templates`,`email_logs` · BE:`services/email_service.py` · Deploy:flagship:PRE_P6 |
| FTR-018 | Admin operational log viewer | CT staff admin | IMPLEMENTED_AND_WIRED | AD:`components/admin/LogViewer.jsx`,`pages/admin/…/log-viewer` · API:legacy `/api/admin/logs`(8) · DB:`activity_logs`,`processing_logs`,`user_activity_log` |
| FTR-019 | Admin beta-programme management | CT staff admin | IMPLEMENTED_AND_WIRED — retention PO-undecided (POD-012) | AD:`pages/admin/BetaManagement.js` · API:legacy `/api/admin/beta`(10) · DB:`beta_users`,`beta_access_codes` · DOC:PO register §9.2 |
| FTR-020 | Admin QC/issue authority gate (global-admin only endpoints) | CT system admin | IMPLEMENTED_AND_WIRED | API:`/api/v3/qc/*`(3), `/api/v3/issues/admin/open` · DOC:ADMIN_CONTROL_PLANE §3 · T:regression test cited in §3 (QC cannot approve customer reviews) |

### Domain 02 — Authentication (FTR-021…029)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-021 | Email + password authentication | all users | IMPLEMENTED_AND_WIRED | Frontend `supabaseClient.js` + `Login.js`; `auth.users` 1,206 rows read live in `postgres`; DB:`password_reset_tokens`,`login_history` · DOC:CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md · Deploy:flagship:PRE_P6 |
| FTR-022 | Google OAuth + OAuth callback | customer users | IMPLEMENTED_AND_WIRED | Route `/auth/callback` (`AuthCallback.js`); DOC:production auth access spec · Deploy:frontend PV |
| FTR-023 | Magic-link authentication | customer users | IMPLEMENTED_AND_WIRED | Route `/auth/magic` (`MagicLink.jsx`) · Deploy:frontend |
| FTR-024 | Password reset / recovery | all users | IMPLEMENTED_AND_WIRED | DB:`password_reset_tokens` (flagship present) · BE:`backend/auth.py` · DOC:production login runbook |
| FTR-025 | TOTP MFA / authenticator-app capability | customer/CT users | PARTIALLY_IMPLEMENTED — configured, enforcement PO-undecided | DB:`system_settings.two_factor_required`,`two_factor_method` (columns read live) · DOC:AGENTS §69 (production enforcement = separate decision) |
| FTR-026 | Auth session/context resolution API | all authenticated users | IMPLEMENTED_AND_WIRED | API:`/api/v3/context`(1), `/api/v3/ops/me` · BE:`api/v3_context.py`,`api/dependencies.py`,`backend/auth.py` |
| FTR-027 | Fail-closed authentication error surface | all users | IMPLEMENTED_AND_WIRED | UI:`AuthServiceUnavailable.jsx` · UI:`AuthCallback.js` · DOC:CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md |
| FTR-028 | Login history and account audit | customer/CT users | IMPLEMENTED_AND_WIRED | DB:`login_history` · API:legacy auth/user routers · Deploy:flagship:PRE_P6 |
| FTR-029 | Beta entry authentication (beta login/signup) | prospective customers | IMPLEMENTED_AND_WIRED — retirement PO-undecided (P0-REG-F03 / POD-012) | Routes `/beta-login`,`/beta/signup` (`BetaLogin.jsx`,`BetaSignup.jsx`); API:legacy beta(10); DB:`beta_users`,`beta_access_codes` |

### Domain 03 — Authorization (FTR-030…036)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-030 | Row-level security (RLS) enforcement across tenant tables | platform | IMPLEMENTED_AND_WIRED (repository) — coverage varies per database | `pg_policies`: 178 in `postgres`, 222 in `ct_local_93d5cdd`, 201 in `carbontally_qa_phase8` (all read live); MIG:`20260803000000_rc2_rls.sql`,`20260925000000_p8_rls_4b_group1_enablement.sql` |
| FTR-031 | Server-side role/authorization guards on every sensitive endpoint | platform | IMPLEMENTED_AND_WIRED | BE:`api/dependencies.py`,`consultant_auth.py`,`pe_auth.py`,`operations_auth.py`,`insight_authz.py`,`accounting_context_auth.py`,`manual_processing_auth.py`; `require_org_admin`/`ensure_staff_permission` per DOC:ADMIN_CONTROL_PLANE §2 |
| FTR-032 | Resolved staff permission model (`can_process`,`can_review`,`can_manage_staff`,`can_manage_billing`,`can_view_all`) | CT internal staff | IMPLEMENTED_AND_WIRED | DB:`staff_roles.permissions` jsonb (seed matrix in DOC:ADMIN_CONTROL_PLANE §3) · API:`/api/v3/ops/me` |
| FTR-033 | Permission-aware navigation / role-scoped routing | all roles | IMPLEMENTED_AND_WIRED | UI:`v3/components/RoleRoute.jsx`; T:`customer-blocked-visibility.test.jsx`,`operations-page-assignment-gating.test.jsx`; DOC:CL-62 note in ADMIN_CONTROL_PLANE §2 |
| FTR-034 | Consultant-scoped authorization (active client grant) | consultant users | IMPLEMENTED_AND_WIRED | MIG:`20260821000000_d20_d15_active_consultant_grant.sql`,`20260831040000_consultant_revocation_roles.sql`; BE:`api/consultant_auth.py`; DB:`consultant_clients` |
| FTR-035 | PE-scoped authorization and no-download boundary | PE users | IMPLEMENTED_AND_WIRED | BE:`api/pe_auth.py`; UI:`v3/components/workbench/SecureDocumentViewer.jsx`; T:`secure-document-viewer.test.jsx` |
| FTR-036 | Anonymised/public grant containment (anon + authenticated privilege hardening) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260920000000_p8_rls_anon_grant_containment.sql`,`20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql`,`20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql` |

### Domain 04 — Organizations (FTR-037…047)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-037 | Organisation profile & metadata management | Owner / Admin | IMPLEMENTED_AND_WIRED | API:`/api/v3/organizations`(28) · UI:`admin/ProfileTab.jsx`,`OrganizationMetadata.jsx` · DB:`organizations`,`organization_metadata` · API:legacy `/api/organizations/metadata`(15) · Deploy:flagship:PRE_P6 |
| FTR-038 | Organisation membership management (invite/accept/remove/role change) | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`organization_members` (1,125 rows live; roles observed `owner,admin,member,viewer`) · API:`/api/v3/organizations/members`; legacy `/api/organizations/members`(10) · UI:`admin/MembersTab.jsx`,`TeamManagement.js` |
| FTR-039 | Organisation invitations & pending invites | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`pending_invites`,`user_invitations` (both present in flagship) · BE:`data/invitations.py` · API:`/api/v3/organizations/invitations` |
| FTR-040 | Self-service customer onboarding (D35) | prospective customer | IMPLEMENTED_AND_WIRED | MIG:`20260824010000_d35_self_service_onboarding.sql` · UI:`SelfServiceSignup.jsx`,`OnboardingWizard.jsx`,`OnboardingPage.jsx`,`CompanyNamePrompt.jsx` · routes `/signup`,`/onboarding` |
| FTR-041 | Organisation lifecycle states (suspend/archive/restore, D27/D19) | Owner / Admin + CT | IMPLEMENTED_AND_WIRED | MIG:`20260822010000_d27_d19_customer_lifecycle.sql` · API:`/api/v3/organizations/*` · UI:`admin/AdminPage.jsx` |
| FTR-042 | Org-level private document storage linkage | Owner / Admin | IMPLEMENTED_AND_WIRED | MIG:`20260823000000_d32_private_documents_storage.sql` · DB:`organization_files` · UI:`customer/DocumentsPage.jsx` |
| FTR-043 | Organisation-level branding / white-label settings | Owner / Admin (+ consultant) | IMPLEMENTED_AND_WIRED | MIG:`20260821010000_d21_white_label_branding.sql` · API:`/api/v3/whitelabel`(9) · UI:`consultant/WhiteLabelTab.jsx` · DB:`consultant_custom_domains`,`consultant_senders` |
| FTR-044 | Organisation type & consolidation approach (P17-A dimension) | Owner / Admin | IMPLEMENTED_AND_WIRED (repository) — SCHEMA_ONLY where P17 unapplied | MIG:`20261010000000_p17a_…` (`organizations.organization_type`,`consolidation_approach`) · verified present only in `ct_p17k_20260926` (Deploy:p17clone:YES; flagship:NO) |
| FTR-045 | Customer dashboard / organisation analytics | Owner / Admin / Member | IMPLEMENTED_AND_WIRED | API:legacy `/api/customer/dashboard`(12) · DB:`dashboard_metrics` · UI:`customer/DashboardPage.jsx` |
| FTR-046 | Multi-organisation membership resolution | account holder | PARTIALLY_IMPLEMENTED — switching PO-undecided (P4-F03/F04) | MIG:`20260831000000_v3m10_org_membership_unique.sql` (uniqueness) · DOC:CARBONTALLY_PHASE4_INDIVIDUAL_USER_ARCHITECTURE_DESIGN.md · API:`/api/v3/context` resolves a single active org |
| FTR-047 | Organisation search / lookup for staff & consultants | CT staff / consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/search`(1) · BE:`data/search.py`,`infra/search_index.py` · UI:`v3/components/SearchBox.jsx` |

### Domain 05 — Users (FTR-048…052)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-048 | Team management / user administration | Owner / Admin | IMPLEMENTED_AND_WIRED | API:legacy `/api/users`(5), `/api/team`; UI:`TeamManagement.js` · DB:`users`,`organization_members` · DOC:AGENTS §14 (user creation = privileged) |
| FTR-049 | User profile self-service | all authenticated users | IMPLEMENTED_AND_WIRED | UI:`admin/ProfileTab.jsx` · API:`/api/v3/context`,legacy `/api/users` · DB:`organization_metadata`/profile fields |
| FTR-050 | User presence / typing status | authenticated users | IMPLEMENTED_AND_WIRED | DB:`user_presence`,`typing_status` (both present in flagship) · UI:`components/StaffPresence.jsx` |
| FTR-051 | User feedback submission | all users | IMPLEMENTED_AND_WIRED | API:legacy `/api/feedback`(6) · DB:`user_feedback` · Deploy:flagship:PRE_P6 |
| FTR-052 | Waitlist / access request (pre-launch marketing) | public visitor | IMPLEMENTED_AND_WIRED | API:legacy `/api/waitlist` · DB:`waitlist` · DOC:PO register §1.1–§1.2 (closed signup) |

### Domain 06 — Roles & Permissions (FTR-053…059)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-053 | Customer role model (owner / admin / member / viewer) | platform | IMPLEMENTED_AND_WIRED | Observed live in `organization_members.role` (`owner,admin,member,viewer`); DOC:AGENTS §9 · T:`customer-blocked-visibility.test.jsx` |
| FTR-054 | Internal staff role model (admin, system_admin, operator, reviewer, qc_specialist, pe_manager) | CT internal | IMPLEMENTED_AND_WIRED | DB:`staff_roles` + seed matrix DOC:ADMIN_CONTROL_PLANE §3; MIG:`20260828010000_v3m8_system_admin_role_model.sql`,`20260828020000_v3m8_pe_manager_role.sql` |
| FTR-055 | PE role model (PE manager, PE staff/operator) | PE users | IMPLEMENTED_AND_WIRED | MIG:`20260828020000_v3m8_pe_manager_role.sql` · API:`/api/v3/pe`(20) · UI:`v3/pe/*` |
| FTR-056 | Consultant role / capability flags | consultant users | IMPLEMENTED_AND_WIRED | MIG:`20260906100000_p6_2a_consultant_processing_permissions.sql` · DB:`consultant_firm_members`,`consultant_profiles` · API:`/api/v3/consultants`(32) |
| FTR-057 | Legacy `roles` catalogue (name + permissions jsonb) | legacy admin | SCHEMA_ONLY (empty) | DB:`roles` exists in `postgres` and `qa133` with **0 rows** (read live); no `role_permissions` or `profiles` table exists; legacy `/api/admin/permissions`(7) still mounted |
| FTR-058 | Data-driven permission catalogue / role CRUD | CT staff admin | PARTIALLY_IMPLEMENTED | API:legacy `/api/admin/permissions`(7) returns empty for staff-admin per DOC:ADMIN_CONTROL_PLANE §1 (split-brain note); canonical permissions live in `staff_roles.permissions` |
| FTR-059 | Role capability matrix as a governed artefact | product | DOCUMENTED_ONLY — PO-undecided (POD-017) | DOC:ADMIN_CONTROL_PLANE §3,§5; DOC:census §11.2 POD-017 |

### Domain 07 — Consultant Management (FTR-060…069)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-060 | Consultant workspace (portfolio + client operations) | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/consultants`(32) · UI:`consultant/ConsultantPage.jsx` · T:`consultant-page.test.jsx` |
| FTR-061 | Consultant portfolio listing & consultant-client dashboard | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/reporting/consultant-portfolio`, `/api/v3/reporting/consultant-client/{client_id}`(15 total in `v3_reporting.py`) · DB:`consultant_clients` |
| FTR-062 | Active-client switching / acting-for context | consultant | IMPLEMENTED_AND_WIRED | MIG:`20260821000000_d20_d15_active_consultant_grant.sql` (D15 active grant) · API:`/api/v3/consultants/active`, `/api/v3/accounting`(8) · UI:`ConsultantPage.jsx` |
| FTR-063 | Consultant team management (firm members) | consultant owner | IMPLEMENTED_AND_WIRED | DB:`consultant_firm_members` · UI:`consultant/ConsultantTeamTab.jsx` · MIG:`20260906090000_p6_1c_consultant_engagement.sql` |
| FTR-064 | Consultant new-customer onboarding (CON-1) | consultant | IMPLEMENTED_AND_WIRED | UI:`consultant/NewCustomerView.jsx` · API:`/api/v3/consultants/clients` · DOC:CARBONTALLY_P6_2_CONSULTANT_PROCESSING_WORKFLOW_ARCHITECTURE.md |
| FTR-065 | Consultant engagement confirmation for pre-existing organisations | consultant + customer | IMPLEMENTED_AND_WIRED | MIG:`20260906090000_p6_1c_consultant_engagement.sql` · DOC:CARBONTALLY_PHASE6_P0_PO_RATIFICATION_REPORT.md |
| FTR-066 | Consultant lifecycle / revocation (client leaves, access revoked, data preserved) | consultant / CT | IMPLEMENTED_AND_WIRED | MIG:`20260831040000_consultant_revocation_roles.sql` · BE:`services/consultant_lifecycle.py` · DOC:AGENTS §11 |
| FTR-067 | Consultant processing capability flags (D7 processing-mode provenance) | consultant | IMPLEMENTED_AND_WIRED | MIG:`20260906100000_p6_2a_…`,`20260910120000_p6_2d_consultant_provenance.sql` · BE:`domain/processing_origin.py` |
| FTR-068 | Consultant white-label branding, custom domains, verified senders | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/whitelabel`(9) · DB:`consultant_custom_domains`,`consultant_senders` · UI:`consultant/WhiteLabelTab.jsx` · DOC:AGENTS §64 |
| FTR-069 | Consultant billing / commercial relationship | consultant | IMPLEMENTED_BACKEND_ONLY — no UI route found | DB:`consultant_billing` · API:`/api/v3/commercial`(24) · DOC:CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md · Deploy:flagship:PRE_P6 |

### Domain 08 — Consultant Clients (FTR-070…074)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-070 | Client organisation registry (consultant-owned relationships) | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/consultants/clients`(32 total) · DB:`consultant_clients` (present in flagship) · DOC:docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md |
| FTR-071 | Client-scoped context resolution (documents, evidence, issues, processing, reports) | consultant | IMPLEMENTED_AND_WIRED | API pattern `/api/v3/consultants/clients/{client_id}/{documents,evidence,issues,reports,processing/items,processing/status,context,dashboard}` (path strings verified in `backend/api/v3_consultants.py`) |
| FTR-072 | Client document upload & processing on behalf of client | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/documents`(9) + consultant client routes · DB:`customer_documents` · DOC:AGENTS §10 (consultants are operators, not read-only) |
| FTR-073 | Client review / approval participation boundaries | consultant + client owner | PARTIALLY_IMPLEMENTED — approval boundary frozen (P6-2C) | DOC:CARBONTALLY_P6_2C_APPROVAL_BOUNDARY_HARDENING_IMPLEMENTATION_CONTRACT.md · API:`/api/v3/review`(6), `/api/v3/verifications`(4) |
| FTR-074 | Client ↔ consultant messaging (active-client only) | consultant + client | IMPLEMENTED_AND_WIRED | UI:`consultant/ClientMessagingTab.jsx` · API:`/api/v3/messaging`(10) · DOC:AGENTS §28 (N1 frozen) |

### Domain 09 — Acting-For / Delegation (FTR-075…077)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-075 | Acting-for write paths (consultant acts for client on write operations) | consultant | IMPLEMENTED_AND_WIRED | DOC:CT-PO-P17-IMPLEMENT-02-API-ACTING-FOR-WRITE-PATHS-20250925.md, CT-PO-P17-IMPLEMENT-03-WIRE-ACTING-FOR-WRITE-PATHS-20250925.md · BE:`domain/acting_for.py`,`api/acting_for` surfaces · API:`/api/v3/accounting`(8) |
| FTR-076 | Acting-for attribution on results & logs (`performed_by_organization_id`, `acting_for_organization_id`) | consultant / platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent where P17 unapplied | MIG:`20261010000000_p17a_…` · verified columns present only in `ct_p17k_20260926` (Deploy:p17clone:YES) · API:`/api/v3/reporting/audit-activity`, `/acting-for/attribution` |
| FTR-077 | Delegation / impersonation / "act as user" | CT staff | UNKNOWN — no evidence found | Searched both trees for impersonation/delegation features (`backend/**`, `frontend/src/**`, `docs/**`); only consultant acting-for exists; recorded as an unresolved product question (§5) |

### Domain 10 — Principal / Reporting Entities (PE) (FTR-078…082)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-078 | PE terminology determination | product | DOCUMENTED_ONLY / UNRESOLVED | The tree uses **"Processing Entity" (PE)** throughout legal, schema, API and UI (e.g. `processing_entities`, `/api/v3/pe`, `/api/v3/admin/entities`); "Principal Entity" appears only in this task's example list; no "principal entity" implementation exists → terminology conflict recorded in §5 |
| FTR-079 | Processing entity registry (first-class entity model) | CT staff admin | IMPLEMENTED_AND_WIRED | DB:`processing_entities` (flagship present) · MIG:`20260810000000_v3m1_processing_entities.sql` · API:`/api/v3/admin/entities`(4), `/api/v3/processing-entities` |
| FTR-080 | Entity relationship / hierarchy model | CT staff admin | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent in every local DB except clones | MIG:`20260810010000_v3m2_entity_relationships.sql` · live probe: `entity_relationships` **absent** in `postgres`, present in clones · API:`/api/v3/pe`(20) |
| FTR-081 | Entity-scoped RLS policies | platform | IMPLEMENTED_AND_WIRED | MIG:`20260810050000_v3m6_entity_rls.sql`,`20260822000000_p9_rls_recursion_fix.sql` · policy counts per DB §1.1 |
| FTR-082 | PE administration screens | CT staff admin | IMPLEMENTED_AND_WIRED | UI:`v3/ops/ProcessingEntitiesTab.jsx` · AD:legacy admin `/admin/…` entity screens · API:`/api/v3/admin/entity/{entity_id}` |

### Domain 11 — Facilities & Locations (FTR-083…085)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-083 | Facilities master data | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`facilities` (flagship present) · UI:`admin/FacilitiesTab.jsx` · API:`/api/v3/organizations/facilities` · DOC:D17 / AGENTS §34,§41 |
| FTR-084 | Locations master data | Owner / Admin | PARTIALLY_IMPLEMENTED — UI exists, dedicated table not found | UI:`admin/LocationsTab.jsx`; live probe: **no `locations` table in any DB tested**; location semantics appear folded into `facilities` (and `calculation_snapshots.facility_id` under P17-A) → schema/UI mismatch recorded (§5) |
| FTR-085 | Facility as an accounting dimension on results | platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent where P17 unapplied | MIG:`20261010000000_p17a_…` adds `facility_id` to `calculation_snapshots` + `emissions_logs`, index `idx_calc_snapshots_org_facility`,`idx_emissions_logs_org_facility`; present only in `ct_p17k_20260926` |

### Domain 12 — Assets & Vehicles (FTR-086…088)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-086 | Assets master data | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`assets` (flagship present) · UI:`admin/AssetsTab.jsx`,`AssetManager.js` · API:`/api/v3/organizations/assets`; legacy `/api/organizations/assets`(11) · DOC:D17 |
| FTR-087 | Vehicles master data | Owner / Admin | IMPLEMENTED_AND_WIRED | MIG:`20260825000000_v3m7_vehicles.sql` · DB:`vehicles` (flagship present) · API:`/api/v3/vehicles`(5) · UI:`admin/VehiclesTab.jsx` |
| FTR-088 | Asset/facility-vs-UUID presentation rule (business-first display) | platform | DOCUMENTED_ONLY | DOC:AGENTS §34,§75 (show facility name, not UUID) — no code assertion located that enforces it |

### Domain 13 — Suppliers (FTR-089…091)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-089 | Suppliers master data | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`suppliers`,`supplier_categories` (flagship present) · API:`/api/v3/suppliers`(5) · UI:`admin/SuppliersTab.jsx` · DOC:D17 |
| FTR-090 | Supplier resolution / matching on extraction | platform | IMPLEMENTED_AND_WIRED | BE:`engines/supplier_resolution.py` · MIG:`20261014000000_p17_10_product_contract_reporting_dimensions.sql` references supplier reporting dimension |
| FTR-091 | Supplier category taxonomy | Owner / Admin | IMPLEMENTED_AND_WIRED | DB:`supplier_categories` (flagship present) · API:legacy organization/supplier routers · Deploy:flagship:PRE_P6 |

### Domain 14 — Documents (FTR-092…101)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-092 | Document upload (single + multi) | Owner / Admin / Member / consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/documents`(9), legacy `/api/upload`(10), `/api/customer/documents`(16) · DB:`customer_documents`,`upload_batches` |
| FTR-093 | Bulk upload (multi-file, batch) | customer / consultant | IMPLEMENTED_AND_WIRED | UI:`BulkUpload.jsx` · DB:`upload_batches`,`import_batches` · API:legacy `/api/upload` |
| FTR-094 | PDF ingestion portal | customer / consultant | IMPLEMENTED_AND_WIRED | UI:`PDFIngestionPortal.jsx` · UI:`components/FileUploadHero.jsx` |
| FTR-095 | Private document storage bucket + storage policies | platform | IMPLEMENTED_AND_WIRED | MIG:`20260823000000_d32_private_documents_storage.sql` · DOC:docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md · AGENTS §68 |
| FTR-096 | Document status tracking | customer / consultant | IMPLEMENTED_AND_WIRED | UI:`DocumentStatus.jsx`,`document/…` routes · API:legacy `/api/document-activity`(6) · DB:`document_activity_log` |
| FTR-097 | Document type taxonomy & classification | platform | IMPLEMENTED_AND_WIRED | DB:`document_types`,`document_type_categories` (flagship present) · BE:`utils/document_classifier.py` · API:legacy `/api/admin/document-types`(14) |
| FTR-098 | Document processing queue (legacy intake queue) | platform | IMPLEMENTED_AND_WIRED (legacy) | DB:`document_processing_queue`,`processing_queue` · MIG:`20260807060000_add_dpq_workflow_columns.sql` · AD:legacy queue screens |
| FTR-099 | Manual entry (single + standalone + admin-assisted) | customer / CT operator | IMPLEMENTED_AND_WIRED | UI:`components/ManualEntry.jsx`,`ManualEntryStandalone.jsx`,`ManualEntryView.jsx`; AD:`AdminManualEntry.jsx`,`StaffManualEntry.jsx`; DB:`draft_entries`; API:legacy `/api/drafts`(6),`/api/drafts/enhanced`(6) |
| FTR-100 | File attachments (document ↔ entity linking) | customer / CT operator | IMPLEMENTED_AND_WIRED | DB:`file_attachments` (flagship present) · API:legacy `/api/organizations/files`(18) |
| FTR-101 | Secure document viewer with no-download policy (PE boundary) | PE users / reviewers | IMPLEMENTED_AND_WIRED | UI:`v3/components/workbench/SecureDocumentViewer.jsx` · T:`secure-document-viewer.test.jsx` · DOC:AGENTS §12 (PE source-document boundary) |

### Domain 15 — Extraction (FTR-102…111)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-102 | PDF text extraction engine | platform | IMPLEMENTED_AND_WIRED | BE:`engines/extraction.py`,`backend/pdf_engine.py`,`engines/pdf_render.py` · API:legacy `/api/extraction` |
| FTR-103 | OCR capability (scanned PDF/image) | platform | IMPLEMENTED_BACKEND_ONLY — environment dependency unresolved | BE:`engines/extraction.py` · Tooling `tools/provision_tesseract_local.sh` (historical tree) · DOC:AGENTS §20 + census §6 CAP-139 (OCR availability = deployment dependency) |
| FTR-104 | AI-assisted document extraction | platform | IMPLEMENTED_AND_WIRED | BE:`engines/ai_extraction.py`,`services/ai_document_extraction.py`,`infra/ai_runtime.py`,`infra/llm_client.py` · API:`/api/v3/manual-extraction`(6) |
| FTR-105 | Invoice/utility document extraction (supplier-specific) | platform | IMPLEMENTED_AND_WIRED | BE:`engines/invoice_extraction.py` · DOC:CT-P8-B1 collection + docs/sample_bills (8 files) |
| FTR-106 | Automatic extraction orchestration (durable worker) | platform | IMPLEMENTED_AND_WIRED | BE:`services/automatic_extraction.py`,`services/automatic_processing.py`,`workers/automatic_processing.py` · MIG:`20260829000000_v3m9_durable_automatic_processing.sql` · API:`/api/v3/processing/automatic`(6) |
| FTR-107 | Manual extraction review with FIN-06 governance | CT operator + customer | IMPLEMENTED_AND_WIRED | MIG:`20260927000000_p8_fin06_manual_processing_governance.sql` · API:`/api/v3/manual-extraction`(6), manual-processing admin(4) · BE:`api/manual_processing_auth.py`,`data/manual_processing.py` · DOC:docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md |
| FTR-108 | Extraction fidelity scoring and field suggestions | CT operator | IMPLEMENTED_BACKEND_ONLY | BE:`services/extraction_fidelity.py`,`services/extraction_suggestions.py` · DOC:docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md §8 lists the extraction-suggestion tests |
| FTR-109 | Structured data preview in the review workbench | CT operator / reviewer | IMPLEMENTED_AND_WIRED | UI:`v3/components/workbench/StructuredDataPreview.jsx` · T:`structured-data-preview.test.jsx` |
| FTR-110 | Extraction error review (admin) | CT operator | IMPLEMENTED_AND_WIRED (legacy) | AD:`pages/admin/ExtractionErrorReview.js`,`ErrorDetailModal.js`,`ReviewExtractionModal.js` · API:legacy `/api/admin/extraction` |
| FTR-111 | Activity clarifications & adjudication lifecycle (F-039-1) | customer / CT operator | IMPLEMENTED_AND_WIRED | MIG:`20260928000000_p8_fs_activity_clarifications.sql`,`20260929000000_…_fks.sql`,`20260930000000_…_adjudication_lifecycle.sql`,`20260931000000_…_context_lineage.sql` · DB:`activity_clarifications` (clone only) · API:`/api/v3/activity-clarifications`(5) · BE:`domain/activity_clarification.py` |

### Domain 16 — Mapping & Unit Normalisation (FTR-112…117)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-112 | Factor matching engine | platform | IMPLEMENTED_AND_WIRED | BE:`engines/factor_matching.py`,`engines/matching_stages.py` · DOC:OHD G-1/R-A independent verification records (factor wiring) |
| FTR-113 | Factor selection policy (precedence + safety) | platform | IMPLEMENTED_AND_WIRED | BE:`engines/factor_selection_policy.py` · DOC:AGENTS §15 (approved customer factor first) · T:`test_factor_set_context.py` (8/8 per OHD audit citation) |
| FTR-114 | Mapping stage pipeline (multi-stage match) | platform | IMPLEMENTED_AND_WIRED | BE:`engines/matching_stages.py` · MIG:`20260807050000_add_factor_aliases.sql` (alias-assisted matching) |
| FTR-115 | Unit normalisation (central mechanism) | platform | IMPLEMENTED_AND_WIRED | BE:`core/units.py` · DB:`units` (flagship present) · DOC:AGENTS §23 · MIG:`20260800000000_rc2_schema.sql`,`20260801000000_rc2_constraints.sql` |
| FTR-116 | Multi-line / item-level factor contract | platform | IMPLEMENTED_AND_WIRED | BE:`domain/line_items.py`,`domain/matching.py` · MIG:`20260916000000_p8_b2_evidence_line_items.sql`,`20260916010000_p8_b2_provenance_line_links.sql` |
| FTR-117 | Mapping UI inside the processing workbench (D19) | CT operator / customer | IMPLEMENTED_AND_WIRED | UI:`v3/ops/ExtractionPanel.jsx`,`v3/ops/WorkItemWorkspace.jsx`,`v3/components/workbench/*` · T:`workbench.test.jsx` |

### Domain 17 — Manual Review & QC (FTR-118…125)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-118 | Review queue (customer/organisation-scoped) | customer reviewer | IMPLEMENTED_AND_WIRED | API:`/api/v3/review`(6) · UI:`customer/ReviewPage.jsx`,`customer/ReviewDetailPage.jsx` · routes `/review`,`/review/:itemId` |
| FTR-119 | Operator review queue & routed workspaces | CT operator / reviewer | IMPLEMENTED_AND_WIRED | UI:`ops/OperatorQueue.jsx`,`ops/ReviewQueue.jsx`,`ops/ReviewItemPage.jsx`,`ops/OperatorItemPage.jsx` · routes `/ops/items/:itemId`,`/ops/review/:itemId` |
| FTR-120 | Review workspace — D19 processing workbench (frozen UX) | CT operator / reviewer | IMPLEMENTED_AND_WIRED | UI:`ops/WorkItemWorkspace.jsx`,`components/workbench/WorkbenchShell.jsx`,`SplitPane.jsx`,`WorkflowNav.jsx`,`AutosaveIndicator.jsx` · DOC:AGENTS §39 (D19) · T:`workbench.test.jsx` |
| FTR-121 | Review/item assignment ledger (D38 / WS4 Gate 3) | CT staff admin / operator | IMPLEMENTED_AND_WIRED | MIG:`20260902030000_phase5_work_item_assignments.sql`,`20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` · DB:`work_item_assignments` (flagship present) · UI:`ops/OpsAssignmentsTab.jsx` · T:`ops-assignments-tab.test.jsx` |
| FTR-122 | Reassignment & review-assignment history | CT staff admin | IMPLEMENTED_AND_WIRED (legacy) | DB:`reassignment_history`,`review_assignment_history` (both present in flagship) · AD:`pages/admin/ReviewAssignment.js` · API:legacy `/api/admin/reviews`(12) |
| FTR-123 | CarbonTally QC queue and QC records | CT QC specialist | IMPLEMENTED_AND_WIRED | API:`/api/v3/qc`(3) · UI:`ops/QcQueue.jsx`,`ops/QcItemPage.jsx`,`ops/CtQcTab.jsx` · DB:`qc_checks`,`qc_errors`,`qc_checklists` · route `/ops/qc/:itemId` |
| FTR-124 | Quality chain: PE QC → CarbonTally QC → customer final approval | platform | IMPLEMENTED_AND_WIRED | MIG:`20260902020000_v1_2_dual_origin_workflow.sql` (dual-origin workflow + CT QC gate) · DOC:CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md · T:QC/customer-approval regression cited in ADMIN_CONTROL_PLANE §6 (D-P2-03) |
| FTR-125 | Manual review queue (legacy operator queue) | CT operator | IMPLEMENTED_AND_WIRED (legacy) | DB:`manual_review_queue` (flagship present) · AD:`pages/admin/ManualReviewQueue.js` · API:legacy `/api/admin/manual-review-queue` |

### Domain 18 — Evidence (FTR-126…130)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-126 | Evidence trail & source-evidence viewer | reviewer / customer / auditor | IMPLEMENTED_AND_WIRED | UI:`v3/components/EvidenceTrail.jsx`,`v3/evidence/SourceEvidenceViewer.jsx` · T:`evidence-trail.test.jsx`,`source-evidence-viewer.test.jsx` · API:`/api/v3/evidence`(1) |
| FTR-127 | Evidence line items (P8-B2) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260916000000_p8_b2_evidence_line_items.sql` · DB:`evidence_line_items` (present in `qa133`/clones; absent in flagship) · API:`/api/v3/evidence` · route `/evidence/line-items/:lineItemId` |
| FTR-128 | Provenance line links (evidence ↔ source line) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260916010000_p8_b2_provenance_line_links.sql` · DB:`provenance_line_links` (clone only) · BE:`data/evidence_line_items.py` |
| FTR-129 | Evidence traceability columns (authoritative source lineage, D33) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260823010000_d33_evidence_traceability.sql` · DOC:CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md |
| FTR-130 | Evidence idempotency and correction privileges (P8-B1) | platform / customer owner | IMPLEMENTED_AND_WIRED | MIG:`20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` · DB:`disclosure_value_evidence` |

### Domain 19 — Data Quality & Validation (FTR-131…135)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-131 | Validation engine & issue lifecycle (V3M-5) | platform / customer | IMPLEMENTED_AND_WIRED | MIG:`20260810040000_v3m5_issues.sql` · BE:`engines/validation.py`,`domain/issue.py`,`domain/validation.py` · DB:`issues` (flagship present) |
| FTR-132 | Issues API and issue resolution surface | customer / CT operator | IMPLEMENTED_AND_WIRED | API:`/api/v3/issues`(6) + `/api/v3/issues/admin/open` · UI:`customer/IssuesPage.jsx`, route `/issues` · UI:`ops/IssuesTriageTab.jsx` |
| FTR-133 | Data-quality workflow columns (DPQ) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260807060000_add_dpq_workflow_columns.sql` · DB columns on `document_processing_queue` |
| FTR-134 | Data-quality scanning with reproducibility (Insight P3) | platform | IMPLEMENTED_AND_WIRED | BE:`domain/data_quality.py`,`domain/insight_quality.py` · MIG:`20261007000000_p8_insight_data_quality_reproducibility.sql` · API:`/api/v3/insight/*` |
| FTR-135 | Data-quality dimension on calculation results | platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent where P17 unapplied | MIG:`20261010000000_p17a_…` adds `data_quality` to `calculation_snapshots` + `emissions_logs` with CHECK and scope constraints · present only in `ct_p17k_20260926` |

### Domain 20 — Emission Factors (FTR-136…143)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-136 | DEFRA/DESNZ factor provider and catalogue | platform | IMPLEMENTED_AND_WIRED | DB:`emission_factors` **7,049 rows** read live in flagship; `import_batches` lineage · BE:`data/emission_factors.py`,`backend/defra.py` · MIG:`20260807010000_add_emission_factors_import_batch.sql` · DOC:CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md (source register) |
| FTR-137 | SEAI (Ireland) factor provider | platform | IMPLEMENTED_AND_WIRED | BE:historical `src/commands/import_seai.py` + current provider registry (`domain/provider.py`) · DOC:factor-provider lineage in census CAP-050 |
| FTR-138 | Factor aliases (synonym resolution) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260807050000_add_factor_aliases.sql` · DB:`factor_aliases` (flagship present) · BE:`data/factor_aliases.py` |
| FTR-139 | Customer custom factors with owner self-approval | Customer Owner | IMPLEMENTED_AND_WIRED | MIG:`20260810020000_v3m3_customer_factors.sql` · DB:`customer_factors` (flagship present) · API:`/api/v3/customer-factors`(6) · UI:`admin/CustomFactorsTab.jsx` · T:`customer-factors-tab.test.jsx` · DOC:AGENTS §16 (owner may self-approve — ratified) |
| FTR-140 | Customer-factor approval workflow & precedence over generic factors | Customer Owner / Member | IMPLEMENTED_AND_WIRED | BE:`domain/customer_factor.py`,`engines/factor_selection_policy.py` · DOC:AGENTS §15,§16 · T:`test_factor_set_context.py` (referenced) |
| FTR-141 | Factor import batches and versioning of source data | CT operator | IMPLEMENTED_AND_WIRED | DB:`import_batches`,`emission_factors.import_batch_id` · MIG:`20260807000000_add_import_batches.sql` |
| FTR-142 | `emission_factors` internal containment (customer cannot read internal corpus) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260926000000_p8_d4_emission_factors_internal_containment.sql` · DOC:census CHG (D-4 ratified) |
| FTR-143 | Qualified unit selection / EF-E refinement | platform | PARTIALLY_IMPLEMENTED — branch divergence | DOC:CT-P8-P2_FACTOR_CATALOGUE_CENSUS / OHD audit note: EF-E refinements exist on the historical `main` branch but not on the release branch (`p8-release-reconciled`) |

### Domain 21 — Factor Governance (FTR-144…147)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-144 | Factor governance attributes (method, category hint, factor type, gas coverage) | CT staff admin | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent where P17 unapplied | MIG:`20261010000000_p17a_…` §3 adds `emission_factors.scope2_method`,`scope3_category_hint`,`factor_type`,`gas_coverage` + index · verified present only in `ct_p17k_20260926` |
| FTR-145 | Factor provenance captured on every result (`factor_id`,`factor_kind`,`customer_factor_id`) | platform | IMPLEMENTED_AND_WIRED | BE:`engines/calculation.py`,`domain/factor.py` · DOC:AGENTS §15,§17 · DB:`calculation_snapshots` |
| FTR-146 | Provider ownership & provider-driven factor updates | CT staff admin | IMPLEMENTED_AND_WIRED | API:`/api/v2/admin/providers`(2) · BE:`domain/provider.py` · MIG:`20260926000000_p8_d4_…` |
| FTR-147 | Governed capability statement of factor-based support (per scope/method) | product | IMPLEMENTED_AND_WIRED | MIG:`20261020000000_p17k_governed_capability_catalogue.sql` (reference data only) · BE:`domain/capability_catalogue.py` · DB:`disclosure_requirement_versions` (55 rows in `ct_p17k_20260926`; absent elsewhere) |

### Domain 22 — Scope 1 (FTR-148…150)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-148 | Scope 1 fuel/combustion accounting (stationary & mobile) | customer / consultant | IMPLEMENTED_AND_WIRED | BE:`domain/cams.py`,`engines/calculation.py`,`services/scope3_calculation.py` scope-family handling · DB:`calculation_snapshots`,`emissions_logs` · MIG:`20261010000000_p17a_…` scope constraints · DOC:CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md |
| FTR-149 | Scope 1 energy-type dimension (fuel type / combustion basis) | platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA absent where P17 unapplied | MIG:`20261010000000_p17a_…` adds `energy_type` + `calc_snapshots_energy_type_check`,`…_scope_check`; present only in `ct_p17k_20260926` |
| FTR-150 | Natural-gas / combustion basis product decisions | product | DOCUMENTED_ONLY — PO closure recorded | DOC:CARBONTALLY_PHASE8_D_A_NATURAL_GAS_BASIS_PO_CLOSURE_DECISION_20260918.md |

### Domain 23 — Scope 2 Location-Based (FTR-151…153)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-151 | Scope 2 location-based calculation engine | customer / consultant | IMPLEMENTED_AND_WIRED | BE:`services/scope2_calculation.py`,`domain/scope2.py`,`engines/calculation.py` · API:`/api/v3/scope2`(1) · MIG:`20261010000000_p17a_…` (`scope2_method` CHECK with `LOCATION_BASED`) · DOC:CT-PO-P17-IMPLEMENT-05-SCOPE2-CALCULATION-20250925.md |
| FTR-152 | Grid/energy factor selection for location-based method | platform | IMPLEMENTED_AND_WIRED | BE:`engines/factor_matching.py` + `emission_factors.scope2_method` (P17-A) · DOC:P17-ARCH-01 |
| FTR-153 | Location-based method constraint enforcement on results | platform | IMPLEMENTED_AND_WIRED (repository) — absent where P17 unapplied | MIG:`20261010000000_p17a_…` (constraints `calc_snapshots_method_scope_consistency`, `calc_snapshots_scope2_method_check`) — verified `scope2_method` present in `ct_p17k_20260926`, absent in 4 other DBs |

### Domain 24 — Scope 2 Market-Based (FTR-154…156)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-154 | Scope 2 market-based method support | customer / consultant | PARTIALLY_IMPLEMENTED — governed status is `MISSING_CAPABILITY` | DOC:CT-PO-P17-K-… §10.3 (market-based row is `MISSING_CAPABILITY`, not `SUPPORTED`) · MIG:`20261010000000_p17a_…` allows `MARKET_BASED` in the CHECK vocabulary · DOC:CT-PO-P17-DECISION-03 §10.3 `SC-4` |
| FTR-155 | Residual-mix / supplier-specific factor handling | customer / consultant | DOCUMENTED_ONLY (governed value = `MISSING_CAPABILITY`) | DOC:CT-PO-P17-L-… (capability truth surface renders the missing prerequisite) · no engine file found asserting residual-mix logic |
| FTR-156 | Market-based disclosure claim boundary | product | DOCUMENTED_ONLY — PO-frozen | DOC:CT-PO-P17-DECISION-03-… §10.3 |

### Domain 25 — Contractual Instruments (FTR-157…160)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-157 | Contractual instrument repository (energy attribute certificates etc.) | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — table only in clones | MIG:`20261011000000_p17c_contractual_instruments_and_allocations.sql` creates `contractual_instruments`,`instrument_allocations`; verified **present** in `ct_p17k_20260926`, absent in `postgres`/`qa133`/`local135` · BE:`domain/contractual_instruments.py`,`data/contractual_instruments.py` · DOC:CT-PO-P17-IMPLEMENT-06-… |
| FTR-158 | Instrument allocations (link instrument → consumption/result) | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — see above | MIG:`20261011000000_p17c_…` · DB:`instrument_allocations` |
| FTR-159 | Instrument API & persistence wiring | consultant / customer | IMPLEMENTED_AND_WIRED | BE:`data/contractual_instruments.py` · API:`/api/v3/scope2`(1), `/api/v3/accounting`(8) · DOC:CT-PO-P17-IMPLEMENT-06-… |
| FTR-160 | Instrument evidence and audit linkage | platform | PARTIALLY_IMPLEMENTED | Instrument rows participate in evidence line items/provenance (P8-B2) only where both migrations are applied — no database on this host has both P8-B2 **and** P17-C · T:none located that asserts the cross-feature chain |

### Domain 26 — Allocations (FTR-161…163)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-161 | Instrument allocation to consumption/result rows | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — clone-only schema | MIG:`20261011000000_p17c_…` · DB:`instrument_allocations` · BE:`domain/contractual_instruments.py` |
| FTR-162 | Multi-entity / multi-facility allocation of emissions | CT staff admin / consultant | PARTIALLY_IMPLEMENTED — entity model not deployed anywhere durable | MIG:`20260810010000_v3m2_entity_relationships.sql` + P17-A `facility_id`; live probe: `entity_relationships` absent in every persistent DB tested; `facility_id` present only in `ct_p17k_20260926` |
| FTR-163 | Allocation provenance & double-count prevention across allocations | platform | PARTIALLY_IMPLEMENTED | BE:`domain/estimation.py` (double-counting detectors, P17-H) · DOC:CT-PO-P17-IMPLEMENT-MASTER-01-IMPLEMENTATION-REPORT-20250925.md |

### Domain 27 — Scope 3 (FTR-164…169)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-164 | Scope 3 category taxonomy — exactly 15 categories (P17-D reference seed) | platform | IMPLEMENTED_AND_WIRED (repository) — clone-only table | MIG:`20261012000000_p17d_scope3_category_taxonomy.sql` (`CREATE TABLE … scope3_categories` + read policy, verified by file read) · present in `ct_p17k_20260926`, absent in flagship/qa133/local135 |
| FTR-165 | Scope 3 calculation engine (all categories) | customer / consultant | IMPLEMENTED_AND_WIRED | BE:`services/scope3_calculation.py`,`domain/scope3.py`,`domain/scope3_contracts.py` · DOC:CT-PO-P17-IMPLEMENT-07-SCOPE3-ALL-15-CATEGORIES-20250925.md, CT-PO-P17-IMPLEMENT-09-COMPLETE-SCOPE2-SCOPE3-ALL15-20250925.md |
| FTR-166 | Scope 3 API persistence surface | customer / consultant | IMPLEMENTED_AND_WIRED — thin surface | API:`/api/v3/scope3`(**1 endpoint**), `/api/v3/emissions`(10) · BE:`api/v3_scope3.py` · DOC:CT-PO-P17-IMPLEMENT-08-SCOPE3-API-PERSISTENCE-COMPLETION-20250925.md |
| FTR-167 | Category-specific dimensions (transport boundary, waste origin, transaction provider) | platform | IMPLEMENTED_AND_WIRED (repository) — absent where P17 unapplied | MIG:`20261010000000_p17a_…` (`transport_boundary`,`waste_origin`, CHECKs) + `20261014000000_p17_10_…` (`scope3_method`,`transaction_provider` on snapshots **and** emissions_logs) |
| FTR-168 | Scope 3 governed capability mapping (per-category support status) | product / customer | IMPLEMENTED_AND_WIRED | DOC:CT-PO-P17-K-… §11 and CT-PO-P17-L-… Scope-3 block (categories 1–15 with governed values; rollup 4/6/3/2) · BE:`domain/capability_catalogue.py` (`scope3_capability_rollup`) |
| FTR-169 | Scope 3 estimation & assumption support | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — clone-only table | MIG:`20261013000000_p17h_estimation_and_assumption_records.sql` (`estimation_records` + 4 org policies, verified by file read) · BE:`domain/estimation.py`,`data/estimation_records.py` |

### Domain 28 — Accounting Dimensions (FTR-170…174)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-170 | Accounting-dimension columns on results (method, category, energy type, quality, facility, boundaries) | platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA clone-only | MIG:`20261010000000_p17a_…` adds 10 columns to `calculation_snapshots` **and** `emissions_logs`: `scope2_method, scope3_category, energy_type, data_quality, facility_id, transport_boundary, waste_origin, source_snapshot_id, performed_by_organization_id, acting_for_organization_id` + 8 indexes · verified present only in `ct_p17k_20260926` |
| FTR-171 | Accounting-context API (dimension read/write with authorization) | customer / consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/accounting`(8) · BE:`api/v3_accounting_context.py`,`api/accounting_context_auth.py`,`data/accounting_context.py` |
| FTR-172 | Unified CAMS domain & accounting boundaries | platform | IMPLEMENTED_AND_WIRED | BE:`domain/cams.py` · DOC:CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md |
| FTR-173 | Consolidation approach & organisation type as accounting context | Owner / Admin | IMPLEMENTED_AND_WIRED (repository) — SCHEMA clone-only | MIG:`20261010000000_p17a_…` §5 (`organizations.consolidation_approach`,`organization_type` + index) |
| FTR-174 | Product-contract reporting dimensions (scope3 method, transaction provider, quality) on logs & snapshots | platform | IMPLEMENTED_AND_WIRED (repository) — SCHEMA clone-only | MIG:`20261014000000_p17_10_…` — verified by file read: `ALTER TABLE calculation_snapshots` L72, `ALTER TABLE emissions_logs` L84, six CHECKs, 2 indexes |

### Domain 29 — Estimation & Assumptions (FTR-175…178)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-175 | Estimation records (P17-H) | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — SCHEMA clone-only | MIG:`20261013000000_p17h_estimation_and_assumption_records.sql` (`estimation_records`, 4 org policies) · BE:`domain/estimation.py`,`data/estimation_records.py` |
| FTR-176 | Assumption sets / basis-of-preparation capture | customer / consultant | PARTIALLY_IMPLEMENTED — no `assumption_sets` table found | Live probe: `assumption_sets` absent in all DBs tested; assumption semantics appear inside `estimation_records`/disclosure narrative |
| FTR-177 | Double-counting detectors | platform | IMPLEMENTED_AND_WIRED | BE:`domain/estimation.py` · DOC:CT-PO-P17-IMPLEMENT-MASTER-01-IMPLEMENTATION-REPORT-20250925.md |
| FTR-178 | Estimation disclosure narrative integration | product | IMPLEMENTED_AND_WIRED | MIG:`20260918000000_p8_b4_narrative_overlay.sql` · BE:`services/disclosure_narrative.py`,`domain/disclosure_narrative.py` |

### Domain 30 — Calculations (FTR-179…187)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-179 | Server-authoritative calculation engine | platform | IMPLEMENTED_AND_WIRED | BE:`engines/calculation.py`,`domain/calculation.py`,`backend/process_emissions.py` · DOC:AGENTS §25 |
| FTR-180 | Immutable calculation snapshots | platform | IMPLEMENTED_AND_WIRED | MIG:`20260807020000_add_calculation_snapshots.sql` · DB:`calculation_snapshots` (flagship present) · BE:`data/*` + `domain/calculation.py` |
| FTR-181 | Calculation idempotency (deterministic request id) | platform | IMPLEMENTED_AND_WIRED (repository) — unique index clone-only | MIG:`20261009000000_p16r7_calculation_request_idempotency.sql` (`CREATE UNIQUE INDEX uq_calc_snapshots_request_id`, verified by file read) · live probe: `calculation_request_id` column absent outside `ct_p17k`-class clones |
| FTR-182 | Result reportability lifecycle | platform / CT / customer | IMPLEMENTED_AND_WIRED (repository) — `reportability_status` absent in 4 of 5 DBs tested | MIG:`20261008000000_p16r5_result_reportability_lifecycle.sql` (`ALTER TABLE calculation_snapshots` ×5 blocks, `emissions_logs` ×5 blocks, 2 indexes) · live probe: `reportability_status` present only in `ct_p17k_20260926` |
| FTR-183 | Emissions logs (result ledger) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260807030000_add_emissions_logs_snapshot.sql` · DB:`emissions_logs` (flagship present) |
| FTR-184 | Calculation actor attribution (Gate 4) | platform / CT staff | IMPLEMENTED_AND_WIRED | MIG:`20260905000000_gate4_actor_provenance.sql` |
| FTR-185 | Machine/automation provenance gates (Gate 5 T1/T6) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260905010000_gate5_t1_automation_provenance.sql`,`20260905020000_gate5_t6_automation_write_once_guard.sql` |
| FTR-186 | Human-after-automation attribution + extracted output (Gate 6 W1) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260906010000_gate6_w1_automation_extracted_output.sql` |
| FTR-187 | Calculation reproducibility/verification record for the demo journey | CT staff / product | IMPLEMENTED_AND_WIRED (independently verified instance) | DOC:OHD R-A independent verification (snapshot `af640887`, log `eb88e764`, arithmetic 12181.4 × 0.2027 = 2469.169780) as cited in DOC:docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md §15 |

### Domain 31 — Workflow & Processing Jobs (FTR-188…196)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-188 | Durable automatic document processing worker | platform | IMPLEMENTED_AND_WIRED | MIG:`20260829000000_v3m9_durable_automatic_processing.sql` · BE:`workers/automatic_processing.py`,`services/automatic_processing.py`,`domain/automatic_processing.py` · DOC:AGENTS §19 |
| FTR-189 | Processing workflow / job state machine | platform | IMPLEMENTED_AND_WIRED | BE:`engines/processing_workflow.py`,`engines/workflow.py`,`domain/workflow.py` · API:`/api/v3/processing/workflow`(20) |
| FTR-190 | Processing queue, steps, logs and time log (legacy pipeline) | CT operator | IMPLEMENTED_AND_WIRED (legacy) | DB:`processing_queue`,`processing_steps`,`processing_logs`,`processing_time_log`,`processing_assignments`,`processing_audit_trail` (all present in flagship) |
| FTR-191 | Dual-origin workflow (V1.2) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260902020000_v1_2_dual_origin_workflow.sql` · DOC:CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md |
| FTR-192 | Work-item assignment foundation (WS4 Gate 3 / D38) | CT staff admin | IMPLEMENTED_AND_WIRED | MIG:`20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` · DB:`work_item_assignments` · BE:`services/work_items.py` · DOC:CARBONTALLY_WS4_GATE3_WS4A_ITEM_ASSIGNMENT_FOUNDATION_REPORT.md |
| FTR-193 | Manual-processing governance grants (FIN-06) | CT staff admin | IMPLEMENTED_AND_WIRED | MIG:`20260927000000_p8_fin06_manual_processing_governance.sql` · DB:`manual_processing_grants` (clone-only) · API:`/api/v3/admin/manual-processing`(4) |
| FTR-194 | Processing-mode provenance (D7) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260910120000_p6_2d_consultant_provenance.sql` · BE:`domain/processing_origin.py` |
| FTR-195 | Intake batches (upload/import batch tracking) | customer / CT operator | IMPLEMENTED_AND_WIRED | MIG:`20260807000000_add_import_batches.sql` · DB:`upload_batches`,`import_batches` · API:legacy `/api/upload`, admin `/batches` screens |
| FTR-196 | Operational health, alerting and intelligence (X1/X2/X4) | CT operations | IMPLEMENTED_AND_WIRED / backend-only in part | UI:`ops/OperationalHealthTab.jsx` · BE:`services/operational_alerting.py`(CODE_ONLY per census CAP-120), `services/operational_intelligence.py`(CAP-121), `domain/operational_health.py` · DOC:CARBONTALLY_PHASE8X_* contracts (X1 20260914, X2 20260914, X4 20260914) |

### Domain 32 — Approvals (FTR-197…201)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-197 | Customer final approval gate (owner/admin only) | Customer Owner / Admin | IMPLEMENTED_AND_WIRED | BE:`require_org_admin` guard (DOC:ADMIN_CONTROL_PLANE §6 D-P2-03) · API:`/api/v3/review`(6) · T:regression proving QC/staff cannot approve |
| FTR-198 | Approval requests & decisions records | customer / CT | IMPLEMENTED_AND_WIRED | DB:`approval_requests`,`approval_decisions` (both present in flagship) |
| FTR-199 | Customer verification workflow | customer | IMPLEMENTED_AND_WIRED | API:legacy `/api/customer/verifications`(13) + `/api/v3/verifications`(4) · DB:`customer_verifications`,`verification_logs`,`verification_activity_log` |
| FTR-200 | QC approval boundary enforcement (QC never customer-approves) | CT QC | IMPLEMENTED_AND_WIRED | DOC:ADMIN_CONTROL_PLANE §6 D-P2-03 · MIG:`20260902020000_v1_2_…` |
| FTR-201 | Approval evidence & audit capture | platform | PARTIALLY_IMPLEMENTED | Approval records exist (`approval_requests`,`approval_decisions`, flagship-present); whether approvals carry evidence-line linkage was **not established** in this pass (columns not inspected) → recorded as an unresolved verification item (§5) |

### Domain 33 — Audit & Auditability (FTR-202…210)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-202 | Legacy `audit_logs` ledger (actor, org, action, before/after, IP, UA) | CT staff / org admin | IMPLEMENTED_AND_WIRED | Columns read live (17): `user_id, staff_id, organization_member_id, organization_id, action_type, resource_type, resource_id, action, description, ip_address, user_agent, old_data, new_data, changes, metadata, created_at` · `audit_logs` present in all 6 DBs probed |
| FTR-203 | `audit_trail` ledger (table/record-level change capture) | platform / auditor | IMPLEMENTED_AND_WIRED | Columns read live (13): `action_type, table_name, record_id, performed_by, performed_at, old_data, new_data, changes, ip_address, user_agent, metadata` · P7 immutability MIG:`20260912000000_p7_audit_immutability_and_indexes.sql` |
| FTR-204 | Immutability hardening for audit + activity tables (WS1 / DB-0001, P7) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260831020000_audit_activity_immutability.sql`,`20260912000000_p7_audit_immutability_and_indexes.sql` · DOC:AGENTS §12 (immutability not inferred from the table name — enforcement is via trigger/grants in these migrations) |
| FTR-205 | Activity feed and activity logging | customer / CT staff | IMPLEMENTED_AND_WIRED | DB:`activity_logs`,`activity_feed`,`user_activity_log`,`staff_activity_log` (all present in flagship) · UI:`components/ActivityFeed.jsx` · UI:`admin/ActivityTab.jsx` |
| FTR-206 | Domain events (backend event bus ledger) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260807040000_add_domain_events.sql` · DB:`domain_events` · BE:`infra/event_bus.py`,`data/events.py` |
| FTR-207 | Audit console (admin + ops tabs) | CT staff admin / auditor | IMPLEMENTED_AND_WIRED | UI:`ops/AuditConsoleTab.jsx` · UI:`admin/AuditTab.jsx` · T:`audit-console-tab.test.jsx` · API:`/api/v2/admin/audit`(4), legacy `/api/admin/audit-logs`(12) |
| FTR-208 | Audit-readiness & audit-activity reporting endpoints | auditor / customer owner | IMPLEMENTED_AND_WIRED | API:`/api/v3/reporting/audit-readiness`, `/api/v3/reporting/audit-activity`, `/api/v3/ops/reporting/audit`, `/api/v3/ops/entities/{entity_id}/audit-activity` |
| FTR-209 | Audit package export (`audit-package.json`) | auditor | IMPLEMENTED_AND_WIRED | Endpoint path `GET /audit-package.json` verified present in `backend/api/*.py` (module not attributed in this pass) · API:`/api/v3/exports`(4) · BE:`data/exports.py` |
| FTR-210 | Audit-log retention configuration | CT staff admin | PARTIALLY_IMPLEMENTED — destructive enforcement deferred | DB:`system_settings.audit_log_retention_days` = **1** (read live; suspicious value flagged in §5) · BE:`services/retention.py` · DOC:ADMIN_CONTROL_PLANE §6 D-P2-04 |

### Domain 34 — Reporting (FTR-211…222)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-211 | Report lifecycle & report catalogue | customer / CT | IMPLEMENTED_AND_WIRED | MIG:`20260913000000_p8_report_lifecycle_status.sql` · DB:`report_versions`,`report_templates`,`report_generation_queue`,`report_comments` · API:`/api/v3/reports`(14) · UI:`reports/ReportsPage.jsx`, routes `/reports`,`/reports/:id` |
| FTR-212 | Report lifecycle state panel (status machine) | customer / CT | IMPLEMENTED_AND_WIRED | UI:`reports/ReportLifecyclePanel.jsx` · T:`report-lifecycle-panel.test.jsx`,`report-meta-layout.test.jsx`,`reports-page.test.jsx` |
| FTR-213 | Report generation engine | platform | IMPLEMENTED_AND_WIRED | BE:`engines/report_generation.py`,`backend/report_generator.py`,`services/report_artefact_storage.py` |
| FTR-214 | Report exports & export history | customer / CT | IMPLEMENTED_AND_WIRED | DB:`export_history` · API:`/api/v3/exports`(4) · BE:`data/exports.py` |
| FTR-215 | Legacy reporting suite (customer reports, drafts, analytics) | customer / CT | IMPLEMENTED_AND_WIRED (legacy) | API:legacy `/api/reports`(23), `/api/legacy-reports`, `/api/analytics`, `/api/exports` · BE:`backend/report_generator.py` |
| FTR-216 | Reporting intelligence API (customer dashboard, emissions trend, member activity, consultant portfolio) | customer / consultant / CT | IMPLEMENTED_AND_WIRED | API:`/api/v3/reporting`(15): `customer-dashboard`, `emissions-trend`, `member-activity`, `audit-readiness`, `audit-activity`, `consultant-portfolio`, `consultant-client/{id}`, `consultant-client/{id}/audit-activity` |
| FTR-217 | Operational reporting (aging, QC, review, platform, audit) | CT operations | IMPLEMENTED_AND_WIRED | API:`/api/v3/ops/reporting/{aging,qc,review,platform,audit}` (53 endpoints in `v3_operations.py`) |
| FTR-218 | Report comments / collaboration | customer / CT | IMPLEMENTED_AND_WIRED | DB:`report_comments` (flagship present) · API:`/api/v3/reports/*` |
| FTR-219 | Intensity catalogue & ratios (B3) | customer / consultant | IMPLEMENTED_AND_WIRED | MIG:`20260917000000_p8_b3_intensity_catalogue.sql`,`20260917010000_p8_b3_intensity_ratios.sql` · DB:`disclosure_intensity_denominator_types`,`disclosure_intensity_ratios` (qa133 yes; flagship no) |
| FTR-220 | Report finalisation & frozen artefact (B4) | customer / CT | IMPLEMENTED_AND_WIRED | MIG:`20260919000000_p8_b4_frozen_artefact.sql` · DB:`report_version_artifacts` (qa133 yes; flagship no) · DOC:docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md |
| FTR-221 | Emissions reporting/intelligence surface | customer / consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/emissions`(10) · UI:`customer/EmissionsPage.jsx`, route `/emissions` |
| FTR-222 | Regulatory framework requirement verification register | product | DOCUMENTED_ONLY | DOC:CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md (§4 source register; §9.0 verified framework versions) |

### Domain 35 — Report Versions & Frozen Artefacts (FTR-223…225)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-223 | Report versions with single-valued `is_current` integrity (S2) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260921000000_p8_s2_is_current_single_valued.sql` · DB:`report_versions` (flagship present) |
| FTR-224 | Version artefacts (stored rendered files) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260919000000_p8_b4_frozen_artefact.sql` · DB:`report_version_artifacts` (qa133 yes) · BE:`data/report_artefacts.py`,`services/report_artefact_storage.py` |
| FTR-225 | Frozen-artefact immutability (finalised calculation evidence) | platform / auditor | PARTIALLY_IMPLEMENTED | `audit_trail` immutability trigger claimed in OHD audit (§15 P0-REG-F24) with the note "Lab holds exactly one authoritative emission record" · DOC:docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md |

### Domain 36 — Disclosures (FTR-226…233)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-226 | Disclosure model foundation (frameworks, versions, requirement mappings) | product / CT | IMPLEMENTED_AND_WIRED | MIG:`20260914000000_p8_b1_disclosure_model_foundation.sql` · DB:`disclosure_frameworks`,`disclosure_framework_versions`,`disclosure_requirement_versions`,`disclosure_requirement_mappings` (qa133 + clones yes; flagship **no**) |
| FTR-227 | Governed requirement-version capability rows (P17-K reference data) | product | IMPLEMENTED_AND_WIRED | MIG:`20261020000000_p17k_governed_capability_catalogue.sql` (reference-data only; creates no object) · DB rows: `disclosure_requirement_versions` = **55** in `ct_p17k_20260926` (read live); table absent elsewhere |
| FTR-228 | Disclosure values & value-evidence | customer / CT | IMPLEMENTED_AND_WIRED | DB:`disclosure_values`,`disclosure_value_evidence` (qa133 yes) · MIG:`20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` |
| FTR-229 | Disclosure narrative overlay (B4) | customer / CT staff | IMPLEMENTED_AND_WIRED | MIG:`20260918000000_p8_b4_narrative_overlay.sql` · DB:`disclosure_narrative_entries` · BE:`services/disclosure_narrative.py` |
| FTR-230 | Disclosure projection engine (effective class derived, never stored) | platform | IMPLEMENTED_AND_WIRED | BE:`domain/disclosure_projection.py` (`derive_effective_class`),`services/disclosure_projection.py`,`data/disclosure_projection.py` · DOC:CT-PO-P17-K-… §8.4 |
| FTR-231 | Disclosure report purposes & instance binding | customer / CT | IMPLEMENTED_AND_WIRED | DB:`disclosure_report_purposes`,`disclosure_report_purpose_versions`,`disclosure_report_instance_binding`,`disclosure_purpose_requirements` (qa133 yes) |
| FTR-232 | Disclosure applicability assessments | customer / CT | IMPLEMENTED_AND_WIRED | DB:`disclosure_applicability_assessments` (qa133 yes) · DOC:CT-PO-P17-DECISION-02-RECONCILE-CAMS-DISCLOSURE-APPLICABILITY-20250925.md |
| FTR-233 | Disclosure finalisation service | CT / customer | IMPLEMENTED_AND_WIRED | BE:`services/disclosure_finalisation.py`,`api/v3_disclosure.py`(15 endpoints) |

### Domain 37 — Insight (FTR-234…242)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-234 | Insight Layer-1 persistence (I1) | customer / consultant | IMPLEMENTED_AND_WIRED (repository) — schema absent in every durable DB tested | MIG:`20261001000000_p8_i1_insight_persistence.sql` · DB:`carbontally_insight_conversations`,`carbontally_insight_messages`,`carbontally_insight_tool_calls` (present in `ct_p17k_20260926` and `carbontally_test`; **absent** in flagship, `ct_local_93d5cdd`, `carbontally_qa_phase8`) · BE:`data/insight.py` |
| FTR-235 | Insight Layer-1 authorization boundary (I2, author-kind policy) | customer | IMPLEMENTED_AND_WIRED | MIG:`20261002000000_p8_i2_insight_authorization.sql` · BE:`api/insight_authz.py` · DOC:OHD-P8-I2-INSIGHT-AUTHORIZATION-INDEPENDENT-VERIFICATION-20260921.md |
| FTR-236 | Insight tool catalogue (I3) — four ratified read-only tools | customer | IMPLEMENTED_AND_WIRED | BE:`domain/insight_tool.py`,`services/insight_tools.py`,`api/v3_insight_tools.py`(3) · DOC:OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921.md |
| FTR-237 | Insight Layer-2 interaction orchestration (I4) | customer | IMPLEMENTED_AND_WIRED | MIG:`20261003000000_p8_i4_insight_interactions.sql` · DB:`carbontally_insight_interactions` · API:`/api/v3/insight/interactions`(3) · DOC:CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md |
| FTR-238 | Insight query planner, context assembly, rate limiting, concurrency leases | platform | IMPLEMENTED_AND_WIRED | BE:`services/insight_query_planner.py`,`services/insight_context.py`,`services/insight_rate_limit.py` · DB:`insight_rate_limit_buckets`,`insight_concurrency_leases` (clone-only) · MIG:`20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` |
| FTR-239 | Insight temporal comparison (P2) | customer | IMPLEMENTED_AND_WIRED | MIG:`20261006000000_p8_insight_temporal_comparison.sql` · UI:`insight/InsightComparison.jsx` · T:`insight-comparison.test.jsx` |
| FTR-240 | Insight data-quality + reproducibility (P3) | customer | IMPLEMENTED_AND_WIRED | MIG:`20261007000000_p8_insight_data_quality_reproducibility.sql` · BE:`domain/insight_quality.py` |
| FTR-241 | Insight customer UI (page, references, answer-state model) | customer | IMPLEMENTED_AND_WIRED | UI:`insight/InsightPage.jsx`,`InsightReferences.jsx`,`InsightAnswerState.jsx`,`InsightInteraction.jsx`, route `/insight` · T:`insight-page.test.jsx`,`insight-references.test.jsx` |
| FTR-242 | Insight AI content history (AI answer auditability) | CT staff / auditor | IMPLEMENTED_AND_WIRED | DB:`ai_content_history` (present in flagship, qa133, clones) · DOC:CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md |

### Domain 38 — Dashboards & Analytics (FTR-243…248)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-243 | Customer dashboard (org-scoped KPIs) | Owner / Admin / Member | IMPLEMENTED_AND_WIRED | UI:`customer/DashboardPage.jsx`; `<Route path="/dashboard/*">`,`/home` · DB:`dashboard_metrics` · API:legacy `/api/customer/dashboard`(12) |
| FTR-244 | Consultant client dashboard (portfolio → client drill-down) | consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/reporting/consultant-portfolio`, `/consultant-client/{client_id}/dashboard` · UI:`consultant/ConsultantPage.jsx` |
| FTR-245 | PE manager dashboard (F1) | PE manager | IMPLEMENTED_AND_WIRED | UI:`ops/PEManagerDashboard.jsx`, route `/pe` · API:`/api/v3/pe`(20) |
| FTR-246 | CT operations dashboard | CT operations | IMPLEMENTED_AND_WIRED | UI:`ops/OpsDashboard.jsx`,`ops/OpsAssignmentsTab.jsx` · API:`/api/v3/ops/*` |
| FTR-247 | Emissions trend & emissions intelligence | customer / consultant | IMPLEMENTED_AND_WIRED | API:`/api/v3/reporting/emissions-trend`, `/api/v3/emissions`(10) · UI:`customer/EmissionsPage.jsx` |
| FTR-248 | Benchmarking domain | customer / product | IMPLEMENTED_BACKEND_ONLY | BE:`domain/benchmarking.py`,`engines/benchmarking.py` — no API/UI surface located in this pass |

### Domain 39 — Notifications (FTR-249…254)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-249 | In-app notifications | all authenticated users | IMPLEMENTED_AND_WIRED | API:`/api/v3/notifications`(3), legacy `/api/notifications` · DB:`notifications` (flagship present) · UI:`NotificationsPage.jsx` (route `/notifications`),`v3/pe/PeNotificationsBell.jsx` |
| FTR-250 | Notification delivery ledger | platform | IMPLEMENTED_AND_WIRED | DB:`notification_delivery`,`notification_templates` (flagship present) · MIG:`20260902050000_phase5_notification_event_key.sql` |
| FTR-251 | Notification event-key production (WS3 / D40) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260902050000_phase5_notification_event_key.sql` · DOC:CARBONTALLY_PHASE5_WS3_D40_IMPLEMENTATION_REPORT.md |
| FTR-252 | Email delivery via Resend | platform | IMPLEMENTED_AND_WIRED | BE:`services/email_service.py`,`services/v3_email.py`,`utils/email.py` · Config `RESEND_API_KEY`,`FOUNDER_EMAIL` (`backend/config.py` L19–20) · DB:`email_logs` · DOC:AGENTS §5 (Resend) |
| FTR-253 | Notification preferences UI | customer | IMPLEMENTED_AND_WIRED | UI:`components/NotificationSettings.jsx` |
| FTR-254 | Notification templates management | CT staff admin | IMPLEMENTED_AND_WIRED | DB:`notification_templates`,`email_templates` · API:legacy `/api/admin/email-templates`(8) |

### Domain 40 — Messaging (FTR-255…262)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-255 | Authenticated messaging (N1 model) | customer / consultant / CT | IMPLEMENTED_AND_WIRED | DB:`conversations`,`conversation_participants`,`messages` (all flagship present) · API:`/api/v3/messaging`(10) · UI:`customer/MessagingPage.jsx` (route `/messaging`) · DOC:AGENTS §28 |
| FTR-256 | Conversation participant uniqueness (MSG-1) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260828000000_v3m8_messaging_unique_participants.sql` |
| FTR-257 | PE ↔ CarbonTally operations messaging (D39) | PE users / CT ops | IMPLEMENTED_AND_WIRED | MIG:`20260902040000_phase5_pe_operational_messaging.sql` · UI:`ops/OpsPeMessagingTab.jsx`,`v3/pe/PeMessagingPage.jsx` (route `/pe/messages`) · DOC:CARBONTALLY_PHASE5_WS2_D39_IMPLEMENTATION_REPORT.md |
| FTR-258 | Consultant ↔ active-client messaging | consultant + client | IMPLEMENTED_AND_WIRED | UI:`consultant/ClientMessagingTab.jsx` · DOC:AGENTS §28 (authorised active-client only) |
| FTR-259 | Operations internal messaging | CT ops | IMPLEMENTED_AND_WIRED | UI:`ops/OpsMessagingTab.jsx` · API:`/api/v3/messaging`(10) |
| FTR-260 | Messaging activity logging | platform / auditor | IMPLEMENTED_AND_WIRED | DB:`message_activity_log`,`conversation_activity_log` (flagship present) |
| FTR-261 | Realtime subscription support (Supabase Realtime) | all users | IMPLEMENTED_AND_WIRED — live-channel verification not possible without the app running | BE:`backend/supabase/` + frontend `supabaseClient.js` · DOC:AGENTS §5 · census CAP-100 |
| FTR-262 | Public CarbonTally Assistant chat (visitor) | public visitor | IMPLEMENTED_AND_WIRED (legacy) | API:legacy `/api/communication`(22) · UI:`frontend/src/components/chat/**` · DB:`conversations`,`messages`,`ai_content_history` · DOC:AGENTS §29 |

### Domain 41 — Storage (FTR-263…266)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-263 | Private documents bucket with storage policies (D32) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260823000000_d32_private_documents_storage.sql` · DOC:AGENTS §68 (signed-URL sensitivity) |
| FTR-264 | Report artefact bucket provisioning & retention | platform / CT | IMPLEMENTED_AND_WIRED | BE:`services/report_artefact_storage.py` · DOC:docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md |
| FTR-265 | Storage usage metering per organisation | platform / commercial | IMPLEMENTED_AND_WIRED | DB:`billing_storage_usage` (flagship present) · MIG:`20260824030000_d37_master_commercial_billing.sql` |
| FTR-266 | Signed-URL issuance policy (authorization before URL) | platform | DOCUMENTED_ONLY — enforcement location not proven in this pass | DOC:AGENTS §68 · BE:`services/storage.py` |

### Domain 42 — Integrations (FTR-267…272)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-267 | Admin-configurable Google Analytics 4 bootstrap | CT staff admin / product | IMPLEMENTED_AND_WIRED | DB:`system_settings.analytics_ga4` (read live) · UI:`components/AnalyticsBootstrap.jsx` · T:`AnalyticsBootstrap.test.jsx` · DOC:CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md |
| FTR-268 | PostHog analytics lineage | product | HISTORICAL_ONLY | DOC:historical tree `posthog-self-driving-report.md`; no PostHog code located in the release tree |
| FTR-269 | Resend email provider integration | platform | IMPLEMENTED_AND_WIRED | BE:`services/email_service.py`,`services/v3_email.py` · `backend/config.py` L19 |
| FTR-270 | LLM / AI runtime integration (OpenRouter-class) | platform | IMPLEMENTED_AND_WIRED | BE:`infra/llm_client.py`,`infra/ai_runtime.py`,`services/ai_document_extraction.py` · DOC:AGENTS §57 (key via environment only; never printed) |
| FTR-271 | Webhook configuration surface (retry/timeout settings) | CT staff admin | SCHEMA_ONLY — settings exist, no dispatcher found | `system_settings` columns `webhook_retry_count`,`webhook_retry_delay`,`webhook_timeout_seconds` (read live); no webhook dispatcher module located in `backend/**` in this pass |
| FTR-272 | DEFRA/SEAI factor import commands (historical CLI lineage) | CT operator | HISTORICAL_ONLY | Historical tree `src/commands/import_defra.py`,`src/commands/import_seai.py`; superseded by in-app admin import + `/api/v2/admin/providers` |

### Domain 43 — API Platform (FTR-273…280)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-273 | V3 API surface (59 modules / 370 endpoints) | all actors | IMPLEMENTED_AND_WIRED | `backend/api/*.py` enumerated; registered in `backend/api/router.py`; mounted at `backend/main.py` L265 |
| FTR-274 | Legacy v2.1 API surface (401 endpoints across 40+ routers) | all actors | IMPLEMENTED_AND_WIRED (legacy; retirement PO-undecided POD-005) | `backend/routes/**`; mounted `backend/main.py` L212–259 |
| FTR-275 | Dual router mount (both API generations served in one app) | platform | IMPLEMENTED_AND_WIRED | DOC:AGENTS §79; census CAP-150; verified `main.py` registers both |
| FTR-276 | Dual ASGI entrypoints (`main.py`, `main_v2.py`) | platform | IMPLEMENTED_AND_WIRED | Files present in `backend/`; census CAP-151 |
| FTR-277 | Consistent error envelope & request correlation contract | platform | IMPLEMENTED_AND_WIRED | DOC + code in `backend/api/router.py` docstring + `core/exceptions.py`,`api/middleware.py` |
| FTR-278 | Health / liveness endpoints | platform | IMPLEMENTED_AND_WIRED | API:`/api/v2/health`(`api/router.py`), `/api/v3/health`(1) · DOC:production deployment readiness |
| FTR-279 | Rate limiting middleware | platform | IMPLEMENTED_AND_WIRED | BE:`backend/middleware/rate_limit.py` · config columns `api_rate_limit`,`api_rate_limit_burst` |
| FTR-280 | API documentation artefacts (endpoints summary, OpenAPI) | developers | IMPLEMENTED_AND_WIRED | Files `API_ENDPOINTS.md` (both trees), `docs/architecture/API_DOCUMENTATION.md`,`API_SUMMARY.md`; live spec `https://carbontally-api.onrender.com/openapi.json` (documented, not fetched) |

### Domain 44 — Operations (FTR-281…289)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-281 | Operations console shell & navigation | CT operations | IMPLEMENTED_AND_WIRED | UI:`ops/OperationsPage.jsx` (route `/ops`) · T:`operations-page-assignment-gating.test.jsx` |
| FTR-282 | Operator queue → focused workspace routing | CT operator | IMPLEMENTED_AND_WIRED | UI:`ops/OperatorQueue.jsx`,`ops/OperatorItemPage.jsx` (route `/ops/items/:itemId`) · DOC:AGENTS §38 (workspace UX) |
| FTR-283 | PE work items and assignments surface | PE users / CT ops | IMPLEMENTED_AND_WIRED | API:`/api/v3/pe`(20) · UI:`pe/PeWorkItemsPage.jsx`,`pe/interfaces` (routes `/pe`,`/pe/assignments`) · T:`pe-work-items-page.test.jsx` |
| FTR-284 | PE routed item workspace (G5) | PE users | IMPLEMENTED_AND_WIRED | UI:`ops/PEEntityItemPage.jsx`, route `/pe/items/:entityId/:itemId` · UI:`ops/EntityExtractionWorkspace.jsx` |
| FTR-285 | Operations issue triage | CT ops | IMPLEMENTED_AND_WIRED | UI:`ops/IssuesTriageTab.jsx` · API:`/api/v3/issues/admin/open` |
| FTR-286 | Ops assignments management (queue assignment gating) | CT staff admin | IMPLEMENTED_AND_WIRED | UI:`ops/OpsAssignmentsTab.jsx` · T:`ops-assignments-tab.test.jsx` |
| FTR-287 | Staff roster & presence for operations | CT ops | IMPLEMENTED_AND_WIRED | UI:`ops/StaffRoster.jsx` · DB:`staff_profiles`,`user_presence` |
| FTR-288 | SLA definitions & compliance tracking | CT ops | IMPLEMENTED_AND_WIRED (data) — enforcement/reporting path not proven | DB:`sla_definitions`,`sla_compliance` (both flagship present) · UI:`ops/SlaTab.jsx` · census CAP-123 records SLA reporting as CODE-ONLY |
| FTR-289 | Ops commercial tab (entitlements/commercial visibility) | CT staff admin | IMPLEMENTED_AND_WIRED | UI:`ops/CommercialTab.jsx` · API:`/api/v3/commercial`(24) |

### Domain 45 — Admin Console (FTR-290…296)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-290 | Admin customer & organisation administration | CT staff admin | IMPLEMENTED_AND_WIRED (legacy surface, deprecated D-P2-02) | AD:`pages/admin/Customers.js`,`Organizations.js`,`CustomerDetailModal.js` · API:legacy `/api/admin/*` |
| FTR-291 | Admin user administration | CT staff admin | IMPLEMENTED_AND_WIRED (legacy surface) | AD:`pages/admin/Users.js` · API:legacy admin users routes · DB:`users`,`user_invitations` |
| FTR-292 | Admin batch & upload review | CT operator | IMPLEMENTED_AND_WIRED (legacy surface) | AD:`pages/admin/Batches.js` · DB:`upload_batches`,`import_batches` |
| FTR-293 | Admin dashboard summary & recent activity | CT staff admin | IMPLEMENTED_AND_WIRED (legacy surface) | AD:`pages/admin/Dashboard.js`,`components/admin/RecentActivity.js`,`ActivityChart.js`,`StatCard.js` |
| FTR-294 | Admin staff review queue & review workflow | CT reviewer | IMPLEMENTED_AND_WIRED (legacy surface) | AD:`pages/admin/Reviews.js`,`StaffReviewQueue.jsx`,`components/admin/ReviewWorkflow.js` · API:legacy `/api/admin/reviews`(12) |
| FTR-295 | Admin live queue statistics | CT operator | IMPLEMENTED_AND_WIRED (legacy surface) | AD:`pages/admin/LiveQueueStats.jsx`,`components/admin/LiveQueueStats.jsx` |
| FTR-296 | Legacy admin deployment state (admin build served by rewrite) | platform | PARTIALLY_IMPLEMENTED — operational configuration PO-undecided (POD-011) | DOC:ADMIN_CONTROL_PLANE §2 ("served only by the deployment rewrite") · DOC:census §11.2 POD-011 (Supabase build settings) |

### Domain 46 — Security, Identity & Access Control (FTR-297…307)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-297 | Supabase Auth integration (email/password + Google OAuth) | all users | IMPLEMENTED_AND_WIRED — live provider configuration not verifiable without the running app | BE:`backend/auth.py`, `backend/supabase/**` · FE:`frontend/src/supabaseClient.js`,`AuthCallback.js` · DOC:AGENTS §69 (TOTP MFA part of the architecture; production enforcement is a separate deployment decision) |
| FTR-298 | JWT verification & request identity/context resolution | platform | IMPLEMENTED_AND_WIRED | BE:`backend/auth.py` (token decode, current-user dependency),`backend/api/dependencies.py`,`backend/api/middleware.py` |
| FTR-299 | Unified principal identity model (users, staff profiles, membership) | all roles | IMPLEMENTED_AND_WIRED | DB:`users`,`staff_profiles`,`organization_members` · live counts in flagship: `organization_members` **1,125** rows · BE:`data/roles.py` |
| FTR-300 | Organisation membership uniqueness integrity (V3M10) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260831000000_v3m10_org_membership_unique.sql` |
| FTR-301 | Customer role model (owner / admin / member / viewer) | customer users | IMPLEMENTED_AND_WIRED — role *names* verified live; the legacy `roles` catalogue table is EMPTY (0 rows) = SCHEMA_ONLY, so the authoritative role source is membership rows, not `roles` | live role values observed in flagship membership data: `owner,admin,member,viewer` · DB:`roles` (0 rows) · DOC:AGENTS §9 |
| FTR-302 | System Admin role model (V3M8) | CT system admin | IMPLEMENTED_AND_WIRED | MIG:`20260828010000_v3m8_system_admin_role_model.sql` · DOC:AGENTS §13,§14 (admin ≠ universal shortcut; System Admin is distinct) |
| FTR-303 | PE Manager & PE staff role model (V3M8) | PE users | IMPLEMENTED_AND_WIRED | MIG:`20260828020000_v3m8_pe_manager_role.sql` · DOC:AGENTS §12 |
| FTR-304 | Consultant authorization, active-client grant & revocation | consultant / client | IMPLEMENTED_AND_WIRED | MIG:`20260821000000_d20_d15_active_consultant_grant.sql`,`20260831040000_consultant_revocation_roles.sql`,`20260906090000_p6_1c_consultant_engagement.sql`,`20260906100000_p6_2a_consultant_processing_permissions.sql`,`20260910120000_p6_2d_consultant_provenance.sql` · BE:`backend/api/consultant_auth.py` |
| FTR-305 | Domain-specific authorization guard modules (per-surface authz) | all roles | IMPLEMENTED_AND_WIRED | BE:`backend/api/{operations_auth,pe_auth,consultant_auth,insight_authz,accounting_context_auth,manual_processing_auth}.py`,`backend/auth.py`,`backend/data/roles.py`,`backend/routes/admin/permissions.py` |
| FTR-306 | RLS policy layer, tenant containment & recursion fix | platform | IMPLEMENTED_AND_WIRED | MIGs:`20260803000000_rc2_rls.sql`,`20260807070000_add_new_table_rls.sql`,`20260810050000_v3m6_entity_rls.sql`,`20260822000000_p9_rls_recursion_fix.sql`,`20260920000000_p8_rls_anon_grant_containment.sql`,`20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql`,`20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql`,`20260925000000_p8_rls_4b_group1_enablement.sql`,`20260926000000_p8_d4_emission_factors_internal_containment.sql` · QA:`qa_harness/db/rls.py`,`qa_harness/rules/security.py` |
| FTR-307 | Tenant isolation enforcement at column level (`tenant_org_id` NOT NULL) | platform | IMPLEMENTED_AND_WIRED | MIG:`20260831030000_tenant_org_id_not_null.sql` |

### Domain 47 — Investor Demo & Synthetic Data (FTR-308…313)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-308 | Investor demo identity manifest (1,185 demo identities) | CT / QA / demo operator | IMPLEMENTED_AND_WIRED in the **working repo** — the manifest is **absent from the release tree** at `cb70fd6` | Manifest path `/home/shomonrobie/carbon_tally/tools/seed_investor_demo/DEMO_IDENTITIES.md` (176 lines) · counts as documented there: 1,325 users / 976 orgs / 50 direct customer orgs / 911 client owners / 916 consultant-client rows / 1,127 memberships / 22 staff profiles / 11 processing entities / **1,185 demo identities** · AGENTS §54 names the same path |
| FTR-309 | Investor demo seeder pipeline (manifest → GoTrue users → core/aux/documents/messaging seeds → verify) | CT / QA | IMPLEMENTED_AND_WIRED (working repo) | `/home/shomonrobie/carbon_tally/tools/seed_investor_demo/`: `__main__.py`,`pipeline.py`,`manifest.py`,`seed_core.py`,`seed_aux.py`,`seed_documents.py`,`seed_messaging.py`,`synthetic.py`,`verify.py`,`reset.py`,`safety.py`,`config.py`,`demo_manifest.json` |
| FTR-310 | Demo lab stack (isolated demo environment provisioning) | CT / demo operator | IMPLEMENTED_AND_WIRED | `tools/demo_lab/`: `lab.py`,`stack.py`,`provision.py`,`storage.py`,`manifest.json`,`run_demo_lab.sh`,`reset_demo_lab.sh`,`seed_factors.py`,`verify.py`,`backend.env.example` + phase probes `p12_*`,`p16*`,`t3_*` |
| FTR-311 | Synthetic document & dataset generation | CT / QA | IMPLEMENTED_AND_WIRED | `tools/generate_synthetic_documents.py`,`generate_messy_fuel_csv.py`,`generate_messy_utility_csv.py`,`mock_scope3.csv`,`mock_uk_fuel_card_messy.csv`,`mock_uk_utility_bill.csv`,`CarbonTally_DB_Schema_V3M2.sql` |
| FTR-312 | Carbon data factory (factor + activity data generation/import) | CT operations | IMPLEMENTED_AND_WIRED | `tools/carbon_data_factory/` (`importer`,`schemas`,`factors`,`seed.ts`,`verify.ts`,`analyze_project.py`) + `tools/provision_tesseract_local.sh` (OCR dependency provisioning, AGENTS §20) |
| FTR-313 | Investor demo verification evidence (DR-001…DR-007) | CT / PO | VERIFIED (documented evidence) — not re-executed in this pass | DOC:`docs/demo-investor/DR-001…DR-007` (frontend customer journey, runtime browser verification, demo-lab CORS, deep browser verification, remaining investor workflows, report refresh, defect triage) |

### Domain 48 — QA & Independent Verification (FTR-314…322)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-314 | QA Harness entrypoint + deterministic mode | QA / CT | IMPLEMENTED_AND_WIRED (harness code present); **not executed in this pass** | `qa_harness/scripts/run_all.py`,`run_db.py`,`run_api.py`,`run_browser.py`,`run_workflows.py`,`run_agents.py`,`preflight.py`,`reclassify.py`,`common.py`,`audit_openapi_bindings.py` · `qa_harness/Makefile`,`pyproject.toml`,`requirements.txt`,`README.md` · DOC:AGENTS §52 (`python qa_harness/scripts/run_all.py [--no-ai]`) |
| FTR-315 | QA database suite (schema inventory, migrations, constraints, indexes, integrity, RLS) | QA | IMPLEMENTED_AND_WIRED | `qa_harness/db/{schema_inventory,migrations,constraints,indexes,integrity,rls,discovery}.py` |
| FTR-316 | QA API suite (contract, inventory, probe, session, authorization, security, workflows) | QA | IMPLEMENTED_AND_WIRED | `qa_harness/api/{contract,inventory,probe,session,authorization,security,workflows}.py` |
| FTR-317 | QA browser sweep + axe accessibility suite | QA | IMPLEMENTED_AND_WIRED | `qa_harness/browser/sweep.py` · `qa_harness/visual/axe` (AGENTS §50) |
| FTR-318 | QA role-workflow suites + demo-identity resolution | QA | IMPLEMENTED_AND_WIRED | `qa_harness/workflows/{customer,consultant,client,pe,operations,admin,messaging,executor,base}.py` · `qa_harness/identities/{loader,resolver,selectors,context}.py` (AGENTS §56) |
| FTR-319 | QA finding / evidence / status / safety model | QA | IMPLEMENTED_AND_WIRED | `qa_harness/core/{evidence,findings,status,safety,secrets,credentials,config,run_context}.py`,`qa_harness/findings/store.py`,`qa_harness/rules/{business,navigation,security,tables}.py` · status vocabulary PASS/FAIL/SKIPPED/BLOCKED/UNVERIFIED (AGENTS §52) |
| FTR-320 | AI analyst swarm (API / security / UX / workflow / judge) | QA / CT | IMPLEMENTED_AND_WIRED | `qa_harness/agents/{api,security,ux,workflow,judge}_agent.py`,`base.py`,`swarm.py` · DOC:AGENTS §57 (key from environment only; AI analyses deterministic evidence, never replaces it) |
| FTR-321 | pytest suites — unit/regression + integration | developers / QA | IMPLEMENTED_AND_WIRED (16 unit-level modules + 54 integration modules on disk); **not executed in this pass** | `backend/tests/*.py` = **16** files; `backend/tests/integration/*.py` = **54** files (incl. `test_disclosure_b3_v3_security.py`) · destructive `TRUNCATE … RESTART IDENTITY CASCADE` setup in `backend/tests/integration/conftest.py` with the F-046-1 target-name refusal guard (AGENTS §55.1) |
| FTR-322 | Playwright browser E2E security acceptance + isolated E2E environment | QA | IMPLEMENTED_AND_WIRED (code present); **credentials-dependent; specs SKIP rather than pass when the environment is not provided** | `playwright.config.ts` (testDir `./tests/e2e`, `E2E_BASE_URL`, persona credentials, 30 s timeout) · `e2e/environment/scripts/{bootstrap,apply_migrations,reset,teardown,capture_env,seed_e2e,seed_lifecycle_fixtures,run_acceptance,run_p6f_acceptance,verify_auth,verify_lifecycle_events}.py/sh` + `e2e/environment/supabase/migrations/*` (isolated env, PO-PHASE6-F-ENV-20260910) · DOC:docs/architecture/CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md |

### Domain 49 — Billing, Subscription & Commercial (FTR-323…329)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-323 | Billing security & configurable subscription foundation (D37.0) | commercial admin | IMPLEMENTED_AND_WIRED | MIG:`20260824020000_d37_0_billing_security_and_configurable_subscription.sql` |
| FTR-324 | Master commercial billing model — plans, subscriptions, orders, payments, ledger | commercial admin | IMPLEMENTED_AND_WIRED | MIG:`20260824030000_d37_master_commercial_billing.sql` · API:`/api/v3/commercial/plans{,/{plan_code}}`,`/subscriptions`,`/subscriptions/{id}/status`,`/orders`,`/orders/{id}`,`/orders/{id}/complete`,`/payments`,`/ledger`,`/overview` (24 endpoints, `backend/api/v3_commercial.py`) |
| FTR-325 | Credits ledger with grant / adjust / reverse / refund / rollover | commercial admin | IMPLEMENTED_AND_WIRED | API:`POST /api/v3/commercial/credits/{grant,adjust,reverse,refund,rollover}` · `GET /api/v3/billing/me/credits` |
| FTR-326 | Storage usage metering & refresh | customer / commercial admin | IMPLEMENTED_AND_WIRED | DB:`billing_storage_usage` · API:`POST /api/v3/billing/me/storage/refresh`,`GET /api/v3/commercial/storage` |
| FTR-327 | Entitlement resolution per organisation | customer / commercial admin | IMPLEMENTED_AND_WIRED | API:`GET /api/v3/commercial/entitlement/{organization_id}` · referenced by `HAS_ENTITLEMENT` semantics in RLS migration `20260925000000_p8_rls_4b_group1_enablement.sql` |
| FTR-328 | Assisted / managed order workflow (CarbonTally-operated purchase) | customer / CT commercial admin | IMPLEMENTED_AND_WIRED | API:`POST /api/v3/billing/orders/assisted`,`/orders/{id}/approve`,`/orders/{id}/cancel`,`POST /api/v3/billing/managed/orders`,`GET /api/v3/billing/me/orders`,`/me/orders/{id}` |
| FTR-329 | Commercial configuration control plane (config keys, plans, organisations view) | commercial admin | IMPLEMENTED_AND_WIRED | API:`GET/PUT /api/v3/commercial/config/{config_key}`,`GET /commercial/organizations` · config store observed live (`system_settings`: `default_currency=GBP`, `default_tax_rate`, `default_vat_rate`) · DOC:AGENTS §43 (configurable, not hard-coded) |

### Domain 50 — Product Capability Model (FTR-330…335)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-330 | Capability census register (`CAP-001…152`) | product / PO | IMPLEMENTED (register document) — superseded in breadth by this catalogue | DOC:`CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` (152 capability rows) · reconciliation against this catalogue in §6 |
| FTR-331 | Governed capability catalogue reference data (P17-K) | product / platform | IMPLEMENTED_AND_WIRED | MIG:`20261020000000_p17k_governed_capability_catalogue.sql` (capsule/reference-data only — creates no schema object) · DOC:`CT-PO-P17-K-*` decision documents |
| FTR-332 | Customer-facing capability truth surface (capability pages) | customer / investor | IMPLEMENTED_AND_WIRED | UI:`frontend/src/v3/capabilities/CapabilitiesPage.jsx`,`InvestorCapabilityPage.jsx`,`capabilities.css` · UI:`frontend/src/v3/components/CapabilityTruthSurface.jsx` |
| FTR-333 | Role-based route gating in the UI | all roles | IMPLEMENTED_AND_WIRED — **UI gating only; explicitly not a security boundary** (server-side authorization is authoritative, AGENTS §7,§44) | UI:`frontend/src/v3/components/RoleRoute.jsx` |
| FTR-334 | Plan → capability entitlement mapping | commercial admin / customer | IMPLEMENTED_AND_WIRED | API:`/api/v3/commercial/plans`, `/api/v3/commercial/entitlement/{organization_id}` · RLS `HAS_ENTITLEMENT`-style gating in MIG:`20260925000000_p8_rls_4b_group1_enablement.sql` |
| FTR-335 | Frozen product/UX decision register & coverage matrices (D1–D21, N1, N3) | PO / product | DOCUMENTED_ONLY | DOC:AGENTS §63 (frozen decisions incl. D17, D19, D21, N1, N3) · DOC:`CarbonTally_PO_Insight_Capability_Coverage_Matrix_2026-09-22.md`,`CT-PO-INSIGHT-CAPABILITY-COVERAGE-MATRIX-IMPLEMENTATION-20260922.md`,`CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` |

### Domain 51 — Design System & UI Shell (FTR-336…340)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-336 | D21 unified design-token layer (`ct-*` vocabulary) | all UI surfaces | IMPLEMENTED_AND_WIRED | `frontend/src/v3/tokens.css` — declared "single source of truth for the `ct-*` design-token vocabulary shared by every V3 surface (customer, consultant, Processing Entity, CarbonTally staff and CarbonTally admin)"; D21.1 unification records the historical dual-green (`#2f855a` in `v3.css` vs `#2d6a4f` in `App.css`) consolidated on `#2f855a`, darkest shade `--ct-color-primary-dark: #1b4332`, historical blues unified on `--ct-color-accent: #2b6cb0` |
| FTR-337 | V3 shared visual system & application shell | all V3 users | IMPLEMENTED_AND_WIRED | `frontend/src/v3/v3.css` (v3-* classes consuming ct-* tokens) · `frontend/src/v3/components/V3Layout.jsx` · legacy `frontend/src/App.css` retained for legacy surfaces (AGENTS §79) |
| FTR-338 | Shared V3 component library (states, search, evidence trail) | all V3 users | IMPLEMENTED_AND_WIRED | `frontend/src/v3/components/`: `ui/`,`StateViews.jsx`,`SearchBox.jsx`,`EvidenceTrail.jsx`,`EvidenceRecordPanel.jsx`,`CapabilityTruthSurface.jsx` |
| FTR-339 | D19 processing workbench UI shell (frozen UX) | CT operator / PE / reviewer | IMPLEMENTED_AND_WIRED | `frontend/src/v3/components/workbench/` · DOC:AGENTS §39 (workbench-first; changes require PO review) · census D19 |
| FTR-340 | Standard loading / empty / error / state presentation | all users | IMPLEMENTED_AND_WIRED | `frontend/src/v3/components/StateViews.jsx` · DOC:AGENTS §46,§47,§48 (no raw technical errors; loading ≠ working; meaningful empty states) |

### Domain 52 — Public Website & Visitor Surface (FTR-341…345)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-341 | Public landing & marketing pages | public visitor | IMPLEMENTED_AND_WIRED | FE:`frontend/src/LandingPage.jsx`,`AboutUs.jsx`,`Glossary.jsx`,`CarbonReductionPlan.jsx`,`PricingPage.jsx` · DOC:AGENTS §30 (public website `carbontally.co.uk` is a distinct surface from the authenticated application) |
| FTR-342 | Legal, policy & consent surface | public visitor | IMPLEMENTED_AND_WIRED | FE:`PrivacyPolicy.jsx`,`TermsPage.jsx`,`CookiePolicy.jsx`,`CookieBanner.jsx`,`DataSecurity.jsx`(+`DataSecurity.test.jsx`) · DOC:`docs/legal`,`docs/business` |
| FTR-343 | Public visitor assistant / chat entry | public visitor | IMPLEMENTED_AND_WIRED (legacy stack) | FE:`frontend/src/components/chat/**` · API:legacy `/api/communication`(22) · DOC:AGENTS §29 (visitor-facing; not a substitute for authenticated messaging) |
| FTR-344 | Public self-service signup, onboarding & organisation metadata entry | prospective customer | IMPLEMENTED_AND_WIRED | FE:`BetaSignup.jsx`,`BetaLogin.jsx`,`SelfServiceSignup.jsx`,`OnboardingWizard.jsx`,`OnboardingPage.jsx`,`CompanyNamePrompt.jsx`,`OrganizationMetadata.jsx`,`TeamManagement.js` · MIG:`20260824010000_d35_self_service_onboarding.sql` |
| FTR-345 | Public demo / presentation surface | sales / investor | IMPLEMENTED_AND_WIRED | FE:`frontend/src/components/CarbonTallyDemo.jsx` · `carbon-tally-ui-demo/` · DOC:`docs/Pricing`,`docs/business`,`docs/legal` |

### Domain 53 — Deployment, Build & Operational Tooling (FTR-346…350)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-346 | Vercel hosting config — SPA rewrites, `/admin` rewrite, security headers | platform / deployment | IMPLEMENTED_AND_WIRED (config as code); deployed state not verifiable in this pass | Root `vercel.json`: rewrites `/admin/static/(.*)`,`/admin/(.*\..*)`,`/admin/(.*)`→`/admin/index.html`,`/admin`,`/static/(.*)`,`/(.*)`→`/index.html`; headers `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, a restrictive `Permissions-Policy`, `Content-Security-Policy` (`object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'`) and a report-only CSP allowlisting `*.supabase.co`, `carbontally-api.onrender.com`, `googletagmanager.com` · `frontend/vercel.json` (SPA rewrite) |
| FTR-347 | Monorepo build pipeline (frontend + legacy admin → public bundle) | developers / deployment | IMPLEMENTED_AND_WIRED | Root `package.json`: `build` = frontend `npm install && npm run build` → admin `npm install && npm run build` → `mkdir -p public/admin` → copy `frontend/build/*` to `public/` and `admin/build/*` to `public/admin/` |
| FTR-348 | Backend runtime pinning & Render deployment configuration | deployment | PARTIALLY_IMPLEMENTED — runtime pinned, but **no `render.yaml`/blueprint is present in the release tree** (deployment configuration exists as documentation only) | `runtime.txt` = `python-3.11.9`; `requirements.txt` · DOC:`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` · target API host referenced in CSP: `carbontally-api.onrender.com` |
| FTR-349 | Migration-drift gate, operations runbooks & backup/recovery drill tooling | CT operations | IMPLEMENTED_AND_WIRED (documented runbooks + script); not executed in this pass | DOC:`docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`,`CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`,`CARBONTALLY_BACKUP_RECOVERY_DRILL.md`,`MANUAL_PROCESSING_GOVERNANCE_FIN06.md` · `tools/backup_recovery_drill.py` |
| FTR-350 | Build-metadata, API-doc & endpoint-inventory generators | developers | IMPLEMENTED_AND_WIRED | `tools/generate_build_info.js`,`generate_api_docs.py`,`list_endpoints.py`,`export_postman.py`,`quick_api_ref.py`,`test_endpoints.py` · `API_ENDPOINTS.md` (both trees) · `qa_harness/scripts/audit_openapi_bindings.py` (AGENTS §65: API contract must not be invented) |

### Domain 54 — Historical, Legacy & Unreconciled Artefacts (FTR-351…354)

| ID | Feature | Primary actor | Truth | Evidence |
|---|---|---|---|---|
| FTR-351 | Historical archive document corpus (prior designs, plans, reconstructed task history) | historians / PO | HISTORICAL_ONLY — may not describe current behaviour (AGENTS §80) | Trees `docs/Final/`,`docs/Final_Kimi/`,`docs/ChatGPT/`,`docs/standalone/`,`docs/implementation/`,`docs/cline/` · files `docs/RECONSTRUCTED_TASK_HISTORY.md`,`docs/Todos.md`,`docs/featurellist.md`,`v1.9.txt`,`admin_log_viewer.feature.txt` |
| FTR-352 | Historical audit, OHD and verification corpus (findings used as regression targets) | QA / CT | HISTORICAL_ONLY as findings; used as regression targets and requirements | Trees `docs/audit/`,`docs/audits/`,`docs/ohd/`,`docs/verification/` · `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md` (**447 rows**) · root `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md`,`costrict-p3-ov-01-independent-re-verification.txt`,`CARBONTALLY_V3_PHASE_2_*` reports |
| FTR-353 | Legacy Prisma/schema artefact lineage | developers | HISTORICAL_ONLY / SUPERSEDED — Supabase migrations are authoritative; disposition PO-undecided | `prisma/`,`prisma.config.ts`,`seed.ts`,`seed.config.ts`,`schema.sql`,`CarbonTally_DB_Schema_V3M2.sql`,`database/` · AGENTS §66 (migrations are the change mechanism) |
| FTR-354 | Retained scratch/backup artefacts awaiting disposition | PO / CT | PRESENT — retention/removal **PO DECISION REQUIRED** | `backend - backup.zip`,`backups/`,`output/`,`uploads/`,`frontend_backup_pre_v3_public_20260827/`,`carbon-tally-ui-demo/`,`create_admin_dashboard.py`,`test_results.json`,`test_results_all.json`,`clean_emissions_output.json`,`__pycache__/` · AGENTS §42 (retention is a configurable, PO-controlled capability) |

---

## 5. SCHEMA & CONFIGURATION REQUIREMENTS DERIVED FROM FUNCTIONALITY

### 5.1 Method

For every domain in §3 the *shape* of the required persistence/configuration was
derived from the functionality itself (what the feature must store, key, isolate,
version, gate or configure), then compared against:

1. the migration ledger in Git (`supabase/migrations/`, **89 files**),
2. the actual schema present in each local database, live-queried in this pass,
3. the configuration store actually populated in the live system
   (`system_settings`).

This section therefore answers the question the feature catalogue raises:
*"if every FTR above is to be durable, what objects must exist — and where do they
actually exist today?"*

### 5.2 Requirement classes

| Class | Meaning | Count of domains affected |
|---|---|---|
| **A — SATISFIED** | Required object(s) exist in the current durable flagship database and are reachable by the running code path | most domains (see §5.4) |
| **B — MIGRATED_BUT_UNAPPLIED** | The object exists as a migration in Git but that migration has **never been applied** to the flagship database | 11 domains (P8 disclosure / evidence / adjudication / insight, P8x telemetry retention, P16-R, P17-A/C/D/H/10/K) |
| **C — CLONE_ONLY** | The object exists **only** in a disposable clone (`ct_*`) or the ephemeral demo database — i.e. no durable local database holds it | P17 capability set (`estimation_records`, contractual instruments, `scope3_categories`, product/contract reporting dimensions) |
| **D — NOT_IN_ANY_DATABASE** | The functionality implies an object that exists in **no** database at all (naming drift, empty catalogue table, or unimplemented persistence) | `accounting_dimensions` (table never created — P17-A is an `ALTER TABLE`), `roles` catalogue (0 rows), production objects (all `UNKNOWN`, production never contacted) |
| **E — CONFIGURATION_ONLY** | Requirement is satisfied by a settings key rather than a table | AGENTS §42 retention, §43 billing, upload limits, SLA, security policy, locale/format defaults (see the Configuration Catalogue deliverable) |

### 5.3 Live-verified environment divergence (queried this pass)

| Database | Public tables | Migration ledger | Organisations | P8 disclosure / evidence | P8 insight | P8 adjudication | P17 (estimation, contractual, scope3) |
|---|---|---|---|---|---|---|---|
| `postgres` (**flagship / durable**) | **116** | **46** | **975** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** |
| `carbontally_demo_local` | 141 | ledger unreadable | 4 | PRESENT | PRESENT | PRESENT | ABSENT |
| `carbontally_test` (disposable integration target) | 117 | ledger unreadable | 3 | PARTIAL (evidence/artefacts absent) | PRESENT | PRESENT | ABSENT |
| `carbontally_qa_phase8` | 133 | 0 | 25 | PARTIAL (disclosure + evidence present, adjudication absent) | ABSENT | ABSENT | ABSENT |
| `ct_local_93d5cdd` | 135 | ledger unreadable | 25 | PRESENT (disclosure + evidence + artefacts) | **ABSENT** | PRESENT | ABSENT |
| `ct_p17k_20260926` (**disposable clone**) | **145** | ledger unreadable | 5 | PRESENT | PRESENT | PRESENT | **PRESENT** |

Cluster total: **78 databases** (1 flagship `postgres`, 6 named/durable-ish environments, ~71 disposable `ct_*` clones carrying phase evidence).

Additional live checks this pass:

- `accounting_dimensions` (as a table) = **0 rows in every database** → the P17-A
  concept is realised as 10 added columns on `calculation_snapshots` /
  `emissions_logs`, not as a dimensions table. **Naming drift confirmed.**
- `product_categories` exists in the flagship but is the **legacy** activity
  catalogue — the P17-10 *product/contract reporting dimensions* are separate and
  absent from the flagship. Do not conflate them.
- Flagship ledger = 46 rows; release tree = 89 migration files; ledger-consistent
  delta = **43 unapplied migrations**, exactly the ordered set
  `20260905000000_gate4_actor_provenance.sql` → `20261020000000_p17k_governed_capability_catalogue.sql`
  (46 + 43 = 89 ✓).

### 5.4 Per-domain persistence requirements (derived) vs reality

**Verified flagship inventory used for this table (queried live this pass):** `postgres` = **116 public tables, 0 public views**. Class letters follow §5.2.

#### Domains 01–27 (complete)

| Domain | Persistence / configuration the functionality requires | Creation path | Class |
|---|---|---|---|
| D01 Platform Administration | `system_settings` (63 columns; `analytics_ga4`, `platform_retention` rows live), `audit_logs`, `staff_profiles`, `staff_roles` | `rc2_schema`, `v3m8_system_admin_role_model` | **A** (+**E** for the ~50 settings keys) |
| D02 Authentication | `auth.users`, `login_history`, `password_reset_tokens`, `beta_users`, `beta_access_codes`, `pending_invites`, `user_invitations` | `rc2_schema`, `d35_self_service_onboarding` | **A** |
| D03 Authorization | Membership rows + RLS policies + guard modules; **P8 RLS hardening programme** (anon grant containment, authenticated grant hardening, 4b group1 enablement, factor containment) | `rc2_rls`, `v3m6_entity_rls`, `p9_rls_recursion_fix` applied; `p8_rls_*` (20260920→20260926) **unapplied** | **A** baseline / **B** hardening |
| D04 Organizations | `organizations`, `organization_members`, `organization_metadata`, `organization_files`; P17 organisation dimensions `organization_type`, `consolidation_approach` | applied set; `p17a_accounting_dimensions_and_factor_governance` | **A** / P17 columns **C** (clone-only; 0 occurrences in flagship) |
| D05 Users | `users`, `staff_profiles`, `user_presence`, `typing_status`, `user_feedback` | applied set | **A** |
| D06 Roles & Permissions | Role catalogue table + role→permission mapping + membership role | `roles` exists but **0 rows**; `staff_roles.permissions` (jsonb) is authoritative for staff | **D** (catalogue never populated) + **A** (staff roles) |
| D07 Consultant Management | `consultant_profiles`, `consultant_firm_members`, `consultant_clients`, `consultant_custom_domains`, `consultant_senders`, `consultant_billing`, `consultant_tasks`; engagement & processing-permission provenance | applied set; `p6_1c`, `p6_2a`, `p6_2d` (20260906→20260910) **unapplied** | **A** / provenance **B** |
| D08 Consultant Clients | `consultant_clients` + revocation roles | applied set (`consultant_revocation_roles`) | **A** |
| D09 Acting-For / Delegation | `acting_for_organization_id` on calculation/emissions records (10 occurrences in clone) | `p17a` | **C** |
| D10 Principal / Reporting Entities (PE) | `processing_entities`, `processing_assignments`, PE role grants via `staff_profiles`, `reassignment_history` | `v3m1_processing_entities`, `v3m8_pe_manager_role`, `d22_processing_work_assignment` | **A** |
| D11 Facilities & Locations | `facilities` (+ `organization_metadata`); **no distinct `locations` table exists in the flagship inventory** — location data is carried within facility/master-data records | `rc2_schema` + `v3m*` | **A** for `facilities`; a *separate* Locations entity is **absent (D)** and is an architecture/PO question (AGENTS §34, §35) |
| D12 Assets & Vehicles | `assets`, `vehicles` | `rc2_schema`, `v3m7_vehicles` | **A** |
| D13 Suppliers | `suppliers`, `supplier_categories` | `rc2_schema` | **A** |
| D14 Documents | `customer_documents`, `upload_batches`, `import_batches`, `document_activity_log`, `document_types`, `document_type_categories`, `document_processing_queue`, `processing_queue`, `draft_entries`, `file_attachments`, `organization_files` + private storage bucket | `rc2_*`, `add_import_batches`, `d32_private_documents_storage` | **A** |
| D15 Extraction | `manual_extraction_batches`, `manual_extraction_items`, `manual_review_queue`, durable-processing tables; **`activity_clarifications`** | applied set; `p8_fs_activity_clarifications` (+fks, lifecycle, lineage) **unapplied** | **A** / clarifications **B** (present only in clones) |
| D16 Mapping & Unit Normalisation | `units`, `factor_aliases`, `emission_factors`; line-item persistence | applied set; `p8_b2_evidence_line_items`, `p8_b2_provenance_line_links` **unapplied** | **A** / line items **B** |
| D17 Manual Review & QC | `manual_review_queue`, `qc_checklists`, `qc_checks`, `qc_errors`, `review_audit_trail`, `review_assignment_history`, `customer_review_log` | `v3m5_issues`, `rc2_schema` | **A** |
| D18 Evidence | `evidence_line_items` + provenance line links + evidence idempotency | `p8_b2_*`, `p8_b1_correction_privileges_and_evidence_idempotency` | **B** |
| D19 Data Quality & Validation | `issues` (+ V3M5 lifecycle), validation rule storage | `v3m5_issues` | **A** |
| D20 Emission Factors | `emission_factors` (7,049 rows in flagship), `factor_aliases`, factor versioning/typing | `rc2_schema`, `add_emission_factors_import_batch`; P17 factor governance columns (`scope3_category_hint`, `scope2_method`, `factor_type`, `gas_coverage`) | **A** / P17 governance columns **C** |
| D21 Factor Governance | factor governance/approval state + customer-factor precedence | `p17a_accounting_dimensions_and_factor_governance` | **C** |
| D22 Scope 1 | `calculation_snapshots`, `emissions_logs`, activity categories, facility linkage (`facility_id` exists) | applied set | **A** |
| D23 Scope 2 Location-Based | as D22 + `scope2_method` + energy-type columns | `p17a`/P16-R columns | **C** (`scope2_method` = 0 occurrences in flagship) |
| D24 Scope 2 Market-Based | as D23 + contractual instrument linkage | `p17c_contractual_instruments_and_allocations` | **C** |
| D25 Contractual Instruments | `contractual_instruments` + allocation records | `p17c` | **C** (absent everywhere except P17 clones) |
| D26 Allocations | allocation records linked to instruments and snapshots | `p17c` | **C** |
| D27 Scope 3 | `scope3_categories` taxonomy + `scope3_category` on snapshots/emissions | `p17d_scope3_category_taxonomy` | **C** (0 occurrences in flagship) |

#### Domains 28–40

| Domain | Persistence / configuration the functionality requires | Creation path | Class |
|---|---|---|---|
| D28 Accounting Dimensions | 10 dimension columns on `calculation_snapshots` / `emissions_logs` — **deliberately not a separate table** | `p17a_accounting_dimensions_and_factor_governance` (ALTER TABLE) | **C** (clone) / naming-drift **D** for the "table" mental model |
| D29 Estimation & Assumptions | assumption/estimation record persistence for estimated values | `p17h_estimation_and_assumption_records` | **C** (`estimation_records` present only in P17 clones) |
| D30 Calculations | `calculation_snapshots`, `emissions_logs` (+ deterministic request idempotency key) | applied set; `p16r7_calculation_request_idempotency` | **A** / idempotency **B** |
| D31 Workflow & Processing Jobs | durable job records (V3M9), `processing_queue`, `processing_steps`, `processing_logs`, `processing_time_log`, `processing_assignments`, `processing_audit_trail`, `work_item_assignments`, `upload_batches`, `import_batches`; governance grants `manual_processing_grants` | applied set except `p8_fin06_manual_processing_governance`, `p6_2d_consultant_provenance` | **A** / FIN-06 + provenance **B** |
| D32 Approvals | `approval_requests`, `approval_decisions`, `customer_verifications`, `verification_logs`, `verification_activity_log` | applied set | **A** |
| D33 Audit & Auditability | `audit_logs`, `audit_trail`, `domain_events`, `activity_feed`, `activity_logs`, `user_activity_log`, `staff_activity_log`, immutability guards | `audit_activity_immutability` applied; `p7_audit_immutability_and_indexes` (20260912) | **A** / P7 index+immutability re-assertion **B** |
| D34 Reporting | `report_versions`, `report_templates`, `report_generation_queue`, `report_comments`, `export_history`, `dashboard_metrics`; report lifecycle status, result reportability lifecycle | applied set; `p8_report_lifecycle_status` (20260913), `p16r5_result_reportability_lifecycle` (20261008) | **A** / lifecycle **B** (`reportability_status` = 0 occurrences in flagship) |
| D35 Report Versions & Frozen Artefacts | frozen report artefact persistence + bucket | `p8_b4_frozen_artefact` | **B** (`report_version_artifacts` absent from flagship) |
| D36 Disclosures | `disclosure_*` family — 16 tables observed (frameworks, purposes, requirement versions/mappings, values, value evidence, assessments, intensity denominators/ratios, narrative entries, report instance binding) | `p8_b1_disclosure_model_foundation`, `p8_b3_intensity_catalogue`, `p8_b3_intensity_ratios`, `p8_b4_narrative_overlay` | **B** (absent from flagship; present in demo/QA/clone DBs) |
| D37 Insight | `carbontally_insight_conversations`, `_messages`, `_interactions`, `_tool_calls`, `insight_rate_limit_buckets`, `insight_concurrency_leases` | `p8_i1_insight_persistence`, `p8_i2_insight_authorization`, `p8_i4_insight_interactions`, `p8_insight_discovery_aggregation_rate_limit`, `p8_insight_temporal_comparison`, `p8_insight_data_quality_reproducibility` | **B** (absent from flagship) |
| D38 Dashboards & Analytics | `dashboard_metrics`, `usage_tracking`, `data_discovery_requests`, `activity_feed`; GA4 config key | applied set + `system_settings.analytics_ga4` | **A** (+**E**) |
| D39 Notifications | `notifications`, `notification_delivery`, `notification_templates`, `email_templates`, `email_logs`; telemetry retention policy | applied set; `p8x_x2_operational_telemetry_retention` (20260924) | **A** / retention controls **B**+**E** |
| D40 Messaging | `conversations`, `conversation_participants`, `messages`, `message_activity_log`, `conversation_activity_log`, `typing_status`, `customer_communication` + unique-participant constraint + PE operational messaging | `v3m8_messaging_unique_participants`, `phase5_pe_operational_messaging` (applied) | **A** |

#### Domains 41–54

| Domain | Persistence / configuration the functionality requires | Creation path | Class |
|---|---|---|---|
| D41 Storage | Supabase storage buckets + policies for private documents, report artefacts and evidence; `organization_files`, `customer_documents`, `file_attachments` | `d32_private_documents_storage` (applied); artefact bucket provisioning is an operations step | **A** / report-artefact bucket **B** (pending `p8_b4_frozen_artefact`) |
| D42 Integrations | `email_templates`, `email_logs` (Resend), webhook retry/timeout settings, GA4 key, DEFRA factor-import batches | applied set + `system_settings` keys (`webhook_retry_count`, `webhook_retry_delay`, `webhook_timeout_seconds`, `analytics_ga4`) | **A** (+**E**) |
| D43 API Platform | Router registry only (no new tables); API rate limits and request limits as configuration | `system_settings.api_rate_limit`, `api_rate_limit_burst`, `max_*` limits; `backend/middleware/rate_limit.py` | **E** (no schema requirement) |
| D44 Operations | `queue_settings`, `manual_review_queue`, `processing_queue`, `staff_workload`, `staff_performance`, `staff_daily_performance`, `team_performance`, `reassignment_history`, `staff_activity_log` | applied set | **A** |
| D45 Admin Console | Legacy admin screens depend on `waitlist`, `business_hours`, `usage_tracking`, `data_discovery_requests`, `glossary`, `product_categories`, `activity_categories`, `units`, `roles`, `beta_*`, plus the V3 ops tables | applied set; admin legacy surface is DEPRECATED (PO D-P2-02) | **A** (DEPRECATED surface) |
| D46 Security, Identity & Access Control | Identity + membership + `staff_roles` + RLS policies; MFA lives in Supabase `auth.*` (`auth.mfa_factors`, `auth.mfa_challenges`, `auth.mfa_amr_claims` observed) | applied set + `system_settings` security keys (`two_factor_required`, `two_factor_method`, `session_timeout_minutes`, `password_*`, `login_attempts_*`) | **A** (+**E**); P8 RLS hardening suite **B** |
| D47 Investor Demo & Synthetic Data | **No product-schema requirement.** Requires a *disposable* environment plus the local identity manifest and seeder — must never be applied to production | dev tooling only (AGENTS §54, §55) | **N/A to production schema** |
| D48 QA & Independent Verification | **No product-schema requirement.** Requires evidence/finding persistence in the harness and a disposable target database (destructive fixture) | `qa_harness/core/evidence.py`, `qa_harness/findings/store.py`; AGENTS §55.1 target-safety invariant | **N/A to production schema** |
| D49 Billing, Subscription & Commercial | `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `billing_idempotency_keys`, `customer_subscriptions`, `consultant_billing` | `d37_0_billing_security_and_configurable_subscription`, `d37_master_commercial_billing` | **A** |
| D50 Product Capability Model | Capability reference data; plan → capability entitlement mapping | `p17k_governed_capability_catalogue` (reference data, no object created) | **B** / mapping via billing tables **A** |
| D51 Design System & UI Shell | **No persistence requirement** (tokens, CSS, components) | `frontend/src/v3/tokens.css`, `v3.css` | **N/A** |
| D52 Public Website & Visitor Surface | `waitlist`, `beta_users`, `beta_access_codes`, `glossary`, `user_feedback`, `customer_communication` | applied set (`d35_self_service_onboarding`) | **A** |
| D53 Deployment, Build & Operational Tooling | **No application-schema requirement**; depends on disciplined use of `supabase_migrations.schema_migrations` and deployment configuration keys | `vercel.json`, `runtime.txt`, runbooks | **N/A** (+**E**) |
| D54 Historical, Legacy & Unreconciled Artefacts | **No schema requirement**; legacy Prisma/schema artefacts are superseded and must not be treated as authoritative | `prisma/`, `schema.sql`, `CarbonTally_DB_Schema_V3M2.sql` | **N/A** (disposition PO-undecided) |

**Derived totals:** 40 domains require production persistence (**A**, with **B**/**C**/**D** exceptions); 4 domains are substantially configuration-only (**E**); and **9 domains (D47, D48, D51, D53, D54 and the dev-tooling parts of D42/D43/D50) require no production schema change at all.**

### 5.5 Derived implementation requirements (what must be true for the catalogue to be durable)

| # | Derived requirement | Basis | Status |
|---|---|---|---|
| R1 | Apply the **43 unapplied migrations** (`20260905000000` → `20261020000000`) to a durable, backed-up database, in filename order, only after verifying their prerequisites | §5.3 ledger arithmetic (46 + 43 = 89) | **NOT DONE** — no durable local DB carries them |
| R2 | Reconcile the **`accounting_dimensions` naming drift**: either the documented "table" is renamed, or the 10 columns are declared authoritative; the docs-vs-schema mismatch is a real traceability defect | live `information_schema` checks (§5.3) | OPEN — PO/architecture decision |
| R3 | Populate or retire the **`roles` catalogue** (0 rows) so role→permission mapping has one authoritative source (`staff_roles.permissions` jsonb is currently the only populated source) | live count 0; AGENTS §9, §14 | OPEN — PO/architecture decision |
| R4 | Decide whether **Locations** is a distinct entity or a facet of Facilities; the flagship has `facilities` but no `locations` table | flagship inventory; AGENTS §34, §35 | OPEN — PO decision |
| R5 | Review live retention config before any enforcement: `system_settings['platform_retention'].audit_log_retention_days = 1` while `data`/`document`/`backup` retention = 365 | live `system_settings` row | OPEN — flagged PO decision (tension with AGENTS §42 auditability) |
| R6 | P16-R / P17 reporting, disclosure, Insight and adjudication functionality must be treated as **not currently durable** until R1 completes and is re-verified against a durable database | §5.3 | OPEN |
| R7 | Production schema state remains **UNKNOWN** — production was never contacted in this discovery pass | discovery protocol | UNKNOWN |

---

## 6. UNRESOLVED ITEMS, TERMINOLOGY & PO DECISIONS

### 6.1 Terminology and naming conflicts (documented, not silently resolved)

| # | Conflict | Evidence | Consequence |
|---|---|---|---|
| T1 | **PE = "Processing Entity" vs "Principal / Reporting Entity"** | AGENTS §8/§12 and the code/schema use *Processing Entity* (`processing_entities`, PE workspace, PE roles). The capability census (CAP-065/CAP-066) and part of the domain language in this catalogue use *Principal Entity* / *Principal / Reporting Entities* (Domain 10 heading) | Two different concepts risk being conflated: a PE is an **operational actor**; a "reporting/principal entity" is an **accounting boundary**. The catalogue keeps both terms but does not merge the concepts — **PO terminology decision required** |
| T2 | **`accounting_dimensions` documented as a table, implemented as columns** | 0 rows for a table named `accounting_dimensions` in all 78 databases; P17-A is `ALTER TABLE` adding 10 columns | Any downstream artefact written against an "accounting_dimensions table" will not work |
| T3 | **`product_categories` (legacy) vs P17-10 product-contract reporting dimensions** | `product_categories` exists in the flagship; the P17-10 dimensions do not | Reporting scope can be misread as "already present" |
| T4 | **"Locations" as a distinct master-data entity** | AGENTS §34/§35 and D17 speak of Locations; the flagship has `facilities` and no `locations` table | Data model vs information architecture drift |
| T5 | **Two admin surfaces** | Legacy admin CRA (19 screens) DEPRECATED by PO D-P2-02, yet still served via the `vercel.json` `/admin` rewrite and still catalogued as live features (D45) | Deprecation is a decision, not yet a deployment fact |
| T6 | **`roles` table empty while role behaviour is live** | 0 rows in `roles`; roles are enforced from membership/`staff_roles` | A future reader of `roles` would wrongly conclude RBAC is unimplemented |

### 6.2 Truth-state distribution across the 354 features

Counts are of catalogue rows whose **Truth** cell contains the token (tokens are not mutually exclusive where a row states a baseline plus an exception):

| Truth token | Rows | Reading |
|---|---|---|
| `IMPLEMENTED_AND_WIRED` | **313** | code exists *and* is reachable from a wired route/page |
| `PARTIALLY_IMPLEMENTED` | **17** | works in part; a PO decision, an unapplied migration or a missing surface blocks completion |
| `DOCUMENTED_ONLY` | **9** | documented as decision/register/law-of-the-product, with no runtime object |
| `HISTORICAL_ONLY` | **5** | must not be read as current behaviour (AGENTS §80) |
| `IMPLEMENTED_BACKEND_ONLY` | **4** | engine/service present without a verified wired surface |
| `SCHEMA_ONLY` | **4** | object exists but is unused/empty |
| `SUPERSEDED` | **1** | Prisma/schema lineage replaced by Supabase migrations |
| `DEPRECATED` | **1** | legacy admin control plane (PO D-P2-02) |
| `CODE_ONLY` | **1** | service exists, no wired route (per census CAP-120 style classification) |
| `PRESENT` (artefact on disk, disposition open) | **1** | scratch/backup artefacts |
| production (`PROD:`) states | **354 × UNKNOWN** | production was never contacted (see §6.4) |

### 6.3 Register of open Product Owner decisions arising from this catalogue

*(This is the catalogue's own register; it is distinct from the census's `POD-xxx` numbering unless a census `POD` is named explicitly.)*

| ID | Decision required | Why it is a PO decision |
|---|---|---|
| POD-A | Which durable environment must carry the **43 unapplied migrations**, and in what order/authorisation | Changes durable data; AGENTS §55.1 forbids pointing destructive harnesses at durable data |
| POD-B | `accounting_dimensions`: ratify columns as authoritative **or** require a table | Product/architecture semantics (T2) |
| POD-C | `roles` catalogue: populate, or formally retire it as a legacy artefact | Authoritative RBAC source (T6) |
| POD-D | Locations: separate entity vs facility facet | Information architecture (D17/T4) |
| POD-E | Retention: `system_settings['platform_retention'].audit_log_retention_days = 1` vs 365 for data/documents/backups | Conflicts with auditability expectations (AGENTS §42) |
| POD-F | PE terminology: Processing Entity vs Principal/Reporting Entity | Cross-cutting naming (T1) |
| POD-G | Legacy admin control plane: confirm retirement path and the `/admin` rewrite's end state | AGENTS §31 + PO D-P2-02 |
| POD-H | Legacy artefact disposition (Prisma lineage, backups, `carbon-tally-ui-demo`, scratch outputs) | AGENTS §42, §79 |
| POD-I | Production schema/migration state: is production expected to match the release tree, and who verifies it | Currently `UNKNOWN` |
| POD-J | Capability-census residual capabilities (SEO/PWA, X7 runtime metrics, shared table/pagination standard) — catalogue them as features or declare them out of scope | Scope of the commercial product (AGENTS §36) |

### 6.4 Explicitly NOT verified in this discovery pass

| Not verified | Why | How it should be verified |
|---|---|---|
| Production schema, migrations, RLS and data | Production was never contacted | Approved, authorised production read-only census |
| Live runtime behaviour of any feature (no API/frontend/worker was started) | Read-only discovery posture; no servers launched | Start stack + QA Harness run (`run_all.py --no-ai`) |
| Whether each RLS policy actually denies the negative cases in AGENTS §45 | Policy bodies were not executed | `qa_harness/db/rls.py` + `qa_harness/api/security.py` on a disposable clone |
| Whether approvals carry evidence-lineage linkage | Columns not inspected for this question | Targeted column/constraint inspection (recorded as open in FTR-201) |
| OCR availability in any deployed environment | Environment dependency (AGENTS §20) | Deployment verification (`tools/provision_tesseract_local.sh` equivalent in prod) |
| GA4 live delivery and any external integration actually firing | External systems not exercised | Integration test with a real provider in a sandbox |
| Unit/integration/e2e suites passing | Tests were **not executed** (only inventory-counted: 16 unit files, 54 integration files, Playwright config) | Run against `carbontally_test` per AGENTS §55.1 |
| Whether the 4 `IMPLEMENTED_BACKEND_ONLY` features have any UI entry point at all | UI wiring not exhaustively proven negative | Targeted UI/wiring trace per feature |

### 6.5 Read-only attestation

- **No** database write, migration application, seed, truncate, drop or configuration change was performed. All database access was `information_schema`/count queries executed read-only inside the local Supabase Postgres container.
- **No** repository mutation other than creating this discovery document (and its sibling deliverables) under `docs/architecture/`.
- **No** server, worker, harness, test suite or browser was started.
- **No** secret, credential, JWT or signed URL appears in this document; the investor-demo local password is referenced only by its canonical store path.
- **No** production or remote environment was contacted.

---

## 7. RECONCILIATION WITH THE 152-CAPABILITY CENSUS (`CAP-001…152`)

### 7.1 Why the numbers differ (152 → 354)

| Mechanism | Explanation | Effect |
|---|---|---|
| **API surface vs UI surface separation** | The census often recorded one capability where the implementation has a distinct API feature and a distinct UI feature with independent lifecycles (e.g. a review capability = queue API + workbench UI + routed item page) | +many FTR |
| **Sub-feature discovery inside the 59 V3 API modules (370 endpoints) and 292 frontend API functions** | Endpoints that exist and are wired but were not catalogued as separate capabilities (bulk operations, search, exports, admin imports, verifications, clarifications, capability pages, etc.) | +many FTR |
| **Four additional domains (51–54)** | Design system & UI shell, public website & visitor surface, deployment/build & operational tooling, historical/legacy artifacts — the census folded these into other capabilities (CAP-132/133/134/149/150/151/143/144/145) | +FTR +4 domains |
| **Domain internal split** | Security/identity/access control and QA were each a handful of census rows but are many distinct features (7 authz guard modules, RLS programme, QA suites) | +FTR |
| **Retention** | Every one of the 152 census capabilities is represented by at least one FTR — the census is a subset in **breadth**, not a contradiction | 152/152 covered |

> The ID-exact `CAP-xxx ↔ FTR-xxx` join table is carried in the third deliverable,
> `CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md`, so that this
> catalogue stays readable and the join stays machine-checkable.

### 7.2 Census capabilities that needed an explicit home (residual register)

| Census ID | Census capability | Where it is covered here |
|---|---|---|
| CAP-005 | Cookie consent banner | FTR-342 (legal/policy & consent surface) |
| CAP-010 | SEO and PWA artefacts | **NOT individually catalogued** — see POD-J and §7.3 |
| CAP-070 | Seven governed capability values / one vocabulary | FTR-330 + FTR-331 (capability model cluster) |
| CAP-074 | Actor / automation / write-once provenance gates | D33 audit cluster (FTR-202…210) + D30 calculation provenance |
| CAP-091 | Legacy reporting and report generator | D34 reporting cluster (FTR-211…222, legacy surfaces) |
| CAP-122 | Persisted API runtime metrics (X7) | **NOT individually catalogued** — see POD-J and §7.3 |
| CAP-133 | Build provenance (SHA + branch in bundle) | FTR-350 (build metadata generation) |
| CAP-145 | Prisma schema snapshot & introspection lineage | FTR-353 |
| CAP-148 | Shared table contract, pagination and page-size standard | **NOT individually catalogued** — see POD-J and §7.3 |
| CAP-150 | Legacy API surface and dual router mount | FTR-273…280 (API platform, dual mount) |
| CAP-151 | Dual ASGI entrypoints | FTR-273…280 (API platform) |

### 7.3 Coverage gaps declared rather than papered over

Three census capabilities (CAP-010 SEO/PWA, CAP-122 X7 persisted API runtime
metrics, CAP-148 shared table/pagination standard) are **not** represented by an
individual FTR. They are not contradicted by this catalogue; they are simply
outside what this pass could evidence at feature granularity. They are raised as
**POD-J** rather than invented as features — consistent with AGENTS §62 and §74.

---

## 8. VERDICT, HAND-BACK & REMAINING WORK

**Verdict token:**

```
CT_FEATURE_01_COMPLETE_WITH_OBSERVATIONS
```

**Meaning of the verdict.** The discovery objective — a complete, evidence-backed
catalogue of CarbonTally features/functionality with configuration surfaces,
roles and traceability — is **met**: 354 features across 54 domains, each with a
controlled truth status, a primary actor and an evidence path, plus derived
persistence requirements and a census reconciliation. The verdict is
**WITH_OBSERVATIONS**, not clean, because the discovery surfaced facts that a
reader of this catalogue must not be allowed to miss:

1. **The release tree implements a feature surface that no durable local database
   carries.** 43 migrations (`20260905000000` → `20261020000000`) are unapplied;
   P16-R/P17 objects exist **only** in the disposable clone `ct_p17k_20260926`.
2. **`accounting_dimensions` is not a table** — P17-A adds 10 columns instead.
3. **Production is `UNKNOWN` for all 354 features** — production was never
   contacted, and no production verification artefact exists for this pass.
4. **`system_settings['platform_retention'].audit_log_retention_days = 1`** conflicts with the
   auditability expectations of AGENTS §33/§42 and is raised as POD-E.
5. **Three census capabilities (CAP-010, CAP-122, CAP-148) are not individually
   catalogued** and are raised as POD-J rather than invented.
6. **Ten PO decisions (POD-A…POD-J)** are open; none was decided by this document.

### 8.1 Hand-back

| Item | Value |
|---|---|
| Task ID | `CT-FEATURE-01-20260927-CARBONTALLY-COMPLETE-FEATURE-AND-FUNCTIONALITY-CATALOGUE-FROM-SCHEMA-CODE-AND-HISTORICAL-EVIDENCE` |
| Verdict | `CT_FEATURE_01_COMPLETE_WITH_OBSERVATIONS` |
| Canonical tree | `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, branch `p8-release-reconciled` |
| Historical tree | `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79`, branch `main` |
| Document | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` |
| Sections | §0 reading rules · §1 summary · §2 method/sources · §3 domain index · §4 feature catalogue (354 rows) · §5 derived schema/config requirements · §6 unresolved items/terminology/PO register · §7 census reconciliation · §8 verdict/hand-back |
| Features catalogued | **354** (`FTR-001…354`), contiguous, no gaps |
| Domains | **54** |
| Truth statuses | 313 `IMPLEMENTED_AND_WIRED` · 17 `PARTIALLY_IMPLEMENTED` · 9 `DOCUMENTED_ONLY` · 5 `HISTORICAL_ONLY` · 4 `IMPLEMENTED_BACKEND_ONLY` · 4 `SCHEMA_ONLY` · 1 each `SUPERSEDED` / `DEPRECATED` / `CODE_ONLY` / `PRESENT` (token-presence counts, §6.2) |
| Roles catalogued | Customer Owner/Admin/Member/Viewer · Consultant + team member · Client owner/staff · PE Manager/Staff · CT Operator/Reviewer/QC/Staff Admin/System Admin |
| Production states | 354 × `UNKNOWN` (never contacted) |
| DB evidence | 78 local databases probed read-only; flagship `postgres` = 116 public tables, 0 views, 975 organisations, 7,049 factors, 1,125 members, 46 migration-ledger rows; clone `ct_p17k_20260926` = 145 tables |
| Writes performed | **None** (docs only) |
| Migrations applied | **None** |
| Seeds/truncates | **None** |
| Secrets in document | **None** |

### 8.2 Companion deliverables (same task, `docs/architecture/`)

| # | Deliverable | Purpose |
|---|---|---|
| 1 | `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` | **this document** — the feature census |
| 2 | `CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md` | every configuration surface: settings tables/keys, env vars, feature flags, retention, limits, defaults, and who can change them |
| 3 | `CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md` | the `CAP-xxx ↔ FTR-xxx ↔ evidence` join, role→feature matrix, and end-to-end workflow traces |
| 4 | `CT-PO-CARBONTALLY-FEATURE-GAP-ANALYSIS-20260927.md` | classified gaps (PO decision / implementation / verification / environment), severity, and what closes each |
| 5 | `CT-PO-CARBONTALLY-FEATURE-DISCOVERY-20260927-REPORT.md` | the executive report: method, findings, limitations, acceptance language |

### 8.3 Remaining work (explicitly not performed here)

1. Verification of any feature by execution (running the API/UI/worker/tests) —
   outside the read-only discovery posture.
2. Production truth for any capability — requires an authorised production census.
3. Resolution of POD-A…POD-J — Product Owner decisions.
4. The ID-exact `CAP ↔ FTR` join and role→feature matrix — carried in
   deliverable #3; not duplicated here to keep this catalogue readable.

<!--CTEOF-->
