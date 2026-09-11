# CarbonTally V3 — Cline Implementation Backlog

**Source:** Full Persona Acceptance Audit, 2026-08-28 (OHD). Each item is actionable without re-running the audit. Implement in the order given (P1 → P2 → P3). Do not start a downstream item until its upstream dependency is done.

**Legend — affected layer:** FE = Frontend, BE = Backend, API = HTTP contract, DB = Database/schema/migration, RLS = Row-Level Security policies, ST = Storage, CFG = Configuration, T = Tests, DOC = Documentation.

**Golden rule for the auditor-approved items:** none of these items may be "fixed" by hiding UI. Every fix must be verifiable at the API/DB layer.

---

## P0

*No P0 items. No data-leakage, corruption, or privilege-escalation defect was found. The closest candidate (SEC-1) is P1: an authorisation gap (write on a read-only role), not a leak.*

---

## P1 — Security / authorisation / broken core business workflows

### CL-01 Viewer can upload documents (authorisation gap)
- **Finding:** SEC-1. **Role:** Customer Viewer. **Workflow:** Viewer document upload. **Screen:** `/documents`.
- **Expected:** Viewer (read-only role) is denied every write operation server-side.
- **Actual:** `POST /api/v3/uploads` returns **201** for a viewer; the file appears in the org document list (`viewer_up.pdf` observed in Org A). Viewer batch/facility/approval writes are correctly 403 — only uploads are affected.
- **Root cause:** `POST /api/v3/uploads` authorises with `require_org_member()`; the viewer *is* an org member. No member-role check (`viewer` excluded) on the upload path.
- **Required change:** Gate uploads to non-viewer roles (member/admin/owner). Either add a `require_org_contributor()` (member+) guard to `api/v3_uploads.py`, or check `member.role != 'viewer'` inside the endpoint after membership resolution. Do the same for any other write endpoint that currently accepts `require_org_member()` but should exclude viewers (audit the full endpoint list for `require_org_member()` write paths — uploads is the confirmed one).
- **Affected layer:** BE + API (+ T).
- **Dependencies:** none.
- **Security implications:** closes the read-only-role write gap; prevents viewers from polluting org data.
- **Acceptance criteria:** (1) viewer `POST /api/v3/uploads` → 403; (2) member/admin/owner upload → 201; (3) existing viewer-uploaded test rows remain readable by members (no purge required).
- **Regression tests:** API test viewer-upload-denied; UI test viewer sees read-only documents page.
- **PO decision required?** NO (D1 roles model: viewer = read-only).
- **Authoritative source:** D1 one-account-one-role; role descriptions in `organization_members` constraint (`viewer` = read-only).

### CL-02 Customer review & approval queue is broken (500)
- **Finding:** PRC-1. **Role:** Customer Owner/Admin (and any customer). **Workflow:** Review & approve processed items → report. **Screen:** `/review` ("Review & approve").
- **Expected:** Customer sees items awaiting review and can approve/reject; approving flows the item into the report pipeline.
- **Actual:** `/review` renders "Something went wrong — Network error". `GET /api/v3/processing/customer-review?organization_id=…` and `GET /api/v3/processing/queue?organization_id=…&stage=review` → **500 `column reference "id" is ambiguous`**.
- **Root cause:** the review-queue SQL joins tables where `id` is unqualified (backend query in the processing review-queue path). Frontend is not at fault.
- **Required change:** locate the queue/customer-review SQL (in `backend/domain/…`/`backend/data/…` used by `api/v3_processing.py`) and qualify every `id` with its table alias; verify the query returns the review queue correctly. Add a regression test that hits both endpoints.
- **Affected layer:** BE + API (+ T).
- **Dependencies:** none.
- **Security implications:** none (availability).
- **Acceptance criteria:** (1) both endpoints return 200 with the correct review-queue items for an org that has `review`-stage items; (2) `/review` page loads; (3) approve/reject action on a review item returns 200 and transitions the item status.
- **Regression tests:** API tests for `customer-review` and `queue?stage=review` with a seeded review-stage item; UI test for `/review`.
- **PO decision required?** NO (D18 workflow; review/approve is in the master workflow map).
- **Authoritative source:** `MASTER_WORKFLOW_MAP.md` (CUSTOMER REVIEW → CUSTOMER APPROVAL); D18.

### CL-03 Messaging conversation creation always fails (500)
- **Finding:** MSG-1. **Role:** all personas (customer, consultant, staff). **Workflow:** N1 messaging — create a new conversation. **Screen:** `/messaging` ("Start" / new-thread action).
- **Expected:** Creating a conversation returns 201, records the creator as a participant, and the thread appears in conversation lists for authorised actors.
- **Actual:** `POST /api/v3/messaging/conversations` → **500 `there is no unique or exclusion constraint matching the ON CONFLICT specification`**. Because the conversation row is inserted before the failing participant insert and there is **no transaction**, each attempt leaves an **orphan conversation with zero participants** (verified: `conversation_participants` is empty; orphan threads "OHD test conv", "OHD c-created" accumulated during testing).
- **Root cause:** `backend/data/messaging.py::add_participant` executes `INSERT … ON CONFLICT (conversation_id, user_id) DO UPDATE …` but `conversation_participants` has **no unique constraint on `(conversation_id, user_id)`** (its pkey is `conversation_participants_pkey` on `id`). Postgres rejects the ON CONFLICT target at plan time.
- **Required change:** (a) add a unique index `UNIQUE (conversation_id, user_id)` on `conversation_participants` (new migration) — matches the repo's upsert semantics; AND (b) wrap create-conversation (and message-insert if any) in a transaction so a participant failure cannot leave an orphan; AND (c) clean up existing orphan conversations (subjects "OHD test conv", "OHD c-created", and any row with 0 participants) if the PO approves (they are OHD test artefacts).
- **Affected layer:** BE + DB (+ API + T).
- **Dependencies:** none.
- **Security implications:** restores the participant model that N1 isolation relies on; prevents orphan accumulation.
- **Acceptance criteria:** (1) owner creates conversation → 201 with participant row; (2) consultant creates conversation in an active client org → 201; (3) entity-staff create → 403 (unchanged); (4) no new orphan rows after failed attempts; (5) conversation lists and read/unread still work.
- **Regression tests:** API tests for create-conversation (owner/consultant/staff/PE), participant uniqueness (re-adding participant upserts), no-orphan assertion.
- **PO decision required?** NO (N1 frozen: Supabase Realtime messaging).
- **Authoritative source:** N1; `MASTER_UX_DECISION_RECONCILIATION_REPORT.md`; `backend/data/messaging.py`.

### CL-04 Vehicles master data is non-functional (missing table)
- **Finding:** MD-2. **Role:** Customer Owner/Admin. **Workflow:** D17 vehicles CRUD. **Screen:** `/organization` → Vehicles tab.
- **Expected:** Owner can create, list, edit, archive vehicles.
- **Actual:** Vehicles tab shows "Action failed — Network error" and "No vehicles yet". `POST /api/v3/vehicles` → **500 `relation "public.vehicles" does not exist`**; `GET /api/v3/vehicles` → 500; verified `to_regclass('public.vehicles')` is NULL — **no migration creates the table**.
- **Root cause:** schema/migration gap — `api/v3_vehicles.py` (GET/POST/PUT/DELETE) assumes a `vehicles` table that was never created.
- **Required change:** create a `vehicles` migration matching `api/v3_vehicles.py` expectations (vehicle: id, organization_id, name, registration, make, model, year?, status, is_active, created_at, updated_at; org FK; RLS policies mirroring `facilities` — org-scoped select/insert/update/delete for member/admin). Wire RLS so viewers can read but not write. Ensure the frontend `VehiclesTab` create payload matches the API schema (it sends `name`+`registration`+`make`+`model`; confirm field names against the create model).
- **Affected layer:** DB + RLS + BE + API (+ FE check) (+ T).
- **Dependencies:** none.
- **Security implications:** ensure RLS on the new table is org-scoped (copy the facilities pattern); verify cross-org denial.
- **Acceptance criteria:** (1) owner creates a vehicle → 201 and it renders in the tab; (2) viewer can read but vehicle create → 403; (3) cross-org vehicle read → 403; (4) edit/archive work; (5) no UI "Network error".
- **Regression tests:** API CRUD + RLS negative tests for vehicles.
- **PO decision required?** NO (D17 vehicles are in the frozen master-data set).
- **Authoritative source:** D17; `MASTER_SCREEN_INVENTORY.md` (Organisation → Vehicles); `MASTER_UI_UX_ASCII_DESIGNS.md`.

### CL-05 Consultant cannot create customers
- **Finding:** CON-1. **Role:** Consultant. **Workflow:** Client list → create customer. **Screen:** `/consultant` (client list).
- **Expected:** Consultant can onboard a new customer organisation (create org + link as client) from the UI.
- **Actual:** No "Add client/new customer" action anywhere in the consultant UI. `POST /api/v3/consultants/me/clients` requires an existing `organization_id` (422 otherwise) — it only links pre-existing orgs. `POST /api/v3/organizations` exists (D35 self-service; any authenticated user) but creates the caller as OWNER and is not exposed to consultants.
- **Root cause:** missing consultant-side customer-creation flow — no UI entry point; clients API links only; org-create endpoint has no consultant-specific path.
- **Required change (depends on PO-4 in the audit — consultant operating scope):** implement an "Add client" flow in `/consultant`: (a) consultant calls org-create with a consultant context so the new org's initial owner is a customer placeholder or the consultant is granted a consultant-grant rather than ownership (PO decision); (b) then create the client link with `organization_id`. If PO confirms consultants should not create orgs directly (PO-4 = manage-only), this becomes a scoping decision rather than an implementation. **Implement only after PO-4.**
- **Affected layer:** FE + BE + API (+ DB if grants change) (+ T).
- **Dependencies:** PO-4 (audit §29) — the consultant operating model.
- **Security implications:** a consultant must never become an org OWNER (would break the one-account-one-role model and grant them customer-admin powers).
- **Acceptance criteria:** (1) consultant UI offers "Add client"; (2) flow creates a new org and links it as a client; (3) new org's membership/roles are correct (no consultant=owner); (4) the new client appears in the client list and is selectable.
- **Regression tests:** consultant create-customer API + UI; role assertion on the new org.
- **PO decision required?** YES (PO-4) — the fix shape depends on the consultant operating model.
- **Authoritative source:** D14 (consultant acquisition); `MASTER_WORKFLOW_MAP.md` (consultant lifecycle); Option C docs.

### CL-06 Consultant cannot upload documents
- **Finding:** CON-2. **Role:** Consultant. **Workflow:** client document upload. **Screen:** `/consultant` (client workspace — expected "Documents").
- **Expected:** Consultant uploads documents into the active client's document store.
- **Actual:** No upload UI for consultants; API uploads → 403 "Organization member access required" (consultants are not org members).
- **Root cause:** upload endpoint authorises org members only; consultants hold an active-grant on the client org, not membership. No consultant-scoped upload path exists.
- **Required change:** extend the upload path to accept consultants with an active grant for the target org (mirror how messaging `_authorize_org_actor` accepts "org member or active-grant consultant"), and add a Documents/Upload surface in the consultant client workspace. Enforce the active-client scope (uploads land in the *active* client's org only).
- **Affected layer:** BE + API + FE (+ T).
- **Dependencies:** CL-05/PO-4 (consultant operating model).
- **Security implications:** the active-grant check must be identical to messaging's (revoked/suspended clients denied); verify cross-client upload denial when Client B is active targeting Client A.
- **Acceptance criteria:** (1) consultant uploads into active client → 201; (2) upload into inactive/other client → 403; (3) document appears under the correct org; (4) customer members see the consultant-uploaded document.
- **Regression tests:** consultant upload (active/inactive client), cross-client denial.
- **PO decision required?** YES (tied to PO-4).
- **Authoritative source:** D14; N1 active-grant pattern; `MASTER_WORKFLOW_MAP.md` (DOCUMENT UPLOAD step for consultants).

### CL-07 Consultant cannot process / map
- **Finding:** CON-3. **Role:** Consultant. **Workflow:** batch creation → processing → extraction → mapping for the active client. **Screen:** `/consultant` client workspace (expected "Processing").
- **Expected:** Consultant can create batches from uploaded documents, run/perform extraction and mapping for the active client.
- **Actual:** No processing/mapping UI for consultants; `POST /api/v3/manual-extraction/batches` → 403; ops endpoints → 403.
- **Root cause:** processing endpoints are scoped to org members or internal staff; consultant active-grants are not honoured on processing paths.
- **Required change:** (a) honour active-grant consultants on the batch/processing surfaces scoped to the active client (same grant check as CL-06); (b) add batch-create + processing/mapping UI to the consultant client workspace (or reuse the ops ExtractionPanel in consultant mode, matching D19 for consultants); (c) enforce active-client scoping on every consultant processing call.
- **Affected layer:** FE + BE + API (+ T).
- **Dependencies:** CL-06 (documents must be uploadable before batches exist), PO-4.
- **Security implications:** grant-check must be per-request with active-client scoping; cross-client batch access must be 403.
- **Acceptance criteria:** (1) consultant creates a batch from an active-client document → 201; (2) extraction/mapping for the active client persists item statuses; (3) attempts against the inactive client → 403; (4) the client dashboard's processing status reflects the new items.
- **Regression tests:** consultant batch create + item transition + cross-client denial.
- **PO decision required?** YES (tied to PO-4).
- **Authoritative source:** D14; D19; `MASTER_WORKFLOW_MAP.md`.

---

## P2 — Important functionality / UX

### CL-08 Facility create fails without postcode/eircode
- **Finding:** MD-1. **Role:** Owner/Admin. **Workflow:** D17 facility create. **Screen:** `/organization` → Facilities & Assets → "+ New facility".
- **Expected:** Creating a facility with only a name succeeds (postcode is optional in the UI).
- **Actual:** `POST /organizations/{org}/facilities {name}` → **500 `violates check constraint facilities_postcode_or_eircode_check`**; the UI shows a 500 toast.
- **Root cause:** API schema `FacilityCreate.postcode: Optional[str]` conflicts with DB CHECK `postcode IS NOT NULL OR eircode IS NOT NULL`.
- **Required change (pick one, engineer + PO):** (a) relax the DB CHECK to allow null postcode+eircode (locations without addresses exist), or (b) require postcode/eircode in the API schema with a 422 + clear UI validation. Prefer (a) with a migration, matching "locations are facilities" (N2) where sites may have no postcode.
- **Affected layer:** DB (+ BE validation) (+ FE validation) (+ T).
- **Dependencies:** none.
- **Security implications:** none.
- **Acceptance criteria:** (1) facility create without postcode → 201 (or a clear 422, depending on the chosen option); (2) with postcode → 201; (3) facility list/detail render.
- **Regression tests:** facility create (no postcode / with postcode), UI toast assertion.
- **PO decision required?** NO for the bug; the chosen option is an engineering decision. Authoritative: N2 locations==facilities.
- **Authoritative source:** N2; D17.

### CL-09 Fuel-type reference endpoint 500
- **Finding:** CAL-3. **Role:** all (fuel-type dropdowns). **Workflow:** any screen using the fuel-type reference list.
- **Expected:** fuel-type list returns 200.
- **Actual:** `GET /api/reference/fuel-types` → **500 PGRST205 `Could not find the table 'public.defra_conversion_factors'`**.
- **Root cause:** the reference endpoint queries a stale table name; the schema cache has `emission_factors`.
- **Required change:** point the fuel-type query at the current factors table (or introduce a stable `fuel_types` view), keeping the public contract.
- **Affected layer:** BE + API (+ T).
- **Dependencies:** none.
- **Acceptance criteria:** endpoint returns 200 with the fuel-type list; downstream dropdowns populate.
- **Regression tests:** reference endpoint 200; no PGRST205.
- **PO decision required?** NO.
- **Authoritative source:** D-cf factor-source model; `emission_factors` table.

### CL-10 Notifications feature broken for all users
- **Finding:** PERF-1. **Role:** all. **Workflow:** notifications bell/list/unread. **Screen:** app shell (bell + `/notifications`).
- **Expected:** Users see their notifications and unread count.
- **Actual:** Every page logs `Error fetching notifications: Object`; the bell never populates. The backend `/api/v3/notifications` returns 200 (empty for the test user), but the UI **does not use it** — `frontend/src/context/RealtimeContext.jsx` queries Supabase directly via `supabase.from('notifications').select('*')`, which fails because **`notifications` has RLS enabled with zero policies** (deny-everything).
- **Root cause:** RLS misconfiguration (table RLS on, no policies) + frontend bypassing the API.
- **Required change:** (a) add RLS policies to `notifications` (user reads own notifications; service-role writes; `is_read` update by owner); or (b) switch the frontend to the working `/api/v3/notifications` endpoint. Prefer (b) + (a) for defence-in-depth.
- **Affected layer:** RLS + DB (+ FE).
- **Dependencies:** none.
- **Security implications:** RLS-on-no-policies is currently safe (deny), but any future `FORCE ROW LEVEL SECURITY` off or bulk-import could expose cross-user rows; adding policies is the correct hardening.
- **Acceptance criteria:** (1) notification select via user JWT returns the user's rows; (2) unread count renders; (3) no console error; (4) cross-user notification read denied.
- **Regression tests:** RLS policy test (own rows only); frontend notification render.
- **PO decision required?** NO.
- **Authoritative source:** N1 (notifications are part of authenticated communication); audit evidence.

### CL-11 Documents page: foreground the emissions outcome
- **Finding:** UX-8 / DOC-3. **Role:** customer. **Workflow:** document → emissions. **Screen:** `/documents`.
- **Expected:** Documents are presented as a business workflow (status, per-document emissions result, next actor), not a file browser.
- **Actual:** page shows NAME/TYPE/SIZE/UPLOADED + a per-doc "Emissions from this document" link; size is the emphasised metadata.
- **Required change:** add a per-document status/emissions summary (calculated CO2e where the item is calculated, processing stage, next actor) while keeping upload; show "no emissions yet" honestly where none exist. (Spec-level confirmation via PO-3.)
- **Affected layer:** FE (+ minor BE if status aggregation needed).
- **Dependencies:** none.
- **Acceptance criteria:** (1) each document shows its processing/emissions state; (2) documents without emissions state so honestly; (3) existing upload flow unchanged.
- **Regression tests:** document list render with new fields; empty-state.
- **PO decision required?** YES (PO-3) — confirms the desired presentation spec.
- **Authoritative source:** task §12 ("documents as a business workflow, not a file manager"); `MASTER_UX_RECOMMENDATION.md`.

### CL-12 D19 split-screen workbench: top nav + split presets
- **Finding:** D19-2. **Role:** operator/PE/QC. **Workflow:** processing workbench. **Screen:** `/ops` Data entry / PE extraction.
- **Expected (D19 frozen):** top workflow navigation (Queue→Extract→Map→Validate→Review→QC→Evidence), split presets 40/60, 50/50, 60/40, keyboard divider control, secure viewer.
- **Actual:** stage tabs (Queue/Extract/Map/Calculate/Clarify or Queue/Extract/Map/Validate/Review/QC/Evidence) with a fixed split; no preset selector or keyboard divider.
- **Required change:** implement the D19 workbench chrome: top nav rendering the frozen stage list, split-preset buttons, keyboard divider adjustment, while keeping the existing (working) ExtractionPanel actions underneath.
- **Affected layer:** FE (+ CSS) (+ T if component tests exist).
- **Dependencies:** none (purely presentational on top of working actions).
- **Acceptance criteria:** (1) top nav renders the frozen stages for the persona; (2) presets change the split; (3) keyboard divider works; (4) existing claim/save/map/calculate still work after refactor.
- **Regression tests:** workbench UI interaction tests; existing extraction flow tests.
- **PO decision required?** NO (D19 frozen).
- **Authoritative source:** D19; `MASTER_UI_UX_ASCII_DESIGNS.md`.

### CL-13 Legacy styling/nav leaks (D21)
- **Finding:** D21-2. **Role:** customers. **Workflow:** all. **Screen:** app shell.
- **Expected:** unified D21 design system.
- **Actual:** legacy shell nav ("History & Trends", "Reports (V3)", "Organization (V3)", "Consultant (V3)", "Team Management", assets) coexists with the V3 shell; legacy-styled buttons/tables remain on some screens.
- **Required change:** remove/redirect legacy shell entries for V3 personas; sweep remaining legacy-styled controls to V3 tokens.
- **Affected layer:** FE (+ CSS).
- **Dependencies:** none.
- **Acceptance criteria:** consistent V3 chrome on all persona surfaces; no legacy nav entries for customer/consultant/staff.
- **Regression tests:** visual + route audit per persona.
- **PO decision required?** NO (D21 frozen).
- **Authoritative source:** D21; `CARBONTALLY_V3_DESIGN_SYSTEM.md`.

### CL-14 Custom-factor approval deadlock in single-admin orgs
- **Finding:** FAC-1 / PO-1. **Role:** Owner. **Workflow:** custom factor draft → active.
- **Expected:** every org with the ability to create factors can complete approval.
- **Actual:** self-approval is correctly blocked (403); in an org with a single admin there is no other approver, so factors stay in `draft`.
- **Required change:** implement the PO-decided approver path (options in PO-1): CarbonTally staff approval, mandatory second admin, or flagged self-approval. Update the Custom Factors tab to explain who can approve and when approval is possible.
- **Affected layer:** BE + API + FE (per decision) (+ T).
- **Dependencies:** PO-1.
- **Security implications:** preserve no-self-approval unless PO opts for a flagged exception.
- **Acceptance criteria:** per the PO decision (e.g. staff approval: owner-created factor approved by staff → active; single-admin org factors can be approved).
- **Regression tests:** per the chosen flow + existing self-approval 403 test.
- **PO decision required?** **YES (PO-1)** — this item is blocked on the decision.
- **Authoritative source:** D-cf-3 (factor approval); audit PO-1.

### CL-15 Retention: verify/enforce N3 server-side
- **Finding:** RET-1. **Role:** Staff Admin. **Workflow:** retention configuration. **Screen:** `/ops` Settings tab.
- **Expected:** configured retention values persist and are enforced server-side; unset = no policy; audit/evidence excluded per D15.
- **Actual:** UI renders "Not configured" defaults with Save changes ("Enforcement is server-side"); save/enforcement not yet exercised end-to-end.
- **Required change:** complete the retention endpoint round-trip (save → persist → read-back), add server-side enforcement for configured values with audit/evidence exclusions, and add a dry-run/report of what a run would remove.
- **Affected layer:** BE + API + DB (+ FE if persistence state missing) (+ T).
- **Dependencies:** PO-2 (durations model).
- **Security implications:** enforcement must never delete audit/evidence rows; document exclusions.
- **Acceptance criteria:** (1) staff-admin saves retention values → read-back matches; (2) enforcement respects exclusions; (3) dry-run output documented.
- **Regression tests:** retention CRUD API; exclusion test.
- **PO decision required?** **YES (PO-2)** — durations and exclusions are unspecified.
- **Authoritative source:** N3; D15/8.1 ("do not implement a new retention architecture until legal/contractual minimums… are established").

### CL-16 Finalised evidence immutability
- **Finding:** EVD-3. **Role:** operations/QC. **Workflow:** finalised calculation evidence.
- **Expected (D7.3):** finalised calculation evidence is immutable.
- **Actual:** no finalisation/lock path was exercised; the report pipeline reads `emissions_logs` but no freeze mechanism was verified.
- **Required change:** verify (or add) a finalisation state for calculated items after QC approval such that downstream edits are blocked or versioned; assert immutability in tests.
- **Affected layer:** BE + API (+ DB if a status/version field is missing) (+ T).
- **Dependencies:** none.
- **Acceptance criteria:** once an item is finalised, further edits return 409 (or create a new version); evidence reflects the finalised values.
- **Regression tests:** finalise-then-edit test.
- **PO decision required?** NO (D7.3 locked).
- **Authoritative source:** D7.3; `MASTER_UX_RECOMMENDATION.md` evidence section.

---

## P3 — Polish / non-blocking

### CL-17 Remove stray test role from staff selectors
- **Finding:** UX-7. **Role:** Staff Admin. **Screen:** `/ops` Staff tab role select.
- **Expected:** role select lists the four real roles.
- **Actual:** includes `t_ba_34e3cb`.
- **Required change:** delete the stray `staff_roles` row (test artefact) or filter it.
- **Affected layer:** DB (+ FE if it reads roles directly).
- **Acceptance criteria:** selector shows only operator/reviewer/qc_specialist/admin.
- **PO decision required?** NO.
- **Authoritative source:** audit AUTH-2.

### CL-18 Format emissions figures (units, rounding)
- **Finding:** UX-9. **Role:** customer + consultant dashboards. **Screen:** consultant client workspace, customer emissions, reports summaries.
- **Expected:** "10,732 kg CO₂e" style formatting.
- **Actual:** raw floats "8850.000000", "11735.015649".
- **Required change:** shared number formatter (kg/t, 1 decimal) for all CO2e displays.
- **Affected layer:** FE.
- **Acceptance criteria:** no raw float on any dashboard; consistent units.
- **PO decision required?** NO.
- **Authoritative source:** D21 design system.

### CL-19 Show factor label in calculation history
- **Finding:** UX-6. **Role:** customer. **Screen:** `/emissions`.
- **Expected:** history row shows the matched factor (name + source + year).
- **Actual:** FACTOR column renders "—".
- **Required change:** join/populate the factor label in the calculation-history response/UI.
- **Affected layer:** BE (if not returned) + FE.
- **Acceptance criteria:** history row shows the factor that produced the number.
- **PO decision required?** NO (D-cf factor provenance).
- **Authoritative source:** D6.4 factor provenance.

### CL-20 /ops/me probe noise for non-staff
- **Finding:** PERF-2. **Role:** customers/consultants. **Workflow:** shell render.
- **Expected:** no error log for non-staff.
- **Actual:** `GET /api/v3/ops/me` → 403 logged on every customer/consultant page.
- **Required change:** only call `/ops/me` when the session is likely staff, or treat 403 as expected (no error log).
- **Affected layer:** FE.
- **Acceptance criteria:** clean console for customers/consultants.
- **PO decision required?** NO.
- **Authoritative source:** audit PERF-2.

### CL-21 Reconcile issue status-transition endpoint
- **Finding:** API-6. **Role:** customer/staff. **Workflow:** issues lifecycle.
- **Expected:** the documented status-transition path works.
- **Actual:** `POST /api/v3/issues/{id}/status` → 404 in testing.
- **Required change:** align frontend call with the actual route in `api/v3_issues.py` (and add the missing route if the frontend path is the intended one); then verify create → assign → respond → resolve → reopen.
- **Affected layer:** BE + FE (+ T).
- **Acceptance criteria:** full issue lifecycle round-trip works from the UI.
- **PO decision required?** NO.
- **Authoritative source:** `MASTER_WORKFLOW_MAP.md` issues section.

### CL-22 Locations tab affordance (N2)
- **Finding:** MD-3 polish. **Role:** Owner. **Screen:** `/organization` → Locations.
- **Expected:** easy path from Locations to the facilities manager.
- **Actual:** text explains locations==facilities; no button.
- **Required change:** add a "Manage facilities" link on the Locations tab (optional).
- **Affected layer:** FE.
- **Acceptance criteria:** one click from Locations to Facilities & Assets.
- **PO decision required?** NO (N2 already resolved).
- **Authoritative source:** N2.

### CL-23 Stage-vocabulary de-duplication
- **Finding:** PRC-3. **Role:** ops/PE. **Workflow:** workbench.
- **Expected:** one stage vocabulary.
- **Actual:** backend `extraction/mapping/validation/calculation` vs frontend tab ids `extract/map/calculate/validate`; `getNextItem()` unused.
- **Required change:** adopt one vocabulary (suggest backend canonical) across tabs, API helpers and tests; remove dead `getNextItem` if unused.
- **Affected layer:** FE (+ T).
- **Acceptance criteria:** single source of truth for stage ids; no dead code.
- **PO decision required?** NO (engineering decision).
- **Authoritative source:** D19; audit PRC-3.

### CL-24 Nav label/route consistency
- **Finding:** D21-5. **Role:** customers. **Screen:** shell.
- **Expected:** consistent "Organisation"/"Organization" label vs `/organization` route.
- **Actual:** UK label + US route.
- **Required change:** pick one spelling (recommend route stays `/organization`; label matches brand).
- **Affected layer:** FE.
- **Acceptance criteria:** consistent spelling.
- **PO decision required?** NO.
- **Authoritative source:** D21.

---

## Continuation additions (investor-scale session, 2026-08-28)

Findings from `CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` (ISC-*). These are additive to CL-01..CL-24 above; no ID collisions.

### P1

#### CL-25 Document → emissions reverse lookup (D33) is broken — `calculation_snapshots.source_item_id` never written

- **Role:** Customer Owner / Member; Ops (evidence view)
- **Workflow:** Document → emissions evidence (D33 reverse lookup); Documents page "Emissions from this document"
- **Expected:** after a pipeline run, `GET /api/v3/documents/{file_id}/emissions` returns the emission(s) derived from the document (chain `organization_files.id ← manual_extraction_items.file_id ← calculation_snapshots.source_item_id ← emissions_logs.snapshot_id`), and the Documents page shows the emissions outcome for each document.
- **Actual:** endpoint returns `{"emissions":[]}`; Documents page shows "Emissions from this document —" for a document whose item is `approved` and whose `emissions_logs` row exists (2661.55 kg CO₂e).
- **Root cause:** `backend/api/v3_operations.py` `calculate_item` builds `CalculationRequest(…, source_file=item.file_name, …)` without `source_item_id=item.id`; the engine persists the snapshot with `source_item_id=NULL`, so `data/emissions_logs.py::list_for_file` (JOIN on `s.source_item_id`) matches nothing.
- **Severity:** P1 (evidence chain invisible to the customer — undermines the flagship demo story)
- **Required change:** populate `source_item_id=item.id` (and `source_page` if available) in the `CalculationRequest` in `calculate_item` (and in the line-item calculation path `_run_line_calculation` if used).
- **Affected layer:** Backend (API) + Frontend (Documents page display already exists; will populate once API returns data)
- **Dependencies:** none
- **Security implications:** none (org-scoped read; the D33 audit record already exists)
- **Acceptance criteria:** full pipeline (upload→extract→map→validate→calculate→customer approve) then `GET /api/v3/documents/{file}/emissions` returns ≥1 row with `calculated_kg_co2e` equal to the snapshot value; Documents page shows the tCO₂e/status per document.
- **Regression tests required:** pipeline→document-emissions assertion; document_emissions 404/403 paths.
- **PO decision required?** NO (D33 evidence traceability is frozen)

### P2

#### CL-26 Blocking validation issues are never closed on re-validation / approval

- **Role:** Customer Owner; Ops
- **Workflow:** Validation → issues → re-validation → approval → dashboard attention counts
- **Expected:** when a later validation passes or the item reaches `calculated`/`approved`, previously opened blocking issues for that item/batch transition to resolved/closed and the dashboard "Open issues" count reflects reality.
- **Actual:** 2 issues (`Validation: EXTRACTION_MISSING_FIELD`) remain `open` with `resolved_at` NULL after the item was re-validated clean and **approved**; dashboard permanently shows "Open issues: 2" on an approved item.
- **Root cause:** no close/supersede transition wired from validation re-run or item terminal states to the `issues` lifecycle (`backend/engines/processing_workflow.py` opens issues; no complementary close path).
- **Severity:** P2
- **Required change:** on a passing re-validation of the same item/batch, mark the previously opened validation issues resolved (or link them to the item lifecycle and close on `calculated`/`approved`).
- **Affected layer:** Backend (engine + API)
- **Dependencies:** none
- **Security implications:** none
- **Acceptance criteria:** blocking validate (issues open) → re-validate clean → calculate → approve → issues resolved/closed; dashboard count drops.
- **Regression tests required:** issue lifecycle transition test.
- **PO decision required?** NO (issue lifecycle is part of the approved workflow model)

### P3

#### CL-27 Emissions history list omits `activity` (and factor label)

- **Role:** Customer
- **Workflow:** Emissions history
- **Expected:** the history row shows the activity (and factor name/rate) from the calculation snapshot.
- **Actual:** ACTIVITY and FACTOR columns render "—"; the exports list payload has no `activity` field and no factor-name join.
- **Severity:** P3
- **Required change:** include `activity` (and factor name + multiplier) in the emissions list payload (`backend/data/exports.py` / `api/v3_exports.py`), render in `EmissionsPage.jsx`.
- **Affected layer:** Backend + Frontend
- **PO decision required?** NO

#### CL-28 Asset creation 500 on missing facility; asset list shows facility UUID

- **Role:** Customer Owner
- **Workflow:** Organisation → Facilities & Assets → New asset
- **Expected:** missing required `facility_id` → 422 validation (not 500); asset list renders facility name.
- **Actual:** `POST /organizations/{org}/assets` with `facility_id:null` → 500 (`violates not-null constraint`); asset row shows the raw UUID.
- **Severity:** P3
- **Required change:** pre-validate `facility_id` in `add_asset` (422); join facility name in asset serialization.
- **Affected layer:** Backend (API) + Frontend (FacilitiesTab)
- **PO decision required?** NO

#### CL-29 Notifications hook calls removed legacy endpoint (root cause of PERF-1)

- **Role:** all authenticated
- **Workflow:** Notification bell / unread counts
- **Expected:** notification count loads from the working V3 endpoint.
- **Actual:** `frontend/src/hooks/useNotifications.js` calls `GET /api/notifications` → 404; console logs "Error fetching notifications: Object" on every page.
- **Severity:** P3
- **Required change:** migrate the hook to `/api/v3/notifications`.
- **Affected layer:** Frontend
- **PO decision required?** NO

#### CL-30 Locations tab shows newly created facilities as Inactive

- **Role:** Customer Owner
- **Workflow:** Organisation → Locations (N2 facilities model)
- **Expected:** a facility created with `is_active=true` displays as Active.
- **Actual:** Locations tab shows `Inactive` for a new facility whose API state is `is_active:true`.
- **Severity:** P3
- **Required change:** align the Locations view's status source with the facility create payload.
- **Affected layer:** Backend or Frontend (LocationsTab)
- **PO decision required?** NO

## Session-3 additions (investor-scale battery, 2026-08-28) — CL-31..CL-34

Findings ISC-8..ISC-16 from `CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` §8. Additive to CL-01..CL-30; no ID collisions.

### CL-31 Custom-factor create returns raw 500 on duplicate factor family (ISC-8)

- **Finding:** ISC-8. **Role:** Customer Owner/Member. **Workflow:** Custom factors — create.
- **Expected:** creating a factor that collides with an existing org factor family `(activity_type, reporting_year, country, unit, scope)` returns a clean 409/422 ("a factor with this activity/unit/scope/year already exists").
- **Actual:** `POST /api/v3/customer-factors` → 500 `duplicate key value violates unique constraint "idx_customer_factors_family_version"` when the org already has a factor in the same family (common: the seed preloads "Customer Diesel factor v1" etc. per org).
- **Root cause:** `api/customer_factors.py` create path does not catch the Postgres unique-violation (IntegrityError) → unhandled 500.
- **Severity:** P2 (opaque failure in the common case; demo would show a server error).
- **Required change:** catch the unique-violation in the create path and return 409 with an actionable message naming the existing factor family (or implement D-cf-4 version-bump semantics if PO prefers).
- **Affected layer:** Backend (API) + Tests.
- **Dependencies:** none. **Security implications:** none.
- **Acceptance criteria:** colliding create → 409 with message; non-colliding create → 201; no 500. **Regression tests:** factor-create collision unit test.
- **PO decision required?** NO (409 vs auto-version-bump is a product nuance — flag PO-1 family but the defect fix is unambiguous).

### CL-32 Mapping dead-ends for spend-based activities — empty factor candidates + no fallback (ISC-9)

- **Finding:** ISC-9. **Role:** Customer Owner (self-service processing); internal operator. **Workflow:** Mapping (D19 map stage).
- **Expected:** any extracted activity can be mapped — either factor candidates derived from activity/unit, or a manual factor browse/search fallback; mapping must not dead-end with an empty factor list.
- **Actual:** `GET /api/v3/processing/items/{id}/mapping-options` returns `"factors": []` for "Purchased goods"/GBP (and any activity whose exact unit is absent from the factor sets); `POST …/map` then 422 "an emission factor must be selected". The DEFRA-2025/SEAI-2025 sets (7,049 rows) contain no £-denominated spend factors and `find_by_activity` requires activity ILIKE **and exact unit match**.
- **Root cause:** (1) factor-set coverage gap (TEST-DATA — spend-based factors not loaded); (2) no fallback factor picker and exact-unit-only matching (IMPLEMENTATION GAP).
- **Severity:** P2 — investor-demo-critical (seeded spend documents cannot reach calculation/emissions/review/report).
- **Required change:** (a) add a factor browse/search fallback to mapping-options + mapping UI (search across factor sets, show unit + source); (b) decide factor-set coverage with PO — load DEFRA scope-3 spend-based (£) factors; (c) optionally unit-normalize matching.
- **Affected layer:** Backend (`data/emission_factors.py`, `api/v3_processing_workflow.py`) + Frontend (map picker) + Data/factor sets.
- **Dependencies:** PO decision on factor-set coverage (new PO item, see §PO items). **Security implications:** none.
- **Acceptance criteria:** a "Purchased goods"/GBP item maps to a selected factor and calculates; mapping UI offers a searchable factor list even when derived candidates are empty.
- **PO decision required?** PARTIAL — factor-set coverage = YES (PO-6); fallback picker = NO.

### CL-33 system_admin role is not a superset of staff admin — denied audit + billing (ISC-10)

- **Finding:** ISC-10. **Role:** System Admin. **Workflow:** Control plane (audit trail, billing config).
- **Expected:** the highest-privilege role (`system_admin`, `is_superuser`) can do everything staff-admin can (audit trail, billing, staff, ops queues).
- **Actual:** `system-admin.demo` perms = `{can_manage_staff, can_process, can_review, can_view_all, is_superuser}` — **missing `can_manage_billing`**; `GET /api/v2/admin/audit` → **403 "Admin privileges required"** while `staff-admin` gets 200.
- **Root cause:** the seed added a distinct `system_admin` staff role without a superset permission mapping; the legacy `/api/v2/admin/*` authorizer uses a role-name whitelist that excludes `system_admin`.
- **Severity:** P2 (System Admin persona cannot audit the platform or manage billing).
- **Required change:** single source of truth for role permissions (e.g., role→perm mapping table); make `system_admin` a superset of `admin`; align legacy `/api/v2/admin/*` authorizers to the new role model; update seed role config.
- **Affected layer:** Backend (`api/admin_audit.py` authorizer, staff role config) + Database seed (staff_roles/permissions) + Tests.
- **Dependencies:** PO ratification of the role model (PO-5 extended: system_admin responsibilities). **Security implications:** currently denies-too-much (no data exposure); after fix, keep least-privilege for non-admin roles.
- **Acceptance criteria:** system-admin can access audit + billing + staff; staff-admin still can; operator/reviewer/QC still cannot.
- **PO decision required?** YES (role model) — see PO-5 update.

### CL-34 Demo dataset: PE queues empty + no item in customer_review state (ISC-14/15)

- **Finding:** ISC-14/ISC-15. **Role:** PE manager/staff; customer. **Workflow:** PE assignment; customer review/approval demo.
- **Expected:** the investor demo dataset represents the full workflow state — PE entities have assigned batches/items; at least one item sits in `customer_review` for the customer approval screen.
- **Actual:** 0 of the 3 demo PE entities have assigned batches (only 1 entity-assigned batch in the whole DB); 0 of 221 items are in `customer_review` (seeded pipeline wrote `approved` directly); 53/56 batches remain `open`.
- **Root cause:** seeder advances item statuses without exercising the runtime assignment/review flows.
- **Severity:** P3 (demo-state/data completeness — no code defect).
- **Required change:** extend `tools/seed_investor_demo` (or a follow-on script) to assign batches to the 3 PEs and advance one or more items to `customer_review` (through the API so RLS/state transitions are exercised) — after CL-02 fixes the review queue.
- **Affected layer:** Data/tests (seeder) — NOT application code.
- **Dependencies:** CL-02 (review queue) for the demo to be watchable. **Security implications:** none.
- **Acceptance criteria:** PE dashboards show assigned work; customer review screen lists ≥1 item; approvals flow to `approved`.
- **PO decision required?** NO (data/demo state).

## Recommended implementation order & dependencies

1. **P1 wave 1 (independent, high impact):** CL-01 (viewer upload), CL-02 (review queue), CL-03 (conversation creation), CL-04 (vehicles table), **CL-25 (document→emissions evidence)** — none depend on each other.
2. **P1 wave 2 (consultant chain):** PO-4 decision → CL-05 → CL-06 → CL-07 (strict dependency chain: customer creation → upload → process/map).
3. **P2:** CL-08, CL-09, CL-10 (independent); **CL-26 (issue lifecycle)**; **CL-31** (independent); **CL-32** (fallback picker independent; factor-set coverage needs PO-6); **CL-33** (blocked on PO-5 role-model); CL-11, CL-12, CL-13 (independent); CL-14 (blocked on PO-1); CL-15 (blocked on PO-2); CL-16.
4. **P3:** any order; CL-21 benefits from CL-02 being fixed (same processing area); CL-27..CL-30 independent; CL-34 after CL-02.
5. **PO decisions to request before/with the backlog:** PO-1 (factor approval), PO-2 (retention durations), PO-3 (documents presentation), PO-4 (consultant operating model), PO-5 (System Admin role — now confirmed real in the dataset: seed added `system_admin` with an inconsistent permission set), PO-6 (factor-set coverage — which emission-factor categories the product ships; spend-based £ factors are absent).

*Prepared by OHD, 2026-08-28 (updated with investor-scale continuation additions CL-25..CL-34). Companion deliverables: the Master Acceptance Audit (`CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md`), the Investor-Scale continuation audit (`CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md`), Persona Test Matrix, and Security Acceptance Findings.*
