# CarbonTally Phase 6 — P6-0.1 — Commercial Consultant Clarification

**Status:** READ-ONLY reconciliation — **no implementation performed.**
**Date:** 2026-09-04
**Mode:** Plan / STOP after deliverable
**Scope:** Reconcile the PO clarification (SaaS self-registration allowed;
self-authorization denied) with the current architecture before revised P6-1
authorization.

## Implementation-state declaration (required by the clarification)

P6-1 had **NOT** started when this clarification arrived. Inspection/probing
performed for P6-1 was read-only:

- DB probes (`/tmp/p61_probe.py`): consultant_profiles ↔ consultant_firm_members
  relationship sample (54/54 rows are owner-self: `member.user_id =
  profile.user_id`, `firm_id = own profile id`); 55 profiles, 0 users with >1
  profile; no shared multi-member firms in the dataset.
- Source reads: `backend/api/v3_consultants.py`, `consultant_auth.py`,
  `backend/data/consultants.py`, `domain/partners.py`, RLS function
  `is_org_consultant`, consultant/`user_invitations` schema migrations, D37
  billing migrations, D15/D20/D27/revocation-role migrations.

No product code, schema, migration, RLS, API, UI, or data was changed; no
fixtures created; nothing committed or pushed. Git working tree contains only
pre-existing modifications (`.agents/skills/prisma-*` docs) plus the untracked
P6-0 report authored before this task.

---

# 1. Current Consultant self-registration behaviour (verified)

| Path | What it does today | Clarified-policy fit |
|---|---|---|
| `POST /api/v3/consultants/me` (`create_my_profile`) | Any **authenticated** user (no consultant profile) creates an ACTIVE `consultant_profiles` row (`company_name`) — i.e. self-service commercial registration of a consultant firm identity. Does **not** create a `consultant_firm_members` row, so the creator cannot yet pass `require_consultant` (API) until a member row exists. | **Compatible** with "self-registration allowed". Under P6-0's "close self-provisioning" framing this endpoint was to be closed; under the clarified policy it is the intended commercial entry path (P6-1A). |
| `POST /api/v3/consultants/me/customers` (`create_customer`) | `can_manage_clients` member creates a NEW customer organisation (owner identity provisioned) and links the firm via an ACTIVE `consultant_clients` grant in the same operation (PO Decision 3 / CON-1). | **Compatible** — the consultant is creating their own client, not seizing an existing one. Grant creation must stay explicit + audited. |
| `POST /api/v3/consultants/me/clients` (`add_client`) | `can_manage_clients` member links **any existing `organization_id`** to the firm with an ACTIVE grant — no customer-side or CT confirmation, no invitation, no acceptance. | **NOT compatible as-is** for arbitrary pre-existing organisations — that is self-authorization to an organisation the consultant does not own/create. Must become a controlled engagement. |
| `POST /api/v3/consultants/me/team` (`add_team_member`) | `can_manage_team` member inserts a `consultant_firm_members` row for **any supplied `user_id`**, role free-form, flags default FALSE, no invitation/acceptance/expiry. | **NOT compatible as-is** — arbitrary firm-membership creation without the invitee's consent/identity binding. Replaced by P6-1B invitation/acceptance. |

There is **no frontend self-service consultant signup** in the current product:
the decision register notes "no self-serve UI — provisioning is seed/data-driven",
and the API surface described above exists backend-side.

---

# 2. Current Consultant firm model (verified)

- `consultant_profiles` = the **firm** AND the individual's identity row: the
  profile owner is `user_id`; `id` doubles as the firm id used by
  `consultant_firm_members.firm_id` and `consultant_clients.consultant_id`.
- `consultant_firm_members.firm_id` → `consultant_profiles.id`; a member row
  carries `role`, four `can_*` flags (default FALSE), `client_access uuid[]`,
  `is_active`, `invited_by`, `invited_at`, `joined_at`, `role_id`,
  `permissions JSONB`.
- **Verified data reality:** 54/54 existing member rows are owner-self
  (`firm_id = own profile id`, `user_id = own user`). The dataset contains **no
  shared multi-member firm**.
- RLS helper `is_org_consultant(org)` (D20 override) resolves the chain as:
  `consultant_firm_members WHERE user_id = auth.uid() AND is_active` →
  EXISTS `consultant_clients cc WHERE cc.consultant_id = cfm.firm_id AND
  cc.organization_id = p_org AND cc.status='active'`. Membership is therefore
  **firm_id-based**, and a member of firm F inherits F's client grants even
  when the member's own profile differs from F.
- **API/context inconsistency (real defect):** `require_consultant` →
  `_resolve_context` resolves the member via `get_profile_by_user(user)` then
  `get_firm_member_by_user(own_profile.id, user)`. A member whose membership
  row points at a *different* firm profile (the only sane multi-member model,
  and the model RLS already implements) **cannot pass the API check** — their
  own profile id is not their firm id. Multi-member consultant teams therefore
  exist in schema but are not usable on the V3 consultant API.

# 3. Current Consultant client-grant model (verified)

- `consultant_clients`: one row per (firm, organisation); `status` free-varchar
  with lifecycle `active / suspended / ended / inactive` (D27/D19); only
  `active` grants access (D15, RLS + API). `organization_id` → `organizations`
  FK; a `created_by` column exists but the repository `add_client` does not set
  it today (audit gap worth closing in P6-1C).
- Grants are **firm-level** (owned by `consultant_id` = firm profile). Members
  inherit access through the firm (RLS chain above); per-member `client_access`
  is explicitly NOT an independent grant (D15/D20).
- Creation today: consultant-created customers (create_customer) and
  arbitrary-org linking (`add_client`, gated only by `can_manage_clients`).
- Revocation: `status='ended'` via soft lifecycle (`ended_at`/`ended_by`,
  actor), role-gated to Owner/Admin/Manager (WS6/SEC-0003, RLS
  `is_consultant_firm_revoker` + `consultant_clients_tenant_delete` scoped to
  customer owner/admin). Revocation preserves history.


# 4. Current subscription architecture (verified)

- **Customer side:** `customer_subscriptions` (org-scoped, D37),
  `billing_plans`, `billing_commercial_config` (configurable plans, D37-0),
  `organizations` billing columns + default `billing_mode`, and org-scoped
  `billing_credit_ledger` / `billing_orders` / `billing_payment_records` /
  `billing_storage_usage` / `billing_idempotency_keys`. Self-serve customer
  onboarding (`POST /v3/organizations`) creates the org; plan/subscription is
  org-scoped.
- **Consultant side:** a legacy `consultant_billing` table exists keyed to
  `consultant_id` (`plan`, auto/manual extraction credit counters). Per
  D37-0 (2026-08-24) **consultant-specific billing was REVOKEd from
  `authenticated` writes** — there is no active consultant billing surface, no
  consultant plan purchase flow, and no consultant subscription record in use.
- **No consultant commercial plan/entitlement exists in the active
  architecture.** "Purchase the applicable Consultant subscription/product"
  therefore has no implementation today.

# 5. Current credit/metering ownership

- Extraction/processing metering is **organisation-scoped** (the organisation
  owns the work; credit-ledger rows and orders are organisation-keyed). D7
  (client org owns consultant processing entitlement) is consistent with this:
  a consultant operating a client org must consume/verify the **client org's**
  entitlement, not the firm's. No consultant-firm credit model is active; the
  legacy per-firm `consultant_billing` counters are disconnected from the
  active organisation-scoped ledger.

# 6. Current `can_*` semantics (verified)

- Four real flag columns on `consultant_firm_members`: `can_manage_clients`,
  `can_upload_documents`, `can_generate_reports`, `can_manage_team` — all
  **default FALSE**, never set by any endpoint today (no permission
  administration surface; only the demo seed sets them). `role` is
  display-only; the flags are the authorization surface.
- D-3 processing capabilities (`can_extract/map/validate/calculate/review/
  submit`) **do not exist** — correct, they belong to P6-2.
- `ensure_consultant_permission` maps the four real columns; no self-elevation
  path exists in code (no API route can write the flags).

# 7. Current organization / entity model

- `organizations` (customer data tenants, self-service creation),
  `organization_members` with owner/admin/member/viewer roles. Processing
  Entities are first-class separate entities with their own staff and
  org/PE assignment model (Phase 5). "Customer" and "Consultant" are distinct
  surfaces: a person is a customer via org membership, and a consultant only
  via a consultant profile + active firm membership.
- **There is no organisation↔consultant-firm binding.** An organisation cannot
  "be" a consultant firm; nothing on `organizations` points to a
  `consultant_profiles` row, and nothing prevents the same person from holding
  both a customer membership and a consultant identity.

# 8. Organization → Consultant upgrade feasibility

Feasible **additively**, with no data destruction:

- The customer org keeps its identity; consultant capability would attach
  either as (a) a `consultant_profiles`/`consultant_firm_members` identity
  owned by the org's owner user, or (b) a new explicit organisation↔firm
  binding. Option (b) is cleaner for "the organisation itself operates as a
  consultant business" (direct reuse of org-scoped billing). Neither exists
  today, so **a mapping decision is required** (see §13 D-C).
- Subscription side reuses `billing_plans`/`customer_subscriptions` scoped to
  the organisation once the firm identity is resolvable from the org.
- No existing customer org data, memberships, or history needs mutation under
  either option.

# 9. Exact P6-1 changes required after this clarification

Re-scoped **P6-1A … P6-1D** (each is the minimum change for the clarified
policy; full authorization remains P6-2):

### P6-1A — Safe Consultant self-registration (keep open, add commercial state)
1. Keep `POST /consultants/me` creating the firm identity, but make it
   **registration-complete only** — it must still NOT by itself create an
   active `consultant_firm_members` row or any client grant.
2. Add explicit commercial state to the profile (e.g. reuse existing
   `default_plan` / `partner_status`, or add `registration_state`) so a
   registered consultant is distinguishable from an activated/subscribed one —
   exact semantics pending PO decision D-A (§13).
3. The P6-0 "close this endpoint" interpretation is superseded for the
   registration path (invitation is not the mechanism for commercial
   registration).

### P6-1B — Controlled Consultant firm membership (invitation/acceptance)
4. Firm membership creation moves behind **invitation → acceptance**:
   `POST /me/team` (arbitrary `user_id` add) is removed or rejected, replaced
   by an invitation endpoint (firm admin holding `can_manage_team`, or CT
   operations for CT-originated invites) plus identity-bound acceptance.
5. Acceptance requires the intended authenticated identity (token + email/
   user binding), is idempotent, refuses duplicates, enforces the 7-day expiry
   (constant; no config subsystem), and creates the member row with **role
   from the invitation and all `can_*` flags FALSE** (no self-elevation).
6. Resolve the API/RLS membership mismatch (§2): a member operating a firm
   grant uses the firm identified by their `consultant_firm_members.firm_id`
   (aligned with the existing RLS chain), rather than the owner-self
   assumption in `require_consultant`. This is implementation alignment with
   the ratified D15/D20 model, not a new product decision.
7. Invitation record minimum fields: invitee identity/email, firm, intended
   role, inviter, created_at, expires_at (7 days), status, acceptance
   actor/time. Reuse `user_invitations` (add consultant-firm/role semantics)
   or create a dedicated narrow consultant-invitation table following its
   patterns (`token UNIQUE`, `expires_at`, status vocabulary) — implementation
   detail, decided in P6-1B.

### P6-1C — Controlled client engagement (explicit authorized grant)
8. `POST /me/clients` arbitrary-org linking is restricted: consultant-created
   customers (create_customer) keep their atomic explicit grant; linking a
   **pre-existing** organisation requires an authorized engagement —
   customer-owner confirmation, CT confirmation, or a formal engagement
   invitation/acceptance (decision D-D) — and `created_by` must record the
   authorizing actor.
9. The resulting `consultant_clients` row is `active` only after the
   engagement completes; the D19 lifecycle / revocation semantics are
   unchanged.

### P6-1D — No-self-elevation safeguards
10. Confirm by construction that no endpoint may set `can_*`/`permissions`,
    bind a firm to an organisation it did not create/own (without engagement),
    add membership without acceptance, or elevate to PE / CarbonTally
    Operations / Admin / customer final-approval authority.

# 10. Exact P6-2 dependencies

- Model C action/resource/stage guards (identity → firm → active grant →
  resource → action → stage) on the consultant routes created in P6-1B/C.
- D-3 capability flags (`can_extract` … `can_submit`) + checks + a
  **controlled** capability-assignment surface — the clarification requires an
  authoritative commercial/administrative mechanism; P6-2 must define who may
  assign flags (the permission-administration surface P6-0 flagged as missing).

# 11. Security implications

The clarified model aligns with the platform security principles:

- Self-registration creates identity only; access still requires
  identity → firm → **active grant** → action authorization. RLS
  (`is_org_consultant`) and `ensure_consultant_org_access` already enforce the
  grant server-side; the UI is never the security boundary.
- Original P6-1 SEC-001…012 remain valid once re-scoped:
  - SEC-001/002: unchanged — no unauthenticated/arbitrary member creation;
    self-registration ≠ self-membership.
  - SEC-003/004: unchanged — no self-add to another firm/client. The two
    concrete holes today are `add_team_member` (firm-admin adds an arbitrary
    user with no consent/acceptance) and `add_client` (firm-admin links an
    arbitrary pre-existing org); both are controlled by P6-1B/P6-1C.
  - SEC-005: holds today (no flag-writing route) and must remain true.
  - SEC-006/007/008/009: become the invitation acceptance contract
    (identity binding, 7-day expiry, single-use, cross-firm/cross-client
    denial, revocation before acceptance).
  - SEC-010: holds — acceptance activates only consultant firm membership;
    PE/Operations/Admin/customer-approval authority live in separate role
    models outside this surface.
  - SEC-011/012: unchanged — soft revocation preserves provenance; the active
    grant is the access key, never the profile alone.
- New risk introduced by the clarified model: a commercial "plan" must never
  become a substitute for the org grant chain. Entitlement checks are
  commercial gates; `consultant_clients.status='active'` remains the access
  gate (D15). Recommended rule for P6-2+: capability flags may gate actions;
  they never grant org access by themselves.

# 12. Contradictions

1. **P6-0 D-1 wording vs clarified policy.** P6-0 framed consultant
   provisioning as purely "invitation-based" and identified open profile
   creation (`POST /consultants/me`) as the behaviour D-1 closes. The
   clarification reverses that for initial commercial registration. **Not an
   architecture conflict** — no code changed under the old framing — but the
   P6-0 D-1 section and its §12 dependency list are superseded for the
   registration path. Invitation remains the mechanism for firm membership and
   client engagement, not for commercial registration.
2. **API vs RLS membership resolution mismatch** (§2) — an internal
   consistency defect P6-1B must fix. RLS is authoritative and firm_id-based;
   aligning the API is implementation, not product change.
3. **Legacy `consultant_billing`** is write-revoked and disconnected (D37-0);
   the clarified "consultant subscription/product purchase" has no active home.
   P6-1 does not need it; D7/P6-3 metering stays organisation-scoped.

# 13. Remaining PO decisions

**D-A — Consultant commercial activation model (material).** What makes a
self-registered consultant "commercially active"? (1) Open registration with
no plan gate (matches current behaviour; plans enforced later); (2) consultant
plan/subscription required before the firm can operate commercially; (3) plan
required per firm, surfaced via a `registration_state`/plan column. Affects
P6-1A schema.

**D-B — Team-member identity/firm semantics (material).** Confirm a team
member's operating context is the firm they belong to
(`consultant_firm_members.firm_id`, matching RLS), that invitees do not need
their own consultant profile/firm to join an existing firm, and who may send
P6-1B invitations (firm `can_manage_team` member only, vs CT operations).

**D-C — Organization → Consultant upgrade mapping (material, later
workstream).** Binding model (org-owned firm via owner user vs explicit
organisation↔firm binding table) and confirmation that no customer-org data
mutates. Not needed for P6-1.

**D-D — Engagement authority for pre-existing client organisations (material).**
The authorized-engagement mechanism for linking an existing customer org:
customer-owner confirmation, CT confirmation, or formal engagement invitation
accepted by the customer owner — and confirmation that consultant-created
customers (PO Decision 3) keep automatic active grants. Affects P6-1C.

Minor (implementation, not policy): 7-day expiry as constant vs configurable;
whether CT Operations may also send/revoke firm invitations; flag/role storage
shape for invitations (`role_id`/`permissions` columns already exist on
`consultant_firm_members`).

---

## Final verdict

### `P6-0.1 CLARIFICATION REQUIRES PO DECISION`

The clarified commercial model is **architecturally compatible**: no conflict
with the frozen trust/authorization model — self-registration already exists,
access already requires active grants, and RLS is already firm/grant-based.
P6-1 re-scopes cleanly into P6-1A (safe self-registration), P6-1B (controlled
firm membership), P6-1C (controlled client engagement) and P6-1D
(no-self-elevation). However, four **material** commercial/entity/
authorization decisions (D-A … D-D, §13) remain genuinely unresolved and must
not be invented by an implementation agent. They do not block re-scoping
P6-1, but D-A (activation/commercial state) and D-D (engagement authority for
existing orgs) must be answered before P6-1A/P6-1C code, and D-B shapes
P6-1B.

**STOPPED — no implementation performed, nothing committed.**
PO review of D-A … D-D and the revised P6-1 authorization is required before
any P6-1A–D implementation begins.

