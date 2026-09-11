# CarbonTally V3 — Independent UI/UX Visual Acceptance Audit

- **Audit type:** READ-ONLY visual / interaction acceptance audit (no code, DB, seed,
  migration, RLS, API, configuration or documentation changes).
- **Date:** 2026-08-28 (session 2026-08-24 context, latest build verified live)
- **Baseline:** `main @ c36c848` (HEAD = origin/main). History: `9458067` (D20–D37 commercial
  platform release — contains WorkbenchShell), `077c866` (admin tabs, custom factors).
- **Harness:** CDP headless Chromium (`/tmp/ct_audit/cdp.js`, port 9333) against the running
  local stack: frontend `http://localhost:3000`, backend `http://localhost:8050`,
  Supabase auth `127.0.0.1:54425`, Postgres `127.0.0.1:54426`.
- **Personas/identities:** investor-scale demo set (`@demo.carbontally.local`, shared local
  password `CarbonTally-Local-Demo-2026!`), per `tools/seed_investor_demo/DEMO_IDENTITIES.md`.
  **No identity was reset or altered.**
- **Authoritative baseline docs:** `docs/audit/openhands/ui-ux/` (MASTER_INDEX,
  MASTER_SCREEN_INVENTORY, MASTER_UI_UX_ASCII_DESIGNS, MASTER_WORKFLOW_MAP,
  MASTER_UX_RECOMMENDATION, UI_UX_IMPLEMENTATION_MATRIX, CARBONTALLY_V3_DESIGN_SYSTEM,
  PRODUCT_OWNER_DECISION_REGISTER_v1, MASTER_UX_DECISION_RECONCILIATION_REPORT,
  IMPLEMENTATION_STATUS_V3_UX_BASELINE).

---

## 1. Executive summary

The V3 application is **substantially further along than the last recorded audit**: the
**D19 split-screen workbench is now really implemented** (WorkbenchShell: top workflow nav
`Queue › Extract › Map › Validate › Review › QC › Evidence`, 40/60·50/50·60/40 pane presets,
autosave "PENDING / Not saved yet" state, source/data tray toggles, validation banner,
claim/save/draft/map/calculate actions, view-only source pane, mobile tray transform).
The **design-token consolidation (G-P0-9)** is also largely done (`v3/tokens.css` is the
single `ct-*` vocabulary; App.css now aliases `--primary: var(--ct-color-primary, #2f855a)`).

**However, the user's primary concern is CONFIRMED.** On the ops **Data entry** surface the
page renders, in order:

1. Top rail (58 px)
2. "Internal Operations" page title
3. **Full 53-row batch queue table — 2,579 px tall**
4. **Batch-items table** (4 items, 227 px)
5. **The D19 workbench — at y ≈ 3,180 px** (its split panes only 487 px tall each)

The canonical design (ASCII E1 → E2) is: **Ops hub = queue** → "open workspace" →
**standalone workbench page** with its own prev/next item navigation. The implementation
instead embeds the workbench at the bottom of one very long queue page, so the operator must
scroll through ~3,100 px of queue table before reaching the primary workspace. On a 390×844
phone the workbench sits at y ≈ 3,243 px. This is the single most important visual-hierarchy
defect found and it applies to the **PE extraction workspace** as well (same page model).

Additional confirmed issues: the reviewer's **Review queue lists 3 legacy seed rows with
synthetic UUIDs that do not exist in the database**, so "Open workspace" fails with
"item not found" (reviewer workflow dead-ends); the **workbench extraction form displays raw
internal placeholder text** ("missing extracted field 'supplier'", "missing quantity", …);
the customer **"Review & approve" route still 500s** (PRC-1 reconfirmed); the **Vehicles tab
errors** ("Action failed — Network error", missing `vehicles` table — CL-4 reconfirmed);
**assets still render raw facility UUIDs** (CL-19 not fixed); **notifications still call the
legacy endpoint** (ISC-6 reconfirmed); and the mobile customer home shows **six stacked stat
cards before any real dashboard content**.

**Headline numbers:** 50+ screens captured across 13 personas at 4 viewports; **no
horizontal overflow anywhere** (390–1440 px); 3 P1 / 4 P2 / 15 P3 findings (incl.
reconfirmations); 14 findings marked RECONFIRMED, 2 marked FIXED-verify, 13 new.

---

## 2. Audit methodology

1. **Read the authoritative UX docs first** (`ui-ux/` set listed above) — no new UX direction
   invented; every judgement below is anchored to D1–D21/N1–N3 and the ASCII designs.
2. **Baseline freeze:** confirmed `git status`/`git log` baseline `c36c848` before testing;
   verified the workbench code exists in `9458067` and admin tabs in `077c866`.
3. **Live capture (primary evidence):** CDP (Chrome DevTools Protocol) against the running
   app. For each persona/route: login → navigate → wait → capture (a) full-page screenshot,
   (b) full-page text, (c) DOM block-layout JSON (tag, class, y-offset, height, first-viewport
   membership). 141 PNGs + 40+ layout JSON files in `/tmp/ct_audit/`.
4. **Viewport control:** `Emulation.setDeviceMetricsOverride` at 1440×900, 1024×768,
   768×1024, 390×844 (mobile UA for 390) with overflow scans.
5. **API cross-checks:** direct curl against `/api/v3/*` and Supabase PostgREST to distinguish
   "UI hiding a working backend" from "backend genuinely broken" (e.g., review-queue
   synthetic rows, member-activity race, customer-review 500).
6. **Console capture:** `Runtime.consoleAPICalled`/`Log` to capture client errors (403 probe
   noise, "Error fetching notifications", network failures).
7. **Reconciliation:** every finding compared against
   `CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md`,
   `CARBONTALLY_V3_CLINE_IMPLEMENTATION_BACKLOG.md` (CL-1..CL-34) and
   `previous-session/CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md` (ISC-1..ISC-16).
   No findings duplicated — existing ones are marked RECONFIRMED or FIXED-verify.
8. **No modifications:** the working tree was NOT touched by this audit (the dirty tree is
   pre-existing Cline/prior-session state; `frontend/src/v3/__tests__/api.test.js` was already
   modified before this session and was not opened/edited).

### Evidence fidelity notes
- Full-page screenshots use `captureBeyondViewport` (the whole page), so block offsets are in
  document coordinates (`top` = y from document top; `vh` = viewport height).
- The ops dashboard needs ~4 s to render aggregates (earlier 2.6 s captures show the loading
  state — not a defect).
- The member-activity card intermittently fails on first paint after login (see UH-5).

---

## 3. Personas tested

| # | Persona | Identity | Surface tested |
|---|---------|----------|----------------|
| 1 | Customer Owner | `owner.demo0001@demo.carbontally.local` (Quayside Energy `bc197ccf-…`) | /home, /documents, /processing, /review, /emissions, /reports, /issues, /billing, /organization (+7 tabs), /messaging, /existing-data, /notifications |
| 2 | Customer Admin | `admin.demo0001@demo.carbontally.local` | shell + org tabs (spot) |
| 3 | Customer Member | `member.demo0001@demo.carbontally.local` | shell + home (spot) |
| 4 | Customer Viewer | viewer demo identity | viewer home/org/documents (re-confirmed read-only) |
| 5 | Consultant | `consultant.demo0001@demo.carbontally.local` | /consultant dashboard, client switch, client workspace, firm branding, white-label, client messages |
| 6 | PE Manager | `pe-manager-1.demo@demo.carbontally.local` | /ops PE landing (extraction workspace) |
| 7 | PE Staff/Operator | `pe-staff-1.demo@…` | /ops PE landing (spot) |
| 8 | Internal Operator | `operator.demo@demo.carbontally.local` | /ops Data entry (queue + D19 workbench), dashboard |
| 9 | Internal Reviewer | `reviewer.demo@demo.carbontally.local` | /ops Review queue, review reporting, open workspace |
| 10 | QC | `qc.demo@demo.carbontally.local` | /ops QC reporting (spot) |
| 11 | Staff Admin | `staff-admin.demo@demo.carbontally.local` | /ops all 13 tabs (Dashboard, Data entry, Review, QC, Staff, Roles, Entities, SLA, Commercial, Issues, Messaging, Audit, Settings) |
| 12 | System Admin | `system-admin.demo@…` | control-plane (403 on audit/billing — ISC-10 reconfirmed via prior audit) |
| 13 | Entity staff | `entity-staff` / PE roles | PE workspace (empty queues — ISC-14) |

---

## 4. Screens / workflows tested

**Customer:** Dashboard, Documents (upload + batches), Processing (batch list + item
expansion), Review & approve (broken 500), Emissions & calculations, Reports (+ exports),
Issues (report + triage), Billing, Organisation (Overview & Settings, Locations,
Facilities & Assets, Vehicles, Suppliers, Members & Invitations, Custom Factors, Activity,
Security), Messaging (conversation list + create), Existing data (discovery), Notifications.

**Consultant:** Consultant dashboard (portfolio KPIs), client list, client context switch
(select), client workspace (banner + stats + processing status), firm branding form,
white-label mode, client messages (permission-gated).

**PE:** PE landing ("Extraction workspace", "Assigned batches" — empty), entity-scoped nav.

**CarbonTally staff:** Ops dashboard (pipeline by stage, platform & quality, queue aging),
Data entry (queue → workbench), Review (reporting + queue + open workspace), QC (reporting +
processor performance), Staff, Roles, Entities, SLA, Commercial, Issues triage, Messaging,
Audit console, Settings (retention N3).

**Admin/control plane:** staff-admin full tab set (Audit, Commercial, Settings, Entities, SLA).

**Responsive:** customer Home + Processing, ops Data entry/workbench at 1440×900, 1024×768,
768×1024, 390×844.

**Total:** 50+ rendered screens, 13 personas, 12+ major workflows.

---

## 5. D19 workbench findings

### What is correctly implemented (verified visually)
- **Top workflow navigation** — `Queue › 2 Extract › 3 Map › 4 Validate › 5 Review › 6 QC › 7
  Evidence` (WorkbenchShell, `frontend/src/v3/components/workbench/WorkbenchShell.jsx`),
  active step highlighted. D19-2 (nav + presets) is now implemented → **FIXED-verify**.
- **Pane presets** — 40/60 · 50/50 · 60/40 buttons rendered and functional (state on shell).
- **Autosave state** — "PENDING — Not saved yet" pill in the shell header.
- **Source ⇄ Data trays** — toggle row "Source / Extraction"; mobile transform
  (`ct-wb-tray--source` confirmed at 390 px).
- **Split panes** — left `ct-pane` = source document viewer ("View only — download disabled
  for this role"), right `ct-pane` = extraction form; pixel probe of the scrolled screenshot
  confirms two distinct panes (page background `#f7fafc`, right pane white surfaces,
  primary-green `#2f855a` action button at right-bottom).
- **Validation banner** — "Validation (7) — resolve the flagged fields before calculation."
- **Workflow controls** — Claim stage · Save extraction · Save draft · Save mapping ·
  Calculate · Previous · Next.
- **No horizontal overflow** at any viewport; reduced-motion + focus-visible respected.

### What is wrong

**UH-1 [P1] — The D19 workbench is buried ~3,100 px below the full batch queue (NEW).**
- **Persona:** Operator / PE staff / Reviewer / QC.
- **Route/screen:** `/ops` → Data entry (and the same page model on PE "Extraction workspace").
- **Workflow:** Queue → Extract → Map → Validate → Review → QC → Evidence.
- **Current behaviour:** opening a batch then an item renders the WorkbenchShell **at the
  bottom of the same page**, after the complete 53-batch queue table (y=250, h=2,579) and the
  batch-items table (y=2,879). Workbench top at y≈3,180 (desktop full-page 1440×2000) and
  y≈3,243 at 390×844. `fullyVisible:false` at a 1913 px capture height.
- **Expected behaviour (canonical E1→E2):** the queue is the **hub**; opening an item
  navigates to a **standalone workbench** whose own header shows `← prev · item i/n · next →`.
  No 2,579-px queue above the primary workspace.
- **Evidence:** `visaudit/wb_workbench.json` (block map above), `shots/wb_workbench.png`,
  `shots/wb_focused_scrolled.png`, `visaudit/responsive/*.json`, ASCII E1/E2.
- **UX principle/decision violated:** D19 (top workflow nav + split-screen workbench);
  ASCII E2 "NEXT STATE: workbench"; D18 (the workbench is the primary workspace for the job).
- **Severity:** P1 (the flagship D19 pattern exists but is effectively hidden below a legacy
  table wall).
- **Recommended fix:** split the ops Data-entry surface into two destinations: **Batch queue**
  (list + open) and **Item workbench** (route-level, opened from the queue, with its own
  prev/next). Alternative minimal fix: when an item is open, collapse the batch queue to a
  compact summary/collapsed panel above the workbench and auto-scroll to the workbench.
- **Acceptance criteria:** after clicking "Open" on an item, the workbench is the first
  meaningful element in the viewport (top ≤ 200 px below the rail), queue visible only as a
  collapsed/collapsible summary; prev/next navigates between items without re-scrolling.
- **Regression test:** route `/ops/data-entry` → open item → assert `document.querySelector(
  '.ct-wb')` bounding top < 400 px and queue table not taller than the viewport when
  collapsed; repeat at 390 px.

**UH-2 [P2] — Queue table is visually dominant over the workbench (NEW, related to UH-1).**
- **Persona:** Operator / PE staff.
- **Current behaviour:** a single `.v3-ops-table` of 53 batches is 2,579 px tall — more than
  5× the workbench panes (487 px each). Batches each render an inline "Progress" bar and an
  "Open"/"Upload" control, which compounds the height.
- **Expected:** queue rows are compact (or paginated) when they coexist with an open
  workbench; the workbench is the dominant visual mass.
- **Evidence:** `visaudit/wb_workbench.json`; `shots/wb_ops_queue.png`.
- **Table/log audit (see §7):** the 53-batch table is *primary* for the "find my batch" job
  but should be a separate screen; on the workbench it is secondary and should be collapsed.
- **Severity:** P2. **Fix:** paginate/collapse per UH-1. **Acceptance:** queue ≤ ~400 px when
  an item is open. **Regression:** screenshot-diff the Data-entry page.

**UH-4 [P3] — Workbench extraction form shows raw technical placeholders (NEW).**
- **Persona:** Operator / PE staff.
- **Route/screen:** workbench extraction pane.
- **Current behaviour:** fields render the internal fixture/absence message as visible field
  content: `missing extracted field 'supplier'`, `missing extracted field 'date'`,
  `missing extracted field 'activity'`, `missing quantity`, `missing unit` (item
  `Waste_2025-01.pdf`).
- **Expected:** an empty field with a muted human hint ("No value extracted — enter
  manually"), not an internal key name.
- **Evidence:** `visaudit/wb_workbench.json` (full text), `shots/wb_workbench.png`.
- **UX principle:** "debug information exposed to normal users" (§6 legacy list); D21 copy.
- **Severity:** P3. **Fix:** map absence to a friendly empty-state label. **Acceptance:** no
  string containing "missing extracted field" or "missing " appears in any field. **Regression:**
  open the same item and assert field placeholder text.

**UH-6 [P3] — Raw staff UUIDs in ops Review queue "ASSIGNED" column (NEW).**
- **Persona:** Reviewer / QC / staff-admin.
- **Route/screen:** `/ops` Review tab (review queue table).
- **Current behaviour:** `ASSIGNED` column shows `76793ebb-7e8e-4a04-8a05-6d62a474a15f` instead
  of "Reviewer One" (the same row is summarised by name in the "Reviewer workload" card above).
- **Expected:** staff display name (matches CL-19 pattern for asset facilities).
- **Severity:** P3. **Fix:** join/display `staff_profiles.display_name`. **Acceptance:**
  ASSIGNED shows a name for every seeded staff. **Regression:** review queue smoke.

**UH-7 [P2] — Reviewer "Open workspace" fails: "item not found" — the review queue lists
non-existent legacy seed rows (NEW, functional).**
- **Persona:** Reviewer / QC.
- **Route/screen:** `/ops` Review queue → "Open workspace".
- **Current behaviour:** the queue returns 3 items with synthetic UUIDs
  (`78222222-2222-4222-8222-222222222222`, org `11111111-1111-4111-8111-111111111111`, batch
  `76222222-…`) that **do not exist** in `manual_extraction_items`/`manual_review_queue`/
  `organizations` (verified via PostgREST: empty). Clicking "Open workspace" → backend 404
  "item not found" → page shows "item not found". Root cause: rows came from the legacy
  `local_backups/seed_demo_data.sql` fixture.
- **Expected:** the review queue lists only rows that resolve to a real item+document; opening
  one renders the review workbench (or a clean "no items assigned" empty state).
- **Evidence:** `visaudit/review_workspace.json`, `shots/review_workspace.png`, API probes.
- **UX principle:** D19/D6 quality chain must be traversable; legacy data must not surface.
- **Severity:** P2 (reviewer workflow dead-ends in the demo).
- **Fix (Cline):** clean the orphan `manual_review_queue` rows (data hygiene) **or** make the
  queue filter to rows with a resolvable `item_id`; regression: reviewer opens a seeded item
  successfully. **PO decision:** none required (D6/D19 already define the queue contract).

---

## 6. Visual-hierarchy findings (per-screen A–F)

> Method: for each screen, primary job (A), primary workspace (B), dominance (C), what is
> above the workspace (D), what pushes the workspace down (E), first-viewport action (F).

| Screen | A (primary job) | B (workspace) | C dominant? | D above | E pushes down | F first viewport |
|---|---|---|---|---|---|---|
| **Customer Home** | See emissions status & act | Reporting overview card | Yes on desktop (report card 330 px under 2×3 stat cards) | 6 stat cards, cookie banner | stat cards + 330 px reporting card + trend card | 1440: stats + reporting overview visible; **390: only 6 stacked stat cards (510 px)** — UH-3 |
| **Customer Documents** | Upload & browse evidence | Upload form + Documents table | Yes | — | — | Upload form + docs table both visible |
| **Customer Processing** | Monitor batches/items | Batch table (expandable items) | Yes | — | — | Batch table visible; expandable |
| **Customer Review & approve** | Review calculated items | (broken) | n/a | n/a | n/a | 500 → error card (PRC-1) |
| **Customer Emissions** | Run authoritative calc | Calculate form + history | Yes | — | — | Form visible; history below |
| **Customer Reports** | Export/generate reports | Stats + generate card | Yes | — | — | visible |
| **Customer Organisation** | Maintain master data | Tabbed master-data panels | Yes | profile block | — | profile form visible |
| **Customer Messaging** | Talk to consultant | Conversation list | Yes | — | — | visible (2 convos) |
| **Consultant** | Manage clients | Client workspace | Yes after switch | dashboard stats | default active client = Dover (non-managed) → **permission dead-end on fresh login** (CON-6) | stats + warning banner |
| **Ops Dashboard** | See pipeline health | KPI cards + aging | Yes (loads ~4 s) | — | slow aggregates | visible after load |
| **Ops Data entry** | Extract/map items | **D19 workbench** | **NO** | **53-row queue table (2,579 px) + items table** | **queue wall (UH-1/UH-2)** | only the queue |
| **Ops Review** | Review items | Review queue + workbench | NO (queue + reporting) | reporting cards + workload table + issues | queue rows | reporting cards; queue below |
| **Ops QC** | QC reporting | QC stats | Yes | — | — | visible |
| **PE Extraction workspace** | Entity extraction | workbench | NO | "Assigned batches" empty state | (empty dataset — ISC-14) | empty state |

**UH-3 [P3] — Mobile customer home: six stacked stat cards fill the first viewport (NEW).**
- At 390×844 the 6 `.v3-stat-card`s stack vertically (each 85 px, w=350) occupying y=153–663
  (plus header y=82). "Reporting overview" — the real dashboard content — starts at y≈755,
  below the fold. The first screen is just numbers: `0 0 5 4 0 0.00`.
- **Fix:** responsive stat grid (2×3 on mobile) or collapse stats behind a summary; move
  "Reporting overview" ahead of the stats on small screens. **Acceptance:** at 390 px the
  Reporting overview title is within the first viewport. **Regression:** 390 px capture of
  /home asserting `h2` "Reporting overview" `top < 844`.

**UH-5 [P3] — "Activity by member" card intermittently shows "Network error" on first paint
(NEW).**
- The member-activity request fires right after login; on some first renders it fails with
  "Failed to fetch" and the card renders `Network error — please check your connection and try
  again.`; a subsequent reload succeeds (API verified 200 via curl). See §2 fidelity note.
- **Fix:** retry-once on 0-status network errors or await auth/org context before firing.
  **Severity:** P3. **Acceptance:** first paint of /home after login always renders the
  activity table (or a neutral "Activity loading" that resolves). **Regression:** 5× fresh
  login → /home at 3 s.

**UH-10 [P3] — Customer batch items include OHD test artifacts (NEW).**
- Quayside Energy's "Uploads" batch lists three `ohd_test.txt` rows (`pending`, type "—").
  Test artefacts from a previous OHD run are visible to a customer org.
- **Fix:** remove the `ohd_test.txt` uploads from the demo dataset (data hygiene, not code).
  **Severity:** P3. **Acceptance:** no `ohd_test`-named rows in customer-visible batches.

**UH-11 [P3] — Header/nav copy inconsistencies persist (RECONFIRMED — CL-21 partial).**
- Nav "Home" vs h1 "Dashboard"; nav "Messaging" vs h1 "Messages"; nav "Organisation" (UK)
  vs route `/organization` (US). CL-21 fixed the nav label only.
- **Fix:** align h1s and route names to D18 copy. **Severity:** P3.

**UH-12 [P3] — Demo entities list: four "Babui" rows + entities named "A"/"B" (NEW).**
- `ops_entities` shows `Babui` ×4 and `A`, `B`. Seed-quality noise in a staff surface.
  **Fix:** seed cleanup (renaming). **Severity:** P3.

---

## 7. Table / log audit

| Table/log | Intended user | Decision supported | Needed here? | Primary/secondary | Move below workbench? | Collapse/drawer/remove? | Duplicates? |
|---|---|---|---|---|---|---|---|
| **Ops Data-entry batch queue (53 rows)** | Operator | Choose the batch to work | Yes — but not on the same page as the workbench | Primary on queue screen; **secondary on workbench page** | **Yes (UH-1/UH-2)** | Collapse when an item is open | No |
| Batch items table (4 rows) | Operator | Pick the item | Yes | Secondary | Yes (above workbench) | Merge into workbench prev/next | Partially — workbench header also shows the item |
| Ops Review queue (3) | Reviewer | Pick item to review | Yes | Primary | n/a | n/a | Yes — "Reviewer workload" card above repeats the same reviewer/assignment info (UH-6) |
| Ops Dashboard stat cards (BATCHES/ITEMS/%COMPLETE/…) + Pipeline by stage + Platform & quality | staff-admin | At-a-glance health | Yes | Primary | n/a | n/a | PARTIAL — "Pipeline by stage" and "Platform & quality → ITEMS COMPLETE 37.5%" both derive from the same data; acceptable as two views, but 3 card rows before the queue-aging table |
| Review reporting cards (PENDING/IN REVIEW/COMPLETED/SLA BREACHED) | Reviewer | Queue health | Yes | Primary | n/a | n/a | No |
| Issues triage table (ops) | staff-admin | Route issues | Yes | Primary | n/a | n/a | No |
| Audit console (ops Audit) | staff-admin | Forensics | Yes | Primary | n/a | n/a | No |
| Customer docs table | Owner | Browse evidence | Yes | Primary | n/a | n/a | No |
| Customer batch items (expandable) | Owner | Monitor progress | Yes | Secondary (expandable — good) | n/a | Already collapsed by default — **good pattern** | No |
| Activity by member (home + org) | Owner | See member contributions | Yes | Secondary | n/a | Could collapse on mobile | **Yes** — duplicated between /home card and /organization Activity tab (acceptable: different context, but note it) |

**Net:** the only *harmful* table placement is the 53-batch queue above the D19 workbench
(UH-1/UH-2). Everything else is defensible; none of the "remove" options are recommended
because the data supports a real operational decision.

---

## 8. Legacy UI detection

| Finding | Evidence | Classification |
|---|---|---|
| **Queue table above the workbench on the same page** | `wb_workbench.json` | **Architectural conflict** (D19 E1→E2 says queue hub → workbench page) — UH-1 |
| **Review queue lists legacy `seed_demo_data.sql` rows** (fake 1111/2222 UUIDs, non-existent org/items) | API probes + `local_backups/seed_demo_data.sql` | **Legacy data surviving in V3 surface** — UH-7 |
| **Raw UUIDs in staff UI** (ASSIGNED in review queue; FACILITY in assets) | screenshots | Technical IDs where names should appear (CL-19 + UH-6) |
| **"missing extracted field 'x'" placeholders in workbench form** | workbench text | Debug information exposed to normal users — UH-4 |
| **"qc_errors is not populated by the current workflow; recurring-quality identification is NOT SUPPORTED"** | ops QC reporting | Technical limitation surfaced as prose — UH-8 |
| Notifications bell calls legacy `/api/notifications` → "Error fetching notifications: Object" | console | Legacy endpoint in V3 UI — **RECONFIRMED (ISC-6/CL-11)** |
| Consultant/customer pages fire `/ops/me` + `/consultants/me` probes that 403 on every load (console noise) | console | Duplicated role probing — **RECONFIRMED (CL-24)** |
| Cookie banner overlays bottom of every surface | screenshots | Intentional/acceptable (compliance); overlaps content at 390 px |
| "CarbonTally Assistant" bubble on every surface | screenshots | Intentional (N1 assistant); acceptable |
| Ops dashboard shows `© 202` (year truncated in captured text — cosmetic) | text dumps | Visual clutter (P3, may be a render artifact of capture) |

**UH-8 [P3]** — QC surface limitation prose (above). **Fix:** reword as a product note or
implement; **Acceptance:** no "NOT SUPPORTED" strings in staff UI.

**UH-9 [P3]** — Ops dashboard first render shows "Loading dashboard…" for ~2.6–4 s (aggregate
queries); acceptable but should show the queue-aging table first (it is the only fast part).
Not a defect — noted for polish.

---

## 9. Responsive findings

Tested 1440×900, 1024×768, 768×1024, 390×844 on /home, /processing, and the ops workbench.

- **No horizontal overflow** at any viewport (`scrollWidth == innerWidth` everywhere) — good.
- **Workbench mobile trays work:** `ct-wb-tray--source` + "Source / Extraction" toggle at
  390 px. **But** the workbench is at y≈3,243 (behind the queue wall, UH-1) so trays are only
  reachable after a huge scroll.
- **Customer home 390:** UH-3 (six stacked stat cards above real content).
- **Customer processing 390:** batch table renders wider than the viewport but is clipped by a
  container (no doc-level overflow); the table is not horizontally scrollable within the card
  (last column may be clipped) — verify during the Cline pass.
- **Navigation at 390:** 12 customer nav items wrap to a multi-line rail (tall header);
  acceptable but pushes content down ~75 px more than desktop.
- **Sticky/fixed:** nav rail fixed; cookie banner fixed at bottom (overlaps content at 390 —
  content scrolls under it); no other fixed elements.
- **Scrolling:** single vertical scroll; workbench fully scrollable (no internal scroll traps).

---

## 10. Design-system findings

- **Tokens consolidated (G-P0-9 FIXED — verify current implementation):** `v3/tokens.css`
  defines the full `ct-*` vocabulary (colours, typography, spacing, radii, shadows,
  breakpoints, z-index); App.css aliases `--primary: var(--ct-color-primary, #2f855a)`; both
  surfaces share `#0f172a` nav, `#2f855a` primary, `#52b788` light, `#2b6cb0` accent,
  `#1a202c` text. Dual-green history documented in the file header.
- **Residual:** `#2d6a4f` survives in 3 decorative gradient rules in App.css (lines 1344,
  1353, 1362) — P3 cleanup.
- **Computed styles verified:** h1 24 px/700 `#1a202c`; h2 16 px/600; secondary button white
  with `1px solid #cbd5e0`, radius 6 px; table header 12 px uppercase `#718096` on `#f7fafc`;
  status badge pill radius 999 px `#fed7d7`/`#9b2c2c`; nav `#0f172a`, nav tag `#2f855a`.
  Consistent across customer/ops/consultant probes — matches D21.1–D21.9.
- **Status colour not the only signal:** text labels + icons accompany colour (D21.4) — good.
- **Accessibility:** focus-visible ring + reduced-motion in tokens.css; heading hierarchy OK
  (prior a11y fixes held); no horizontal overflow (D21.3). Keyboard divider control for the
  workbench panes is still absent (part of D19-2 remainder).
- **Conclusion:** design system is in good shape; only P3 residuals.

---

## 11. Investor-demo findings

For each persona: "can I immediately understand this screen?" / "can I see the main workflow?" /
"is the important work visually prominent?"

| Persona | Understand? | See workflow? | Important work prominent? | Verdict |
|---|---|---|---|---|
| Customer owner | Yes — Home/Processing/Documents all self-explanatory | Yes up to mapping; **Review & approve 500s** (PRC-1); emissions history empty (ISC-3); reverse lookup broken (ISC-1) | Yes on desktop; No on mobile (UH-3) | **Demo-blocked** at the handoff step |
| Consultant | Yes | Manage-only (CON-1..3); fresh login lands on a permission dead-end (default client not managed — CON-6) | No — the first thing seen is the dead-end workspace | **Demo-blocked** until a managed default client is configured |
| PE | Yes ("Extraction workspace") | Empty queues (ISC-14 — dataset has no PE-assigned batches) | n/a (empty) | **Demo-blocked** (data, not code) |
| Internal operator | Yes | **Only after scrolling 3,100 px** past the queue (UH-1) | No — the workbench is hidden below a table wall | **Demo-blocked** for the flagship workbench moment |
| Reviewer | Yes | **Review queue rows are phantom** (UH-7) — open workspace fails | No | **Demo-blocked** |
| staff-admin | Yes | Dashboard → tabs all render with real aggregates | Yes | Good |

**Investor blockers:** UH-1 (workbench below queue), UH-7 (phantom review items), PRC-1
(customer review 500), CON-6 (consultant default dead-end), ISC-14 (no PE work), ISC-1
(evidence chain invisible). The upload→extract→map→validate→approve→calculate→evidence
journey is **not yet continuously demonstrable in the UI**.

---

## 12. Functional-vs-visual classification

| Category | Findings |
|---|---|
| **Functional defects (backend or wiring)** | PRC-1 (review 500), UH-7 (phantom review rows), ISC-6 (legacy notifications), CL-4 (vehicles 500), MSG-1 (conversation create 500), ISC-1 (source_item_id NULL), ISC-2 (blocking issues never closed) |
| **Functional defects (frontend)** | CON-6 (consultant default dead-end), ISC-9 (mapping dead-end spend), CL-2/CL-3 (calculate/unit alias), CL-8 (system_admin 403) |
| **Visual hierarchy (placement/dominance)** | **UH-1, UH-2** (workbench below queue), **UH-3** (mobile stats wall) |
| **Visual/copy quality** | UH-4 (placeholder strings), UH-5 (network-error race), UH-6 (UUIDs), UH-8 (limitation prose), UH-9 (slow first paint), UH-11 (h1/nav copy) |
| **Data/demo hygiene** | UH-7 (legacy rows), UH-10 (ohd_test.txt), UH-12 (Babui dupes), CL-22 (stray role), ISC-14 (no PE work) |
| **Correct today** | D19 shell (nav/presets/trays/autosave/actions), design tokens, no overflow, org admin tabs (incl. Activity — G-P1-4 FIXED), consultant branding/whitelabel, ops admin control plane (Audit/Commercial/Retention), locations N2 |

---

## 13. P0/P1/P2/P3 findings

### P0 (must fix before any external demo) — none new
No P0 defects were found in this visual pass. (Existing P1s stand; no new security/P0.)

### P1
| ID | Title | Reconciled with |
|----|-------|-----------------|
| **UH-1** | D19 workbench buried ~3,100 px below the full batch queue (Data entry + PE) | NEW (extends D19-2 which is otherwise FIXED) |
| **PRC-1** | Customer "Review & approve" queue 500 → "Network error" | **RECONFIRMED** (CL-1) |
| **ISC-1** | Document→emissions reverse lookup broken (`source_item_id` NULL) | RECONFIRMED (existing) |

### P2
| ID | Title | Reconciled with |
|----|-------|-----------------|
| **UH-2** | Queue table visually dominates the workbench | NEW (component of UH-1) |
| **UH-7** | Reviewer "Open workspace" → "item not found" (phantom legacy review rows) | NEW |
| **ISC-2** | Blocking validation issues never closed on approval | RECONFIRMED (existing) |
| **ISC-9** | Mapping dead-ends for spend activities (`factors: []`) | RECONFIRMED (existing) |

### P3
| ID | Title | Reconciled with |
|----|-------|-----------------|
| **UH-3** | Mobile home: six stacked stat cards before content | NEW |
| **UH-4** | Workbench fields show "missing extracted field '…'" | NEW |
| **UH-5** | Member-activity card "Network error" on first paint (race) | NEW |
| **UH-6** | Review queue shows raw staff UUIDs | NEW (same pattern as CL-19) |
| **UH-8** | QC surface "…NOT SUPPORTED" limitation prose | NEW |
| **UH-9** | Ops dashboard slow first paint (~2.6–4 s) | NEW (polish) |
| **UH-10** | Customer batch items include `ohd_test.txt` artefacts | NEW |
| **UH-11** | h1/nav copy mismatches (Home/Dashboard, Messaging/Messages) | RECONFIRMED (CL-21 partial) |
| **UH-12** | Duplicate "Babui" entities + A/B names in ops Entities | NEW |
| **CL-4** | Vehicles tab errors (missing `vehicles` table) | RECONFIRMED |
| **CL-19** | Asset list renders facility UUIDs | RECONFIRMED |
| **ISC-6/CL-11** | Notifications bell → legacy endpoint error | RECONFIRMED |
| **ISC-3** | Emissions history lacks activity/factor | RECONFIRMED |
| **ISC-4** | Asset create 500 on missing facility; facility UUID | RECONFIRMED |
| **ISC-7** | Locations tab new facilities show Inactive | RECONFIRMED |

**Totals: P1 = 3 (1 new + 2 reconfirmed) · P2 = 4 (2 new + 2 reconfirmed) · P3 = 15 (8 new +
7 reconfirmed).**

---

## 14. Screenshot / evidence index

All evidence in `/tmp/ct_audit/` (temporary; deleted after session): 141 PNGs
(`shots/*.png`), layout JSON (`visaudit/*.json`, `visaudit/responsive/*.json`), scripts
(`cdp.js`, `vis_audit.mjs`, `wb_audit.mjs`, `wb_scroll.mjs`, `dash_check.mjs`,
`responsive.mjs`, `design_check.mjs`, `review_wb.mjs`, `home_check.mjs`, `proc_expand.mjs`,
`consultant2/3.mjs`, `org_tabs.mjs`).

Key evidence files:
- **Workbench + queue wall:** `shots/wb_workbench.png`, `shots/wb_focused_scrolled.png`,
  `shots/wb_mobile_390.png`, `visaudit/wb_workbench.json`, `visaudit/responsive/*.json`
- **Review phantom rows:** `shots/review_workspace.png`, `visaudit/review_workspace.json`
- **OPS admin plane:** `shots/ops_{dashboard,commercial,audit,settings,entities,sla,issues,
  qc}.png`
- **Customer:** `shots/{home,documents,processing,review,emissions,reports,issues,billing,
  organization,messaging,existing-data,notifications}.png`,
  `shots/resp_home_*.png`, `shots/resp_processing_*.png`
- **Consultant:** `shots/c_{dashboard,workspace_granite,branding_granite,messaging_granite,
  whitelabel}.png`
- **PE:** `shots/pe_dashboard.png`, `shots/pe_workspace.png`
- **Design system:** `visaudit/ds_{customer,ops,consultant}.json`

---

## 15. Cline-ready implementation backlog (new/updated entries)

> Existing CL-1..CL-34 remain as the backlog baseline. This audit adds/updates the following.
> Reconciliation against `CLINE_IMPLEMENTATION_BACKLOG.md` was performed — no duplicates.

- **CL-35 (P1) — D19 workbench placement: split "Batch queue" and "Item workbench" into
  separate surfaces** (ops Data entry + PE extraction workspace). Queue becomes the hub
  (E1); opening an item navigates to the workbench page (E2) with prev/next. Minimal
  alternative: collapse the queue when an item is open + auto-scroll. Acceptance: workbench
  top ≤ ~200 px below rail after opening an item, at 1440 and 390. Regression: layout
  assertion per UH-1. No PO decision needed (D19/E2 ASCII is authoritative).
- **CL-36 (P2) — Review queue data hygiene + name resolution.** Delete/repair the legacy
  `manual_review_queue` rows pointing at non-existent items/orgs (from
  `local_backups/seed_demo_data.sql`); make the queue join to `staff_profiles` for the
  ASSIGNED name; "Open workspace" must resolve or show a clean empty state. Acceptance:
  reviewer can open a real item; no 1111/2222 UUIDs in the UI. Regression: UH-7 scenario.
- **CL-37 (P3) — Workbench empty-field placeholders.** Replace "missing extracted field
  'x'" / "missing quantity" / "missing unit" with a muted human empty-state label.
  Acceptance: no internal key strings in the extraction pane.
- **CL-38 (P3) — Mobile customer home stat grid.** 2-column stat grid ≤ 640 px; move
  "Reporting overview" above the stats on mobile. Acceptance: overview h2 in first viewport
  at 390 px.
- **CL-39 (P3) — Member-activity retry.** Retry once on network-status 0 before rendering
  the error. Acceptance: 5 consecutive fresh logins render the activity table.
- **CL-40 (P3) — Demo data hygiene.** Remove `ohd_test.txt` rows from customer-visible
  batches (UH-10); dedupe/rename the four "Babui" entities and "A"/"B" (UH-12); remove
  `#2d6a4f` gradient residuals (App.css 1344/1353/1362); reword the QC "NOT SUPPORTED" note
  (UH-8).
- **CL-41 (P3) — Copy consistency.** h1 "Dashboard"→"Home", h1 "Messages"→"Messaging"
  (align with D18 nav); keep /organization route but surface UK spelling consistently.

---

## 16. Items already correct (verified this session)

- D19 workbench shell: workflow nav, pane presets, autosave state, tray toggles, validation
  banner, view-only source, claim/save/draft/map/calculate/prev/next.
- Design-token consolidation (tokens.css; App.css aliases) — G-P0-9 FIXED-verify.
- Org administration: Overview/Settings, Locations (N2), Facilities & Assets, Suppliers,
  Members & Invitations, Custom Factors, **Activity (G-P1-4 FIXED-verify)**, Security all
  render with real data.
- Consultant: client switch works (native select), workspace with explicit
  "You are working on: <client>" isolation banner, firm branding form, white-label mode,
  client messages surface.
- Ops control plane: Dashboard (real aggregates), Staff/Roles/Entities/SLA/Commercial/
  Issues/Messaging/**Audit console/Settings (retention N3)** all functional for staff-admin.
- No horizontal overflow at any viewport; responsive trays; focus-visible + reduced-motion.
- Customer journeys: Home stats, Documents upload, Processing monitor+expand, Emissions
  calculate form, Reports exports, Issues report, Messaging list, Existing-data discovery,
  Notifications empty state — all render.
- Reviewer/QC reporting cards render real aggregates (workload, processor performance).

## 17. Items requiring no change

- Customer/ops nav rail (12 items) — additive items are intentional; no legacy sidebar exists.
- Cookie banner (compliant; keep).
- CarbonTally Assistant bubble (N1; keep).
- Ops dashboard layout (cards + pipeline + aging) — acceptable as a monitoring surface.
- Customer batch table with expandable items (good pattern to copy into the queue fix).
- Org Locations reuse of facilities (N2 engineering decision).

## 18. Items requiring Product Owner decision

- **D-CON-1 (carried):** consultant write-scope (create customer/upload/process/map) —
  needed before CL-7.
- **CF-1 (carried):** single-owner custom-factor approval (CL-17).
- **Review queue contract:** whether the review queue should include `qc_approved`→
  `customer_review` items only, or all statuses — affects CL-36 and the phantom-row fix.
- **Mobile stat-card treatment** (UH-3): collapse vs reorder — recommend reorder, but the PO
  may prefer collapse for "at-a-glance".

## 19. Recommended implementation order

1. **P1 workbench placement (CL-35 + UH-1/UH-2)** — the flagship D19 pattern must be the
   first thing an operator sees after opening an item.
2. **P1 review 500 (CL-1/PRC-1)** and **P1 evidence chain (ISC-1)** — unblock the customer
   handoff.
3. **P2 review-queue hygiene (CL-36/UH-7)** — unblock the reviewer path.
4. **P1 consultant (CL-7)** after D-CON-1.
5. **P2 mapping dead-end (ISC-9)** + **calculate/unit (CL-2/CL-3)** — make the pipeline
   produce results.
6. **P3 polish batch (CL-37..CL-41, CL-19, CL-4, ISC-3/4/6/7, CL-11, CL-24).**

## 20. Final readiness assessment

- **Design system:** ready (only P3 residuals).
- **D19 workbench:** implemented and correct in *content*, but **not presentable** while
  buried under the queue wall (UH-1) — the single most impactful fix.
- **Customer journey:** demonstrable up to upload/extract/monitor; **not** past review/approve
  (PRC-1) or into evidence (ISC-1).
- **Consultant journey:** demonstrable as manage-only with a manual client switch; default
  landing is a dead-end (CON-6).
- **PE journey:** structurally present; no data (ISC-14).
- **Internal ops:** dashboard/review/QC/admin control plane largely work; reviewer
  item-open fails (UH-7); operator must scroll 3,100 px to the workbench (UH-1).
- **Overall:** **NOT yet investor-demo ready end-to-end.** The UI is coherent and
  design-consistent, but the primary workbench is visually hidden, the review path dead-ends,
  and the customer handoff 500s. A focused Cline cycle on CL-35/CL-1/ISC-1/CL-36 plus the P3
  polish batch would bring the demo to a presentable state. **No P0, no security regressions
  observed; all findings are implementation-gap or polish, not architecture-level.**

---

## Appendix — environment limitations

- The running dataset is the investor-scale seed (Cline-created, not reset per instructions).
  Several findings (UH-7, UH-10, UH-12, ISC-14) are dataset-state issues, not code.
- Ops dashboard renders in ~4 s; captures <3 s show loading (documented, not a defect).
- `psql` was unavailable (auth prompt); DB checks used Supabase PostgREST with persona tokens
  (RLS-respecting) — sufficient to prove the phantom-row finding.
- The customer Review page error is a connection-level failure (backend crash), so the UI
  shows "Network error" rather than the friendlier 5xx copy; CL-12's friendly-error mapping
  only helps when a response body exists.
- OHD org/report detail from prior sessions was not re-captured (accounts are prior-session
  artefacts); report-detail evidence is carried from the investor-scale audit.
