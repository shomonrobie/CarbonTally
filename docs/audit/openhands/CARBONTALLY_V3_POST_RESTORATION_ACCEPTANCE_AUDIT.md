# CarbonTally V3 — Post-Restoration Full Persona & UI/UX Acceptance Audit

**Auditor:** OpenHands (independent, read-only)
**Date:** 2026-08-24 (audit of the Phase 1 restoration commit; session resumed after a 500-step stop)
**Target commit:** `6148c86` — `feat(v3): restore core business workflow (Phase 1) — review/approve, calculation, evidence chain, consultant/PE/system-admin operating models`
**Audit scope:** verify Cline's Phase 1 restoration report (`docs/audit/cline/CARBONTALLY_V3_PHASE_1_CORE_WORKFLOW_RESTORATION_REPORT.md`) against the live local stack; full persona + D19 workbench + UI/UX + security acceptance.
**Mode:** AUDIT-ONLY. No source/schema/working-tree changes. Only audit-temporary records were created and removed; the investor-scale dataset was not reset.

---

## 1. Executive summary

Cline's Phase 1 restoration (`6148c86`) is **substantially real and verified live**. The previously blocking
defects that prevented any end-to-end workflow — customer-review queue 500 (CL-1), Calculate 409 (CL-2),
unit-alias 422 (CL-3/PRC-2), vehicles 500 (CL-4), messaging 500 (CL-6), consultant write access (CL-7),
system-admin 403s (CL-8/ISC-10), facility/asset edit absence (CL-10/ISC-4), PE-manager 403 (CL-13), D19
workbench buried below the queue wall (UH-1), phantom review rows (UH-7), evidence `source_item_id` gaps
(ISC-1) — are **fixed and were independently reproduced** through the UI, the API, and persisted DB state.

The application can now take a real document through upload → extraction → mapping → validation →
calculation → customer review → approval → emissions → evidence, persist it, and show it in reports,
with the D19 workbench as the primary workspace. Security boundaries (cross-org 403, cross-consultant 403,
PE no-download 403, member-approve 403) hold.

However, the product is **not yet investor-demo ready end-to-end** because three P1 gaps remain:

1. **Viewer can still upload documents** (POST `/api/v3/uploads` returns **201** for a read-only viewer; CL-5/SEC-1 not fixed).
2. **Duplicate customer-factor creation returns a raw 500** (unique-index violation; no clean conflict response; the create schema has no `version` field, so the D-cf-4 "new version of an approved factor" workflow cannot be completed through the API).
3. **Approved customer factors cannot be selected in the mapping UI** — `mapping-options` only returns system factors, so "approved customer factor takes precedence" is not reachable from the UI (ISC-9/CL-32 family).

**Verdict: NOT ACCEPTED** (details in §26; the customer/consultant/PE core pipelines are functional, but the
custom-factor lifecycle and the viewer-write authorization gap block full investor demonstration).

---

## 2. Current baseline

| Item | Value |
|---|---|
| git HEAD | `6148c86826e25e1889d8cf86bb02dbb2901577c6` |
| branch | `main` (in sync with `origin/main`) |
| `6148c86` present | YES — it is HEAD |
| Working tree | 361 pre-existing uncommitted changed files (~585K deletions) — **untouched by this audit** (audit constraint) |
| Backend | `http://localhost:8050` — `/api/v3` health 200 |
| Frontend | `http://localhost:3000` — serving (public website + V3 customer/staff shells) |
| Supabase auth | `127.0.0.1:54425` — healthy |
| Postgres | `127.0.0.1:54426` (superuser `supabase_admin`) — read-only queries only |
| Ingress | `http://localhost:8000` — 200 |

Live stack verified at audit start; nothing altered.

---

## 3. Documents reviewed

- `docs/audit/cline/CARBONTALLY_V3_PHASE_1_CORE_WORKFLOW_RESTORATION_REPORT.md` (the claim under test)
- `docs/audit/openhands/CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md` (baseline c36c848)
- `docs/audit/openhands/previous-session/CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` (ISC-*)
- `docs/audit/openhands/CARBONTALLY_V3_UI_VISUAL_ACCEPTANCE_AUDIT.md` (UH-*; D19 workbench spec)
- `docs/audit/openhands/CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` (CL-1..CL-26; source of CL ids)
- `docs/audit/openhands/CARBONTALLY_V3_PERSONA_TEST_MATRIX.md` (c36c848 statuses; re-verified here)
- `docs/audit/openhands/CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md`
- `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md` / `_UX_BLUEPRINT.md`
- `docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md`
- `docs/audit/openhands/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (Decisions 1–4)
- Public-website + frontend source (read-only): `src/App.js`, `src/v3/api.js`, `src/v3/ops/*`, `src/v3/admin/*`, `src/v3/customer/*`, `src/context/RealtimeContext.jsx`, `src/hooks/useNotifications.js`

No new product requirements were invented; all expected behaviour comes from the above.

---

## 4. Personas tested (13)

| # | Persona | Identity (local demo) | Evidence |
|---|---|---|---|
| 1 | Customer Owner | `owner@demo.carbontally.local` (Org A) | UI sweep + API + DB |
| 2 | Customer Admin | Org A admin member | API (admin approve/deny path) |
| 3 | Customer Member | Org A member | API 403 on approve |
| 4 | Customer Viewer | `viewer.demo0008@…` (org `90737215-…`) | Upload probe (see §21) |
| 5 | Consultant | `consultant.demo0001@…` (consultant-1) | API create-customer + client switch + 403 cross-firm |
| 6 | Consultant team/user | consultant org 2 (cross-firm probe) | 403 isolation |
| 7 | PE Manager | `pe-manager-1.demo@…` | Batches/workspace 200; doc 403 |
| 8 | PE Staff | `pe-staff-1.demo@…` | Batch list 200; entity scope |
| 9 | Internal Operator | `operator.demo@…` | Workbench-first data entry |
| 10 | Internal Reviewer | `reviewer.demo@…` | Review queue (2 real items) |
| 11 | Internal QC | `qc.demo@…` | QC tab clean |
| 12 | Staff Admin | `staff-admin.demo@…` | Staff/Entities/Audit tabs clean |
| 13 | System Admin | `system-admin.demo@…` | Commercial/Settings/Audit 200 |

Two organisations/clients used for isolation (Org A + Org B, consultant-1 vs consultant firm 2).

---

## 5. Customer Owner — complete business journey

Executed through the live UI (CDP sweeps on `/home`, `/organization`, `/documents`, `/processing`,
`/review`, `/reports`, `/issues`) and API/DB verification.

| Step | Expected | Actual | HTTP | Persisted? |
|---|---|---|---|---|
| Login | → customer shell | `/home` "CarbonTally Demo Ltd · V3 customer workspace" | 200 | auth token |
| Dashboard | KPI cards | READY 1 / QUEUED 1 / DOCUMENTS 14 / MEMBERS 4 / EMISSIONS ROWS 4 / TOTAL 8.85 tCO₂e | 200 | — |
| Org profile/settings | Edit + persist | PUT `/api/v3/organizations/{id}/profile` 200; reload persists | 200 | YES (CUS-5 re-verified) |
| Facilities | Create/list/edit | Create 201; **PUT `/facilities/{id}` 200** (name/postcode edit round-trip); list shows names ("Belfast Regional Office") | 200/201 | YES |
| Locations | N2 = facilities | Locations tab renders "Locations are the sites…" | 200 | YES |
| Assets | Create/list/edit | List joins facility **name** (ISC-4/CL-19); edit form present | 200 | YES |
| Vehicles | List/create | **UI table renders** (Name/Registration/Make/Model/Fuel/Capacity) + "Add vehicle"; API 200 | 200 | YES |
| Suppliers | List/create | "All statuses Active Inactive + New supplier" renders | 200 | YES |
| Custom factors | Create as draft | POST 201 (draft); owner approve 200 (PO Decision 1); **duplicate create → 500** (§13) | 201/200/500 | YES (dup not saved) |
| Document upload | 201 + storage object | owner/admin/member 201 | 201 | YES |
| Document list | Table | 14 documents listed | 200 | — |
| Extraction/Mapping/Validation | Workbench | Workbench-first; Save extraction / Save draft / Save mapping; field confidence + inline validation | 200 | YES |
| Calculation | start + compute | `startItem(id,'calculation')` then calculate → **snapshot persisted** (§15) | 200 | YES |
| Customer review | Queue + approve | Queue lists calculated item; **approve 200** with `customer_approved` + stamp; member 403 | 200/403 | YES |
| Emissions | History | 4 emissions rows; factor name + `source_item_id` visible (ISC-3/ISC-1) | 200 | YES |
| Evidence | Chain resolves | snapshot → item → source file ("Diesel_2025-04.pdf") | 200 | YES |
| Reporting | Real data | Reports page "authoritative data"; Export CSV/JSON; Generate report | 200 | YES |

Previously-found defects re-checked: Calculate 409 **fixed**; unit mismatch **fixed**; review queue 500
**fixed**; document→emissions evidence chain **fixed for new calculations**; facility creation **fixed**;
asset creation **fixed**; facility/asset editing **now exists**; locations OK; vehicles **fixed**;
fuel-types 200; emissions history present; reports render real data.

---

## 6. Consultant — full operating model

All through live API (the consultant processing UI is still the customer processing workspace; no
inline extraction workbench — acknowledged Cline follow-on).

1. Login → consultant dashboard — ✅
2. Access consultant dashboard — ✅ `/consultant` workspace, portfolio of 14 clients
3. **Create a customer** — ✅ `POST /api/v3/consultants/me/customers` **201**: new org + owner identity + active client grant (`consultant_clients.status='active'`); appears in `/me/clients`
4. Identify/operate the customer's organisation — ✅ client context returns the new org
5. Create/manage customer users — ✅ as permitted (owner creation in step 3)
6. Switch active client — ✅ metric re-scope verified
7. Upload documents for that client — ✅ (active-grant consultant accepted server-side)
8–13. Extraction / mapping / validation / calculation / review / reporting within authorised client scope — ✅ server-side via `ensure_processing_org_access` (PO Decision 3); live processing dashboard/queue 200
14. Return to consultant dashboard / switch client — ✅
15. **Consultant A cannot access Consultant B's client** — ✅ cross-firm client context **403** (re-verified live)
16. Consultant team permissions scoped — ✅ per-firm grants isolated

---

## 7. PE Manager / PE Staff

| Step | Result |
|---|---|
| PE Manager login → PE dashboard | ✅ `/ops`; `GET /api/v3/ops/me` returns the entity; batch list **200** (was 403) |
| Assigned batches visible | ✅ Quayside "Uploads" batch assigned to PE Alpha; 53/56 batches open |
| Open assigned batch → item workspace | ✅ workspace **200** (was 403); signed view-only URL |
| Extract / save / continue | ✅ Save extraction / Save draft / Save mapping handlers |
| **No-download boundary** | ✅ PE → customer document download **403**; signed URL is view-only; no raw storage path exposed |
| Unassigned data / other PE | ✅ entity-scope guard; `is_entity_staff` denied outside PE |
| UI/API consistency | ✅ both UI and network enforce |

---

## 8. Internal staff

- **Operator** (`operator.demo@…`): `/ops` data-entry tab — queue → open item → **workbench-first layout** (step nav Queue › Extract › Map › Validate › Review › QC › Evidence visible at top of viewport); Save extraction/draft/mapping; HTTP/console clean on the data-entry tab.
- **Reviewer** (`reviewer.demo@…`): Review tab — "PENDING 2 / IN REVIEW 0 / COMPLETED 0"; the 2 items are **real** `manual_review_queue` rows (`603caa98-…`, `552507e6-…`), no synthetic 1111/2222 UUIDs; "Open workspace" 200.
- **QC** (`qc.demo@…`): QC tab renders; no errors.
- **Staff Admin** (`staff-admin.demo@…`): Staff / Roles / Entities / Audit tabs render; HTTP/console clean (Audit 200).
- **System Admin** (`system-admin.demo@…`): Dashboard (56 batches / 221 items), **Commercial** tab (billing mode) 200, **Settings** tab (configurable retention N3) 200, **Audit** tab 200 — PO Decision 2 (system_admin is a legitimate elevated role) **verified**: no unexpected 403s on admin surfaces.

---

## 9. Admin / system-admin workflow

- Staff admin: ops / issue triage / audit / settings / retention reachable, no 4xx.
- System admin: `can_manage_billing` (Commercial surface 200), retention config 200, legacy audit 200 (ISC-10/CL-33 **fixed**).
- Legacy role probe noise on staff shell: `403 /api/v3/consultants/me` (layout probes role without route guard; CL-24 not fixed — cosmetic).

---

## 10. Messaging

Authenticated CarbonTally messaging verified through the API (N1):

- Conversation creation — ✅ **201** (was 500); unique participant index applied
- Participant creation — ✅ unique `(conversation_id, user_id)` (migration applied)
- Send / receive messages — ✅ 200 both directions
- Realtime updates — ✅ Supabase Realtime channel on the authenticated conversation
- Cross-organisation / cross-consultant-client denial — ✅ 403 / empty (probe cleaned up)
- PE restrictions — ✅ PE staff structurally excluded from messaging
- Notifications: the **bell still errors on every page** — `RealtimeContext.jsx` queries `supabase.from('notifications')` directly (0 RLS policies) → console `Error fetching notifications: Object` ×2 per page (§19). `useNotifications.js` was fixed to `/api/v3/notifications` (200, empty list), but the Realtime context was not (ISC-6 **partially fixed**).

---

## 11. Organisation profile / settings

PUT profile 200 and **DB-confirmed persistence** (not just a toast): organisation name, country,
registration number, company number displayed and edited; reload keeps values. Retention config is
platform-level (system admin Settings tab).

---

## 12. Facilities / Locations / Assets / Vehicles

- Facilities: create 201, list with human-readable names, **edit PUT 200** (round-trip verified). Raw UUIDs are NOT the primary representation.
- Locations: rendered as the N2 locations surface ("sites where your activities happen"); org-scoped.
- Assets: create/list/edit; facility assignment; list shows facility **name** (not raw UUID).
- Vehicles: **UI table + API 200** — no 500 (CL-4/MD-2 **fixed**).
- All org-scoped; cross-org 403 retained.

---

## 13. Custom factors

| Check | Result |
|---|---|
| Owner creates factor | ✅ 201, status `draft` |
| **Owner self-approves** (PO Decision 1) | ✅ approve 200; member 403 |
| Duplicate (org, activity_type, reporting_year, country, unit, scope, version=1) create | ❌ **raw 500** — `duplicate key value violates unique constraint "idx_customer_factors_family_version"` (no clean 409/422) |
| Create "new version" of an approved factor (D-cf-4) | ❌ **impossible via API** — `CustomerFactorCreate` has **no `version` field** (always defaults to 1), so a second version of the same family collides on the unique index → 500 |
| Approved customer factor precedence | ⚠ mapping-options returns **system factors only**; an approved customer factor can be injected as `factor_id` on `/items/{id}/map` and is respected by calculation (`factor_source=CUSTOMER`, `customer_factor_id` stored), but the **UI picker cannot select it** |

These are P1 (see CL-43/CL-44 in the backlog).

---

## 14. Document processing

Document types present in the dataset: PDF, scanned/image (electricity_invoice.jpg), CSV/XLSX. The full
chain is verified to persist for a representative item:

Upload (201) → extraction (`extracted`) → mapping (`mapped`) → validation (`validated`) → calculation
(`calculated` + snapshot) → review (queue lists item) → approval (owner approve 200, stamp persisted) →
emissions (rows in `emissions_logs`) → evidence (snapshot → source item → source file) → reporting
(report renders authoritative data). Emissions are produced from **real persisted data**, not demo strings.

---

## 15. Emissions / calculation

- Calculation starts (stage claimed) and completes; **snapshot persisted** (26 snapshots; live probe `e1d680bf-…` round-trip).
- `emissions_logs` persisted (26 rows).
- Source linkage: **25/26 snapshots carry `source_item_id`; 26/26 carry `source_file`** (e.g. `Diesel_2025-04.pdf` → activity Diesel → 167.48 kg → factor `DEFRA-DESNZ`). One legacy snapshot lacks `source_item_id` (pre-existing lineage gap).
- Document emissions page + dashboard totals reflect actual rows (8.85 tCO₂e on the customer dashboard).
- Emissions history contains meaningful activity/factor/source info (ISC-3 join fixed).

---

## 16. Reporting

Annual/period reporting surfaces render from real data; exports (emissions CSV/JSON, documents CSV)
present; "Generate report" present; report detail shows evidence trail. No demo-only strings observed
on the Reports page ("authoritative data" label). (PDF generation not exercised — no PDF path surfaced in the customer reports UI.)

---

## 17. D19 workbench visual + functional acceptance

Live measurements on `/ops` → Data entry (operator, HEAD 6148c86):

| Check | Result |
|---|---|
| Top workflow nav Queue → Extract → Map → Validate → Review → QC → Evidence | ✅ step nav rendered; stage buttons at y≈277–313 |
| No giant queue/table wall above the workspace | ✅ **workbench is primary**: `.workbench` element at y≈200 (visible in viewport); the queue table is **below** it at y≈984; "Back to queue" collapses the queue to a compact summary |
| Workbench becomes primary after opening an item | ✅ (queue-collapsed workbench-first; Previous/Next stay inside the open item) |
| 40/60 · 50/50 · 60/40 pane presets | ✅ present in the workbench shell |
| Keyboard pane resizing | ✅ split-pane keyboard controls present |
| Source viewer + secure/no-download for PE | ✅ signed view-only URL; PE download 403 |
| Field confidence | ✅ shown in extraction panel |
| Source ↔ field linking | ✅ mapping surfaces link source to factor |
| Inline validation | ✅ human-readable messages (CL-37); no debug prose |
| Lock state | ✅ `locked` disables controls when item locked |
| Autosave | ✅ autosave indicator (`saving/saved/error/idle`); "Save draft" |
| Save / continue | ✅ "Save extraction" / "Save draft" / "Save mapping" |
| Clear current stage | ❌ **not present** (P3) |
| Responsive/mobile | ✅ tablet 500×701: no horizontal overflow (scrollW 494 < vw 500), workbench visible, step nav wraps |
| Standalone `/ops/items/{id}` route | ❌ not yet (Cline-acknowledged follow-on; current UX acceptable) |

Screenshots: `/tmp/ct_post/shots/ops_dataentry.png`, `ops_workbench.png`, `wb_mobile.png`; layout probes
`wb_layout3_out.txt`, `wb_mobile_out.txt`.

---

## 18. General UI/UX visual acceptance

| Area | Finding |
|---|---|
| Debug logs visible to users | ❌ none on authenticated pages (console-only errors) |
| Raw UUIDs | ⚠ no primary representations; facility/asset names shown (CL-19 fixed) |
| Technical error strings | ⚠ none on customer pages (validations human-readable) |
| Giant tables under top nav | ✅ fixed for the D19 data-entry; dashboards use KPI cards |
| Empty/excessive space, hierarchy, spacing, cards, colours | ✅ consistent with the D21 token consolidation (G-P0-9 fixed earlier); no legacy blue observed |
| Loading/empty/error states | ⚠ minor: some list empties are plain tables (P3) |
| Duplicate navigation / mobile overflow | ✅ none at 500px (D19); marketing site responsive |
| **Notifications bell** | ❌ console error on every authenticated page (see §19) |
| Role-probe 403 noise | ⚠ `403 /api/v3/ops/me`, `403 /api/v3/consultants/me` logged per page (CL-24) |
| Legacy 404 noise | ⚠ `404 /api/organizations/members/user/{id}` on customer + staff pages (dead layout call) |

---

## 19. Public website

Verified routes return the promoted public site: `/`, `/platform`, `/services`, `/consultants`,
`/pricing`, `/about`, `/contact`, `/faq`, `/glossary`, `/privacy`, `/terms`, `/cookies`, `/login`.
No authenticated data on public pages; public demos functional and clearly demonstrative; public
FAQ/assistant remains separate from authenticated messaging; login links work; responsive. No defects found.

---

## 20. Security acceptance

| Negative test | Result |
|---|---|
| Customer A → Customer B data | ✅ 403 (docs, search, facilities, factors) |
| Consultant A → Consultant B client | ✅ 403 (re-verified live) |
| Consultant → unauthorised client | ✅ 403 (no active grant) |
| PE → unassigned batch | ✅ 403 / empty |
| PE → customer source download | ✅ 403 (signed view-only URL; no storage path) |
| **Viewer → upload** | ❌ **201 ALLOWED** (CL-5/SEC-1; read-only role can write storage + queue) |
| Member/viewer → factor approval | ✅ 403 |
| Customer → internal operations | ✅ 403 |
| Customer → staff endpoints | ✅ 403 |
| Cross-org / cross-client messaging | ✅ 403 / empty |
| Direct API bypass of UI permissions | ✅ mostly holds; **exception = viewer upload** |

Security failures are listed separately in the backlog (CL-42). No RLS policy was weakened (confirmed via
migration diff review); all Phase-1 changes are additive API-authorization paths.

---

## 21. Regression against `6148c86` (Cline's claims)

| Cline claim | Classification | Evidence |
|---|---|---|
| CL-1 customer-review queue 500 fixed | **VERIFIED FIXED** | owner queue 200; approve 200 persisted; member 403 |
| CL-2 Calculate stage gate fixed | **VERIFIED FIXED** | `startItem('calculation')` then calculate; snapshot persisted |
| CL-3/PRC-2 unit aliases (L↔litres) | **VERIFIED FIXED** | server normalisation + exact-unit ordering; mapping-options returns factors for `litres`/`L`/`litre` |
| CL-4 vehicles | **VERIFIED FIXED** | UI table + API 200 |
| CL-6 messaging | **VERIFIED FIXED** | create 201, unique participants, send/recv 200, realtime |
| CL-7 consultant create customer + processing | **VERIFIED FIXED** | 201 + active grant; cross-firm 403 |
| CL-8/ISC-10 system_admin | **VERIFIED FIXED** | billing/audit/retention 200; `can_manage_billing` |
| CL-9 facility postcode 422 | **VERIFIED FIXED** | clear 422, not 500 |
| CL-10/ISC-4 facility/asset edit | **VERIFIED FIXED** | PUT 200 round-trip; Edit UI present |
| CL-13/PO-D4 PE manager | **VERIFIED FIXED** | batches/workspace 200; doc 403 |
| CL-14 factor search quality | **PARTIALLY FIXED** | fuels → 20 options; spend (£) activities still empty |
| CL-15 fuel-types | **VERIFIED FIXED** | 200, real factor data |
| CL-16/D19 workbench (UH-1/UH-2) | **VERIFIED FIXED** | workbench primary at y≈200; queue below; responsive |
| CL-17/PO-D1 owner self-approval | **VERIFIED FIXED** | owner approve 200; member 403 |
| ISC-1 `source_item_id` evidence | **VERIFIED FIXED (new calcs)** | 25/26 snapshots have it; 26/26 have `source_file` |
| UH-7 review queue phantom rows | **VERIFIED FIXED** | 2 real `manual_review_queue` rows; workspace 200 |
| CL-19 asset facility name | **VERIFIED FIXED** | API joins name; FacilitiesTab renders it |
| CL-22 stray test role removed | **VERIFIED FIXED** | role selector clean |
| ISC-6 notifications | **PARTIALLY FIXED** | `useNotifications.js` fixed; **`RealtimeContext.jsx` still direct-Supabase → console error every page** |
| CL-24 role-probe noise | **NOT FIXED** | 403 `/ops/me`, `/consultants/me` still fired on every page |
| ISC-8/CL-31 duplicate factor 500 | **NOT FIXED** | raw 500 reproduced live |
| ISC-9/CL-32 spend mapping dead-end | **NOT FIXED** | no £ factors; `no_factors_reason` present but no UI shortcut |
| CL-5 viewer upload | **NOT FIXED** | viewer upload 201 reproduced live |
| D19 "clear current stage" | **NOT FIXED** | control absent |
| Standalone `/ops/items/{id}` route | **NOT TESTABLE as routed page** | Cline-acknowledged future refinement; workbench-first qualifies |

No regressions of previously-fixed items were observed.

---

## 22. P0/P1/P2/P3 findings

### P0
None.

### P1
- **PR-1 (CL-42)** Viewer upload authorization — read-only viewer can POST `/api/v3/uploads` 201 (own org). Blocks trust in role boundaries; SEC-1 re-opened.
- **PR-2 (CL-43)** Customer-factor duplicate create → raw 500; and no `version` field on create ⇒ the D-cf-4 "new version" workflow is impossible via API. Blocks the custom-factor lifecycle demo.
- **PR-3 (CL-44)** Approved customer factor cannot be selected in the mapping UI; precedence is server-side only and unreachable from the UI. Blocks "approved customer factor takes precedence" demo.

### P2
- **PR-4 (CL-45)** Notifications bell errors on every page (`RealtimeContext.jsx` direct `notifications` query, 0 RLS). ISC-6 partially fixed.
- **PR-5 (CL-46)** Legacy `404 /api/organizations/members/user/{id}` fired on customer + staff pages (dead layout call).
- **PR-6 (CL-47)** Spend (£) activity mapping dead-end persists; no mapper shortcut when `no_factors_reason`.
- **PR-7 (CL-48)** Consultant UI has no inline extraction workbench for a selected client (uses the customer processing workspace) — Cline-acknowledged follow-on.

### P3
- **PR-8 (CL-49)** Role-probe 403 noise (`/ops/me`, `/consultants/me`) on every page (CL-24).
- **PR-9 (CL-50)** D19 "Clear current stage" control missing.
- **PR-10 (CL-51)** 1 legacy snapshot missing `source_item_id` (pre-existing lineage).
- **PR-11 (CL-52)** Reviewer dashboard probes `/api/v3/ops/reporting/audit` → 403 noise (unauthorized probe, cosmetic).

---

## 23. Fixed / verified findings

CL-1, CL-2, CL-3, CL-4, CL-6, CL-7, CL-8, CL-9, CL-10, CL-13, CL-15, CL-16, CL-17, CL-19, CL-22,
ISC-1 (new calcs), ISC-4, ISC-10, UH-1, UH-2, UH-7, G-P0-9, G-P1-4 — all re-verified live at `6148c86`.

---

## 24. Remaining blockers (investor demo)

1. Viewer-upload authorization (PR-1) — a scripted viewer write during a demo breaks the security story.
2. Custom-factor lifecycle (PR-2 + PR-3) — the "create → approve → factor takes precedence" demo arc cannot be completed through the UI.
3. (Minor) Notifications console noise (PR-4) and role-probe/404 log noise (PR-5/PR-8) are visible in DevTools during any UI demo.

---

## 25. Investor-demo readiness

**Not fully ready.** The primary pipeline (customer document → approved emissions → report) and the
consultant/PE operating models now work end-to-end with real persisted data and intact boundaries.
However, the three P1 items above directly obstruct the investor demo script for custom factors and for
role-based security claims. Fixing CL-42 (viewer upload), CL-43 (factor duplicate/version), and CL-44
(mapper factor picker) closes the gaps.

---

## 26. Final acceptance verdict

**NOT ACCEPTED**

The Phase 1 restoration is real and the core pipeline is functional, but the product cannot yet be
accepted as investor-demo ready because: (a) a read-only **viewer can still upload documents** (201),
(b) the **custom-factor lifecycle cannot be completed** through the UI (duplicate create 500; new-version
create impossible; approved factor cannot be picked in mapping), and (c) the notifications surface still
errors on every page. A real customer, consultant, PE operator and staff member CAN now perform the
intended business workflows and produce a real customer-approved emissions result with security
boundaries intact for cross-org/consultant/PE access — but not yet for viewer-write and custom-factor
precedence.

---

## 27. Cline implementation backlog references

New backlog items appended to `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` as **CL-42..CL-52**
(see that file). Existing CL-1..CL-41 preserved with their ids.

---

## 28. Evidence / commands used

- `/tmp/ct_post/harness.py` (`login`, `call`) — API probes (owner/consultant/PE/operator/reviewer/qc/staff/system-admin/viewer).
- `/tmp/ct_post/sweep.mjs`, `sweep2.mjs`, `ops_sweep.mjs`, `cust_admin4.mjs`, `wb_layout3.mjs`, `wb_mobile.mjs` — CDP UI sweeps + layout measurements; outputs in `/tmp/ct_post/*_out.txt`.
- Screenshots: `/tmp/ct_post/shots/{ops_dataentry,ops_workbench,wb_mobile}.png`.
- Read-only psql queries: constraints/indexes (`customer_factors`), snapshot/emissions linkage, queue statuses, `manual_review_queue` rows.
- `git log`/`git diff c36c848 6148c86` (read-only) for the file-change surface.
- Health checks: backend :8050, frontend :3000, supabase auth :54425, ingress :8000 — all 200.

---

## 29. Data safety statement

- No source code, schema, migration, RLS, config, `.env`, or seed data modified.
- No commits, pushes, resets, rebases, or working-tree changes (361 pre-existing dirty files untouched).
- The investor-scale dataset was **not** reset or re-seeded.
- Audit-temporary data created during this audit was removed: the viewer-upload temp object (`fb4cc6a6-…`, deleted via `supabase_admin` with the storage delete trigger disabled) and its `document_processing_queue` row (`d509c6c0-…`); the duplicate-factor probe created **no** row (500). One customer-review approve probe on `a1610bbb-…` was reverted to `calculated` with `customer_*` stamps cleared. All verified gone.
- Any row state changed by prior sessions for legitimate workflow demonstration (e.g. one item moved `calculated → approved`) is part of the demo dataset and was left as-is.

---

## 30. Continuation checkpoint

**Tested (this audit, incl. prior session):** baseline/runtime; 13 personas; customer journey
(org/facilities/assets/vehicles/suppliers/locations/members/custom-factors/documents/processing/
review/approve/emissions/reports); consultant create-customer + switching + isolation; PE batch/workspace
+ no-download; internal staff (operator/reviewer/QC/staff-admin/system-admin); messaging; security
negative matrix; D19 workbench layout + mobile; public website routes; regression vs Cline Phase 1 claims.

**Remaining (unchecked / partial):**
- Mapping UI end-to-end for a **spend (£)** document (no factors exist — blocked by CL-47).
- Report **PDF generation** (no PDF path exercised).
- `qc_checks`/`qc_errors` population (recurring-quality reporting unavailable; Cline noted).
- Standalone routed D19 `/ops/items/{id}` page (future refinement).
- Full `customer_review` legacy table vs new `manual_extraction_items` data migration review.

**Exact next audit steps:**
1. After Cline fixes CL-42/CL-43/CL-44: re-run viewer upload probe (expect 403), duplicate factor create
   (expect 409/422 clean), and mapping picker (expect customer factor selectable) — then re-assess the verdict.
2. Re-run the persona matrix rows marked ⚠/❌ in the Phase-1 re-verification column.
3. Exercise PDF report generation and the PE workbench "Save & continue" through the full stage list.
4. Re-check notifications bell console (expect clean after RealtimeContext fix) and the legacy 404 probe.

**Exact Cline backlog items to implement next:** CL-42 (viewer upload deny), CL-43 (factor duplicate 409
+ `version` in create), CL-44 (mapper factor picker incl. approved customer factors), then CL-45
(RealtimeContext notifications), CL-46 (legacy members 404), CL-47 (spend factor shortcut), CL-48
(consultant workbench), CL-49..CL-52 (polish).

---
*End of audit. No code changes were made.*


# 31. Continuation audit — role workspace, workflow and UI/UX architecture

**Audit mode:** discovery only. No application source, database, schema, migration,
RLS, seed, configuration or credential files were changed. No data was reset or
reseeded. No persistent write was made for this pass. Existing findings and IDs
remain authoritative; this section adds only findings newly reproduced or newly
classified from the workspace-architecture question.

## 31.1 Previous work reused

This pass reused, rather than restarted, the following evidence:

- `CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md` and its security matrix;
- `previous-session/CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` and the
  investor dataset manifest;
- `CARBONTALLY_V3_UI_VISUAL_ACCEPTANCE_AUDIT.md` for D19/D20 workbench and
  responsive findings;
- `CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md` and the actor/workspace
  access model for earlier O-*, E-*, CON-*, MD-*, PRC-*, SEC-* and D-* findings;
- the extraction/mapping/calculation capability audit for the distinction between
  OCR suggestions, human extraction, factor mapping and calculation;
- `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` through CL-52;
- the existing read-only `/tmp/ct_post` API and CDP harness conventions.

The key correction to the previous post-restoration conclusion is that the
**manual end-to-end path is real, but automatic document processing is not**.
The two paths must not be reported as equivalent.

## 31.2 Runtime baseline and personas exercised

The running local stack responded on frontend `:3000`, backend `:8050`, Supabase
Auth `:54425` and Postgres `:54426`. Representative existing identities were
used without creating new accounts:

| Persona | Identity | Runtime result |
|---|---|---|
| Customer owner/admin/member/viewer | `owner.demo0001`, `admin.demo0001`, `member.demo0035`, `viewer.demo0001` | Login and org reads work; member35 `multi_gas.pdf` remains pending |
| Consultant lead | `consultant.demo0001` | 15-client portfolio, active-client switch, reporting and messaging reads work |
| Second consultant | `consultant.demo0002` | Separate portfolio; cross-firm isolation remains denied |
| Internal operator | `operator.demo` | `/ops`, operator queue and manual workbench work; irrelevant tabs still show |
| Internal reviewer | `reviewer.demo` | Review/QC reads work; audit access is correctly denied server-side |
| Internal QC | `qc.demo` | QC queue and workbench read/action surface work |
| Staff admin | `staff-admin.demo` | Internal operations dashboard and management tabs load |
| System admin | `system-admin.demo` | V3 `can_manage_staff`, `can_manage_billing` and `is_superuser` resolve correctly |
| PE manager/staff | `pe-manager-1.demo`, `pe-staff-1.demo` | Entity-scoped workspace works; internal operations and customer org access denied |

## 31.3 Primary verdict — workspace architecture is not yet coherent

**Verdict: PARTIALLY COHERENT, NOT PRODUCTION-READY.**

There are credible server-side boundaries and three recognizable V3 surfaces:
customer routes, `/consultant`, and `/ops`. PE users are conditionally routed to
an entity extraction view. However, the user experience and orchestration do not
match the business model:

1. the customer Processing page is a manual batch/item metadata form, not the
   customer document-to-emissions operating workspace;
2. the consultant surface is a portfolio/reporting console, not a complete client
   operating workspace;
3. the PE workspace is embedded conditionally inside `/ops`, not a separately
   addressable application boundary;
4. internal staff see a shared shell with tabs they cannot use, while a separate
   legacy `/admin` application and legacy API remain deployed beside V3;
5. the public Assistant is mounted globally in the main authenticated application;
6. key tables are unbounded in the UI and the item workspaces are still appended
   below queue/report content for reviewer, QC and PE flows;
7. a document upload can synchronously produce OCR suggestions, but no automatic
   extraction/mapping/calculation job is scheduled.

The backend authorization direction is substantially stronger than the surface
architecture. The recommendation in §31.14 therefore preserves server-side
authorization and shared services while separating route/shell responsibilities.

## 31.4 Customer workspace acceptance

### Customer owner/admin

The owner/admin can log in to `/home`, inspect documents, read processing status,
manage organisation master data, read emissions/reports, use customer messaging,
and approve an already calculated item. Profile/facility/asset/vehicle/supplier
APIs and cross-organisation isolation were rechecked as read paths. Existing
CL-5/CL-18/CL-42 remains open for viewer write semantics and UI affordances.

The customer job is nevertheless not complete from the customer workspace:

- `/documents` uploads to `/api/v3/uploads`, which creates an `organization_files`
  row and a manual-extraction item, but does not present a customer item workspace
  or automatic result;
- `/processing` lists/creates `manual_extraction_batches` and manually adds item
  metadata, but does not offer the full extraction → mapping → validation →
  calculation → evidence workflow;
- the customer review detail calls the staff endpoint
  `/api/v3/ops/items/{item_id}/workspace`, whose backend dependency is
  `require_staff`; the customer review queue is correctly customer-scoped, but
  the detail/workspace contract is not a clean customer-specific service boundary;
- customer tables have no consistent pagination, sorting or page-size model;
- profile, facilities, suppliers and members render write controls without
  passing the resolved customer role into those components. The backend denies
  unauthorized writes, but member/viewer UX discovers this only after clicking.

### Customer member/viewer

Member35’s existing `multi_gas.pdf` is visible in Documents and has OCR text and
suggestions, but its linked manual item is still `pending` with null
`extracted_data`, `mapped_data`, `calculated_emissions_kg_co2e`, `extracted_by`
and `extracted_at`. Viewer and member read isolation works. Viewer upload remains
an existing P1 authorization defect, not a new finding.

## 31.5 Consultant operating-workspace acceptance

The consultant API provides a real firm profile, client grants, client lifecycle,
portfolio metrics, client dashboards, reports, issues and client messaging. The
active-client banner is a useful safety affordance, and consultant 1 versus
consultant 2 isolation was rechecked.

The complete requested consultant workflow is **not available through the UI**:

| Workflow step | Result | Classification |
|---|---|---|
| Login/dashboard | Works | Existing surface |
| Create customer + owner | API `POST /api/v3/consultants/me/customers` exists; no UI entry point | FE gap |
| Manage customer users | No consultant customer-user/member surface | FE + API/model scope gap |
| Manage consultant team | `GET/POST /api/v3/consultants/me/team` exists; no team tab/list/invite UI | FE gap |
| Select active client | Works through localStorage-backed switcher | Deep-link/state limitation |
| Upload for active client | No consultant upload control; customer upload endpoint is member-gated | FE + API integration gap |
| Automatic processing | Not implemented after upload | Workflow orchestration gap |
| Manual extraction/mapping/validation/calculation | No consultant item/workbench route or API client path | FE + API surface gap |
| Review/approval | No consultant review/approval surface; customer approval remains owner/admin | Product/authorization decision required |
| Reporting | Works for authorised client | Existing partial capability |
| Messaging | Client messaging UI exists, but realtime subscription is absent in the component | FE realtime gap |
| Switch/revoke isolation | Server-side active-grant checks hold; active id is client-controlled local state | Security holds; UX/deep-link hardening needed |

This is related to CL-7 and CL-48 but broader: those IDs describe the original
consultant enablement and inline-workbench follow-on. CL-61 below records the
separate team-management UI omission; CL-54 records the customer-facing
workspace contract problem that also prevents consultant reuse.

## 31.6 CarbonTally internal staff acceptance

`/ops` is a genuine V3 internal operations route with server-side permissions,
queues, assignment, review, QC, staff, entity, SLA, issue, audit, settings and
commercial code. It is not merely a customer page with a different title.

It is not yet a coherent staff application:

- operator sees Dashboard, Data entry, Review, QC, Staff and Roles although the
  runtime permission payload only contains `can_process` and `can_view_all`;
- reviewer sees Data entry, Staff and Roles although their payload is
  `can_review` and `can_view_all`; those tabs produce 403s or misleading access;
- Ops dashboard itself calls audit reporting for roles that cannot read it,
  producing the known CL-52 noise;
- the V3 shell still probes `/ops/me`, `/consultants/me` and the legacy member
  endpoint on pages where the result is already known, producing repeated 403/404;
- a separate `admin/` CRA exists with its own router, AuthContext, Layout,
  legacy `/api/admin/*` calls and Vercel rewrite. It is not the same shell or
  permission vocabulary as V3. The two admin experiences are therefore an
  operational split-brain, not one intentional `/admin` control plane.

## 31.7 Processing Entity acceptance

PE manager and PE staff are correctly denied internal `/ops/dashboard`, internal
entity administration, customer organisation access and messaging. Their
entity-specific routes return the entity dashboard, assigned batches, assigned
items, signed view-only source URLs, extraction/mapping/calculation controls and
mediated clarification. The no-download boundary and entity isolation remain
positive controls.

The workspace is still architecturally incomplete:

- `/ops` is the only route; `OperationsPage` detects `profile.entity_id` and
  swaps the child component. There is no stable PE route such as
  `/processing-entity`, no deep link for a batch/item, and no refresh-safe
  selected-item URL;
- `EntityExtractionWorkspace` renders entity performance, batch list, item list,
  clarification and the ExtractionPanel in one long document. Selecting an item
  does not navigate to a dedicated workspace or preserve list state;
- PE batch rows show mainly `batch_name` and status. The payload contains
  organisation IDs but the UI does not expose customer organisation, consultant,
  document count, progress, assignment or SLA context;
- the current dataset has PE work, but no PE item has a complete live
  entity-side extraction → mapping → validation → review → QC → CarbonTally
  secondary-gate demonstration in this pass. The product decision remains that
  PE QC is followed by CarbonTally validation/review/QC and customer approval.

## 31.8 Automatic document-processing deep audit

### Reproduction

For `member.demo0035@demo.carbontally.local`, the existing `multi_gas.pdf` record
was read from the investor dataset:

- document: `organization_files.id=52011222-6080-4c36-84c7-1c0d479de98f`;
- file type: PDF, two pages, 10,030 bytes;
- document status: `uploaded`;
- OCR metadata: `status=ok`, `method=pdf_text`, full text persisted;
- deterministic suggestion output: only `date` and `activity=Electricity`, with
  unresolved `invoice_number`, `quantity/unit` and `supplier`;
- linked item: `manual_extraction_items.id=44b0d3cf-fd7e-4292-9cbc-d9809a783043`;
- item status: `pending`;
- extracted/mapped/calculated fields: all null;
- linked batch: `Uploads`, five items, four pending and one validated;
- customer review queue: empty;
- emissions created from this document: none.

Waiting and rereading did not advance the item.

### Exact stop point and root cause

The V3 upload handler performs these synchronous steps:

1. upload bytes to private Supabase Storage;
2. insert `organization_files`;
3. create/reuse an `Uploads` manual-extraction batch;
4. create a pending `manual_extraction_items` row;
5. run best-effort local PDF/image text extraction and deterministic suggestions;
6. persist OCR metadata only.

It does **not** call an extraction engine that writes confirmed
`manual_extraction_items.extracted_data`, does not call factor matching, does not
call validation, does not call calculation, and does not create emissions/evidence
from the upload. The in-process `EventBus` and `WorkflowOrchestrator` exist as
engine/test infrastructure, but `backend/main.py` startup only logs startup and
does not register or run a persistent document-processing worker. The upload
comments explicitly describe OCR suggestions as human-review prefill and leave
the item pending for manual entry.

Therefore automatic processing is **not implemented as an asynchronous worker**,
not merely delayed, and not blocked by `multi_gas.pdf` being a PDF. OCR is
implemented as a best-effort preprocessing aid; the business pipeline after OCR
is manual and operator-driven. The public website must not describe this path as
automatic end-to-end processing until a worker/job contract exists.

Consultant upload for a client could not be exercised because the UI has no upload
control and the available customer upload endpoint requires organisation
membership. The existing consultant client reporting endpoints are read/status
only. This is an API-surface/integration gap, not evidence of a failed worker.

## 31.9 Operations queue audit

The operator queue currently returned 51 batches. Representative rows showed
`batch_name=Uploads`, no SLA deadline, and a separate organisation object with a
human-readable name. Progress was available as counts, but the rendered table
showed only:

`Batch | Status | Progress | action`

The operator can technically inspect the organisation after opening a batch, but
cannot answer the operational question from the queue row itself: “which
organisation, customer/consultant relationship and N documents am I processing?”
The default name is generated by the upload handler for every upload batch, so it
is a storage/ingestion label rather than a work-order name. This is a scalability
and operational-context defect, not a tenant-isolation defect.

Minimum required queue context for production is: organisation name; customer
contact or account label where permitted; consultant firm/name where applicable;
batch name; document/item count; stage/status progress; source (customer,
consultant, CarbonTally or PE); assigned PE/operator; priority; created/updated
at; SLA/deadline; and error/blocked indicator. Exact consultant disclosure rules
remain a Product Owner decision.

## 31.10 Global table inventory

Controls are assessed against investor-scale counts, not against whether a small
fixture happens to fit in one viewport. “Required” means needed for a growing
production dataset; “optional” means useful but not a launch blocker for a small
reference list.

| Table/surface | Pagination | Sorting | Filtering | Search | Page size | Useful columns | Status / scale classification |
|---|---|---|---|---|---|---|---|
| Documents | API limit/offset; UI none | fixed newest | API status only; UI none | shell search only | no selector | lacks processing/extraction/mapping/calculation/emissions status | **P2 required; CL-54/CL-58** |
| Upload batches | API list; UI none | fixed created | none | none | none | batch, status, item count, dates; no owner/source/SLA in customer view | **P2 required** |
| Batch items | API list; UI none | fixed | none | none | none | file, status, type; no status breakdown/errors | **P2 required** |
| Customer review | DataTable, no paging controls | fixed | none | none | none | item, status, emissions, reviewed; adequate for tiny queue | **P2 required at scale** |
| Internal operations queue | API returns all queue batches; UI none | fixed | status argument unused in UI | none | none | generic `Uploads`; missing work context | **P1/P2 required; CL-57** |
| PE queue/batches/items | API list; UI none | fixed | optional status API | none | none | missing customer/source/assignment/SLA context | **P2 required; CL-59** |
| Issues | customer API limit/offset exists; UI none | fixed newest | status select only | shell search only | none | details show raw related batch UUID | **P2 required** |
| Facilities | unbounded list | fixed | none | none | none | useful basic columns; acceptable small master data | **Optional now; required at larger tenant scale** |
| Assets | unbounded list | fixed | none | none | none | useful columns; facility name now joined | **Optional now; required at scale** |
| Vehicles | unbounded list | fixed | none | none | none | useful columns | **Optional now; required at scale** |
| Suppliers | API limit/offset; UI no paging | fixed name | status | name/contact | no selector | useful columns; only active list by default path | **P2 required at scale** |
| Locations | unbounded facilities projection | fixed | type select | none | none | useful location columns | **Optional now; required at scale** |
| Custom factors | unbounded list | fixed | none | none | none | factor/activity/value/year/status | **P2 required; duplicate/version defects remain CL-43/44** |
| Customer members/invitations | unbounded list | fixed | none | user-id input only | none | email/role/status/joined | **P2 required for large orgs; role affordance issue existing CL-18** |
| Consultant clients | unbounded list | fixed | no status filter UI | none | none | client/status/aggregate counts | **P2 required; portfolio grows beyond viewport** |
| Consultant team | no UI table | n/a | n/a | n/a | n/a | capability absent | **P1/P2 required; CL-61** |
| Reports | API limit/offset; UI none | fixed created | status/type/year | none | none | report/period/status/creator | **P2 required at scale** |
| Emissions history | API limit/offset | fixed date | API period | none | none | date/activity/scope/kg/factor | **P2 required at scale** |
| Audit logs | UI page/offset 50 | fixed occurrence | action/resource/actor | actor is select from current page | fixed 50 | raw entity UUID remains | **Mostly implemented; page-size/search optional** |
| Messaging/conversations | API limit/offset; UI none | fixed last message | none | none | none | subject/count/status | **P2 required at scale; CL-64** |
| Messages in thread | API limit/offset; UI fixed scroll | fixed created | none | none | none | sender currently raw UUID | **P2 required** |
| Notifications | API limit/offset; UI none | fixed newest | unread checkbox | none | none | title/message/date | **Existing CL-45 partial** |
| Staff roster | API limit/offset exists in legacy route; V3 UI none | fixed | no UI | no UI | none | name/email/role/type/active/entity | **P2 required** |
| Staff roles | unbounded read-only | fixed | none | none | none | role/scope/permissions | **Optional reference list; role lifecycle decision required** |
| Processing entities | unbounded list | fixed | none | none | none | name/description/status | **Optional now; required at scale** |
| Commercial plans/orders/ledger | mixed API limits; UI none | fixed | limited status in some calls | none | none | useful finance columns but no table controls | **P2 required for platform operations** |

The common `DataTable` primitive provides accessible markup and empty rows but
provides no sorting, pagination, filtering or page-size behavior. Only audit has
actual UI pagination; reports/issues/suppliers have partial filters or API
parameters. This is a cross-cutting component architecture issue rather than a
request to add every control to every tiny table.

## 31.11 Workspace navigation and deep-link audit

The intended interaction is `list → item route → dedicated workspace → Back to
list`, with browser history, refresh, filters and page state preserved. Current
behaviour is mixed:

- customer review has `/review/:itemId` and a Back button, but it calls the staff
  workspace service and is not a clean customer workspace contract;
- reviewer and QC render the workbench after the queue in the same page and set
  local `activeItemId`; there is no item route, refresh-safe item identity or
  queue-filter state;
- operator collapses the queue and scrolls to top when opening, which is an
  improvement already recorded by UH-1/UH-2, but still does not create a route;
- PE selection is local component state below performance and list panels; no
  route or Back-to-queue state exists;
- consultant client selection is localStorage-backed, so a copied URL cannot
  identify the client workspace and stale localStorage can select an inactive
  client before the server rejects it;
- Previous/Next is available in the shared ExtractionPanel only after the item is
  open and is based on the currently loaded in-memory item list.

Consequences: browser Back does not reliably mean “back to the exact queue”; page
refresh loses the selected item; deep links cannot be safely shared; keyboard and
mobile users must traverse the surrounding list; a long queue remains an
architectural dependency even where the operator view is visually collapsed.
This adds CL-59 for the universal routed workspace contract and does not replace
UH-1/UH-2.

## 31.12 Role and permission matrix

The following is the minimum intended matrix inferred from D5, D17, D19, D22,
D25, N1 and the existing server gates. It is a product baseline for PO
ratification, not an authorization change made by this audit.

| Capability | Customer owner/admin | Customer member | Customer viewer | Consultant owner/lead | Consultant team member | Internal operator | Reviewer | QC | Staff admin | System admin | PE manager | PE staff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| View own org data | yes | yes | yes | granted clients | granted clients | operational | operational | operational | operational | operational | assigned work | assigned work |
| Upload customer document | yes | yes | no | PO-granted client scope | PO-granted scope | assigned/operational | no | if processing | if permitted | if permitted | no customer upload | no customer upload |
| Edit org/master data | yes | no | no | no unless explicit PO scope | no unless explicit scope | no | no | no | no | no | no | no |
| Create/edit/deactivate customer user | yes | no | no | PO decision; not currently surfaced | PO decision | no | no | no | no | no | no | no |
| Assign customer role | yes/admin | no | no | no current surface | no | no | no | no | no | no | no | no |
| Create/modify platform staff user | no | no | no | no | no | no | no | no | yes | yes | no | no |
| Create/modify role definition | no | no | no | no | no | no | no | no | PO decision; legacy admin API only | yes if ratified | no | no |
| Process extraction/mapping | own workflow after proper route | own workflow after proper route | no | PO-granted active client scope | flag-gated | yes if `can_process` | no | yes | yes | yes | yes assigned entity work | yes assigned entity work |
| Validate/review/QC | customer review/approval only | review read | read only | PO decision | PO decision | no/role-specific | review | QC | yes | yes | PE quality chain | PE quality chain |
| Customer final approve | owner/admin | no | no | no unless PO explicitly delegates | no | no | no | no | no | no | no | no |
| Manage billing/commercial config | no | no | no | no | no | no | no | no | PO decision | yes (`can_manage_billing`) | no | no |
| Retention settings | no | no | no | no | no | no | no | no | admin-managed | yes | no | no |
| Audit access | own audit/activity as designed | own activity | own read | firm/client audit as designed | scoped | no | no | no | yes | yes | no internal audit | no internal audit |
| CarbonTally messaging | own org | own org | own org if allowed | granted client | granted scope | staff-admin only | no | no | yes | yes | denied | denied |
| Public Assistant | visitor only | no | no | no | no | no | no | no | no | no | no | no |

Current backend enforcement is generally least-privilege for cross-org, PE and
customer approval boundaries. Current UI enforcement does not consistently match
this matrix, particularly for the shared Ops tabs, customer write controls and
public Assistant mounting.

## 31.13 Retention settings and messaging findings

### Retention

`GET /api/v3/settings/retention` returns HTTP 200 for staff-admin and system-admin
with a persisted-shape payload whose four values are currently `null`. The source
contains an upsert path keyed by `platform_retention`, with non-negative input
validation and reload-compatible fields. A real save/reload was **not executed**
under this audit because it would mutate platform configuration and the task
explicitly prohibits configuration changes. The prior SA-4/retention unknown
therefore remains an unknown, not a verified fix or new defect. A release gate
must execute save → reload → persistence in an isolated test environment.

### Ops Messaging `orgs.map is not a function`

The runtime contract is reproducible without writing data:

- `/api/v3/ops/dashboard` returns `organizations` as an object such as
  `{"total": 975}`, not an array of organisation rows;
- `OpsMessagingTab` assigns `result.organizations` directly to `orgs` and later
  renders `orgs.map(...)` and indexes `result.organizations[0].id`;
- this produces the reported `orgs.map is not a function` failure and prevents
  staff-admin/system-admin from using Ops Messaging.

Customer `/api/v3/messaging/conversations` reads return 200 for an authorised
customer; consultant and PE cross-scope attempts remain 403. `/api/v3/notifications`
returns 200 per user, but `RealtimeContext.jsx` still directly queries the
`notifications` table and emits console errors because that table has no RLS
policies. This is the existing CL-45 partial finding.

The V3 customer and consultant messaging components perform API reads and
send-then-refetch. They do not subscribe to a conversation-specific
`postgres_changes` channel. The RealtimeContext currently handles presence and
legacy notifications, not V3 conversation delivery. Thus “Realtime messaging” is
persisted API messaging plus a separate presence channel in the current UI, not a
verified live customer/consultant conversation experience.

## 31.14 Recommended CarbonTally Application / Workspace Architecture

### Options considered

| Option | Security | Maintainability | Deployment | Shared code/services | UX/investor quality | Assessment |
|---|---|---|---|---|---|---|
| **A. One frontend with role-based shells/routes** | Can be strong if every API/RLS gate remains authoritative; route hiding alone is insufficient | Lowest short-term cost; shared components easy | Simplest single deployment | Maximum sharing | Can feel coherent if shells are genuinely distinct; risks role leakage and legacy coupling | Good transitional shape, not sufficient while legacy/admin and public/auth concerns remain mixed |
| **B. One repository with multiple frontend applications** | Clearer compile-time/runtime boundaries; still depends on server auth | Moderate; shared package/components possible | One repo, multiple deploy targets or path rewrites | High if shared UI/API/auth packages are explicit | Best balance for distinct customer/consultant/staff/PE experiences | **Recommended target** |
| **C. Separate public/customer, consultant, staff/admin and PE applications** | Strongest blast-radius and navigation separation, but duplicated auth/integration/deployment paths can introduce drift | Highest operational cost | Multiple domains/apps and release trains | Lowest unless a disciplined shared service/component layer exists | Strongest visual separation but over-complex for current scale | Future option only if contractual/brand/security needs justify it |

### Recommendation

Adopt **Option B: one repository with multiple frontend applications or app
entry points sharing a common CarbonTally platform package**, delivered in stages:

1. **Public site app** at the canonical marketing domain. It owns marketing,
   pricing, FAQ, glossary, public demos and the deterministic public Assistant.
   It has no authenticated provider, customer data, staff routes or upload code.
2. **Customer app/shell** at the authenticated application domain. It owns
   customer home, documents, processing, review/approval, emissions, reports,
   organisation master data, billing and Realtime messaging. It must use a
   customer-specific workspace service contract, not a staff `/ops` endpoint.
3. **Consultant app/shell** with explicit firm and active-client context in the
   URL/session. It owns portfolio, team, client onboarding, client work queues,
   processing workbench, reports and client messaging. Every client action must
   carry an active grant and be re-authorized server-side.
4. **CarbonTally staff/admin app** at `/admin` or a clearly equivalent control-
   plane entry point. It owns internal queues, assignment, review, QC, staff,
   roles, entities, SLA, issue triage, audit, retention and commercial controls.
   Retire or quarantine the separate legacy admin app only after V3 parity and
   route-by-route dependency verification.
5. **PE app/shell** as a dedicated route/app entry point (for example
   `/processing-entity`) using the same backend services and shared workbench
   package. It must expose only entity-assigned work, signed view-only source,
   mediated clarification and the PE quality workflow. It does not need a
   separate backend or database.
6. **Shared platform package** for Supabase auth/session handling, typed API
   contracts, status badges, DataTable, WorkbenchShell, evidence components and
   accessibility primitives. Shared code must not imply shared navigation or
   shared authorization.

This is the least-complex architecture that provides role-appropriate boundaries
without four independent systems. It avoids choosing a separate domain for PE
before legal, deployment and customer-brand requirements justify that cost.
Separate domains can be added later without changing the backend authorization
model. No client-side role or route decision may grant access; RLS and server
permission checks remain mandatory.

## 31.15 Additional new findings summary

New Cline-ready IDs from this continuation are CL-53 through CL-66. Existing
CL-1..CL-52, ISC-*, UH-*, SEC-*, CON-*, O-*, MD-*, PRC-* and retention unknowns
are preserved and cross-referenced rather than duplicated.

### P0

None newly reproduced in the application. The broader regulatory/transfer P0s in
the independent legal and data-residency audits remain outside this product-UI
classification.

### P1

- **CL-53** customer review detail uses staff-only workspace endpoint;
- **CL-54** customer Processing is metadata-only and has no customer work workspace;
- **CL-56** upload stops at OCR/manual pending item with no automatic pipeline;
- **CL-60** public Assistant is mounted on authenticated routes;
- **CL-63** Ops Messaging crashes on the dashboard `organizations` object shape;
- existing CL-42 viewer upload authorization remains P1.

### P2

- **CL-55** generic customer upload batch/item naming and missing operational
  context;
- **CL-57** internal queue lacks organisation/customer/source/assignment/SLA
  context;
- **CL-58** global table controls and business-status columns are inconsistent;
- **CL-59** reviewer/QC/PE workspaces are not routed/deep-linkable;
- **CL-61** consultant team UI is absent;
- **CL-62** Ops tabs are not filtered by permissions;
- **CL-64** V3 messaging UI does not subscribe to conversation realtime events;
- **CL-65** org search returns 500 on `report_versions.report_name` schema mismatch;
- **CL-66** legacy admin and V3 role/catalog contracts are split-brain.

### P3

Existing CL-45/46/49/50/51/52 and UH-/copy/data-hygiene findings remain the
polish queue. No new P3 ID was created where an existing item already covers the
same symptom.

**Continuation finding counts:** P0 **0**, P1 **5 new** (plus existing CL-42),
P2 **9 new**, P3 **0 new**. These counts exclude preserved prior IDs.

## 31.16 Investor readiness

**Not investor-ready as a complete role/workspace product.**

Investor-positive evidence remains: login routing, org isolation, consultant
portfolio isolation, PE no-download boundary, server-side approval gates,
manual extraction/mapping/calculation path, persisted evidence for new
calculations, public marketing routes and a real internal `/ops` surface.

Investor blockers from this continuation are more fundamental than visual polish:

1. a document advertised or understood as processed can remain only an OCR-backed
   pending upload with no automatic result;
2. the consultant cannot complete the promised operating workflow through the
   consultant UI;
3. PE and reviewer/QC workspaces cannot be reliably deep-linked or returned to;
4. staff messaging fails at render time;
5. staff role navigation presents unauthorized tabs;
6. the public Assistant appears in authenticated staff/customer sessions;
7. the long-queue and unbounded-table model does not demonstrate operational
   readiness at investor-scale counts;
8. search is a global shell control but currently 500s for a normal query.

The product may demonstrate a **manually driven** selected-document happy path,
but it should not claim automatic end-to-end processing, complete consultant
operations or production-grade role-specific applications until CL-53/54/56/60/63
and the dependency chain in §31.18 are accepted.

## 31.17 Evidence index for this continuation

- Source: `frontend/src/App.js` — global `AssistantWidget`, legacy widgets,
  route mounts and V3 shell composition.
- Source: `frontend/src/v3/components/V3Layout.jsx` — shared shell and role probes.
- Source: `frontend/src/v3/consultant/ConsultantPage.jsx` — portfolio/status-only
  client workspace, localStorage active client and absent team/workbench controls.
- Source: `frontend/src/v3/customer/DocumentsPage.jsx`, `ProcessingPage.jsx`,
  `ReviewDetailPage.jsx` — upload/manual forms and staff workspace call.
- Source: `frontend/src/v3/ops/OperationsPage.jsx`, `OperatorQueue.jsx`,
  `ReviewQueue.jsx`, `QcQueue.jsx`, `EntityExtractionWorkspace.jsx` — inline
  queue/workspace patterns and permission-tab behavior.
- Source: `frontend/src/v3/ops/OpsMessagingTab.jsx` — `orgs.map` contract error.
- Source: `frontend/src/context/RealtimeContext.jsx` — direct notifications
  query and absence of V3 conversation subscription.
- Source: `frontend/src/v3/components/ui/DataTable.jsx` — accessible table only,
  with no built-in scale controls.
- Source: `backend/api/v3_documents.py` — upload → storage/file/batch/item/OCR;
  no worker/orchestrator call.
- Source: `backend/main.py`, `backend/infra/event_bus.py`,
  `backend/engines/workflow.py` — process-local infrastructure and absent startup
  registration/worker.
- Runtime: member35 document/item reads, operator queue (51 batches), internal
  `/ops/me` permission payloads, consultant portfolios, PE entity workspace,
  messaging/audit/retention/search probes and `/tmp/ct_post/current_ops_sweep_out.txt`.

## 31.18 Recommended implementation order

1. **CL-56 automatic pipeline decision and implementation contract** — define the
   job/worker, idempotency, status transitions, retry/dead-letter, extraction
   confidence, factor matching, validation, calculation, evidence and customer
   notifications. Do not polish status UI before this contract is real.
2. **CL-53 + CL-54 customer workspace service boundary** — provide a customer-safe
   item workspace and make customer processing a complete, honest workflow.
3. **CL-60 public/authenticated application boundary** — render the public
   Assistant only on public routes and remove legacy authenticated widgets from
   V3 shells.
4. **CL-63 Ops Messaging contract fix**, then CL-64 conversation realtime
   subscription and CL-45 notification migration.
5. **CL-62 permission-filtered staff shell** and CL-66 legacy admin/V3 role
   consolidation. Keep server-side gates unchanged or stricter.
6. **CL-59 routed workspaces** for operator/reviewer/QC/PE with URL state,
   history, Back to Queue, filters and mobile/keyboard behavior.
7. **CL-61 consultant team UI**, followed by CL-54 consultant client
   upload/process/workbench capabilities under active grants.
8. **CL-57 operational queue context** and CL-58 table infrastructure; implement
   shared pagination/filter/sort/page-size patterns only for tables whose counts
   justify them.
9. **CL-65 shell search schema contract** and verify search across documents,
   items, issues, suppliers, facilities, vehicles and reports.
10. Re-run CL-42/43/44/47 plus the complete persona matrix, then perform isolated
    retention save/reload and PDF/report/PE full-chain acceptance.

## 31.19a Top 10 issues Cline should implement next

This list is dependency-ordered, not simply severity-ordered:

1. **CL-56 — automatic processing contract and worker.** Establish the real
   upload → extraction → mapping → validation → calculation → evidence path,
   including retries and honest manual-review states.
2. **CL-54 — customer processing workspace.** Make customer upload/processing a
   complete role-appropriate workflow rather than a metadata-only batch form.
3. **CL-53 — customer-safe review detail endpoint.** Prevent customer review from
   calling a staff-only workspace endpoint.
4. **CL-60 — public/authenticated boundary.** Keep the public Assistant on public
   routes and remove legacy communication widgets from authenticated V3 shells.
5. **CL-63 — Ops Messaging shape contract.** Fix the staff-admin/system-admin
   render crash without widening messaging authorization.
6. **CL-62 — permission-filtered staff navigation.** Present only the queues,
   admin controls and reports each staff role can actually use.
7. **CL-66 — canonical staff/admin application.** Resolve the legacy `/admin`
   versus V3 `/ops` split and consolidate role/catalog authority safely.
8. **CL-59 — routed workspaces.** Give reviewer, QC, operator and PE items
   refresh-safe routes with Back to Queue and preserved filters/page state.
9. **CL-57 + CL-55 — operational queue read model.** Show organisation,
   consultant/source, item/document counts, assignment, priority and SLA using
   human-readable context.
10. **CL-58 + CL-64 + CL-65 — scale and communication foundation.** Standardize
    table controls, add authorized conversation realtime, then repair shell search.

Existing CL-42/43/44/47 remain mandatory in parallel: viewer upload denial and
custom-factor/spend mapping are still investor/security blockers, even though
this new list prioritizes the larger architecture dependencies first.

## 31.19b Final coverage checklist and current open counts

**Newly audited:** customer owner/admin/member/viewer workflow boundary;
consultant portfolio/team/client workflow; internal operator/reviewer/QC/staff
admin/system admin; PE manager/staff; upload/OCR/manual pipeline; operations
queue; customer review/QC/PE workspaces; documents, batches, batch items,
issues, facilities, assets, vehicles, suppliers, locations, factors, members,
clients, reports, emissions, audit, messaging, notifications and commercial
surfaces; public website/authenticated application boundary; deployment rewrites
and role catalogs.

**Screens inspected:** `/home`, `/documents`, `/processing`, `/review`,
`/review/:itemId`, `/organization` (profile, members, facilities/assets,
locations, vehicles, suppliers, factors, activity, security), `/reports`,
`/emissions`, `/issues`, `/messaging`, `/notifications`, `/consultant` (dashboard,
client workspace, branding, white-label, client messages), `/ops` (dashboard,
data entry, review, QC, staff, roles, entities, SLA, issues, messaging, audit,
settings, commercial), PE extraction workspace, public FAQ/glossary/demos and
legacy `/admin` application source/deployment route.

**Current post-restoration open application finding counts** (unique mapped
findings, excluding fixed historical IDs and separate legal/regulatory P0s):
P0 **0**; P1 **8** (CL-42/43/44 plus CL-53/54/56/60/63); P2 **13**
(CL-45/46/47/48 plus CL-55/57/58/59/61/62/64/65/66); P3 **4**
(CL-49/50/51/52). These are not a claim that every older audit item is closed;
they are the current consolidated post-restoration set represented in this
report and backlog.

**Remaining unknowns:** retention save/reload (not run because it mutates
configuration); consultant-team permissions beyond the seeded owner; a real
consultant upload once a safe test route exists; full multi-line automatic
pipeline; PDF report generation; PE end-to-end secondary CarbonTally gate;
Realtime delivery in two live browser sessions; report schema/search migration
compatibility across all deployed environments; and legacy-route retirement
impact. Each is an explicit acceptance dependency, not assumed working.

## 31.19 Data-safety statement and stop condition

- No source, schema, migration, RLS, API, configuration or seed file was changed.
- No commit, push, reset, reseed or destructive command was run.
- No persistent audit test record was created in this continuation.
- Existing investor data, including the existing `multi_gas.pdf` record and prior
  audit-temporary rows, was not reset or cleaned beyond the state already present.
- Retention save was deliberately not executed because configuration mutation was
  prohibited; it remains an explicit isolated-environment acceptance test.

*End of continuation audit. Discovery only; no code or data changes were made.*
