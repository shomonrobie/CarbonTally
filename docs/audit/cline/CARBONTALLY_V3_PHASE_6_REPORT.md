---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CarbonTally_V3_Architecture_Specification_v1.0.md, CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md, V3M2 schema (RC2)
---

# CarbonTally V3 — Phase 6: Customer Administration Report

## 1. Implemented capabilities

| # | Capability | Status |
|---|---|---|
| 1 | Organization profile | **COMPLETE (read) / PARTIAL (write)** — full real profile read via `GET /api/v3/organizations/{id}/profile`; admin update via `PUT` on a strict real-column whitelist |
| 2 | Organization settings | **COMPLETE** — settings/metadata read (`GET /{id}/metadata`) + admin update (`PUT /{id}/metadata`) over real V3M2 columns |
| 3 | Members | **COMPLETE** — list (email-enriched via `users`), detail, add, role update, remove (org-isolated, admin-guarded) |
| 4 | Invitations | **COMPLETE** — `user_invitations` repository + list/create/revoke endpoints (admin, org-isolated) |
| 5 | Roles | **COMPLETE** — the V3 customer role model (`organization_members.role` CHECK: owner/admin/member/viewer) surfaced read-only; role assignment validated against it (422 on invalid) |
| 6 | Suppliers | **COMPLETE** — list/get/create/update/remove + read-side search/filter (search / category / status) over real columns |
| 7 | Facilities | **COMPLETE** — list/create/remove + detail (with real asset relationship) |
| 8 | Assets | **COMPLETE** — list/create/remove + detail |
| 9 | Security settings | **PARTIAL** — account info + sign-in provider (real Supabase Auth data), change-password via `supabase.auth.updateUser`; MFA/TOTP **NOT IMPLEMENTED** (documented limitation, no fake MFA) |
| 10 | Authentication/provider info | **COMPLETE** — real Supabase Auth provider + identities surfaced read-only; no custom authentication |
| 11 | MFA/TOTP interface | **NOT IMPLEMENTED** — documented limitation (no CarbonTally MFA surface; Supabase platform MFA enablement unverifiable here) |

## 2. Files created

| File | Purpose |
|---|---|
| `backend/data/invitations.py` | `InvitationsRepository` over `user_invitations` |
| `backend/data/roles.py` | `RolesRepository` (read-only `roles` reference) |
| `backend/tests/unit/api/test_v3_customer_admin.py` | Route registration + API behaviour tests |
| `backend/tests/integration/test_customer_admin.py` | Integration tests for the new repo surfaces |
| `frontend/src/v3/admin/AdminPage.jsx` | Customer administration hub (tabbed) |
| `frontend/src/v3/admin/ProfileTab.jsx` | Organization profile + settings (read/edit) |
| `frontend/src/v3/admin/MembersTab.jsx` | Members + invitations + roles |
| `frontend/src/v3/admin/SuppliersTab.jsx` | Suppliers (search/filter/create/remove) |
| `frontend/src/v3/admin/FacilitiesTab.jsx` | Facilities + assets |
| `frontend/src/v3/admin/SecurityTab.jsx` | Security (provider info, password, MFA limitation) |
| `frontend/src/v3/admin/admin.css` | V3 admin stylesheet |
| `docs/audit/cline/CARBONTALLY_V3_PHASE_6_REPORT.md` | This report |

## 3. Files modified

| File | Change |
|---|---|
| `backend/data/organizations.py` | Added full-row columns/mappers, `get_profile`, `get_metadata_full`, `update_profile`, `update_metadata_full`, `list_members_with_email`, `get_member` |
| `backend/data/suppliers.py` | Added `search_for_org` (search/category/status filters over real columns) |
| `backend/api/v3_organizations.py` | Added `ORG_ROLES`, profile/settings GET+PUT, member detail, roles, invitations, facility/asset detail; member role validation; member list email enrichment |
| `backend/api/v3_suppliers.py` | List endpoint accepts search/category/status/limit/offset |
| `backend/api/dependencies.py` | `RepositoryBundle` gains `invitations` + `roles` |
| `backend/data/__init__.py` | Exports `InvitationsRepository` + `RolesRepository` |
| `backend/tests/unit/api/fakes.py` | Extended `MemoryOrganizations`, added `MemorySuppliers`, `MemoryInvitations`, `MemoryRoles`, `MemoryTenant`; completed `InMemoryWorld.bundle()`; added `org_admin_user` |
| `backend/tests/integration/conftest.py` | Added `user_invitations` to the truncate list |
| `frontend/src/v3/api.js` | Added customer-administration API methods |
| `frontend/src/App.js` | Registered `/organization` route + nav button + import |
| `frontend/src/v3/__tests__/api.test.js` | Added customer-admin API client tests |

## 4. API endpoints used / created

Created/extended (all `require_org_member`/`require_org_admin` + `ensure_org_access`):
- `GET/PUT /api/v3/organizations/{id}/profile` — full profile read (member) / admin update.
- `GET/PUT /api/v3/organizations/{id}/metadata` — metadata read (member) / admin update.
- `GET /api/v3/organizations/{id}/members` — email-enriched member list.
- `GET /api/v3/organizations/members/{member_id}` — member detail (org-isolated).
- `POST /{id}/members`, `PUT /members/{member_id}` — role-validated (admin).
- `DELETE /api/v3/organizations/members/{member_id}` — remove (admin).
- `GET /api/v3/organizations/{id}/roles` — customer role set (member).
- `GET/POST /{id}/invitations`, `DELETE /invitations/{id}` — admin, org-isolated.
- `GET /api/v3/organizations/facilities/{facility_id}` — detail + assets.
- `GET /api/v3/organizations/assets/{asset_id}` — detail.
- `GET /api/v3/suppliers` — extended filters.

Reused (existing, not duplicated): `GET /{id}`, facility/asset list/create/delete, supplier CRUD.

## 5. Database tables used

| Table | Usage |
|---|---|
| `organizations` | Profile + settings (real columns; no schema change) |
| `organization_metadata` | Extended metadata (real columns; no schema change) |
| `organization_members` | Members + role model (CHECK: owner/admin/member/viewer) |
| `user_invitations` | Invitations (real table; no schema change) |
| `roles` | Read-only reference for invitation `role_id` |
| `suppliers`, `facilities`, `assets` | Supplier/facility/asset surfaces |
| `users` | Email/name join for members |

**No database changes, no migrations, no RLS changes, no Supabase policy changes.**

## 6. Organization profile status

**COMPLETE (read) / PARTIAL (write).** `GET /{id}/profile` returns the full
real `organizations` row (name, legal/company, address, country, industry,
reporting prefs, sustainability flags, default settings, subscription tier —
all genuine V3M2 columns). `PUT /{id}/profile` (admin) updates a strict
whitelist of real columns (422 on unknown fields or empty name). The
subscription/billing **state** fields and system-managed columns are read-only
on this surface. Frontend provides loading/empty/error/success/validation
states.

## 7. Organization settings status

**COMPLETE.** `GET/PUT /{id}/metadata` expose the real `organization_metadata`
columns (employees, revenue, floor areas, renewable/carbon-offset percentages,
industry/NAICS/SIC, fiscal year, contacts, sustainability officer, reporting
standard). Only real columns are read/written; no settings were invented.

## 8. Members status

**COMPLETE.** Member list (email + name joined from `users`), member detail,
add member, role update, remove — all org-isolated and admin-guarded. Role
assignment is validated against the DB CHECK set (`owner`/`admin`/`member`/
`viewer`) → 422 on any other value (a customer cannot assign roles outside the
V3 role model, and cannot touch another org's members).

## 9. Invitations status

**COMPLETE.** `user_invitations` repository + `GET/POST /{org_id}/invitations`
(admin) and `DELETE /invitations/{id}` (revoke). Invitations carry email,
token, status (`pending` → `revoked`), 7-day expiry, and invited_by. `role_id`
is resolved from the `roles` table when a matching name exists, otherwise NULL
(recorded truthfully — the customer role set is the `organization_members`
CHECK model, not the staff `roles` rows).

## 10. Roles status

**COMPLETE.** The V3 customer role model is the `organization_members.role`
CHECK constraint (`owner` / `admin` / `member` / `viewer`) — surfaced via
`GET /{id}/roles` and enforced by `validate_org_role` on every member and
invitation role write. **No second role system was created.** The legacy
`roles` RBAC table is used read-only for invitation resolution.

## 11. Suppliers status

**COMPLETE.** Org-scoped supplier list/get/create/update/remove (existing V3
surface) plus read-side search/filter (`search` ILIKE on name/email/contact,
`category_id`, `status` active/inactive) added over real columns. The frontend
provides search, status filter, create and remove (with confirmation).

## 12. Facilities status

**COMPLETE.** Org-scoped facility list/create/remove (existing) + `GET
/facilities/{id}` detail that includes the facility's real assets. Facility
relationships (organization, assets) use real data; org isolation enforced.

## 13. Assets status

**COMPLETE.** Org-scoped asset list/create/remove (existing) + `GET
/assets/{id}` detail. Asset facility relationship and type use real columns.

## 14. Security settings status

**PARTIAL.** The Security tab shows real account data (email, user id) and the
sign-in provider from the Supabase Auth user; change-password uses the existing
`supabase.auth.updateUser` API (no custom authentication). Password/security
controls beyond that (password policy configuration, session management) are
**NOT SUPPORTED** by the CarbonTally backend and are documented, not invented.

## 15. Google authentication / provider status

**COMPLETE (read-only).** The existing frontend already handles the Google
OAuth callback through Supabase Auth; the Security tab surfaces the real
provider (`user.app_metadata.provider`) and linked identities
(`user.identities`) — genuine Supabase Auth data. No provider configuration is
exposed from the backend (no credentials/secrets in frontend code).

## 16. MFA/TOTP status

**NOT IMPLEMENTED (FOLLOW-ON).** CarbonTally has no MFA backend/UI surface.
The Supabase Auth platform schema includes `auth.mfa_factors` /
`auth.mfa_challenges`, but project-level MFA enablement cannot be verified in
this environment. The Security tab queries `supabase.auth.mfa.listFactors()`
and reports the real status or the documented limitation — it does **not**
provide a fake enrollment flow.

## 17. Authorization / tenant-isolation status

**COMPLETE.** Every endpoint uses the existing V3 pattern
(`require_org_member` / `require_org_admin` + `ensure_org_access`):
- Profile/settings read and write are org-isolated (cross-org → 403).
- Members: list/detail/remove cross-org → 403; role assignment validated.
- Invitations: list/create/revoke are admin-only and org-isolated.
- Suppliers/facilities/assets: list/detail cross-org → 403.
- A customer can never read/write another org's data through these surfaces.
- No RLS redesign, no service-role/credential exposure.

## 18. Tests added

- `backend/tests/unit/api/test_v3_customer_admin.py` (56 tests):
  - route registration (13 fragments); role-set validation;
  - organization profile (member read, cross-org 403, 404, staff 403, admin
    update, non-admin 403, unknown-field 422, empty payload 422, cross-org 403,
    nonexistent 404);
  - settings/metadata (read, cross-org 403, admin update, non-admin 403,
    cross-org 403);
  - members + roles (list, email enrichment, cross-org 403, detail, 404,
    cross-org detail 403, invalid role 422, admin-required 403, role update,
    cross-org remove 403, roles list, cross-org roles 403);
  - invitations (admin-required 403, create, invalid role 422, cross-org 403,
    org-scoped list, cross-org 403, revoke, cross-org revoke 403, 404);
  - suppliers (org-isolated list, cross-org 403, search/category/status
    filters, cross-org detail 403, 404);
  - facilities (org-isolated list, cross-org 403, detail + assets, cross-org
    detail 403, 404);
  - assets (org-isolated list, cross-org 403, detail, cross-org detail 403, 404).
- `backend/tests/integration/test_customer_admin.py` (5 tests): profile
  roundtrip, metadata upsert roundtrip, members-with-email, invitations
  roundtrip, roles repository.
- `frontend/src/v3/__tests__/api.test.js` — customer-admin API client exports.
- Route-fragment coverage in `test_v3_customer_admin.py`; the existing
  `test_v3_legacy_reimplementation.py` org fragments remain valid.

## 19. Tests executed

**STATIC VERIFICATION — COMPLETE.** All new/modified files were reviewed for
syntax, imports, wiring and test-logic correctness (route fragments match
mounted paths; fakes satisfy the full `RepositoryBundle`; `MemoryTenant`
returns domain objects matching the production tenant repo; memory fakes mirror
the production row shapes).
**RUNTIME TESTS NOT EXECUTED** — the development shell is wedged (documented
environment blocker), so `pytest`/`npm test` cannot run. No runtime pass is
claimed.

## 20. Runtime verification status

**BLOCKED** — the known wedged shell prevents running `pytest`, `uvicorn`,
`npm test` or any interactive command in this environment. Static checks only.

## 21. Known limitations

- **MFA/TOTP** is not implemented (no CarbonTally surface; Supabase platform
  MFA enablement unverifiable) — documented limitation, no fake MFA.
- **Invitation `role_id`** is resolved from the `roles` table when a matching
  name exists; the seeded `roles` table contains staff roles (admin,
  data_extractor, …), so customer-role invitations typically record
  `role_id = NULL` (the intended customer role is still carried by the
  invitation flow and validated by `validate_org_role`).
- **Organization profile write** is limited to the real-column whitelist;
  subscription/billing state, logo, metadata jsonb and `vat_registered` etc.
  are read-only on this surface (system-managed).
- **Supplier update** remains limited to name/contact_email/is_active (the
  existing V3 surface); full-column supplier editing is a follow-on.
- `user_invitations.invited_by` references `auth.users` (Supabase platform) —
  fine in production (the caller's Supabase user id), but integration tests
  pass `None` to avoid a cross-schema FK dependency.

## 22. API gaps

| Capability | Endpoint checked | Repo checked | DB objects checked | Missing | Minimum clean V3 implementation |
|---|---|---|---|---|---|
| MFA/TOTP enrollment/status | none (CarbonTally) | none | `auth.mfa_factors` (Supabase platform) | backend/UI surface | MFA backend + enrollment UI on Supabase Auth MFA — follow-on |
| Supplier full-column edit | `PUT /api/v3/suppliers/{id}` | `backend/data/suppliers.py` | `suppliers` (many real columns) | update of category/type/address/emissions fields | extend `SupplierUpdate` + `SuppliersRepository.update` — follow-on |
| Organization logo / metadata jsonb write | `PUT /profile` | `backend/data/organizations.py` | `organizations.logo_url`, `.metadata` | upload + jsonb write surface | storage upload + metadata write — follow-on |
| Invitation accept flow | `POST /{id}/invitations` | `backend/data/invitations.py` | `user_invitations` | accept endpoint + membership creation | accept endpoint (token verify → `organization_members` insert) — follow-on |

## 23. Database gaps

| Table | Missing data | Proposed change | Relationships | RLS implications | Reason |
|---|---|---|---|---|---|
| none required | — | none | — | — | All Phase 6 surfaces map to existing V3M2 tables/columns; **no schema change was made** |
| `user_invitations.invited_by` | cross-schema `auth.users` FK | none (works in production) | auth.users | none | documented only |

## 24. Follow-on work

- MFA/TOTP backend + enrollment UI (Supabase Auth MFA).
- Invitation accept flow (token verify → member creation).
- Full-column supplier editing.
- Organization logo / metadata jsonb write surfaces.
- Runtime verification once the environment recovers.

## 25. Phase 7 readiness decision

**READY — with the same runtime caveat as Phases 4–5.** Phase 6 code, wiring
and static verification are complete; the customer administration workflow runs
on the authoritative V3 chain with org isolation. Phase 7 (Consultants) must
not begin until (a) the wedged shell is recovered and the full backend +
frontend suites execute green, and (b) the documented follow-ons (MFA,
invitation accept, supplier full edit) are explicitly approved. Per
instructions, Phase 7/Consultants is **NOT started**.



