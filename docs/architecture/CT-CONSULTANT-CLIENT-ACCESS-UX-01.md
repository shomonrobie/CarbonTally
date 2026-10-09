# CT-CONSULTANT-CLIENT-ACCESS-UX-01
## Consultant Client Access UI + CT-04 Consultant API Wiring

**Task ID:** CT-CONSULTANT-CLIENT-ACCESS-UX-01
**Date:** 2026-10-07
**Scope:** Frontend UX + API wiring (consultant plane). No new backend policy,
no migration, no PO decision reopened.
**Closes:** CoStrict finding **F3** (info / scope gap) from
`CT-CONSULTANT-CLIENT-IDENTITY-INDEPENDENT-VERIFY-01`.

---

## 1. User-reported problem

A consultant operating a managed client navigated to the client's
**Organisation** area and found a **"Members & Invitations"** tab. That is an
*Organisation-administration* surface, and it is the wrong plane for a
consultant. Attempting to send an invitation produced:

> You don't have permission to access this area.

The consultant reasonably expected to be able to invite their client to the
client's own CarbonTally dashboard. The correct consultant workflow is:

```
Consultant -> Managed Client -> Client Access -> Invite Client
          -> enter client email -> choose access level -> Send Invitation
          -> pending invitation -> client accepts -> client dashboard
```

## 2. CoStrict finding F3 (verified)

> **F3 — INFO / scope gap:** "Consultant-side client-invitation UI is not wired."
>
> The consultant API helpers/endpoints already exist and are server-gated
> (`listClientInvitations`, `createClientInvitation`, `revokeClientInvitation`,
> `updateClientUser`), but no consultant UI component consumes them. The visible
> "Members & Invitations" UI is an Organisation/admin surface and is **not** the
> correct consultant-plane implementation.

F3 is a **wiring** gap, not an authorisation defect. The fix is to wire the
existing, server-gated endpoints into the consultant plane — **not** to grant
consultants Organisation-admin privileges.

## 3. Root cause (current code, verified)

The consultant client operating plane renders the shared customer
Organisation-admin page directly:

* `frontend/src/App.js` — route
  `/consultant/clients/:clientId/organization` renders `<AdminPage />` inside
  `ClientOrgShell`.
* `AdminPage` (`frontend/src/v3/admin/AdminPage.jsx`) shows the tab
  **"Members & Invitations"**, which renders `MembersTab`.
* `MembersTab` (`frontend/src/v3/admin/MembersTab.jsx`) calls the
  **ORGANISATION-scoped** helpers on `organization.id`:

  | UI action | helper | backend route | gate |
  |-----------|--------|---------------|------|
  | list members | `listMembers` | `GET /api/v3/organizations/{org}/members` | `require_org_member()` |
  | create invitation | `createInvitation` | `POST /api/v3/organizations/{org}/invitations` | `require_org_admin()` |

A consultant is **not** an organisation member (AGENTS.md §29 — the client id in
the URL is re-authorised against the consultant-client grant, not a membership).
The org-scoped endpoint therefore returns **403**, and `v3Fetch`'s
`friendlyError(403)` in `frontend/src/v3/api.js` maps any 403 to
*"You don't have permission to access this area."*

**So the error was correct security behaviour on the wrong surface.** The
consultant should never have been routed to the org-member/org-admin endpoints.

## 4. Old path vs new path

| | OLD (wrong plane) | NEW (correct plane) |
|---|---|---|
| Surface | Organisation "Members & Invitations" | Client plane **"Client Access"** |
| Component | `admin/MembersTab.jsx` | `consultant/ClientAccessTab.jsx` |
| API | `listMembers`, `createInvitation`, `updateMember`, `removeMember` on `/organizations/...` | `listClientUsers`, `listClientInvitations`, `createClientInvitation`, `revokeClientInvitation`, `updateClientUser` on `/consultants/clients/{id}/...` |
| Gate | `require_org_member()` / `require_org_admin()` | `require_consultant` + `manage_clients` + ACTIVE consultant-client grant |
| Result for a consultant | **403** | **201 / 200** for an authorised consultant |

No consultant-facing code path now calls the org-admin invitation endpoints, and
no org-admin permission is granted to consultants.

---

## 5. Client Access UX

`frontend/src/v3/consultant/ClientAccessTab.jsx` (D21 tokens; reuses the existing
admin card/table primitives):

* Title **"Client Access"**.
* Copy: *"Invite your client to access their CarbonTally dashboard and manage
  authorised client users."*
* Primary CTA: **"+ Invite Client"** (reveals the invite form).
* **Pending Invitations** table — `Email | Access | Status | Action`.
* **Client Users** table — `User | Access | Status | Action`.

Empty, loading, denial and action-error states are all explicit (§48 / §46).
A 403 on load renders a controlled message (never a raw error, never a crash).

`AdminPage` is now consultant-aware: inside the client plane (`consultantClientId`
set via `useConsultantClientContext`) the members tab is relabelled
**"Client Access"** (same tab id, so `?tab=members` deep links keep working) and
renders `ClientAccessTab`; outside the client plane it renders the unchanged
`MembersTab`. `listOrgRoles` is not probed in the client plane (a consultant is
not an org member, so the probe would emit a 403).

## 6. Invite Client workflow

```
Client Access -> + Invite Client
  Email address [ client@example.com ]
  Client access [ Client Member v ]
  [ Send Invitation ]
```

* Calls `createClientInvitation(clientId, { email, role })`.
* The consultant **never** enters or sees a raw `user_id`, an internal
  Organisation id, a consultant firm id, an invitation token, or an accept URL.
* The existing CT-04 single-use invitation lifecycle is reused unchanged
  (email-bound, expiring, revocable, atomic consumption).

## 7. Role terminology

The database role vocabulary is unchanged (`owner/admin/member/viewer`,
`organization_members.role` CHECK constraint, PD-2A `client_identity.CLIENT_ROLES`).
Only the **presentation** label changes:

| DB role | UI label | Description shown |
|---------|----------|-------------------|
| `owner` | Client Owner | Full control of the client organisation and its users |
| `admin` | Client Admin | Manage client users and organisation settings |
| `member` | Client Member | Contribute data and view reports |
| `viewer` | Client Viewer | Read-only access |

No second role system is introduced. The UI offers exactly the four roles the
backend accepts.

## 8. `user_id` decision

The consultant plane does **not** expose a raw `user_id` control and does **not**
provide an "Add existing user" search. No safe, tenant-scoped existing-user
search API exists, and AGENTS.md §11 / task §11 forbid creating a global
user-directory / broad user-enumeration capability.

**Decision (permitted by task §11):** make **Invite Client by email** the primary
and only normal workflow; keep the secure backend behaviour; document that
"add existing user" is intentionally not implemented in the consultant plane.
The consultant is never forced to understand CarbonTally user ids.

## 9. Security invariants preserved (no CT-04 regression)

* Consultant plane responses **redact** `token` and `accept_url`
  (`describe_invitation(redact_token=True)`); the new UI renders neither, has no
  "Copy link", and keeps no bearer token in React state.
* Invitations remain **single-use, expiring, revocable, email-bound, atomic,
  cross-tenant-safe** — the UI change touches none of this.
* The org-admin plane's existing "Copy link" behaviour is untouched and is **not**
  carried into the consultant plane.
* A consultant manages the client's users but gains **no client data access**
  (PD-2A); the write path re-resolves the target member through the real
  organisation membership store and verifies it belongs to the authorised client.

## 10. Tenant isolation

Enforced entirely server-side (`require_consultant` + `manage_clients` +
`_authorized_client_org`, D15 — an inactive/ended grant denies access):

| Actor | Action | Expected |
|-------|--------|----------|
| Consultant Firm A → its Client A | invite/manage | ALLOW |
| Consultant Firm A → Client B (Firm B) | invite/manage | DENY (403) |
| Consultant without `manage_clients` | invite | DENY (403) |
| Client organisation member | consultant endpoint | DENY (403) |
| Unauthenticated | consultant endpoint | 401 |
| Expired/ended grant | invite | DENY (403) |

Confirmed by the backend assertion suite (see §12). The frontend is not, and is
not treated as, the security boundary (§44).

## 11. Browser verification

A real headless-Chrome walkthrough script accompanies this task:
`tools/demo_lab/verify_consultant_client_access_browser.py` (real password login
against the local lab GoTrue, no token injection). It drives the consultant →
managed client → **Client Access** path and asserts the page title, the
**"+ Invite Client"** CTA, the email-based invite (no `user_id`), the pending
invitation, the absence of any token/accept link, and that a direct customer
still sees **"Members & Invitations"**. Screenshots are written to the lab
evidence directory.

**Result (this environment): 20 checks passed, 0 failed.** Screenshots at
`~/ct_local_env/demo_lab/evidence/browser/ct_client_access_*.png`.

**Lab pre-condition discovered during verification:** the local Demo Lab database
(`carbontally_demo_local`) was provisioned *before* the CT-04 migration existed,
so `public.user_invitations` was missing the CT-04 columns (`role`,
`invited_by_firm_id`, …). That made `repos.invitations.list_for_org` raise
`UndefinedColumnError` → a 500 surfaced in the browser as an opaque CORS
"Failed to fetch". The lab rebuilds from `supabase/migrations/*.sql` with no
tracking table, so the fix was to (re)apply the additive, idempotent CT-04
migration to the disposable lab DB:
`docker exec -i supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -v ON_ERROR_STOP=1 < supabase/migrations/20261104000000_ct_consultant_client_identity_04.sql`.
This is an **environment** gap, not a code defect; the CT-04 migration is correct
and additive and remains the only schema change required. The full lab should be
re-provisioned (`tools/demo_lab/stack.py`) so its schema tracks HEAD.

---

## 12. Test results

**Backend** (`backend/.venv/bin/python -m pytest`, from `backend/`):

| Suite | Result |
|-------|--------|
| `tests/unit/api/test_ct_consultant_client_identity_04.py` | **52 passed** (50 + 2 added) |
| `tests/unit/api` (full) | **2716 passed** (was 2714) |

Two boundary cases were added to the CT-04 file (no backend code changed):

1. `test_client_user_is_denied_on_the_consultant_endpoint` — a client org member
   is denied (403) on `POST /consultants/clients/{id}/invitations`.
2. `test_unauthenticated_is_rejected_on_the_consultant_endpoint` — 401.

The pre-existing CT-04 coverage already asserts, on the same endpoints: create
with `manage_clients` (201), deny without `manage_clients` (403), deny a foreign
firm's client (403), deny an inactive grant (403), email-binding on accept,
token redaction in the consultant plane, pending list, revoke, role assignment,
member-outside-client denial, invalid-role 422, and cross-tenant role denial.

**Frontend** (`react-scripts test` from `frontend/`):

| Suite | Result |
|-------|--------|
| `src/v3/__tests__/consultant-client-access.test.jsx` | **10 passed** |
| Full frontend suite | **613 passed / 1 pre-existing unrelated failure** (`dr007-investor-display-fixes.test.jsx:107`) |

The new suite covers the required UI cases: Client Access page renders, Invite
Client form renders, email submission calls the **consultant** API (and not the
org API), no raw `user_id` required, pending invitations render (with no token /
accept URL in the DOM), revoke calls the consultant API, role change calls the
consultant API, role list is exactly the four client roles, a 403 renders a
controlled message, the client-plane tab is **"Client Access"** while the
direct-customer plane keeps **"Members & Invitations"**.

## 13. Files changed

New:

* `frontend/src/v3/consultant/ClientAccessTab.jsx` — consultant-plane Client Access UI.
* `frontend/src/v3/__tests__/consultant-client-access.test.jsx` — UI wiring tests.
* `docs/architecture/CT-CONSULTANT-CLIENT-ACCESS-UX-01.md` — this document.
* `tools/demo_lab/verify_consultant_client_access_browser.py` — browser verification.

Modified:

* `frontend/src/v3/admin/AdminPage.jsx` — consultant-aware members tab.
* `frontend/src/v3/api.js` — added `listClientUsers`; 204 empty-body guard in `v3Fetch`.
* `frontend/src/v3/admin/admin.css` — small D21 styles for the Client Access tab.
* `backend/tests/unit/api/test_ct_consultant_client_identity_04.py` — 2 boundary tests.

**No backend application code was changed.**

## 14. Migrations

**None.** The CT-04 consultant invitation/user-management backend already existed
in full. No new tables, no duplicate identity/invitation tables, no schema change.

## 15. Git state

Worked on branch `p8-release-reconciled` from starting HEAD
`3fec874ca1f170ecb03e7daf69992dbf9e9cd18e`. The worktree was (and remains)
intentionally dirty with unrelated in-progress work; all of it was preserved
(no reset / clean / stash / rebase). Ending HEAD and full file list are recorded
in the final report. No commit was made (not instructed).

## 16. Remaining gaps

1. **"Add existing client user"** is intentionally not implemented — it would
   require a safe, tenant-scoped existing-user search that does not exist (§8).
2. **P3 audit-trail gap** (CoStrict): CT-04 invite/accept/revoke and client-user
   role changes are not appended to the central `repos.audit` trail. This is a
   pre-existing, task-external gap; wiring the UI introduces **no new** audit
   requirement (the same domain provenance as before). Retained for a later
   closure task; not silently expanded into scope here.
3. **PO decision open:** whether a consultant may copy/forward a raw invite link.
   The consultant plane never exposes one (CT-04 invariant); no change made.
4. **Browser walkthrough** depends on the local Demo Lab being up; if it cannot
   be run headlessly here, the deterministic backend + frontend suites stand in
   and the browser step is reported as PENDING (not PASS).

## 17. Relationship to CT-04

CT-CONSULTANT-CLIENT-IDENTITY-04 delivered the consultant-side endpoints and the
token-security invariants. **This task consumes them, unchanged.** It adds no new
endpoint, no new policy, and no new authorisation rule; it removes the accidental
route through the org-admin surface. The CT-04 security contract is a hard
constraint here and is re-asserted by the added boundary tests (§12) and the
UI's refusal to render any token/accept link (§9).

## 18. Relationship to CT-05

CT-05 (White-Label email) is **out of scope** and untouched. This task reuses the
existing CT-04 invitation/email service as-is: firm-level branding, mode/entitlement
gated, verified-sender only, platform fallback, no per-client branding.


