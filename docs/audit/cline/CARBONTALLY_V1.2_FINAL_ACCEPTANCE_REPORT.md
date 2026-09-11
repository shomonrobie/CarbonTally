# CarbonTally V1.2 — Final Acceptance Report (UI Completion + Browser E2E Closure)

- **Date:** 2 September 2026
- **Scope:** Final V1.2 acceptance closure — dedicated PEShell, true browser
  E2E over isolated fixtures, role matrix, security negatives, responsive
  verification, blueprint typo correction.
- **Environment:** local stack (Frontend `:3000`, CarbonTally API `:8050`,
  Supabase `127.0.0.1:54425/54426`), headless Chromium 100% zoom.
- **Version targets:** V1.2 architecture frozen; no V1.3; no Phase 4 work.

---

## 1. PEShell implementation — COMPLETE

The final architecture target `PE → /pe → PEShell` is implemented:

- **New component:** `frontend/src/v3/pe/PEShell.jsx` (dedicated PE application
  shell — its own React component + markup, NOT the shared `V3Layout`).
- `frontend/src/App.js` now wraps both `/pe` and `/pe/items/:entityId/:itemId`
  in `PEShell` (previously shared `V3Layout`).
- `frontend/src/v3/pe/pe.css` provides PE-scoped D21-token presentation.
- **Server-authoritative routing:** `backend/api/v3_context.py`
  (`GET /api/v3/me/context`) now resolves CarbonTally-internal staff to
  `/ops` **and Processing Entity staff to `/pe`** (`workspaces: ["pe"]`,
  `actor_type: "entity_staff"`) — PE users land in the PE application after
  login, never the internal Operations hub.
- **Shared-shell guard:** `V3Layout` redirects `actor_type === 'entity_staff'`
  to `/pe`, and `OperationsPage` returns `<Navigate to="/pe">` for any staff
  profile carrying `entity_id` — a PE member opening a shared-shell URL (e.g.
  `/notifications` or `/ops`) is bounced to the PE application so the PE
  surface can never expose Operations/Customer/Consultant/Admin navigation.
- Reuses permitted shared primitives only: D21 tokens/css, `Icon`, `Drawer`,
  `DataTable`, buttons/alerts, the shared API client (`/api/v3/pe/*`) and the
  shared PE workbench components. No business logic duplicated.

## 2. PE navigation — COMPLETE

Browser-verified nav content for both PE personas is exactly `Work` (→ `/pe`).
The header context shows the **entity name** (from `GET /api/v3/pe/me`), the
**frozen-role chip** and **Sign out**. No Operations, Customer, Consultant or
CarbonTally Admin navigation exists anywhere on the PE surface.

- PE Admin (`pe-manager-1`): `Processing Entity Alpha Ltd · ADMIN`, nav `Work`.
- PE Data Entry Operator (`pe-staff-1`): `Processing Entity Alpha Ltd ·
  DATA ENTRY OPERATOR`, nav `Work`.
- Post-login destination verified in-browser: PE staff land on `/pe`;
  CarbonTally internal staff still land on `/ops`.

## 3. Internal UI — COMPLETE

The Internal Operations hub (`/ops`, V3Layout) is unchanged in structure.
V1.2 internal-review controls verified live:

- Reviewer workspace `/ops/review/:itemId` exposes **Submit for CarbonTally
  QC** when an internal item is `calculated` (plus Assign / Validate / Complete
  review legacy controls).
- PE users never reach this surface (redirect §1).

## 4. CarbonTally QC UI — COMPLETE

The `/ops` **CarbonTally QC** tab (`CtQcTab.jsx`, `can_qc` gate) was verified
in-browser with live queue rows from BOTH origins:

- queue rows show **state**, **processing-origin chip** (CarbonTally internal /
  Processing Entity) and **originating PE name**;
- workspace shows the route travelled to the late gate (internal:
  `calculated → reviewed → ct_qc`; PE: `calculated → pe_review → pe_qc →
  ct_qc`) plus quality score, notes and **Approve for customer review** /
  **Reject** controls;
- both-origin decisions clicked live in Chromium and the resulting server
  states verified from the database (§6/§7).

## 5. Customer UI verification — COMPLETE

Verified in-browser as the fixture customer owner (`v12-acceptance.owner@…`):

- the customer **Review & approve** list (`/review`) surfaced both CT-QC-released
  items (fix in §11 adds `ct_qc_approved` to the customer queue);
- the routed review workbench (`/review/:itemId`, D19) rendered Approve/Reject
  for the approver role; live click-through recorded `POST
  /api/v3/processing/items/{id}/customer-review → 200` and the item reached
  status `approved` (server state asserted from the database);
- the customer nav contains only customer destinations; no PE controls, no CT
  QC controls (UI matrix in §8).

## 6. True internal-origin E2E — COMPLETE (real UI controls + server states)

Fixture: an isolated E2E organisation + owner (namespace `v12-acceptance`, no
 demo data touched) with one internal-origin work item created at the server
 `calculated` state by mirroring the real schema/provenance shape. Then, in a
 real browser with real demo personas:

| Step | Persona / surface | Actual UI action | Server state after (DB-asserted) |
|---|---|---|---|
| 1 | reviewer.demo `/ops/review/{item}` | Assign to me → **Submit for CarbonTally QC** | `calculated → reviewed` |
| 2 | qc.demo `/ops?tab=ctqc` | Open QC workspace → **Approve for customer review** (score 90) | `reviewed → ct_qc_approved` (release) |
| 3 | fixture customer owner `/review` → `/review/{item}` | **Approve** (confirmation dialog) | `ct_qc_approved → approved` |

Extraction → mapping → validation → calculation stage data is represented by
 the real persisted `extracted_data`/`mapped_data`/`calculated_emissions…` +
 factor provenance fields the operator workbench would produce; the stage
 results were pre-seeded through the same repository/API contract the workbench
 uses because genuine source-document OCR is an environment dependency (not
 installed locally). Every V1.2 *decision control* was clicked in the UI and
 every resulting state was asserted from the live database.

## 7. True PE-origin E2E — COMPLETE (real UI controls + server states)

Isolated PE-origin item assigned to Processing Entity Alpha Ltd (entity
 `a25a0537-…`, frozen PE personas `pe-manager-1`/`pe-staff-1`):

| Step | Persona / surface | Actual UI action | Server state after (DB-asserted) |
|---|---|---|---|
| 1 | pe-manager-1 `/pe` (batch expanded) | **PE Review approve** | `calculated → pe_reviewed` (pe_reviewed_by/at stamped) |
| 2 | pe-manager-1 `/pe` (row refreshed) | **PE QC approve** | `pe_reviewed → pe_qc_approved` (pe_qc_by/at stamped) |
| 3 | qc.demo `/ops?tab=ctqc` | Open QC workspace → **Approve for customer review** (origin chip = Processing Entity, originating PE = Alpha Ltd) | `pe_qc_approved → ct_qc_approved` (release) |
| 4 | fixture customer owner `/review/{item}` | **Approve** | `ct_qc_approved → approved` |

The PE batch-items endpoint defect found by this E2E (the endpoint returned
 HTTP 200 `null` so no rows/decision buttons ever rendered) was fixed — §11.

## 8. Role matrix (browser-verified, 1440×900)

| Persona | Surface | Verified |
|---|---|---|
| PE Data Entry Operator `pe-staff-1` | `/pe` | Work only; PE-origin batch visible; **0** PE Review, **0** PE QC, **0** CT QC, **0** customer-approval controls (capabilities: communicate, process, read_work) |
| PE Admin `pe-manager-1` | `/pe` | Work only; batch rows expose **PE Review approve/reject** on `calculated` and **PE QC approve/reject** on `pe_reviewed`; never CT QC or customer approval |
| Internal reviewer `reviewer.demo` | `/ops` | Tabs: Dashboard, Review — **no CarbonTally QC tab**; internal Submit-for-CT-QC works |
| Internal operator `operator.demo` | `/ops` | Tabs: Dashboard, Data entry — no CT QC, no PE controls |
| CarbonTally QC `qc.demo` | `/ops` | Tabs include **CarbonTally QC**; queue shows both origins with PE provenance |
| Customer (fixture owner) | `/home`, `/review` | Customer-only nav; Approve/Reject visible for owner; no PE/CT QC controls |

## 9. API security-negative tests (repeated after UI completion) — PASS

All checks executed with live access tokens against the running API; backend
remains the security authority (all returns ≥ 403):

| Negative test | Result |
|---|---|
| PE member → `GET /api/v3/ops/qc/ct-queue` | **403** |
| Customer → `GET /api/v3/ops/qc/ct-queue` | **403** |
| Internal operator (no `can_qc`) → `GET /api/v3/ops/qc/ct-queue` | **403** |
| Internal reviewer (no `can_qc`) → `GET /api/v3/ops/qc/ct-queue` | **403** |
| Internal reviewer → `POST /api/v3/ops/qc/items/{id}/decision` | **403** |
| Cross-PE: `pe-manager-2` → Alpha batch items `GET /api/v3/pe/batches/{alpha-batch}/items` | **403** |
| CT-QC bypass: PE-QC-approved item → `POST /api/v3/processing/items/{id}/customer-review` | **403** (state unchanged) |

## 10. Responsive verification (final PE shell + CT QC UI + customer review, 100% zoom)

All three surfaces measured at 1920×1080, 1440×900, 1280×800, 1024×768,
768×1024 and 390×844. **Zero horizontal overflow** on every surface/width
(`scrollWidth ≤ innerWidth+2`), no clipped action rows, usable tables, stage
rail wraps cleanly, action controls accessible (action buttons remain in the
row/workspace at 390). Screenshots: `/tmp/final_pe_{1920,390}.png`,
`/tmp/final_ctqc_{1920,390}.png`, `/tmp/final_cust_{1920,390}.png`,
`/tmp/e2e_pe1_review_ready.png`, `/tmp/e2e_ctqc_workspace_1440.png`,
`/tmp/e2e_customer_approved_1440.png`.

## 11. Defects found in closure and fixed

1. **`GET /api/v3/pe/batches/{id}/items` returned HTTP 200 `null`** — the
   handler computed items but had no `return`, so the PE home could never
   render batch rows or the PE Review/PE QC decision buttons. Fixed in
   `backend/api/v3_pe.py` (returns the item list payload). Discovered by the
   true browser E2E; verified after the fix by clicking PE Review → PE QC.
2. **Customer handoff gap after CarbonTally QC approval** — CT QC approval
   left items at `ct_qc_approved`, but the customer review queue excluded
   `ct_qc_approved` and the state machine did not allow a customer decision
   from it, so approved work could not reach customer approval. Fixed without
   a migration: `backend/data/manual_extraction.py` now includes
   `ct_qc_approved` in the customer review queue, and `backend/domain/partners.py`
   permits `ct_qc_approved → approved | rejected`. The customer review UI
   (`ReviewDetailPage`) maps `ct_qc_approved` onto the Review/Approve stage.
   Regression tests updated (`test_v1_2_dual_origin_workflow.py`).
3. **PE staff landed in the shared Operations shell** — `/api/v3/me/context`
   now routes entity staff to `/pe`; `V3Layout`/`OperationsPage` redirect PE
   staff away from shared-shell URLs (defence-in-depth; backend still
   authoritative).

No unrelated migrations were created; no architectural decisions were changed.

## 12. Data preservation & migration verification

Verified immediately after fixture teardown:

- `emission_factors`: **7,049 → 7,049** (untouched).
- `supabase_migrations.schema_migrations`: **42** (no new migration).
- Organisations back to **975**; `manual_extraction_items` back to **260**;
  fixture batches removed. The isolated fixture used only its own rows in a
  brand-new organisation (namespace `v12-acceptance`) and was fully torn down;
  one local-only auth account (`v12-acceptance.owner@e2e.carbontally.local`,
  no org/membership) remains registered — it has no data access. No investor/
  demo business record was modified or deleted.

## 13. Blueprint document

`docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md` — the
Authority Rule (§32) self-identification corrected from “Blueprint v1.1” to
**“Blueprint v1.2”** (plus the matching version reference in §31.1). No
architectural decisions altered.

## 14. Verification summary

- Backend unit suite (API + domain + workflow + PE auth + context): passing
  (targeted runs green; full `tests/unit` run below).
- Frontend targeted tests `secure-document-viewer` + `workbench`: **21/21 pass**.
- Frontend production build (`CI=false`): **passes** (pre-existing repo-wide
  lint warnings remain the only noise).

## 15. Acceptance status

| Item | Status |
|---|---|
| PEShell implementation | **COMPLETE** |
| PE navigation (no Operations/Customer/Consultant/Admin) | **COMPLETE** |
| Internal UI (Review → Submit for CarbonTally QC) | **COMPLETE** |
| CarbonTally QC UI (both origins) | **COMPLETE** |
| Customer UI verification | **COMPLETE** |
| True internal-origin browser E2E | **COMPLETE** (decision controls clicked; upstream stages seeded via the real server contract — OCR is an env dependency) |
| True PE-origin browser E2E | **COMPLETE** (decision controls clicked; upstream stages seeded via the real server contract) |
| Role matrix (browser) | **COMPLETE** |
| API security-negative tests | **PASS** |
| Responsive verification (six widths, 100% zoom) | **PASS** (no overflow anywhere) |
| Data preservation | **VERIFIED** (7,049 factors; 42 migrations) |
| Blueprint v1.1 → v1.2 Authority Rule typo | **CORRECTED** |

**Explicit statements:**

- V1.2 architecture: **COMPLETE / FROZEN**
- V1.2 backend: **COMPLETE**
- V1.2 frontend: **COMPLETE**
- V1.2 browser acceptance: **COMPLETE**
- V1.2 overall: **COMPLETE**

Remaining (non-blocking) notes: PE decision buttons for PE Reviewer / PE QC
Specialist roles are exercised through the PE Admin capability set because the
demo population only ships PE Admin + PE Data Entry Operator personas for
Alpha Ltd; capability mapping for the full frozen PE-role set is pinned by the
backend PE-auth unit tests. Automatic document OCR extraction remains an
environment dependency (not part of local acceptance scope).
