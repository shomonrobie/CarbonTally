# Gap 4 — Supplier Engagement Portal: Current State Research

**Prompt ID:** CT-GAP4-SUPPLIER-PORTAL-RESEARCH-2026-09-30-001
**Repository:** /home/shomonrobie/ct_93d5cdd
**Date:** 2026-09-30
**Mode:** READ-ONLY

---

## 1. Executive Summary

- **Overall stage: ABSENT (with reusable infrastructure present upstream).**
  No supplier-facing portal exists at any layer. There is no supplier invitation, no
  supplier-facing route, no questionnaire/data-request model, no supplier-response
  tracking, no supplier upload endpoint and no supplier-progress reporting. What exists
  is the *internal* supplier master-data capability (CRUD inside the authenticated
  app) plus a set of generic capabilities (documents, bulk upload, messaging,
  notifications, evidence, reporting) that a future supplier portal could reuse — but
  none of those capabilities currently exposes a supplier or unauthenticated surface.

- **Repo-language note on the gap label.** The string "Gap 4" in this repository does
  **not** refer to a supplier portal. The only `Gap 4` found in `docs/**` is
  `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md:754`
  ("Gap 4 — the 18 March 2026 CSRD amendment"), an unrelated regulatory-documentation
  gap. The supplier-portal concept appears only as an explicitly *deferred/out-of-scope*
  item (see §1 evidence below). The "internal gap reference: Gap 4" must therefore be
  treated as an external programme label not recorded in this repository.

- **Highest-risk unknowns.**
  1. Whether the P8-B2 tables (`evidence_line_items`, `provenance_line_links`) and the
     P17 accounting-dimension columns referenced below are actually applied in the
     authoritative database. Not determinable by static inspection; catalogue doc
     records them as "clone only / absent in flagship".
  2. Whether an unmerged/half-built supplier-portal branch or a second repo exists
     outside this tree (see the historical audit note that `suppliers.portal_user_id`
     was *considered* and deliberately not built).
  3. No DB connection was attempted, so per-database application state is UNKNOWN.

- **Estimated build distance.** Greenfield supplier-facing surface. The reuse targets
  named in the prompt (messaging, notifications, documents, bulk upload, evidence,
  customer factors, reporting, public/anonymous routing pattern) all exist as
  authenticated internal capabilities. Gap 4 requires: a supplier-identity/invitation
  model (new), a supplier-facing unauthenticated access path (new), a data-request /
  questionnaire model (new), supplier-scoped upload (new), supplier-provided factor
  capture (new wiring over partially-existing columns), supplier progress tracking
  (new), and supplier→evidence linkage (new). Estimate: **large multi-phase build**;
  the reuse targets reduce delivery cost but do not reduce schema/identity scope.

---

## 2. Component-by-Component Findings

### 2.1 Supplier invitation with unique link
- **Classification: ABSENT.**
- **Evidence (file paths, migrations, routes):**
  - The only invitation tables are for *internal users*, not suppliers:
    `supabase/migrations/00000000000000_init_schema.sql:345` (`public.pending_invites`)
    and `:356` (`public.user_invitations`), consumed by
    `backend/data/invitations.py` (`InvitationsRepository`, docstring "Invitations
    repository (V3 Phase 6) … organisation-scoped invitation records").
  - No supplier-facing invite table, token column, or route exists. Filename search for
    `*invite*`/`*invitation*` returns only `backend/data/invitations.py`; no
    `supplier_invite`, `supplier_portal` or equivalent.
  - The only unauthenticated "magic link" flow is user authentication, not supplier
    access: `frontend/src/MagicLink.jsx` (route `/auth/magic`,
    `frontend/src/App.js:1979`) and `frontend/src/BetaLogin.jsx`.
  - The single supplier API router is fully authenticated:
    `backend/api/v3_suppliers.py:51` (`require_org_member()`), `:70`
    (`require_org_admin()`), `:128`, `:146`.
- **Gaps and unknowns:** No supplier identity model, no invite/token issuance, no
  unauthenticated supplier route, no supplier login. Historical audit confirms this was
  a deliberate non-build: `docs/Final_Kimi/.../CarbonTally_v1.0_Management_Approval_Report.md:98`
  ("C28 Supplier-portal identity model … v2.0") and
  `docs/Final_Kimi/.../research/carbontally_dim03_perf_security_governance.md:160-161`
  ("`suppliers` has no `portal_user_id`/auth linkage and `users.user_type` has no
  supplier value").

### 2.2 Structured data request questionnaire
- **Classification: ABSENT.**
- **Evidence:** Whole-of-repo searches for `questionnaire`, `data_request`,
  `supplier_request` return **zero** hits in `backend/**`, `supabase/**`,
  `frontend/src/**` and `qa_harness/**` (the term appears only in marketing/product
  docs, e.g. `docs/Pricing/CarbonTally_Pricing_Comparison_Baseline_v2.md:47`). No model,
  table, API or UI exists.
- **Gaps and unknowns:** Entire questionnaire domain is missing (definition, issuance,
  response capture, scoring/completeness). See §2.8 for the *unrelated* taxonomy that
  exists.

### 2.3 Activity data CSV/Excel upload by suppliers
- **Classification: PARTIALLY_IMPLEMENTED (customer/consultant surface only; supplier
  surface ABSENT).**
- **Evidence:**
  - Upload capability exists and is wired, but only for authenticated customer/consultant
    actors: `frontend/src/BulkUpload.jsx`; `backend/data/upload_batches.py`
    (repo for `upload_batches`); table `public.upload_batches`
    (`supabase/migrations/00000000000000_init_schema.sql:1922`);
    `import_batches` (`supabase/migrations/20260807000000_add_import_batches.sql:21`);
    `backend/api/v3_documents.py`; legacy `backend/routes/upload.py`,
    `backend/routes/customer_documents.py`.
  - The feature catalogue records FTR-092/093 as `IMPLEMENTED_AND_WIRED`
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:401-402`).
  - There is **no** supplier-scoped upload route and no supplier upload UI. Route
    inventory for `upload`/`invite`/`supplier` returns only `/api/v3/suppliers` (CRUD)
    and the authenticated document surfaces.
- **Gaps and unknowns:** No template download for suppliers, no supplier-scoped
  ingestion, no supplier identity to attribute an upload to.

### 2.4 Supplier-specific factor capture
- **Classification: SCHEMA_ONLY (columns exist; no supplier-provided-factor service,
  API or UI).**
- **Evidence:**
  - `public.suppliers` already carries supplier-factor columns:
    `annual_emissions_scope1/2/3`, `reporting_year`, `emission_factor_scope1/2/3`,
    `emission_factor_unit`, `annual_emissions`, `emission_factor`
    (`supabase/migrations/00000000000000_init_schema.sql:486-517`). These are read/written
    only through the generic supplier CRUD (`backend/data/suppliers.py:13-18`,
    `backend/api/v3_suppliers.py`) — the V3 repository column list does **not** surface
    the `emission_factor*`/`annual_emissions_scope*` columns at all.
  - `public.customer_factors` has a free-text `factor_source` documented as
    "'CUSTOMER' (or supplier name)" but has **no** `supplier_id` and **no**
    `supplier_factor` flag (`supabase/migrations/20260810020000_v3m3_customer_factors.sql:54-108`).
  - No `supplier_factor`, `supplier_factors`, or supplier-provided-emission-factor table
    exists anywhere.
- **Gaps and unknowns:** No mechanism for a supplier to *provide* a factor, no
  provenance tying a factor to a specific supplier record, no approval path for
  supplier-supplied factors.

### 2.5 Progress dashboard (response tracking, completeness)
- **Classification: ABSENT (supplier variant); generic reporting exists but carries no
  supplier-response concept.**
- **Evidence:** No supplier-response/completeness table or metric exists. Reporting
  intelligence exists but is customer/consultant-scoped:
  `backend/api/v3_reporting.py` (`/api/v3/reporting/customer-dashboard` L69,
  `member-activity` L172, `audit-readiness` L378, etc.); catalogue FTR-216
  (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:625`). No
  supplier-progress endpoint and no supplier dashboard UI (UI inventory: no
  Supplier/Portal/Invite component beyond `SuppliersTab.jsx`, an internal admin tab).
- **Gaps and unknowns:** No per-supplier request state, no completeness metric, no
  reminder/nudging surface.

### 2.6 Evidence linkage into CarbonTally evidence trail
- **Classification: PARTIALLY_IMPLEMENTED (evidence trail exists; no supplier-data →
  evidence linkage).**
- **Evidence:**
  - Evidence infrastructure exists: `public.evidence_line_items`
    (`supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql:61`),
    `provenance_line_links` (`supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql`
    — implemented as `calculation_snapshots.source_line_item_id` L42 and
    `disclosure_value_evidence.source_line_item_id` L70); repository
    `backend/data/evidence_line_items.py`; API `backend/api/v3_evidence.py`
    (`/line-items/{line_item_id}` L103); UI
    `frontend/src/v3/components/EvidenceTrail.jsx`.
  - Critically, `evidence_line_items` references `manual_extraction_items(id)`
    (migration L64-65), **not** any supplier response/supplier-upload object. There is no
    column or table linking supplier-provided data to the evidence trail.
  - The catalogue records FTR-127/128 as `IMPLEMENTED_AND_WIRED` but notes the tables are
    "present in `qa133`/clones; absent in flagship"
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:456-457`).
- **Gaps and unknowns:** Application state of the P8-B2 tables in the authoritative DB
  is UNKNOWN. No supplier provenance path exists.

### 2.7 Messaging/notification reuse
- **Classification: BACKEND_ONLY (reusable infrastructure exists and is wired for
  authenticated actors; no supplier outreach path).**
- **Evidence:**
  - Messaging: `public.conversations`, `conversation_participants`, `messages`
    (`supabase/migrations/00000000000000_init_schema.sql:673,695,709`); repository
    `backend/data/messaging.py`; API `backend/api/v3_messaging.py`
    (`prefix="/api/v3/messaging"` L35; 10 endpoints); catalogue FTR-255
    (`...FEATURE-CATALOGUE-20260927.md:694`).
  - Notifications: `public.notifications`, `notification_delivery`,
    `notification_templates` (`init_schema.sql:1409,1429,151`);
    `backend/data/notifications.py`; UI `frontend/src/components/NotificationSettings.jsx`;
    API `backend/api/v3_notifications.py` (3 endpoints); email delivery via Resend
    (`services/email_service.py`, `services/v3_email.py`) — FTR-249-254
    (`...FEATURE-CATALOGUE-20260927.md:683-688`).
  - **No supplier participant type or supplier recipient exists.** All messaging and
    notification dependencies resolve to authenticated org members/consultants/staff.
- **Gaps and unknowns:** A supplier outreach flow would need a new participant/recipient
  model; the transport (conversations + notifications + Resend) is reusable.

### 2.8 Questionnaire engine reusing document type taxonomy
- **Classification: ABSENT as a questionnaire engine; the referenced taxonomy exists but
  is unrelated.**
- **Evidence:**
  - The document taxonomy exists: `public.document_types`
    (`init_schema.sql:55`), `public.document_type_categories` (L34) — the latter carries
    `requires_supplier BOOLEAN DEFAULT FALSE` (L43) and related `requires_facility`,
    `requires_asset`, `requires_date_range` flags. FTR-097
    (`...FEATURE-CATALOGUE-20260927.md:406`).
  - There is **no** questionnaire engine, questionnaire table, form schema, or
    `questionnaire_response`. Searches for `questionnaire` return nothing in code.
- **Gaps and unknowns:** The taxonomy is a classification reference for uploaded
  documents; it is not a questionnaire definition/response system and there is no code
  bridging it to any supplier data request.

### 2.9 Bulk upload reuse
- **Classification: IMPLEMENTED_AND_WIRED (as a customer/consultant capability); reuse
  for a supplier surface is a design target, not implemented.**
- **Evidence:** `frontend/src/BulkUpload.jsx`; `public.upload_batches`
  (`init_schema.sql:1922`) and `import_batches`
  (`20260807000000_add_import_batches.sql:21`); `backend/data/upload_batches.py`;
  catalogue FTR-093 (`...FEATURE-CATALOGUE-20260927.md:402`).
- **Gaps and unknowns:** The batch model is org-scoped and authenticated-actor-scoped;
  no supplier-attributed batches.

### 2.10 Reporting intelligence reuse
- **Classification: IMPLEMENTED_AND_WIRED (generic); no supplier-progress reporting.
  **
- **Evidence:** `backend/api/v3_reporting.py` (15 endpoints incl.
  `/api/v3/reporting/customer-dashboard`, `emissions-trend`, `member-activity`,
  `audit-readiness`, `audit-activity`, `consultant-portfolio`); catalogue FTR-216
  (`...FEATURE-CATALOGUE-20260927.md:625`).
- **Gaps and unknowns:** No supplier-progress dataset to report on (no response-tracking
  schema — §2.5).

---

## 3. Reuse Infrastructure Verification

| Feature ID | Table / Route / File | Present? | Reachable? | Notes |
|---|---|---|---|---|
| FTR-089 Supplier master data | `suppliers`, `supplier_categories` (`init_schema.sql:473,85`); `/api/v3/suppliers` (`backend/api/v3_suppliers.py:21`, 5 endpoints); UI `frontend/src/v3/admin/SuppliersTab.jsx` | Yes | Yes (authenticated only) | Wired into `frontend/src/v3/admin/AdminPage.jsx:12,123`; frontend client `frontend/src/v3/api.js:393-416`. Org-scoped; no supplier/anonymous access path. |
| FTR-090 Supplier resolution engine | `backend/engines/supplier_resolution.py` | Yes | Yes (internal) | Pure/deterministic org-scoped matching on extraction; no HTTP surface of its own (invoked by extraction/processing). |
| FTR-091 Supplier category taxonomy | `supplier_categories` (`init_schema.sql:85`) | Yes | Yes (via supplier CRUD) | No `supplier_category_id` write exposure beyond `SupplierCreate.supplier_category_id`. |
| FTR-255 Messaging | `conversations`, `conversation_participants`, `messages`; `/api/v3/messaging` (`backend/api/v3_messaging.py:35`) | Yes | Yes (authenticated) | No supplier participant/recipient concept. |
| FTR-249–254 Notifications | `notifications`, `notification_delivery`, `notification_templates`; `/api/v3/notifications` (`backend/api/v3_notifications.py:13`) | Yes | Yes (authenticated) | Email via Resend (`services/email_service.py`, `services/v3_email.py`). No supplier recipient. |
| FTR-127 Evidence line items | `evidence_line_items` (`20260916000000_p8_b2_evidence_line_items.sql:61`); `/api/v3/evidence` (`backend/api/v3_evidence.py:48`) | Yes (in repo) | Partially | Catalogue records "present in clones; absent in flagship" (`...FEATURE-CATALOGUE-20260927.md:456`). DB application state UNKNOWN. |
| FTR-128 Provenance line links | `calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id` (`20260916010000_...sql:42,70`); `backend/data/evidence_line_items.py` | Yes (in repo) | Partially | "clone only" per catalogue (`:457`). No supplier linkage. |
| FTR-139 Customer factors | `customer_factors` (`20260810020000_v3m3_customer_factors.sql:54`); `/api/v3/customer-factors` (`backend/api/customer_factors.py:43`, 6 endpoints); UI `frontend/src/v3/admin/CustomFactorsTab.jsx` | Yes | Yes (authenticated) | Org-scoped; `factor_source` free-text only; no `supplier_id`. |
| FTR-092 Document upload | `/api/v3/documents` (`backend/api/v3_documents.py`); `customer_documents` (`init_schema.sql:572`) | Yes | Yes (authenticated) | `customer_documents.supplier_id` FK exists (`init_schema.sql:596`). |
| FTR-093 Bulk upload | `frontend/src/BulkUpload.jsx`; `upload_batches` (`init_schema.sql:1922`); `import_batches` (`20260807000000_add_import_batches.sql:21`) | Yes | Yes (authenticated) | No supplier-scoped batch. |
| FTR-216 Reporting intelligence | `/api/v3/reporting/*` (`backend/api/v3_reporting.py`) | Yes | Yes (authenticated) | No supplier-progress reporting. |
| FTR-341–345 Public/visitor surface | `frontend/src/LandingPage.jsx`, `PricingPage.jsx`, `PrivacyPolicy.jsx`, `BetaSignup.jsx`, `frontend/src/public/**`; `frontend/src/App.js:1959-1979` | Yes | Yes (unauthenticated) | Establishes that unauthenticated public routing *exists as a pattern*, but **no** supplier route is among them. |

**Reachability caveat.** "Reachable" above means the module is registered in
`backend/api/router.py` (`v3_suppliers` L227, `v3_notifications` L213,
`v3_messaging` L232, `v3_reporting` L237, `v3_evidence` L249) or mounted in
`frontend/src/App.js`. No P8-B2/P17-clone-only object was verified against a live
database (see §9).

---

## 4. CBAM / CSRD / ESRS Adjacency Findings

**What exists**
- CSRD/ESRS exist as **report types and disclosure frameworks**, not as supplier-data
  collection:
  - Organisation framework flags: `esrs_enabled`, `secr_enabled`, `issb_enabled`
    (`supabase/migrations/00000000000000_init_schema.sql:208`;
    `backend/data/organizations.py:27,72,172`;
    `frontend/src/v3/admin/ProfileTab.jsx:62,165`).
  - Disclosure model: framework code `ESRS_E1` and `ESRS_E1_QUANT`
    (`supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql:49,188,546,556`;
    `backend/data/disclosure.py:177,190`; `backend/domain/disclosure.py:32,94,167-178`).
  - Report-generation surface accepts CSRD type: `backend/routes/reports.py:243,1456,1463`;
    `frontend/src/App.js:1371` (`type: 'CSRD'`).
  - Public glossary defines CSRD/ESRS for visitors: `frontend/src/public/glossaryData.js:72-76`.
- **CBAM does not exist in application code or schema at all.** The only two hits are
  marketing/legacy-mock text: `docs/Pricing/CarbonTally_Pricing_Comparison_Baseline_v2.md:47`
  (competitor feature list) and `docs/architecture/UI2/js/batch_management.js` (legacy
  UI mock). No CBAM goods taxonomy, no Annex I mapping, no embedded-emissions
  calculation.

**What does not exist**
- No `cbam`, `csrd`, `esrs`, `scope3_primary`, `supplier_data` or `supplier_primary`
  naming in backend logic, migrations or frontend. No CSRD Scope-3 data-collection form,
  no ESRS data-point mapping module, no CBAM embedded-emissions engine.

**Extension potential**
- The disclosure framework scaffolding (`ESRS_E1`) is a *reporting-output* layer and
  could host CSRD/ESRS disclosure values, but it provides **no** supplier-primary-data
  intake. Gap 4 would be building the Scope-3 primary-data intake from scratch;
  CBAM would additionally need an entirely new taxonomy + calculation layer (nothing to
  extend).

---

## 5. Migration Inventory (Supplier-Related)

All paths relative to `supabase/migrations/` unless noted. "Applied in which DBs" is
UNKNOWN for all rows — no live database was queried (constraint §5), and the catalogue
document records divergent per-database state (see §9).

| Migration File | Tables Created | Columns Added / Touched | Applied in Which DBs |
|---|---|---|---|
| `00000000000000_init_schema.sql` | `suppliers` (L473), `supplier_categories` (L85), `customer_documents` (L572), `upload_batches` (L1922), `user_invitations` (L356), `pending_invites` (L345), `document_type_categories` (L34), `document_types` (L55) | `suppliers` full column set incl. `emission_factor_scope1/2/3`, `annual_emissions_scope1/2/3`, `supplier_type`, `supplier_rating`, `is_certified`; `customer_documents.supplier_id` FK (L596); `document_type_categories.requires_supplier` (L43) | UNKNOWN |
| `20260800000000_rc2_schema.sql` | — | `suppliers.sort_code` (L223, PII register) | UNKNOWN |
| `20260801000000_rc2_constraints.sql` | — | supplier constraint/backfill handling (L152, L168) | UNKNOWN |
| `20260802000000_rc2_indexes.sql` | — | `suppliers_org_idx`, `suppliers_name_trgm_idx`, `suppliers_vat_number_trgm_idx` (L52-85) | UNKNOWN |
| `20260803000000_rc2_rls.sql` | — | `supplier_categories` RLS reference-list grant (L120) | UNKNOWN |
| `20260806000000_rc2_verification.sql` | — | verification of `suppliers.sort_code` and `customer_documents.supplier_id` FK (L90, L115, L153) | UNKNOWN |
| `20260810020000_v3m3_customer_factors.sql` | `customer_factors` (L54) | `factor_source` comment references supplier name (L108); no `supplier_id` | UNKNOWN |
| `20260925000000_p8_rls_4b_group1_enablement.sql` | — | RLS enablement referencing `suppliers`, `supplier_categories`, `upload_batches` (L76, L88) | UNKNOWN |
| `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | — | `suppliers` acting-for columns (`ALTER TABLE public.suppliers` L314; `acting_for_organization_id` comment L334; index `idx_suppliers_acting_for` L341); data-quality vocabulary value `primary_supplier` (L80, L166) | UNKNOWN |
| `20261011000000_p17c_contractual_instruments_and_allocations.sql` | — | instrument type `supplier_specific_contract` (L64) | UNKNOWN |
| `20261013000000_p17h_estimation_and_assumption_records.sql` | — | estimation source value `supplier_specific` (L49) | UNKNOWN |
| `20261014000000_p17_10_product_contract_reporting_dimensions.sql` | — | references canonical activity `supplier_id`/`supplier_name`, `transaction_provider`/`underlying_supplier` (L7-34) | UNKNOWN |
| `20261020000000_p17k_governed_capability_catalogue.sql` | — | reference-data mention of supplier figure vs spend-based (L301) | UNKNOWN |

**Not applied / non-migration artefacts.**
- `docs/architecture/DB_Migration/MIGRATION_004_SUPPLIER_MANAGEMENT.sql` defines
  `suppliers`, `supplier_contacts`, `supplier_addresses`, `supplier_categories`,
  `supplier_documents`, `supplier_notes`, `supplier_tags`, `supplier_emissions`,
  `supplier_spend` — but it lives in the **docs** directory and is **not** part of
  `supabase/migrations/`. Its `suppliers` shape (e.g. `supplier_code`, `legal_name`,
  `tier`) does **not** match the applied `suppliers` table (`init_schema.sql:473`), and
  none of `supplier_contacts`, `supplier_emissions`, `supplier_spend`, etc. appear in
  the live migration tree. Treat as **historical design, not applied**.
- `database/rc2/*.sql` duplicate the RC2 supplier objects and are not the applied
  migration chain.

**No supplier data-request / response / factor-provision tables exist in any migration.**

---

## 6. Route Inventory (Supplier-Related)

| Route Path | Method | Module | Auth Required? | Purpose |
|---|---|---|---|---|
| `/api/v3/suppliers` | GET | `backend/api/v3_suppliers.py:43` | Yes (`require_org_member`, L51) | List/search org suppliers |
| `/api/v3/suppliers` | POST | `backend/api/v3_suppliers.py:67` | Yes (`require_org_admin`, L70) | Create supplier (acting-for attributed) |
| `/api/v3/suppliers/{supplier_id}` | GET | `backend/api/v3_suppliers.py:111` | Yes (`require_org_member`, L114) | Read supplier |
| `/api/v3/suppliers/{supplier_id}` | PUT | `backend/api/v3_suppliers.py:124` | Yes (`require_org_admin`, L128) | Update supplier |
| `/api/v3/suppliers/{supplier_id}` | DELETE | `backend/api/v3_suppliers.py:143` | Yes (`require_org_admin`, L146) | Remove supplier |

- **These are the only supplier routes in the codebase.** A search of `backend/api/**`
  and `backend/routes/**` for a `supplier` route prefix returns only
  `backend/api/v3_suppliers.py:21`. There is **no** `/api/v3/suppliers/*` invite/upload/
  questionnaire/progress sub-route.
- Legacy `backend/routes/**` contains **no** supplier router (only an unrelated
  descriptive string in `backend/routes/admin/document-types.py:247`).
- Related authenticated routes that a portal might reuse are listed in §3; none is
  supplier-facing or unauthenticated.
- **Unrelated "portal" naming:** `frontend/src/PDFIngestionPortal.jsx` and
  `frontend/src/css/PDFIngestionPortal.css` are an authenticated customer document-
  ingestion UI, **not** a supplier portal.

---

## 7. UI Inventory (Supplier-Related)

| Component Path | Route | Purpose | Wired? |
|---|---|---|---|
| `frontend/src/v3/admin/SuppliersTab.jsx` | tab within `/organization` (AdminPage) | Internal supplier master-data CRUD | Yes — imported/rendered in `frontend/src/v3/admin/AdminPage.jsx:12,123` |
| `frontend/src/v3/api.js` (`listSuppliers`/`getSupplier`/`createSupplier`/`updateSupplier`/`removeSupplier`, L393-416) | — | API client for `/api/v3/suppliers` | Yes |
| `frontend/src/PDFIngestionPortal.jsx` | (customer ingestion surface) | Document ingestion portal — **not supplier-facing** | Yes (unrelated to Gap 4) |
| `frontend/src/BulkUpload.jsx` | customer document UI | Bulk document upload | Yes (authenticated) |
| `frontend/src/MagicLink.jsx` | `/auth/magic` (`App.js:1979`) | User authentication magic link | Yes (not supplier) |

- **No** UI component contains "Supplier Portal", "Questionnaire", "Invite" (as a
  supplier concept), or a supplier-facing route. Frontend `App.js` routes enumerated
  (`App.js:1959-2269`) contain no `/supplier/*` path. `frontend_backup_pre_v3_public_20260827/`
  and `carbon-tally-ui-demo/` contain no supplier-portal UI either (search for
  `supplier` in `carbon-tally-ui-demo` returns nothing).

---

## 8. Build Distance Assessment

| Build Component | Current State | Remaining Work | Estimated Effort |
|---|---|---|---|
| Supplier invitation w/ unique link | ABSENT | Supplier-identity/invite model + token issuance + unauthenticated route + link UI | Large |
| Structured data request questionnaire | ABSENT | Definition model, issuance, response capture, completeness scoring | Large |
| Supplier activity-data CSV/Excel upload | PARTIALLY_IMPLEMENTED (customer-only) | Supplier-scoped route + identity attribution + template download; reuse `upload_batches`/ingestion | Medium |
| Supplier-specific factor capture | SCHEMA_ONLY | Service/API/UI over existing `suppliers` factor columns; supplier-provenance link; approval path | Medium |
| Progress dashboard | ABSENT | Response-tracking schema + completeness metrics + supplier-facing dashboard + reminders | Large |
| Evidence linkage (supplier-data → evidence) | PARTIALLY_IMPLEMENTED | New supplier-source object + link into `evidence_line_items`/provenance model | Medium–Large |
| Messaging/notification reuse | BACKEND_ONLY (reusable) | Supplier participant/recipient model; event wiring | Medium |
| Questionnaire engine reuse of taxonomy | ABSENT | Questionnaire engine; taxonomy bridging | Large |
| Bulk upload reuse | IMPLEMENTED_AND_WIRED (customer) | Supplier attribution/scoping | Small–Medium |
| Reporting intelligence reuse | IMPLEMENTED_AND_WIRED (generic) | Supplier-progress dataset + endpoint | Medium |

---

## 9. Risks and Unknowns

**Unverified items**
- Database application state of every supplier-related migration (no DB queried; see
  constraint §5). The applied `suppliers` shape (`init_schema.sql:473`) is inferred from
  repository migrations, not read live.
- P8-B2 evidence tables: the catalogue asserts clone-only presence
  (`...FEATURE-CATALOGUE-20260927.md:456-457`) with a documented downgrade in
  `docs/architecture/CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md:227-228`
  ("table created by unapplied `20260916000000`; no durable store anywhere").
- Whether `20261010000000_p17a` (supplier acting-for columns) is present in the
  authoritative DB, given the catalogue notes P17 objects "appear only in clones/demo"
  (`docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:126`).

**Assumptions that must be confirmed by PO or engineering**
- The "Gap 4 = Supplier Engagement Portal" mapping is external; the repository's own
  "Gap 4" is an unrelated CSRD item (§1). PO must confirm the programme numbering.
- Whether a supplier **identity** is intended (login-less magic link vs. authenticated
  supplier user). Repo evidence points to an intentional non-build of a supplier
  identity model (audit C28), so the target identity model is a genuine open decision.
- Whether supplier-provided data should be modelled as documents (reusing
  `customer_documents`/`upload_batches`) or as a new first-class supplier-response
  object.

**Schema present in clones but not flagship (if applicable)**
- `evidence_line_items`, `provenance_line_links` (P8-B2) — clone-only per catalogue.
- P17 accounting-dimension / supplier acting-for columns and `scope3_categories`,
  `estimation_records` — "appear only in clones/demo" per
  `CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:126`.

---

## 10. Recommendations for Next Research Pass

**Specific files / modules / DBs to inspect**
- `backend/api/v3_documents.py`, `backend/routes/upload.py`,
  `backend/routes/customer_documents.py`, `backend/data/upload_batches.py` — to confirm
  the exact upload/batch contract a supplier surface could extend.
- `backend/data/evidence_line_items.py` and `backend/api/v3_evidence.py` — to confirm
  how a new supplier-source object could join the evidence trail.
- `backend/data/messaging.py`, `backend/api/v3_messaging.py`,
  `backend/data/notifications.py` — to confirm the participant/recipient extension
  points for supplier outreach.
- `backend/auth.py`, `backend/api/dependencies.py`, `backend/api/router.py` — to confirm
  the unauthenticated-route pattern (public visitor routes) that a supplier magic-link
  route would follow.
- Live DB introspection (read-only) on the authoritative environment to confirm which
  migrations in §5 are applied.

**Questions for engineering**
1. Is there an out-of-tree branch, second repository, or product spec defining Gap 4
   (Supplier Engagement Portal) that is not in this tree?
2. Is a supplier identity/login in scope, or is the intent a fully login-less tokenised
   link?
3. Should supplier-submitted data become `customer_documents`/`upload_batches` records,
   or a distinct supplier-response model?
4. Should supplier-provided emission factors be captured on `suppliers`
   (`emission_factor_*` columns, already present) or as `customer_factors` rows with a new
   supplier linkage?
5. Which environment is authoritative for P8-B2/P17 objects (flagship vs clone)?

---

## 11. Appendix — Raw Search Evidence

**Commands run (representative, read-only; bash, UTF-8)**
- `find . -type f \( -iname '*supplier*' -o -iname '*questionnaire*' -o -iname '*data_request*' -o -iname '*invite*' -o -iname '*portal*' -o -iname '*cbam*' -o -iname '*csrd*' -o -iname '*esrs*' \) -not -path '*/node_modules/*' -not -path '*/.git/*'`
- `grep -rIil -E 'cbam|csrd|esrs' .` (excl. `node_modules`, `.git`, `__pycache__`)
- `grep -rEin 'questionnaire|data_request|supplier_invite|supplier_portal|supplier_factor|magic.?link|supplier_request' backend/api backend/data backend/engines backend/services backend/domain backend/routes supabase/migrations prisma frontend/src`
- `grep -rEin 'cbam|csrd|esrs|scope3_primary|supplier_data|supplier_primary' backend/api backend/data backend/engines backend/services backend/domain backend/routes supabase/migrations prisma frontend/src`
- `grep -rniE 'create table[^;]*supplier' supabase/migrations database`
- `grep -nEi 'CREATE TABLE|supplier|evidence_line|provenance_line|customer_factor|upload_batch|import_batch|notification|conversation|document_type|invitation|questionnaire' supabase/migrations/00000000000000_init_schema.sql`
- `grep -rEi 'FTR-089|FTR-090|FTR-091|FTR-092|FTR-093|FTR-097|FTR-127|FTR-128|FTR-139|FTR-216|FTR-24[9]|FTR-25[0-5]|FTR-34[1-5]' docs backend/featurelist.txt`
- `grep -nE '<Route ' frontend/src/App.js`
- `grep -rnE 'prefix="[^"]*supplier' backend/api backend/routes`
- `for f in supabase/migrations/*.sql; do grep -niE 'supplier' "$f"; done` (targeted subset reported in §5)

**Files inspected (primary evidence)**
- `backend/api/v3_suppliers.py`, `backend/data/suppliers.py`, `backend/data/invitations.py`,
  `backend/engines/supplier_resolution.py`, `backend/domain/partners.py`,
  `backend/api/router.py`, `backend/api/v3_messaging.py`, `backend/api/v3_notifications.py`,
  `backend/api/v3_reporting.py`, `backend/api/v3_evidence.py`, `backend/api/customer_factors.py`,
  `backend/data/upload_batches.py`, `backend/featurelist.txt`
- `supabase/migrations/`: `00000000000000_init_schema.sql`,
  `20260800000000_rc2_schema.sql`, `20260801000000_rc2_constraints.sql`,
  `20260802000000_rc2_indexes.sql`, `20260803000000_rc2_rls.sql`,
  `20260806000000_rc2_verification.sql`, `20260807000000_add_import_batches.sql`,
  `20260810020000_v3m3_customer_factors.sql`, `20260905000000_gate4_actor_provenance.sql`,
  `20260914000000_p8_b1_disclosure_model_foundation.sql`,
  `20260916000000_p8_b2_evidence_line_items.sql`,
  `20260916010000_p8_b2_provenance_line_links.sql`,
  `20260925000000_p8_rls_4b_group1_enablement.sql`,
  `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql`,
  `20261011000000_p17c_contractual_instruments_and_allocations.sql`,
  `20261013000000_p17h_estimation_and_assumption_records.sql`,
  `20261014000000_p17_10_product_contract_reporting_dimensions.sql`,
  `20261020000000_p17k_governed_capability_catalogue.sql`
- `docs/architecture/DB_Migration/MIGRATION_004_SUPPLIER_MANAGEMENT.sql`
- `frontend/src/App.js`, `frontend/src/v3/admin/SuppliersTab.jsx`,
  `frontend/src/v3/admin/AdminPage.jsx`, `frontend/src/v3/api.js`,
  `frontend/src/BulkUpload.jsx`, `frontend/src/PDFIngestionPortal.jsx`,
  `frontend/src/MagicLink.jsx`, `frontend/src/public/glossaryData.js`
- `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md`,
  `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`,
  `docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md`,
  `docs/architecture/CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md`,
  `docs/architecture/CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md`,
  `docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md`,
  `docs/cline/prompt-history/CT-P8-DISCOVERY-20260912-008.md`,
  `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/CarbonTally_v1.0_Management_Approval_Report.md`,
  `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/research/carbontally_dim03_perf_security_governance.md`
- `qa_harness/db/schema_inventory.py`, `qa_harness/config/roles.yaml`

**Negative results (searched but not found)**
- `questionnaire` — **0 hits** in `backend/api`, `backend/data`, `backend/domain`,
  `backend/routes`, `backend/services`, `supabase`, `frontend/src`, `qa_harness`.
- `data_request` — **0 hits** in `backend`, `supabase`, `frontend/src`.
- `supplier_invite`, `supplier_portal`, `supplier_factor`, `supplier_request` — **0 hits**
  in code/schema.
- Supplier-facing or unauthenticated supplier route — **not found** (only
  `/api/v3/suppliers`, all authenticated).
- `S upplier Portal` / `Questionnaire` / `Invite` supplier UI component — **not found**;
  no `/supplier/*` route in `frontend/src/App.js`.
- CBAM in application code/schema — **not found** (only in `docs/Pricing` marketing text
  and a legacy UI mock `docs/architecture/UI2/js/batch_management.js`).
- Supplier data-request / supplier-response / supplier-provided-factor table — **not
  found** in any migration.
- Supplier actor/participant in messaging or notifications — **not found**.
- An internal `Gap 4 = Supplier Engagement Portal` reference — **not found**; the only
  `Gap 4` in docs is the CSRD-amendment documentation gap.
