# CarbonTally V3 — Security / Authorization Acceptance Findings

**Date:** 2026-08-28 · **Baseline:** `c36c848` (main) · **Environment:** local/dev. All tests were executed as the stated persona against the real API + database (no mocking, no UI-hiding assumptions). Every "denied" result is a server-side HTTP 403 observed in the response body.

---

## 1. Summary

- **P0 findings: none.** No cross-org data leak, privilege escalation, or data corruption was found.
- **P1 findings: one (SEC-1).** The Customer **Viewer** role can upload documents — a write operation on a read-only role.
- **Everything else denied correctly.** 18 further negative tests produced the correct 403.

| Test | Attempt (persona → action) | Result | Verdict |
|---|---|---|---|
| SEC-1 | Viewer → upload document to own org | **201 allowed** | ❌ **ALLOWED — bug** |
| SEC-2 | Viewer → create batch | 403 | ✅ denied |
| SEC-3 | Viewer → create facility | 403 | ✅ denied |
| SEC-4 | Viewer → approve processed item | 403 | ✅ denied |
| SEC-5 | Viewer → edit org profile | 403 | ✅ denied |
| SEC-6 | Owner B → read Org A facilities | 403 | ✅ denied |
| SEC-7 | Owner B → upload to Org A | 403 | ✅ denied |
| SEC-8 | Owner A → search documents in Org B | 403 | ✅ denied |
| SEC-9 | Reviewer → operator queue | 403 `can_process` | ✅ denied |
| SEC-10 | Reviewer → calculate item | 403 | ✅ denied |
| SEC-11 | Customer admin → staff ops surface | 403 `all-false` | ✅ denied |
| SEC-12 | PE → org-scoped queue | 403 org access | ✅ denied |
| SEC-13 | PE → read customer org documents | 403 | ✅ denied |
| SEC-14 | PE → post message to customer conversation | 403 | ✅ denied |
| SEC-15 | PE → download customer document | file_url empty / no path | ✅ denied (boundary holds) |
| SEC-16 | Consultant → upload into client org | 403 | ✅ denied (but see CON-2 — this is the *functionality* gap, not a security failure) |
| SEC-17 | Factor creator → approve own factor | 403 self-approval | ✅ denied |
| SEC-18 | Customer → cross-org conversation access | 403 / not listed | ✅ denied |
| SEC-19 | Non-staff → `/api/v3/ops/me` | 403 | ✅ denied (noise only, PERF-2) |

---

## 2. Detailed findings

### 2.1 SEC-1 (P1, authorisation) — Viewer can upload documents

- **Persona:** Customer Viewer (role = `viewer`; read-only per the V3 role model).
- **Endpoints:** `POST /api/v3/uploads` (multipart).
- **Observed:** viewer token → **201**, response includes `organization_id` and `name`; the object is visible in the org document list (`viewer_up.pdf` in Test Organisation A).
- **Root cause:** the upload endpoint authorises with org-**membership** (`require_org_member()`); `viewer` is an org member. There is no member-role ("contributor") check on this path. The sibling write endpoints (batch create, facility create, item approval) use `require_org_admin()` and therefore correctly reject the viewer.
- **Impact:** a read-only user can add documents to the organisation's data; downstream this could trigger processing work and pollute evidence. No cross-org impact (org-scoped RLS still holds).
- **Fix:** CL-01 (require member+/non-viewer on all write endpoints; audit the endpoint list for other `require_org_member()` write paths).
- **Also observed:** the viewer-created document is fully consistent with the org (RLS correct). The bug is role authorisation, not tenant isolation.

### 2.2 Org/tenant isolation (all passed)

- Cross-org reads, uploads, and searches are denied with **403** at the API layer for both directions (Owner B↔Org A). RLS on `organization_members`/`documents`/etc. is active and denies without policies. PostgREST queries by non-members return `Organization access denied` (API) / empty or error (direct RLS).
- **DB evidence:** `organization_members` has RLS enabled (`relrowsecurity=t`); per-table RLS verified via behavioural tests rather than policy listing (audit does not modify policies).

### 2.3 PE boundary (all passed)

- PE staff (entity-staff) cannot:
  - read the org-scoped operations queue (403),
  - read customer organisation documents (403),
  - download customer documents (item `file_url` empty; no download endpoint for PE),
  - message customer organisations (403) — **customer ↔ PE direct messaging is impossible** (N1 isolation).
- PE **can** see and process only work assigned to their entity (verified: assigned batch appears; unassigned orgs invisible). `max_concurrent_tasks` and claim/start semantics enforce the PE work scope.

### 2.4 Role gates inside CarbonTally (all passed)

- Reviewer (`can_review`) cannot use the operator queue (`can_process` required) — 403.
- Reviewer cannot calculate — 403 (`can_process`).
- QC (`qc_specialist`, `can_review + can_process`) can validate; QC tab honestly reports quality-data model limitations.
- Customer admin is not staff: `/api/v3/ops/me` → 403.
- Staff-role management (`can_manage_staff`) is admin-only (staff `admin` role).

### 2.5 Messaging isolation (all passed except creation)

- PE → customer conversation: 403.
- Cross-org conversation listing: org-scoped (`list_conversations` authorised for org members / active-grant consultants only).
- Consultant → active-client conversations only; switching clients re-scopes the conversation list.
- **Exception (availability, not isolation):** conversation creation always fails (MSG-1, CL-03) and leaves orphan threads. The participant table is currently empty, so participant-scoped authorisation is inert; once CL-03 adds the unique constraint + transaction, re-run the isolation tests.

### 2.6 Custom-factor approval (all passed)

- Owner-created factor: self-approve → 403 (`a factor's creator cannot approve their own factor`).
- Owner-created factor approved by Admin → 200 `active`.
- Draft-only editing; approved factors return 409 for edits (versioned changes only).
- **Remaining gap (product, not security):** single-admin orgs have no approver — PO-1.

### 2.7 Notifications RLS (informational)

- `notifications` has **RLS enabled with zero policies** (verified via `pg_policies` = 0 rows for the table) — this is a **deny-everything** state, so no data is exposed, but the frontend's direct Supabase read fails for every user (PERF-1). The backend `/api/v3/notifications` (service-role) works. Fix direction: CL-10 (add owner-scoped policies and/or move the UI to the API).

---

## 3. Document / evidence boundary

- No persona outside the owning org (and its active-grant consultant) can read customer documents at the API/DB layer.
- PE download prevention is enforced at the data layer (no signed URL / empty `file_url` for PE-facing item payloads) **and** at the API (403 on org document reads). No browser-only hiding.
- Upload objects are org-scoped in storage paths and RLS-scoped in metadata (verified by cross-org upload denial + same-org visibility).

---

## 4. Residual risks / recommendations

1. **Audit all `require_org_member()` write endpoints** for the viewer gap (SEC-1) — uploads confirmed; batch/facility/approval already admin-gated.
2. **After CL-03**, re-test messaging participant isolation (participant-scoped authorisation becomes live for the first time).
3. **Notifications policies** should be added (CL-10) — current deny-all is safe but fragile.
4. **`staff_roles` stray row** (`t_ba_34e3cb`) is test residue in a role table that drives staff creation — remove it (CL-17).
5. **No credentials, tokens, or passwords** are included in this report or any audit deliverable.

---

## 5. Investor-scale continuation security evidence (2026-08-28, second session)

Negative tests re-run/expanded against the new self-service org `OHD Audit Org Ltd` (`290ed626-…`) and demo tenants. All denied **server-side** (no hidden-UI effects).

| # | Attempt | Actor | Result |
|---|---|---|---|
| N-01 | `GET /api/v3/documents/{granite-doc}` | OHD owner (other org) | **403** Organization access denied |
| N-02 | `GET /api/v3/documents?organization_id={granite}` (list) | OHD owner | **403** |
| N-03 | `GET /api/v3/documents/{ohd-file}` | PE `entity-staff@demo` | **403** Organization member access required |
| N-04 | `GET /api/v3/documents/{file}/signed-url` (OHD file) | PE staff | **403** |
| N-05 | `GET /api/v3/documents/{file}/signed-url` (Granite file) | PE staff | **403** — PE no-download boundary holds for all tenants |
| N-06 | `POST /api/v3/messaging/conversations/{granite-conv}/messages` | PE staff | **403** Messaging requires active membership/grant/staff — **Customer ↔ PE direct messaging blocked** |
| N-07 | `POST /api/v3/messaging/conversations/{granite-conv}/messages` | OHD owner | **403** — cross-org messaging blocked |
| N-08 | `POST /api/v3/organizations/{granite}/facilities` | viewer@demo | **403** Organization admin privileges required |
| N-09 | `POST /api/v3/customer-factors/{id}/approve` | factor creator (owner) | **403** self-approval prevention (D-cf-3) |
| N-10 | `POST /api/v3/ops/me` | customer (OHD owner) | **403** Staff access required (role separation) |

**Conclusions (continuation):** the authorisation surface remains correct — org isolation (both directions), PE no-download, PE messaging boundary, viewer write denial, factor self-approval prevention, and customer/staff role separation all hold at the API layer. **No P0 security issue found.** The only authorisation defect remains prior SEC-1 (viewer upload) — unchanged code.

**Non-security defect surfaced during boundary testing:** `POST /api/v3/organizations/{org}/assets` with `facility_id:null` returns **500** (DB NOT NULL violation) instead of 422 — a robustness defect (ISC-4/CL-28), not a security leak (no data exposed).

## 4. Session-3 negative-test evidence (investor-scale battery, 2026-08-28)

| # | Attempt | Actor | Result |
|---|---------|-------|--------|
| N-11 | `GET /api/v3/documents?organization_id=<Org B>` | Owner Org A (Quayside) | **403** |
| N-12 | `GET /api/v3/organizations/<Org B>/facilities` | Owner Org A | **403** |
| N-13 | `GET /api/v3/documents?organization_id=<Org A>` | Owner Org B (Granite) | **403** |
| N-14 | `GET /api/v3/documents?organization_id=<same-consultant other client org>` | Client owner 1.1 (consultant 1) | **403** |
| N-15 | `GET /api/v3/consultants/clients/{id}` | Consultant 1 → consultant 2's client | **403** |
| N-16 | `GET /api/v3/ops/entities/{pe}/extraction/next-item` (unassigned) | PE staff Alpha | **403** "staff lacks permission: can_process" |
| N-17 | `GET /api/v3/documents?organization_id=<customer>` | PE manager Alpha | **403** |
| N-18 | `POST /api/v3/messaging/conversations/{customer_conv}/messages` | PE manager Alpha | **403** |
| N-19 | `POST /api/v3/customer-factors/{id}/approve` | Viewer / Member (non-admin) | **403** (both) |
| N-20 | `POST /api/v3/ops/items/{id}/calculate` | Reviewer (no can_process) | **403** |
| N-21 | `GET /api/v2/admin/audit` | **System admin** | **403** "Admin privileges required" (staff-admin → 200) — role-matrix inconsistency ISC-10/CL-33, denies-too-much not data exposure |
| N-22 | `POST /api/v3/organizations/{org}/members` | Member (non-admin) | **403** |

**Conclusions (session 3):** all twelve new boundary attempts were correctly denied server-side. Cross-tenant (org↔org), same-consultant client-org, consultant↔consultant, PE document + messaging, factor-approval, reviewer-calculate, and member-invite gates all hold. **No P0 security issue found.** Two non-security correctness items surfaced: (1) `system_admin` role cannot audit/bill (ISC-10 — functional gap, no leak); (2) custom-factor create 500 on duplicate family (ISC-8 — robustness, no leak).

*Companion deliverables: Master Acceptance Audit (`CARBONTALLY_V3_FULL_PERSONA_ACCEPTANCE_AUDIT.md`), Investor-Scale continuation audit (`CARBONTALLY_V3_INVESTOR_SCALE_ACCEPTANCE_AUDIT.md`), Persona Test Matrix, Cline Implementation Backlog.*
