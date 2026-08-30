# CARBONTALLY V3 — PHASE 2 COMPLETION REPORT

**Verdict:** **PHASE 2 — NOT COMPLETE** (several mandatory requirements remain
PARTIAL or PO-gated; see sections 3–12 and the completion matrix). The final
close-out session (below) completed the remaining implementation items,
**live-verified the full customer pipeline end-to-end**, fixed three P1 defects
found by that E2E, and re-verified the persona/security boundaries — but the
PO decisions (queue disclosure, legacy admin retirement, QC authority,
retention scheduling) and the remaining incremental/UX work mean Phase 2
cannot yet be certified COMPLETE.

**Generated:** 2026-08-30 (close-out session) · **Branch:** `main`

## 0. Close-out session (2026-08-30) — delivered

New commits since the prior report (`1b55ad6`):

| Commit | Scope |
|---|---|
| `fc05f05` | PE Manager distinct role dashboard (F1), consultant team revoke/deactivate (E9), consultant evidence view (E7) |
| `d494999` | Entities catalogue server-side pagination (H4) |
| `17db17d` | **P1 fix** — blocking validation 500'd on issues FK violation (batch_id/work_item_id wrote into FK columns referencing other tables) |
| `78718bb` | **P1 fix** — multi-line validation ignored the documented item-level factor contract (mapped item could never pass validation) |
| `899706d` | **P1 fix** — customer `/calculate` lacked D23 multi-line support (422 on multi-line items); shared ops line-calculation + item-level factor fallback |
| `8041001` | DataTable rollout remainder (H4/H5): emissions history server pagination + facilities/assets/suppliers |

**Customer E2E (item 6) — COMPLETE and live-verified:** on the Quayside org,
upload `CT-E2E-20260830.csv` → auto-extract → auto-map (customer Diesel factor)
→ validate → start calculation → calculate (**1881.31 kg CO₂e**, snapshot +
`emissions_logs` row persisted with `source_item_id`) → customer approve
(`approved: true`) → emissions history lists the row. All QA records were then
**cleaned up and verified** (item, snapshot, log, 5 E2E issues, queue row,
organisation file, storage object); the shared demo "Uploads" batch and its 7
legitimate items were left intact.

**Security/persona regression sweep (live, 13 checks) — ALL PASS:**
cross-org customer isolation (emissions/documents/batches 403), viewer upload
deny (403), consultant cross-firm client access across context/evidence/
documents/dashboard (403) + own-client positives (200), PE cross-entity
batches/performance (403) + own-entity positives (200), PE → customer data
(403), staff → customer surface (403), staff/internal positives (200).

**Test totals:** backend unit suite **1202 passing / 0 failing** (baseline 1177);
frontend **131 passing** (one suite fails to load on a pre-existing
`react-router-dom` module-resolution issue, unrelated to this session).

## 1. Starting baseline

- **Start of continuation:** HEAD `58285e6` (previous Phase 2 report; Phases A–C
  + D/E-partial committed).
- **End of continuation:** HEAD `1b55ad6` — 6 new commits:

| Commit | Scope |
|---|---|
| `6b4d749` | Phase E — consultant operational workspace (CON-2/3/6/7) |
| `85eb074` | Phase F/G — PE routed item workspace (G5) |
| `60e2ab9` | Phase H/I — review/QC pagination + operator status filter |
| `dc931a3` | Phase K — retention persistence fix |
| `d632afc` | Phase L — search result navigation deep-links |
| `5fa19d0` | Phase 2 completion matrix update |
| `1b55ad6` | Phase H — staff roster pagination |

## 2. Requirement completion matrix

Full matrix (D–M + reporting + factor + security) lives at
`docs/cline/CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md`. Summary:

| Phase | Complete | Partial | Not implemented |
|---|---|---|---|
| D — Communication | D1–D4, D6, D8 | D5, D7 | — |
| E — Consultant | E1, E2, E10, E11, E12 | E3, E7, E8, E9 | E4/E5/E6 were the big gap → **now implemented** (upload+processing+routed workspace) |
| F — PE | F2–F6 | F1 | — |
| G — Workspaces | G1–G3, G4, G5 | — | — |
| H — Tables | H1, H2, H3 (review/QC/operator), H4-staff | H4 (entities/clients/messaging), H5 | — |
| I — Ops queue | I2 (status filter) | I1 (org+items done; consultant/SLA pending) | I3 (search), I4 (SLA) — PO-gated |
| J — Master data | J1, J2 (live-verified) | J3–J5 | — |
| K — Retention | K1, K2 (fixed+verified), K3 | — | — |
| L — Search | L1, L2, L3 | — | — |
| M — Error/UX | M3 | M1, M2, M4, M5 | — |
| Reporting/PDF | R1, R2 (verified), R3 (handoff unblocked) | R3 live E2E | — |
| Factor lifecycle | FCT1, FCT2 | — | — |
| Security | S1 (suites pass; no P0) | — | — |


## 3. Phase E status

**Consultant now has a genuine operational workspace (the central Phase E gap).**

- **CON-2 (upload)** — `POST /api/v3/consultants/clients/{id}/documents`: active
  grant + firm ownership + `can_upload_documents` enforced server-side; reuses
  the shared durable pipeline. **Live-verified:** upload 201 → item created →
  **automatic processing advanced it to `extracted`** server-side.
- **CON-3 (processing)** — `GET /clients/{id}/processing/items` (org context +
  stage filter) and a routed `/consultant/items/:clientId/:itemId` workspace
  using the shared ExtractionPanel over the consultant-authorized
  `/api/v3/processing/*` surface (extract → map → validate → calculate).
- **CON-6** — never land on an unmanaged active client (auto-select first
  managed client). **CON-7** — CO₂e business formatting.
- **Team (E9)** — roster + add (manage_team) exist; **revoke/deactivate member
  UI is still missing** (PARTIAL).
- **Evidence view (E7)** — the consultant sees item status via the processing
  pipeline; a dedicated consultant evidence-trail view is still PARTIAL.

## 4. Phase F status

- **PE Staff (F2/F3/F4/F6)** — entity-scoped workspace persists; isolation and
  the D20 no-download boundary hold (verified). PE calculation from the UI works
  (start('calculation') then calculate).
- **PE Manager (F1/F5)** — `pe_manager` role now resolves `can_process` +
  `can_review` + `can_view_all`; the entity workspace shows assigned batches,
  entity performance (workload, SLA, quality, staff table). **Live-verified** the
  manager reads their entity batches (200, total=1) and a foreign entity id is
  403. A *distinct* manager dashboard (role-specific view) is the remaining
  enhancement (PARTIAL).
- **G5** — PE items open in a dedicated routed workspace
  `/pe/items/:entityId/:itemId` with Back-to-entity, Previous/Next, and the
  mediated-clarification control.

## 5. Phase G status

## 7. Phase I status

- Operator queue rows expose **Organisation + Items + Status** context (I1
  PO-free subset) with server-side pagination and a **status filter** (I2).
- **PO-gated remainder (I1/I3/I4):** consultant/source/PE-assignment/SLA columns
  and queue search require Product Owner disclosure sign-off (backlog CL-55/57
  explicitly flag this). Not implemented pending that decision.

## 8. Phase J status

- **Live-verified:** facility create without postcode → clean 422 (was a raw DB
  500); with postcode → 201; vehicle create → 201; delete → 204. QA records
  cleaned up (0 remaining in DB; storage matched 0).
- Facility edit/delete endpoints exist; assets/suppliers CRUD + per-role gates
  are present and covered by the existing unit suites (J3–J5 PARTIAL until the
  full per-role live matrix is re-run).

## 9. Phase K status

- **Retention persistence was BROKEN and is now fixed:** `PUT
  /api/v3/settings/retention` 500'd with `null value in column
  "setting_value"` — the upsert never supplied the NOT NULL
  `system_settings.setting_value`. Now stores a JSON snapshot alongside the
  columns.
- **Live-verified full round-trip:** GET → PUT 200 → GET-after persists → DB row
  shows the value + `setting_value` set → negative durations still 422.
- Regression tests added (update round-trip + negative validation).
- System Admin (`system_admin` ∈ `ADMIN_ROLE_NAMES`) can configure retention
  (K3).

## 10. Phase L status

- CL-65 search 500 fixed (reports query on `report_generation_queue`).
- Boundaries: org-scoped endpoint, consultants/PE denied server-side.
- **L3 result navigation:** the nav SearchBox deep-links results — item results
  now open the routed `/processing/:id` workspace (improved this session).

## 11. Phase M status

## 13. Security verification

- **No P0 issue.** Cross-org, cross-client, cross-firm, PE-boundary and role-gate
  negative tests pass (security suites run individually; the 236-failure combined
  run was a **environment artifact** — system Python lacking pytest-asyncio, not a
  code regression; the venv run passes **1177**).
- New surfaces server-enforced: consultant upload (cross-firm 403, permission
  403), consultant processing-items (cross-firm 403), PE item workspace (foreign
  entity 403), retention (admin-only).
- No RLS bypasses; no secrets in code; demo credentials never committed.

## 14. Automated tests

- **Backend unit suite: 1177 passed** (start of continuation: 1171; +4 consultant
  tests, +2 retention tests).
- **Frontend v3 suite: 131 passed** (9 suites).
- **Frontend build:** `react-scripts build` OK (pre-existing legacy warnings).

## 15. Live verification

- Consultant upload → durable pipeline → `extracted` (201/200).
- PE manager entity batches 200 (total=1); foreign entity 403.
- Customer-review queue 200 (handoff unblocked).
- Report → completed → PDF 200 (application/pdf).
- Facility/vehicle CRUD 422/201/204 (clean errors).
- Retention PUT→GET→DB round-trip (200 + persisted value).
- Org search 200 (no 500); notifications 200; org selector 200/403 staff gate.

## 16. Database/migration changes

- **No schema migration added.** The Phase K fix is a repository-level INSERT
  correction (setting_value supplied). The `conversation_participants` unique
  index (MSG-1) was applied in a prior session (present in the running DB).

## 17. Files changed

Backend: `api/v3_documents.py`, `api/v3_consultants.py`, `api/v3_operations.py`,
`api/v3_qc.py`, `data/settings.py`, `tests/unit/api/fakes.py`,
`tests/unit/api/test_v3_consultants.py`, `tests/unit/api/test_v3_settings.py`.
Frontend: `App.js`, `v3/api.js`, `v3/components/SearchBox.jsx`,
`v3/consultant/ConsultantItemPage.jsx` (new), `v3/consultant/ConsultantPage.jsx`,
`v3/consultant/NewCustomerView.jsx` (new), `v3/consultant/ConsultantTeamTab.jsx`
(new), `v3/ops/PEEntityItemPage.jsx` (new), `v3/ops/EntityExtractionWorkspace.jsx`,
`v3/ops/OperatorQueue.jsx`, `v3/ops/ReviewQueue.jsx`, `v3/ops/QcQueue.jsx`,
`v3/ops/StaffRoster.jsx`.
Docs: `docs/cline/CARBONTALLY_V3_PHASE2_COMPLETION_MATRIX.md` (new),
`docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` (prior session).

## 18. Commits

`55410d9` (prior), `a0194a9` (prior), `5d35603` (prior), `4e2c3e3` (prior),
`4491103` (prior), `58285e6` (prior) then this session: `6b4d749`, `85eb074`,
`60e2ab9`, `dc931a3`, `d632afc`, `5fa19d0`, `1b55ad6`.

## 19. Remaining PO decisions

1. **Queue disclosure columns** (CL-55/57) — consultant/source/PE-assignment/SLA
   columns and queue search in internal queues (PO disclosure sign-off).
2. **Legacy admin retirement** (CL-66) — approve the deprecation plan after the
   dependency inventory.
3. **QC authority** — dedicated QC permission vs global-admin gate.
4. **Retention enforcement schedule** — retention is configurable and consumed
   server-side; the enforcement scheduler invocation is a deployment decision.

## 20. Remaining technical work

Completed this close-out session (was open in the prior report):

1. ✅ PE Manager distinct role dashboard (F1) — `PEManagerDashboard` with entity
   overview, team workload, SLA/quality, batch status distribution + "Open item
   work" switch (ops `/ops` routes `pe_manager` role to it unless `?view=work`).
2. ✅ DataTable rollout remainder — **emissions history** now uses the shared
   DataTable with real server pagination (`/api/v3/exports/emissions.json`
   honours limit/offset/total; the silent `slice(0, 25)` cap is gone) and the
   **admin facilities/assets/suppliers** master-data tables were converted to
   the shared DataTable (D21 consistency). Consultant client lists remain
   bounded per-firm (14–15 in demo) and are intentionally not paginated.
3. ✅ Consultant team revoke/deactivate (E9) + dedicated consultant evidence
   view (E7) — deactivate/reactivate endpoints (manage_team-gated, cross-firm
   404, audit trail; `require_consultant` rejects inactive members server-side)
   with UI controls; evidence reuses the emissions-snapshot contract.
4. ✅ Systematic error/UX audit (M1/M2) — performed per surface: `v3Fetch`
   surfaces the backend's friendly error envelope with quiet role probes; every
   checked surface has LoadingState/ErrorState/EmptyState; expected failures
   return 4xx; no raw technical errors reach the UI.
5. ✅ Customer E2E (item 6) — upload → extraction → mapping → validation →
   calculation → customer approval → emissions row, **live-verified
   end-to-end** (see §0). R3 report handoff browser E2E remains the final
   acceptance step (report generation itself is live-verified).

Remaining (incremental / PO-gated):

1. **R3 full browser E2E** of customer review → approval → report handoff.
2. Messaging + notifications DataTable adoption (bounded lists today).
3. M4 (CAL-3 reference endpoint) and M5 (mapping-options quality) final
   verification.
4. Legacy admin retirement, queue disclosure columns, QC authority, retention
   scheduling — all **PO decisions required** (§19).


- Quiet role probes (M3) done; v3Fetch surfaces human-readable errors and most
  surfaces use LoadingState/ErrorState/EmptyState (M1/M2 PARTIAL — a
  systematic per-surface audit remains).
- M4 (CAL-3 reference endpoint) and M5 (mapping-options quality) remain PARTIAL
  (the reference endpoint was not re-verified as broken this session).

## 12. Reporting/PDF status

- **Live-verified:** report create → status **completed** → PDF download **200,
  `application/pdf`, 5,933 bytes** (real persisted data; no fake values).
- R3 (customer review → approval → report handoff) is **unblocked** — the
  customer-review queue returns 200 (was 500). Full browser E2E of the handoff
  remains the final acceptance step.


- **Routed workspaces complete for all five surfaces:**
  customer `/processing/:id` + `/review/:id`, consultant
  `/consultant/items/:clientId/:itemId`, internal `/ops/items/:id`,
  `/ops/review/:id`, `/ops/qc/:id`, PE `/pe/items/:entityId/:itemId`. All have
  Back-to-list, Previous/Next, deep links, refresh-safe state.

## 6. Phase H status

- **Shared DataTable contract** (total/limit/offset + sort) implemented.
- **Server-side pagination rolled out to:** operator queue (org + items columns,
  status filter), review queue, QC queue, staff roster, **entities catalogue
  (H4)**, and **emissions history (H5)** — the JSON history surface now honours
  limit/offset/total (previously a silent 25-row UI cap). **Admin master data
  (facilities/assets/suppliers) converted to the shared DataTable** for D21
  consistency (bounded per-org, client mode). Consultant client lists remain
  bounded per-firm and are intentionally not paginated. Messaging + notifications
  remain bounded lists (follow-on, low priority).
