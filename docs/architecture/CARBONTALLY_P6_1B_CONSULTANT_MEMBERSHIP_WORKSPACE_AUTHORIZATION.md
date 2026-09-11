# CarbonTally P6-1B — Consultant Membership, Team & Workspace Authorization

**Status:** IMPLEMENTED AND VERIFIED (bounded workstream) — no migration, no
commit/push.
**Authority:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` + ratified
P6-0.1 / P6-BILL-1 decisions (D-C org-scoped Consultant capability, PO-D7).
**Readiness:** `CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md`.

---

## 1. Current Consultant identity model

- **Identity/firm:** `consultant_profiles` is BOTH the consultant user identity
  row AND the firm record — `id` doubles as the firm id referenced by
  `consultant_firm_members.firm_id` and `consultant_clients.consultant_id`.
- **Membership:** `consultant_firm_members` links a user to a firm with a
  display `role`, four real `can_*` permission columns, `is_active`, and
  `invited_at`/`joined_at`. There is **one membership row per (firm, user)**.
- **Runtime data reality (verified):** 55 profiles, 54 firm-membership rows
  (all currently owner-self), 917 client grants across 975 organisations.
- **P6-1B change:** user→firm→membership resolution is now **membership-first**
  and firm_id-authoritative (see §6), matching the RLS helper
  `is_org_consultant` (which already resolves membership by `user_id` +
  `is_active` + the firm's grants). This also makes a team member added under
  another firm's profile resolve correctly on the API (previously the API
  keyed membership to the user's own profile and rejected such members while
  RLS allowed them).

## 2. Firm membership model

| Concept | Representation |
|---|---|
| firm owner / sole consultant | `consultant_profiles.user_id` = owner; the owner-self `consultant_firm_members` row is the membership |
| team member | `consultant_firm_members` row whose `firm_id` is the firm's profile |
| firm administrator | an ACTIVE member whose row has `can_manage_team` = true (flag-based; `role` is display-only) |
| ordinary member | active row without `can_*` flags |
| inactive/revoked | `is_active=false` on the member row |

Firm administration endpoints (`POST /me/team`, deactivate, reactivate) act
only on the FIRM resolved server-side (`context.profile.id`) — the operating
firm is never client-selectable. New members are added with a validated role
and **all `can_*` flags FALSE**; no permission flag is grantable through the
provisioning endpoint (forged extra payload fields are ignored).

## 3. Membership states

Two states (existing model, unchanged): **active** and **inactive (revoked)**.
`is_active=false` → the member row never resolves at `require_consultant`, so
revocation is immediate and server-authoritative. No additional states were
invented. Ambiguity rule added (P6-1B): a user with active membership rows in
more than one DISTINCT firm is DENIED consultant context (single-firm model;
never silently guessed) — RLS is unaffected.

## 4. Consultant capability relationship

Consultant capability is an **organisation-scoped commercial entitlement**
(`billing_plans.features.consultant`, resolved by
`BillingService.consultant_capability(org)` — P6-BILL-1). It is a distinct
layer from membership:

**Entitlement ≠ membership ≠ client access.**

No organisation↔firm binding exists yet (deferred D-C mapping), so no
capability is bound to a firm today. The existing architecture intentionally
permits consultant profiles/workspaces before any subscription is active
(preserved). The server exposes this explicitly in `GET /consultants/me`
under `entitlement_scope`
(`consultant_capability_required_for_workspace: false`,
`bound_organization_id: null`) so no client state can claim otherwise.

## 5. Permission model

Real flag columns on `consultant_firm_members`; evaluated server-side by
`ensure_consultant_permission(context, name)` which maps the canonical name →
the real column and rejects (403) when false. Current enforcement map
(verified by inspection of `v3_consultants.py`):

| Permission | Column | Enforced at |
|---|---|---|
| manage_clients | `can_manage_clients` | `POST /me/clients`, `POST /me/customers` (grant creation) |
| manage_team | `can_manage_team` | `POST /me/team`, `deactivate`, `reactivate` |
| upload_documents | `can_upload_documents` | `POST /clients/{id}/documents` |
| generate_reports | `can_generate_reports` | **represented, not action-enforced yet** (no report-GENERATION action exists on the consultant surface; report reads are client-grant-gated). Deferred to the P6 report-generation action surface. |

Client relationship revocation is deliberately role-based (Owner/Admin/Manager,
WS6/SEC-0003), not flag-based. Permission flags never grant client access and
cannot be set by any client request.


## 6. Workspace authorization chain

Canonical server-side rule implemented in `api/consultant_auth.py`
`_resolve_context` (used by `require_consultant` and the brand/context
resolvers):

1. **Layer 1 Identity** — authenticated user (401 otherwise).
2. **Layer 2 Membership** — the user's ACTIVE `consultant_firm_members` rows
   (`repos.consultants.get_active_memberships_by_user`, new canonical query
   mirroring `is_org_consultant`). Zero rows → deny. The single distinct firm
   is the operating firm; its `consultant_profiles` row must exist and be
   active. Inactive membership → deny. Multiple distinct active firms →
   deny (ambiguous).
3. **Layer 3 Capability** — organisation-scoped entitlement is a separate
   server surface (`entitlement_scope`/`BillingService.consultant_capability`).
   Because no organisation↔firm binding exists yet, capability is not a hard
   workspace gate today; existing pre-commercial consultant profiles are
   permitted (preserved distinction, per P6-1B §5). No consultant profile or
   membership can assert capability on its own.
4. **Layer 4 Permission** — `ensure_consultant_permission` on the specific
   action (server-side flags).
5. **Layer 5 Client grant** — active `consultant_clients` grant for the
   specific organisation (`_authorized_client_org`, D15) before any client
   data endpoint serves data.

`/consultant` (frontend route) is never authorization: every consultant API
route requires the server-resolved context, and tests prove unauth/ordinary/
inactive/ambiguous users get 401/403.

`GET /api/v3/consultants/me` now returns the authoritative `membership` block
(id, firm_id, role, is_active, joined/invited, source) plus
`entitlement_scope` so clients can render from server state only.

## 7. Client-grant boundary (unchanged, preserved)

Membership and subscription NEVER grant client access. Client-resource access
continues to require an explicit ACTIVE `consultant_clients` grant row for the
specific organisation (D15/D20; RLS `is_org_consultant` + API
`_authorized_client_org`). P6-1B added no grant-creation behaviour: firm
membership, capability and `can_*` flags cannot bypass `consultant_clients`.

## 8. API enforcement

- Identity gate: `require_consultant` on every `/api/v3/consultants/*`
  protected route (verified across v3_consultants, v3_whitelabel, context).
- Registration: `POST /consultants/me` (open/closed by registration mode,
  P6-BILL-1) creates a profile only — no membership, no workspace, no grants.
- Firm administration: `manage_team`-gated add/deactivate/reactivate with
  validated role vocabulary, duplicate/self-add rejection, cross-firm member
  id denial (404), and append-only audit (`consultant.team.added`,
  authenticated actor; never a client-supplied actor).
- Client resource/processing/reporting/messaging routes were NOT changed;
  processing/workflow actions remain out of scope (P6-3+).

## 9. RLS / security model

- **No RLS change** was made. `is_org_consultant` remains the authoritative
  DB-layer gate (active membership by user + the firm's ACTIVE grants); the API
  now resolves the same membership-first chain, eliminating the previous
  API/RLS mismatch for team members without their own profile-firm.
- Security guarantees preserved by construction (each covered by a focused
  test): workspace denied without auth (401), ordinary customers denied (403),
  inactive membership/firm denied (403), capability never grants client access,
  membership never grants client access, inactive grants deny client data,
  PE and Operations surfaces deny consultants, forged ids/role/actor/permission
  fields cannot select a firm or elevate anything, revocation takes effect on
  the next request.
- Server-authoritative only: no frontend role, URL, firm id, organisation id or
  permission value is trusted.

## 10. Tests

- **New P6-1B suite** `backend/tests/unit/api/test_p6_1b_membership_workspace_authorization.py`:
  **22/22 PASS.** Covers: unauth/customer/profile-only/inactive-membership/
  inactive-firm/ambiguous-multi-firm denials; active-member workspace allow
  with authoritative membership + entitlement_scope; revocation re-evaluation;
  team administration (manage_team required, safe default flags on add, role
  whitelist, duplicate/self rejection, forged permission flags ignored,
  cross-firm member denial); client boundary (active grant allows, inactive and
  cross-firm grants deny client data, unknown id 404); Operations/PE surface
  denial; and membership + org-capability two-layer resolution.
- **Consultant regression** (v3_consultants, branding, revocation, context,
  whitelabel + P6-BILL-1 suite): **112/112 PASS.**
- **Full unit suite** `pytest tests/unit -q`: **all pass, 0 failures** (dots to
  100%, no failures reported; only a pre-existing third-party urllib3/chardet
  warning).
- Real-PostgreSQL read-only probe: the new `get_active_memberships_by_user`
  SQL resolves an active member correctly against the live schema
  (firm_members total unchanged at 54).

## 11. Known limitations

- Single-firm assumption enforced server-side: a user with active memberships in
  more than one distinct firm is DENIED consultant context (documented
  behaviour, not multi-firm support).
- Workspace entry is not capability-gated because no organisation↔firm binding
  exists yet (see §4); the field `entitlement_scope.consultant_capability_required_for_workspace`
  is currently `false` and is the switch point for that gate once the D-C
  binding lands.
- `can_generate_reports` remains represented but not action-enforced (no
  consultant report-GENERATION action exists yet).
- Team member invitations still use the raw firm-admin add endpoint (no
  invitee-consent/expiry token); consent-based invitation is deferred (P6-1B
  hardening kept the smallest safe server change: admin-only add + safe
  defaults + audit).
- `GET /clients/{id}/context` returns grant meta for own-firm rows regardless
  of grant status; client DATA endpoints enforce the active grant (D15).

## 12. Deferred Consultant workflow work

- Consultant processing actions (extract/map/validate/calculate) and workflow
  stages (P6-2 / P6-3).
- Consent-based firm-member invitations with expiry (P6-1B invitation boundary;
  existing org-invitation flow untouched).
- Existing-org engagement confirmation (P6-1C / CT-CONSULT-003).
- Organisation↔firm binding and workspace capability gate activation (D-C).
- Checkout / payment provider / public pricing.
- Full Consultant UI (P6-6).
- D39 messaging / D40 notification changes (only membership-authorization
  defects would be in scope; none were found).

