# CarbonTally V3 — Investor-Scale Acceptance / UAT Audit (Continuation)

**Date:** 2026-08-28 (continuation session)
**Auditor:** OpenHands (OHD), independent Product Owner acceptance audit
**Baseline tested:** Git `c36c848` (current `main`); local/dev stack (frontend `localhost:3000`, backend `localhost:8050`, Supabase auth `127.0.0.1:54425`, Postgres `127.0.0.1:54426`)
**Relation to prior report:** this is the **investor-scale continuation** of the canonical acceptance audit. The earlier deliverable `CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md` (same date) remains the primary canonical report for the pre-existing finding set (SEC-1, MSG-1, PRC-1, CON-1..3, MD-1, MD-2, CAL-3, PERF-1/2, UX-6..9, D19-2, D21-2/5, FAC-1, RET-1, EVD-3, PRC-3, API-6, AUTH-2). **This document records the continuation session only**: new runtime evidence (a full self-service investor chain on a brand-new organisation) and the new findings discovered since that report was written. It does **not** repeat prior findings; where a prior finding was re-verified during continuation, it is listed in §5 with a cross-reference only.

> **Method.** Same rules as the prior report: every claim verified at runtime (browser UI, HTTP API, PostgreSQL). No source/schema/RLS/API/config/seed modification. No commit/push. Statuses: `VERIFIED WORKING`, `PARTIALLY WORKING`, `BROKEN`, `NOT IMPLEMENTED`, `NOT TESTABLE`, `ENVIRONMENT BLOCKED`, `PO DECISION REQUIRED`.

---

## 1. Continuation scope and what was tested

The continuation focused on the **investor demonstration chain** that the prior report could only partially exercise: a **brand-new self-service customer organisation** taken through the complete document-to-emissions journey, plus targeted re-verification of the highest-risk boundaries.

**New test tenant (OHD-created, synthetic):** `OHD Audit Org Ltd` (org `290ed626-0fc7-446c-9077-7a220bffc093`), created entirely through the product's own self-service onboarding flow (no admin/SQL insert). Primary user `ohd.audit.20260828@…` (owner), second member `ohd.audit.admin2@…` (admin, added through the Members API as the owner).

### T65 end-to-end chain — REAL actions, REAL persistence

All steps performed with live API calls / browser against the running app; states confirmed in Postgres.

| Step | Actor | Action | Result (verified) |
|---|---|---|---|
| 1 | New user | `POST /auth/v1/signup` (new email) | Session created; no existing-user redirect issue |
| 2 | New user | Landing → `/onboarding` (D35) | Correct — new user reaches onboarding (no false `/onboarding` for existing users; see §5) |
| 3 | New user | Onboarding form → create organisation | Org `290ed626…` created; workspace `/home` live |
| 4 | Owner | `POST /api/v3/uploads` (form: `organization_id` + `data_type`) with `ohd_invoice_9999.pdf` (730 B synthetic PDF) | File row `c8d9dd53-…` in `organization_files`, bucket `documents` |
| 5 | Owner | Batch create | Batch `38acbc6c-…` status `pending` |
| 6 | Ops | `/items/{id}/start` → `/extract` → `/map` → `/validate` → `/calculate` | All transitions returned expected statuses: `extracting→extracted→mapping→mapped→validating→validated→calculating→calculated` |
| 7 | Engine | Calculation (factor `7de17915-…` Diesel 2.57082 kg CO₂e/L × 1000 L) | `emissions_logs` row `3434db95-…` `raw_quantity=1000.0 → calculated_kg_co2e=2661.55`; immutable snapshot `4184ad72-…` with `content_hash=c0311499…`, `co2e_multiplier=2.66155`, `factor_kind/emission_factor` provenance |
| 8 | Owner | Customer review → approve (`/customer-review`) | Item `ab54fd1c-…` status → `approved` |
| 9 | Owner | `/home` dashboard | `EMISSIONS ROWS 1`, `TOTAL TCO₂E 2.66`, "Emissions 2.66 tCO₂e (1 rows) — Scope 1 — Latest month: 2026-08", monthly trend populated |
| 10 | Owner | `/emissions` | Calculation history shows the row: `2026-08-28 — Scope 1 2661.55`; "View evidence" renders the snapshot (factor, multiplier, content hash) |
| 11 | Owner | `POST /api/v3/reports` (annual 2026) | Report `9b512445-…` status `completed` with **real** data: `totals.total_co2e_kg=2661.550000`, `total_rows=1`, `scopes.Scope 1=2661.55`, lineage `emissions_logs.count=1`, resolved factor `7de17915-…` |
| 12 | Owner | `GET /reports/{id}/download` + `/pdf` | JSON metadata 200; **6-page PDF** generated 200 |

**ISC-V1 (POSITIVE) — the acceptance chain `REAL USER → REAL ROLE → REAL WORKSPACE → REAL ACTION → REAL API → REAL AUTHORIZATION → REAL DATABASE → REAL BUSINESS LOGIC → REAL RESULT → REAL NEXT ACTOR` works for a self-service customer organisation through calculation and reporting.** A real (synthetic) document became a real emissions result (2661.55 kg CO₂e) that is visible on the dashboard, in the emissions history, in the evidence view, and in a generated annual report + PDF. No demo/hard-coded numbers are involved anywhere in this chain.

### Re-verified boundaries (cross-reference, not duplicate)

| Prior finding | Continuation re-verification |
|---|---|
| MSG-1 (conversation create 500) | Reproduced exactly: `POST /api/v3/messaging/conversations` → 500 `there is no unique or exclusion constraint matching the ON CONFLICT specification` (`conversation_participants` has no `UNIQUE (conversation_id, user_id)`). |
| PRC-1 (customer review queue 500) | Reproduced: `GET /api/v3/processing/customer-review?organization_id=290ed626…` → 500 `column reference "id" is ambiguous`. |
| MD-2 (vehicles broken) | Reproduced: `POST /api/v3/vehicles` → 500 `relation "public.vehicles" does not exist`; Vehicles tab shows "Action failed — Network error… No vehicles yet". Migration `supabase/migrations/20260825000000_v3m7_vehicles.sql` defines the table but it is **not applied** in this environment (deployment dependency). |
| SEC-1 (viewer upload) | Not re-tested (unchanged code); see prior report. |
| CON-1..3 (consultant operating gaps) | Not re-tested (unchanged code); see prior report §8. |

---

## 2. NEW FINDINGS (continuation session)

Finding IDs use the `ISC-` prefix to keep them distinct from the prior report's IDs.

---

### ISC-1 — Document → emissions reverse lookup (D33) is broken: `calculation_snapshots.source_item_id` is never written

- **Severity:** P1
- **Persona:** Customer Owner / Member (evidence chain); affects staff/ops too (evidence lookup)
- **Workflow:** Document → emissions evidence (D33 reverse lookup); Documents page "Emissions from this document"
- **Exact reproduction:**
  1. Run the full pipeline (T65) so an item is `approved` and `emissions_logs` row `3434db95-…` exists.
  2. `GET /api/v3/documents/{file_id}/emissions` for the source document `c8d9dd53-…` → returns `{"emissions":[]}` (empty), despite the emissions row and snapshot existing.
  3. Browser `/documents` page shows the row `ohd_invoice_9999.pdf · PDF · 730 B` with **"Emissions from this document —"** (dash/placeholder).
- **Expected behaviour:** The document exposes the emissions result derived from it (D33: `organization_files.id ← manual_extraction_items.file_id ← calculation_snapshots.source_item_id ← emissions_logs.snapshot_id`), so the customer sees "this document produced 2661.55 kg CO₂e / 2.66 t CO₂e, evidence snapshot 4184ad72-…".
- **Actual behaviour:** The reverse lookup joins `calculation_snapshots s ON s.id = l.snapshot_id JOIN manual_extraction_items i ON i.id = s.source_item_id`; `s.source_item_id` is **NULL** for every item calculated through `/api/v3/ops/items/{id}/calculate` (`backend/api/v3_operations.py` builds `CalculationRequest(… source_file=item.file_name …)` without `source_item_id=item.id`). The chain therefore terminates at the snapshot, and the document's emissions outcome is invisible. The document UI keeps a file-size orientation (730 B) with an empty emissions slot — directly the PO-observed "documents emphasize file size instead of emissions outcome".
- **Classification:** IMPLEMENTATION GAP
- **Evidence:**
  - `emissions_logs.snapshot_id = 4184ad72-…`; `calculation_snapshots.source_item_id = NULL` (Postgres, read-only).
  - `GET /api/v3/documents/c8d9dd53…/emissions` → `{"document_id":"c8d9dd53…","emissions":[]}`.
  - Browser `/documents`: "Emissions from this document —"; `/home`: "TOTAL TCO₂E 2.66".
- **Affected files/endpoints:** `backend/api/v3_operations.py` (`calculate_item` — request construction); `backend/data/emissions_logs.py` (`list_for_file`, lines ~301–313); `backend/api/v3_documents.py` (`document_emissions`); `frontend/src/v3/customer/DocumentsPage.jsx`.
- **Recommended fix:** populate `source_item_id=item.id` (and optionally `source_page`) in the `CalculationRequest` used by `calculate_item`, and add a regression test that asserts `GET /api/v3/documents/{file}/emissions` returns the emission after a full pipeline run.
- **Regression test:** full pipeline (upload→extract→map→validate→calculate→approve) then assert document emissions endpoint returns ≥1 row with `calculated_kg_co2e` matching the snapshot.
- **Investor-demo impact:** **HIGH** — the flagship "single document, fully evidenced" story is undermined when the document page cannot show the emissions outcome.

---

### ISC-2 — Blocking validation issues are never closed: an `approved` item still carries open blocking issues

- **Severity:** P2
- **Persona:** Customer Owner; CarbonTally Ops; issue lifecycle
- **Workflow:** Validation → issues → re-validation → approval
- **Exact reproduction:**
  1. First validation of the OHD item (with `blocking: true`, missing activity/date) opened 2 issues: `Validation: EXTRACTION_MISSING_FIELD` (ids `71766ac9-…`, `4bc6adce-…`), status `open`, created 11:30:01.
  2. The item was re-validated clean (no findings), mapped, calculated, and **customer-approved** (status `approved`).
  3. The 2 issues remain `open` with `resolved_at`/`closed_at` NULL (Postgres, read-only). Dashboard `/home` shows "Needs your attention — Open issues: 2" on an **approved** item.
- **Expected behaviour:** When a blocking finding is resolved (re-validation passes) or the item reaches an approved terminal state, the corresponding issues should transition to resolved/closed (or be explicitly linked to the item lifecycle), and the dashboard's attention counts should reflect reality.
- **Actual behaviour:** Issues persist open indefinitely; the dashboard permanently shows "Open issues: 2" for an approved, reportable emission. An approved item coexisting with open blocking issues is a state contradiction that will confuse customers and pollute issue counts.
- **Classification:** IMPLEMENTATION GAP
- **Evidence:** Postgres `issues` rows for org `290ed626-…` (2 rows `status=open`, `resolved_at=NULL`); item `ab54fd1c-…` status `approved`; browser `/home` "Open issues: 2".
- **Affected files/endpoints:** `backend/engines/processing_workflow.py` (issue opening); `backend/api/v3_processing_workflow.py` (validate / customer-review handlers); dashboard issue counting (`frontend/src/v3/customer/DashboardPage.jsx`).
- **Recommended fix:** close (or supersede) validation issues when a later validation of the same item/batch passes, and/or when the item reaches `calculated`/`approved`; add status transition on the issue lifecycle.
- **Regression test:** run a blocking validation (issues open), re-validate clean, approve; assert issues are resolved and dashboard "Open issues" reflects the resolution.
- **Investor-demo impact:** **MEDIUM-HIGH** — an investor clicking "Needs your attention" on a fully processed, approved item will see stale blocking issues.

---

### ISC-3 — Emissions history cannot show what was calculated: `activity` is absent from the list payload

- **Severity:** P3
- **Persona:** Customer Owner/Member; reporting evidence
- **Workflow:** Emissions history list
- **Exact reproduction:** `/emissions` page after the T65 pipeline shows the history row as `2026-08-28 — Scope 1 2661.55 —` (ACTIVITY and FACTOR columns render "—"). `GET /api/v3/exports/emissions.json` row keys contain **no `activity` field** (verified: `['asset_id','calculated_kg_co2e','created_at','emission_factor_id','end_date','evidence_status','id','organization_id','raw_quantity','scope','snapshot_id','source_file','source_item_id','source_page','start_date','unit']`), and no factor name join — even though the snapshot records `activity="Diesel"` and the factor is `Diesel (average biofuel blend) 2.57082`.
- **Expected behaviour:** The history list should surface the activity (and factor name/rate) from the calculation snapshot so the row is self-describing evidence.
- **Actual behaviour:** activity/factor fields are "—"; the customer cannot tell from the list what activity produced the emission (must open evidence view).
- **Classification:** IMPLEMENTATION GAP (partially overlaps prior UX-6 "FACTOR column —"; ISC-3 adds the missing `activity`).
- **Evidence:** browser `/emissions` history row; exports payload keys (above).
- **Affected files/endpoints:** `backend/api/v3_exports.py` / `backend/data/exports.py` (emissions list payload), `frontend/src/v3/customer/EmissionsPage.jsx`.
- **Recommended fix:** include `activity` (and factor name + multiplier) in the emissions list payload by joining the snapshot/factor.
- **Regression test:** after a pipeline calculation, assert the emissions list contains the activity string.
- **Investor-demo impact:** LOW-MEDIUM.

---

### ISC-4 — D17 master data usable through the API for a self-service org; asset creation requires a facility (500 on null)

- **Severity:** P3 (UX robustness)
- **Persona:** Customer Owner
- **Workflow:** Organisation → Facilities & Assets
- **Exact reproduction:**
  1. `POST /api/v3/organizations/{org}/facilities` (name + address + postcode) → 201, facility `b33a79c4-…` created; Facilities tab shows it (1 asset).
  2. `POST /api/v3/organizations/{org}/assets` with `facility_id: null` → **500** `null value in column "facility_id" of relation "assets" violates not-null constraint`. With the facility id → 201, asset `c9c28f6c-…`.
  3. `POST /api/v3/suppliers` (body `organization_id`) → 201, supplier `4b11f282-…`; Suppliers tab shows it ACTIVE.
  4. The Assets list in the UI shows the facility as the raw **UUID** (`b33a79c4-…`) instead of the facility name.
- **Expected behaviour:** a missing required facility should be a clean 422 validation error, not a 500; the asset list should resolve the facility name.
- **Actual behaviour:** 500 on missing facility; UUID shown instead of name.
- **Classification:** IMPLEMENTATION GAP (asset 500 + facility-name display); facility/asset create otherwise working.
- **Evidence:** API responses (above); browser Facilities & Assets tab.
- **Affected files/endpoints:** `backend/api/v3_organizations.py` (`add_asset` — validate `facility_id` before insert); asset serializer/`frontend/src/v3/admin/FacilitiesTab.jsx`.
- **Recommended fix:** pre-validate `facility_id` (422 when absent), join facility name in the asset list payload.
- **Regression test:** asset create without facility → 422 (not 500); asset list renders facility name.
- **Investor-demo impact:** LOW.

---

### ISC-5 — Custom-factor approval path works only with a second admin; self-approval correctly blocked (re-verified positive)

- **Severity:** positive verification + note
- **Persona:** Customer Owner/Admin
- **Workflow:** Custom factors draft → approve
- **Exact reproduction/result:**
  1. Owner creates factor `55a5b51a-…` (Draft) via `POST /api/v3/customer-factors`.
  2. Owner self-approve → **403** `a factor's creator cannot approve their own factor` (correct, D-cf-3).
  3. Owner adds second user `ohd.audit.admin2@…` as org **admin** via `POST /{org}/members` → 201 (`0f197d0d-…`).
  4. Second admin approves factor → **200**, status **`active`** in DB.
- **Expected:** D-cf-3 approval model enforced; cross-admin approval works.
- **Actual:** works as designed when ≥2 admins exist. Single-admin orgs remain deadlocked (prior finding FAC-1 / PO-1 stands).
- **Classification:** VERIFIED WORKING (two-person path) + PO DECISION REQUIRED (single-admin deadlock, prior FAC-1).
- **Investor-demo impact:** LOW (two-person path demonstrable).

---

### ISC-6 — Notifications: legacy `/api/notifications` 404 (frontend still calls the old endpoint)

- **Severity:** P3 (feature-level break already covered by prior PERF-1; this is the precise root cause)
- **Exact reproduction:** console on every authenticated page: `Error fetching notifications: Object`. `frontend/src/hooks/useNotifications.js` calls `GET /api/notifications?limit=50` → **404** `{"detail":"Not Found"}` (verified via API). The working V3 endpoint is `GET /api/v3/notifications` (returns 200). The hook was not migrated to the V3 API, so the notification bell count never loads.
- **Classification:** IMPLEMENTATION GAP (root cause for PERF-1).
- **Affected files/endpoints:** `frontend/src/hooks/useNotifications.js`, `frontend/src/context/RealtimeContext.jsx:275`, `backend/api/v3_notifications.py` (exists, unused by the hook).
- **Recommended fix:** point the hook at `/api/v3/notifications` and remove the legacy path.
- **Investor-demo impact:** LOW.

---

### ISC-7 — Org "Locations" tab status shows newly created facilities as `Inactive`

- **Severity:** P3
- **Persona:** Customer Owner
- **Workflow:** Organisation → Locations (N2: facilities model)
- **Exact reproduction:** after creating facility `b33a79c4-…` (API returned `is_active: true`), the Locations tab lists it as `OHD Test Facility A · LS1 1AA · Unclassified · **Inactive**`.
- **Expected:** a facility created with `is_active=true` should display as Active.
- **Actual:** displayed Inactive — the Locations view derives status from a field that is not set on newly created facilities (likely `type` or a different flag), contradicting the API state.
- **Classification:** IMPLEMENTATION GAP (minor)
- **Evidence:** browser Locations tab; API create response `is_active:true`.
- **Affected files/endpoints:** `backend/api/v3_organizations.py` (facility create — set the field the Locations view reads) or `frontend/src/v3/admin/LocationsTab.jsx`.
- **Investor-demo impact:** LOW.

---

## 3. New positive verifications (not demo data)

- **ISC-V1** — full self-service org chain (above): signup → onboarding → upload → processing pipeline → server-authoritative calculation (content-hashed snapshot) → customer approval → dashboard total → emissions history → evidence view → annual report + 6-page PDF, all fed by the real `emissions_logs`/`calculation_snapshots` rows.
- **ISC-V2** — Report generation is data-driven: `POST /api/v3/reports` produced totals/scope/lineage directly from `emissions_logs` (total 2661.55 kg, factor `7de17915-…`, `count=1`), and `GET /api/v3/reports?organization_id=…` now lists it `completed` (`count_by_status: {completed:1}`). Prior "reports empty" state was simply "no report generated yet" — generation itself works.
- **ISC-V3** — Negative authorisation batch all denied (403) for the new org: OHD owner → Granite document/list (403); PE `entity-staff@demo` → customer document GET and signed-url for OHD and Granite files (403, **PE no-download boundary holds**); PE → customer conversation message (403, **Customer ↔ PE messaging blocked**); viewer → facility create (403); OHD owner → Granite conversation message (403). All server-side, none hidden-UI.
- **ISC-V4** — PE positive path: `GET /api/v3/ops/entities/{Entity Beta}/extraction/next-item?stage=extraction` returns an assigned item (`FuelCard_01_Statement.pdf`, status `extracted`, with extracted_data) — PE can claim and work assigned items.

---

## 4. Updated gap register (continuation additions)

| ID | Severity | Title | Resolution |
|---|---|---|---|
| ISC-1 | P1 | D33 document→emissions reverse lookup broken (`source_item_id` NULL) | IMPLEMENTATION GAP |
| ISC-2 | P2 | Blocking validation issues never closed on re-validation/approval | IMPLEMENTATION GAP |
| ISC-3 | P3 | Emissions history lacks `activity` (and factor) in list payload | IMPLEMENTATION GAP |
| ISC-4 | P3 | Asset create 500 on missing facility; facility shown as UUID | IMPLEMENTATION GAP |
| ISC-5 | — | Custom-factor two-person approval VERIFIED WORKING; single-admin deadlock remains | VERIFIED + PO DECISION REQUIRED (prior FAC-1/PO-1) |
| ISC-6 | P3 | Notifications hook calls removed legacy `/api/notifications` (root cause of PERF-1) | IMPLEMENTATION GAP |
| ISC-7 | P3 | Locations tab shows new facilities Inactive | IMPLEMENTATION GAP |

## 5. Updated P0/P1/P2/P3 summary (continuation)

- **P0:** none found (unchanged — no data leakage, corruption, or privilege escalation; all continuation negative tests correctly denied).
- **P1 additions:** ISC-1 (document→emissions evidence chain invisible). Prior P1 set stands (SEC-1, MSG-1, PRC-1, CON-1..3, MD-2).
- **P2 additions:** ISC-2.
- **P3 additions:** ISC-3, ISC-4, ISC-6, ISC-7.
- **Prior totals to carry forward:** P1=8, P2=8, P3=8 (from FULL_PERSONA §28) → **updated totals: P1=9, P2=9, P3=12** (ISC-5 is a verification, not a defect).

## 6. Cline fix queue (continuation additions)

Add to the existing `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` (P1/P2/P3 order):

1. **P1 — ISC-1:** set `source_item_id` (and `source_page`) on the `CalculationRequest` in `calculate_item`; regression: document emissions endpoint returns the emission after a pipeline run. Dependency: none. Security: none (evidence visibility, org-scoped). PO decision: NO (D33 already specifies the chain).
2. **P2 — ISC-2:** close/supersede validation issues when a later validation passes or the item reaches `calculated`/`approved`. Regression: blocking validate → re-validate clean → approve → issues resolved.
3. **P3 — ISC-3:** join snapshot `activity` (and factor name/rate) into the emissions list payload.
4. **P3 — ISC-4:** 422 (not 500) for asset create without facility; render facility name in asset list.
5. **P3 — ISC-6:** migrate `useNotifications` to `/api/v3/notifications`.
6. **P3 — ISC-7:** Locations tab Active/Inactive derives from the correct field for new facilities.

All items: affected layer (Backend API / Frontend), acceptance criteria as above, no open PO decision (except single-admin factor approval — prior PO-1).
## 7. Investor-demo readiness (continuation view — updated after session 3)

- **Customer journey (self-service):** DEMONSTRABLE end-to-end up to and including report + PDF on the OHD org. **New blockers found in session 3:** (a) mapping-options returns `factors: []` for spend-based activities such as "Purchased goods"/GBP and the map step then 422s — the seeded spend documents **cannot be mapped at all**, so the pipeline dead-ends at mapping for a large share of the demo dataset (ISC-9); (b) creating a custom factor that collides with an existing org factor family returns a raw 500 instead of a clean 409 (ISC-8). **Still broken on screen:** customer "Review & approve" 500 (PRC-1), "Emissions from this document —" (ISC-1), open issues on approved items (ISC-2).
- **Consultant journey:** manage-only (prior CON-1..3); portfolio mechanics verified at investor scale — 14 clients, dashboard + client context work, cross-consultant and same-consultant client-org isolation hold (ISC-11/ISC-12).
- **PE journey:** manager/staff workspaces + entity dashboard work; boundaries hold; **no batches are assigned to the 3 demo PEs in the dataset** — their queues are empty (demo-state note, ISC-14).
- **CarbonTally journey:** operator/reviewer/QC gates verified; conversation creation still broken (MSG-1, re-confirmed with a fresh orphan-conversation side effect); **system_admin role added by the seed cannot access the audit trail or billing that staff-admin can** (ISC-10).
- **Security:** no P0. All 12 negative tests run this session correctly denied (cross-org documents/facilities, same-consultant client orgs, consultant-to-other-consultant, PE-to-customer docs/messaging, viewer/member factor approval, reviewer calculate).

## 8. SESSION-3 CONTINUATION (investor-scale API battery) — NEW FINDINGS ISC-8..ISC-16

Run against the investor-scale dataset (Quayside Energy `bc197ccf-…`, Granite Distribution `e5218a70-…`, consultant 1 portfolio, Processing Entity Alpha `a25a0537-…`, internal staff roles). All evidence is live-API/DB. No app/schema/RLS/seed modification; only OHD test rows added (documented at the end).

### ISC-8 (P2) — Custom-factor create returns raw HTTP 500 on duplicate factor family
- **Persona:** Customer Owner/Member (any org staff). **Org:** Quayside Energy.
- **Steps:** `POST /api/v3/customer-factors` with `{"organization_id": QS, "activity_type": "Diesel", "unit": "litres", "scope": "Scope 1", "reporting_year": 2025, "co2e_multiplier": "1.5"}`.
- **Expected:** clean 409/422 — "a factor with this activity/unit/scope/year already exists" (D-cf-4 semantics: create a new **version** or reject).
- **Actual:** `500 {"message": "duplicate key value violates unique constraint \"idx_customer_factors_family_version\"…"}`. Quayside's seed already contains "Customer Diesel factor v1" (active) for exactly this family, so **any** collision attempt 500s.
- **Root cause:** `api/customer_factors.py` POST path does not catch the Postgres unique-violation — unhandled 500. **Affected layer:** Backend (`api/customer_factors.py`). **Security impact:** none. **Workflow impact:** factor creation fails opaquely in the common case (seed preloads per-org factors), and the factor-creation demo would show a server error.
- **Fix:** map unique-violation to 409 with an actionable message; surface the existing factor family. **PO decision?** NO.

### ISC-9 (P2) — Mapping dead-ends for spend-based activities: `mapping-options` returns `factors: []` and map 422s
- **Persona:** Customer Owner (self-service processing). **Org:** Quayside Energy, item `f87711a4-…` (Purchased_goods_2025-01.pdf, extracted: activity "Purchased goods", unit "GBP").
- **Steps:** `GET /api/v3/processing/items/{id}/mapping-options` -> `"factors": []` (facilities/assets/suppliers populated); `POST …/map` -> `422 "an emission factor must be selected"`.
- **Expected:** factor candidates for the extracted activity (or a manual factor picker) so every extracted document can be mapped and calculated.
- **Actual:** only fuel/energy activities match. The loaded DEFRA-2025/SEAI-2025 sets (7,049 rows) contain **no £-denominated spend factors** (units are kg, kWh, litres, tonnes, km, GJ, …), and `find_by_activity` requires `activity_type ILIKE` **and exact unit match** — so "Purchased goods"/GBP returns nothing.
- **Root cause:** (1) factor-set coverage — spend-based (scope-3 £) factors not loaded (TEST-DATA/DATA-GAP); (2) `mapping-options` has **no fallback browse/search** and exact-unit matching only (IMPLEMENTATION GAP). **Affected:** backend `data/emission_factors.py` + `api/v3_processing_workflow.py` (mapping-options). **Workflow impact:** seeded spend documents (a large share of the dataset) can never reach calculation/emissions/review/report through the UI. This is **investor-demo-critical**.
- **Fix:** (a) add a factor browse/search fallback + unit-normalized matching to mapping-options; (b) load DEFRA scope-3 spend-based factors into the sets. **PO decision?** The factor-set coverage question needs PO visibility; the missing fallback picker is a pure implementation defect.

### ISC-10 (P2) — `system_admin` role added by the seed is inconsistent: denied audit + billing that staff-admin can access
- **Persona:** System Admin vs Staff Admin. **Org:** CarbonTally internal.
- **Evidence:** `GET /api/v3/ops/me` perms — staff-admin: `{can_manage_billing, can_manage_staff, can_process, can_review, can_view_all}`; system-admin: `{can_manage_staff, can_process, can_review, can_view_all, is_superuser}` (**no can_manage_billing**). `GET /api/v2/admin/audit` -> staff-admin **200**, system-admin **403 "Admin privileges required"**.
- **Expected:** the highest-privilege role is a superset of staff admin (audit + billing + staff + ops).
- **Actual:** the seeded `system_admin` role (staff_roles row `ec5c88ea-…`, `system_admin`) cannot perform control-plane functions the lower `admin` role can. **This UPDATES prior AUTH-2:** a distinct system_admin role now exists in the dataset (the earlier report found none), but its permission matrix is not a superset and the legacy `/api/v2/admin/*` authorizer uses a role-name whitelist that excludes it.
- **Root cause:** role-permission configuration without a superset ordering; legacy authorizers don't honour the new role. **Affected:** Backend `api/admin_audit.py` (authorizer) + staff role configuration. **Security impact:** none (denies too much, not too little) — but a "system admin" cannot audit the system. **Workflow impact:** System Admin persona is not actually able to operate the control plane.
- **Fix:** single source of truth for role permissions; make `system_admin` a superset of `admin`; align legacy `/api/v2/admin/*` checks. **PO decision?** YES — the role model (which roles exist, what system_admin must be able to do) needs PO ratification.

### ISC-11 (POSITIVE) — Consultant portfolio mechanics verified at investor scale
`consultant.demo0001` (Net Zero Advisory): `/me/clients` -> 14 clients (12 active, 2 onboarding); `/me/dashboard` -> client_count 14, active 12, pending_reviews 0; `/clients/{id}/context` -> 200 with full client payload; **cross-consultant** client detail (`consultant.demo0001` -> `consultant.demo0002` client) -> 403; **same-consultant** client-org document isolation (client owner 1.1 -> client 1.2 org) -> 403. VERIFIED WORKING.

### ISC-12 (POSITIVE) — Client-owner landing + isolation at scale
`client.owner.demo0001.1` resolves own org (Quayside Distribution `38ab85cb-…`) via `/api/organizations/members/user/{id}` -> 200; own org documents -> 200; same-consultant other client (client 1.2, org `be6ecdd4-…`) documents -> 403. VERIFIED WORKING.

### ISC-13 (POSITIVE) — Factor approval gates verified at scale
Member-created draft (`OHD member factor`, Natural gas/kWh): viewer approve -> 403, member approve -> 403, admin approve -> 200 and status flips to active. Matches D-cf-3 (no self-approval; admin/owner approver). VERIFIED WORKING.

### ISC-14 (POSITIVE + demo note) — PE manager/staff boundaries; dataset PE queues are empty
`pe-manager-1.demo` and `pe-staff-1.demo` (Processing Entity Alpha Ltd): `/ops/me` -> 200 (staff profile, entity scope); entity dashboard -> 200; claiming unassigned next-item -> 403 "staff lacks permission: can_process" (no assignment); PE -> customer documents -> 403; PE -> customer conversation message -> 403. **Demo note:** the 3 demo PEs have **zero assigned batches** in the dataset (only 1 batch in the whole DB is entity-assigned, `f77e6b5f-…` -> Beta), so PE workspaces are empty in the demo unless batches are assigned beforehand.

### ISC-15 (P3) — Dataset workflow-state distribution: no item ever reaches `customer_review`
221 items: 151 pending, 25 extracted, 14 calculated, 12 mapped, 9 approved, 6 validated, 3 rejected, 1 qc_approved; 53/56 batches `open`. **No item is in `customer_review` status** anywhere — the customer approval step is unrepresented in the demo dataset state (the seeded pipeline wrote `approved` directly), and combined with PRC-1 the review/approve screen cannot be demonstrated from seeded data.

### ISC-16 (P3) — ISC-1 breadth confirmed on the dataset: 25/27 snapshots have `source_item_id` NULL
The document→emissions reverse-lookup breakage (ISC-1) affects essentially **all** dataset emissions, not just OHD-created ones. Positive control: the evidence endpoint itself works for seeded emissions (Granite `98953812-…` + snapshot `846e1c86-…` -> full evidence payload).

### Re-confirmed this session (no change to prior verdicts)
- **PRC-1** — `GET /api/v3/processing/customer-review` -> 500 `column reference "id" is ambiguous`.
- **CAL-3** — `GET /api/reference/fuel-types` -> 500.
- **MSG-1** — `POST /api/v3/messaging/conversations` with valid `{organization_id, subject}` -> 500 `there is no unique or exclusion constraint matching the ON CONFLICT specification`; **side effect confirmed:** an orphan conversation row with **0 participants** is left behind (`2bf079ae-…` this session, plus earlier `a3f59827-…`, `c0930e7e-…`, `34285806-…`).
- Authorisation positives: owner/admin/member/viewer document reads correct; member invite -> 403; viewer facility create -> 403; customer -> /ops/me -> 403; staff-admin `/api/v2/admin/audit` -> 200; customer `billing/me` -> 200 (CREDIT mode, credits 0).
- **Cleanup note:** OHD test rows added this session (left in place, consistent with prior practice): message `97cbbf66-…` in Quayside conversation `0a78e2d3-…`; customer factor `0a02b7eb-…` ("OHD member factor", now active); orphan conversations `2bf079ae-…` (MSG-1 side effect). Failed creates (duplicate factor 500s, conv 422s) left no rows. No demo/legit data modified.

## 9. CONTINUATION CHECKPOINT (updated after session 3)

- **Completed in this session (3):** full investor-scale API battery across 13 personas/48+32 checks (batteries in `/tmp/ct_audit/isc_battery*.py`); new findings ISC-8..ISC-16; positive verifications ISC-11..14; PRC-1/CAL-3/MSG-1 re-confirmed; factor-approval gates; consultant + client-owner isolation at scale; system_admin role inconsistency root-caused.
- **Carried (documented earlier):** viewer upload (SEC-1); consultant operating gaps (CON-1..3); MSG-1/PRC-1/MD-2; D19-2; D21-2; RET-1/SA-4; AUTH-1; ISC-1..ISC-7.
- **Incomplete / next exact tests:**
  1. UI capture of customer "Review & approve" page (PRC-1) — API proof complete; harness session-restore flakiness prevented a clean capture this session (repeated login -> /review renders the login page; documented environment limitation).
  2. Realtime message **push** delivery timing (MSG-2): channel setup + persisted reads verified; live push still not instrumented.
  3. Responsive re-check of customer shell at 768/1440 px; D21 token audit of new-org screens (inherits D21-2).
  4. Retention enforcement dry-run (RET-1) — blocked on PO-2 (durations undefined).
  5. Factor-set coverage decision (ISC-9) and system_admin role-model ratification (ISC-10) — PO items.
- **Unresolved environment blockers:** vehicles migration `20260825000000_v3m7_vehicles.sql` not applied (MD-2); browser session-restore flakiness in the CDP harness (login works, deep-link navigate loses session — intermittent).
- **OHD-created data remaining (cumulative):** `OHD Audit Org Ltd` + its artefacts (report, factor, facility, asset, supplier, emissions, issues); plus session-3 additions listed in §8 (Quayside message + factor + orphan conversations). All synthetic and labelled; left in place (evidence/RI). No demo/legit data modified; dataset not reset or reseeded.

---

*Prepared by OpenHands (OHD) as the continuation of the independent Product Owner acceptance audit. Primary canonical report for the pre-existing finding set: `CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md`. Companion deliverables: `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md`, `CARBONTALLY_V3_PERSONA_TEST_MATRIX.md`, `CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md`.*
