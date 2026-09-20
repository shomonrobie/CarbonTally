# DR-005 — Remaining Investor Workflow Browser Verification

- **Prompt ID:** `DR-005`
- **Date/time:** 2026-09-20–21, ~22:15–23:5x UTC (local session)
- **Nature:** strictly read-only verification. No feature implemented, no fix applied, no data changed, nothing approved.

Evidence labels: `BROWSER-VERIFIED` · `RUNTIME-OBSERVED` · `DATABASE-OBSERVED` · `CODE-TRACED` · `INFERENCE` · `LIMITATION`.

---

## 1. Git baseline

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `0c6d4dc18eb162165f2cf292dfe0837587e963ac` (== DR-004, as required) |
| Working tree | clean (`git status --porcelain` empty) |
| Remote divergence | `0 0` vs `github/p8-release-reconciled` |

## 2. Browser environment

| Item | Value |
| --- | --- |
| Frontend | `http://localhost:3000` → 200 |
| Demo Lab backend | `http://127.0.0.1:8070` → 200 (`/health`) |
| Gateway | `http://127.0.0.1:54430` → 200 (`/rest/v1/`) |
| Browser | `/usr/bin/google-chrome` headless `--headless=new`, 1440×900 |
| Harness | unchanged read-only CDP harness (`/tmp/dr005b.js`, Node 22 global `WebSocket`); **no tooling added to the repository**; Demo Lab configuration untouched |
| Identities | `org_a_owner` (customer), `consultant_owner` (consultant), `client_a_owner` (client) — all existing Demo Lab identities, each authenticated through the real `/login` form (no session seeding) |
| Evidence | `/tmp/dr005b.log`, screenshots `/tmp/dr005_shots/{a_exception,b1_reports,b2_report_detail,c1_consultant,c2_consultant_client,d_client_home}.png`; server-side read-only artifact fetches `/tmp/export.csv`, `/tmp/artifact.bin`, `/tmp/artifact2.bin` |

## 3. Exception workspace verification (Part C)

`BROWSER-VERIFIED` — opened through the normal UI (processing queue → row click):

| Item | Finding |
| --- | --- |
| Scenario | `t3imp_uk-water__ORG_030_thames_water_202605.pdf` |
| Route | `/processing/d0e979a0-c5cf-47fc-9bc3-7ec3259059ea` (`ProcessingItemWorkspace`) |
| Ids | item `d0e979a0-c5cf-47fc-9bc3-7ec3259059ea`; document `0acbea6e-90e9-426f-9418-db5a7a761b51`; extraction batch `3e6d33af-47ca-44d5-a9b0-091b176cefd4` |
| State | `EXTRACTED`, sub-state **`MANUAL_REVIEW`** |
| Exact blocking reason | **"Manual review · attempt 0/3 · mapping could not auto-resolve: line 1: no confident factor for 'Water' litres (status=no_match, confidence=0.00)"** |
| Explanation shown | Nothing was discarded; Extraction panel: *"Confirm or correct the fields extracted from the source document. OCR suggestions are pre-filled for review."*; Calculation panel: *"No calculation yet. The server computes the result from the extracted quantity and mapped factor - the client never supplies it."*; Emissions & evidence: *"No emissions have been calculated from this document yet."* |
| Extraction shown | JSON `extracted_data`: `{"date":"Mar 02, 2025","unit":"L","activity":"Water","quantity":67,"invoice_number":"INV2025008630"}`; `mapped_data {}`, `emission_factor_used null`, `calculated_emissions_kg_co2e null` |
| Mapping state | `Load factor options → "No factor options loaded yet."` (with explanatory hint) — no factor resolved |
| Validation | `No validation findings recorded yet.` |
| Available actions | `Retry job`, `Confirm after review`, `Save extraction`, `Save mapping`, `Back to processing`, `Open review workbench`; source pane shows **"View only — download disabled for this role"**. **None clicked.** |
| Evidence/provenance | No evidence record exists for this item (nothing was calculated) — correct for its state |
| API trace | `GET /api/v3/processing/items/d0e979a0…/workspace → 200`, `GET /api/v3/manual-extraction/batches/3e6d33af…/items → 200`, `GET /api/v3/processing/jobs → 200`, `GET /api/v3/documents/0acbea6e…/emissions → 200`; **zero console errors** |

**Investor answer:** yes — what CarbonTally attempted (automatic mapping), the exact machine reason (`no_match`, confidence 0.00, `Water` litres) and the next step (manual review: correct fields / confirm after review) are all visible on one screen. `BROWSER-VERIFIED`
Note: this also corrects DR-004's `LIMITATION` — the workspace endpoint is `/api/v3/processing/items/{id}/workspace` (HTTP 200), not the path guessed then.

## 4. Report verification (Part D)

`BROWSER-VERIFIED` — `/reports` → row click → `/reports/906ce1fc-066a-49c4-b651-8dc964a8c091`:

- List: `READY 2 · QUEUED 0 · GENERATING 0 · FAILED 0`; rows `Annual emissions report 2025 | annual | 2025 | Ready | Sep 20, 2026, 07:47 PM | 1 | 589dbadf` and `ghg_inventory 2025 | ghg_inventory | 2025 | Ready | v1`.
- Detail sections: reporting period, Scope summaries, **Emissions totals**, Source lineage, Factor provenance, Calculation information, Validation, Benchmarking, Organization, Evidence trail — labelled `COMPLETE` where applicable, with the disclaimer *"The evidence trail shows how this result was produced from the source record. It is not an independent audit or certification."*
- Identity/period: `ORGANIZATION Demo Lab Organisation A`, `REPORT TYPE annual`, `REPORTING PERIOD 2025-01-01 → 2025-12-31`, `STATUS Ready`, `CREATED/GENERATED Sep 20, 2026, 07:47 PM` (12 pages).
- **Displayed emissions:** `{"note":"no emissions data in reporting period","unit":"kg unknown","status":"insufficient_data","total_co2e_kg":null}`; Source lineage `{"source":"emissions_logs + emission_factors (read-only aggregation)","aggregate":{"total_rows":0,"by_scope_count":0},"emissions_logs":{"count":0,"reporting_year":2025},"emission_factors":{"resolved":0,"factor_ids":[]}}`.
- APIs: `GET /api/v3/reports`, `/api/v3/reports/<id>`, `/api/v3/reports/<id>/content`, `/api/v3/reports/<id>/versions` — all **200**; zero console errors.

The reports are **real 12-section generated artefacts** (real organisation, period, lineage, validation, provenance, branding) that **display no emissions for 2025** — cause: **staleness, not a generator defect** (§5). `BROWSER-VERIFIED` + `RUNTIME-OBSERVED`

## 5. Report artifact verification (Part D, download)

Read-only retrieval of the two **existing** artefacts (no generation, regeneration or state change) — `RUNTIME-OBSERVED`:

| Artifact | Filename | MIME | Size | Opens? | Consistent with UI? |
| --- | --- | --- | --- | --- | --- |
| `906ce1fc-…` annual 2025 | `report-906ce1fc-066a-49c4-b651-8dc964a8c091.json` | `application/json` (HTTP 200) | 2,358 B | yes — valid JSON, 12 `content` sections | **yes** — same `insufficient_data` totals, `emissions_logs.count 0`, org, period, `generated_at 2026-09-20T13:47:27Z` |
| `baf7e3f8-…` ghg_inventory 2025 | `report-baf7e3f8-…json` | `application/json` (HTTP 200) | 2,372 B | yes | **yes** — same "no emissions data in reporting period", 12 sections, no `2469` |

**Root cause of the empty report content (timestamp evidence, `DATABASE-OBSERVED`):**

- both artefacts were **generated `2026-09-20T13:47:27Z`**;
- the R-A emissions row (`eb88e764-b93a-4bd6-8b66-a24fd6e45ca9`, `source_item_id 2b41b332-…`, `2025-05-05`, `12181.4 kWh (Net CV)`, `2469.16978`, snapshot `af640887…`) was **created `2026-09-20T19:16:24Z`** — **5 h 29 m after** generation.

The reports are therefore correct **point-in-time snapshots taken before the R-A calculation existed**. **Regeneration was not performed** (a mutation, out of scope). `DATABASE-OBSERVED` + `INFERENCE`
Demo consequence: an investor opening today's reports sees a real report reporting *insufficient data* for 2025 while the dashboard shows 2.47 tCO₂e and the CSV export contains the R-A row — a **demo-coherence gap**, not corrupted data.

## 6. Export verification (Part E)

`CODE-TRACED` + `RUNTIME-OBSERVED`:

- UI controls on `/reports` and report detail: `Export emissions CSV`, `Export emissions JSON`, `Export documents CSV`.
- Frontend path: `api.js` → `exportEmissionsUrl(orgId, format, params)` builds `${API_URL}/api/v3/exports/emissions.${format}?organization_id=…`; `downloadExport(url)` performs a **`GET`** with the bearer token and writes the response blob to a download — **no POST, no job creation, no server-side artifact** (`CODE-TRACED`).
- Server-side read-only retrieval of the same endpoint with a real token: `GET /api/v3/exports/emissions.csv?organization_id=…` → **HTTP 200**, `text/csv; charset=utf-8`, `content-disposition: attachment; filename="emissions.csv"`, 703 bytes.
- Content check: header row + exactly the R-A row — `eb88e764-b93a-4bd6-8b66-a24fd6e45ca9`, org `3fd0f325-…`, `emission_factor_id b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5`, `2025-05-05`, `12181.4`, **`2469.16978`**, `kWh (Net CV)`, `Scope 1`, snapshot `af640887-…`, plus `source_item_id`, `source_file`, `source_page`, `activity`, `activity_type` → the export is **real, org-scoped and provenance-rich** (it even carries the emissions-log id DR-004 could not find in the UI).

The export buttons were **not clicked in the browser** (server-side GET + code trace establish the same read-only behaviour); formats available: emissions CSV, emissions JSON, documents CSV. `BROWSER-VERIFIED` (UI present) + `RUNTIME-OBSERVED` (endpoint) + `CODE-TRACED` (method)

## 7. Review / approval verification (Part F)

- **State (unchanged, re-checked):** `/review` → `t3imp_uk-gas__ORG_022_british_gas_202511.pdf | CALCULATED | 2469.16978 | Reviewed: Not yet`; `GET /api/v3/processing/customer-review → 200`. Approval has **not** been performed. `BROWSER-VERIFIED`
- **Controls present:** on `/review/<id>` — `Approve`, `Reject`, `Notes (optional)`, `Close` (per DR-004); none was clicked in DR-005 either.
- **Wiring (`CODE-TRACED`, `frontend/src/v3/customer/ReviewDetailPage.jsx`):**
  - `const APPROVER_ROLES = ['owner','admin']` → `isApprover = APPROVER_ROLES.includes(role)`; controls render only `{isApprover && !alreadyDecided && …}` and `onDecide()` re-checks `if (!isApprover) return;` — **role-gated in the UI**.
  - `onDecide()` requires a confirmation dialog, requires a non-empty **rejection reason** when rejecting (*"A rejection reason is required."*), then calls `submitCustomerReview(itemId, { approved, rejection_reason?, customer_notes? })` from `../api`, and shows `Item approved.` / `Item rejected and returned for correction.`
  - File header states the design intent: *"Approve/Reject is the distinct approver gate: org owner/admin only (D5), **server-authoritative — the UI never approves locally**."*
  - `api.js` additionally exposes report lifecycle actions `submitReportVersion`, `approveReportVersion`, `requestChangesReportVersion`, `rejectReportVersion`, `finalizeReportVersion` and `REPORT_LIFECYCLE_ACTION_CALLS` — a versioned report approval path exists alongside item approval.
- **Conclusion:** the approval workflow is **wired** (UI control → `submitCustomerReview` → V3 API) with owner/admin gating, confirmation, mandatory rejection reason and server authority. The backend handler and DB effect were **not executed**. `CODE-TRACED`
- **Not verified:** server-side authorisation of a non-approver role (e.g. Member attempting approval) — outside read-only scope.

## 8. Consultant verification (Part G)

`BROWSER-VERIFIED` — authenticated through the real form as `consultant_owner`:

- `/consultant` renders the consultant shell: `Consultant | Notifications | CONSULTANT | Sign out`; "Consultant workspace — Demo Lab Carbon Consultants · multi-client portal"; nav `Consultant dashboard · Client workspace · Clients · Firm branding · White-label · Team · Client messages`.
- Dashboard KPIs: `CLIENTS 2 · ACTIVE CLIENTS 2 · PENDING REVIEWS 0 · OPEN ISSUES 0 · READY REPORTS 0`; portfolio health `ACTIVE 2 / SUSPENDED 0 / ENDED 0`.
- **Client list:** `CLIENTS IN DETAIL (2)` — `Demo Lab Client A | 2 documents | 2 items | 0 open issues | 0 ready reports | Reporting →`, `Demo Lab Client B | 1 | 1 | 0 | 0 | Reporting →`.
- **Client selection** (clicked `Client workspace`) switches the active client to `Demo Lab Client A` with the explicit scoping banner **"⚠ You are working on: Demo Lab Client A — every action here applies to this client only."**, and the client-scoped workspace shows `TOTAL CO2E (2026) 0 kg CO₂e · ROWS 0 · DOCUMENTS 2`; a per-client upload control (*"The document is stored under the client organisation and enters the same durable server-side pipeline as a customer upload"*); `Processing pipeline (2)` with stage tabs `All items | Extraction | Mapping | Validation | Calculation | Customer review` and rows `t3imp_consultant-client-a__ORG_022_edf_energy_202606.pdf → extracted (Open workspace)` and `…ORG_029_edf_energy_202510.pdf → extracted`; per-client documents table (2 PDFs, 10 KB / 9 KB); processing counts; `Evidence — persisted calculations (0)`; `Reports — No reports yet.`
- **No cross-boundary leakage observed:** the consultant's Client A view shows Client A's 2 documents/items, not Organisation A's 9 documents or the R-A `2469.16978` row.
- **Role separation:** `org_a_owner` is redirected away from `/consultant` (DR-003), and `consultant_owner` gets the `CONSULTANT` shell rather than the customer shell. APIs: `GET /api/v3/me/context 200`, `GET /api/v3/notifications 200` + client-scoped calls; zero console errors.

## 9. Client verification (Part H)

`BROWSER-VERIFIED` — authenticated through the real form as `client_a_owner` (existing consultant-client owner):

- `/home`: `Demo Lab Client A · V3 customer workspace` — `READY REPORTS 0 · QUEUED REPORTS 0 · DOCUMENTS 2 · MEMBERS 1 · EMISSIONS ROWS 0 · TOTAL TCO₂E 0.00`; `Emissions 0.00 tCO₂e (0 rows)`; `Documents Total 2 · Processed 0 · Pending 0`; `Processing 2 items · 0% complete · Mapped 0 · Unmapped 2`.
- `/documents`: `Documents (2)` — `t3imp_consultant-client-a__ORG_029_edf_energy_202510.pdf` (PDF, 10.4 KB) and `…ORG_022_edf_energy_202606.pdf` (PDF, 9.4 KB); the `Uploaded` column again shows "—" for both.
- **Tenant scoping correct:** the client identity sees only its own organisation's 2 documents / 2 items / 0 emissions; Organisation A's 9 documents and the R-A result are **not** visible, and no consultant/ops surfaces appear in its navigation. `BROWSER-VERIFIED`
- Client depth beyond the shell (item workspaces, review, reports per item) was not walked — `PARTIALLY VERIFIED`.

## 10. Billing verification (Part I)

- `BROWSER-VERIFIED` (DR-003/DR-004 captures): `/billing` renders "Your commercial plan, credits, storage and orders" — `Plan: No active subscription (v— · —)`, `Billing mode CREDIT`, "Customer-specific (never silently changed)", `Credits 0 available / 0 included monthly`, `Storage 0 B used / 0 B included`, `Credit history: No credit activity yet.`, `Assisted Processing estimate` (line-complexity selector + `Create estimate`), `Managed Processing` (`Submit managed request`), `Orders: No orders yet.`
- `CODE-TRACED`: `frontend/src/v3/customer/BillingPage.jsx` renders a **provider-neutral payments list** with the note *"Provider-neutral records — no payment details stored."*; no Stripe/checkout/card fields/redirect flow appear in that page. Endpoints referenced in the frontend: `/api/v3/billing/me`, `/billing/me/credits`, `/billing/me/orders`, `/billing/me/payments`, `/billing/me/storage/refresh`, `/billing/orders/assisted`, `/billing/managed/orders`.
- **No** subscription, estimate, order, plan change or payment action was taken; **no** external provider was contacted. Any end-to-end local demo purchase path was **not executed** — `IMPLEMENTED — NOT VERIFIED`.

## 11. Realtime investigation (Part J)

`CODE-TRACED` + `RUNTIME-OBSERVED` (DR-003):

- **Gateway:** the Demo Lab nginx gateway serves only `/auth/v1/`, `/rest/v1/`, `/storage/v1/` — there is **no `/realtime/v1/` location**, so `ws://127.0.0.1:54430/realtime/v1/websocket` fails. Not modified (out of scope).
- **Frontend Realtime consumers:** `lib/realtime/manager.js`, `context/RealtimeContext.jsx`, `hooks/useNotifications.js`, `v3/messaging/useConversationRealtime.js`, plus legacy `components/DocumentStatus.jsx`, `components/ActivityFeed.jsx`, chat widget.
- **HTTP polling already covers the operational surfaces:** `v3/customer/ProcessingPage.jsx` → `setInterval(() => load(org.id), 10000)`; `ProcessingItemWorkspace.jsx` → interval refresh. Processing/document/review status therefore does **not** depend on Realtime.
- **Affected:** live notification push and live message delivery in messaging (history loads over HTTP). Sending a message is a mutation and was **not attempted**.
- **Verdict:** the missing route affects **messaging live-delivery and notification push only**, not the calculation/processing/reporting journey. `PARTIALLY VERIFIED` / `BLOCKED` (messaging-live).

## 12. UI → API traces (Part L)

| # | Surface / component | Frontend function | Endpoint (observed) | Result | Rendered |
| --- | --- | --- | --- | --- | --- |
| 1 | `ProcessingItemWorkspace` (exception item) | workspace loader | `GET /api/v3/processing/items/{id}/workspace`; `GET /api/v3/manual-extraction/batches/{id}/items`; `GET /api/v3/processing/jobs`; `GET /api/v3/documents/{id}/emissions` | all **200** | blocking reason, extraction JSON, empty mapping/calculation/evidence |
| 2 | `ReportsPage` (`/reports`) | `listReports` | `GET /api/v3/reports` | **200** | 2 READY reports + counters |
| 3 | `ReportDetailPage` (`/reports/{id}`) | `getReport`, `getReportContent`, `getReportVersions` | `GET /api/v3/reports/{id}`, `…/content`, `…/versions` | all **200** | 12-section preview, `insufficient_data` totals, lineage/provenance/validation, org + period |
| 4 | Report artifact download | `downloadReport(reportId)` | `GET /api/v3/reports/{id}/download` | **200**, `application/json`, 2,358 B | real 12-section JSON artifact |
| 5 | Export buttons | `exportEmissionsUrl` + `downloadExport(url)` | `GET /api/v3/exports/emissions.csv?organization_id=…` (also `.json`, `/documents.csv`) | **200**, `text/csv`, 703 B | real CSV incl. the R-A row `2469.16978` |
| 6 | Approval controls | `submitCustomerReview(itemId, {approved, rejection_reason?, customer_notes?})` | review decision API (`GET /api/v3/processing/customer-review` observed 200) | **not executed** | `Approve`/`Reject` render only for owner/admin |
| 7 | `ConsultantPage` (`/consultant`) | consultant loaders | `GET /api/v3/me/context` + client-scoped document/reporting calls | **200** | 2 clients, KPIs, client-scoped workspace banner |
| 8 | Client shell (`client_a_owner`) | standard V3 loaders | `GET /api/v3/me/context`, `GET /api/v3/documents`, reporting endpoints | **200** | only Client A's 2 documents / 0 emissions |
| 9 | `BillingPage` (`/billing`) | billing loaders | `GET /api/v3/billing/me`, `/credits`, `/orders`, `/payments` (code-traced) | not re-executed | "No active subscription", CREDIT mode |
| 10 | Realtime | `RealtimeContext` / `useNotifications` / `useConversationRealtime` | `ws://…/realtime/v1/websocket` | **connection fails** | processing unaffected (10 s HTTP polling) |

## 13. Verification matrix (Part M)

| Capability | Browser status | Backend status | Real data? | Mutation attempted? | Evidence | Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Exception workspace | **BROWSER VERIFIED** | 200 on workspace / batch items / jobs / document emissions | yes (`Water`, 67 L, `INV2025008630`) | **No** | §3, `a_exception.png` | none material |
| Reports | **BROWSER VERIFIED** | 200 on list / detail / content / versions | yes (real org, period, 12 sections) | **No** | §4, `b1/b2` screenshots | content says "no emissions data" (stale — §5) |
| Report artifact | **BROWSER VERIFIED** (UI) + artifact retrieved read-only | 200, 2,358 B / 2,372 B JSON | yes — real artefacts | **No** | §5 | predates the R-A row by 5 h 29 m |
| Export | **BROWSER VERIFIED** (UI) + `RUNTIME-OBSERVED` | 200, 703 B `text/csv` | yes — contains the R-A row | **No** (GET only) | §6, `/tmp/export.csv` | buttons not clicked in-browser |
| Review | **BROWSER VERIFIED** | `customer-review` 200 | yes | **No** | §7 | approval not executed |
| Approval wiring | `CODE-TRACED` (control → fn → API) | handler not executed | n/a | **No** | §7 | server-side authorisation untested |
| Consultant | **BROWSER VERIFIED** | 200 (`me/context` + client calls) | yes — 2 clients, scoped items | **No** | §8, `c1/c2` screenshots | consultant member role untested |
| Client | **BROWSER VERIFIED** (shell/scoping) / `PARTIALLY VERIFIED` (depth) | 200 | yes — Client A only | **No** | §9, `d_client_home.png` | per-item client depth not walked |
| Billing | `BROWSER VERIFIED` (display; DR-003/4) | endpoints code-traced | plan/credits display yes | **No** | §10 | no execution path exercised |
| Realtime/messaging | `BLOCKED` (WS fails) | `/realtime/v1/` absent from the lab gateway | messaging history HTTP; live delivery no | **No** | §11 | not fixed (out of scope) |

## 14. Actual data used

Organisation `Demo Lab Organisation A` (`3fd0f325-16a1-5b53-8fb8-27929cf218fa`) with 9 documents and 1 emissions row; exception item `d0e979a0-c5cf-47fc-9bc3-7ec3259059ea` / `t3imp_uk-water__ORG_030_thames_water_202605.pdf`; reports `906ce1fc-…` (annual 2025) and `baf7e3f8-…` (ghg_inventory 2025); consultant firm `Demo Lab Carbon Consultants` with clients `Demo Lab Client A` (2 docs / 2 items) and `Demo Lab Client B` (1 / 1); client identity `client_a_owner`. Identities used: `org_a_owner`, `consultant_owner`, `client_a_owner` — all pre-existing, authenticated through the real login form.

## 15. Data-mutation audit

| Action class | Occurred? |
| --- | --- |
| Upload / retry / confirm / correct / delete | **No** |
| Approve / reject / request changes / finalize | **No** |
| Report generation or regeneration | **No** (existing artefacts only read/downloaded) |
| New export artifact/job | **No** — export is a GET stream; nothing persisted |
| Subscription / plan change / payment | **No** — no provider contacted |
| Message send / conversation change | **No** |
| Organization or member change | **No** |
| Demo Lab reset / reseed / configuration change | **No** |
| Observational writes | authentication sessions for three existing demo identities (inherent to real login; permitted) |
| Read-only interactions | 3 browser logins, ~12 authenticated page views, 1 exception workspace opened, 1 report detail opened, 2 artifact downloads (read-only GET), 1 server-side export GET |
| Console errors | **none** in the browser run |

No supposedly read-only operation mutated state; the Part K guarantee held.

## 16. Concrete defects

1. **Reports are stale relative to the R-A calculation** — both READY artefacts (generated 13:47) predate the emissions row (created 19:16), so a real report reports `insufficient_data` / "no emissions data in reporting period" while the dashboard shows 2.47 tCO₂e and the export contains the row. Requires regeneration (a mutation — not performed).
2. **`Uploaded` column empty ("—")** for every document, reproduced for the client identity too.
3. Carried over from DR-004 and still true: workspace `Scope -`, review `Mapped activity —`, factor source labelled `DEFRA-DESNZ`, extraction `Currency/Amount` labels without values, no customer document-detail/preview.
4. **Messaging live-delivery cannot work** in the Demo Lab because the gateway has no `/realtime/v1/` route (lab capability gap, not an application defect).

## 17. Implemented but unverified functionality

- Approval/rejection **execution** and its server-side effects; authorisation of a non-approver role.
- Report **generation/regeneration** and the versioned report lifecycle actions (`submit/approve/requestChanges/reject/finalizeReportVersion`).
- Billing execution paths (assisted/managed orders, credits, storage refresh) and the plans list beyond "No active subscription".
- Client depth beyond the shell (client item workspace, client review, client report).
- Consultant `Team`, `Firm branding`, `White-label`, `Client messages` tabs and the consultant **member** role.
- Messaging surfaces (inbox rendering / send paths), blocked by the missing Realtime route for live delivery.

## 18. Blocked functionality

- **Messaging live delivery / notification push** in the Demo Lab (no `/realtime/v1/` gateway route).
- Browser-click verification of export/report download beyond the server-side GET equivalence (buttons intentionally not clicked; the endpoints themselves were verified read-only).

## 19. Deferred functionality

- Report regeneration so demo reports contain the R-A emissions (mutation — needs PO authorisation).
- R-A approval walkthrough (PO authorisation required).
- Realtime route addition to the lab gateway (lab capability; needs authorisation).
- Consultant/client deep journeys and PE/internal surfaces.

## 20. PO decisions required

1. Authorise **report regeneration** after the R-A calculation so the demo reports contain the emissions (removes the demo-coherence gap).
2. Authorise a bounded **approval/rejection walkthrough** (real state change on an authorised identity) — or decide approval stays unexercised for the demo.
3. Decide whether to add the missing **`/realtime/v1/` gateway route** to the Demo Lab (enables messaging live-delivery verification).
4. Decide whether the **`Uploaded` column** and the other display gaps (DR-004 §18) should be triaged as frontend defects.
5. Confirm whether a **safe local demo billing flow** exists and should be demonstrated (no provider contact).
6. Authorise verification depth for consultant/client per-item journeys and PE/internal surfaces.

## 21. Final bounded verdict

Beyond the core calculation journey, the implemented CarbonTally product **is** browser-demonstrable across the remaining investor workflows, from live backend data: the exception workspace explains precisely what was attempted, why mapping stopped (`no_match`, confidence 0.00 for `Water` litres) and what the customer can do next; reports are real 12-section generated artefacts with organisation, period, lineage, provenance, validation and branding — their empty 2025 emissions content being a **staleness** effect (generated 5 h 29 m before the R-A row), not a generator defect; exports are real org-scoped CSV/JSON GETs whose CSV contains the R-A row with `2469.16978`, the factor id, the snapshot id and the emissions-log id; the approval workflow is wired with owner/admin gating, confirmation, a mandatory rejection reason and server authority (never executed); the consultant workspace shows a 2-client portfolio with explicit active-client scoping and client-scoped documents/items; the client identity is correctly restricted to its own two documents with no cross-tenant leakage; billing renders provider-neutral plan/credit/order surfaces with no payment integration; and the missing Realtime route affects only messaging live-delivery and notification push, because processing views already refresh via 10-second HTTP polling. Nothing was mutated, nothing was approved, no configuration or application code was changed, and this report asserts nothing beyond the evidence above; CarbonTally is **not** declared investor-ready.
