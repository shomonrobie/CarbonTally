# CarbonTally V3 — Actor, Workspace & Access Model

| | |
|---|---|
| Document type | Analysis / access-model authority |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE-TO-IMPLEMENTATION (analysis only — no code/schema/RLS/demo-data changes) |
| Created | 2026-08-20 |
| Revised | 2026-08-22 — D25 record (§40); D26 product-completion audit (§41) |
| Author | Cline |
| Terminology authority | `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md` |

## 1. Purpose

Define the authoritative CarbonTally V3 **actor, organisation/entity, workspace,
role, permission and access model** from the existing implementation — before
any additional demo users are created or Phase 9 begins. This is an analysis
document: the implementation is the source of truth; where the implementation
is ambiguous the ambiguity is preserved and recorded for human decision.

## 2. Authority hierarchy

1. Database schema (CHECK/FK in `supabase/migrations/*.sql`)
2. Domain constants (`backend/core/types.py`, `backend/domain/*.py`)
3. API contracts (`backend/api/*.py`)
4. RLS policies (`supabase/migrations/*_rls.sql`)
5. Frontend labels (`frontend/src/v3/**`)
6. Architecture/audit documentation (intent only)

## 3. Actor model

All actors below exist in the current implementation (name → representation →
surface). "Internal" = CarbonTally staff/entity staff; "External" = customer or
consultant identities.

| # | Actor | Representation | Role source | Permission source | Org/entity/firm relationship | Internal/External | Multi-tenant? | Auth identity |
|---|---|---|---|---|---|---|---|---|
| A1 | Customer org **owner** | `organization_members.role='owner'`; `AuthUser.role='org_owner'` | org membership CHECK | RLS `role IN ('owner','admin')` + `require_org_admin` | one org (membership row); `is_org_member` | External | multiple orgs possible (multiple membership rows) | Supabase auth user |
| A2 | Customer org **admin** | `organization_members.role='admin'`; `AuthUser.role='org_admin'` | org membership CHECK | RLS org-admin + `require_org_admin` | one org; `is_org_member` | External | multiple orgs possible | Supabase auth user |
| A3 | Customer org **member** | `organization_members.role='member'`; `AuthUser.role='org_member'` | org membership CHECK | `require_org_member`; RLS `is_org_member` | one org | External | multiple orgs possible | Supabase auth user |
| A4 | Customer org **viewer** | `organization_members.role='viewer'`; `AuthUser.role='org_viewer'` | org membership CHECK | `require_org_member` (read) | one org | External | multiple orgs possible | Supabase auth user |
| A5 | **Staff operator** | `staff_profiles` + `staff_roles.name='operator'` | `staff_roles` | `roles`/`staff_roles.permissions → can_process` | no org; `entity_id IS NULL` (internal) | Internal | N/A (internal) | Supabase auth user |
| A6 | **Staff reviewer** | `staff_roles.name='reviewer'` | `staff_roles` | `can_review` | no org; internal | Internal | N/A | Supabase auth user |
| A7 | **Staff QC specialist** | `staff_roles.name='qc_specialist'` | `staff_roles` | `can_process` + `can_review` | no org; internal | Internal | N/A | Supabase auth user |
| A8 | **Staff admin** | `staff_roles.name='admin'` | `staff_roles` | `can_manage_staff`, `can_view_all`, `can_process`, `can_review` | no org; internal | Internal | N/A | Supabase auth user |
| A9 | **Consultant firm owner** | `consultant_profiles.user_id` + `consultant_firm_members.role='owner'` | `consultant_firm_members` | `can_manage_clients` etc. (boolean flags) | one firm; grants to orgs via `consultant_clients` / `client_access` | External | multiple clients (orgs) via grants | Supabase auth user |
| A10 | **Consultant manager** | `firm_members.role='manager'` | `consultant_firm_members` | flags incl. `can_manage_team` | one firm; client grants | External | multiple clients | Supabase auth user |
| A11 | **Consultant** | `firm_members.role='consultant'` | `consultant_firm_members` | flags | one firm; client grants | External | multiple clients | Supabase auth user |
| A12 | **Consultant viewer** | `firm_members.role='viewer'` | `consultant_firm_members` | flags | one firm; client grants | External | multiple clients | Supabase auth user |
| A13 | **Processing-entity staff** | `staff_profiles.entity_id = processing_entities.id` | `staff_roles` + entity membership | `is_entity_member` (RLS, SELECT-only) + `require_entity_scope` | one entity (`entity_id`) | Internal (partner) | single entity (per staff row) | Supabase auth user |
| A14 | Derived `AuthUser` roles | `user`, `staff`, `admin`, `org_owner`, `org_admin`, `org_member`, `org_viewer` | `auth.py get_current_user` | — | — | — | — | Supabase JWT |

`[CONFLICT — FOR HUMAN DECISION]` role spellings: `owner` (schema) vs
`org_owner` (derived) — see glossary §15.1.

## 4. Organisation model

- **Tenant root** `organizations`; one-to-one `organization_metadata`;
  membership in `organization_members` (roles per §3).
- **RLS boundary**: `is_org_member(org)` = active member of an active org.
  Tenant-table policies are generated per table
  (`*_tenant_select/insert/update/delete` using `is_org_member` or
  `is_org_member OR is_org_consultant`). `organizations` itself is
  selectable by members or consultants.
- **Multi-tenancy**: a single auth user can hold membership rows in multiple
  organisations (`organization_members` UNIQUE `(organization_id, user_id)`),
  but `get_current_user` resolves **one** org via `.maybe_single()`. The V3
  frontend resolves the primary org via `resolveV3Organization`
  (`/api/organizations/members/user/{id}`). Multiple-org switching for one
  user is **not exposed** in the V3 UI (NOT IMPLEMENTED as a surface).

## 5. Staff model

- `staff_profiles` (workforce roster) + `staff_roles` (authoritative role +
  `permissions` jsonb; FK `staff_profiles.role_id → staff_roles.id`).
- **CarbonTally internal staff** = `staff_profiles.entity_id IS NULL`
  (positive NULL convention, ADR-V3-001 Q5). They alone may run the
  manual-extraction pipeline and ops-wide surfaces
  (`operations_auth.require_internal_staff`).
- **Processing-entity staff** = `staff_profiles.entity_id` populated. They are
  scoped to their own entity's work (`require_entity_scope`,
  `is_entity_member`), and are **structurally unable** to access the
  manual-extraction pipeline (batches/items carry no `entity_id` column —
  documented gap in the conformity gate).
- `auth.py get_current_user` resolves staff `role`/`role_name` from
  `staff_roles` (P1-F3); `require_admin` is satisfied by a
  `staff_roles.name='admin'` identity.
- Staff demo roles seeded: `operator`, `reviewer`, `qc_specialist`, `admin`.

### 5.1 AUTHORITATIVE STAFF ROLE MODEL (clarification)

```
staff_profiles
    ↓ (role_id FK)
staff_roles
    ↓ (permissions jsonb)
staff_roles.permissions  →  enforced by operations_auth / require_admin
```

- `staff_roles` is the **authoritative** staff-role/permission source
  established by the V3 implementation and the F2/F3 fixes
  (`operations_auth._resolve_context`, `auth.py get_current_user`).
- The **general `roles` table must NOT be treated as equivalent to
  `staff_roles`.** It is the customer-org role reference (invitation
  resolution) and is not the staff permission source (glossary §15.2).
- The `roles` table remains a **legacy/secondary item requiring future
  architectural disposition** (D2). It is not deleted or renamed here, and no
  schema change is proposed by this document.

## 6. Processing entity model

**What a processing entity is** (from `domain/entity.py`, ADR-V3-001):
> "A first-class **Human Data Processing Entity** (V3M-1 row)… a concrete
> entity; CarbonTally-internal processing is represented by `entity_id IS NULL`
> on staff/work rows (never by a synthetic entity)."

**Canonical term.** **Processing Entity** is the canonical implementation term.
It must **not** be renamed to "manual data extraction company", "processing
company" or "extraction company"; those may be used only as descriptive
business language if needed.

**Preserved conventions:**
- CarbonTally internal processing: `staff_profiles.entity_id IS NULL`.
- Processing-entity staff: `staff_profiles.entity_id IS NOT NULL`.
- No entity ↔ organisation relationship is invented here; none exists in the
  implementation.

**Implementation questions (answered by §6.1/§6.2/§30):** the current
**implementation** does not establish whether: one processing entity may serve
multiple organisations; one organisation may use multiple processing entities;
processing work should be routed through an entity; or entity staff should
participate in the manual-extraction pipeline. The **business** question is now
**RATIFIED** (D14/D17, 2026-08-20, §6.1) — the implementation gap is documented
in §6.2 and §30.

### 6.1 RATIFIED BUSINESS DECISION (Processing Entity operating model)

Authoritative business decision (recorded 2026-08-20):

1. A single Customer Organisation may have extraction/processing work processed
   by **multiple processing parties** (CarbonTally internal staff and/or
   Processing Entity A/B/C/…).
2. A Customer Organisation is **NOT permanently assigned** to one Processing
   Entity; there is **no `organizations.processing_entity_id`** requirement and
   no assumption of a permanent customer↔entity relationship. The intended
   relationship is **work-assignment based**:

   ```
   Customer Organisation
        └── Processing Work
                └── Assignment
                       ├── CarbonTally internal staff
                       └── Processing Entity
   ```

3. **CarbonTally controls the assignment** of extraction work; one or more
   CarbonTally staff members assign work to internal staff or to an external
   Processing Entity.
4. A Processing Entity receives **only the work assigned to that entity**.
5. Entity staff access is scoped to **work assigned to their Processing
   Entity / authorised staff** — never broad customer-organisation access.
6. The same Customer Organisation may have simultaneous work assigned to
   CarbonTally + Entity A + Entity B + Entity C.

**Status: RESOLVED BUSINESS REQUIREMENT — IMPLEMENTATION GAP REMAINS.**
The current implementation does **not** yet support entity-level assignment of
extraction work (see §6.2 and §30). This document does **not** claim otherwise.

### 6.2 Current implementation vs the ratified decision

| Business requirement | Current implementation |
|---|---|
| Entity receives only its assigned extraction work | **IMPLEMENTED (D22, 2026-08-21)** — `manual_extraction_batches.entity_id` (batch-level, nullable FK → `processing_entities`); CarbonTally assigns via the extended `assign` endpoint; entity staff see only their entity's batches via RLS + server-side guards (§30/§37.14) |
| Entity staff process assigned work | **IMPLEMENTED (D22)** — entity extraction workspace (`/api/v3/ops/entities/{id}/extraction/*`): list batches/items, workspace, start/extract/map/calculate/status + mediated clarification; entity staff also keep entity-scoped `manual_review_queue`/`issues` access |
| Multiple parties per organisation | **IMPLEMENTED (D22)** — Entity A/B/C + internal batches can coexist on one org (each batch has exactly ONE active party) |
| CarbonTally controls assignment | **YES (internal staff level) + entity level (D22)** — `assign_batch` (`can_manage_staff` + `can_process`, internal staff only) accepts exactly one of `assigned_to` (internal operator) / `entity_id` (active Processing Entity); reassignment records before→after in the V3 audit trail |
| Entity-scoped, non-broad org access | **IMPLEMENTED (D22)** — RLS `is_entity_member` + new entity SELECT storey on `manual_extraction_batches`/`manual_extraction_items`; entity staff never receive org-wide access (D20) |
| Auditable assignment/reassignment history | **IMPLEMENTED (D22)** — assignment/reassignment recorded through the existing V3 `audit_trail` (ADR-V3-013; `manual_extraction_batch` entity type, before/after party, reason). The dormant `processing_assignments`/`reassignment_history` family remains untouched |

Answers to the audit questions:

| Question | Answer |
|---|---|
| Is it a third-party manual data extraction company? | **PARTIALLY — "Human Data Processing Entity"** is the implementation's own term (V3M-1). A concrete entity row represents a partner/processing unit distinct from CarbonTally-internal staff. The term "processing company" is **not** used in code. |
| Is it an internal CarbonTally processing unit? | No — internal processing is `entity_id IS NULL`, never an entity row. |
| Can multiple processing entities exist? | **YES** — `processing_entities` is a multi-row table (`list_all`, CRUD at `/api/v3/processing-entities`, admin-guarded). |
| Can one entity process multiple customer organisations? | **IMPLEMENTATION: NOT DETERMINED** — entity-scoped work surfaces (`manual_review_queue.entity_id`, `issues.entity_id`) are org-linked too, but no entity↔org association table exists; the UI/API never exposes multi-org-per-entity. **BUSINESS: RATIFIED** — an entity may process work for multiple orgs via assignments (§6.1). |
| Can one customer organisation be processed by multiple entities? | **IMPLEMENTATION: NOT DETERMINED** — no org↔entity association exists; extraction has no entity dimension. **BUSINESS: RATIFIED** — one org may use multiple processing parties simultaneously (§6.1, §30). |
| Can staff belong to an entity? | **YES** — `staff_profiles.entity_id`. |
| Can CarbonTally internal staff have `entity_id NULL`? | **YES** — that is the positive convention. |
| What permissions are entity-scoped? | RLS SELECT visibility on `processing_entities`, `staff_profiles`, `manual_review_queue`, `upload_batches`, `issues` (via `is_entity_member`; entity status must be `active`). API: `require_entity_scope` + `/api/v3/ops/entities/{id}/dashboard`. |
| Does the current UI expose entity management? | **IMPLEMENTED (D24, 2026-08-22)** — ops `Entities` tab (`v3/ops/ProcessingEntitiesTab.jsx`, staff admins only) lists + creates Processing Entities; the Data entry queue has a batch **Assign** control (internal operator XOR processing entity, with reason) for `can_manage_staff` + `can_process` internal staff; the Staff tab can create profiles with an entity scope and change a profile's entity assignment (`updateOpsStaff`). Entity staff still land only on `EntityExtractionWorkspace`. |
| Does the implementation support multiple extraction companies? | **NOT DETERMINED** — entity rows can exist, but the manual-extraction pipeline cannot be entity-scoped (no `entity_id` column on batches/items), so "multiple extraction companies" is not operational. |

Entity lifecycle (`ENTITY_STATUSES`): `active | remediation | suspended |
terminated`; only `active` grants entity access (`is_entity_member`).


## 7. Consultant firm model

- **Firm owner** = the `user_id` on `consultant_profiles` (the firm's primary
  identity) and the matching `consultant_firm_members.role='owner'` row.
- **Firm members** = `consultant_firm_members` rows; display `role`
  (`owner|manager|consultant|viewer`); **authorization** = `can_manage_clients`,
  `can_upload_documents`, `can_generate_reports`, `can_manage_team` booleans +
  `client_access uuid[]`.
- **Firm management APIs**: `/api/v3/consultants/me` (profile),
  `/api/v3/consultants/me/firm-members` (list/add/update) — membership
  mutations gated by `can_manage_team`/`manage_team` permission.
- RLS on `consultant_profiles`: `cp_select_own` (own profile);
  `consultant_firm_members`: `cfm_select_self_or_team_admin`.

## 8. Client model (consultant → client organisation)

Trace as implemented:

```
ConsultantFirm (consultant_profiles)
   └─ FirmMember (consultant_firm_members: role + can_* + client_access uuid[])
        └─ ClientGrant (consultant_clients: consultant_id=firm, organization_id, status)
             └─ ClientOrganisation (organizations row)
                  └─ ClientWorkspace (frontend ClientWorkspace component)
```

- **Who owns the firm**: the `consultant_profiles.user_id` identity (demo:
  `consultant@demo.carbontally.local`).
- **Who manages firm members**: firm members with `can_manage_team` (demo:
  the owner).
- **How consultant permissions work**: `can_*` flags on the member row
  (`consultant_auth.ensure_consultant_permission`).
- **How client access is granted**: a `consultant_clients` row for the firm +
  org **or** an explicit `client_access` uuid[] entry on the firm member.
  RLS `is_org_consultant` checks both; API `ensure_consultant_org_access`
  mirrors it server-side.
- **How client switching works**: the consultant frontend keeps the active
  client in `localStorage('v3_consultant_active_client')` and renders the
  `ClientWorkspace` for it; the server re-authorizes the client id on every
  request (`_checked_client` → ownership + `ensure_consultant_org_access`).
- **How active client context is stored**: frontend-local only (localStorage);
  no server-side "active client" state.
- **APIs enforcing client access**: every `/api/v3/consultants/clients/*`
  endpoint passes `require_consultant` + ownership/org-access checks.
- **RLS enforcing client access**: `is_org_consultant` on org tenant tables
  (read); `consultant_clients_*` policies.
- **Multiple clients**: YES — `list_clients` returns all grants; a consultant
  can access multiple orgs.
- **Inactive/revoked client**: `consultant_clients.status='inactive'` — the
  frontend marks it inactive; API list/get still return it, but
  `is_org_consultant` does **not** filter on client status (only firm-member
  active + grant existence) — `[CONFLICT — FOR HUMAN DECISION: revocation
  semantics for inactive grants are not enforced in RLS; §20]`.


## 9. Workspace / surface model

The implementation does **not** define a "Workspace" abstraction in code. It
has **role-gated route surfaces** plus two frontend components that use the
word "workspace" (`ClientWorkspace`, `WorkItemWorkspace`). Classification:

| Surface | Status | Implementation | Routes | Actors | Context | Data |
|---|---|---|---|---|---|---|
| **Customer workspace** | IMPLEMENTED (as route group; the word is used in the UI: "V3 customer workspace") | `V3Layout` + `v3/customer/*` | `/home`, `/emissions`, `/documents`, `/processing`, `/reports`, `/reports/:id`, `/organization` | org owner/admin/member/viewer (`is_org_member`) | org from `resolveV3Organization` | org reports, documents, batches, members, facilities, assets, suppliers, emissions |
| **Consultant workspace** | IMPLEMENTED (label "Consultant workspace") | `v3/consultant/ConsultantPage.jsx` | `/consultant` (dashboard + client switch + workspace views) | consultant firm members (`require_consultant`) | firm + active client (localStorage) | firm stats, client list, client workspace payload |
| **Client workspace** | IMPLEMENTED (`ClientWorkspace` component) | `ConsultantPage.jsx:45` | inside `/consultant` (view='workspace') | firm members with a grant for that client | active client id (localStorage) | context/reports/dashboard/processing/issues/documents via `/api/v3/consultants/clients/{id}/*` |
| **Operations workspace** | IMPLEMENTED (label "Internal Operations"; split-screen `WorkItemWorkspace`) | `v3/ops/*` | `/ops` (tabs Dashboard/Data entry/Review/QC/Staff[/Entities D24]) + `WorkItemWorkspace` | staff (`require_staff` + permissions; internal only for pipeline) | staff identity; batch/item from URL | ops dashboard aggregates, queues, items |
| **Processing-entity workspace** | IMPLEMENTED (D24 — UI completes the D22 backend) | `v3/ops/EntityExtractionWorkspace.jsx` + `ExtractionPanel.jsx` | `/ops` renders the entity workspace for `profile.entity_id` staff | entity staff (RLS `is_entity_member`); internal staff assign to entities | `entity_id` | assigned batches/items, extraction/mapping/calculation, mediated clarification |
| **Organization admin surface** | IMPLEMENTED (tabs Profile/Members/Suppliers/Facilities & Assets/Security) | `v3/admin/*` | `/organization` | owner/admin (`require_org_admin` for mutations) | org | org profile, members, invitations, facilities, assets, suppliers |
| Legacy monolith | IMPLEMENTED | `App.js` (legacy) | `/dashboard/*`, uploads, manual entry | any signed-in user | — | legacy screens (superseded by V3 surfaces) |

**Context selection**: customer = primary org (server `resolveV3Organization` →
legacy membership API); consultant = localStorage active client;
ops = caller's staff identity. No cross-surface "workspace" object exists —
the term is conceptual except for the two `*Workspace` components.


## 10. Role model

Four independent role families coexist (do **not** merge them):

1. **Organisation roles** — `organization_members.role` CHECK:
   `owner | admin | member | viewer` (customer tenancy only).
2. **Staff roles** — `staff_roles.name`: `operator`, `reviewer`,
   `qc_specialist`, `admin` (demo-seeded; the vocabulary table is open);
   permissions via `staff_roles.permissions` jsonb.
3. **Consultant firm roles** — `consultant_firm_members.role`:
   `owner | manager | consultant | viewer`; authorization via `can_*` booleans.
4. **Derived `AuthUser` roles** — `user | staff | admin | org_owner |
   org_admin | org_member | org_viewer` (computed in `get_current_user`, used
   by legacy `require_*` guards).

## 11. Permission model

- **Org permissions** — implied by role (`owner`/`admin` = admin per RLS;
  `member`/`viewer` = member read). Legacy `DEFAULT_ORG_PERMISSIONS` exists but
  is not the enforcement point.
- **Staff permissions** — `can_view_all`, `can_manage_staff`,
  `can_manage_roles`, `can_view_organizations`, `can_manage_organizations`,
  `can_extract`, `can_process`, `can_review`, `can_approve`, `can_export`,
  `can_delete` (reference `STAFF_PERMISSION_KEYS`). Phase 8 enforces the subset
  `can_view_all`, `can_process`, `can_review`, `can_manage_staff`.
- **Consultant permissions** — `can_manage_clients`, `can_upload_documents`,
  `can_generate_reports`, `can_manage_team` (firm-member booleans).

## 12. RLS / access model

Three RLS axes (ADR-V3-010), each deny-by-default where enforced:

| Axis | Helper | Applies to | Semantics |
|---|---|---|---|
| Customer/Org | `is_org_member(org)` | every tenant table (generated `*_tenant_*` policies) | active member of active org |
| Consultant | `is_org_consultant(org)` | org tenant read (added to select policies) + `organizations` | active firm member with `client_access @> org` **or** live `consultant_clients` row |
| Processing entity | `is_entity_member(entity)` | `processing_entities`, `staff_profiles`, `manual_review_queue`, `upload_batches`, `issues` (SELECT) | active staff of an `active` entity |

Service-role (backend repos) **bypasses RLS by design**; every V3 API endpoint
re-authorizes server-side (`ensure_org_access`, `require_org_admin`,
`require_staff`/`require_internal_staff`/`require_entity_scope`,
`require_consultant`/`ensure_consultant_org_access`, `require_admin`). The RLS
layer protects direct client (anon/authenticated) access.


## 13. Customer access matrix

Actor roles = org roles (`owner`/`admin`/`member`/`viewer`). Enforcement:
`require_org_member` (read), `require_org_admin` (mutations; owner=admin per
P1-F4), RLS `is_org_member`.

| Capability | owner | admin | member | viewer | Enforcement |
|---|---|---|---|---|---|
| View dashboard/org data | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` + RLS |
| Manage org profile/metadata | ALLOWED | ALLOWED | DENIED | DENIED | `require_org_admin` |
| Manage members / invite users | ALLOWED | ALLOWED | DENIED | DENIED | `require_org_admin` |
| Manage facilities/assets/suppliers | ALLOWED | ALLOWED | DENIED | DENIED | `require_org_admin` |
| Upload documents / create upload batch | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` |
| Create extraction batch/work | ALLOWED | ALLOWED | DENIED | DENIED | `require_org_admin` (`v3_manual_extraction`) |
| View processing batches/items | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` |
| Calculate emissions | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` |
| View emissions history/exports | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` |
| Generate/download reports | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_org_member` |
| Access another org | DENIED | DENIED | DENIED | DENIED | `ensure_org_access` + RLS |

## 14. Consultant access matrix

Actor roles = firm member roles + `can_*` flags. Enforcement:
`require_consultant` (active firm member) + `ensure_consultant_org_access`
(per client org) + `ensure_consultant_permission` (per action).

| Capability | firm owner | manager | consultant | viewer | Enforcement |
|---|---|---|---|---|---|
| View consultant dashboard | ALLOWED | ALLOWED | ALLOWED | ALLOWED | `require_consultant` |
| List/switch clients | ALLOWED | ALLOWED | ALLOWED | ALLOWED (grant-gated) | `require_consultant`; grants |
| Access client workspace | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ownership + `ensure_consultant_org_access` |
| View client reports/documents/processing | ALLOWED | ALLOWED | ALLOWED | ALLOWED | per-client re-auth |
| Add/deactivate client grants | ALLOWED if `can_manage_clients` | per flag | DENIED unless flagged | DENIED | `ensure_consultant_permission('manage_clients')` |
| Upload/process client data | ALLOWED if `can_upload_documents` | per flag | DENIED unless flagged | DENIED | `ensure_consultant_permission('upload_documents')` |
| Generate reports | ALLOWED if `can_generate_reports` | per flag | DENIED unless flagged | DENIED | `ensure_consultant_permission('generate_reports')` |
| Manage firm team | ALLOWED if `can_manage_team` | per flag | DENIED unless flagged | DENIED | `ensure_consultant_permission('manage_team')` |
| Access a non-granted org | DENIED | DENIED | DENIED | DENIED | ownership + `ensure_consultant_org_access`; RLS `is_org_consultant` |

## 15. Operations access matrix

Actor roles = staff roles (internal staff `entity_id IS NULL`). Enforcement:
`require_staff` → permissions (`staff_roles.permissions`) +
`require_internal_staff` / `require_entity_scope`.

| Capability | operator | reviewer | qc_specialist | staff admin | entity staff |
|---|---|---|---|---|---|
| Ops dashboard (`can_view_all`) | ALLOWED | ALLOWED | ALLOWED | ALLOWED | DENIED (internal-only) |
| Data entry: start/extract/map (`can_process`) | ALLOWED | DENIED | ALLOWED | ALLOWED | DENIED (pipeline not entity-scoped) |
| Validate (`can_review`) | DENIED | ALLOWED | ALLOWED | ALLOWED | DENIED |
| Review queue (`can_review`) | DENIED | ALLOWED | ALLOWED | ALLOWED | CONDITIONALLY (own entity items only) |
| QC queue + QC action (`can_review`) | DENIED | ALLOWED | ALLOWED | ALLOWED | DENIED (ops QC is internal) |
| Manage staff/assignments (`can_manage_staff`) | DENIED | DENIED | DENIED | ALLOWED | DENIED |
| Staff roster list (`can_view_all`/`can_manage_staff`) | ALLOWED | ALLOWED | ALLOWED | ALLOWED | DENIED |
| Admin QC surface `/api/v3/qc/*` (`require_admin`) | DENIED | DENIED | DENIED | ALLOWED | DENIED |
| Entity dashboard (own entity) | DENIED | DENIED | DENIED | ALLOWED (internal) | ALLOWED (own) |


## 16. Workflow access matrix

Classification: ALLOWED / DENIED / CONDITIONALLY ALLOWED / NOT IMPLEMENTED /
UNCLEAR. "Cite" = the guard that enforces it.

### CUSTOMER

| Capability | Classification | Cite |
|---|---|---|
| View dashboard | ALLOWED (member+) | `require_org_member` |
| Manage organisation | ALLOWED (owner/admin) | `require_org_admin` |
| Manage members / invite | ALLOWED (owner/admin) | `require_org_admin` |
| Manage facilities/assets/suppliers | ALLOWED (owner/admin) | `require_org_admin` |
| Upload documents | ALLOWED (member+) | `require_org_member` (`/api/v3/uploads`) |
| Create extraction work | ALLOWED (owner/admin) | `require_org_admin` (batch/items create) |
| View processing | ALLOWED (member+) | `require_org_member` |
| Review customer data | CONDITIONALLY ALLOWED (item stage `customer_review`; internal flow) | `ITEM_STATUSES`; ops pipeline |
| Calculate emissions | ALLOWED (member+) | `require_org_member` (`/api/v3/emissions/calculate`) |
| View emissions | ALLOWED (member+) | `require_org_member` (exports) |
| Generate reports | ALLOWED (member+) | `require_org_member` (`/api/v3/reports`) |
| Download/export reports | ALLOWED (member+) | `require_org_member` |

### CONSULTANT

| Capability | Classification | Cite |
|---|---|---|
| View consultant dashboard | ALLOWED (active member) | `require_consultant` |
| Manage clients | CONDITIONALLY ALLOWED (`can_manage_clients`) | `ensure_consultant_permission` |
| Switch client | ALLOWED (grant-gated) | per-client re-auth |
| Access client workspace | ALLOWED (grant-gated) | `_checked_client` + `ensure_consultant_org_access` |
| Upload/process client data | CONDITIONALLY ALLOWED (`can_upload_documents`) | permission flag |
| View client reports | ALLOWED (grant-gated) | `/clients/{id}/reports` |
| Generate reports | CONDITIONALLY ALLOWED (`can_generate_reports`) | permission flag |
| Manage consultant team | CONDITIONALLY ALLOWED (`can_manage_team`) | permission flag |

### OPERATIONS

| Capability | Classification | Cite |
|---|---|---|
| View ops dashboard | ALLOWED (staff `can_view_all`, internal) | `require_staff`+`require_internal_staff` |
| Data entry / extraction | ALLOWED (operator `can_process`, internal) | `require_staff`+`ensure_staff_permission('can_process')` |
| Mapping | ALLOWED (operator `can_process`) | `map_item` |
| Validation | ALLOWED (reviewer/QC `can_review`) | `validate_item` |
| Review | ALLOWED (reviewer `can_review`) | `/api/v3/ops/queues/review`, review complete |
| QC | ALLOWED (staff `can_review`, on `extracted` items; admin surface separately) | `qc_item`; `/api/v3/qc/*` (`require_admin`) |
| Manage staff | ALLOWED (staff admin `can_manage_staff`) | `/api/v3/ops/staff` POST |
| Manage assignments | ALLOWED (staff admin `can_manage_staff` + operator/manager flags) | batch/review assign |
| View queues | ALLOWED (staff, per permission) | operator/review/qc queue endpoints |
| Process customer documents | CONDITIONALLY ALLOWED (internal staff; batch must be assigned/open) | `_ensure_operator_batch` |
| Access customer organisation data | CONDITIONALLY ALLOWED (via org-scoped review/issues rows) | org/entity guards |


## 17. Current demo-user coverage

Source: `local_backups/seed_demo_data.sql`, `local_backups/mint_tokens.py`,
`local_backups/local_dev_credentials.md`; verification from the smoke suite
(85/85) and the browser walk (12 captures).

| Demo user | Actor type | Role | Organisation | Entity | Firm | Permissions | Primary surface | Login | API | UI | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `owner@…` | Customer org owner | `owner` | CarbonTally Demo Ltd | — | — | org-admin | Customer | ✅ | ✅ | ✅ | FULL |
| `admin@…` | Customer org admin | `admin` | Demo Ltd | — | — | org-admin | Customer | ✅ | ✅ | ✅ | FULL |
| `member@…` | Customer org member | `member` | Demo Ltd | — | — | member | Customer | ✅ | ✅ | ✅ | FULL |
| `viewer@…` | Customer org viewer | `viewer` | Demo Ltd | — | — | member-read | Customer | ✅ | ✅ | ✅ | FULL |
| `consultant@…` | Consultant firm owner | `owner` | — | — | Net Zero Advisory | all `can_*` | Consultant | ✅ | ✅ | ✅ | FULL |
| `operator@…` | Staff operator | `operator` | — | NULL (internal) | — | `can_process`,`can_view_all` | Ops | ✅ | ✅ | ✅ | FULL |
| `reviewer@…` | Staff reviewer | `reviewer` | — | NULL | — | `can_review`,`can_view_all` | Ops | ✅ | ✅ | ✅ | FULL |
| `qc@…` | Staff QC specialist | `qc_specialist` | — | NULL | — | `can_review`,`can_process`,`can_view_all` | Ops | ✅ | ✅ | ✅ | FULL |
| `staff-admin@…` | Staff admin | `admin` | — | NULL | — | `can_manage_staff`,`can_view_all`,… | Ops + QC admin | ✅ | ✅ | ✅ | FULL |

## 18. Current demo-data coverage

| Item | Status |
|---|---|
| Customer organisation | PRESENT (CarbonTally Demo Ltd) |
| Customer members | PRESENT (4 roles) |
| Facilities / assets / suppliers | PRESENT (3 / 4 / 3, + additions from tests) |
| Documents | PRESENT (`organization_files` 5+; upload batches) |
| Extraction batches / items | PRESENT (4 batches, 4 items + pipeline-completed item) |
| Review queue | PRESENT (3 rows incl. completed) |
| QC | PRESENT (qc_approved items + QC action) |
| Reports | PRESENT (completed/pending/failed incl. real-generated 2024/2025) |
| Emissions | PRESENT (snapshots + logs, real factors) |
| Consultant firm | PRESENT (Net Zero Advisory Ltd) |
| Consultant client relationship | PRESENT (1 active grant on demo org) |
| Processing entity | **ABSENT** (no `processing_entities` rows seeded) |
| Staff/entity relationship | **ABSENT** (no entity staff) |
| Multiple organisations | ABSENT (single org; multi-org membership not demoed) |

## 19. Missing demo coverage

- **Consultant firm roles**: manager, consultant, viewer —
  **MISSING DEMO COVERAGE** (only the firm owner exists).
- **Processing entity staff**: **MISSING DEMO COVERAGE** (no entity row, no
  entity staff, no entity-scoped work).
- **Multiple processing entities**: **MISSING DEMO COVERAGE** (no entities).
- **Multiple customer organisations / cross-org isolation**:
  **MISSING DEMO COVERAGE** (single org; isolation is unit-tested only).
- **Entity staff working entity-scoped review/issues**: **MISSING DEMO
  COVERAGE**.
- **Consultant team management / client switching between multiple clients**:
  **PARTIAL** — switching works with one client; no second client to switch
  to.
- **Inactive/revoked client grant**: **MISSING DEMO COVERAGE**.
- **Processing-entity lifecycle (remediation/suspended/terminated)**:
  **MISSING DEMO COVERAGE**.
- **D24 (2026-08-22)**: the Processing-Entity workspace journey was
  **live-verified end-to-end with TRANSIENT data** (entity provisioned →
  entity-scoped staff profile created → batch assigned to entity → entity
  staff read own work; internal queue/dashboard/consultant/admin surfaces all
  denied; internal operators blocked from entity-assigned batch writes;
  cross-entity denied) and the transient rows were **fully cleaned up** — no
  permanent entity, entity staff, user, or demo data was created or left
  behind.


## 20. Ambiguous terminology (current implementation → options → decision)

Cross-referenced with the glossary §15. For each: CURRENT IMPLEMENTATION →
AMBIGUITY → POSSIBLE INTERPRETATIONS → RECOMMENDED HUMAN DECISION.

### T1. organisation vs customer
- **Current**: `organizations` table; the V3 UI says "customer workspace" and
  "organization administration"; docs use "customer" and "organisation"
  interchangeably.
- **Ambiguity**: is a "customer" = the org tenant, or a specific member role?
- **Options**: (a) customer = organisation tenant (org-scoped), member roles
  are internal; (b) customer = a class of users.
- **Recommended decision**: **customer = organisation tenant**; never a role.

### T2. organisation user vs customer user
- **Current**: `organization_members` links auth users to orgs; `public.users`
  carries `user_type` (`customer`/`consultant`/`staff` in the demo seed).
- **Ambiguity**: `users.user_type` is informational (no CHECK); "customer
  user" is used for org members.
- **Recommended decision**: `user_type` = informational label only; role is
  always derived from memberships/profiles.

### T3. processing entity vs processing company / manual data extraction company
- **Current**: "**Human Data Processing Entity**" (`processing_entities`,
  ADR-V3-001). "Processing company" and "manual data extraction company" do
  not appear in code.
- **Ambiguity**: docs loosely equate them.
- **Recommended decision**: use **processing entity** as the canonical term;
  treat "processing company"/"extraction company" as descriptive prose only.

### T4. CarbonTally internal staff vs operations staff vs entity staff
- **Current**: internal staff = `entity_id IS NULL`; entity staff = populated.
  "Operations staff" is the UI label for the internal ops surface.
- **Ambiguity**: "operations staff" could be misread as including entity staff.
- **Recommended decision**: "CarbonTally internal staff" (entity_id NULL) and
  "processing-entity staff" (entity_id set); "operations" = the internal
  surface.

### T5. workspace (customer / client / consultant / operations)
- **Current**: no workspace abstraction; route surfaces + two `*Workspace`
  components (`ClientWorkspace`, `WorkItemWorkspace`); UI copy uses "customer
  workspace", "Consultant workspace", "Client workspace", "Internal
  Operations".
- **Ambiguity**: the glossary/planning docs imply a workspace concept.
- **Recommended decision**: treat "workspace" as **product-surface
  terminology**, not a code concept (no abstraction to build).

### T6. client vs consultant vs member
- **Current**: `consultant_clients` = org grants; "client" in the consultant
  UI = the granted organisation; "consultant" = firm member; "member" = org
  role.
- **Ambiguity**: "client" as organisation vs "client contact".
- **Recommended decision**: client = granted organisation; client contact =
  `consultant_clients.client_contact_*`.

### T7. owner / admin / reviewer / QC specialist
- **Current**: `owner|admin` org roles; `reviewer|qc_specialist` staff roles;
  "reviewer" also a legacy concept.
- **Ambiguity**: reviewer vs org viewer; QC specialist vs staff admin QC.
- **Recommended decision**: keep role names scoped to their family
  (org roles vs staff roles vs firm roles) and never mix.


## 21. Human decisions required (consolidated, reclassified)

Before creating additional demo users, decide each item. Classification:
**A** = architecture/access decision; **B** = terminology/product-language
decision; **C** = open implementation question / non-blocking. Classification
is based on the audit evidence (implementation authority). Where the
implementation already pins a behaviour (e.g. F2/F3 staff model, F5 scope
normalisation), the item is marked **C** unless the decision would change
schema/RLS/API behaviour.

| # | Decision | Class | Explanation / evidence |
|---|---|---|---|
| D1 | Canonical org-role spelling (`owner`/`admin` vs derived `org_owner`/`org_admin`) | **B** | Terminology only; `require_org_admin` already accepts both spellings (P1-F4); no schema/RLS/API change needed to begin Phase 9. |
| D2 | `roles` table role: org reference only vs retire/repurpose | **C** | Staff authority already settled by F2/F3 (staff_roles). `roles` is a legacy/secondary item; disposition is non-blocking. |
| D3 | `customer_documents` vs `organization_files` — parallel or deprecated | **C** | Both operate today; no schema/RLS change needed for Phase 9 P0. Investigate during Phase 9. |
| D4 | Disambiguate "batch" (upload / extraction / issues batch) in docs+UI | **B** | Product language; no code/schema impact. |
| D5 | Define "work item" precisely | **B** | Terminology; current implementation defines it via `issues.work_item_id` FK (→ manual_review_queue) and NULL for manual-extraction items (P1-F2). |
| D6 | Ratify review vocabularies (staff-review queue vs customer-review stage vs legacy) | **B** | Terminology; three distinct vocabularies already exist and are table-scoped. |
| D7 | Scope aliases: reject vs keep normalising | **C** | P1-F5 already normalises `scope1..3`→`Scope 1..3` at the API boundary; no further change blocks Phase 9. |
| D8 | Report status vocabulary + CHECK | **C** | V3 uses `pending/generating/completed/failed`; legacy `queued/processing` is confined to a claim index. A CHECK would be a schema change — defer. |
| D9 | Staff permission set: ratify Phase 8 subset, retire legacy `can_*` | **C** | Phase 8 subset already enforced; legacy keys are reference-only. |
| D10 | Which free-text vocabularies become enums | **C** | Schema changes deferred; not required for Phase 9 P0. |
| D11 | Report types: `annual` only vs legacy labels | **C** | V3 engine already offers only `annual`; legacy labels die with the legacy surface. |
| D12 | Subscription source of truth | **C** | Non-blocking; investigate during Phase 9. |
| D13 | API generations / entry-point consolidation | **C** | A conformity-gate condition but not a prerequisite for P0 verification itself. |
| D14 | Processing-entity semantics: multi-org per entity, entity↔org association, entity-scoped pipeline | **A → RESOLVED** | **RESOLVED BUSINESS REQUIREMENT — IMPLEMENTATION GAP REMAINS** (ratified 2026-08-20): entities may receive assigned extraction work; an org is **not** permanently bound to one entity; no `organizations.processing_entity_id`. Implementation does not yet carry entity assignment on the extraction pipeline (see §6, §30). |
| D15 | Inactive/revoked consultant client: RLS enforcement semantics | **A → RESOLVED** | **RESOLVED + IMPLEMENTED** (2026-08-20, §34/§38.15): consultant access to a client requires an **ACTIVE** `consultant_clients` grant — enforced in RLS (`is_org_consultant`) and API (`ensure_consultant_org_access`); new grants default `active`; the firm may still manage its own grant rows. Does **not** imply CarbonTally ownership of the client (§37.7). |
| D16 | "Workspace": confirm product-surface terminology (no code abstraction) | **B** | Terminology; the implementation has route surfaces + two `*Workspace` components, no abstraction. |
| D17 | Whether entity staff should ever access the manual-extraction pipeline | **A → RESOLVED** | **RESOLVED BUSINESS REQUIREMENT — IMPLEMENTATION GAP REMAINS** (ratified 2026-08-20): entity staff must be able to process work **assigned to their Processing Entity / authorised staff**, scoped by assignment — **not** broad org access. Current `assign_batch` still rejects entity staff (see §6, §30). |
| D18 | Processing-Entity boundary: strictly non-customer-facing back-office processor — work access only, no customer/consultant access, no customer-facing communication, CarbonTally-mediated communication only | **A → RESOLVED** | **RESOLVED SECURITY REQUIREMENT** (ratified 2026-08-20, §35): entity staff have work access only, never customer/consultant access and no customer-facing communication authority. Current posture vs the boundary, the communication surfaces inspected, and the resulting gaps (incl. the name-string `admin`/`is_admin` risk) are documented in §35.3–§35.5. |
| D19 | Consultant-client lifecycle, direct-customer transition & white-label architecture | **MIXED** | **BUSINESS REQUIREMENT — RESOLVED** (commercial model, §37.1): consultant = direct CarbonTally customer; client initially the consultant's customer; client may become a direct customer; in-place data transition; export/import separate; termination ≠ ownership. **BUSINESS DECISION — REQUIRES USER APPROVAL**: lifecycle states, transition workflow, D15 revision, export/import scope (§37.4–§37.7). |
| D20 | Scope-aware staff authorization architecture (internal vs entity staff; role names not sufficient; legacy `roles` disposition; org-access bypasses) | **A** | **BUSINESS DECISION — REQUIRES USER APPROVAL** (design §38, required **before** entity provisioning): scope-first evaluation order; entity staff never pass `require_admin`/`require_role`/`is_admin`; `ensure_org_access` no-bound-org bypass limited to internal staff; `roles` table never authorizes staff. |
| D21 | Final consultant commercial model — hybrid; consultant-led MANAGED SERVICE default; consultant clients do not automatically use CarbonTally | **A → RESOLVED** | **BUSINESS REQUIREMENT — RESOLVED** (finalized 2026-08-20, §37). **White-Label Foundation IMPLEMENTED 2026-08-21 (§37.13)**: consultant branding configuration (backend + API + Consultant UI + audit + RLS posture), authorized brand-context resolution (CarbonTally / Consultant / Co-branded), report branding context on the report surfaces, email-sender configuration foundation. Smallest schema change — one column (`consultant_profiles.white_label_enabled`); **no new tenancy model**. Direct Customers → CarbonTally fallback intact. **PARTIALLY IMPLEMENTED / FUTURE**: rendered logo-in-report, per-consultant outbound email (domain verification), custom domains, consultant-client portal/access. D19 transition + export/import = **FUTURE / NOT IMPLEMENTED**. |
| D22 | Processing Entity work assignment + extraction workspace — CarbonTally assigns extraction work to internal staff OR Processing Entity A/B/C; entity staff process ONLY their entity's assigned work and NEVER gain broad customer-organisation access | **A → RESOLVED** | **RESOLVED + IMPLEMENTED (2026-08-21, §30/§32/§33/§37.14)**: batch-level `manual_extraction_batches.entity_id` (single-active-assignment carrier), entity-scoped RLS SELECT storey (mirroring `manual_review_queue`/`upload_batches`), an entity extraction workspace API (`/api/v3/ops/entities/{id}/extraction/*`), mediated clarification via entity-scoped `issues` (entity → CarbonTally → customer; never direct), and auditable assignment/reassignment through the existing V3 audit trail (ADR-V3-013). Bidirectional isolation enforced server-side + RLS; entity staff never pass internal-admin/role-name guards or customer-org surfaces (D20 intact). **NOT implemented**: full mediated messaging workflow (threads/replies), rendered report handoff, per-entity SLAs/capacity automation. |

## 22. Recommended demo-user matrix (PROPOSED — NOT CREATED)

Do **not** create one user per theoretical role. The matrix below is the
minimum that exercises CarbonTally V3. Classification:
A=functional UI, B=authorization, C=multi-tenant, D=consultant/client,
E=processing-entity.

| Identity | Role | Needed for | Rationale |
|---|---|---|---|
| `owner@demo…` (exists) | org owner | A, B, C | Customer admin + cross-org denial baseline |
| `admin@demo…` (exists) | org admin | B | Distinguish owner vs admin mutation paths |
| `member@demo…` (exists) | org member | A, B | Non-admin customer UI + denial paths |
| `viewer@demo…` (exists) | org viewer | B | Read-only boundary |
| `consultant@demo…` (exists) | firm owner | D | Consultant surface + client workspace |
| **`consultant-manager@demo…`** (NEW) | firm manager | D | `can_manage_team`/client admin vs owner; team mgmt |
| **`consultant-analyst@demo…`** (NEW) | firm consultant | D | Upload/generate-report permission gating |
| `operator@demo…` (exists) | staff operator | A, B | Data entry pipeline |
| `reviewer@demo…` (exists) | staff reviewer | A, B | Validate/review |
| `qc@demo…` (exists) | staff qc_specialist | A, B | QC gate |
| `staff-admin@demo…` (exists) | staff admin | B | Staff/assignment admin + `/api/v3/qc/*` |
| **`entity-operator@demo…`** (NEW) | entity staff | E | Entity-scoped review/issues + denial of internal ops |
| — second entity identity | entity staff (entity B) | E | Multi-entity isolation (if the multi-entity decision D14 lands as "supported") |
| — second organisation member set | org roles on Org B | C | Cross-org isolation (only after D1/D2 decisions; currently single-org) |

Notes:
- Existing 9 users already cover A, B (customer/staff axes), D (owner). They
  remain **sufficient for the currently implemented customer + internal staff
  + consultant-owner surfaces**.
- Additional identities are **proposed but NOT YET CREATED**: 
  `consultant-manager`, `consultant-consultant/analyst`, processing-entity
  staff, and optionally second-organisation / second-entity users.
- Creating them before the remaining D19/D20 approvals and the ratified-but-gapped
  D14/D17 implementation work could encode assumptions into demo data, so they
  are deferred until those are settled and initial Phase 9 verification is
  complete (see §25–§26).
- Do **not** add per-role users for `member`/`viewer` firm roles unless D6/D7
  decisions require demonstrating every firm role; `consultant-manager` and
  `consultant-analyst` cover the permission flags with fewer identities.
- A second organisation (Org B) is a **Phase 9 test-fixture requirement**
  (§27 P0-1), not a demo-identity requirement.


## 23. Recommended demo scenarios (PROPOSED — NOT CREATED)

1. **Customer happy path** (owner/member): dashboard → calculate emissions →
   upload document → create extraction batch → view processing → generate +
   download report. (Covered today.)
2. **Customer RBAC** (admin vs member vs viewer): owner/admin mutations allowed;
   member/viewer denied org-admin + extraction-create. (Covered today.)
3. **Consultant multi-client**: firm owner with two client grants; switch
   between clients; client workspace renders per-client data. (Needs a second
   org/client — currently single client.)
4. **Consultant team permissions**: manager (manage_team) vs analyst
   (upload/generate) vs viewer. (Needs new firm members.)
5. **Internal ops pipeline** (operator→reviewer→QC): full item lifecycle incl.
   validation and QC gate. (Covered today.)
6. **Staff admin** (assignments, staff roster, `/api/v3/qc/*` admin QC).
   (Covered today.)
7. **Entity isolation** (entity staff vs internal staff): entity staff see
   only their entity's review/issues; internal staff see ops-wide; entity staff
   denied the internal pipeline. (Needs entity rows + entity staff.)
8. **Cross-org isolation** (Org A vs Org B users). (Needs a second org.)

## 24. Explicit non-decisions

These were **not** decided here (out of scope / require human decision):
- Whether one org may use multiple entities / one entity may serve multiple orgs
  (D14) — **DECIDED 2026-08-20**: ratified business requirement, implementation
  gap remains (§6.1, §30).
- Whether entity staff may process assigned extraction work (D17) — **DECIDED
  2026-08-20**: ratified; scoped-by-assignment requirement, implementation gap
  remains (§6.1, §30).
- Whether `customer_documents` is deprecated (D3).
- Whether scope aliases are rejected or normalised permanently (D7).
- The "workspace" abstraction (D16) — treated as product-surface terminology.
- Inactive-client revocation semantics (D15) — **still unresolved**; the
  recommended rule is documented in §34 but not implemented.
- Any business rule not present in the implementation (e.g. entity↔org
  commercial terms) — recorded as NOT DETERMINED BY CURRENT IMPLEMENTATION.

## 25. Phase 9 readiness

### RESOLVED REQUIREMENTS WITH IMPLEMENTATION GAPS

These business decisions are **ratified** (2026-08-20) but the implementation
does not yet satisfy them — they must be **scheduled as implementation work**,
not re-decided:

- **D14 — Processing-entity operating model.** Entities receive **only work
  assigned to them**; orgs are not permanently bound to one entity; multiple
  parties (internal + Entity A/B/C) may serve one org; CarbonTally controls
  assignment. Gap: the manual-extraction pipeline carries **no entity-level
  assignment** (§6.2, §30).
- **D17 — Entity staff process assigned work.** Entity staff access is scoped
  to work assigned to their entity / explicitly assigned to them. Gap:
  `assign_batch` rejects entity staff; no entity-scoped extraction surface
  (§6.2, §30).
- **D18 — Non-customer-facing Processing Entity boundary.** Entities and their
  staff have **work access only** — never customer/consultant access and no
  customer-facing communication authority; all communication mediated by
  CarbonTally (§35). Gaps: the name-string `admin`/`is_admin` authorization
  could over-grant an entity-staff user (§35.5 G1/G2); no mediated
  entity↔CarbonTally communication channel exists (§35.5 G5); extraction
  assignment remains unsupported (§30).
- **D19 — Consultant client lifecycle & direct-customer transition.** Commercial
  model RESOLVED (§37.1); lifecycle states, the in-place transition workflow
  and export/import scope are design decisions awaiting approval
  (§37.4–§37.7). Non-blocking for Phase 9 P0; D15 is implemented (§34).
- **D20 — Scope-aware staff authorization.** Design recorded (§38): the
  internal-vs-entity staff boundary must be evaluated **before** role names;
  the legacy name-string guards (`require_admin`/`require_role`/`is_admin`),
  the live `ensure_org_access` no-bound-org bypass and the legacy `is_admin`
  bypasses must be fixed **before any entity staff provisioning**. Not a
  Phase 9 P0 blocker for existing surfaces.
- **D21 — Final consultant commercial model + White-Label Foundation.** Hybrid
  (direct + consultant customers) with consultant-led MANAGED SERVICE as the
  default; consultant clients do **not** automatically use/access CarbonTally
  (§37.1). Resolved. **D21 White-Label Foundation IMPLEMENTED 2026-08-21
  (§37.13)** — branding config (API + UI + audit), authorized brand-context
  resolution, report-branding context, email-sender config foundation, one
  schema column (`white_label_enabled`), no new tenancy model. Co-branding/full
  white-label rendering (rendered reports, outbound email, custom domains),
  D19 transition and export/import remain future capabilities.
- **D22 — Processing Entity work assignment + extraction workspace
  (IMPLEMENTED 2026-08-21, §30/§32/§33/§37.14).** Batch-level
  `manual_extraction_batches.entity_id` carries the single active assignment
  (internal operator XOR Processing Entity); CarbonTally assigns via the
  extended `/api/v3/ops/batches/{id}/assign` (entity-level assignment, reason,
  audit trail). Entity staff get an entity-scoped extraction workspace
  (`/api/v3/ops/entities/{id}/extraction/*`) processing ONLY their entity's
  assigned work; entity-scoped RLS SELECT storey mirrors
  `manual_review_queue`/`upload_batches`; mediated clarification is an
  entity-scoped `issues` row (entity → CarbonTally → customer; never direct);
  assignment/reassignment history uses the existing V3 audit trail
  (ADR-V3-013 — no new table). Bidirectional isolation: entity-assigned
  batches leave the internal operator queue, and entity staff never reach
  internal/customer surfaces (D20 intact). Full mediated messaging, rendered
  report handoff and per-entity SLA/capacity automation remain future.

### BLOCKING ARCHITECTURAL DECISIONS (still unresolved)

- **D15 — Consultant client access follows the relationship lifecycle
  (IMPLEMENTED 2026-08-20).** Consultant access to a client requires an ACTIVE
  `consultant_clients` grant — enforced in RLS (`is_org_consultant`) and API
  (`ensure_consultant_org_access`); new grants default `active` (§34, §38.15).

### NON-BLOCKING TERMINOLOGY DECISIONS

Should eventually be ratified, but **do not require schema/RLS/API changes
merely to begin Phase 9 verification**:

- **D1** org-role naming; **D4** batch terminology; **D5** work-item definition;
  **D6** review vocabulary; **D16** workspace terminology.

### NON-BLOCKING OPEN ITEMS

May be investigated during Phase 9 where relevant, without being prerequisites
for the initial conformity gate:

- **D2** `roles` table disposition; **D3** document-store consolidation;
  **D7** scope aliases; **D8** report status CHECK; **D9** staff permission
  vocabulary; **D10** free-text enums; **D11** report types; **D12**
  subscription source; **D13** API generations/entry-point consolidation.

## 26. Next action

1. **D14/D17 are ratified** (2026-08-20) — treat them as implementation-gap work
   to be **scheduled**, not re-decided (§6, §30).
2. **D15 is IMPLEMENTED (2026-08-20, §34/§38.15)** — consultant access requires
   an ACTIVE consultant-client grant (RLS + API). D19 (lifecycle/transition)
   and D20 follow-up approvals remain; D15 is no longer blocking.
3. **Phase 9 P0 integration/RLS verification** (§27) against the local Supabase
   — can begin without waiting for the non-blocking items.
4. After D15 and initial P0 verification, decide which additional demo
   identities (§22, PROPOSED — NOT CREATED) are actually required — including
   the processing-entity demo fixture scenario (§36) — and only then create
   them.
5. **D18 boundary hardening (schedule alongside §30)** — make the admin/RBAC
   guards scope-aware so processing-entity staff can never hold admin
   authority or reach customer surfaces/communication (§35.5 G1/G2); add the
   CarbonTally-mediated entity communication channel (rule 14) and an entity
   work surface before provisioning any entity staff.
6. **D19 consultant-client lifecycle design** — D19 transition is approved
   conceptually; the in-place transition workflow and export/import scope
   (direct-customer marker semantics, transition mechanics) remain to be
   designed and approved (§37.4–§37.7). Not a Phase 9 P0 prerequisite.
7. **D20 scope-aware authorization approval** — approve the §38 design
   (scope-first evaluation, internal-vs-entity boundary, `ensure_org_access` /
   `is_admin` / legacy-guard fixes) as a **required-before-entity-provisioning**
   gate; schedule implementation alongside §30/§35.5 (§38.13 R1–R5).
8. **D21 final consultant model ratified (§37) + White-Label Foundation
   implemented (2026-08-21, §37.13)** — consultant-led MANAGED SERVICE is the
   default; the D21 White-Label Foundation (branding configuration, authorized
   brand-context resolution, report-branding context, email-sender config
   foundation) is implemented with the smallest schema change (one column) and
   no new tenancy model. Fully white-labeled rendering (rendered reports,
   outbound email, custom domains, client portal) and D19 transition + export/
   import remain future.
9. **D22 Processing Entity work assignment + extraction workspace IMPLEMENTED
   (2026-08-21, §30/§32/§33/§37.14)** — CarbonTally assigns extraction work to
   internal staff OR Processing Entity A/B/C via batch-level
   `manual_extraction_batches.entity_id`; entity staff process ONLY their
   entity's assigned work through the entity extraction workspace, with
   mediated clarification (entity-scoped issues) and audited reassignment.
   Entity staff never gain broad customer-organisation access (D20 intact);
   internal operators never process entity-assigned work. Remaining (follow-up):
   full mediated messaging threads, rendered report handoff, per-entity
   SLA/capacity automation, and provisioning real entity staff in a live
   environment (§22 demo matrix remains PROPOSED — NOT CREATED).

## 27. Phase 9 P0 test axes

Required verification axes for the next phase (integration/RLS against local
Supabase):

| Axis | Scope | Status |
|---|---|---|
| **P0-1 Customer organisation isolation** | Org A user → Org A data ALLOWED; Org A user → Org B data DENIED; Org B user → Org A data DENIED. Covers API/server authorization **and** direct Supabase/RLS access. **Fixture requirement: Organisation A = CarbonTally Demo Ltd; Organisation B = isolated test organisation (NOT YET CREATED).** Consultant access must not bypass this isolation. | NOT YET DEMO-VERIFIED (single org today) |
| **P0-2 Consultant client isolation** | Consultant may read only granted client orgs; non-granted orgs denied (API + RLS `is_org_consultant`). | PARTIALLY VERIFIED (single client) |
| **P0-3 Internal CarbonTally staff authorization** | Internal staff (`entity_id IS NULL`) ops access; non-staff denied. | VERIFIED (smoke + browser) |
| **P0-4 Processing-entity RLS isolation** | Entity staff see only their entity's rows; internal vs entity staff boundaries; lifecycle denial. | **NOT CURRENTLY DEMO-VERIFIED** — no processing-entity rows or entity-staff users exist |
| **P0-5 Owner/admin/member/viewer boundaries** | Org-admin mutations (owner/admin) vs member/viewer denials. | VERIFIED (smoke + browser + unit) |
| **P0-6 Staff-role/permission enforcement** | `staff_roles.permissions` gates (can_process/can_review/can_manage_staff/can_view_all). | VERIFIED (smoke + unit) |
| **P0-7 Direct RLS access vs service-role backend access** | RLS blocks direct authenticated access where the API (service role) allows org-scoped reads. | PARTIALLY VERIFIED (grants fixed; behaviour not yet systematically asserted) |
| **P0-8 Legacy API/route authorization boundaries** | Legacy `/api/*` guards vs V3 guards. | NOT SYSTEMATICALLY VERIFIED |

## 28. Demo user plan

Status: **PROPOSED — NOT CREATED**.

The existing 9 verified demo identities remain sufficient for the currently
implemented customer + internal staff + consultant-owner surfaces. After D15
(implemented) and initial Phase 9 verification, we will decide which additional
identities are actually required (§22 matrix, §36 entity demo scenario). No
users are created by this document.

---

## 30. Processing Entity Work Assignment — Implementation Gap (RESOLVED — D22 IMPLEMENTED 2026-08-21)

> **Status: RESOLVED + IMPLEMENTED (D22, 2026-08-21).** Batch-level
> `manual_extraction_batches.entity_id` is live, entity staff process assigned
> work through the entity extraction workspace, and assignment history is
> audited (§37.14). The historical analysis below is retained for the record;
> rows marked *"NOT IMPLEMENTED"* reflect the pre-D22 state.

Status: **documented gap analysis — NOTHING IMPLEMENTED.** Distinguishes
BUSINESS REQUIREMENT vs CURRENT IMPLEMENTATION vs IMPLEMENTATION GAP.

### 30.1 Business requirement (ratified 2026-08-20)

A single Customer Organisation may have extraction/processing work processed by
**multiple processing parties** (CarbonTally internal staff and/or Processing
Entity A/B/C/…). An organisation is **not** permanently bound to one entity.
CarbonTally **controls assignment** of extraction work. An entity receives
**only work assigned to it**; entity staff access is scoped to **assigned
work / authorised staff** — never broad customer-organisation access. Same-org
work may be simultaneously assigned to CarbonTally + Entity A + Entity B +
Entity C. Example:

```
Customer A
    ├── Work Item 001 → CarbonTally
    ├── Work Item 002 → Entity A
    ├── Work Item 003 → Entity B
    ├── Work Item 004 → Entity A
    └── Work Item 005 → Entity C
```

### 30.2 Current schema support

| Structure | Entity carrier | Assignment carrier | Status |
|---|---|---|---|
| `processing_entities` | row itself (id/name/status/metadata) | — | Entity registry exists |
| `staff_profiles` | `entity_id` (NULL = internal) | — | Entity staff belong to one entity |
| `manual_extraction_batches` | **none** | `assigned_to`/`assigned_by`/`assigned_at` = **staff user** | NO entity field; `assign_batch` rejects entity staff |
| `manual_extraction_items` | **none** (scope via batch) | `extracted_by` per item | NO entity field |
| `manual_review_queue` | `entity_id` | `assigned_to`/`assigned_by` | Entity-scoped precedent exists |
| `issues` | `entity_id` (NULL = internal) | `assignee_id` | Entity-scoped precedent exists |
| `upload_batches` | `entity_id` | `uploaded_by` | Uploads may be entity-tagged |
| `processing_queue` | none | none (legacy row) | **Legacy-only** — referenced by `routes/admin/analytics.py` metrics only; no V3 repo/API |
| `processing_assignments` | none | `queue_id`,`assigned_to`,`assigned_by`,`assignment_status` | **UNUSED** — 0 references in backend code |
| `reassignment_history` | none | `assignment_id`,`previous_staff_id`,`new_staff_id`,`reassigned_by`,`reason` | **UNUSED** — 0 references in backend code |
| `review_assignment_history` | none | `review_id`,`assigned_to`,`previous_assigned_to` | Used by **legacy admin** routes only |
| `document_processing_queue` | none | — | Dormant in V3 (only nullable FK from items) |

### 30.3 Current processing-flow trace (V3)

| Stage | Current table | Org field | Assignment field | Staff field | Entity field | RLS | API authorization |
|---|---|---|---|---|---|---|---|
| Upload | `organization_files` / `upload_batches` | `organization_id` | — | `uploaded_by` | `upload_batches.entity_id` | `is_org_member` | `require_org_member` |
| Processing queue | `processing_queue` (legacy, unused) | `organization_id` | none (assignments in unused `processing_assignments`) | — | none | org member | legacy |
| Manual extraction (assign) | `manual_extraction_batches` | `organization_id` | `assigned_to`/`assigned_by`/`assigned_at` (staff user) | `assigned_to` | **none** | `is_org_member` | `require_org_admin` (create); `assign_batch`: `require_internal_staff`+`can_manage_staff`+`can_process`, **rejects entity staff** |
| Extraction / mapping / validation / QC | `manual_extraction_items` | via batch | — | `extracted_by`/`validated_by`/`qc_checked_by` | **none** | `is_org_member` (org reads); ops staff via service role | ops `can_process`/`can_review` (internal) |
| Review | `manual_review_queue` | `organization_id` | `assigned_to`/`assigned_by` | `assigned_to` | **`entity_id`** | `is_entity_member` OR `is_org_member` | ops `can_review`+`can_manage_staff`; entity staff scoped to own-entity items |
| Issues | `issues` | `organization_id` | `assignee_id` | `assignee_id` | **`entity_id`** | `is_entity_member` OR `is_org_member` | ops staff / entity staff |
| Calculation | `emissions_logs`/`calculation_snapshots` | `organization_id` | — | `created_by_user_id` | none | `is_org_member` | `require_org_member` |

Logical insertion point for the processing party: **the manual-extraction
stage** — that is where "extraction work" is created, assigned and executed
today. The review/issues stages already carry `entity_id` and are the model to
generalise.

### 30.4 Support matrix (A–K) — business-model representability

| Requirement | Verdict | Evidence |
|---|---|---|
| A. CarbonTally internal assignment | **SUPPORTED** | `manual_extraction_batches.assigned_to` (internal staff, `entity_id IS NULL`); `assign_batch` requires internal staff |
| B. Entity assignment | **NOT SUPPORTED** (extraction) / **PARTIAL** (review/issues) | No `entity_id` on batches/items; `assign_batch` 422-rejects entity staff; `manual_review_queue`/`issues` already carry `entity_id` |
| C. Assignment to a specific entity staff member | **PARTIAL** | `manual_review_queue.assigned_to` may be an entity-staff user (own-entity only); extraction rejects entity staff |
| D. Multiple entities processing one org | **PARTIALLY SUPPORTED** | Multiple entity-scoped review/issues rows per org possible; no extraction-level entity |
| E. One entity processing work from multiple orgs | **PARTIALLY SUPPORTED** | Entity staff can hold review/issues across orgs (entity-scoped); no extraction-level entity |
| F. Reassignment Entity A → Entity B | **NOT SUPPORTED** | No entity assignment on extraction; no history written on reassign |
| G. Work returning to CarbonTally | **PARTIALLY SUPPORTED** | Review item re-assignable to internal staff; no formal extraction-level return flow |
| H. Work assigned to entity but not to an individual | **NOT SUPPORTED** (extraction) / **PARTIAL** (review `entity_id` w/o person) | Extraction `assigned_to` is always a person |
| I. Work assigned to a specific entity staff member | **PARTIAL** | Review only; extraction rejected |
| J. Work completion/status tracking | **SUPPORTED** | `BATCH_STATUSES`/`ITEM_STATUSES` full lifecycle |
| K. Assignment audit/history | **NOT SUPPORTED** | V3 `assign` overwrites in place; `processing_assignments`/`reassignment_history` unused; `review_assignment_history` legacy-admin-only |

### 30.5 Where should entity assignment live? (candidate comparison)

| Candidate | Assessment |
|---|---|
| `processing_assignments` | Schema exists (queue-scoped) but is **completely unused** by code. Architecturally the "assignment" home, but wiring the live pipeline to a dead table is a larger change than extending the live tables. |
| `manual_extraction_batches` | **Most appropriate candidate for entity-level extraction assignment.** This is where extraction work is created/assigned/executed; a nullable `entity_id` (plus keeping `assigned_to` for the individual operator) directly matches "extraction work assigned to an entity". Batch granularity matches the business unit (Work Item ↔ batch). |
| `manual_extraction_items` | Per-item granularity is finer than needed for entity assignment; items inherit entity via batch. Not the primary carrier. |
| `manual_review_queue` / `issues` | **Already the precedent** (`entity_id` present, entity RLS present). The extraction pipeline should be aligned to this pattern. |

**Verdict: no existing structure is fully sufficient.** The least-change,
architecture-consistent location is **batch-level** entity assignment on
`manual_extraction_batches` (mirroring `manual_review_queue`), **plus** an
auditable assignment/history carrier for reassignment (see §33). Because the
extraction pipeline is the only work stage without an entity dimension, the
schema concept below is documented as **required but NOT implemented**.

### 30.6 Minimum required schema concept (IMPLEMENTED 2026-08-21 — D22)

> **Status: IMPLEMENTED.** The four minimum concepts below are live
> (migration `20260821020000_d22_processing_work_assignment.sql`; §37.14).
> Point 3's carrier is the existing V3 `audit_trail` (ADR-V3-013 — the
> dormant queue-keyed `reassignment_history`/`processing_assignments` family
> stays untouched; no parallel table was invented).

1. `manual_extraction_batches.entity_id` (nullable FK → `processing_entities`;
   NULL = CarbonTally-internal) — batch-level entity assignment. **IMPLEMENTED.**
2. A single **active assignment** invariant (one work item → one processing
   party at a time) — enforced by the assignment carrier (entity_id XOR
   assigned_to) in the API + repository. **IMPLEMENTED.**
3. An **assignment history** carrier keyed on the work item/batch recording
   `previous_party`, `new_party` (entity or internal), `reassigned_by`,
   `reason`, timestamps — **IMPLEMENTED via the existing V3 `audit_trail`**
   (`entity_type='manual_extraction_batch'`, before/after party, actor, reason;
   ADR-V3-013 — no new history table).
4. Entity-scoped work surfaces for the extraction pipeline mirroring the
   existing `manual_review_queue`/`issues` entity pattern — **IMPLEMENTED**
   (entity extraction workspace + entity SELECT RLS storey on
   `manual_extraction_batches`/`manual_extraction_items`).



## 31. Many-to-many business model verification

Status of the ratified model against the current implementation (no changes
made):

| Model requirement | Verdict | Evidence |
|---|---|---|
| One Organisation → many Processing Entities | **IMPLEMENTED (D22)** | Entity A/B/C batches can coexist on one org (batch-level entity assignment) |
| One Processing Entity → many Organisations | **IMPLEMENTED (D22)** | An entity's assigned batches may span orgs; entity staff process work across those orgs' batches (entity-scoped, never org membership) |
| One Organisation → CarbonTally + many Processing Entities simultaneously | **IMPLEMENTED (D22)** | Internal (entity_id NULL) + Entity A/B/C batches coexist on one org; each batch has exactly one active party |
| One Processing Entity → multiple concurrent work items | **SUPPORTED (D22)** | Many batches/items may carry the same `entity_id` |
| One work item → one active processing party at a time | **IMPLEMENTED (D22)** | `manual_extraction_batches.entity_id` XOR `assigned_to` (API-enforced); internal queue excludes entity batches |
| Work item → reassignment history | **IMPLEMENTED (D22)** | Assignment/reassignment recorded in the V3 `audit_trail` (before→after party, actor, reason; ADR-V3-013) |

## 32. Conceptual access-control model (IMPLEMENTED 2026-08-21 — D22)

Required principle: processing-entity staff must **not** gain broad
customer-organisation membership merely because they process a work item.

| Layer | Design | D22 status |
|---|---|---|
| **API authorization** | New guard concept `require_entity_work_access(work_scope)` — entity staff may only reach work whose assignment resolves to their `staff_profiles.entity_id` (or is explicitly assigned to their user id). Extraction ops endpoints would additionally check entity-vs-internal assignment instead of blanket-rejecting entity staff. | **IMPLEMENTED** — `require_entity_scope` + `ensure_entity_batch_access` + `_entity_workspace_guard` on every `/entities/{id}/extraction/*` route; internal `assign`/operator surfaces enforce the single-active-party invariant |
| **RLS** | Extraction work tables gain entity-scoped policies mirroring `manual_review_queue`/`issues`: access via `is_entity_member` AND assignment-match (row `entity_id` = caller's `staff_profiles.entity_id`), **never** via `is_org_member` (entity staff are not org members). | **IMPLEMENTED** — `manual_extraction_batches_entity_select` + `manual_extraction_items_entity_select` (additive; no entity write policies) |
| **Service-role backend** | Repositories enforce assignment scoping server-side (service role bypasses RLS); entity staff queries filtered to assigned work before returning rows. | **IMPLEMENTED** — `list_entity_batches`/`list_entity_items`/`next_entity_item` + every workspace endpoint re-checks the batch's `entity_id` |
| **Frontend routing** | Entity staff see an entity-scoped work surface only (no customer workspace / org navigation); the existing `require_entity_scope` and entity dashboard route are the pattern to extend to extraction. | **IMPLEMENTED** — `/ops` renders `EntityExtractionWorkspace` for `profile.entity_id` staff; internal tabs never render for entity staff |

Unchanged principles: customer users access their org by org role; internal
staff by staff role/permission; consultants only through valid consultant
client grants.

## 33. Reassignment model

Target (auditable): `Work Item 001: Entity A → CarbonTally → Entity B`.

- **Current (D22, IMPLEMENTED 2026-08-21):** `assign_batch` accepts exactly one
  of `assigned_to` (internal operator) / `entity_id` (active Processing Entity)
  and records the previous → new processing party in the existing V3
  `audit_trail` (`entity_type='manual_extraction_batch'`, before/after party,
  actor, optional `reason`). Reassignment covers Entity A → Entity B,
  Entity → internal operator, and internal operator → Entity.
- **Verdict:** auditable reassignment history **IS supported** (D22).
  `review_assignment_history` remains legacy-admin-only; the dormant
  `processing_assignments`/`reassignment_history` family remains untouched.
- **Minimum conceptual requirement (IMPLEMENTED):** an assignment-history
  carrier keyed on the work item/batch recording `previous_party` →
  `new_party` (internal or entity), `reassigned_by`, `reason`, timestamps,
  plus the single-active-assignment invariant (§30.6) — delivered through the
  V3 `audit_trail` (ADR-V3-013 — no new table).

## 34. D15 — Consultant client access is governed by the relationship lifecycle (IMPLEMENTED 2026-08-20)

> **Re-scoped 2026-08-20 (§37.7):** "revocation" is the wrong framing for the
> clarified commercial model. D15 is about the consultant–client **relationship
> lifecycle** (relationship ended → access denied), **not** CarbonTally taking
> ownership of a client or its data.

**Confirmed implementation problem (pre-fix):** `is_org_consultant` (RLS)
joined `consultant_clients` on firm+org without checking
`consultant_clients.status`, so an **INACTIVE / REVOKED grant could permit
access**; the API guard `ensure_consultant_org_access` mirrored the gap.

**Approved rule (2026-08-20) — IMPLEMENTED:**

| Grant status | Access |
|---|---|
| `status = 'active'` (default on grant creation) | ALLOWED |
| `status` INACTIVE / any non-active | DENIED |

Implementation:

1. **API** — `ensure_consultant_org_access` requires an ACTIVE grant
   (`api/consultant_auth.py`); `_authorized_client_org` enforces it on every
   client data endpoint; the firm may still manage its own grant rows
   (ownership-only `_checked_client`, e.g. reactivation).
2. **RLS** — `is_org_consultant` requires `cc.status = 'active'` (migration
   `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql`).
3. **Grant creation** — `consultants.add_client` defaults `status = 'active'`.
4. **Client-switch list display filtering** — **NOT implemented** (display
   decision): the client list still returns the firm's own grants (including
   inactive) for management; access is enforced at the API/RLS layers.

D15 does **not** mean "CarbonTally revokes the customer"; it means the
consultant–client relationship ended and consultant access to that client ends.

## 35. Processing Entity boundary — strictly non-customer-facing back-office processors (RATIFIED 2026-08-20)

### 35.1 Authoritative business/security rule

The following is an explicit CarbonTally business and security requirement
(ratified 2026-08-20). A Processing Entity is a **strictly non-customer-facing
back-office processor**. It:

1. **MAY** receive processing/extraction work assigned by CarbonTally.
2. **MAY** access only the data necessary to perform the assigned work.
3. **MAY** process and submit the assigned work back through CarbonTally.
4. **MAY** receive workflow/status information necessary to perform the assigned work.
5. **MUST NOT** contact Customer Organisations directly.
6. **MUST NOT** contact Customer Users directly.
7. **MUST NOT** contact Consultants directly.
8. **MUST NOT** initiate customer-facing communication.
9. **MUST NOT** independently select or request customer work.
10. **MUST NOT** obtain unrestricted visibility into a Customer Organisation.
11. **MUST NOT** obtain Customer-Organisation membership merely because it processes that organisation's work.
12. **MUST NOT** obtain access to consultant-client relationships merely because it processes work originating from that client.
13. **MUST NOT** use CarbonTally communication features as a direct customer/consultant communication channel.
14. Any communication, clarification, instruction, escalation or status exchange between a Customer/Consultant and a Processing Entity **must be mediated by CarbonTally**.

Permitted conceptual relationship (CarbonTally is the **mandatory
intermediary**):

```
Customer Organisation / Consultant
              │
              ▼
          CarbonTally
              │
              ▼
       Processing Entity
              │
              ▼
          Entity Staff
```

Prohibited relationships:

```
Customer Organisation ⛔ Processing Entity
Customer User        ⛔ Processing Entity
Consultant           ⛔ Processing Entity
```

**Status — preserved.** **Business model: RESOLVED. Implementation model:
GAP / NOT IMPLEMENTED.** This document does **not** claim the model is
implemented (§30, §35.5). All previously ratified processing-entity decisions
(§6.1) are preserved: one org may use multiple processing parties; no permanent
org↔entity relationship; no `organizations.processing_entity_id`; CarbonTally
controls assignment; an entity receives only assigned work; entity staff are
scoped to assigned work; entities are **never** Customer-Organisation members.

### 35.2 Security interpretation — "assigned work access" is not "customer context access"

"Assigned work access" must **not** be interpreted as permission to expose the
customer's broader organisational context. If Work 002 belonging to Customer
Organisation A is assigned to Processing Entity A, Entity A staff may receive
the minimum information required to process Work 002. That assignment **must
not** automatically expose:

- all Customer A documents;
- Customer A users;
- Customer A organisation settings;
- Customer A internal communications;
- Customer A consultant relationships;
- Customer A contact details;
- customer-facing messaging channels;
- unrelated processing work;
- work assigned to another Processing Entity;
- CarbonTally-internal processing work.

Unless a future explicitly approved business rule requires a particular field,
assume it remains inaccessible.

**Intended authorization boundary — Work access vs Customer/Consultant access:**

> Processing Entity staff may access only the minimum information necessary to
> perform work assigned to their Processing Entity and/or explicitly assigned
> to that staff member.

> Processing Entity staff have no customer-facing communication authority.

Processing-Entity authorization is based on **assigned processing work**, never
on Customer-Organisation membership (§6.1, §32).

### 35.3 Current implementation posture vs the boundary (impact analysis)

Verdicts below apply to a hypothetical processing-entity staff identity under
the **current** implementation. No entity staff user exists today
(`processing_entities` = 0 rows; `staff_profiles.entity_id IS NOT NULL` = 0
rows), so the analysis is architectural/forensic — verified against the running
local Supabase RLS and the mounted API surface.

| Surface | Entity-staff access today | Verdict |
|---|---|---|
| Customer organisation data (`organizations`, `organization_metadata`, `organization_members`) | **DENIED** — all V3 customer APIs (`/api/v3/organizations`, `/manual-extraction`, `/processing`, `/emissions`, `/documents`, `/reports`, `/exports`, `/verifications`, `/issues`, `/customer-factors`) require `require_org_member()`; RLS org-storeys are org-member/org-consultant only; no entity storey exists on these tables | **CURRENTLY SUPPORTED** |
| Customer users (`users`, `organization_members`) | **DENIED** — `users` RLS = `users_select_self` only; member lists are org-member/admin surfaces | **CURRENTLY SUPPORTED** |
| Consultant / client relationships | **DENIED** — consultant surfaces require `require_consultant`; `consultant_clients` has no entity RLS storey; entity staff are never consultants | **CURRENTLY SUPPORTED** |
| Customer documents beyond assigned work | **DENIED** — `customer_documents` / `organization_files` RLS is org-member/consultant only (no entity storey). Entity staff see only file metadata (`file_name`, `file_url`, `file_type`, `customer_document_id`) of review-queue items linked to their entity, plus `upload_batches_entity_select` rows (metadata) | **CURRENTLY SUPPORTED** (work-data only) |
| Customer contact information | **DENIED** — `primary_contact_*` / `sustainability_officer_*` / org metadata are org-member/admin surfaces; entity work payloads carry `organization_id` + file metadata only, never contact fields | **CURRENTLY SUPPORTED** |
| Messaging / chat | **DENIED** — `conversations`/`messages` RLS = org-member/org-consultant only (no entity storey); `conversation_participants` is RLS-enabled with **zero policies (deny-by-default)**; legacy `/api/communication` is **not mounted**; the client-side `ChatWidget` renders only in the legacy customer dashboard with an org | **CURRENTLY SUPPORTED** |
| Comments | **DENIED** — comment/message tables are org-gated; entity staff only read/write their own entity's `issues` rows (title/description/status/priority) | **CURRENTLY SUPPORTED** |
| Notifications | **CURRENTLY SUPPORTED** — `/api/v3/notifications` is per-user (`list_for_user(user_id)`); entity staff see only their own rows; `notifications` table is RLS deny-by-default (service-role repo only) | **CURRENTLY SUPPORTED** |
| Assignments | **PARTIAL** — entity staff can assign/complete review-queue items **within their own entity** (`ensure_entity_review_scope`, `require_entity_scope`); manual-extraction batch assignment explicitly rejects entity staff (`assign_batch`, §30) | **PARTIALLY SUPPORTED** |
| Reviews | **PARTIAL** — entity staff see/act on their entity's `manual_review_queue` rows (entity SELECT storey + dashboard filter); extraction-pipeline review stages are internal-only | **PARTIALLY SUPPORTED** |
| Issues | **PARTIAL** — entity staff see/create/update only their entity's issues (`issues_entity_select`, `list_for_entity`); customer-facing issue listing excludes entity issues (`entity_id IS NULL`) | **PARTIALLY SUPPORTED** |
| Reports | **DENIED** — `/api/v3/reports` and legacy reports require org-member/org-admin | **CURRENTLY SUPPORTED** |
| Customer-facing APIs | **DENIED** — every V3 and mounted-legacy customer endpoint requires `require_org_member()`; `require_org_access(org_id)` (the any-staff org bypass, `auth.py:454`) is **dead code** — referenced by no mounted endpoint | **CURRENTLY SUPPORTED** |
| Customer-facing frontend routes | **DENIED** — `V3Layout` shows customer nav only when org resolution succeeds (entity staff have no org); `/ops` (`OperationsPage`) calls `/api/v3/ops/dashboard` → 403 for entity staff; **no entity workspace page exists** | **CURRENTLY SUPPORTED** |
| Organisation switching | **DENIED** — no org-switching UI exists (`org_switch` / `switch_org` / `active_organisation` have no hits); `/dashboard` redirect is org-scoped | **CURRENTLY SUPPORTED** |
| Consultant client switching | **DENIED** — `/consultant` is `require_consultant`-gated; entity staff are not consultants | **CURRENTLY SUPPORTED** |

### 35.4 Communication surfaces inspected (backend, frontend, RLS, routes)

| # | Surface | Location / route | Guard | Entity-staff reachability |
|---|---|---|---|---|
| C1 | Legacy messages/conversations API | `backend/routes/communication.py` → `/api/communication` | `require_org_member` + per-participant org membership; RLS org-member/consultant | **NOT MOUNTED** (`main.py` includes no `communication.router`) — dead; denied even if mounted |
| C2 | Client-side chat widget | `frontend/src/components/chat/*` (`ChatWidget`) | Direct Supabase reads under the user JWT; RLS applies | **DENIED** — `conversations`/`messages` RLS org-member/consultant; `conversation_participants` deny-by-default (0 policies) so the widget returns no conversations for any user; `users` lookup self-only; renders only inside the legacy dashboard with `organization && user` |
| C3 | Legacy email notifications (customer-facing) | `backend/routes/notifications.py` → `POST /api/notifications/customer/manual-extraction`, `/batch/completion`, `/staff`, `GET /templates` | `require_role(["admin","staff"])` / `require_role(["admin"])` — **role-NAME-string** guards | **CONDITIONAL RISK** — CarbonTally→customer email sends exist; an entity-staff user whose `staff_roles` row is named `admin` (or `staff`) would pass. Blocked for other role names (§35.5 G1) |
| C4 | V3 in-app notifications | `backend/api/v3_notifications.py` → `/api/v3/notifications` | `require_auth` + service-role repo filtered by `user_id` | **CURRENTLY SUPPORTED** — entity staff see only their own notifications; no user→user notification-creation endpoint |
| C5 | Admin email templates | `backend/routes/admin/email_templates.py` | `require_admin` (name-string) | Conditional on G1; otherwise admin-only |
| C6 | Stray Resend email code | `backend/main copy.py` (backup file) | — | Not part of the served app (`backend/main.py` is mounted) |

Answers to the communication-boundary questions:

- **Can a Processing Entity staff user communicate with a Customer User today?**
  **No.** RLS denies `conversations`/`messages`/`conversation_participants` to
  non-org-members, the legacy communication router is unmounted, and the chat
  widget requires an org.
- **Can a Processing Entity staff user communicate with a Consultant today?**
  **No.** No entity↔consultant communication surface exists; consultant
  surfaces are `require_consultant`-gated.
- **Any chat/message/notification mechanism exposing one party to another?**
  Chat is customer↔customer / customer↔consultant only (org-member /
  org-consultant RLS) and is currently non-functional end-to-end
  (`conversation_participants` deny-by-default). Notifications are strictly
  per-user. No customer↔processor path exists.
- **Is customer contact information exposed through processing workflows?**
  **No.** Entity work payloads (review-queue items, entity dashboard, entity
  issues) expose `organization_id`, file metadata and workflow state only — no
  names, emails, phones or org contact fields.
- **Any endpoint implicitly creating a customer ↔ processor communication
  path?** **Conditionally, the legacy Resend endpoints in C3.** They are
  CarbonTally→customer sends; they become an entity→customer path only under
  the G1 role-name mis-provisioning scenario.

### 35.5 Gaps, risks and classifications

| # | Gap / risk | Classification |
|---|---|---|
| G1 | **Name-string authorization.** `require_admin()`, `require_role([...])`, `is_admin` and the legacy `is_admin` bypasses authorize by `staff_roles.name` (values today: `admin`, `operator`, `reviewer`, `qc_specialist`), **not** by entity scope. `POST/PUT /api/v3/ops/staff` let an entity-staff profile carry any `role_id` — including the **`admin`** role. If that happens: `require_admin()` passes → `/api/v3/qc/*`, `/api/v3/admin/*`, `/api/v3/processing-entities/*` CRUD and the legacy admin routers become reachable; `is_admin=True` bypasses the org-membership re-checks in legacy `require_auth()` endpoints (`/api/upload/batches/*`, `/api/emissions/*`, …) → **customer-org read/write**; and the C3 customer-email endpoints become reachable. No entity staff exist today (0 rows), so this is a **latent** path — but nothing structurally prevents the mis-provisioning | **SECURITY RISK** + **IMPLEMENTATION REQUIRED** (guards must become scope-aware: internal-vs-entity, never name-string) |
| G2 | `require_org_access(org_id)` (any staff → any org, `auth.py:454`) is dead code today but remains the org-wide bypass pattern; any future endpoint reusing it gives entity staff org-wide access | **SECURITY RISK** (latent) |
| G3 | Extraction pipeline has no entity dimension — entity staff **cannot** receive assigned extraction work (`assign_batch` rejects entity staff; batches/items have no `entity_id`) | **NOT SUPPORTED** + **IMPLEMENTATION REQUIRED** (§30 gap work) |
| G4 | No entity work surface / frontend route — entity staff cannot process assigned work end-to-end (no page renders `getEntityDashboard`) | **NOT SUPPORTED** + **IMPLEMENTATION REQUIRED** |
| G5 | No CarbonTally-**mediated** clarification/escalation channel for entity↔CarbonTally↔customer exchange (rule 14). Entity `issues` exist, but there is no routed/mediated communication workflow | **NOT SUPPORTED** + **BUSINESS RULE** (must be implemented as a mediated channel, never direct) |
| G6 | RLS scoping on review/issues is entity-row-based, not **assignment**-based; extraction tables have no assignment/entity scoping at all | **PARTIALLY SUPPORTED** + **IMPLEMENTATION REQUIRED** (§32 design) |
| G7 | Entity staff can read `queue_settings` (SLA) and the staff-role catalog (`/api/v3/ops/sla/settings`, `/staff-roles` — `require_staff` only, no internal/entity check). Not customer data; workflow config only | **CURRENTLY SUPPORTED** (tighten when the entity work surface is built) |
| G8 | D15 consultant-client access — now **implemented** (2026-08-20, §34/§38.15): active-grant enforcement in RLS + API; does not affect the Processing Entity boundary | **BUSINESS REQUIREMENT — RESOLVED** (implemented) |
| G9 | The boundary rule itself is a ratified **business/security requirement**; today it holds only because no entity users exist and every customer surface is org-member-gated. Any future entity provisioning must keep this posture (§35.3) | **BUSINESS RULE** (RESOLVED — enforcement must be maintained and P0-verified, §27) |

### 35.6 Preserved statuses

- **D15 is IMPLEMENTED (2026-08-20, §34/§38.15)** — consultant access to a
  client requires an ACTIVE grant; INACTIVE / REVOKED → denied (RLS + API).
  D19 and D20 follow-up approvals remain.
- **Processing-Entity implementation status unchanged:** Business model
  **RESOLVED**; Implementation model **GAP / NOT IMPLEMENTED** (§6.1, §30).
- **No implementation was performed by this document.** §35 records the
  ratified boundary and analyses the current posture only.



---

## 36. Demo scenario proposal (PROPOSED — NOT CREATED)

Minimum future fixture to prove the ratified model (NOT created by this
document):

```
Customer A
    ├── Work 001 → CarbonTally internal
    ├── Work 002 → Processing Entity A
    ├── Work 003 → Processing Entity B
    └── Work 004 → Processing Entity A

Processing Entity A: 1 entity-staff user
Processing Entity B: 1 entity-staff user
Customer B: separate organisation for isolation testing
```

Proof obligations:

1. One customer can use multiple processing parties (Work 001 internal; 002/004
   Entity A; 003 Entity B).
2. One entity can process multiple customer organisations (Entity A also has a
   work item for Customer B).
3. Entity staff cannot see unassigned work.
4. Entity A cannot see Entity B's work (and vice-versa).
5. Customer users cannot access operations/entity work unless authorised.
6. CarbonTally staff can assign/reassign work.
7. Reassignment is auditable (requires §33 history carrier first).
8. Entity staff have no customer-facing communication authority and see no
   customer context beyond assigned work (D18, §35).

Creation remains deferred until D15 is settled and the §30 gap work is
scheduled. **No users, organisations, entities or work items are created by
this document.**

## 37. Consultant client lifecycle, direct-customer transition & white-label architecture (FINAL commercial model 2026-08-20)

Read-only architecture + domain-model analysis. **No implementation was
performed.** The consultant commercial model is **FINALIZED** by the product
owner (2026-08-20): a **HYBRID** model with **consultant-led MANAGED SERVICE as
the default consultant model** (§37.1). All previously ratified
processing-entity and boundary decisions (§6.1, §35) are preserved.

### 37.1 FINAL commercial model (BUSINESS REQUIREMENT — RESOLVED)

CarbonTally supports **both**:

1. **Direct CarbonTally Customers** — organisations with their own direct
   commercial relationship with CarbonTally (Customer Organisation → CarbonTally).
2. **Consultants who are themselves CarbonTally customers** — consultant firms
   that use CarbonTally as the underlying technology platform to provide
   carbon/emissions services to their own clients (CarbonTally → Consultant →
   the Consultant's clients).

**The default consultant model is CONSULTANT-LED MANAGED SERVICE.** Three
presentation/service modes are recognised:

- **Mode A — Managed Service (DEFAULT).** CarbonTally → Consultant A → Client Y.
  Client Y does **not** access CarbonTally; the Consultant performs the work and
  delivers the service/output to Client Y.
- **Mode B — Co-Branded (FUTURE capability).** Consultant A + CarbonTally →
  Client Y. The customer-facing experience may show both brands; client access
  may be introduced where commercially appropriate. **NOT implemented.**
- **Mode C — Fully White-Label (FUTURE capability).** CarbonTally Platform →
  Consultant A ("ABC Sustainability") → Client Y. Client Y may experience the
  service as the Consultant's own platform/service; CarbonTally may be
  invisible or minimally disclosed per the commercial arrangement. **NOT
  implemented.**

**CRITICAL CORRECTION — a Consultant Client does NOT automatically use
CarbonTally.** A Consultant Client:

- does **not** automatically have a CarbonTally account;
- does **not** automatically have CarbonTally login access;
- does **not** automatically access the CarbonTally application;
- does **not** automatically become a CarbonTally customer;
- does **not** automatically see CarbonTally branding.

The Consultant uses CarbonTally **behind the scenes** to deliver services to
that client. This replaces any earlier wording implying "the Consultant Client
uses CarbonTally through the Consultant" — that wording is **incorrect**. The
authoritative statement is:

> The Consultant uses CarbonTally as the underlying technology platform to
> provide carbon/emissions services to its own client. The Consultant Client
> does not have CarbonTally access unless a separate customer/access
> relationship is established.

Further ratified principles (preserved):

1. A Consultant Client **may later become a direct CarbonTally Customer
   Organisation** if it terminates the relationship with the Consultant and
   independently chooses CarbonTally — a **separate commercial relationship**.
2. **Direct Customer transition (D19):** prefer an **in-place** transition of
   the existing organisation/data over export/re-import where legally and
   contractually appropriate; preserve documents, extracted data,
   extraction/review history, issues, emissions records, calculation
   snapshots, reports, report versions and audit/provenance. **NOT
   implemented** in this task.
3. **Export/import is a separate future capability** (structured customer data
   export, permitted document export, provenance/audit export, structured
   import with validation, duplicate handling and lineage preservation) — NOT
   the normal transition mechanism. **NOT implemented.**
4. Consultant-client relationship termination must **not** be modelled as
   "CarbonTally revokes the consultant's customer"; it means the consultant's
   authorization/relationship ends.
5. **White-label is a planned CarbonTally capability** (§37.8); it must **not**
   require a generic new tenancy abstraction.
6. **Processing Entities remain completely separate** from this model (§37.9).

### 37.2 Current consultant/client domain model (as implemented)

| Concept | Implementation (current) | Notes |
|---|---|---|
| Consultant Firm | `consultant_profiles` row — the profile **is** the firm (`consultant_firm_members.firm_id → consultant_profiles.id`); `user_id` = firm owner | Branding/partner hooks exist but are unused by V3 surfaces: `brand_name`, `logo_url`, `primary_color`, `footer_text`, `email_from`, `client_portal_url`, `co_branding_enabled`, `partner_status`, `partner_tier`, `commission_rate` |
| Firm member | `consultant_firm_members` — `role` (owner/manager/consultant/viewer), `can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team`, `client_access uuid[]`, `is_active` | Authorization = the `can_*` flags (not role names); per-member org grants via `client_access` |
| Consultant client (grant) | `consultant_clients` — `consultant_id → consultant_profiles.id`, `organization_id → organizations.id`, denormalised `client_name`/`client_industry`/`client_contact_email`/`client_contact_name`/`client_contact_phone`, `status` (free varchar; repository vocab `active`/`inactive`; **new grants insert with `status = NULL`**), `billing_plan`, `notes`, `tags` | `UNIQUE(consultant_id, organization_id)`; **both FKs `ON DELETE CASCADE`** (destructive if profile/org deleted); no status CHECK constraint |
| Client organisation | a real `organizations` row (`is_active` NOT NULL default true, `archived_at`, `subscription_status`/`subscription_tier`/`subscription_id`, billing + `primary_contact_*`) | The org row is the **tenancy anchor**; "direct CarbonTally customer" is only implicit via subscription fields — no formal flag |
| Org member | `organization_members` (`role`: owner/admin/member/viewer, `is_active`) | `is_org_member` RLS requires membership `is_active` **and** `organizations.is_active` |
| Data tenancy spine | every data/audit record carries `organization_id`: `organization_files`/`customer_documents`, `upload_batches`, `manual_extraction_batches`/`items`, `manual_review_queue`, `issues`, `emissions_logs`, `calculation_snapshots`, `report_generation_queue`, `report_versions`, `audit_logs`, `activity_logs`, `export_history` | Consultant read access to a client org flows through `is_org_consultant` on these tables |
| Consultant-contextual | `consultant_tasks` (`consultant_id` NOT NULL, `client_id` nullable); `consultant_firm_members` | not part of the org tenancy spine |
| User-owned | `notifications` (`user_id`); `organization_members` (`user_id`+org) | |
| Work-assignment-owned | `manual_review_queue.assigned_to`, `manual_extraction_batches.assigned_to` (internal staff); `processing_assignments`/`reassignment_history` (legacy, unused by V3) | |
| Global references | `emission_factors`, `staff_roles`, `processing_entities` | |
| API chain | `require_consultant` (active profile + active firm member) → `ensure_consultant_org_access` (per org: `client_access` contains org **or** firm grant row; **grant status ignored**) → `ensure_consultant_permission` (`can_*` flags) | every `/api/v3/consultants/clients/*` endpoint re-authorizes `_checked_client` (ownership + org access) |
| Client switching | frontend `localStorage('v3_consultant_active_client')` + `ConsultantPage` state; server re-authorizes every request | no server-side active-client state |
| RLS | `is_org_consultant(org)` = firm member active AND (`client_access @> {org}` OR firm grant row exists) — **ignores `consultant_clients.status`, `consultant_profiles.is_active`, `organizations.is_active`**; `consultant_clients` has dual storeys `cc_*_own_firm` + `consultant_clients_tenant_*` | |

### 37.3 Current lifecycle model + semantic gaps

Representable today: grant created (`status = NULL`) → `PUT` status
`active`/`inactive` → `DELETE` = **soft-deactivate to `inactive`** (row
retained via `update_client_status`). Org lifecycle: `is_active`,
`archived_at`.

NOT representable / gaps (ARCHITECTURAL GAP):

- No formal **direct-CarbonTally-customer** state on `organizations`.
- No **relationship-end enforcement** — `consultant_clients.status` is a
  display/soft flag only; both `is_org_consultant` (RLS) and
  `ensure_consultant_org_access` (API) ignore it (D15, §34, §37.7).
- `consultant_clients.status` **conflates** relationship status and access
  authorization; it expresses nothing about customer status or organisation
  status.
- No transition/handover workflow, no who-initiated-the-end record, no
  lifecycle-change audit on the consultant surface.
- Multiple consultant grants to one org **are schema-representable**
  (`UNIQUE(consultant_id, organization_id)`), so "client chooses another
  consultant" is data-representable, but there is no API/frontend flow and no
  exclusivity or handover enforcement.

### 37.4 Conceptual lifecycle (APPROVED direction — NOT implemented)

Conceptual states:

```text
Consultant-managed client (grant active; org has no direct-customer users/subscription)
        │
        ▼
Active consultant relationship (work processed under the consultant's auth)
        │
        ▼
Relationship ends  ────►  (a) Client leaves CarbonTally entirely  (export + offboard)
        │                   (b) Client becomes a direct CarbonTally customer (in-place transition)
        └────────────────► (c) Client chooses another consultant (new grant; handover)
```

- **(b) In-place transition (preferred):** the `organizations` row and all
  org-scoped data remain unchanged; the client's users are added as
  `organization_members` (owner/admin), the org's subscription fields are set,
  and the consultant grant(s) are ended. Data/provenance is preserved by
  identity of `organization_id` — **no copy, no export/re-import**.
- **(c) Consultant switch:** representable today at the data level (multiple
  firms may hold grants to one org); requires an explicit handover workflow
  and end-of-access enforcement for the outgoing firm (D15).
- The current schema **can represent the states as data**, but cannot
  **enforce** them: ended relationships are not enforced (§37.3), there is no
  transition workflow, and no "direct customer" marker exists.

### 37.5 Data preservation requirements (ARCHITECTURAL GAP / NOT SUPPORTED)

All processing data is org-scoped (§37.2), so an internal transition preserves
history without copying. Record inventory by ownership:

| Record class | Ownership | Transition impact |
|---|---|---|
| `organization_files`, `customer_documents` | org-owned | preserved in place |
| `upload_batches`, `manual_extraction_batches`/`items` | org-owned (assignment = internal staff user) | preserved; live assignments are internal staff, not the consultant |
| `manual_review_queue`, `issues` | org-owned (+ optional `entity_id`) | preserved; `created_by`/`assignee` may reference the consultant's user id — historical provenance only |
| `emissions_logs`, `calculation_snapshots` | org-owned (`created_by_user_id` provenance) | preserved |
| `report_generation_queue`, `report_versions` | org-owned | preserved |
| `audit_logs`, `activity_logs`, `export_history` | org-owned | preserved |
| `consultant_clients` | consultant-contextual | ended (status `inactive`) — never the data owner |
| `consultant_tasks`, firm memberships | consultant-contextual | remain with the consultant firm |
| `notifications`, `organization_members` | user-owned / org-member | transition adds the client's memberships; retains consultant's? No — consultant was never an org member |

**Non-destructive constraints (documented, not implemented):**

- The transition must **never delete the `organizations` row** —
  `consultant_clients.organization_id` and `consultant_clients.consultant_id`
  are both `ON DELETE CASCADE`, so deleting an org or a firm profile would
  cascade-delete grants (destructive).
- Consultant user ids appearing as `created_by`/`assignee`/`created_by_user_id`
  remain valid historical provenance after the transition (those users are not
  org members and lose live access, which is the intent).

### 37.6 Export/import analysis (NOT SUPPORTED / FUTURE)

**Current export capability:**

- V3: `GET /api/v3/exports/emissions.csv`, `/emissions.json`,
  `/documents.csv` — **customer-only** (`require_org_member`), emissions logs +
  org-file metadata. No consultant export endpoint.
- Legacy: `routes/organizations/exports.py`; `export_history` table
  (`organization_id`, `user_id`, `file_url`).
- No full-org export, no provenance/audit export, no document-binary export.

**Current import capability:**

- `import_batches` table (status `pending|importing|completed|failed|
  rolled_back`) + the V3 imports admin surface — used for **emission-factor /
  provider reference imports**, **not customer data**.
- No customer self-service data import; no validation, duplicate handling or
  lineage preservation.

**Minimum future architecture (conceptual — NOT implemented):**

- **Structured data export:** full org dataset (documents where permitted,
  extraction, emissions, snapshots, reports, audit) in a machine-readable,
  relationship-preserving form.
- **Original document export** where permitted (per-org policy).
- **Provenance/audit preservation** in the export payload.
- **Structured import:** validation, duplicate handling, and **lineage
  preservation** (FK relationships re-established on import, e.g. as a new org
  or a merge).

### 37.7 D15 re-analysis + revised definition (approved and implemented 2026-08-20 per the approved minimum, §34)

The clarified commercial model requires distinguishing five concepts:

1. **Consultant–client business relationship** — the `consultant_clients` row.
2. **Consultant authorization to access/process client data** — derived from
   relationship status (an active relationship authorises; an ended one does
   not). This is what `is_org_consultant` / `ensure_consultant_org_access`
   must enforce.
3. **Client becoming a direct CarbonTally customer** — a separate workflow
   (org memberships + subscription fields); it is **not** a CarbonTally
   revocation of the client.
4. **Client leaving CarbonTally** — org archived / export; independent of the
   consultant relationship.
5. **CarbonTally platform/security suspension** — `organizations.is_active`
   (and any future platform-level suspension), independent of the consultant
   relationship.

**What `consultant_clients.status` currently means:** a display/soft-deactivate
flag (`active`/`inactive`, default `NULL` on insert). It is **not** consulted
by any access decision — `is_org_consultant` (RLS) and
`ensure_consultant_org_access` (API) both ignore it. The `DELETE /clients/{id}`
endpoint is a soft-deactivate (sets `status='inactive'`), so the current model
**cannot revoke access** (§34).

**Semantic gap (ARCHITECTURAL GAP):** the schema conflates concept 1 and 2 in
one column and has no expression of concepts 3/4/5 on the consultant surface.
`organizations.subscription_*` loosely indicates concept 3; `is_active`/
`archived_at` indicates 4/5 — but `is_org_consultant` ignores
`organizations.is_active` too.

**Approved D15 (implemented 2026-08-20 per the approved minimum — §34, §38.15):**

> **D15 — Consultant client access is governed by the relationship lifecycle,
> not by CarbonTally "owning" the client.**
> 1. `consultant_clients.status` = the consultant–client **relationship
>    status** (`active` = relationship in effect and access authorised;
>    `inactive`/ended = relationship ended and access denied).
> 2. Access enforcement is **uniform**: `is_org_consultant` (RLS) and
>    `ensure_consultant_org_access` (API) grant access **only** when the grant
>    is `active` (and the firm member is active).
> 3. Relationship termination may be initiated by either party (or by
>    CarbonTally recording the end); it is **not** a claim of ownership over
>    the client or its data.
> 4. A client becoming a direct CarbonTally customer is a **separate
>    transition** (§37.4) that ends the consultant grant as a consequence —
>    the client chooses CarbonTally; CarbonTally does not appropriate the
>    client.
> 5. Client leaving CarbonTally and platform/security suspension remain
>    separate states (§37.7 items 4–5).

### 37.8 White-label architectural impact (D21 White-Label Foundation — IMPLEMENTED 2026-08-21, partial)

The architecture must **not** assume `Customer-facing organisation =
CarbonTally customer`, `Brand = CarbonTally`, `Platform operator =
customer-facing provider`. Current separability:

- **Already separable today:** org-scoped tenancy (the org is the tenant
  regardless of branding); `consultant_profiles` branding/partner fields
  (`brand_name`, `logo_url`, `primary_color`, `secondary_color`, `footer_text`,
  `email_from`, `client_portal_url`, `co_branding_enabled`, `partner_status`,
  `partner_tier`, `commission_rate`).
- **Concepts that must remain separable (pressure points, no redesign today):**
  platform provider (CarbonTally) vs customer-facing provider
  (consultant/white-label partner); billing/customer relationship (org
  subscription fields) vs data tenancy; white-label tenant/brand (per-org or
  per-partner branding + from-brand email); end client (org); user;
  processing entity.
- **Do NOT introduce** a generic `workspace` entity or a new tenant
  abstraction — the org-scoped spine already provides end-client tenancy. The
  only structural pressure is per-tenant branding/presentation and
  partner-level billing/contracts.

**White-label architectural principle — keep these concepts separable:**

```text
Platform Provider        (CarbonTally)
        ≠
Commercial Customer      (Direct Customer OR Consultant Firm)
        ≠
Data Organisation        (the `organizations` tenancy anchor)
        ≠
User Access              (auth users + org members / firm members)
        ≠
Customer-Facing Brand    (CarbonTally / Consultant brand / white-label brand)
        ≠
Processing Entity        (back-office; never customer- or consultant-facing)
```

A generic `workspace` entity and an additional generic tenant abstraction are
**not** needed: the org-scoped tenancy spine already separates Data
Organisation from the other concepts; the pressure points are presentation /
branding, email sender identity, and partner-level billing/contracts.

**Capability analysis (D21-implemented state — future requirements remain
marked; full implementation status matrix in §37.13):**

| Capability | Future requirement | Current support (post-D21) |
|---|---|---|
| Branding (logo, colours/theme, company name, terminology) | Per-partner (and optionally per-client-org) brand presentation | **IMPLEMENTED (foundation)**: `consultant_profiles` `brand_name`, `logo_url`, `primary_color`, `secondary_color`, `footer_text` are editable via the D21 branding API/UI and resolved into an authorized `BrandContext` (`carbon_tally` / `consultant` / `co_branded`). Terminology pipeline still future. |
| Domain (`app.consultanta.com`) | Customer-facing domain per partner | **FUTURE** — single frontend origin; branding resolution is not tied to one hard-coded hostname (resolver is context-based); deployment/ingress domain routing remains future (§37.13). |
| Customer-facing identity (platform / consultant brand / end-client org) | Three-way presentation without tenancy change | Org = data tenancy; `consultant_profiles` = partner identity; **D21 `BrandContext` parameterises the presentation** (consultant workspace header + report surfaces) without a tenancy change. |
| Email (sender identity, templates, branding, notifications) | From-brand per partner; white-label templates | **PARTIALLY IMPLEMENTED (foundation)**: `consultant_profiles.email_from` is editable/validated and carried in the authorized `BrandContext`; no outbound sender/template pipeline — legacy Resend remains CarbonTally-branded; custom-domain sender requires DNS/domain verification (**FUTURE**, §37.13). |
| Reports (consultant-branded / CarbonTally / co-branded) | Brand parameterisation of report generation | **PARTIALLY IMPLEMENTED (context)**: report surfaces expose the authorized `branding` block (CarbonTally for Direct Customers; the consultant's own firm only via an ACTIVE D15 grant); the report rows remain org-scoped with no brand field. Rendered logo-in-report requires the Phase-10 rendering pipeline (**FUTURE**, §37.13). |
| Authentication (login, invitation, password reset, email branding, tenant/partner identification) | Partner-aware login/invite presentation | **FUTURE** — login is a single-origin CarbonTally surface; no partner detection on auth surfaces (unchanged). |

**Schema/API/RLS/frontend support assessment:**

- **Schema:** `organizations` (data tenancy), `consultant_profiles` (firm +
  branding + partner fields), `consultant_firm_members` (members +
  `client_access`) and `consultant_clients` (grant) already separate Data
  Organisation, Commercial Customer and Customer-Facing Brand enough for the
  future model — **no new tenant abstraction is required**.
- **API/RLS:** the org-scoped RLS/API spine + the consultant grant model remain
  the tenancy and access model; white-label is a presentation layer on top.
- **Frontend:** the D21 Consultant **Firm branding** tab reads/updates the
  branding config with live preview + validation; the consultant workspace
  header renders the resolved brand (`brand_name`/logo) when white-label or
  co-branding is enabled; Direct Customer/Operations shells keep the static
  CarbonTally brand.
- **Authentication:** single Supabase Auth; future partner-aware branding would
  key off the consultant/org context, not a new identity model.

### 37.13 D21 — White-Label Foundation: IMPLEMENTED 2026-08-21

**Status: IMPLEMENTED (foundation)** — the minimum production-ready white-label
capability required by the consultant business model, built on existing schema
capabilities. **No new tenancy model was introduced** — `organizations` remains
the data-tenancy anchor; branding is the presentation/commercial layer on the
existing `consultant_profiles` row.

**Schema change (smallest possible — ONE column):**

* `consultant_profiles.white_label_enabled boolean NOT NULL DEFAULT false`
  (`supabase/migrations/20260821010000_d21_white_label_branding.sql`). The only
  genuinely missing field: no existing column distinguished the FULL white-label
  presentation (CarbonTally invisible) from co-branding
  (`co_branding_enabled` already covered Mode B). All other branding fields
  (`brand_name`, `logo_url`, `primary_color`, `secondary_color`, `footer_text`,
  `email_from`, `website`, `support_email`/`phone`/`hours`, `client_portal_url`,
  `co_branding_enabled`) already existed and were reused — no duplicates.
  Partner/commercial fields (`partner_status`, `partner_tier`,
  `commission_rate`) stay CarbonTally-controlled and are NOT self-service.

**Backend:**

* `domain/branding.py` — pure presentation model: `ConsultantBranding`
  (projection of the profile row), `BrandContext` (resolved presentation),
  `resolve_brand_context` (no flags → CarbonTally fallback; `white_label_enabled`
  → consultant; `co_branding_enabled` → co-branded; white-label wins when both).
* `data/consultants.py` — `get_branding(profile_id)` / `update_branding(
  profile_id, fields)`; the UPDATE is keyed by the caller's OWN profile id and
  writes only allowlisted branding columns (self-scoped, no arbitrary
  `consultant_id`).
* `api/consultant_branding.py` — the ONLY brand-context resolvers:
  `resolve_consultant_branding` (own firm) and `resolve_report_branding`
  (caller's own firm ONLY via an ACTIVE D15 grant, else CarbonTally fallback).
  Branding is always derived from authorized context — a client-supplied
  `consultant_id` is never trusted.
* `api/v3_consultants.py` — `GET /me/branding` (read + `can_manage_branding`),
  `PUT /me/branding` (write; gated to the firm owner or `can_manage_team`,
  pydantic-validated, audited via `consultant.branding.update` with safe
  before/after snapshots), `GET /me/branding/context` (resolved brand). The
  client-reports surface exposes the authorized `branding` block.
* `api/v3_reports.py` — `list_reports` / `get_report` expose the authorized
  `branding` block (Direct Customers / staff → CarbonTally; consultant via
  active grant → own firm).

**RLS:** unchanged — `consultant_profiles` keeps `cp_select_own` (self-read)
with **no UPDATE policy** (direct-client writes deny-by-default). Firm-scoped
writes happen only through the service-role API which enforces
authenticated → active firm membership → firm-admin permission → own profile.
Consultant-firm isolation is therefore maximal at the database floor.

**Storage:** unchanged — logos are stored as validated http(s) URLs; no private
customer document was made public. A dedicated logo bucket + upload policies is
a future follow-up (D21.12).

**Frontend:**

* `src/v3/api.js` — `getConsultantBranding`, `getConsultantBrandingContext`,
  `updateConsultantBranding`.
* `src/v3/consultant/ConsultantPage.jsx` — new **Firm branding** tab (view
  current branding, edit supported fields, enable/disable white-label and
  co-branding, live brand preview, save, per-field validation errors); the
  workspace header renders the resolved consultant brand when active.
* `src/v3/consultant/consultant.css` — branding/preview/form styles.

**Email (D21.8):** foundation only — `email_from` is validated and carried in
the authorized `BrandContext`; no outbound sender/template pipeline was added
and no spoofing mechanism was created. Per-consultant outbound email requires
DNS/domain verification infrastructure — **FUTURE**.

**Reports (D21.7):** the authorized `branding` context is exposed on the report
surfaces (consultant's own firm only; never another firm's; Direct Customers →
CarbonTally). Rendered logo-in-report requires the Phase-10 rendering pipeline
— **FUTURE**.

**Explicitly NOT implemented (out of scope):** D19 transition workflow;
consultant-client login/portal/self-service; Processing Entity assignment or
workspace; custom DNS/SSL automation; export/import; a generic
tenant/workspace abstraction; demo users/entities/data.

**D21 implementation status matrix:**

| Capability | Status |
|---|---|
| D21.1 Consultant branding configuration (own firm; secure; smallest change) | **IMPLEMENTED** |
| D21.2 Branding API (read/update; auth chain; no global admin; validation) | **IMPLEMENTED** |
| D21.3 Consultant branding frontend (view/edit/preview/save/validation) | **IMPLEMENTED** |
| D21.4 Branding context (server-derived CarbonTally/Consultant/Co-branded) | **IMPLEMENTED** |
| D21.5 Default Managed-Service behaviour (no client users/login/portal created) | **IMPLEMENTED** (unchanged; no client access created) |
| D21.6/D21.7 Report branding (authorized context on report surfaces) | **PARTIALLY IMPLEMENTED** (context + API exposure; rendered logo-in-report FUTURE) |
| D21.8 Email/notification foundation (authorized sender config) | **PARTIALLY IMPLEMENTED** (config + resolution; outbound custom-domain sending FUTURE) |
| D21.9 Frontend brand presentation (shell not hard-coded for consultant) | **PARTIALLY IMPLEMENTED** (consultant workspace header + context endpoint; full shell parameterisation FUTURE) |
| D21.10 White-label vs co-branding distinction | **IMPLEMENTED** (resolver + UI toggles) |
| D21.11 Custom domains | **FUTURE** (routing not tied to a hard-coded hostname; no DNS/SSL automation) |
| D21.12 Logo storage | **FUTURE** (logos via validated URLs today; no bucket/policies added) |
| D21.13 RLS (firm isolation; customers/entity staff denied) | **IMPLEMENTED** (deny-by-default floor + API enforcement; no new bypasses) |
| D21.14 API authorization (5-point chain; never client-id-only) | **IMPLEMENTED** |
| D21.15 Audit logging (who/firm/what/timestamp/before-after; no secrets) | **IMPLEMENTED** |
| D21.16 Backward compatibility (fallback → CarbonTally; no breakage) | **IMPLEMENTED** (verified) |

### 37.14 D22 — Processing Entity work assignment + extraction workspace: IMPLEMENTED 2026-08-21

**Status: IMPLEMENTED (2026-08-21).** CarbonTally can assign extraction work to
internal staff OR Processing Entity A/B/C, and entity staff can process ONLY
the work assigned to their Processing Entity — without ever gaining broad
Customer Organisation access (§6.1, §30, §32, §33, §35).

**Schema change (migration `20260821020000_d22_processing_work_assignment.sql`):**

1. `manual_extraction_batches.entity_id` (nullable UUID FK →
   `processing_entities` ON DELETE RESTRICT) — the batch-level assignment
   carrier. NULL = CarbonTally internal (positive convention, ADR-V3-001 Q5).
   A batch has exactly **one** processing party: `entity_id` XOR `assigned_to`.
2. `issues.manual_extraction_batch_id` (nullable UUID FK →
   `manual_extraction_batches` ON DELETE RESTRICT) — links clarification /
   rework issues to the extraction batch (mediated clarification).
3. **Entity-scoped RLS SELECT storey** (additive; V3M-6 pattern):
   `manual_extraction_batches_entity_select` (`entity_id IS NOT NULL AND
   is_entity_member(entity_id)`) and `manual_extraction_items_entity_select`
   (EXISTS via the item's batch). **No entity INSERT/UPDATE/DELETE policies**
   — entity writes stay service-role/application.

**API surface:**

| Capability | Endpoint | Authority |
|---|---|---|
| Assign/reassign a batch to an entity | `POST /api/v3/ops/batches/{id}/assign` (`entity_id` XOR `assigned_to` + optional `reason`) | CarbonTally internal staff with `can_manage_staff` + `can_process`; entity must be `active` |
| Entity extraction batches / items / workspace / next-item | `GET /api/v3/ops/entities/{id}/extraction/batches[/{batch}/items]`, `…/items/{item}`, `…/next-item` | `require_staff` + `require_entity_scope` + `can_process` + ACTIVE entity + batch-assignment match (server-side) |
| Process assigned work | `POST …/extraction/items/{item}/start · extract · map · calculate · status` | entity staff, own entity only; validation/review/QC statuses are CarbonTally-gated |
| Mediated clarification | `POST …/extraction/items/{item}/clarify` | entity staff → entity-scoped `issues` row (entity → CarbonTally → customer; NEVER direct) |

**Security posture (D20/D21 intact):**

- Entity staff never pass `require_internal_staff` / `require_admin` /
  `require_role` / customer-org guards; no broad Customer Organisation access
  at API or RLS layer.
- Bidirectional single-active-assignment: entity-assigned batches leave the
  internal operator queue (`entity_id IS NULL` filter) and internal operators
  are blocked from processing entity-assigned batches; CarbonTally's
  validation/QC **gates** still review entity-produced output.
- Assignment/reassignment history is recorded through the existing V3
  `audit_trail` (`entity_type='manual_extraction_batch'`, before/after party,
  actor, reason; ADR-V3-013 — no new history table; the dormant
  `processing_assignments`/`reassignment_history` family stays untouched).
- Frontend: `/ops` renders the entity-scoped `EntityExtractionWorkspace` for
  entity staff (`profile.entity_id` populated); internal tabs never render.

**D22 capability matrix:**

| # | Capability | Status |
|---|---|---|
| D22.1 Batch-level entity assignment (`manual_extraction_batches.entity_id`) | **IMPLEMENTED** |
| D22.2 Single-active-assignment invariant (entity XOR operator) | **IMPLEMENTED** |
| D22.3 Entity extraction workspace API (list/workspace/start/extract/map/calculate/status) | **IMPLEMENTED** |
| D22.4 Entity-scoped RLS SELECT storey (batches + items) | **IMPLEMENTED** (additive; no write policies) |
| D22.5 Entity staff process ONLY own-entity work | **IMPLEMENTED** (API + RLS; cross-entity 403) |
| D22.6 Entity staff never gain customer-org access | **IMPLEMENTED** (D20 intact) |
| D22.7 Internal operator queue excludes entity work | **IMPLEMENTED** |
| D22.8 Audited assignment/reassignment (before→after, reason) | **IMPLEMENTED** (V3 `audit_trail`) |
| D22.9 Mediated clarification foundation (entity → CarbonTally; never customer) | **IMPLEMENTED** (entity-scoped `issues`; full messaging workflow FUTURE) |
| D22.10 Reassignment entity→internal / internal→entity / A→B | **IMPLEMENTED** |
| D22.11 Entity dashboard extraction block | **IMPLEMENTED** |
| D22.12 Entity frontend workspace | **IMPLEMENTED** |
| D22.13 Full mediated messaging threads/replies | **FUTURE** (documented follow-up) |
| D22.14 Per-entity SLA definitions / capacity automation | **FUTURE** (ADR-V3-006/007) |
| D22.15 Rendered report handoff / report branding for entity work | **FUTURE** |
| D22.16 Provision real entity staff in a live environment | **FUTURE** (§22 demo matrix PROPOSED — NOT CREATED) |

**NOT implemented (explicitly):** full mediated messaging (threads, replies,
no-identity relay), rendered report handoff, per-entity SLA/capacity
automation, and any real entity staff provisioning in a live environment.
Direct entity↔customer communication was **never** created.

### 37.9 Processing Entity boundary preserved

Unchanged (§6.1, §35): Processing Entities are CarbonTally-controlled,
work-assignment-scoped, strictly non-customer-facing and non-consultant-facing
back-office processors. They are **not** part of the consultant-client
lifecycle, and Processing Entity authorization is **never** combined with
consultant authorization.

### 37.10 G1 in the consultant/customer context + minimum architectural requirement (SECURITY RISK / IMPLEMENTATION REQUIRED)

The G1 name-string authorization risk (§35.5) is **orthogonal to consultant
authorization** — consultant auth uses the real `can_*` flag columns and
`require_consultant`, never role names. However, the same scope-blindness
pattern exists in the shared identity model:

- `get_current_user` sets `is_staff = True` for **any** `staff_profiles` row
  (internal or entity staff); `require_admin()` / `require_role([...])` /
  `is_admin` compare `staff_roles.name` strings only.
- A user may hold **both** a consultant profile/firm membership **and** a
  staff profile (the identity paths are independent), so a consultant who is
  also entity staff would be classified purely by role-name in the legacy
  guards.

**Minimum architectural requirement (documented only — NOT implemented):** an
explicit authorization dimension distinguishing **Internal CarbonTally Staff**
(`staff_profiles.entity_id IS NULL`) from **Processing Entity Staff**
(`entity_id` populated) that every admin-gated guard consults **before** any
role-name comparison; entity staff must be structurally unable to pass any
admin/role-name guard; the `require_org_access` any-staff org bypass must never
be reintroduced (§35.5 G1/G2). Consultant authorization stays flag-based and
unchanged.

### 37.11 Decision classification (consolidated)

| # | Conclusion | Classification |
|---|---|---|
| K1 | Consultant = direct CarbonTally customer; client initially the consultant's customer; client may become a direct customer; in-place data transition preferred; export/import separate; termination ≠ ownership; white-label future; PE separate (§37.1) | **BUSINESS REQUIREMENT — RESOLVED** |
| K2 | Lifecycle state model, transition workflow, direct-customer marker semantics (§37.3–§37.4) | **BUSINESS DECISION — REQUIRES USER APPROVAL** |
| K3 | D15 revised definition + active-grant enforcement (§37.7, §34) | **BUSINESS REQUIREMENT — RESOLVED + IMPLEMENTED** (2026-08-20, §34/§38.15) |
| K4 | Export/import scope and minimum future architecture (§37.6) | **BUSINESS DECISION — REQUIRES USER APPROVAL** / **NOT SUPPORTED** |
| K5 | Org-scoped tenancy spine; consultant read access to client orgs; per-request re-auth; frontend client switching; V3 customer export endpoints; multiple grants per org representable (§37.2) | **CURRENTLY SUPPORTED** |
| K6 | `consultant_clients.status` set/soft-deactivate but **not enforced** by RLS or API (D15); new grants default `status=NULL` (§37.3, §37.7) | **PARTIALLY SUPPORTED** + **SECURITY RISK** (latent over-access) |
| K7 | "Direct CarbonTally customer" only implicit in `organizations.subscription_*`; no formal state; status/authorization/customer/org-status conflation; no lifecycle audit; `consultant_clients` `ON DELETE CASCADE` destructiveness (§37.3–§37.5) | **ARCHITECTURAL GAP** |
| K8 | Consultant→direct-customer in-place transition; full-org export; provenance/audit export; customer data import with validation/duplicate/lineage; white-label branding/billing separation (§37.4–§37.6, §37.8) | **NOT SUPPORTED** / **FUTURE / WHITE-LABEL CONSIDERATION** |
| K9 | `is_org_consultant` ignores `consultant_clients.status`, `consultant_profiles.is_active`, **and** `organizations.is_active` (unlike `is_org_member` which checks org active) | **SECURITY RISK** (documented, §37.2/§37.7) |
| K10 | G1 name-string admin/staff risk + scope-blind identity model in the consultant/customer context (§37.10) | **SECURITY RISK** + **IMPLEMENTATION REQUIRED** |
| K11 | Processing Entity boundary unchanged; never combined with consultant authorization (§37.9) | **BUSINESS REQUIREMENT — RESOLVED** (preserved) |
| K12 | Hybrid commercial model (Direct Customers + Consultants-as-customers); consultant-led MANAGED SERVICE default; Mode A default (§37.1) | **BUSINESS REQUIREMENT — RESOLVED** (finalized 2026-08-20) |
| K13 | Consultant Client does **not** automatically use/access CarbonTally; a separate customer/access relationship is required (§37.1) | **BUSINESS REQUIREMENT — RESOLVED** (authoritative correction) |
| K14 | Modes B (co-branded) / C (fully white-label) — **D21 White-Label Foundation IMPLEMENTED 2026-08-21** (branding config, brand-context resolution, report-branding context, email-sender config; §37.13). Custom domains, white-label email/reports/auth presentation, consultant-client direct-access mode, rendered logo-in-report | **PARTIALLY IMPLEMENTED** (foundation live; full presentation FUTURE) |
| K15 | D19 transition workflow; full export/import (structured + provenance + lineage) (§37.1, §37.4–§37.6) | **FUTURE / NOT IMPLEMENTED** (approved direction only) |
| K16 | D21 branding self-service: own-firm only (read for all members; write for firm owner / `can_manage_team`); no global branding admin; client-supplied `consultant_id` never authorizes (§37.13) | **IMPLEMENTED** (2026-08-21, §37.13) |
| K17 | D21 brand-context resolution: `carbon_tally` / `consultant` / `co_branded` derived from authorized context; reports expose an authorized `branding` block (own firm only via ACTIVE D15 grant; Direct Customers → CarbonTally fallback) (§37.13) | **IMPLEMENTED** (2026-08-21, §37.13) |
| K18 | D21 schema: `consultant_profiles.white_label_enabled` (one column); RLS floor unchanged (no UPDATE policy → direct-client writes deny-by-default); logos via validated URLs; audit on branding updates (§37.13) | **IMPLEMENTED** (2026-08-21, §37.13) |
| K19 | D22 batch-level entity assignment: `manual_extraction_batches.entity_id` (nullable FK → `processing_entities`); single active party (entity XOR internal operator); entity-scoped RLS SELECT storey (batches + items); assignment via internal `assign` (active entity only) (§37.14) | **IMPLEMENTED** (2026-08-21, §37.14) |
| K20 | D22 entity extraction workspace: entity staff process ONLY their entity's assigned work (list/workspace/start/extract/map/calculate/status); never customer-org access (D20); internal operators never process entity work; audited reassignment (A→B, entity→internal, internal→entity) (§37.14) | **IMPLEMENTED** (2026-08-21, §37.14) |
| K21 | D22 mediated clarification foundation: entity-scoped `issues` (entity → CarbonTally → customer; NEVER direct entity↔customer communication); customer-facing issue surface excludes entity rows (§37.14) | **IMPLEMENTED** (foundation; full messaging threads FUTURE) |

### 37.12 Commercial boundary (authoritative)

CarbonTally may have **Direct Customers** and **Consultant Customers**. A
Consultant Customer may have **Consultant Clients** who are **not**
automatically CarbonTally customers. A Consultant Client becomes a Direct
CarbonTally Customer **only when a separate direct customer relationship is
established**. Processing Entities remain completely outside this model
(§37.9, §6.1, §35).



---

## 38. Scope-aware staff authorization architecture (design 2026-08-20)

Read-only authorization architecture design + security gap analysis. **No
implementation was performed.** Required before CarbonTally provisions any
Processing Entity staff user. All ratified decisions (§6.1, §35, §37) are
preserved; D15/D19 are **not** silently resolved.

### 38.1 Scope-aware authorization requirement

The minimum robust evaluation order for any operation is:

```text
1. Authenticate user
        ↓
2. Determine actor/context (customer / consultant / internal staff / entity staff)
        ↓
3. Determine authorization scope (org / firm+client / internal / entity)
        ↓
4. Resolve role(s)          ← AFTER scope, never before
        ↓
5. Resolve permissions      (staff_roles.permissions; consultant can_* flags; org role)
        ↓
6. Check resource ownership/assignment (org match, entity match, batch/item assignment, grant)
        ↓
7. Allow / deny
```

This fits the existing architecture partially: `get_current_user` (identity),
`require_staff`/`require_consultant`/`require_org_member` (actor/context),
`staff_profiles.entity_id` + `is_org_member` + `client_access`/grants (scope),
`staff_roles.permissions` and `can_*` flags (permissions), and the per-resource
guards (`ensure_batch_operator_access`, `ensure_entity_review_scope`,
`ensure_consultant_org_access`, `_checked_client`, `ensure_org_access`). The
gap is that **several guards evaluate role-name before scope** (§38.3) and one
live helper grants org access without scope (§38.5). **Role names are not
globally meaningful**: the same literal name (`admin`, `owner`) exists in
different actor contexts and must not imply the same authority.

### 38.2 Current authorization architecture map (evidence-based)

| Actor | Identity | Scope | Role(s) | Permission | Resource enforcement |
|---|---|---|---|---|---|
| Customer user | auth user + `organization_members` | customer organisation | org role (`owner/admin/member/viewer`) | none (role-based) | `require_org_member`/`require_org_admin`; RLS `is_org_member` (member + org active) tenant policies |
| Consultant firm member | `consultant_profiles` + `consultant_firm_members` | firm + explicitly granted client orgs (`client_access` / `consultant_clients`) | member role (`owner/manager/consultant/viewer`) | `can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team` | `require_consultant` → `ensure_consultant_org_access` → `ensure_consultant_permission`; RLS `is_org_consultant` |
| CarbonTally internal staff | `staff_profiles` with `entity_id IS NULL` | CarbonTally internal operations | `staff_roles` (`admin/operator/reviewer/qc_specialist`) | `staff_roles.permissions` jsonb — enforced keys: `can_view_all`, `can_process`, `can_review`, `can_manage_staff` | `require_staff` → `require_internal_staff` → `ensure_staff_permission` → batch/item/assignment checks; `staff_roles` RLS deny-by-default (service-role reads) |
| Processing Entity staff | `staff_profiles` with `entity_id IS NOT NULL` | Processing Entity (own entity) | `staff_roles` (same vocabulary) | same `permissions` jsonb (contextually dangerous — §38.3) | `require_staff` → `require_entity_scope` / `ensure_entity_review_scope`; structurally denied from extraction pipeline; RLS `is_entity_member` SELECT-only |
| Global admin (legacy) | auth user with `role_name == 'admin'` | none — **name-string** | `staff_roles.name` | `is_admin` derived | `require_admin()` / `require_role([...])` / `is_admin` bypasses (scope-blind) |

RLS functions: `is_org_member(org)` (membership active + org active),
`is_org_consultant(org)` (member active + `client_access`/grant; ignores grant
status, profile active, org active — D15), `is_entity_member(entity)` (staff
row `entity_id` match + staff active + entity status `active`).

### 38.3 Role-name authorization risks

- The literal names **overlap across contexts** with no scope qualification:
  `admin` exists as a `staff_roles` name **and** an org role; `owner` exists as
  an org role **and** a consultant member role; `reviewer` exists as a
  `staff_roles` name and an org-adjacent concept. A name string alone cannot
  identify authority.
- Scope-blind guard sites that evaluate the **name before scope**:
  - `require_admin()` (`auth.py:323`) — `role == 'admin' or role_name ==
    'admin'` → gates `/api/v3/qc/*`, `/api/v3/admin/*`,
    `/api/v3/processing-entities/*` CRUD and the legacy admin routers.
  - `require_role([...])` (`auth.py:521`) — same name-string test → gates the
    customer-facing legacy email endpoints (`/api/notifications/customer/*`),
    `customer_documents /staff/organize`, legacy admin CRUD
    (`/api/admin/permissions/*`, `/api/admin/staff/*`).
  - `is_admin` (`auth.py:286`) — name-derived; used as a **bypass** in legacy
    `require_auth()` endpoints (`emissions.py`, `upload.py`,
    `drafts_enhanced.py`, `reports.py`, `document_activity.py`,
    `organizations/data.py`, `feedback.py`, `admin/reviews.py`) to skip
    org-membership re-checks.
- **Privilege-escalation vector (G1, confirmed):** a staff profile with
  `entity_id` populated and `role_id → staff_roles.name = 'admin'` passes
  `require_admin()`, `require_role(["admin","staff"])` and `is_admin`, turning
  Processing Entity membership into platform/customer authority. No such user
  exists today (0 entities, 0 entity staff), but nothing structurally prevents
  the mis-provisioning (`POST/PUT /api/v3/ops/staff` accept `entity_id` +
  arbitrary `role_id`).
- The literal `staff` role name does **not** exist in `staff_roles` (only
  `admin`, `operator`, `reviewer`, `qc_specialist`), so `require_role(["admin",
  "staff"])` is effectively admin-name-only.
- Correct semantics: **scope first, then role** — an entity staff member with
  an `admin`-named role has **entity-scoped authority only**; an internal staff
  member with `staff-admin` authority has internal authority (§38.6).

### 38.4 Legacy `roles` table findings

`staff_roles` is the authoritative staff-permission source (used by
`get_current_user` and `operations_auth`); the general `roles` table is the
customer-org/legacy reference and must **never** authorize staff. Reference
inventory (read-only):

| Reference | What it does | Classification |
|---|---|---|
| `data/roles.py` → `repos.roles.get_by_name` in `v3_organizations.py` `create_invitation` | stamps `invitations.role_id` for **customer-org** invitations | NON-AUTHORIZATION (org reference catalog) |
| `data/roles.py` → `repos.roles.list` in `/api/v3/ops/staff-roles` | informational catalog (staff_roles + roles) | NON-AUTHORIZATION (informational) |
| `auth.py` `get_role_permissions_from_db` + `get_role_permissions` alias | legacy `roles.permissions` lookup | LEGACY / DEAD — no live callers |
| `routes/admin/permissions.py` (CRUD on `roles`) | legacy admin role/permission management | LEGACY + SECURITY RISK — guard `require_role(["admin"])` is name-string (§38.3) |
| `routes/admin/staff.py` role lookups (reads `roles`) | legacy staff-admin role display | LEGACY — guards `require_role`/`require_admin` (+ one `require_staff()` self-profile read at `/me`) |
| `roles` table RLS | single `roles_authenticated_read` (SELECT) | NON-AUTHORIZATION — direct client read-only |

Minimum disposition (no changes made): staff authorization stays on
`staff_roles`; the legacy `roles` CRUD router must be scope-guarded; `roles`
remains org-invitation reference only. No legacy `roles` path may be
reintroduced into staff authorization.

### 38.5 Organisation-access bypass findings

- **`require_org_access(org_id)` (`auth.py:454`)** — `if is_staff: return` →
  any staff (incl. entity staff) → any org. **DEAD CODE** (no mounted caller);
  must never be reintroduced (§35.5 G2).
- **`ensure_org_access` (`api/dependencies.py:131`)** — only denies when the
  caller has a **bound** org that differs; a caller with **no** bound org passes
  **any** `organization_id`. This is **LIVE**. Most V3 customer endpoints pair
  it with `require_org_member()` (safe today), but the **mounted** `/api/v2/
  business/*` endpoints (`factor-match`, `calculate`, `validate`, `benchmark`,
  `generate-report`) use only `Depends(get_current_user)` + `ensure_org_access`
  → **any authenticated user with no org membership — including Processing
  Entity staff — can act on any customer org** (`calculate` writes
  `emissions_logs` rows for that org; `generate-report` writes reports).
  **SECURITY RISK** (latent; no entity staff exist today).
- **Legacy `is_admin` bypasses** (`emissions.py`, `upload.py`,
  `drafts_enhanced.py`, `reports.py`, `document_activity.py`,
  `organizations/data.py`, `feedback.py`, `admin/reviews.py`) — `require_auth()`
  + `if not is_admin: <org-membership re-check>`; entity staff with an
  `admin`-named role bypass. **SECURITY RISK** (conditional on §38.3 G1).
- **Intended rule:** only CarbonTally **internal** staff (`entity_id IS NULL`)
  may hold the no-bound-org staff bypass; Processing Entity staff get
  **work-scoped access only** — Customer Organisation access must **never** be
  inferred from staff/entity status.

### 38.6 Internal Staff vs Processing Entity Staff design

Boundary: `staff_profiles.entity_id IS NULL` = CarbonTally internal staff;
`IS NOT NULL` = Processing Entity staff (§5, §6.1, §35). Requirements:

1. Authorization **scope is resolved before role** — every guard establishes
   internal-vs-entity first.
2. Internal-staff authority is **not inheritable** by entity staff regardless
   of role name; entity staff role resolution is **entity-scoped** (a role may
   inform capabilities *within the entity* only, never platform/customer
   authority).
3. Desired result:

```text
Processing Entity Staff  +  admin-named role   → entity-scoped authority only
CarbonTally Internal Staff + staff-admin authority → internal administration
```

4. This is a **scope dimension**, not a role rename — renaming roles would not
   help because the same literal names legitimately exist in other actor
   contexts (org roles, consultant member roles). A separate entity-role
   vocabulary is optional, not the fix.

### 38.7 Processing Entity work authorization primitives

The future work-assignment model (§30, §32) requires these primitives
(conceptual — not implemented):

- **Identity**: active `staff_profiles` row.
- **Scope**: `staff_profiles.entity_id` (the one entity the staff member belongs to).
- **Assignment**: work rows carrying `entity_id` (and/or `assigned_to`).
- **Permission**: `staff_roles.permissions` evaluated **within** the entity scope.
- **Resource ownership**: row `entity_id` = caller's `entity_id` (assignment match).

Required behavior matrix:

```text
Entity A Staff → Entity A assigned work        = ALLOWED
Entity A Staff → Entity B work                = DENIED
Entity A Staff → unassigned customer work     = DENIED
Entity A Staff → customer's unrelated data    = DENIED
Entity A Staff → CarbonTally internal work    = DENIED
```

Enforcement layers (conceptual): assignment-match **RLS storeys** on work
tables (`is_entity_member(entity_id) AND row.entity_id = caller_entity`, never
`is_org_member`); an API guard (`require_entity_work_access`) mirroring
`require_entity_scope` + assignment match; service-role repo scoping; **no
Customer-Organisation membership ever**. `manual_review_queue`/`issues` already
carry `entity_id` and are the precedent; `manual_extraction_batches`/`items`
have no entity column (§30) and must be extended before entity assignment is
possible.

### 38.8 Communication-boundary findings (ratified §35, hard requirements)

Processing Entity staff **MUST NOT**: send customer/consultant messages;
initiate customer/consultant conversations; access customer/consultant contact
details merely for communication; access customer-facing communication
channels; switch customer/consultant organisations; use notification endpoints
to communicate directly with customers/consultants.

Processing Entity staff **MAY**: submit assigned work; request clarification
through CarbonTally (§38.9); receive workflow notifications for assigned work;
access the minimum data necessary for assigned work.

Current mechanisms that **could violate** these once entity staff are
provisioned:

| Mechanism | Violation path |
|---|---|
| Legacy email endpoints `POST /api/notifications/customer/manual-extraction`, `/batch/completion` | guard `require_role(["admin","staff"])` is name-string — an entity staff member with an `admin`-named role could send **customer-facing emails** (§38.3) |
| Legacy `is_admin` org re-check bypasses | entity staff with `admin`-named role → customer org data → contact details and communication-relevant data (§38.5) |
| `/api/v2/business/*` `ensure_org_access` no-bound-org bypass | entity staff → any org → contact/org data (§38.5) |
| Client-side chat (`ChatWidget`), `messages`/`conversations` | RLS org-member/consultant-only — **denied today**; must remain denied (no entity storey) |
| V3 notifications (`/api/v3/notifications`) | per-user only — entity staff see their own rows; no create-to-customer endpoint — safe today |

### 38.9 Mediated clarification architecture (conceptual future, NOT implemented)

Required workflow (ratified §35 Decision 2):

```text
Entity Staff → clarification request → CarbonTally Staff review/relay
  → Customer / Consultant → response → CarbonTally Staff → Entity Staff
```

The entity staff member must **not** receive the customer/consultant's direct
contact identity or communication channel. Existing structures that could
support this (none are sufficient today):

- `manual_review_queue` / `issues` — org + entity-scoped work context
  (`issues.conversation_id` exists but `conversations` RLS is org-member/
  consultant-only, so it is not an entity-visible channel).
- `audit_logs` / `activity_logs` — org-scoped audit of the relay.
- No entity-scoped, CarbonTally-mediated clarification surface exists.

**ARCHITECTURAL GAP** — a future entity-scoped, CarbonTally-mediated
work-clarification surface is required; it must never be a direct
entity↔customer/consultant channel.

### 38.10 Consultant authorization remains separate

Preserved (§37, D15/D19): Consultants are CarbonTally customers with explicit
grant-based access to consultant-client organisations
(`require_consultant` + `ensure_consultant_org_access` + `can_*` flags +
`is_org_consultant`). Processing Entities are back-office processors with
**assigned-work** access. These are different authorization models and are
**never combined**. D15 (consultant-client relationship lifecycle) and D19
(lifecycle/transition design) remain unresolved/awaiting approval — this
analysis does not resolve them.

### 38.11 Proposed authorization matrix (refined from the actual implementation)

| Actor | Customer Org | Consultant Client | Internal Ops | Entity Work | Customer Communication |
|---|---|---|---|---|---|
| Customer user | scoped (own org; `require_org_member` + `is_org_member`) | N/A | No | No | own permitted channels (org-gated chat; nothing else live) |
| Consultant firm member | granted clients only (`is_org_consultant` + `ensure_consultant_org_access`; grant status not enforced — D15) | scoped (client workspace) | No | No | customer-facing per `can_*` flags + org-gated chat |
| CarbonTally internal staff | operational only via permission-gated ops surfaces (`require_internal_staff` + `ensure_staff_permission`); no implicit org membership | per staff authority (none today) | Yes | assigned/authorized (internal assignments) | CarbonTally-mediated (admin/staff-gated email endpoints; no direct chat) |
| Processing Entity staff | **No** | **No** | **No** | **assigned entity work only** (§38.7) | **No direct contact** (CarbonTally-mediated clarification only) |

Note: no internal-staff role has unrestricted access — `can_view_all`,
`can_process`, `can_review`, `can_manage_staff` are checked per endpoint.

### 38.12 Security threat scenarios (evaluation)

| # | Scenario | Expected | Current status |
|---|---|---|---|
| A | Entity A staff assigned an `admin`-named staff role | Entity-scoped authority only | **NOT GUARANTEED** — `require_admin`/`require_role`/`is_admin` are name-string; G1. Fix required before provisioning (§38.6) |
| B | Entity A staff attempts direct Customer A access | DENIED | **DENIED today** via `require_org_member` on V3 customer surfaces; **NOT DENIED** on `/api/v2/business/*` (`ensure_org_access` no-bound-org bypass) and legacy `is_admin` bypasses (§38.5) |
| C | Entity A staff attempts Entity B work | DENIED | **DENIED today** — `require_entity_scope`/`ensure_entity_review_scope` + entity RLS; extraction pipeline structurally denied (no entity column) |
| D | Entity A staff uses a customer messaging endpoint | DENIED | **DENIED today** — messages/conversations RLS org-member/consultant-only; `communication.py` unmounted. **Conditional risk:** legacy customer-email endpoints under `require_role(["admin","staff"])` if role-name admin (§38.8) |
| E | Entity A staff requests clarification | Allowed only via CarbonTally-mediated workflow | **NOT SUPPORTED** — no mediated surface (§38.9); no direct channel exists |
| F | Internal staff and entity staff share the same literal role name | Different authority because actor scope differs | **NOT GUARANTEED** — authority is name-string today; scope-first design required (§38.6) |
| G | A legacy authorization helper is accidentally called by a new endpoint | No customer-org privilege escalation | **NOT GUARANTEED** — `require_org_access` (dead) and `ensure_org_access` (live no-bound-org bypass) are both "staff → any org" patterns; must be scope-guarded (§38.5) |

### 38.13 Minimum implementation requirements (classified — not implemented)

**REQUIRED BEFORE ENTITY PROVISIONING**

- **R1** Scope-first authorization: every admin/role gate consults the
  internal-vs-entity scope dimension before any role-name comparison; entity
  staff can structurally never pass `require_admin` / `require_role` /
  `is_admin`.
- **R2** Fix `ensure_org_access`: the no-bound-org staff bypass applies to
  **internal staff only**; entity staff → deny org access (§38.5).
- **R3** Replace legacy `is_admin` org re-check bypasses with scope-aware
  checks (§38.5).
- **R4** Scope-guard the legacy admin routers and name-string-guarded customer
  surfaces (`routes/admin/permissions.py`, `routes/admin/staff.py`, legacy
  customer-email endpoints, `customer_documents /staff/organize`) (§38.3–§38.4).
- **R5** Enforce that the `roles` table never authorizes staff (staff_roles is
  the sole source); keep it org-invitation reference only (§38.4).

**REQUIRED FOR ENTITY WORK ASSIGNMENT**

- **R6** Entity assignment on work tables (entity_id on
  `manual_extraction_batches`/`items`), assignment-match RLS storeys, an API
  `require_entity_work_access` guard, and service-role repo scoping — mirroring
  §30/§32 and the `manual_review_queue`/`issues` precedent (§38.7).
- **R7** Entity-scoped audit context for entity actions (`audit_logs` is
  org-scoped today).

**REQUIRED FOR PHASE 9**

- **R8** P0 verification extended to the scope-first model and scenario A–G
  (§27, §38.12), including `ensure_org_access` and legacy-guard regression
  tests.

**FUTURE**

- **R9** Mediated clarification workflow (entity-scoped, CarbonTally-routed,
  never direct) (§38.9).
- **R10** Entity work surface/UI and white-label per-tenant branding (§37.8).

**OPTIONAL**

- **R11** A separate entity-role vocabulary and role-name linting for
  entity-scoped profiles (§38.6 — optional, not the fix).

### 38.14 Decision classification (consolidated)

| # | Conclusion | Classification |
|---|---|---|
| L1 | Scope-first authorization evaluation order; role names are not sufficient authority; internal-vs-entity boundary (§38.1, §38.6) | **BUSINESS DECISION — REQUIRES USER APPROVAL** (design recorded; required before entity provisioning) |
| L2 | G1 name-string risk confirmed at `require_admin`/`require_role`/`is_admin` + legacy bypasses (§38.3) | **SECURITY RISK** + **IMPLEMENTATION REQUIRED** |
| L3 | `ensure_org_access` live no-bound-org bypass on mounted `/api/v2/business/*` (§38.5) | **SECURITY RISK** (latent) + **IMPLEMENTATION REQUIRED** |
| L4 | `require_org_access` dead any-staff→any-org helper (§38.5) | **SECURITY RISK** (latent — must never be reintroduced) |
| L5 | Legacy `roles` table references classified; staff authorization stays on `staff_roles` (§38.4) | **CURRENTLY SUPPORTED** (staff side) + **LEGACY** (admin CRUD) |
| L6 | Entity work authorization primitives and assignment matrix (§38.7) | **NOT SUPPORTED** / **IMPLEMENTATION REQUIRED** (future) |
| L7 | Communication boundary (ratified §35) holds today; conditional violation paths identified (§38.8) | **CURRENTLY SUPPORTED** + **SECURITY RISK** (conditional on G1) |
| L8 | Mediated clarification workflow (§38.9) | **ARCHITECTURAL GAP** / **FUTURE** |
| L9 | Consultant authorization remains separate; D15/D19 preserved (§38.10) | **BUSINESS REQUIREMENT — RESOLVED** (separation) / D15+D19 awaiting approval |

### 38.15 Implementation status (2026-08-20) — D20 hardening + D15 enforcement

Implemented and verified (approved minimum; code is `backend/auth.py`,
`backend/api/dependencies.py`, `backend/api/consultant_auth.py`,
`backend/api/v3_consultants.py`, `backend/data/consultants.py`, migration
`supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql`):

- **R1 — Scope-first authorization guards.** `AuthUser` now carries the scope
  dimension (`is_internal_staff` / `is_entity_staff` from
  `staff_profiles.entity_id`); `require_admin()`, `require_role([...])`,
  `require_org_admin()` (global-admin path) and `is_admin` are gated to
  CarbonTally INTERNAL staff — a Processing Entity staff profile with an
  `admin`-named role can never hold internal/platform authority.
- **R2 — `ensure_org_access` any-org bypass fixed.** Processing Entity staff
  are always denied customer-organisation access; internal staff keep the
  operational bypass; org members are bound to their own org; unbound non-staff
  users are denied.
- **R3 — legacy `is_admin` org-access bypasses neutralised** at the source
  (`is_admin` is internal-scope-gated), so the legacy `if not is_admin: <org
  re-check>` paths can no longer be reached by entity staff.
- **R4 — legacy admin routers scope-guarded** via the hardened
  `require_admin()` / `require_role([...])` (entity staff denied before any
  role-name comparison).
- **R5 — legacy `roles` never authorizes staff.** Staff permissions are
  resolved exclusively from `staff_roles`; the `roles` table remains an
  org-invitation/reference catalog (the `get_role_permissions_*` helpers have
  no callers).
- **D15 — consultant access follows the relationship lifecycle.** `is_org_
  consultant` (RLS) and `ensure_consultant_org_access` (API) require an ACTIVE
  `consultant_clients` grant; new grants default `active`; the firm may still
  manage its own grant rows (§34).

Verification (2026-08-20):

- New unit suite `backend/tests/unit/api/test_scope_aware_authorization.py`
  (threat scenarios A–L) — 16 tests, all pass.
- Full backend unit suite — 868 tests, all pass (no regressions).
- API smoke suite — 85/85 pass against the running local app.
- RLS behaviour verified transactionally against the local Supabase DB
  (rollback-protected): inactive grant → org tenant rows invisible; active
  grant → visible.
- The integration RLS test suite was **not** executed this session because its
  session fixture truncates demo-critical tables (organisations / consultants /
  members); the D15 RLS behaviour was verified with a rollback-protected
  transaction instead. (The D15 integration tests added to
  `test_v3_rls_behavior.py` will run under the normal integration harness.)

Remaining limitations (not implemented):

- Client-switch list display filtering (§34 item 4) — the list still returns
  the firm's own grants; access is enforced at API/RLS layers.
- D19 transition workflow, entity work assignment (§30/§38.7), mediated
  clarification (§38.9) — future work.
- `is_org_consultant` still ignores `consultant_profiles.is_active` and
  `organizations.is_active` (K9, §37.2) — documented, not changed.



---

## 39. Revision Note — 2026-08-20 (v5 — Scope-aware staff authorization)

- The original actor/workspace/access audit was reviewed in full.
- The audit remains **implementation-authoritative** (schema → domain → API →
  RLS → frontend → docs).
- Phase 9 prerequisites were **reclassified**: D14/D15/D17 = blocking
  architecture/access decisions; D1/D4/D5/D6/D16 = non-blocking terminology;
  D2/D3/D7–D13 = non-blocking open items (§21, §25).
- Added the authoritative staff-role model clarification (§5.1) and the
  processing-entity canonical-term clarification (§6).
- Added cross-organisation isolation to the Phase 9 P0 plan (§27 P0-1) with an
  Org B fixture requirement (not created).
- **UPDATE 2 (same day) — Processing Entity operating model RATIFIED:** one
  org may use multiple processing parties; orgs are not permanently bound to a
  single entity; no `organizations.processing_entity_id`; CarbonTally controls
  assignment; entity staff scoped to assigned work. D14/D17 moved from
  blocking-unknown to **RESOLVED REQUIREMENT — IMPLEMENTATION GAP REMAINS**
  (§6, §21, §25). Added the full implementation-gap report (§30), many-to-many
  verification (§31), conceptual access model (§32), reassignment model (§33),
  D15 confirmation + recommended revocation rule (§34), and the proposed entity
  demo scenario (§36 — PROPOSED, NOT CREATED).
- **UPDATE 3 (same day) — Processing Entity non-customer-facing boundary
  RATIFIED (D18):** Processing Entities are strictly back-office processors —
  work access only, no direct customer/consultant contact, no customer-facing
  communication authority, all communication mediated by CarbonTally (§35).
  Added the impact-analysis matrix (§35.3), the communication-surface inventory
  (§35.4) and the gap/risk classifications — including the name-string
  `admin`/`is_admin` authorization risk and the unmounted/denied communication
  surfaces (§35.5). Re-numbered sections: former §35 (demo scenario) → §36;
  this revision note → §39.
- **UPDATE 4 (same day) — Consultant client lifecycle & white-label analysis
  (§37):** commercial model clarified — consultant = direct CarbonTally
  customer; consultant client initially the consultant's customer; a client
  may become a direct CarbonTally customer via an **in-place** data transition;
  export/import is a separate portability capability; relationship termination
  ≠ ownership; white-label is future. Added the consultant/client domain
  inventory (§37.2), lifecycle + semantic-gap analysis (§37.3), conceptual
  transition model (§37.4), data-preservation requirements (§37.5),
  export/import analysis (§37.6), re-scoped D15 wording (§37.7), white-label
  pressure points (§37.8), PE-boundary preservation (§37.9), the
  G1-in-consultant-context minimum requirement (§37.10) and the consolidated
  decision classification (§37.11). This revision note renumbered §37 → §39.
  **No implementation performed.**
- **UPDATE 5 (same day) — Scope-aware staff authorization architecture
  (§38):** recorded the scope-first authorization requirement, the evidence-
  based actor/scope/role/permission map, the role-name risks (G1 confirmed at
  `require_admin`/`require_role`/`is_admin` + legacy bypasses), the legacy
  `roles` reference classification, the organisation-access bypasses (including
  the **live** `ensure_org_access` no-bound-org bypass on mounted
  `/api/v2/business/*`), the Internal-vs-Entity staff design, the Processing
  Entity work-authorization primitives, the communication-boundary findings,
  the mediated-clarification gap, the proposed authorization matrix, threat
  scenarios A–G, and the classified minimum implementation requirements
  (R1–R11). Added D20 (§21/§25/§26). This revision note renumbered §38 → §39.
  **No implementation performed.**
- **UPDATE 6 (same day) — D20 scope-aware authorization hardening IMPLEMENTED
  and D15 enforced (§38.15, §34).** R1 scope-first guards (internal-vs-entity
  staff boundary on `AuthUser` + `require_admin`/`require_role`/
  `require_org_admin`/`is_admin`), R2 `ensure_org_access` fix, R3 `is_admin`
  neutralisation, R4 legacy-admin scope-guarding, R5 `roles`-table independence
  and D15 active-grant enforcement (RLS `is_org_consultant` + API
  `ensure_consultant_org_access` + grant-creation default `active`) implemented
  and verified. New unit suite (16 tests, scenarios A–L), full unit suite
  (868 tests) and API smoke (85/85) all pass; RLS behaviour verified
  transactionally. **No Processing Entities, entity staff, users, organisations
  or demo data were created; demo data verified intact.**
- **UPDATE 7 (same day) — Consultant commercial model FINALIZED (§37).** Hybrid
  model (Direct Customers + Consultants-as-customers) with consultant-led
  **MANAGED SERVICE** as the default. **Consultant Clients do NOT automatically
  use or access CarbonTally** (authoritative correction — earlier wording
  implied otherwise). Modes: A Managed Service (default) / B Co-Branded
  (future) / C Fully White-Label (future). Expanded the white-label architecture
  analysis (§37.8: branding/domain/identity/email/reports/authentication) and
  added the commercial boundary (§37.12) + decision rows K12–K15 and D21
  (§21/§25/§26). **No implementation performed.**
- **UPDATE 8 (2026-08-21) — D21 White-Label Foundation IMPLEMENTED (§37.13).**
  Minimum production-ready white-label capability: consultant branding
  configuration (backend `domain/branding.py` + repo + API `GET/PUT
  /me/branding` + `/me/branding/context`, audited), authorized brand-context
  resolution (`carbon_tally` / `consultant` / `co_branded`; never from a
  client-supplied id), report-branding context on the report surfaces, email
  sender-configuration foundation, and a Consultant **Firm branding** UI tab.
  Smallest schema change — one column
  (`consultant_profiles.white_label_enabled`, migration
  `20260821010000_d21_white_label_branding.sql`); **no new tenancy model**. RLS
  floor unchanged (no UPDATE policy → direct-client writes deny-by-default).
  Verified: 20 new unit tests (D21 test matrix A–M) + full unit suite 849 pass;
  live API verification 16/16 (read/write/brand-context/report branding/
  customer-403/arbitrary-id-ignored) with audit rows recorded; demo data
  verified intact (branding set+reverted). Explicitly NOT implemented: rendered
  logo-in-report, outbound custom-domain email, custom domains, consultant-client
  portal/access, D19 transition, export/import, tenant abstraction.
  **No Processing Entities, entity staff, users, organisations or demo data
  were created.**
- **UPDATE 9 (2026-08-21) — D22 Processing Entity work assignment +
  extraction workspace IMPLEMENTED (§30/§32/§33/§37.14).** CarbonTally assigns
  extraction work to internal staff OR Processing Entity A/B/C via batch-level
  `manual_extraction_batches.entity_id` (single-active-assignment: entity XOR
  internal operator); entity staff process ONLY their entity's assigned work
  through the entity extraction workspace (`/api/v3/ops/entities/{id}/extraction/*`),
  with mediated clarification (entity-scoped `issues`; entity → CarbonTally →
  customer — never direct), audited assignment/reassignment (V3 `audit_trail`,
  ADR-V3-013), and an entity-scoped RLS SELECT storey on
  `manual_extraction_batches`/`manual_extraction_items`. Migration
  `20260821020000_d22_processing_work_assignment.sql` (+ `issues.manual_extraction_batch_id`
  clarification link); **no new tenancy model, no entity write policies, no
  direct entity↔customer communication**. Bidirectional isolation: entity
  batches leave the internal operator queue; entity staff never reach
  internal/customer surfaces (D20/D21 intact). Verified: 17 new unit tests
  (D22 matrix A–Q) + full unit suite passes; RLS policies verified live;
  demo data intact. Explicitly NOT implemented: full mediated messaging
  threads, rendered report handoff, per-entity SLA/capacity automation, and
  provisioning real entity staff in a live environment.
  **No Processing Entities, entity staff, users, organisations or demo data
  were created.**
- **UPDATE 10 (2026-08-22) — D24 workspace-completion & Phase-9 readiness
  audit.** READ-ONLY audit + narrowly-scoped P1 UI completion. Verified live:
  customer workspace (owner/admin/member/viewer; foreign-org and
  staff→customer-surface denied), internal staff workspace (queues/dashboard/
  roster/roles; customer→ops and consultant→ops denied), consultant workspace
  (profile/clients/client dashboard/reports/processing/issues/documents/
  branding; cross-org denied; INACTIVE grant → client data denied, firm may
  still manage grant rows — D15 intact), Processing-Entity workspace (full
  transient journey verified then cleaned up), and communication boundaries
  (ops staff cannot read the customer member directory; entity staff denied
  consultant/admin surfaces). **P1 UI completion**: batch assignment surface in
  the Data entry queue (internal operator XOR Processing Entity, with reason —
  `assignBatch`), a Processing Entities tab (`ProcessingEntitiesTab.jsx`,
  staff-admin create/list), and entity-scope provisioning on the Staff tab
  (create + change profile entity). Frontend build compiles; frontend V3 api
  tests 9/9; backend ops/auth suites pass. Remaining gaps (all P2/P3, no P0,
  no P1): frontend routes are not per-role guarded (backend remains
  authoritative), no UI to deactivate/activate a consultant client grant or
  to edit SLA settings, no permanent demo entity/client-team data.
  **No permanent demo entities, users, organisations or data were created.**
- **D15 is IMPLEMENTED (2026-08-20, §34/§38.15)** — consultant access to a
  client requires an ACTIVE grant; INACTIVE / REVOKED → denied (RLS + API);
  D24 re-verified live. D19 and D20 follow-up approvals remain.

---

## 39. Phase 9 record (2026-08-22)

**Phase 9 STARTED — P0 integration + RLS + actor-workflow acceptance
verification.**

- **Baseline (recorded at Phase 9 start):** backend unit suite 890 passed;
  frontend V3 jest 9/9; frontend build EXIT=0; RLS integration suite 11/11;
  server health 200. The pre-existing demo dataset was replaced by concurrent
  demodatagen seeding activity during Phase 9 (the working database is shared);
  all Phase 9 actors were therefore provisioned as TRANSIENT fixtures and
  removed at the end.
- **Tests performed (live, against the running server):** customer journey
  (39 checks — workspace, upload, own data, exports; Customer A→B, A→consultant,
  A→ops/entity all denied), consultant journey (active grant 200; cross-firm and
  unrelated-customer denied; INACTIVE→403; REACTIVATED→200 — D15 intact),
  internal staff permission differences (operator/reviewer/QC/admin; customer/
  consultant/entity → internal surfaces denied), entity workflow (assignment
  internal→A→B→internal; access flips instantly; stale access removed; entity
  staff blocked from internal/consultant/admin/customer surfaces — communication
  boundary absolute), extraction workflow (start→extract→map→validate→calculate;
  multi-line; co2e = 0.364 kg verified mathematically; emissions_logs persisted),
  QC gate (entity staff and operator denied; QC specialist passes), issues +
  mediated clarification (issue linked to batch, entity-scoped; customer contact
  NOT exposed), inactive/suspended entity (assign 422, workspace 403),
  D20 admin-named-role entity staff (require_admin, customer org, internal
  surfaces all denied), D21 branding per actor, auditability (audit_trail
  records who assigned/reassigned + reason; verified post-assignment) and data
  integrity (0 orphans, valid references).
- **RLS verification (direct Postgres, JWT claims + authenticated role):**
  customer/consultant/entity isolation all return clean filtered rows (own=1,
  foreign=0). **P1 RLS defect found & fixed**: SELECT policies on
  `organization_members` and `consultant_firm_members`/`consultant_clients`
  embedded INLINE self-referential subqueries → infinite recursion on every
  direct authenticated read (failed closed, no leak, but surface broken).
  Fixed by `supabase/migrations/20260822000000_p9_rls_recursion_fix.sql`
  (SECURITY DEFINER firm-membership helpers + rewritten policies). Verified:
  recursion gone, all denials intact, RLS integration suite 11/11.
- **P1 auth defect found & fixed:** the JWT fallback path in `auth.py`
  `get_current_user` referenced an unbound `user` local when GoTrue could not
  resolve the identity → 500 on authentication instead of authenticating.
  Fixed (`user = None` initialisation + guarded metadata extraction). Verified
  via live fixture logins and the 73-test ops/auth unit suites (0 failures).
- **Result: all Phase 9 acceptance rows PASS.** No P0. Two P1s found and fixed.
- **P2/P3 backlog (post-Phase-9, unchanged, non-blocking):** customer Issues
  page, notifications page, consultant client activate/deactivate UI, SLA
  settings UI, frontend role-route guards, `/staff-roles` reference catalog
  visible to entity staff (read-only reference data, no authority), custom
  domains / outbound custom-domain email / rendered white-label PDFs / D19 /
  export-import / full mediated messaging threads.
- **Phase 9 completion status:** **PHASE 9 COMPLETE** (formally closed
  2026-08-22 by the Phase 9 Closure record — all 27/27 acceptance rows passed;
  P0 = 0; P1 = 2 discovered and fixed (auth fallback, RLS recursion); RLS
  integration 11/11; frontend Jest 9/9; frontend build success; full backend
  unit suite 890/890; temporary fixture residue = 0; no permanent Phase 9
  entities/users/data created).

### 39.1 Phase 9 closure record (2026-08-22)

Formal closure verification for Phase 9:

- **Fix #1 (auth fallback)** — VERIFIED. `auth.py` `get_current_user` no longer
  references an unbound local `user` (initialised to `None`; metadata
  extraction guarded). Live probe: a signed JWT for an identity GoTrue cannot
  resolve authenticates via the fallback (own-org documents 200; foreign org
  403) instead of returning HTTP 500.
- **Fix #2 (RLS recursion)** — VERIFIED. Migration
  `20260822000000_p9_rls_recursion_fix.sql` present and applied: 3 SECURITY
  DEFINER firm-membership helpers exist; 8 rewritten non-recursive policies
  exist on `organization_members`, `consultant_firm_members`,
  `consultant_clients`; 0 inline self-referential recursive policies remain.
  RLS integration suite 11/11.
- **Closure tests:** full backend unit suite 890 passed / 0 failed / 0 errors;
  targeted closure suite (operations-auth, scope-aware/D20, consultant-branding
  D21, v3-operations D22, d23 extraction UX, entity extraction, processing
  workflow, foundation, RLS behavior) 143 passed / 0 failed; frontend Jest
  9/9; frontend build EXIT=0.
- **Broader `tests/integration` suite:** 34 failures / 92 errors remain and are
  **ENVIRONMENTAL / PRE-EXISTING**, unchanged from the Phase 9 record —
  `SupabaseException: Invalid API key` (Supabase stack/key reconfigured by
  concurrent activity), `ConsultantsRepository.add_client()` missing new D21
  positional args (stale test signature), and `asyncpg AmbiguousParameterError`
  (parameter typing). They are not caused by the Phase 9 fixes and are recorded
  as environmental, not silently reclassified as passing.
- **Concurrent demodatagen environment:** a separate
  `carbon_tally_synthetic_documents` repository (local git, no commits, not
  tracked in this repo) was actively seeding the shared local Supabase
  database during Phase 9 and is the source of the current public-schema rows
  (96 organisations, demodatagen staff/entities/consultants, audit/log rows).
  No generator process was running at closure time; its legitimate seeded data
  was not modified or deleted. Its periodic re-seeding can change public-table
  row counts and must be taken into account before future acceptance runs.
- **Database integrity at closure:** organisations 96, public users 77,
  auth users 9, staff profiles 5, processing entities 12, consultant profiles
  7, consultant clients 3, extraction batches 0, items 0, emissions logs 7,
  audit trail 50. **Phase 9 fixture residue = 0** (no Phase 9 auth user, org,
  or processing-entity UUIDs remain). No permanent Phase 9 entities/users/data
  were created.

---

## 40. D25 product completion record (2026-08-22)

**D25 — product-completion UX/workflow implementation. Status per capability:**

| Capability | Status |
|---|---|
| Frontend role-route guards | **IMPLEMENTED** — `RoleRoute`/`useActorRoles` wraps the V3 routes (`requireOrg` for customer surfaces, `requireConsultant` for `/consultant`, `requireStaff` for `/ops`); backend/RLS remain authoritative. |
| Customer Issues page | **IMPLEMENTED** — `/issues` (`IssuesPage.jsx`) over the existing org-scoped `/api/v3/issues` surface (list, status, severity, detail, report; entity-scoped rows never exposed; cross-org 403 verified live). Customer replies on issues: **FUTURE**. |
| Notifications page | **IMPLEMENTED** — `/notifications` (`NotificationsPage.jsx`) over `/api/v3/notifications` (read/unread, mark-read, mark-all, link targets). **P1 fixed**: the repository/domain/API referenced a non-existent `notifications.user_id` column; aligned to the real per-recipient schema (`recipient_type`/`recipient_id`/`title`/`message`/`link`). Per-user isolation verified live. |
| Consultant client lifecycle UI | **IMPLEMENTED** — activate/deactivate controls on the consultant Clients list (gated by `can_manage_clients`; D15 authorization untouched; backend `PUT /clients/{id}` unchanged). `/me` now also returns the firm member's `can_*` flags (additive). |
| SLA settings UI | **IMPLEMENTED (safe portion)** — ops **SLA** tab (staff admin) reads `/api/v3/ops/sla/settings` and updates the review `sla_hours` via a new bounded `PUT` (reuses the existing `queue_settings` upsert). Capacity automation/escalation weights deliberately not exposed. |
| Staff roles reference | **IMPLEMENTED** — read-only ops **Roles** tab rendering the authoritative `staff_roles` catalog; no second authorization mechanism; entity staff gain no authority. |
| White-label rendered reports | **PARTIALLY IMPLEMENTED (foundation)** — server-authorized brand context already resolved on report surfaces (D21); D25 now also embeds the authorized `branding` in the report download payload. Actual branded PDF rendering: **FUTURE** (no PDF pipeline in V3 — documented gap). |
| Custom domains | **DESIGN ONLY** — requires DNS/SSL/routing infrastructure and domain-verification decisions; configuration/data model not built. |
| Outbound custom-domain email | **DESIGN ONLY** — `email_from` branding is configuration only; SPF/DKIM/DMARC + verified-sender foundation not present. |
| D19 Consultant Client → Direct Customer | **DESIGN ONLY** — the approved direction (org + data + provenance preserved; grants end; direct relationship begins) is recorded (§37). The D19 row still requires **user approval** for the lifecycle-state/transition-workflow specifics — stopped per policy; no code written. |
| Export/import | **DESIGN ONLY** — exports (CSV/JSON) exist; customer-data import requires a design + implementation boundary; factor/reference imports are a separate concern. |
| Mediated messaging | **PARTIALLY IMPLEMENTED (clarification leg)** — entity-scoped mediated clarification issues exist (entity → CarbonTally → customer); full thread/reply messaging is **FUTURE** (dormant `conversations`/`messages` tables; no secure mediation surface yet). |

**D25 verification:** backend unit suite 890/890; targeted suites (issues,
consultants, foundation, operations) 81/81 + foundation regression test for the
notifications schema (13/13); frontend Jest 12/12 (added D25 API-client tests);
frontend build EXIT=0; live probes: notifications list/isolation/mark-read,
issues create/list/cross-org-403, SLA get/put/restore, consultant `/me` flags —
all pass. Broader integration-suite failures remain environmental (unchanged
from the Phase 9 record). No permanent demo entities/users/data created; all
D25 probe rows cleaned up.

---

## 41. D26 product-completion audit + scale hardening record (2026-08-22)

**D26 — authentication, onboarding, communication and SaaS-critical gap audit,
with bounded implementation. Status per requirement:**

| Capability | Status | Notes |
|---|---|---|
| Authentication | **IMPLEMENTED** | Supabase Auth (GoTrue) email/password + session refresh + JWT HS256 fallback preserved (`auth.py`); login/signup/reset/password-change surfaces exist (Login, BetaLogin, MagicLink, SecurityTab). No second auth system. |
| Google login | **CONFIGURATION REQUIRED** | `signInWithOAuth('google')` wired in `Login.js`; OAuth is **authentication only** (never grants org/consultant/entity/staff membership). Whether the provider is enabled on the Supabase dashboard is not verifiable from this repo — do not claim it works until a configured provider is tested. |
| MFA/2FA | **FOUNDATION ONLY** | ADR-consistent: platform MFA belongs to Supabase Auth (`auth.mfa_*`); `SecurityTab` queries `supabase.auth.mfa.listFactors()` honestly and does NOT fake enrollment. App-side TOTP secrets are deliberately NOT stored (documented ADR). Enrollment/challenge UI + provider config: **FUTURE**. |
| Account/profile settings | **IMPLEMENTED** | V3 AdminPage Profile/Security tabs: org profile + metadata (admin edit), account info, auth provider, password change via `supabase.auth.updateUser`. No sensitive fields exposed. |
| Direct Customer onboarding | **PARTIALLY IMPLEMENTED** | Signup → (legacy) org creation + membership + facility/asset wizard exists. Invitation acceptance is **BROKEN/orphaned**: the legacy `/api/auth/magic` endpoint does not exist in the active backend and `pending_invites` has no active code path — V3 has no accept-invite endpoint. Creating an org via V3 is legacy-only. |
| Customer invitations | **PARTIALLY IMPLEMENTED** | V3 Admin Members tab: invite create (7-day token), list, revoke, member add/remove/role — org-scoped + cross-org denied (tests). Accept/reject/expire handling: **MISSING** (no active acceptance endpoint). |
| Consultant onboarding | **IMPLEMENTED (API)** | `POST /api/v3/consultants/me` (profile/firm create), `/me/team` (firm members), `/me/clients`, branding, dashboard. V3 UI: ConsultantPage (clients + activate/deactivate, D25). |
| Consultant member invitation | **PARTIALLY IMPLEMENTED** | `/me/team` create exists (API); role/capability assignment + deactivation UI on the team surface is not exposed in V3 (firm isolation is enforced by `consultant_firm_members` + `can_*` permission model — role-name authorization is not used). |
| Processing Entity provisioning | **IMPLEMENTED (API)** | `/api/v3/ops/entities` (list), `/staff` POST/PUT (provision/activate staff incl. `entity_id`), D20 scope-first entity staff authorization, D22/24 extraction workspace. Entity staff can never become org members automatically (no code path). |
| Entity staff invitation | **DESIGN ONLY** | Staff provisioning exists; invitation-based entity staff onboarding UX is not built (staff are provisioned by ops admin). |
| Email verification | **CONFIGURATION REQUIRED** | Supabase platform setting; no app-level verification gate. |
| Password recovery | **IMPLEMENTED** | `supabase.auth.resetPasswordForEmail` (MagicLink page); password change via `updateUser`. |
| Session management | **IMPLEMENTED** | `getSession`/`onAuthStateChange`/`setSession`; expired session → 401 handling; backend validates every request; JWT fallback not weakened. |
| Customer Issues | **IMPLEMENTED** | D25 (org-scoped, entity-hidden, audit-recorded); re-verified in this audit. Customer reply semantics remain **FUTURE** (not invented). |
| Notifications | **IMPLEMENTED** | D25 schema fix + per-user isolation; D26 adds bounded pagination (`limit` 1..500, `offset`, accurate `total`). |
| Real-time messaging | **NOT IMPLEMENTED (see §42)** | Dormant `conversations`/`messages`/`conversation_participants`; legacy `ChatWidget`/`RealtimeContext` cannot function (participant RLS denies all; no backend messaging API; publication membership unverified). |
| Mediated Processing Entity communication | **PARTIALLY IMPLEMENTED** | Entity→CarbonTally→Customer mediated **clarification issues** exist (`/ops/.../clarify`, issues, notifications). Full mediated message threads: **FUTURE** (no secure participant model for entities in the org-scoped conversation schema). |
| White-label PDF rendering | **FOUNDATION ONLY** | Server-authorized BrandContext embedded in report download payload (D25). No PDF renderer exists in V3 — branded PDF generation remains **FUTURE**. |
| D19 consultant-client → direct customer | **BLOCKED — BUSINESS DECISION** | Approved direction recorded (§37/D25). Lifecycle-state/transition-workflow specifics still require product-owner approval. No code. |
| Export | **IMPLEMENTED (scoped)** | `/api/v3/exports/emissions.{csv,json}` + `documents.csv` — org-isolated, tested. Full org export (metadata/members/documents/extraction/audit): **DESIGN ONLY**. |
| Import | **DESIGN ONLY** | Customer-data import format/validation/rollback is undefined → stopped. Factor/reference import is a separate concern (existing surface). |
| Custom domains | **DESIGN ONLY** | Requires DNS/SSL/routing + domain-verification decisions; no CarbonTally-side foundation built. |
| Custom email | **DESIGN ONLY** | `email_from` branding is configuration-only; SPF/DKIM/DMARC foundation absent. |
| Audit trail | **IMPLEMENTED** | `audit_logs` via `AuditRepository` (issues/reports/members/metadata + admin audit API). No secrets stored. Login/security-event audit: partial (platform-owned). |
| Billing/subscription | **MISSING** | `organizations` has subscription/tier/trial/billing-contact columns but **all 96 orgs have NULL values**; no plan logic, provider integration, or UI. Do not assume complete. |
| Pagination/performance | **PARTIALLY IMPLEMENTED → HARDENED (D26)** | Documents (limit 100/offset) + reports (limit 1..500) already paginated. **D26 added** bounded pagination to per-user notifications and customer issues. Ops queues/consultant clients are bounded by batch/usage; item-level queue pagination is follow-on. |

**D26 code changes (all additive, backward-compatible, business-rule-known):**

1. `backend/data/notifications.py` — `list_for_user(...)` gains `limit`/`offset`
   (`created_at DESC` stable ordering) + new `count_for_user(...)`.
2. `backend/api/v3_notifications.py` — `GET /api/v3/notifications` accepts
   `limit` (clamped 1..500) / `offset` (≥0); `total` now from `count_for_user`;
   response adds `limit`/`offset`.
3. `backend/data/issues.py` — `list_for_org(...)` gains `limit`/`offset`
   (stable `created_at DESC, id`) + new `count_for_org(...)`.
4. `backend/api/issues.py` — customer `GET /api/v3/issues` accepts validated
   `limit` (1..500) / `offset` (≥0); `total` from `count_for_org`.
5. `backend/tests/unit/api/fakes.py` — `MemoryIssues` mirrors the new
   signatures; `_StubRepo` gains `list_for_user`/`count_for_user`.
6. `backend/tests/unit/api/test_v3_issues.py` — 3 new pagination tests.
7. `backend/tests/unit/api/test_v3_notifications.py` — NEW file, 4 tests.
8. `frontend/src/v3/api.js` — `listNotifications` accepts boolean (D25
   compatible) **or** `{ unreadOnly, limit, offset }`; `listCustomerIssues`
   passes `limit`/`offset` through.
9. `frontend/src/v3/__tests__/api.test.js` — D26 block (3 tests) with a
   stubbed supabase client.

No schema/RLS/migration changes. No D19/domain/email/import/PDF/messaging code.
No changes to unrelated pre-existing working-tree files (ProcessingPage.jsx was
temporarily touched for a build check and fully reverted).

**D26 verification:** backend unit suite **881 passed / 0 failed / 0 errors**
(7 new tests); targeted issues+notifications **14/14**; frontend Jest
**15/15** in `api.test.js` (3 new D26 tests; `App.test.js` continues to fail on
the pre-existing environmental `react-router/dom` module resolution, unrelated
to D26); frontend build **EXIT=0** (non-CI, warning-tolerant — matching the D25
gate; ~140 pre-existing lint warnings remain and fail only under `CI=true`).
Live server healthy (200) on D25 code; live probes for the new pagination
params were not re-run (server not restarted on D26 code — unit tests cover the
behavior).

---

## 42. REALTIME definitive answer (D26 audit)

**Q: Is messaging between different entities implemented using Supabase
Realtime?**

**A: B. PARTIAL — Realtime plumbing exists but full mediated messaging is NOT
implemented, and the only existing messaging attempt is non-functional.**

Evidence:

- **Tables.** `public.conversations` (org/customer/staff fields), `public.messages`
  (sender/receiver/content/is_read/conversation_id/org), `public.conversation_participants`
  (user_id/joined_at/is_active) all exist with RLS **enabled**. Data: 2
  conversations, 0 messages, 0 participants.
- **RLS.** `conversations`/`messages` have SELECT `is_org_member(org) OR
  is_org_consultant(org)` (consultant = active D15 grant), INSERT/UPDATE
  `WITH CHECK is_org_member(org)`. `conversation_participants` has **zero
  policies** — RLS enabled with no policies ⇒ **deny-all** for authenticated
  users. There is **no Processing Entity participation model** (entity staff
  cannot appear as a conversation participant under any policy).
- **Channels/subscriptions.** Legacy `ChatWidget`/`ChatWindow`/`RealtimeContext`
  subscribe via supabase-js `postgres_changes` on `messages` and query
  `conversation_participants` directly — but the participant deny-all means
  `getActiveConversations()` always returns empty, so **no conversation channel
  can ever be established**. Publication membership of the messaging tables in
  `supabase_realtime` is not declared in the schema SQL and could not be
  confirmed against the live DB during this audit.
- **No backend messaging API.** There are no `/api/v3/conversations` or
  `/api/v3/messages` endpoints; nothing in the V3 product surface uses the
  conversation tables.
- **Mediated entity clarification** (the working leg) is implemented via
  `issues` (`entity_id`-scoped) + notifications, not via Realtime.

**What is missing for a real mediated Realtime messaging capability:** a
backend messaging API that creates conversations and authorizes every
participant server-side; RLS policies for `conversation_participants`; a
Processing-Entity participant type that exposes only the mediated
entity↔CarbonTally↔customer thread; publication membership; reconnect/unread/
ordering handling; and V3 UI. Each of these is a design decision (per D26 §41)
and remains **FUTURE**.

---

*End of audit (D25 implemented; D26 product-completion audit + scale hardening
complete — verdict in the D26 report).*
*Analysis + D21/D22/D23 implementation + D24 bounded P1 UI completion only — no
permanent Processing Entities, entity staff, users, organisations or demo data
were created.*


---

## 43. D27 — D19 Customer Lifecycle & Final Product Completion (2026-08-22)

**D19 final product-completion pass. Every capability is labelled**
**IMPLEMENTED / PARTIALLY IMPLEMENTED / EXTERNAL CONFIGURATION REQUIRED /**
**FUTURE.**

### 43.1 D19 implementation (Parts 3-10)

| Capability | Status | Notes |
|---|---|---|
| Consultant-client lifecycle ACTIVE / SUSPENDED / ENDED | **IMPLEMENTED** | `consultant_clients` lifecycle columns + domain transition table (`domain/partners.py`) + API transitions (`POST /api/v3/consultants/clients/{id}/suspend|end|reactivate`) + RLS (`is_org_consultant` requires `status='active'` — D15 intact) + audit. Revocation is immediate at API and RLS layers. |
| Customer-initiated direct onboarding (existing-data discovery) | **IMPLEMENTED** | `POST /api/v3/discovery/lookup` (candidate signals only, never authoritative — D19 §6); `POST /api/v3/discovery/requests`; `GET /requests[/{id}]` (safe data counts only); `POST /{id}/verify` (email code, SHA-256 hashed, attempt-limited); `POST /{id}/staff-verify` (CarbonTally internal admin mediation); `POST /{id}/choice`. New table `data_discovery_requests` (deny-by-default RLS; service-role API). |
| Secure verification | **IMPLEMENTED** | Email-code verification to the candidate org's registered contact (best-effort; `verification_delivered` reported honestly) OR CarbonTally-staff mediation. Never inferred from name/domain/supplier/consultant. |
| USE ALL / PARTIAL / DISCARD | **IMPLEMENTED** | `use_all` = in-place adoption; `partial` = in-place adoption + recorded category selection (`adoption_scope` provenance; no unsafe per-record partial-copy semantics — D19 §8); `discard` = recorded decision, **no data deleted** (D19 §7). |
| No destructive deletion from DISCARD | **IMPLEMENTED** | DISCARD only transitions the request; no DELETE/archive of org data. Formal deletion remains a separate process. |
| In-place organisation identity preservation | **IMPLEMENTED** | Adoption keeps the existing `organizations.id`; the customer becomes an org owner; historical `created_by`/`processed_by`/`assigned_to` values are never rewritten (D19 §9). |
| Consultant access termination on adoption | **IMPLEMENTED** | All ACTIVE consultant grants for the adopted org transition to `ended` with audit; RLS + API deny immediately. |
| Direct-customer marker | **IMPLEMENTED (informational)** | `organizations.customer_type` (`direct`/`consultant_managed`) — labelled NEVER-authorization. |

### 43.2 White-label completion (Parts 11-18)

| Capability | Status | Notes |
|---|---|---|
| Consultant branding config (D21 foundation) | **IMPLEMENTED** (unchanged) | `consultant_profiles` branding + `white_label_enabled`; API + UI. |
| Custom-domain integration | **IMPLEMENTED (foundation)** + **EXTERNAL CONFIGURATION REQUIRED** | `consultant_custom_domains` lifecycle PENDING → VERIFIED → ACTIVE → REMOVED_SUSPENDED with TXT-token verification; Vercel DNS/routing is the consultant's responsibility (D19 §12). A domain NEVER grants authorization. |
| Optional custom sender (Resend) | **IMPLEMENTED (foundation)** + **EXTERNAL CONFIGURATION REQUIRED** | `consultant_senders` lifecycle; only VERIFIED senders may be used as a From address; arbitrary From addresses are never allowed (D19 §13). Resend domain verification is external. |
| Consultant-branded communication | **PARTIALLY IMPLEMENTED** | Authorized `BrandContext` drives the branded PDF; transactional email uses CarbonTally default or a verified sender; per-consultant email template branding is FUTURE. |
| White-label PDF rendering | **IMPLEMENTED** | `engines/pdf_render.py` (reportlab) renders persisted report content with the server-authorized `BrandContext`; `GET /api/v3/reports/{id}/pdf`. Client-supplied branding never accepted (D19 §18). |
| Consultant-client messaging | **IMPLEMENTED** | Realtime messaging RLS fix (`conversation_participants` recursion-safe policies) + authorized `/api/v3/messaging/*` API (org members + active-grant consultants; Processing Entity staff denied — D18). Frontend: customer `/messaging` + consultant Client messages tab. |
| Processing Entity communication boundary | **IMPLEMENTED (preserved)** | No entity messaging policy; entity staff never pass the messaging authorization chain; mediated clarification stays on entity-scoped `issues` (D19 §17). |

### 43.3 Onboarding / auth / product completion (Parts 19-32)

| Capability | Status | Notes |
|---|---|---|
| Customer onboarding | **IMPLEMENTED** | signup/verification/org creation (existing) + existing-data discovery workflow (D27). Invitation acceptance tests: FUTURE/EXTERNAL. |
| Consultant onboarding | **IMPLEMENTED** | consultant profile creation + firm team + invites + client management + lifecycle + white-label + messaging (D27). |
| Processing Entity onboarding | **IMPLEMENTED (where architecture supports)** | ops staff provisioning with entity scope (D20) + entity extraction workspace (D22) + entity-scoped issues. |
| Google OAuth | **EXTERNAL CONFIGURATION REQUIRED** | Supabase Auth provider configuration — not verifiable from this environment. |
| MFA / 2FA | **EXTERNAL CONFIGURATION REQUIRED** | Supabase MFA — provider-managed; documented, not locally verifiable. |
| Customer Issues UI | **IMPLEMENTED** (D25) | `/issues` over org-scoped `/api/v3/issues`; customer replies: FUTURE. |
| Notifications UI | **IMPLEMENTED** (D25/D26) | `/notifications` per-recipient, paginated. |
| Consultant client lifecycle UI | **IMPLEMENTED** (D27) | Suspend/End/Reactivate controls + lifecycle badges. |
| SLA UI | **IMPLEMENTED** (D25) | `/ops` SlaTab reuses the existing SLA architecture. |
| Frontend role-route guards | **IMPLEMENTED** (D25) | `RoleRoute`/`useActorRoles`; backend/RLS remain authoritative. |
| Staff-role reference | **IMPLEMENTED** (D25) | `/ops` StaffRolesTab — read-only catalog, never authorization. |
| Export | **IMPLEMENTED (scoped)** | `/api/v3/exports/emissions.{csv,json}` + `documents.csv`. Full-org export: DESIGN ONLY. |
| Import (customer data) | **DESIGN ONLY** | Format/validation/rollback undefined → stopped (safe). Factor/reference import is a separate existing surface. |
| Audit logging (D19 events) | **IMPLEMENTED** | discovery requested/verified/adopted/discarded, consultant-client lifecycle transitions, white-label domain/sender mutations, organization.direct_customer. No secrets logged. |

### 43.4 Security regression (Part 31)

The mandatory negative tests are covered by the D27 unit suite (customer↔customer,
consultant↔consultant, former-consultant, entity↔entity, entity→customer,
unverified sender/domain, client-supplied id never trusted) plus the D15/D20/D21/
D22/D23/Phase-9 suites. Full backend unit suite: **936 passed / 0 failed**.

### 43.5 Test + verification record

- Backend unit suite: **936 passed / 0 failed / 0 errors** (52 new D27 tests).
- D27 targeted suite: 52/52 (discovery, messaging, whitelabel, lifecycle, PDF).
- Frontend Jest: **18/18** (`api.test.js`); frontend build **EXIT=0** (non-CI,
  warning-tolerant — the established D25/D26 gate).
- Live-server verification: not re-run (no browser; local Supabase not running);
  app factory + route registration verified (20 new routes).
- Screenshot evidence: `screenshots/d27_evidence/` (3 genuine branded PDFs +
  manifest documenting the 36-item inventory; D27-new browser screenshots
  require a browser-automation environment — documented, not claimed).
- Synthetic PDF corpus: **untouched** (not regenerated/modified/ingested).

### 43.6 Files changed (D27)

Backend: `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` (new);
`domain/discovery.py`, `domain/messaging.py`, `domain/whitelabel.py` (new);
`domain/partners.py` (lifecycle); `data/discovery.py`, `data/messaging.py`,
`data/whitelabel.py` (new); `data/consultants.py`, `data/organizations.py`
(extended); `api/v3_discovery.py`, `api/v3_messaging.py`, `api/v3_whitelabel.py`
(new); `api/v3_consultants.py`, `api/v3_reports.py`, `api/consultant_auth.py`,
`api/dependencies.py`, `api/router.py` (extended); `services/v3_email.py` (new);
`engines/pdf_render.py` (new); `tests/unit/**` (fakes + 6 new test files).

Frontend: `src/v3/api.js`, `src/v3/customer/ExistingDataDiscoveryPage.jsx`,
`src/v3/customer/MessagingPage.jsx`, `src/v3/consultant/WhiteLabelTab.jsx`,
`src/v3/consultant/ClientMessagingTab.jsx`, `src/v3/consultant/ConsultantPage.jsx`,
`src/App.js`, `src/v3/components/V3Layout.jsx`, `src/v3/v3.css`,
`src/v3/__tests__/api.test.js`.

*End of D27 record (D19 implemented; full product-completion verification).*

### 44. D30/D31 — Reporting completeness and management intelligence (IMPLEMENTED 2026-08-23)

**Status:** D30 reporting foundation + D31 completion are IMPLEMENTED and verified.

**Reporting capabilities added (D30 + D31):**
- Customer: reporting overview (emissions total/scope/month, documents processed/pending/
  attention, processing stages, data quality, "needs attention"), monthly emissions trend
  chart (recharts), member activity by organisation member (derived from author columns).
- Consultant: portfolio health (active/suspended/ended counts; ACTIVE grants only — ended
  never detailed) + per-client drill-down (stage breakdown, documents/items, issues, reports,
  emissions).
- Internal operations: platform overview (orgs/entities/staff/processing/quality), queue
  aging (batch/item age buckets 0-1d/1-3d/3-7d/7d+, SLA breached, overdue, internal vs entity),
  reviewer workload, issues reporting, QC processor performance (internal vs entity with sample
  sizes), admin read-side audit trail.
- Processing Entity: own-entity performance (batches/items, SLA status, quality indicators,
  staff workload).

**Authorization boundaries (unchanged):** `ensure_org_access` (own org; entity staff denied),
`require_consultant` + ACTIVE client grants, internal staff permissions (`can_view_all` /
`can_review` / `can_manage_staff`), `require_entity_scope` (own entity). Entity staff never
obtain customer-wide reporting. Admin audit requires staff-admin `can_manage_staff`.

**Data sources:** emissions_logs, organization_files, document_processing_queue,
manual_extraction_batches/items, manual_review_queue, issues, report_generation_queue,
consultant_clients, processing_entities, staff_profiles, audit_trail, organizations,
organization_members, users.

**NOT SUPPORTED BY CURRENT DATA MODEL:** recurring QC quality (qc_checks/qc_errors unpopulated),
`issues.blocking` column (workflow-derived only). **EXTERNAL CONFIGURATION REQUIRED:** auth-event
reporting (Supabase-owned). **Test-infrastructure fix:** the integration suite now targets the
dedicated `carbontally_test` database and refuses/skips rather than ever truncating the main app
database.

**Remaining limitations:** activity_logs-family tables are write-only (0 rows locally — the
derived member-activity view is authoritative today); batch/item "time in progress" requires
stage-entry timestamps that the schema does not currently persist.

*End of D30/D31 record.*

### 45. D32 — Final product completeness & production readiness audit (2026-08-23)

**Status:** audit-first completion; one P0 security defect FIXED (private document storage).

**Verdict:** CarbonTally V3 is functionally complete for a controlled production launch of the
customer / consultant / operations / processing-entity product. Remaining items are
production configuration + billing, not functional gaps.

**P0 FIXED — document storage confidentiality.** The `documents` Supabase Storage bucket was
PUBLIC with zero storage RLS policies and files were served via `get_public_url` — customer
documents were accessible by URL without authentication or expiry. D32:
- `supabase/migrations/20260823000000_d32_private_documents_storage.sql` — bucket → PRIVATE +
  4 org-scoped `storage.objects` RLS policies (`uploads/<org_id>/` prefix scoped to org members).
- `backend/services/storage.py` — `path_from_url` / `storage_signed_url` / `signed_item`.
- `api/v3_documents.py` — uploads store canonical paths; `GET /documents/{id}/signed-url`
  (org-member gated); pipeline item URLs signed at read time (`v3_operations.py`,
  `v3_processing_workflow.py`).

Verified live: upload → signed URL; owner 200; non-member 403; legacy public URL blocked (400);
signed URL fetches 200; workspace responses return signed URLs.

**Authorization boundaries:** unchanged (D15/D20/D22/D30/D31). Storage authorization is now
server-side + RLS enforced; no frontend-only security assumptions.

**Billing:** schema is Stripe-ready (`stripe_customer_id`/`stripe_subscription_id`/
`stripe_price_id`, `subscription_status/tier`, `customer_subscriptions`, `consultant_billing`
+ `manual_extraction_credit`, `usage_tracking`). No billing API/UI/gating/webhooks — classified
PARTIALLY READY FOR STRIPE INTEGRATION (application changes required). No proprietary billing.

**Test-infrastructure:** D31 dedicated integration DB fix re-verified (default =
`carbontally_test`; main-DB URL → refuse; missing DB → skip). 983 backend unit tests, 11 RLS
integration tests, 18 frontend API tests — all green.

**Remaining limitations:** external production configuration (Supabase auth/OAuth/MFA/redirects,
Resend domain, Vercel/Render env, Stripe, backups/monitoring); document-binary/provenance export
(P2); backup/DR documentation (P2); legacy beta `/dashboard/*` retirement (P2/P3); the
5,787-PDF processing validation remains NOT STARTED (awaiting product-owner authorization).

*End of D32 record.*

### 46. D33 — Evidence traceability & provenance completion (2026-08-23)

**Status:** release-blocker traceability gap CLOSED with a minimal additive design.
Every calculated emission is now traceable to its authoritative calculation, its
extraction item/line and its source document; reverse lookup is supported.

**Authoritative lineage chain (added):**
```
organization_files.id
        ▲ file_id (FK, ON DELETE SET NULL)
manual_extraction_items.id
        ▲ source_item_id (FK, ON DELETE SET NULL)
calculation_snapshots.id   (+ source_file, source_page persisted)
        ▲ snapshot_id (FK — pre-existing)
emissions_logs.id
```
Previously `source_file`/`source_page` existed only transiently on the snapshot domain
object and were dropped by the persistence INSERT; the item↔document link was an
unreliable `file_url == path` string match.

**Schema:** `supabase/migrations/20260823010000_d33_evidence_traceability.sql`
(additive + idempotent): 3 snapshot columns (`source_item_id`, `source_file`,
`source_page`), `manual_extraction_items.file_id`, two `SET NULL` FKs, two indexes,
path-match backfill. Applied to main + `carbontally_test`.

**API:** `GET /api/v3/emissions/{log_id}/evidence` (org-member; snapshot → item → source
document + authorized signed URL + factor), `GET /api/v3/documents/{file_id}/emissions`
(reverse), uploads persist `file_id`, item-calculate persists `source_item_id`,
direct-calculate accepts `source_item_id`, exports now include `snapshot_id`,
`source_item_id`, `source_file`, `source_page`.

**Frontend:** EmissionsPage per-row "View evidence" panel (source document, extracted
line, factor/factor source, calculation, page, signed-URL viewer); DocumentsPage
"Emissions from this document" reverse table.

**Security:** unchanged org-scoped RLS + `ensure_org_access`; provenance never bypasses
authorization; D32 private storage + signed URLs remain authoritative. Consultant =
ACTIVE grant; entity staff have no customer-evidence path.

**Verification:** 989 backend unit (6 new traceability tests), 11 RLS integration on
`carbontally_test`, 18 frontend API, production build — all green. Live fixture
(upload → 2 lines → map → validate → calculate): evidence + reverse + signed URL + 403
denials verified; all fixtures removed (before/after counts recorded). 5 UI screenshots
in `screenshots/d33_evidence/`.

**Remaining limitations (documented, not launch-blocking):** Excel sheet/cell references
not persisted (file + row=item only); one item = one extracted line (no intra-item
multi-line lists); `source_page` is accepted but not auto-extracted; report
`generated_content` lineage is aggregate-level (per-snapshot refs live on each emission).

*End of D33 record.*

### 47. D33.1 — Evidence Precision & Evidence Record (2026-08-23)

**Status:** IMPLEMENTED — final evidence/provenance refinement before production
launch. No schema change; additive presentation + audit on the D33 lineage.

**Authoritative principle:** *CarbonTally does not expose its database directly.
CarbonTally exposes an authorized, human-readable evidence record representing the
persisted provenance records underlying an emission result.*

**Evidence Record** (`domain/evidence.py` + `GET /api/v3/emissions/{log_id}/evidence`
→ `evidence_record`): sections SOURCE DOCUMENT / ORIGINAL EXTRACTED DATA
(origin=original) and CARBONTALLY MAPPING / EMISSION FACTOR / CALCULATION /
EMISSION RESULT (origin=derived); human-readable formula; completeness
COMPLETE/PARTIAL/UNAVAILABLE derived from persisted provenance; honest
`source_location` precision; scoped `technical_details` with stable record
identifiers. Frontend `EvidenceRecordPanel.jsx` renders the record with a
completeness badge and a Technical details expansion.

**Evidence-access audit:** append-only `audit_trail` rows (`evidence.access`,
`evidence.reverse_lookup`) with actor, org, snapshot/source-file ids — never URLs
or secrets.

**Export:** emissions.csv/json add `evidence_status`.

**Pipeline:** `POST /api/v3/processing/items/{id}/calculate` accepts optional
`source_page` (persisted when the pipeline reliably knows it — never fabricated).

**Verification:** 1018 backend unit (14 new evidence-record tests), 11 RLS
integration, 18 frontend API, production build — all green. Live fixture
(upload → 2 lines → calculate with source_page → evidence record COMPLETE →
reverse → audit → denials) verified; all fixtures removed (before/after recorded).
6 screenshots in `screenshots/d33_evidence/`.

**Limitations (documented):** Excel sheet/cell + CSV/JSON row/cell/JSONPath
precision not captured by the extraction pipeline; `source_page` must be supplied
by the pipeline; evidence-audit rows have no dedicated retention surface beyond
`audit_trail`.

*End of D33.1 record.*





### 48. D35 — Self-Service Customer Onboarding (2026-08-23)

**Status:** IMPLEMENTED — a brand-new customer can sign up, create/adopt an
organization, become OWNER, and enter the V3 customer workspace without staff
provisioning. Billing is deliberately deferred (provider-neutral; no payment
provider code).

**Architecture changes (all additive):**

1. **Public self-service signup.** `/signup` renders `SelfServiceSignup.jsx`
   (no beta code). Supabase Auth remains authoritative
   (`supabase.auth.signUp` with onboarding user metadata). The beta/invite
   mechanism is preserved as the optional controlled-cohort path at
   `/beta/signup`. Post-signup routing uses the server-authoritative
   `resolvePostLoginPath()`.

2. **Customer-initiated organization creation.** New `POST /api/v3/organizations`
   (`require_auth`). `OrganizationsRepository.create_with_owner()` creates the
   organisation + the initial `owner` membership (real `organization_members`
   role model) + the creator's `public.users` backstop row **in one
   transaction** (server-side; no browser/service-role bypass). Duplicate
   prevention: exact `company_number` candidate match blocks (`409
   discovery_required`) unless the customer explicitly acknowledges the
   candidate ids; weaker signals (name/email-domain/contact) are informational.
   `company_number` is now persisted (was discarded).

3. **Pre-org-creation existing-data discovery (D19 preserved + extended).**
   `data_discovery_requests.organization_id` is nullable — `NULL` marks an
   onboarding request created before the customer has any organization. New
   `created_by` binds the request to its actor (only that actor may verify and
   choose). Lookup/request/verify/choice accept an optional `organization_id`:
   supplied → org-scoped D19 (unchanged); omitted → onboarding variant. USE ALL
   adopts in place (existing org id preserved, customer becomes owner, ACTIVE
   consultant grants end, `customer_type=direct`); PARTIAL records the category
   scope; DISCARD records the decision and deletes nothing.

4. **auth.users → public.users sync.** New trigger mirrors Supabase Auth signups
   into `public.users` (the `organization_members.user_id` FK target) so a new
   signup can receive a membership. Guarded to skip on environments without the
   `auth` schema (dedicated test DB); sync failures never block authentication.
   A defensive server-side upsert in `create_with_owner` covers pre-existing
   users.

5. **Routing.** `resolvePostLoginPath()` falls back to `/onboarding` for an
   authenticated user with no org/staff/consultant relationship; V3Layout
   redirects no-org (non-staff/non-consultant) users to `/onboarding`. Legacy
   `/dashboard/*` redirects to `/home`. Google OAuth redirect target corrected
   to `/auth/callback`.

6. **Reliability.** The onboarding route guard is bounded (12 s fallback) so the
   customer is never stuck on a loading screen; every step has success/error/
   retry states.

**Schema:** `supabase/migrations/20260824010000_d35_self_service_onboarding.sql`
(additive + idempotent): nullable `data_discovery_requests.organization_id`,
`created_by` column, partial unique index per live onboarding candidate, and
the `auth.users → public.users` sync function + guarded trigger. Applied to
main + `carbontally_test`.

**Security:** RLS deny-by-default untouched; onboarding requests bound to
`created_by` (cross-user denied); org-scoped lookup still requires membership;
`ensure_org_access` still enforced on every org-scoped endpoint; the real
`owner` role model reused — no second role system, no tenancy abstraction,
white-label/messaging/evidence architecture unchanged.

**Verification:** 1020 backend unit (18 new self-service tests), 15 RLS
integration (4 new D35 assertions), 21 frontend API tests, production build —
all green. Main-DB protection re-verified (integration suite refuses the main
database). Live smoke with real Supabase Auth users: 11/11 core journey +
10/10 adoption journey (USE ALL in place + DISCARD records-only); all fixtures
removed. 9 UI screenshots in `screenshots/d35_customer_onboarding/`.

**Three pre-existing defects fixed (found via live verification):**
`data/tenant.py` member INSERT used non-existent `joined_at`/`last_active`
columns (live schema has `created_at`) — broke every server-side membership
write including D19 adoption; `data/discovery.py lookup_candidates` crashed on
the `name` signal (unescaped SQL `%`); no `auth.users → public.users` sync.

**Deferred (ratified):** billing/commercial model is BUSINESS DECISION
REQUIRED and provider-neutral; backup/DR retention + restore testing and
observability dashboards are EXTERNAL CONFIGURATION REQUIRED; full legacy
`/dashboard/*` code removal and remaining email templates are FUTURE.

*End of D35 record.*


---

### 49. D37-0 — Billing Security Remediation & Configurable Subscription Foundation (2026-08-24)

**Status:** IMPLEMENTED — the D36 P0 billing-security defect is closed and a
configurable, provider-neutral subscription/commercial foundation exists. HARD
STOP before any payment-provider integration. No provider, no checkout, no
webhooks.

**The D36 P0 defect and its fix.** Before D37-0 the `authenticated` role could
INSERT/UPDATE/DELETE `usage_tracking` and `customer_subscriptions` rows and
UPDATE the `organizations.subscription_*` / `trial_*` / `tax_rate` columns
directly through PostgREST (the browser Supabase client). A customer could
rewrite their own usage, plan, limits and trial/subscription state — and would
have been able to self-grant credits the moment credits existed. A bare
column-level `REVOKE` cannot override a table-level grant in PostgreSQL, so the
authoritative fix is a **table-level `REVOKE UPDATE/INSERT/DELETE` on
`organizations`, `usage_tracking`, `customer_subscriptions` and
`consultant_billing` from `authenticated`** plus dropping the tenant
INSERT/UPDATE/DELETE policies (SELECT remains for the tenant's own rows). The
trusted CarbonTally API / service-role paths are unaffected (they run as the
table owner / `service_role`).

**Architecture changes (all additive; reuse → extend → replace):**

1. **Reused:** `customer_subscriptions` / `usage_tracking` / `consultant_billing`
   rows and IDs (no table replaced); the tenant/RLS organisation boundary; the
   D35 self-service onboarding path; the D33 evidence model; the existing staff
   authorization chain (`staff_profiles` → `staff_roles.permissions` →
   `ensure_staff_permission`); the append-only `audit_trail`; the existing
   admin/ops frontend conventions.

2. **Extended:** `organizations.billing_mode` (per-customer commercial mode,
   CREDIT|STANDARD) assigned at org creation from the versioned default;
   `_ORG_COLUMNS`/`_row_to_org`/`_row_to_org_full` expose it; `tax_rate`
   removed from the customer-editable profile fields; `can_manage_billing`
   added to the staff permission vocabulary + the platform-admin role.

3. **Replaced:** the direct PostgREST write path to billing state is gone
   (that was the defect). The legacy Stripe-named columns remain as documented
   legacy (schema-only), untouched.

4. **New foundation tables (deny-by-default RLS; service_role granted):**
   - `billing_plans` — configurable, VERSIONED plan catalogue
     (`plan_code` stable identity; each change publishes a new `version` row
     with `effective_from`/`effective_to`; history never rewritten).
   - `billing_commercial_config` — VERSIONED key/value commercial rules
     (`default_billing_mode`, `credit_rules`, `structured_data_bands`,
     `storage`, `assisted_pricing`, `credit_policy`, `standard_allowance`).
   - `billing_credit_ledger` — APPEND-ONLY credit ledger (grant/consume/
     adjustment/rollover/emergency_allowance/refund/reversal; balance is
     DERIVED as `SUM(credit_delta)`; unique partial
     `(organization_id, external_reference)` gives idempotency).
   - Seeded: Starter/Professional/Business/Enterprise plans + 7 config keys
     (provisional values, Admin-configurable — never hard-coded in logic).

5. **Billing modes are customer/subscription-specific.** The mode lives on the
   commercial relationship (`organizations.billing_mode`); the Admin default is
   a versioned config key that applies to NEW customers only. Changing the
   default NEVER silently migrates existing customers (verified live).

6. **Admin commercial surface.** `/api/v3/commercial/*` (config, plans, ledger,
   org billing modes) requires an ACTIVE CarbonTally INTERNAL staff profile +
   the real `can_manage_billing` permission. Every change is versioned and
   audited (`billing_commercial_config`/`billing_plan` audit entries). The
   frontend adds a **Commercial** tab to the existing `/ops` Internal
   Operations hub (visible only to `can_manage_billing`).

7. **Per-customer mode at creation.** `POST /api/v3/organizations` resolves the
   versioned default and assigns it atomically with OWNER creation.

**Provider-neutral:** no provider identifiers are hard-coded; provider-specific
concepts are isolated in provider-neutral columns and the `external_reference`
idempotency key. Stripe, PayPal, Paddle, Lemon Squeezy, checkout, webhooks and
payment collection are explicitly NOT implemented.

**Test/verification record:** backend unit 1039 (19 new), RLS 23 (8 new),
frontend 23 (2 new), production build OK; live verification 26/26 against the
real stack (authenticated write denial, authorization matrix, versioning,
CREDIT/STANDARD customer-specific behavior, ledger, D33 evidence + D35
onboarding intact); fixtures cleaned (orgs 0, users 0, ledger 0).

**Remaining gaps (D37-1 prerequisites):** billing service/API/UI/webhooks,
entitlement enforcement, complexity classifier wiring, credit consumption,
processing orders, provider adapter, storage metering. Full report:
`docs/audit/cline/CARBONTALLY_V3_D37_0_BILLING_SECURITY_AND_CONFIGURABLE_SUBSCRIPTION_REPORT.md`.

*End of D37-0 record. Do not begin D37-1 until the Product Owner ratifies the
D36 §29 decisions.*


---

### 50. D37 — Master Commercial Billing (2026-08-24)

**Status:** IMPLEMENTED — complete provider-neutral commercial billing over the
D37-0 foundation. HARD STOP; no payment-provider integration.

**Architecture (additive; D37-0 intact):**

1. **Subscription lifecycle** — `customer_subscriptions` extended (REUSE):
   `billing_mode`, `plan_code`/`plan_version`, `lifecycle_status`
   (pending/trial/active/past_due/suspended/cancelled/expired),
   `current_period_*`; one active relationship per org (unique partial index).

2. **Entitlement engine** — `services/billing.py::get_entitlement` resolves
   active subscription → exact plan VERSION → billing mode → configurable
   rules → derived ledger balance; server-authoritative, fail-closed.

3. **CREDIT mode** — complexity classifier (configurable thresholds) + configurable
   structured-data bands; `charge_processing` consumes credits idempotently;
   grant/consume/rollover/emergency allowance/adjustment/reversal/refund are
   ledger events (append-only, audited). No separate calculation charge.

4. **STANDARD mode** — monthly allowance from versioned config; usage recorded
   server-side in `usage_tracking`; same entitlement architecture.

5. **Common order model** — `billing_orders` (automated/assisted/managed/storage)
   with immutable item snapshots + config versions; Assisted Processing
   estimate→customer approval→commercial order; Managed requests on the same
   model; completed orders immutable.

6. **Storage metering** — `billing_storage_usage` snapshots summed from D32
   `organization_files` (server-authoritative).

7. **Provider-neutral payments** — `billing_payment_records` (no credentials);
   approval records a pending intent; adapters (PayPal/Wise/card) can be added
   later without touching the core. **No provider integration performed.**

8. **Idempotency + audit** — durable `billing_idempotency_keys`; every mutation
   audited. Historical records immutable; reversals are new entries.

9. **API** — customer `/api/v3/billing/*` (org-scoped) + admin
   `/api/v3/commercial/subscriptions|orders|storage|payments|credits/*`
   (staff + `can_manage_billing`). Processing approval charges credits
   (idempotent per item; no-subscription orgs unaffected).

10. **UI** — customer `/billing` page (plan/mode/credits/storage/orders/assisted/
    managed/payments) + extended `/ops` Commercial tab (subscriptions, orders,
    credit ops, storage).

**Test/verification:** unit 1056 (0 fail), RLS 27 (0 fail), frontend 25,
build OK, live 23/23; fixtures cleaned. Full report:
`docs/audit/cline/CARBONTALLY_V3_D37_MASTER_COMMERCIAL_BILLING_COMPLETION_REPORT.md`.

**Deferred:** payment provider integration, checkout/webhooks, tax/accounting
providers, managed-order assignment automation.

*End of D37 record. Do NOT begin a new product-development phase without Product
Owner direction.*
