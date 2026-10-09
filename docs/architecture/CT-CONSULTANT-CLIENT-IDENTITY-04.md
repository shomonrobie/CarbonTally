# CT-CONSULTANT-CLIENT-IDENTITY-04

**Client-user invitation lifecycle (PD-1A), role administration (PD-2A) and
white-label invitation email**

- **Date:** 2026-10-07
- **Status:** Implemented (unit-tested) — pending independent verification
- **Ratified basis:**
  - `docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md` §2
    - **PD-1A** — CarbonTally-controlled, secure, single-use, expiring client
      invitation.
    - **PD-2A** — dual authority with explicit boundaries (client owner/admin
      manage their own Organisation's users; the consultant firm may
      create/manage those users on the client's behalf within the permitted
      client-role boundary, without gaining client DATA access).
  - **D19 §13** — a customer/consultant sender domain requires an externally
    verified sender row (`consultant_senders`); CarbonTally is not an email
    provider.
  - **D21** — consultant branding is presentation, never a security identity.
  - AGENTS.md §7/§8/§17/§44/§70/§74.

---

## 1. Problem

Before CT04 the client-user identity lifecycle was incomplete:

1. **The requested role was discarded.** `POST /{org_id}/invitations` validated
   `role` but never persisted it, so acceptance could not know which role the
   inviter was authorised to assign (PD-2A).
2. **There was no acceptance endpoint.** No route could turn a token into an
   organisation membership, so PD-1A could not be satisfied end-to-end.
3. **No consultant-plane invite surface.** A consultant could *view* a client's
   users but had no sanctioned way to invite or administer them (PD-2A).
4. **No branded invitation email.** Invitations were recorded but never sent;
   white-label firms could not present their own brand/sender.
5. **Role administration was not org-scoped.** `PUT /members/{id}` mutated a
   member by id without verifying the member belonged to the acting admin's
   tenant.

---

## 2. Design

### 2.1 Single policy module (`domain/client_identity.py`)

All PD-1A / PD-2A business rules live in one pure, I/O-free module so both API
planes apply identical rules:

- the client role vocabulary is **not** redefined — it is the
  `organization_members.role` CHECK set (`owner/admin/member/viewer`);
- `resolve_invitation_state()` derives `expired` from `expires_at` — it is
  **never stored**, so expiry needs no scheduled job to be authoritative;
- `may_manage_client_users()` / `permitted_assignable_roles()` bound PD-2A.

### 2.2 Durable invitation states

| stored `status` | meaning |
| --- | --- |
| `pending` | created, awaiting acceptance |
| `accepted` | consumed exactly once (single-use) |
| `revoked` | withdrawn before acceptance |

`expired` is **derived** (`pending` AND `expires_at <= now`) and returned as the
`state` projection — it is intentionally absent from the durable column.

### 2.3 Single-use consumption = conditional UPDATE

`InvitationsRepository.consume()` is the single-use guarantee:

```sql
UPDATE user_invitations
   SET status='accepted', accepted_at=NOW(), accepted_by=$2
 WHERE token=$1
   AND status='pending'
   AND (expires_at IS NULL OR expires_at > NOW())
RETURNING ...;
```

A second acceptance (or a stale/expired token) matches no row and returns
`None` — there is no read-then-write race. The API maps this to HTTP 409.

### 2.4 Acceptance is bound to a person

`POST /api/v3/organizations/invitations/accept` (`require_auth`) requires the
authenticated identity's email to match the invited address (403 otherwise), so
possession of a token alone never grants membership. Order of checks:

1. token lookup → 404;
2. effective state → 409 (accepted/revoked) / 410 (expired);
3. email binding → 403;
4. atomic consume → 409 if lost;
5. membership create/reactivate with the invited role.

`OrganizationsRepository.accept_invited_membership()` performs steps in a single
transaction (the `users` FK anchor is upserted idempotently, then the membership
is created or re-activated). An **already-active** membership is returned
unchanged so acceptance never silently escalates an existing member.

### 2.5 PD-2A boundaries

- **Client plane:** the client Organisation `owner`/`admin` manage their own
  users (`require_org_admin()`); `member`/`viewer` cannot invite.
- **Consultant plane:** a consultant holding `can_manage_clients` **and** an
  ACTIVE consultant-client grant (D15) may invite / list / revoke client users
  and assign client roles. This never makes the firm an `organization_members`
  row and never grants client DATA access.
- **Role boundary:** both planes validate roles against the single policy set
  and return 422 for anything else. Provenance of a consultant-created
  invitation is recorded in `user_invitations.invited_by_firm_id` (nullable FK
  to `consultant_profiles`).

### 2.6 White-label invitation email (D19 §13 / D21)

`services/client_invitations.py` is the single composition + sender resolver:

- the presentation brand is the **inviting party's** brand (the firm's own D21
  branding, or the CarbonTally fallback);
- the From address is the firm's own **VERIFIED** custom sender
  (`consultant_senders.status='verified'`) when one exists, otherwise the
  admin-configured platform sender. An unverified address is never used;
- delivery failures are reported honestly (`email_delivered: false`); a mail
  failure never invents success and never breaks invitation creation.

### 2.7 Consultant never receives the invitation token

`describe_invitation(..., redact_token=True)` is used on the consultant plane:
PD-1A states the consultant never receives the invitation token. The invitee
receives the single-use link by email; the client's own owner/admin may see
their Organisation's invitation link (they administer their own users).

---

## 3. API surface

### Organisation plane (`api/v3_organizations.py`)

| Method | Path | Guard | Purpose |
| --- | --- | --- | --- |
| `GET` | `/{org_id}/invitations` | org admin | list with derived `state` + `accept_url` |
| `POST` | `/{org_id}/invitations` | org admin | create (persists `role`), send branded email |
| `POST` | `/invitations/accept` | authenticated | PD-1A accept → membership |
| `DELETE` | `/invitations/{invitation_id}` | org admin | revoke (`revoked_by` recorded) |
| `PUT` | `/members/{member_id}` | org admin | PD-2A role change, **org-scoped** |

### Consultant plane (`api/v3_consultants.py`)

| Method | Path | Guard | Purpose |
| --- | --- | --- | --- |
| `GET` | `/clients/{client_id}/invitations` | `manage_clients` + active grant | list (token redacted) |
| `POST` | `/clients/{client_id}/invitations` | `manage_clients` + active grant | invite client user |
| `POST` | `/clients/{client_id}/invitations/{id}/revoke` | `manage_clients` + active grant | revoke |
| `PATCH` | `/clients/{client_id}/users/{member_id}` | `manage_clients` + active grant | assign client role |

---

## 4. Data model (migration)

`supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`
adds, **additively and idempotently**, to `public.user_invitations`:

- `role` (CHECK `owner/admin/member/viewer`, nullable);
- `invited_by_firm_id` (FK → `consultant_profiles(id)` `ON DELETE SET NULL`);
- `accepted_at`, `accepted_by`;
- `revoked_at`, `revoked_by`;
- index `idx_user_invitations_org_status (organization_id, status)`.

Column comments document that `expired` is derived and never stored.

---

## 5. Files changed

| File | Change |
| --- | --- |
| `backend/domain/client_identity.py` | **new** — pure PD-1A/PD-2A policy |
| `backend/services/client_invitations.py` | **new** — email composition + white-label sender resolution + `describe_invitation` |
| `backend/data/invitations.py` | `consume()`, `revoke(revoked_by=)`, `role`/firm provenance in the row projection, `token` surfaced for authorised callers |
| `backend/data/organizations.py` | `get_member_by_user()`, `accept_invited_membership()` |
| `backend/api/v3_organizations.py` | role persisted on create; derived `state`/`accept_url`; `POST /invitations/accept`; `revoked_by`; org-scoped `PUT /members/{id}`; branded email |
| `backend/api/v3_consultants.py` | client invitation list/create/revoke + client-user role `PATCH` |
| `backend/tests/unit/api/fakes.py` | invitation + membership doubles extended to the new surface |
| `backend/tests/unit/api/test_ct_consultant_client_identity_04.py` | **new** — policy + route tests |
| `supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql` | additive schema |
| `frontend/src/v3/api.js` | `acceptInvitation`, consultant client-invitation + `updateClientUser` clients |
| `frontend/src/v3/admin/MembersTab.jsx` | derived `state` badge + "Copy link" for pending invitations |
| `frontend/src/AcceptInvitation.jsx` | **new** — invitee acceptance journey (`/accept-invitation`) |
| `frontend/src/css/AcceptInvitation.css` | **new** — D21-token styling for the acceptance page |
| `frontend/src/App.js` | `/accept-invitation` public route + `PUBLIC_ROUTE_PREFIXES` entry |
| `frontend/src/__tests__/accept-invitation.test.jsx` | **new** — acceptance-journey tests |
| `tools/demo_lab/systemd/carbontally-demo-lab.service` | **new** — local auto-start `systemd --user` unit |
| `tools/demo_lab/supervise_demo_lab.py` | `run --ensure-containers` for boot; docstring update |
| `tools/demo_lab/README.md` | reboot section: installed + enabled unit |

---

## 6. Tests

`backend/tests/unit/api/test_ct_consultant_client_identity_04.py` (50 tests):

- **Policy** — role vocabulary, expiry-derived state, consumability, PD-2A
  authority.
- **Email** — accept-url shape, brand/role rendering, verified-only sender,
  no-firm → no custom sender.
- **Org plane** — create persists role; role validation (422); admin-only (403);
  list shows derived state; accept creates the membership with the invited role;
  single-use (409); email mismatch (403); expired (410); revoked (409); unknown
  token (404); unauthenticated (401).
- **Role admin** — role change is org-scoped (403 cross-tenant); owner may
  change a role (200); ordinary member denied (403); a client role cannot be
  escalated to `consultant`/`staff`/`super_admin`/`ceo` (422).
- **Consultant plane** — create/list/revoke; token is never returned; no
  `manage_clients` (403); inactive grant (403); cross-firm (403); invalid role
  (422); role assignment is client-org-scoped (404 outside the client).
- **Token security** — consultant list never exposes `token`/`accept_url`;
  org-admin may see the link but an ordinary member cannot (403); a consultant
  holding the raw token still cannot accept (403, email-bound); `consume()` is a
  conditional `UPDATE` with no preceding `SELECT`; concurrent consumption yields
  exactly one winner.

Frontend — `frontend/src/__tests__/accept-invitation.test.jsx` (6 tests):
a link without a token is reported safely; an unauthenticated invitee is offered
sign-in/sign-up; signing in transitions to acceptance and lands on the
workspace; an existing session auto-accepts; expired and reused invitations
show safe errors and do not redirect.

Auto-start — see §12 (unit parse, start/stop/restart, duplicates, disable/enable).

Run:

```bash
cd backend && .venv/bin/python -m pytest \
  tests/unit/api/test_ct_consultant_client_identity_04.py -q
cd frontend && CI=true npx react-scripts test --watchAll=false \
  --testPathPattern='accept-invitation'
```

### Regression status

Full `tests/unit/api` suite: **2714 tests, exit 0 (all passed)** on this run.
The previously observed failure
`test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
(`verification_delivered`) is **environment-dependent** and did not reproduce in
this run; it was separately confirmed to fail on the pristine baseline with CT04
changes stashed, so it is not attributable to CT04 in either case.

Frontend — related suites (`api.test.js`, `App.test.js`): 7 suites / 92 tests
passed. CT04 acceptance journey: 6 tests passed.

---

## 7. Security verification

- Identity is never self-inserted: acceptance requires an authenticated email
  match, and the consultant plane cannot create a membership directly.
- Single-use: the atomic conditional UPDATE is the only consumption path; the
  derived `expired` state cannot be consumed.
- Tenant isolation: every org-plane route calls `ensure_org_access`; the
  member-role route now resolves the target member and org-scope-checks it.
- Consultant boundaries: `ensure_consultant_permission("manage_clients")` plus
  `ensure_consultant_org_access` (ACTIVE grant, D15); cross-firm access is 403.
- The invitation token is not issued to the consultant plane (PD-1A).
- The frontend is not a security boundary: every rule is enforced server-side.

---

## 8. Invitation Token Security

**The consultant never receives the raw invitation token. Verified.**

`describe_invitation()` is the single projection used by both planes:

```python
if redact_token:
    view.pop("token", None)
    view.pop("accept_url", None)
    return view
```

| surface | token / accept_url |
| --- | --- |
| `POST /api/v3/consultants/clients/{cid}/invitations` (create) | **absent** (`redact_token=True`) |
| `GET  /api/v3/consultants/clients/{cid}/invitations` (list) | **absent** (`redact_token=True`) |
| consultant-plane *detail* route | does not exist — nothing to expose |
| `POST /api/v3/organizations/{org}/invitations` (org create) | present — `require_org_admin()` (owner/admin) only |
| `GET  /api/v3/organizations/{org}/invitations` (org list) | present — `require_org_admin()` only |

The asymmetry is deliberate and matches PD-1A: the **client owner/admin is the
inviting authority** for their own organisation and may hand the invitee a link;
the consultant plane, which acts *on the client's behalf*, never receives the
bearer token. The token itself is never authority — acceptance additionally
requires an authenticated **email match** (`403` on mismatch) and is **single-use**
(`consume()` is an atomic conditional `UPDATE`; a second attempt → `409`; a stale
token → no row). Cross-tenant access is denied (`ensure_org_access` /
`ensure_consultant_org_access`), and unknown/expired/revoked tokens return
`404` / `410` / `409` respectively.

Browser network responses therefore never carry the token on the consultant
plane, React state never stores it there, and the consultant cannot accept an
invitation using consultant-side data (`test_consultant_cannot_accept_even_holding_the_raw_token`).

---

## 9. Copy Link Semantics

The `MembersTab.jsx` **"Copy link"** control belongs to the **organisation-admin
plane** (`frontend/src/v3/admin/MembersTab.jsx`, reached via `AdminPage`), which is
guarded by `require_org_admin()` server-side and by `ProtectedRoute` +
`RoleRoute requireOrg` client-side. It copies `invitation.accept_url`, i.e.

```
{CARBONTALLY_APP_BASE_URL}/accept-invitation?token=<single-use token>
```

for a **pending** invitation only. That is exactly the intended behaviour: the
organisation owner/admin who created the invitation is the responsible inviting
party and may forward the link to the invitee.

There is **no consultant-side equivalent control**: the consultant-plane client
invitation helpers in `frontend/src/v3/api.js` (`listClientInvitations`,
`createClientInvitation`, `revokeClientInvitation`, `updateClientUser`) are
exported for the consultant workspace but are not yet consumed by a consultant
component, and the endpoints they call are redacted. The consultant plane
therefore has no control that could copy a bearer token.

---

## 10. Client Acceptance UX

**Implemented.** A public route renders the invitee's journey:

- route: `/accept-invitation` (added to `PUBLIC_ROUTE_PREFIXES`; the invitee may
  be unauthenticated when they open the link)
- component: `frontend/src/AcceptInvitation.jsx` (+ `css/AcceptInvitation.css`,
  D21 tokens only)

Behaviour:

1. the single-use token is read from the link (`?token=…`) and kept in
   `sessionStorage` (never `localStorage`) so an email-confirmation round-trip
   resumes;
2. a link without a token shows a safe "This link is incomplete" state;
3. the invitee signs **in** or **up** with the invited email using the existing
   Supabase Auth (`signInWithPassword` / `signUp` / Google OAuth). No second
   authentication system is introduced and CarbonTally never stores a password;
4. on an existing/arriving session the token is exchanged via
   `POST /api/v3/organizations/invitations/accept`; the backend enforces the
   email binding, expiry and single-use rules;
5. success shows "Invitation accepted" and redirects through
   `goToWorkspace()` to the actor's server-authoritative workspace (the client
   portal);
6. `404` / `409` / `410` / `403` map to safe, generic copy — invalid link,
   already used/withdrawn, expired, wrong email — and **no tenant existence
   information** (no organisation name/id) is displayed before a successful
   authenticated acceptance.

The frontend remains a UX layer only: it cannot create a membership the backend
would refuse.

---

## 11. Local Demo Lab Auto-Start

**Mechanism (local-development only):** a `systemd --user` unit. It is *installed
and enabled* so the local Demo Lab returns by itself after a PC restart/reboot
with no manual terminal commands.

| item | value |
| --- | --- |
| tracked source | `tools/demo_lab/systemd/carbontally-demo-lab.service` |
| installed copy | `~/.config/systemd/user/carbontally-demo-lab.service` |
| service name | `carbontally-demo-lab.service` |
| manager | user-level systemd (`systemctl --user`) |
| boot persistence | `loginctl enable-linger "$USER"` (currently `Linger=yes`) |
| `ExecStart` | `/usr/bin/python3 <repo>/tools/demo_lab/supervise_demo_lab.py run --ensure-containers` |
| restart policy | `Restart=always`, `RestartSec=10` |

**Why foreground `run`, not `start`:** `start` detaches a supervisor, which
systemd cannot track (it would spawn a competing supervisor on every restart).
`run` is the foreground supervisor, so the service owns the whole process tree.

**Startup order**

1. `network-online.target` (`After=`).
2. Docker is already enabled at boot; every local container is created with
   `--restart unless-stopped`, so the Supabase stack and the three disposable
   lab containers return on their own.
3. `--ensure-containers` starts any *stopped* disposable lab container
   (idempotent; fail-closed if a *required* container is absent).
4. The supervisor starts the release backend (`backend/.venv/bin/uvicorn
   main:app` on `127.0.0.1:8070`) then the frontend
   (`frontend/node_modules/.bin/react-scripts start`, `PORT=3000`).

**Commands**

```bash
# status
systemctl --user status carbontally-demo-lab.service
python3 tools/demo_lab/supervise_demo_lab.py status

# logs
journalctl --user -u carbontally-demo-lab.service -f
python3 tools/demo_lab/supervise_demo_lab.py logs [backend|frontend|supervisor]

# restart / stop / disable / enable
systemctl --user restart carbontally-demo-lab.service
systemctl --user stop    carbontally-demo-lab.service
systemctl --user disable carbontally-demo-lab.service
systemctl --user enable --now carbontally-demo-lab.service
```

**Security boundaries**

- localhost only: backend `127.0.0.1:8070`, frontend `http://localhost:3000`,
  gateway `127.0.0.1:54430`.
- no production configuration and no production secrets: the backend environment
  is read from `~/ct_local_env/demo_lab/backend.env` (generated locally,
  mode `0600`, outside the repository). The unit references no hosted
  Supabase/Render/Vercel endpoint.
- **no duplicate instances:** the supervisor's pid file is a single lock — a
  second supervisor refuses to start, so systemd and a manual `start` cannot
  produce two backends or two frontends.

**Prerequisites the unit relies on** (pre-existing, not created by it):
`backend/.venv`, `frontend/node_modules`, and
`~/ct_local_env/demo_lab/backend.env` (from
`python3 tools/demo_lab/lab_env.py --write`). Without `backend.env` the service
logs a clear `missing lab backend environment` error and retries.

---

## 12. Auto-Start Verification

Performed on this workstation against the **running** service (localhost only).

| # | check | result |
| --- | --- | --- |
| A | unit parses (`systemd-analyze --user verify`) | PASS (rc=0) |
| B | service starts (`start`) | PASS (rc=0) |
| C | dependencies start | PASS (containers already running; `--ensure-containers` reported them correctly) |
| D | backend available | PASS (`GET /health` → 200 within 5 s) |
| E | frontend available | PASS (`GET /` → 200 within 5 s) |
| F | no duplicate processes | PASS (supervisor=1, uvicorn=1, node=1 — also after a manual `start` attempt) |
| G | restart works | PASS (healthy in 15 s; counts 1/1/1) |
| H | stop works | PASS (ports 8070/3000 free; counts 0/0/0) |
| I | start works again | PASS (healthy in 5 s) |
| J | disable works | PASS (`is-enabled` → `disabled`) |
| K | enable works | PASS (`is-enabled` → `enabled`) |
| L | no production endpoint referenced | PASS (unit + supervisor clean) |

Raw evidence (recorded during the run):

```
=== I. start ===            start rc=0 ; healthy after 5s (backend=200 frontend=200) ; counts supervisor=1 uvicorn=1 node=1
=== F. duplicate prevention ===  manual start while service owns it → counts supervisor=1 uvicorn=1 node=1
=== G. restart ===          restart rc=0 ; healthy after 15s ; counts 1/1/1
=== H. stop ===             stop rc=0 ; ports 8070/3000 free ; counts 0/0/0
=== J/K. disable / enable ===   disabled → enabled
=== restart after disable+enable === healthy after 15s ; active=active enabled=enabled
=== linger ===              Linger=yes
=== L. no production endpoints === unit + supervisor: no production reference
```

**REAL REBOOT VERIFICATION NOT PERFORMED.** A machine reboot would disrupt the
working session, so it was not executed. The strongest safe equivalent was run:
the unit is `enabled`, linger is active, and full start/restart/stop/disable/
enable cycles were exercised with the service actually serving the backend and
frontend. Boot behaviour is inferred from `WantedBy=default.target` +
`Linger=yes` + `Restart=always` + Docker's boot-time restart policy for the
containers. This is not a substitute for an observed reboot.

Environmental note (not a defect): an *optional* container,
`supabase_studio_carbon_ledger`, failed to start during `--ensure-containers`
with `Address already in use`. It is not required by the lab, the supervisor
continued correctly, and the backend/frontend reached healthy.

---

## 13. Remaining Gaps

- **Consultant-side invitation UI.** The consultant-plane client-invitation
  helpers exist in `frontend/src/v3/api.js` but no consultant component consumes
  them yet, so a consultant cannot yet create/list/revoke a client invitation
  from the UI (the endpoints and their authorisation are implemented and
  tested). `MembersTab` (org-admin plane) is the only invitation UI today.
- **PO DECISION REQUIRED (unchanged)** — the decision register states "Consultant
  never receives passwords/tokens"; CT04 interprets the invitation token as
  covered by that rule and redacts it from the consultant plane. If the PO
  intends the consultant to be able to copy/forward the raw link, that is a
  policy choice to confirm. Until then the consultant plane exposes no token and
  has no Copy-link control.
- **Email provider.** Invitation email delivery is best-effort and reported
  honestly; end-to-end delivery requires configured provider settings
  (`email_provider`), out of scope here.
- **Real reboot verification** — see §12 (not performed; safe equivalent run).
- **Pre-existing, unrelated test failure** —
  `test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin`
  (`verification_delivered`) fails on the pristine baseline too; it is not
  introduced by CT04.
- No changes were made to RLS policies; schema changes are additive columns and
  an index only.





