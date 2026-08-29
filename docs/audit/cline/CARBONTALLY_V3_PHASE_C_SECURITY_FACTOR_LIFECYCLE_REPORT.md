# CarbonTally V3 — Phase C (CL-42, CL-43, CL-44, CL-47): Security / Factor Lifecycle — Implementation Report

**Implementer:** Cline
**Date:** 2026-08-29
**Baseline:** `6148c86` (`main`) + Phase A (CL-56) + Phase B (CL-54)
**Authoritative contract:** OpenHands `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` CL-42, CL-43, CL-44, CL-47
(the P1 security/lifecycle items), per the recommended implementation order.

---

## 1. Summary

Phase C closes the three P1 gaps that blocked investor demonstration, plus the
P2 spend-mapping dead-end:

| Item | Contract | Outcome |
|---|---|---|
| **CL-42** | Viewer upload MUST return 403 at the API (viewer is read-only; owner/admin/member keep 201) | **Implemented + live-verified** |
| **CL-43** | Customer-factor lifecycle: duplicate family/version → clean 409 (never 500); version representable; approved factor can get a new version; explicit lifecycle; audit preserved | **Implemented + live-verified** |
| **CL-44** | Approved customer factors MUST appear in the mapping UI; customer factor takes precedence; source made clear | **Implemented + live-verified** |
| **CL-47** | Spend/GBP mapping must not dead-end: supported workflow surfaced explicitly (create an approved customer factor) | **Implemented + live-verified** |

---

## 2. CL-42 — Viewer upload denied (read-only role cannot write)

**Backend** (`backend/api/v3_documents.py`):
- The upload handler already used `require_org_member()` + `ensure_org_access()` — but a
  **Viewer is an org member**, so the read-only role passed.
- Added an explicit read-only gate **before any storage object or database row is created**:
  `current_user.role_name == "org_viewer"` (or `role == "org_viewer"`) → **403**
  `"Viewers are read-only and cannot upload documents"`.
- Owner / Admin / Member (`org_owner` / `org_admin` / `org_member`) keep 201.

**Acceptance evidence:**
- Live (local stack): `viewer.demo0008@demo.carbontally.local` upload → **403**; owner upload
  path is covered by the unit test (201, org-files row created) and the existing upload flow.
- The 403 happens before any write: the regression test asserts the org-files fake stays empty.

## 3. CL-43 — Customer-factor lifecycle (duplicate 409, version N+1, audit)

**Contract** (`backend/api/contracts.py`):
- `CustomerFactorCreate` gains an **optional `version`** field (`>= 1`).

**Repository** (`backend/data/customer_factors.py`):
- `find_by_family(...)` — resolves every factor in the version family
  `(organization_id, activity_type, reporting_year, country, COALESCE(unit,''), COALESCE(scope,''))`,
  exactly the columns of the unique `idx_customer_factors_family_version`.
- `next_version(...)` — `max(version)+1` in the family (or 1).

**API** (`backend/api/customer_factors.py`):
- **Explicit version** that is already occupied → clean **409** (never the raw 500 the
  unique-index raised before).
- **No version supplied**:
  - the newest slot in the family is still a **draft** → **409** ("a draft customer factor
    already exists in this family … edit the draft, approve it, or create an explicit new version") —
    this is the "duplicate create" conflict;
  - the newest slot is **active** (an approved factor) → the create auto-bumps to
    **draft vN+1** (D-cf-4: a new version of an approved factor without touching the active row).
- A `UniqueViolationError` race on the family index is mapped to the same clean 409.
- **Auditability preserved:** every lifecycle event (`customer_factor:created`, `:approved`,
  `:deactivated`) writes an append-only `AuditEntry` (entity_type `customer_factors`,
  carrying version/status/activity/unit/scope + actor), failures never break the request.

**Frontend** (`frontend/src/v3/admin/CustomFactorsTab.jsx`):
- **Version column** renders `v{n}` — the version is explicit in the UI.
- **"New version" action** on active factors opens the form pre-filled (labelled
  "Create a new version of … (draft vN+1)") and creates draft N+1 via the API.
- **409 handling**: duplicate/conflict responses surface the clean backend message
  ("…already exists — edit the draft above or create a new version"), never a raw 500.
- **Spend units** (`GBP`/`EUR`/`USD`) are representable in the factor form (feeds CL-47).

## 4. CL-44 — Approved customer factors in the mapping UI

**Backend** (`backend/api/dependencies.py` + the three mapping-options endpoints):
- New shared helper `customer_factor_mapping_options(repos, org_id)` returns the org's
  **approved (active)** customer factors as mapping candidates, each labelled
  `factor_kind='customer_factor'` (+ name/version/unit/scope).
- Merged into **all three** mapping-options surfaces:
  - `GET /api/v3/processing/items/{id}/mapping-options` (customer workspace),
  - `GET /api/v3/ops/items/{id}/mapping-options` (internal ops),
  - `GET /api/v3/ops/entities/{eid}/extraction/items/{id}/mapping-options` (PE workspace).
- Each response now carries `factors` (system) **and** `customer_factors` (approved customer
  factors). `no_factors_reason` is suppressed when a relevant factor exists.

**Frontend:**
- Customer workspace (`ProcessingItemWorkspace.jsx`): the picker merges
  `customer_factors` **first** (D-cf-5 precedence) and labels them
  `Customer factor v{n}` so the selected source is unambiguous.
- Ops/PE workbench (`ExtractionPanel.jsx`): the same merge + source label; the honest
  `no_factors_reason` is now shown in the line-item table when present.

**Why this completes the workflow:** the map endpoint already accepted a customer factor id
and the calculation engine already records `factor_kind='customer_factor'` + `customer_factor_id`
provenance (O1) — the missing piece was that the **UI could not reach** those factors.

## 5. CL-47 — Spend (GBP) mapping is never a silent dead-end

**Backend** (`backend/core/units.py` + mapping-options endpoints):
- New `spend_mapping_suggestion(activity, unit, has_factors)` returns a machine-readable
  payload for currency activities with no applicable factor:
  `{kind: 'spend_based', activity, unit, action: 'create_customer_factor', message: …}`.
- New `relevant_customer_factors(customer_factors, activity, unit)` ensures the guidance
  reflects whether ANY factor (system **or** customer) actually covers THIS activity/unit —
  an unrelated approved customer factor (e.g. a Diesel factor) must not mask a spend dead-end.
- The responses now carry `spend_suggestion` on all three mapping-options surfaces.

**Frontend:**
- Customer workspace mapping pane: when `spend_suggestion` is present, an actionable card
  appears — **"Create a spend-based customer factor"** — which deep-links to
  `Organisation administration → Custom Factors` (`/organization?tab=factors`, deep-link
  support added to `AdminPage.jsx`). The owner/admin creates and approves the spend factor;
  the item then maps to it and the automatic pipeline calculates it as `spend_based`.
- `CustomFactorsTab` unit options now include `GBP`/`EUR`/`USD` so spend factors are
  representable end-to-end.


---

## 6. Files changed

### Backend
| File | Change |
|---|---|
| `backend/api/v3_documents.py` | CL-42 — viewer deny before any write (403). |
| `backend/api/contracts.py` | CL-43 — optional `version` on `CustomerFactorCreate`. |
| `backend/data/customer_factors.py` | CL-43 — `find_by_family` + `next_version`. |
| `backend/api/customer_factors.py` | CL-43 — version resolution, duplicate 409 (pre-check + race fallback), `_audit_factor` on created/approved/deactivated. |
| `backend/api/dependencies.py` | CL-44 — shared `customer_factor_mapping_options` helper. |
| `backend/core/units.py` | CL-47 — `spend_mapping_suggestion` + `relevant_customer_factors`. |
| `backend/api/v3_processing_workflow.py` | CL-44/47 — customer mapping-options merges customer factors + spend guidance. |
| `backend/api/v3_operations.py` | CL-44/47 — staff + entity mapping-options merge customer factors + spend guidance. |
| `backend/tests/unit/api/fakes.py` | Test infra: `processing` on the bundle, `find_by_activity` on MemoryFactors, `create` on MemoryFiles, `find_by_family`/`next_version` on MemoryCustomerFactors. |
| `backend/tests/unit/api/test_v3_phase_c_regressions.py` | **New** — 11 regression tests (CL-42/43/44/47). |
| `backend/tests/unit/test_units.py` | CL-47 — `relevant_customer_factors` unit tests. |

### Frontend
| File | Change |
|---|---|
| `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | CL-44 — customer factors merged first + source label; CL-47 — spend CTA card. |
| `frontend/src/v3/admin/CustomFactorsTab.jsx` | CL-43 — version column, "New version" action, 409 handling; CL-47 — GBP/EUR/USD units; removed dead `retryCount` state. |
| `frontend/src/v3/admin/AdminPage.jsx` | `?tab=factors` deep-link support. |
| `frontend/src/v3/ops/ExtractionPanel.jsx` | CL-44 — customer factors in the ops/PE picker + `no_factors_reason`. |
| `frontend/src/v3/__tests__/customer-processing-workspace.test.jsx` | CL-44/47 — picker precedence + spend CTA tests. |
| `frontend/src/v3/__tests__/customer-factors-tab.test.jsx` | **New** — CL-43/47 factor-tab tests (version visibility, new-version action, 409 conflict, spend units). |

---

## 7. Verification

### Backend
- `python -m pytest tests/unit` → **1169 passed, 0 failed** (including the 13 new Phase C tests).
- The API unit-test suite required two pre-existing test-infra repairs from Phase A
  (`processing` bundle field + missing fake methods); those were fixed in `fakes.py`.

### Frontend
- `src/v3` suites → **131 tests passed / 9 suites** (incl. the new `customer-factors-tab` suite
  and the CL-44/47 additions). The single failing suite is the legacy `src/App.test.js`
  (`Cannot find module 'react-router/dom'` — a pre-existing react-router-dom v7
  module-resolution quirk at import time, unrelated to Phase C).
- `npx react-scripts build` → **success**.

### Live API (local stack, `127.0.0.1:8050`)
| Check | Result |
|---|---|
| CL-42 viewer upload (Pinnacle Works viewer) | **403** "Viewers are read-only and cannot upload documents" |
| CL-43 duplicate explicit `version:1` on Quayside's active Diesel family | **409** "…already exists at version 1 — create a new version instead" |
| CL-43 draft v1 → owner self-approve → new version (no explicit version) | **201 draft v2** (active v1 untouched) |
| CL-44 Quayside Diesel item mapping-options | **200**, `customer_factors` includes the active customer factor (`factor_kind='customer_factor'`), `no_factors_reason=None` |
| CL-47 Quayside Purchased goods/GBP item mapping-options | **200**, `factors=[]` + `spend_suggestion={kind:'spend_based', action:'create_customer_factor', unit:'GBP'}` |

### Demo-data safety
All live QA rows were created with clearly-labelled names, verified, and **soft-cleaned**
(deactivated) at the end of the run. Quayside's active "Customer Diesel factor v1" is intact;
no demo identity, document, or calculation was altered. The only residue is one orphaned
storage object (`phase_c_probe.pdf` — DB row deleted) from a pre-fix upload probe.

---

## 8. Remaining limitations / follow-on

- The "create a spend-based customer factor" CTA navigates to the organisation Custom
  Factors tab (deep-link); an inline create/approve wizard inside the mapper is a possible
  future polish, but the supported workflow is now reachable end-to-end.
- The legacy `src/App.test.js` react-router-dom v7 module-resolution failure pre-dates
  Phase C (fails at import) and is tracked separately.
- Next phases in the architecture order: **Phase D** (Staff/Admin canonical application,
  resolving the legacy `admin/` vs `v3/ops` split) → **Phase E** (PE application) →
  **Phase F** (shared-platform separation).

