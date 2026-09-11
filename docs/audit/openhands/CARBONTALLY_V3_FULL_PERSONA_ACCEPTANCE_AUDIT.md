# CarbonTally V3 — Full Persona-Based Product Acceptance & Workflow Audit

**Independent acceptance audit — verified against the live local platform.**
**Date:** 2026-08-28 · **Git baseline:** `c36c848` (main) · **Environment:** local/dev
**Auditor:** OpenHands (independent persona simulation + real API/database verification; read-only)

> This audit is an independent verification pass. It does not modify source, schema, RLS,
> migrations, API, configuration, or production data. Temporary test artifacts created during
> this pass were removed (see §30). A prior audit-session deliverable set was preserved under
> `previous-session/` in the same directory and is cross-referenced where relevant.

---

## 1. Executive summary

CarbonTally V3 is a substantial, real implementation: authentication, persona routing, the
customer organisation shell, consultant active-client switching, PE workspace, the ops
control plane, master data, the processing state machine, a server-authoritative calculation
engine, reporting, issues, billing surfaces, and org-scoped authorisation are all present and
**mostly correctly secured**.

However, **no persona can drive the core business outcome — a document becoming an emissions
result that the customer reviews and approves — end-to-end from the UI.** The chain breaks in
four places, independently reproduced:

1. **The UI cannot complete calculation.** The workbench `Calculate` action calls
   `calculateItem()` directly, but the backend state machine requires
   `validated → calculating → calculated`. The intermediate `start('calculation')` is never
   invoked by the UI, so `Calculate` returns **409** for every item. (`PRC-1`)
2. **Unit aliases break matching.** Factors are keyed as `litres` while extracted/entered
   activity uses `L`; the backend's `_resolve_unit_for_factor` performs exact/substring
   matching only, so a correctly-mapped `Diesel` item returns **422 UNIT_MISMATCH**. (`PRC-2`)
3. **The customer review queue is a 500.** `GET /api/v3/processing/customer-review` and
   `GET /api/v3/processing/queue?stage=review` raise `column reference "id" is ambiguous`.
   The customer `/review` screen shows a misleading "Network error". This blocks the
   **CALCULATE → CUSTOMER REVIEW → CUSTOMER APPROVAL → REPORT** handoff entirely. (`PRC-3`)
4. **N1 messaging cannot create conversations.** `POST /api/v3/messaging/conversations`
   returns **500** for every persona (`create_conversation` performs an
   `INSERT ... ON CONFLICT (conversation_id, user_id) DO NOTHING` but
   `conversation_participants` has **no unique constraint** on that pair — the upsert is a
   no-op and Postgres errors). No conversation can be created in UI or API. (`MSG-1`)

Additional material findings: the **vehicles table does not exist in the running database**
(migration present in the repo, not applied) — the Vehicles tab and **org-wide search both
500**; the **Viewer role can upload documents** through the API (read-only role can write);
the **System Admin role cannot use admin-gated surfaces** (retention, commercial) because
`require_admin` only matches the role literally named `admin`; the **notifications bell is
broken for every user** (legacy direct-table query, RLS-denied); **facility creation fails
with an empty postcode** (DB check vs API schema mismatch); the **consultant cannot create
customers, upload documents, process, or map** — confirmed hypotheses, with no UI path at all.

**Security verdict:** No P0 data-leak/privilege-escalation issue was found. Cross-organisation,
cross-client, PE-boundary and role-gate negative tests were denied correctly at the API/RLS
layer (see the Security acceptance findings document). One P1 authorization defect: **Viewer
can upload documents** (a write on a read-only role).

**Acceptance verdict:** **NOT ACCEPTED for end-to-end business use.** Individual workflows work,
but the primary customer outcome (document → verified emissions → customer-approved report)
cannot be completed in the UI by any single actor or handoff.

---

## 2. Audit methodology

- **Persona simulation** against the live local stack (Supabase auth on `127.0.0.1:54425`,
  API on `localhost:8050`, DB on `127.0.0.1:54426`). Real login → real workspace → real screen
  (headless Chromium via CDP) → real action → real API → real authorisation → real DB state.
- **API/DB/RLS inspection** (read-only) to classify root cause; no mocks.
- **Negative testing** for every persona; every "denied" is a server-side HTTP 403 verified in
  the response body, never a UI-only hiding.
- **Cleanup:** every record created in this pass (3 uploaded test files, 1 facility,
  pipeline state on a demo item) was removed or restored. OHD-created artifacts from earlier
  sessions that are safe to remove were also removed (8 conversations, 7 factors); OHD-created
  facilities/suppliers/assets/items with referential weight were left intact and are listed in §30.
- Prior-session reports were **not** trusted; all their material claims were re-verified
  (they are largely confirmed — see cross-references).

## 3. Baseline tested

- Git `c36c848` (main). Working tree otherwise untouched by the audit.
- Running services: Supabase (local) + V3 API (`:8050`) + frontend (`:3006`) + website (`:3003`).
- No source, schema, RLS, migration, configuration or data file was modified.

## 4. Persona list (test identities)

Existing local demo accounts were used (no new accounts created — existing coverage was complete):

| Test identity | Persona | Organisation | Tested |
|---|---|---|---|
| owner.demo0001 | Customer Owner | Org A (Quayside Energy) | YES |
| admin.demo0001 | Customer Admin | Org A | YES |
| member.demo0001 | Customer Member | Org A | YES |
| viewer.demo0001 | Customer Viewer | Org A | YES |
| owner.demo0043 | Customer Owner | Org B (Dover) | YES |
| consultant.demo0001 | Consultant | CarbonTally Demo Ltd / Granite Solutions (multi-client) | YES |
| pe-manager-1.demo | PE Manager | Processing Entity A | YES |
| pe-staff-1.demo | PE Staff | Processing Entity A | YES |
| operator.demo | CarbonTally Operator | — | YES |
| reviewer.demo | CarbonTally Reviewer | — | YES |
| qc.demo | CarbonTally QC | — | YES |
| staff-admin.demo | Staff Admin | — | YES |
| system-admin.demo | System Admin | — | YES |

No test identities could not be created or authenticated. (No OHD accounts were created.)

## 5. Role × capability matrix (observed behaviour)

| Capability | Owner | Admin | Member | Viewer | Consultant | PE | Operator | Reviewer | QC | Staff Admin | Sys Admin |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Login & route | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Org profile edit | ✅ | ✅ | ✅403* | 403 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Members/invites | ✅ | ✅ | 403 | 403 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Upload document | ✅ | ✅ | ✅ | ✅ **BUG** | 403 | n/a | n/a | n/a | n/a | n/a | n/a |
| Facility create | ✅ | ✅ | ✅ | 403 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Facility edit | ❌ **no endpoint** | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Vehicles | ❌ **table missing** | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Custom factor approve | self-403 | ✅ | 403 | 403 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Customer review/approve | 500 **queue broken** | 500 | 403 | 403 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Client switch | n/a | n/a | n/a | n/a | ✅ | n/a | n/a | n/a | n/a | n/a | n/a |
| Consultant create client | n/a | n/a | n/a | n/a | ❌ **no UI** | n/a | n/a | n/a | n/a | n/a | n/a |
| PE assigned work | n/a | n/a | n/a | n/a | n/a | ✅ | n/a | n/a | n/a | n/a | n/a |
| PE unassigned work | n/a | n/a | n/a | n/a | n/a | ✅403 | n/a | n/a | n/a | n/a | n/a |
| Operator queue | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | 403 | ✅ | ✅ | ✅ |
| Validate item | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Calculate (UI) | n/a | n/a | n/a | n/a | n/a | **409** | **409** | 403 | **409** | **409** | **409** |
| Staff roster | n/a | n/a | n/a | n/a | n/a | n/a | ✅(view) | ✅(view) | ✅(view) | ✅ | ✅ |
| Retention (N3) | n/a | n/a | n/a | n/a | n/a | n/a | 403 | 403 | 403 | ✅ | **403 BUG** |
| Commercial config | n/a | n/a | n/a | n/a | n/a | n/a | 403 | 403 | 403 | ✅ | **403 BUG** |
| Org-wide search | ✅ | ✅ | ✅ | ✅ | 403 | 403 | n/a | n/a | n/a | n/a | n/a |

\* Member editing org profile is denied (403); viewer too. ✅ = verified working; ❌ = missing/blocked.

## 6. Authentication findings

- **AUTH-1 VERIFIED WORKING — persona routing.** All 13 identities authenticate via the
  Supabase password grant and land on the correct workspace: customers → `/` (V3 customer
  shell), consultant → `/consultant`, staff → `/ops`, PE staff → `/ops` (PE surface),
  system-admin → `/ops`. **No existing user was redirected to `/onboarding`** — the reported
  onboarding regression could not be reproduced. Root-cause check: post-login resolution runs
  `/api/v3/organizations/members/user/{id}` for customers and `/api/v3/ops/me` for staff/PE;
  both return correct data in the tested environment.
- **AUTH-2 VERIFIED — separation.** A customer calling `/api/v3/ops/me` → 403
  (`Staff access required`); a staff user cannot reach customer-org data without membership.
- **AUTH-3 NOISE (P3) — role-probe 403s.** Every page render fires `GET /api/v3/ops/me` and
  `GET /api/v3/consultants/me`, which 403 for non-staff/non-consultants; combined with the
  broken notifications fetch (NOT-1) this produces 10–30 console errors per page load. No user
  impact beyond console noise and slightly inflated request volume.

## 7. Customer findings

- **CUS-1 P1 BROKEN — customer review & approval.** `GET /api/v3/processing/customer-review`
  and `GET /api/v3/processing/queue?stage=review` → **500 `column reference "id" is
  ambiguous`** (backend SQL; an unqualified `id` in the JOIN). The customer `/review` screen
  shows "Something went wrong — Network error — please check your connection" (verified in
  browser). This blocks the handoff **CALCULATE → CUSTOMER REVIEW → CUSTOMER APPROVAL → REPORT**
  entirely. Root cause: **BACKEND/API (SQL)**; the misleading message is a **FRONTEND**
  error-handling defect (v3Fetch maps 500 → generic "Network error").
- **CUS-2 VERIFIED — documents.** Upload works for owner/admin/member (201; storage object +
  DB row). The documents page renders name/type/size and includes an "Emissions from this
  document" section (per-document emissions appear once items are calculated) — but the page
  is still file-browser flavoured, confirming the PO observation that documents emphasise file
  size over emissions outcome (P3 UX).
- **CUS-3 VERIFIED — emissions.** `/emissions` renders "Authoritative V3 calculation — the
  backend matches factors and computes results". A manual calculation persisted to the
  emissions history (server-authoritative; not a demo string).
- **CUS-4 P2 — viewer read-only is not reflected in the UI.** The Viewer sees enabled edit
  inputs and Save buttons (org metadata, profile) that return 403 on submit. "UI hiding is not
  security" cuts both ways: the API is secure, but the UI misleads the viewer into believing
  they can edit. UX defect.
- **CUS-5 VERIFIED — organisation profile/members.** Profile PUT persists across reload;
  member role changes and invitations work; viewer/member PUTs → 403.
- **CUS-6 P3 — route/label mismatch.** Route is `/organization` (US spelling) while the nav
  label is "Organisation" (UK). Trivial consistency issue.
- **CUS-7 P3 — reports for Org A.** `/reports` renders real rows; a prior-generation report
  honestly surfaces `Failed: no emissions_logs rows…` (no fabricated data).

## 8. Consultant findings (deep acceptance test)

- **CON-1 P1 BROKEN — cannot create customers/organisations.** No "Add client / New customer"
  action exists in the consultant UI. `POST /api/v3/consultants/me/clients` only **links an
  existing** organisation (422 without `organization_id`); `POST /api/v3/organizations`
  (D35 self-service) exists and is callable by the consultant, but it would make the caller
  the org **owner** — incompatible with the consultant model — and no consultant UI exposes it.
  **A consultant cannot onboard a new customer through the product.** (Confirmed PO hypothesis.)
- **CON-2 P1 BROKEN — cannot upload documents.** No upload entry point in the consultant UI;
  the API rejects consultants because they are not members of the client org (403
  `Organization member access required`). (Confirmed PO hypothesis.)
- **CON-3 P1 BROKEN — cannot process / extract / map.** No processing entry point; manual
  extraction and ops endpoints 403 for consultants. (Confirmed PO hypothesis.)
- **CON-4 PARTIAL — settings.** Consultant settings = **Firm branding** and **White-label**
  tabs only; none of the operational settings. (Confirmed PO hypothesis "lacks expected
  settings", narrowed: branding settings exist.)
- **CON-5 VERIFIED — client list & switching.** Two clients; the "CURRENT ORGANIZATION"
  selector switches the active client and every metric re-scopes (verified in browser:
  switching to Granite Solutions changed the workspace header and data). The banner
  "⚠ You are working on: {client} — every action here applies to this client only." is shown.
  **Active-client isolation holds for the visible data.**
- **CON-6 P2 — default active client dead-end.** The onboarding grant makes
  Dover Logistics the active client, but Dover is not a consultant-managed client, so the
  consultant workspace 403s on client data by default. A fresh consultant login lands on a
  "permission" dead-end until they switch client.
- **CON-7 P3 — formatting.** CO₂e figures render as raw floats without units ("8850.000000").
- **CON-8 P3 — console noise** (AUTH-3).
- **Cross-client isolation:** consultant active-client = Client A cannot read Client B data
  through the consultant surface; the org-scoped search API also denies consultants (403).
  No cross-client leak found. Note: full cross-client isolation of **document upload /
  processing** cannot be exercised because those consultant functions do not exist (CON-2/3).

## 9. PE findings

- **PE-1 VERIFIED — PE workspace & boundary.** PE staff see only entity-assigned work; the PE
  extraction workspace (source viewer, lines, save extraction) is real and persists. Attempts
  to read the org-scoped queue (403), customer org documents (403), unassigned batches, and to
  download customer documents (no download path; `file_url` empty) are **all correctly denied**.
  The D20 no-download boundary holds at UI + API level.
- **PE-2 P2 — PE Manager cannot see assigned work.** The PE Manager (staff role `reviewer`)
  fetching their entity's batch list → **403 `staff lacks permission: can_process`**. The
  manager's "Assigned batches" and "Entity performance" surfaces therefore render empty/zero
  even when work is assigned to the entity. Root cause: the entity batch-list endpoint is
  gated on `can_process`; the manager role only has `can_review`.
- **PE-3 P1 — PE cannot complete calculation from the UI** (PRC-1/PRC-2 apply identically to
  entity items: the entity `Calculate` button skips `start('calculation')` → 409; the entity
  demo item with unit `L` → 422).
- **PE-4 VERIFIED — Customer ↔ PE direct messaging not possible.** PE posts to a customer-org
  conversation are denied at the API layer (403). N1 isolation holds (creation itself is
  broken — MSG-1).

## 10. CarbonTally operations findings

- **OPS-1 VERIFIED — Operator.** Data-entry queue + workbench function (perms `can_process`,
  `can_view_all`). Claim/extract/map/validate all persist.
- **OPS-2 VERIFIED — Reviewer gate.** `can_review` only: operator queue → 403; validate → 200;
  calculate → 403 (needs `can_process`). Correct least-privilege.
- **OPS-3 VERIFIED — QC gate.** `qc_specialist` has `can_review + can_process`; QC queue
  renders; the QC tab honestly states recurring-quality identification is not supported by the
  current data model.
- **OPS-4 P1 — no one can complete calculation via the UI** (PRC-1). The operator's
  `Calculate` button on a validated item → 409.
- **OPS-5 VERIFIED — Staff Admin control plane.** Dashboard, Data entry, Review, QC, Staff,
  Roles, Entities, SLA, Issues, Messaging, Audit, Settings (retention), Commercial all render
  from real endpoints; retention read 200; commercial config 200.
- **OPS-6 P1 — System Admin role cannot use admin-gated surfaces.** `system-admin.demo`
  accesses `/ops/me`, `/ops/staff`, `/ops/entities`, `/ops/dashboard`, `/ops/queues/review`
  (200) but **403s on `/api/v3/settings/retention` and all `/api/v3/commercial/*`** because
  `require_admin()` matches only `role == 'admin'`/`role_name == 'admin'` and the
  `system_admin` role is never mapped to admin authority. **The System Admin persona cannot
  operate retention/commercial/billing configuration** — the role exists but is only
  partially wired into the permission model.

## 11. Admin findings

- **SA-1 VERIFIED — Staff management.** Roster, role select, entity scope, create form work.
- **SA-2 VERIFIED — Commercial.** Billing mode (CREDIT/STANDARD) with explicit non-silent
  change semantics; versioned rules; plans catalogue. Read surfaces verified.
- **SA-3 P2 — publish/save round-trips** for commercial versions and retention values were not
  executed (they would persist platform-wide configuration). Endpoints + UI exist; marked for
  Cline acceptance test.
- **SA-4 P3 — stray test role.** `t_ba_34e3cb` appears in `staff_roles` and the role
  selector — test data leaking into a production-facing control plane.
- **SA-5 P3 — operator can view the staff roster and entities** (via `can_view_all`).
  Likely intended for the internal ops dashboard, but "general staff can list the staff
  roster" should be confirmed against the access model.

## 12. D17 — master-data findings (actual CRUD)

- **MD-1 P1 BROKEN — facility create without postcode.** `POST …/facilities {name}` →
  **500** `violates check constraint facilities_postcode_or_eircode_check`. The API schema
  allows `postcode: null`, but the DB CHECK requires postcode **or** eircode. The "+ New
  facility" form with an empty postcode shows a generic "Action failed" toast. Facility
  **read/list/create-with-postcode/soft-delete** work (delete = `is_active=false` soft
  archive). **There is no facility EDIT endpoint at all** (no PUT) — "Facilities cannot be
  properly viewed/edited" is confirmed at the API level.
- **MD-2 P1 BROKEN — Vehicles.** `GET/POST /api/v3/vehicles` → **500
  `relation "public.vehicles" does not exist`**. The `vehicles` table is absent from the
  running database; migration `supabase/migrations/20260825000000_v3m7_vehicles.sql` exists
  in the repo but was **not applied** to the local DB. The Vehicles tab shows an error for
  every org user. **Knock-on: org-wide search also 500s** because the search SQL reads
  `vehicles` (SRH-1). Root cause: ENVIRONMENT/DEPLOYMENT (migration not applied); from the
  acceptance standpoint the feature is not implementable in the current environment.
- **MD-3 VERIFIED — Locations (N2).** The Locations tab honestly states the resolution
  ("CarbonTally models locations on the facilities entity — manage the underlying records in
  the Facilities & Assets tab") and lists the org's facilities. **The PO example "Owner cannot
  create Locations" is resolved by design**; no separate locations create exists (intentional).
  A cross-link affordance would help (P3).
- **MD-4 VERIFIED (with a UX defect) — Assets.** Assets list/create work; the asset `type`
  column exists and is editable; the assets list renders the **raw `facility_id` UUID instead
  of the facility name** (UX defect, P3). Some seeded assets have null types (sparse seed
  data — the reason the PO saw "—").
- **MD-5 VERIFIED — Suppliers.** List/create/update API work; the Suppliers tab has a
  "+ New supplier" dialog; **no edit UI** exists even though the API supports update (P3).
- **MD-6 PARTIAL — detail/edit.** Asset detail exists; facility/asset edit endpoints are
  absent (MD-1). Editing round-trips could not be tested where the endpoint does not exist.

## 13. Documents findings

- **DOC-1 VERIFIED — upload pipeline.** Upload → storage object + `organization_files` row +
  upload batches + documents page. `POST /api/v3/uploads` works for owner/admin/member
  (**and viewer — see SEC-1**).
- **DOC-2 P1 — document-to-emissions outcome blocked** by PRC-1/PRC-2 (UI cannot reach
  `calculated`) and PRC-3 (customer review queue 500).
- **DOC-3 P3 — file-manager orientation.** "NAME TYPE SIZE UPLOADED" table; the emissions
  outcome is a secondary section. PO observation substantially confirmed.
- **DOC-4 PARTIAL — issue/document search.** In-org document search works when the search
  endpoint is healthy, but the org-wide search currently 500s on the missing `vehicles` table
  (SRH-1).

## 14. Processing findings

- **PRC-1 P1 BROKEN — UI cannot complete calculation.** The ops/entity workbench
  `Calculate` action calls `calculateItem()` directly; the backend requires
  `validated → calculating → calculated` via `startItem(id,'calculation')`, which no UI
  component ever calls. Verified: reviewer validates (200) → operator `Calculate` → **409**
  `transition validated→calculated not allowed`. Root cause: FRONTEND (missing stage call) +
  BACKEND (strict state machine that the UI doesn't drive).
- **PRC-2 P1 BROKEN — unit aliases break matching.** The correct DEFRA factor is stored with
  unit `litres`; item activity is entered with unit `L`; `_resolve_unit_for_factor` only does
  exact/substring matching → **422 `UNIT_MISMATCH`** on a perfectly mapped diesel item.
  Common abbreviations (`L`, `t`, `kg`, `kWh`) must be normalised server-side.
- **PRC-3 P1 BROKEN — customer review queue 500** (CUS-1). The handoff
  CALCULATE → CUSTOMER REVIEW → CUSTOMER APPROVAL → REPORT cannot happen.
- **PRC-4 VERIFIED — the API pipeline works when driven precisely.** Driving the demo diesel
  item exactly (extract → map → validate → `start('calculation')` → calculate) produced
  **10,732.4 kg CO₂e** — the correct DEFRA 2026 value for 4,258.9 L at 2.52 kg/L. The engine
  is sound; the UI cannot reach it. Corroboration: an earlier audit session drove a complete
  chain through the API on its own test org (upload → batch → extract/map/validate/calculate →
  customer approve → annual report PDF), confirming the engine, the approval action and report
  generation all work at the API level — only the UI path and the review-queue listing are
  broken.
- **PRC-5 P2 — mapping-options quality.** `GET /api/v3/mapping-options?activity=Diesel`
  returns the biofuel/car factors but not the correct "Diesel (average biofuel blend) — litres"
  factor within the default 20 results; operators must page or search by factor name.
  `GET /api/v3/mapping-options` without an activity returns no factors (top-level match only).
- **PRC-6 P2 — PE Manager batch list 403** (PE-2).

## 15. Calculation findings

- **CAL-1 VERIFIED — server-authoritative engine.** Factor matching, precedence, scope/country/
  year filtering, unit conversion (when units match), CO₂e computation and persistence are
  real; the demo record (10,732.4 kg ≈ 10.7 t) is reproducible via the API.
- **CAL-2 P1 — the UI cannot produce a calculated item** (PRC-1/2). Until fixed, the customer
  review queue, evidence chains, and reports will never contain newly-processed items.
- **CAL-3 P2 BROKEN — reference endpoint.** `GET /api/reference/fuel-types` → **500
  PGRST205** (schema cache references `public.defra_conversion_factors`, which does not exist;
  the data lives in `emission_factors`). Any fuel-type dropdown using this endpoint is broken.

## 16. Evidence findings

- **EVD-1 PARTIAL — evidence chain exists in schema** (source → extracted lines → mapped
  factor → calculation → emissions log → report), but a complete chain requires items to reach
  `calculated`, which the UI cannot do (PRC-1). The public demo's "fully evidenced" record
  (INV-2026-0417 → 10.7 t) renders, but as demo data, not via a live UI workflow.
- **EVD-2 VERIFIED — no overclaiming.** No screen claims certification or independent
  assurance; language is honest ("evidence", not "assurance").
- **EVD-3 PARTIAL — immutable finalised evidence** not exercisable (no finalisation path in
  current flows; reports generate from logs). D7.3-style finalisation remains unverified.

## 17. Reporting findings

- **RPT-1 VERIFIED — reports from real data.** Ready/Queued/Failed statuses render; failed
  generation surfaces the honest error ("no emissions_logs rows for organisation…"); export
  CSV/JSON works.
- **RPT-2 P1 — customer approval of reports blocked** by PRC-3 (review queue 500). A report
  cannot complete the review → approval handoff in the UI.
- **RPT-3 PARTIAL — report detail** (View action) not fully exercised in this pass; the
  generation + download paths were.

## 18. Custom-factor findings

- **CF-1 P2 — single-owner orgs cannot approve owner-created factors.** Self-approval → 403
  (correct no-self-approval), but with only one owner in the org, no other actor can approve;
  the owner still sees the enabled "Approve" affordance (dead button). Statuses observed:
  `draft`/`active`; no separate "pending review" stage exists. **The authoritative docs do not
  define who approves an owner-created factor in a single-owner org → PO DECISION REQUIRED**
  (self-approval exception for org owners, or an explicit CarbonTally reviewer path).
- **CF-2 VERIFIED — lifecycle mechanics.** Create (draft), edit draft, approve (admin/owner),
  deactivate, rejection-on-self-approval all behave correctly at the API layer.
- **CF-3 PARTIAL — factor search** works; precedence against DEFRA factors per D9 is
  implemented (custom factor matched and used when active).

## 19. Messaging / N1 findings

- **MSG-1 P1 BROKEN — conversation creation 500s.** `POST /api/v3/messaging/conversations`
  returns **500** for every persona (ownerA, member, consultant verified). Root cause:
  `create_conversation` inserts the conversation, then inserts participants with
  `INSERT … ON CONFLICT (conversation_id, user_id) DO NOTHING` — but
  `conversation_participants` has **no unique constraint** on that pair, so the upsert clause
  is invalid and Postgres raises. **No conversation can be created through UI or API**;
  N1 (Supabase Realtime messaging) is not usable end-to-end. Prior-session send/reply on a
  pre-existing thread worked, which is consistent: only creation is broken.
- **MSG-2 P2 — the authenticated bell/messaging is not Realtime-driven yet.** The messaging
  list in the customer shell loads from the API; Realtime subscription behaviour was not
  observed (creation fails first). Unread-state handling is incomplete in the UI.
- **MSG-3 VERIFIED — Customer ↔ PE direct messaging not possible** (API denies PE posting into
  customer-org conversations; the UI explicitly states PEs never participate).
- **MSG-4 P2 — notifications bell broken for every user** (NOT-1): the bell queries the
  `notifications` table directly via the Supabase JS client with a `user_id` filter, but the
  table has **no `user_id` column** (uses `recipient_id`/`recipient_type`) and **RLS is
  enabled with zero policies**, so the query errors on every page. The working
  `/api/v3/notifications` endpoint is never called by the bell (legacy code path).
- **MSG-5 P3 — N1 isolation** otherwise holds (participant validation + PE denial).

## 20. AI assistant findings

- **AI-1 VERIFIED — architectural distinction preserved.** The public website FAQ assistant is
  deterministic local knowledge (no AI provider/key, deep-links to `/faq#faq-…`). It is not an
  alternate permission system and does not receive authenticated data. Authenticated AI is a
  separate (unselected) programme decision — no provider or credentials were fabricated.
- **AI-2 PARTIAL — the authenticated shell's "CarbonTally Assistant"** widget renders on
  authenticated pages but is the same public FAQ knowledge layer; its presence inside the
  authenticated shell is acceptable per N1 as long as it is not the primary communication
  mechanism (which it is not — messaging is the V3 surface, currently broken per MSG-1).

## 21. D19 findings

- **D19-1 PARTIAL — split workbench is real.** The ops/PE extraction workspace has a source
  pane + data pane, claim/save/draft/map/calculate actions, autosave indicator, validation
  findings, and view-only source viewer. These work against real data.
- **D19-2 NOT IMPLEMENTED — top workflow nav & split presets.** The Queue→Extract→Map→
  Validate→Review→QC→Evidence top workflow navigation, the 40/60 · 50/50 · 60/40 split
  presets, and keyboard divider control are **not exposed** in the ops/PE extraction screen
  (tab navigation with a default split instead). This is the frozen D19 direction (Option B+C)
  and remains unimplemented in the workbench surface.
- **D19-3 PARTIAL — confidence/linking.** Source↔field linking and per-field confidence are
  partially present in the extraction surface; full D19 parity (locked items, inline
  validation, evidence tab) is not reachable because the workflow cannot advance past
  calculation.

## 22. D21 findings

- **D21-1 PARTIAL — design tokens consistent** across the V3 customer/ops/consultant surfaces
  (buttons, tables, status badges, alerts, forms). Legacy styling remains in the website and
  in a few pages (P3).
- **D21-2 P3 — inconsistent states.** "Permission denied" and destructive-action confirmations
  are handled inconsistently; some 403s surface as generic "Action failed" toasts; several
  empty states (PE manager, client messages) are the *result* of swallowed API errors rather
  than true empty states.
- **D21-3 PARTIAL — accessibility.** Heading hierarchy was previously fixed; the mobile
  workbench loads without horizontal overflow (verified at 390 px). Keyboard divider control
  is absent (D19-2).

## 23. API findings

- **API-1 P1 — customer review queue SQL** (`column reference "id" is ambiguous`): PRC-3.
- **API-2 P1 — messaging insert bug** (`ON CONFLICT` without a constraint): MSG-1.
- **API-3 P1 — search 500** (missing `vehicles`): SRH-1.
- **API-4 P1 — facility CHECK mismatch** (postcode null): MD-1.
- **API-5 P2 — `/api/reference/fuel-types` stale schema**: CAL-3.
- **API-6 P2 — unit alias resolution**: PRC-2.
- **API-7 P2 — no facility/asset edit endpoints**: MD-1/MD-6.
- **API-8 P3 — misleading error mapping**: v3Fetch reports any non-JSON/500 response as
  "Network error — please check your connection", which hid the review-queue 500 from users.

## 24. Database findings

- **DB-1 P1 — `vehicles` table absent** while migration exists: MD-2.
- **DB-2 P2 — `conversation_participants` lacks the unique constraint the code assumes**: MSG-1.
- **DB-3 P2 — `notifications` table has RLS enabled with zero policies** (direct queries
  always denied; the bell is broken rather than leaking): NOT-1.
- **DB-4 P2 — `facilities` CHECK requires postcode/eircode while the API allows null**: MD-1.
- **DB-5 P3 — stale schema cache for `defra_conversion_factors`**: CAL-3.

## 25. RLS / security findings

See `CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md` for the full table. Highlights:
- **SEC-1 P1 — Viewer can upload documents** (201). The upload endpoint gates on
  `require_org_member()`, which the read-only Viewer role passes. This is a write on a
  read-only role. UI disables the button; the API does not.
- **SEC-2 VERIFIED — cross-org isolation.** Owner A cannot read/search/upload into Org B and
  vice versa (403 at API). Search cross-org → 403.
- **SEC-3 VERIFIED — PE boundary.** Unassigned work, customer org docs, document download,
  and customer-org messaging all denied (403 / no path).
- **SEC-4 VERIFIED — role gates.** Member/viewer cannot approve items, edit org profile, or
  manage members (403). Reviewer cannot run the operator queue or calculate (403). Customers
  cannot reach staff surfaces (403 all-false).
- **SEC-5 P2 — System Admin role cannot reach admin-gated config** (OPS-6) — a
  role-mapping gap, not a leak.
- No P0 (data leak / privilege escalation / corruption) found.

## 26. Negative-test results

| Attempt | Result | Verdict |
|---|---|---|
| Viewer → upload document (API) | 201 | ❌ **ALLOWED — SEC-1** |
| Viewer/Member → approve processed item | 403 | ✅ denied |
| Viewer/Member → edit org profile | 403 | ✅ denied |
| Viewer/Member → add member | 403 | ✅ denied |
| Owner A → read/search/upload Org B | 403 | ✅ denied |
| Owner B → read/search Org A | 403 | ✅ denied |
| Reviewer → operator queue | 403 `can_process` | ✅ denied |
| Reviewer → calculate | 403 | ✅ denied |
| Customer → staff ops surface | 403 | ✅ denied |
| PE → org queue / customer docs / download / messaging | 403 / no path | ✅ denied |
| Consultant → upload into client org | 403 | ✅ denied (functionality gap, not a leak) |
| Consultant → inactive-client data (search) | 403 | ✅ denied |
| Owner → self-approve custom factor | 403 | ✅ denied (CF-1 for the dead-end) |
| Operator/Reviewer/QC/SysAdmin → retention | 403 (SysAdmin should pass — OPS-6) | ✅ denied / ⚠ role gap |

## 27. Complete gap register

| ID | Severity | Area | Status | Root cause |
|---|---|---|---|---|
| PRC-3 / CUS-1 | P1 | Customer review & approve | BROKEN | BACKEND SQL |
| MSG-1 | P1 | N1 messaging creation | BROKEN | BACKEND/DATABASE |
| PRC-1 | P1 | UI calculate (stage gate) | BROKEN | FRONTEND + BACKEND |
| PRC-2 | P1 | Unit alias matching | BROKEN | BACKEND |
| MD-2 | P1 | Vehicles (+search knock-on) | BROKEN | ENVIRONMENT/DEPLOYMENT |
| SRH-1 | P1 | Org-wide search | BROKEN | ENVIRONMENT (vehicles) |
| SEC-1 | P1 | Viewer upload | ALLOWED | BACKEND/AUTHORIZATION |
| CON-1..3 | P1 | Consultant create/upload/process/map | NOT IMPLEMENTED | PRODUCT/UX |
| OPS-6 | P1 | System Admin role gaps | BROKEN | BACKEND/AUTHORIZATION |
| MD-1 | P1 | Facility create without postcode | BROKEN | BACKEND + DATABASE |
| NOT-1 | P2 | Notifications bell | BROKEN | FRONTEND (legacy) + DATABASE |
| PRC-5 | P2 | Factor search quality | PARTIAL | BACKEND |
| PRC-6/PE-2 | P2 | PE Manager batch list | BROKEN | BACKEND |
| CF-1 | P2 | Owner-factor approval (single-owner org) | PARTIAL | PO DECISION REQUIRED |
| CAL-3 | P2 | fuel-types reference | BROKEN | BACKEND (schema cache) |
| CUS-4 | P2 | Viewer UI shows edit affordances | PARTIAL | FRONTEND UX |
| D19-2 | P2 | Workbench top nav/presets/keyboard | NOT IMPLEMENTED | FRONTEND |
| MD-6/API-7 | P2 | Facility/asset edit | NOT IMPLEMENTED | BACKEND |
| RPT-2 | P1 | Customer report approval handoff | BROKEN | (depends PRC-3) |
| AUTH-3 | P3 | Role-probe console noise | PARTIAL | FRONTEND |
| CUS-6 | P3 | /organization vs "Organisation" | PARTIAL | FRONTEND |
| MD-4/UX | P3 | Asset list raw UUID | PARTIAL | FRONTEND |
| SA-4 | P3 | Stray test role in roster | PARTIAL | TEST DATA |
| MD-3 | P3 | Locations cross-link affordance | PARTIAL | UX |

## 28. P0/P1/P2/P3 summary

- **P0: none.**
- **P1 (10):** PRC-1, PRC-2, PRC-3(CUS-1), MSG-1, MD-2/SRH-1, SEC-1, CON-1/2/3, OPS-6, MD-1, RPT-2.
- **P2 (11):** NOT-1, PRC-5, PE-2, CF-1, CAL-3, CUS-4, D19-2, MD-6/API-7, PRC-6, MSG-4 (same as NOT-1), DB-2/3/4.
- **P3:** styling, labels, formatting, console noise, stray test role, asset UUID display, locations link.

## 29. PO decision items

1. **CF-1 — who may approve an owner-created custom factor in a single-owner organisation?**
   Options: org-owner self-approval exception, or CarbonTally reviewer path. (Not determined by
   D1–D21/N1–N3.)
2. **OPS-6 — is `system_admin` expected to manage retention/commercial config?** If yes, map
   the role to admin authority (or grant the underlying permissions).
3. **CON-1..3 — consultant customer-creation model.** Confirm whether consultants may create
   organisations (and under whose ownership) or must use the D35 self-service path. (D-model
   implies consultants operate on existing orgs; the missing UI remains.)
4. **PE-2 — should the PE Manager (reviewer role) view the entity batch list?** Manager
   oversight suggests yes.

## 30. Environment limitations & test-data cleanup

- Environment confirmed **local/dev** (Supabase local on 54425/54426, API on 8050) before any
  test action. No production data was touched.
- **Removed this pass:** 3 uploaded `ohd_test.txt` files (storage objects + DB rows), 1 test
  facility, pipeline state on the demo item restored to `pending`, 8 OHD-named conversations
  and 7 OHD-named custom factors from earlier sessions (unreferenced, safe to remove).
- **Left intact (OHD-created test data from earlier sessions, with referential weight):**
  facilities "OHD Facility Alpha" (+5 assets), "OHD Facility Bravo", "OHD Test Facility A"
  (+1 asset); suppliers "OHD Test Supplier 2 (renamed)", "OHD Synthetic Fuels Ltd";
  items `ohd_test_invoice.pdf` (validated) and the batch `c743b982…` electricity items
  (calculated). These remain so as not to break referential integrity/evidence; they are
  clearly identifiable by the `OHD` prefix.
- **No OHD accounts were created in this pass** (existing demo accounts sufficed). Prior
  audit sessions did create OHD identities and an OHD org ("OHD Audit Org Ltd", `ohd.*@
  test.carbontally.local` accounts, a `viewer_up.pdf` document, a supplier, and an approved
  test item); those remain in the local database, clearly labelled with the OHD prefix, and
  are not part of this pass's footprint. Prior-session deliverables were preserved in
  `previous-session/`.

## 31. Final acceptance assessment

**Can a Customer Owner operate CarbonTally end-to-end? NO.** Upload → processing works and the
calculation engine is correct, but the UI cannot complete calculation (PRC-1/2) and the
customer cannot review/approve (PRC-3). Owner master-data management is partially blocked
(facility edit missing, vehicles dead, facility create fragile).

**Admin/Member?** Same operational ceiling as Owner; member cannot perform owner-only actions
(correct).

**Viewer truly read-only? NO.** Read-only at the UI, but the API lets a Viewer upload
documents (SEC-1).

**Consultant manage and process customers? NO.** Client viewing/switching works; creating
customers, uploading, processing and mapping are absent (CON-1..3).

**PE staff perform assigned extraction work? PARTIALLY.** Extraction/mapping work and the
document boundary are correct; calculation cannot be completed from the UI, and the PE manager
cannot see assigned work (PE-2/3).

**Operators process work? PARTIALLY.** Same calculation ceiling. Reviewers/QC gates are
correct.

**Staff Admin / System Admin control plane?** Staff Admin: YES (all admin surfaces work).
System Admin: PARTIAL — ops read surfaces work, but admin-gated retention/commercial config
403 (OPS-6).

**Can a document become a real emissions result? PARTIALLY — engine YES, UI NO.**
The API chain produces the correct 10.7 t result when driven precisely; the UI cannot reach it.

**Result → evidence → report → customer approval? NO.** Reports generate from logs; the
customer approval handoff is broken (PRC-3).

**N1 messaging? NO.** Cannot create conversations (MSG-1).

**D17 master data usable? PARTIALLY.** Facilities/assets/suppliers basic CRUD; vehicles dead;
facility edit missing; facility create fragile.

**D19 workbenches usable? PARTIALLY.** Split source/data panes work; frozen top-nav + preset
direction not implemented.

**D21 consistent? PARTIALLY.** Tokens consistent; state/error handling inconsistent.

**Authorization/RLS correct? MOSTLY.** No P0; one P1 (viewer upload); system-admin role gap.

**What should Cline implement next?** See `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md`.

**Overall: NOT ACCEPTED for end-to-end business use.** The engineering is real and the security
boundaries are largely sound, but the primary customer outcome cannot be completed in the UI.
