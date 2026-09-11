# CarbonTally Phase 4 — Individual User Architecture (Design Gate)

- **Phase:** 4 — Individual User Architecture
- **Nature:** DESIGN-BEFORE-IMPLEMENTATION GATE — no implementation performed.
- **Date:** 2 September 2026
- **Authoritative baseline:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.2.md`
  (frozen). V1.2 acceptance is complete and is NOT reopened by this document.
- **Status:** `PHASE 4 DESIGN COMPLETE — AWAITING PRODUCT OWNER APPROVAL`

Every section distinguishes **CURRENT FACT** (verified against the running
system, database and source) from **PROPOSED DESIGN** and
**PRODUCT OWNER DECISION REQUIRED**. Nothing in this document implements,
migrates, re-authorizes or routes anything.

---

## 1. Executive Summary

CarbonTally's V1.2 identity/actor model is **organisation-centric and
actor-domain-centric**. A person authenticates once (Supabase Auth) and is then
resolved by the server into exactly one operational actor domain — customer
organisation member, consultant firm member, Processing Entity member,
CarbonTally internal staff, or (for authenticated persons with no productive
relationship) a "new user" whose destination is onboarding.

**Key finding.** There is **no approved product problem that requires a
personal/individual data workspace**, and the current architecture already
solves the plausible lightweight use cases (a person can exist as an account
that authenticates, joins invitations, and is onboarded into an
organisation). A genuine *individual workspace* (personally owned documents,
emissions, calculations, reports, subscriptions) would require a **new
authorization and data-ownership domain** — it cannot be bolted onto
`users.user_type`, and it would intersect every V1.2 security invariant.

**Recommendation (single architecture): OPTION A — do not implement a
personal workspace.** Keep one server-authoritative actor resolution with
organisation/consultant/PE/staff/admin domains, and treat "individual" as a
pre-relationship identity state (account + onboarding + invitations), never
as an emissions-data-owning workspace. Optional identity-only account
refinements (OPTION B) may be considered separately by the Product Owner, but
must not introduce personal data ownership.

---

## 2. Current-State Findings (CURRENT FACT)

### 2.1 Database (verified live)

- `users(id, email, first_name, last_name, user_type VARCHAR NULL, is_active,
  email_verified, last_login, created_at, updated_at, is_anonymised)`.
  No constraint on `user_type`. Counts in the live DB: `customer` 915,
  `consultant` 52, `staff` 16, `NULL/''` 346. (Total users 1,329.)
- **`users.user_type` is inert at runtime** (§4). Application code never
  reads it; it appears only in the init schema and as a "protected column"
  comment in `rc2_rls.sql`. It has **no** effect on authorization, onboarding,
  routing, billing or RLS.
- Organisations: **975**. Memberships (`organization_members(organization_id,
  user_id, role, is_active)` with unique `(organization_id, user_id)`):
  owner 964, admin 52, member 57, viewer 52.
- **Multi-organisation membership is schema-permitted but unused in
  practice**: no current user holds more than one active membership
  (verified: `max_orgs = 1`).
- Actor tables: `staff_profiles` (with `entity_id` distinguishing CarbonTally
  internal vs Processing Entity staff, and `role_id` → `staff_roles(name,
  permissions)`), `consultant_profiles`, `consultant_firm_members`,
  `consultant_clients(consultant_id, organization_id)`, `processing_entities`
  (PE members ride on `staff_profiles.entity_id`). There are **no**
  `actor`, `workspace` or `account` tables.

- Billing is **organisation- or firm-scoped, never user-scoped**:
  `customer_subscriptions(organization_id)`, `billing_plans`,
  `billing_credit_ledger(organization_id)`, `billing_orders(organization_id)`,
  `billing_payment_records`, `consultant_billing(consultant_id)`,
  `billing_commercial_config`, `billing_storage_usage`,
  `billing_idempotency_keys`. `BillingService.charge_processing(...)` charges a
  **organisation** (`job.organization_id`); orgs without an active
  subscription are not charged.
- Data ownership is organisation-first: `emissions_logs`,
  `calculation_snapshots`, `customer_factors`, `organization_files`,
  `customer_documents`, `customer_subscriptions`, `billing_credit_ledger`,
  `billing_orders`, `user_invitations`, `pending_invites`, and workflow items
  (`manual_extraction_items → manual_extraction_batches(organization_id)`)
  all carry `organization_id`. PE work is **customer-org-owned work assigned
  to a processing entity** (`batches.entity_id`, immutable item
  `processing_origin`/`processing_entity_id`). Global factors
  (`emission_factors`, 7,049 rows) have no org owner. Reporting is derived
  from org-owned emissions; persisted report content lives in
  `report_versions`.
- Migrations: **42** (unchanged baseline). No Phase-4 migration was created.

### 2.2 Authorization (CURRENT FACT)

- `AuthUser` (backend/auth.py) is resolved from the Supabase user plus real
  rows: one `staff_profiles` row (→ role/permissions, `entity_id`) and **one**
  active `organization_members` row. It carries `is_staff`, `is_org_member`,
  `organization_id`, `entity_id`, `role_name`. `user_type` is never consulted.
- `require_org_access(organization_id)` compares the requested org to the
  **resolved single** `current_user.organization_id` — no client-side
  organisation selection can grant another org (RLS is defence-in-depth).
- `GET /api/v3/me/context` precedence (server-authoritative, fail-closed):
  1) CarbonTally internal staff → `/ops`; 2) Processing Entity staff → `/pe`;
  3) consultant firm member → `/consultant`; 4) organisation member → `/home`;
  5) authenticated with no relationship → `/onboarding`; resolution errors →
  HTTP 500 (never "new user").
- RLS relevant to identity: organisation-membership policies
  (`om_select_self_or_admin`, `om_insert_admin`, `om_update_admin`, etc.) and
  staff/entity policies keyed on membership/profile rows — not on `user_type`.

### 2.3 Frontend (CURRENT FACT)

- Login/sign-up authenticate via Supabase; post-login routing calls
  `/api/v3/me/context` (`goToWorkspace`). No route is granted from the
  frontend role.
- Surfaces: `/home…` (customer, V3Layout), `/consultant` (V3Layout),
  `/pe` (dedicated PEShell), `/ops` (internal), `/admin` legacy control plane
  (quarantined, not the target architecture), `/onboarding` for new users.
- There is no workspace switcher. PE staff are redirected away from shared
  shells by the server context and by frontend defence-in-depth.

### 2.4 What is NOT present (CURRENT FACT)

No personal workspace, no personal emissions/report/document storage model, no
user-owned credits/subscription, no user-level billing, no personal-account
application surface, no `users.user_type='individual'` value in use, and no
approved PO decision authorising any of these.

## 3. Existing Identity Model (CURRENT FACT)

- Identity = Supabase Auth identity (one platform, one auth system).
- `public.users` is the product identity row: contact/profile fields plus
  lifecycle flags (`is_active`, `email_verified`, `is_anonymised`).
- `users.user_type` is a **legacy/inert denormalised label** — see §4. It is
  safe to retain because nothing depends on it, and it must NOT be repurposed
  into an authorization value without a PO decision and an explicit
  authorization policy.
- Identity becomes **operational** only through relationship rows:
  `organization_members`, `staff_profiles`, `consultant_firm_members`,
  `consultant_profiles` (firm), `processing_entities` (via staff profile
  `entity_id`), and membership `role`s.

## 4. Investigation of `users.user_type` (CURRENT FACT)

| Question | Evidence |
|---|---|
| Meaningful runtime behaviour? | **No.** Backend application code contains zero reads of `users.user_type` (only hits found were inside vendored packages). |
| Which values exist? | Live DB: `customer` 915, `consultant` 52, `staff` 16, `NULL`/empty 346. |
| Where referenced? | Seeder writes; init-schema column; `rc2_rls.sql` lists it among protected columns (column-level protection only — no policy **reads** its value). |
| Affects authorization? | **No.** `AuthUser` is resolved from staff/membership/entity rows only. |
| Affects onboarding/routing? | **No.** Routing uses `/api/v3/me/context` relationship resolution. |
| Affects billing? | **No.** Billing keys on `organization_id` / `consultant_id`. |
| Affects RLS? | **No.** Identity RLS keys on membership/profile rows. |
| Legacy/unused? | **Yes** — inert label retained for compatibility/audit context. |
| Safe to retain? | Yes — no policy reads it, it is column-protected, and ignoring it cannot be exploited because nothing grants on it. |
| Safe to repurpose? | **No, not without a PO decision.** Repurposing it into an authorization signal without a full identity+workspace+ownership+action policy would create security ambiguity (violates §9 of the directive). |

## 5. Existing Actor Model (CURRENT FACT)

Five actor domains, each with its own membership/role and server-side guards:

1. **Customer organisation member** — `organization_members` role
   owner/admin/member/viewer; org-scoped data via `organization_id`; final
   customer approval authority for owner/admin.
2. **Consultant firm member** — `consultant_profiles` + firm membership;
   client relationships via `consultant_clients(consultant_id,
   organization_id)` with ACTIVE/SUSPENDED/ENDED semantics.
3. **Processing Entity member** — `staff_profiles.entity_id`; frozen PE roles
   (Data Entry Operator, Reviewer, QC Specialist, Admin); assignment-scoped
   access to customer-org work; no customer/CT-QC/Admin powers.
4. **CarbonTally internal staff** — `staff_profiles.entity_id IS NULL`;
   role/permissions via `staff_roles`; `/ops` operations incl. CT QC.
5. **CarbonTally Admin** — internal roles (incl. `system_admin`); privileged
   control-plane only.

Actor resolution is **single**, server-authoritative, precedence-ordered and
fail-closed (`/api/v3/me/context`). PE Admin ≠ CarbonTally Admin. PE staff are
never customers merely for having accounts.

## 6. Existing Workspace Model (CURRENT FACT)

- Destination is derived server-side, never from the URL or frontend role.
- `/home…` (customer) → `/consultant` → `/pe` (PEShell) → `/ops` → `/admin`
  (legacy quarantined) → `/onboarding` (no relationship yet).
- PE staff are bounced out of shared shells (server context + frontend
  defence-in-depth). No workspace-switcher UI exists.

## 7. Existing Billing & Data Ownership Model (CURRENT FACT)

- Subscriptions/credits/orders are **organisation-owned**; consultant billing
  is **firm-owned** (`consultant_billing.consultant_id`). `BillingService`
  charges an organisation; orgs without an active subscription are not
  charged (provider-neutral per V1.2).
- Data is organisation-owned through `organization_id` on every emissions,
  calculation, factor, document, workflow and storage table; PE processing is
  assignment of org-owned work; global factors are platform-owned. No table
  carries meaningful **user-owned** business data today (`users` holds
  profile/lifecycle only; any per-user row such as review stamps is
  provenance of an actor, not ownership of the record).

## 8. Product Problem Definition (CURRENT FACT + PROPOSED DESIGN)

**CURRENT FACT:** No PO-approved product problem exists today that requires an
individual data workspace. The pipeline CarbonTally monetises is
organisation-level emissions processing with evidence, review and approval.

**PROPOSED DESIGN (analysis framing):** the Phase-4 question is not "should we
add a personal tab?" but *"which concrete business problem needs a person-owned
emissions workspace that an organisation/firm/entity cannot already own?"* The
candidates below are analysed without being decided.

## 9. Individual-User Use Cases (analysis — NOT decisions)

| Use case | Already supported today? | Would require new architecture? |
|---|---|---|
| Person exploring CarbonTally before creating an organisation | Account exists; lands on `/onboarding` until an org relationship is formed. Identity-only state is supported. | No (identity-only). A *pre-org dashboard* would be new UX only if PO asks. |
| Sole trader / one-person business | Supported as an organisation with a single owner/member. | No. |
| Independent sustainability professional (consultancy of one) | Architecturally representable as a consultant firm with members; **consultant self-service sign-up is NOT approved** (see §14). | PO decision required on self-service consultant onboarding. |
| Person preparing personal/non-company emissions information | **Not supported.** No personal ownership domain exists. | Yes — full OPTION C-style domain. |
| Consultant before joining a firm | Identity-only; onboarding until relationship. | No. |
| User in multiple organisations | Schema permits; **no workspace switching and single-org runtime resolution**; no live multi-membership rows. | Yes (switching) — PO decision required. |
| User in a customer org AND a consultant firm (dual actor) | Schema permits both rows; runtime precedence currently resolves consultant-over-org in `/api/v3/me/context` while org-scoped authorization remains available to the same user. Precedence is implicit, not a ratified decision. | PO decision required on precedence/switching. |
| User needing billing before org creation | Not meaningful — billing is org-level; no org = nothing to bill. | Only if individual billing were ever approved. |

## 10–13. Candidate Architectures (PROPOSED DESIGN — analysis only)

### OPTION A — No personal workspace (status quo, clarified)

Every productive user belongs to an organisation, consultant firm, PE or
CarbonTally internal domain. An authenticated person with no relationship
remains an **identity-only** account whose destination is onboarding until an
organisation relationship exists. No personal emissions ownership is
introduced.

### OPTION B — Individual as lightweight identity only

Same as A plus explicit identity-only account capabilities: profile
management, invitation receipt/acceptance, join flows, and a controlled
onboarding destination. **No** personally owned emissions/documents/reports/
subscriptions.

### OPTION C — Individual personal workspace

A user receives a true personal workspace owning documents, emissions,
calculations, reports and potentially subscriptions. This is a **new
authorization/data-ownership domain** (new resource scoping, RLS family, API
context, workspace surface, storage, billing object).

### OPTION D — Hybrid (individual first, then org/firm/entity)

An individual account may later own or participate in organisations, firms and
entities. Inherits every OPTION C complexity plus actor-precedence and
conversion/merging complexity, and blurs the V1.2 trust-domain separation.

### Comparative decision matrix

| Dimension | A | B | C | D |
|---|---|---|---|---|
| Business value now | Preserves approved model | Marginal identity UX | High effort, undefined demand | High effort + ambiguity |
| Security risk | None (unchanged) | Low (identity-only) | High (new domain, IDOR/cross-workspace/privilege surface) | Highest |
| Billing impact | None | None | New user-level model (PO) | New model + migration |
| Data ownership | Org/firm/entity only | Unchanged | New user-owned tier | Mixed ownership ambiguity |
| Actor precedence impact | None | None | Requires personal-vs-org precedence rule | Complex switching |
| Schema/migration | None | None (or minimal profile fields) | Large (ownership columns/tables/RLS) | Largest |
| V1.2 preservation | Complete | Complete | Requires careful layering | Strains every invariant |

## 14. Security Analysis (per candidate — PROPOSED DESIGN)

- **A/B:** no new attack surface. Identity-only accounts must still be bound
  by RLS (no data rows to read), invitations must remain server-authorised,
  and `/onboarding` must stay relationship-gated. The untrusted list
  (frontend role, user metadata incl. `user_type`, URL/org params, route
  guards) is unchanged.
- **C:** requires a new authorization tuple
  `identity + workspace + resource + action + policy`. Risks: IDOR across
  personal workspaces, personal↔org data cross-reads (documents, factors,
  evidence), privilege escalation if personal rows ever join org/PE queries,
  billing charge confusion, lifecycle orphans (what happens to a personal
  workspace when the account is deleted/anonymised), and report/evidence
  provenance ambiguity. RLS must be extended consistently for every personal
  resource and every existing org-scoped table that might gain a nullable
  `owner_user_id` — nullable ownership columns are a classic RLS bypass and
  cross-workspace leak vector and would need careful NOT-NULL-safe design.
- **D:** inherits C risks and adds precedence races when a user is both
  individual and org/consultant/PE/staff — the exact class of ambiguity
  `user_type`-style shortcuts create.

## 15. Data Ownership Analysis (PROPOSED DESIGN)

Today's data is deterministically organisation-owned (customer org),
platform-owned (global factors/templates), firm-owned (consultant billing), or
assignment-scoped work on org-owned batches (PE). No table is user-owned.

For any individual workspace (C), a new ownership carrier is required for:
documents, extracted/mapped/calculated data, calculation snapshots, evidence,
emissions logs, reports, customer factors, subscriptions/credits/orders,
storage usage, invitations and retention metadata — i.e. a parallel to the
`organization_id` column family, or new personal-scoped tables. Under A/B, no
ownership change is required and data ownership stays unambiguous.

## 16. Billing Analysis (PROPOSED DESIGN — no billing changes)

- Subscriptions/credits/orders are organisation-owned; consultant billing is
  firm-owned; charges key on `organization_id`; provider-neutral per V1.2.
- Under **A/B**: no individual subscription or credit object is needed;
  nothing to change.
- Under **C**: individual subscriptions, user-owned credits and invoices
  would be **required** — a new commercial model (who owns credits? who pays?
  how does an individual convert to an organisation without re-billing?)
  needing PO + legal/commercial decisions. V1.2 billing must not be silently
  redesigned.

## 17. Onboarding Analysis (PROPOSED DESIGN)

- **A/B:** the `/onboarding` destination remains the correct home for an
  authenticated person with no relationship. Onboarding = form an
  organisation (self-service sign-up → org owner, already in V1.2 D35) or
  accept an invitation into an existing org/firm. No personal workspace
  step.
- **C:** onboarding would need a branching decision (personal workspace vs
  organisation) before any org context exists — a new product flow with
  conversion ambiguity.

## 18. Conversion / Lifecycle Analysis (PROPOSED DESIGN — no implementation)

Scenarios analysed under the recommended A/B model (identity-only):

- Individual (no relationship) → joins organisation: one `organization_members`
  insert; nothing to migrate; the identity stays the same row.
- Individual → creates organisation (owner): supported today (D35).
- Individual → consultant: requires a firm/membership; **consultant
  self-service sign-up remains an open PO decision** (§20).
- Individual → PE staff: provisioned staff profile with `entity_id`;
  assignment-scoped access only; PE Admin never becomes CarbonTally Admin.
- User leaves org / relationship ends: membership `is_active=false` or row
  removed; **data is preserved and remains org-owned** (revocation ≠
  deletion, per CarbonTally principle); audit/provenance retained.
- Account deletion/anonymisation: governed by retention/anonymisation
  (`is_anonymised`) — business data is org-owned, not user-owned, so account
  lifecycle never threatens org data.

## 19. Multi-Actor / Dual-Identity Analysis (CURRENT FACT + analysis)

- Schema-permitted combos: org member + staff profile; org member + consultant
  firm member; consultant firm member + PE staff; staff + PE are mutually
  exclusive by `entity_id` semantics; multiple org memberships are permitted
  by the schema but currently unused (no live multi-org users; single-org
  runtime resolution).
- `/api/v3/me/context` currently gives **one destination** using fixed
  precedence (staff → PE → consultant → org → onboarding). For a dual
  consultant+org user the destination is `/consultant` while org-scoped
  authorization remains valid for the same identity — i.e. the current
  model is single-destination but **not** single-actor-strict.
- **PROPOSED DESIGN:** do not change precedence during Phase 4. If the PO
  later wants explicit dual-actor support, workspace switching must be
  server-authoritative (a chosen active context stored/derived server-side,
  not a frontend tab), gated per actor domain, and validated as a separate
  decision. A personal workspace would add a third context type to this
  already-sensitive resolution and is not recommended.

## 20. Recommended Architecture (PROPOSED DESIGN — recommendation)

**Recommendation: OPTION A** — do not implement a personal workspace — with
OPTION B treated as an optional, separately-approved identity-only account
polish, never a data-owning surface.

Why it best fits CarbonTally:

- **Business:** the platform's value chain is organisation emissions
  processing with evidence/review/approval; no approved individual product
  problem exists. Sole traders/one-person businesses already use orgs;
  pre-relationship persons already have identity + onboarding.
- **Value:** zero new security surface, zero new billing model, zero new
  ownership ambiguity; preserves V1.2 trust-domain separation and the frozen
  actor/workspace architecture.
- **Security:** no new authorization domain; the untrusted list stays
  unchanged; RLS unchanged; actor precedence unchanged.
- **V1.2 preservation:** complete.
- **Onboarding:** unchanged — `/onboarding` until an org/firm/PE/staff
  relationship exists.
- **Billing:** unchanged (org/firm-owned). Individual billing is NOT needed.
- **Data ownership:** unchanged (org/platform/firm/assignment).
- **Multi-actor:** unchanged single-destination precedence; if the PO later
  approves explicit dual-actor switching it is a separate, server-authoritative
  design decision and must not reuse `user_type`.
- **Complexity:** near zero for A; identity-only polish (B) is contained.
  Migration/testing/maintenance costs of C/D are disproportionate to any
  currently-defined demand.

Explicit statement: **Do NOT implement a personal workspace.**

## 21. Product Owner Decisions Required

The following are **OPEN** and require explicit PO approval. None is decided
by this document:

1. Existence of a personal workspace → **recommended: NO (OPTION A)**.
2. Personal data ownership → **NO unless 1 is approved**.
3. Personal documents → **NO unless 1 is approved**.
4. Personal reports → **NO unless 1 is approved**.
5. Personal subscriptions → **NO unless 1 is approved** (billing remains
   org/firm-owned).
6. Personal credits → **NO unless 1 is approved**.
7. Multi-workspace switching → separate decision; if pursued, must be
   server-authoritative and PO-approved.
8. Multi-organisation membership precedence → PO decision required before any
   switching; current single-org resolution is the ratified default.
9. Individual → organisation conversion → already supported (org create/invite);
   confirm as the only sanctioned path.
10. Individual → consultant conversion → **UNDECIDED**: consultant
    self-service sign-up is NOT approved and must not be silently added.
11. Individual → PE conversion → **NO** self-service; PE membership is
    provisioned/assignment-scoped only.
12. Account deletion/lifecycle → governed by retention/anonymisation rules;
    confirm org-owned data survives account lifecycle.
13. Data retention after conversion → org data remains org-owned; identity is
    not copied; confirm no data copying is ever performed on conversion.

## 22. Security / Legal / Commercial Review Items (PROPOSED DESIGN — requested)

**Security review:** any future approval of C/D (not recommended) requires a
security review of: personal-workspace resource ownership + RLS family,
nullable-owner-column risks, personal↔org cross-read vectors, actor-precedence
races, account lifecycle/deletion semantics, and `user_type`-style shortcuts.
For A/B no security review is required beyond routine identity work.

**Legal/commercial review:** any individual-subscription/credit model
(recommended: not pursued) requires legal/commercial review (who pays, invoice
ownership, VAT, retention of personal data, GDPR deletion/anonymisation).
Also confirm no marketing of "personal carbon accounts" precedes a PO
decision.

## 23. Implementation Impact — IF APPROVED (currently NOT approved)

- **A (recommended):** no implementation beyond optional documentation of the
  identity-only state and (if PO approves B) minimal identity-only account
  pages. No routes, no schema, no auth, no billing changes.
- **C/D (not recommended, NOT approved):** new ownership columns/tables, RLS
  policies, `/api/v3/me/context` extension or new context resolver,
  personal workspace surface, personal storage policy, user-level billing
  objects, retention/lifecycle handling — a full new domain.

## 24. Migration Impact — IF APPROVED (currently NOT approved)

- **A:** none (migration count stays 42).
- **C/D:** large, multi-migration programme; every new ownership carrier and
  RLS policy must be backwards compatible with the 42-migration baseline and
  the 7,049 factors; no ad-hoc schema edits.

## 25. Testing Strategy — IF APPROVED (currently NOT approved)

- **A:** existing identity/workspace regression suite (context resolution,
  org/staff/entity guards, RLS) remains the acceptance gate.
- **B:** add tests for identity-only account flows (profile, invitations,
  onboarding) — no data-ownership tests needed.
- **C/D:** new negative test matrix (personal→org, org→personal, cross-user
  IDOR, precedence, lifecycle/deletion, billing ownership) mirroring the
  Customer A↔B / Consultant / PE isolation test families.

## 26. Explicit Non-Goals

Phase 4 does NOT: create a personal workspace; create `user_type='individual'`
authorization; modify `/api/v3/me/context`; change actor precedence; modify
RLS; change authentication; change frontend routes/shells; change billing;
create database tables/migrations; start Phase 5; or implement D38/D39/D40.

## 27. Phase 4 Exit Criteria

All of the following hold (checked): actual identity/actor/workspace/billing/
data-ownership/multi-actor implementation inspected (read-only); `users.user_type`
behaviour investigated and evidenced; ≥3 architecture candidates analysed with
security/data/billing/onboarding/lifecycle implications; one recommended
architecture identified; PO decisions and security/legal/commercial review
items listed; implementation/migration/testing impact documented; no
implementation, migration, RLS, billing, route or actor-domain change made;
no V1.2 architecture change; no business data modified; 7,049 factors intact;
42-migration baseline intact; deliverable present at the required path.
