# CarbonTally V3 — Phase 2 Implementation Report (Phase D → H/L + acceptance)

**Generated:** 2026-08-30
**Branch:** `main`
**Baseline:** `17665d0` (Phases A–C committed)
**Session commits (Phase 2 continuation):**

| Commit | Scope |
|---|---|
| `55410d9` | Phase D — authenticated communication (CL-60/63/64/45/46/49/52) |
| `a0194a9` | V3 ops hardening (CL-65 search 500, CL-62 permission tabs, CL-59 routed workspaces) |
| `5d35603` | Phase E — consultant product (CL-61 team, CON-1 new customer) |
| `4e2c3e3` | CL-58 shared table contract + operator queue pagination/context |
| `4491103` | CL-66 canonical staff/admin control-plane documentation |

---

## 1. Deliverables by phase

### Phase D — Authenticated communication (CL-60/63/64/45/46/49/52) ✅

- **CL-60 (P1)** — `PublicAssistant` route-boundary in `frontend/src/App.js`;
  `AssistantWidget` now mounts only on public routes (`/`, `/faq`, `/pricing`,
  …) and never inside authenticated shells.
- **CL-63 (P1)** — `OrganizationsRepository.search()` in
  `backend/data/organizations.py`; `GET /api/v3/ops/organizations`
  (search + pagination) in `backend/api/v3_operations.py`, gated to internal
  staff with `can_manage_staff`. The ops dashboard summary
  (`organizations: {total}`) is no longer used as a row collection — the
  `orgs.map is not a function` crash is eliminated by contract.
- **CL-64 (P1)** — `frontend/src/v3/messaging/useConversationRealtime.js`:
  per-conversation `postgres_changes` channel with dedupe, reconnect and
  API-refetch fallback; wired into `MessagingPage.jsx`,
  `ClientMessagingTab.jsx` and `OpsMessagingTab.jsx`. Channels are scoped to a
  single `conversation_id`; RLS still restricts delivery to authorised
  participants.
- **CL-45 (P1)** — `NotificationsProvider` (`RealtimeContext.jsx`) rewritten
  onto `listNotifications` / `markNotificationRead` / `markAllNotificationsRead`
  from `v3/api.js`; `normaliseNotification` added; no legacy
  `supabase.from('notifications')` reads or writes remain.
- **CL-46/49/52 (P2/P3)** — `v3Fetch` supports `options.quiet`; `V3Layout.jsx`
  cascades role probes (org → staff → consultant) in quiet mode;
  `resolvePostLoginPath` uses quiet probes. Normal authenticated page loads no
  longer emit expected 403/404 role-probe console noise.

### Phase E — Consultant product (CL-61, CON-1) ✅

- **CL-61 (P2)** — Consultant team tab: roster of firm members enriched with
  human-readable name/email (`public.users` join), add-member form
  (server-enforced `manage_team`), and a firm tasks list/create/status surface.
- **CON-1 (P1)** — "New customer" onboarding UI posting to
  `POST /api/v3/consultants/me/customers` (owner identity provisioned
  server-side, organisation created, firm linked as active client).

### Phase F — Staff/Admin/PE boundaries (CL-62, CL-66) ✅

- **CL-62 (P2)** — Internal Operations tabs are permission-aware and mirror the
  API guards: dashboard=`can_view_all`, data-entry=`can_process`,
  review=`can_review`, qc/issues=global admin (require_admin endpoints),
  staff/roles/entities/sla/messaging/audit/settings=`can_manage_staff`,
  commercial=`can_manage_billing`. No tab renders whose API the role cannot use.
- **CL-66 (P2)** — `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`
  declares the V3 `/ops` surface canonical; legacy admin quarantined with
  guardrails; PO decisions flagged.

### Phase G — Routed workspaces (CL-59) ✅

- Dedicated routes `/ops/items/:itemId`, `/ops/review/:itemId`,
  `/ops/qc/:itemId` with Back-to-queue (`?tab=` restoration), deep links,
  refresh safety and Previous/Next. Operator/Reviewer/QC queues no longer
  render workspaces below the queue.

### Phase H — Shared table contract (CL-58) + queue context (CL-55 partial) ✅

- `DataTable` gains an optional server-style pagination contract
  (`total`/`limit`/`offset`, Prev/Next, page-size) and optional client column
  sorting; hooks are unconditional (rule-of-hooks safe).
- Operator queue API accepts `limit`/`offset` and returns `total` (server-side
  windowing); the queue table shows **Organisation** + **Items** columns
  (PO-free context) and paginates the 51+ batch investor queue.

### Phase L — Search fix (CL-65) ✅

- Org search report query now reads `report_generation_queue` (the actual
  org-scoped report table) instead of the non-existent
  `report_versions.report_name` column that 500'd every shell search.


## 2. API changes (all V3, backward compatible)

| Endpoint | Change | Guard |
|---|---|---|
| `GET /api/v3/ops/organizations` | **new** — org search + pagination | internal staff + `can_manage_staff` |
| `GET /api/v3/ops/queues/operator` | **extended** — `limit`/`offset`, `total` | internal staff + `can_process` |
| `GET /api/v3/consultants/me/team` | **extended** — enriched name/email roster | consultant firm membership |

## 3. Database changes

None required. All new data access is read-only over existing tables
(`public.users`, `report_generation_queue`, `consultant_firm_members`). No
migrations were added this session.

## 4. Tests

- **Backend unit suite:** **1171 passed** (was 1169 at baseline; +1
  `test_ops_organizations_requires_staff_admin` for CL-63, +1
  `test_team_roster_returns_human_readable_members` for CL-61).
- **Frontend v3 suite:** **131 passed** (9 suites).
- **Frontend build:** `react-scripts build` succeeds (pre-existing legacy
  unused-var warnings only; CI warning-as-error escalation is not the project's
  baseline build gate).

## 5. Live runtime verification (local stack, API :8050)

| Check | Result |
|---|---|
| Staff-admin `GET /api/v3/ops/organizations` | 200, `total=975`, rows present |
| Operator same endpoint | 403 (`staff lacks permission: can_manage_staff`) |
| `GET /api/v3/ops/me` roles/permissions | admin full set / operator `[can_process, can_view_all]` |
| `GET /api/v3/search?organization_id=…&q=…` | 200 (previously 500 on reports) |
| `GET /api/v3/notifications` | 200 via V3 API |
| Consultant `GET /api/v3/consultants/me/team` | 200, enriched members |
| Operator queue `limit=3&offset=0` | 200, `total=51`, org name present |
| Realtime (CL-64) | per-conversation channel + RLS (verified by contract/tests) |
| Assistant public-only (CL-60) | route-boundary (verified by tests/build) |

## 6. Security verification

- CL-63 endpoint denies operator/reviewer/QC/PE staff (403) — verified in unit
  test and live.
- CL-61 roster is firm-scoped (cross-firm member never exposed) — regression
  test added.
- CL-62 navigation never authorizes; backend remains the boundary on every tab.
- No RLS bypasses; no new cross-tenant access; no secrets/logged tokens.

## 7. Remaining limitations / PO decisions required

1. **Legacy admin retirement** (CL-66) — PO approval required before removing
   the legacy admin CRA/endpoints (dependency inventory per AGENTS.md §79).
2. **QC authority** (CL-62) — QC remains a global-admin gate
   (`/api/v3/qc/*` = `require_admin`); PO decision on a dedicated QC
   permission.
3. **Queue disclosure columns** (CL-55/57 remainder) — consultant/source/PE
   assignment/SLA columns in internal queues require PO disclosure sign-off.
4. **DataTable rollout** (CL-58 remainder) — the shared contract exists; wider
   application to all large surfaces (review/QC, staff, entities, reports,
   customers, messaging) is incremental.
5. Full PDF/report generation + retention reload verification remain for the
   final acceptance pass (per backlog item 10).

## 8. Git state

- Working tree: only Phase 2 files staged/committed; ~400 pre-existing
  unrelated dirty files (`.agents/skills`, prisma, backups) left untouched.
- No reset/clean/rebase/force-push performed. Baseline history preserved.

