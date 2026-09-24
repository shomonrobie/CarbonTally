# CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924

**Type:** READ-ONLY FORENSIC PRODUCT-CAPABILITY / ARCHITECTURE / DEMO-EXPERIENCE STUDY. **Authorizes nothing.**
**Date:** 2026-09-24 (session local, UTC+06:00) · **Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Remote:** `github`
**Deliverable:** reverse-engineer the *actual* CarbonTally product — personas, topology, PE workflow, lifecycle, messaging, reporting, evidence, Insight, document processing — and define what must exist in a credible investor demo, potential-customer demo and realistic demo-user environment.

**Evidence labels:** `CODE-TRACED` · `DATABASE-OBSERVED` · `BROWSER-VERIFIED` · `GIT-VERIFIED` · `DOCUMENT-SOURCED` · `INFERENCE` · `UNKNOWN`.

---

## 1. Executive conclusion

**CarbonTally is a far broader operational product than its demo currently shows. The capability surface is real; the demonstration surface is thin, unconfigured and, in three places, empty.**

1. **The persona model is comprehensive and code-enforced**: five operating planes — **customer** (`owner`/`admin`/`member`/`viewer`), **consultant firm** (plus client organisations with an engagement lifecycle), **processing entity** (`pe_manager`/`pe_staff`), **internal CarbonTally staff** (role-permission catalogue incl. system admin) and **system administration** — wired through nine `require_*` authorization gates and a fail-closed frontend `RoleRoute`. `CODE-TRACED`.
2. **The Manual Processing Entity workflow is genuinely implemented — and never exercised in the current demo.** Schema: batches/items carry `entity_id` (NULL = internal processing); a dedicated `work_item_assignments` ledger records `assign|reassign|claim|recover` with `assignee_kind ∈ {internal_staff, processing_entity}` and close reasons `released|completed|reassigned|recovered|superseded`, **at most one open assignment per item**; a PE API surface exists (`/api/v3/pe/*`: work, claim, release, complete, extract, map, validate, calculate, pe-review, pe-qc, clarify, issues, team, workspace); FIN-06 `manual_processing_grants` gates manual processing off by default. **Data**: the Demo Lab has **0 work_item_assignments, 0 grants, 0 PE-assigned work**; the legacy dataset has **2** assignments. `CODE-TRACED` + `DATABASE-OBSERVED`.
3. **PE ↔ CarbonTally operational messaging exists as a separate plane** (`conversation_kind = 'entity'`, actor domains `pe`/`ops`, batch/item context validated against the assignment, internal staff gated on `can_manage_staff`), while **customer-plane messaging** (`org` conversations) admits org members, granted consultants and internal support staff and **explicitly excludes PE staff**. `CODE-TRACED`.
4. **Reporting is a full lifecycle** (`DRAFT → REVIEWED → APPROVED → FINAL`, plus `CHANGES_REQUESTED`/`REJECTED`/`SUPERSEDED`, immutable once approved/final) with generation, content, versions, download and PDF routes — yet **every report version in every database is `DRAFT`**. `CODE-TRACED` + `DATABASE-OBSERVED`.
5. **Document processing supports PDF, scanned PDF/image (Tesseract with a RapidOCR/ONNX fallback), CSV and XLSX** (tabular parse, no LLM for spreadsheets; OCR is an environment dependency). The external generator — local checkout **= the pinned commit `8ade2bf…`** — can produce 8 document types with injected difficulty, but CarbonTally's **factor coverage resolves only 2 of 11 curated scenarios** (natural gas, water); electricity/diesel/waste are ambiguous or no-match and **spend has no factors at all**. `CODE-TRACED` + `DOCUMENT-SOURCED`.
6. **The evidence chain is architecturally complete but empty everywhere**: `evidence_line_items` is populated only by an offline, authorization-gated CLI (`backfill_evidence_line_items`), never by online processing; the independently verified Viewer therefore has nothing to display in any environment. `CODE-TRACED` + `DATABASE-OBSERVED`.
7. **Insight is implemented (10 tools, deterministic planner, `/insight` UI) but cannot run in any local database** because the six Insight migrations are unapplied. `DATABASE-OBSERVED`.
8. **No safe read-only production inspection path exists.** `/home/shomonrobie/carbon_tally/.env.production` holds a **service-role key** and an **owner-level Postgres URI** (both mutation-capable) plus public anon keys — there is **no read-only credential**, so production was **not contacted**: `LIVE INSPECTION BLOCKED — NO SAFE READ-ONLY ACCESS PATH`. `CODE-TRACED` (credential *types* only; **no value was read, printed or transmitted**).

**Consequence:** the binding constraint is **not** missing product capability but **unpopulated, unconfigured or unprovisioned capability** — mostly *data, configuration and demonstration* work, plus two genuine code gaps (an online evidence-line materialisation path; factor coverage/browse fallback).

---

## 2. Repository / Git baseline

| Item | Value | Evidence |
| --- | --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` | `GIT-VERIFIED` |
| Branch | `p8-release-reconciled` | `GIT-VERIFIED` |
| HEAD | `f54c61c7128f10abc041761e06d22d610922b821` — `docs(p12): comprehensive investor-ready platform forensic study (planning artifact only)` | `GIT-VERIFIED` |
| `github/p8-release-reconciled` | identical SHA | `GIT-VERIFIED` |
| Alignment | `HEAD...github/p8-release-reconciled` → `0 0` | `GIT-VERIFIED` |
| Working tree | ` M .gitignore` (pre-existing PO change) + untracked PO/CoStrict artefacts (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, 8 untracked `docs/` reference documents) | `GIT-VERIFIED` |
| Remotes | `github` = `https://github.com/shomonrobie/CarbonTally.git` (authoritative); `origin` = `/tmp/ct_step2` (not contacted) | `GIT-VERIFIED` |
| Release migrations | **81** | `GIT-VERIFIED` |
| Code scale | `backend/api` 55 route modules · 103 unit-API test modules · 45 integration test modules · 52 frontend routes | `CODE-TRACED` |

**Prior studies this builds on (referenced, not repeated):** `CT-PO-P12-INVESTOR-DEMO-READINESS-PREFLIGHT-20260923.md` (698 lines) and `CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md` (892 lines). **This study's new contribution:** persona/topology/PE/lifecycle/messaging/reporting/document-processing reverse-engineering, the production-access safety determination, the generator↔product coverage comparison, and the demo design (topology, dataset, journeys).

---

## 3. Evidence sources reviewed

| Group | Sources | What was taken |
| --- | --- | --- |
| Migrations (81) | `00000000000000_init_schema.sql`; `20260810000000_v3m1_processing_entities`; `…v3m2_entity_relationships`; `…v3m6_entity_rls`; `…v3m8_system_admin_role_model`; `20260902020000_v1_2_dual_origin_workflow`; **`20260902030000_phase5_work_item_assignments`**; `20260903010000_ws4_gate3_4a_item_assignment_foundation`; `20260829000000_v3m9_durable_automatic_processing`; D-series RLS hardening; P6-2x consultant series; reporting-lifecycle; disclosure B1–B4; Insight I1–I4/P2/P3 | status vocabularies, ledger shapes, RLS posture, lifecycle constants |
| Backend | `auth.py`; `api/{v3_pe,v3_qc,v3_review,v3_processing_workflow,v3_consultants,v3_messaging,v3_reports,v3_organizations,v3_suppliers,v3_vehicles,v3_documents,v3_evidence,v3_exports,manual_processing_admin}.py`; `data/{manual_extraction,evidence_line_items,messaging,manual_processing}.py`; `services/{automatic_extraction,automatic_processing}.py`; `domain/{workflow,manual_processing,partners,staff,entity,report_lifecycle,issue,customer_factor}.py` | persona gates, PE routes, lifecycle, messaging authorization, reporting lifecycle, extraction formats |
| Frontend | `App.js` (52 routes); `v3/components/RoleRoute.jsx`; `v3/insight/*`; `v3/evidence/SourceEvidenceViewer.jsx` | UI surfaces per persona, guard semantics |
| Demo tooling | `tools/demo_lab/*` (15 files), `t3_manifest.json`, `README.md`, `run_demo_lab.sh`, `reset_demo_lab.sh`; `docs/audit/cline/CARBONTALLY_V3_INVESTOR_DEMO_DATA_REPORT.md` | demo topology, corpus contract, reset mechanics, historical dataset spec |
| Verification records | DR-001…DR-007; `OHD_TASK_079`; `OHD-P8-I1/I2/I3(+re-verification)`; Source Evidence Viewer OHD verification; P1/P2/P3 series incl. P3-IV-01 remediation/re-verification; INS-01 closure/reconciliation; master preflight; Insight Architecture v2; Question Library; Capability/Decision matrices; QA-AI-001 | independently verified vs claimed |
| Synthetic generator | `/home/shomonrobie/carbon_tally_synthetic_documents` (git `origin` = `carbon_tally_synthetic_documents_generator`, **HEAD `8ade2bf778d518d59924905849ab114ab2d0820a`** = CarbonTally's pin), `README.md`, `generation_report.md`, `generator/*` | document types, difficulty mix, corpus inventory, truth sidecars |
| Production config | `/home/shomonrobie/carbon_tally/.env.production` — **credential types only, no values** | §18 safety determination |
| Local databases | `carbontally_demo_local` (136 tables), `ct_local_93d5cdd` (135), `postgres` (116, legacy investor dataset), `carbontally_qa_phase8` (133) | persona/assignment/messaging/reporting data reality |

---

## 4. Current product architecture (as implemented)

```text
React SPA (frontend/src)              52 routes · public site + 5 authenticated planes
        │  Supabase Auth session
        ▼
FastAPI backend (backend/)            55 route modules · domain/service/data layers
        │  server-side authorization on every business endpoint
        ▼
Supabase PostgreSQL                   RLS + API-level org scoping + append-only audit_trail
        │
        ├── Storage (documents, report artefacts, private buckets)
        └── Realtime (messaging/notification delivery)
```

| Layer | Implementation facts | Evidence |
| --- | --- | --- |
| API | 55 modules covering customer, consultant, PE, ops/QC/review, admin, reporting, disclosure, billing/commercial, exports, evidence, Insight, messaging, settings, search, verifications, whitelabel, supplier/vehicle master data | `CODE-TRACED` |
| Domain | Explicit state machines: `DOCUMENT_PIPELINE` (12 states), report lifecycle (6 statuses + 5 transitions), issue, customer-factor, entity, consultant-client lifecycle | `CODE-TRACED` |
| Authorization | Nine `require_*` gates (`auth`/`admin`/`staff`/`org_member`/`org_admin`/`org_access`/`entity_member`/`role`/`permission(s)`), a staff permission catalogue, consultant capability flags, and FIN-06 manual-processing grants (default **off**) | `CODE-TRACED` |
| RLS | RLS broadly enabled; high-risk workflow ledgers (e.g. `work_item_assignments`) have **RLS enabled with no policies** so only the V3 API (asyncpg) can touch them; the messaging participant policy was repaired for recursion-safety | `CODE-TRACED` |
| Audit | append-only `audit_trail` (+ entity-conversation audit records) | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Frontend guards | `RoleRoute` supports `requireOrg`, `requireStaff`, `requireInternalStaff`, `requireEntityStaff`, `requireConsultant`; resolution failure **fails closed** with a retry (never a silent redirect); the destination is server-authoritative | `CODE-TRACED` |

---

## 5. Persona model (reverse-engineered from code and schema)

### 5.1 Personas that actually exist

| # | Persona | Identity & role source | Relationship / tenant boundary | Permissions source | UI surface | API surface (representative) | Independently verified |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | **Customer owner** | `organization_members.role='owner'` | own organisation (`organization_id` = tenant boundary) | org permissions + owner authority (`require_org_admin`) | `/home`, `/emissions`, `/documents`, `/processing(/:itemId)`, `/review(/:itemId)`, `/issues`, `/notifications`, `/reports(/:id)`, `/billing`, `/organization`, `/messaging`, `/insight`, `/evidence/line-items/:id`, `/existing-data` | `/api/v3/organizations/*`, `/documents`, `/processing/*`, `/reports*`, `/billing/me*`, `/messaging/*` | `BROWSER-VERIFIED` (DR-003/004/005) |
| P2 | **Customer admin** | `role='admin'` | as P1 | as P1 | as P1 | as P1 | `DOCUMENT-SOURCED` (ISC-13 factor approval) |
| P3 | **Customer member** | `role='member'` | as P1 | `require_org_member`; owner/admin surfaces denied | as P1 minus admin actions | denials verified on audit surfaces | `DOCUMENT-SOURCED` |
| P4 | **Customer viewer** | `role='viewer'` | as P1, **read-only** | explicit write denials (`CL-42` upload; facility create; audit) | as P1, read-only | `403` verified on writes | `CODE-TRACED` + `DOCUMENT-SOURCED` (SEC-1 fixed) |
| P5 | **Consultant firm owner** | `consultant_profiles` + firm role `owner` | consultant firm + **client organisations** via `consultant_clients` | consultant capability flags: `can_manage_clients`, `can_upload_documents`, `can_extract`, `can_map`, `can_validate`, `can_calculate`, `can_confirm_automation`, `can_submit` | `/consultant`, `/consultant/items/:clientId/:itemId` | `/api/v3/consultants/{me,me/clients,me/dashboard,me/team,me/tasks,clients/{id}/context,clients/{id}/dashboard}` | `DOCUMENT-SOURCED` (ISC-11/12) |
| P6 | **Consultant team member** | firm role `consultant`; flags may be **all false** (least privilege) | firm; acts only for granted clients | capability flags + `require_consultant` | `/consultant` (restricted) | consultant endpoints; flag-based denials | `DOCUMENT-SOURCED` |
| P7 | **Consultant client (client-org owner)** | `organization_members.role='owner'` on a client org | own client organisation | org owner + engagement | `/home` … (as P1) | customer endpoints; **cross-client denied** | `DOCUMENT-SOURCED` (ISC-12) |
| P8 | **PE manager** | `staff_profiles.entity_id` = PE, role `pe_manager` | Processing Entity; **not** an org member | entity-scoped staff permissions (`can_process`, `can_review`, …) | `/pe`, `/pe/assignments`, `/pe/messages`, `/pe/items/:entityId/:itemId` | `/api/v3/pe/*` (work, batches, item ops, pe-review, pe-qc, clarify, issues, team, work/claim/release/complete) | `DOCUMENT-SOURCED` (ISC-14 boundaries verified; workflow itself unexercised) |
| P9 | **PE staff/operator** | `entity_id` + role `pe_staff` | as P8 | entity-scoped permissions; claim denied without `can_process` | as P8 | as P8 (subset) | `DOCUMENT-SOURCED` |
| P10 | **CarbonTally internal operator** | `staff_profiles.entity_id IS NULL`, role from `staff_roles` (e.g. `operator`) | internal; may see org work by permission | staff permission catalogue | `/ops`, `/ops/items/:itemId`, `/ops/operational-health` | `/api/v3/processing/*`, `/ops/*` | `CODE-TRACED` |
| P11 | **CarbonTally reviewer** | internal staff role `reviewer` | internal | `can_review` | `/ops/review/:itemId` | `/api/v3/review/*` (review-queue, assign, complete, SLA settings) | `DOCUMENT-SOURCED` (SLA surfaces still failing — D-29) |
| P12 | **CarbonTally QC specialist** | internal staff role `qc` | internal | QC/review permissions | `/ops/qc/:itemId` | `/api/v3/qc/queue`, `/stats`, `/items/{id}/review` | `CODE-TRACED` |
| P13 | **CarbonTally staff admin** | internal staff role with `can_manage_staff`, `can_manage_billing` | internal | staff catalogue + `ensure_staff_permission` | `/ops` administrative surfaces | `/api/v3/admin/*`, `/api/v3/commercial/*` | `DOCUMENT-SOURCED` |
| P14 | **System administrator** | internal role `admin`/`system_admin` (`ADMIN_ROLE_NAMES`) | platform-wide | `require_admin`; role model per `v3m8_system_admin_role_model` | `/ops` + admin control plane | `/api/v3/admin/*` | `DOCUMENT-SOURCED` (ISC-10 inconsistency open) |
| P15 | **PE ↔ CarbonTally operations participant** | actor domains `pe` / `ops` | entity-scoped conversation | `_resolve_entity_actor` (+`can_manage_staff` for `ops`) | `/pe/messages` | `/api/v3/messaging/entity-conversations*` | `CODE-TRACED` |
| P16 | **External auditor** | **no persona exists** (no principal, no route); only a *role* that is denied/not authorized | — | — | — | — | `DOCUMENT-SOURCED` (P-02 DEFERRED / NOT AUTHORIZED) |
| P17 | **Public visitor / investor-as-visitor** | unauthenticated | public site only | none | `/`, `/platform`, `/pricing`, `/services`, `/processing-services`, `/consultants`, `/faq`, `/contact`, … | public endpoints | `DOCUMENT-SOURCED` |

**No persona exists beyond those listed.** `UNKNOWN`: a dedicated "CarbonTally carbon/accounting expert" role beyond the reviewer/QC permission set — the permission vocabulary contains no carbon-specialist role name. `CODE-TRACED`.

### 5.2 Rights matrix (`CODE-TRACED`; ✓ permitted · ✗ denied · ~ conditional)

| Persona | Read own tenant | Write own tenant | Process (extract→calc) | Approve (customer) | Review/QC | Message org plane | Message entity plane | Reports | Export | Evidence | Admin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Customer owner (P1) | ✓ | ✓ | ~ (self-service) | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| Customer admin (P2) | ✓ | ✓ | ~ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| Customer member (P3) | ✓ | ~ | ~ | ✗ (owner/admin gate) | ✗ | ✓ | ✗ | ~ | ~ | ✓ | ✗ |
| Customer viewer (P4) | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ (read) | ~ | ✓ (read) | ✗ |
| Consultant owner (P5) | ✓ (granted clients) | ✓ | ✓ (flags) | ✗ (client approves) | ~ (`consultant-review`) | ✓ (active grant) | ✗ | ~ (client reports) | ~ | ✓ | ✗ |
| Consultant member (P6) | ✓ per flags | ~ | ~ per flags | ✗ | ~ per flags | ✓ (active grant) | ✗ | ~ | ~ | ✓ | ✗ |
| Client owner (P7) | ✓ own client org | ✓ | ~ | ✓ | ✗ | ✓ (with consultant) | ✗ | ✓ | ✓ | ✓ | ✗ |
| PE manager/staff (P8/P9) | ✓ assigned work only | ✓ assigned work only | ✓ assigned work | ✗ | ~ (`pe-review`/`pe-qc`) | ✗ (**excluded**) | ✓ entity plane | ✗ | ✗ (download disabled by role — DR-005) | ~ | ✗ |
| Internal operator (P10) | ✓ per permission | ✓ per permission | ✓ | ✗ | ✗ | ✗ (unless `can_manage_staff`) | ~ (ops domain) | ~ | ~ | ✓ | ✗ |
| Reviewer (P11) | ✓ | ~ | ✗ | ✗ | ✓ | ✗ | ~ | ~ | ~ | ✓ | ✗ |
| QC (P12) | ✓ | ~ | ✗ | ✗ | ✓ | ✗ | ~ | ~ | ~ | ✓ | ✗ |
| Staff admin (P13) | ✓ | ~ | ~ | ✗ | ~ | ✓ (`can_manage_staff`) | ✓ (ops) | ~ | ✓ | ✓ | ~ |
| System admin (P14) | ✓ | ✓ | ✓ | ✗ | ~ | ✓ | ✓ | ~ | ✓ | ✓ | ✓ |
| Auditor (P16) | ✗ (no persona) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Denied-by-design boundaries (each is code-enforced, not UI-hidden):** PE staff and general CarbonTally employees are **excluded from org conversations** (`_authorize_org_actor` returns 403); a client can never name the messaging counterparty (server-resolved); PE conversations may only carry context for **work assigned to that entity** (403 otherwise); viewer writes are refused server-side; `can_manage_billing` is required for commercial surfaces; `work_item_assignments` is API-only (RLS on, no policies). `CODE-TRACED`.

---

## 6. Organisation topology (supported relationship model)

| Relationship | In schema | Backend | Frontend | Authorization enforced | Demonstrated | Investor-demo value | Synthetic data needed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Organisation → members (owner/admin/member/viewer) | ✔ `organization_members.role` CHECK | ✔ | ✔ | ✔ `require_org_member/_org_admin` | ✔ (DR-005 client scoping; ISC tests) | HIGH | yes (per-persona users) |
| Organisation → facilities → assets | ✔ (`facilities`, `assets`) | ✔ CRUD routes | ✔ `/organization` | ✔ | ✔ facilities/assets exercised on the legacy dataset; **0 in the Demo Lab** | MED–HIGH (per-site emissions) | yes |
| Organisation → suppliers | ✔ (`suppliers`) | ✔ read route | ✔ | ✔ | partially; **0 rows in Demo Lab** | MED (ISC-9 caveat: `supplier_id` never written) | yes |
| Organisation → vehicles | ✔ (`vehicles`; migration now applied in all local DBs) | ✔ read route | ✔ | ✔ | 3 rows in legacy dataset; 0 in Demo Lab | LOW | optional |
| Organisation → customer factors | ✔ (`customer_factors` + family/version index) | ✔ create/approve/deny | ✔ | ✔ (creator-approval rule) | ✔ ISC-5/13 | MED (governance story) | yes (a few) |
| **Consultant firm → clients (client organisations)** | ✔ `consultant_profiles`, `consultant_clients` (+ engagement lifecycle states) | ✔ full `v3_consultants` surface incl. accept/reject/suspend/end/reactivate | ✔ `/consultant` | ✔ active-grant requirement | ✔ ISC-11/12 | **HIGH** | yes |
| Consultant firm → team members | ✔ firm roles + capability flags | ✔ team create/deactivate/reactivate | ✔ | ✔ | partially | MED | yes |
| **Organisation ↔ Processing Entity** | ✔ `entity_id` on batches/items/monitoring tables; `processing_entities` + relationships | ✔ (PE routes; assignment ledger) | ✔ `/pe` | ✔ | ✗ **never exercised** (0 assignments in Demo Lab) | **HIGH** | **yes — required** |
| PE → multiple organisations | ✔ (entity_id is per batch/item, not per org) | ✔ | ✔ | ✔ | ✗ | HIGH | yes |
| PE ↔ CarbonTally staff (operational messaging) | ✔ `conversation_kind='entity'` + `processing_entity_id` | ✔ entity-conversation routes | ✔ `/pe/messages` | ✔ | 1 conversation in the legacy dataset | HIGH | yes |
| CarbonTally staff → organisations | ✔ grants/permissions | ✔ | ✔ `/ops` | ✔ (`can_manage_staff`) | partially (legacy reviews) | MED | yes |
| CarbonTally staff → consultants | ✔ (consultant admin surfaces exist) | ✔ | ~ | ✔ | `UNKNOWN` depth | MED | optional |
| CarbonTally staff → PEs | ✔ (`admin_entities` CRUD; PE team view) | ✔ | ✔ `/ops` | ✔ | partially | MED | yes |
| PE ↔ organisation/consultant direct messaging | **✗ not supported by design** (PE excluded from org plane) | ✗ | ✗ | enforced | n/a | — (state as a **boundary**, a selling point) | none |
| External auditor → anything | ✗ (no persona) | ✗ | ✗ | n/a | ✗ | deferred | none |

**Topology verdict:** the product supports a **rich multi-party topology** (customer ∥ consultant↔client ∥ PE ∥ internal staff) with strict isolation, and the requested PE scenario (PE-1 → Org A and Org B, PE-2 → Org C, staff supervising both) is **supported by schema, backend and UI** — but it has **never been populated or demonstrated** anywhere. `CODE-TRACED` + `DATABASE-OBSERVED` + `INFERENCE`.

---

## 7. Permission / RLS model

| Mechanism | Implementation | Evidence |
| --- | --- | --- |
| Authentication gates | `require_auth`, `require_admin`, `require_staff`, `require_org_member`, `require_org_admin`, `require_org_access(organization_id)`, `require_entity_member(entity_id)`, `require_role(...)`, `require_permission/any/all` | `CODE-TRACED` |
| Customer permissions | `DEFAULT_ORG_PERMISSIONS` = `can_view_org_data`, `can_edit_org_data`, `can_delete_org_data`, `can_manage_org_members`, `can_generate_reports`, `can_export_org_data` (fallback defaults **false**) | `CODE-TRACED` |
| Staff permissions | `DEFAULT_STAFF_PERMISSIONS` = `can_view_all`, `can_manage_staff`, `can_manage_roles`, `can_manage_billing`, `can_view_organizations`, `can_manage_organizations`, `can_extract`, `can_process`, `can_review`, `can_approve`, `can_export`, `can_delete` — resolved from the **`staff_roles.permissions` JSONB catalogue**, never from a client claim | `CODE-TRACED` |
| Admin role names | `ADMIN_ROLE_NAMES = ("admin","system_admin")` | `CODE-TRACED` |
| Consultant capabilities | `ConsultantCapabilities` flags + firm roles + client lifecycle transitions | `CODE-TRACED` |
| FIN-06 manual-processing governance | `manual_processing_grants` keyed by `scope_type`/`scope_id`, **most-specific-wins**, **fails closed** when nothing matches, `default_off = True`; admin-only management routes + `/effective/{organization_id}` diagnostic | `CODE-TRACED` |
| RLS | Enabled broadly with org-scoped predicates; several workflow ledgers (e.g. `work_item_assignments`) are **RLS-enabled with no policies** so only the API (asyncpg) can read/write them; messaging participant access uses a recursion-safe policy added in the D26/D27 lifecycle migration | `CODE-TRACED` |
| Audit | append-only `audit_trail`; entity-conversation actions audited; assignment changes audited (`_record_batch_assignment_audit`) | `CODE-TRACED` |
| Frontend guard | `RoleRoute` (fail-closed); the code states the UI is not the security boundary | `CODE-TRACED` |

**Client factor-approval rule (honoured):** a factor's creator cannot approve their own factor (403) → a **second admin** is required, and a **single-admin organisation is deadlocked** (`FAC-1`/`PO-1`). `DOCUMENT-SOURCED` (ISC-5/13).

---

## 8. Manual Processing Entity workflow (high priority)

### 8.1 How work reaches a PE — the implemented chain

```text
organisation upload  →  batch/item created (entity_id NULL = CarbonTally internal)
        │
        ├─ staff assignment  POST /api/v3/ops/batches/{batch_id}/assign
        │                    POST /api/v3/ops/items/{item_id}/work/assign    (assignee_kind=processing_entity)
        │                    POST /api/v3/ops/items/{item_id}/work/reassign  (explicit reassignment)
        │                        ▼
        │                 work_item_assignments (status=open, at most ONE open per item;
        │                     previous_assigned_to / previous_processing_entity_id retained;
        │                     close_action ∈ released|completed|reassigned|recovered|superseded)
        ├─ PE self-claim     POST /api/v3/pe/items/{item_id}/work/claim      (action='claim')
        │                    POST /api/v3/pe/items/{item_id}/work/release
        │                    POST /api/v3/pe/items/{item_id}/work/complete
        ▼
PE workspace   /pe → /pe/assignments → /pe/items/{entityId}/{itemId}
        │
        ├─ processing ops  /api/v3/pe/items/{id}/{start,extract,map,validate,calculate,status,pe-review,pe-qc,clarify}
        ├─ queues/context  /api/v3/pe/{me,work,batches/{id}/items,issues,issues/{id},team,items/{id}/workspace,items/{id}/work}
        └─ messaging       /api/v3/messaging/entity-conversations (context must be a batch/item ASSIGNED to this entity)
                                    ▼
        CarbonTally operations (internal staff, entity_id IS NULL, can_manage_staff): supervision, reassignment, escalation
```

### 8.2 Evidence per element

| Element | Finding | Evidence |
| --- | --- | --- |
| Assignment of organisations/batches/items to a PE | **Implemented** — batch-level (`/ops/batches/{id}/assign`), item-level (`/ops/items/{id}/work/assign`); `entity_id` on batches/items; PE claim/release/complete | `CODE-TRACED` |
| PE queues | **Implemented** — `/pe/work`, `/pe/batches/{id}/items`, `/pe/items/{id}/work`; open-assignment index by entity | `CODE-TRACED` |
| Document access by PE | **Entity-scoped**; document download disabled for the role ("View only — download disabled for this role", DR-005) | `CODE-TRACED` + `BROWSER-VERIFIED` |
| PDF / XLSX / CSV / image processing by PE | **Implemented through the shared extraction service** (`PDF`, `IMAGE` with OCR, `SPREADSHEET` incl. xlsx tabular parse) | `CODE-TRACED` |
| Manual extraction / mapping / validation / calculation | **Implemented** as PE item ops (`extract`, `map`, `validate`, `calculate`) + `pe-review` / `pe-qc` | `CODE-TRACED` |
| Partial / completed / blocked processing | **Implemented** — item statuses plus assignment `close_action` set; queue statuses include `manual_review`, `qc`, `customer_review`, `approved`, `rejected`, `completed`, `failed` | `CODE-TRACED` |
| Reassignment | **Implemented and audited** — explicit `reassign` action retaining `previous_*`; a legacy `reassignment_history` table also exists | `CODE-TRACED` |
| Work ownership (single owner) | **Enforced** — unique partial index: at most ONE open assignment per work item | `CODE-TRACED` |
| Multiple PEs | **Supported** — `assignee_kind='processing_entity'` + `processing_entity_id`; legacy dataset has 11 PEs and 2 assignment rows | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Staff escalation | **Implemented** — PE `clarify`; entity-scoped `issues`; entity conversations; staff reassignment/recovery; FIN-06 grants | `CODE-TRACED` |
| Comments / notes | **Implemented as issues + messages + QC notes** (`qc_notes`); no separate free-text PE comment field found | `CODE-TRACED` |
| Approval / review / customer review | **Implemented** — PE review/QC → consultant review (when a consultant is active) → CarbonTally QC → customer review/approval | `CODE-TRACED` |
| Audit trail | **Implemented** — assignment/reassignment, entity conversations, workflow transitions (113 audit rows in the Demo Lab) | `CODE-TRACED` + `DATABASE-OBSERVED` |

### 8.3 The requested scenario, assessed against evidence

> *PE-1 processes Organisation A; PE-1 partially processes Organisation B; PE-2 processes Organisation C; PE-2 later processes another item for Organisation A; CarbonTally staff supervises/communicates with both PEs.*

| Claim in the scenario | Supported? | Why |
| --- | --- | --- |
| PE-1 works on **two organisations** | **Yes (schema + API)** | assignment is per item/batch with `processing_entity_id`; nothing constrains an entity to one organisation. **Not demonstrated** (0 assignments in the Demo Lab) |
| PE-1 leaves Org-B work **partial** | **Yes** | open assignment + item statuses; `close_action` distinguishes partial release (`released`) from completion (`completed`) |
| PE-2 handles Org C | **Yes** | same mechanism, different entity |
| PE-2 later takes **another Org A item** | **Yes** | item-level assignment is organisation-agnostic; the one-open-assignment rule prevents double ownership of the *same item*, not of the same organisation |
| Staff supervises / communicates with both PEs | **Yes** | `/ops` assignment + `/api/v3/messaging/entity-conversations` (ops domain) + issue/clarify surfaces |
| PE talks **directly** to the customer | **No — by design** | PE is excluded from org conversations; PE↔customer is routed through CarbonTally ops |

**Verdict:** the requested PE operating model is **implemented but unexercised**. Demonstrating it needs **data population** (batches assigned to entities, assignment rows, an entity conversation) and **no new code** — unless the PO wants an automatic work-routing rule (none exists; assignment is an explicit staff action or a PE claim). `CODE-TRACED` + `DATABASE-OBSERVED` + `INFERENCE`.

---

## 9. Processing lifecycle (the actual state model)

### 9.1 Overlapping vocabularies (all real; enforced in different layers)

| Layer | Vocabulary | Where defined | Evidence |
| --- | --- | --- | --- |
| **Queue status** | `pending`, `processing`, `ai_extracted`, `manual_review`, `manual_extraction`, `qc`, `customer_review`, `approved`, `rejected`, `completed`, `failed` | `document_processing_queue_status_check` | `CODE-TRACED` |
| **Queue stage** | stage column driving durable/resumable processing | `20260829000000_v3m9_durable_automatic_processing` | `CODE-TRACED` |
| **Pipeline state machine** | `pending → uploaded → classifying → extracting → ai_matching → matched → customer_review → reviewed → calculating → completed`, with `manual_review` and `failed` branches (`("*","failed")` catch-all) | `domain/workflow.py::DOCUMENT_PIPELINE` | `CODE-TRACED` |
| **Work-item status** | free-form `VARCHAR` driven by code; observed: `pending`, `extracting`, `extracted`, `mapping`, `mapped`, `validated`, `calculated`, `consultant_reviewed`, `ct_qc_approved`, `qc_approved`, `customer_review`, `approved`, `rejected` | `manual_extraction_items.status` + services | `CODE-TRACED` + `DATABASE-OBSERVED` |
| **Assignment state** | `open`/`closed`; actions `assign|reassign|claim|recover`; close reasons `released|completed|reassigned|recovered|superseded` | `work_item_assignments` | `CODE-TRACED` |
| **Report lifecycle** | `DRAFT → REVIEWED → APPROVED → FINAL` (+`CHANGES_REQUESTED`, `REJECTED`, `SUPERSEDED`) | `domain/report_lifecycle.py` | `CODE-TRACED` |

### 9.2 Who does what, and where

| Transition (typical) | Actor(s) who can trigger | Endpoint | Persisted evidence | UI | Demonstrated |
| --- | --- | --- | --- | --- | --- |
| upload → queued | customer owner/admin/member; consultant (client docs) | `POST /api/v3/uploads`; `POST /api/v3/consultants/clients/{id}/documents` | `organization_files`, batch, item, storage object, job | `/documents` | ✔ (T3; DR-004/005) |
| queued → extract | automatic durable worker | internal (`automatic_processing`) | extraction result + job stage | `/processing` | ✔ (one complete; 13 honest blocks) |
| extract → map | customer / consultant / PE / ops | `POST /api/v3/processing/items/{id}/map`; `/api/v3/pe/items/{id}/map` | `mapped_data` + factor | `/processing/:itemId` | ~ (blocked for most corpus docs — ISC-9) |
| map → validate | as above | `…/validate` | validation findings (issues) | workspace + `/issues` | ~ |
| validate → calculate | as above | `…/calculate` | immutable `calculation_snapshots` + `emissions_logs` | workspace | ✔ (1 record) |
| consultant review | consultant with `can_submit` | `…/consultant-review`, `…/consultant-submit` | `consultant_reviewed` → CarbonTally QC intake | `/consultant/items/:clientId/:itemId` | ✗ (no engagement data exercised) |
| PE review / QC | PE manager/staff | `/api/v3/pe/items/{id}/pe-review`, `…/pe-qc` | item status + QC notes | `/pe/items/...` | ✗ |
| CarbonTally review | reviewer | `/api/v3/review/review-queue/{id}/{assign,complete}` | review assignment history | `/ops/review/:itemId` | ✗ (SLA surfaces failing — D-29) |
| CarbonTally QC | QC specialist | `/api/v3/qc/items/{id}/review` | QC state | `/ops/qc/:itemId` | ✗ |
| customer review → approved/rejected | customer owner/admin | `/api/v3/processing/items/{id}/customer-review` | approval + resolved blocking issues (ISC-2 fixed) | `/review` | ✗ (never executed — ISC-15) |
| any → failed / manual_review | system or staff | pipeline catch-all; `…/status` | job stage/status + `attempt_count` | `/processing` | ✔ (13 blocked items) |

**Honest reading:** the *automatic* half of the lifecycle is demonstrated (upload → extract → honest block, plus one complete calculation); the *human* half (consultant review, PE review/QC, internal review/QC, customer approval) is **implemented, code-traced and never exercised in any current environment**. `CODE-TRACED` + `DATABASE-OBSERVED`.

---

## 10. Consultant / client workflow

| Element | Finding | Evidence |
| --- | --- | --- |
| Firm identity & branding | `consultant_profiles` + branding/whitelabel routes (`/me/branding`, `/me/branding/context`) | `CODE-TRACED` |
| Client portfolio | `POST /me/clients`, `POST /me/customers`, `/me/clients`, `/clients/{id}` CRUD, `/me/dashboard` | `CODE-TRACED` |
| Client lifecycle | `onboarding → active → suspended → ended` with a transitions map; **client-side** `accept`/`reject` engagement routes | `CODE-TRACED` |
| Consultant processing rights | capability flags gate extract/map/validate/calculate/confirm-automation/submit; least-privilege members may hold none | `CODE-TRACED` |
| Consultant review step | `consultant-review` (pass → `consultant_reviewed`; fail → back to `mapping`), then `consultant-submit` into the CarbonTally QC intake (**non-charging**) | `CODE-TRACED` |
| Team & tasks | `/me/team` (create/deactivate/reactivate), `/me/tasks` (+ status update) | `CODE-TRACED` |
| Client workspace access | `/clients/{id}/context`, `/clients/{id}/dashboard`; UI `/consultant`, `/consultant/items/:clientId/:itemId` | `CODE-TRACED` |
| Isolation | cross-consultant 403; same-consultant cross-client 403 — independently confirmed at investor scale | `DOCUMENT-SOURCED` (ISC-11/12) |
| Data reality | Demo Lab: 1 profile, 2 client engagements, 0 client documents. Legacy dataset: 55 profiles, **917** engagements | `DATABASE-OBSERVED` |

---

## 11. CarbonTally staff workflow

| Element | Finding | Evidence |
| --- | --- | --- |
| Operations surfaces | `/ops`, `/ops/items/:itemId`, `/ops/operational-health`; ops processing endpoints (dashboard, status, queues, batch start/complete/cancel, item ops) | `CODE-TRACED` |
| Review queue | `/api/v3/review/review-queue` (+ item, `assign`, `complete`) and SLA settings routes | `CODE-TRACED` |
| QC queue | `/api/v3/qc/queue`, `/stats`, `/items/{id}/review` | `CODE-TRACED` |
| Entity administration | `/api/v3/admin/entities` CRUD | `CODE-TRACED` |
| Manual-processing governance | `/api/v3/admin/manual-processing/grants` (+`/effective/{organization_id}`); **default off, fails closed** | `CODE-TRACED` |
| Assignment / supervision | `POST /ops/batches/{id}/assign`, `POST /ops/items/{id}/work/assign|reassign`, `POST /review/{review_id}/assign` | `CODE-TRACED` |
| Commercial (staff) | `/api/v3/commercial/*` gated on `can_manage_billing` | `CODE-TRACED` |
| Audit & exports | `/api/v3/admin/audit*`, `/api/v3/exports/*` incl. `audit-package.json` | `CODE-TRACED` |
| Known defect surfaces | `F-T1-001` (`reporting/audit-activity` 500) and the three failing SLA surface tests (D-29) | `DOCUMENT-SOURCED` |
| Data reality | Demo Lab: 3 staff profiles / 3 roles, 0 review or QC activity; legacy dataset: 21 profiles, 6 roles, 30 approved items | `DATABASE-OBSERVED` |

---

## 12. Messaging model

### 12.1 Two planes, three gates

| Plane | Participants | Conversation identity | Gate | Evidence |
| --- | --- | --- | --- | --- |
| **Org / customer plane** | org members; consultants with an **active grant**; internal CarbonTally support (`entity_id IS NULL` + `can_manage_staff`) | `conversation_kind='org'`, `organization_id` | `_authorize_org_actor` — everyone else **403** (incl. PE staff and general employees) | `CODE-TRACED` |
| **Entity / operational plane** | PE members (`entity_id` set, entity `status='active'`) and authorised CarbonTally Operations (`can_manage_staff`) | `conversation_kind='entity'`, `processing_entity_id` | `_resolve_entity_actor` + `_entity_conv_read_access` (a PE may read only its **own** entity's conversations) | `CODE-TRACED` |

**Counterparty resolution (org plane):** `_resolve_support_participant` picks the CarbonTally support participant **server-side** (internal staff with `can_manage_staff`, deterministic lowest user id). A client **cannot name** the counterparty; if no authorised participant exists the API returns **409**, never a silent unauthenticated channel. `CODE-TRACED`.

**Entity-conversation context:** `context = {type: 'batch'|'item', id}` is accepted **only when that work is assigned to that entity** — otherwise **403**; malformed context → **422**. `CODE-TRACED`.

### 12.2 Which boundaries are and are not supported

| Relationship | Supported | Note |
| --- | --- | --- |
| Customer ↔ CarbonTally support | ✔ | org plane (N1) |
| Customer-internal (owner ↔ admin ↔ member) | ✔ | org plane |
| Consultant ↔ its client | ✔ | org plane via active grant |
| Consultant ↔ CarbonTally support | ✔ | org plane (support side) |
| **PE ↔ CarbonTally operations** | ✔ | **entity plane** (operational context only) |
| **PE ↔ customer / consultant** | ✗ **by design** | PE is not a participant in org conversations |
| PE ↔ PE (cross-entity) | ✗ | entity scoping prevents it |
| Auditor ↔ anything | ✗ | no persona |

### 12.3 Defects and verification status

* **MSG-1** (`POST /conversations` → 500 from `ON CONFLICT` with no matching constraint, leaving orphan conversations with zero participants): **fixed in code** (insert no longer uses `ON CONFLICT`); the **legacy side effect persists** — the historical dataset still holds **2 orphan** conversations of 36. `CODE-TRACED` + `DATABASE-OBSERVED`.
* **RLS:** `conversation_participants` originally had **zero policies (deny-all)**; a recursion-safe participant policy was added. `CODE-TRACED`.
* **Realtime delivery:** blocked in the Demo Lab (no `/realtime/v1` route on the lab gateway); processing views poll over HTTP. `DOCUMENT-SOURCED` (DR-005).
* **Independent verification:** the messaging **boundaries** were probed at investor scale (PE→customer conversation 403; PE→customer documents 403; cross-consultant 403), but there is **no dedicated verification record for the messaging planes**, and the entity plane has **one** historical conversation. `DOCUMENT-SOURCED` + `DATABASE-OBSERVED`.

**Data reality:** Demo Lab — **0** conversations/messages/participants. Configured dev DB — **10** org conversations, 0 messages. Legacy dataset — 36 conversations (`org`=35, `entity`=1), 54 messages, 65 participants. `DATABASE-OBSERVED`.

---

## 13. Reporting model

| Element | Finding | Evidence |
| --- | --- | --- |
| Report types | `/api/v3/reports/types`; generation supports **`annual`** (a `ghg_inventory` refresh returns 422 — DR-006) | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Lifecycle | `DRAFT → REVIEWED → APPROVED → FINAL` + `CHANGES_REQUESTED`, `REJECTED`, `SUPERSEDED`; `APPROVED`/`FINAL` immutable; a post-final change creates a **new DRAFT version** | `CODE-TRACED` |
| Version operations | `POST /{report_id}/versions` (new version), `…/submit`, `…/request-changes`, `…/reject`, `…/approve`, `…/finalize` | `CODE-TRACED` |
| Content / artefacts | `GET /{report_id}/content`, `/versions`, `/download`, `/pdf`; `report_version_artifacts`; storage-backed artefacts | `CODE-TRACED` |
| Disclosure layer | B1–B4 disclosure model + `disclosure_report_*` tables + intensity ratios (B3); `disclosure_value_evidence` is the structured evidence projection (0 rows everywhere) | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Audit package | `/api/v3/exports/audit-package.json` (content contract undefined — D-16) | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Report-to-data consistency | DR-006: after regeneration the annual report's UI, API and artefact all reported the real `2469.169780 kg CO₂e` with factor provenance and no `insufficient_data` | `DOCUMENT-SOURCED` (browser-verified) |
| Freshness problem | The pre-existing annual report was **stale** (generated before the R-A row) and a **duplicate** annual report plus an unrefreshable `ghg_inventory` remain visible (DR-007 issues 8–9, PO decision) | `DOCUMENT-SOURCED` |
| Data reality | **Every report version in every database is `DRAFT`** (17 in the legacy dataset, 2 in the Demo Lab); `report_version_artifacts` = 0 in the Demo Lab and the table is **absent** in the legacy dataset | `DATABASE-OBSERVED` |

**Minimum complete reporting story by audience:** (i) **one organisation** — a generated annual report whose numbers match the dashboard and export, with an artefact download and an evidence/trail section; (ii) **one consultant with a client** — the same report produced for the client, with consultant branding and the client's own approval state; (iii) **PE/operational context** — reporting is **not** a PE responsibility; the PE story is operational (assignment → processing → completion/communication), and any report belongs to the organisation. `INFERENCE`.

---

## 14. Evidence / provenance model

| Chain link | How it is populated | Demo Lab | Legacy dataset | Live |
| --- | --- | --- | --- | --- |
| source document | upload writes `organization_files` + storage object | 14 files / 15 objects | 263 files / 685 objects | UNKNOWN |
| extracted data | pipeline writes extraction result on the item | 11 `extracted` | 29 extracted + 2 extracting | UNKNOWN |
| **line items** | `evidence_line_items` materialisation / `extracted_data.line_items[]` | **0 rows** | table **absent** | UNKNOWN |
| mapping / factor | item `mapped_data` + snapshot `factor_id` | 1 snapshot factor populated | 76/100 snapshots have a factor | UNKNOWN |
| validation | findings → `issues` | 0 issues | 62 issues | UNKNOWN |
| calculation | immutable `calculation_snapshots` | **1** | **100** | UNKNOWN |
| emissions | `emissions_logs` row (snapshot-linked) | **1** | **100** | UNKNOWN |
| **evidence** | `evidence_line_items` (+ `disclosure_value_evidence`) | **0 / 0** | table absent | UNKNOWN |
| provenance | `source_item_id` (snapshot→item) + `source_line_item_id` (line-level) | item link ✔, line link NULL | 99/100 item links; line column absent | UNKNOWN |
| report | `report_versions` + artefacts | 2 versions, 0 artefacts | 17 versions, artefacts table absent | UNKNOWN |
| Insight | `carbontally_insight_*` | tables **absent** | tables absent | UNKNOWN |

**What the Source Evidence Viewer requires:** an authorised `evidence_line_items` row id (`GET /api/v3/evidence/line-items/{line_item_id}`), which the viewer re-authorises per read (DM-6). With **zero rows in every environment**, the viewer is **not demonstrable today** even though its code is independently verified (`PASS WITH NON-BLOCKING OBSERVATIONS`, 2026-09-22). The only population path is the **offline, dry-run-by-default CLI** `tools/backfill_evidence_line_items.py` ("execution against any environment is separately authorised"), and online processing deliberately **only looks up** materialised lines. `CODE-TRACED` + `DATABASE-OBSERVED` + `DOCUMENT-SOURCED`.

---

## 15. Insight model

| Element | Finding | Evidence |
| --- | --- | --- |
| Registered tools (10) | 4 ratified (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`) + INS-01 (`insight_discovery`, `insight_aggregation`, `insight_aggregate_provenance`) + P2 (`insight_temporal_comparison`) + P3 (`insight_data_quality`, `insight_calculation_reproducibility`) | `CODE-TRACED` (pinned by test `== 10`) |
| Deterministic planner | `plan_question` routes question classes to: temporal comparison, data quality, reproducibility, **aggregate provenance**, aggregation, discovery | `CODE-TRACED` |
| Answer/status vocabulary | 6 `ToolStatus` values; 15 I4 answer states incl. `no_data`, `zero`, `multiple_matches`, `rate_limited`, `provider_unavailable`; `reason` is a free-form contract string | `CODE-TRACED` |
| API | `/api/v3/insight/tools`, `/invoke`, `/intent`, `/conversations*`, `/interactions*` | `CODE-TRACED` |
| UI | `/insight` (customer plane, `RoleRoute requireOrg`); components `InsightPage`, `InsightInteraction`, `InsightAnswerState`, `InsightReferences`, **`InsightComparison` (P2 only)**; `no_data` is explicitly never rendered as `zero` | `CODE-TRACED` |
| Provenance integration | aggregates name `insight_aggregate_provenance`; references are locators, never grants; the shared Source Evidence Viewer is the single evidence destination | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| Rate limiting | PostgreSQL buckets + concurrency leases (closed under INS-01) | `DOCUMENT-SOURCED` |
| Tenant isolation | I2 `authorize_insight_scope` + per-object organisation re-check | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| **Data dependency** | `carbontally_insight_interactions` / `_tool_calls` / `conversations` / `messages` — **absent in every local database** | `DATABASE-OBSERVED` |
| Supported today (if provisioned) | identified calculation, discovery, aggregation, aggregate provenance, temporal comparison (two explicit periods), data quality, reproducibility | `DOCUMENT-SOURCED` |
| **Unsupported / must answer honestly** | Scope 3 categories, market-based Scope 2, Scope 1 decomposition, variance/attribution, supplier analytics (`supplier_id` never written), knowledge/RAG, decision/reduction, supplier/factor-history intelligence | `DOCUMENT-SOURCED` |
| UI limitation | only `insight_temporal_comparison` has a dedicated structured renderer; **P3 results render only as a tool-call row + narration** | `CODE-TRACED` |
| Verification status | INS-01 closed+verified; **P2 PO-closed**; **P3 independently verified, not PO-closed** (P3-IV-01 remediated and re-verified) | `DOCUMENT-SOURCED` |
| Demonstrability today | **none** — no Insight schema in any reachable database | `DATABASE-OBSERVED` |

---

## 16. Document-processing capability

### 16.1 What CarbonTally actually ingests (`CODE-TRACED`)

| Format | Support | Mechanism |
| --- | --- | --- |
| **PDF (text-native)** | ✔ | direct text extraction |
| **PDF (scanned) / images** | ✔ (environment-dependent) | Tesseract OCR, with a **RapidOCR/ONNX fallback** over rendered pages; images classified as `IMAGE` (jpg/jpeg/png/gif/webp/bmp) |
| **CSV** | ✔ | tabular parse (`SPREADSHEET` class); currency amounts without a unit column become spend-based lines |
| **XLSX/XLS** | ✔ | workbook/sheet parse, explicitly **"parsed tabularly, not sent to an LLM"** |
| Other | `OTHER` class → no extraction path | — |

Upload MIME mapping covers `pdf, jpg, jpeg, png, gif, webp, bmp, csv, xlsx`. Processing is a **durable, resumable pipeline** with stages, attempts and a manual-review gate.

### 16.2 What the external generator can produce (`DOCUMENT-SOURCED`, local checkout at pinned commit `8ade2bf…`)

* **Document types (8)**: Electricity, Gas, Fuel, Water, Waste, Logistics, Travel, General.
* **Difficulty mix**: Clean 20% · Realistic 60% · Difficult 15% · Edge 8%.
* **Realistic identifiers**: 21-digit MPAN (electricity), 6–10 digit MPRN (gas), UK VRMs (fuel/logistics), multi-currency (mixed mode) with spend-based fallbacks.
* **Dual pool**: direct customers and consultant-client organisations (hierarchical output).
* **Visual variation**: 8 table layouts, 12 colour schemes, 5 paper colours, scan degradation, watermarks, signatures, barcodes.
* **Deterministic + addressable**: fixed repo/commit/seed/globs; every document carries a **ground-truth JSON sidecar** (an oracle only — never a CarbonTally source).
* **Corpus inventory in the checkout**: **20,176 PDFs**, 20,533 truth JSONs, **33 CSVs**, **17 PNGs** (scan samples); last documented run: 27 organisations · 4 consultants · 1,688 PDFs · 12 months. **No XLSX** is generated.

### 16.3 Where the corpus meets the product (the honest coverage map)

| Demo scenario class | Generator can supply | CarbonTally can process | Evidence |
| --- | --- | --- | --- |
| **Happy-path PDF** | ✔ (gas, water, electricity, diesel, waste, logistics, travel) | **Only 2/11 curated scenarios resolve a factor**: **natural gas (Net CV)** and **water** | `t3_manifest.json` (`EXPECTED_MATCHED`) |
| **Happy-path spreadsheet (CSV/XLSX)** | ✔ CSV (33 in corpus); XLSX must be produced externally | ✔ pipeline supports both; **no curated spreadsheet scenario exists** | `CODE-TRACED` + `DOCUMENT-SOURCED` |
| **Happy-path image** | ✔ PNG scans | ✔ technically (OCR), **environment-dependent**; no curated image scenario | `CODE-TRACED` |
| **Manual-processing input** | ✔ (difficult/edge variants, scans) | ✔ — this is exactly what the 13 blocked Demo-Lab documents are | `DATABASE-OBSERVED` |
| **Partial / completed / blocked extraction** | ✔ | ✔ statuses + assignment close reasons | `CODE-TRACED` |
| **Mapping: successful match** | ✔ (gas, water) | ✔ 2 scenarios | `DOCUMENT-SOURCED` |
| **Mapping: ambiguous** | ✔ (electricity, diesel, waste) | ✔ `EXPECTED_AMBIGUOUS` (confidence 0.0) | `DOCUMENT-SOURCED` |
| **Mapping: no match** | ✔ (generic waste wording) | ✔ `EXPECTED_NO_MATCH` | `DOCUMENT-SOURCED` |
| **Mapping: spend-based** | ✔ (spend fallbacks) | ✗ **no £/GBP or spend activity factors exist in either database** (ISC-9) | `DATABASE-OBSERVED` |
| **Validation: clean / blocking / corrected** | ✔ | ✔ (engine + issue lifecycle fixed) | `CODE-TRACED` |
| **Calculation: Scope 1** | ✔ (gas) | ✔ (one live record) | `DATABASE-OBSERVED` |
| **Calculation: Scope 2** | ✔ (electricity) | ~ location-based only; **market-based does not exist** | `DOCUMENT-SOURCED` |
| **Multiple periods / records** | ✔ (12 months of history) | ✔ mechanically — but the Demo Lab holds **one** record in **one** period | `DATABASE-OBSERVED` |
| **Review: customer review / approve / reject** | n/a | ✔ implemented, **never executed** (ISC-15) | `DOCUMENT-SOURCED` |
| **Evidence: source-level** | ✔ | ~ lineage panels only | `DATABASE-OBSERVED` |
| **Evidence: line-level / Viewer** | ✔ (line-item truth sidecars) | ✗ `evidence_line_items` empty everywhere | `DATABASE-OBSERVED` |

**Rule applied throughout:** a document type is *not* claimed as supported merely because the generator can create it; each row above cites either a curated expectation or an actual database/service fact. `CODE-TRACED` + `DATABASE-OBSERVED` + `DOCUMENT-SOURCED`.

---

## 17. Local database findings (read-only, 2026-09-24)

| Object | `carbontally_demo_local` (136 tables) | `ct_local_93d5cdd` (135, configured) | `postgres` (116, legacy) | `carbontally_qa_phase8` (133) |
| --- | --- | --- | --- | --- |
| organisations | 4 | 25 | **975** | — |
| members / auth users | 8 / 13 | 16 / — | **1,125 / 1,205** | — |
| documents (`organization_files`) | 14 | **0** | 263 | 0 |
| processing queue | 14 (13 blocked, 1 review) | 0 | 40 | 0 |
| extraction items / batches | 14 / 4 | 1 / 1 | **264 / 57** | 0 |
| **work_item_assignments** | **0** | 0 | **2** | 0 |
| `processing_assignments` / `reassignment_history` | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| **`manual_processing_grants`** | **0** | 0 | table **absent** | 0 |
| issues | **0** | 3 | 62 | 0 |
| conversations (by kind) | **0** | 10 (org) | 36 (**org 35, entity 1**) | 0 |
| messages / participants | 0 / 0 | 0 / 0 | 54 / 65 | 0 / 0 |
| calculation snapshots / emissions | **1 / 1** | 0 / 0 | **100 / 100** | 0 / 0 |
| **evidence_line_items** | **0** | 0 | table **absent** | 0 |
| report versions (status) | 2 (all DRAFT) | 0 | **17 (all DRAFT)** | 0 |
| report artefacts | 0 | 0 | table **absent** | 0 |
| emission factors | **7,049** | **0** | 7,049 | 0 |
| customer factors | 0 | 5 | 245 | 0 |
| facilities / assets / suppliers / vehicles | **0 / 0 / 0 / 0** | 0 / 0 / 0 / 0 | 157 / 310 / 156 / 3 | 0 |
| processing entities | 1 | 7 | **11** | 0 |
| staff profiles / roles | 3 / 3 | 5 / 3 | 21 / 6 | — |
| consultant profiles / client engagements | 1 / 2 | 3 / 3 | **55 / 917** | 0 |
| audit rows | 113 | 0 | 563 | 0 |
| `emissions_logs.supplier_id` populated | 0 | 0 | **0** | 0 |
| Insight tables | **absent** | absent | absent | absent |

**Findings:**

1. **The Demo Lab is the only current-schema environment and it is thin**: zero assignments, zero grants, zero messaging, zero issues, zero master data, zero evidence lines, and one calculation. `DATABASE-OBSERVED`
2. **The configured dev database (`ct_local_93d5cdd`) is not a demo environment at all**: 25 organisations, no documents, **no factors**, no snapshots, and a **2-table storage substrate** — it cannot process a document. `DATABASE-OBSERVED`
3. **The legacy `postgres` dataset is the only one with breadth** (975 orgs, 917 client engagements, 264 items, 100 calculations, 30 approvals, 62 issues, 54 messages) — but it is a **pre-evidence, pre-disclosure, pre-`source_line_item_id` schema** with **no `manual_processing_grants`**, and it is **not regenerable** (its seeder is absent from the checkout). `DATABASE-OBSERVED`
4. **PE operational data exists in exactly one place**: 2 assignment rows and 1 entity conversation, both in the legacy dataset — i.e. the PE plane has been *touched once, historically*, and never in the Demo Lab. `DATABASE-OBSERVED`
5. `supplier_id` is **never populated** in any database → supplier analytics remain structurally `no_data` (as documented). `DATABASE-OBSERVED`

---

## 18. Live database findings

```text
LIVE INSPECTION BLOCKED — NO SAFE READ-ONLY ACCESS PATH
```

**Determination (credential *types* only; no value was read, printed or transmitted):**

| Configured item in `/home/shomonrobie/carbon_tally/.env.production` | Type found | Read-only safe? |
| --- | --- | --- |
| `SUPABASE_PostgreSQL_URI` | direct Postgres connection string to a **hosted Supabase pooler**, **password present**, **user class = owner/superuser** | **NO — mutation-capable (DDL/DML)** |
| `SUPABASE_SERVICE_KEY` | Supabase **service-role** key (bypasses RLS) | **NO — mutation-capable** |
| `REACT_APP_SUPABASE_ANON_KEY`, `VITE_SUPABASE_ANON_KEY` | public anon keys (RLS-limited) | Not a *schema-inspection* credential; using an anon key against production risks exposing customer data given this repository's own anon-grant containment history (`20260920000000_p8_rls_anon_grant_containment.sql`, `20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql`) |
| `SUPABASE_URL`, `VITE_SUPABASE_URL` | hosted Supabase project endpoints | access requires one of the credentials above |
| `RESEND_API_KEY` | transactional-email key | **NO — send-capable** |
| `REACT_APP_API_URL` | loopback/`localhost` | n/a |

**Conclusion:** the only database-capable credentials in the production configuration are **mutation-capable**; there is **no read-only credential**. Per the task's rule ("If only a mutation-capable service-role credential exists, DO NOT use it for inspection"), production was **not contacted** — no connection, no query, no probe, no hostname request. `CODE-TRACED`.

**Corroborating prior record:** `docs/verification/CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md` reached the same position for the database, Render and Vercel: **`BLOCKED — PRODUCTION STATE UNKNOWN`**. `DOCUMENT-SOURCED`.

**Therefore, for every production dimension in this study: `UNKNOWN`** — schema, migration state, persona data, PE/messaging/reporting/evidence/Insight presence and drift are all unknown and are **not inferred**. Unblocking requires an authorised **read-only** inspection path (e.g. a dedicated read-only Postgres role, or an approved exported migration ledger + anonymised aggregate counts). `INFERENCE`.

---

## 19. Historical investor dataset reconciliation

| Question | Verdict | Evidence |
| --- | --- | --- |
| Where does it live? | The local stack database named `postgres` (38 MB): 975 orgs, 1,205 auth users, 1,125 members, 917 client engagements, 264 items, 100 calculations/emissions, 62 issues, 36 conversations, 54 messages, 157 facilities, 310 assets, 156 suppliers, 3 vehicles, 245 customer factors, 11 PEs, 21 staff profiles, 17 report versions | `DATABASE-OBSERVED` |
| Which schema version? | **Pre-B2/B3**: 116 tables; **no `evidence_line_items`**, **no `source_line_item_id`**, **no `disclosure_*`**, **no `report_version_artifacts`**, no `manual_processing_grants` | `DATABASE-OBSERVED` |
| Which capabilities does it still demonstrate? | Breadth of personas/topology (multiple direct orgs, consultant portfolios, PE staff), **approved** work items (30), issue lifecycle (62), messaging both planes (35 org + **1 entity**), reporting records (17, all DRAFT), master data | `DATABASE-OBSERVED` |
| Which parts are obsolete? | The evidence/disclosure/lineage layer (impossible there), `report_version_artifacts`, the grants plane, and any pre-fix data defect (e.g. the 1 NULL `source_item_id`) | `DATABASE-OBSERVED` |
| Is it reproducible? | **No** — `tools/seed_investor_demo/` and `DEMO_IDENTITIES.md` **do not exist** in this checkout; the dataset has also **drifted** from its own report (263 docs vs 219; 917 vs 916 clients; 1,205 vs 1,323 users) | `GIT-VERIFIED` + `DOCUMENT-SOURCED` + `DATABASE-OBSERVED` |
| Does its seeding mechanism still exist? | **No** (code absent). Its *data* survives; its *mechanism* does not | `GIT-VERIFIED` |
| Should it remain? | **Yes — as a read-only historical/UAT reference**, never as the demo environment and never mutated. Treat it as regression context and persona-research material | `INFERENCE` |
| Conceptually migratable? | Persona/topology **shapes** are reproducible on the current schema by the Demo Lab tooling; the *rows* themselves are not migratable (schema gap + no seeder + drift) | `INFERENCE` |
| Which of its persona scenarios should be recreated in the Demo Lab? | (a) direct org with 4 roles; (b) consultant firm with 2–3 clients incl. a client owner; (c) **PE assignment work** (the legacy dataset's 2 assignments show the path); (d) org+entity messaging; (e) an issue lifecycle; (f) an approved report | `INFERENCE` |

---

## 20. Demo Lab reconciliation

| Aspect | Finding | Evidence |
| --- | --- | --- |
| Tooling | Complete and current: `lab.py`, `provision.py`, `stack.py`, `storage.py`, `seed_factors.py`, `t3_scenarios.py`, `verify.py`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `manifest.json` (13 actors), `t3_manifest.json` (11 scenarios) | `CODE-TRACED` |
| Schema | **Current release minus the six Insight migrations** (136 tables; `work_item_assignments`, `manual_processing_grants`, evidence/disclosure tables all **present but empty**) | `DATABASE-OBSERVED` |
| Data | 4 orgs, 13 identities, 14 documents (13 blocked, 1 review), **1** calculation, 1 emissions log, 0 evidence, 2 DRAFT report versions, 7,049 factors, 113 audit rows, **0** assignments/grants/issues/conversations/master data | `DATABASE-OBSERVED` |
| Can it demonstrate the customer journey? | Yes for the core chain (auth → upload → extract → honest block; one full calculation → report → export) | `DOCUMENT-SOURCED` (DR-003…DR-006) |
| Can it demonstrate the PE journey? | **No** — no entity-assigned work, no grants, no entity conversation | `DATABASE-OBSERVED` |
| Can it demonstrate the consultant journey? | Partially — 2 client engagements exist, but no client documents and no consultant processing | `DATABASE-OBSERVED` |
| Can it demonstrate messaging? | **No** — 0 conversations; and the lab gateway has no `/realtime/v1` | `DATABASE-OBSERVED` + `DOCUMENT-SOURCED` |
| Can it demonstrate reporting fully? | Partially — reports generate (verified in DR-006) but **no version has advanced beyond DRAFT** and the current report set includes a stale/duplicate artefact | `DATABASE-OBSERVED` + `DOCUMENT-SOURCED` |
| Can it demonstrate evidence? | **No** — 0 evidence line items | `DATABASE-OBSERVED` |
| Can it demonstrate Insight? | **No** — Insight schema absent | `DATABASE-OBSERVED` |
| Reset/repeatability | Tooling exists (`reset_demo_lab.sh`, idempotent seeds) but **no verified reset→reseed rehearsal** exists for the current release, and `/tmp/extgen` (the pinned generator checkout needed for `sync-corpus`) is **absent** — although the generator checkout is now available at `/home/shomonrobie/carbon_tally_synthetic_documents` (**pinned commit match**) and can serve as `--source` | `CODE-TRACED` + `DATABASE-OBSERVED` |
| Role in the canonical environment | **The Demo Lab is the right shell** — it needs provisioning to the current schema + population, not replacement | `INFERENCE` |

---

## 21. Requirements — A. Investor demonstration

What must be **shown** so an investor understands the product. "Mode" distinguishes a live screen from a diagram or a spoken statement — the distinction matters for truthfulness.

| # | Requirement | Why it matters to an investor | Mode | Current state |
| --- | --- | --- | --- | --- |
| A1 | One **real document** producing a **deterministic, traceable** emissions result, with the arithmetic visible (quantity × factor) | proves the engine is real, not a calculator mock | live | ✔ (one record) |
| A2 | **Evidence traceability** from the result back to the source document/page | the core differentiator vs spreadsheets | live | ✗ (no evidence rows) |
| A3 | **Multi-tenant security**: ALLOW own data, DENY another tenant — shown, not asserted | investors and their technical advisers ask this first | live | ✔ code + probes; needs scripted presentation |
| A4 | **Persona breadth**: customer roles, consultant + client, PE, internal ops/admin each landing in a distinct workspace | proves it is a platform, not a single-user tool | live | ~ (customer/consultant/ops/PE routes exist; consultant/PE journeys unpopulated) |
| A5 | **The PE operating model**: work assigned → processed → completed/partial → operational messaging | the "outsourced processing" business model | live | ✗ (no data) |
| A6 | **Reporting** with a downloadable artefact whose numbers match the dashboard/export | customer-facing output | live | ~ (generation verified; artefact/lifecycle states unexercised) |
| A7 | **Insight**: a bounded question → deterministic answer → provenance → evidence | the AI story, told honestly | live | ✗ (schema absent) |
| A8 | **Honest failure**: an ambiguous/unmappable document explaining exactly why, with a next step | demonstrates engineering integrity and the human-in-the-loop design | live | ✔ (13 blocked items with machine reasons) |
| A9 | **Auditability**: append-only audit trail; who did what, when | regulated-buyer credibility | live (spot check) + diagram | ✔ data exists (113 rows) |
| A10 | **Architecture**: durable job pipeline, resumable stages, deterministic calculation, RLS boundaries, evidence model | technical due diligence | diagram + code walkthrough | ✔ explainable from code |
| A11 | **Scale/coverage honesty**: which scopes/categories are supported today and which are roadmap | prevents over-claiming; builds trust | spoken + on-screen coverage table | requires the limitation script |
| A12 | **Repeatability**: the demo resets and reruns deterministically | proves it is a product, not a one-off | live | ✗ (no verified rehearsal) |

**Investor-demo minimum:** A1, A2, A3, A4, A6, A8, A9, A10, A11, A12 — with **A5 and A7 strongly desirable** because they are the two capabilities (outsourced processing; grounded AI) that differentiate CarbonTally from a calculator. `INFERENCE`.

---

## 22. Requirements — B. Potential-customer demonstration

What a prospective **customer** (an organisation buying emissions processing) must see to trust the product with their data.

| # | Requirement | Why the customer cares | Mode | Current state |
| --- | --- | --- | --- | --- |
| B1 | **Onboarding** — signup/invite → organisation created → role assigned → lands in the right workspace | first 5 minutes decide the sale | live | ~ (`/onboarding`, invitations exist; never demoed) |
| B2 | **Upload their own documents** (PDF, spreadsheet, scan) and see them accepted, stored privately and queued | the core intake promise | live | ✔ |
| B3 | **Automatic processing visibility**: what stage, what was extracted, what is blocked and why | removes the "black box" fear | live | ✔ (stages + block reasons) |
| B4 | **Correction path**: fix extraction, re-map, re-validate, recalculate | real documents are messy; the customer must be able to rescue them | live | ~ (workspace actions exist; not exercised end-to-end) |
| B5 | **The calculated result with its factor and method** | the number must be explainable to their auditor | live | ✔ (one record) |
| B6 | **Review and approval by their own staff** (owner/admin), with rejection + reason | governance and accountability | live | ✗ (never executed) |
| B7 | **Dashboard / emissions history** with real totals by scope and period | day-to-day value | live | ~ (1 record; history thin) |
| B8 | **Reports** (annual) matching the dashboard, downloadable | deliverable they can hand to a board | live | ~ |
| B9 | **Evidence**: show me the invoice line behind this number | audit defensibility | live | ✗ |
| B10 | **Exports** (CSV/JSON) | their own analysis/assurance workflows | live | ✔ (exports verified) |
| B11 | **Master data** (facilities, assets, suppliers) so emissions attach to their real estate/operations | they think in sites and suppliers | live | ✗ (0 rows) |
| B12 | **Support/communication** — message CarbonTally inside the product, scoped correctly | trust and escalation | live | ~ (surfaces exist; 0 conversations) |
| B13 | **Consultant option** — "my sustainability adviser works for me in the same platform" | a common buying route | live | ~ (engagements exist, no client documents) |
| B14 | **Their data boundaries** — the platform cannot leak to another customer (demonstrated, not promised) | procurement/legal | live | ✔ code + probes |
| B15 | **Which document types/scopes are supported today** — stated plainly | avoids a failed pilot | spoken + on-screen | requires the limitation script |

**Customer-demo minimum:** B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, B14, B15 — i.e. the demo must exercise the **human review/approval** half of the lifecycle (never yet run) and show **master data** and **evidence**. `INFERENCE`.

---

## 23. Requirements — C. Demo-user / product simulation

What must **exist in the environment** so multiple synthetic users can operate CarbonTally realistically (rather than merely being shown a screen). This is the operational substrate for A and B.

| Requirement | Why it must exist | Today |
| --- | --- | --- |
| **Identities with correct role bindings** across all five planes, able to log in simultaneously | multi-persona demos need live sessions | ✔ tooling; counts to raise (§24) |
| **Two-plus organisations** with separate members so cross-tenant DENY can be shown live | the security story is the first question asked | ✔ 4 orgs |
| **A consultant firm with ≥2 clients**, one client-owner identity, one `active` engagement | consultant story + isolation | ~ engagements exist; no client documents |
| **≥2 Processing Entities**, each with a manager and a staff identity, and **live assignments** | the PE story cannot be simulated without assignments | ✗ (0 assignments) |
| **Internal staff identities** across operator/reviewer/QC/staff-admin/system-admin | ops, review, QC and administration journeys | ✔ 3 profiles (lab) |
| **Work items in many states at once**: blocked, extracted, mapped, validated, calculated, in review, approved, rejected | queues are only meaningful when populated | ~ (13 blocked + 1 review) |
| **An assigned-and-processed PE batch per entity**, including one **partial** and one **completed** item | proves ownership, reassignment and completion semantics | ✗ |
| **Real documents** (PDF text, one scan/image, one spreadsheet) with ground-truth sidecars | extraction honesty + OCR path | ~ (PDFs only) |
| **Master data** (facilities, assets, suppliers) attached to at least one organisation | reporting/Insight context and realistic dashboards | ✗ |
| **Issues** (open, in-progress, resolved) on real items | exception workflow + validation lifecycle | ✗ |
| **Conversations on both planes** (org↔support, consultant↔client, PE↔ops) with a few messages | messaging story + N1 boundaries | ✗ |
| **Reports** at more than one lifecycle state, with an artefact | reporting lifecycle + "approve a report" | ✗ (all DRAFT, no artefacts) |
| **Evidence line items** for the calculated items | Viewer + answer-to-evidence chain | ✗ |
| **Insight interactions** recorded (one conversation, a few tool calls) | proves the Insight plane persists and audits | ✗ (schema absent) |
| **A reset→provision→seed→verify rehearsal** reproducing all of the above | repeatability | ✗ |

---

## 24. Canonical demo topology (minimum, capability-justified)

Sized for **capability coverage, realistic workflow, security demonstration and repeatability** — not dataset size. Every count answers a requirement in §21–§23.

| Element | Minimum | Justification |
| --- | --- | --- |
| **Direct customer organisations** | **2** (Org A primary; Org B isolation control) | one to work in, one to be **denied** (A3, B14) |
| **Users per direct org** | **4** (owner, admin, member, viewer) | owner/admin approve (B6); member processes; viewer read-only (SEC-1) |
| **Consultant firms** | **1** | consultant plane (A4, B13) |
| **Consultant identities** | **2** (firm owner + least-privilege member) | owner operates; member demonstrates capability gating |
| **Client organisations** | **2** (Client A worked-on; Client B isolation control) | cross-client DENY (ISC-12) + one client with a real document/calculation |
| **Client-owner identities** | **2** | client self-determination (A4, B13) |
| **Processing entities** | **2** (PE Alpha, PE Beta) | multi-PE ownership + reassignment (A5; §8.3) |
| **PE identities** | **2 per PE** (manager + staff) = 4 | manager performs PE QC; staff processes; `can_process` gating (ISC-14) |
| **Internal CarbonTally identities** | **4** (operator, reviewer, QC, staff-admin/system-admin) | ops/review/QC/admin journeys; `can_manage_staff` gates messaging + grants |
| **Identity total** | **≈18** (today 13; legacy dataset 1,205) | enough for every plane and every DENY pair; small enough to re-provision deterministically |
| **Batches** | **3** (Org A, Client A, Org B) | per-organisation intake |
| **Work items** | **≈12–15**, deliberately spread: 2 blocked (ambiguous + no-match), 1 spend/unsupported, 2 extractable-not-mapped, 1 mapped, 1 validated, **2 calculated in different periods**, 1 awaiting customer review, 1 approved, 1 rejected, 1 PE-assigned-partial, 1 PE-assigned-completed | every lifecycle state and queue visible on one screen (A8, B3, B4, B6) |
| **PE assignments** | **3** (Alpha→Org A completed; Alpha→Org B **released/partial**; Beta→Client A or a second Org A item) | proves multi-org, partial and reassignment semantics (§8.3) |
| **Documents** | **≈12–15** (matching the items) + 1 scan/image + 1 CSV/XLSX | format coverage (16.1) + OCR path |
| **Master data** | 2–3 facilities, 3–4 assets, 2–3 suppliers, 1–2 customer factors | dashboards, reports, Insight context (B11), factor-approval story (ISC-13) |
| **Issues** | **3–5** (open, in-progress, resolved) | exception workflow (A8, B3) |
| **Conversations** | **4** (Org A↔support; consultant↔Client A; PE Alpha↔ops; PE Beta↔ops), 2–4 messages each | both messaging planes + the N1 boundary (PE context must reference assigned work) |
| **Reports** | **2** (Org A annual; Client A annual) — one advanced to `REVIEWED`/`APPROVED` with an artefact | reporting lifecycle + report approval (A6, B8) |
| **Evidence line items** | **≥ the calculated items** (2–4) | Viewer + answer-to-evidence (A2, B9) |
| **Insight interactions** | **2** (one aggregation, one temporal comparison) + **1 honest `no_data`/`unsupported`** | Insight plane (A7) incl. failure honesty |
| **Scopes / periods** | Scope 1 in **two reporting periods**; Scope 2 location-based in **one** | makes P2 temporal comparison meaningful without inventing market-based Scope 2 |
| **Deny pairs to script** | Org A→Org B; Client A→Client B; consultant→unrelated org; viewer→upload; PE→customer document/conversation; customer→`/ops` | the full security narrative |

**Deliberate non-goals:** no 1,000-org dataset, no fake payment transactions, no invented Scope 3 categories, no auditor persona, no PE↔customer channel. `INFERENCE` grounded in the code evidence above.

---

## 25. Canonical demo dataset (minimum, per data class)

"Tooling" = producible with the **current** Demo Lab tooling (provision/seed/T3) without code change; "seed-only" = needs new synthetic data authored (no code change); "new build" = needs implementation or a decision first.

| Data class | Minimum | Purpose | Persona | Required relationship / state | Tooling? | Seed-only? | New build? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Organisations** | 2 direct + 2 client | work + isolation | all | distinct tenants; org profile filled | ✔ `manifest.json` | — | — |
| **Users / identities** | ≈18 | five planes + DENY pairs | all | correct role bindings; `expect` destinations | ✔ `provision.py` | — | — |
| **Consultant ↔ client** | 1 firm, 2 clients, 2 client owners, 1 `active` engagement | consultant journey + isolation | consultant, client owner | engagement accepted by the client | ✔ | — | — |
| **PE assignments** | 2 PEs, 4 PE identities, **3 assignments** (1 completed, 1 partial/released, 1 second-org) | the PE operating model | PE manager/staff, ops | batches assigned to entities; open/closed ledger rows | ✗ (no seeder) | ✔ (via API) | — |
| **CarbonTally staff** | 4 (operator, reviewer, QC, staff-admin/system-admin) | ops/review/QC/admin | staff | `staff_roles` permissions incl. `can_manage_staff` | ✔ (`manifest.json` has 3) | ✔ (add QC/admin) | — |
| **Documents** | 12–15 + 1 scan + 1 spreadsheet | the intake story | customer, consultant | uploaded, stored privately, queued | ✔ (T3 corpus sync) | ✔ (scan/CSV from the generator) | — |
| **Document states** | spread across ≥6 states | shows the pipeline truthfully | all | pending/extracting/extracted/manual_review/customer_review | ✔ (natural outcomes) | ✔ | — |
| **Extraction records** | all processed docs | extraction visibility | customer, PE | `extracted_data` populated; honest failures kept | ✔ | ✔ | — |
| **Mapping outcomes** | 1 matched, 1 ambiguous, 1 no-match, 1 spend-unsupported | the mapping story incl. honesty | customer, PE | factor referenced for the matched one | ✔ (product behaviour) | ✔ | **spend coverage decision needed** |
| **Validation outcomes** | 1 clean, 1 blocking, 1 corrected | validation lifecycle | customer, PE | issues created then resolved | ✔ | ✔ | — |
| **Calculation records** | **2–3 across two periods** | the core value | customer | snapshots + emissions logs with factor provenance | ✔ | ✔ | — |
| **Two-period comparison** | Scope 1 in period A and B | P2 Insight demo | customer | snapshots in both periods | ✔ | ✔ | — |
| **Scope coverage** | Scope 1 (multiple) + Scope 2 location-based (one) | honest coverage | customer | scope recorded on snapshots | ✔ | ✔ | market-based Scope 2 = **decision** |
| **Facilities / assets** | 2–3 / 3–4 | attach emissions to real estate | customer | assets linked to facilities | ✔ (CRUD) | ✔ | — |
| **Suppliers** | 2–3 | supplier context (with caveat) | customer | supplier rows exist; **note**: `supplier_id` is not written by the emissions path | ✔ (CRUD) | ✔ | supplier-persistence = **decision** |
| **Issues** | 3–5 | exception workflow | customer, staff, PE | open/in-progress/resolved on real items | ✔ (product behaviour) | ✔ | — |
| **Conversations** | 4 (both planes) | messaging + boundaries | customer, consultant, PE, staff | `conversation_kind` correct; PE context = assigned work | ✗ (no seeder) | ✔ (via API) | — |
| **Messages** | 2–4 per conversation | the messaging story | as above | participants correct; no orphans | ✗ | ✔ (via API) | — |
| **Reports** | 2, one `REVIEWED`/`APPROVED` with artefact | reporting lifecycle | customer, client owner | numbers match dashboard/export | ✔ (generation) | ✔ | artefact bucket must exist |
| **Evidence line items** | 2–4 | the evidence chain + Viewer | customer, staff | materialised from real extraction line data | ✗ | ✔ (**requires the authorized backfill path**) | possible **online materialisation gap** |
| **Insight interactions** | 2 + 1 honest failure | the AI story | customer | Insight tables provisioned; interaction + tool calls persisted | ✗ (schema absent) | ✔ after provisioning | provisioning |
| **Approval state** | 1 approved + 1 rejected item, 1 approved report | governance | customer owner/admin | resolution of blocking issues on approval | ✔ (product behaviour) | ✔ | — |

**Critical dependency:** every row marked "seed-only ✔ (via API)" requires the **API to be running against a provisioned lab**, and the evidence row additionally requires the **separately authorised** `backfill_evidence_line_items` execution path. No row requires new *product* code except the two decision-linked items (spend coverage; potential online evidence materialisation). `INFERENCE`.

---

## 26. Investor / demo journeys

Each journey is assessed against **what the code and data actually support today**.

### Journey 1 — Direct customer (upload → … → evidence)
**Steps:** login as Org A owner → upload a document → watch extraction → map (or accept the honest block) → validate → calculate → see the result with factor and method → review/approve → dashboard → annual report → follow evidence to source.
**Works today:** upload → extraction → honest block (13 cases) and **one** complete calculation → report → export. **Does not work today:** the approval step (never executed), the evidence destination (0 rows), and a two-record dashboard.
**Verdict:** *partially demonstrable*; needs §24/§25 population + an approval walkthrough (+ the evidence path) to become the flagship journey. `DATABASE-OBSERVED` + `DOCUMENT-SOURCED`.

### Journey 2 — Consultant
**Steps:** consultant logs in → sees the client portfolio → enters Client A's context → uploads client documents → processes them → consultant review/submit → the client owner logs in, sees their own data, reviews and approves → client report.
**Works today:** portfolio/context/isolation are **independently verified**; the client engagement rows exist in the Demo Lab. **Does not work today:** no client documents, no consultant processing, no client approval.
**Verdict:** *demonstrable after data population* — no code change. `DOCUMENT-SOURCED` + `DATABASE-OBSERVED`.

### Journey 3 — Manual Processing Entity
**Steps:** ops assigns an Org-A batch to PE Alpha → PE manager sees it in `/pe/assignments` → PE staff claims/processes → extracts → maps (blocked documents escalate) → PE review/QC → completes (or releases partially) → messages ops about a specific assigned item → ops reassigns a second Org-A item to PE Beta.
**Works today:** every step exists in code. **Does not work today:** there are no assignments, no grants, no entity conversation and no PE-assigned batches in any demo environment.
**Verdict:** *the biggest untold story*; needs data population and (for manual extraction specifically) a **FIN-06 grant** decision, since manual processing is **off by default**. `CODE-TRACED` + `DATABASE-OBSERVED`.

### Journey 4 — CarbonTally staff
**Steps:** operator monitors the queue and operational health → assigns work → reviewer works the review queue → QC reviews → staff admin configures manual-processing grants / entities → system admin inspects audit.
**Works today:** the surfaces and endpoints exist; the Demo Lab has 3 staff profiles and 113 audit rows. **Does not work today:** review/QC queues are empty; **SLA surfaces are among the known failing tests** (D-29) and `reporting/audit-activity` returns 500 (**F-T1-001**) — the script must avoid or narrate those screens.
**Verdict:** *partially demonstrable*; requires queue population. `CODE-TRACED` + `DOCUMENT-SOURCED`.

### Journey 5 — Insight
**Steps:** ask "what were our Scope 1 emissions in 2025?" → deterministic aggregation → structured answer → provenance → open the evidence.
**Works today:** nothing at runtime — the Insight schema is absent in every database, and only P2 has a dedicated renderer.
**Verdict:** *not demonstrable today*; requires provisioning (all six Insight migrations) + populated calculations + the §24 decision on the P3 presentation surface. `DATABASE-OBSERVED`.

### Journey 6 — Honest failure
**Steps:** upload an ambiguous document (electricity) → the workspace states exactly what was attempted and why it stopped (`no_match`, confidence 0.00) → the presenter offers the next step (manual correction / factor choice) → optionally show a genuinely unsupported question returning `no_data`/`unsupported`.
**Works today:** **yes** — this is the strongest truthful narrative the product has (13 blocked items with machine-readable reasons, and the answer-state vocabulary forbids conflation of `no_data` with `zero`).
**Verdict:** *fully demonstrable today*. `BROWSER-VERIFIED` + `DATABASE-OBSERVED`.

### Journey 7 — Security
**Steps:** Org A owner reads own data (ALLOW) → attempts Org B data (DENY 403/404) → viewer attempts an upload (DENY) → PE attempts a customer document/conversation (DENY) → consultant attempts an unrelated organisation (DENY).
**Works today:** all pairs are implemented and probeable (server-side); DR-005 browser-verified client scoping.
**Verdict:** *demonstrable today*, and it needs no data beyond the two organisations that already exist — it needs a **script**. `CODE-TRACED` + `DOCUMENT-SOURCED`.

### Journey feasibility summary

| Journey | Today | Needs data | Needs code | Needs PO decision | Demo value |
| --- | --- | --- | --- | --- | --- |
| 1 Direct customer (full) | partial | ✔ | ~ (evidence path) | ✔ (approval + evidence + scope) | HIGHEST |
| 2 Consultant | partial | ✔ | ✗ | ~ | HIGH |
| 3 PE | none | ✔ | ✗ | ✔ (FIN-06 grant) | HIGH |
| 4 Staff/ops | partial | ✔ | ✗ | ~ | MED |
| 5 Insight | none | ✔ | ~ (P3 presenter) | ✔ | HIGH |
| 6 Honest failure | **yes** | ✗ | ✗ | ✗ | HIGH |
| 7 Security | **yes** | ~ | ✗ | ✗ | HIGHEST |

---

## 27. Canonical capability matrix

Legend for the state columns: `✔` present · `~` partial · `✗` absent · `UNK` unknown. Requirement columns: `Y` required · `-` not required · `opt` optional.

### 27.1 Customer-facing and processing capabilities

| Capability | Schema | Backend | API | Frontend | Auth/RLS | Existing data | Verified | Demo-req | Investor-req | Cust-demo-req | Missing impl | Data/seed gap | Policy decision | PO auth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Authentication (email/password, personas) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ 13 identities | `BROWSER-VERIFIED` | Y | Y | Y | — | — | — | — |
| Organisation profile / settings | ✔ | ✔ | ✔ | ✔ | ✔ | ~ profile thin | `CODE-TRACED` | Y | opt | Y | — | ✔ | — | — |
| Members & invitations | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ 8 memberships | `CODE-TRACED` | Y | ~ | Y | — | — | — | — |
| Facilities | ✔ | ✔ | ✔ | ✔ | ✔ | ✗ 0 rows | `CODE-TRACED` | Y | ~ | Y | — | ✔ | — | — |
| Assets (facility-linked) | ✔ | ✔ | ✔ | ✔ | ✔ | ✗ 0 rows | `CODE-TRACED` | Y | ~ | Y | ISC-4 unverified | ✔ | — | — |
| Suppliers | ✔ | ✔ | ✔ (read) | ✔ | ✔ | ✗ 0 rows | `CODE-TRACED` | opt | opt | ~ | `supplier_id` never written | ✔ | **supplier persistence (D-09)** | — |
| Vehicles | ✔ | ✔ | ✔ (read) | ✔ | ✔ | ✗ 0 rows | `CODE-TRACED` | opt | - | opt | — | opt | — | — |
| Customer factors (+ approval) | ✔ | ✔ | ✔ | ✔ | ✔ (creator ≠ approver) | ✗ 0 in lab | `DOCUMENT-SOURCED` (ISC-13) | Y | Y | Y | — | ✔ | **single-admin deadlock (FAC-1)** | — |
| Document upload (PDF/CSV/XLSX/image) | ✔ | ✔ | ✔ | ✔ | ✔ (viewer denied) | ✔ 14 docs | `BROWSER-VERIFIED` | Y | Y | Y | — | ✔ | — | — |
| PDF text extraction | ✔ | ✔ | ✔ | ✔ | ✔ | ~ 11 extracted | `BROWSER-VERIFIED` | Y | Y | Y | — | ✔ | — | — |
| OCR (scan/image, Tesseract + ONNX fallback) | ✔ | ✔ | ✔ | ✔ | ✔ | ✗ no scan in lab | `CODE-TRACED` + env dependency | opt | opt | opt | env provisioning | ✔ | — | — |
| Tabular extraction (CSV/XLSX) | ✔ | ✔ | ✔ | ✔ | ✔ | ✗ no tabular doc in lab | `CODE-TRACED` | opt | opt | Y | — | ✔ | — | — |
| Factor mapping (workspace + mapping-options) | ✔ | ✔ | ✔ | ✔ | ✔ | ~ 0 mapped in lab | ISC-9 partially fixed | Y | Y | Y | **browse/search fallback** | ✔ | **spend coverage** | — |
| Validation + issue lifecycle | ✔ | ✔ | ✔ | ✔ | ✔ | ✗ 0 issues in lab | ISC-2 fixed | Y | Y | Y | — | ✔ | — | — |
| Calculation (immutable snapshots + emissions) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ **1** record | `BROWSER-VERIFIED` | Y | Y | Y | — | ✔ (need 2–3 in 2 periods) | Scope 2 method | — |
| Emissions history | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ 1 row | DR-005 | Y | Y | Y | — | ✔ | — | — |
| Customer review / approve / reject | ✔ | ✔ | ✔ | ✔ | ✔ (owner/admin) | ✗ **never executed** | `CODE-TRACED` (ISC-15) | Y | Y | Y | — | ✔ + a live walkthrough | — | **mutating demo step** |
| Consultant review / submit | ✔ | ✔ | ✔ | ✔ | ✔ (flags) | ✗ no engagement work | `CODE-TRACED` | Y | Y | opt | — | ✔ | — | — |

### 27.2 Platform, PE, evidence and Insight capabilities

| Capability | Schema | Backend | API | Frontend | Auth/RLS | Existing data | Verified | Demo-req | Investor-req | Cust-demo-req | Missing impl | Data/seed gap | Policy decision | PO auth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PE workspace & queues | ✔ | ✔ | ✔ `/api/v3/pe/*` | ✔ `/pe`, `/pe/assignments`, `/pe/items/:entityId/:itemId` | ✔ entity-scoped | ✗ 0 assigned work | `DOCUMENT-SOURCED` (boundaries) | Y | Y | opt | — | ✔ **required** | — | — |
| PE assignment ledger (assign/reassign/claim/release/complete) | ✔ `work_item_assignments` (one open/item) | ✔ | ✔ ops `assign`/`reassign` + PE `claim`/`release`/`complete` | ✔ | ✔ RLS on, no policies (API-only) | ✗ 0 rows | `CODE-TRACED` | Y | Y | opt | — | ✔ **required** | — | — |
| FIN-06 manual-processing grants | ✔ | ✔ (fails closed) | ✔ admin | ✔ | ✔ admin-only | ✗ 0 rows (table absent in legacy) | `DOCUMENT-SOURCED` | Y (if manual extraction is shown) | opt | opt | — | ✔ | **grant policy decision** | **mutating** |
| Internal review queue | ✔ | ✔ | ✔ | ✔ `/ops/review/:itemId` | ✔ | ✗ empty | `DOCUMENT-SOURCED` (SLA tests failing, D-29) | Y | Y | opt | SLA surface fix | ✔ | — | — |
| QC queue | ✔ | ✔ | ✔ | ✔ `/ops/qc/:itemId` | ✔ | ✗ empty | `CODE-TRACED` | opt | ~ | opt | — | ✔ | — | — |
| Messaging — org plane | ✔ `conversation_kind='org'` | ✔ | ✔ | ✔ `/messaging` | ✔ N1 gate (PE excluded) | ✗ 0 in lab | `CODE-TRACED` | Y | Y | Y | realtime route (lab) | ✔ **required** | — | — |
| Messaging — entity plane (PE ↔ ops) | ✔ `conversation_kind='entity'` | ✔ | ✔ | ✔ `/pe/messages` | ✔ assignment-scoped context | 1 historical only | `CODE-TRACED` | Y | Y | opt | — | ✔ **required** | — | — |
| Notifications | ✔ | ✔ | ✔ `/api/v3/notifications` | ✔ | ✔ | ✗ 0 | ISC-6 fixed | opt | - | opt | — | ✔ | — | — |
| Reports: generation + lifecycle + artefacts | ✔ | ✔ | ✔ (types/create/content/versions/download/pdf/submit/approve/finalize) | ✔ `/reports(/:id)` | ✔ | ~ 2 versions, **all DRAFT**, 0 artefacts | DR-006 (generation) | Y | Y | Y | — | ✔ (+ lifecycle walkthrough) | — | **mutating** |
| Exports (CSV/JSON, audit-package) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ 1 row exportable | DR-005 | Y | Y | Y | audit-package contract (D-16) | ✔ | — | — |
| **Evidence line items** | ✔ | ✔ (repo + CLI, not online) | ✔ read route | ✔ Viewer | ✔ DM-6 re-check | ✗ **0 everywhere** | viewer `PASS WITH NON-BLOCKING OBSERVATIONS` | Y | Y | Y | **possible online materialisation gap** | ✔ (**authorized backfill**) | — | **backfill auth** |
| Source Evidence Viewer | ✔ | ✔ | ✔ | ✔ `/evidence/line-items/:id` | ✔ | ✗ nothing to resolve | `DOCUMENT-SOURCED` (verified code) | Y | Y | Y | — | ✔ | — | — |
| Disclosure / B-series projection | ✔ | ✔ | ✔ | ~ | ✔ | ✗ 0 rows | `DOCUMENT-SOURCED` | opt | ~ | opt | — | ✔ | D-18 frameworks | — |
| **Insight tools (10) + planner** | ✗ **tables absent** | ✔ | ✔ | ✔ `/insight` | ✔ I2 + rate limit | ✗ non-runnable | INS-01 closed; P2 PO-closed; P3 verified (not closed) | Y | Y | Y | P3 presenter surface | ✔ | **P3 wording** | **provisioning** |
| Rate limiting (technical) | ✗ tables absent locally | ✔ | ✔ | — | ✔ | ✗ | INS-01 closed | opt | ~ | opt | — | ✔ | — | — |
| Audit trail | ✔ | ✔ | ✔ (admin) | ~ | ✔ | ✔ 113 rows | `CODE-TRACED` | Y | Y | ~ | F-T1-001 on one surface | — | — | — |
| Billing / commercial surfaces | ✔ | ✔ | ✔ | ✔ `/billing` | ✔ `can_manage_billing` | ✗ no rows | `DOCUMENT-SOURCED` | opt | opt | opt | no PSP (by design) | opt | **D-20…D-26** | — |
| Admin control plane (entities/grants/roles) | ✔ | ✔ | ✔ | ✔ `/ops` | ✔ admin | ~ 1 entity, 3 roles | `CODE-TRACED` | opt | ~ | opt | — | ✔ | ISC-10 role model | — |
| Search | ✔ | ✔ | ✔ | ~ | ✔ org-scoped | ~ thin | `CODE-TRACED` | opt | - | opt | — | ✔ | — | — |
| Whitelabel / consultant branding | ✔ | ✔ | ✔ | ✔ | ✔ | ~ | `CODE-TRACED` | opt | opt | opt | customer-owned DNS (per AGENTS.md §64) | opt | — | — |
| **Demo reset / repeatability** | — | — | — | — | — | tooling present | ✗ no verified rehearsal | Y | Y | Y | — | ✔ | **re-provision auth** | **mutating** |
| Demo verification tooling (incl. Insight checks) | — | — | — | — | — | identities/authorization only | harness's only IV = **FAIL** | Y | Y | Y | Insight checks absent | ✔ | — | **IV auth** |

---

## 28. Gaps and defects

### 28.1 Genuine code / implementation gaps

| # | Gap | Impact | Evidence |
| --- | --- | --- | --- |
| G1 | **No online evidence-line materialisation path**: processing only *looks up* materialised lines, so `evidence_line_items` (and hence the Viewer and the E3 promise) stays empty unless the offline CLI is run | the differentiated "evidence behind the number" story is unavailable | `CODE-TRACED` |
| G2 | **Factor mapping has no browse/search fallback**, and **no spend-factor coverage exists** (0 £/GBP factors, 0 spend activities) | a large class of real documents dead-ends at mapping (ISC-9) | `CODE-TRACED` + `DATABASE-OBSERVED` |
| G3 | **No automatic work-routing to a PE**: assignment is an explicit staff action or a PE claim; no dispatch rule/queue engine exists | at scale a human must dispatch; the demo must show that step explicitly | `CODE-TRACED` |
| G4 | **Review/SLA surfaces are among the known failing tests** (`test_review_sla_surfaces.py` ×3) and `reporting/audit-activity` returns **500** for an authorised owner (F-T1-001) | two investor-visible surfaces must be avoided or narrated | `DOCUMENT-SOURCED` |
| G5 | **`supplier_id` is never written** by the emissions path | supplier analytics/Insight permanently `no_data` (D-09) | `DATABASE-OBSERVED` + `DOCUMENT-SOURCED` |
| G6 | **P3 has no UI renderer** | P3 can only be shown as a tool-call + narration | `CODE-TRACED` |
| G7 | **`ghg_inventory` reports cannot be refreshed** (generation supports `annual` only → 422) | a legacy report remains stale wherever one exists | `DOCUMENT-SOURCED` (DR-006) |
| G8 | **Single-admin customer-factor deadlock** (the creator cannot self-approve) | a one-admin organisation cannot approve its own factors | `DOCUMENT-SOURCED` (FAC-1) |

### 28.2 Environment / schema / data gaps

| # | Gap | Impact |
| --- | --- | --- |
| E1 | **Insight schema absent in every database** (six migrations unapplied) | the entire Insight plane is non-functional locally |
| E2 | **Demo Lab thin**: 0 assignments, 0 grants, 0 messaging, 0 issues, 0 master data, 0 evidence, 1 calculation | the PE, consultant, messaging, reporting-lifecycle and evidence stories cannot be shown |
| E3 | **Configured dev DB unusable as a demo** (no factors, no documents, 2-table storage substrate) | confusion about which environment is which |
| E4 | **Legacy dataset on a pre-evidence schema** (116 tables; no evidence/disclosure/artefacts/grants) | cannot express the modern capability set |
| E5 | **Generator checkout for `sync-corpus`**: `/tmp/extgen` is gone; the pinned checkout is now at `/home/shomonrobie/carbon_tally_synthetic_documents` (pin matches) and must be supplied as `--source` | corpus re-sync blocked until `--source` is provided |
| E6 | **No verified reset→re-provision→re-seed rehearsal** for the current release | repeatability unproven |
| E7 | **Realtime route missing in the lab gateway** | messaging live delivery cannot be shown |
| E8 | **No demo script, runbook or limitation script** | the audience may hear claims the screens do not support |
| E9 | **`F-046-1` name guard does not match the legacy dataset's DB name (`postgres`)** | residual destructive-test risk |

### 28.3 Verification gaps

| # | Gap | Impact |
| --- | --- | --- |
| V1 | The demo harness's only independent verdict is **FAIL** (pre-remediation); the remediation is implementer-verified | the tooling that produces demo evidence is itself unverified |
| V2 | **No independent verification of the messaging planes, the PE workflow, the assignment ledger, the reporting lifecycle or master-data CRUD** | unverified areas would be presented as if verified |
| V3 | **P3 remains PO-unclosed** (P3-IV-02…05 open) | wording risk in any Insight narrative |
| V4 | ISC-4/ISC-7 (asset 500 without facility; facility shown `Inactive`) were **not re-verified** here | unknown whether they still reproduce |

---

## 29. Policy decisions

### 29.1 New decisions raised by this study (demo/product-facing)

| ID | Decision | Why it matters | Evidence | Options | Downstream | Mutation risk | Demo impact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D-P1** | **Which environment is canonical for the demo** | everything else depends on it | §17–§20 | (a) provision the Demo Lab to the current schema; (b) build a new lab DB; (c) modernise the legacy dataset | all demo work | **yes** (provision/reset) | determines what can be shown |
| **D-P2** | **Whether manual processing (therefore FIN-06 grants) is switched on for the demo** | without a grant the PE manual-extraction path cannot be exercised; with one, a governance gate is opened for the demo orgs | grants default off; the legacy dataset has no grants table | (a) grant for demo orgs only; (b) automatic-only PE processing; (c) skip PE | PE journey | **yes** | PE journey on/off |
| **D-P3** | **Spend-document policy** | decides whether spend invoices are shown, excluded or fixed | 0 spend factors; ISC-9 | (a) load spend factors + browse fallback; (b) exclude and state it; (c) keep unsupported but narrated | mapping coverage | data load | mapping story |
| **D-P4** | **Evidence-line policy** — authorized backfill vs an online materialisation change | the E3 evidence promise | G1, E2 | (a) authorize a demo-lab backfill; (b) implement online materialisation; (c) show lineage panels only and say so | evidence journey | **yes** (backfill) | highest-value differentiator |
| **D-P5** | **P3 presentation wording and surface** | honesty + investor value | P3 not closed; no renderer | (a) tool-call + narration; (b) minimal presenter surface; (c) defer P3 | Insight journey | no | Insight narrative |
| **D-P6** | **Whether an approval walkthrough (item + report) is performed on demo data** | the governance half of the lifecycle has never been executed | ISC-15 | (a) authorize on the lab; (b) narrate as "wired, not executed" | customer journey | **yes** | credibility of the approval story |
| **D-P7** | **Supplier-persistence decision** | supplier analytics cannot work without it | G5 / D-09 | (a) authorise a capture point; (b) keep `no_data` and narrate | Insight supplier family | possibly schema | avoids a false impression |
| **D-P8** | **Scope coverage statement** (Scope 1 + Scope 2 location-based in; Scope 3 / market-based / Scope 1 decomposition out) | prevents over-claiming | prior study §13 | (a) publish the coverage table in the script; (b) stay silent (not recommended) | all narratives | no | investor trust |
| **D-P9** | **Live-environment inspection path** (read-only credential or ledger) | every live claim is `UNKNOWN` | §18 | (a) provide read-only access; (b) accept `UNKNOWN` for this phase | drift assessment | **yes if misused** | live demo claims |
| **D-P10** | **Confirm the PE ↔ customer communication boundary as deliberate product design** | it is both a differentiator and a constraint | §12.2 | (a) confirm as designed; (b) revisit | topology | no | how the PE story is told |

### 29.2 Existing decisions still open and relevant

`D-09` supplier persistence · `D-10` Scope 2 market-based · `D-11` comparison basis/restatements · `D-12` variance · `D-13` Scope 3 taxonomy + factor history · `D-14` data-quality signals · `D-15` Scope 1 decomposition · `D-16` E4 audit package · `D-18` reporting frameworks · `D-19` reduction · `D-20…D-26` commercial · `D-27` untracked-doc durability · `D-28` X2/X7 records · `D-29` reviewer/SLA failures · `FAC-1` single-admin factor approval · `ISC-10` staff role model · `P-01/P-02` consultant/auditor Insight · `P-03/P-04/P-05` I7/I8/production.

---

## 30. Recommended implementation roadmap

Ordered by dependency. **None of it is authorized by this study.** "Safe now?" = could be authorized without further PO input (an authorization is still required).

| # | Package | Objective & capability | Evidence | Depends on | DB impact | Code impact | UI impact | Demo impact | Security implications | Data need | Independent verification | Safe now? | PO decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **R1** | Documentation & decision reconciliation | record the persona/topology reality; reconcile `AGENTS.md` §54, P1-matrix staleness, T3 record inconsistency | this study; prior studies | — | none | none | none | prevents mis-citation | none | none | not required | **Yes** | D-P10 + divergence handling |
| **R2** | Mapping fallback (bounded code) | factor browse/search fallback in `mapping-options`, preserving allowlist + org scoping | ISC-9; `mapping_options` exists | — | none | one module + tests | workspace behaviour | removes the most common dead-end | must preserve allowlist/tenant scoping | a few extra factors | unit + API tests | **Yes** | D-P3 |
| **R3** | Canonical environment provisioning | provision the Demo Lab to the current schema (all 81 migrations incl. the six Insight ones); record the schema revision; enable `sync-corpus --source <pinned checkout>` | E1, E2, E5 | D-P1 | lab DB rebuilt | none (run tooling) | enables `/insight` + rate limiting | enables every journey | lab-only; never touch `postgres` | full re-provision | pre-demo verification + rehearsal | **No — needs D-P1** | D-P1 |
| **R4** | Demo population & script | seed the §24/§25 topology: personas, PE assignments, documents in many states, master data, issues, conversations, reports, approvals | E2; §23–§25 | R3; D-P2/D-P6 | lab inserts via API | none | all surfaces populated | turns journeys 1–4 live | FIN-06 grant decision; no fabricated data | substantial seed effort | pre-demo run + rehearsal | **No — mutating** | D-P2, D-P6 |
| **R5** | Evidence enablement | populate `evidence_line_items` for demo items; demonstrate the Viewer (dry run first) | G1, E2 | R4; D-P4 | evidence rows (lab) | **possibly one gap** (online materialisation) if the PO wants it permanent | Viewer becomes live | unlocks the flagship evidence story | DM-6 re-check shown; no signed URLs | line data must exist in extraction | independent check + end-to-end journey | **No — backfill auth** | D-P4 |
| **R6** | Insight presentation | run the Insight plane end-to-end (P2 comparison, aggregation, provenance, P3 with honest wording) + add Insight checks to the demo verifier | E1, V3 | R3, R4, R5 | none | optional minimal P3 renderer | `/insight` demonstrable | the differentiated AI story | I2 + rate limiting must hold | two periods of data | demo verification run | **No — needs R3** | D-P5 |
| **R7** | Messaging & PE operational demo | seed both messaging planes (incl. PE↔ops with assigned-work context) and exercise the PE journey | E2, E7 | R4; D-P2 | conversations/messages (lab) | none (realtime route optional) | `/messaging`, `/pe/messages` live | proves the operating model + boundaries | participant/context gates must be shown working | 4 conversations | demo verification | **No — mutating** | D-P2 |
| **R8** | Demo-harness verification | independent verification of the remediated `t3_scenarios.py` + manifest, and of the PE/messaging/reporting paths | V1, V2 | R3 | none | none | none | the demo's own evidence becomes trustworthy | none | none | **independent pass (required)** | **No — IV auth** | — |
| **R9** | Demo gate & runbook | pre-demo verification record, limitation script, gate checklist | E8 | R2–R8 | none | small verifier additions | none | repeatable, truthful demo | ALLOW/DENY scripted | none | the gate itself | No | D-P8 |
| **R10** | Review/SLA & F-T1-001 triage | fix or narrate the two failing surfaces | G4 | — | none | small | `/ops` review + audit screens | removes two landmines | none | none | regression tests | **No — separate triage** | — |
| **R11** | Accounting expansion (Scope 3 / market-based Scope 2 / Scope 1 decomposition / variance / supplier / factor history / methodology) | future capability | prior study §13 | policy decisions | schema | significant | significant | **out of scope for the demo** | new dimensions must be org-owned + immutable | significant | package-specific | **No — policy-blocked** | D-09…D-15 |
| **R12** | L7 / L8 / commercial / production | governance, lifecycle, operations, billing, deployment | prior studies | PO decisions | various | various | various | **outside the demo gate** | significant | various | separate gates | **No** | D-01…D-08, D-20…D-26, G0-D |

**Recommended sequence:** **R1 → R2 → R3 → R4 → R5 → R7 → R6 → R8 → R9**, with R10 handled in parallel as a separate triage and R11/R12 explicitly outside.

---

## 31. Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| K1 | **Over-claiming to an investor** (e.g. showing Insight, evidence or the PE workflow as if operating) | High if unauthorised demos proceed | Reputationally fatal | the limitation script (R9); present unexercised surfaces as "wired, not yet exercised" |
| K2 | **Destructive test or reset aimed at the wrong database** (the harness truncates its target; `postgres` is not covered by the `F-046-1` name guard) | Medium | Loss of the only legacy dataset | never point integration/reset tooling at `postgres`; consider extending the guard (separate authorization) |
| K3 | **Mutating the legacy dataset** while trying to "modernise" it | Medium | Irreversible loss of UAT breadth | keep it read-only; recreate shapes in the lab instead (D-P1) |
| K4 | **Granting FIN-06 manual processing broadly** to make the demo work | Medium | Weakens a governance control | scope grants to demo orgs; document the reason and expiry |
| K5 | **Fabricating demo data** (invented totals, fake suppliers, mocked messages) | Medium | Directly contradicts AGENTS.md §85 | only real pipeline outcomes; keep honest failures visible |
| K6 | **Insight provisioning without verification** (the six migrations applied but the plane untested) | Medium | A "working" Insight page that errors | R8 independent verification incl. Insight checks |
| K7 | **P3 presented as closed** while P3-IV-02…05 remain open | Medium | Unsupported claim | D-P5 wording decision; state P3 status precisely |
| K8 | **Live claims made without a read-only path** | Medium | Unverifiable statements | keep `UNKNOWN`; D-P9 |
| K9 | **Demo drift** (a rehearsed demo fails live) | Medium | Loss of credibility | R9 gate + rehearsal; verifier run immediately before |
| K10 | **Time/cost**: population + verification is substantial work | High | Delay | bounded packages with explicit stop points (as in this study) |

---

## 32. Recommended next PO actions

1. **Decide D-P1** (canonical environment) — this unblocks R3 and everything after it.
2. **Decide D-P2 / D-P6 / D-P4** (PE grant, approval walkthrough, evidence policy) — these are the three decisions that convert the product's best stories from "implemented" to "demonstrated".
3. **Authorize R1 and R2** (documentation reconciliation; bounded mapping fallback) — both are low-risk and independent.
4. **Authorize R3 as a *proposal* first** (a written re-provision plan naming the exact target DB, migrations, and the pre/post verification) before any reset.
5. **Authorize R8 early** — an independent verification of the demo harness and of the PE/messaging/reporting paths should run **before** the demo is scripted around them.
6. **Decide D-P8 + D-P5** (coverage and P3 wording) and commission the limitation script so no presenter can over-claim.
7. **Decide D-P9** (read-only live path) if any live-environment statement is to be made.
8. **Note the standing constraints:** the legacy `postgres` dataset stays read-only; no evidence backfill without explicit authorization; no P3 closure claim; the investor demo dataset must not be reset casually.

---

## 33. Explicitly NOT AUTHORIZED work

* Any implementation, refactor or code change (including the mapping fallback R2 until authorized).
* Any schema change, migration or migration execution against **any** persistent environment.
* Any database mutation: INSERT/UPDATE/DELETE/TRUNCATE/ALTER/DROP, seeds, resets, backfills.
* The `backfill_evidence_line_items --apply` path in **any** environment.
* Demo Lab reset or re-provision.
* Modification or migration of the historical `postgres` dataset; reviving the old seeder.
* Any change to the synthetic generator (external infrastructure) or its pinned commit.
* Frontend, configuration, billing or commercial changes.
* Creating demo users, sending messages or invoking mutating endpoints in **any** live environment.
* Production deployment, credential creation/modification, or use of the production service-role/owner credentials.
* Any claim of investor readiness, production readiness, certification, audit assurance, commercial readiness or live-environment readiness.
* Insight L7/L8, Scope 3, market-based Scope 2, Scope 1 decomposition, variance/attribution, supplier intelligence, RAG/NL-SQL, consultant/auditor Insight.

---

## 34. Study limitations

1. **Read-only and non-exhaustive**: this study inspected code, schema, local data and documents; it did **not** run the product, execute tests, or mutate anything. `BROWSER-VERIFIED` claims are inherited from prior records, not re-derived here.
2. **No live inspection**: production is entirely `UNKNOWN` (no safe path). Every live row in this report says so.
3. **Insight could not be exercised** in any reachable database (schema absent), so Insight findings are code/contract-level only.
4. **CRLF caution**: line-based text matching against CRLF SQL mementos can be misleading; structural claims were cross-checked via `psql` where possible.
5. **The PE, messaging, reporting-lifecycle and master-data paths are code-traced, not exercised** — their "implemented" status reflects code, not runtime proof; V2 records this.
6. **Schema naming vs reality**: `manual_extraction_items.status` has no CHECK constraint, so a status observed in data is app-driven and cannot be treated as a fixed enumerated vocabulary.
7. **Persona completeness**: it is possible that rare role names exist in `staff_roles` data (e.g. beyond operator/reviewer/qc/admin) that were not enumerated; the permission *vocabulary* was enumerated instead.

---

## 35. Repository-impact verification

**Method.** Immediately before committing, the study verified: (a) the tracked-file diff; (b) the untracked inventory; (c) that no application, test, migration, frontend, configuration, demo-tooling or database-related file appears in either set; (d) that the new report contains no credential material.

| Check | Command | Result |
| --- | --- | --- |
| Tracked modifications | `git status --porcelain \| grep -v '^??'` | ` M .gitignore` **only** — pre-existing PO change, untouched by this study |
| Tracked diff stat | `git diff --stat` | `.gitignore \| 215 +++/--- (108 insertions, 107 deletions)` — pre-existing, unmodified |
| Untracked inventory | `git status --porcelain \| grep '^??'` | pre-existing PO artefacts (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-…txt`, 8 `docs/` reference documents) **plus exactly one new file**: `docs/architecture/CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md` |
| Code/test/migration/frontend/config changes | `git status --porcelain \| grep -E 'backend/\|frontend/\|supabase/\|tools/\|\.env\|\.json$\|\.sql$'` | **NONE** |
| Report size | `wc -l`, `wc -c` | **983 lines**, **113,797 bytes (~114 KB)** — 35 numbered sections |
| Secret scan | `grep -E 'eyJ\|postgres://\|postgresql://\|service_role\|sk-\|passw\|secret'` and JWT/opaque-token shapes | **no credential material**: matches are limited to the words "password"/"authorised", function names (`require_consultant`, `require_permission`), public document names, migration filenames and public commit SHAs. **No JWT-shaped strings; no connection strings; no keys** |
| Generated data / dumps committed | inspection | **none** — `diff` and `add` scoped to the single report path |
| Files outside the repository touched | `/home/shomonrobie/carbon_tally/.env.production` (read for credential *types* only — **not modified, not copied**); `/home/shomonrobie/carbon_tally_synthetic_documents` (**read-only**; untracked `generation_report.md`/`output/` belong to the generator's prior runs, not to this study) | no modification |

**Statement of scope compliance:** this task created exactly **one** repository file, modified **no** other repository file, executed **no** migration, seed, reset, backfill or mutating statement, and contacted **no** production system. `GIT-VERIFIED`.

























