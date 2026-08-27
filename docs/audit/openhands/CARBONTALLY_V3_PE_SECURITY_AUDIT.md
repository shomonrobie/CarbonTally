# CarbonTally V3 — Processing Entity Technical Security & Access-Control Audit

**Audit:** Processing-Entity workforce authorization chain, document/storage security,
RLS storey, assignment/QC gates, and the issues storey.
**Audited commit:** `d4dcca1eb11f86bcae497815c8592d688a7e305f` — `feat(v3): commit D20-D37
commercial platform release` (`origin/main`, checked out clean in the read-only worktree
`/tmp/ct_pe_audit`).
**Note on the requested SHA:** `945806c073bdaedae2a621b9cee42e419f14a75` does **not** exist —
not locally, and not on `github.com/shomonrobie/CarbonTally` (GitHub API: "No commit found").
The repository's actual current commit is `d4dcca1` (local clone and remote agree). The audit
was therefore performed against `d4dcca1`, which is the only state available.
**Method:** read-only source inspection of `backend/`, `supabase/migrations/`,
`frontend/src/v3/`, plus execution of the unit test suite (535+ API unit tests) against the
checkout. No code changes; the developer's main CarbonTally directory was not touched.

---

## 1. Executive summary

The processing-entity (PE) workforce authorization chain is **soundly designed and, on the
V3 surface, consistently enforced.** The D20 scope-first model (internal staff vs entity
staff), the D22 assignment model (exactly one processing party per batch, CarbonTally-controlled
assignment, audited reassignment), the private-storage/signed-URL story (D32), and the
deny-by-default RLS storey (init schema + RC2 tenant loop + V3M-6 `is_entity_member` + D22
batch/item policies) all hold up under inspection and under the security test suite
(65/65 security-focused tests pass; full unit suite 1051 passed / 5 failed).

Six findings were identified — two medium, three low/robustness, one defense-in-depth:

| # | Severity | Finding |
|---|---|---|
| F1 | **P2** | Suspended/terminated entity staff retain **API read access** to the entity dashboard, performance report, and entity issues/review lists (no `status='active'` gate on these read endpoints; only extraction *writes* gate on active). |
| F2 | **P2** | Legacy upload surface IDOR: `GET /api/upload/batches/stats?organization_id=…` and `GET /api/upload/batches/{id}/progress` lack org-scope checks (any authenticated user, incl. entity staff/unbound users). |
| F3 | **P3** | `require_org_admin`'s authoritative fallback calls `get_supabase_client()` outside its `try/except` → 500 instead of 403 when Supabase init fails; causes 5 failing unit tests. |
| F4 | **P3** | 171 legacy references to `current_user.id` (non-existent attribute; the field is `user_id`) → AttributeError → 500 on legacy org-scoped endpoints; fail-closed but broken surface. |
| F5 | **P3** | XOR invariant (`assigned_to` vs `entity_id`) is enforced in the API only — no DB CHECK constraint (defense-in-depth). |
| F6 | **P3** | Dual-scope combinations are not prevented at provisioning: a user could hold both entity-staff AND customer-org membership (or consultant membership); V3 API blocks the org path for entity staff, but RLS tenant policies and legacy routes would still honor the org membership. |

---

## 2. Verified controls (with evidence)

### 2.1 Authorization chain (D20) — CONFIRMED
`backend/auth.py` `get_current_user` → JWT (Supabase) → optional `staff_profiles` row →
`staff_roles.permissions` (authoritative) → entity scope via `staff_profiles.entity_id`.
- `AuthUser.is_internal_staff` = `is_staff and not entity_id`; `is_entity_staff` =
  `is_staff and bool(entity_id)`.
- `is_admin` (global admin) is explicitly scoped to **internal** staff:
  `is_staff and entity_id IS NULL and role/role_name == 'admin'` — a PE staff profile with an
  `admin`-named role can never become a global admin (verified in code and in
  `test_b_entity_staff_admin_role_is_not_internal_admin`).
- `require_admin` re-checks the same D20 gate, so `/api/v3/admin/*` review-queue and
  `/api/v3/processing-entities` CRUD are entity-staff-proof.

### 2.2 Entity workspace guard (D22) — CONFIRMED
`backend/api/operations_auth.py`:
- `_entity_workspace_guard`: own-entity + `can_process`; stage allowlist is
  extraction/mapping/calculation only — validation/review/QC are CarbonTally-only gates.
- `_get_item_and_batch`: internal staff may view any batch; entity staff only own-entity.
- `assign_batch`: internal staff only (`can_manage_staff` + `can_process`); exactly ONE
  processing party (internal operator XOR entity); reassignment clears the other side and
  records before→after + reason via `audit_trail` (ADR-V3-013; no new history table);
  assignment to a non-`active` entity rejected.

### 2.3 Private document storage (D32) — CONFIRMED
- `documents` bucket is **PRIVATE**; only short-lived signed URLs via
  `services/storage.py::storage_signed_url`; `path_from_url` normalizes public/signed/bare
  paths.
- `v3_documents.py` re-issues a fresh signed URL per view; `GET /documents/{id}/signed-url`
  is org-member + `ensure_org_access` gated.
- PE staff receive **raw storage paths** (never signed URLs) — verified end-to-end in
  `frontend/src/v3/ops/EntityExtractionWorkspace.jsx` (items carry `file_url`, no signed
  fetch). This is a deliberate gap (see F7/note §6).

### 2.4 RLS storey — CONFIRMED (init → RC2 → V3M-6 → D22)
- `00000000000000_init_schema.sql`: loop `ENABLE ROW LEVEL SECURITY` on every public table
  (deny-by-default).
- `20260803000000_rc2_rls.sql`: dynamic tenant policy loop (SELECT/INSERT/UPDATE/DELETE) for
  `authenticated` keyed on `organization_members`/`is_org_member`.
- `20260810050000_v3m6_entity_rls.sql`: `is_entity_member()` helper (active entity +
  matching `staff_profiles.entity_id`); entity-scoped policies are deny-by-default/additive.
- `20260821020000_d22_processing_work_assignment.sql`: entity-scoped **SELECT** policies on
  `manual_extraction_batches` (`entity_id IS NOT NULL AND is_entity_member(entity_id)`) and
  `manual_extraction_items` (via batch join); items have no other authenticated policy.
- `20260822010000_d27_d19_customer_lifecycle.sql`: fixes the D26 §42 gap —
  `conversation_participants` had ZERO policies (deny-all) → recursion-safe SELECT added;
  PE staff get **no** messaging storey (D18 boundary preserved).
- Later migrations (D35 onboarding, D37 billing) are additive and deny-by-default.

### 2.5 Issues storey — CONFIRMED
- `issues.entity_id UUID REFERENCES processing_entities(id) ON DELETE RESTRICT`.
- Customer-facing `/api/v3/issues` surfaces exclude entity-scoped rows (404 / filtered out,
  `entity_id` forced NULL on create).
- Entity staff read own-entity issues via `/admin/entity/{entity_id}` +
  `require_entity_member`; `/admin/open` is `require_admin` (CarbonTally-internal).
- D22 adds `issues.manual_extraction_batch_id` FK for mediated clarification
  (Entity → CarbonTally → Customer; never direct).

### 2.6 Other gates — CONFIRMED
- `ensure_org_access` (D20): PE staff hard-denied customer orgs; internal staff any-org;
  org members own-org only.
- Messaging: `_authorize_org_actor` = org member OR active consultant-client grant; PE staff
  403; RLS has no entity messaging storey.
- Consultant surface: `require_consultant` (active firm member) + `ensure_consultant_org_access`
  (active `consultant_clients` grant only, D15/D27 lifecycle).
- White-label: custom domains **never grant authorization** (D27/d21 design, verified in
  `v3_whitelabel.py`).
- Evidence traceability (D33): `/emissions/{log_id}/evidence` is org-member +
  `ensure_org_access`, returns a **fresh signed URL** (never a public URL).
- Secrets: all credentials come from environment variables (`SUPABASE_SERVICE_KEY`,
  `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`, LLM keys); no hardcoded secrets in Python sources.
- AI extraction engine (`engines/ai_extraction.py`) can send document text to an external LLM,
  but is **not wired into the HTTP API surface** (only `engines/workflow.py` + tests) — see §6.

---

## 3. Findings

### F1 — Suspended/terminated entity staff keep API READ access to entity dashboard/performance/issues (P2)

**Where:** `backend/api/v3_operations.py::entity_dashboard`, `v3_reporting.py` (or
`api/v3_operations.py`) `entity_performance_report`, `backend/api/issues.py::list_entity_issues`;
guard `auth.require_entity_member` / `api.operations_auth.require_entity_scope`.

**Issue:** `_entity_workspace_guard` gates extraction *writes* on `entity.status == 'active'`,
and RLS `is_entity_member` requires an active entity, so **direct DB reads** by a suspended
entity's staff are denied. But the API reads bypass RLS (service-role pool) and only check
`current_user.entity_id == entity_id` — a `suspended`/`terminated` entity's still-active staff
profiles can keep reading the entity dashboard (review/issues/staff aggregates, SLA breach
counts), the performance report, and the entity's issue list. No automation deactivates entity
staff when an entity is suspended/terminated. No test covers suspended-entity read access
(the only suspended-entity fixture in `test_v3_entity_extraction.py` is not exercised against
these endpoints).

**Recommendation:** add an `entity.status == 'active'` gate to `require_entity_scope` /
`require_entity_member` (single place), or to `entity_dashboard` / `entity_performance_report`
/ `list_entity_issues`; add negative tests for suspended/terminated entities on all read
surfaces; optionally auto-deactivate staff profiles when an entity leaves `active`.

### F2 — Legacy upload IDOR: `GET /api/upload/batches/stats` and `.../progress` (P2)

**Where:** `backend/routes/upload.py` (mounted in the legacy `main.py` app at `/api`).

- `GET /api/upload/batches/stats?organization_id=<any>` — when the caller supplies
  `organization_id`, the query is filtered by it **without any membership check**
  (`elif not current_user.is_admin` branch is skipped). Any authenticated user — including a
  PE staff member or an unbound user — can enumerate batch statistics (counts, statuses, file
  totals) for any organisation.
- `GET /api/upload/batches/{batch_id}/progress` — **no authorization check at all**; any
  authenticated user can read upload progress (file counts, status, timestamps) of any batch
  by UUID.

Sibling endpoints (`status`, `cancel`) do perform an org-membership check — confirming these
two are omissions, not a design pattern.

**Recommendation:** enforce org membership for the caller-supplied `organization_id` (and the
batch's org) on both endpoints, or decommission the legacy upload routes in favour of
`/api/v3/uploads` / `/api/v3/documents` (the V3 surfaces are correctly scoped).

### F3 — `require_org_admin` fallback calls `get_supabase_client()` outside its try/except → 500 (P3)

**Where:** `backend/auth.py::require_org_admin` (~line 469).

`supabase = get_supabase_client()` sits **outside** the `try/except Exception: pass` that wraps
the authoritative membership lookup. When the client cannot initialise (no credentials — as in
test environments — or a transient Supabase outage), a denied org-member request returns
**500** instead of **403**. This is fail-closed (no data exposure) but noisy, and it breaks
5 unit tests: `test_v3_customer_admin.py::test_update_profile_requires_admin`,
`test_update_metadata_requires_admin`, `test_add_member_requires_admin`,
`test_invitations_requires_admin`, `test_member_cannot_create_facility` (all `assert 500 == 403`).

**Recommendation:** move `get_supabase_client()` inside the `try`, or wrap the whole fallback
in try/except and default to the 403 raise.

### F4 — Legacy routes reference `current_user.id` (171 occurrences) → AttributeError → 500 (P3)

**Where:** `AuthUser` (pydantic) exposes `user_id`, **not** `id`. `grep -rn "current_user.id" backend/routes/` returns **171 hits** across the legacy surface (`routes/organizations/*`, `routes/emissions.py`, `routes/upload.py`, `routes/reference.py`, …).

Every such reference raises `AttributeError` on non-admin users → caught by the generic
`except Exception` → 500. Consequences:
- Membership checks written as `.eq('user_id', current_user.id)` never evaluate (the intended
  cross-org 403 becomes a 500).
- Data writes (`updated_by = current_user.id`, `created_by = current_user.id`) fail on the
  legacy path.

This is **fail-closed** but means the legacy surface is effectively broken for ordinary users
and is untested against the current auth model. One file even carries the comment
"Use current_user.user_id instead of current_user.id" (`routes/reports.py:512`).

**Recommendation:** mechanical sweep of the 171 occurrences → `current_user.user_id`; add a
legacy-route regression test; treat the legacy surface as a decommission candidate.

### F5 — Assignment XOR invariant is API-only (no DB CHECK) (P3)

**Where:** `20260821020000_d22_processing_work_assignment.sql` — the column comment documents
"exactly ONE processing party (entity_id OR assigned_to)" but no CHECK constraint is created.
The invariant is maintained only by `assign_batch` / `update_batch` in the API.

All writes are service-role, so the realistic risk is low (a coding slip, not an attacker).
Still, a DB-level guard is cheap defense-in-depth. Note the self-serve open queue
(`entity_id IS NULL AND assigned_to IS NULL`) must remain legal, so the CHECK would be
`NOT (entity_id IS NOT NULL AND assigned_to IS NOT NULL)`.

### F6 — Dual-scope combinations not prevented at provisioning (P3)

Nothing prevents a single auth user from holding **both** a `staff_profiles` row with
`entity_id` (PE staff) **and** an `organization_members` row (customer org member) or a
`consultant_firm_members` row. The V3 API correctly denies the customer-org path for entity
staff (`ensure_org_access`/`is_entity_staff`, messaging and consultant guards), but:
- RLS tenant policies (`organization_members`-based) would still grant the user DB-level read
  on the org's rows, and
- legacy routes honor the org membership directly.

**Recommendation:** add a provisioning-time guard (internal staff admin) that rejects
creating/assigning entity staff for users who already hold org/consultant memberships, and
document the intended boundary explicitly.

---

## 4. Test results

Executed in the checkout (in-memory fakes, no DB access; venv at `/tmp/ct_pe_venv`):

- Security-focused suites — **65/65 pass**:
  `test_scope_aware_authorization.py`, `test_operations_auth.py`, `test_v3_entity_extraction.py`,
  `test_storage_security.py`. Coverage includes: entity staff cannot touch another entity's
  workspace, never see internal batches, cannot fake the `entity_id` parameter, cannot pass
  internal/global-admin gates, denied customer-org/consultant/messaging surfaces; internal
  operators blocked from entity batches; assignment requires exactly one party; reassignment
  records history; cross-org signed URL denied; `path_from_url` normalization.
- Full API unit suite: **535 passed, 5 failed** (all 5 are F3 — `require_org_admin` 500-vs-403
  in an environment without Supabase credentials).
- Full `tests/unit/`: **1051 passed, 5 failed** (same 5).

No integration tests were run (they require a live database).

---

## 5. Overall assessment

The V3 processing-entity access-control implementation is mature and internally consistent:
the scope-first authorization chain, deny-by-default RLS with additive entity storeys, private
storage with short-lived signed URLs, and the mediated-clarification issues storey all match
their declared designs (D20/D22/D27/D32/D33/D35/D37, ADR-V3-013). The most security-relevant
deficiencies are the two P2s: entity read endpoints not gated on entity lifecycle status (F1)
and the legacy upload IDOR (F2). The remaining items are fail-closed robustness/defense-in-depth
issues. None of the findings allow cross-entity data disclosure on the **V3** surface; the
legacy surface is where the IDOR and the `current_user.id` breakage live, and it is the
strongest candidate for decommissioning or a scoping sweep.

---

## 6. Informational notes

- **N1 — Legacy signed-URL exposure (P0 candidate, carried from prior passes):** legacy routes
  (`/api/documents`, `/api/customer-documents`, `routes/organizations/files.py`
  `/{file_id}/download`, `require_org_member` + org_id) predate D32's private-bucket
  migration; they must be verified against the PRIVATE bucket semantics and either scoped to
  signed URLs or decommissioned. This pass reconfirmed their existence (see F2/F4 for adjacent
  legacy defects) but did not find a live path that hands a long-lived public URL to a
  non-owner.
- **N2 — AI/LLM extraction is not exposed via the API** today; if enabled later, document
  content would be transmitted to a third-party LLM endpoint (server-side, server-held key) —
  a data-processing consideration requiring consent/DPIA rather than an access-control defect.
- **N3 — CORS:** explicit production origin allow-list with `CORS_ALLOW_CREDENTIALS=True`;
  the `https://*.onrender.com` entry is ineffective under Starlette's exact-match semantics
  (harmless). `CORS_ALLOW_HEADERS=["*"]` reflects request headers — acceptable given the
  restricted origin list.
- **N4 — Entity document viewing:** entity staff see raw storage paths (no signed URLs). The
  corresponding UI (document viewer in the entity workspace) therefore cannot render
  documents client-side; if document preview for entity staff is desired, add an
  entity-scoped signed-URL endpoint (mirroring `v3_documents` but guarded by
  `_entity_workspace_guard` + `can_process`), not a widening of the org-member endpoint.
