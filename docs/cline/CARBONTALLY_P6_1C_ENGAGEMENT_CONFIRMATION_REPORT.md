# P6-1C — Consultant Engagement Confirmation (implementation report)

Date: 2026-09-06 · Component: backend (FastAPI) + Supabase migration · Agent: Cline

## Task

Establish customer-side authorization **before** active consultant access for
ALREADY-EXISTING organisations. Previously `POST /me/clients` created an ACTIVE
grant in one step by naming an org id; at RLS level any authenticated user
could INSERT (even `status='active'`) with no qualifier. Both paths are closed.

## Design

Single relationship model retained (`consultant_clients`) — no duplicate table.
Additive schema + origin provenance; the RLS/API layer enforces state.

- `relationship_origin`: `legacy` (pre-1C rows, kept) |
  `consultant_created_customer` (Case A — firm created the org via
  `POST /me/customers`, active immediately, no second acceptance) |
  `engagement_request` (Case B — pre-existing org → **pending**, customer
  acceptance required).
- Only `status='active'` grants access (D15 unchanged). `pending`/`rejected`
  never grant.
- Customer acceptance/rejection is the ONLY `pending → active` /
  `pending → rejected` path (owner/admin authority).
- Firm may withdraw pending (→ ended), re-request rejected/ended (→ pending),
  suspend/end/reactivate once live. Legacy + Case-A rows keep the ratified D19
  firm lifecycle. Pending/rejected cannot be manufactured on non-engagement
  rows.
- RLS: authenticated INSERT/UPDATE policies on `consultant_clients` are dropped
  (incl. the **unqualified** `consultant_clients_tenant_insert` and member
  `consultant_clients_tenant_update`). All writes are server-authoritative
  (service role) via the API, which enforces the policy.

## Files changed

| File | Change |
| --- | --- |
| `supabase/migrations/20260906090000_p6_1c_consultant_engagement.sql` | **new** — columns, provenance, additive CHECK constraints, RLS hardening (idempotent) |
| `backend/domain/partners.py` | extended status vocab (incl. pre-existing `onboarding`), transitions, `can_transition_consultant_engagement` pure policy, dataclass provenance fields |
| `backend/api/consultant_auth.py` | `CLIENT_STATUSES` += `pending`/`rejected` |
| `backend/data/consultants.py` | columns/mapper, origin+status params on `add_client`, decided-field provenance on transition, `list_engagements_for_org` |
| `backend/api/v3_consultants.py` | `POST /me/clients` → engagement **request** for existing orgs (pending, target validation, re-request from rejected/ended, internal/PE-type deny); `GET /me/engagements`; origin-aware guards on PUT/suspend/end/reactivate/delete |
| `backend/api/v3_organizations.py` | customer `GET /{org}/consultant-engagements`, `POST …/accept`, `POST …/reject` (org owner/admin, org-scoped) |
| `backend/tests/unit/api/fakes.py` | mirror new signature/fields + `seed_org`/`list_engagements_for_org` |
| `backend/tests/unit/api/test_v3_consultants.py` | one test adapted to the new (intended) pending-first semantics |
| `backend/tests/unit/api/test_p6_1c_engagement_confirmation.py` | **new** — 25 tests (routes, request, firm restrictions, customer list/accept/reject, org/role isolation, domain policy) |
| `docs/cline/CARBONTALLY_P6_1C_ENGAGEMENT_CONFIRMATION_REPORT.md` | this report |

## Runtime verification (real local PG)

- Migration applied idempotently (`APPLY_EXIT:0` twice).
- Live status distribution check surfaced pre-existing `onboarding` (244 rows)
  → CHECK constraint is additive and includes it (672 active, 1 inactive intact).
- Verified: RLS enabled; 4 new columns; both constraints present; policies now
  `cc_delete_own_firm, cc_select_own_firm, consultant_clients_tenant_delete,
  consultant_clients_tenant_select`; 917 existing rows defaulted to `legacy`.
- Tests: 14 targeted suites incl. the new file → **EXIT:0** (D19 lifecycle,
  customer admin, consultant revocation/branding/context/white-label,
  P6-BILL-1, P6-1B, onboarding, billing, audit).

## Remaining work / notes

- Frontend: surface pending engagements on the customer org admin UI
  (list/accept/reject) and reflect `pending` status in the consultant client
  list. No UI changes were made in this backend-scoped task.
- Any legacy client/UI flow that previously INSERTed/UPDATEd
  `consultant_clients` directly (PostgREST) is now blocked by RLS by design —
  such flows must go through the FastAPI routes.
- No Git commit created (per session protocol the change set is left in the
  working tree for review).
