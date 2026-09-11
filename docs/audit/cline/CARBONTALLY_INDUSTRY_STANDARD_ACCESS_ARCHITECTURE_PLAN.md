# CarbonTally — Industry-Standard Application & Access Architecture Plan

> **Type:** Phase 1 — architecture compliance, gap analysis and implementation plan (read-only).
> **Date:** 2026-09-01
> **Git HEAD:** `16391217103b98dcea520070c5a22c68f12fe607` (branch `main`)
> **Mode honoured:** no application/database/migration/RLS/package/config/test/Docker/deployment
> changes; no commits/pushes. Only this report file is created.
> **Method:** evaluates the current, live-verified CarbonTally architecture against current
> enterprise/industry principles — primarily **NIST SP 800-207 (Zero Trust Architecture)** and
> **NIST SP 800-207A**, OWASP Zero-Trust and authorization guidance, least privilege, separation
> of duties, defense in depth, data minimization and secure API design. This is an **architecture
> alignment assessment, not a certification**.
> **Key posture:** URLs (`/app`, `/consultant`, `/ops`, `/admin`, `/pe`) and deployment topology
> are **CarbonTally design choices**, not standards. The standards are the principles
> (identity-based authorization, resource-level enforcement, least privilege, separation of
> duties, trust-boundary separation).

---

# 1. Executive Summary

CarbonTally's core security architecture is **already strongly Zero-Trust-aligned**:

- Authorization is **identity-based** (Supabase Auth → `get_current_user`), **tenant/entity-based**
  (organization, consultant-firm, processing-entity access axes), and **resource/action-based**
  (RLS + `require_*` guards + per-item/per-batch re-authorization).
- The **PE boundary is verified sound** at three layers (RLS `is_entity_member` + 7 entity
  policies; API `require_staff` + `require_entity_scope`; auth `require_admin` hard-blocks
  `is_entity_staff`). Live probes confirmed 403 for PE→customer-org list, PE→foreign entity,
  PE→messaging. **No security defect found → the boundary must be preserved, not redesigned.**
- **No network/geographic/location-based authorization exists** — compliant with the
  Zero-Trust requirement that IP/geo/subnet/URL/route are never the primary authorization
  boundary.
- The frontend is explicitly never the security boundary (route guards are UX only; backend +
  RLS enforce).

The principal **gaps** are architectural/compliance items, not PE security defects:

1. **Frontend trust-domain separation is incomplete** — PE, Staff, and parts of Admin share one
   shell (`V3Layout`) and one route table; the PE application is not a distinct surface. Zero
   Trust's "micro-segmentation" is well-enforced at the *data/API* layer but not reflected at the
   *application-surface* layer.
2. **The legacy `admin/` CRA reads Supabase directly**, bypassing the FastAPI application
   boundary — a genuine trust-boundary violation (quarantined per CL-66, but still present).
3. **No token audience/scope separation** across applications — one bearer token is valid for
   every API surface; resource guards compensate, but audience-scoped tokens (or an equivalent
   server-side surface claim) would harden cross-application control.
4. **FORCE RLS is deferred** (known decision) — tenant policy currently depends on application
   service-role access + explicit authorization; the RLS layer is present but not force-toggled.
5. **Document preview defect** (signed-URL download scope) is a P1 backlog item — it does **not**

---

# 2. Industry Principles Used

| Principle | Source | CarbonTally meaning |
|---|---|---|
| Zero Trust — no implicit trust by network location | NIST SP 800-207 §3.1.1 | Authorization depends on identity, tenant/entity, role, resource, action, assignment, session/policy — never IP/geo/subnet/URL/route |
| Continuous, per-request authorization | NIST SP 800-207 §3.1.2 | Every protected API re-authorizes (org guards, entity guards, per-item/batch checks) |
| Policy based on identity + context (800-207A attributes) | NIST SP 800-207A | Actor attributes (staff/entity/consultant), resource ownership, assignment/scope are the policy inputs |
| Least privilege | NIST 800-207; OWASP | Staff vs Admin vs PE vs Customer permission separation; `can_*` permission keys; entity scoping |
| Separation of duties | OWASP; NIST | QC ≠ customer approval; Operator ≠ Reviewer; PE ≠ CarbonTally staff; Operations ≠ Administration |
| Resource/data-level authorization | OWASP Authorization Cheat Sheet; RLS | RLS policies on every tenant table; row-level denials; exactly-one-source snapshot checks |
| Defense in depth | NIST | RLS + API guard + auth guard + frontend UX guard (frontend never the boundary) |
| Data minimization | NIST; GDPR | PE-visible data classified (REQUIRED / OPTIONAL / MASKED / NEVER) for the future privacy layer |
| Secure API design | OWASP API Security | Consistent error envelope, `limit/offset` pagination, server-authoritative calculation |
| Secure document access | ZTA data-plane | Private bucket, short-lived signed URLs, authorize-before-issue, no-download for PE |

---

# 3. Current Architecture

- **Backend:** one FastAPI app (`main.py`) mounting legacy routes (~405 endpoints) + the V3
  router (220 V3 + 17 V2 OpenAPI paths; 290 V3 route decorators); layered
  routers → repositories (36) → domain (25) → engines (12); service-role asyncpg pool.
- **Auth:** Supabase Auth; `backend/auth.py` `get_current_user` + `require_org_member` /
  `require_org_admin` / `require_staff` / `require_admin` (hard-blocks `is_entity_staff`) /
  `require_entity_member`; ops-specific `operations_auth.py` (`StaffContext`,
  `require_internal_staff`, `require_entity_scope`).
- **Context:** single authoritative `GET /api/v3/me/context` → `actor_type` ∈
  `customer | staff | entity_staff | consultant | new_user` + `destination`.
- **Database:** Supabase Postgres; RLS via SECURITY DEFINER helpers (`is_org_member`,
  `is_org_consultant`, `is_org_admin_or_owner`, `is_entity_member`, `is_org_active`); 41
  migrations; 7,049 emission factors verified intact.
- **Frontend:** one CRA (`frontend/`) for public + all authenticated surfaces (`V3Layout`
  role-aware shell); separate legacy CRA (`admin/`, quarantined, bypasses FastAPI); D21
  hand-rolled UI primitives (`v3/components/ui/*`); DataTable; D19 workbench.
- **Storage:** private `documents` bucket; short-lived signed URLs; authorize-before-issue.

   weaken the PE no-download boundary, but it must be fixed before any PE preview milestone.
6. **PE role vocabulary is not product-separated** (PE Manager vs PE Staff via one
   `staff_roles.name`); a PE-side role model is a PO decision.
7. **Legacy API surface** (~405 endpoints) remains mounted — a Zero-Trust "attack-surface
   minimization" gap, removal gated on dependency inventory.

**Target:** six application surfaces (Public, Customer, Consultant, **PE**, Operations, Admin)
sharing one identity system, one V3 API domain layer, and one D21 UI foundation, with a
deliberate **PE API contract** (`/api/v3/pe/*` or equivalent), server-side-only authorization, and
a deployment topology that can later split PE (and others) onto independent hostnames/deployments
without redesigning the core domain. **Nothing in this plan reinterprets PE as a customer or as
CarbonTally staff.**

# 4. Current PE Boundary (verified — PRESERVE)

| Layer | Mechanism | Status |
|---|---|---|
| Model | `processing_entities` (dedicated); `staff_profiles.entity_id` (NULL = internal); `manual_extraction_batches.entity_id` (D22 assignment, one party per batch) | ✅ |
| RLS | `is_entity_member` + 7 entity SELECT policies (`processing_entities`, `staff_profiles`, `manual_review_queue`, `manual_extraction_batches`, `manual_extraction_items`, `upload_batches`, `issues`) | ✅ |
| API | `require_staff` → `require_entity_scope(context, entity_id)` on all 14 `/api/v3/ops/entities/*` endpoints; `ensure_batch_operator_access` | ✅ |
| Auth | `require_admin` hard-blocks `is_entity_staff` (D20 scope-first fix implemented) | ✅ |
| Verified denials | PE→`/ops/organizations` 403; PE→foreign entity dashboard 403; PE→org messaging 403 | ✅ |
| Documents | signed URLs only; `allowDownload=false` for PE; no-download server-side | ✅ (preview defect = P1 UI item, not a boundary breach) |

**Verdict: the PE backend boundary is sound. It is preserved unchanged by this plan.** The
frontend separation (PE application surface) is the change, and it does **not** require touching
RLS, migrations, the entity model, or the PE authorization helpers.

---

# 5. Current Customer Boundary

Org-scoped (`is_org_member`) read + owner/admin mutation + owner/admin approval gates; org
master data, documents, processing, emissions, reports, billing, messaging under
`/api/v3/*` (org-scoped). Verified: customer surfaces return 200 for the demo owner; cross-customer
denials enforced by RLS + org guards. Customers cannot reach PE/staff/admin surfaces (route
guards redirect; backend denies).

---

# 6. Current Consultant Boundary

Firm-scoped (`consultant_firm_members` + `client_access` array) + per-client re-authorization
(`ensure_consultant_org_access`, `_checked_client`) on `/api/v3/consultants/clients/{id}/*`.
Consultant clients do not log in (D31). Revocation by Owner/Admin/Manager only; revocation never
deletes data (WS6/SEC-0003).


---

# 7. Current Staff Boundary

`require_staff` + `require_internal_staff` + `can_*` permission keys (operator/reviewer/
qc/admin/system_admin) over `/api/v3/ops/*`; canonical Operations app `/ops` (D-P2-02). Staff
admin can assign PE work; QC cannot approve customer reviews (D-P2-03).

---

# 8. Current Admin Boundary

Two surfaces: (a) legacy `admin/` CRA — **direct Supabase reads, bypasses FastAPI** (quarantined
per CL-66; not running locally); (b) modern admin tabs inside `/ops` (`require_admin`:
Commercial, QC, Issues, Audit, Settings, Staff/Roles/Entities/SLA). The `/admin`-vs-`/ops`
ruling is PO-pending (decision register §39).

| Independent deployment | ZTA enterprise deployment | Application boundaries allow separate hostnames/deployments without domain redesign |
| Attack-surface minimization | NIST; OWASP | Legacy routes to be removed after dependency inventory; PE API exposes only PE-appropriate actions |

Explicitly **NOT** standards: `/admin`, `/ops`, `/pe` URLs; specific subdomains; any single
deployment topology. Those are CarbonTally design choices derived from the principles.

---

# 9. Target Application Architecture

Six distinct application/trust surfaces (URLs are illustrative CarbonTally choices):

| Surface | Route (candidate) | Trust/role justification | Deployment independence |
|---|---|---|---|
| Public | `/` | unauthenticated marketing/visitor | vercel frontend |
| Customer | `/app` (or current flat routes) | org tenant roles owner/admin/member/viewer | app.carbontally.co.uk (future) |
| Consultant | `/consultant` | firm roles + client grants | consultant.carbontally.co.uk (future) |
| PE | `/pe` | entity staff/manager/owner; third-party processor | pe.carbontally.co.uk (future) |
| Operations | `/ops` | CarbonTally staff; internal pipeline | ops.carbontally.co.uk (future) |
| Admin | `/admin` | CarbonTally platform control plane | admin.carbontally.co.uk (future) |

Justification for separation (per the task): each surface differs in **trust boundary** (internal
vs external), **role**, **responsibility** (operations vs governance vs processing),
**data access** (org/entity/system), **security risk**, **operational function**, and **future
deployment independence**. Separation is justified; collapse would only be "technically easier".
But separation is **application/shell/navigation**, not duplicated logic or a new component
system.

---

# 10. Target API Architecture

```
PE Application        Operations App        Customer App      Consultant App      Admin App
   │                      │                    │                  │                  │
   ▼                      ▼                    ▼                  ▼                  ▼
 /api/v3/pe/*      /api/v3/ops/*        /api/v3/* (org)    /api/v3/consultants/*  /api/v3/* (admin)
   │                      │                    │                  │                  │
   └──────────────────────┴────────────────────┴──────────────────┴──────────────────┘
                                        ▼
                        domain/services/engines (SHARED, single copy)
                                        ▼
                                        repositories → PostgreSQL
```

- **Different access contracts, shared domain logic.** No duplicated business logic.
- **PE API boundary (`/api/v3/pe/*`):** a deliberate thin router exposing **only** PE-appropriate
  resources/actions, reusing the existing entity-scoped services. It may call the same domain
  functions as `/api/v3/ops/entities/*`; it must not re-implement them.
- **Classification of current `/api/v3/ops/entities/*` endpoints (14):**
  - *Become PE API* (entity-staff-operated): `entities/{id}/dashboard`, `extraction/batches`,
    `extraction/batches/{id}`, `extraction/batches/{id}/items`, `extraction/items/{id}`,
    `mapping-options`, `next-item`, `start|extract|map|calculate|status|clarify`.
  - *Remain Operations-internal* (CarbonTally staff/admin): `GET /entities` (list/CRUD) —
    PE management stays in Operations (CarbonTally controls assignment).
  - *Shared domain services:* the extraction/mapping/calculation engine calls are common; the PE
    router and the ops router both call them (e.g. `services/automatic_extraction`,
    `engines/calculation`) — **single implementation**.
  - *Retired later:* duplicate/dead families (e.g. `/api/v3/admin/review-queue` with zero
    consumers) per the earlier forensic findings.
- **No new `ops` duplication:** `/api/v3/pe/*` is an access-contract layer over existing domain
  logic, not a copy.

---

# 11. PE Architecture


---

# 12. Operations Architecture

Operations application `/ops` (unchanged canonical staff app): assignment, extraction ops,
processing queues, mapping, validation, review, QC, exception handling, PE assignment/
coordination, operational messaging, workflow monitoring. Operations does **not** automatically
grant platform-administration authority (separate Admin surface, §13). PE branch moves out of
`OperationsPage` into `/pe` (non-destructive migration).

---

# 13. Admin Architecture

Dedicated administrative control plane `/admin` (candidate) for platform functions:
organizations, users, roles, staff, consultants, PEs, platform config, factor administration,
billing config, retention config, security/audit, feature settings. Separation from Operations is
justified by least privilege, separation of duties, operational risk and platform governance.
**Implementation is deferred until the PO ruling** (decision register §39); the structural
separation is designed now (dedicated shell + page set on the V3 API), and the quarantined legacy
`admin/` CRA (direct-Supabase) must be retired as part of this — it is the only surface that
bypasses the application boundary.

---

# 14. Customer Architecture

Customer application (current flat routes or `/app` prefix): org isolation, role authorization,
customer routes/API scope, document access, reports, approvals, users/team, settings. Customers
cannot enter PE/Operations/Admin except through explicitly authorized controlled transitions
(none today).

---

# 15. Consultant Architecture

Consultant application `/consultant`: firm org, consultant users, client relationships, roles,
client-scoped authorization, API access, customer-data boundaries. Consultant access never grants
Admin/Staff/PE access (verified by separate guard families).

---

# 16. Authentication

- **One coherent identity system (Supabase Auth).** No separate user databases for separate
  frontends.
- Session handling, role detection (`/api/v3/me/context`), org/entity context, logout, session
  expiry: existing and shared.
- **Token audience/scope (evaluation):** today one bearer token is accepted by every API surface;
  guards are the authority. Options to harden (not required for correctness):
  - (a) per-application audience claim/scope claim in JWTs, validated by the PE API router and
    other routers; or
  - (b) a server-side "surface" check — e.g. the PE router additionally asserts
    `is_entity_staff` (already true via `require_staff`+`require_entity_scope`), and customer
    routers assert org membership.
  - Recommendation: option (b) is the smallest safe change and already effectively in place;
    option (a) is a future hardening item. **A PE user gains no privilege by navigating to another
    application's URL** (verified backend behaviour).
- MFA readiness: authenticator-app TOTP is part of the architecture (AGENTS.md §69); production
  enforcement is a deployment/policy decision.
- Privileged-admin authentication: `require_admin` + `ADMIN_ROLE_NAMES`; entity staff hard-blocked.
- PE authentication: same Supabase identity; entity staff do not obtain staff/admin/ops privileges
  (verified).

---

# 17. Authorization

Three levels, all server-side:

| Level | Mechanism | Evidence |
|---|---|---|
| Identity (who) | `get_current_user` (Supabase JWT) | ✅ |
| Organization/entity (which tenant) | `is_org_member`, `is_org_consultant`, `is_entity_member`; `require_org_access` | ✅ |
| Resource/action (what exactly) | RLS row policies + `require_org_admin`, `require_entity_scope`, `ensure_batch_operator_access`, per-client re-authorization, permission keys | ✅ |

- Backend enforcement: ✅ (routers guard every endpoint).
- RLS enforcement: ✅ (tenant tables + entity storeys).
- Assignment-level authorization: ✅ (`ensure_batch_operator_access`, `require_entity_scope`).
- Horizontal privilege escalation (customer A→B, PE A→B): ✅ denied (RLS + guards; live 403s).
- Vertical privilege escalation (entity→admin, member→admin): ✅ `require_admin` blocks
  `is_entity_staff`; `require_org_admin` gates org admin.
- Cross-tenant / cross-PE: ✅ verified.
- Frontend menu/button hiding: explicitly NOT security (UX only; backend is authority).

---

# 18. RLS

---

# 19. Document Security

- Private `documents` bucket; short-lived signed URLs; authorize-before-issue; PE no-download
  (server-side + UX `allowDownload=false`).
- **Original customer document vs PE-visible processing document:** today PE sees a signed view of
  the assigned source item. The plan requires: PE receives **only** the PE-visible signed render;
  never unrestricted original-document URLs; future sanitized/redacted derivatives.
- **Backlog item (P1):** the signed-URL download-scope defect — fix `storage_signed_url` to issue a
  render-scope URL and align the iframe sandbox (or render via `react-pdf`). Not a security
  boundary breach; a preview defect.

---

# 20. PE Privacy (future layer — NOT implemented in this phase)

Design intent only: PE-visible aliases (`CT-CLIENT-004821`, `CT-DOC-771923`, `SUPPLIER-019`),
pseudonyms, sanitized derivatives, redaction, minimum-necessary metadata. Mapping stays inside
CarbonTally; PE cannot reverse aliases via API/DB. **What a PE genuinely needs to perform
extraction (information classes):** the document content (or sanitized derivative), quantity/unit
fields, date, document type, page count, work status, assigned work identifier. **It does NOT
need:** customer name/contact, supplier identity beyond what appears in the document, org
settings, other customers' data, messaging channels to customers, CarbonTally-internal
operations data. This classification (§25) is the foundation for the future phase.

---

# 21. UI Design System

All applications share the **D21 foundation** (`v3/components/ui/*` + tokens). No separate PE
component ecosystem; no shadcn/ui unless explicitly approved after review. Standardization
targets: Button, Input/Select/TextArea, Form, Dialog, Drawer, Card/Badge, Tabs (adopt
`ui/Tabs.jsx`, currently 0 consumers), Loading/Error/Empty (StateViews), DataTable, pagination,
sorting, filtering, search, page headers, navigation shells, responsive layouts. Applications
differ in navigation/workflows, not in the component foundation.

- **Application:** `/pe` namespace + `PEShell` + `RoleRoute requirePE`; pages `v3/pe/*`
  (Dashboard, Assigned Work, Work item workspace on `WorkbenchShell`+`ExtractionPanel`, Work
  status/evidence, Messaging with CarbonTally, Team, Settings).
- **Roles:** PE Owner/Admin · PE Manager · PE Staff (PE-side vocabulary, PO decision; mapped
  server-side to entity-scoped capabilities; PE Admin ≠ CarbonTally Admin; PE Staff ≠
  CarbonTally Staff).
- **Boundary:** preserve the verified backend boundary (§4) exactly.
- **Exposed modules only:** entity-scoped work + PE administration; never customer/consultant/
  staff/admin modules.

---

# 22. DataTable Standard

One canonical table architecture: **DataTable** (server `limit/offset/total` + `onPage`, server
sort `onSortChange`, client sort fallback, page-size options, honest totals, empty state,
`aria-sort`/`scope` accessibility). Fragmentation today: `DataTable` (13 consumers), hand-rolled
`v3-ops-table` (11 files), raw `<table>` (22 files), admin react-table. **Migration/convergence
plan (not immediate):** (1) add bulk-selection + shared filter-toolbar to DataTable; (2) migrate
ops queues and PE lists to DataTable; (3) wrap remaining raw tables; (4) retire `v3-ops-table`
markup. New PE pages must use DataTable from day one. No immediate rewrite of every table.

---

# 23. Responsive UX

Representative audit widths: 1920 / 1440 / 1280 / 1024 / 768 / 390 at **100% zoom** (60% zoom is
never acceptable). Known issues from the functional audit:
- Duplicate `.v3-form-grid` definitions (`v3.css` minmax 220px vs `admin.css` minmax 280px);
- risk of text collapsing when grid/flex children lack `min-width:0` + `overflow-wrap`;
- raw tables without horizontal-scroll wrappers;

---

# 24. Deployment Architecture

Future (candidate) deployment model — **deployment controls, not security boundaries**:

| Surface | Candidate host | Rationale |
|---|---|---|
| Public | carbontally.co.uk | marketing |
| Customer | app.carbontally.co.uk | app surface |
| Consultant | consultant.carbontally.co.uk | app surface |
| Operations | ops.carbontally.co.uk | internal ops |
| Admin | admin.carbontally.co.uk | control plane |
| PE | pe.carbontally.co.uk | partner app (Stage 2) |

Separate hostnames/subdomains are useful for WAF policies, CSP, deployment independence,
monitoring, and access policies — **not required for security** (identity-based authorization
already holds regardless of host). The PE app is designed to move from same-infrastructure →
`pe.carbontally.co.uk` → external PE platform without domain redesign.

---

# 25. Multi-location Architecture

CarbonTally supports geographically distributed users/systems: customers/consultants anywhere;
PEs potentially in Bangladesh (policy-gated, D08); CarbonTally staff distributed. Zero-Trust
posture: location is **never** an authorization boundary (already compliant). Architecture
handles distribution via: regional deployment of the same app binaries (frontend CDN/Vercel),
single Supabase project (or future regional replicas), signed-URL document access independent of
geography, and the PE legal/transfer gates (SCC/IDTA) managed at the contract layer, not the
network layer. No code change required for multi-location today; deployment/legal controls are
the mechanism.


Existing RLS is preserved unchanged. It supports: customer isolation (`is_org_member`),
consultant-client isolation (`is_org_consultant` with active grant), PE isolation
(`is_entity_member`, active entity only), staff scope (internal via app layer), admin scope
(`ADMIN_ROLE_NAMES`), audit/provenance (immutable snapshots + audit tables), document ownership
(org/entity storage policies + signed URLs), assignment ownership (`manual_extraction_batches.
entity_id`). **Gaps:** FORCE RLS deferred (known decision) — until then tenant policy relies on
the service-role app layer + RLS; no speculative migrations are proposed.

---

# 26. Threat Model

| Threat | Design/control | Status |
|---|---|---|
| PE → another PE | `require_entity_scope` + RLS entity policies; cross-entity 403 | STRONG (verified) |
| PE → customer data | `require_internal_staff` denies org lists; entity staff never org members | STRONG (verified) |
| PE → supplier identity | PE sees only the assigned document content; no supplier catalogue; future masking (§20) | PARTIAL (masking future) |
| PE → original documents | signed URLs only; no-download; render-scope fix pending | STRONG (fix P1 preview) |
| PE → CarbonTally staff escalation | `require_internal_staff` gates ops pipeline; entity staff excluded | STRONG (verified) |
| PE → Admin escalation | `require_admin` hard-blocks `is_entity_staff` | STRONG (verified) |
| Customer → another customer | `is_org_member` RLS + org guards | STRONG |
| Consultant → unauthorized client | per-client re-authorization + RLS | STRONG |
| Staff → unauthorized org | org guards + internal-staff checks | STRONG |
| Admin privilege misuse | `ADMIN_ROLE_NAMES` + permission keys + audit trail; separation of duties | STRONG (audit trail present) |
| Direct API access bypassing UI | every endpoint guarded server-side; UI never authority | STRONG |
| Manipulated URLs / IDs | guards re-check every id (org, entity, item, batch, client) | STRONG |
| Leaked signed URLs | short TTL + authorize-before-issue; storage RLS | STRONG (TTL to verify/configure) |
| Session/token misuse | JWT validation; session expiry; MFA future | PARTIAL (MFA enforcement pending) |

---

# 27. Industry-Principle Mapping

| NIST/OWASP principle | CarbonTally status |
|---|---|
| Identity-based authorization (800-207) | **STRONG** |
| No network/location as authz boundary | **COMPLIANT** (no IP/geo/subnet authz exists) |
| Resource/data-level authorization (RLS) | **STRONG** (FORCE RLS deferred → PARTIAL overall) |
| Continuous per-request authorization | **STRONG** |
| Least privilege (roles/permissions) | **STRONG** (legacy admin CRA direct-Supabase → PARTIAL for that surface) |
| Separation of duties | **STRONG** (QC ≠ approval; ops ≠ admin; PE ≠ staff) |
| Defense in depth | **STRONG** (RLS + API + auth + UX) |
| Micro-segmentation (application surfaces) | **PARTIAL** (data-plane segmented; frontend surfaces not yet) |
| Data minimization | **PARTIAL** (privacy/masking layer future) |
| Secure API design | **STRONG** (V3; legacy surface → PARTIAL for legacy) |
| Secure document access | **STRONG** (preview defect is a P1 usability item) |
| Independent deployment | **PARTIAL** (architected; not yet deployed separately) |
| Attack-surface minimization | **PARTIAL** (405 legacy endpoints pending removal) |
| MFA / privileged access | **PARTIAL / NOT YET VERIFIED** (architecture ready; enforcement pending) |
| Formal certification | **NOT APPLICABLE** — alignment assessment, not certification |

- workspace needs D19 tray flow below ~900px.
**Grouped causes → shared fixes:** (a) reconcile form-grid CSS into one shared rule; (b) add
`min-width:0`/`overflow-wrap:anywhere` to the shared layout primitives; (c) table scroll wrapper
or DataTable everywhere; (d) shared responsive shell rules per application. Fix the foundation,
not individual screens. (The org-profile overflow reported at 100% zoom was not reproduced in
headless Chromium at tested widths; the duplicate-CSS risk is verified.)

---

# 28. Current Gaps

| # | Gap | Severity | Notes |
|---|---|---|---|
| G1 | Frontend trust-domain separation incomplete (PE inside `/ops` shell) | P1 (product architecture) | not a backend defect |
| G2 | Legacy `admin/` CRA bypasses FastAPI (direct Supabase) | P1 (trust boundary) | quarantined; retire on dependency inventory |
| G3 | Document preview defect (signed-URL download scope) | P1 (usability/UX) | does not weaken no-download boundary |
| G4 | No token audience/scope separation across applications | P2 | guards compensate; hardening future |
| G5 | FORCE RLS deferred | P2 | known decision |
| G6 | PE-side role vocabulary not separated | P2 | PO decision |
| G7 | Legacy API surface (~405 endpoints) still mounted | P2 | removal gated |
| G8 | Table/component duplication (3 systems) | P3 | convergence plan |
| G9 | Duplicate `.v3-form-grid` CSS + responsive risk factors | P2 | shared foundation fix |
| G10 | PE privacy/masking not implemented | P3/FUTURE | designed, not built |
| G11 | Entity-scoped PE messaging not implemented | P2 | PO decision (N1 boundary approved) |
| G12 | MFA enforcement not yet configured | P2 | deployment/policy decision |

---

# 29. Implementation Priorities

1. **P0 — pre-requisites:** signed-URL render-scope fix (G3); unit-normalisation + methodology
   server-side; responsive foundation (G9).
2. **P1 — PE application surface:** `/pe` + `PEShell` + `requirePE` + `/api/v3/pe/me`;
   move PE components (non-destructive); `/ops`→`/pe` redirect bridge; acceptance tests.
3. **P2 — Operations/Admin separation:** remove PE branch from OperationsPage; Admin surface per
   PO ruling (G1/G2); retire legacy admin CRA.
4. **P3 — hardening:** token audience/scope (G4), MFA posture (G12), FORCE RLS decision (G5),
   legacy-route removal (G7).
5. **P4 — convergence:** DataTable standard (G8), PE privacy/masking (G10), entity messaging
   (G11, if approved), independent PE deployment.

---

---

# 30. Migration Strategy (non-destructive)

1. Add `/pe` surface while `/ops` PE branch remains fully functional (bridge: PE users redirected
   to `/pe`).
2. Preserve all data: users, assignments, work items, documents, extraction data, QC, audit
   history, database, RLS, APIs — **no data/DB/RLS/API changes** for the frontend separation.
3. Run acceptance tests (§31) against the new surface while the old branch is retained.
4. After verification (e.g. N days of green acceptance), retire the `/ops` PE branch and the
   bridge. Never delete the PE functionality until the replacement is verified.

---

# 31. Acceptance Tests

**PE:** login → lands on `/pe`; dashboard = own entity only; role-aware navigation (Owner/Admin/
Manager/Staff matrices); assigned work = own entity only; document viewer renders inline (no
download control); extract/map/validate/QC 200 for own items; cross-PE → 403; cross-customer →
403; Admin → 403 + redirect; Staff → 403 + redirect; direct unauthorized API → 403; cannot
enumerate customer orgs.
**Customer:** access; cross-customer denial; PE/Staff/Admin denial.
**Consultant:** client access; unauthorized-client denial; PE/Admin denial.
**Staff:** operations access; assignment; review/QC; PE management; cannot reach PE application's
entity work unless authorized internal workflow.
**Admin:** platform administration; privileged operations appropriate to role; remains separate
from Staff and PE.
**Responsive:** all new PE pages pass 1920/1440/1280/1024/768/390 at 100% zoom (no overflow, no
one-character text).

---

# 32. Risks

- Migration breaks PE users → non-destructive bridge + retention of old branch until green.
- Duplication of logic across app surfaces → shared V3 API + D21 primitives enforced.
- `/admin` ruling ambiguity → structural separation designed regardless; page-set decision only.
- Preview remains broken → P0 fix gated before PE milestones.
- PE app accidentally calls org-wide aggregates → entity-scoped queries only; no customer lists.
- Layout regression → shared responsive foundation + acceptance widths.
- PE role model conflicts with internal `staff_roles` → separate PE vocabulary (PO decision);
   guards stay entity-scoped.

---

# 33. Architectural Invariants

1. Authorization is always identity + tenant/entity + resource/action; never IP/geo/URL/route.
2. The frontend is never the security boundary.
3. The verified PE backend boundary (RLS + API + auth) is preserved unchanged.
4. PE is never a customer; PE staff are never CarbonTally staff; PE Admin is never CarbonTally
   Admin.
5. One identity system; no per-app user databases.
6. One V3 API domain layer; different access contracts, never duplicated business logic.
7. One D21 UI foundation; no per-app component ecosystems.
8. Data minimization is the default for PE-visible information (future layer).
9. All existing data (incl. 7,049 emission factors) and RLS/migrations are preserved.
10. Every application surface can eventually deploy independently without domain redesign.

| Cross-application privilege escalation | backend denies by surface guards; PE→/ops and PE→/app verified 403 | STRONG |

---

# 34. Decisions Already Established

- V3 canonical; legacy temporary; legacy-route removal gated on dependency inventory (D17).
- Four access axes never interchangeable (D22); one account, one role (D03).
- PE = third-party processor, not customer; dedicated table; work-assignment based (D23/D24).
- PE strictly non-customer-facing; no direct customer↔PE communication (D25/N1).
- PE no-download; private storage + signed URLs (D07/D44).
- Quality chain PE QC → CT QC → Customer final approval (D05/D20).
- Customer Owner MAY self-approve custom factors (later PO clarification).
- Retention configurable; destructive enforcement deferred (N3/D-P2-04).
- Billing provider-neutral, configurable, GBP indicative (D41).
- `/ops` is the canonical Staff/Operations app; legacy admin CRA quarantined (D-P2-02).
- QC limited authority (D-P2-03); system_admin superset (V3M8).
- D21 UI foundation; no shadcn assumption (D21/D47).
- FORCE RLS deferred (known decision).
- Consultant revocation Owner/Admin/Manager only; never deletes data (WS6/SEC-0003).

# 35. Decisions Still Requiring Product Owner Approval

1. **PE application surface** — approve `/pe` namespace + `PEShell` as the PE application.
2. **PE API contract** — approve `/api/v3/pe/*` thin boundary (vs reusing `/api/v3/ops/entities/*`
   directly); which endpoints become PE API vs remain ops-internal.
3. **PE-side role vocabulary** (`owner|admin|manager|staff`) and its storage mapping.
4. **Admin final surface** — dedicated `/admin` AdminApp vs `/ops` (decision register §39 #1).
5. **Entity-scoped PE ↔ CarbonTally operational messaging** (decision register §39 #2).
6. **MFA enforcement posture** for production.
7. **FORCE RLS** — final decision to enable force row-level security.
8. **Token audience/scope separation** — approve as a hardening item or defer.
9. **Data minimization/masking scope** for the future PE privacy phase.
10. **Optional `/app` prefix** for the Customer application (vs current flat routes).

---

# 36. Final Recommended Blueprint

```
PUBLIC ──> /            (marketing, unauth)
CUSTOMER ──> /app       CustomerApp  │
CONSULTANT ──> /consultant  ConsultantApp │
PE ──> /pe            PEApp (PEShell)     │   all → shared V3 API → authz →
OPS ──> /ops           OpsApp (staff)     │   domain services → repositories → DB
ADMIN ──> /admin        AdminApp           │   (single identity + RLS + D21 UI)
```

1. **Preserve** the verified PE backend boundary; do not redesign it.
2. **Build** the six application surfaces as explicit shells over the shared V3 API and D21 UI
   foundation, starting with the PE application (`/pe`) via a non-destructive migration.
3. **Define** the deliberate PE API contract (`/api/v3/pe/*`) sharing domain services; classify
   the 14 entity endpoints (PE API vs ops-internal vs shared services).
4. **Fix** the P0 pre-requisites (document viewer render scope; unit-normalisation; responsive
   foundation) before PE milestones.
5. **Resolve** the §35 PO decisions (PE surface/API/roles, Admin surface, PE messaging, MFA,
   FORCE RLS, token scopes, masking scope).
6. **Keep** industry alignment: identity + resource-based authorization (STRONG), separation of
   duties (STRONG), no location-based trust (COMPLIANT), data minimization (future), application
   micro-segmentation (closing the PARTIAL gap), attack-surface minimization (retire legacy).
7. **Deploy** independently later (pe/app/ops/admin hostnames) as deployment controls — never as
   security boundaries.

---

## Data-minimization appendix (foundation for the future PE privacy phase)

| Information | PE | Customer | Consultant | Staff | Admin |
|---|---|---|---|---|---|
| Customer name/brand | SHOULD BE MASKED (future) | REQUIRED | REQUIRED | OPTIONAL | REQUIRED |
| Supplier identity | OPTIONAL (as in document) | REQUIRED | REQUIRED | OPTIONAL | REQUIRED |
| Document content | REQUIRED (assigned work only) | REQUIRED | REQUIRED | REQUIRED | REQUIRED |
| Customer org settings | MUST NEVER BE EXPOSED | REQUIRED | OPTIONAL (client-scoped) | OPTIONAL | REQUIRED |
| Other customers' data | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | CONDITIONAL (assigned) | REQUIRED (governance) |
| Internal ops/audit | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | REQUIRED | REQUIRED |
| Cross-entity/PE data | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | MUST NEVER BE EXPOSED | OPTIONAL (ops-wide) | REQUIRED |
| Contact details | MUST NEVER BE EXPOSED | REQUIRED (own) | REQUIRED (clients) | OPTIONAL | REQUIRED |

## Safety confirmation

Read-only. No application files, database, migrations, RLS, packages, configuration, tests,
Docker or deployment files modified; no documents deleted/moved/renamed; no commits/pushes. Only
this report file was created.

