# CT-CONSULTANT-CLIENT-IDENTITY-INDEPENDENT-VERIFY-01

**Independent verification of CT-CONSULTANT-CLIENT-IDENTITY-04**
(Client-user invitation lifecycle PD-1A, client-user role administration PD-2A,
white-label invitation email, and Demo Lab auto-start)

- **Task ID:** CT-CONSULTANT-CLIENT-IDENTITY-INDEPENDENT-VERIFY-01
- **Date:** 2026-10-07
- **Repository:** /home/shomonrobie/ct_93d5cdd
- **Branch:** p8-release-reconciled
- **Verifier:** CoStrict (independent — not the implementation agent)
- **Verdict class:** independent verification report (NOT a PO acceptance)

---

## 1. Task ID

CT-CONSULTANT-CLIENT-IDENTITY-INDEPENDENT-VERIFY-01 — independent verification
of CT-CONSULTANT-CLIENT-IDENTITY-04.

## 2. Date

2026-10-07.

## 3. Repository

`/home/shomonrobie/ct_93d5cdd` (local Demo Lab workstation; localhost only).

## 4. Branch

`p8-release-reconciled`.

## 5. HEAD

- Actual HEAD (verified): `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`
  (`docs(CT-HANDOVER-2026-10-05-CHECKPOINT-01): add 2026-10-05 master handover checkpoint`).
- Handoff brief states the expected HEAD as
  `3fec874ca1f170ec03e7daf69992dbf9e9cd18e`.

**Observation (INFO, not a defect):** the brief's expected-HEAD string is 41 hex
characters and does not match the actual 40-character commit id; the two strings
agree on the visible prefix `3fec874ca1f170ec…` and differ only in that the brief
appears to contain a stray `0`. The checked-out HEAD corresponds to the same
commit the brief describes (2026-10-05 handover checkpoint). No re-verify was
possible from a shorter SHA, so the discrepancy is recorded as a documentation
transcription artefact, not a state divergence.

## 6. Initial worktree state

`git status --short` was captured before any action. The worktree was **already
dirty** prior to this verification (pre-existing state, unrelated to this task):

- Branch: `p8-release-reconciled`; HEAD `3fec874ca…18e`.
- 67 tracked files modified (`git diff --stat`: 67 files changed,
  7061 insertions(+), 903 deletions(-)).
- 244 total `git status --short` entries (modified + untracked).
- Notable tracked modifications relevant to CT-04:
  `backend/data/invitations.py`, `backend/data/organizations.py`,
  `backend/api/v3_consultants.py`, `backend/api/dependencies.py`,
  `backend/api/v3_organizations.py`, `frontend/src/v3/api.js`,
  `frontend/src/App.js`, `frontend/src/v3/admin/MembersTab.jsx`,
  `tools/demo_lab/stack.py`, `tools/demo_lab/supervise_demo_lab.py`.
- Notable untracked CT-04 additions:
  `backend/domain/client_identity.py`, `backend/services/client_invitations.py`,
  `backend/tests/unit/api/test_ct_consultant_client_identity_04.py`,
  `frontend/src/AcceptInvitation.jsx`, `frontend/src/css/AcceptInvitation.css`,
  `frontend/src/__tests__/accept-invitation.test.jsx`,
  `supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`,
  `tools/demo_lab/systemd/carbontally-demo-lab.service`.

CoStrict recorded this state and did not modify any tracked file.

## 7. Verification scope

Read-only independent verification of the effective authorization model

```
EFFECTIVE CLIENT ACCESS =
RELATIONSHIP ∩ CLIENT ROLE/CAPABILITY ∩ CLIENT ACCESS PROFILE
∩ CONSULTANT ENTITLEMENT ∩ PLATFORM AUTHORITY
```

for CT-04: invitation lifecycle (PD-1A), token confidentiality, Copy-link plane,
email binding, acceptance UX, dual-authority role administration (PD-2A),
privilege escalation, tenant isolation, `organization_members` invariant, client
access profile ceilings, client portal authorization, white-label sender,
API/database authorization, audit/provenance and the Demo Lab auto-start
service.

Out of scope (per the brief): fixing findings, modifying source/tests/migrations/
RLS/systemd/docs, production/hosted-Supabase/Render access, real external email,
machine reboot.

## 8. Authority sources

- `docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md` §1/§2 (PD-1A, PD-2A), §3 (profiles).
- `docs/architecture/CT-CONSULTANT-CLIENT-IDENTITY-04.md` (implementation/closure report — evidence to evaluate, not authority).
- `AGENTS.md` §7/§8/§17/§44/§70/§74.
- Current source (authoritative per AGENTS.md §2): `backend/domain/client_identity.py`,
  `backend/services/client_invitations.py`, `backend/data/invitations.py`,
  `backend/data/organizations.py`, `backend/data/tenant.py`, `backend/auth.py`,
  `backend/api/dependencies.py`, `backend/api/consultant_auth.py`,
  `backend/api/client_portal_auth.py`, `backend/api/v3_organizations.py`,
  `backend/api/v3_consultants.py`, `frontend/src/AcceptInvitation.jsx`,
  `frontend/src/v3/api.js`, `frontend/src/v3/admin/MembersTab.jsx`,
  `supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`,
  `tools/demo_lab/systemd/carbontally-demo-lab.service`,
  `tools/demo_lab/supervise_demo_lab.py`.
- Current runtime: local Demo Lab backend `127.0.0.1:8070`, frontend `http://localhost:3000`.

## 9. Methodology

1. Baseline `git status`/branch/HEAD.
2. Static read of the single policy module, the shared email/sender service, the
   repositories and every CT-04 API route, plus the guard family
   (`require_org_admin`, `require_org_member`, `ensure_org_access`,
   `require_consultant`, `ensure_consultant_permission`,
   `ensure_consultant_org_access`, `require_client_portal_context`).
3. Independent execution of CT-04 backend tests, the full backend
   `tests/unit/api` suite and the full frontend suite.
4. Live (localhost) probes against the running Demo Lab backend to confirm route
   existence and authentication gating, and live systemd/service inspection.
5. Classification of every result as PASS / FAIL / PARTIAL / NOT TESTED with the
   evidence, and refusal to accept any Cline claim without independent evidence.

## 10. CT-04 implementation claims

PD-1A: secure client-user invitations; single-use tokens; expiring; revocable;
email-bound acceptance; atomic membership creation; Supabase Auth reuse; consultant
-plane token redaction; white-label sender resolution.
PD-2A: consultant-side client-user administration; client owner/admin user
administration; permitted client roles; role-boundary enforcement; separation of
consultant roles from client roles.
Frontend: `/accept-invitation`; sign-in/sign-up then acceptance; safe
invalid/expired/reused handling.
Demo Lab: user-level systemd service; auto-start; supervisor ownership; duplicate
prevention; backend/frontend health.
Reported test counts: 50 CT-04 backend; 2714 unit/API; 6 accept-invitation;
92 related frontend; 603 frontend with 1 unrelated pre-existing failure.

## 11. Independently verified claims

| # | Claim | Independent result |
| --- | --- | --- |
| 1 | "consultant never receives raw token" | **VERIFIED** (code + route projection) |
| 2 | "Copy link is organisation-admin plane only" | **VERIFIED** (source) |
| 3 | "acceptance requires authenticated email match" | **VERIFIED** (source; unit test) |
| 4 | "single-use atomic UPDATE" | **VERIFIED** (source; unit test) |
| 5 | "concurrency exactly one winner" | **PARTIAL** — proven by construction + unit test; not re-run live |
| 6 | "cross-tenant denied" | **VERIFIED (static)** for member-role route; UNIT-verified matrix; **NOT re-run live with real JWTs** |
| 7 | "full unit/API suite 2714 passed" | **VERIFIED** (2714 collected/passed, 0 F/E, exit 0) |
| 8 | "frontend 603 passed with one unrelated failure" | **VERIFIED count** (603 passed / 1 failed); failure is in an unrelated suite |
| 9 | "systemd service active + enabled + healthy" | **VERIFIED live** |
| 10 | "exactly one supervisor / one uvicorn / one node" | **VERIFIED live** (1 supervisor, 1 uvicorn, 1 react-scripts + child) |

## 12. Invitation security results

Verified from `backend/domain/client_identity.py`, `backend/data/invitations.py`,
`backend/api/v3_organizations.py` (`accept_invitation`, lines 692–765):

- Invitation belongs to exactly one organisation (`organization_id` column) — YES.
- Belongs to the intended email (`email` column) — YES.
- Expires: `expires_at` persisted; effective `expired` **derived**, never stored
  (`resolve_invitation_state`, `domain/client_identity.py:116`).
- Revocable: `InvitationsRepository.revoke(..., revoked_by=)` (`data/invitations.py:148`).
- Single-use: `consume()` is a conditional `UPDATE … WHERE token=$1 AND status='pending'
  AND (expires_at IS NULL OR expires_at > NOW())` (`data/invitations.py:123`). No
  read-then-write race.
- Replay: second accept matches no row → `409` (`v3_organizations.py:743`).
- Malformed/unknown token → `404` (`v3_organizations.py:716`); expired → `410`;
  revoked/accepted → `409`.
- Concurrent acceptance: single winner guaranteed by the conditional UPDATE (unit
  test `consume()` "no preceding SELECT"); not re-executed live.
- Cannot create consultant membership: acceptance calls
  `accept_invited_membership` which inserts only into `organization_members`
  (`data/organizations.py:712`). No `consultant_firm_members`/`consultant_clients`
  write exists on the accept path.
- Cannot create CarbonTally staff membership: no such insert on the accept path.
- Cannot modify consultant relationship / commercial entitlement / white-label
  entitlement: none of those tables are touched on the accept path.
- Cannot target an arbitrary organisation: target org is the invitation row's
  `organization_id`; no request-supplied org id is used (`v3_organizations.py:754`).

## 13. Token confidentiality results

**Consultant plane redacts the token — VERIFIED.**

- `GET /api/v3/consultants/clients/{client_id}/invitations` returns
  `describe_invitation(r, redact_token=True)` (`v3_consultants.py:1915`).
- `POST /api/v3/consultants/clients/{client_id}/invitations` returns
  `describe_invitation(invitation, redact_token=True)` (`v3_consultants.py:1976`).
- `describe_invitation(..., redact_token=True)` pops both `token` and `accept_url`
  (`services/client_invitations.py:87`).
- No consultant-plane detail route exposes a token.
- `frontend/src/v3/consultant/*` renders no `token`/`accept_url` (only the
  unrelated `WhiteLabelTab.jsx` uses domain-verification TXT tokens).

**Organisation plane exposes the token/accept_url — by design (see §14).**

The repository projection surfaces `token` (`data/invitations.py:41`) only through
the two org-admin-guarded routes.

## 14. Copy Link results

- The only "Copy link" invitation control is in
  `frontend/src/v3/admin/MembersTab.jsx:245-252`, rendered only when
  `state === 'pending'` and `invitation.accept_url` exists.
- That component is the **organisation-admin** members surface (`AdminPage`),
  protected server-side by `require_org_admin()` on
  `GET /{org_id}/invitations` (`v3_organizations.py:626`), which returns
  `_invitation_view(r, include_accept_url=True)` (token-bearing).
- The consultant plane has **no** Copy-link control and its responses are
  redacted, so no consultant-plane token leak exists.
- The link becomes invalid after acceptance/revocation/expiry because those states
  are not `pending` and/or `consume()` refuses them.
- No consultant UI consumes `listClientInvitations`/`createClientInvitation`/
  `revokeClientInvitation`/`updateClientUser` yet (CT-04 §13 "Remaining gaps");
  the endpoints are implemented and server-gated but the consultant UI is absent.

**Conclusion:** contracting the Copy-link behaviour to the organisation-admin plane
is consistent with PD-1A ("Consultant never receives passwords/tokens"). The
consultant obtains no usable bearer token from any CT-04 surface. Note this is a
PO-policy-adjacent area; CT-04 itself flags it as a PO confirmation point and
CoStrict does not reopen it.

## 15. Email-binding results

`POST /api/v3/organizations/invitations/accept` requires `require_auth()` and
compares the authenticated email to the invited email
(`v3_organizations.py:731`), returning `403` on mismatch — **VERIFIED in source**
and by the CT-04 unit tests (`email mismatch (403)`).

- Test A (invited email + valid token) → success: covered by CT-04 unit test (accept creates the membership).
- Test B (different authenticated email + valid token) → `403`: covered by unit test.
- Test C (unauthenticated invalid/expired token) → `401` first (auth required):
  **live-verified** (accept with no/bad bearer → `401`).
- Test D (authenticated user from another org) → must not gain target-org access:
  covered by the email binding + org-derived target; not re-run live with a real
  foreign JWT.

Error responses are generic and disclose no tenant existence (bounded copy in
`frontend/src/AcceptInvitation.jsx` and simple backend detail strings).

## 16. Acceptance UX results

`/accept-invitation` is a public route (`frontend/src/App.js`,
`PUBLIC_ROUTE_PREFIXES`) rendering `frontend/src/AcceptInvitation.jsx`:

- Reads the single-use token from `?token=…`, keeps it in `sessionStorage`
  (`TOKEN_KEY`), never `localStorage` (`AcceptInvitation.jsx:29,60-67`).
- Offers Google OAuth and email/password sign-in or sign-up using the **existing**
  Supabase Auth (`supabase.auth.*`); no second auth system; CarbonTally stores no
  password.
- Auto-accepts on an existing/arriving session (`useEffect` + `onAuthStateChange`).
- Maps `404/409/410/403/401` to safe generic copy and shows **no** tenant
  existence information.
- Removes the token from `sessionStorage` on success; keeps it on failure so a
  retry can re-read it.

Frontend acceptance tests: **6/6 passed** (independently run).

**Observation (P3/informational):** the token remains in `sessionStorage` after a
*failed* acceptance until the tab/session ends. This is deliberate (retry/resume)
and bounded by the single-use + email-bound server rules, so it is a hardening
note, not a defect. Not changed (read-only verification).

## 17. PD-2A role administration results

- **Client plane:** `GET/POST /{org_id}/invitations` and
  `DELETE /invitations/{invitation_id}` and `PUT /members/{member_id}` are guarded
  by `require_org_admin()` (`v3_organizations.py:629,643,771,514`). `owner`/`admin`
  only (`require_org_admin` / `_org_admin_authority`). Roles validated against the
  single `CLIENT_ROLES` vocabulary via `validate_org_role` →
  `validate_client_role` (`v3_organizations.py:429`), returning `422` for anything
  else.
- **Consultant plane:** `GET/POST /clients/{client_id}/invitations`,
  `POST …/revoke`, `PATCH /clients/{client_id}/users/{member_id}` require
  `get_current_user` + `require_consultant` + `ensure_consultant_permission(context,
  "manage_clients")` + `_authorized_client_org` (active grant, D15)
  (`v3_consultants.py:1896-2032`).
- Provenance of consultant-created invitations recorded in
  `user_invitations.invited_by_firm_id` (`v3_consultants.py:1957`).
- Single role vocabulary reused; no second client-role system.

## 18. Privilege-escalation results

Static analysis of the write paths:

| # | Scenario | Result |
| --- | --- | --- |
| 1 | client owner → member/admin/viewer | allowed (within client roles) |
| 2 | client admin → permitted client role | allowed |
| 3 | client member/viewer → user administration | denied (`require_org_admin`) |
| 4 | client → consultant role | impossible — role validated against `CLIENT_ROLES` only (`422`) |
| 5 | client → CarbonTally staff role | impossible — same validation |
| 6 | consultant → client-to-consultant promotion | impossible — client plane only writes `organization_members` role ∈ client set |
| 7 | consultant → platform-staff promotion | no route writes staff roles |
| 8 | consultant → commercial entitlement | no CT-04 route touches entitlement |
| 9 | client → `consultant_firm_members` | no such write |
| 10 | client → `consultant_clients` | no such write |
| 11 | client → another organisation's membership | denied (`ensure_org_access`, see §19) |
| 12 | invalid role string | `422` (`validate_org_role` / `_validate_client_role`) |

`organization_members.role` CHECK is mirrored by `CLIENT_ROLES`
(`domain/client_identity.py:54`). No route can write a non-client role.

Covered by the CT-04 unit suite (role boundary `422`, escalations denied).

## 19. Tenant-isolation results

- `PUT /members/{member_id}` (`v3_organizations.py:510`) resolves the target member
  and calls `ensure_org_access(current_user, target["organization_id"])` before any
  update — the previously reported cross-tenant gap is **closed in source**. A
  client admin of Org A updating an Org B member id fails `ensure_org_access`
  (org A ≠ org B → `403`). If the member does not exist at all, `update_member`
  returns `None` → `404`.
- `GET /members/{member_id}` and `DELETE /members/{member_id}` likewise
  `ensure_org_access` on the resolved member's org.
- `GET/POST/DELETE` invitation routes call `ensure_org_access(current_user, org_id)`
  (org path) or `_authorized_client_org` (consultant path, which re-authorizes the
  consultant against the grant's org).
- `revoke_invitation` resolves the invitation and checks
  `ensure_org_access(current_user, invitation["organization_id"])`
  (`v3_organizations.py:777`). `revoke_client_invitation` compares the invitation
  org to the consultant's authorised client org (`v3_consultants.py:1998`).
- `_authorized_client_org` (`v3_consultants.py:1837`) re-checks the ACTIVE grant via
  `ensure_consultant_org_access` (`consultant_auth.py:269`), which requires
  `consultant_clients.status='active'` for the firm.

Live probe: unauthenticated calls to the accept and consultant-invitation routes
return `401`. Cross-tenant with a real foreign JWT was **not** re-run live (only
unit-tested), so this remains static + unit evidence.

## 20. organization_members invariant

- `organization_members` = customer organisation membership. Acceptance inserts
  here only (`data/organizations.py:712`, `accept_invited_membership`), targeting
  the invitation's org and the accepting user's own auth id.
- `consultant_firm_members` = consultant firm membership — never written by CT-04.
- `consultant_clients` = consultant↔managed-org relationship — never written by
  CT-04 (the client-plane create/invite paths never insert a consultant row).
- Consultant operators are **not** inserted into `organization_members` for managed
  clients; the consultant plane calls `repos.tenant.update_member` /
  `repos.invitations.*` only, and never `add_member`/`accept_invited_membership`
  for the firm itself.
- Client users are **not** inserted into `consultant_firm_members`.

Direct source inspection supports the invariant. Not re-verified against a live
PostgreSQL cross-tenant query in this pass.

## 21. Profile matrix

`backend/domain/relationship_access.py` + `backend/api/client_portal_auth.py`:

- OFF → `state_has_client_plane`/`has_client_login` denies; `profile_allows` read
  ops false.
- READ_ONLY → reads + comment only; no `upload_document`, `edit_master_data`,
  `approve_final` (`PROFILE_READ_ONLY` = `{OP_COMMENT}`).
- COLLABORATIVE → comment, upload, edit master data, correct submitted data,
  approve_final.
- MANAGED → read + comment only.
- RETAINED_READ_ONLY → reads only; no writes, no messaging-send.
- `CLIENT_FORBIDDEN_OPERATIONS = {map_factors, edit_mappings, recalculate}` are
  **always** denied in every profile/state (`relationship_access.py:120,169`).

CT-04 introduces no profile change and no bypass; authentication alone grants no
profile privilege. Covered by the CT-03 suite (`test_ct_consultant_model_03.py`),
part of the 2714-passing backend run.

## 22. Client portal results

`resolve_client_portal_context` (`client_portal_auth.py:80`):

- denies internal staff and entity staff (identity separation);
- requires the caller be an organisation member whose `organization_id` equals the
  route `client_id` (`:98-101`) — **clientId is not treated as identity**;
- requires a consultant relationship with a client plane active (ACTIVE or
  RETAINED) and a client-plane-entitled firm mode;
- exposes only a UI capability hint; enforcement is `ensure_client_operation`
  (profile ceiling).

Live full portal walkthrough (with real client users across two tenants) was **not**
executed in this pass; the result is source-verified and covered by the CT-03
suite.

## 23. White-Label sender results

`backend/services/client_invitations.py`:

- Brand is the **inviting firm's own** firm-level branding
  (`_resolve_brand(repos, firm_id)` → `get_branding(firm_id)`), else the
  CarbonTally fallback — never per-client branding.
- `resolve_brand_context` is **mode/entitlement gated** (`domain/branding.py:147`):
  a STANDARD (or bare) firm falls back to CarbonTally regardless of stray flags.
- Sender: `resolve_invitation_sender` returns only a **`status='verified'`** sender
  for the firm, validated against the sender's own domain, else `None` → platform
  sender (`client_invitations.py:148`). Unverified senders are never used.
- Delivery failures are reported honestly (`email_delivered: false`); a mail
  failure never breaks invitation creation and never invents success
  (`v3_organizations.py:674`, `v3_consultants.py:1963`).

Per-client branding is not introduced; branding never determines tenant identity.
No real external email was sent (constructs inspected + unit-tested only).

## 24. API authorization review

All CT-04 routes confirmed present in the live OpenAPI document and server-side
guarded:

| Route | Guard |
| --- | --- |
| `POST /api/v3/organizations/invitations/accept` | `require_auth()` + email binding (`v3_organizations.py:692`) — live: `401` unauthenticated |
| `GET /api/v3/organizations/{org_id}/invitations` | `require_org_admin()` + `ensure_org_access` (`:626`) |
| `POST /api/v3/organizations/{org_id}/invitations` | `require_org_admin()` + `ensure_org_access` (`:639`) |
| `DELETE /api/v3/organizations/invitations/{id}` | `require_org_admin()` + `ensure_org_access(target)` (`:768`) |
| `PUT /api/v3/organizations/members/{member_id}` | `require_org_admin()` + `ensure_org_access(target)` (`:510`) — **cross-tenant gap closed** |
| `GET /api/v3/consultants/clients/{id}/invitations` | `require_consultant` + `manage_clients` + active grant (`v3_consultants.py:1896`) — live: `401` unauthenticated |
| `POST /api/v3/consultants/clients/{id}/invitations` | same (`:1921`) |
| `POST …/invitations/{id}/revoke` | same (`:1982`) |
| `PATCH /clients/{id}/users/{member_id}` | same (`:2005`) |

The previously reported `PUT /members/{id}` cross-tenant vulnerability is closed in
source (§19).

## 25. Database / RLS review

`supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`:

- Additive + idempotent only: adds nullable columns `role`, `invited_by_firm_id`,
  `accepted_at`, `accepted_by`, `revoked_at`, `revoked_by` (`ADD COLUMN IF NOT
  EXISTS`).
- Adds CHECK `user_invitations_role_check` (owner/admin/member/viewer) — guard via
  `pg_constraint` existence check.
- Adds FK `invited_by_firm_id → consultant_profiles(id) ON DELETE SET NULL`
  (existence-guarded).
- Adds index `idx_user_invitations_org_status (organization_id, status)`.
- Comments document that `expired` is derived, never stored.
- **No** column drop/rename/retype; **no** privilege grant; **no** `DISABLE ROW
  LEVEL SECURITY`; **no** new permissive policy. The migration explicitly notes the
  table stays service-role-API only (deny-by-default). Columns are nullable so
  existing rows are untouched.

Migration not executed by CoStrict (read-only); assessed statically.

## 26. Audit / provenance review

- **Durable domain provenance exists:** the invitation row records `invited_by`,
  `invited_by_firm_id`, `created_at`, `accepted_by`, `accepted_at`, `revoked_by`,
  `revoked_at` (`data/invitations.py:29-56`); the membership row records the role.
- **Central audit-trail gap (finding F1, P3):** the CT-04 handlers do not append to
  the central `repos.audit` trail. `_record_audit` is defined
  (`v3_organizations.py:62`) and used elsewhere (e.g. `:232`, `:813`) but is **not**
  called by `create_invitation`, `accept_invitation`, `revoke_invitation` or
  `update_member`; likewise `_ct03_audit` in `v3_consultants.py` is used at
  `:596,:664,:709,:1765,:1808` but **not** by the new consultant invitation/role
  routes. Sensitive events (invitation create/accept/revoke, role change) are thus
  recorded only in the domain tables, not in the append-only audit log.
- No tokens/passwords appear in any audit payload (none are captured there).
- Actor and target organisation provenance is present in the domain rows.

Severity rationale: the business provenance required by AGENTS.md §17 is present in
the domain tables, so this is a defense-in-depth/central-audit completeness gap,
not a lost-provenance failure (hence P3, not P2).

## 27. Demo Lab systemd review

`tools/demo_lab/systemd/carbontally-demo-lab.service` (read; not modified):

- `[Unit]`: `After=network-online.target`, `Wants=network-online.target`.
- `[Service]`: `Type=simple`; `WorkingDirectory=%h/ct_93d5cdd`;
  `ExecStart=/usr/bin/python3 %h/ct_93d5cdd/tools/demo_lab/supervise_demo_lab.py run
  --ensure-containers`; `Restart=always`; `RestartSec=10`; `KillMode=mixed`;
  `TimeoutStopSec=40`.
- `[Install]`: `WantedBy=default.target`.
- Header documents localhost-only ports (backend `127.0.0.1:8070`, frontend
  `http://localhost:3000`, gateway `127.0.0.1:54430`), that the environment lives in
  `~/ct_local_env/demo_lab/backend.env` (mode 0600, outside the repo) and that the
  supervisor pid file is the duplicate guard.
- `tools/demo_lab/supervise_demo_lab.py` is stdlib-only; process discovery is
  strictly bounded to this lab's markers/ports; no production endpoints; no secrets.
  `run --ensure-containers` is the foreground supervisor (no detached competing
  supervisor).
- Live check: installed unit at
  `~/.config/systemd/user/carbontally-demo-lab.service` is **byte-identical** to the
  tracked source (`diff -q` → IDENTICAL).

## 28. Auto-start verification

Live inspection on this workstation (localhost only):

| Check | Result |
| --- | --- |
| `systemctl --user is-enabled` | `enabled` |
| `systemctl --user is-active` | `active` |
| `ActiveState`/`SubState` | `active` / `running` |
| `FragmentPath` | `~/.config/systemd/user/carbontally-demo-lab.service` |
| `UnitFileState` | `enabled` |
| `Restart` / `RestartUSec` | `always` / `10s` |
| `WorkingDirectory` | `/home/shomonrobie/ct_93d5cdd` |
| `loginctl … Linger` | `Linger=yes` |
| supervisor processes | 1 (`supervise_demo_lab.py run --ensure-containers`) |
| uvicorn processes | 1 (`main:app --host 127.0.0.1 --port 8070`) |
| node/react processes | 1 `react-scripts start` + its child `start.js` (single frontend) |
| backend health | `GET http://127.0.0.1:8070/health` → `200` |
| frontend health | `GET http://localhost:3000/` → `200` |
| no production endpoints / no secrets | unit + supervisor reference none |

No destructive restart was performed; the singleton property was confirmed by live
process counts (one supervisor/one uvicorn/one frontend). A manual duplicate-start
was **not** executed to avoid perturbing the running lab; the pid-file lock is
present in source and the live counts show no duplication.

## 29. Reboot verification status

**REBOOT PERSISTENCE = NOT VERIFIED.** No machine reboot was performed (would
disrupt the working session, and the brief forbids an unauthorised reboot). The
strongest safe equivalent observed: unit `enabled`, `Linger=yes`,
`WantedBy=default.target`, `Restart=always`, and a healthy running service. Boot
behaviour is inferred, not observed. This matches (and does not upgrade) the
implementation report's own "REAL REBOOT VERIFICATION NOT PERFORMED".

## 30. Test results

Independently executed by CoStrict on the current, unmodified tree:

- **CT-04 backend:** `tests/unit/api/test_ct_consultant_client_identity_04.py`
  → 50 passed, 0 failed (exit 0).
- **Full backend `tests/unit/api`:** 2714 collected, **2714 passed, 0 failures,
  0 errors**, exit 0 (verified via progress-dot count = 2714 and exit code 0; this
  environment's pytest suppresses the trailing summary line, but `[100%]` with only
  dots and `exit=0` establishes all-pass). Matches CLAIM 7.
- **Frontend acceptance:** `accept-invitation.test.jsx` → **6/6 passed**.
- **Full frontend:** **604 total, 603 passed, 1 failed**, exit 1. The single failure
  is `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` →
  "Issue 3 — customer review detail shows Mapped activity from mapped_data.activity"
  (expects `Natural gas`, received `Mapped activity`). That suite renders
  `customer/ProcessingItemWorkspace` and `customer/ReviewDetailPage`, which are
  **not** CT-04 files; CT-04's frontend changes are `v3/api.js`,
  `v3/admin/MembersTab.jsx`, `AcceptInvitation.jsx`, `AcceptInvitation.css`,
  `App.js`. Matches CLAIM 8's count (603 passed / 1 failed).

Failure classification:

- F2 (dr007 mapped-activity) → **unrelated to CT-04** (different feature area and
  files). Note the CT-04 report attributed the single frontend failure differently
  (it mentioned a backend `test_v3_discovery` pre-existing failure, which did **not**
  reproduce here — the backend suite is fully green). The frontend failure is real
  and reproducible on this tree; because it renders components CT-04 does not touch,
  it is classified E (unrelated), with the caveat that a pristine-baseline rerun to
  positively prove pre-existence was not performed (reverting is not permitted).

## 31. Browser results

- A full 20-step interactive browser walkthrough with real Demo Lab identities was
  **not** performed in this pass (no CT-04-specific browser script exists in
  `tools/demo_lab/`).
- Automated component-level acceptance evidence: 6/6 `accept-invitation` tests
  cover the key UI states (missing token, needs-auth, sign-in→accept→workspace,
  auto-accept, expired, reused).
- Live API probes (localhost) confirm the routes exist and are auth-gated
  (`401`).
- **NOT TESTED (browser):** live login as Consultant Firm A/B and Client A/B; live
  wrong-email acceptance; live reused/expired invitation in the browser; live
  cross-tenant portal; consultant/admin UI walkthrough. These are marked PARTIAL /
  NOT TESTED in the gate matrix rather than inferred from unit tests.

## 32. Finding register

| ID | Finding | Severity | Evidence |
| --- | --- | --- | --- |
| F1 | CT-04 invitation lifecycle (create/accept/revoke) and client-user role changes are not appended to the central audit trail (`repos.audit`); only domain-row provenance is recorded. | P3 (LOW) | `v3_organizations.py:62,232,813` (no call in 639–778); `v3_consultants.py:517` (no call in 1896–2032) |
| F2 | Frontend suite has one failing test (`dr007-investor-display-fixes.test.jsx`) unrelated to CT-04. | P3 (LOW) / pre-existing | `frontend` run: 603 passed / 1 failed; failing test renders non-CT-04 components |
| F3 | Consultant-side client-invitation **UI** is not wired (endpoints implemented + server-gated + tested, but no consultant component consumes them). | INFO / scope gap | CT-04 §13; grep of `frontend/src/v3/consultant/*` finds no consumer of `listClientInvitations`/`createClientInvitation`/`revokeClientInvitation`/`updateClientUser` |
| F4 | Handoff brief expected-HEAD string does not match the actual 40-char commit id (transcription artefact). | INFO | §5 |
| F5 | `sessionStorage` retains a failed-acceptance token until session end (deliberate; bounded by single-use + email binding). | P3 hardening | `AcceptInvitation.jsx:29,60-67,87` |

No P0/P1 finding was identified.

## 33. Severity classifications

- P0/CRITICAL: none.
- P1/HIGH: none.
- P2/MEDIUM: none.
- P3/LOW: F1 (central-audit completeness), F2 (unrelated failing test), F5
  (token-in-sessionStorage hardening).
- INFO: F3 (consultant UI gap), F4 (HEAD transcription).

## 34. Acceptance-gate matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| G1 PD-1A invitation lifecycle secure | PASS | §12 (source + 50 CT-04 tests) |
| G2 Invitation token not exposed to unauthorized actors | PASS | §13/§14 (redaction on consultant plane) |
| G3 Single-use & concurrency-safe | PASS (static+unit) / PARTIAL live | `consume()` conditional UPDATE; unit "exactly one winner"; live not re-run |
| G4 Email-bound | PASS | `v3_organizations.py:731`; live `401`; unit `403` |
| G5 Cross-tenant invitation use impossible | PASS (static+unit) / PARTIAL live | org-derived target; not re-run with foreign JWT |
| G6 PD-2A dual-authority enforced server-side | PASS | §17 (guards on every route) |
| G7 No client role grants consultant/platform privileges | PASS | §18 (`CLIENT_ROLES` validation → `422`) |
| G8 organization_members invariant | PASS (static) | §20 |
| G9 Client portal tenant isolation | PASS (static+CT-03 suite); NOT TESTED live | §22 |
| G10 Profile ceilings | PASS | §21 (`profile_allows`, PO-9 always-deny) |
| G11 White-Label sender entitlement/mode/verified gated | PASS (static) | §23 (`resolve_brand_context`, verified-only sender) |
| G12 No per-client branding introduced | PASS | §23 (firm-level only) |
| G13 Audit/provenance adequate | PARTIAL | §26 (domain provenance yes; central audit missing — F1) |
| G14 Direct customer behaviour intact | PASS (suite) | full backend + frontend direct-customer tests green except F2 |
| G15 Frontend acceptance flow works | PASS (component) / PARTIAL live | 6/6 tests; no full browser walkthrough |
| G16 Demo Lab auto-start service valid & healthy | PASS (service) / PARTIAL (boot) | §28; reboot NOT VERIFIED (§29) |
| G17 No production exposure/secrets | PASS | §27/§28 (localhost-only, env outside repo) |
| G18 Existing consultant navigation intact | PASS (suite) | consultant tests green in 2714 |
| G19 No blocking regression | PASS | backend 2714/2714; frontend 603/604 with unrelated F2 |
| G20 Worktree unmodified by CoStrict | PASS | §35 |

## 35. Worktree integrity

- Baseline captured before any action: branch `p8-release-reconciled`, HEAD
  `3fec874ca…18e`, dirty worktree (67 tracked modifications, 244 status entries).
- CoStrict modified **no** tracked file, test, migration, RLS policy, systemd file
  or documentation. Only `/tmp` scratch files were written by test runs.
- Final `git status --short` count remained **244**; `git diff --stat` remained
  **67 files changed, 7061 insertions(+), 903 deletions(-)**; HEAD unchanged.
- The single intentional worktree addition is **this verification report**
  (`docs/architecture/CT-CONSULTANT-CLIENT-IDENTITY-INDEPENDENT-VERIFY-01.md`), the
  required deliverable. It was confirmed absent before creation.

## 36. Limitations

1. No live browser walkthrough with real Demo Lab identities (§31); UI evidence is
   component-test + static.
2. No live cross-tenant request matrix using real foreign JWTs (§19); isolation is
   source- + unit-verified.
3. No live concurrency execution of single-use acceptance; proven by the
   conditional-UPDATE construction and unit test.
4. No live PostgreSQL/RLS query of `organization_members` invariant (§20); source-
   verified.
5. Reboot persistence inferred, not observed (§29).
6. Central-audit absence (F1) identified statically; not exercised live.
7. Positive "pre-existing" proof of the unrelated frontend failure would require
   reverting the dirty tree, which is not permitted.

## 37. Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS**

Rationale: no P0/P1 (blocking) finding was identified. The CT-04 client-identity
surface is enforced server-side — the consultant plane redacts the invitation
token, acceptance is authenticated + email-bound + single-use via an atomic
conditional UPDATE that targets only the invitation's own organisation, the
member-role route is org-scoped (the prior cross-tenant gap is closed), roles are
constrained to the single client-role vocabulary, the client portal keys off
identity+relationship rather than `clientId`, profile ceilings and PO-9 forbidden
operations are preserved, and white-label branding/sender are firm-level,
mode-gated and verified-only. The migration is additive and does not weaken RLS.
The Demo Lab user-level systemd unit is enabled, active, healthy, singleton, and
localhost-only. Independent test runs reproduce 2714/2714 backend and 603/604
frontend (the single failure is unrelated to CT-04).

Findings are non-blocking: F1 (central audit-trail completeness, P3), F2 (unrelated
frontend failure, P3), F5 (sessionStorage hardening, P3) and F3/F4 (INFO). The
explicitly unverified items (live browser/JWT adversarial matrix, live RLS
cross-tenant query, real reboot) are recorded as PARTIAL/NOT TESTED rather than
inferred from unit tests. A full live browser + foreign-JWT adversarial pass is
recommended before PO acceptance, but on the evidence gathered CT-04 is safe,
tenant-isolated and policy-compliant.

This is an independent verification verdict. It is **not** an acceptance — CoStrict
does not issue ACCEPTED / IMPLEMENTED / READY FOR PO ACCEPTANCE.
