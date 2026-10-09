# CT-MP-SUB-004 — Manual Processing Commercial & Entitlement UI/UX — Implementation Report

**Document ID:** CT-MP-SUB-004
**Date:** 2026-10-04
**Status:** IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
**Governing specification:** `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md`
(UI/UX) + the ratified CT-PO-MP-SUB-003 commercial model
**Backend reuse:** CT-MP-SUB-003 (`backend/api/manual_processing_admin.py`,
`backend/services/manual_processing_routing.py`, `backend/data/manual_processing.py`)

> No production deployment, migration, configuration or commit was performed.
> No commercial rule, pricing, capacity tier, payment provider, persona or
> parallel subscription table was introduced.

---

## 1. Task and scope

CT-MP-SUB-004 exposes the **already-approved** CT-MP-SUB-003 commercial model to the
three audiences the PO-approved UI/UX specification defines, and keeps the three
concepts the specification requires to stay separate:

```
COMMERCIAL COVERAGE (direct | consultant-sponsored)
        -> ENTITLEMENT
              -> FIN-06 GOVERNANCE
                    -> PROCESSING ENTITY / ROUTING
```

In scope:

| # | Surface | Change |
|---|---|---|
| 1 | Platform Admin | A **Commercial Coverage** tab, visibly separate from the existing operational-routing tab, over the existing `/api/v3/admin/manual-processing/*` endpoints |
| 2 | Consultant | A **Manual Processing** tab in the existing consultant workspace, over the new caller-scoped `/api/v3/consultants/me/manual-processing/*` endpoints |
| 3 | Customer | A `/manual-processing` page in the existing customer shell, over the new org-scoped `GET /api/v3/organizations/{id}/manual-processing` endpoint |

Out of scope (explicitly not authorised by the specification, §8/§9): production
deployment/migration/configuration, new billing architecture, new commercial rules,
new authorization model, new persona, automatic PE assignment, deletion of
historical data, pricing / plan names / capacity tiers / payment mechanics.

---

## 2. Backend contract

All three endpoints are **caller-scoped**: no endpoint accepts an identity that the
browser could forge, and every commercial decision is re-checked server-side.

| Method | Path | Authorization | Purpose |
|---|---|---|---|
| GET | `/api/v3/organizations/{organization_id}/manual-processing` | `require_org_member()` | The caller's OWN organisation effective Manual Processing service state |
| GET | `/api/v3/consultants/me/manual-processing/coverage` | `require_consultant` | The caller's OWN firm purchased coverage + allocations |
| POST | `/api/v3/consultants/me/manual-processing/allocations` | `require_consultant` + `ensure_consultant_permission(context, "manage_clients")` | Allocate one eligible client under `SELECTED_CLIENTS` coverage |
| DELETE | `/api/v3/consultants/me/manual-processing/allocations/{allocation_id}` | same as above | Release one ACTIVE allocation belonging to the caller's OWN firm |

### 2.1 Authorization reuse (no new model)

* **Customer** — `require_org_member()` applies the existing F-05-R1 exact-tenant
  path rule, so `organization_id` must be the caller's own organisation. A
  consultant (not an org member) is denied; internal staff keep their existing
  operational exemption inside that guard.
* **Consultant** — `require_consultant` resolves the firm from authoritative server
  state (`consultant_firm_members` → the single distinct active firm →
  `consultant_profiles`). The firm id is read from
  `ConsultantContext.firm_member.firm_id`; **it is never taken from the request**.
* **Consultant writes** — the existing `can_manage_clients` capability flag
  (`ensure_consultant_permission`) is the closest existing "manage my client
  portfolio" surface. No new permission was invented.

### 2.2 Server-enforced write rules (mirroring `manual_processing_admin.py`)

Before any allocation is created, the endpoint re-checks, in order:

1. purchased coverage is **enabled** → else `409`;
2. coverage mode is `SELECTED_CLIENTS` → else `409` (an `ALL_ELIGIBLE_CLIENTS` firm
   needs no allocation);
3. capacity is not exhausted (`available > 0`) → else `409` "capacity is exhausted";
4. the target organisation is an **ACTIVE** client of THIS firm
   (`consultants.get_client_by_org` + `status == "active"`) → else `403`;
5. a duplicate active allocation surfaces as `409` (unique-active-allocation guard).

Release re-reads the caller's own ACTIVE allocations first and returns `404` for
anything else — a cross-firm allocation id is never silently released. (This is
deliberately stricter than the Admin release endpoint, which is admin-gated.)

### 2.3 Customer payload discipline

The customer response is a **projection**, not a subset dump. It exposes ONLY:

`organization_id`, `status`, `coverage_sources`, `direct_entitled`,
`sponsored_entitled`, `effective_entitled`, `consultant.{company_name}`,
`processing_mode`, `governance.enabled`,
`processing_entity.{configured,processing_entity_id}`, `operational_status`,
`effective.{enabled,effective,outcome}`.

It deliberately **omits** the consultant's `capacity`, `allocated`, `available`,
`over_allocated`, `allocations`, `eligible_clients`, `plan_code`, `firm_id`,
`firm_organization_id`, `consultant_id` and allocation ids — asserted by test.

### 2.4 Audit

Every allocation change records one entry through the EXISTING audit
infrastructure (`repos.audit.record(AuditEntry(...))`) with
`entity_type="consultant_mp_allocation"` and action
`manual_processing:allocation_created` / `manual_processing:allocation_released`,
scoped to the caller's firm, carrying the organisation id and `via="consultant"`.

---

## 3. Files changed

### 3.1 Backend (additive only)

| File | Change |
|---|---|
| `backend/api/v3_manual_processing_coverage.py` | **New** (404 lines). Three caller-scoped surfaces: customer read, consultant read, consultant allocate/release. Reuses CT-MP-SUB-003 domain + repository methods and the existing authorization chains. |
| `backend/api/router.py` | **Edited.** Import (lines 67–69) + `router.include_router(v3_manual_processing_coverage_router)` after the FIN-06 admin router (line 247). |

No existing endpoint, schema, migration, RLS policy or domain rule was modified.
There is **no new table and no new migration**. The only pre-existing test file
touched is the frozen org-scoped guard register (see §10), which its own docstring
requires to be updated deliberately when such a route is added.

### 3.2 Frontend

| File | Change |
|---|---|
| `frontend/src/v3/api.js` | **Edited.** Admin coverage/client-state/allocate/release clients; consultant coverage/allocate/release clients; customer `getMyManualProcessing(organizationId)`. |
| `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx` | **New.** Admin **Commercial Coverage** surface (§2 screens: firm coverage, SELECTED_CLIENTS capacity, ALL_ELIGIBLE_CLIENTS, effective entitlement). |
| `frontend/src/v3/ops/OperationsPage.jsx` | **Edited.** Registers the `Commercial Coverage` tab next to the existing `Manual Processing` tab; the coverage tab takes the same admin capability gate. |
| `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx` | **New.** Consultant coverage surface (§4 screens + §7 states). |
| `frontend/src/v3/consultant/ConsultantPage.jsx` | **Edited.** One added tab (`Manual Processing`) in the existing consultant tab set, passing the existing `can_manage_clients` capability. |
| `frontend/src/v3/customer/ManualProcessingPage.jsx` | **New.** Customer service-state page (§3 screens + §7 states). |
| `frontend/src/App.js` | **Edited.** One added route: `/manual-processing` (`ProtectedRoute` → `RoleRoute requireOrg` → `V3Layout`). |
| `frontend/src/v3/components/V3Layout.jsx` | **Edited.** One added entry in the existing D18 customer navigation model. |

### 3.3 Tests (new)

| File | Purpose |
|---|---|
| `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py` | **New** — 24 API acceptance/security tests (route exposure, customer surface, consultant surface, negatives). |
| `frontend/src/v3/__tests__/manual-processing-coverage.test.jsx` | **New** — 22 UI tests across the customer, consultant and Admin surfaces. |

---

## 4. Frontend surfaces and specification mapping

| Spec section | Requirement | Implementation |
|---|---|---|
| §2 Admin | Distinguish commercial coverage from operational routing | `ManualProcessingCoverageTab` is a separate tab; its header states the separation explicitly |
| §2 Admin | `SELECTED_CLIENTS` capacity/allocation | Purchased capacity, `allocated / capacity`, available, capacity meter (`role="progressbar"`), covered-clients table, release |
| §2 Admin | `ALL_ELIGIBLE_CLIENTS` | Eligible count, "covered automatically", "future eligible clients: automatically covered", eligibility source |
| §2 Admin | Effective entitlement | Per-organisation panel: direct / sponsored / effective / FIN-06 governance / Processing Entity / routing outcome / consultant relationship — never collapsed |
| §3 Customer | Effective service state only | `ManualProcessingPage` with direct, sponsored, direct+sponsored, not-entitled and entitled-but-unconfigured variants |
| §3 Customer | Do not expose consultant commercial data | Response omits it; a UI test asserts no `capacity`/`allocated`/`allocation`/`firm_id` text renders |
| §4 Consultant | Purchased coverage + remaining selected capacity | Coverage / mode / capacity / allocated / available + meter |
| §4 Consultant | Covered clients within authorization scope | Covered-clients table built from the caller's OWN firm allocations |
| §4 Consultant | Selected vs all-eligible distinguished | Mode badge + mode-specific rows; `ALL_ELIGIBLE_CLIENTS` offers "View Eligible Clients" and no allocation control |
| §4 Consultant | "Capacity exhausted" state | Explicit alert stating the consequence; the allocate control is not offered |
| §5 Transitions | No silent destruction of history | No transition write UI is offered; a released allocation stays as history and is excluded from "covered clients" |
| §6 State rules | Existing server semantics only | The UI renders server values verbatim (`SELECTED_CLIENTS`, `ALL_ELIGIBLE_CLIENTS`, `configured`, `not_yet_configured`, `enabled`) — no new status vocabulary |
| §7 Empty/error states | Explicit Admin / Consultant / Customer / allocation-error copy | Implemented as the empty and allocation-error states |
| §8 Navigation | Existing surfaces; make the distinction visible | `Commercial Coverage` + `Manual Processing` tabs; one consultant tab; one customer nav entry + route |
| §9 Unresolved commercials | Display configured values only | No price, plan name, tier or payment surface exists in the new UI |
| §10 Acceptance | Criteria 1–17 | Covered by the tests in §6 |

### 4.1 Design-system compliance (D21 / §40 / §50)

New UI uses the D21 primitives (`Card`, `Badge`, `Alert`, `EmptyState`,
`LoadingState`, `ErrorState`) and the established class vocabulary (`v3-page`,
`v3-page-header`, `v3-table`, `v3-btn`, `v3-form-group`, `v3-actions`,
`v3-muted`) plus the existing Admin-tab workspace classes. No one-off visual
system was introduced.

Status is never communicated by colour alone (badges always carry text), and the
capacity meter is exposed to assistive technology via `role="progressbar"` with
`aria-valuenow` / `aria-valuemin` / `aria-valuemax` and an `aria-label`.

---

## 5. Navigation and authorisation boundary

| Surface | Entry point | UI gate | Server boundary |
|---|---|---|---|
| Admin | Operations → **Commercial Coverage** tab | `can_manage_organizations` (existing) | `/api/v3/admin/manual-processing/*` (FIN-06 admin gate) |
| Consultant | Consultant workspace → **Manual Processing** tab | existing `prof.can_manage_clients` (write controls only) | `require_consultant` + `ensure_consultant_permission(..., "manage_clients")` |
| Customer | Customer nav → **Manual processing** (`/manual-processing`) | `RoleRoute requireOrg` | `require_org_member()` (F-05-R1 exact tenant) |

The UI gates are navigation/affordance only. A disabled or absent control is never
the security boundary: both new write endpoints re-check permission, capacity, mode
and eligibility server-side, and the customer/consultant reads are scoped to the
authenticated caller's own organisation/firm.


---

## 6. Tests

### 6.1 New backend API tests — `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py` (24 tests, all pass)

Route exposure uses the shared helper the repo already provides
(`tests/unit/api/route_paths.flatten_router_paths`), so the three new paths are
verified as genuinely registered on `api.router` — not merely declared.

* **Route exposure** — the three paths + `{allocation_id}` are exposed.
* **Customer** — 401 unauthenticated; `not_included` with no commercial path;
  direct → `available`; sponsored → names the consultant; direct+sponsored;
  entitled-but-unconfigured is NOT reported as not-subscribed; the payload never
  leaks `capacity` / `allocated` / `available` / `over_allocated` / `allocations` /
  `eligible_clients` / `unallocated_eligible_clients` / `covered_clients` /
  `plan_code` / `firm_id` / `firm_organization_id` / `consultant_id` /
  `allocation_id`; cross-organisation read → `403`; a consultant → `403`.
* **Consultant** — firm resolved from context (never the request); mode/capacity/
  allocated/available/allocations/eligible clients; client names resolved; non
  consultant → 401/403; allocate → `200` + audit entry; `manage_clients` missing →
  `403`; ineligible organisation → `403`; capacity exhausted → `409`;
  duplicate → `409`; `ALL_ELIGIBLE_CLIENTS` → `409`; no purchased coverage → `409`;
  release → `200` + capacity returned + audit entry; **another firm's allocation →
  `404`**; unknown allocation → `404`; release without `manage_clients` → `403`;
  unknown payload fields (`consultant_id`) → `422` (a client cannot name a firm).

### 6.2 New frontend UI tests — `frontend/src/v3/__tests__/manual-processing-coverage.test.jsx` (22 tests, all pass)

Customer (6), Consultant (9), Admin (7) — covering the five customer states, the
mode-specific consultant views, capacity exhaustion, permission-disabled writes,
and both empty/error states. Includes the negative assertion that the customer
surface renders no internal consultant commercial text.

### 6.3 Regression

| Suite | Result |
|---|---|
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` + `backend/tests/unit/domain/test_consultant_mp_coverage.py` + `backend/tests/unit/api/test_v3_routes_exposed.py` | **55 passed** |
| `backend/tests/unit/api` (full directory) | see §7.2 |
| Full frontend Jest suite | **568 passed, 1 pre-existing failure** (see §9) |

Commands used (this environment):

```
cd /home/shomonrobie/ct_93d5cdd
/usr/bin/python3.14 -m pytest backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py -q

cd frontend
CI=true npx --no-install react-scripts test --testPathPattern 'manual-processing-coverage' --watchAll=false
```

---

## 7. Runtime verification

### 7.1 Backend

`/usr/bin/python3.14 -m pytest backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py -q`
→ `24 passed`, exit 0.

Route registration is proven at runtime by the route-exposure test and by the
functional tests actually dispatching to the new handlers through the real
`api.router.create_app()` app built by `tests/unit/api/conftest.py`.

### 7.2 Full backend API unit directory

`/usr/bin/python3.14 -m pytest backend/tests/unit/api -q` → **2393 tests collected, 1 failure**.
The single failure is the pre-existing, environment-dependent
`test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
(§9.3). The previously-failing F-05-R1 frozen-register test now **passes** after the
deliberate register update described in §10.

### 7.3 Frontend

* New suite: `22 passed`, exit 0.
* Full suite: `Test Suites: 2 failed, 47 passed, 49 total` /
  `Tests: 1 failed, 568 passed, 569 total` (the failures are the pre-existing
  environment/dependency issues in §9.1 and §9.2).
* All modified/new source files parse cleanly (JSX, via `@babel/parser`).

---

## 8. Security verification

| Boundary | Verified |
|---|---|
| Customer A → Customer B organisation | `403` (F-05-R1 exact tenant; asserted) |
| Consultant → customer organisation route | `403` (not an org member; asserted) |
| Non-consultant → consultant route | `401/403` (asserted) |
| Consultant without `manage_clients` → allocate/release | `403` (asserted) |
| Consultant → allocation of an organisation that is not their active client | `403` (asserted) |
| Consultant A → Consultant B's allocation (release) | `404` — never silently released (asserted) |
| Client forging `consultant_id` in the allocate body | `422` (`extra="forbid"`; asserted) |
| Customer response leaking consultant capacity/ids | asserted absent |
| Capacity over-allocation | `409` server-side (asserted) |
| Duplicate active allocation | `409` server-side (asserted) |

No RLS policy was changed, no RLS bypass was introduced, and no service-role
behaviour was widened. The new endpoints use the same repository methods and the
same authorization chains as the existing FIN-06 Admin control plane.



---

## 9. Pre-existing failures (NOT caused by CT-MP-SUB-004)

Three failures exist in the working tree that are **not** attributable to this task.
They are stated here rather than silently omitted (§73/§74).

### 9.1 `src/App.test.js` — suite cannot load (frontend)

```
Cannot find module 'react-router/dom' from 'node_modules/react-router-dom/dist/index.js'
  at Object.<anonymous> (src/App.js:4:1)
```

A broken/mismatched `react-router-dom` install in the local `node_modules`
(the installed `react-router` build does not expose the `react-router/dom`
subpath that the installed `react-router-dom` requires). The failure occurs while
resolving the pre-existing `import ... from 'react-router-dom'` at
`src/App.js:4`, before any CT-MP-SUB-004 import is reached. This is an
environment/dependency-install defect, not a source defect.

### 9.2 `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` — 1 failing test (frontend)

```
DR-007 investor-facing display fixes › Issue 3 —
customer review detail shows Mapped activity from mapped_data.activity
Expected substring: "Natural gas"   Received string: "Mapped activity"
```

`frontend/src/v3/customer/ReviewDetailPage.jsx` and the test file are both
**unmodified** in this working tree, and neither is imported by any
CT-MP-SUB-004 file.

### 9.3 `backend/tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` (backend)

```
assert body["verification_delivered"] is False
E  assert True is False
```

`backend/api/v3_discovery.py` returns the honest outcome of
`send_transactional_email(...)`, which depends on whether an email provider /
credential is configured in the environment. The test assumes none is; this local
environment reports delivery. Both `backend/api/v3_discovery.py` and the test file
are **unmodified** (`git status --porcelain` → empty) and unrelated to Manual
Processing.

---

## 10. Deliberate update to an existing frozen register

`backend/tests/unit/api/test_f05_r1_org_scope_authorization.py` maintains
`FROZEN_ORG_SCOPED_GUARDED_ROUTES` — the register of every organisation-path route
guarded by `require_org_member()` / `require_org_admin()`. Its docstring requires
that **adding such a route be a deliberate act**: the register must be updated
after confirming the new route really enforces F-05-R1 exact-tenant authorization.

The new customer endpoint is exactly such a route (organisation id in the path,
guarded by `require_org_member()`, exact-tenant enforced by
`auth.enforce_org_path_scope`). It was therefore **deliberately added** to the
register with an explanatory comment, and the test now passes.

This is the only pre-existing test file modified by CT-MP-SUB-004.

---

## 11. Git state

* Branch/HEAD at time of implementation: `375a48dc1b9e9cfd74090bbf747554ae997acb59`.
* **No commit, no push, no branch change, no history rewrite, no reset.**
* No `.env`, credential, token, JWT or signed URL was created or committed.
* No production resource was touched; no migration was added or applied.

Working-tree changes introduced by CT-MP-SUB-004:

```
 M backend/api/router.py
 M backend/tests/unit/api/test_f05_r1_org_scope_authorization.py
 M frontend/src/App.js
 M frontend/src/v3/api.js
 M frontend/src/v3/components/V3Layout.jsx
 M frontend/src/v3/consultant/ConsultantPage.jsx
 M frontend/src/v3/ops/OperationsPage.jsx
?? backend/api/v3_manual_processing_coverage.py
?? backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py
?? frontend/src/v3/__tests__/manual-processing-coverage.test.jsx
?? frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx
?? frontend/src/v3/customer/ManualProcessingPage.jsx
?? frontend/src/v3/ops/ManualProcessingCoverageTab.jsx
?? docs/architecture/CT-MP-SUB-004-implementation-report.md
```

(The working tree also contains earlier, unrelated CT-MP-SUB-003 / CT-DISC-SUB-001
changes from previous sessions; none were reverted, absorbed or reformatted.)

---

## 12. Remaining limitations and deferred work

1. **No live/browser acceptance run was performed in this session.** Verification
   here is unit + API level (Jest + pytest over the in-memory fakes). The
   acceptance criteria in §10 of the specification should be confirmed in a real
   browser against the local stack, with screenshots per AGENTS.md §53.
2. **Admin lookups are by id.** The Admin Commercial Coverage tab takes a
   consultant firm id / organisation id, matching the existing Admin Manual
   Processing tab's convention. A searchable picker was not added because no
   existing endpoint provides an admin-facing consultant/organisation search on
   this surface; adding one would be new API surface, not a UI change.
3. **Coverage transitions (§5) are display-only.** The specification requires that
   if the implemented system does not support an operation the UI must not pretend
   it does. Mode changes happen through the existing plan/subscription
   administration, so no transition write UI was added; the tab states that
   existing allocations are preserved as history.
4. **`test_v3_discovery` and the two frontend failures** in §9 remain open and
   pre-existing.
5. **Investor demo data was not mutated.** No demo identity, credential, database
   row or seeded record was created, changed or deleted.
6. **Outstanding PO decisions remain unresolved** (pricing, plan names, capacity
   tiers, payment mechanics, proration, refunds, grace period, tax/VAT, custom
   enterprise pricing, independent capacity purchase, unused-capacity carryover —
   specification §9). The UI displays configured values only.

---

## 13. Status

**CT-MP-SUB-004 — IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

Implemented and tested at unit/API level. Not committed, not pushed, not deployed,
not independently accepted. Independent QA should re-test the three surfaces,
the cross-tenant negatives, and the Admin commercial-vs-operational distinction in
a browser.
