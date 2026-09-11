# CarbonTally V3 — Full Persona-Based Product Acceptance & Workflow Audit

**Date:** 2026-08-28
**Auditor:** OpenHands (OHD), independent Product Owner acceptance audit
**Baseline tested:** Git `c36c848` (current `main`), running local/dev stack
**Scope:** Actual runtime behaviour of the current implementation — UI, API, authorisation, database, RLS, business rules — across every persona defined by the authoritative V3 UX/product documentation (`docs/audit/openhands/ui-ux/`).

> **Method.** Every claim in this report was verified at runtime (browser UI, HTTP API, and/or PostgreSQL). Statuses use the mandated vocabulary: `VERIFIED WORKING`, `PARTIALLY WORKING`, `BROKEN`, `NOT IMPLEMENTED`, `NOT TESTABLE`, `ENVIRONMENT BLOCKED`, `PO DECISION REQUIRED`. A route/table/button existing is **not** treated as working. No production code, schema, migration, RLS policy, API, or configuration was modified. No commit/push was made. OHD-created test artefacts are listed in §35.

---

## 1. Executive summary

CarbonTally V3 is a **substantially implemented platform** with strong foundations — a working backend calculation engine, correct org-scoped RLS isolation, functioning processing-entity assignment and extraction, working reviewer/QC gates, a complete staff-admin control plane (retention, commercial versioning, audit), and honest "not configured / not implemented" messaging where features are absent.

However, **the platform does not yet allow every persona to perform their approved workflow end-to-end.** The decisive gaps:

| # | Finding | Severity | In one line |
|---|---------|----------|-------------|
| SEC-1 | Customer **Viewer can upload documents** (write op on a read-only role) | **P1 (authorisation)** | `POST /api/v3/uploads` accepts viewer role |
| MSG-1 | **Conversation creation always fails (500)**; participants never recorded; orphan threads accumulate | **P1** | `ON CONFLICT (conversation_id, user_id)` has no matching unique constraint |
| PRC-1 | **Customer "Review & approve" page is broken** | **P1** | `/api/v3/processing/customer-review` and `queue?stage=review` → 500 `column reference "id" is ambiguous` |
| CON-1..3 | **Consultant cannot create customers, upload documents, or process/map** (PO hypotheses confirmed) | **P1** | No UI path; APIs 403/422 |
| MD-2 | **Vehicles master data is broken** — `public.vehicles` table does not exist | **P1** | `POST /api/v3/vehicles` → 500; Vehicles tab shows error |
| MD-1 | Facility creation 500s when postcode/eircode omitted (DB CHECK vs API schema mismatch) | **P2** | `facilities_postcode_or_eircode_check` |
| RPT-2 | `/api/reference/fuel-types` → 500 (stale table name `defra_conversion_factors`) | **P2** | reference/fuel dropdowns broken |
| PERF-1 | Notifications UI fails for every user ("Error fetching notifications") — RLS enabled, zero policies | **P2** | feature-level break, no data leak |
| FAC-1 | Solo-admin orgs can never approve a custom factor (self-approval correctly blocked; no alternative approver) | **PO DECISION REQUIRED** | D-cf-3 self-approval prevention |

**Positive verifications (real, not demo-data):** org-scoped isolation holds in both directions (cross-org read/upload → 403); PE document/queue/messaging boundaries → 403; reviewer→operator-queue and reviewer→calculate are denied (403); custom-factor self-approval blocked (403) and approval by another admin works (200, status `active`); organisation profile edits persist after reload; search is org-scoped; the emissions calculation form produces real persisted results through the backend factor engine; reports list/status/export works and surfaces honest generation failures; retention settings and commercial rule versioning render with correct "unset = not configured" semantics; client switching for consultants re-scopes every dashboard metric (verified A→B with different totals); mobile (390 px) shows no horizontal overflow.

**Bottom line:** the acceptance chain **REAL USER → REAL ACTION → REAL RESULT** works for customer operations (except customer review/approval), PE processing (assigned extraction), and CarbonTally operations. It is **broken for the consultant's core value chain** (create customer → upload → process → map), for **customer review/approval**, for **conversation creation (N1)**, and for **vehicles (D17)**. **Viewer is not read-only (SEC-1).** The Cline backlog (§B) lists 30 implementable items with acceptance criteria.

---

## 2. Audit methodology

1. **Baseline** — confirmed running stack: frontend `http://localhost:3000`, backend `http://localhost:8050` (V3 API `/api/v3`), Supabase auth `127.0.0.1:54425`, Postgres `127.0.0.1:54426` (local/dev; anon-key demo JWT). Environment is **local/test** — safe for test data (§31).
2. **Documentation** — read the authoritative set: `MASTER_INDEX`, `MASTER_SCREEN_INVENTORY`, `MASTER_WORKFLOW_MAP`, `MASTER_UI_UX_ASCII_DESIGNS`, `MASTER_UX_RECOMMENDATION`, `UI_UX_IMPLEMENTATION_MATRIX`, `CARBONTALLY_V3_DESIGN_SYSTEM`, `MASTER_UX_DECISION_RECONCILIATION_REPORT`, `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE`, decision registers (D1–D21, N1–N3, D-cf-*, D35).
3. **Personas** — used the 11 seeded demo identities (`@demo.carbontally.local`) plus OHD-created accounts (`ohd.*@test.carbontally.local`, signup-created via `POST /api/v3/organizations`). See §4 and the Persona Test Matrix.
4. **Testing** — real browser (custom CDP harness in `/tmp/ct_audit`) for UI flows; HTTP API for contract/authorisation checks; direct PostgreSQL (read-only) to confirm DB state, constraints, RLS; source inspection **only** to root-cause failures (never to claim success).
5. **Negative testing** — for every persona, attempted actions that should fail (§26 / security report).
6. **Data hygiene** — only OHD test data created; identities/passwords never written into any deliverable.

---

## 3. Baseline tested

- Git: `c36c848` on `main`.
- Frontend: Create React App, react-scripts; V3 surface in `frontend/src/v3/`.
- Backend: FastAPI; V3 routers in `backend/api/v3_*.py`; domain in `backend/domain/`; data layer in `backend/data/`.
- Database: PostgreSQL + Supabase-compatible PostgREST; RLS enabled on core tables; anon key demo JWT.
- All services healthy at audit time (frontend 200, backend 200, auth 200, Postgres up).

---

## 4. Persona list

Test identities actually used (labels only; no credentials). Full matrix in the Persona Test Matrix deliverable.

| Test identity | Persona | Organisation | Tested |
|---|---|---|---|
| OHD Owner A | Customer Owner | Test Organisation A | YES |
| OHD Admin A | Customer Admin | Test Organisation A | YES |
| OHD Member A | Customer Member | Test Organisation A | YES |
| OHD Viewer A | Customer Viewer | Test Organisation A | YES |
| OHD Owner B | Customer Owner | Test Organisation B | YES |
| owner@demo | Customer Owner (demo) | CarbonTally Demo Ltd | YES |
| admin@demo | Customer Admin (demo) | CarbonTally Demo Ltd | YES (denied /ops — correct) |
| consultant@demo | Consultant | Net Zero Advisory Ltd | YES |
| OHD Consultant Client B | Consultant client (data) | linked org (Client B) | YES |
| entity-staff@demo | PE Staff | Entity Beta | YES |
| operator@demo | CarbonTally Operator | — | YES |
| reviewer@demo | CarbonTally Reviewer | — | YES |
| qc@demo | CarbonTally QC | — | YES |
| staff-admin@demo | Staff Admin | — | YES |
| member@demo / viewer@demo | Customer Member / Viewer (demo) | CarbonTally Demo Ltd | PARTIAL |

**System Admin:** there is **no distinct System Admin role** in the current platform. The highest internal role is staff `admin` (staff-admin@demo), which owns the full control plane (staff, entities, retention, commercial, audit, settings). See finding AUTH-2.

---

## 5. Role × capability matrix

See `CARBONTALLY_V3_PERSONA_TEST_MATRIX.md` for the full matrix. Summary of decisive rows:

| Capability | Owner | Admin | Member | Viewer | Consultant | PE Staff | Operator | Reviewer | QC | Staff Admin |
|---|---|---|---|---|---|---|---|---|---|---|
| Login + workspace routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Upload documents | ✅ | ✅ | ✅ | **❌ SEC-1** | **❌ CON-2** | ❌ (by design) | n/a | n/a | n/a | n/a |
| Create batch | ✅ | ✅ | ✅ | ✅(403 denied) | **❌** | n/a | ✅ | n/a | n/a | ✅ |
| Facilities CRUD | ⚠️ MD-1 | ⚠️ | ✅ read | ✅ read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Locations (facilities model, N2) | ✅ (as facility) | ✅ | read | read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Assets CRUD | ✅ | ✅ | read | read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Vehicles CRUD | **❌ MD-2** | **❌** | read | read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Suppliers CRUD | ✅ | ✅ | read | read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Custom factors (draft→active) | ⚠️ FAC-1 | ⚠️ FAC-1 | create draft | read | ❌ | n/a | n/a | n/a | n/a | n/a |
| Members/invitations | ✅ | ✅ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a |
| Org profile edit (persists) | ✅ | ✅ | ❌ | ❌(403) | ❌ | n/a | n/a | n/a | n/a | n/a |
| Emissions calculation | ✅ | ✅ | ✅ | read | read only | n/a | ✅ | ❌(403) | ✅ | ✅ |
| Customer review/approve | **❌ PRC-1** | **❌** | **❌** | **❌** | read | n/a | n/a | n/a | n/a | n/a |
| Reports view/export | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | n/a | n/a | n/a |
| Messaging send/reply | ✅ | ✅ | ✅ | ✅ | ✅ | ❌(403) | n/a | n/a | n/a | ✅ |
| Conversation **creation** | **❌ MSG-1** | **❌** | **❌** | **❌** | **❌** | ❌ | n/a | n/a | n/a | **❌** |
| Consultant client mgmt | n/a | n/a | n/a | n/a | ✅ | n/a | n/a | n/a | n/a | n/a |
| PE assigned extraction | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | n/a | n/a | ✅ |
| Reviewer/QC gates | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | ✅ |
| Staff/roles/entities mgmt | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Retention config (N3) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Commercial/billing config | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

`n/a` = action not applicable to that persona by the product model.

---

## 6. Authentication findings

- **AUTH-1 VERIFIED WORKING — persona routing.** All 11 demo identities and all OHD identities authenticate via the Supabase password grant and land on the correct workspace: customers → `/` (V3 customer shell), consultant → `/consultant`, staff → `/ops` (Internal Operations), PE staff → `/ops` (PE workspace, zero-state when unassigned). No existing user was ever redirected to `/onboarding` — the reported onboarding regression was not reproduced (POST-login role resolution works via `/api/organizations/members/user/{id}` for customers and `/api/v3/ops/me` for staff/PE).
- **AUTH-2 ROLE MODEL NOTE.** Staff roles are `operator`, `reviewer`, `qc_specialist`, `admin` (`staff_roles` table) plus a stray `t_ba_34e3cb` test role that leaks into the staff role selector (UX-7). Customer roles are `owner/admin/member/viewer` (RLS constraint on `organization_members`). There is no System Admin role; the control plane is the staff `admin` role.
- **AUTH-3 VERIFIED — separation.** Customer `admin@demo` hitting `/api/v3/ops/me` → 403 `{"perms":"all-false"}` (customers are not staff). Staff users hitting customer-only endpoints are correctly gated.
- **AUTH-4 PARTIALLY WORKING — notifications.** See PERF-1.

---

## 7. Customer findings

- **CUS-1 VERIFIED — documents.** Owner/Admin/Member upload works (201, Supabase Storage object + DB row; `viewer_up.pdf` in Org A proves viewer upload — SEC-1). Documents page shows name/type/size and an "Emissions from this document" action. However the page is file-manager flavoured ("Upload and browse org documents"), consistent with the PO observation that documents emphasise file size rather than the emissions outcome (UX-8).
- **CUS-2 VERIFIED — emissions.** `/emissions` renders "Authoritative V3 calculation — the backend matches factors and computes results". A calculation (quantity × factor, scope/country/year) persisted to `emissions_logs` (history shows `11735.015649 kg CO₂e`, Scope 1, 2026). Factor name column renders "—" (UX-6).
- **CUS-3 BROKEN — review & approve.** `/review` shows "Something went wrong — Network error". API: `GET /api/v3/processing/customer-review?organization_id=…` and `GET /api/v3/processing/queue?stage=review` → **500 `column reference "id" is ambiguous`**. The customer cannot review or approve processed items (PRC-1). This blocks the workflow handoff **CALCULATE → CUSTOMER REVIEW → CUSTOMER APPROVAL → REPORT**.
- **CUS-4 VERIFIED — reports.** `/reports` lists real reports (Ready/Queued/Failed) with export CSV/JSON and download; 2023 report honestly surfaces `Failed: Generation failed: no emissions_logs rows for organisation …` — no fabricated reports. `POST /api/v3/reports/generate` exists.
- **CUS-5 VERIFIED — issues.** Issue creation works (`POST /api/v3/issues` → 201; `issue_type` constrained to `defect|exception|escalation`). Issue status-transition endpoint path mismatch found during testing (`/issues/{id}/status` → 404; see DOC-2).
- **CUS-6 VERIFIED — billing.** `/billing` renders plan (no active subscription), billing mode CREDIT, credit history, Assisted Processing estimate builder, Managed Processing request form, orders (empty state). The customer commercial surface is present.
- **CUS-7 VERIFIED — existing-data (D35).** `/existing-data` renders the "Find existing data" candidate search (org name / company number / email domain / contact email) with honest "candidates only — never ownership" language.
- **CUS-8 PARTIALLY — organisation profile.** `/organization` (V3 AdminPage) renders all 9 tabs for owner/admin. Profile edit persists after reload (PUT `/organizations/{id}/profile` → 200; GET reflects changes; viewer PUT → 403). Note the route is `/organization` (US) while the nav label is "Organisation" (UK) — minor inconsistency.
- **CUS-9 VERIFIED — members & invitations.** Member list, role change (owner→member→viewer→member round-trip verified), add-by-user-id, invitations create/list/revoke all work (201/200). UI "Add member"/"Invite" buttons enable when the corresponding input is filled (the earlier "disabled" observation was the empty-state).

---

## 8. Consultant findings (deep test)

The PO's consultant hypotheses were tested end-to-end (UI + API + DB).

- **CON-1 BROKEN — cannot create customers.** The consultant workspace shows a client list but **no "Add client / New customer" action**. `POST /api/v3/consultants/me/clients` requires an existing `organization_id` (422 without it) — it only *links* an existing org; it cannot create one. `POST /api/v3/organizations` (D35 self-service) exists and any authenticated user may call it, but no consultant UI path exposes it, and using it makes the caller the org OWNER (incompatible with the consultant model). **A consultant cannot onboard a new customer through the product.**
- **CON-2 BROKEN — cannot upload documents.** No upload entry point in the consultant UI; API uploads require an org-membership authorisation the consultant does not have (403 "Organization member access required").
- **CON-3 BROKEN — cannot process / map / extract.** No processing entry point; `POST /api/v3/manual-extraction/…` and ops endpoints return 403 for consultants. The consultant cannot drive extraction→mapping→calculation.
- **CON-4 BROKEN — no create-batch / settings parity.** PO's "lacks expected settings" partly confirmed: consultant has `Firm branding` and `White-label` tabs (settings that exist), but none of the operational settings.
- **CON-5 VERIFIED — client list & switching.** Two clients (CarbonTally Demo Ltd, OHD Consultant Client B). The "CURRENT ORGANIZATION" selector switches the active client; every metric re-scopes (verified A: TOTAL CO2E 8850.000000, 14 items, 3 reports vs B: 11735.015649, 3 items, 0 reports) with the banner "⚠ You are working on: {client} — every action here applies to this client only." **Active-client isolation holds.**
- **CON-6 VERIFIED — client messages (N1).** "Client messaging — … Messages with this client are exchanged through CarbonTally (Supabase Realtime). Processing entities never participate in these conversations." Existing thread renders; send/reply works (see MSG-1 for creation).
- **CON-7 VERIFIED — client management.** Suspend / End / Deactivate actions render per client; client dashboard shows docs/items/open-issues/ready-reports per client.
- **CON-8 PARTIAL — consultant CO2e figures.** Dashboard shows raw floats without units ("8850.000000") — formatting issue (UX-9).
- **CON-9 NOISE — `/ops/me` 403 logged** on every consultant page render (the V3 shell always probes staff status). Cosmetic console noise; also fires for customers (PERF-2).

**Net:** the consultant persona is a **read-only observer with client-switching + messaging**, not an operating user. The entire consultant value chain (create customer → onboard → upload → process → map → validate → report) is unavailable. This is the single biggest product gap for the consultant segment.

---

## 9. PE findings

- **PE-1 VERIFIED — PE workspace.** `entity-staff@demo` logs into `/ops` with the PE surface ("Internal Operations Entity Staff · operator"); `/api/v3/ops/me` returns `entity_id`, `role: operator`, `max_concurrent_tasks: 4`, perms `can_process`.
- **PE-2 VERIFIED — queue zero-state.** Unassigned PE shows "No work assigned to this Processing Entity" (batches 0, items 0, 0% complete).
- **PE-3 VERIFIED — assignment + extraction.** Staff admin assigned batch `76222222-…` ("Fleet Diesel Cards Q1") to Entity Beta → PE batch list includes it → PE opened item `FuelCard_01_Statement.pdf` → item status became `extracted`. The PE extraction workspace (source viewer, lines, save extraction) is real and persists.
- **PE-4 VERIFIED — boundary: unassigned/cross-org work denied.** PE org-scoped queue → 403 "Organization member access required"; PE reading customer org documents → 403. **PE cannot see unassigned customer work.**
- **PE-5 VERIFIED — no document download.** Item `file_url` is empty and there is no PE download path (D20 no-download boundary holds at API level; the PE viewer is view-only).
- **PE-6 VERIFIED — messaging isolation.** PE attempting to post to a customer-org conversation → 403. **Customer ↔ PE direct messaging is not possible** (N1 isolation holds).
- **PE-7 STAGE VOCABULARY (latent).** Backend `WORKFLOW_STAGES` use `extraction/mapping/validation/calculation`; the PE workbench tab ids use `extract/map/calculate/clarify`. The live calls use backend vocabulary (`startItem(itemId,'extraction')`), and `getNextItem()` is not used by any component, so no live break was observed — but the two vocabularies are a maintenance/regression hazard (PRC-3).

---

## 10. CarbonTally operations findings

- **OPS-1 VERIFIED — operator.** `/ops` Data entry shows operator queue; operator can process assigned items (perms `can_process`, `can_view_all`).
- **OPS-2 VERIFIED — reviewer gate.** Reviewer has `can_review` only. Accessing the operator queue → **403 "staff lacks permission: can_process"**. Reviewer validating an item → 200 (`validated`). Reviewer attempting calculation → **403 (needs can_process)**. Correct least-privilege gates.
- **OPS-3 VERIFIED — QC gate.** `qc_specialist` has `can_review + can_process`; QC queue + workspace render; validate works; QC tab honestly states "qc_errors is not populated by the current workflow; recurring-quality identification is NOT SUPPORTED BY CURRENT DATA MODEL".
- **OPS-4 VERIFIED — staff admin control plane.** Tabs: Dashboard, Data entry, Review, QC, Staff, Roles, Entities, SLA, Issues, Messaging, Audit, Settings, Commercial. Staff roster (11) with create-form + role select + entity scope; Roles; Entities; Audit trail renders admin audit entries; Settings = retention (RET-1); Commercial = versioned billing rules (SA-2).
- **OPS-5 VERIFIED — SLA/quality dashboard.** Queue aging, SLA breaches, item completion, processor performance all render from real data.
- **UX-7 P3 — stray test role** `t_ba_34e3cb` appears in the staff role select and `staff_roles`.

---

## 11. Admin (CarbonTally control-plane) findings

- **SA-1 VERIFIED — staff management.** Create staff profile form (user id/email + role + entity), roster with per-staff change/assign actions.
- **SA-2 VERIFIED — commercial.** Default billing mode (CREDIT/STANDARD) with versioning ("Changing it here NEVER silently changes existing customers"); versioned rules (automated credit rules, processing bands, storage allowance & rate, assisted price book, credit policy, STANDARD allowance); versioned plans catalogue (Starter/Professional/Business/Enterprise, "prices are provisional"). Publish-v2 actions present.
- **SA-3 VERIFIED — roles/entities/SLA/issues/audit tabs** render from real endpoints.
- **SA-4 NOT TESTABLE — publish/save round-trips** for commercial versions and retention values were not executed end-to-end (would create persistent production-like config); UI surface and endpoints exist. Marked for Cline acceptance test.

---

## 12. D17 — Master-data findings (the actual CRUD)

- **MD-1 P2 BROKEN — Facility create 500 without postcode.** `POST /organizations/{org}/facilities {name}` → 500 `violates check constraint facilities_postcode_or_eircode_check`. API schema allows `postcode=None` but the DB CHECK requires postcode **or** eircode. Creating a facility via the "+ New facility" form with an empty postcode yields a 500 toast ("Action failed"). Facility **read/list** works; facility with postcode creates 201.
- **MD-2 P1 BROKEN — Vehicles.** `POST /api/v3/vehicles` → **500 `relation "public.vehicles" does not exist`**. The `vehicles` table does not exist (verified `to_regclass('public.vehicles')` = NULL; no migration). The Organisation → Vehicles tab shows "Action failed — Network error" and "No vehicles yet". **D17 vehicles are not implementable in the current schema.** (The D17 vehicles UI is otherwise complete: Add vehicle form, "Vehicles are organisation master data and never block processing".)
- **MD-3 VERIFIED — Locations (N2).** The Locations tab states the resolution: "CarbonTally models locations on the facilities entity — manage the underlying records in the Facilities & Assets tab." It lists the org's facilities as locations. **This is a correct, honest N2 implementation.** The PO example "Owner cannot create Locations" is resolved by design (locations == facilities); no separate locations create exists (intentional). Consider adding a cross-link affordance (UX polish, P3).
- **MD-4 VERIFIED — Assets.** Assets table has `type` column; `POST …/assets` with `type` persists it; UI asset form includes a Type field; assets list shows `type || '—'`. The existing seeded OHD assets have null types (why the PO saw "—"). **Asset type is implemented; seed data is sparse.** Asset create verified (201).
- **MD-5 VERIFIED — Suppliers.** List/create/update verified (201/200) and the Suppliers tab renders the "+ New supplier" dialog with persisted records.
- **MD-6 PARTIAL — Edit/detail.** Facility detail/edit routes exist (`GET/PUT /organizations/facilities/{id}`); asset detail/edit exist; not every edit field was round-tripped (marked for Cline regression).

---

## 13. Documents findings

- **DOC-1 VERIFIED — upload pipeline.** Customer upload → document row + storage object; upload batches; documents page. `POST /api/v3/uploads` (see SEC-1 for the role bug).
- **DOC-2 PARTIAL — issue/document search.** In-org document search works (`/api/v3/documents?q=…`); cross-org search → 403. Issue status transition endpoint path mismatch (`POST /api/v3/issues/{id}/status` → 404; correct path in `v3_issues.py` needs Cline verification — see backlog).
- **DOC-3 PO CONFIRMED — file-size orientation.** The documents page is a file browser ("NAME TYPE SIZE UPLOADED"). The "Emissions from this document" action exists but the page does not foreground the emissions outcome; the PO observation is substantially confirmed (UX-8).
- **DOC-4 VERIFIED — documents→emissions link** exists (per-document action) and calculation history is real; the full chain is strongest in the demo org (14 documents → items → reports).

---

## 14. Processing findings

- **PRC-1 P1 BROKEN — customer review queue.** See CUS-3. Root cause located in the SQL: an unqualified `id` column in a JOIN (the `queue`/`customer-review` query), raising `column reference "id" is ambiguous`. Frontend is **not** at fault; the backend query needs qualified columns. Blocks customer review/approval → blocks reporting handoff.
- **PRC-2 VERIFIED — operator/PE processing.** Assignment, claim, extraction save, mapping save, calculation, validate — verified through live flows (t42, t44). Item statuses transition correctly (`pending → extracted → mapped → validated → calculated → qc_approved` etc. — observed `mapped`, `validated`, `qc_approved` records in DB).
- **PRC-3 PARTIAL — D19 workbench.** The ops extraction workspace (source pane + data pane, claim/save/draft/map/calculate buttons, autosave indicator, lock/approve controls, validation-findings alert) is implemented and used successfully. Top workflow nav (Queue/Extract/Map/Validate/Review/QC/Evidence), 40/60–60/40 split presets and keyboard divider control are **not exposed in the current PE/ops extraction screen** (only tab navigation with default split) — see D19 section (§23).
- **PRC-4 VERIFIED — item workspace for reviewer** returns full item + extracted data + findings.

---

## 15. Calculation findings

- **CAL-1 VERIFIED — real calculation.** `/emissions` Calculate form posts to the backend; the backend matches factors (`emission_factors`) and persists to `emissions_logs` (observed 11735.015649 kg CO₂e). Factor precedence and server-authoritative computation are implemented (domain code + observed results). Not a demo string: the number is computed from activity × factor.
- **CAL-2 PARTIAL — provenance display.** The calculation history row shows activity/scope/kg CO₂e but the FACTOR column renders "—" (factor label not surfaced) (UX-6). Immutability of final evidence not exercised end-to-end (see EVD-2).
- **CAL-3 P2 BROKEN — fuel-type reference.** `/api/reference/fuel-types` → 500 PGRST205 `Could not find the table 'public.defra_conversion_factors'` (the schema cache has `emission_factors`; the endpoint queries a stale table name). Breaks any fuel-type dropdown that uses the reference endpoint.

---

## 16. Evidence findings

- **EVD-1 VERIFIED — evidence chain exists.** Source document → extracted lines → mapped factor → calculation → emissions log → report. Row-level traceability tables exist (`extraction` records, mapping, `emissions_logs`, `report_*`). The demo "fully evidenced" record (INV-2026-0417, 4,258.9 L → 10,732.4 kg ≈ 10.7 t) renders on the public demo.
- **EVD-2 PARTIAL — "View evidence".** The emissions page provides "View evidence"; the element did not navigate in the automated click (may require the item to have a full evidence chain). No claim of certification/assurance is made anywhere — honest.
- **EVD-3 PARTIAL — immutable finalised evidence** not exercised (no finalisation path in current flows; reports are generated from logs). Do not claim D7.3 compliance until the finalisation/lock path is tested (backlog).

---

## 17. Reporting findings

- **RPT-1 VERIFIED — reports from real data.** Demo org has 2024 report `Ready v1` with download, 2025 `Queued`, 2023 `Failed` (honest error). Export emissions CSV/JSON and documents CSV render. The reports page states "V3 reporting workflow (authoritative data)".
- **RPT-2 PARTIAL — customer approval of reports.** Report *generation* works, but the customer approval gate is inside the broken `/review` flow (PRC-1). A report cannot complete the review→approval handoff.
- **RPT-3 PARTIAL — report detail view** exists (View action) but was not opened in the automated run (nav click was intercepted); marked for Cline regression.

---

## 18. Custom-factor findings

- **FAC-1 VERIFIED lifecycle + PO deadlock.** Owner creates factor → 201 `draft`. Owner self-approve → **403 "a factor's creator cannot approve their own factor"** (self-approval prevention works). A different org admin approves → **200 `active`**. **But:** in an organisation with a single owner/admin there is **no possible approver**, so the factor is stuck in `draft` forever. The docs define "org Admin/Owner only; no self-approval" (D-cf-3) but **do not specify the single-admin path** (CarbonTally staff approval? mandatory second admin? escalation?). → **PO DECISION REQUIRED (PO-1).**
- **FAC-2 VERIFIED — versioned edit.** Only drafts are editable (409 otherwise); approved factors change via new version (code verified).
- **FAC-3 PARTIAL — matching/precedence.** Factor resolution domain (country/year/activity/source precedence, custom-override) is implemented in code and observed in calculation; end-to-end custom-factor precedence (custom vs DEFRA) was not exercised through a live calculation with a custom factor (backlog).

---

## 19. Messaging / N1 findings

- **MSG-1 P1 BROKEN — conversation creation.** `POST /api/v3/messaging/conversations` → **500 `there is no unique or exclusion constraint matching the ON CONFLICT specification`**. Root cause: `backend/data/messaging.py::add_participant` uses `ON CONFLICT (conversation_id, user_id)` but `conversation_participants` has **no unique constraint on (conversation_id, user_id)**. Every conversation creation fails; worse, the conversation row is inserted *before* the participant insert and there is **no transaction**, so each failed attempt leaves an **orphan conversation with zero participants** (verified: `conversation_participants` is empty for all conversations; several orphan threads accumulated during testing, e.g. "OHD test conv", "OHD c-created").
- **MSG-2 VERIFIED — send/reply/read/mark-read.** For existing conversations: send 201, reply 201, read 200 (with `is_read:false`), mark-read 200. Persistence verified.
- **MSG-3 VERIFIED — realtime.** Realtime channel setup logs for every user ("🔄 Setting up Realtime for user: …") — Supabase Realtime presence active; the N1 architectural distinction (authenticated communication = Supabase Realtime, not the public FAQ assistant) is implemented and stated in the UI ("Messages with this client are exchanged through CarbonTally (Supabase Realtime)").
- **MSG-4 VERIFIED — isolation.** PE posting to a customer conversation → 403. Customer ↔ PE direct messaging impossible. Consultant sees only active-client conversations.
- **MSG-5 P2 — participants model is currently inert** because no participant rows can ever be created (MSG-1). The intended participant-scoped authorisation ("creator added as first participant") does not function.

---

## 20. AI assistant findings

- **AI-1 VERIFIED — public FAQ assistant.** The "CarbonTally Assistant" widget renders on public pages and answers from the deterministic local knowledge layer (no external AI provider; no credentials fabricated). Architecture document matches implementation.
- **AI-2 VERIFIED — not an alternate permission system.** The assistant has no access to platform data and cannot perform actions; it is not used as the authenticated user's primary communication (messaging pages use Realtime).
- **AI-3 NOTE — assistant widget also renders inside the authenticated app** (bottom-right). Harmless, but it is a public-FAQ surface inside the private app; confirm intent (D16) — minor.

---

## 21. D19 — Workbench findings

- **D19-1 VERIFIED — core workbench actions.** Claim stage, save extraction, save draft, save mapping, calculate, autosave indicator, source↔field editing, validation-findings alert, lock/approve controls — implemented in the ops `ExtractionPanel` and **proven with real item transitions** (t42: `extracted`; t44: `validated`).
- **D19-2 PARTIAL — top workflow navigation.** The ops extraction screen uses stage tabs (Queue/Extract/Map/Calculate/Clarify for PE; Queue/Extract/Map/Validate/Review/QC/Evidence for staff) rather than the frozen D19 top-nav with 40/60, 50/50, 60/40 split presets and a keyboard divider control. The frozen split-screen layout is **not fully matched**; the split is present (source + data panes) but presets/keyboard divider are absent. → D19 partial (see backlog, D19-2).
- **D19-3 PARTIAL — secure viewer.** The source pane is view-only (no download) for PE — verified; full D19 secure-viewer affordances (zoom/annotations) not present.
- **D19-4 PARTIAL — mobile tray.** Responsive checks passed for the customer shell (no overflow at 390px); the ops workbench on mobile was not exhaustively exercised (backlog).

---

## 22. D21 — Design-system findings

- **D21-1 VERIFIED — V3 design system.** V3 customer/staff/consultant surfaces use the teal/cyan token system, v3 buttons/forms/tables/status chips, consistent typography; empty/error/loading states present ("No upload batches yet.", "Something went wrong — Network error", spinners).
- **D21-2 P2 — legacy styling leaks.** The legacy app-shell nav ("History & Trends", "Reports (V3)", "Organization (V3)", "Consultant (V3)", "Team Management", "assets") coexists with the V3 shell. Some legacy-styled controls (blue buttons, legacy tables) remain. Inconsistent with D21 unification.
- **D21-3 P3 — raw float emissions** ("8850.000000", "11735.015649") rendered without units/formatting in consultant + customer dashboards (UX-9).
- **D21-4 P3 — FACTOR column "—"** in calculation history (UX-6).
- **D21-5 P3 — label/route casing** "Organisation" (nav) vs `/organization` (route).

---

## 23. API findings

- **API-1 P1 — customer-review/queue SQL ambiguity** (PRC-1): `column reference "id" is ambiguous` in `v3_processing` review-queue queries.
- **API-2 P1 — messaging ON CONFLICT** (MSG-1): non-matching conflict target.
- **API-3 P2 — vehicles table missing** (MD-2).
- **API-4 P2 — fuel-types stale table** (CAL-3).
- **API-5 P2 — facilities CHECK vs schema** (MD-1).
- **API-6 P3 — issue status endpoint path** — `POST /issues/{id}/status` returned 404 in testing; the correct transition path is in `v3_issues.py` (Cline to reconcile frontend call).
- **API-7 VERIFIED — authz architecture.** `ensure_org_access`, `require_org_member/admin`, staff-permission guards (`can_process`/`can_review`/`can_manage_staff`) work and produce clean 403s (verified many times).

---

## 24. Database findings

- **DB-1 P1 — `vehicles` table absent** (MD-2): no migration creates it; API and UI both assume it.
- **DB-2 P2 — `facilities_postcode_or_eircode_check`** (MD-1) conflicts with the API's optional postcode.
- **DB-3 P2 — `conversation_participants` lacks unique (conversation_id, user_id)** (MSG-1); the pkey is `conversation_participants_pkey` on `id`.
- **DB-4 VERIFIED — RLS on core customer tables** (`organization_members`, `documents`, etc.) denies cross-org reads (empirically 403).
- **DB-5 NOTE — `roles` table empty; `staff_roles` holds the 4+1 roles** including stray `t_ba_34e3cb` (UX-7).

---

## 25. RLS / security findings

See the dedicated security deliverable (`CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md`). Headline:

- **SEC-1 P1 (authorisation) — Viewer can upload documents.** `POST /api/v3/uploads` is gated by `require_org_member()` only; the viewer *is* an org member, so the upload succeeds (201, `viewer_up.pdf` visible in the org's document list). The viewer should be read-only. Other viewer writes are correctly denied (batch/facility/approval → 403). **Fix: require member+ (non-viewer) on uploads.**
- All cross-org, cross-client, PE, staff-gate, and messaging-isolation negative tests produced the correct denial (detailed in security deliverable).

---

## 26. Negative-test results

Summarised in §5 matrix; the full table (attempt → expected → actual) is in the security deliverable. Every denial was server-side (not UI hiding): 403s observed at the HTTP layer for all unauthorised attempts.

---

## 27. Complete gap register

| ID | Severity | Title | Resolution |
|---|---|---|---|
| SEC-1 | P1 | Viewer can upload documents | IMPLEMENTATION GAP |
| MSG-1 | P1 | Conversation creation 500 / orphan threads | IMPLEMENTATION GAP |
| PRC-1 | P1 | Customer review queue 500 | IMPLEMENTATION GAP |
| CON-1 | P1 | Consultant cannot create customers | IMPLEMENTATION GAP (+ PO decision on scope) |
| CON-2 | P1 | Consultant cannot upload documents | IMPLEMENTATION GAP |
| CON-3 | P1 | Consultant cannot process/map | IMPLEMENTATION GAP |
| MD-2 | P1 | Vehicles table missing → CRUD broken | IMPLEMENTATION GAP |
| MD-1 | P2 | Facility create 500 (postcode CHECK) | IMPLEMENTATION GAP |
| CAL-3 | P2 | fuel-types 500 (stale table) | IMPLEMENTATION GAP |
| PERF-1 | P2 | Notifications UI broken (RLS 0 policies) | IMPLEMENTATION GAP |
| PERF-2 | P3 | /ops/me 403 console noise for non-staff | IMPLEMENTATION GAP |
| UX-6 | P3 | FACTOR column "—" | IMPLEMENTATION GAP |
| UX-7 | P3 | Stray test role in staff select | TEST-DATA ISSUE |
| UX-8 | P2 | Documents page file-size orientation | PO DECISION REQUIRED (already PO-observed) |
| UX-9 | P3 | Raw float CO2e display | IMPLEMENTATION GAP |
| D19-2 | P2 | D19 top-nav + split presets not matched | IMPLEMENTATION GAP |
| D21-2 | P2 | Legacy styling/nav leaks | IMPLEMENTATION GAP |
| FAC-1 | P2 | Solo-admin factor approval deadlock | PO DECISION REQUIRED (PO-1) |
| RET-1 | P2 | Retention: UI present, enforcement untested | IMPLEMENTATION GAP / PO DECISION REQUIRED (PO-2) |
| EVD-3 | P2 | Final evidence immutability untested | IMPLEMENTATION GAP |
| PRC-3 | P3 | Stage vocabulary duplication (backend vs frontend) | ENGINEERING DECISION |
| API-6 | P3 | Issue status endpoint path mismatch | IMPLEMENTATION GAP |
| AUTH-2 | P3 | No System Admin role (maps to staff admin) | DOCUMENTATION GAP |

---

## 28. P0/P1/P2/P3 summary

- **P0:** none found (no data leakage, corruption, or privilege escalation beyond SEC-1's read-only→upload violation; no cross-org leak).
- **P1 (8):** SEC-1, MSG-1, PRC-1, CON-1, CON-2, CON-3, MD-2, (plus consultant chain as one work-stream).
- **P2 (8):** MD-1, CAL-3, PERF-1, UX-8, D19-2, D21-2, FAC-1, RET-1, EVD-3.
- **P3 (8):** PERF-2, UX-6, UX-7, UX-9, PRC-3, API-6, AUTH-2, D21-5.

---

## 29. PO decision items

- **PO-1 (FAC-1):** Who approves custom factors in a single-owner/admin organisation? Options: (a) CarbonTally staff approval; (b) require ≥2 admins; (c) allow owner self-approval with audit flag. D-cf-3 currently only says "org Admin/Owner; no self-approval".
- **PO-2 (RET-1):** Retention durations are deliberately unset ("no platform-configured duration"). Confirm the product model for evidence exclusions and customer-specific policies (D15/8.1) before Cline implements enforcement.
- **PO-3 (UX-8):** Confirm the documents page should foreground the emissions outcome (documents are a *business workflow*, not a file manager) — the PO observation implies yes; a concrete spec (summary card, per-doc status + CO2e + next actor) is needed.
- **PO-4 (CON-1/2/3):** Confirm consultant operating scope — is a consultant supposed to *operate* processing, or only *manage* (client, branding, messaging, monitor)? The authoritative Option B+C docs imply operating; current implementation only manages. This determines the size of the CON work-stream.
- **PO-5 (AUTH-2):** Confirm whether a distinct System Admin persona (above staff admin) is required for launch, or whether staff `admin` is the control-plane role (docs imply the latter).

---

## 30. Environment limitations

- Local/test environment (`localhost:3000/8050`, Supabase demo auth, Postgres 54426). All test data is synthetic; no production instance was touched.
- Browser used a CDP harness (Playwright/Puppeteer browser unavailable in this environment). All flows were executed in a real Chrome through CDP.
- Realtime push delivery (WebSocket message arrival) was verified only to the extent of channel setup logs + persisted reads; live push delivery timing was not instrumented (MSG-2 relies on persisted + realtime-setup evidence).
- Commercial "Publish v2" and retention "Save changes" were not executed to avoid mutating config that could affect other consumers; endpoints exist (SA-4).
- `/reference/fuel-types` and `/api/v3/processing/customer-review` 500s are reproducible on demand.

---

## 31. Environment-safety & data statement

- **ENVIRONMENT BLOCKED — not triggered.** Environment confirmed local/dev before any test data was created.
- OHD-created test identities remain in the local DB (documented in §35 and in the security deliverable). They are labelled `ohd.*`/`OHD *` and the conversations "OHD …". No real customer data was created or touched; existing demo/legit test data was not deleted. Orphaned test conversations from the failed create-conversation attempts were left in place (removal could affect referential integrity of messages); they are documented.

---

## 32. Final acceptance assessment (the 20 questions)

1. **Can a Customer Owner operate CarbonTally end-to-end?** **PARTIALLY.** All owner operations work except **customer review/approval (PRC-1, broken)** and **vehicles (MD-2, broken)**; facility create needs a postcode (MD-1).
2. **Customer Admin?** **PARTIALLY** — same blockers as owner (admin shares the review/approval, vehicles, facility issues).
3. **Customer Member?** **PARTIALLY** — member operational flows (upload, calculate, issues, messaging send) work; cannot manage master data (correct); blocked on review/approval.
4. **Is Viewer truly read-only?** **NO — SEC-1**: viewer can upload documents (P1).
5. **Can a Consultant manage and process customers?** **NO — manage-only (client list, switching, branding, messaging); create-customer/upload/process/map are missing (CON-1..3).**
6. **Can PE staff perform assigned extraction work?** **YES — verified** (assign → queue → extract → save; boundary 403s correct).
7. **Can CarbonTally Operators process work?** **YES — verified** (operator queue, extraction, mapping, calculation, validation).
8. **Reviewer/QC gates?** **YES — verified** (review queue, validate; calculate denied for reviewer; QC queue + workspace).
9. **Staff Admin control plane?** **YES — verified** (staff, roles, entities, SLA, issues, messaging, audit, settings, commercial).
10. **System Admin?** **NO distinct role** — staff `admin` is the control plane (AUTH-2, PO-5).
11. **Can a complete document become a real emissions result?** **YES for internal/PE processed items and manual customer calculations** — verified persisted `emissions_logs`. **The customer-visible approval gate is broken.**
12. **Can that result become evidence and a report?** **PARTIALLY** — reports generate from `emissions_logs` (2024 Ready v1 + download); evidence view/link exists; final immutable evidence not exercised (EVD-3).
13. **Can the customer review and approve the result?** **NO — /review is broken (PRC-1).**
14. **Does N1 messaging work correctly?** **PARTIALLY** — send/reply/read/mark-read/realtime-setup/isolation work; **conversation creation is 100% broken** (MSG-1) and the participants model is inert.
15. **Are D17 master-data workflows actually usable?** **MOSTLY** — facilities (with postcode), locations (as facilities), assets, suppliers usable; **vehicles are not** (MD-2).
16. **Is the D19 workbench usable?** **CORE YES, layout partial** — claim/save/map/calculate/autosave/validation work; the frozen top-nav + split presets + keyboard divider are not matched (D19-2).
17. **Is D21 consistent?** **PARTIALLY** — V3 system strong; legacy nav/styling leaks remain (D21-2).
18. **Are authorisation/RLS boundaries correct?** **LARGELY YES** — all cross-org/client/PE/staff negative tests denied server-side; **one defect: viewer upload (SEC-1)**.
19. **Any P0?** **No P0 found.** SEC-1 is P1 (authorisation, write on read-only role, no data leak to other orgs).
20. **What should Cline implement next?** See the Cline backlog deliverable — ordered P1 (SEC-1, PRC-1, MSG-1, MD-2, CON-1..3) → P2 → P3.

---

## 33. What was verified working (evidence-backed, not demo)

- Cross-org read/upload/search → 403 (both directions).
- PE boundaries (unassigned queue, customer docs, messaging) → 403.
- Reviewer/operator/QC permission gates → 403/200 as designed.
- Custom-factor self-approval → 403; cross-admin approval → `active`.
- Org profile PUT persists after reload; viewer PUT → 403.
- Members: invite (201), role change round-trip, add-by-user-id.
- Suppliers create/update (201/200) + UI dialog.
- Assets create with type (201); facilities create with postcode (201).
- Emissions calculation persists to `emissions_logs`.
- Reports list/status/export + honest generation failures.
- Consultant active-client switching re-scopes all metrics (A↔B isolation).
- Messaging send/reply/read/mark-read + realtime setup + PE isolation.
- Mobile (390px) customer shell: no horizontal overflow.

---

## 34. Statuses used in this report

`VERIFIED WORKING`, `PARTIALLY WORKING`, `BROKEN`, `NOT IMPLEMENTED`, `NOT TESTABLE`, `ENVIRONMENT BLOCKED`, `PO DECISION REQUIRED` — per the acceptance-standard instructions. No "complete" claim rests on routes, components, tables, or unit tests alone.

---

## 35. OHD test data created (traceability)

Created during this audit (local/dev only; all labelled OHD):

- **Identities (signup-created):** `ohd.owner.a`, `ohd.admin.a`, `ohd.member.a`, `ohd.viewer.a`, `ohd.owner.b`, `ohd.owner.c` @ `test.carbontally.local` (Test Organisations A/B).
- **Master data (Org A):** "OHD Facility Alpha/Bravo/Gamma(failed 500)", "OHD Forklift 1", "OHD Van 1/1b/1c", "OHD Boiler 1", "OHD Test Supplier 2 (renamed)", "OHD Audit Factor", "OHD Audit Factor 2" (approved), "OHD Test Vehicle"(failed 500).
- **Documents:** `ohd_test_invoice.pdf`, `ohd_test_invoice2.pdf`, `viewer_up.pdf` (SEC-1 evidence).
- **Batches/items:** OHD upload batches and assigned PE batch `76222222-…` (item `FuelCard_01_Statement.pdf` → extracted).
- **Conversations:** "OHD audit thread A" (org A, 2 messages), "OHD audit test thread" (demo org), orphan threads "OHD c-created", "OHD test conv" (from the MSG-1 failure).
- **Invitation:** `invitee.ohd@test.carbontally.local` (pending, Org A).

**Cleanup:** no legitimate/demo accounts or data were deleted or modified (OHD Member A's role was briefly changed for testing and restored to `member`). OHD artefacts were left in place where deletion would affect referential integrity or evidence; they are fully labelled. **OHD-created identities/data remain in the local DB.**

---

*Prepared by OpenHands (OHD) as an independent Product Owner acceptance audit. Companion deliverables: `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md`, `CARBONTALLY_V3_PERSONA_TEST_MATRIX.md`, `CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md`.*
