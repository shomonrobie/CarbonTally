# CarbonTally V3 — Phase 1 Core Business Workflow Restoration Report

**Date:** 2026-08-29
**Implementer:** Cline
**Baseline commit:** `c36c848` (HEAD = `origin/main`, verified)
**Task:** CarbonTally V3 Phase 1 — restore the core emissions-processing lifecycle
(Organization → Customer/Consultant access → Document → Batch → Extraction →
Mapping → Validation → Calculation → Review → Approval → Emissions → Evidence →
Reporting) against the current repository state and the authoritative OHD audit
findings (PRC-1..3, CL-1..CL-41, ISC-1..ISC-16, UH-1..UH-12, PO Decisions 1–4).

---

## 1. Baseline

- `git rev-parse HEAD` = `c36c848759e2099d9f86e537000e77f74d9b0aae` (`main`, in sync with `origin/main`).
- Verified live stack: backend `localhost:8050`, frontend `localhost:3000`,
  Supabase auth `127.0.0.1:54425`, Postgres `127.0.0.1:54426`.
- The investor-scale demo dataset (976 orgs / 1,325 users / 1,185 demo identities /
  916 consultant-client assignments / 221 items / 27 snapshots / 27 emissions) was
  **preserved** — no reset, no destructive seed, no truncation. Only rows explicitly
  identified as audit-invalid legacy/test artifacts were removed (see §7).

## 2. Files changed

### Backend (implementation)

| File | Change |
|---|---|
| `backend/core/units.py` | **NEW** — canonical unit-alias table (`L`↔`litres`, `t`↔`tonnes`, `kWh`↔`kWh (Gross CV)`, `m3`↔`cubic metres` …), `normalize_unit`, `units_equivalent`, `resolve_unit_for_factor`, currency-unit detection, honest `mapping_no_factors_reason` (CL-3/PRC-2, ISC-9/CL-32). |
| `backend/data/manual_extraction.py` | Fixed the CL-1 500: JOIN queries qualify every item column (`_ITEM_COLUMNS_I` = `i.`-prefixed); `list_customer_review` now returns `customer_review` + `calculated` items and excludes cancelled batches; added `find_item_by_file` (UH-7 resolution). |
| `backend/data/issues.py` | Added `resolve_open_for_item` / `resolve_open_for_batch` so clean validation/approval closes stale blocking issues (ISC-2/CL-26). |
| `backend/data/emission_factors.py` | `find_by_activity` normalises the unit alias server-side and orders exact-unit matches first (CL-3/CL-14). |
| `backend/data/exports.py` | Emissions list joins snapshot `activity`/`activity_type` + factor name (ISC-3). |
| `backend/data/organizations.py` | Facilities payload now carries `is_active`/`type`/`country` (ISC-7); assets list joins the facility **name** (ISC-4/CL-19). |
| `backend/data/tenant.py` | Full facility/asset **edit** surface (name/type/address/postcode/is_active/metadata) (MD-1/ISC-4). |
| `backend/domain/organization.py` | `Facility`/`Asset` domain models carry `is_active`, `type`, `country`, `facility_name`. |
| `backend/engines/processing_workflow.py` | Human-friendly validation messages (no debug prose) (CL-37/UH-4). |
| `backend/data/reporting.py` | Reworded the QC "NOT SUPPORTED" technical prose (CL-40/UH-8). |
| `backend/auth.py` | PO Decision 2 — `ADMIN_ROLE_NAMES`; `require_admin`/`require_org_admin`/`require_role` honour `system_admin` (superset, least privilege otherwise). |
| `backend/api/v3_operations.py` | ISC-1 `source_item_id` in both calculate paths; unit-normalised calculation; mapping-options `no_factors_reason`; issue resolution on clean validate; review queue resolves real items + reviewer names (UH-7); `_resolve_unit_for_factor` uses `core.units`. |
| `backend/api/v3_processing_workflow.py` | Unit-normalised calculate; review queue includes calculated items; consultants (active grant) may operate client processing (PO Decision 3 via `ensure_processing_org_access`); issue resolution on validate + approve. |
| `backend/api/v3_consultants.py` | **NEW** `POST /me/customers` — consultant creates a customer org + owner identity + active client grant (CON-1/PO Decision 3). |
| `backend/api/v3_organizations.py` | Facility create without postcode → 422; asset without valid facility → 422; **new** `PUT /facilities/{id}` and `PUT /assets/{id}` edit endpoints (MD-1/ISC-4). |
| `backend/api/customer_factors.py` | PO Decision 1 — org OWNER may approve their own custom factor (self-approval removed for owners only). |
| `backend/api/dependencies.py` | **NEW** `ensure_processing_org_access` — org member OR authorised consultant (active grant); Processing-Entity staff always denied. |
| `backend/routes/reference.py` | `fuel-types` now reads the authoritative `emission_factors` (CAL-3/CL-15). |


### Frontend

| File | Change |
|---|---|
| `frontend/src/v3/ops/ExtractionPanel.jsx` | CL-2 — Calculate first claims the `calculation` stage; CL-37 — sanitises legacy debug-placeholder field values. |
| `frontend/src/v3/ops/OperatorQueue.jsx` | UH-1/UH-2 — workbench-first: opening an item collapses the queue wall to a compact summary + scrolls to top; Previous/Next stay inside the open item. |
| `frontend/src/v3/ops/ReviewQueue.jsx` | UH-7 — opens the real `item_id`, shows reviewer display names. |
| `frontend/src/v3/admin/FacilitiesTab.jsx` | Assets show the facility name; facility + asset **Edit** forms (MD-1/ISC-4). |
| `frontend/src/v3/admin/CustomFactorsTab.jsx` | Decision-1 copy (owner may self-approve). |
| `frontend/src/v3/api.js` | `updateFacility` / `updateAsset` client functions. |
| `frontend/src/hooks/useNotifications.js` | ISC-6 — uses `/api/v3/notifications` (+ defined `API_URL`/`getToken`); fixes legacy 404 noise. |
| `frontend/src/v3/customer/DashboardPage.jsx` | UH-3/CL-41 — h1 "Home"; CL-39 — member-activity retry-once on 0-status. |
| `frontend/src/v3/customer/MessagingPage.jsx` | h1 "Messaging" (CL-41). |
| `frontend/src/v3/customer/EmissionsPage.jsx` | Shows the factor name from the snapshot join (ISC-3). |
| `frontend/src/v3/v3.css` | CL-38 — 2-column stat grid ≤ 640 px. |
| `frontend/src/App.css` | CL-40 — residual `#2d6a4f` decorative gradients consolidated to `#2f855a`. |

### Migrations (created + applied locally)

| Migration | Purpose |
|---|---|
| `supabase/migrations/20260828000000_v3m8_messaging_unique_participants.sql` | MSG-1 — UNIQUE `(conversation_id, user_id)` on `conversation_participants` (de-dupe + drop non-unique index). |
| `supabase/migrations/20260828010000_v3m8_system_admin_role_model.sql` | PO Decision 2 — `system_admin` gains `can_manage_billing`; CL-22 — stray `t_ba_34e3cb` test role/profile removed. |
| `supabase/migrations/20260828020000_v3m8_pe_manager_role.sql` | PO Decision 4 — dedicated `pe_manager` staff role (can_process + can_review + can_view_all); demo PE managers re-roled. |

Also **applied** the previously-unapplied `20260825000000_v3m7_vehicles.sql`
(CL-4/MD-2) to the local database.

### Tests

- `backend/tests/unit/test_units.py` — **NEW** unit-alias/normalisation/currency regressions.
- `backend/tests/unit/api/test_phase1_core_regressions.py` — **NEW** CL-1 queue, ISC-1 snapshot `source_item_id`, ISC-10/PO-D2 system-admin authorizer.
- `backend/tests/unit/api/test_v3_operations.py` — ISC-2 issue-lifecycle + UH-7 review-queue resolvability.
- `backend/tests/unit/api/test_v3_customer_factors.py` — PO Decision 1 owner self-approval.
- `backend/tests/unit/api/test_v3_customer_admin.py` — ISC-4 asset 422 (fixed invalid fixture id).
- `backend/tests/unit/api/fakes.py` — fakes mirror the new repository behaviour.


## 4. Security / RLS changes

- **No RLS policy weakened.** All access changes are additive API-authorization paths
  that re-check the authoritative boundary server-side:
  - Consultant processing is gated by `consultant_clients.status = 'active'`
    (`ensure_consultant_org_access`), re-checked per request; cross-firm and
    unrelated-customer isolation unchanged (verified: consultant2 -> client context 403).
  - Processing-Entity staff remain structurally excluded from customer organisations
    and messaging (`is_entity_staff` denied in `ensure_processing_org_access`; the
    existing PE no-download/signed-URL boundary intact — verified PE -> customer doc 403).
  - `system_admin` is a *superset* of `admin` for the legacy `require_admin` /
    `require_role(["admin"])` gates; operator/reviewer/qc/entity staff retain
    least privilege (verified: operator -> legacy audit 403; entity-staff with an
    admin-named role -> legacy audit 403).
- RLS behaviour suites (`test_scope_aware_authorization.py`,
  `test_operations_auth.py`, `test_v3_entity_extraction.py`, `test_storage_security.py`)
  all pass unchanged.

## 5. Database / schema changes

- Migrations listed in §2 applied to the local Postgres (no destructive DDL; all
  additive/idempotent except the audit-identified test-row cleanup).
- Demo-data hygiene (CL-40/UH-10/UH-12): removed the 3 `ohd_test.txt` items from
  Quayside's customer-visible "Uploads" batch (audit-identified invalid artifacts);
  renamed the 6 test processing entities (`Babui` x4, `A`, `B`) to distinct
  `Test Processing Entity ...` names (referenced staff profiles prevent deletion);
  removed the audit-identified phantom `manual_review_queue` rows and created 2
  **real** review rows linked to real extraction items (so the reviewer demo works).
- Assigned Quayside's "Uploads" batch to Processing Entity Alpha so the PE Manager

## 6. Tests run / results

| Suite | Result |
|---|---|
| `backend/tests/unit` (full) | **All pass** (EXIT=0) — includes the new regression files. |
| `backend/tests/integration` | Pre-existing environment-dependent failures unchanged (DB-backed suites; not related to this phase). |
| Frontend `react-scripts build` | **EXIT=0** ("Compiled with warnings" — pre-existing `App.js` unused-var warnings only). |
| Frontend `react-scripts test` (src/v3) | **6 suites / 118 tests pass** (EXIT=0). |
| Live API probes | customer-review 200 (was 500); messaging conversation create/send 200; system_admin legacy audit 200 (was 403); PE manager batches 200 (was 403); consultant create-customer 201 + isolation 403; facility/asset 422s; vehicles 200; fuel-types 200; approve->evidence chain 200. |

## 7. Demo-data preservation confirmation

- No database reset, destructive seed, truncation, or full re-seed was performed.
- The investor-scale dataset (976 orgs, 1,325 users, 1,185 demo identities, 916
  consultant-client assignments, 221 items, 27 snapshots, 27 emissions logs) remains
  intact. The only removals were rows explicitly identified by the audits as invalid
  legacy/test artifacts (`ohd_test.txt` items, phantom `manual_review_queue` rows,
  stray `t_ba_34e3cb` test role). One Quayside item was moved from `calculated` to
  `approved` through the restored customer-approval journey (a legitimate workflow
  demonstration). One batch was entity-assigned to Alpha for the PE demo.
- Storage was **not** re-seeded (the previous missing-document alarm was a false
  positive, per the task instructions).

## 8. Acceptance-workflow results (real persisted data)

- **Customer Owner:** review queue lists the calculated item -> approve returns 200 ->
  item `approved` with stamps -> emissions list includes `activity`/`factor_name` /
  `source_item_id` -> evidence endpoint resolves the full chain. Facility/asset
  create/edit + vehicles + fuel-types all verified live.
- **Consultant:** creates a customer (org + owner + active client link, 201);
  sees the new client in `/me/clients`; client context 200; **cross-firm client 403**;
  processing dashboard/queue for a managed client 200.
- **PE Manager:** `/ops/me` shows the entity; assigned batches 200; batch items 200;
  item workspace 200 (signed URL); customer document 403 (no-download boundary intact).
- **Reviewer/QC:** review queue returns 2 resolvable real items (no 1111/2222
  synthetic rows) with `item_id`; "Open workspace" targets the real item.
- **Staff Admin / System Admin:** system_admin can read the legacy admin audit and
  has `can_manage_billing` (Commercial surface reachable).

## 9. Remaining known issues / not completed

- The D19 standalone **routed** workbench page (canonical E1->E2) is implemented as
  the queue-collapsed workbench-first layout on `/ops/data-entry` (the allowed
  minimum per the task). A separate `/ops/items/{id}` route is a future refinement.
- Consultant end-to-end processing on a *freshly created* customer is enabled
  server-side (the pipeline endpoints accept active-grant consultants), but the
  consultant UI does not yet expose an inline extraction workbench for a selected
  client — the consultant uses the customer processing workspace. This is a UI
  follow-on, not a backend dead-end.
- `backend/tests/integration/*` failures are pre-existing (require the live test
  database wiring); they were failing before this phase and are unchanged.
- The legacy pre-existing dirty-tree files (`.agents/skills/*`, `.claude/skills/*`,
  `.windsurf/skills/*`, `API_ENDPOINTS.md`, `CarbonTally_DB_Schema_V3M2.sql`,
  `admin/*`, ...) were **not** absorbed into this phase's commit.

## 10. Git safety

- No `--force`, `--rebase`, `--reset`, or history rewrite was used.
- The commit contains only the files changed for this task.
- A secret/credential scan was run: no `.env`, credentials, `node_modules`,
  generated caches, or unrelated tool directories are staged.

## 11. Recommended next phase

1. Route the D19 item workbench to a standalone `/ops/items/{itemId}` page (full
   E1->E2) and add a consultant client-processing surface.
2. Seed spend-based customer factors for the demo spend documents, or add a
   customer-factor creation shortcut from the mapper when `no_factors_reason` is
   returned.
3. Populate `qc_checks`/`qc_errors` in the workflow so recurring-quality reporting
   becomes supported (currently documented as unavailable).

  demo has real assigned work (approved operating model; other batches untouched).
