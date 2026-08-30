# CARBONTALLY V3 — PHASE 2 COMPLETION REPORT

**Verdict:** **PHASE 2 — NOT COMPLETE** (several mandatory requirements remain
PARTIAL; see sections 3–12 and the completion matrix).

**Generated:** 2026-08-30 (continuation session) · **Branch:** `main`

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

1. PE Manager distinct role dashboard (F1 enhancement).
2. DataTable rollout to remaining large surfaces (H4/H5: entities, client lists,
   master data, factors, emissions, messaging, notifications).
3. Consultant team revoke/deactivate UI + dedicated consultant evidence view
   (E9/E7).
4. Systematic per-surface error/UX audit (M1/M2) + M4/M5 verification.
5. Full browser E2E of the customer review → approval → report handoff (R3)
   and the full persona acceptance re-pass.


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
  status filter), review queue, QC queue, staff roster. **Still incremental
  (PARTIAL):** entities, client lists, master data, factors, emissions,
  messaging, notifications use the contract but are not yet all wired.
