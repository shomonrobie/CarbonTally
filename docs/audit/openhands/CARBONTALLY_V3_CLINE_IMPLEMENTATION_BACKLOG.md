# CarbonTally V3 — Cline Implementation Backlog

**Source:** independent persona acceptance audit (2026-08-28, baseline `c36c848`), verified
against the live local platform. Each item is actionable without re-discovering the audit.
Priorities: P0 (none — no security P0 found) → P1 → P2 → P3.

Legend — Affected layer: FE=frontend, BE=backend/API, DB=database/schema/RLS,
ENV=environment/deployment, CFG=configuration, TEST=tests, DOC=docs.

---

# P1 — broken core business workflows / authorization

## CL-1 · Customer review & approve queue returns 500

- **Role:** Customer Owner/Admin (also affects consultants/ops reading `stage=review`)
- **Workflow:** CALCULATE → CUSTOMER REVIEW → CUSTOMER APPROVAL → REPORT
- **Screen:** `/review` (customer shell)
- **Expected:** Queue lists items awaiting customer verification; owner/admin can approve/reject.
- **Actual:** `GET /api/v3/processing/customer-review?organization_id=…` and
  `GET /api/v3/processing/queue?stage=review` → **500 `column reference "id" is ambiguous`**.
  The UI shows "Something went wrong — Network error — please check your connection".
- **Root cause:** Unqualified `id` in a JOIN in the review/queue SQL (backend query), so the
  database cannot disambiguate `id` across joined tables.
- **Required change:** Qualify the ambiguous `id` references (e.g. `mi.id`) in the review-queue
  and `stage=review` queries; return the intended item rows. Also improve `v3Fetch` so HTTP 500
  responses surface the server error message instead of a generic "Network error" (see CL-12).
- **Affected layer:** BE (SQL), FE (error message)
- **Dependencies:** none
- **Security implications:** none (deny stays deny); unblocking approval re-enables the D5
  owner/admin gate which must be regression-tested.
- **Acceptance criteria:** Owner sees calculated items in `/review`; approving marks
  `customer_approved` with stamp; rejecting requires a reason and routes back to `mapping`;
  member/viewer still get 403.
- **Regression tests:** queue query; approve/reject round-trip; member/viewer 403; rejection
  reason required.
- **PO decision required?** NO
- **Authoritative source:** D5 (distinct approver action, owner/admin), D2/D37;
  MASTER_WORKFLOW_MAP (customer review/approval stage).

## CL-2 · Workbench "Calculate" cannot complete (stage gate)

- **Role:** Operator, PE Staff, QC, Staff Admin
- **Workflow:** Validate → Calculate → Calculated
- **Screen:** `/ops` data-entry workbench / PE extraction workspace
- **Expected:** Clicking Calculate on a validated item produces a server-computed CO₂e result.
- **Actual:** The UI calls `calculateItem()` directly; the backend state machine requires
  `validated → calculating → calculated`, so Calculate returns **409
  `transition validated→calculated not allowed`**. No UI component calls
  `startItem(id,'calculation')` first.
- **Root cause:** FE workflow gap (missing intermediate stage call) against a strict BE state
  machine.
- **Required change:** In the workbench `run('calculate')` handler, first call
  `startItem(itemId, 'calculation')`, then `calculateItem(itemId, {…})`, handling the 409/422
  paths with the server messages. (Verify `startItem` stage vocabulary: backend uses
  `calculation`.)
- **Affected layer:** FE
- **Dependencies:** none
- **Security implications:** none (calculation remains server-authoritative).
- **Acceptance criteria:** A validated item becomes `calculated` with
  `calculated_emissions_kg_co2e` via the UI for operator and PE staff; the reviewer still
  cannot calculate (403).
- **Regression tests:** full UI calculate path; reviewer deny; duplicate/race double-click.
- **PO decision required?** NO
- **Authoritative source:** D18 server-authoritative calc; MASTER_WORKFLOW_MAP (calculation
  stage); PE/D19 workbench spec.

## CL-3 · Unit alias resolution (422 UNIT_MISMATCH on `L`)

- **Role:** Operator, PE Staff, QC
- **Workflow:** Map → Calculate
- **Screen:** extraction workspace (Calculate action)
- **Expected:** An item with activity `4258.9`, unit `L`, mapped to "Diesel (average biofuel
  blend) — litres" calculates (2.52 kg/L → 10,732.4 kg CO₂e).
- **Actual:** **422 `UNIT_MISMATCH`**. `_resolve_unit_for_factor` matches units exactly or by
  substring; extracted/entered units use abbreviations (`L`, `t`, `kg`, `kWh`) that never match
  the factor's canonical unit (`litres`, etc.).
- **Root cause:** BE unit-normalisation gap.
- **Required change:** Normalise common unit aliases server-side before matching
  (L↔litres, t↔tonne, kg↔kilograms, kWh, m³↔cubic metres, MJ, etc.), or store units against
  factor ids so matching is by factor, not by unit string.
- **Affected layer:** BE
- **Dependencies:** none
- **Security implications:** none.
- **Acceptance criteria:** Diesel item with unit `L` calculates to 10,732.4 kg; other aliased
  units (kWh, t, m³) calculate for their factors.
- **Regression tests:** unit-alias matrix; factor precedence unchanged; 422 for genuinely
  mismatched units.
- **PO decision required?** NO
- **Authoritative source:** D18 (unit conversion), DEFRA 2026 factor set.

## CL-4 · Apply the vehicles migration to the local/dev database

- **Role:** All (Vehicles tab; also unblocks search)
- **Workflow:** D17 Vehicles CRUD; org-wide search
- **Screen:** Organisation → Vehicles; Search
- **Expected:** Vehicles CRUD works; org search returns vehicles results.
- **Actual:** `GET/POST /api/v3/vehicles` → **500 `relation "public.vehicles" does not
  exist`**. `public.vehicles` is absent from the running DB; the migration
  `supabase/migrations/20260825000000_v3m7_vehicles.sql` exists in the repo but was never
  applied locally. **Org-wide search also 500s** because it queries `vehicles`.
- **Root cause:** ENV (migration not applied). Confirm the migration is in the deployment
  pipeline and apply it in the target environments; verify RLS policies for `vehicles` exist.
- **Required change:** Run/apply the vehicles migration (local + any environment where
  vehicles should work); verify table + RLS + indexes; then verify Vehicles tab and search.
- **Affected layer:** DB/ENV
- **Dependencies:** none
- **Security implications:** confirm RLS on `vehicles` is org-scoped before/after applying.
- **Acceptance criteria:** Vehicles tab lists/creates vehicles for an org member; search
  returns vehicle hits; non-members denied.
- **Regression tests:** vehicles CRUD; search smoke; cross-org search still 403.
- **PO decision required?** NO
- **Authoritative source:** D17 master data; v3m7 migration; v3_vehicles API.

## CL-5 · Viewer must not upload documents (authorization)

- **Role:** Customer Viewer
- **Workflow:** Documents → Upload
- **Screen:** `/documents`
- **Expected:** Viewer is read-only; upload denied server-side (403).
- **Actual:** `POST /api/v3/uploads` → **201 for the Viewer** (the UI disables the button, but
  the API accepts it). Upload gating is `require_org_member()` + `ensure_org_access`, which the
  read-only Viewer role passes.
- **Root cause:** BE authorization (upload endpoint does not exclude the viewer role).
- **Required change:** Restrict uploads to owner/admin/member (e.g. deny `viewer` in the
  upload endpoint or via a role check), keeping member uploads allowed.
- **Affected layer:** BE
- **Dependencies:** none
- **Security implications:** **P1 authorization fix** — restores read-only semantics for
  Viewer at the API layer.
- **Acceptance criteria:** Viewer upload → 403; member/owner/admin upload → 201.
- **Regression tests:** upload per role; storage object not created for denied upload.
- **PO decision required?** NO
- **Authoritative source:** Actor/Workspace/Access model (Viewer = read-only); D-model role
  matrix; existing security acceptance finding SEC-1.

## CL-6 · Messaging: fix conversation creation (N1)

- **Role:** Customer Owner/Admin/Member, Consultant, Staff
- **Workflow:** N1 messaging — create conversation → add participants → send → receive
- **Screen:** `/messaging` (customer), consultant client messages, ops Messaging
- **Expected:** Any authorised actor can create a conversation with valid participants.
- **Actual:** `POST /api/v3/messaging/conversations` → **500 for every persona**.
  `create_conversation` inserts participants with
  `INSERT … ON CONFLICT (conversation_id, user_id) DO NOTHING`, but
  `conversation_participants` has **no unique constraint** on
  `(conversation_id, user_id)` — the upsert is invalid and Postgres raises.
- **Root cause:** BE + DB (missing unique index/constraint the code relies on).
- **Required change:** Add a unique index on `conversation_participants
  (conversation_id, user_id)` (migration) or rewrite the insert to a guarded insert/select;
  keep the ON CONFLICT semantics idempotent. Verify participant-type validation still
  prevents PE participation in customer conversations.
- **Affected layer:** BE + DB
- **Dependencies:** none
- **Security implications:** keep the Customer↔PE prohibition intact; re-run N1 isolation
  tests after the fix.
- **Acceptance criteria:** Owner creates a conversation with another org member; send + receive
  persists; Realtime/unread surface updates; PE attempts still denied; cross-org participant
  selection still denied.
- **Regression tests:** create idempotency (double submit), participant isolation matrix,
  Realtime delivery.
- **PO decision required?** NO
- **Authoritative source:** N1 (Supabase Realtime messaging architecture); messaging RLS/API
  docs.

## CL-7 · Consultant: create customer / upload / process / map entry points

- **Role:** Consultant
- **Workflow:** CREATE CUSTOMER → ONBOARDING → UPLOAD → PROCESS → MAP (whole consultant lifecycle)
- **Screen:** `/consultant`
- **Expected:** Per the consultant model, the consultant can onboard a new customer
  organisation, upload documents for the active client, and drive processing/mapping.
- **Actual:** No "Add client / New customer" UI; `POST /api/v3/consultants/me/clients` only
  links an existing org (422 without id) and `POST /api/v3/organizations` would make the
  caller the owner (incompatible with the consultant model). No upload entry point (API 403 —
  consultant is not an org member). No processing/mapping entry point (API 403).
- **Root cause:** Missing consultant product surfaces (FE + BE authorization gap for the
  intended consultant operations).
- **Required change (needs PO confirmation of the model, then):** (a) a consultant
  "create customer" flow that creates the organisation under consultant ownership/management
  (with an owner/manager account assigned); (b) an upload path that authorises the active
  client's org (consultant-as-agent on the active client); (c) processing/mapping surfaces
  scoped to the active client.
- **Affected layer:** FE + BE
- **Dependencies:** PO decision D-CON-1 (see decision items in the master audit §29).
- **Security implications:** HIGH ATTENTION — consultant write access to client orgs must be
  scoped to the **active** client and revocable on client switch/suspension.
- **Acceptance criteria:** Consultant creates Customer B; uploads a document for B; B appears
  in the client list; processing/mapping operate on B only; switching to A cannot reach B data.
- **Regression tests:** active-client isolation across all new consultant actions.
- **PO decision required?** YES (model: creation ownership + active-client write scope)
- **Authoritative source:** MASTER_WORKFLOW_MAP (consultant lifecycle); actor/access model;
  D-model consultant persona.

## CL-8 · System Admin role mapping to admin-gated surfaces

- **Role:** System Admin
- **Workflow:** Admin control plane (retention N3, commercial/billing config)
- **Screen:** `/ops` Settings/Commercial tabs
- **Expected:** System Admin can operate administrative configuration (or is documented as
  read-only for these).
- **Actual:** `system-admin.demo` gets 200 on ops read surfaces but **403 on
  `/api/v3/settings/retention` and `/api/v3/commercial/*`** because `require_admin()` only
  matches `role == 'admin'`/`role_name == 'admin'`; the `system_admin` role is not mapped to
  admin authority.
- **Root cause:** BE authorization (role-to-permission mapping incomplete).
- **Required change:** Map `system_admin` to admin authority in the auth/permission model (or
  explicitly document the System Admin role as non-admin for these surfaces and hide the tabs).
- **Affected layer:** BE (auth) (+FE tab visibility if role remains non-admin)
- **Dependencies:** none
- **Security implications:** grant must be least-privilege — System Admin should not gain
  customer data access; only platform-config authority.
- **Acceptance criteria:** System Admin reads retention + commercial config (200) and can
  save; staff-admin unchanged; operator/reviewer still 403.
- **Regression tests:** per-role access matrix for settings + commercial.
- **PO decision required?** YES (confirm System Admin is intended to manage these)
- **Authoritative source:** N3 retention (configurable platform capability); D37 commercial
  model; staff_roles/system_admin role definition.

## CL-9 · Facility create: postcode/eircode check mismatch

- **Role:** Customer Owner/Admin
- **Workflow:** D17 Facilities → Create
- **Screen:** Organisation → Facilities & Assets → "+ New facility"
- **Expected:** Facility can be created with optional postcode (API allows null).
- **Actual:** Create without postcode → **500** `violates check constraint
  facilities_postcode_or_eircode_check`. UI shows generic "Action failed".
- **Root cause:** BE (API schema allows null postcode) + DB (CHECK requires postcode or
  eircode) mismatch.
- **Required change:** Make the backend validate postcode/eircode and return a 422 with a
  clear message, or make the DB CHECK nullable-friendly (align schema + API contract; add a
  migration if the constraint changes).
- **Affected layer:** BE (+DB if constraint changes)
- **Dependencies:** none
- **Security implications:** none.
- **Acceptance criteria:** Facility create with no postcode either succeeds or returns a clear
  422 field error (no 500); create with postcode/eircode still 201.
- **Regression tests:** create with/without postcode/eircode; owner + admin.
- **PO decision required?** NO
- **Authoritative source:** D17 facilities; facilities CHECK constraint.

## CL-10 · Facility and asset EDIT surfaces (missing endpoints)

- **Role:** Customer Owner/Admin
- **Workflow:** D17 Facilities/Assets → Edit
- **Screen:** Organisation → Facilities & Assets
- **Expected:** Owner can open a facility/asset detail and edit/save changes.
- **Actual:** No `PUT`/`PATCH` endpoints exist for facilities or assets; the UI cannot open a
  proper edit view. Lists/creates work.
- **Root cause:** BE (endpoints never implemented) + FE (no edit UI).
- **Required change:** Add facility update and asset update endpoints (org-scoped, admin-gated
  for writes) and wire the detail/edit UI. Keep soft-delete semantics.
- **Affected layer:** BE + FE
- **Dependencies:** none
- **Security implications:** writes must be org-scoped + owner/admin-gated.
- **Acceptance criteria:** Owner edits a facility (name/postcode) and an asset (name/type)
  and changes persist after reload; member cannot edit (403).
- **Regression tests:** edit round-trip per role; cross-org edit 403.
- **PO decision required?** NO
- **Authoritative source:** D17 master-data CRUD expectation.

# P2 — important functionality/UX

## CL-11 · Notifications bell: use the V3 API surface

- **Role:** All authenticated users
- **Workflow:** Notifications
- **Screen:** global header bell
- **Expected:** Bell shows the user's notifications.
- **Actual:** Every page logs "Error fetching notifications". The bell queries the
  `notifications` table directly via the Supabase client with a `user_id` filter; the table has
  no `user_id` column and RLS (enabled, zero policies) denies the query. The working
  `/api/v3/notifications` endpoint is never called.
- **Root cause:** FE legacy path + DB (RLS w/o policies).
- **Required change:** Rewire the bell to `GET /api/v3/notifications` (and unread/mark-read
  endpoints); remove the direct table query. Optionally add RLS policies for future direct use.
- **Affected layer:** FE (+DB optional)
- **Dependencies:** none
- **Security implications:** keep notifications read restricted to the recipient.
- **Acceptance criteria:** Bell renders real notifications without console errors; unread
  counts update.
- **Regression tests:** bell for customer, consultant, staff; no console errors on load.
- **PO decision required?** NO
- **Authoritative source:** N1/authenticated messaging architecture; v3_notifications API.

## CL-12 · v3Fetch: surface server errors instead of "Network error"

- **Role:** All
- **Workflow:** Any failing API call
- **Screen:** global
- **Expected:** A 500 shows the server message (e.g. "column reference id is ambiguous" → the
  human message) so users/operators can act.
- **Actual:** Any non-2xx/non-JSON response is rendered as "Network error — please check your
  connection and try again", masking backend failures (observed on the customer review queue).
- **Root cause:** FE error mapping.
- **Required change:** Parse the V3 error envelope (`{error:{message}}`) and surface it; keep
  the friendly copy for genuine network failures.
- **Affected layer:** FE
- **Dependencies:** none
- **Security implications:** ensure error payloads don't leak internals (log detail server-side
  only).
- **Acceptance criteria:** A 500 shows the API's message; 403 shows the permission message.
- **Regression tests:** mocked 500/403/network-error paths.
- **PO decision required?** NO
- **Authoritative source:** V3 API error envelope convention.

## CL-13 · PE Manager: view entity batch list

- **Role:** PE Manager (staff role `reviewer` scoped to an entity)
- **Workflow:** PE manager oversight of assigned work
- **Screen:** `/ops` PE surface ("Assigned batches", "Entity performance")
- **Expected:** The manager sees batches/items assigned to their entity.
- **Actual:** Entity batch list endpoint → **403 `staff lacks permission: can_process`**; the
  manager's surfaces render empty/zero.
- **Root cause:** BE authorization (endpoint gated on `can_process`; manager has `can_review`).
- **Required change:** Grant entity-scoped batch visibility to the manager (e.g. read access to
  the manager's own entity), while preserving the `can_process` gate for actual processing.
- **Affected layer:** BE (+FE if empty state was masking the error)
- **Dependencies:** none
- **Security implications:** read-only, entity-scoped.
- **Acceptance criteria:** Manager sees entity batches/items; still cannot process/claim them.
- **Regression tests:** manager vs staff visibility on the same entity.
- **PO decision required?** YES (confirm manager read-scope intent)
- **Authoritative source:** PE actor model (PE Manager oversight).

## CL-14 · Factor search quality (mapping options)

- **Role:** Operator, PE Staff
- **Workflow:** Map → factor selection
- **Screen:** extraction workspace mapping
- **Expected:** Searching "Diesel" surfaces the correct "Diesel (average biofuel blend) —
  litres" factor first.
- **Actual:** The correct factor is not in the default 20 results (biofuel/car factors
  dominate); no results when activity is omitted; unit display in results is inconsistent.
- **Root cause:** BE search/relevance (token matching + top-N).
- **Required change:** Improve relevance (name + alias + unit matching), include factors whose
  unit matches the entered activity unit, and return a sane default set.
- **Affected layer:** BE
- **Dependencies:** CL-3 (unit normalisation makes unit-matching meaningful).
- **Security implications:** none.
- **Acceptance criteria:** "Diesel" query returns the litres diesel factor in the first page;
  results include the entered unit variant.
- **Regression tests:** search relevance fixtures; unit-variant inclusion.
- **PO decision required?** NO
- **Authoritative source:** D18 factor matching; extraction-mapping-calculation docs.

## CL-15 · `/api/reference/fuel-types` stale schema

- **Role:** Any consumer of the reference endpoint
- **Workflow:** fuel-type dropdowns
- **Screen:** wherever the reference endpoint is used
- **Expected:** Fuel types list returns data.
- **Actual:** **500 PGRST205** — the query references `public.defra_conversion_factors`
  (stale); data lives in `emission_factors`.
- **Root cause:** BE schema-cache/query stale.
- **Required change:** Point the reference query at the current factor table (or refresh the
  schema cache); verify the response shape.
- **Affected layer:** BE (DB schema cache)
- **Dependencies:** none
- **Security implications:** none.
- **Acceptance criteria:** `/api/reference/fuel-types` returns 200 with fuel types.
- **Regression tests:** endpoint smoke; dropdown consumer.
- **PO decision required?** NO
- **Authoritative source:** emissions/factor reference API.

## CL-16 · D19 workbench: top workflow nav + split presets + keyboard divider

- **Role:** Operator, PE Staff, QC
- **Workflow:** D19 processing workbench
- **Screen:** `/ops` extraction workspace
- **Expected:** Top workflow nav Queue→Extract→Map→Validate→Review→QC→Evidence; split presets
  40/60, 50/50, 60/40; keyboard divider control; mobile tray.
- **Actual:** Tab navigation with a default split only; presets/nav/keyboard divider absent.
- **Root cause:** FE (frozen D19 direction not implemented in the workbench surface).
- **Required change:** Implement the D19 workbench chrome per CARBONTALLY_V3_DESIGN_SYSTEM.md
  and MASTER_UI_UX_ASCII_DESIGNS.md.
- **Affected layer:** FE (+CSS)
- **Dependencies:** none (pure UI; data already flows through the workspace)
- **Security implications:** none.
- **Acceptance criteria:** Top nav visible and stage-aware; presets re-split panes; keyboard
  divider works; mobile tray usable at 390 px.
- **Regression tests:** workbench interactions; responsive checks.
- **PO decision required?** NO
- **Authoritative source:** D19; MASTER_UI_UX_ASCII_DESIGNS.md; UI_UX_IMPLEMENTATION_MATRIX.

## CL-17 · Custom-factor approval in single-owner orgs

- **Role:** Customer Owner (single-owner org)
- **Workflow:** Custom factors → APPROVE
- **Screen:** Organisation → Custom Factors
- **Expected:** A pathway exists for owner-created factors to become active.
- **Actual:** Self-approval → 403 (correct no-self-approval) but no other actor exists in a
  single-owner org; the Approve button stays enabled → dead affordance. No "pending review"
  stage exists.
- **Required change (after PO decision):** either allow org-owner self-approval (with audit
  stamp) or introduce a CarbonTally review path for custom factors.
- **Affected layer:** BE + FE (+DB if a review stage is added)
- **Dependencies:** PO decision CF-1.
- **Security implications:** self-approval must be audited; keep rejection/self-approval
  semantics for non-owner roles.
- **Acceptance criteria:** Owner-created factor can reach `active` through a defined,
  authorised path.
- **Regression tests:** approval matrix (owner/admin/member/reviewer).
- **PO decision required?** YES
- **Authoritative source:** D17 custom factors; factor precedence (D9); PO decision register.

## CL-18 · Viewer UI should reflect read-only state

- **Role:** Customer Viewer
- **Workflow:** any viewer-visible edit affordance
- **Screen:** `/organization` (profile/metadata), documents, etc.
- **Expected:** Viewer sees read-only controls (no enabled Save/Edit buttons).
- **Actual:** Edit inputs/buttons are enabled and 403 on submit.
- **Root cause:** FE (role-based UI gating missing for viewer).
- **Required change:** Disable/hide write affordances for viewer based on membership role.
- **Affected layer:** FE
- **Dependencies:** none
- **Security implications:** none (API already denies; UI-only).
- **Acceptance criteria:** Viewer sees no enabled write controls; API behaviour unchanged.
- **Regression tests:** viewer UI smoke on /organization, /documents, /emissions.
- **PO decision required?** NO
- **Authoritative source:** Viewer read-only definition in the access model.

# P3 — polish

- **CL-19** — Asset list: render facility **name**, not the raw `facility_id` UUID (FE).
- **CL-20** — Consultant CO₂e formatting: units/rounding ("8850.000000" → "8,850 t CO₂e") (FE).
- **CL-21** — Route/label consistency: `/organization` (US) vs "Organisation" (UK) (FE).
- **CL-22** — Remove stray test role `t_ba_34e3cb` from `staff_roles` and the role selector
  (DB seed/TEST data).
- **CL-23** — Locations tab: add a cross-link to Facilities & Assets (N2 affordance) (FE).
- **CL-24** — Reduce role-probe console noise: only call `/ops/me` and `/consultants/me` when
  the route could be staff/consultant, or tolerate known 403s silently (FE).
- **CL-25** — Supplier edit UI (API exists) (FE).
- **CL-26** — `notifications` table: add RLS policies if any future direct reads are intended
  (DB) — otherwise delete the legacy table/columns and rely on the API.

---

## Recommended implementation order

1. **P1 authorization:** CL-5 (viewer upload) — small, security-relevant.
2. **P1 core workflow (pipeline):** CL-2 (calculate stage) + CL-3 (unit alias) — together they
   make the UI able to produce a calculated result; CL-4 (vehicles migration) unblocks search
   + vehicles; CL-9 (facility postcode) small DB/API contract fix; CL-1 (review queue) unblocks
   the customer handoff; CL-6 (messaging) unblocks N1; CL-8 (system admin) small auth fix.
3. **P1 consultant surfaces (CL-7):** after PO decision D-CON-1; design with active-client
   isolation from the start.
4. **P2 (CL-11..CL-18):** notifications, error surfacing, PE manager view, factor search,
   fuel-types, D19 workbench, factor approval (after PO decision), viewer UI.
5. **P3 polish (CL-19..CL-26).**

Dependency notes: CL-14 depends on CL-3; CL-1 unblocks RPT-2 (customer report approval);
CL-7 depends on the PO decision for consultant write-scope; CL-17 depends on PO decision CF-1.


---

# Phase 1 restoration verification (`6148c86`, 2026-08-24 independent audit)

Status of the pre-existing backlog items **re-verified live** against the Phase 1 commit. Items not
listed were either fixed earlier or not re-tested in this pass. Full evidence:
`docs/audit/openhands/CARBONTALLY_V3_POST_RESTORATION_ACCEPTANCE_AUDIT.md`.

| Item | Status at `6148c86` |
|---|---|
| CL-1 review queue 500 | VERIFIED FIXED (owner queue 200; approve 200 persisted; member 403) |
| CL-2 Calculate 409 | VERIFIED FIXED (`startItem('calculation')` + calculate; snapshot persisted) |
| CL-3 unit alias L<->litres | VERIFIED FIXED (server normalisation + exact-unit ordering) |
| CL-4 vehicles | VERIFIED FIXED (UI table + API 200) |
| CL-6 messaging | VERIFIED FIXED (create 201; unique participants; send/recv 200) |
| CL-7 consultant write scope | VERIFIED FIXED (create customer 201; active-grant processing; cross-firm 403) |
| CL-8 system admin | VERIFIED FIXED (billing/audit/retention 200; `can_manage_billing`) |
| CL-9 facility postcode | VERIFIED FIXED (422, not 500) |
| CL-10 facility/asset edit | VERIFIED FIXED (PUT 200 round-trip; Edit UI) |
| CL-11 notifications | PARTIALLY FIXED (`useNotifications.js` -> v3 API; **`RealtimeContext.jsx` still direct-Supabase**) -> CL-45 |
| CL-12 v3Fetch error surfacing | VERIFIED FIXED (server messages shown) |
| CL-13 PE manager | VERIFIED FIXED (batches/workspace 200; doc 403) |
| CL-14 factor search quality | PARTIALLY FIXED (fuels 20 options; spend still empty) -> CL-47 |
| CL-15 fuel-types | VERIFIED FIXED |
| CL-16 D19 workbench | VERIFIED FIXED (workbench-first at y=200; queue below; responsive) |
| CL-17 factor approval | VERIFIED FIXED (owner self-approval per PO Decision 1; member 403) |
| CL-18 viewer UI | PARTIALLY (viewer sees read-only UI, but upload API still accepts) -> CL-42 |
| CL-19 asset UUIDs | VERIFIED FIXED (facility name shown) |
| CL-22 stray test role | VERIFIED FIXED |
| CL-24 role-probe noise | NOT FIXED -> CL-49 |
| CL-26 notifications RLS | pending - direct reads still exist in RealtimeContext -> CL-45 |
| ISC-1 source_item_id | VERIFIED FIXED for new calcs (25/26 snapshots; 26/26 source_file) |
| ISC-8 duplicate factor 500 | NOT FIXED -> CL-43 |
| ISC-9 spend mapping dead-end | NOT FIXED -> CL-47 |
| ISC-10 system_admin 403 | VERIFIED FIXED |
| UH-1/UH-2 workbench-first | VERIFIED FIXED |
| UH-7 phantom review rows | VERIFIED FIXED (2 real rows; workspace 200) |

No regressions of previously-fixed items observed.

---

# Post-restoration findings - new items (CL-42..CL-52)

**Source:** post-restoration acceptance audit at `6148c86` (see the POST_RESTORATION report).
Priorities follow the same P0/P1/P2/P3 scheme. All are implementation-ready.

## P1

### CL-42 - Viewer upload not denied (read-only role writes)

- **Role:** Customer Viewer
- **Workflow:** UPLOAD (any)
- **Screen:** `/documents`
- **Expected:** POST `/api/v3/uploads` -> 403 for viewer (read-only).
- **Actual:** **201**; storage object + `document_processing_queue` row created. Verified live with
  `viewer.demo0008@` (org `90737215-f871-5969-9bbb-c6a98d445075`); temp artifact created and removed.
- **Root cause:** upload handler authorises org membership only; does not check role read-only.
- **Affected layer:** BE (`v3_documents.py` upload path; add viewer deny alongside the existing role gates).
- **Acceptance criteria:** viewer upload -> 403 with clear message; owner/admin/member still 201.
- **Regression tests:** viewer upload 403; owner/admin/member upload 201; storage object absent on 403.
- **Dependencies:** none. **Security impact:** authorization gap (write by read-only role).

### CL-43 - Customer-factor duplicate create -> raw 500; new-version create impossible

- **Role:** Customer Owner/Admin
- **Workflow:** CUSTOM FACTOR create/version
- **Screen:** `/organization` -> Custom Factors
- **Expected:** duplicate (same family) -> clean 409/422 "factor already exists"; D-cf-4 new-version create
  (version N+1 of an approved factor) succeeds.
- **Actual:** POST duplicates -> **raw 500** `duplicate key value violates unique constraint
  "idx_customer_factors_family_version"` (org, activity_type, reporting_year, country, unit, scope, version).
  `CustomerFactorCreate` has **no `version` field** (always 1), so the new-version workflow is impossible.
- **Root cause:** unique index + unhandled IntegrityError; create schema omits `version`.
- **Affected layer:** BE (`customer_factors.py` create; add conflict mapping + optional `version` on create
  when bumping an approved factor), FE (factor form error handling).
- **Acceptance criteria:** duplicate -> 409/422 with message; version bump create -> 201 draft `version=N+1`;
  no 500.
- **Regression tests:** duplicate create; version bump; approved->new-version->approve cycle.

### CL-44 - Approved customer factor not selectable in mapping UI

- **Role:** Operator / Consultant / Owner (mapping stage)
- **Workflow:** MAP
- **Screen:** D19 workbench Mapping pane / mapping-options picker
- **Expected:** approved (active) customer factors for the org appear in the mapping picker and are
  selectable; calculation then uses the customer factor (precedence).
- **Actual:** `mapping-options` returns system factors only; an approved customer factor works only if the
  client injects its `factor_id` directly into `/items/{id}/map` (calculation stores `factor_source=CUSTOMER`,
  `customer_factor_id`). UI cannot reach it.
- **Root cause:** mapping-options filters to system factor sets; customer factors not merged.
- **Affected layer:** BE (`v3_operations.py` mapping-options), FE (mapper picker).
- **Acceptance criteria:** active customer factor selectable; selected -> snapshot records `factor_source=CUSTOMER`;
  precedence over system factor for same activity/unit.
- **Regression tests:** mapping-options includes active customer factor; map with it; snapshot precedence.

## P2

### CL-45 - Notifications bell still errors (RealtimeContext direct Supabase)

- **Role:** all authenticated
- **Screen:** every authenticated page
- **Expected:** bell reads `/api/v3/notifications` (200, empty list) with no console errors.
- **Actual:** `src/context/RealtimeContext.jsx` L264-270 still queries `supabase.from('notifications')`
  directly -> 0 RLS policies -> `Error fetching notifications: Object` x2 on every page.
- **Root cause:** ISC-6 fix applied to `useNotifications.js` only; Realtime context not migrated.
- **Affected layer:** FE (`RealtimeContext.jsx`); optionally drop legacy table (CL-26).
- **Acceptance criteria:** no console error; bell shows v3 notifications.

### CL-46 - Legacy 404 `GET /api/organizations/members/user/{id}` on every page

- **Role:** customer + staff pages
- **Actual:** layout fires the dead legacy endpoint -> 404 noise on every page (e.g. customer `/home`,
  staff `/ops`). New endpoint: `GET /api/v3/organizations/members/{id}` (200).
- **Affected layer:** FE (layout/header member lookup), BE (remove legacy route or return 410).
- **Acceptance criteria:** no 404 in network tab.

### CL-47 - Spend (GBP) mapping dead-end persists

- **Role:** Operator/Consultant (spend documents)
- **Expected:** mapper returns candidate factors for spend activities, or a "create customer factor" shortcut
  when `no_factors_reason` is returned.
- **Actual:** spend activities -> `factors: []`; no shortcut; dead-end for the demo spend documents.
- **Affected layer:** BE (spend factor seeding or factor-set membership), FE (mapper empty-state CTA).
- **Acceptance criteria:** a spend item can be mapped (either a DEFRA/other GBP factor or an inline customer-factor create).

### CL-48 - Consultant inline extraction workbench (client-processing surface)

- **Role:** Consultant
- **Expected:** consultant can open a client item in a workbench inside the consultant shell (not only via
  the customer processing workspace).
- **Actual:** server-side fully enabled; consultant UI reuses the customer processing workspace. UI follow-on.
- **Affected layer:** FE (consultant client processing view).
- **Acceptance criteria:** consultant opens a client item workbench; saves persist; boundary intact.

## P3

### CL-49 - Role-probe console noise (`403 /ops/me`, `/consultants/me`)

- **Actual:** layout probes both endpoints on every page -> 403 noise x3 each page (CL-24 not fixed).
- **Fix:** route-guard the probes or tolerate known 403s silently.

### CL-50 - D19 "Clear current stage" control missing

- **Screen:** D19 workbench
- **Expected (D19):** a control to clear/restart the current stage.
- **Actual:** absent (Save extraction / Save draft / Save mapping exist).
- **Fix:** add the clear-stage affordance in the workbench shell (small FE).

### CL-51 - One legacy calculation snapshot lacks `source_item_id`

- **Actual:** 25/26 snapshots have `source_item_id`; 1 legacy row is NULL (pre-existing lineage).
- **Fix:** backfill or annotate; ensure future calcs always set it.

### CL-52 - Reviewer dashboard 403 probe noise (`/api/v3/ops/reporting/audit`)

- **Actual:** reviewer tab fires the audit-reporting endpoint -> 403 (reviewer lacks audit). Cosmetic.
- **Fix:** only call when the role has audit permission.

---

## Recommended implementation order (updated)

1. **P1 authorization:** CL-42 (viewer upload deny) - small, security-critical.
2. **P1 custom-factor lifecycle:** CL-43 (duplicate 409 + version-on-create) then CL-44 (mapper factor picker) -
   together complete the PO-approved factor precedence arc.
3. **P2 hygiene before any demo:** CL-45 (notifications), CL-46 (legacy 404), CL-49 (probe noise).
4. **P2 workflow:** CL-47 (spend mapping), CL-48 (consultant workbench).
5. **P3 polish:** CL-50, CL-51, CL-52.


# Continuation workspace-architecture findings (CL-53..CL-66)

**Source:** role workspace, workflow and UI/UX architecture continuation audit.
These entries are additive to CL-1..CL-52 and preserve all prior IDs. The audit
was discovery-only: no application, database, schema, migration, RLS,
configuration or seed files were changed.

## P1 — core workflow, authorization boundary, or critical availability

### CL-53 — Customer review detail calls the staff-only workspace endpoint

- **Priority:** P1
- **Persona:** Customer owner/admin/member/viewer (customer review)
- **Workflow:** calculated item → customer review detail → approve/reject
- **Screen:** `/review/:itemId`
- **Expected:** An authorised customer member can open the customer-safe review
  workspace; owner/admin can approve or reject, while member/viewer remain read
  only. The customer route must not depend on internal staff authorization.
- **Actual:** `ReviewDetailPage` calls the shared `getItemWorkspace()` client
  function, which requests `/api/v3/ops/items/{item_id}/workspace`. The backend
  `v3_operations.item_workspace` depends on `require_staff`. Customer review
  queue and approval APIs are separate and customer-scoped, but the detail page
  is coupled to a staff-only endpoint and can fail/deny for a normal customer.
- **Reproduction:** Login as `owner.demo0001` or `member.demo0035`; open the
  customer review route or select a review row; inspect the network request for
  `/api/v3/ops/items/{id}/workspace` and compare it with the endpoint's
  `require_staff` dependency. Do not use a staff token to mask the defect.
- **Evidence:** `frontend/src/v3/customer/ReviewDetailPage.jsx` lines 11/59;
  `frontend/src/v3/api.js` `getItemWorkspace`; `backend/api/v3_operations.py`
  `item_workspace` dependency. Existing CL-1/PRC-1 covers the queue/approval
  path, not this customer workspace contract.
- **Root cause:** FE shared API function is bound to an internal ops route;
  customer-safe workspace endpoint/contract is missing.
- **Affected layer:** FE + BE/API contract + authorization boundary.
- **Security impact:** Current failure is deny/availability, not leakage. Do not
  solve it by broadening the staff endpoint to all customers; preserve org/RLS
  and expose only customer-appropriate evidence fields.
- **UX impact:** Review appears reachable from the list but becomes a dead end.
- **Scalability impact:** Separate role-specific contracts are needed before
  routed workspaces and pagination can scale safely.
- **Acceptance criteria:** customer owner/admin/member can load `/review/:id`
  using a customer-safe endpoint; member/viewer see evidence without decision
  controls; owner/admin approve/reject persists; staff endpoint remains staff-only;
  cross-org item IDs return 403/404 without data.
- **Regression test:** customer owner/member detail load; viewer read-only load;
  owner approve/reject; member/viewer approve 403; customer token on ops
  workspace 403; staff token still loads ops workspace.
- **Dependencies:** Customer workspace contract decision; CL-59 routing; existing
  CL-1/CL-17/CL-42.
- **Product Owner decision required:** NO for the separation; YES only for the
  exact customer evidence fields and whether customer members may see all review
  details.

### CL-54 — Customer Processing is metadata-only, not a customer work workspace

- **Priority:** P1
- **Persona:** Customer owner/admin/member; consultant-managed customer users
- **Workflow:** upload → extraction → mapping → validation → calculation → evidence
- **Screen:** `/documents`, `/processing`
- **Expected:** A customer can follow a real uploaded document into an item
  workspace, see processing state, confirm extraction, map factors, validate,
  calculate and trace the result to evidence. Member permissions should be
  explicit; owner/admin approval remains distinct.
- **Actual:** `/documents` uploads to V3 and creates a pending manual item. The
  `/processing` screen lists batches and offers a form to manually create batch
  items from `file_name`/`file_url`; it has no item-open workbench, no stage
  actions, no evidence detail and no customer status progression. The only
  complete processing UI is internal/PE `ExtractionPanel`.
- **Reproduction:** Login as `member.demo0035`; visit `/documents` and
  `/processing`; observe the uploaded `multi_gas.pdf` and `Uploads` batch. The
  customer page exposes no action to open the linked item or continue the stages.
- **Evidence:** `frontend/src/v3/customer/ProcessingPage.jsx` only calls
  `v3ListExtractionBatches`, `v3ListExtractionItems`, `v3CreateExtractionBatch`
  and `v3CreateExtractionItem`; `frontend/src/v3/ops/ExtractionPanel.jsx` owns
  the actual stage controls.
- **Root cause:** customer and staff processing surfaces were implemented as
  different capability levels without a customer item-workspace orchestration
  contract.
- **Affected layer:** FE + API/service contract + workflow orchestration.
- **Security impact:** Do not reuse internal staff/PE permissions; preserve
  org-scoped access and distinct final approval.
- **UX impact:** upload appears successful but the user cannot complete the job.
- **Scalability impact:** batch/item navigation and status queries cannot be
  operated by customers at investor-scale without a routed queue/workspace.
- **Acceptance criteria:** customer can open a real uploaded item from the list;
  permitted roles can complete the defined stages; every stage and failure is
  visible; all writes are server-authorized; customer review/approval is a
  separate gate; refresh/deep link preserves the item.
- **Regression test:** upload → item appears → open → save extraction → map →
  validate → calculate → review; member/viewer matrix; cross-org denial; reload
  at every stage.
- **Dependencies:** CL-56 pipeline decision; CL-53 customer workspace; CL-59
  routed workspace; existing CL-7/CL-48 for consultant reuse.
- **Product Owner decision required:** YES — confirm whether customers perform
  extraction/mapping themselves, or only review results from CarbonTally/PE.

### CL-56 — Upload has no automatic extraction-to-emissions pipeline

- **Priority:** P1
- **Persona:** Customer, consultant, internal operator, PE workflow owner
- **Workflow:** upload → trigger → OCR/AI extraction → mapping → validation →
  calculation → evidence/emissions
- **Screen:** `/documents`, `/processing`, operator/PE queues
- **Expected:** Upload creates a durable job with observable status, triggers the
  configured extraction path, retries failures, maps/validates/calculates when
  eligible, persists evidence and reports a clear blocked/manual-review state.
- **Actual:** Upload stores the object and file row, creates/reuses an `Uploads`
  manual batch and a pending item, then runs best-effort synchronous local PDF/
  image text extraction plus deterministic suggestions. It does not populate
  `extracted_data`, call factor matching, validate, calculate, create emissions
  or create evidence. No persistent worker/queue registration was found at
  startup; the process-local EventBus/WorkflowOrchestrator is not a durable
  upload worker.
- **Reproduction:** Existing `member.demo0035` `multi_gas.pdf`:
  `organization_files.status=uploaded`, OCR `status=ok`, only date/activity
  suggestions, linked item `44b0d3cf-...` remains `pending` with null extracted,
  mapped and calculated fields; customer review is empty. Re-read after waiting.
- **Evidence:** `backend/api/v3_documents.py` upload handler; `backend/main.py`
  startup; `backend/infra/event_bus.py`; `backend/engines/workflow.py`; runtime
  `/api/v3/documents`, `/api/v3/manual-extraction/batches/{id}/items` and
  `/api/v3/processing/status` responses.
- **Root cause:** automatic post-OCR orchestration/worker is absent. Existing
  engines and tests are not wired to the V3 upload event.
- **Affected layer:** BE workflow orchestration + worker/queue/ENV integration;
  FE status presentation; potentially AI/OCR provider integration.
- **Security impact:** fail closed; never auto-approve low-confidence or
  unvalidated data. Keep source storage private and audit worker identity.
- **UX impact:** misleading “uploaded” success with no next action or ETA.
- **Scalability impact:** synchronous request work and manual-only progression do
  not provide throughput, retry, idempotency, dead-letter or SLA behavior.
- **Acceptance criteria:** durable idempotent job on upload; explicit statuses
  and timestamps; worker trigger and retry/dead-letter path; extraction output
  remains reviewable; factor selection is explainable; validation/calculation/
  evidence/emissions persist only after gates; failures are actionable; customer
  and consultant uploads use the same observable pipeline.
- **Regression test:** PDF text, scanned PDF/image, CSV/XLSX and multi-line PDF;
  duplicate event; worker retry; OCR failure; no-factor/manual-review path;
  end-to-end database lineage and emissions; customer and consultant-grant
  uploads; no automatic approval.
- **Dependencies:** PO automation scope; CL-54; CL-57/58 status UI; factor
  coverage CL-47 and customer-factor CL-44 where applicable.
- **Product Owner decision required:** YES — automation provider, confidence
  thresholds, human-review gates, SLA and whether mapping can ever be automatic.

### CL-60 — Public CarbonTally Assistant is mounted on authenticated routes

- **Priority:** P1
- **Persona:** all authenticated customers, consultants, staff and PE users
- **Workflow:** public visitor assistance versus authenticated product support
- **Screen:** global main app shell; `/home`, `/consultant`, `/ops`, `/notifications`
- **Expected:** public Assistant appears only on public website routes. Authenticated
  users use authenticated CarbonTally messaging/Realtime support, with no public
  FAQ assistant presented as their product communication channel.
- **Actual:** `AssistantWidget` from `frontend/src/public/assistant` is rendered
  outside the route switch in `frontend/src/App.js`, so it is present on
  authenticated shells. The current staff CDP sweep captured “CarbonTally
  Assistant” on the `/ops` staff-admin loading state. The same app also retains
  legacy `ChatWidget` mounts in the authenticated application.
- **Reproduction:** Login as `staff-admin.demo` or a customer; open `/ops` or
  `/home`; inspect body text and floating controls for “CarbonTally Assistant”.
- **Evidence:** `frontend/src/App.js` global `<AssistantWidget />` at the route
  wrapper; `/tmp/ct_post/current_ops_sweep_out.txt`; public assistant source.
- **Root cause:** public and authenticated route trees share a global widget
  mount; legacy and V3 communication components are co-located.
- **Affected layer:** FE application boundary and navigation/communication
  architecture.
- **Security impact:** no direct data leak proven, but it risks users sending
  authenticated support questions to an unscoped public knowledge surface.
- **UX impact:** wrong audience, duplicated/conflicting communication affordances.
- **Scalability impact:** public and authenticated dependency bundles/releases
  cannot be independently governed.
- **Acceptance criteria:** Assistant renders only on approved public routes;
  authenticated customer/consultant/staff/PE shells show role-appropriate
  messaging; no legacy chat/assistant on V3 pages; direct URL and refresh retain
  the boundary.
- **Regression test:** route matrix for public pages versus every authenticated
  persona; assert widget presence/absence and messaging entry points.
- **Dependencies:** CL-64; CL-66; architecture decision in §31.14.
- **Product Owner decision required:** NO for public-only placement; YES for the
  final authenticated support/messaging ownership model.

### CL-63 — Ops Messaging crashes because `organizations` has the wrong shape

- **Priority:** P1
- **Persona:** Staff Admin and System Admin
- **Workflow:** internal support messaging → select organisation → conversation
- **Screen:** `/ops` → Messaging
- **Expected:** staff-admin/system-admin can select an organisation, list/create
  conversations, read and send messages; other staff/PE roles are denied or do
  not see the tab.
- **Actual:** `/api/v3/ops/dashboard` returns `organizations` as an object such
  as `{total: 975}`, but `OpsMessagingTab` stores it as `orgs` and calls
  `orgs.map(...)` and `organizations[0].id`. The reported `orgs.map is not a
  function` runtime crash prevents use of the tab.
- **Reproduction:** Login as `staff-admin.demo`; open `/ops`, select Messaging;
  inspect `/api/v3/ops/dashboard` payload and browser exception. The API payload
  and component assumptions are directly incompatible.
- **Evidence:** runtime dashboard response (`organizations: {total: 975}`);
  `frontend/src/v3/ops/OpsMessagingTab.jsx` lines 34–38/141–143; V3 messaging
  API contract. Customer and PE messaging probes separately returned expected
  customer 200/PE 403 boundaries.
- **Root cause:** dashboard summary object is consumed as an organisation-row
  array; no dedicated authorised organisation-list contract is used.
- **Affected layer:** FE/API contract; staff messaging availability.
- **Security impact:** preserve staff-admin permission and organisation scope;
  do not fix by exposing all organisations to non-admin staff.
- **UX impact:** hard crash rather than recoverable error state.
- **Scalability impact:** organisation selector needs pagination/search rather than
  loading 975 rows into a dashboard response.
- **Acceptance criteria:** dashboard summary and org-list contracts are distinct;
  staff-admin/system-admin can search/select authorised organisations and use
  conversations; operator/reviewer/QC/PE remain denied/hidden; no React crash.
- **Regression test:** payload-shape contract test; staff-admin open/create/read/
  send; non-admin/PE 403; large organisation list search/pagination.
- **Dependencies:** CL-57/58; CL-64; architecture shell decision.
- **Product Owner decision required:** NO for shape fix; YES for which staff roles
  may contact customers and whether support is organisation-wide or assigned.

## P2 — major workflow, navigation, scalability or maintainability issues

### CL-55 — Upload batch naming and work context are not operationally meaningful

- **Priority:** P2
- **Persona:** Internal Operator, Reviewer, QC, PE manager
- **Workflow:** queue triage → identify work → assign/process
- **Screen:** `/ops` Data entry and PE assigned batches
- **Expected:** each row identifies organisation, customer/consultant context,
  batch/work-order name, document/item count, status/stage progress, source,
  assigned PE/operator, priority, created/updated date and SLA/deadline.
- **Actual:** 51 operator batches mostly render as generic `Uploads`; the table
  displays only Batch, Status, Progress and action. Organisation is present in a
  separate payload object but not rendered in the row; consultant/source,
  assignment, priority, dates and SLA are absent or not visible.
- **Reproduction:** Login as `operator.demo`; open Data entry; observe rows such
  as `Uploads`, `open`, `0%`/`25%`; compare the returned batch/organization/
  progress payload.
- **Evidence:** runtime operator queue payload (`queued=51`, batch_name=`Uploads`);
  `frontend/src/v3/ops/OperatorQueue.jsx` table; upload handler default batch
  name in `backend/api/v3_documents.py`.
- **Root cause:** ingestion default name is reused as the operational work-order
  identity; queue response/UI does not project relationship context.
- **Affected layer:** FE + API read model; data naming/product semantics.
- **Security impact:** labels must respect customer/consultant disclosure rules;
  this is not a reason to expose raw IDs.
- **UX impact:** operator cannot confidently select the right customer work.
- **Scalability impact:** triage by 51+ batches without context increases error
  risk and makes SLA/assignment operations impractical.
- **Acceptance criteria:** row exposes human-readable organisation and source,
  counts, status/stage, assignment, priority, dates and SLA; generic fallback is
  only used when no better name exists; detail remains org/entity-authorized.
- **Regression test:** queue rows across direct customer, consultant-managed and
  PE-assigned batches; missing relationship data; no cross-tenant labels.
- **Dependencies:** CL-56 status model; PO disclosure rules; CL-58 tables.
- **Product Owner decision required:** YES for customer/consultant names and
  source disclosure in internal/PE queues.

### CL-57 — Internal queue read model lacks organisation and relationship context

- **Priority:** P2
- **Persona:** Internal Operator, Staff Admin, System Admin
- **Workflow:** operations queue → assignment/reassignment → SLA management
- **Screen:** `/ops` Data entry, Dashboard queue drill-down
- **Expected:** an operator can answer “Organisation X, managed by Consultant Y,
  N documents, assigned to PE/operator Z, due date D” from one stable queue row.
- **Actual:** organisation is returned as a separate minimal object in the
  operator endpoint, but no consultant firm/customer relationship, source,
  document count, item count column set, or SLA/priority filtering model is
  available in the queue UI. Dashboard counts and queue rows are separate
  aggregates with no drill-down contract.
- **Reproduction:** inspect `/api/v3/ops/queues/operator` and
  `OperatorQueue.jsx`; compare the 51-row response with rendered columns and
  available controls.
- **Evidence:** `backend/api/v3_operations.py` operator queue/read models;
  `frontend/src/v3/ops/OperatorQueue.jsx`; runtime queue payload.
- **Root cause:** queue API is batch-centric and UI-centric rather than a
  server-defined operational read model.
- **Affected layer:** BE read model/API + FE queue.
- **Security impact:** keep internal/PE projections separate and avoid exposing
  customer data to entity staff beyond assigned work.
- **UX impact:** assignment decisions are opaque.
- **Scalability impact:** requires loading each batch to understand work and
  cannot support server-side filtering/SLA sorting.
- **Acceptance criteria:** documented queue schema supports stable filters,
  sorting, pagination and human-readable context; internal versus PE projections
  enforce distinct disclosure; assignment is auditable.
- **Regression test:** 51+ batches; filter by status/entity/operator/SLA/source;
  stable sort and page boundaries; cross-entity/cross-org negative tests.
- **Dependencies:** CL-55; CL-58; CL-59; CL-66.
- **Product Owner decision required:** YES for queue columns and PE disclosure.

### CL-58 — Global V3 tables lack a consistent scalability contract

- **Priority:** P2
- **Persona:** all customer, consultant, staff and PE users
- **Workflow:** browse/search/triage any large collection
- **Screen:** documents, batches/items, review/QC, members, clients, reports,
  emissions, issues, factors, master data, messaging, notifications, staff,
  entities and commercial tables
- **Expected:** collections with production-scale counts have server-side
  pagination, stable sorting, relevant filtering/search, page-size selection or
  a documented fixed size, useful business columns and honest empty states.
- **Actual:** the shared `DataTable` only renders rows/headers/empty row; it has
  no sorting, pagination, filtering or page-size behavior. Only audit has UI
  pagination. Reports/issues/suppliers have partial API/UI filters; customer,
  consultant, ops, PE, messaging and most master-data lists render unbounded
  arrays with fixed ordering. Documents omit the processing/emissions state that
  users need.
- **Reproduction:** inspect the table inventory in the continuation report §31.10;
  compare component source and API list contracts. Investor dataset has 51 ops
  batches, 55 batches and 226 items.
- **Evidence:** `frontend/src/v3/components/ui/DataTable.jsx`; V3 table inventory;
  `backend/data/*` and `backend/api/v3_*.py` limit/offset coverage.
- **Root cause:** pagination was added selectively to APIs but not standardized
  as a shared UI/read-model contract.
- **Affected layer:** FE component architecture + BE list contracts.
- **Security impact:** server-side tenant/entity filters must be applied before
  pagination; never paginate an already over-broad result set in the browser.
- **UX impact:** long scroll, lost position, unclear empty/filter states.
- **Scalability impact:** high memory, slow first paint, unstable operations and
  unusable investor-scale lists.
- **Acceptance criteria:** define a reusable table contract (`items`, `total`,
  `limit`, `offset/cursor`, sort/filter metadata); implement controls for large
  surfaces first; stable deterministic ordering; preserve URL state; retain
  simple tables for tiny reference data.
- **Regression test:** 0/1/25/51/500 rows; filters/sorts/page transitions;
  keyboard/mobile; tenant isolation on every page; no duplicate/missing rows.
- **Dependencies:** CL-55/57/59; endpoint-specific status/search decisions.
- **Product Owner decision required:** YES for required columns, default page
  sizes and which tables need cursor versus offset pagination.

### CL-59 — Reviewer, QC and PE workspaces are inline state, not routed workspaces

- **Priority:** P2
- **Persona:** Internal Reviewer, QC, PE Manager/Staff; later consultant/customer
- **Workflow:** queue → open item → work → Back to Queue/Next item
- **Screen:** `/ops` Review, `/ops` QC, `/ops` PE extraction workspace
- **Expected:** list page → dedicated item workspace route → Back to Queue, with
  browser history, refresh, deep linking, mobile/keyboard access and preserved
  queue filters/page.
- **Actual:** reviewer and QC set `activeItemId` and render `WorkItemWorkspace`
  below the queue; PE holds selected batch/item in component state and renders
  `ExtractionPanel` below performance/list panels. Operator scroll-to-top/collapse
  is an improvement already covered by UH-1/UH-2, but is not a durable route.
  No PE item URL or queue-state restoration exists.
- **Reproduction:** use existing UI sweep; open operator/reviewer/QC/PE item,
  refresh or browser Back, and observe selected workspace/list state is not
  represented in the URL. Inspect `ReviewQueue.jsx`, `QcQueue.jsx` and
  `EntityExtractionWorkspace.jsx`.
- **Evidence:** source components; existing UH-1/UH-2 and current continuation
  layout observations.
- **Root cause:** workspaces are local child components instead of route-level
  resources with queue-state serialization.
- **Affected layer:** FE routing/state architecture; API deep-link contract.
- **Security impact:** route parameters must be re-authorized on every request;
  never trust a saved item ID or client-side active-client state.
- **UX impact:** Back/refresh/deep links do not behave predictably; long queues
  remain a navigation obstacle.
- **Scalability impact:** virtual/paginated queues cannot preserve context without
  URL/cursor state.
- **Acceptance criteria:** item routes for operator/reviewer/QC/PE; direct URL,
  refresh and browser Back work; Back to Queue restores filters/page/scroll;
  Previous/Next respects current server-authorized queue; mobile and keyboard
  navigation are usable.
- **Regression test:** open from page 1/page 3; filter then open; refresh; Back;
  copied URL; stale/foreign item; mobile viewport; keyboard focus return.
- **Dependencies:** CL-53/54; CL-57/58; PE route/shell decision.
- **Product Owner decision required:** NO for the interaction pattern; YES for
  whether consultant/customer use the same routed workbench.

### CL-61 — Consultant team management is API-only

- **Priority:** P2
- **Persona:** Consultant owner/lead and consultant manager/team member
- **Workflow:** firm onboarding → invite/manage team → assign client access/work
- **Screen:** `/consultant`
- **Expected:** firm owner/manager can list team members, invite/add members,
  assign capabilities/client scope, deactivate/revoke access and see current
  role/permission state. Team members see only permitted client work.
- **Actual:** `GET/POST /api/v3/consultants/me/team` exists and is permission-
  gated, but `ConsultantPage` has no team tab, list, invite form, edit or
  deactivation controls. The visible “Clients” list is not a consultant team.
- **Reproduction:** login as `consultant.demo0001`; inspect all tabs and buttons;
  only dashboard, client workspace, branding, white-label and client messages
  exist. Compare with `/me/team` API.
- **Evidence:** `frontend/src/v3/consultant/ConsultantPage.jsx`;
  `backend/api/v3_consultants.py` team routes; runtime team payload.
- **Root cause:** team API was implemented without a firm-admin UI/read model.
- **Affected layer:** FE + consultant lifecycle API/model scope.
- **Security impact:** client access must be grant-scoped, revocable and never
  inferred from a UI-selected client or role label.
- **UX impact:** consultant firm cannot operate as a team.
- **Scalability impact:** owner must manage people outside the product and cannot
  delegate a growing portfolio safely.
- **Acceptance criteria:** team list/invite/edit/deactivate; real `can_manage_team`
  gating; client grants visible/manageable only by authorized users; audit trail;
  team member switch and access isolation.
- **Regression test:** owner/manager/member/viewer matrix; invite duplicate;
  deactivate then access; consultant 1/2 cross-firm; client grant isolation.
- **Dependencies:** existing CL-7/CL-48; PO consultant operating model.
- **Product Owner decision required:** YES for team roles, client assignment and
  whether team members may upload/process/approve.

### CL-62 — Ops tabs are not filtered by actual staff permissions

- **Priority:** P2
- **Persona:** Internal Operator, Reviewer, QC, Staff Admin, System Admin
- **Workflow:** staff login → choose permitted operating surface
- **Screen:** `/ops`
- **Expected:** each actor sees only tabs they are authorized and trained to use;
  unauthorized routes remain server-denied and produce a deliberate access state.
- **Actual:** `BASE_TABS` always includes Dashboard, Data entry, Review, QC, Staff
  and Roles. Operator payload has `can_process`/`can_view_all` but sees Review/QC/
  Staff/Roles; reviewer sees Data entry/Staff/Roles despite lacking permissions.
  The CDP sweep captured repeated 403s and role-probe noise.
- **Reproduction:** login as operator and reviewer; inspect `/ops` tab labels and
  click Review/QC/Staff/Roles; compare with `/api/v3/ops/me.permissions`.
- **Evidence:** `OperationsPage.jsx` computes tabs from `canManageStaff` only;
  runtime permission payloads and current UI sweep.
- **Root cause:** UI checks only staff-management permission, not each tab’s
  `can_process`, `can_review`, `can_manage_staff`, `can_manage_billing` etc.
- **Affected layer:** FE navigation/route guard; BE remains authoritative.
- **Security impact:** no bypass observed; retain server-side 403s and add route
  tests so hiding tabs never becomes the only defense.
- **UX impact:** unauthorized controls look broken and generate error banners.
- **Scalability impact:** noisy requests and irrelevant workflows increase support
  cost as staff roles multiply.
- **Acceptance criteria:** permission-to-tab map; operator sees process-only;
  reviewer review-only; QC process/review; admin control plane; system admin
  commercial/audit/settings per ratified matrix; direct unauthorized URL 403 or
  safe redirect; no noisy probes.
- **Regression test:** all internal roles, PE roles, direct URL navigation and
  server denial; assert no unauthorized API calls on initial render.
- **Dependencies:** CL-66; existing CL-49/52; PO role matrix.
- **Product Owner decision required:** YES for exact tab/action mapping.

### CL-64 — V3 customer and consultant messaging does not subscribe to conversation realtime

- **Priority:** P2
- **Persona:** Customer owner/admin/member/viewer, Consultant, authorised staff
- **Workflow:** conversation → receive message → unread/notification → reply
- **Screen:** `/messaging`, `/consultant` Client messages, Ops Messaging
- **Expected:** Supabase Realtime delivers authorized conversation messages and
  unread state to the active UI; API remains authoritative fallback.
- **Actual:** customer and consultant components load messages and refetch after
  the current user sends. No conversation-specific `postgres_changes` subscription
  is present in `MessagingPage`, `ClientMessagingTab` or `OpsMessagingTab`.
  `RealtimeContext` handles presence and direct legacy notifications, not V3
  message delivery. `/api/v3/messaging` persistence/authorization reads work;
  live UI delivery is not verified.
- **Reproduction:** open the same authorized conversation in two sessions;
  send from one and observe the other without reload/refetch. Inspect component
  source for channel subscriptions.
- **Evidence:** three V3 messaging components; `frontend/src/context/RealtimeContext.jsx`;
  `/api/v3/messaging` contract; prior API persistence verification does not prove
  UI realtime delivery.
- **Root cause:** persisted messaging and presence were wired separately; no
  shared authorized conversation subscription lifecycle.
- **Affected layer:** FE Realtime integration + notification/read-state contract.
- **Security impact:** channel filters must be tenant/participant-authorized;
  never subscribe to a global conversation stream.
- **UX impact:** users believe messaging is stale or broken.
- **Scalability impact:** polling/refetch per action does not scale to active
  support/client conversations.
- **Acceptance criteria:** authorized conversation updates appear without reload;
  inactive tabs update unread state; reconnect/backoff works; PE remains denied;
  API fallback and duplicate-event handling are deterministic.
- **Regression test:** two customer sessions, consultant-client session, staff
  support session, cross-org and PE negative tests, reconnect and duplicate event.
- **Dependencies:** CL-60; CL-63; existing CL-45 notification migration.
- **Product Owner decision required:** YES for who receives unread notifications
  and whether staff support messages are participant- or org-broadcast.

### CL-65 — Organisation shell search returns 500 on report schema mismatch

- **Priority:** P2
- **Persona:** Customer owner/admin/member/viewer
- **Workflow:** authenticated shell search → open matching document/item/report
- **Screen:** V3 header search on customer routes
- **Expected:** an org-scoped query returns useful matches or an honest empty
  state across documents, items, issues, suppliers, facilities, vehicles and
  reports.
- **Actual:** `GET /api/v3/search?organization_id=e589...&q=multi_gas` returns
  HTTP 500 `column "report_name" does not exist`. The query searches
  `report_versions.report_name` even though the running schema uses a different
  report shape. A global shell control therefore fails for a normal search.
- **Reproduction:** login as `member.demo0035`; call the above endpoint or type
  `multi_gas` in the authenticated shell search; observe 500/error state.
- **Evidence:** runtime response; `backend/data/search.py` selects
  `report_versions.report_name`; `frontend/src/v3/components/SearchBox.jsx`.
- **Root cause:** search repository and database report schema are out of contract.
- **Affected layer:** BE query/schema contract + FE shell search.
- **Security impact:** preserve org scoping and test all result types after any
  query correction.
- **UX impact:** prominent search produces a server error.
- **Scalability impact:** one broken UNION-like search surface prevents reliable
  discovery across growing data.
- **Acceptance criteria:** search returns 200 for each supported type, excludes
  unsupported schema fields, is org-scoped, bounded and stable; result routes
  open meaningful detail/workspace pages; failures are non-fatal and friendly.
- **Regression test:** document/item/issue/supplier/facility/vehicle/report
  queries; empty/long/special query; cross-org query; missing optional tables.
- **Dependencies:** CL-58/59; report schema decision.
- **Product Owner decision required:** NO for schema alignment; YES for search
  result taxonomy and navigation destinations.

### CL-66 — Legacy admin and V3 staff role/catalog contracts are split-brain

- **Priority:** P2
- **Persona:** Staff Admin, System Admin, Operator/Reviewer/QC
- **Workflow:** staff provisioning → role assignment → admin control plane
- **Screen:** `/admin`, `/ops` Staff/Roles/Settings/Commercial/Audit
- **Expected:** one intentional staff application/control plane with one role and
  permission vocabulary, or clearly documented app boundaries with equivalent
  server enforcement and no conflicting sources of truth.
- **Actual:** repository contains a separate `admin/` CRA with its own AuthContext,
  Layout, `/admin/*` routes and legacy `/api/admin/*` endpoints, while the main
  frontend has V3 `/ops` and a customer-facing V3 shell. The legacy admin roles
  endpoint returned `success=true, data=[], total=0` for staff-admin while V3
  `/ops/me` and `/staff-roles` returned populated permission data. Deployment
  rewrites serve the legacy admin app separately; the V3 main app has no explicit
  `/admin` route.
- **Reproduction:** inspect `vercel.json`, `admin/src/App.js`, main
  `frontend/src/App.js`; login staff-admin and call both legacy and V3 role/admin
  endpoints. Observe different contracts and catalogs.
- **Evidence:** deployment rewrite; both app routers/AuthContexts; runtime legacy
  `/api/admin/permissions/roles` versus V3 `/api/v3/ops/me` responses.
- **Root cause:** incremental V3 restoration left a parallel legacy admin app and
  APIs mounted beside the new role model.
- **Affected layer:** FE application architecture + BE legacy/V3 authorization
  contracts + deployment.
- **Security impact:** conflicting role sources and legacy name-string guards are
  a privilege-drift risk even where current negative probes deny access. Do not
  remove legacy routes without dependency and migration review.
- **UX impact:** staff do not know whether `/admin` or `/ops` is authoritative.
- **Scalability impact:** duplicate releases, tests, navigation and role catalogs
  increase drift and operational cost.
- **Acceptance criteria:** choose one authoritative staff app; route `/admin` or
  equivalent is explicit; legacy routes are retired/quarantined only after
  dependency inventory; role/permission catalog and audit semantics are unified;
  server-side authorization remains least-privilege and tested.
- **Regression test:** all staff personas against both old/new URLs during
  migration; role CRUD/read; system-admin settings/commercial/audit; PE and
  customer denials; deployment route smoke tests.
- **Dependencies:** architecture recommendation §31.14; CL-60/62; existing
  CL-8/33 and legacy-route PO decision.
- **Product Owner decision required:** YES — approve the canonical staff app,
  migration/deprecation plan and final role authority.

## Updated implementation order for CL-53..CL-66

1. CL-56 (automatic pipeline contract/worker) and CL-54 (customer processing
   semantics) — otherwise status/table work only disguises the missing product.
2. CL-53 (customer-safe review workspace) — do not broaden staff endpoints.
3. CL-60 (public/authenticated boundary) — isolate public Assistant and legacy
   authenticated widgets.
4. CL-63 (Ops Messaging crash), CL-64 (conversation Realtime), then CL-45
   (notifications direct-table error).
5. CL-62 (permission-filtered staff navigation) and CL-66 (canonical admin/V3
   control plane), preserving server-side gates.
6. CL-59 (routed item workspaces), then CL-57/CL-55 operational queue read model.
7. CL-61 consultant team UI, followed by existing CL-7/CL-48 consultant
   upload/process/workbench implementation.
8. CL-58 shared table contract and prioritized controls.
9. CL-65 search schema alignment and result navigation.
10. Re-run CL-42/43/44/47, retention save/reload in an isolated environment,
    PDF/report generation and the complete persona matrix.

*End of continuation backlog additions. No code changes were made.*
