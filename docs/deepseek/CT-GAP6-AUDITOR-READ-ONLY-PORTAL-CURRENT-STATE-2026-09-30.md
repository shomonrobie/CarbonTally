# Gap 6 — Auditor Read-Only Portal: Current State Research

**Prompt ID:** CT-GAP6-AUDITOR-PORTAL-RESEARCH-2026-09-30-001
**Repository:** /home/shomonrobie/ct_93d5cdd
**Date:** 2026-09-30
**Mode:** READ-ONLY

---

## 1. Executive Summary

- **Overall stage: ABSENT (with a fully wired upstream reuse stack, and one customer/consultant-facing audit-evidence package already shipped under the "Phase 7 — Auditor / Assurance" label).**
  No external-auditor-facing portal exists at any layer. There is no auditor
  identity, no auditor role, no auditor access-grant table, no auditor-facing
  route, no auditor-scoped UI and no time-limited access mechanism for a third
  party. What *does* exist is:
  1. a **Phase 7 "Auditor / Assurance" capability** that is deliberately
     **customer/consultant/internal-staff scoped** (organisation owner/admin or
     an authorized consultant), which produces an *evidence* package — explicitly
     *not* an assurance opinion;
  2. an **explicit, ratified refusal of the auditor persona** in the Insight
     authorization model (`api/insight_authz.py`), and a documented historical
     audit note that "External Auditor: NO unrestricted role created";
  3. a **mature reuse stack** (role model, permission-aware routing, evidence
     trail, secure document viewer, audit console, audit-package export, audit
     immutability, report versions) that a future auditor portal could consume —
     none of which currently exposes a third-party auditor surface.

- **Highest-risk unknowns.**
  1. Whether the P7 audit-immutability migration (`20260912000000_p7_*`) and the
     S2 `report_versions.is_current` migration (`20260921000000_p8_s2_*`) are
     applied in the authoritative database. Repository docs (FIEW register)
     record them as **unapplied / BLOCKED_BY_SCHEMA**; this is not determinable
     by static inspection and no DB connection was attempted.
  2. Whether an auditor-portal branch or a second repository exists outside this
     tree. Not determinable from this workspace.
  3. Per-database application state (which of the 11 databases referenced in the
     repo's own verification docs are authoritative) — **UNKNOWN**; all schema
     claims below are from migrations and repository documentation, not live
     reads.

- **Estimated build distance.**
  Medium-to-large. The evidence/document/audit/export primitives are already
  built and wired (see §3, §8), so the portal is not greenfield in the way Gap 4
  (supplier portal) is. However, the four things the gap actually names —
  **auditor identity**, **time-limited access grant with expiry**, a
  **read-only-scoped route family**, and an **auditor export/section** — are
  **all absent**. The P7 audit-package endpoint is the closest existing artifact
  but is authorized for *the customer's own owner/admin or their consultant*, not
  for an external auditor, and is not time-bound. Estimate: **one focused build
  phase** reusing existing primitives, plus a new identity/grant model that does
  not exist today.

- **Repo-language note on the gap label.** The string "Gap 6" in this repository
  does **not** refer to an auditor portal. Searches of `docs/**` for `Gap 6`
  / `gap-6` / `gap_6` return only `FTR-GAP-6`, an unrelated *feature-catalogue
  methodology gap* about "role surfaces are representative ranges, not
  per-permission matrices"
  (`docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:173,185`,
  `docs/architecture/CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md:446`).
  The "internal gap reference: Gap 6" must therefore be treated as an **external
  programme label not recorded in this repository** (same situation as the Gap 4
  research pass recorded in
  `docs/architecture/CT-GAP4-SUPPLIER-ENGAGEMENT-PORTAL-CURRENT-STATE-2026-09-30.md:21-27`).

---

## 2. Component-by-Component Findings

### 2.1 Auditor role definition
- **Classification: ABSENT.**
- **Evidence (file paths, migrations, routes):**
  - The customer role model is **fixed to four values** by a CHECK constraint:
    `supabase/migrations/00000000000000_init_schema.sql:285`
    (`CONSTRAINT organization_members_role_check CHECK (role IN ('owner','admin','member','viewer'))`).
    No `auditor` value exists.
  - The staff role model has **no auditor row** and no auditor seed:
    `staff_roles` is defined at
    `supabase/migrations/00000000000000_init_schema.sql:1220-1230`
    (`name`, `description`, `permissions jsonb`). Whole-repo `*.sql` search for
    `auditor` returns **only three comment hits** (no DDL, no seed):
    `supabase/migrations/20260807020000_add_calculation_snapshots.sql:9`,
    `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql:2`,
    `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql:11`.
  - The codebase **states outright that no auditor role exists**:
    `backend/api/insight_authz.py:70-73`
    ("No auditor role/table/permission model exists in CarbonTally (D2 §10.3) …
    `AUDITOR_ROLE_NAMES = ("auditor", "org_auditor", "assurance_reviewer", "auditor_reviewer")`"),
    and denies that persona by name at `backend/api/insight_authz.py:243-246`.
  - Historical verification confirms the deliberate non-build:
    `docs/cline/prompt-history/CT-P7-INDEPENDENT-VERIFICATION-20260912-005.md:203`
    ("**External Auditor: NO unrestricted role created** — grep found no auditor
    role/table/policy (comments only). Residual confirmed intentional."), and
    `docs/architecture/CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md:108`
    ("**External auditor** — **no persona exists** (no principal, no route)").
- **Gaps and unknowns:** No `auditor` role value, no `auditor` staff-role seed,
  no auditor principal type. Whether a *future* design intends a role value, a
  separate principal, or a time-bound grant (see §2.6) is **UNKNOWN** and is a PO
  decision.

### 2.2 Read-only access via RoleRoute (FTR-033)
- **Classification: PARTIALLY_IMPLEMENTED (guard infrastructure present; no auditor scope, no read-only flag).**
- **Evidence:**
  - `frontend/src/v3/components/RoleRoute.jsx:83-91` exposes exactly five scope
    props: `requireOrg`, `requireStaff`, `requireInternalStaff`,
    `requireEntityStaff`, `requireConsultant`. There is **no `requireAuditor`**
    and **no read-only / `can_view` variant**.
  - Roles are resolved server-side from `/api/v3/me/context`
    (`frontend/src/v3/components/RoleRoute.jsx:29-71`), and the guard is
    explicitly *UX/navigation only* — "The backend/RLS remain the authoritative
    security boundary; these guards are UX/navigation only"
    (`RoleRoute.jsx:4-6`).
  - The router wires RoleRoute across the workspace tree
    (e.g. `frontend/src/App.js:1988, 2172, 2190, 2235`), but a whole-file search
    of `frontend/src/App.js` for `auditor` returns **only the `AUDITOR_EXCEL`
    report-type option** (`App.js:1373`), not a route or guard.
  - `FTR-033` is catalogued as `IMPLEMENTED_AND_WIRED`
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:287`).
- **Gaps and unknowns:** No auditor-gated route, no read-only navigation mode.
  Reusable: the guard pattern itself.

### 2.3 Auditor-scoped evidence trail viewer
- **Classification: PARTIALLY_IMPLEMENTED — the evidence viewer is IMPLEMENTED_AND_WIRED but is scoped to customer members/consultants, never to an auditor.**
- **Evidence:**
  - `frontend/src/v3/components/EvidenceTrail.jsx:67-68` (universal evidence-chain UI)
    and `frontend/src/v3/evidence/SourceEvidenceViewer.jsx:1-46`
    (shared Source Evidence Viewer, PO authorization 2026-09-22).
  - Backend: `GET /api/v3/evidence/line-items/{line_item_id}`
    (`backend/api/v3_evidence.py:103-118`), read-only, re-authorizes on every
    read, requires `require_org_member()` (`v3_evidence.py:106`).
  - The evidence viewer's authorization is **organisation isolation + DM-6
    drill-down depth** (`v3_evidence.py:14-19`); it is **not** auditor-aware, and
    it explicitly denies PE and internal staff
    (`v3_evidence.py:18-19`).
  - `FTR-126` catalogued `IMPLEMENTED_AND_WIRED`
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:455`).
- **Gaps and unknowns:** No auditor filter, no auditor-scoped projection, no
  auditor principal accepted on the endpoint.

### 2.4 Auditor no-edit document viewer boundary
- **Classification: PARTIALLY_IMPLEMENTED — the secure viewer exists as a reusable no-download primitive; there is no auditor boundary and no server-enforced "no edit" scope for an external principal.**
- **Evidence:**
  - `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx:42`
    (`allowDownload = false` default; `:67-73` and `:113-118` render
    "View only — download disabled for this role").
  - The component is explicit that it is **presentation only**, not the security
    boundary: "the security boundary is server-side (signed URLs + RLS). This
    component never fabricates a security guarantee"
    (`SecureDocumentViewer.jsx:19-21`).
  - The document pointer is a **short-lived, private-bucket signed URL**
    (`SecureDocumentViewer.jsx:9-12`), backed by `backend/services/storage.py`
    (signed URL creation with mandatory expiry, `services/storage.py:9-11`).
  - `FTR-101` catalogued `IMPLEMENTED_AND_WIRED`
    (`docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:410`).
- **Gaps and unknowns:** The viewer is inherently view-only; there is no
  auditor-scoped download policy, and no external principal can reach it.

### 2.5 Auditor-scoped audit trail access
- **Classification: PARTIALLY_IMPLEMENTED — an org-scoped audit trail is fully wired, but its authorization admits owner/admin, authorized consultant and internal staff, never an auditor.**
- **Evidence:**
  - `backend/api/dependencies.py:264-321` (`ensure_org_audit_access`): the
    permitted set is internal staff (oversight), organisation **owner/admin only**
    (`_ORG_AUDIT_ROLES = {"owner","admin","org_owner","org_admin"}`, `:265`), or
    a consultant with an **ACTIVE client grant** (`:312-316`). No auditor branch
    exists.
  - Routes: `GET /api/v3/reporting/audit-readiness`
    (`backend/api/v3_reporting.py:378`),
    `GET /api/v3/reporting/audit-activity` (`v3_reporting.py:394`),
    `GET /api/v3/reporting/consultant-client/{client_id}/audit-activity`
    (`v3_reporting.py:427`), `GET /api/v3/ops/entities/{entity_id}/audit-activity`
    (`v3_reporting.py:458`), `GET /api/v3/ops/reporting/audit`
    (`v3_reporting.py:258`).
  - UI: `frontend/src/v3/ops/AuditConsoleTab.jsx:74-82` is gated to
    "staff-admin only" (`canManage`), and `frontend/src/v3/admin/AuditTab.jsx:29`
    is the customer org-scoped surface.
  - `FTR-207`/`FTR-208` catalogued `IMPLEMENTED_AND_WIRED`
    (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:611-612`).
- **Gaps and unknowns:** No auditor scope on any audit route; no auditor-specific
  filters beyond the generic taxonomy filters.

### 2.6 Time-limited access grants with expiry
- **Classification: ABSENT for the auditor-portal purpose — no "grant" table with expiry exists; several sibling expiry mechanisms exist that could be extended (see §4).**
- **Evidence:**
  - `manual_processing_grants` is the only table named "*grant*" and it is
    **not time-limited**: columns are `scope_type, scope_id, enabled, reason,
    set_by, set_at, updated_at` — **no `expires_at`**
    (`supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql:54-68`),
    and it is a CarbonTally-Admin governance control plane, not an access grant.
  - `consultant_clients` — the consultant engagement "grant" — has **no expiry
    column**: columns are `status`, `billing_plan`, `billing_cycle`, `tags`,
    `created_at`, `updated_at`, … (`supabase/migrations/00000000000000_init_schema.sql:1554-1572`).
    Access is granted/revoked by `status = 'active'`
    (`backend/api/consultant_auth.py:231-241`).
  - The one *real* time-limited authorization model is **report sharing**:
    `report_shares` has `expires_at`, `revoked_at`, `revoked_by`,
    `revocation_reason`, `access_count`, `last_accessed_at`
    (`supabase/migrations/20261022000000_ct02_report_sharing.sql:121-145`),
    with server-side expiry evaluation and one-way revocation
    (`backend/services/report_shares.py:128-147`, `:215-219`).
  - No table, column or route containing `time_limited`, `access_grant`,
    `auditor*`, or `valid_until` was found anywhere in `backend/**` or `*.sql`
    (whole-tree searches returned zero DDL/route hits).
- **Gaps and unknowns:** No time-bound third-party access model exists; the
  closest reusable pattern is `report_shares` (expiry + revocation + audit), which
  is a report-scoped recipient model, not a portal session model.

### 2.7 Auditor export format
- **Classification: PARTIALLY_IMPLEMENTED — a JSON audit/evidence package exists, but there is no auditor-specific format and it is not auditor-authorized.**
- **Evidence:**
  - `GET /api/v3/exports/audit-package.json`
    (`backend/api/v3_exports.py:90-111`), assembled by
    `ReportingRepository.audit_package(...)`
    (`backend/data/reporting.py:1152-1229`).
  - The payload is *evidence*, explicitly **not** an assurance opinion:
    `document_type: "carbontally_audit_evidence_package"`,
    `not_assurance: true` (`data/reporting.py:1195-1203`).
  - Authorization is `ensure_org_audit_access` (`api/v3_exports.py:107`) — i.e.
    owner/admin, an authorized consultant, or internal staff — **never an
    external auditor**.
  - `FTR-209` catalogued `IMPLEMENTED_AND_WIRED` but with a **documentation
    inaccuracy**: the catalogue attributes the assembly to
    `data/exports.py` (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:613`);
    in fact `backend/data/exports.py` only implements emissions/documents CSV/JSON
    (`data/exports.py:66-143`) and the audit package is assembled in
    `backend/data/reporting.py:1152`.
- **Gaps and unknowns:** No auditor-named format/module; no time-bound token in
  the export path; no per-auditor delivery mechanism.

### 2.8 Auditor section in audit package export (FTR-209)
- **Classification: ABSENT.**
- **Evidence:** The package has exactly these sections — `package`,
  `organization`, `readiness`, `calculation_snapshots`, `workflow_history`,
  `integrity`, `counts`
  (`backend/data/reporting.py:1194-1228`). There is **no `auditor` section**,
  no auditor identity block, no engagement scope, and no auditor-specific field.
  The `integrity.package_hash` (SHA-256 over the canonical content,
  `data/reporting.py:1209-1224`) is the only integrity/attribution artifact.
- **Gaps and unknowns:** What an "auditor section" must contain (engagement id,
  scope period, access window, recipient identity) is undefined and is a PO
  decision.

### 2.9 Role model reuse (FTR-053–056)
- **Classification: IMPLEMENTED_AND_WIRED (reusable; no auditor role within it).**
- **Evidence:**
  - Customer role model: `organization_members.role` CHECK = `owner/admin/member/viewer`
    (`supabase/migrations/00000000000000_init_schema.sql:285`);
    enforced in code at `backend/api/v3_organizations.py:31-33,405-407`
    (`ORG_ROLES`) and pinned by test
    (`backend/tests/unit/api/test_v3_customer_admin.py:43-45`).
  - Internal staff role model: `staff_roles.permissions jsonb`
    (`init_schema.sql:1220-1230`), resolved via `staff_profiles.role_id`
    (`init_schema.sql:1240`), read through `backend/data/staff.py:240-250`,
    `backend/data/roles.py:33-47`, `backend/api/operations_auth.py:56-73`.
  - Consultant capability flags: `consultant_firm_members`
    (`init_schema.sql:1576-1594`).
  - Catalogue rows FTR-053…056 all `IMPLEMENTED_AND_WIRED`
    (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:322-325`).
- **Gaps and unknowns:** The legacy `roles` table exists but is empty
  (`FTR-057` = `SCHEMA_ONLY (empty)`,
  `CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:326`);
  it is a customer-org reference, not a staff/auditor model
  (`backend/data/roles.py:1-8`).

### 2.10 Evidence trail reuse (FTR-126)
- **Classification: IMPLEMENTED_AND_WIRED (reusable as-is; not auditor-scoped).**
- **Evidence:** `frontend/src/v3/components/EvidenceTrail.jsx`,
  `frontend/src/v3/evidence/SourceEvidenceViewer.jsx`,
  `GET /api/v3/evidence/line-items/{line_item_id}` (`backend/api/v3_evidence.py:103`),
  backing tables `evidence_line_items` / `provenance_line_links` created by
  `supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` and
  `supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql`.
  Route + component pinned by tests
  (`backend/tests/unit/api/test_source_evidence_viewer.py`,
  `frontend/src/v3/__tests__/source-evidence-viewer.test.jsx`).
- **Gaps and unknowns:** The catalogue records `evidence_line_items` as
  "present in `qa133`/clones; absent in flagship"
  (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:456`) — applied
  state is UNKNOWN without a DB read.

### 2.11 Secure document viewer reuse (FTR-101)
- **Classification: IMPLEMENTED_AND_WIRED (reusable as-is; not auditor-scoped).**
- **Evidence:** `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx`
  (`:42` `allowDownload` boundary; `:49,102` sandbox policy),
  consumed by `WorkbenchShell.jsx:43` and `SourceEvidenceViewer.jsx:120-121`.
  No-download policy test:
  `frontend/src/v3/__tests__/secure-document-viewer.test.jsx`.
  Catalogue: `IMPLEMENTED_AND_WIRED`
  (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:410`).
- **Gaps and unknowns:** View-only is UX + server signed URLs; there is no
  auditor principal to enforce it for.

### 2.12 Audit console reuse (FTR-207)
- **Classification: IMPLEMENTED_AND_WIRED (staff-admin / customer-org console; not auditor-scoped).**
- **Evidence:** `frontend/src/v3/ops/AuditConsoleTab.jsx:1-13` (staff-admin only)
  and `frontend/src/v3/admin/AuditTab.jsx:1-29` (customer org surface);
  backend `GET /api/v3/ops/reporting/audit` (`backend/api/v3_reporting.py:258`)
  and admin `/api/v2/admin/audit` (`backend/api/admin_audit.py:83`).
  Catalogue: `IMPLEMENTED_AND_WIRED`
  (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:611`).
- **Gaps and unknowns:** The catalogue counts the **legacy
  `/api/admin/audit-logs` (12 endpoints) as part of the wired console**, but an
  independent reconciliation found those endpoints are **unrouted/orphan**
  (`docs/architecture/CT-PO-CARBONTALLY-CT-AUDIT-01-CANONICAL-AUDIT-SYSTEM-RECONCILIATION-20260927.md:611,650-651,663`).
  This is a documentation over-count, not a live capability.

---

## 3. Reuse Infrastructure Verification

| Feature ID | Table / Route / File | Present? | Reachable? | Notes |
|---|---|---|---|---|
| FTR-053–056 Role model | `organization_members.role` CHECK (`init_schema.sql:285`); `staff_roles.permissions` (`:1220-1230`); `consultant_firm_members` (`:1576-1594`) | Yes | Yes | No auditor role inside any model; legacy `roles` table empty (`FTR-057 SCHEMA_ONLY`) |
| FTR-033 Permission-aware routing | `frontend/src/v3/components/RoleRoute.jsx`; wired in `App.js:1988…2267` | Yes | Yes | Five scopes only; **no auditor / read-only scope** |
| FTR-126 Evidence trail | `EvidenceTrail.jsx`, `SourceEvidenceViewer.jsx`, `GET /api/v3/evidence/line-items/{id}` (`v3_evidence.py:103`) | Yes | Yes | Re-authorizes per read; no auditor scope |
| FTR-101 Secure document viewer | `SecureDocumentViewer.jsx` (`:42`) | Yes | Yes | View-only primitive; no auditor boundary |
| FTR-207 Audit console | `ops/AuditConsoleTab.jsx`, `admin/AuditTab.jsx`, `GET /api/v3/ops/reporting/audit` (`v3_reporting.py:258`) | Yes | Yes | Staff-admin/customer-org only; legacy 12 endpoints orphan (see §2.12) |
| FTR-209 Audit package export | `GET /api/v3/exports/audit-package.json` (`v3_exports.py:90`); `data/reporting.py:1152` | Yes | Yes | Customer/consultant/staff auth; **not** auditor; docs mis-attribute assembly to `data/exports.py` |
| FTR-204 Audit immutability | `supabase/migrations/20260831020000_audit_activity_immutability.sql`; `20260912000000_p7_audit_immutability_and_indexes.sql` | Partially | UNKNOWN | `20260831020000` is the WS1/DB-0001 hardening; `20260912000000` (P7) is recorded **unapplied** → `FTR-204 PARTIALLY_IMPLEMENTED` (`docs/architecture/CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:156`) |
| FTR-223 Report versions `is_current` | `report_versions`; `supabase/migrations/20260921000000_p8_s2_is_current_single_valued.sql` | Partially | UNKNOWN | Table present; single-valued rule migration recorded **UNAPPLIED / BLOCKED_BY_SCHEMA** (`…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:108`) |
| Gap 7 Assurance integration | No assurance-statement table/service/route | **No** | **No** | Only negative markers (`not_assurance: true`, `data/reporting.py:1203`); a SECR *template* mentions an "Assurance Statement" section (`docs/architecture/UI/back/secr_report.md:1413`) but no code implements it |

---

## 4. Time-Limited Access Patterns Found

**Existing expiry mechanisms (reusable precedents — none is an auditor portal):**

- **Report shares (closest match).** `report_shares.expires_at` / `revoked_at` /
  `revoked_by` / `revocation_reason` / `access_count` / `last_accessed_at`
  (`supabase/migrations/20261022000000_ct02_report_sharing.sql:121-145`);
  server-side expiry evaluation and one-way revocation
  (`backend/services/report_shares.py:128-147, 215-219`);
  `services/report_shares.py:8-9` records the *pre-existing* defect ("no
  server-side authorization, no tenant isolation, no expiry and no revocation")
  that this migration fixed.
- **Invitations.** `user_invitations.expires_at`
  (`supabase/migrations/00000000000000_init_schema.sql:364`),
  `pending_invites` (`:345-352`, **no expiry column**); enforced at
  `backend/api/v3_organizations.py:43,602-611`
  (`_INVITATION_EXPIRY_DAYS = 7`) and `backend/data/invitations.py:36-37`.
- **Beta access codes.** `beta_access_codes.expires_at`
  (`init_schema.sql:380`); created with `expires_in_days` and expiry-checked at
  `backend/routes/admin/beta.py:123, 240-244`.
- **Password reset tokens.** `password_reset_tokens.expires_at`
  (`init_schema.sql:336`); 1-hour expiry at `backend/routes/users.py:78, 139-141`.
- **Operational/download artifacts.** 7-day export links
  (`backend/routes/organizations/exports.py:106-108`), signed storage URLs with
  mandatory expiry (`backend/services/storage.py:9-11`).
- **Scheduled-report / signing URLs.** `expires_in`/`expires_at` at
  `backend/routes/organizations/files.py:423-424`.
- **Insight concurrency leases.** `lease_expires_at`
  (`supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql:104-115`).

**Grant tables with expiry:** **None.** The only `*grant*` tables
(`manual_processing_grants`, and the consultant engagement model via
`consultant_clients`) carry **no expiry column**:
`manual_processing_grants` (`20260927000000_…:54-68`) and
`consultant_clients` (`init_schema.sql:1554-1572`, status-driven, not time-driven).

**Extension potential:** The `report_shares` model (expiry + revocation +
access-count + audit) is the strongest reusable template for a time-limited
auditor grant. Consultant engagement (FTR-062/066) is *status*-based, not
time-based, and would need an added expiry dimension to serve as an auditor-grant
base. Neither is currently wired to any auditor concept.

---

## 5. Migration Inventory (Auditor / Grant / Expiry Related)

> Note: there is **no top-level `migrations/` directory**. Migrations live in
> `supabase/migrations/` (primary, 90 files), plus `database/rc1`, `database/rc2`,
> `database/v3` and a static dump `CarbonTally_DB_Schema_V3M2.sql`.

| Migration File | Tables Created | Columns Added | Applied in Which DBs (if determinable) |
|---|---|---|---|
| *(none)* — no migration filename contains `auditor` | — | — | `auditor` appears only in 3 comment lines (see §2.1) |
| `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql` | `is_org_consultant()` function (RLS) | — | Not determinable (no DB read) |
| `supabase/migrations/20260831040000_consultant_revocation_roles.sql` | consultant revocation roles | — | Not determinable |
| `supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql` | `manual_processing_grants` | — | Not determinable; **no expiry column** |
| `supabase/migrations/20261022000000_ct02_report_sharing.sql` | `report_shares` | `expires_at, revoked_at, revoked_by, revocation_reason, access_count, last_accessed_at` | Not determinable |
| `supabase/migrations/00000000000000_init_schema.sql` | `roles`, `organization_members`, `staff_roles`, `pending_invites`, `user_invitations`, `beta_access_codes`, `password_reset_tokens`, `dashboard_metrics`, `organization_files` | `expires_at` on several (`:336,:364,:380,:1915,:2107`) | Not determinable |
| `supabase/migrations/20260831020000_audit_activity_immutability.sql` | — (policy drops) | — | Not determinable (`FTR-204` "applied" per FIEW) |
| `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql` | — (P7 audit integrity) | — | Recorded **UNAPPLIED** (`…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:156`) |
| `supabase/migrations/20260921000000_p8_s2_is_current_single_valued.sql` | — | `report_versions.is_current` rule | Recorded **UNAPPLIED** (`…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:108`) |
| `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | `insight_concurrency_leases` | `lease_expires_at` | Not determinable |
| `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` | (discovery) | `verification_code_expires_at` | Not determinable |

**Applied-state caveat:** repository verification docs consistently record that a
large block of migrations is unapplied in the flagship environment (e.g.
`docs/architecture/CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md:184`
"the 43 unapplied migrations"). No live DB reads were performed for this pass, so
per-database application state is **UNKNOWN**.

---

## 6. Route Inventory (Auditor / Audit / Export Related)

| Route Path | Method | Module | Auth Required? | Purpose |
|---|---|---|---|---|
| `/api/v3/exports/audit-package.json` | GET | `backend/api/v3_exports.py:90` | Yes — `get_current_user` + `ensure_org_audit_access` (owner/admin, consultant w/ active grant, internal staff) | Audit/evidence JSON package; `not_assurance: true` |
| `/api/v3/reporting/audit-readiness` | GET | `backend/api/v3_reporting.py:378` | Yes — `ensure_org_audit_access` | Evidence-readiness indicator |
| `/api/v3/reporting/audit-activity` | GET | `backend/api/v3_reporting.py:394` | Yes — `ensure_org_audit_access` | Org-scoped activity timeline |
| `/api/v3/reporting/consultant-client/{client_id}/audit-activity` | GET | `backend/api/v3_reporting.py:427` | Yes — `ensure_consultant_org_access` (active grant) | Consultant client audit activity |
| `/api/v3/ops/entities/{entity_id}/audit-activity` | GET | `backend/api/v3_reporting.py:458` | Yes — `require_staff` | Entity-scoped activity |
| `/api/v3/ops/reporting/audit` | GET | `backend/api/v3_reporting.py:258` | Yes — staff admin | Ops audit console feed |
| `/api/v3/exports/emissions.csv` \| `.json` \| `/documents.csv` | GET | `backend/api/v3_exports.py:40,54,79` | Yes — `require_org_member()` | Data exports (not audit) |
| `/api/v3/evidence/line-items/{line_item_id}` | GET | `backend/api/v3_evidence.py:103` | Yes — `require_org_member()` + DM-6 | Source evidence viewer |
| `/api/v2/admin/audit/export` | GET | `backend/api/admin_audit.py:83` | Yes — admin | Admin audit CSV |
| `/api/admin/beta/codes` (create/list) | GET/POST | `backend/routes/admin/beta.py:54,96` | Yes — `require_admin()` | Beta codes **with expiry** (precedent only) |
| `/api/admin/audit-logs` (12 endpoints) | GET | legacy | — | **Orphan — no route registered** (`…CT-AUDIT-01-…-RECONCILIATION-20260927.md:650-651`) |
| `/api/v3/commercial/credits/grant` | POST | `backend/api/v3_commercial.py:684` | Yes — billing admin | Credit grant (**not** access) |
| `/api/v3/ops/manual-processing/grants` | GET/PUT/DELETE | `backend/api/manual_processing_admin.py:71,153,252` | Yes — CarbonTally Admin | Manual-processing governance |

**Negative result:** No route string in `backend/**` contains `auditor`,
`readonly`, `read-only`, or `time-limited` (searches returned zero matches).

---

## 7. UI Inventory (Auditor / Audit / Evidence Related)

| Component Path | Route | Purpose | Wired? |
|---|---|---|---|
| `frontend/src/v3/components/RoleRoute.jsx` | (guard, all workspaces) | Role-scoped route gate — 5 scopes, **no auditor** | Yes (`App.js:1988…2267`) |
| `frontend/src/v3/admin/AuditTab.jsx` | Admin page tab | Customer org audit-readiness + activity + evidence-package download | Yes (`AdminPage.jsx:20`) |
| `frontend/src/v3/ops/AuditConsoleTab.jsx` | Ops console tab | Staff-admin audit trail | Yes (`OperationsPage.jsx:21,99`) |
| `frontend/src/v3/components/EvidenceTrail.jsx` | Embedded | Universal evidence-chain UI | Yes (`ReportDetailPage.jsx:16,203`, `ProcessingItemWorkspace.jsx:25,835`) |
| `frontend/src/v3/evidence/SourceEvidenceViewer.jsx` | `/evidence/line-items/:lineItemId` (`App.js:2083`) | Source-evidence viewer (secure doc + provenance) | Yes |
| `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx` | Embedded | View-only document container (`allowDownload`) | Yes |
| *(none)* named `AuditPortal` / `AuditorPortal` | — | — | **Absent** — whole-tree search for `auditor_portal`/`audit-portal`/`read_only_portal` returns 0 |

**Negative result:** `frontend/src/v3/**` contains **no** `Auditor` page, route or
navigation entry. The only `auditor` hits are the `AUDITOR_EXCEL` export option
(`App.js:1373`) and marketing/FAQ copy
(`frontend/src/public/faqData.js:453-455`, `LandingPage.jsx:74`, `AboutUs.jsx:54`).
`qa_harness/**` "auditor" hits are **test-harness classes**
(`TableAuditor`, `ResponsiveAuditor`) — not a portal
(`qa_harness/browser/tables/auditor.py:35`,
`qa_harness/browser/responsive/auditor.py:51`).

---

## 8. Build Distance Assessment

| Build Component | Current State | Remaining Work | Estimated Effort |
|---|---|---|---|
| Auditor identity / role | ABSENT | Define principal model (role value vs separate principal vs time-bound grant); add role/staff-role/grant rows; add resolution + refusal-by-default | Medium (design + schema) |
| Time-limited access grant w/ expiry | ABSENT (precedents: `report_shares`, invitations, beta codes) | New grant table (`expires_at`, `revoked_at`), issue/revoke service, server-side expiry enforcement, audit | Medium |
| Read-only route family | ABSENT (RoleRoute reusable) | Auditor scope in RoleRoute + backend guard; read-only navigation | Small–Medium |
| Auditor-scoped evidence viewer | ABSENT scope (viewer wired) | Auditor-safe projection + filter; accept auditor principal | Small–Medium |
| Auditor no-edit doc boundary | PARTIAL primitive | Auditor download policy decision + enforcement | Small |
| Auditor-scoped audit trail | ABSENT scope (trails wired) | Auditor scope on audit routes + filters | Small–Medium |
| Auditor export format | PARTIAL (`audit-package.json`) | Auditor-named format, time-bound delivery token | Small–Medium |
| Auditor section in package (FTR-209) | ABSENT | Define + add `auditor`/engagement block + attribution | Small |
| Reuse verification (FTR-033/053-056/101/126/204/207/209/223) | PRESENT (204/223 unapplied) | Apply/confirm 20260912 + 20260921 migrations | Small (ops) |
| Gap 7 assurance integration | ABSENT | Out of scope for Gap 6; noted as dependency | n/a (separate gap) |

---

## 9. Risks and Unknowns

- **Unverified items.**
  - Applied-but-unverified: `20260912000000_p7_audit_immutability_and_indexes.sql`
    (FTR-204) and `20260921000000_p8_s2_is_current_single_valued.sql` (FTR-223) —
    recorded **unapplied** in repository docs; no live confirmation.
  - Table-placement: `evidence_line_items` / `provenance_line_links` and
    `report_version_artifacts` are recorded "clone/qa-only; absent in flagship"
    (`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md:456`,
    `…FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md:107`).
  - `frontend_backup_pre_v3_public_20260827/**`, `admin/**`, `carbon-tally-ui-demo/**`
    were **not** exhaustively searched for auditor artifacts.
- **Assumptions requiring PO/engineering confirmation.**
  - Whether Gap 6 intends an *internal-user* auditor role, or a *non-user*
    time-bound external access grant (the historical position is explicitly the
    latter: "An external auditor is not automatically a tenant user;
    customer-authorized export/evidence workflows are preferred over direct
    auditor tenant access unless separately authorized",
    `docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md:175`).
  - What an "auditor export format" and an "auditor section" must contain.
  - Which database is authoritative for applying the blocked migrations.
- **Schema present in clones but not flagship (if applicable).** Yes — several
  reuse tables (evidence line items, provenance links, version artefacts) are
  recorded as clone/disposable-environment only; a portal built on them would
  inherit the same environment gap.

---

## 10. Recommendations for Next Research Pass

- **Specific files/modules/DBs to inspect.**
  - Confirm applied state of `20260912000000_p7_audit_immutability_and_indexes.sql`,
    `20260921000000_p8_s2_is_current_single_valued.sql`,
    `20260916000000_p8_b2_evidence_line_items.sql`,
    `20260916010000_p8_b2_provenance_line_links.sql`,
    `20260919000000_p8_b4_frozen_artefact.sql` in the authoritative DB (read-only
    `\dt`/`information_schema` query).
  - Read the full `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
    and `CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` for the
    ratified Phase 7 auditor-scope statement.
  - Read `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md:517-518,
    803-823` (external-auditor question set + the "does not authorize tenant
    access" note) to bound scope.
  - Inspect `frontend_backup_pre_v3_public_20260827/**` and `admin/**` for any
    prior auditor surface.
- **Questions for engineering.**
  1. Is an external auditor expected to be a **CarbonTally principal at all**, or
     is the intended model a **time-bound export/evidence grant** to an
     unauthenticated recipient?
  2. If a principal: does it live in `organization_members.role`, `staff_roles`,
     or a new table? (All three currently lock the auditor out.)
  3. Which existing expiry pattern (`report_shares` vs invitations) is the
     ratified base for the auditor grant?
  4. Is the `audit-package.json` payload the intended auditor deliverable, or is a
     distinct auditor format required?
  5. Is Gap 7 (assurance statements) a hard dependency for Gap 6, or independent?

---

## 11. Appendix — Raw Search Evidence

**Commands / searches run (read-only; no execution of npm/pip/make/python/pytest/playwright/migrations/seeders; no git; no DB mutation).**

- `list_files` over repository root, `backend/`, `frontend/src/`, `frontend/src/v3/**`,
  `docs/architecture/`, `database/**`, `qa_harness/`, `prisma/`, `supabase/migrations/`.
- `search_files` (recursive regex) for `(?i)auditor` across
  `backend/**` (34 hits — mostly comments/refusals), `frontend/src/**` (11 hits —
  no portal), `database/**` (0), `qa_harness/**` (19 — test harness only),
  `docs/**` (61), all `*.sql` (3 comment hits).
- `search_files` for `(?i)(expires_at|valid_until|access_grant|grant_expires|time_limited|expiry)`
  across `backend/**` and `supabase/migrations/**`.
- `search_files` for `(?i)(read_only|readonly|time_limited|external_auditor|assurance)`
  across `backend/**`.
- `search_files` for `(?i)@router\.(get|post|put|patch|delete)\("…(audit|export|grant|read[-_]?only)…"`
  across `backend/**` (23 hits; route table in §6).
- `search_files` for `(?i)(auditor_portal|audit_portal|auditor-portal|read_only_portal|time_limited_access|external_auditor)`
  across the whole repository → **0 results**.
- `search_files` for `(?i)gap[ _-]?6\b` across `docs/**` → only `FTR-GAP-6`
  (unrelated methodology gap, see §1).
- `search_files` for `(?i)CREATE TABLE[^;]*(role|grant|audit)` and
  `CREATE TABLE … (auditor|grant|expiry|access)` across `*.sql`.
- `search_files` for `(?i)(RoleRoute|SecureDocumentViewer|EvidenceTrail|SourceEvidenceViewer|AuditConsoleTab)`
  across `frontend/src/**` (122 hits).
- `read_file` on: `backend/api/v3_reporting.py`, `backend/api/v3_exports.py`,
  `backend/api/v3_evidence.py`, `backend/api/dependencies.py`,
  `backend/api/insight_authz.py`, `backend/api/consultant_auth.py`,
  `backend/data/roles.py`, `backend/data/exports.py`, `backend/data/reporting.py`,
  `backend/routes/admin/beta.py`, `backend/routes/admin/audit.py`,
  `frontend/src/v3/components/RoleRoute.jsx`,
  `frontend/src/v3/ops/AuditConsoleTab.jsx`, `frontend/src/v3/admin/AuditTab.jsx`,
  `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx`,
  `frontend/src/v3/api.js`, `frontend/src/App.js` (auditor greps),
  `supabase/migrations/00000000000000_init_schema.sql`,
  `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql`,
  `supabase/migrations/20260831020000_audit_activity_immutability.sql`,
  `supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql`,
  `docs/architecture/CT-GAP4-SUPPLIER-ENGAGEMENT-PORTAL-CURRENT-STATE-2026-09-30.md`
  (format reference).

**Negative results (searched but not found).**
- No `auditor` value in any role CHECK, seed or enum.
- No `auditor` column, table, policy or ROUTE anywhere (comments only).
- No `auditor_portal` / `audit_portal` / `read_only_portal` / `time_limited_access`
  identifier anywhere in the repository.
- No route string containing `readonly` / `read-only` / `time-limited`.
- No grant table carrying an `expires_at` column.
- No frontend `AuditPortal`/`AuditorPortal` component and no `/auditor` route.
- No assurance-statement model/table/service (Gap 7).

**Files inspected (representative).** See the `read_file` list above plus the
catalogue/verification docs cited inline:
`CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md`,
`CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md`,
`CT-PO-CARBONTALLY-CT-AUDIT-01-CANONICAL-AUDIT-SYSTEM-RECONCILIATION-20260927.md`,
`CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md`,
`CT-PO-PRODUCT-CAPABILITY-INVESTOR-DEMO-STUDY-20260924.md`,
`docs/cline/prompt-history/CT-P7-INDEPENDENT-VERIFICATION-20260912-005.md`,
`docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md`.
