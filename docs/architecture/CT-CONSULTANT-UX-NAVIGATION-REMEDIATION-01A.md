# CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A

**Consultant UX Context Cleanup, Team Administration and Client Task UX**

Status: **IMPLEMENTED_AND_LAB_VERIFIED** (self, local Demo Lab).
This is NOT independently verified, NOT PO-accepted and NOT production-ready.

---

## 1. Task ID

`CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A`

A narrow follow-up to `CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01` (which was
implemented and locally browser-verified). This task does **not** redo the
navigation redesign, does **not** redesign the consultant business model, and
does **not** change backend authorization/RLS/capabilities except where an
existing defect (a UI control the API rejects) genuinely required it.

---

## 2. Starting SHA

```
branch : p8-release-reconciled
HEAD   : 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
```

The worktree was already dirty from preceding work (the previous task was
intentionally left uncommitted). Those pre-existing modifications were
preserved untouched.

---

## 3. Ending SHA

```
branch : p8-release-reconciled
HEAD   : 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e   (unchanged — no commit)
```

No commit was made (not instructed). All work is worktree-only.

---

## 4. Worktree status

- HEAD is unchanged.
- No `git reset --hard`, no `git clean -fd`, no rebase, no force-push, no
  checkout of unrelated work.
- All pre-existing worktree modifications are intact.
- Files touched by THIS task are listed in §5 (tracked edits + new files). No
  unrelated change was absorbed.

---

## 5. Files changed

### Edited (tracked, pre-existing files)

| File | Change |
|---|---|
| `frontend/src/v3/components/V3Layout.jsx` | Shared-nav consultant entry label reverted to a constant `Consultant` (no `navPrefix`-conditional `Back to Consultant`). |
| `frontend/src/v3/consultant/ClientOrgShell.jsx` | Removed the in-workspace **Switch client** control; context bar now **displays** context only. |
| `frontend/src/v3/consultant/ConsultantPage.jsx` | Removed the global **Active client** selector/state; added a local **Client** selector inside the Client messages view only. |
| `frontend/src/v3/consultant/ConsultantTeamTab.jsx` | Add-member by **email**; real role vocabulary; role↔capability copy; firm-task **client** is now a human-readable select of authorised clients. |
| `frontend/src/v3/customer/DashboardPage.jsx` | Context-aware subtitle (consultant-operated vs direct customer). |
| `frontend/src/v3/api.js` | `addConsultantTeamMember` now takes `{ email \| user_id, role }`. |
| `backend/api/v3_consultants.py` | `FirmMemberCreate` accepts `email` **or** `user_id`; resolve-only email→identity helper; unchanged authorization. |
| `frontend/src/v3/__tests__/consultant-page.test.jsx` | AC-01 (no global Active client) assertions; stale switcher comment removed. |
| `frontend/src/v3/__tests__/consultant-client-org-shell.test.jsx` | Switch-client test inverted (now asserts ABSENCE); exactly-one Back-to-Consultant. |
| `frontend/src/v3/__tests__/consultant-team-capabilities.test.jsx` | New: email identity, real roles, human-readable task client. |

### Created (new files)

| File | Purpose |
|---|---|
| `backend/tests/unit/api/test_ct_consultant_ux_01a_team_identity.py` | Backend tests for the email identity path (6 tests). |
| `tools/demo_lab/verify_consultant_ux_01a_browser.py` | Real-Chrome browser verifier for this task (44 checks). |
| `docs/architecture/CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A.md` | This report. |

---

## 6. Files NOT changed (deliberately)

- `frontend/src/v3/consultant/ClientMessagingTab.jsx` — reused as-is; the local
  client selector was added by the hub, not by rewriting messaging.
- `frontend/src/v3/consultant/ConsultantClientContext.jsx` — reused as-is
  (relationship/portal labels are still the source of truth).
- `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx`,
  `WhiteLabelTab.jsx` — already firm-level; no client context existed.
- No RLS, no migration, no `consultant_clients` / `organization_members`
  semantics, no capability model, no commercial entitlement, no billing.
- `frontend/src/v3/consultant/ConsultantItemPage.jsx` — its `← Back to client
  processing` return path already lands inside the client plane (which carries
  the single "Back to Consultant"); left unchanged (R-NAV-1, see §19).

---

## 7. Root cause analysis

| # | Finding | Existing behaviour | Root cause | Minimal fix |
|---|---|---|---|---|
| F1 | Global "Active client" selector on every firm tab | `ConsultantPage` rendered a `v3-client-switcher` (label "Active client" + `<select aria-label="Select active client">`) driven by hub state `activeClientId` | Pre-parity design that treated the hub as a client-scoped surface; it survived the –01 redesign | Remove the switcher + hub `activeClientId`; keep only the firm identity banner |
| F2 | "Switch client" dropdown inside the workspace | `ClientOrgShell` ContextBar rendered a switch `<select>` when >1 authorised client | Added by –01 (UX-04) but superseded by "Clients → Open workspace" | Delete the switch block; the plane displays context only |
| F3 | Two "Back to Consultant" controls | Context bar link **and** `V3Layout` nav entry both read "Back to Consultant" in the plane | –01 made the nav label `navPrefix ? 'Back to Consultant' : 'Consultant'` | Revert the nav label to a constant `Consultant` |
| F4 | "V3 customer workspace" shown to a consultant | `DashboardPage` subtitle hard-coded | The shared customer page was unaware of the consultant client plane | Read `useConsultantClientContext()` and switch the subtitle when active |
| F5 | "Add team member" required a raw internal User id | `POST /me/team` accepted only `{user_id}`; UI exposed a UUID text box | Endpoint predated a human-readable identity path; the UI surfaced the internal id | Accept `email`; resolve it server-side to an existing identity |
| F6 | Role dropdown offered a value the API rejects (422) | UI offered "Consultant team member" | The label was invented; `CONSULTANT_ROLES = (owner, manager, consultant, viewer)` | Offer the real vocabulary + role/capability copy |
| F7 | "Firm tasks" unexplained and "Client id" was free text | `TaskCreate.client_id` is an optional opaque string; UI took raw text | No explanatory copy; the client reference was never humanised | Clarify the semantics; replace raw text with a select of authorised clients |

---

## 8. Global client context removal

`ConsultantPage` no longer renders any "Active client" block. The firm banner now
states only the actor:

```
Consultant
<firm name>
Signed in as a consultant firm — you operate your clients on their behalf.
```

Removed with it:

- the `activeClientId` hub state, its `localStorage` read/write, and the CON-6
  "auto-select first managed client" logic;
- the `onSwitchClient` handler and the per-row `.active` highlight in the client
  directory (a client row is now display + lifecycle + "Open workspace");
- the legacy `?client=<id>` deep-link restore. The `?view=` deep link is retained
  (the Manual Processing CTA links to `/consultant?view=coverage`).

The dashboard's "Active clients" **count** summary card is unrelated and stays.

`ClientMessagingTab` is a client-scoped surface, so it keeps a client reference —
but via a **local** `<select aria-label="Client">` inside the messages view only
(§14). Firm pages (`Firm branding`, `White-label`, `Team`, `Manual Processing`)
now carry no client context at all.

---

## 9. Client Operating Plane changes

`ClientOrgShell` presents context, not selection:

```
← Back to Consultant
Consultant        <firm>
Working on        <client>   Consultant-managed · Active   Client portal: Managed
```

- The relationship/portal labels come from the REAL `consultant_clients` fields
  (`relationshipLabel`, `clientPortalLabel`) — unchanged.
- The "Switch client" `<select>` is removed. To change client the consultant
  returns to `/consultant` and opens another workspace.
- The URL remains `/consultant/clients/:clientId/*`; the backend re-authorises
  the grant on every request. `setActiveConsultantClientId(clientId)` still
  persists the route-selected client for the shared page components
  (`resolveV3Organization`).

---

## 10. Back-to-Consultant consolidation

There is now **exactly one primary** return control in the client plane: the
context-bar link `← Back to Consultant` (→ `/consultant`, textual, not
icon-only, not history-dependent). The `V3Layout` nav entry inside the plane no
longer duplicates it — it reads a constant `Consultant` in every context. No
third mechanism was introduced.

`ConsultantItemPage` keeps its own `← Back to client processing` button, which
navigates **deeper into** the same client plane (not a second return-to-hub
path).

---

## 11. Team member identity workflow

**Inspection first.** The existing identity architecture was traced:

- `POST /api/v3/consultants/me/team` took `FirmMemberCreate { user_id, role }`.
- The SAME module already resolves/creates auth identities by email for the
  customer-owner flow (`_resolve_or_create_owner_identity`, GoTrue admin API).
- `GET /me/team` already enriches the roster with `email`/`first_name`/`last_name`.
- There is **no** invitation-email subsystem and **no** user-search endpoint.

**Smallest coherent change supported by that architecture:** accept an `email`
in addition to `user_id`, and resolve it server-side to an **existing** identity
via a new **resolve-only** helper (`_resolve_owner_identity_by_email`). It reuses
the same GoTrue admin directory the owner flow uses. It does **not** provision a
new account (a team member must already have signed up), so no dead accounts are
created and no credential is ever returned.

- Unknown email → `404` with a human message ("They must sign up to CarbonTally
  first."); neither identifier supplied → `422`.
- The `manage_team` permission still governs the write; the self-add rejection is
  preserved (the resolved id is compared, not the raw payload).
- The UI: an **Email** field (`type="email"`) + **Role**; no raw `user_id` box.

Documented gap (see §20): an out-of-band invitation / email-verification
lifecycle is NOT part of the current architecture and is not invented here.

---

## 12. Role / capability findings

- Real firm roles (backend `consultant_auth.CONSULTANT_ROLES`):
  `owner`, `manager`, `consultant`, `viewer`.
- The previous UI offered **"Consultant team member"**, which the API rejects
  with `422` — an existing defect. It is replaced by the real vocabulary.
- On add, the backend creates the member with **all `can_*` flags false**,
  regardless of role: a role is a firm **classification**, not a grant.
- The UI now states this: "Role is each member's firm classification.
  Capabilities are what the member may actually do, and the server enforces
  them — a role alone grants nothing."
- The capability editor and defaults are UNCHANGED. No capability was granted,
  revoked or defaulted differently.

Open question for the PO (§20): whether a firm admin should be *permitted* to
assign the `owner` role from this surface (the API already accepts it).

---

## 13. Firm Task semantics

Inspection of the actual model (`backend/api/v3_consultants.py` `TaskCreate`,
`backend/data/consultants.py` `create_task/list_tasks`,
`backend/domain/partners.py` `ConsultantTask`):

- A **firm task** is a lightweight, firm-scoped follow-up item
  (`task_title` required; `task_type` free text; `priority`; `status` in
  `open/in_progress/done/blocked`; **optional** `client_id`; free-form
  `metadata`).
- It is FIRM-internal: it is created against the consultant's own firm and listed
  by firm (`list_tasks(consultant.profile.id)`). There is no assignee field, no
  workflow binding and no processing linkage — it is a reminder/queue, not the
  processing pipeline.
- `client_id` is OPTIONAL — firm-wide tasks are valid.

The panel is clarified to match its real semantics: "Internal follow-up tasks for
your firm. Optionally link a task to one of your clients; tasks are visible to
your firm's members only." The empty state reads "No firm tasks yet — create one
below." No new task functionality (no assignee) was invented.

---

## 14. Client selector implementation

The form's "Client id (optional)" free-text field is replaced by:

```
Client (optional)  [ — No specific client — ▾ ]
```

- Options come from the existing authorised endpoint `GET /me/clients`
  (`listConsultantClients`) — the SERVER-authorised set; no hard-coded names.
- The empty option is preserved so a **firm-wide** task remains possible.
- The option VALUE is the internal client id (submitted as before); the option
  LABEL is the human client name. The user never sees or types a raw UUID.
- The frontend list is NOT an authorization boundary — the backend remains
  authoritative.

The same principle governs Client messages: a **local** `Client` select inside
the messages view only (client-scoped by nature), never a global firm selector.

---

## 15. Security preservation

No authorization boundary was weakened. Specifically:

- **RLS / migrations / tenancy / capabilities / commercial entitlements** were not
  touched.
- The client id in the URL is still re-authorised server-side on every request;
  navigating to an unauthorised client id yields the controlled "Client not
  available" denial (unchanged; asserted in the shell test).
- The team endpoint still enforces `manage_team` server-side; the email path is
  additive and does not bypass it (backend test proves a non-manager with an email
  still gets `403`).
- The task client selector is a convenience over `GET /me/clients`; the backend
  remains authoritative over the submitted `client_id`.
- The UI never becomes a boundary: removing controls (`Active client`,
  `Switch client`) removes convenience, not security — the dropdown was never an
  authorization mechanism.

---

## 16. Tests

### Affected frontend suites (re-run after all edits)

```
PASS src/v3/__tests__/consultant-client-org-shell.test.jsx
PASS src/v3/__tests__/consultant-page.test.jsx
PASS src/v3/__tests__/consultant-ux-navigation.test.jsx
PASS src/v3/__tests__/consultant-team-capabilities.test.jsx
Test Suites: 4 passed, 4 total
Tests:       25 passed, 25 total   (baseline for these 4 was 22 before this task)
```

New/updated coverage maps to the brief:

- NAVIGATION — consultant plane has NO global Active client selector (AC-01);
  Clients has "Open workspace"; the client plane shows exactly ONE
  "Back to Consultant" (AC-06); NO "Switch client" (AC-07); the shell still
  re-authorises from the URL and denies unauthorised clients.
- TEAM — add-member uses EMAIL, never a raw user id (AC-14); role list is the
  real vocabulary (AC-16); capability grant/revoke still writes exactly the draft
  the server validates (unchanged).
- TASKS — the client field is a human-readable select from the authorised set,
  with a firm-wide empty option (AC-17/AC-18).

### Full frontend suite

```
Test Suites: 1 failed, 52 passed, 53 total
Tests:       1 failed, 593 passed, 594 total
```

The single failure is `dr007-investor-display-fixes` Issue 3, which is
**pre-existing and unrelated** to this task: that test imports only
`ProcessingItemWorkspace` and `ReviewDetailPage` (import list checked), neither
of which this task touches; it failed identically before this task (recorded by
the –01 task and re-confirmed here — no file this task changed is in its import
graph).

### Backend (affected suites + new file)

```
test_p6_1b_membership_workspace_authorization.py \
test_v3_consultants.py test_ct_consultant_model_03.py test_ct_consultant_model_02.py
→ RC=0 (173 tests passed)

test_ct_consultant_ux_01a_team_identity.py → 6 passed
  (email resolves an existing identity; case-insensitive; unknown email → 404;
   no identifier → 422; email path still requires manage_team → 403;
   resolved self → 422)
```

---

## 17. Browser verification

Real headless Chrome against the local Demo Lab (frontend `:3000`, backend
`:8070`, lab GoTrue at `:54430`), with a REAL password login (no token
injection):

```
tools/demo_lab/verify_consultant_ux_01a_browser.py --json
```

```
"passed": 44, "failed": 0, "ok": true   (exit 0)
```

Verified journeys: consultant dashboard (firm identity, no Active client);
Clients directory (Open workspace); Client Operating Plane (one Back to
Consultant, no Switch client, no Active client, consultant-operated subtitle,
single return path works); Firm branding / White-label / Team / Manual Processing
coverage (no client context); Team (Email identity, no User id, real role list,
add-member state); Firm task client selector (human-readable); Client messages
(local Client selector); direct-customer Home (customer nav, no consultant
context, keeps "V3 customer workspace").

Console notes: the consultant session logs `403` from
`/api/v3/reporting/customer-dashboard`, `/reporting/emissions-trend` and
`/reporting/member-activity` — this is **F-NAV-1**, the pre-existing parity gap
(§19). It is recorded verbatim and NOT bypassed or hidden.

---

## 18. Screenshots

Written under
`~/ct_local_env/demo_lab/evidence/browser/ct_ux01a_*.png`:

| §25 item | File |
|---|---|
| 1 Consultant dashboard | `ct_ux01a_dashboard.png` |
| 2 Clients | `ct_ux01a_clients.png` |
| 3 Client workspace | `ct_ux01a_client_plane.png` |
| 4 Firm Branding | `ct_ux01a_branding.png` |
| 5 White-label | `ct_ux01a_whitelabel.png` |
| 6 Team | `ct_ux01a_team.png` |
| 7 Add team member state | `ct_ux01a_team_add_member.png` |
| 8/9 Firm Tasks + client selector open | `ct_ux01a_firm_task_client_select.png` (Team page; the Firm-tasks panel is on the same view, also in `ct_ux01a_team.png`) |
| 10 Client Messages | `ct_ux01a_client_messages.png` |
| 11 Manual Processing coverage | `ct_ux01a_coverage.png` |
| 12 Direct customer Home | `ct_ux01a_direct_customer_home.png` |

---

## 19. Remaining issues (honest findings — none silently closed)

- **F-NAV-1 — OPEN, OUT OF SCOPE.** The reused customer Home inside the client
  plane still calls `/api/v3/reporting/customer-dashboard`,
  `/reporting/emissions-trend` and `/reporting/member-activity`, which return
  `403` for a consultant-operated client workspace (parity-plane authorization
  gap introduced by `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01`).
  Fixing it requires an authorization change, which this task forbids. It is
  **not** bypassed, hidden or weakened; the browser verifier records the `403`s as
  evidence.
- **PD-NAV-1 — OPEN, PRODUCT DECISION REQUIRED.** There is still no dedicated
  consultant "Firm & Billing" surface; the firm's Manual Processing coverage tab
  is used as a stand-in. This task did not create one.
- **R-NAV-1 — OPEN, PRESENTATIONAL.** The legacy consultant item route
  `/consultant/items/:clientId/:itemId` (`ConsultantItemPage`) remains. It routes
  its return path into the client plane (which carries the single
  "Back to Consultant"), so it is no longer a competing top-level destination;
  whether to remove/tombstone the legacy route is left as-is.
- **Not verified by an independent party.** All verification here is
  self-performed on the local Demo Lab.

---

## 20. Product decisions required

- **PD-NAV-1** (unchanged): a dedicated Firm & Billing surface for consultants.
- **PD-1A — Team identity lifecycle.** The current architecture has no invitation
  email and no user-search endpoint. A team member must already have a
  CarbonTally account and is matched by email. If the product wants
  "invite by email with a signup link", that is a NEW capability
  (email + token lifecycle) and must be specified before implementation.
- **PD-2A — Assignable roles.** The API accepts `owner|manager|consultant|viewer`
  when adding a member. The UI now mirrors the real vocabulary (fixing the `422`).
  Whether a firm admin should be *allowed* to mint additional `owner`s from this
  surface is a policy choice, not a technical one.
- **PD-3A — Task client scope.** Whether a task's `client_id` should be validated
  server-side against an active grant (today it is stored as an opaque optional
  string) is a possible hardening decision.

---

## 21. Final status

**IMPLEMENTED_AND_LAB_VERIFIED** (self, local Demo Lab).

- Implemented: all §23 frontend UX items; the additive backend email identity path.
- Tested: affected frontend suites 25/25; new backend suite 6/6; affected backend
  suites RC=0; full frontend suite 593/594 (1 pre-existing, unrelated).
- Lab-verified: real-Chrome browser run 44/44, exit 0, 11 screenshots.

NOT claimed: `VERIFIED`, `ACCEPTED`, `PRODUCTION_READY`. Those require independent
verification and Product Owner acceptance.

Acceptance criteria (§31) coverage: AC-01…AC-08 met; AC-09…AC-13 met (Client
Messages selects locally); AC-14/AC-15 met; AC-16 met; AC-17/AC-18 met; AC-19
preserved (server-authorised); AC-20 met (direct-customer regression verified);
AC-21 met (no boundary weakened); AC-22 met (F-NAV-1 recorded, not bypassed);
AC-23 met (PD-NAV-1 recorded, not decided); AC-24 met (worktree preserved);
AC-25 met (browser evidence).




