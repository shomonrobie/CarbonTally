# CT-MP-SUB-004 — Independent Verification Report

**Document ID:** CT-MP-SUB-004-IV
**Task ID:** CT-MP-SUB-004-IV-20261004
**Status:** COMPLETE — VERIFIED WITH FINDINGS
**Type:** Independent verification (READ-ONLY). No implementation fix, no refactor, no behaviour change, no schema/RLS/migration change, no commit, no push, no deploy.

---

## 1. Task ID

`CT-MP-SUB-004-IV-20261004` — independent verification of the CT-MP-SUB-004
implementation against the authoritative specifications, the actual repository, and
the actual runtime.

---

## 2. Verification date

2026-10-04.

---

## 3. Verifier identity / context

CoStrict, acting as the independent verifier for CarbonTally. No part of the
implementation was authored in this session, and no implementation artefact was
modified.

Verification deployed four independent evidence channels rather than accepting the
implementer's report or its test results:

| Channel | Method | Independence |
| --- | --- | --- |
| C1 | Source inspection of implementation + specs | Read-only |
| C2 | **Own** runtime probe: real `api.router.create_app()`, real HTTP dispatch, own scenarios | Not the implementer's test module |
| C3 | **Live stack**: backend `127.0.0.1:8070` + real demo-lab PostgreSQL + real lab identities via gateway `127.0.0.1:54430` | Real database, real auth |
| C4 | **Browser**: Playwright + Google Chrome against the real CRA dev server with real logins | Real rendered UI |

Declared boundary compliance: no fix was applied, no code refactored, no feature added,
no schema/RLS/migration touched, no commit/push/deploy, no production resource
contacted. One read-only `GET`-only probe plus one `POST` that was **refused by the
server** (see §13.4). One frontend dev server was started for browser verification and
stopped afterwards (§17.3).

---

## 4. Authoritative documents used

| # | Document | Status read from the document itself |
| --- | --- | --- |
| D1 | `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` (CT-PO-MP-SUB-003) | **"PO APPROVED — AUTHORITATIVE COMMERCIAL/ENTITLEMENT"**; §28 "Product Owner Final Decision — APPROVED" |
| D2 | `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` (CT-UX-MP-SUB-003) | **"PROPOSED FOR PO APPROVAL"** (see §4.1 — material) |
| D3 | `docs/architecture/CT-MP-SUB-004-implementation-report.md` | "IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION" |
| D4 | `docs/architecture/CT-MP-SUB-003-implementation-report.md` | Backend CT-MP-SUB-003 report |
| D5 | `backend/domain/manual_processing.py`, `backend/services/manual_processing_routing.py`, `backend/data/manual_processing.py`, `backend/api/manual_processing_admin.py` | Existing architecture |
| D6 | `backend/auth.py`, `backend/api/consultant_auth.py` | Existing authorization model |
| D7 | `backend/tests/unit/api/test_f05_r1_org_scope_authorization.py` | Frozen org-scoped guard register |
| D8 | `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` | FIN-06 governance boundary |

### 4.1 Material discrepancy in the task's premise (read before §18)

The task statement asserts that CT-UX-MP-SUB-003 is
**"PO APPROVED — AUTHORITATIVE UI/UX SPECIFICATION"**.

**The authoritative document does not say that.** D2 states on its face:

* line 6 — `**Status:** PROPOSED FOR PO APPROVAL`
* §11 Governance status table:

  | Item | Status (verbatim) |
  | --- | --- |
  | CT-PO-MP-SUB-003 commercial model | **PO APPROVED / AUTHORITATIVE** |
  | CT-UX-MP-SUB-003 UI/UX design | **PROPOSED FOR PO APPROVAL** |
  | CT-MP-SUB-003 backend | **IMPLEMENTED / READY FOR INDEPENDENT VERIFICATION** |
  | **UI implementation** | **NOT YET AUTHORIZED** |
  | CoStrict verification | **NOT YET STARTED** |

* §11 Recommended PO disposition — *"**APPROVE CT-UX-MP-SUB-003 as the UI/UX
  implementation authority.** After explicit PO approval, create a separate uniquely
  identified Cline implementation prompt."*
* D1 §27 Implementation Boundary authorizes implementation *"through the separately
  identified implementation task `CT-MP-SUB-003`"* — i.e. the **backend** task, not a UI task.
* D1 §28 authority: *"Cline must implement the approved architecture without silently
  broadening, narrowing, or replacing these decisions."*

Per the task's own instruction *"Do not silently reinterpret PO-approved
requirements"*, this discrepancy is **reported, not resolved**. It is the single most
material finding (§18 F-1) and it is the reason the verdict is not A.

---

## 5. Implementation commit / HEAD observed

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`FINAL-03: freeze production cutover release`) |
| Working tree | **NOT clean** — 34 modified (tracked), 97 untracked |
| Branch position | `ahead 229` of `origin/p8-release-reconciled` (pre-existing) |
| Commit/push during verification | **NONE** |

CT-MP-SUB-004 artefacts observed (hashes = working tree):

| Artefact | sha256 |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-implementation-report.md` | `fe188a5146073527f39337404d02312ce536e8d48bbed85ec3294f5d46deb570` |
| `backend/api/v3_manual_processing_coverage.py` | `8951f8351c88f00ca853ffb68817a7c3fe9408f0728c8232acd1cc1731aec75d` |
| `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | `d55644f00ad04014e286597770c57dfff7582bad3fb9523f8729e53e5b29ea5d` |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | `a27ad96428808cc44fe632da41dec77c171ed6909cdbbf7bf8e74d676079f3da` |

---

## 6. Scope verified

| Area | Verified? |
| --- | --- |
| Backend route registration (source + runtime + live process) | **YES** |
| Backend authorization / multi-tenancy / error semantics | **YES** |
| Security negatives (14 cases) | **YES** |
| Audit behaviour | **YES** |
| FIN-06 vs commercial vs PE separation | **YES** |
| Customer / Consultant / Admin frontend source | **YES** |
| Customer / Consultant / Admin rendered UI (browser) | **YES** (3 surfaces) |
| Positive coverage states (capacity, covered clients, allocate/release UI) in browser | **NO — blocked by environment data** (§19) |
| F-05-R1 frozen register change | **YES** |
| Regression attribution (3 claimed failures) | **YES** |
| Scope-expansion / production-safety | **YES** |

---

## 7. Requirement-by-requirement verification matrix

Method key: **S** source inspection · **P** own runtime probe · **L** live stack · **B** browser · **T** test suite.

### 7.1 CT-MP-SUB-003 commercial/entitlement requirements

| # | Requirement (D1) | Impl location | Method | Evidence | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | Direct customer entitlement path (§3.1) | `ManualProcessingRouter.entitlement_for` via `GET /api/v3/organizations/{id}/manual-processing` | P | probe: `seed_entitlement` → `direct_entitled=true`, `coverage_sources=['direct']` | **PASS** |
| 2 | Consultant-sponsored path (§3.2) | `sponsored_entitlement` + firm's own org subscription plan | P | probe S1: sponsored true without allocation (ALL_ELIGIBLE_CLIENTS) | **PASS** |
| 3 | Relationship alone never grants entitlement (§2, §5) | `combine_entitlement` | P | probe: relationship seeded only → `status=not_included` | **PASS** |
| 4 | `SELECTED_CLIENTS`: finite capacity + explicit allocation (§4.1, §6) | `POST/DELETE .../allocations` | P | probe K4 allocate `200`, K8 release `200`; capacity returned | **PASS** |
| 5 | One active allocation = one capacity unit; release returns it (§4.1) | `summarize_allocations` | P | probe K8: `allocated 1→0`, `available 4→5` | **PASS** |
| 6 | `ALL_ELIGIBLE_CLIENTS` covers automatically, no per-client allocation (§4.2, §5) | `coverage_state_for_firm` | P | probe S1 + K13 (allocate → `409`) | **PASS** |
| 7 | Capacity exhaustion blocks new coverage (§6) | allocate guard | P | probe K12: `409 "capacity is exhausted"` | **PASS** |
| 8 | `ALL_ELIGIBLE_CLIENTS` is not an operational toggle (§4.2 Important) | allocation refused in that mode | P | probe K13 `409` | **PASS** |
| 9 | Effective entitlement = direct OR sponsored (§28) | `combine_entitlement` | P | probe S2: `['direct','sponsored']`, effective true | **PASS** |
| 10 | Entitlement ≠ FIN-06 governance ≠ PE assignment (§2, §16, §17) | `governance`/`processing_entity`/`effective` blocks | P | probe F1: entitled + `operational_status=not_yet_configured`, `gov.enabled=false`, `pe.configured=false`, `outcome=not_enabled` | **PASS** |
| 11 | No automatic PE assignment / no silent PE selection (§17) | no PE write in the new module | S | grep: no PE assignment call in `v3_manual_processing_coverage.py` | **PASS** |
| 12 | Existing open human/internal assignment preserved (§17) | untouched (routing layer, not this task) | S | no modification to `route_failed_job` in diff | **PASS** |
| 13 | Legacy `assisted_processing_available` compatibility preserved (§18) | `entitlement_from_plan` fallback | T | `test_consultant_mp_coverage.py` legacy-compat tests pass | **PASS** |
| 14 | No parallel subscription system (§19) | reuses existing model | S | no new table/migration; `git status supabase/migrations` shows only pre-existing files | **PASS** |
| 15 | Cross-tenant isolation (§22) | `require_org_member()` → `enforce_org_path_scope` | P/L | probe C3 `403`; live `403 "You don't have access to this organization"` | **PASS** |
| 16 | Consultant sees only own firm (§22) | firm id from `ConsultantContext.firm_member.firm_id` | S/L | probe K3; live `consultant_id` = caller's firm | **PASS** |

### 7.2 CT-UX-MP-SUB-003 UI/UX requirements + §10 acceptance criteria

| # | Requirement (D2) | Impl location | Method | Evidence | Result |
| --- | --- | --- | --- | --- | --- |
| 1 / AC1 | Admin distinguishes commercial coverage from operational routing | `operationsPage` two tabs | B | live `/ops` tabs: `Commercial Coverage` **and** `Manual Processing` present; coverage tab opens with explicit separation copy | **PASS** |
| 2 / AC2 | Admin distinguishes direct and sponsored entitlement | `ops/ManualProcessingCoverageTab` "Effective entitlement for one organisation" | S | per-client state renders direct/sponsored/effective separately; probe shows distinct fields | **PASS** |
| 3 / AC3 | Admin understands selected capacity/allocation | coverage tab capacity rows + meter | S | `role="progressbar"` + `aria-valuenow` present (`:69-70`) | **PARTIAL** — browser state not reachable (§19) |
| 4 / AC4 | Admin understands all-eligible coverage | coverage tab mode rows | S | `ALL_ELIGIBLE_CLIENTS` branch + "covered automatically" rows | **PARTIAL** — browser state not reachable (§19) |
| 5 / AC5 | Consultant understands purchased coverage | `consultant/ManualProcessingCoverageTab` | B | browser renders "Manual Processing Coverage" + empty state | **PASS** (empty state) / **PARTIAL** for populated |
| 6 / AC6 | Consultant understands remaining selected capacity | capacity rows + meter | S | `role="progressbar"` (`:65-66`), allocated/available rows | **PARTIAL** — not reachable in browser |
| 7 / AC7 | Consultant sees covered clients within authorization scope | `covered_clients` from own firm | S/L | live response returns own-firm `eligible_clients` with names; `covered_clients` derived from own allocations | **PASS** (API) |
| 8 / AC8 | Consultant distinguishes selected vs all-eligible | mode badge + branch | S | `selected = mode === 'SELECTED_CLIENTS'` (`:166`) drives distinct rows/actions | **PARTIAL** — not reachable in browser |
| 9 / AC9 | Customer understands why MP is available | `customer/ManualProcessingPage` | B | renders status/coverage/copy per state | **PASS** (not-included) / **PARTIAL** for available |
| 10 / AC10 | Customer distinguishes direct vs sponsored | separate rows + "Your coverage includes" list | P/B | API returns distinct `direct_entitled`/`sponsored_entitled`; UI renders both branches | **PASS** (API) / **PARTIAL** (browser) |
| 11 / AC11 | Customer cannot see internal consultant commercial data | payload projection | P | probe P2 raw-body leak scan: **NO LEAK TERMS FOUND** (13 terms) | **PASS** |
| 12 / AC12 | FIN-06 distinct from commercial entitlement | separate `governance` block | P | probe F1 | **PASS** |
| 13 / AC13 | Processing Entity distinct from commercial coverage | separate `processing_entity` block | P | probe F1 | **PASS** |
| 14 / AC14 | Empty/error states explicit | EmptyState/ErrorState/Alert in all 3 surfaces | S/B | 10+ empty/error branches; browser shows explicit empty states; `NO_COVERAGE_COPY` present | **PASS** |
| 15 / AC15 | Cross-tenant info not exposed | `require_org_member` | P/L | probe C3 `403`, live `403` | **PASS** |
| 16 / AC16 | No UI creates a commercial rule not in PO spec | no price/tier/plan input | S | grep: no `price`/`tier`/`checkout`/`stripe` in the 3 new files (comments only, asserting the opposite) | **PASS** |
| 17 / AC17 | Existing navigation + authorization architecture preserved | additive tabs/route only | S/B | `V3Layout` +1 entry; `App.js` +1 route; `OperationsPage` +2 tabs; `ConsultantPage` +1 tab | **PASS** |
| — | §2/§8 Admin tabs shown as `[ Commercial Coverage ] [ Operational Routing ] [ Assignments ]` | implemented as `Commercial Coverage` + `Manual Processing` | S/B | label is **"Manual Processing"**, not "Operational Routing" | **PARTIAL** (§18 F-6; §8 permits placement to follow existing architecture) |
| — | §6 no new backend semantic statuses for presentation | renders server values verbatim | S | UI renders `SELECTED_CLIENTS`, `ALL_ELIGIBLE_CLIENTS`, `configured`, `not_yet_configured`, `enabled` | **PASS** |
| — | §7 allocation-error copy | `ALLOCATION_ERROR_COPY` | S | copy lists the three possible reasons (`:52`) | **PASS** |
| — | §5 transitions must not be faked | display-only, no transition write | S | no transition UI; report limitation #3 | **PASS** |
| — | §9 unresolved commercials displayed as configured values only | no invented values | S/B | no price/tier anywhere; admin tab takes ids | **PASS** |

---

## 8. Backend / API findings

**Source verified** (`backend/api/v3_manual_processing_coverage.py`, 404 lines; registered at `backend/api/router.py:67` import + `:247` include):

| Aspect | Finding |
| --- | --- |
| Routes | 4 (3 declared + 1 path-param) — customer read, consultant read, consultant allocate, consultant release |
| Prefix / mounting | `APIRouter(prefix="/api/v3")`; included after the FIN-06 admin router |
| Customer authorization | `Depends(require_org_member())` — the **parenthesised** factory form (correct; the non-parenthesised form would silently skip the check) |
| Consultant authorization | `Depends(require_consultant)` → firm from `consultant_firm_members` → single distinct active firm → active profile; **never from the request** |
| Consultant write authorization | `ensure_consultant_permission(context, "manage_clients")` → mapped to the real column `can_manage_clients` (`consultant_auth.py:46`) — **correct mapping confirmed** |
| Write rule order | enabled → mode → capacity → eligibility → duplicate; matches the implementation report §2.2 |
| Payload hardening | `AllocationRequest` = `{organization_id, reason}` with `model_config = ConfigDict(extra="forbid")` → a forged `consultant_id` yields **422** |
| Release scoping | re-reads the caller's own active allocations; anything else → **404** |
| Audit | `entity_type="consultant_mp_allocation"`, `entity_id=<firm>`, actions `manual_processing:allocation_created` / `:allocation_released`, `via="consultant"` |
| Idempotency | **not applicable / not implemented** — allocate is guarded by the unique-active-allocation constraint (duplicate → 409) rather than a client idempotency key. Acceptable for this surface; noted as an asymmetry with the D37 billing order model (INFO). |

**Runtime route mounting (own probe, independent of the implementer's tests).**
Built the real application via `api.router.create_app()`, read its generated OpenAPI, and
dispatched real HTTP requests:

```
R1 openapi paths (create_app)   → includes admin + the three new manual-processing paths
R2 all 4 expected paths mounted → NONE MISSING
R3 methods → {"/api/v3/organizations/{organization_id}/manual-processing": ["get"],
              "/api/v3/consultants/me/manual-processing/coverage": ["get"],
              "/api/v3/consultants/me/manual-processing/allocations": ["post"],
              ".../allocations/{allocation_id}": ["delete"]}
```

**Live process confirmation.** Against the running backend (`127.0.0.1:8070`), an
unauthenticated request to `/api/v3/consultants/me/manual-processing/coverage` returned
**401** (not 404) — the route exists in the actually-running process.

**Response payload (customer) — projection discipline confirmed** by raw-body scan:
`capacity`, `allocated`, `available`, `over_allocated`, `allocation`, `eligible_client`,
`covered_client`, `plan_code`, `firm_id`, `firm-org`, `consultant_id`, `unallocated` →
**none present**.

---

## 9. Security / authorization findings

### 9.1 Negative cases — 14 executed, all DENIED correctly

| # | Case | Expected | Observed | Verdict |
| --- | --- | --- | --- | --- |
| N1 | Unauthenticated → customer route | 401 | **401** | PASS |
| N2 | Customer A → Customer B organisation (path) | 403 | **403** | PASS |
| N3 | Customer → consultant route | 403 | **403** | PASS |
| N4 | Consultant → customer route | 403 | **403** | PASS |
| N5 | Internal staff → customer route | denied | **403** | PASS (see F-2) |
| N6 | Processing-Entity staff → customer route | denied | **403** | PASS |
| N7 | Non-consultant → consultant coverage | 401/403 | **403** | PASS |
| N8 | Consultant identity with no firm membership | 403 | **403** | PASS |
| N9 | Consultant without `manage_clients` → allocate | 403 | **403** | PASS |
| N10 | Ineligible / forged organisation → allocate | 403 | **403** | PASS |
| N11 | Forged `consultant_id` in body | 422 | **422** | PASS |
| N12 | Duplicate active allocation | 409 | **409** | PASS |
| N13 | Capacity exhausted | 409 | **409** | PASS |
| N14 | `ALL_ELIGIBLE_CLIENTS` allocate | 409 | **409** | PASS |
| N15 | No purchased coverage → allocate | 409 | **409** | PASS |
| N16 | Release another firm's allocation | 404 | **404** | PASS |
| N17 | Release unknown / already-released allocation | 404 | **404** | PASS |
| N18 | Customer → admin route | 403 | **403** | PASS (live) |
| N19 | Live customer A → customer B | 403 | **403** | PASS (live) |

**No unexpected ALLOW was observed.** No cross-tenant leak was observed.

### 9.2 Live-stack security results

| Case | Live result |
| --- | --- |
| `org_a_admin` → own org | **200** |
| `org_a_admin` → `org_b` | **403** "You don't have access to this organization" |
| `consultant_owner` → own firm coverage | **200**, `consultant_id` = own firm |
| `consultant_member` → own firm coverage | **200** (same firm — see F-8) |
| `org_a_admin` → consultant route | **403** "Consultant access required" |
| `org_a_admin` → admin route | **403** "Staff access required" |
| `internal_operator` → admin coverage | **403** "staff lacks permission: can_manage_organizations" (correct for that role) |

### 9.3 Tenant / entitlement boundary conclusions

* The consultant firm id is derived from authoritative server state — a browser cannot
  name a firm.
* Commercial entitlement is evaluated server-side on every request; the UI is never the
  boundary (a disabled control is an affordance only).
* No RLS policy was changed, no RLS bypass introduced, no service-role behaviour widened.
* The customer projection cannot expose consultant commercial internals even when the
  customer *is* sponsored.

---

## 10. Customer UI findings

Source: `frontend/src/v3/customer/ManualProcessingPage.jsx` (231 lines).
Route: `/manual-processing` (`frontend/src/App.js` — `ProtectedRoute → RoleRoute requireOrg → V3Layout`).
Navigation: one added entry `{ to: '/manual-processing', label: 'Manual processing' }` in the existing D18 model (`V3Layout.jsx`).

| Aspect | Finding |
| --- | --- |
| Org resolution | server-side via `resolveV3Organization()`; the browser never supplies the org id |
| States implemented | not-entitled; direct; sponsored (with consultant name); direct+sponsored; entitled-but-unconfigured; plus a separate "configured but not enabled" warning |
| AC11 (no consultant internals) | satisfied — only `consultant.company_name` is rendered |
| FIN-06 / PE separation | rendered as separate rows + explicit explanation |
| Entitled-but-unconfigured | explicitly says *"This is not the same as not being subscribed."* — matches D2 §3 |
| Empty/error | `LoadingState`, `ErrorState` with retry, explicit not-entitled copy |
| D21 design system | uses `Card`, `Badge`, `Alert`, `StateViews` + `v3-*` classes |
| Deviation | none material |

**Live browser evidence:** the page rendered correctly for `org_a_admin` and showed the
**NOT INCLUDED** state with the D2 §3 copy and a working "View available plans" link.

---

## 11. Consultant UI findings

Source: `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx` (393 lines).
Entry: one added `Manual Processing` button in the existing consultant tab set (`ConsultantPage.jsx`), rendering `<ManualProcessingCoverageTab canManageClients={canManageClients} />`.

| Aspect | Finding |
| --- | --- |
| Firm scoping | endpoint is caller-scoped; the tab has no firm-id input |
| SELECTED_CLIENTS | capacity/allocated/available rows + `role="progressbar"` meter + "Add Client" allocation form |
| ALL_ELIGIBLE_CLIENTS | distinct branch: covered automatically, "View Eligible Clients", **no** allocation control |
| Capacity exhausted | explicit alert explaining the consequence and the remedies; allocate control withheld |
| Covered clients | list built from the caller's own firm's allocations |
| Permission gating | write controls `disabled={!canManageClients || busy}` |
| Empty state | "No consultant coverage active" + *"No Manual Processing consultant coverage is currently active. Your firm's subscription coverage will appear here when configured."* — verbatim D2 §7 |
| Unauthorized data | none exposed; no PE assignment surface; no FIN-06 activation control |
| Release semantics | the UI states a released allocation is retained as history; it does **not** promise automatic release (D2 §4 requirement satisfied) |

**Live browser evidence:** the tab rendered, and clicking it produced
`Manual Processing Coverage — No consultant coverage active` + the D2 §7 empty-state copy.
**No page errors.**

---

## 12. Admin UI findings

Source: `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx` (587 lines).
Registration: `OperationsPage.jsx` pushes `Commercial Coverage` **and** `Manual Processing`
under `if (p.can_manage_organizations)`.

| Aspect | Finding |
| --- | --- |
| Commercial vs operational separation | two distinct tabs; the Commercial Coverage tab opens with: *"Who purchased what, and which clients are covered. This is deliberately separate from the operational routing view: buying coverage does not enable processing, and a configured Processing Entity does not create commercial entitlement."* |
| Commercial coverage content | firm coverage (mode, capacity, allocated, available, over-allocated), covered-clients table, eligible-clients-awaiting-allocation table, release action |
| Effective entitlement per client | separate panel keeping direct / sponsored / relationship / governance / PE / routing distinct — never collapsed (D1 §20) |
| `ALL_ELIGIBLE_CLIENTS` | eligible count + automatic coverage messaging |
| `role="progressbar"` | present with `aria-valuenow` |
| Permission gating | `disabled={!canManage || busy}` on allocate/release; an explanatory note when `!canManage` |
| Loading/error/empty | `LoadingState`, `ErrorState`, `EmptyState` ("No coverage configured" / "No clients covered yet" / "No eligible client awaiting allocation") |
| D21 / existing conventions | reuses existing Admin-tab workspace classes; no one-off visual system |
| Lookup convention | firm/organisation are entered by id (no picker) — matches the implementation report limitation #2 and the pre-existing Admin MP tab convention |
| `activeCanManage` | see §12.1 |

### 12.1 `activeCanManage` assessment (explicitly requested)

Implemented logic:

```jsx
const activeCanManage =
  activeId === 'manual-processing' || activeId === 'manual-processing-coverage'
    ? !!p.can_manage_organizations
    : !!p.can_manage_staff;
```

**Correct for all applicable Manual Processing tab IDs.** Both MP tabs resolve to
`can_manage_organizations`, which is the capability the FIN-06/MP backend actually
enforces; every other tab keeps `can_manage_staff`. This diff also **fixes a latent
mis-gating**: previously `canManage={!!p.can_manage_staff}` was passed to *every* tab,
including the Manual Processing tab whose server gate is `can_manage_organizations`.
Confirmed against `ManualProcessingTab`, which consumes `canManage` for its enable/route
controls. → **PASS (improvement)**.

**Live browser evidence:** the admin `/ops` surface rendered both new tabs and the
Commercial Coverage tab opened with the separation statement. **No page errors.**

---

## 13. Browser / Demo Lab evidence

### 13.1 Environment

| Component | State at verification |
| --- | --- |
| Lab gateway `127.0.0.1:54430` | OPEN (nginx; proxies only `/auth/v1` + `/rest/v1` — 404 on `/` is **expected**, not a fault) |
| Backend `127.0.0.1:8070` | OPEN (uvicorn) |
| PostgreSQL `127.0.0.1:5432` | OPEN |
| Lab database | `carbontally_demo_local` (per `tools/demo_lab/lab.py`) |
| Frontend `localhost:3000` | **CLOSED at start** — the CRA dev server was **not running** |
| Static `frontend/build` | present but **STALE** (2026-09-22) and contains **no** CT-MP-SUB-004 code → not usable as evidence |

### 13.2 Method

Started the CRA dev server (`react-scripts start`, which compiled the working-tree source
— `webpack compiled successfully`), then drove the real UI with **Playwright + Google
Chrome (headless)** using **real lab identities** authenticated through the real gateway.

### 13.3 Results (rendered DOM, real logins, real backend)

| Surface | Identity | Result |
| --- | --- | --- |
| Customer nav | `org_a_admin` | `nav text contains 'Manual processing'` → **True** |
| `/manual-processing` | `org_a_admin` | **200**, rendered: `Manual Processing` / `NOT INCLUDED` / *"Manual Processing is not included in your current commercial coverage."* / *"It is not currently available through your commercial coverage."* / `View available plans` / separation explanation / `Organisation: Demo Lab Organisation A`. **page errors: []** |
| Consultant tab | `consultant_owner` | `'Manual Processing' tab found: True`; clicking rendered `Manual Processing Coverage` — `No consultant coverage active` + the D2 §7 copy. **page errors: []** |
| Admin `/ops` | `platform_admin` | `'Commercial Coverage' present: True`, `'Manual Processing' present: True` (two distinct tabs); clicking Commercial Coverage rendered the separation statement and the lookup form. **page errors: []** |

Screenshots captured (full page, 1440×900):
`/tmp/ct_mpsub004_shots/customer-manual-processing.png`,
`/tmp/ct_mpsub004_shots/consultant-coverage.png`,
`/tmp/ct_mpsub004_shots/admin-commercial-coverage.png`.

> **Evidence limitation:** these screenshots live outside the repository (`/tmp`) and are
> therefore ephemeral. The substantive evidence is the rendered DOM text recorded above.
> No file was added to the repository during this verification.

### 13.4 Disclosures

* The live probe issued **one `POST`** (`/consultants/me/manual-processing/allocations`).
  It was **refused with 409** ("Your firm has no purchased Manual Processing coverage"),
  so **no row was created and no state changed**. This is disclosed for completeness.
* No destructive or mutating operation was performed. No demo identity, credential,
  database row or seeded record was created, changed or deleted.
* Positive coverage states could **not** be reached (see §19) because the demo-lab firm has
  no purchased coverage and no plan carries `features.consultant_manual_processing`;
  seeding that would be an unauthorized data mutation.

---

## 14. Regression-test findings

| Claimed failure (report §9) | Reproduced? | File modified by CT-MP-SUB-004? | Classification |
| --- | --- | --- | --- |
| `frontend/src/App.test.js` — suite cannot load: `Cannot find module 'react-router/dom'` | **YES**, identical | `App.test.js` **unmodified**; `App.js` modified (added route only) | **ENVIRONMENT (toolchain)** — see F-4 |
| `frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx` — 1 failed test | **YES** (contributes the `1 failed` test) | test file **unmodified**; `ReviewDetailPage.jsx` **unmodified** | **PRE-EXISTING** |
| `backend/tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | **YES** — `assert body["verification_delivered"] is False` → `assert True is False` | `v3_discovery.py` **unmodified**; test file **unmodified** | **PRE-EXISTING / ENVIRONMENT** (an email provider is configured in this environment, so delivery genuinely succeeded) |

**Attribution evidence (`git diff --name-only` / `git status --porcelain`):**

```
backend/api/v3_discovery.py                                        → NOT modified
backend/tests/unit/api/test_v3_discovery.py                         → NOT modified
frontend/src/v3/customer/ReviewDetailPage.jsx                       → NOT modified
frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx     → NOT modified
frontend/src/App.test.js                                            → NOT modified
frontend/package.json                                               → NOT modified
```

**Independent attribution cross-check.** The CT-DISC-SUB-001 discovery baseline captured
earlier the same day recorded **31 modified / 90 untracked**. The current state is
**34 modified / 97 untracked** — a delta of exactly +3 tracked
(`router.py`, `test_f05_r1_org_scope_authorization.py`, `frontend/src/App.js`) and
+4 untracked, plus edits to three files that were *already* modified before
CT-MP-SUB-004 (`api.js`, `ConsultantPage.jsx`, `OperationsPage.jsx`). **Every file in the
three claimed pre-existing failures lies outside that delta.** → The implementer's
classification is **independently confirmed** (with the F-4 root-cause correction).

**Are the new CT-MP-SUB-004 tests masking failures?** No. The backend suite builds the
**real** application via `create_app()` and overrides only leaf dependencies
(`get_current_user`, `get_repositories`, audit logger, event bus, search index) — the
routers and authorization chains are the production ones. The frontend suite renders the
real components with mocked API clients. My own independent probe reproduced the same
conclusions using a separate harness.

---

## 15. Full test results

| Suite | Collected | Passed | Failed | Skipped | Verdict |
| --- | --- | --- | --- | --- | --- |
| `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py` | 24 | **24** | 0 | 0 | matches claim (24) |
| `backend/tests/unit/api/test_f05_r1_org_scope_authorization.py` | 35 | **35** | 0 | 0 | register update valid |
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` | 32 | **32** | 0 | 0 | — |
| `backend/tests/unit/domain/test_consultant_mp_coverage.py` | 22 | **22** | 0 | 0 | — |
| `backend/tests/unit/api/test_v3_routes_exposed.py` | 1 | **1** | 0 | 0 | — |
| **Report's regression trio** (003 + domain + routes) | 55 | **55** | 0 | 0 | **exact match to claim** |
| `test_fin06_manual_processing_governance.py` | 12 | **12** | 0 | 0 | — |
| `test_fin06_manual_processing_enforcement.py` | 18 | **18** | 0 | 0 | — |
| **`backend/tests/unit/api` (full directory)** | ~2,393 | (all but 1) | **1** | 0 | 1 failure = `test_v3_discovery` (pre-existing) |
| **`frontend` CT-MP-SUB-004 suite** | 22 | **22** | 0 | 0 | matches claim (22) |
| **`frontend` full Jest** | 569 tests / 49 suites | **568** | **1** (1 suite could not load) | 0 | `2 failed, 47 passed` suites — **exact match to claim** |

Counts for the full backend API directory: pytest reported exactly **one** failure
(`test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`); no other
failure, error or skip appeared in the short summary.

**No test was altered, skipped, xfailed or configured away to obtain these results.**

---

## 16. F-05-R1 guard-register assessment

**Change under review** (`backend/tests/unit/api/test_f05_r1_org_scope_authorization.py`,
+9 lines): the customer route
`GET /api/v3/organizations/{organization_id}/manual-processing` was added to
`FROZEN_ORG_SCOPED_GUARDED_ROUTES` with an explanatory comment.

| Criterion | Assessment |
| --- | --- |
| Organisation scope in the path | **YES** — `{organization_id}` |
| Path param recognised by the guard | **YES** — `organization_id ∈ ORG_SCOPE_PATH_PARAMS` (`auth.py:402-406`) |
| `require_org_member()` actually applied | **YES** — `Depends(require_org_member())` (parenthesised, `:123`) |
| F-05-R1 enforcement actually reachable | **YES** — `require_org_member()` → `enforce_org_path_scope(request, current_user)` (`auth.py:953`) |
| Enforcement proven at runtime | **YES** — probe C3 `403`; live cross-tenant `403` |
| Does the change weaken the frozen contract? | **NO** — it is purely additive; no existing entry was removed or relaxed; the frozen set gained one entry |
| Is the register update justified? | **YES** — the register's own docstring requires adding such a route deliberately, and the route genuinely satisfies the criteria |

→ **PASS.** The register change is architecturally correct and does **not** weaken the
frozen security contract. Rejecting it merely because it touches a frozen register would
be unfounded.

---

## 17. Worktree / production-safety assessment

| Check | Result |
| --- | --- |
| Production deployment | **NONE** |
| Production migration | **NONE** — no migration added by CT-MP-SUB-004 |
| Production data mutation | **NONE** |
| Commit / push | **NONE** — HEAD `375a48dc…` unchanged; `git log -1` shows the pre-existing commit |
| Unauthorized configuration change | **NONE** |
| New tables / RLS / policy changes | **NONE** — `git status supabase/migrations/` shows only the two pre-existing untracked files from CT-MP-SUB-003/routing |
| Scope expansion | **NONE FOUND** — no payment provider, checkout, subscription purchase, pricing change, billing lifecycle change, automatic allocation release, or new persona. Grep of the new backend module for `stripe|paypal|checkout|payment_intent|price|pricing|tier|CREATE TABLE|ALTER TABLE|INSERT INTO|DROP` returned **only a comment** at line 14 stating such things were *not* introduced |
| Unrelated working-tree changes | **PRESERVED** — nothing was cleaned, reverted, reformatted or absorbed |
| Secrets | **NONE** introduced, printed or committed. Credentials were read from the mode-0600 file outside the repository and never echoed |

### 17.1 Worktree accounting (independent)

Delta versus the CT-DISC-SUB-001 baseline captured earlier the same day
(31 M / 90 ?? → 34 M / 97 ??):

**+3 tracked** — `backend/api/router.py`, `backend/tests/unit/api/test_f05_r1_org_scope_authorization.py`, `frontend/src/App.js`
**+4 untracked** — `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py`, `frontend/src/v3/__tests__/manual-processing-coverage.test.jsx`, `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx`, `frontend/src/v3/customer/ManualProcessingPage.jsx`, `frontend/src/v3/ops/ManualProcessingCoverageTab.jsx`, `docs/architecture/CT-MP-SUB-004-implementation-report.md` (6 new files), plus this verification report
**Further edits** to three files already modified before CT-MP-SUB-004 — `frontend/src/v3/api.js`, `frontend/src/v3/consultant/ConsultantPage.jsx`, `frontend/src/v3/ops/OperationsPage.jsx`.

`.gitignore` (215 changed lines) and the other pre-existing modifications were **already
present before CT-MP-SUB-004** and are **not** attributable to it.

### 17.2 Report inaccuracy on worktree provenance

The implementation report §11 lists the CT-MP-SUB-004 working-tree changes and then notes
that earlier CT-MP-SUB-003 / CT-DISC-SUB-001 changes are also present. This is broadly
accurate, but it means **file-level diffs cannot be attributed to CT-MP-SUB-004** for the
three files that were already dirty. See F-3.

### 17.3 Environment side-effects of this verification

1. A CRA dev server was started to enable browser verification and **stopped afterwards**
   (port 3000 returned to closed). A pre-existing `react-scripts` process
   (PID 315566, not started by this verification) was **left untouched**.
2. Probe scripts were written to `/tmp` only (`/tmp/ct_mpsub004_probe.py`,
   `/tmp/ct_live_probe.py`, `/tmp/ct_browser_verify.py`, `/tmp/ct_mpsub004_shots/`).
   A temporary copy used for import-path reasons was created and deleted inside `backend/`.
3. No repository file was created or modified except this report.

---

## 18. Findings classified by severity

### BLOCKER

**None.** No material implementation, security or commercial-entitlement failure was found.
All 19 security negatives held; entitlement resolution, capacity, masking and tenant
separation behave as specified.

### HIGH

**F-1 — Governance: UI implemented against a UI/UX specification that is NOT PO-approved.**
`docs/architecture/CT-UX-MP-SUB-003_...md` declares `Status: PROPOSED FOR PO APPROVAL`, and
its §11 table records **"UI implementation — NOT YET AUTHORIZED"**, with the recommended
disposition requiring **explicit PO approval before** a Cline implementation prompt is
created. `CT-PO-MP-SUB-003` §27 authorises implementation only through the backend task
`CT-MP-SUB-003`. CT-MP-SUB-004 nevertheless delivered the customer, consultant and admin
UI surfaces.
*Type:* PO DECISION REQUIRED / authorization gap (not a code defect).
*Impact:* acceptance authority is absent; the delivered scope cannot be declared accepted
until the PO either approves CT-UX-MP-SUB-003 (retrospectively or otherwise) or directs
otherwise. This is the reason the verdict is not A.
*Evidence:* D2 lines 6, 47-49, 629-643; D1 §27 lines 927-947.

### MEDIUM

**F-3 — Scope-attribution not verifiable for `ConsultantPage.jsx`.**
The diff of `frontend/src/v3/consultant/ConsultantPage.jsx` contains changes **outside**
the documented CT-MP-SUB-004 change set: two `consultantUploadError` copy strings were
reworded (upload-authorisation-expired and upload-storage messages).
*Type:* NOT VERIFIABLE (attribution) / documentation transparency.
*Why it matters:* the implementation report §3.2 documents only *"One added tab"* for this
file, so the report under-describes the diff. Because the file was already dirty before
CT-MP-SUB-004, authorship cannot be resolved from the working tree. No functional or
security risk was identified in the changed copy.

**F-5 — Positive coverage states are NOT browser-verified (verification gap).**
In the demo-lab environment the consultant firm reports `enabled:false`, `mode:null`,
`capacity:null` and no plan carries `features.consultant_manual_processing`, so the
following could not be exercised in a real browser: SELECTED_CLIENTS capacity meter and
covered-clients list, the allocate/release flows, the ALL_ELIGIBLE_CLIENTS populated view,
and the customer `available` / direct / sponsored / direct+sponsored states.
*Type:* NOT VERIFIED / BLOCKED BY ENVIRONMENT.
*Impact:* D2 §10 acceptance criteria 3, 4, 5 (populated), 6, 8, 9 (available) and 10
(presentational half) are verified only at unit/API level, not visually.

**F-6 — Admin tab labelling deviates slightly from the specification.**
D2 §2/§8 depict the tab set as `[ Commercial Coverage ] [ Operational Routing ] [ Assignments ]`.
The implementation labels the operational tab **"Manual Processing"** (the pre-existing
surface). D2 §8 states *"The exact placement can follow the existing CarbonTally navigation
architecture"*, and the distinction **is** made explicit in the Commercial Coverage tab's
own copy, so this is a **PARTIAL**, not a defect.
*Type:* PARTIAL / minor spec deviation.

### LOW

**F-2 — Inaccurate claim about internal-staff access on the customer route.**
Implementation report §2.1 states internal staff *"keep their existing operational
exemption inside that guard"*. **Verified false:** `require_org_member()` requires
`current_user.is_org_member`, and internal/PE staff are not organisation members, so they
receive **403** (probe C5, C6, C7).
*Type:* documentation inaccuracy. The behaviour is **stricter** than claimed and is
therefore safe; but the report is wrong, and if internal-staff visibility on this surface
is genuinely wanted, that is a product decision.

**F-4 — Incorrect root cause stated for the `App.test.js` failure.**
Report §9.1 attributes it to a broken install where *"the installed `react-router` build
does not expose the `react-router/dom` subpath"*. **Verified false:** the installed
`react-router@7.18.1` **does** export `./dom` (exports keys: `.`, `./dom`, `./internal`,
`./internal/react-server-client`, `./package.json`). The real cause is that the Jest
resolver shipped with `react-scripts` does not honour the package `exports` subpath
resolution for that module.
*Type:* documentation inaccuracy. Classification remains **ENVIRONMENT**, not a regression.

**F-7 — Over-broad exception mapping on allocate.**
`consultant_allocate_client` wraps `create_allocation` in a bare `except Exception` and
converts **any** failure into `409 "This client already has an active sponsored coverage
allocation."` A genuine infrastructure failure (database unavailable, FK/constraint error
other than the duplicate guard) would be reported to the consultant as a duplicate
allocation — misleading (AGENTS.md §46 discourages converting application errors into
misleading states).
*Type:* robustness / error-fidelity. Not a security defect.

### INFO

**F-8 — Consultant coverage read requires no `manage_clients` capability.**
Any active firm member can read the firm's full coverage payload (probe K17 = **200**),
while allocate/release require `can_manage_clients`. This is a defensible
member-read/capability-write split and is consistent with D2 §6 ("only their firm's
coverage"), but D2 does not state the read capability rule explicitly. Noted for PO
confirmation, not raised as a defect.

**F-9 — No client idempotency key on allocation writes.**
Duplicate protection relies on the unique-active-allocation constraint (409) rather than a
client-supplied idempotency key as used by the D37 billing model. Acceptable for this
surface; recorded as an asymmetry only.

**F-10 — Customer not-entitled state merges D2 §3 and §7 copy.**
The page renders both the §3 sentence and the §7 sentence plus a "View available plans"
link. This is faithful (arguably better) and is recorded only for completeness.

**F-11 — Admin coverage tab requires ids, no picker.**
Consistent with the implementation report's own limitation #2 and the pre-existing Admin MP
tab convention. Not a deviation from D2 (which shows a "Consultant Firm" field). Recorded
for UX follow-up.

---

## 19. Explicit list of anything NOT verified

| # | Not verified | Reason |
| --- | --- | --- |
| NV-1 | Browser rendering of SELECTED_CLIENTS capacity/allocation, covered-clients table, allocate and release flows | **BLOCKED BY ENVIRONMENT** — no firm has purchased MP coverage in the demo-lab database; seeding it would be an unauthorized data mutation |
| NV-2 | Browser rendering of ALL_ELIGIBLE_CLIENTS populated state | same as NV-1 |
| NV-3 | Browser rendering of the customer `available` / direct / sponsored / direct+sponsored states | same as NV-1 (no entitlement source is seeded) |
| NV-4 | Admin Commercial Coverage tab **after** loading a firm/organisation ("Load coverage" / "Load client state") | Deliberate: it would require the id lookups in NV-1 to be meaningful; the empty and unloaded states were verified |
| NV-5 | Responsive behaviour at the AGENTS.md §49 target viewports | Out of scope of the stated verification objectives; only 1440×900 was exercised |
| NV-6 | Accessibility audit beyond the observed `role="progressbar"` + `aria-valuenow` semantics | No automated a11y tooling was run |
| NV-7 | Visual comparison against the D2 ASCII layouts | The D2 ASCII is structural, not pixel-level; only structural presence was verified |
| NV-8 | Consultant allocate/release **against the real database** | Correctly refused (409, no purchased coverage); the write path is verified only against the in-memory harness |
| NV-9 | Long-running/performance behaviour | Out of scope |
| NV-10 | Email/notification side-effects | None expected from this surface |

Also **not verified because the source is not PO-approved**: whether the delivered UI is the
UI the PO actually wants (see F-1).

---

## 20. Explicit list of anything requiring a PO decision

| # | Decision required | Why |
| --- | --- | --- |
| PD-1 | **Retrospective/actual approval of CT-UX-MP-SUB-003**, or a direction on the status of the CT-MP-SUB-004 UI already implemented against it | D2 is `PROPOSED FOR PO APPROVAL` and states UI implementation is `NOT YET AUTHORIZED`; `CT-MP-SUB-003` §27 authorises only the backend task. **This is the gate on acceptance.** |
| PD-2 | Whether internal CarbonTally staff should see the **customer** Manual Processing surface | Currently denied with 403 (F-2), contrary to the implementation report's claim. D2 §6 grants full state to Platform Admin "according to the existing Admin authorization model" — which the Admin tab provides — so the customer-route denial may well be correct, but it should be confirmed (D1 §27: material product decisions must STOP and be reported). |
| PD-3 | Whether a consultant **team member** (any active firm member) may read the firm's full coverage payload without `can_manage_clients` | Verified behaviour (F-8); D2 §6 does not state the read capability rule |
| PD-4 | Whether the Admin operational tab should be **relabelled to "Operational Routing"** to match D2 §2/§8 exactly | F-6; D2 permits existing placement but names the tab explicitly |
| PD-5 | Whether **positive coverage states** need a dedicated demo-lab seeding fixture so future QA can browser-verify criteria 3-8/10 | F-5/NV-1-4 — a QA-infrastructure decision, not a product rule |
| PD-6 | Confirmation that the CT-MP-SUB-003 migrations (`20261010000000` P17A `consultant_profiles.organization_id`, `20261030000000` routing, `20261101000000` `consultant_mp_allocations`) are ratified for application where not yet applied | The demo-lab DB supports the coverage read, but migration-application approval remains a PO/ops gate for other environments |
| PD-7 | Carried forward from D1 §29: final public pricing, payment provider | Already recorded as OPEN by the authoritative spec; re-stated here so they are not lost |

---

## 21. Final verdict

### Summary of the determination

CT-MP-SUB-004 is a **technically sound, security-correct, well-tested and genuinely
working implementation** of the three Manual Processing coverage surfaces. Independently
verified and confirmed:

* all 4 routes are registered and dispatched at runtime (own `create_app()` probe + live
  401/200 evidence);
* **19/19** security and authorization negatives deny correctly, including cross-tenant
  read, cross-firm release, forged consultant id, ineligible client, capacity exhaustion,
  duplicate allocation and missing capability — with **no unexpected ALLOW**;
* the customer payload provably leaks **no** consultant commercial internals;
* commercial entitlement, FIN-06 governance and Processing Entity remain **three separate
  concepts**, exactly as the PO-approved commercial model requires;
* the F-05-R1 frozen register change is **architecturally correct** and does not weaken the
  contract;
* regression failures are **independently confirmed PRE-EXISTING/ENVIRONMENT**, in files
  CT-MP-SUB-004 did not touch;
* test results match the implementer's claims **exactly** (24 / 22 / 55 / 568-1 / 2-suite);
* browser acceptance **was performed** on all three surfaces with **zero page errors**;
* **no** scope expansion and **no** production, commit, push, deploy, schema, RLS or
  migration change.

It is nonetheless **NOT ready for PO acceptance**, because:

1. **F-1 (HIGH)** — the delivered UI/UX was implemented against
   `CT-UX-MP-SUB-003`, which is `PROPOSED FOR PO APPROVAL` and whose own §11 states
   **"UI implementation — NOT YET AUTHORIZED"**. Acceptance authority is therefore absent
   and **PD-1** must be resolved first.
2. **F-5 (MEDIUM)** — the positive coverage/capacity states and the allocate/release flows
   are **not browser-verified**, because the environment has no purchased coverage and
   seeding it would be an unauthorized mutation.
3. **F-3 (MEDIUM)** — part of the `ConsultantPage.jsx` diff lies outside the documented
   CT-MP-SUB-004 scope and is not attributable from the working tree.
4. **F-2, F-4 (LOW)** — two inaccurate claims in the implementation report.
5. **PD-2 … PD-6** — PO decisions confirmed outstanding.

Per the task's own rule — use **A** only if all material requirements are independently
satisfied *and* remaining issues are genuinely unrelated/non-blocking, and **B** if the
implementation is substantially correct but there are findings, unresolved verification
gaps, or PO decisions required — the applicable verdict is **B**.

**CT-MP-SUB-004 VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE**

No remediation was implemented as part of this verification.

---

*Report path: `docs/architecture/CT-MP-SUB-004-independent-verification-report.md`*
