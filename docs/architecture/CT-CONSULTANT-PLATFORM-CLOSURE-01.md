# CT-CONSULTANT-PLATFORM-CLOSURE-01 — Consultant Platform Safe-Closure Implementation Report

## 1. Document control

| Field | Value |
|---|---|
| Task ID | `CT-CONSULTANT-PLATFORM-CLOSURE-01` |
| Title | Consultant Platform safe-closure increments |
| Status | **IMPLEMENTED / TESTED — PARTIALLY VERIFIED. `CLOSURE-BLOCKED-BY-EXPLICIT-PO-DECISION`** (PD-1A, PD-2A, PD-5 remain open; see §24) |
| Date | 2026-10-07 |
| Agent | Cline (implementation) |
| Branch / HEAD | `p8-release-reconciled` @ `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Layer(s) | Backend (FastAPI, repository layer, test doubles), Frontend (shared shell nav), Tests |
| Migrations | **None** (reads tables added by `CT-CONSULTANT-MODEL-IMPLEMENTATION-03`) |
| New API routes | 3 (`GET` only; read-only) |
| PO decisions reopened | **None** (PO-1 … PO-10 preserved) |

## 2. Purpose

`CT-CONSULTANT-MODEL-IMPLEMENTATION-03` (and its independent verifier
`CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01`) left a set of consultant-platform
gaps. Some are **safely closable now** because they are engineering hardening or
read-only review surfaces; others are **blocked** because closing them would
require inventing Product-Owner policy.

This report records the implementation of the safely-closable subset, exactly
what changed, the test evidence, and — deliberately — the items that were **not**
done because they require an explicit Product-Owner decision.

## 3. Scope

**In scope (implemented here):**

- A. Firm-task `client_id` server-side validation (`F-IND-1` / `PD-3A`).
- B. Firm-scoped **read** surface for inbound relationship change/end requests.
- C. Firm-scoped **read** surface for product-mode change requests.
- D. Consultant-side **view** of a managed client's users (the READ half of PO-2).
- E. Client-plane navigation cleanup (one consultant return path).

**Out of scope (explicitly not implemented — §24):**

- Relationship-request / mode-request **approve/reject** decision authority.
- Client-user **invite / create / manage / revoke** (identity lifecycle + role grant).
- Any change to RLS policy, schema, or migrations.
- `F-IND-2` uniform client-context denial contract (recorded as a remaining,
  non-blocking hardening recommendation — §24).

## 4. Binding sources and authority order

Honoured in this order (AGENTS.md §2, §62, §80):

1. **`docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md`** — ratified
   Product-Owner decisions (the ten: PO-1 … PO-10).
2. **`docs/architecture/CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01.md`** —
   decision-state matrix; the register of what is genuinely open (§6) and the
   `PO DECISION REQUIRED` register (§4.4).
3. **`docs/architecture/CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01.md`** —
   independent findings `F-IND-1 … F-IND-5` (§29) and remaining product
   decisions (§31).
4. **`docs/architecture/CT-CONSULTANT-MODEL-IMPLEMENTATION-03.md`** — the schema
   and code the model introduced (the tables these endpoints read).
5. `AGENTS.md` — operating constitution (security, tenancy, testing, reporting).

Every ratified decision (PO-1 … PO-10) was treated as frozen. **No Product-Owner
decision was reopened, reinterpreted, or silently changed.**

## 5. Definition of "safely closable"

An increment is *safely closable* only when **all** hold:

1. It introduces no new business policy (no "who may do X" choice).
2. It cannot weaken tenant isolation, RLS, or authorization.
3. It is server-authoritative and testable without a live production dependency.
4. Where a decision is required, the increment can be built as the **READ**
   half while the **decision/write** half fails closed with no route.

Anything failing these tests was left open rather than invented.

## 6. Executive summary and verdict

Five increments were implemented. All backend and frontend tests pass. The one
full-suite failure observed is **pre-existing and environmental**, proven
unrelated to this work (§23).

**Verdict:** `IMPLEMENTED` and `TESTED`. Not `ACCEPTED` — because three
Product-Owner decisions (`PD-1A`, `PD-2A`, `PD-5`) and one commercial decision
(PO-1 mode-change authority) remain open, and the corresponding decision/invite
halves are intentionally absent. The correct disposition is
**`CLOSURE-BLOCKED-BY-EXPLICIT-PO-DECISION`** for the write/decision halves, with
the read/hardening halves complete.

## 7. Deliverables inventory

| # | Item | Route / Surface | File(s) | Test(s) |
|---|---|---|---|---|
| A | Firm-task `client_id` validation | `POST /api/v3/consultants/me/tasks` | `backend/api/v3_consultants.py` | `TestFirmTaskClientLinkValidation` |
| B | Relationship-request read surface | `GET /api/v3/consultants/me/relationship-requests` | `v3_consultants.py`, `data/consultants.py`, `fakes.py` | `TestRequestReviewSurfaces::test_firm_lists_*` |
| C | Mode-change request read surface | `GET /api/v3/consultants/me/mode-change-requests` | same | `TestRequestReviewSurfaces` |
| D | Consultant view of client users | `GET /api/v3/consultants/clients/{client_id}/users` | `v3_consultants.py` | `TestConsultantViewsClientUsers` |
| E | Client-plane nav cleanup | Shared shell `V3Layout` | `frontend/src/v3/components/V3Layout.jsx` | `consultant-nav-plane.test.jsx`, `consultant-client-org-shell.test.jsx` |

## 8. Item A — firm-task `client_id` server-side validation (F-IND-1 / PD-3A)

**Finding.** `F-IND-1` (LOW): `POST /me/tasks` accepted a `client_id` the firm was
not authorised for, did not own, or that did not exist — returning `201` in every
case. The UI's authorised-client dropdown implied a guarantee the backend did not
enforce. Tracked as `PD-3A`.

**Implementation.** New helper `_ensure_task_client_link_authorized()` in
`backend/api/v3_consultants.py`, called from `create_task()` before the write:

- The acceptable identifiers are resolved from the firm's **authoritative** active
  client set (`repos.consultants.list_clients(firm_id)`), never from the request:
  a client row's own `id` (`consultant_clients.id`) **or** its linked
  `organization_id` is accepted, but only when the relationship `status` is
  `active`.
- A nonexistent, foreign, or inactive id is rejected with **one uniform
  response** (`422`, `"client_id must reference one of your active clients"`) so
  task creation cannot be used as an existence oracle — the caller cannot
  distinguish "not mine" from "does not exist".
- A firm-wide task (no `client_id`) is unaffected (still `201`, `client_id: null`).

**Authority note.** `PD-3A` explicitly asked *whether* the firm-task `client_id`
should be validated server-side against an active grant. The chosen behaviour
(deny foreign/inactive/nonexistent; allow own-active) is the conservative,
security-positive reading and does not alter any commercial policy; it is
recorded here so the PO can ratify or override it.

## 9. Item B — relationship-request read surface (PD-5)

**Gap.** `CT-CONSULTANT-MODEL-IMPLEMENTATION-03` created the durable
`public.consultant_relationship_requests` records and an endpoint that *creates*
them, but no consumer.

**Implementation.** `GET /me/relationship-requests` returns
`{"requests": [...]}` scoped to the **caller's own firm**
(`WHERE consultant_id = $1`), ordered by `created_at DESC`. Cross-firm isolation
is proven by test (a rival firm's request is never returned).

**Fail-closed decision half.** The **approve/reject** authority is a **PD-5** open
decision ("who confirms it, within what SLA"). No approve/reject route exists —
nothing is invented. The read surface exposes the authoritative `status` field so
the eventual decision UI has truthful state to show.

## 10. Item C — mode-change request read surface (PO-1)

**Gap.** The `public.consultant_mode_change_requests` records had a creator but
no consumer.

**Implementation.** `GET /me/mode-change-requests` returns
`{"requests": [...]}` scoped to the caller's firm (`WHERE firm_id = $1`), ordered
by `requested_at DESC`.

**Fail-closed decision half.** Per **PO-1**, a firm's product-mode change is a
CarbonTally (commercial-boundary) decision, not a consultant decision. No
decision route exists here; the surface is read-only.

## 11. Item D — consultant-side client-user view (PO-2 read half)

**Gap.** PO-2 makes inviting/managing/removing **client** users a consultant-side
responsibility, but the consultant had no way to even *see* a managed client's
users.

**Implementation.** `GET /clients/{client_id}/users`:

- Re-authorises via `_authorized_client_org()` → `_checked_client()` (firm owns
  the row) **and** `ensure_consultant_org_access()` (an **ACTIVE** grant, D15).
- Returns `{"organization_id": ..., "users": await
  repos.organizations.list_members_with_email(organization_id)}` — tenant-scoped.
- A non-active (e.g. `ended`) grant serves **403**; another firm's client serves
  **403** (isolation proven by test).

**Fail-closed write half.** Invite / create / manage / revoke are **not**
implemented. Provisioning a brand-new client identity needs an
invitation/signup-email + token lifecycle (`PD-1A`, open); assigning a client
role to an existing identity needs a ratified assignment authority (`PD-2A`,
open). No such route exists → nothing invented.

## 12. Item E — client-plane navigation cleanup (§11)

**Goal.** Inside a managed client's operating plane, exactly one return path to
the Consultant Plane must exist.

**Implementation.** `frontend/src/v3/components/V3Layout.jsx`: the shared nav's
plain **"Consultant"** hub entry now renders only on the consultant **firm**
plane (`!navPrefix`). In the client operating plane (`navPrefix` set) it is
omitted, leaving the client context bar's single textual **"← Back to
Consultant"** (rendered by `ClientOrgShell`) as the one and only return path.

**Supersession.** This supersedes the earlier `UX-NAV-01A` rationale that the
shared nav should *keep* a plain hub entry — recorded in the component comment so
the change is not mistaken for drift.


## 13. API contract (new routes)

All three routes are under the existing consultant router
(`api/v3_consultants.py`, mounted at `/api/v3/consultants`). All require an
authenticated **consultant** (`require_consultant`). None accept a body.

| Method | Path | Auth | Success | Deny |
|---|---|---|---|---|
| GET | `/me/relationship-requests` | consultant | `200 {"requests": [...]}` | `403` non-consultant |
| GET | `/me/mode-change-requests` | consultant | `200 {"requests": [...]}` | `403` non-consultant |
| GET | `/clients/{client_id}/users` | consultant + active grant | `200 {"organization_id","users"}` | `403` non-active grant / foreign client |

`POST /me/tasks` (existing) gained server-side validation of its optional
`client_id`; its contract is otherwise unchanged (`201`).

No request/response schema was invented beyond the existing `TaskCreate` model
and the repository row shapes already present in the database.

## 14. Database and schema impact

**None.** Every new endpoint **reads** existing tables introduced by
`CT-CONSULTANT-MODEL-IMPLEMENTATION-03`:

- `public.consultant_clients` (client access profile + retention columns).
- `public.consultant_relationship_requests` (RLS enabled).
- `public.consultant_mode_change_requests` (RLS enabled).

No table, column, index, constraint, or policy was added or altered.

## 15. Migrations

**None added.** The closure is implemented entirely against already-migrated
schema. This is deliberate (AGENTS.md §66): inspect-then-extend, avoid duplicate
tables. No ad-hoc database modification was performed.

## 16. Backend implementation detail — `backend/api/v3_consultants.py`

- `_ensure_task_client_link_authorized(repos, context, client_id)` — new helper
  (§8). Builds the allowed-id set from the firm's **active** clients
  (`client.id` ∪ `client.organization_id`).
- `create_task()` — calls the helper when a non-empty `client_id` is supplied.
- `list_relationship_requests()` — thin pass-through to the repository, scoped
  to `context.profile.id` (§9).
- `list_mode_change_requests()` — same, scoped to the firm (§10).
- `list_client_users()` — `_authorized_client_org()` admission then repository
  read (§11).

All error responses use the platform's existing error envelope
(`{"error": {"code", "message", ...}}`) via the application exception handler;
tests assert on the envelope shape, not on byte-identical bodies.

## 17. Repository layer — `backend/data/consultants.py`

- `list_relationship_requests(consultant_id)` — parameterised
  `SELECT … FROM public.consultant_relationship_requests WHERE consultant_id = $1
  ORDER BY created_at DESC`.
- `list_mode_change_requests(firm_id)` — parameterised
  `SELECT … FROM public.consultant_mode_change_requests WHERE firm_id = $1
  ORDER BY requested_at DESC`.

Both use the existing `_fetch_all` helper and bound parameters (no string
interpolation) — no injection surface and no cross-tenant leakage.

## 18. Test doubles — `backend/tests/unit/api/fakes.py`

The in-memory consultant fake repository gained matching methods so the API
tests exercise real endpoint logic without a live database:

- `list_relationship_requests(consultant_id)` — filters an internal list by firm.
- `list_mode_change_requests(firm_id)` — filters by firm.

(`list_members_with_email` already existed on **both** the real
`data/organizations.py` and the fake — verified — so Item D's dependency resolves
in production and in tests.)

## 19. Frontend implementation — `frontend/src/v3/components/V3Layout.jsx`

The consultant branch of the shared nav now pushes the `Consultant` hub entry
**only when `!navPrefix`** (firm plane). A component comment records the
supersession of `UX-NAV-01A`. No other navigation, styling, or routing was
changed.


## 20. Security, authorization and tenancy analysis

| Property | Status | Evidence |
|---|---|---|
| Server-side authorization on every new route | ✅ | `require_consultant` dependency; `_authorized_client_org` for client data |
| Tenant isolation (firm scoping) | ✅ | repo queries `WHERE consultant_id/firm_id = $1`; tests assert a rival firm's rows are never returned |
| No existence oracle on task link | ✅ | uniform `422` for foreign/inactive/nonexistent ids (§8) |
| Active-grant enforcement (D15) | ✅ | client-user view requires an **active** relationship; `ended` → `403` |
| Cross-firm denial (DENY path) | ✅ | `test_client_users_denied_for_another_firms_client`, `test_non_consultant_cannot_list_requests` |
| No RLS weakening | ✅ | no policy touched; writes are via the service-role path with application-level authorization |
| No frontend-as-boundary | ✅ | the nav cleanup is cosmetic; every operation is re-authorized server-side |
| No secrets introduced | ✅ | endpoints require no credentials; no tokens logged |

Every ALLOW test also asserts the response contains the **authorised tenant's
own** data; no DENY test leaks data (AGENTS.md §45).

## 21. Test evidence — backend

New file `backend/tests/unit/api/test_ct_consultant_closure_01.py` (15 tests):

- `TestFirmTaskClientLinkValidation` — firm-wide task allowed; own active row id
  allowed; own `organization_id` allowed; foreign id / nonexistent id / inactive
  grant rejected uniformly; non-consultant rejected.
- `TestRequestReviewSurfaces` — firm lists its own relationship requests; a rival
  firm's request is never returned; firm lists its mode-change requests;
  non-consultant is `403` on both.
- `TestConsultantViewsClientUsers` — consultant views an active client's users;
  a non-active grant is `403`; another firm's client is `403`.

Results:

| Suite | Result |
|---|---|
| `test_ct_consultant_closure_01.py` | **15 passed** (`EXIT=0`) |
| Consultant regression set (15 files: `p6_2*`, `consultant*`, `ct_consultant*`, `p6bill1*`, `v3_consultants`) | **485 passed** (`EXIT=0`) |

## 22. Test evidence — frontend

| Suite | Result |
|---|---|
| `consultant-nav-plane.test.jsx` (new) | 2 passed |
| `consultant-client-org-shell.test.jsx` (tightened) | passed |
| `consultant-ux-navigation.test.jsx` | passed |
| `consultant-page.test.jsx` | passed |
| **Total (4 suites)** | **21 passed** (`EXIT=0`) |

- **New** `consultant-nav-plane.test.jsx`: asserts the shared nav keeps the
  single `Consultant` hub entry on the **firm** plane, and **omits** it in the
  client operating plane while still rendering client-prefixed destinations.
- **Tightened** `consultant-client-org-shell.test.jsx`: the return-path test now
  asserts **exactly one** anchor targeting `/consultant` (the context bar), and
  its stale comment (claiming the shared nav keeps the hub entry) was corrected.

## 23. Full API-suite result and pre-existing-failure classification

`pytest backend/tests/unit/api` collects **2646** tests. Observed:
**1 failed**, the rest pass.

- **Failure:** `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
  — `assert body["verification_delivered"] is False` receives `True`.
- **Root cause:** the test asserts the *email-unconfigured* case ("Email delivery
  is NOT configured in unit tests — reported honestly"), but this machine's
  gitignored `backend/.env` **does** configure Resend/SMTP, so a delivery attempt
  succeeds and the flag becomes `True`.
- **Proof it is pre-existing and unrelated:** a clean `git worktree` at HEAD
  (`3fec874`) **passes** the test; copying only `backend/.env` into that same
  clean worktree reproduces the failure. The failure therefore depends solely on
  the environment's `.env`, not on any change in this task. (The temp worktree
  was removed afterwards; no repository state was altered.)

This is environment-dependent test fragility, **not** a regression from
`CT-CONSULTANT-PLATFORM-CLOSURE-01`.


## 24. Open Product-Owner decisions, fail-closed register, remaining findings

| ID | Item | State in this task |
|---|---|---|
| **PD-5** | Authority + SLA to approve/reject a relationship change/end request | **OPEN — PO decision.** Read surface delivered; **no** decision route (fails closed). |
| **PO-1** | Product-mode change authority = CarbonTally Admin (commercial boundary) | **OPEN — commercial decision.** Read surface delivered; **no** decision route. |
| **PD-1A** | Client-user invite / signup-email + token lifecycle | **OPEN — PO decision.** Client-user **view** delivered; **no** invite/intake route. |
| **PD-2A** | May a firm admin assign the `owner` role (client role-assignment authority) | **OPEN — PO decision.** Client-user **view** delivered; **no** role-assignment route. |
| **PD-3A** | Should a firm task's `client_id` be validated server-side? | **Delivered** as conservative hardening (§8); recorded for PO ratification. |
| **PD-NAV-1** | Dedicated consultant "Firm & Billing" surface | **Untouched** (out of scope). |
| **R-NAV-1** | Legacy `/consultant/items/:clientId/:itemId` route consolidation | **Untouched** (presentational). |
| **F-IND-2** | Uniform denial contract for the client-context endpoint | **NOT implemented.** `_checked_client()` still returns `404 "client not found"` vs `403 "client belongs to another consultant firm"`. Non-blocking hardening recommendation; deliberately not folded in to keep scope tight and avoid changing an existing contract without PO sign-off. |
| **F-IND-3/4/5** | Informational observations | **No action** (informational; independent verify §29). |

**Disposition:** the write/decision and identity-lifecycle halves are
`CLOSURE-BLOCKED-BY-EXPLICIT-PO-DECISION`. They must not be implemented until the
Product Owner ratifies `PD-1A`, `PD-2A`, `PD-5`, and the PO-1 mode-change
authority.

## 25. Runtime verification, worktree hygiene, and final disposition

**Runtime verification performed (local only):**

- Backend: new + regression suites executed (15 + 485, all green).
- Frontend: consultant suites executed (21 green) via `react-scripts test`.
- No production, Render, or hosted Supabase surface was contacted (per brief).
- **Demo Lab browser walkthrough and screenshots were NOT performed** in this
  session — recorded honestly as an outstanding verification step, not claimed.

**Worktree hygiene:**

- Branch `p8-release-reconciled`, HEAD `3fec874` (unchanged — **no** commit,
  reset, clean, stash, rebase, or force-push was run).
- The branch was **already dirty** with the wider consultant/manual-processing
  workstream before this task; those pre-existing changes were **not** touched or
  absorbed.
- Files this task changed/added:
  - `backend/api/v3_consultants.py` (helper + `create_task` wiring + 3 GET routes)
  - `backend/data/consultants.py` (2 read methods)
  - `backend/tests/unit/api/fakes.py` (2 fake read methods)
  - `backend/tests/unit/api/test_ct_consultant_closure_01.py` (**new**)
  - `frontend/src/v3/components/V3Layout.jsx` (nav cleanup)
  - `frontend/src/v3/__tests__/consultant-client-org-shell.test.jsx` (tightened)
  - `frontend/src/v3/__tests__/consultant-nav-plane.test.jsx` (**new**)
  - `docs/architecture/CT-CONSULTANT-PLATFORM-CLOSURE-01.md` (**new**, this doc)
- A temporary `git worktree` used only to classify the pre-existing failure was
  pruned/removed; `git worktree list` shows only the main checkout.

**Final disposition:**

- Item A `IMPLEMENTED` + `TESTED` (F-IND-1 closed on the create-task path).
- Items B, C, D `IMPLEMENTED` (READ halves) + `TESTED`; decision/invite halves
  `BLOCKED — PO DECISION REQUIRED`.
- Item E `IMPLEMENTED` + `TESTED`.
- Overall: **`IMPLEMENTED` / `TESTED`; `ACCEPTED` withheld** —
  `CLOSURE-BLOCKED-BY-EXPLICIT-PO-DECISION` for PD-1A / PD-2A / PD-5 / PO-1
  mode-change authority; `F-IND-2` remains a separate open recommendation.

**Remaining work / recommendations:**

1. Obtain PO decisions: `PD-1A`, `PD-2A`, `PD-5`, PO-1 mode-change authority.
2. Independent QA re-verification of the four delivered items (OHD), including a
   Demo Lab browser pass for Item E.
3. Optional hardening: `F-IND-2` uniform denial contract for the client-context
   endpoint (needs PO sign-off as it changes an existing denial contract).

