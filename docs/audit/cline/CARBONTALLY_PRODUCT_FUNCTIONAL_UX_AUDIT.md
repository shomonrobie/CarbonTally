# CarbonTally — Product Functional & UX Audit

> **Type:** Read-only product functionality + UX discovery (no code changes)
> **Date:** 2026-09-01
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Environment tested:** local stack — FastAPI `http://localhost:8050` (uvicorn `main:app`, 621 routes,
> Supabase connected), frontend `http://localhost:3000` (CRA dev), Supabase `http://127.0.0.1:54425`
> (PostgREST/GoTrue/Storage/Realtime), local Postgres `127.0.0.1:54426`.
> **Evidence methods:** live API probes with demo personas, real Chromium (Playwright) browser
> session, Postgres inspection, storage object inspection, source tracing. No files modified
> except this report; no database/migration/RLS/package changes; no commits.
> **Severity:** P0 = security/data-loss/system failure · P1 = major workflow/product failure ·
> P2 = significant usability/functionality/architecture · P3 = minor defect/debt.

---

# 1. Executive summary

The V3 platform is **substantially functional at the API layer** — every persona (customer, staff,
consultant, PE) can authenticate and the major read surfaces return 200 with real data, and the
authorization boundaries (operator→review denied, PE→customer-org list denied) hold. The durable
automatic-processing worker runs and produced 20 completed jobs with 100 immutable calculation
snapshots historically.

However, **two headline problems from the prior real-browser inspection are confirmed or
characterised**, and one additional infrastructure finding surfaced:

1. **Document preview is BROKEN (P1) — root cause identified.** The signed URLs issued by
   `services/storage.py:storage_signed_url()` carry JWT scope `download`
   (`"scope":"download"` verified in the signed URL token). Chromium therefore **starts a
   download** instead of rendering the PDF in the `SecureDocumentViewer` iframe — the iframe loads
   an empty body. Fix is small and frontend/backend-scoped (request a render/inline signed URL +
   align the iframe sandbox). Document-preview API path itself works (signed URL returns 200 with
   real PDF bytes, correct `application/pdf` mimetypes in storage metadata).

2. **Automatic processing is PARTIALLY WORKING — gated at the extraction-quality threshold (P1).**
   The durable pipeline (enqueue → claim → extract → map → validate → calculate) runs, but the
   deterministic extraction stage (`services/automatic_extraction.extract_document`, not the
   LLM-based `AIExtractionEngine` which is only wired into the legacy workflow engine) produces
   completeness 0.00–0.33 for today's uploaded PDFs, below the 0.50 `AUTO_EXTRACT_CONFIDENCE_MIN`
   gate, so jobs are **correctly** routed to manual review. Two additional historical engine bugs
   are evidenced in blocked-job `last_error`:
   - `consumption unit 'm3' does not match factor unit 'cubic metres'` — a calculation path that
     bypasses unit-alias normalisation (`core/units.py` has `m3→cubic metres`);
   - `unknown calculation methodology 'customer_factor'` / `'keyword_search'` — non-enum
     methodology values reaching `CalculationMethodology` validation.

3. **Infrastructure blocker: the legacy `admin/` control-plane app is NOT running (P2).** Port 3001
   is occupied by the OpenHands agent-canvas static server, so `http://localhost:3001/admin/*`
   serves OpenHands, not `carbontally-admin`. The admin control plane (product requirement #3) is
   therefore unreachable in the current local environment, and its code bypasses FastAPI via direct
   Supabase calls (architecture mismatch, §19).

Additional verified facts: the org-profile layout issue reported at 100% zoom was **not reproduced**
in headless Chromium on this org/viewport set (1280–1920 px, 1024, 390, DPI-1) — recorded as
reported-but-not-reproduced with static-CSS risk factors (§13). Demo login credentials in
`.local-demo-credentials.md` (Aug 22) are **stale** relative to the provisioned users (Aug 28,
fallback password) — all demo personas authenticate with the documented fallback password, not the
creds-file value (§17). `customer_documents` is empty (0 rows) while storage holds 681 objects and
the processing queue holds 36 jobs — the V3 upload path writes `organization_files`, not
`customer_documents` (data-model divergence, §16/§19).

---

# 2. Product architecture vs intended architecture

| Product requirement | Intended | Current | Status |
|---|---|---|---|
| 1. Customer application | frontend customer workspace | `/home`, `/documents`, `/processing`, `/review`, `/emissions`, `/reports`, `/billing`, `/organization`, `/messaging`, `/existing-data` | WORKING at API+UI level |
| 2. CarbonTally internal staff | internal operations workspace | `/ops` (OperationsPage tabs; queues, workspaces, review, QC, staff/roles/entities/SLA) | WORKING |
| 3. CarbonTally Admin | dedicated `/admin` control-plane app/surface | **Legacy `admin/` app not running** (port 3001 = OpenHands); modern staff-admin tabs inside `/ops` work; org-settings "AdminPage" is customer-facing | **BROKEN (unreachable) / partially replaced** |
| 4. PE | PE-specific workspace + API boundary, not a customer | `/ops` PE Manager dashboard / EntityExtractionWorkspace; `/api/v3/ops/entities/*`; customer-org access denied (403 verified) | WORKING |
| 5. Consultant | consultant workspace, multi-client | `/consultant`, `/consultant/items/:clientId/:itemId`, 31 client endpoints | WORKING |
| 6. Consultant clients | no direct access; revocation by Owner/Admin/Manager; never deletes data | `consultant_clients` lifecycle (suspend/end/reactivate); revocation roles migration `20260831040000_consultant_revocation_roles` | WORKING (API-level verified; revocation not executed in audit) |
| 7. Customer/consultant processing separate from internal ops | separate pipelines | `/api/v3/processing/*` vs `/api/v3/ops/*` — separate, verified | WORKING (INTENTIONAL) |
| 8. Calculation snapshots API-only for consultants | no client-side calculation | snapshots immutable server-side; consultant read surface only | WORKING |
| 9. V3 canonical, legacy temporary | V3 canonical | both mounted in one FastAPI app; V3 is the live surface | INTENTIONAL transitional |
| 10. DataSecurity public | public page | `/data-security` loads | WORKING |
| 11. Preserve DB data | 7,049 emission factors intact | **verified 7,049 rows** in `emission_factors` | INTACT |
| 12. Do not break migrations/RLS | intact | migrations 41, RLS helpers present, demo seed intact (1,183 demo users) | INTACT |

**Verdict:** the V3 product architecture matches the intended design for customer/staff/PE/
consultant. The **admin control plane is the main mismatch**: the intended dedicated `/admin`
surface exists only as the legacy `admin/` app which is (a) not running locally, and (b)
architecturally divergent (direct Supabase access). PE/admin/customer separation is otherwise
correct and server-enforced.



---

# 3. Customer workflow results

Persona: `owner.demo0001@demo.carbontally.local` (org `bc197ccf-cd12-56dd-8773-3c4d7a16c69e`, "Quayside Energy").
Browser: real Chromium via Playwright. API: live probes.

| Step | Route / component | Frontend fn | HTTP endpoint | Result |
|---|---|---|---|---|
| Login | `/login` (Login.js) | `supabase.auth` | GoTrue password grant | ✅ 200, lands `/home` |
| Dashboard | `/home` DashboardPage | getMeContext, listMembers, emissions/reports | `/api/v3/me/context`, `/api/v3/reporting/customer-dashboard`, `/api/v3/emissions/dashboard` | ✅ 200 |
| Documents | `/documents` DocumentsPage (DataTable) | v3ListDocuments | `/api/v3/documents?organization_id=` | ✅ 200, 1 doc (`scan_heavy_elec.pdf`) |
| Processing list | `/processing` ProcessingPage | getProcessingStatus / getProcessingQueue | `/api/v3/processing/status`, `/queue?stage=` | ✅ 200 — 8 items (6 source, 2 extracted), 1 active batch |
| Processing workspace | `/processing/:itemId` ProcessingItemWorkspace (WorkbenchShell, 7 stages) | getProcessingItemWorkspace | `/api/v3/processing/items/{id}/workspace` | ✅ 200 (item + workflow + viewer_url) |
| Document preview (in workspace) | SecureDocumentViewer iframe | viewer_url → signed URL | storage `/object/sign/documents/...?token=` | ❌ **BROKEN** — iframe body empty; URL triggers download (`scope=download`) |
| Emissions | `/emissions` EmissionsPage (DataTable) | v3ListEmissions | `/api/v3/exports/emissions.json`, `/api/v3/emissions/dashboard` | ✅ 200 (0 rows for this org) |
| Reports | `/reports` ReportsPage (DataTable) | listReports | `/api/v3/reports?organization_id=` | ✅ 200 |
| Billing | `/billing` BillingPage | getMyBilling | `/api/v3/billing/me` | ✅ 200 |
| Review | `/review` ReviewPage | getCustomerReviewQueue | `/api/v3/processing/customer-review` | ✅ 200 (empty queue for this org) |
| Issues | `/issues` IssuesPage | getProcessingIssues | `/api/v3/issues?organization_id=` | ✅ 200 |
| Existing data | `/existing-data` | discovery | `/api/v3/discovery/*` | ✅ 200 |
| Messaging | `/messaging` MessagingPage | conversations | `/api/v3/messaging/*` + Realtime | ✅ API 200; Realtime readiness to be re-probed (§17) |

**Status: PARTIALLY WORKING.** Every surface renders and returns data except **document preview**
(broken — §11) and **end-to-end automatic processing** (gated — §10). No console errors on
`/home`, `/organization`, `/documents`, `/emissions`, `/reports`, `/billing`, `/review`,
`/processing`, `/processing/:itemId` during the browser session.

---

# 4. Individual organization workflow results

Persona: same customer owner; route `/organization` (AdminPage — org settings, not a control plane).

| Tab | Component | API | Result |
|---|---|---|---|
| Profile | ProfileTab | `/api/v3/organizations/{id}/profile` + `/metadata` | ✅ 200 |
| Members | MembersTab (raw table) | `/api/v3/organizations/{id}/members` | ✅ 200 |
| Facilities | FacilitiesTab (DataTable) | `/api/v3/organizations/{id}/facilities` | ✅ 200 |
| Locations | LocationsTab (DataTable) | facility CRUD | ✅ 200 |
| Assets | AssetsTab (DataTable) | `/api/v3/organizations/{id}/assets` | ✅ 200 |
| Suppliers | SuppliersTab (DataTable) | `/api/v3/suppliers?organization_id=` | ✅ 200 |
| Vehicles | VehiclesTab (DataTable) | `/api/v3/vehicles?organization_id=` | ✅ 200 |
| Custom factors | CustomFactorsTab (DataTable) | `/api/v3/customer-factors?organization_id=` | ✅ 200 |
| Activity | ActivityTab (DataTable) | audit/activity | ✅ 200 |

---

# 5. Consultant workflow results

Persona: `consultant.demo0001@demo.carbontally.local`.

| Step | Frontend fn | HTTP endpoint | Result |
|---|---|---|---|
| Login + landing | getMeContext | `/api/v3/me/context` | ✅ 200 → `destination=/consultant` |
| Profile | getConsultantProfile | `/api/v3/consultants/me` | ✅ 200 |
| Dashboard | getConsultantDashboard | `/api/v3/consultants/me/dashboard` | ✅ 200 (client_count, clients_by_status, pending_reviews, open_issues) |
| Client list | listConsultantClients | `/api/v3/consultants/me/clients` | ✅ 200 |
| Client context / dashboard | getClientWorkspaceContext / getClientDashboard | `/api/v3/consultants/clients/{id}/context|dashboard` | ✅ 200 (probe on client 0001.1) |
| Client documents | getClientDocuments | `/api/v3/consultants/clients/{id}/documents` | ✅ 200 |
| Processing items | getClientProcessingItems | `/api/v3/consultants/clients/{id}/processing/items` | ✅ 200 |
| Evidence | getClientEvidence | `/api/v3/consultants/clients/{id}/evidence` | ✅ 200 |
| Reports | getClientReports | `/api/v3/consultants/clients/{id}/reports` | ✅ 200 |
| Team | getConsultantTeam | `/api/v3/consultants/me/team` | ✅ 200 |
| Revocation | suspend/end/reactivate | `/api/v3/consultants/clients/{id}/suspend|end|reactivate` | NOT EXECUTED (state-changing; endpoints present, Owner/Admin/Manager-only per migration `20260831040000`) |

**Status: WORKING.** Consultant processing uses the V3 processing surface (not ops) — INTENTIONAL.
Revocation path is implemented server-side with role gating; not exercised to avoid mutating demo
relationship data (per audit safety rules).

---

# 6. PE workflow results

Persona: `pe-manager-1.demo@demo.carbontally.local` / `pe-staff-1.demo@…` (entity
`a25a0537-056c-561e-8a7b-21eb21703abc` = "Processing Entity Alpha Ltd").

| Step | HTTP endpoint | Result |
|---|---|---|
| Login + landing | `/api/v3/me/context` | ✅ 200 → `/ops` (PE branch in OperationsPage) |
| PE identity | `/api/v3/ops/me` | ✅ 200 (profile.entity_id = PE Alpha) |
| PE dashboard | `/api/v3/ops/entities/{entity}/dashboard` | ✅ 200 (entity + staff_count + staff) |
| Assigned batches | `/api/v3/ops/entities/{entity}/extraction/batches` | ✅ 200 (batch `b88ce621` for customer org — assigned to PE) |
| Next item | `/api/v3/ops/entities/{entity}/extraction/next-item?stage=` | ✅ 200 with stage param (422 without — API requires stage; matches frontend usage) |
| Item workspace / document viewer | `/api/v3/ops/items/{id}/workspace` → viewer_url | ⚠️ API works; **preview broken** by download-scope signed URL (§11) |
| PE → customer-org list | `/api/v3/ops/organizations` | ✅ **403 denied** ("CarbonTally internal staff access required") |
| PE → wrong entity | `/api/v3/ops/entities/999/dashboard` | ✅ **403 denied** |

**Status: WORKING at API level; PE isolation VERIFIED.** PE is not treated as a customer; the
no-download source-document boundary is server-side (SecureDocumentViewer `allowDownload=false`).
Document preview inherits the same §11 defect.

---

# 7. Internal staff workflow results

Personas: `operator.demo@…`, `reviewer.demo@…`, `system-admin.demo@…`.

| Step | HTTP endpoint | Operator | Reviewer | SysAdmin |
|---|---|---|---|---|
| Landing | `/api/v3/me/context` | ✅ `/ops` | ✅ `/ops` | ✅ `/ops` |
| Identity/permissions | `/api/v3/ops/me` | ✅ 200 | ✅ 200 | ✅ 200 |
| Ops dashboard | `/api/v3/ops/dashboard` | ✅ 200 | — | — |
| Operator queue | `/api/v3/ops/queues/operator?limit=3` | ✅ 200 | — | — |
| Review queue | `/api/v3/ops/queues/review?limit=3` | ✅ **403** (no can_review) | ✅ 200 | ✅ 200 |
| QC queue | `/api/v3/ops/queues/qc?limit=3` + `/api/v3/qc/queue` | — | ✅ 200 | ✅ 200 |
| Staff roles | `/api/v3/ops/staff-roles` | — | — | ✅ 200 |
| Commercial config | `/api/v3/commercial/config` | — | — | ✅ 200 |
| Work item workspace | `/api/v3/ops/items/{id}/workspace` | ✅ 200 | ✅ 200 | ✅ 200 |
| Extract/Map/Validate/Calculate/QC | `/api/v3/ops/items/{id}/start|extract|map|validate|calculate|qc` | endpoints present; not executed (state-changing) | | |

**Status: WORKING at API level; permission boundaries VERIFIED (operator denied review queue,
403).** The durable worker (`workers/automatic_processing.py`) is started from `main.py` startup
and is actively processing (jobs updated today 2026-09-01 12:14–12:46). Workflows to completion
(extract→map→validate→calculate) were not re-executed to avoid mutating demo work items; the
pipeline state machine is covered in §10 and its historical completions (20 approved jobs) are
recorded in the DB.

---

# 8. Admin workflow results

| Surface | Result |
|---|---|
| **Legacy admin app** (`admin/`, routes `/admin/*`, `/staff-dashboard`) | ❌ **NOT RUNNING / UNREACHABLE** — port 3001 serves OpenHands agent-canvas; `http://localhost:3001/admin/login` renders OpenHands (title=OpenHands, 0 inputs). The `carbontally-admin` CRA is not started. |
| Modern staff-admin inside `/ops` (CommercialTab, QcQueue, IssuesTriageTab, AuditConsoleTab, SettingsTab, StaffRoster, StaffRolesTab, SlaTab, ProcessingEntitiesTab) | ✅ API 200 for sysadmin (qc queue, staff roles, commercial config, ops dashboard); tabs render (permission-aware) |
| Org-settings AdminPage (`/organization`, customer-facing) | ✅ 200 (see §4) |

**Status: PARTIALLY WORKING / MISMATCH.** The dedicated admin control plane is not reachable in
the current environment (infrastructure blocker, §17) and its implementation bypasses FastAPI
(§19, architecture mismatch). The /ops staff-admin surfaces are functional.

---

# 9. Public website workflow results

Browser at 1280×800, all pages loaded with no horizontal overflow:

| Route | Title | Overflow | Notes |
|---|---|---|---|
| `/` (Landing) | CarbonTally — Carbon Data Processing… | none | ✅ |
| `/pricing` | Pricing — CarbonTally | none | ✅ |
| `/privacy` | Privacy Policy — CarbonTally | none | ✅ |
| `/data-security` | generic SPA title | none | ✅ loads (public per PO intent) |
| `/glossary` | Glossary — CarbonTally | none | ✅ |
| `/contact` | Contact — CarbonTally | none | ✅ |

One **React minified error (#418, HTML-related)** fired on a public page during the session —
P3, to be attributed on the exact page during remediation (§18).

**Status: WORKING** with one minor console error to attribute.


| Security | SecurityTab (raw table) | profile security fields | ✅ 200 |

**Layout at 100% zoom (browser):** at 1280×800 the profile form renders a 4-column
`269px` grid (`repeat(auto-fit, minmax(220px,1fr))`); 1024×768 → 3 columns; 390×844 → 1 column;
1920×1080 → 4 columns. **No horizontal overflow detected** at any of these sizes for this org.
The reported "text collapses to one-character-per-line at 100% zoom, usable at 60%" was **not
reproduced** in headless Chromium. Static risk factors remain (§13).

**Status: WORKING** (API + layout for tested org/viewports); reported overflow **UNVERIFIED**.

---

# 10. Automatic processing forensic trace

**Current DB state (Postgres, 2026-09-01):**

| Table | State |
|---|---|
| `emission_factors` | **7,049 rows** (intact — safety requirement met) |
| `document_processing_queue` | 36 jobs: **20 approved/completed** (created 2026-08-29), **13 manual_review/blocked**, **3 customer_review/review** |
| `calculation_snapshots` | **100 rows** (immutable) |
| `emissions_logs` | 100 rows |
| `customer_documents` | **0 rows** |
| storage `documents` bucket | **681 objects** |

**Full path trace (upload → … → review):**

```
UPLOAD      frontend v3UploadDocument → POST /api/v3/uploads
            → storage upload (documents bucket) + organization_files row (NOT customer_documents)
            → POST /api/v3/processing/documents/{file_id}/enqueue (v3_automatic_processing.py)
INGEST      document_processing_queue row created (status=pending, stage=enqueued, source_item_id set)
CLAIM       workers/automatic_processing.py loop — FOR UPDATE SKIP LOCKED over dpq_auto_claim_idx
EXTRACT     services/automatic_processing._extract → services/automatic_extraction.extract_document
            (deterministic pdfplumber/Tesseract; NOT the LLM AIExtractionEngine)
GATE        completeness = extracted-field coverage (domain/automatic_processing.completeness)
            completeness < 0.50 (AUTO_EXTRACT_CONFIDENCE_MIN) → mark_blocked(manual_review, reason=…)
MAP         factor matching (emission_factor / customer_factor precedence)
VALIDATE    engines/validation
CALCULATE   CalculationEngine → calculation_snapshots (immutable, content_hash, request_id) + emissions_logs
REVIEW      status customer_review → customer approval gate → approved/completed
```

**Where the real system stops (evidence):**

1. **Recent jobs (today) stop at the extraction-quality gate.** `manual_review_reason` =
   `"extraction completeness 0.33/0.00 below 0.50 threshold — unresolved: quantity/unit, supplier"`.
   The deterministic extractor cannot parse the synthetic test PDFs into structured lines →
   jobs are correctly routed to manual review. The **LLM/AI extraction engine
   (`engines/ai_extraction.py`, OpenRouter-based) is NOT wired into the durable pipeline** — it is
   referenced only by the legacy `engines/workflow.py`. → **ARCHITECTURE GAP / P1** (auto pipeline
   lacks the configured AI-extraction capability; without it, most real-world PDFs will block).

2. **Historical jobs (3 days old) show two engine bugs in `last_error`:**
   - `consumption unit 'm3' does not match factor unit 'cubic metres' for factor …` — a
     calculation path that reaches `domain/factor.py:99` / `engines/calculation.py:347` with the
     **raw** unit. `core/units.py` defines `m3→cubic metres`, and

---

# 11. Document preview forensic trace

```
UI        SecureDocumentViewer (iframe.ct-wb-viewer__frame, sandbox="allow-same-origin")
  ↓       src = workspace item's viewer_url (GET /api/v3/processing/items/{id}/workspace)
  ↓       backend returns item.file_url = storage_signed_url(path_from_url(item.file_url))
API       /api/v3/processing/items/{id}/workspace  →  200 {item:{file_url: "http://127.0.0.1:54425/storage/v1/object/sign/documents/uploads/…?token=…"}}
STORAGE   GET signed URL → 200, Content-Type application/octet-stream (workspace item) /
          application/pdf (documents endpoint file), 1,414,997-byte PDF verified
BROWSER   iframe loads the signed URL
```

**Verified failure in Chromium:** navigating the signed URL directly triggers
**`FATAL page.goto: Download is starting`** — Chromium treats the response as a download, not an
inline PDF. The workspace iframe content document body is **empty** (`innerText === ""`).
Root cause: the signed-URL JWT payload decoded shows **`"scope":"download"`**
(`eyJ…` token contains `"scope":"download"`). `services/storage.py:57-71`
`storage_signed_url()` calls `create_signed_url(path, expires)` with **no options**, so Supabase
issues a download-scoped URL. Additionally `SecureDocumentViewer.jsx` sets
`sandbox="allow-same-origin"` on the iframe, which further suppresses Chromium's inline PDF
viewer even for render-scoped URLs.

**Classification: BROKEN (P1).** API + storage are healthy; the defect is the signed-URL scope
option (+ iframe sandbox alignment). Fix candidates (smallest first):
1. backend `storage_signed_url` → request a non-download/render-scoped signed URL (e.g.
   `create_signed_url(path, expires, {"download": False})` or the equivalent option), preserving
   the short TTL and authz; regression-test both `application/pdf` and `application/octet-stream`.
2. align the iframe sandbox to allow inline PDF rendering (or render PDFs via
   `react-pdf`/pdf.js as the codebase already depends on `react-pdf`) while keeping the
   no-download UX.

---

# 12. UI/UX findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| U1 | **Document preview blank in workspace** (all roles) | iframe body empty; download-scope signed URL (§11) | P1 |
| U2 | **Auto-processing shows blocked jobs without clear "why"** — blocked jobs render in the queue with stage "blocked"; the manual-review reason is surfaced in the workspace, but the customer ProcessingPage shows no explanatory call-to-action for the 13 blocked jobs | ProcessingPage/queue data; `manual_review_reason` present server-side | P2 |
| U3 | Duplicated local loading/error helpers vs shared `StateViews` | `ConsultantPage.jsx:60-66` local `LoadingBlock`/`ErrorBlock`; `DashboardPage.jsx:28` local `StatCard` | P3 |
| U4 | Mixed button/form controls — `v3-btn` CSS utility (41 files) vs `ui/Button` (16 files) vs raw `<button>` (41 files) | inventory (§14) | P3 |
| U5 | Dead/parallel primitives: `Tabs` (0 consumers), `CheckboxField` (0), `PermissionState` (0), `Card`/`StatCard` (0) | inventory (§14) | P3 |
| U6 | Org admin tabs are hand-rolled tab bars (`AdminPage`), ops uses `v3-ops-tabs`; `ui/Tabs.jsx` unused | §14 | P3 |
| U7 | Legacy upload path (UploadManager/BulkUpload/PDFIngestionPortal) embedded in an **unrouted** legacy `Dashboard` function (`App.js:498`) — dead-path risk | App.js | P2 |
| U8 | One React minified console error (#418, HTML-related) on a public page | Playwright console capture | P3 |

---

# 13. Responsive-layout findings

- **Org profile (`/organization`):** 4-col grid at ≥1280 (269px tracks), 3-col at 1024, 1-col at
  390. No overflow measured in headless Chromium at 1280/1024/390/1366/1440/1536/1600/1680/1768/
  1856/1920 CSS px and DPI 1. The reported "one-character-per-line at 100% zoom, usable at 60%"
  was **NOT reproduced** for this org/page.
- **Risk factors identified statically** (candidates for the reported break on other orgs/
  browsers): `v3.css:202` and `admin.css:61` both define `.v3-form-grid` with **different**
  `minmax` floors (220px vs 280px) — duplicate definitions, order-dependent; `v3-meta-item` uses a
  fixed 190px label column + `word-break: break-word` (long unbroken values can squeeze); no
  `min-width: 0` on flex/grid children in several admin cards; tables are wrapped but raw tables
  in MembersTab/SecurityTab have no horizontal-scroll wrapper.
- **Recommendation (later):** reconcile the duplicate `.v3-form-grid` definitions; add
  `min-width: 0` + `overflow-wrap: anywhere` safeguards; wrap remaining raw tables. This is a
  reusable component-level fix (form-layout primitive), not a page-specific patch.

**Classification:** reported issue **UNVERIFIED/possibly environment- or content-specific**;
duplicate CSS definitions are a VERIFIED TECHNICAL DEBT (P3→P2 for the reconciliation).

     `services/automatic_processing.py` + `v3_operations.py` + `v3_processing_workflow.py` all call
     `resolve_unit_for_factor` — but at least one older/parallel path did not (job dated 3 days
     before the CL-3 fix or on an unnormalised line path). → P1/P2 (unit alias bypass on one path;
     affects m3/L kWh aliases).
   - `unknown calculation methodology 'customer_factor'` and `…'keyword_search'` — the matching
     stage emits `MatchResult.methodology = stage_name` (`keyword_search`) or `'customer_factor'`
     (`engines/factor_matching.py:128,187`), and `CalculationRequest.__post_init__` validates
     against `CalculationMethodology` enum. The durable service derives methodology safely
     (`_methodology_for`), but **client-supplied `payload.methodology`** on the manual/customer
     calculate endpoints (`v3_operations.py`, `v3_processing_workflow.py`,
     `v3_emissions.py`) can still carry an invalid value. → P2.

3. **Worker liveness:** worker starts in `main.py` startup; jobs updated 2026-09-01 12:14–12:46
   prove it processes; no stale locks (locked_at null on all sampled rows).

**Classification: PARTIALLY WORKING.** The durable pipeline, claim loop, gates and provenance
work; **end-to-end unattended success is blocked** by deterministic-extraction quality and the
two engine defects above.


---

# 14. Component-system audit (usage inventory)

Counts = page files importing the primitive (excluding `ui/` itself and tests).

| Primitive | Canonical impl | Consumers (files) | Competing impls | Verdict |
|---|---|---|---|---|
| Button | `ui/Button.jsx` | 16 | `v3-btn` CSS (41 files), raw `<button>` (41 files), admin react-buttons | Button should become canonical; `v3-btn` retained only for DataTable pagination styling |
| TextInput / SelectInput / TextArea | `ui/FormControls.jsx` | 5 / 4 / 1 | raw `<input>` (27 files), raw `<select>` (21 files) | Converge on FormControls |
| CheckboxField | `ui/FormControls.jsx` | **0** | raw checkboxes | Dead or under-adopted |
| Dialog / ConfirmationDialog | `ui/Dialog.jsx` | 5 / 5 | admin modals (own stack) | Canonical |
| Drawer | `ui/Drawer.jsx` | 1 (V3Layout tray) | — | Canonical |
| Tabs | `ui/Tabs.jsx` | **0** | hand-rolled tab bars (AdminPage, ops `v3-ops-tabs`) | Dead primitive — either adopt or remove |
| DataTable | `ui/DataTable.jsx` | 13 | `v3-ops-table` (11 files), raw `<table>` (22 files) | Canonical; converge queues |
| Pagination | DataTable built-in | 13 | hand-rolled bars (ReviewQueue/QcQueue) | Converge on DataTable |
| LoadingState | `ui/StateViews.jsx` | 15 | local `LoadingBlock` | Canonical |
| ErrorState | `ui/StateViews.jsx` | 22 | local `ErrorBlock`, inline banners | Canonical |
| EmptyState | `ui/StateViews.jsx` | 1 | inline empty markup | Under-adopted |
| PermissionState | `ui/StateViews.jsx` | **0** | inline 403 banners | Dead or under-adopted |
| StatusBadge | `ui/StatusBadge.jsx` | 7 | `v3-ops-badge`, inline spans | Canonical |
| Card / StatCard | `ui/Card.jsx` | **0** | local `StatCard` in DashboardPage; `v3-card` CSS | Dead — local StatCard duplicates it |
| Alert | `ui/Alert.jsx` | 9 | `v3-error`/`v3-note` | Canonical |

---

# 15. DataTable / pagination / search / sort audit

**Can DataTable become the universal foundation?** Yes for the features audited — it already
supports server pagination (`total/limit/offset` + `onPage`), client pagination (`clientPaginate`,
BL-2), client sort (`sortValue`) and server-controlled sort (`onSortChange`/`sortKey`/`sortDir`,
BL-4), row actions (via `col.render` + `onRowClick`), page-size options, honest totals, caption/
`scope`/`aria-sort` accessibility, and empty state. **Verified gaps to close before universal
adoption (P2/P3):**
- **Bulk actions**: not in DataTable (no checkbox column/selection state) — ops/admin tables that
  need bulk assign/reject must extend the component (row-selection prop) rather than fork.
- **Filters**: DataTable has no built-in filter bar — pages implement their own (acceptable; a
  shared `Toolbar` primitive would help).
- **Responsive**: raw tables and `v3-ops-table` rely on the page for wrapping; DataTable's
  `ct-table-wrap` scrolls horizontally — acceptable, but the ops queues should switch to it.
- **Large datasets**: server pagination is wired to the uniform `limit/offset/total` V3 contract;
  no evidence of unbounded client lists in V3 paths traced.

**Pagination/search/sort/filter evidence:** uniform server-side `limit/offset/total` across
ops/consultants/organizations/reports/processing; org-scoped server search (`/api/v3/search`);
dedicated indexes (`dpq_auto_claim_idx`, `dpq_org_created_idx`, `emissions_logs_org_start_date_idx`,
`notifications_unread_recipient_idx`). Two markup generations of pagination coexist (duplication,

---

# 16. Database / performance observations

| Check | Result |
|---|---|
| Factor integrity | `emission_factors` = **7,049** (unmodified) ✅ |
| Worker claim query | **Index Scan `dpq_auto_claim_idx`** (EXPLAIN ANALYZE) ✅ |
| Org listing paths | index-backed (`dpq_org_created_idx`, org composite indexes, v3m11 batch) ✅ |
| Review queue | Seq Scan on 2 rows — fine at current scale; add `(status, priority)` index only if the queue grows (P3/FUTURE) |
| Bounded queries | V3 queues/consultants/reports all `LIMIT/OFFSET` bounded ✅ |
| N+1 / unbounded | none demonstrated in traced V3 paths (repos use explicit SQL); legacy routes not exhaustively audited (FUTURE) |
| Data-model divergence | `customer_documents` empty; uploads write `organization_files` + storage; DPQ carries the evidence chain → document-state duality persists (P2) |
| Storage | 681 objects, correct mimetypes (`application/pdf`, `text/csv`, xlsx) ✅ |

| Icon | `ui/Icon.jsx` (react-icons/fi) | 8 | raw emoji/unicode | Canonical |

**Summary:** the shared primitive set is real and widely adopted (LoadingState 15, ErrorState 22,
DataTable 13, Button 16), but **five primitives are effectively dead** (Tabs, CheckboxField,
PermissionState, Card, StatCard) while pages hand-roll equivalents, and the ops/consultant/admin
surfaces still use parallel CSS-class systems. No role-specific justification exists for the
`v3-ops-table`/hand-rolled pagination variants (they duplicate DataTable's contract exactly) —
convergence is safe. The **admin app is a fully separate third system** (react-table,
react-hook-form, react-select, tailwind) — requires the §19 decision.

| U9 | `customer_documents` empty while storage/queue hold documents — the Documents page lists storage/organization_files, so users see docs, but the canonical document record is inconsistent with the DPQ evidence chain | DB + `/api/v3/documents` | P2 |

---

# 17. Infrastructure blockers

| # | Blocker | Evidence | Impact |
|---|---|---|---|
| I1 | **`admin/` app not running** — port 3001 occupied by OpenHands agent-canvas static server (`pid 29745`, `/admin/login` → title=OpenHands, 0 inputs) | process table + browser | Admin control plane unreachable (P2) |
| I2 | **Stale demo credentials file** — `.local-demo-credentials.md` (Aug 22) predates the seed (Aug 28); users provisioned with the seeder's fallback password; creds-file password fails for **all** personas | GoTrue 400 across 6 personas; fallback password succeeds | QA/agent friction, not product defect (P3) |
| I3 | **Realtime readiness** — `v3_health.py` documents that the local stack Realtime may not complete websocket handshakes (TenantNotFound local provisioning mismatch); not re-probed this session | `backend/api/v3_health.py` | Messaging/presence may be degraded locally (P2, env-specific) |
| I4 | Port 8000 is the OpenHands ingress (not CarbonTally) — frontend correctly configured to 8050; any doc/agent pointing at 8000 hits OpenHands | process table | Operational confusion (P3) |

---

# 18. Broken functionality inventory

| ID | Broken item | Classification | Severity | Fix layer |
|---|---|---|---|---|
| B1 | Document preview renders blank in workspace (all roles) | VERIFIED DEFECT (download-scope signed URL + iframe sandbox) | P1 | backend (signed-URL options) + frontend (sandbox/viewer) |
| B2 | Automatic processing blocked at extraction gate for uploaded PDFs | PARTIALLY WORKING / ARCHITECTURE GAP (LLM extraction not wired into durable pipeline; deterministic extractor completeness < 0.50) | P1 | backend (wire AI extraction / improve deterministic extractor) |
| B3 | Unit-alias mismatch on a calculation path (`m3` vs `cubic metres`) | VERIFIED DEFECT (historical blocked jobs) | P2 | backend (ensure every CalculationRequest path normalises units) |
| B4 | Invalid `methodology` reaching CalculationMethodology (`customer_factor`, `keyword_search`) | VERIFIED DEFECT (historical blocked jobs; client-supplied methodology on manual paths) | P2 | backend (validate/derive methodology server-side) |
| B5 | Legacy admin control plane unreachable | INFRASTRUCTURE BLOCKER | P2 | infra (run admin app on a free port) + arch decision |
| B6 | `customer_documents` empty vs storage/queue evidence chain | TECHNICAL DEBT / data-model divergence | P2 | database/backend (reconcile) |

---

# 19. Architecture mismatches

| # | Intended design | Current behaviour | Classification |
|---|---|---|---|
| M1 | Dedicated `/admin` control plane (admin app/surface) | `admin/` app exists but not running and **bypasses FastAPI** (`admin/src/services/reviewService.js` → `supabase.from('staff_profiles'/'manual_review_queue')` direct); modern admin duties split into `/ops` tabs | ARCHITECTURE GAP (P2) |
| M2 | Automatic pipeline should use the configured AI extraction capability | durable pipeline uses **deterministic** `extract_document`; LLM `AIExtractionEngine` wired only into legacy `engines/workflow.py` | ARCHITECTURE GAP (P1) |
| M3 | Canonical shared component system (D21) | 3 systems coexist (ui/ primitives, v3.css/ops.css utilities, admin stack); dead primitives; raw markup in 41 files | TECHNICAL DEBT (P3) |
| M4 | Uniform table foundation (DataTable) | 3 table approaches (DataTable 13, v3-ops-table 11, raw 22) | TECHNICAL DEBT (P3) |
| M5 | Single authoritative document record | uploads write `organization_files` + storage; `customer_documents` empty; evidence chain in DPQ | DATA-MODEL DIVERGENCE (P2) |
| M6 | Server-authoritative calculation | client-supplied `payload.methodology` accepted on manual/customer calculate endpoints (invalid values reach enum validation) | VERIFIED DEFECT (P2) |
| M7 | Preview must render, not download | signed URLs download-scoped | VERIFIED DEFECT (P1) |

All other requirements (customer/staff/PE/consultant separation, snapshots API-only, revocation
roles, V3 canonical, DataSecurity public, 7,049 factors, migrations/RLS) are satisfied — see §2.

---

# 20. Prioritized remediation plan

Ordering follows the constraint: **smallest safe fix first → reusable/component fix → shared
infrastructure fix → page-specific fix only when necessary**. No giant rewrite.

**Phase 1 — P1 functional blockers (backend, small):**
1. **Fix signed-URL scope** in `backend/services/storage.py:storage_signed_url` (request a
   render/inline signed URL; keep TTL + authz). Add a regression test asserting the signed URL
   token scope is NOT `download` and that `GET` renders inline (content-type) rather than
   Content-Disposition attachment.
2. **Align SecureDocumentViewer** with the render path (adjust `sandbox` to allow inline PDF
   rendering, or render via `react-pdf` which is already a dependency) while preserving the
   no-download affordance.
3. **Normalise units on every CalculationRequest path** (central helper at the engine boundary so
   no caller can bypass `resolve_unit_for_factor`).
4. **Derive/validate `methodology` server-side** — ignore client-supplied methodology on
   manual/customer calculate endpoints; map factor kind → methodology like `_methodology_for`.

**Phase 2 — P1 automatic-pipeline gap (backend, medium):**
5. Wire the configured AI extraction (`AIExtractionEngine` + LLM client) into the durable
   pipeline's extract stage (falling back to deterministic extraction), or raise
   deterministic-extractor quality; verify against the demo PDFs so a representative upload
   completes end-to-end (enqueue→…→calculation→review state).

**Phase 3 — P2 stability (reusable fixes):**
6. Reconcile the duplicated `.v3-form-grid` definitions and add `min-width:0` /
   `overflow-wrap:anywhere` safeguards to the shared form-layout CSS (fixes the reported
   responsive fragility class-wide).
7. Add bulk-selection + shared filter-toolbar capabilities to `DataTable` and migrate
   `v3-ops-table` queues (OperatorQueue/ReviewQueue/QcQueue/roster/PE dashboards) onto DataTable.
8. Reconcile document-state duality: define the authoritative document/evidence record
   (likely DPQ + organization_files) and align `customer_documents` usage or retire it.
9. Attribute + fix the public-page React console error (#418).

**Phase 4 — convergence (P3):**
10. Adopt or remove dead primitives (Tabs, CheckboxField, PermissionState, Card/StatCard — replace
    local `StatCard`/`LoadingBlock`/`ErrorBlock`), retire `v3-btn`-style parallel classes where
    `ui/Button` suffices, remove the unrouted legacy `Dashboard` upload path.

**Phase 5 — admin control plane (PO decision first):**
11. Decide the admin surface strategy (see D below), then run/rebuild it on the V3 API; free port
    3001 for the admin app in the local env.

| B7 | Duplicate `.v3-form-grid` definitions + no `min-width:0` safeguards | TECHNICAL DEBT (reported overflow unverified) | P2 | frontend (shared form-layout primitive) |
| B8 | React console error #418 on a public page | VERIFIED DEFECT (minor) | P3 | frontend |
| B9 | Dead primitives + parallel table/tab/pagination systems | TECHNICAL DEBT | P3 | frontend (convergence) |
| B10 | Legacy unrouted `Dashboard` with embedded upload path | TECHNICAL DEBT (dead-path risk) | P3 | frontend (remove or route) |

not contract divergence).

---

# A. MUST FIX BEFORE BETA

| ID | Item | Severity | Layer |
|---|---|---|---|
| B1/M7 | Document preview must render (signed-URL scope + viewer sandbox) | P1 | backend + frontend |
| B2/M2 | Automatic processing must complete end-to-end for a representative upload (wire AI extraction or raise deterministic extraction quality; verify enqueue→calculate→review) | P1 | backend |
| B3 | Unit-alias normalisation on every calculation path | P1 (calculation correctness) | backend |
| B4 | Methodology derived/validated server-side (no client-supplied enum bypass) | P1 (calculation correctness) | backend |
| B5/I1 | Admin control plane reachable (run `admin/` on a free port, or provide the V3-based admin surface) | P1 (product requirement #3) | infra + arch |

# B. SHOULD FIX BEFORE BETA

| ID | Item | Severity | Layer |
|---|---|---|---|
| B6 | Reconcile `customer_documents` / `organization_files` / DPQ document-state duality | P2 | backend/db |
| B7 | Responsive form-layout reconciliation (duplicate `.v3-form-grid`, min-width safeguards) | P2 | frontend |
| U2 | Blocked-job UX: surface the manual-review reason + next action on customer/ops queues | P2 | frontend |
| U7 | Remove/route the unrouted legacy `Dashboard` upload path | P2 | frontend |
| B8 | Public-page React console error #418 | P3 | frontend |
| U3/U4/U5 | Component convergence (dead primitives, `v3-btn`/raw controls) | P3 | frontend |
| M4 | Migrate ops queues to DataTable (+ bulk selection, shared filter toolbar) | P3 | frontend |

# C. CAN WAIT

- I2/I4 — credentials-file sync and port-8000 documentation (P3, operational)
- I3 — Realtime local-stack provisioning fix (env-specific; re-probe before messaging beta)
- Review-queue `(status, priority)` index (only if the queue grows)
- Legacy route/component retirement scheduling (already tracked as INTENTIONAL transitional debt)

# D. ARCHITECTURE DECISIONS REQUIRED

1. **Admin control plane strategy (PO)** — migrate `admin/` functionality into the main app on the
   V3 API + D21 primitives; rebuild it as a separate `/admin` surface on the V3 API; or keep it as
   a separate app but eliminate direct Supabase access (must flow through FastAPI authorization).
2. **AI extraction in the durable pipeline (PO/architecture)** — confirm the OpenRouter-based
   `AIExtractionEngine` should power automatic extraction (with deterministic fallback) before
   wiring it in; confirm cost/budget posture.
3. **Document evidence single source** — approve DPQ/`organization_files` as authoritative and
   retire/align `customer_documents`, or formalise the current dual state.
4. **Dead endpoint families** — confirm `/api/v3/admin/review-queue` (v3_review.py) and
   `/api/v3/qc/queue` vs `/api/v3/ops/queues/*` canonical owners (from the prior forensic report).
5. **DataTable universal adoption** — approve extending DataTable with bulk-selection/filter
   toolbar as the single operational table contract across roles.

# E. INFRASTRUCTURE BLOCKERS

- `admin/` CRA not running (port 3001 = OpenHands) — must be started on a free port to make the
  admin control plane reachable.
- Demo credentials file stale vs provisioned fallback password — update `.local-demo-credentials.md`
  or re-provision users so the documented credential works for all personas.
- Realtime websocket handshake on the local Supabase stack — re-probe `GET /api/v3/health/realtime`
  before beta messaging verification.

# F. EXACT NEXT IMPLEMENTATION PHASES

1. **F1 (P1 calculation + preview)** — storage signed-URL render scope; SecureDocumentViewer
   sandbox/viewer; engine-boundary unit normalisation; server-side methodology derivation;
   regression tests for each. Verify in-browser: workspace PDF renders; a manual calculate with
   `m3`/`L`/`kWh` aliases succeeds; invalid client methodology returns 4xx not a blocked job.
2. **F2 (P1 automatic processing)** — wire AI extraction into the durable extract stage (or
   improve deterministic extractor), then verify one representative upload reaches
   `customer_review` state with a snapshot + emissions row.
3. **F3 (P2 stability)** — form-layout primitive reconciliation; DataTable bulk/toolbar +
   ops-queue migration; document-record reconciliation; blocked-job UX copy.
4. **F4 (P3 convergence)** — dead-primitive adoption/removal; parallel-class retirement; legacy
   Dashboard removal.
5. **F5 (admin control plane)** — after PO decision D1: run/rebuild the admin surface on the V3
   API; free port 3001; verify Users/Organizations/Reviews/DefraFactors/WorkHub flows against
   FastAPI authorization.

**Each phase ships with regression tests (backend unit/integration + frontend component tests)
and an independent re-audit of the affected workflows before moving on.**

---

## Appendix — Quantitative data (this audit)

- Live probes: 6 personas × ~40 endpoints (≈ 60% 200, 403s where expected for denied scopes).
- Browser: 11 viewport widths + mobile for `/organization`; 9 customer routes; 6 public routes;
  1 workspace; iframe experiments (direct nav → download; sandboxed vs plain iframe).
- DB: 7,049 factors; 975 orgs; 1,183 demo users; 36 DPQ jobs (20 completed / 13 blocked / 3 review);
  100 snapshots; 100 emissions logs; 681 storage objects; 0 `customer_documents` rows.
- Component inventory: 19 primitives counted; 5 with zero consumers; 41 files with raw `<button>`;
  27 `<input>`; 21 `<select>`; 22 `<table>`; 13 DataTable consumers; 11 `v3-ops-table` files.
- Backend surface: 621 routes (499 OpenAPI paths: 220 V3 + 17 V2 + 262 legacy).

## Safety confirmation

No application files, database, migrations, RLS, packages, configuration, tests, Docker or
infrastructure were modified; no commits or pushes. The only file created is this report.
Read-only probes used existing demo data; no state-changing actions were executed (documented
instead); the 7,049 emission factors remain intact.

