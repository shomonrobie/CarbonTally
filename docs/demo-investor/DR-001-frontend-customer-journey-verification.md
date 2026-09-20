# DR-001 — Frontend / Customer-Journey Verification (READ-ONLY)

**Prompt ID:** `DR-001`
**Date/time:** 2026-09-21 (session local, UTC+06:00)
**Type:** VERIFICATION / FORENSICS REPORT — no implementation, no fixes, no data changes

Evidence labels: **[observed]** directly measured this session · **[code-traced]** read from source with file:line · **[runtime]** from a running process/API · **[browser]** observed in a browser render · **[inference]** reasoned conclusion · **[limitation]** known constraint. **No browser evidence exists in this report** (see §3).

---

## 1. Git baseline

| Item | Value |
|---|---|
| Branch | `p8-release-reconciled` **[observed]** |
| HEAD | `295495c9a590f081b3ed98e854ea84994c3ff747` **[observed]** |
| Working tree | **clean** (`git status --porcelain` empty) **[observed]** |
| Remote alignment | `github` (https://github.com/shomonrobie/CarbonTally.git) tip = `295495c9a590f081b3ed98e854ea84994c3ff747` → **aligned** **[observed]** |
| Other remote | `origin` → local mirror `/tmp/ct_step2` (not used for release pushes) **[observed]** |
| Recent commits | `295495c` fix(DEMO-T3-G1) provider vocabulary · `b0a98ac` chore(DEMO-T3-REM-001) corpus reconciliation · `aa73af6` fix(DEMO-T3-REM-001) GoTrue JWKS **[observed]** |

**Baseline confirmation:** the working tree was already clean and remote-aligned at `295495c…`, matching the expected baseline, so **no commit was created at baseline** (Part A.4). The only repository modification made by this task is this report.

## 2. Environment / runtime used

| Component | Status **[observed]** |
|---|---|
| Backend API | `uvicorn main:app --host 127.0.0.1 --port 8070`, PID **445734** (started 2026-09-21 00:26:59), `/api/v2/health` → **200** **[runtime]** |
| Lab gateway | `127.0.0.1:54430` (lab GoTrue/REST/storage) **[observed]** |
| Database | `carbontally_demo_local` (local Supabase stack) **[observed]** |
| Frontend runtime | **NOT RUNNING** — no `build/` or `dist/`; nothing listening on 5173/3000/4173/8080; no `vite`/`webpack`/`react-scripts` serve process; the only `nginx` processes belong to the Supabase/Kong stack **[observed]** |
| Frontend toolchain | Create React App (`react-scripts start/build/test`); deps include `@supabase/supabase-js`, `axios`, `@mui/material`, `react-router-dom`, `recharts`, `react-pdf`, `react-hot-toast`, `framer-motion` **[observed]** |
| Browser automation | none available in this environment **[limitation]** |

### 2.1 Concrete configuration finding (not fixed)

| Fact | Value |
|---|---|
| `frontend/.env.local` | `REACT_APP_API_URL=http://localhost:8060` **[observed]** |
| Running backend | `http://127.0.0.1:8070` **[observed]** |
| Code default | `const API_URL = process.env.REACT_APP_API_URL \|\| 'http://localhost:8000'` (`frontend/src/v3/api.js:7`; same default in `services/apiClient.js:25`, `DocumentStatus.jsx:8`, hooks) **[code-traced]** |
| Listener on 8060 | **nothing** (`ss -ltnp` shows no 8060; the only `:8000` listener is the unrelated OpenHands agent-canvas ingress `node` process) **[observed]** |

**Observation:** the configured frontend API base (`8060`) does not match the backend actually serving CarbonTally (`8070`), so a browser run with the current `.env.local` would target a port with no CarbonTally listener. Reported as fact; **not modified** (out of scope).

## 3. Methodology

1. Git baseline (§1).
2. Runtime and browser-availability determination (§2) — no frontend server/build and no browser tooling were available, so **no browser verification was performed** and none is claimed.
3. Frontend source inspection: route table, guards, V3 page inventory, API client wiring, mock-data usage.
4. Backend/API contract inspection against the **live** OpenAPI document from the running backend: **575 paths / 683 operations** **[runtime]**.
5. Read-only database inspection (counts and existing records only; no writes).
6. Cross-check against previously established task evidence (G-1, N1/N4, R-A) and this session's read-only Demo/Investor assessment.

**PART D outcome — browser verification: NOT AVAILABLE.** Every UI statement in this report is **code-traced**, never browser-verified.

## 4. Frontend route inventory (50 routes, `frontend/src/App.js`) **[code-traced]** (`App.js:1958–2210`)

* **Public / marketing:** `/` (`LandingPage`), `/platform`, `/services`, `/processing-services`, `/consultants`, `/pricing`, `/contact`, `/faq`, `/about`, `/glossary`, `/carbon-reduction-plan`; legal `/privacy`, `/cookies`, `/terms`, `/data-security`.
* **Authentication:** `/login` (`Login`), `/signup` (`SelfServiceSignup`), `/beta/signup`, `/beta-login`, `/auth/callback` (`AuthCallback`), `/auth/magic` (`MagicLink`).
* **Authenticated application** (each wrapped `ProtectedRoute` → `RoleRoute requireOrg` → `V3Layout` → page): `/onboarding` (`OnboardingPage`), `/home` (`DashboardPage`), `/emissions` (`EmissionsPage`), `/documents` (`DocumentsPage`), `/processing` (`ProcessingPage`), `/processing/:itemId` (`ProcessingItemPage`), `/review` (`ReviewPage`), `/review/:itemId` (`ReviewDetailPage`), `/existing-data`, `/messaging`, `/issues`, `/notifications`, `/reports` (`ReportsPage`), `/reports/:id` (`ReportDetailPage`), `/billing` (`BillingPage`), `/organization`, `/consultant` (`ConsultantPage`), `/consultant/items/:clientId/:itemId`, `/ops` (`OperationsPage`), `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId`, `/pe` (`PeWorkItemsPage`), `/pe/assignments`, `/pe/messages`, `/pe/items/:entityId/:itemId`; `/dashboard/*` redirects to `/home`.

**Verified structure [code-traced]:** `ProtectedRoute` at `App.js:189` gates on the Supabase session; `src/v3/components/RoleRoute.jsx` provides the role/org gate; V3 page imports at `App.js:51–76`. Delivery is component-name based, so a route's existence is **not** evidence that the flow works.

## 5. UI → API → backend trace **[code-traced]**

Client layers: `frontend/src/v3/api.js` (`API_URL` at `:7`, `v3Fetch` at `:35` — the V3 surface's single HTTP funnel) and `frontend/src/services/apiClient.js` (`getApiUrl`, `getToken` from the Supabase session, `apiRequest` for legacy surfaces). No mock/static responses were found in these clients.

| Frontend surface | Client function / file | API endpoint(s) invoked | Backend router |
|---|---|---|---|
| Reports list | `v3/api.js` → `/api/v3/reports?…` | `GET /api/v3/reports`, `/reports/types` | `api/v3_reports.py` (23 paths) |
| Report detail / content / versions | `v3/api.js` | `GET /api/v3/reports/{id}`, `/content`, `/versions` | `api/v3_reports.py` |
| Report lifecycle actions | `v3/api.js` | version `submit` / `approve` / `reject` / `request-changes` / `finalize` | `api/v3_reports.py` |
| Report download | `v3/api.js` | `GET /api/v3/reports/{id}/download` | `api/v3_reports.py` (PDF/frozen-artefact/signed-url also exist server-side) |
| Consultant workspace | `v3/api.js` | `/api/v3/consultants/me`, `/me/dashboard`, `/me/clients`, `/me/team`, `/me/tasks`, `/me/branding` | `api/v3_consultants.py` (31 paths) |
| Consultant client context | `v3/api.js` | `/api/v3/consultants/clients/{id}`, `/context`, `/documents`, `/processing/items`, `/processing/status`, `/evidence`, `/issues`, `/reports`, `/dashboard` | `api/v3_consultants.py` |
| Ops review queue + actions | `v3/api.js` | `GET /api/v3/ops/queues/review`, `POST /api/v3/ops/review/{id}/assign`, `/complete` | `api/v3_operations.py` (58 paths) |
| QC item review | `v3/api.js` | `POST /api/v3/qc/items/{itemId}/review` | `api/v3_qc.py` |
| Workbench / processing item | `v3/api.js` | `GET /api/v3/processing/items/{itemId}/workspace`, `POST …/consultant-review`, `…/consultant-submit` | `api/v3_processing_workflow.py` |
| Processing entities | `v3/api.js` | `/api/v3/processing-entities` (requires admin) | `api/v3_processing.py` |
| Emissions (authoritative calculation) | `v3/api.js` (comment `:51`) | `/api/v3/emissions/*` | `api/v3_emissions.py` (9 paths) |
| Workbench UI shell | `v3/components/workbench/*` (`WorkbenchShell`, `SplitPane`, `SecureDocumentViewer`, `StructuredDataPreview`, `WorkflowNav`, `ConfidenceBadge`, `AutosaveIndicator`) | render-only components | — |
| Evidence surfaces | `v3/components/EvidenceTrail.jsx`, `EvidenceRecordPanel.jsx` | render-only (data via page-level calls) | evidence endpoints exist server-side |
| Customer pages | `v3/customer/*` (`DashboardPage`, `DocumentsPage`, `ProcessingPage`, `ProcessingItemPage`, `ProcessingItemWorkspace`, `ReviewPage`, `ReviewDetailPage`, `EmissionsPage`, `IssuesPage`, `MessagingPage`, `ExistingDataDiscoveryPage`, `BillingPage`) | page-level calls through `v3Fetch` | respective routers |
| Design system / states | `v3/components/ui/*` (`Button`, `DataTable`, `Dialog`, `Drawer`, `StatusBadge`, `StateViews`, `Tabs` …) | n/a | n/a |
| Public "try it" widgets using **mock data** | `components/CarbonTallyDemo.jsx` (`MOCK_CSV_DATA`, `:243–244`, `:678`), `components/FileUploadHero.jsx` (`MOCK_FILES`, `:145–146`, `:170`) | **no backend call for the data** | — |

### 5.1 Journeys not located in the frontend during this pass **[limitation]**

* **Document upload call site:** a `grep` for `/api/v3/uploads` across `frontend/src/v3` and `frontend/src/components` returned **no match**; the upload wiring (`UploadManager.js`, `BulkUpload.jsx`, `PDFIngestionPortal.jsx`, customer `DocumentsPage`) was therefore **not** traced to a concrete endpoint in this pass → **NOT VERIFIED** (endpoint exists server-side: `POST /api/v3/uploads`, 201, exercised by Demo-Lab tooling).
* **Correction/confirm call site:** the human-gate endpoint `POST /api/v3/processing/jobs/{id}/confirm` (used successfully by Demo-Lab tooling, R-A) was not located in the frontend in this pass → **NOT VERIFIED** (UI wiring unproven; the endpoint itself is verified server-side).
* **Customer review/approval call site:** `POST /api/v3/processing/jobs/{id}/review` was not located in the frontend in this pass → **NOT VERIFIED** (and approval is not authorized for execution).

## 6. Area-by-area status **[code-traced unless stated]**

| # | Area | Implementation found | Verification status | Notes (facts only) |
|---|---|---|---|---|
| 1 | Marketing / landing | `LandingPage` + 10 public pages + assistant/chat widgets, `CookieBanner` | **IMPLEMENTED — NOT VERIFIED** | two public widgets render **mock data** (`CarbonTallyDemo`, `FileUploadHero`) |
| 2 | Authentication | `Login`, `SelfServiceSignup`, `BetaLogin/BetaSignup`, `AuthCallback`, `MagicLink`; Supabase session; `getToken()` from session | **PARTIALLY VERIFIED** (backend token/session mechanics verified via tooling; UI not run) | logout/error-state behaviour not exercised |
| 3 | Organization / onboarding | `/onboarding` (`OnboardingPage`/`OnboardingWizard`), `/organization`, `CompanyNamePrompt`; `RoleRoute requireOrg`; org/member APIs (25 + 9 paths) | **IMPLEMENTED — NOT VERIFIED** | lab hosts 4 orgs / 8 members |
| 4 | Dashboard | `/home` → `DashboardPage` | **IMPLEMENTED — NOT VERIFIED** | — |
| 5 | Documents | `/documents` → `DocumentsPage`; `UploadManager`, `BulkUpload`, `PDFIngestionPortal` (legacy) | **IMPLEMENTED — NOT VERIFIED** | upload endpoint wiring not located this pass (§5.1) |
| 6 | Processing status | `/processing`, `/processing/:itemId`, `ProcessingItemPage`/`ProcessingItemWorkspace`, workbench shell | **IMPLEMENTED — NOT VERIFIED** | `GET /api/v3/processing/items/{id}/workspace` is called by `v3/api.js` |
| 7 | Extraction result / correction | workbench `StructuredDataPreview`, `SecureDocumentViewer`; `ManualEntryStandalone`, `useManualEntry` | **PARTIALLY VERIFIED** | correction **is** verified server-side (R-A confirm gate); UI call site not located |
| 8 | Factor matching / calculation display | `EmissionsPage` + `/api/v3/emissions/*` client calls | **PARTIALLY VERIFIED** | calculation verified server-side (snapshot `af640887…`, 2,469.16978 kg CO₂e); UI display not exercised |
| 9 | Provenance / audit UI | `EvidenceTrail.jsx`, `EvidenceRecordPanel.jsx`, admin `AuditTab`/`ActivityTab` | **IMPLEMENTED — NOT VERIFIED** | audit data exists (99 rows); `evidence_line_items = 0` |
| 10 | Reports | `/reports`, `/reports/:id`, `ReportsPage`, `ReportDetailPage`; lifecycle client calls | **IMPLEMENTED — NOT VERIFIED** | server: 23 report paths; lab: `report_versions = 1`, `report_version_artifacts = 0`; no T3-attributable artefact |
| 11 | Export / download | report `download` in `v3/api.js`; server `/api/v3/exports/{emissions.csv, emissions.json, documents.csv, audit-package.json}`; legacy `exports.router` | **IMPLEMENTED — NOT VERIFIED** | not executed |
| 12 | Billing / subscription | `/billing` → `BillingPage`; server `/api/v3/billing` (10) + `/api/v3/commercial` (20) | **IMPLEMENTED — NOT VERIFIED** | `billing_plans = 48`; `customer_subscriptions = 0`, `billing_orders = 0`, `usage_tracking = 0`; no provider contacted |
| 13 | Consultant / client | `/consultant`(+item), `ConsultantPage`, `NewCustomerView`, `TeamTab`, `WhiteLabelTab`, `ClientMessagingTab`; client-scoped calls | **PARTIALLY VERIFIED** | consultant API actions verified server-side (T3 upload/retry); UI isolation behaviour not exercised |
| 14 | Error / manual-review states | `ui/StateViews.jsx`, `v3/components/StateViews.jsx`, `StatusBadge`, `statusConfig.js`; clients throw to render controlled error/retry states (`v3/api.js:108`, `:138`) | **IMPLEMENTED — NOT VERIFIED** | blocked/manual-review states exist server-side (12 of 14 jobs) |

## 7. Demo / Investor readiness matrix

| Capability | Status | Evidence | Browser verified? | Backend verified? | Demo-ready? | Blocker / limitation |
|---|---|---|---|---|---|---|
| Landing | IMPLEMENTED — NOT VERIFIED | `App.js:1959`, `LandingPage.jsx` | No | n/a | Unknown | frontend not running; API base mismatch |
| Auth | PARTIALLY VERIFIED | `Login.js`, `supabaseClient.js`; lab token grants | No | Yes (lab password/token path) | Unknown | UI unverified |
| Onboarding | IMPLEMENTED — NOT VERIFIED | `/onboarding`, `OnboardingWizard.jsx` | No | Yes (`/api/v3/organizations` 17 paths) | Unknown | UI unverified |
| Dashboard | IMPLEMENTED — NOT VERIFIED | `/home` → `DashboardPage` | No | Yes (`/api/v3/reporting` 8 paths) | Unknown | UI unverified |
| Upload | IMPLEMENTED — NOT VERIFIED | `DocumentsPage`, `UploadManager.js`; server `POST /api/v3/uploads` | No | Yes (T3 uploads returned 201) | Unknown | UI call site not located |
| Processing | IMPLEMENTED — NOT VERIFIED | `/processing`, workbench components | No | Yes (14 jobs, stage machine) | Unknown | UI unverified |
| Extraction | PARTIALLY VERIFIED | `extracted_data` in DB; workbench preview components | No | Yes (values match ground truth) | Unknown | header `supplier` not auto-extracted |
| Manual correction | PARTIALLY VERIFIED | server confirm gate (R-A); `useManualEntry`, `ManualEntryStandalone` | No | Yes (item `calculated`, audit rows) | Unknown | UI wiring not located |
| Factor matching | VERIFIED (API) / NOT VERIFIED (UI) | `mapped_data`, `factor_match:*` audit rows, G-1 evidence | No | Yes | Partly | 7 scenarios block at mapping; `uk-water` NO_MATCH |
| Calculation | VERIFIED (API) / NOT VERIFIED (UI) | snapshot `af640887…`, emissions log `eb88e764…` | No | Yes | Partly | one journey only |
| Emissions result | PARTIALLY VERIFIED | snapshot + `/api/v3/emissions` paths | No | Yes (snapshot values) | Unknown | no verified aggregate UI |
| Provenance | PARTIALLY VERIFIED | snapshot provenance + audit; `evidence_line_items = 0` | No | Yes (snapshot/audit) | Partly | evidence layer unexercised |
| Review | PARTIALLY VERIFIED | job at `review`/`customer_review`, `review_ready_at` set | No | Yes (state only) | Partly | review action not performed |
| Approval | IMPLEMENTED — NOT VERIFIED | `POST /jobs/{id}/review`; `customer_approved = false` | No | No (not performed) | Unknown | approval not authorized |
| Reports | IMPLEMENTED — NOT VERIFIED | 23 endpoints; `report_versions = 1`, `report_version_artifacts = 0` | No | Partly (rows exist, unattributed) | Unknown | no T3 report artefact |
| Exports | IMPLEMENTED — NOT VERIFIED | `/api/v3/exports/*` (4 endpoints) | No | No | Unknown | not exercised |
| Billing | IMPLEMENTED — NOT VERIFIED | `/api/v3/billing` + `/commercial`; 48 plans; 0 subscriptions/orders/usage | No | No | Unknown | no execution evidence |
| Consultant | PARTIALLY VERIFIED | `ConsultantPage` + client-scoped calls; consultant API used by T3 | No | Partly | Unknown | UI unverified |
| Client | PARTIALLY VERIFIED | client orgs + consultant-scoped routes | No | Partly (client-context jobs) | Unknown | isolation UI unverified |
| Error / manual-review states | IMPLEMENTED — NOT VERIFIED | `StateViews`, `StatusBadge`, `statusConfig.js` | No | Partly (blocked reasons persisted) | Unknown | UI unverified |

## 8. Concrete blockers

1. **No frontend runtime available for this task** — no build/dist, no dev-server process, no frontend port listening, no browser tooling in this environment **[observed]**. UI statements in this report are code-traced; **browser verification is absent, not merely incomplete**.
2. **API base mismatch** — `frontend/.env.local` sets `REACT_APP_API_URL=http://localhost:8060`; the running CarbonTally backend is `:8070`; the code default is `:8000`; nothing listens on 8060 **[observed]**. A UI demo with the current configuration would not reach the backend. **Not modified** (out of scope).
3. **Upload UI wiring not located** — no `/api/v3/uploads` reference found under `src/v3` or `src/components` in this pass **[code-traced absence within that scope]**, so the UI→upload path is unproven even though the endpoint is verified server-side.
4. **Correction / approval UI wiring not located** — the confirm and customer-review job endpoints (available/verified server-side) were not located in the frontend in this pass.
5. **Only one calculating journey exists in the Demo Lab** — `calculation_snapshots = 1`, `emissions_logs = 1` **[observed]**; seven T3 scenarios remain blocked at mapping/clarification/no_match.
6. **Evidence/disclosure layer unexercised** — `evidence_line_items = 0`, `disclosure_value_evidence = 0` **[observed]**.
7. **No report artefact attributable to the demo journey** — `report_version_artifacts = 0`; one `report_versions` row exists but was not attributed in this pass **[observed + limitation]**.
8. **Billing/subscription never executed in this environment** — 48 plans defined, 0 subscription/order/usage rows **[observed]**.
9. **Public demo widgets use mock data** — `CarbonTallyDemo.jsx` (`MOCK_CSV_DATA`) and `FileUploadHero.jsx` (`MOCK_FILES`) render static data with no backend call **[code-traced]** — relevant if mistakable for live processing.
10. **Customer approval not performed** — `customer_approved = false`; approval execution is not authorized **[observed]**.

## 9. Known limitations

* **Browser-verification gap (overall):** no UI flow here was browser-verified; frontend behaviour is unproven (neither proven nor disproven).
* **Route ≠ behaviour:** 50 routes and the component inventory prove structure only.
* **Extraction fidelity:** header `supplier` is not automatically populated for the pinned PDFs; gas multi-line fidelity (ground truth 3 line items vs 1 mapped).
* **Mapping coverage:** 7 of 10 T3 scenarios produce no confident factor; `uk-water` NO_MATCH with factors present (cause not established).
* **Evidence/reporting:** evidence-line-item and disclosure-evidence records unpopulated; report artefact chain unexercised.
* **Billing:** implemented endpoints/tables with zero execution evidence; no provider contacted or verified.
* **Traceability:** OHD artefacts for G-1 and R-A are not in the repository (`docs/verification/` holds only `OHD_TASK_079_…`); those verdicts are recorded from the PO.
* **Search-scope limitation:** the upload/confirm/review call-site searches covered `frontend/src/v3` and `frontend/src/components`; a call site elsewhere in `frontend/src` (legacy root components) was not exhaustively re-searched — a **search-scope limitation**, not evidence of absence.

## 10. Items requiring PO decision

1. Whether to make a frontend runtime available for a browser-verified follow-up pass, and who authorizes bringing the app up (DR-001 does not authorize a service start/restart).
2. Whether to correct the frontend API base configuration (`8060` → the actual backend) — a configuration change requiring authorization.
3. Whether the mock-data public widgets may be used in a demo, presented as clearly illustrative, or withdrawn from the demo path.
4. Whether approval, report generation, export and billing walkthroughs are to be authorized as bounded execution tasks (each would create Demo Lab records).
5. Whether the Demo Lab should be extended to additional calculating scenarios before an investor session.

## 11. Items explicitly NOT authorized (unchanged by this report)

Application/frontend/backend code changes; database/schema changes; factor or manifest changes; synthetic-generator changes; Demo Lab reset or broad reseeding; new synthetic corpus; security/RLS/storage-policy changes; subscription/billing changes or provider contact; customer approval; production deployment; Phase 9; OCR hardening; IE/SEAI synthetic coverage.

## 12. Evidence references

* **Repository (frontend):** `frontend/src/App.js` (routes `1958–2210`; `ProtectedRoute` `:189`; V3 imports `51–76`), `frontend/src/v3/api.js` (`API_URL` `:7`, `v3Fetch` `:35`, endpoint calls §5), `frontend/src/services/apiClient.js` (`:25–50`), `frontend/src/v3/components/**` (workbench, evidence, ui), `frontend/src/v3/customer/**`, `frontend/src/components/CarbonTallyDemo.jsx` (`:243–244`, `:678`), `frontend/src/components/FileUploadHero.jsx` (`:145–146`, `:170`), `frontend/.env.local`.
* **Backend:** live `GET /openapi.json` from `127.0.0.1:8070` (575 paths / 683 operations); routers and modules listed in §5.
* **Database (`carbontally_demo_local`, read-only):** organizations 4, organization_members 8, organization_files 14, manual_extraction_items 14, document_processing_queue 14, calculation_snapshots 1, emissions_logs 1, evidence_line_items 0, emission_factors 7,049, import_batches 2, storage.objects 15, audit_trail 99, customer_factors 0, billing_plans 48, customer_subscriptions 0, billing_orders 0, usage_tracking 0, report_versions 1, report_version_artifacts 0, disclosure_value_evidence 0; R-A snapshot `af640887-5818-47ad-b351-1505ac049c32`, emissions log `eb88e764-b93a-4bd6-8b66-a24fd6e45ca9`, 2,469.16978 kg CO₂e.
* **Runtime:** backend PID 445734 (started 2026-09-21 00:26:59), `/api/v2/health` → 200; lab gateway `127.0.0.1:54430`.
* **Prior reports in-repo:** `docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md`; `docs/architecture/CARBONTALLY_DEMO_T3_IMPLEMENTATION_20260920.md`, `…_REMEDIATION_20260920.md`, `…_REM_001_IMPLEMENTATION_20260920.md`.
* **Transient diagnostics (outside the repository):** `/tmp/e1.txt`–`/tmp/e7.txt`, `/tmp/openapi.json`.

## 13. Final bounded verdict

> **FRONTEND / CUSTOMER JOURNEY — CODE-TRACED IMPLEMENTED, NOT VERIFIED (no browser evidence).**

The frontend contains a coherent V3 application — 50 routes, protected org-role-gated page components for dashboard, documents, processing, workbench, review, emissions, issues, reports, billing, consultant and ops/PE workspaces — funnelling HTTP through a single V3 client (`v3Fetch`) to the real backend (575 paths / 683 operations), with a design-system and state/error components. **No part of the browser-rendered journey was verified in DR-001**, because no frontend runtime, build or browser tooling was available, and the configured API base (`:8060`) does not match the running backend (`:8070`). Server-side, the deepest verified journey remains R-A: upload → extraction → human correction → matching (`b9d1ed06…`, confidence 1.0) → validation passed → calculation snapshot `af640887…` (2,469.16978 kg CO₂e) → emissions log → `customer_review` (unapproved). Evidence-line-item/disclosure records, report artefacts, billing execution and approval remain unexercised. This report asserts nothing beyond the evidence above.





