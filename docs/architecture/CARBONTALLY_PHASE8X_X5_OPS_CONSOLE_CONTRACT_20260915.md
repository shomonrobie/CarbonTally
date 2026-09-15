# CARBONTALLY — PHASE 8-X X5 OPERATIONS CONSOLE EXTENSION: BOUNDED CONTRACT

**Document ID:** `CARBONTALLY_PHASE8X_X5_OPS_CONSOLE_CONTRACT_20260915`
**Stage:** Phase 8-X **X5** (8-X discovery doc Stage X5: *"surface X2–X4 in the existing ops console as
tabs/cards; `frontend/src/v3/ops/**` extension only; no new dashboard shell"*)
**Dependencies:** X1, X2, X4 — all IMPLEMENTED, INDEPENDENTLY VERIFIED, **PO-CLOSED**
**Status:** contract derived **entirely from already-approved decisions** — no new PO decision needed.

---

## 1. Reconciled current state (what exists today)

| Fact | Evidence |
|---|---|
| The ops console is a **permission-gated tab shell** at the single route `/ops` | `frontend/src/App.js` (`/ops` → `ProtectedRoute` → `RoleRoute requireStaff` → `V3Layout` → `OperationsPage`); `OperationsPage.jsx` builds a `TABS` array from `getOpsMe()` permissions and renders `?tab=<id>` |
| **No X1/X4 endpoint has any UI caller today** | repository-wide search: zero frontend references to `operational-health` or `operational-intelligence` |
| X1 exposes two read-only internal endpoints | `GET /api/v3/ops/operational-health/queue` (queue summary), `GET /api/v3/ops/operational-health/worker` (heartbeat + liveness) |
| X4 exposes one read-only internal endpoint | `GET /api/v3/ops/operational-intelligence` (failures + SLA + liveness + `truncated`) |
| **X2's alert deep-link targets a route that does not exist** | `domain/operational_alerts.ALERT_LINK = "/ops/operational-health"`, but `App.js` registers only `/ops`, `/ops/items/:id`, `/ops/review/:id`, `/ops/qc/:id` → **finding `F-X5-1`** |
| Authorization is already correct server-side | X1/X4 routes use `require_staff` → `require_internal_staff` → `can_view_all`; the console's `RoleRoute requireStaff` is a UI convenience only (never a boundary) |
| Existing tab style/conventions | e.g. `SlaTab.jsx` (`v3-ops-error`, `v3-ops-notice`, `workspace-pane/grid`, `v3-loading`); D21 primitives barrel (`Card`, `StatCard`, `Badge`, `DataTable`, `LoadingState`, `ErrorState`, `EmptyState`, `Alert`) |

## 2. The eleven reconciliation questions, answered

| # | Question | Answer for the bounded X5 release |
|---|---|---|
| 1 | **Exact operator-facing information** | Current operational state, verbatim from the two existing internal APIs: queue open/closed + per-stage depth, retry-exhausted, stuck claims, jobs with errors by stage, oldest waiting age; worker liveness (state + age); SLA configured state/value and the persisted breach count. **No derived, computed or new figure** |
| 2 | **Exact X4 data consumed** | The full `/operational-intelligence` payload, displayed as returned — including `truncated`, `read_limit`, `sla_state` and `worker_liveness`. X5 adds no interpretation of its own |
| 3 | **Exact existing operational data sources** | Only the three existing internal endpoints above. No new repository call, no direct database access from the browser, no Supabase query |
| 4 | **Required filters / sorting / drill-down** | **None.** The payloads are small, fixed-shape summaries (counts + state labels). Filters/sorting/drill-down are **not authorised** by any existing decision and would invent interaction semantics → **excluded**, recorded as a possible future increment requiring a PO decision |
| 5 | **Read-only versus actionable controls** | **Read-only.** The only interactive control is a **manual refresh** (re-fetch of the same GETs). No mutation, no acknowledgement, no alert-resolution, no assignment, no retry/re-drive control — none of those are authorised |
| 6 | **Internal staff authorization** | Unchanged and server-enforced: the tab renders only when `getOpsMe()` reports `can_view_all`; the endpoints re-check `require_staff` → `require_internal_staff` → `can_view_all` on every request. The UI is **not** a security boundary |
| 7 | **Customer / PE / entity visibility** | **Excluded.** No customer, consultant, client or PE/entity surface is touched; PE/entity staff are already refused by `require_internal_staff` server-side, and no ops tab is reachable from their shells |
| 8 | **Freshness expectations** | Read-time, no cache and no polling beyond the existing console conventions. The panel shows `evaluated_at`/`generated_at` from the payloads plus the worker-liveness age, so an operator can see whether the numbers are live or the worker is dead. **X5 never presents stale data as current** |
| 9 | **Frontend / API changes** | Frontend only: 3 read-only client wrappers, 1 new tab component, 1 tab registration, 1 route alias so X2's existing alert link resolves, plus small `ops.css` additions on D21 tokens. **No backend change of any kind** |
| 10 | **Schema / RLS / permission change** | **None.** No migration, no RLS change, no new permission key, no new role |
| 11 | **Verification requirements** | Role-based UI tests (tab gating), rendering of returned figures, explicit `truncated` display, SLA not-configured display, worker `UNKNOWN` display, empty/error states, a **"no write controls exist"** assertion, and a responsive/a11y sanity pass per D21 |

## 3. X5 stop conditions — checked, none triggered

No new business definition · no new metric · no new permission model · no RLS change · no schema or
migration · no new retention policy · no new operational action · **no modification of X1/X2/X4
semantics** (their payloads are consumed as-is) · no external evidence · no production access. The
only UI addition beyond a tab is the route alias for X2's *already-shipped* alert link (`F-X5-1`),
which completes an existing approved surface rather than adding new scope.
