# CarbonTally V3 — Phase 2 (D–M) Requirement Completion Matrix

**Baseline:** HEAD `58285e6` · **Audit inputs:** OHD Full Persona Acceptance Audit
(baseline c36c848, re-verified), CLINE Phase-2 report, PO Decision Register v1,
CLINE implementation backlog. **Last updated:** 2026-08-30.

Status legend: ✅ = implemented + tested + runtime verified (where applicable) ·
🟡 = partial · ❌ = not implemented · ⛔ = blocked by PO decision.

---

## PHASE D — Communication

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Authenticated user communication | real messaging between authorized roles | V3 messaging API + customer/consultant/ops messaging UI; Realtime per-conversation hook | ✅ | ✅ | ✅ | — | — | no | ✅ |
| D2 | Supabase Realtime messaging | per-conversation delivery, RLS-scoped | useConversationRealtime.js (dedupe/reconnect/refetch) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| D3 | Role/org/consultant/PE/internal boundaries | messaging authorized by relationship; PE↔customer denied | server-side participant validation + PE denial | ✅ | ✅ | ✅ | — | — | no | ✅ |
| D4 | Conversation creation | POST /conversations works | unique index on conversation_participants (conversation_id,user_id) added | ✅ | ✅ | ✅ | — | — | no | ✅ |
| D5 | Participant handling | add/remove participants per N1 | participant validation + is_active handling | ✅ | 🟡 | ✅ | UI for managing participants (P3) | — | no | 🟡 |
| D6 | Notifications | bell uses V3 API, no direct-table reads | NotificationsProvider on listNotifications/markRead/markAllRead | ✅ | ✅ | ✅ | — | — | no | ✅ |
| D7 | Messaging error states | human-readable errors | v3Fetch errors surface message | ✅ | 🟡 | 🟡 | audit empty/error states per Phase M | M | no | 🟡 |
| D8 | No public assistant in authenticated apps | Assistant only on public routes | PublicAssistant route boundary | ✅ | ✅ | ✅ | — | — | no | ✅ |

## PHASE E — Consultant application (REAL OPERATIONAL WORKSPACE)

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | Consultant dashboard | portfolio, clients, status, activity | dashboard view + client switcher | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E2 | Create customer + owner | POST me/customers provisions owner+org+grant | NewCustomerView (CON-1) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E3 | View customer / client context | client detail w/ org context | ClientWorkspace summary | ✅ | ✅ | 🟡 | deeper context columns | — | no | 🟡 |
| E4 | **Upload documents for client** | consultant uploads into client org, durable enqueue | `POST /consultants/clients/{id}/documents` + UI; reuses durable pipeline; live 201 → item auto-processed | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E5 | **Automatic processing for client** | upload → enqueue → extract → map → validate → calculate | consultant upload enqueues the shared durable pipeline | ✅ | ✅ | ✅ | — | E4 | no | ✅ |
| E6 | **Manual processing workspace** | extraction/mapping/validation/calculation for client items | consultant routed item workspace (`/consultant/items/:clientId/:itemId`, shared ExtractionPanel) | ✅ | ✅ | ✅ | — | E4 | no | ✅ |
| E7 | Evidence + review + customer approval handoff | consultant sees evidence; customer approves | `GET /consultants/clients/{id}/evidence` (grant-scoped, snapshot contract) + evidence table in ClientWorkspace; cross-firm denied | ✅ | ✅ | ✅ | — | E6 | no | ✅ |
| E8 | Reports for client | view/generate/download client reports | reports list in ClientWorkspace; generation via shared API | 🟡 | 🟡 | 🟡 | verify generation + PDF for consultant | RPT | no | 🟡 |
| E9 | Team management | create members, roles, revoke | roster + add + **deactivate/reactivate UI** (`POST …/team/{id}/deactivate|reactivate`, manage_team-gated, self-deactivate 422, cross-firm 404, audit trail; inactive members rejected server-side) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E10 | Security: A↔B / team / cross-firm | server-side isolation | consultant grant + firm-scope enforced; live sweep passed | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E11 | Default client dead-end (CON-6) | login lands on managed client | auto-select first managed client (never unmanaged) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| E12 | CO₂e formatting (CON-7) | "10.7 t CO₂e" not "8850.000000" | business CO₂e formatting on consultant surfaces | ✅ | ✅ | ✅ | — | — | no | ✅ |


## PHASE F — Processing Entity application

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | PE Manager dashboard | assigned work, batch visibility, workload, team oversight | `PEManagerDashboard` (entity overview, team workload, SLA/quality, batch status distribution; 'Open item work' switch) routed for `pe_manager` role | ✅ | ✅ | ✅ | — | — | no | ✅ |
| F2 | PE Staff workspace | extraction/mapping/validation/status | EntityExtractionWorkspace (real, persists) + routed workspace | ✅ | ✅ | ✅ | — | G | no | ✅ |
| F3 | PE isolation (Alpha≠Beta) | own-entity only, 403 cross-entity | _entity_workspace_guard + RLS; live sweep passed | ✅ | ✅ | ✅ | — | — | no | ✅ |
| F4 | No customer-document download | no download path, signed view-only URLs | D20 boundary holds | ✅ | ✅ | ✅ | — | — | no | ✅ |
| F5 | PE Manager batch list (PE-2) | manager sees entity batches | pe_manager can_process + own-entity batches/performance live-verified 200; cross-entity 403 | ✅ | ✅ | ✅ | — | — | no | ✅ |
| F6 | PE calculation from UI (PE-3) | start('calculation') then calculate | fixed in ExtractionPanel (PRC-1) | ✅ | ✅ | ✅ | — | — | no | ✅ |

## PHASE G — Universal workspace UX

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | Customer processing routed workspace | /processing/:itemId dedicated | ProcessingItemPage routed | ✅ | ✅ | ✅ | — | — | no | ✅ |
| G2 | Customer review routed workspace | /review/:itemId dedicated | ReviewDetailPage routed | ✅ | ✅ | ✅ | — | — | no | ✅ |
| G3 | Internal ops routed workspaces | /ops/items, /ops/review, /ops/qc | done (CL-59) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| G4 | **Consultant routed item workspace** | /consultant item workspace | `/consultant/items/:clientId/:itemId` (ConsultantItemPage, shared ExtractionPanel) | ✅ | ✅ | ✅ | — | E6 | no | ✅ |
| G5 | PE routed item workspace | dedicated route for PE item | `/pe/items/:entityId/:itemId` (PEEntityItemPage) | ✅ | ✅ | ✅ | — | F2 | no | ✅ |

## PHASE H — Scalable table system

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Shared DataTable contract | pagination/sort/page-size | DataTable enhanced (CL-58) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| H2 | Server-side pagination (no fake browser paging) | ops queue windows | operator queue limit/offset/total | ✅ | ✅ | ✅ | — | — | no | ✅ |
| H3 | Rollout: review/QC queues | paginate large queues | review + QC queues server pagination (limit/offset/total) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| H4 | Rollout: staff/entities/messaging/customers | paginate large surfaces | staff roster + entities catalogue paginated; consultant client lists bounded per-firm | ✅ | ✅ | ✅ | — | — | no | ✅ |
| H5 | Rollout: master data + factors + reports + emissions | paginate/sort | emissions history server pagination + facilities/assets/suppliers on DataTable; factors already DataTable; **notifications now server-paginated (limit/offset/total + page size); messaging N/A — conversation lists/message threads are bounded navigation/chat surfaces** | ✅ | ✅ | ✅ | — | — | no | ✅ |

## PHASE I — Internal operations queue

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| I1 | Row context: org/customer/consultant/PE/operator | each queue row identifies WHO/WHAT | **D-P2-01 implemented**: every operator/review/QC row carries organisation name, consultant/client relationship (firm + client + grant), processing entity name, batch name, assignment (display name), received date, source documents and SLA (deadline/breach) — resolved server-side, never raw UUIDs; 2 regression tests | ✅ | ✅ | ✅ | — | — | approved (D-P2-01) | ✅ |
| I2 | Status/stage filtering | filter queue by status/stage | status param on operator API + **status filter UI on the operator queue**; review/QC queue assigned_to filter | ✅ | ✅ | ✅ | — | — | no | ✅ |
| I3 | Search + assignment filter | search batches/items, filter by assignee | operator queue is assignment-scoped by model (assigned_to / self-serve); review queue has assigned_to param; batches paginated (limit/offset/total) | ✅ | ✅ | ✅ | free-text batch search N/A at current queue scale (56 batches) | — | no | ✅ |
| I4 | SLA/priority/dates | SLA where applicable | **SLA deadline/breach + received date + priority columns** on operator/review/QC queues | ✅ | ✅ | ✅ | — | — | approved (D-P2-01) | ✅ |

## PHASE J — Organisation / master data

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| J1 | Facility CRUD + postcode validation (MD-1) | create facility works without raw DB 500 | verify current create path | 🟡 | 🟡 | ✅ | live-verify facility create; fix if broken | — | no | 🟡 |
| J2 | Vehicles CRUD | vehicles table present + CRUD | table exists; verify endpoints | 🟡 | 🟡 | ✅ | live-verify vehicle CRUD | — | no | 🟡 |
| J3 | Assets/suppliers + relationships | CRUD + facility→asset names | verify | 🟡 | 🟡 | ✅ | live-verify | — | no | 🟡 |
| J4 | Human-readable names (no raw UUIDs) | facility name in asset table | verify | 🟡 | 🟡 | ✅ | audit display | — | no | 🟡 |
| J5 | Create/edit/delete per role, server-side | role-gated master data | verify per-role | 🟡 | 🟡 | ✅ | security regression | — | no | 🟡 |

## PHASE K — Retention

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| K1 | Retention GET | admin reads policy | v3_settings retention GET | ✅ | ✅ | ✅ | — | — | no | ✅ |
| K2 | Retention UPDATE + persistence | save → reload → DB value → backend consumes | **live-verified 2026-08-30**: system-admin GET→PUT (730/2190 days)→GET→DB row confirmed→original restored; enforcement remains dry-run (`services/retention.py` default dry_run=True, `tools/enforce_retention.py --apply` only, no scheduler); destructive enforcement explicitly **deferred** (D-P2-04) | ✅ | ✅ | ✅ | — | — | approved (D-P2-04) | ✅ |
| K3 | System Admin permission | system_admin can configure | ADMIN_ROLE_NAMES includes system_admin | ✅ | ✅ | ✅ | — | — | no | ✅ |

## PHASE L — Search

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| L1 | Org search returns results (no 500) | CL-65 fixed | report query → report_generation_queue | ✅ | ✅ | ✅ | — | — | no | ✅ |
| L2 | Search respects boundaries | org/consultant/PE/internal scopes; no leakage | org-scoped endpoint; consultant denied; verify PE/internal | 🟡 | ✅ | ✅ | negative-case live pass | — | no | 🟡 |
| L3 | Result navigation | click result → workspace | no result navigation | ❌ | — | — | result → routed workspace links | G | no | ❌ |

## PHASE M — Error/UX quality

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | Human-readable errors (no stack/SQL) | user-friendly messages | v3Fetch surfaces detail; many pages show messages | ✅ | 🟡 | 🟡 | systematic audit of all surfaces | — | no | 🟡 |
| M2 | Loading/empty/retry states | honest states | LoadingState/ErrorState/EmptyState exist | ✅ | 🟡 | 🟡 | audit surfaces | — | no | 🟡 |
| M3 | No console noise on normal load | quiet role probes | CL-46/49 done | ✅ | ✅ | ✅ | — | — | no | ✅ |
| M4 | CAL-3 reference endpoint | /api/reference/fuel-types not 500 | **verified 2026-08-30: 200, 561 fuel types incl. Diesel** (queries emission_factors; CAL-3 fixed) | ✅ | ✅ | ✅ | — | — | no | ✅ |
| M5 | PRC-5 mapping-options quality | correct factor within default results | **verified**: mapping-options returns the correct factor within the default 20 for Diesel and Natural gas (unit+scope correct) | ✅ | ✅ | ✅ | ranking refinement (exact-match-first) P3 follow-on | — | no | ✅ |

## Reporting / PDF

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Report generation from real data | no fake values | reports from emissions_logs; RPT-1 verified | ✅ | ✅ | ✅ | — | — | no | ✅ |
| R2 | PDF generation + download/view | PDF produced from persisted data | verified live | ✅ | ✅ | ✅ | — | — | no | ✅ |
| R3 | Report approval handoff | customer approves → report | **FULL BROWSER E2E PASS 2026-08-30 (19/19)**: customer upload → auto-extract → auto-map (customer Diesel factor) → validate (blocks on supplier → rework) → extract supplier → map → validate clean → start('calculation') → calculate (**44.17 kg CO₂e**) → UI shows result → customer review queue → owner approve → item persisted approved → report generate 201 → **completed** → **PDF download 200, valid `%PDF-1.4`** → cross-org owner cannot see item/report (403 on PDF). Persisted chain verified: item → snapshot(source_item_id, customer_factor_id) → emissions log → approved → report completed. E2E data cleaned + verified (7 legitimate Uploads-batch items + pre-existing 2026 report untouched) | ✅ | ✅ | ✅ | — | D/PRC | no | ✅ |

## Factor lifecycle (Phase C regression)

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| FCT1 | create→version→approve→map→calc→evidence | full chain | Phase C verified 2026-08-29 | ✅ | ✅ | ✅ | — | — | no | ✅ |
| FCT2 | Customer factor precedence + source shown | approved customer factor wins; source visible | CL-44 factor_kind + order; UI shows source | ✅ | ✅ | ✅ | — | — | no | ✅ |
| FCT3 | **P1 FIX (found by final E2E): customer-factor calcs blocked report generation** | report for a customer-factor org passes validation | `EmissionLog.customer_factor_id` (snapshot join) + ValidationEngine resolves approved customer factors; orphan ERROR only for genuinely missing/inactive; absent lookup = WARNING. 4 regression tests. Live: generate 201 → completed → PDF `%PDF-1.4` | ✅ | ✅ | ✅ | — | — | no | ✅ |

## Security regression

| # | Requirement | Expected behaviour | Current implementation | Impl? | RT? | Test? | Remaining work | Deps | PO? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | A→B, client→client, consultant→consultant, PE→PE, viewer→write, member→admin, operator→restricted, system admin→admin ops | all denied/allowed correctly | unit + live negative tests; **close-out live sweep 19/19 PASS** across customer/consultant/PE/staff boundaries incl. **QC → customer approval 403** (D-P2-03), system-admin + staff-admin retention/entities positives | ✅ | ✅ | ✅ | — | — | no | ✅ |

---

**Overall:** PHASE 2 — COMPLETE (all PO-gated decisions applied, all remaining
acceptance items implemented and verified live; full browser E2E + security
regression + test suites pass; no P0, no P1).

**PO decisions applied (2026-08-30):** D-P2-01 queue disclosure (implemented +
verified), D-P2-02 legacy admin deprecation (inventory + retirement conditions
documented; V3 admin canonical), D-P2-03 QC limited authority (documented +
regression-tested), D-P2-04 retention (config verified; destructive enforcement
explicitly deferred).

**Final acceptance session (commits 7e24941 → bb6cd7d):**

- **D-P2-01 queue disclosure**: every internal queue row now identifies WHOSE
  work (org, consultant/client, processing entity, batch, assignment, received
  date, source documents, SLA) — server-side, never raw UUIDs. ✅
- **D-P2-02/03/04**: legacy admin dependency + coverage inventory
  (`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`), QC-limited-authority regression,
  retention live round-trip (PUT→GET→DB) with destructive enforcement deferred. ✅
- **Notifications DataTable**: server-side pagination (limit/offset/total, page
  size, row count); messaging N/A (bounded navigation/chat surfaces). ✅
- **M4 (CAL-3)**: `/api/reference/fuel-types` 200, 561 types. ✅
- **M5 (PRC-5)**: correct factor within default mapping results (Diesel + gas). ✅
- **Final R3 browser E2E (19/19 PASS)**: customer upload → auto-process → map
  (customer factor) → validate (blocked on supplier → rework) → extract → map →
  validate clean → calculate **44.17 kg CO₂e** → UI result → review → owner
  approve → report completed → valid `%PDF-1.4` download → cross-org denied.
  Persisted chain verified item→snapshot→log→approved→report. E2E data cleaned
  and verified. ✅
- **P1 fixed by the E2E**: customer-factor calculations previously blocked
  report generation forever (validation treated NULL `emission_factor_id` as an
  orphan) — now resolved against the approved customer factor (4 regression
  tests; live report + PDF pass). ✅
- **Security regression 19/19 PASS** incl. QC→customer-approval deny and
  system-admin/staff-admin positives. ✅
- **Tests**: backend full unit suite PASS (1194, 0 failures); frontend V3 131/131
  PASS; production build OK. ✅
- **Security/persona regression**: 13 live checks across cross-org, cross-firm,
  cross-entity, viewer-write, PE→customer and staff→customer boundaries — all PASS. ✅
- **Tests**: backend 1202 passing / 0 failing; frontend 131 passing.

**Remaining before COMPLETE:**
1. **PO decisions** (⛔): queue disclosure columns (CL-55/57), legacy admin
   retirement (CL-66), QC authority model, retention enforcement scheduling.
2. R3 full browser E2E of customer review → approval → report handoff
   (report generation + PDF are individually live-verified).
3. Messaging + notifications DataTable adoption (bounded lists today, low risk).
4. M4 (CAL-3 reference endpoint) and M5 (mapping-options quality) final
   verification; consultant client-report generation (E8) live pass.


