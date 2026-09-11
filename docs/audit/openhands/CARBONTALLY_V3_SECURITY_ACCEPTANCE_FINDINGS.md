# CarbonTally V3 — Security / Authorization Acceptance Findings

**Date:** 2026-08-28 · **Baseline:** `c36c848` · **Environment:** local/dev.
All tests executed as the stated persona against the real API + database (no mocking, no
UI-hiding assumptions). Every "denied" is a server-side HTTP 403 observed in the response body.

---

## 1. Summary

- **P0 findings: none.** No cross-org data leak, privilege escalation, data corruption, or
  unauthorised access to another organisation's data was found.
- **P1 findings: one authorization defect.** The Customer **Viewer** role can upload documents
  (a write on a read-only role) — **SEC-1**.
- **P1 findings: one role-mapping gap (availability, not a leak).** The **System Admin** role
  cannot reach admin-gated configuration surfaces (retention, commercial) — **SEC-2**.
- **Everything else denied correctly.** All other negative tests produced the correct 403 or
  had no code path (document download for PE).

## 2. Negative-test results table

| # | Attempt (persona → action) | Result | Verdict |
|---|---|---|---|
| SEC-1 | Viewer → upload document to own org | **201 allowed** | ❌ **ALLOWED — authorization bug** |
| SEC-2 | System Admin → retention config / commercial config | **403 `Admin privileges required` / `staff lacks permission`** | ⚠ denied, but the role should be able to (role-mapping gap) |
| SEC-3 | Member → approve processed item | 403 `Organization admin privileges required` | ✅ denied |
| SEC-4 | Viewer → approve processed item | 403 | ✅ denied |
| SEC-5 | Member → edit org profile | 403 | ✅ denied |
| SEC-6 | Viewer → edit org profile | 403 | ✅ denied |
| SEC-7 | Member → add org member | 403 | ✅ denied |
| SEC-8 | Viewer → add org member | 403 | ✅ denied |
| SEC-9 | Owner A → read Org B facilities/assets/docs | 403 | ✅ denied |
| SEC-10 | Owner B → search Org A | 403 `Organization access denied` | ✅ denied |
| SEC-11 | Owner A → upload into Org B | 403 | ✅ denied |
| SEC-12 | Consultant → upload into client org | 403 `Organization member access required` | ✅ denied (functionality gap, not a leak) |
| SEC-13 | Consultant → org-scoped search (client org) | 403 `Organization member access required` | ✅ denied |
| SEC-14 | Reviewer → operator queue | 403 `staff lacks permission: can_process` | ✅ denied |
| SEC-15 | Reviewer → calculate item | 403 `can_process` | ✅ denied |
| SEC-16 | Customer admin → staff ops surface | 403 (all-perms false) | ✅ denied |
| SEC-17 | PE → org-scoped queue | 403 org access | ✅ denied |
| SEC-18 | PE → read customer org documents | 403 | ✅ denied |
| SEC-19 | PE → post to customer-org conversation | 403 | ✅ denied (Customer↔PE direct messaging impossible) |
| SEC-20 | PE → download customer document | No path; `file_url` empty | ✅ boundary holds |
| SEC-21 | Owner → self-approve own custom factor | 403 | ✅ denied (see CF-1 for the single-owner dead-end) |
| SEC-22 | Operator/Reviewer/QC → retention config | 403 | ✅ denied |

## 3. Detailed findings

### SEC-1 (P1) — Viewer can upload documents

`POST /api/v3/uploads` (multipart) returned **201 with a created `organization_files` row and a
storage object** for `viewer.demo0001` (Org A). The endpoint authorises with
`require_org_member()` + `ensure_org_access()`, and the Viewer role is an org member. The UI
disables the upload button for viewers, but the API accepts the write — a real authorization
defect on the read-only role. Member uploads must remain allowed; viewer must be denied.

### SEC-2 (P1, availability) — System Admin cannot operate admin-gated configuration

`system-admin.demo` received 200 on `/ops/me`, `/ops/staff`, `/ops/entities`,
`/ops/dashboard`, `/ops/queues/review` but **403 on `/api/v3/settings/retention`** and
**403 on `/api/v3/commercial/*`**. `require_admin()` matches only the role literally named
`admin`; the `system_admin` staff role is not mapped to admin authority. This is a
functionality/role-mapping gap (the role exists but is half-wired), not a data exposure.

### SEC-3 (P1, broken gate) — customer approval gate unreachable (not a security failure)

The customer approval gate itself is correctly restricted (owner/admin only; rejection
requires a reason; D5/D37 billing charge on approval). However the gate cannot be reached
because the review queue endpoint 500s (`column reference "id" is ambiguous`). Recorded here
for completeness: the *authorization* is sound, the *availability* is broken (see PRC-3).

## 4. RLS / data-boundary observations

- **`notifications`:** RLS enabled, **zero policies** → direct anon/user queries always fail
  (this is why the bell is broken). This configuration is safe (deny-by-default) but means the
  legacy direct-table path can never work; the bell must use `/api/v3/notifications` (CL-11).
- **`vehicles`:** table absent entirely (migration not applied) — the search SQL that reads it
  raises 500. Applying the migration must ship with org-scoped RLS policies verified.
- **Storage (`documents` bucket):** private bucket + signed URLs; PE has no download path and
  `file_url` is empty for PE-facing items (D20 boundary holds).
- **Cross-org data:** verified denied at API layer for documents, search, facilities, assets,
  uploads in both directions between Org A and Org B.
- **Custom factors:** self-approval denied; owner/admin can approve others' factors; approval
  is not possible in single-owner orgs (PO decision CF-1).

## 5. Recommendations (security-relevant, for Cline)

1. Restrict the upload endpoint to owner/admin/member (SEC-1). — P1
2. Map the `system_admin` role to admin authority for platform configuration, or explicitly
   document/hide those surfaces for it (SEC-2). — P1
3. Apply the vehicles migration and verify its RLS policies (search knock-on). — P1
4. Add a unique index on `conversation_participants (conversation_id, user_id)` and re-run the
   N1 isolation matrix (messaging creation 500). — P1
5. Keep RLS deny-by-default on `notifications`; move the bell to the API surface. — P2
6. After the review-queue SQL fix, re-run the approval matrix (owner/admin approve; member/
   viewer 403; rejection-reason required). — P1
7. Consultant write-scope for future create/upload/process surfaces must be active-client
   scoped and revocable (see backlog CL-7; PO decision required). — P1 (design gate)
